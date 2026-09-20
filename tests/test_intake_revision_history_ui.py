import hashlib
import sqlite3
import time
from pathlib import Path

import app as app_module

from database.intake_correction_versioning_migration import (
    apply_intake_correction_versioning_schema,
)
from services.services_intake_correction_versioning import (
    IntakeCorrectionVersioningError,
    create_answer_revision,
    create_snapshot_version,
    get_intake_revision_history,
)


ROOT = Path(__file__).resolve().parents[1]


def _database(tmp_path):
    path = tmp_path / "revision-history.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.executescript("""
            CREATE TABLE intake_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intake_id TEXT UNIQUE NOT NULL,
                firm_id TEXT NOT NULL
            );
            CREATE TABLE intake_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT NOT NULL,
                firm_id TEXT, question_key TEXT NOT NULL,
                answer_key TEXT NOT NULL, answer_label TEXT,
                created_at TEXT, created_by TEXT
            );
            CREATE TABLE intake_translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT NOT NULL,
                firm_id TEXT, source_key TEXT NOT NULL, system_category TEXT,
                system_meaning TEXT, module_trigger TEXT,
                document_request TEXT, next_session TEXT, risk_flag TEXT,
                created_at TEXT, created_by TEXT
            );
            CREATE TABLE intake_followup_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT NOT NULL,
                firm_id TEXT, task_type TEXT, priority TEXT, status TEXT,
                title TEXT NOT NULL, description TEXT, source TEXT,
                created_at TEXT, updated_at TEXT, created_by TEXT,
                completed_at TEXT, completed_by TEXT
            );
            INSERT INTO intake_sessions (intake_id, firm_id)
            VALUES ('INT-1', 'FIRM-1'), ('INT-2', 'FIRM-2');
        """)
    apply_intake_correction_versioning_schema(path)
    return path


def _answers(*values):
    return [
        {
            "question_key": "assets",
            "answer_key": value,
            "answer_label": value.title(),
        }
        for value in values
    ]


def _snapshot(db, firm, intake, revision, number):
    return create_snapshot_version(
        db,
        firm,
        intake,
        revision["answer_revision_id"],
        [{"source_key": f"assets.v{number}", "system_meaning": "asset"}],
        [],
        "engine",
    )


def _two_revisions(db):
    first = create_answer_revision(
        db, "FIRM-1", "INT-1", _answers("home", "business"), "user"
    )
    first_snapshot = _snapshot(db, "FIRM-1", "INT-1", first, 1)
    second = create_answer_revision(
        db, "FIRM-1", "INT-1", _answers("home", "brokerage"), "user"
    )
    second_snapshot = _snapshot(db, "FIRM-1", "INT-1", second, 2)
    return first, first_snapshot, second, second_snapshot


def _governed_digest(db):
    with sqlite3.connect(db) as connection:
        rows = []
        for table in (
            "intake_answer_revisions",
            "intake_answer_revision_items",
            "intake_snapshot_versions",
            "intake_snapshot_translation_items",
            "intake_snapshot_proposed_tasks",
        ):
            rows.append((table, connection.execute(
                f'SELECT * FROM "{table}" ORDER BY rowid'
            ).fetchall()))
    return hashlib.sha256(repr(rows).encode()).hexdigest()


def test_history_preserves_revisions_pairs_snapshots_and_derives_changes(tmp_path):
    db = _database(tmp_path)
    first, first_snapshot, second, second_snapshot = _two_revisions(db)

    history = get_intake_revision_history(db, "FIRM-1", "INT-1")

    assert [row["answer_revision_no"] for row in history] == [1, 2]
    assert [row["intake_id"] for row in history] == ["INT-1", "INT-1"]
    assert history[0]["answer_revision_id"] == first["answer_revision_id"]
    assert history[0]["snapshot_version"]["snapshot_version_id"] == first_snapshot["snapshot_version_id"]
    assert history[1]["answer_revision_id"] == second["answer_revision_id"]
    assert history[1]["snapshot_version"]["snapshot_version_id"] == second_snapshot["snapshot_version_id"]
    assert history[0]["changes"] == {"additions": [], "removals": []}
    assert history[1]["changes"] == {
        "additions": [{"question_key": "assets", "answer_key": "brokerage"}],
        "removals": [{"question_key": "assets", "answer_key": "business"}],
    }


def test_history_is_strictly_firm_scoped(tmp_path):
    db = _database(tmp_path)
    _two_revisions(db)

    try:
        get_intake_revision_history(db, "FIRM-2", "INT-1")
    except IntakeCorrectionVersioningError:
        pass
    else:
        raise AssertionError("cross-firm history was exposed")


def test_get_route_renders_labels_fallbacks_and_does_not_mutate(tmp_path, monkeypatch):
    db = _database(tmp_path)
    _two_revisions(db)
    with sqlite3.connect(db) as connection:
        revision_id = connection.execute(
            "SELECT answer_revision_id FROM intake_answer_revisions "
            "ORDER BY answer_revision_no DESC LIMIT 1"
        ).fetchone()[0]
        connection.execute(
            "INSERT INTO intake_answer_revision_items "
            "(answer_revision_id, question_key, answer_key, answer_label, created_at) "
            "VALUES (?, 'historic_unknown', 'old_value', NULL, '2026-01-01T00:00:00Z')",
            (revision_id,),
        )

    monkeypatch.setattr(app_module, "DB_PATH", str(db))
    monkeypatch.setattr(app_module, "HINDSFOOT_INTAKE_VERSIONING_1E_ENABLED", True)
    monkeypatch.setattr(app_module, "get_universal_intake_questions", lambda: {
        "assets": {
            "label": "Which assets do you own?",
            "options": {
                "home": "A home",
                "business": "A business",
                "brokerage": "A brokerage account",
            },
        }
    })

    before = _governed_digest(db)
    with sqlite3.connect(db) as connection:
        work_before = connection.execute(
            "SELECT COUNT(*) FROM intake_followup_tasks"
        ).fetchone()[0]

    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()
    with client.session_transaction() as session:
        session["username"] = "auditor"
        session["role"] = "Admin"
        session["firm_id"] = "FIRM-1"
        session["last_activity"] = time.time()
    response = client.get("/intake/INT-1/revision-history")

    with client.session_transaction() as session:
        messages = session.get("_flashes", [])
    assert response.status_code == 200, (response.headers.get("Location"), messages)
    page = response.get_data(as_text=True)
    assert "Revision History" in page
    assert "Which assets do you own?" in page
    assert "A brokerage account" in page
    assert "Historic Unknown" in page
    assert "Old Value" in page
    assert "Changes from Previous Revision" in page
    assert "Return to Current Translation Snapshot" in page
    assert "<form" not in page.lower()
    assert _governed_digest(db) == before
    with sqlite3.connect(db) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM intake_followup_tasks"
        ).fetchone()[0] == work_before


def test_snapshot_link_and_existing_route_contracts_remain_present():
    snapshot = (ROOT / "templates/intake/client_snapshot.html").read_text()
    app_source = (ROOT / "app.py").read_text(encoding="utf-8", errors="replace")
    assert "View Revision History" in snapshot
    assert "intake_universal_profile" in snapshot
    assert "intake_confirm_snapshot" in snapshot
    assert '@app.route("/intake/<intake_id>/revision-history", methods=["GET"])' in app_source
    assert '@app.route("/intake/<intake_id>/snapshot/confirm", methods=["POST"])' in app_source
