import sqlite3

import pytest
from werkzeug.datastructures import MultiDict

from database.intake_correction_versioning_migration import (
    apply_intake_correction_versioning_schema,
)
from services.services_intake_correction_versioning import (
    IntakeCorrectionVersioningError,
    answers_match_latest_governed_revision,
    create_answer_revision,
    create_snapshot_version,
)


LEGACY_SCHEMA = """
CREATE TABLE intake_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intake_id TEXT UNIQUE NOT NULL,
    firm_id TEXT NOT NULL,
    status TEXT,
    updated_at TEXT
);
CREATE TABLE intake_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT NOT NULL,
    firm_id TEXT, question_key TEXT NOT NULL, answer_key TEXT NOT NULL,
    answer_label TEXT, created_at TEXT, created_by TEXT
);
CREATE TABLE intake_translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT NOT NULL,
    firm_id TEXT, source_key TEXT NOT NULL, system_category TEXT,
    system_meaning TEXT, module_trigger TEXT, document_request TEXT,
    next_session TEXT, risk_flag TEXT, created_at TEXT, created_by TEXT
);
CREATE TABLE intake_followup_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT NOT NULL,
    firm_id TEXT, task_type TEXT, priority TEXT, status TEXT,
    title TEXT NOT NULL, description TEXT, source TEXT, created_at TEXT,
    updated_at TEXT, created_by TEXT, completed_at TEXT, completed_by TEXT
);
INSERT INTO intake_sessions (intake_id, firm_id) VALUES ('INT-1', 'FIRM-1');
INSERT INTO intake_sessions (intake_id, firm_id) VALUES ('INT-2', 'FIRM-2');
"""


@pytest.fixture
def governed_db(tmp_path):
    path = tmp_path / "noop-correction.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.executescript(LEGACY_SCHEMA)
    assert apply_intake_correction_versioning_schema(path)["schema_complete"] is True
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE intake_followup_reconciliations "
            "(reconciliation_id TEXT PRIMARY KEY)"
        )
    return path


def _items(*pairs, label="Original label"):
    return [
        {"question_key": question, "answer_key": answer, "answer_label": label}
        for question, answer in pairs
    ]


def _seed_revision(path, pairs):
    return create_answer_revision(path, "FIRM-1", "INT-1", _items(*pairs), "tester")


def test_exact_single_select_identities_match(governed_db):
    _seed_revision(governed_db, [("decision_style", "shared")])
    assert answers_match_latest_governed_revision(
        governed_db, "FIRM-1", "INT-1", _items(("decision_style", "shared"))
    )


def test_multiselect_order_and_labels_are_ignored(governed_db):
    _seed_revision(governed_db, [("assets", "home"), ("assets", "business")])
    submitted = _items(
        ("assets", "business"), ("assets", "home"), label="Renamed display text"
    )
    assert answers_match_latest_governed_revision(
        governed_db, "FIRM-1", "INT-1", submitted
    )


@pytest.mark.parametrize(
    "latest,submitted",
    [
        ([('assets', 'home')], [('assets', 'home'), ('assets', 'cash')]),
        ([('assets', 'home'), ('assets', 'cash')], [('assets', 'home')]),
        ([('assets', 'home')], [('assets', 'business')]),
    ],
    ids=["answer-added", "answer-removed", "answer-key-changed"],
)
def test_identity_differences_do_not_match(governed_db, latest, submitted):
    _seed_revision(governed_db, latest)
    assert not answers_match_latest_governed_revision(
        governed_db, "FIRM-1", "INT-1", _items(*submitted)
    )


def test_duplicate_submitted_identity_is_rejected(governed_db):
    _seed_revision(governed_db, [("assets", "home")])
    with pytest.raises(IntakeCorrectionVersioningError, match="duplicate"):
        answers_match_latest_governed_revision(
            governed_db,
            "FIRM-1",
            "INT-1",
            _items(("assets", "home"), ("assets", "home")),
        )


def test_no_revision_returns_false_and_scope_is_enforced(governed_db):
    assert not answers_match_latest_governed_revision(
        governed_db, "FIRM-1", "INT-1", []
    )
    with pytest.raises(IntakeCorrectionVersioningError, match="same intake"):
        answers_match_latest_governed_revision(
            governed_db, "FIRM-2", "INT-1", []
        )


def _route_setup(monkeypatch, app_module, path):
    questions = {
        "assets": {
            "label": "Assets",
            "input_type": "multi",
            "options": {"home": "Home", "business": "Business", "cash": "Cash"},
        },
        "decision_style": {
            "label": "Decision style",
            "input_type": "single",
            "options": {"shared": "Shared", "solo": "Solo"},
        },
    }
    monkeypatch.setattr(app_module, "DB_PATH", path)
    monkeypatch.setattr(app_module, "HINDSFOOT_INTAKE_VERSIONING_1E_ENABLED", True)
    monkeypatch.setattr(app_module, "ensure_intake_translation_tables", lambda: None)
    monkeypatch.setattr(
        app_module, "get_intake_session",
        lambda intake_id: {"intake_id": intake_id, "intake_lane": "guided"},
    )
    monkeypatch.setattr(app_module, "get_universal_intake_questions", lambda: questions)
    app_module.app.config.update(TESTING=True, SECRET_KEY="test")
    return questions


def _counts(path):
    tables = (
        "intake_answer_revisions", "intake_answer_revision_items",
        "intake_snapshot_versions", "intake_snapshot_translation_items",
        "intake_snapshot_proposed_tasks", "intake_followup_tasks",
        "intake_followup_reconciliations", "intake_answers", "intake_translations",
    )
    with sqlite3.connect(path) as connection:
        return tuple(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                     for table in tables)


def test_identical_governed_correction_redirects_without_any_writes(
    governed_db, monkeypatch
):
    import app as app_module

    revision = _seed_revision(
        governed_db,
        [("assets", "home"), ("assets", "business"), ("decision_style", "shared")],
    )
    snapshot = create_snapshot_version(
        governed_db, "FIRM-1", "INT-1", revision["answer_revision_id"], [], [], "tester"
    )
    with sqlite3.connect(governed_db) as connection:
        connection.execute(
            "UPDATE intake_answer_revisions SET revision_status = 'confirmed' "
            "WHERE answer_revision_id = ?", (revision["answer_revision_id"],)
        )
        connection.execute(
            "UPDATE intake_snapshot_versions SET confirmation_status = 'confirmed' "
            "WHERE snapshot_version_id = ?", (snapshot["snapshot_version_id"],)
        )
    _route_setup(monkeypatch, app_module, governed_db)
    before = _counts(governed_db)
    with app_module.app.test_request_context(
        "/intake/INT-1/universal-profile?correction=1", method="POST",
        data=MultiDict([("assets", "business"), ("assets", "home"),
                        ("decision_style", "shared")]),
    ):
        app_module.session.update(firm_id="FIRM-1", username="tester")
        response = app_module.intake_universal_profile("INT-1")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/intake/INT-1/snapshot")
        assert app_module.session["_flashes"] == [(
            "info",
            "No changes were detected. Your current intake answers remain unchanged.",
        )]
    assert _counts(governed_db) == before
    with sqlite3.connect(governed_db) as connection:
        assert connection.execute(
            "SELECT revision_status FROM intake_answer_revisions"
        ).fetchone()[0] == "confirmed"
        assert connection.execute(
            "SELECT confirmation_status FROM intake_snapshot_versions"
        ).fetchone()[0] == "confirmed"


def test_changed_correction_and_initial_post_stay_on_existing_path(
    governed_db, monkeypatch
):
    import app as app_module

    _seed_revision(governed_db, [("assets", "home")])
    _route_setup(monkeypatch, app_module, governed_db)
    saved = []
    result = {
        "intake_id": "INT-1", "answers": _items(("assets", "cash")),
        "translations": [], "summary": {}, "scores": {},
    }
    monkeypatch.setattr(app_module, "save_universal_profile_answers",
                        lambda **kwargs: saved.append(kwargs) or result)
    monkeypatch.setattr(app_module, "build_client_snapshot", lambda value: {})
    monkeypatch.setattr(app_module, "save_client_snapshot", lambda **kwargs: None)
    monkeypatch.setattr(app_module, "render_template", lambda *args, **kwargs: "rendered")
    monkeypatch.setattr(app_module, "list_intake_followup_tasks", lambda intake_id: [])
    monkeypatch.setattr(app_module, "get_review_note_form_options", lambda: [])
    monkeypatch.setattr(app_module, "get_followup_task_form_options", lambda: [])
    monkeypatch.setattr(app_module, "summarize_followup_tasks", lambda tasks: {})
    monkeypatch.setattr(app_module, "group_followup_tasks", lambda tasks: {})

    with app_module.app.test_request_context(
        "/intake/INT-1/universal-profile?correction=1",
        method="POST", data={"assets": "cash"},
    ):
        app_module.session.update(firm_id="FIRM-1", username="tester")
        assert app_module.intake_universal_profile("INT-1") == "rendered"
    with sqlite3.connect(governed_db) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM intake_answer_revisions"
        ).fetchone()[0] == 2
        assert connection.execute(
            "SELECT COUNT(*) FROM intake_snapshot_versions"
        ).fetchone()[0] == 1

    with app_module.app.test_request_context(
        "/intake/INT-1/universal-profile", method="POST", data={"assets": "cash"},
    ):
        app_module.session.update(firm_id="FIRM-1", username="tester")
        assert app_module.intake_universal_profile("INT-1") == "rendered"
    assert len(saved) == 2


def test_correction_get_prefill_is_unchanged(governed_db, monkeypatch):
    import app as app_module

    _seed_revision(
        governed_db,
        [("assets", "home"), ("decision_style", "shared")],
    )
    _route_setup(monkeypatch, app_module, governed_db)

    with app_module.app.test_request_context(
        "/intake/INT-1/universal-profile?correction=1"
    ):
        app_module.session["firm_id"] = "FIRM-1"
        response = app_module.intake_universal_profile("INT-1")

    assert 'value="home" checked' in response
    assert 'value="shared" checked' in response
    assert (
        'action="/intake/INT-1/universal-profile?correction=1"'
        in response
    )
