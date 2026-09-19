import sqlite3

import pytest

from database.intake_correction_versioning_migration import (
    apply_intake_correction_versioning_schema,
)
from services.services_intake_correction_versioning import (
    IntakeCorrectionVersioningError,
    confirm_snapshot,
    create_answer_revision,
    create_snapshot_version,
    get_intake_correction_versioning_state,
)


LEGACY_SCHEMA = """
CREATE TABLE intake_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intake_id TEXT UNIQUE NOT NULL,
    firm_id TEXT NOT NULL
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intake_id TEXT NOT NULL,
    firm_id TEXT,
    task_type TEXT,
    priority TEXT,
    status TEXT,
    title TEXT NOT NULL,
    description TEXT,
    source TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    completed_at TEXT,
    completed_by TEXT
);
INSERT INTO intake_sessions (intake_id, firm_id) VALUES ('INT-1', 'FIRM-1');
INSERT INTO intake_sessions (intake_id, firm_id) VALUES ('INT-2', 'FIRM-2');
"""


def _db(tmp_path):
    db_path = tmp_path / "disposable-1d.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(LEGACY_SCHEMA)
    result = apply_intake_correction_versioning_schema(db_path)
    assert result["schema_complete"] is True
    return db_path


def _answers(*keys):
    return [
        {
            "question_key": "assets",
            "answer_key": key,
            "answer_label": key.title(),
        }
        for key in keys
    ]


def _translations(meaning):
    return [{
        "source_key": "assets.home",
        "system_category": "ASSET",
        "system_meaning": meaning,
        "module_trigger": "property",
        "document_request": "deed",
        "next_session": "asset_review",
        "risk_flag": None,
    }]


def _tasks(title="Review deed"):
    return [{
        "task_type": "document",
        "priority": "high",
        "title": title,
        "description": "Collect and review the current deed.",
        "source": "guided_intake",
    }]


def test_revision_snapshot_supersession_and_confirmation_lifecycle(tmp_path):
    db_path = _db(tmp_path)

    revision_1 = create_answer_revision(
        db_path, "FIRM-1", "INT-1", _answers("home", "business"), "user-1"
    )
    assert revision_1["answer_revision_no"] == 1
    snapshot_1 = create_snapshot_version(
        db_path,
        "FIRM-1",
        "INT-1",
        revision_1["answer_revision_id"],
        _translations("real_property_v1"),
        _tasks("Review original deed"),
        "engine-1",
    )
    assert snapshot_1["snapshot_version_no"] == 1
    assert snapshot_1["answer_revision_id"] == revision_1["answer_revision_id"]

    with sqlite3.connect(db_path) as connection:
        assert connection.execute(
            "SELECT answer_key FROM intake_answer_revision_items "
            "WHERE answer_revision_id = ? ORDER BY id",
            (revision_1["answer_revision_id"],),
        ).fetchall() == [("home",), ("business",)]
        assert connection.execute(
            "SELECT system_meaning FROM intake_snapshot_translation_items "
            "WHERE snapshot_version_id = ?",
            (snapshot_1["snapshot_version_id"],),
        ).fetchall() == [("real_property_v1",)]
        assert connection.execute(
            "SELECT COUNT(*) FROM intake_snapshot_proposed_tasks "
            "WHERE snapshot_version_id = ? AND proposal_status = 'proposed'",
            (snapshot_1["snapshot_version_id"],),
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM intake_followup_tasks "
            "WHERE snapshot_version_id IS NOT NULL"
        ).fetchone()[0] == 0

    revision_2 = create_answer_revision(
        db_path, "FIRM-1", "INT-1", _answers("home", "brokerage"), "user-1"
    )
    assert revision_2["answer_revision_no"] == 2
    assert revision_2["intake_id"] == revision_1["intake_id"] == "INT-1"
    assert revision_2["supersedes_revision_id"] == revision_1["answer_revision_id"]

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        old_revision = connection.execute(
            "SELECT * FROM intake_answer_revisions WHERE answer_revision_id = ?",
            (revision_1["answer_revision_id"],),
        ).fetchone()
        old_snapshot = connection.execute(
            "SELECT * FROM intake_snapshot_versions WHERE snapshot_version_id = ?",
            (snapshot_1["snapshot_version_id"],),
        ).fetchone()
        assert old_revision["revision_status"] == "superseded"
        assert old_snapshot["confirmation_status"] == "superseded"
        assert connection.execute(
            "SELECT proposal_status FROM intake_snapshot_proposed_tasks "
            "WHERE snapshot_version_id = ?",
            (snapshot_1["snapshot_version_id"],),
        ).fetchone()[0] == "superseded"

    with pytest.raises(IntakeCorrectionVersioningError, match="superseded"):
        confirm_snapshot(
            db_path, "FIRM-1", "INT-1", snapshot_1["snapshot_version_id"], "reviewer"
        )

    snapshot_2 = create_snapshot_version(
        db_path,
        "FIRM-1",
        "INT-1",
        revision_2["answer_revision_id"],
        _translations("real_property_v2"),
        _tasks(),
        "engine-1",
    )
    assert snapshot_2["snapshot_version_no"] == 2
    assert snapshot_2["supersedes_snapshot_id"] == snapshot_1["snapshot_version_id"]

    state = get_intake_correction_versioning_state(db_path, "FIRM-1", "INT-1")
    assert state["answer_revision_no"] == 2
    assert state["snapshot_version_no"] == 2
    assert state["confirmation_state"] == "awaiting_confirmation"
    assert state["correction_allowed"] is True
    assert state["confirmation_allowed"] is True
    assert state["latest_snapshot_matches_latest_revision"] is True
    assert (
        state["current_snapshot_version"]["snapshot_version_id"]
        == snapshot_2["snapshot_version_id"]
    )

    first_confirmation = confirm_snapshot(
        db_path, "FIRM-1", "INT-1", snapshot_2["snapshot_version_id"], "reviewer"
    )
    second_confirmation = confirm_snapshot(
        db_path, "FIRM-1", "INT-1", snapshot_2["snapshot_version_id"], "reviewer"
    )
    assert first_confirmation["materialized_task_count"] == 1
    assert first_confirmation["already_confirmed"] is False
    assert second_confirmation["materialized_task_count"] == 1
    assert second_confirmation["already_confirmed"] is True

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM intake_followup_tasks WHERE snapshot_version_id = ?",
            (snapshot_2["snapshot_version_id"],),
        ).fetchall()
        assert len(rows) == 1
        assert rows[0]["generation_batch_id"] == snapshot_2["generation_batch_id"]
        proposal = connection.execute(
            "SELECT * FROM intake_snapshot_proposed_tasks "
            "WHERE snapshot_version_id = ?",
            (snapshot_2["snapshot_version_id"],),
        ).fetchone()
        assert proposal["proposal_status"] == "materialized"
        assert proposal["materialized_followup_task_id"] == str(rows[0]["id"])

    revision_3 = create_answer_revision(
        db_path, "FIRM-1", "INT-1", _answers("home", "retirement"), "user-2"
    )
    assert revision_3["answer_revision_no"] == 3
    with sqlite3.connect(db_path) as connection:
        confirmed_snapshot = connection.execute(
            "SELECT confirmation_status FROM intake_snapshot_versions "
            "WHERE snapshot_version_id = ?",
            (snapshot_2["snapshot_version_id"],),
        ).fetchone()[0]
        confirmed_tasks = connection.execute(
            "SELECT COUNT(*) FROM intake_followup_tasks WHERE snapshot_version_id = ?",
            (snapshot_2["snapshot_version_id"],),
        ).fetchone()[0]
        assert confirmed_snapshot == "confirmed"
        assert confirmed_tasks == 1

    corrected_state = get_intake_correction_versioning_state(db_path, "FIRM-1", "INT-1")
    assert corrected_state["answer_revision_no"] == 3
    assert corrected_state["confirmation_state"] == "not_generated"
    assert corrected_state["confirmation_allowed"] is False
    assert corrected_state["latest_snapshot_matches_latest_revision"] is False
    assert corrected_state["current_snapshot_version"] is None
    assert (
        corrected_state["latest_snapshot_version"]["snapshot_version_id"]
        == snapshot_2["snapshot_version_id"]
    )


def test_confirmed_and_older_revisions_cannot_generate_snapshots(tmp_path):
    db_path = _db(tmp_path)
    revision_1 = create_answer_revision(
        db_path, "FIRM-1", "INT-1", _answers("home"), "user-1"
    )
    snapshot_1 = create_snapshot_version(
        db_path,
        "FIRM-1",
        "INT-1",
        revision_1["answer_revision_id"],
        _translations("real_property_v1"),
        _tasks("Review original deed"),
        "engine-1",
    )
    confirm_snapshot(
        db_path, "FIRM-1", "INT-1", snapshot_1["snapshot_version_id"], "reviewer"
    )

    with sqlite3.connect(db_path) as connection:
        counts_before_confirmed_rejection = connection.execute(
            "SELECT (SELECT COUNT(*) FROM intake_snapshot_versions), "
            "(SELECT COUNT(*) FROM intake_snapshot_translation_items), "
            "(SELECT COUNT(*) FROM intake_snapshot_proposed_tasks)"
        ).fetchone()

    with pytest.raises(IntakeCorrectionVersioningError, match="not awaiting confirmation"):
        create_snapshot_version(
            db_path,
            "FIRM-1",
            "INT-1",
            revision_1["answer_revision_id"],
            _translations("must_not_exist"),
            _tasks("Must not exist"),
            "engine-1",
        )

    with sqlite3.connect(db_path) as connection:
        assert connection.execute(
            "SELECT (SELECT COUNT(*) FROM intake_snapshot_versions), "
            "(SELECT COUNT(*) FROM intake_snapshot_translation_items), "
            "(SELECT COUNT(*) FROM intake_snapshot_proposed_tasks)"
        ).fetchone() == counts_before_confirmed_rejection

    create_answer_revision(
        db_path, "FIRM-1", "INT-1", _answers("brokerage"), "user-2"
    )
    with sqlite3.connect(db_path) as connection:
        counts_before_older_rejection = connection.execute(
            "SELECT (SELECT COUNT(*) FROM intake_snapshot_versions), "
            "(SELECT COUNT(*) FROM intake_snapshot_translation_items), "
            "(SELECT COUNT(*) FROM intake_snapshot_proposed_tasks)"
        ).fetchone()

    with pytest.raises(IntakeCorrectionVersioningError, match="older/non-current"):
        create_snapshot_version(
            db_path,
            "FIRM-1",
            "INT-1",
            revision_1["answer_revision_id"],
            _translations("must_not_exist"),
            _tasks("Must not exist"),
            "engine-1",
        )

    with sqlite3.connect(db_path) as connection:
        assert connection.execute(
            "SELECT (SELECT COUNT(*) FROM intake_snapshot_versions), "
            "(SELECT COUNT(*) FROM intake_snapshot_translation_items), "
            "(SELECT COUNT(*) FROM intake_snapshot_proposed_tasks)"
        ).fetchone() == counts_before_older_rejection


def test_duplicate_answers_and_invalid_firm_intake_links_are_atomic(tmp_path):
    db_path = _db(tmp_path)

    with pytest.raises(IntakeCorrectionVersioningError, match="duplicate"):
        create_answer_revision(
            db_path, "FIRM-1", "INT-1", _answers("home", "home"), "user-1"
        )
    with sqlite3.connect(db_path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM intake_answer_revisions"
        ).fetchone()[0] == 0

    with pytest.raises(IntakeCorrectionVersioningError, match="same intake"):
        create_answer_revision(
            db_path, "FIRM-2", "INT-1", _answers("home"), "user-1"
        )

    revision = create_answer_revision(
        db_path, "FIRM-1", "INT-1", _answers("home"), "user-1"
    )
    with pytest.raises(IntakeCorrectionVersioningError, match="does not belong"):
        create_snapshot_version(
            db_path,
            "FIRM-2",
            "INT-2",
            revision["answer_revision_id"],
            _translations("wrong_scope"),
            _tasks(),
            "engine-1",
        )
    with sqlite3.connect(db_path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM intake_snapshot_versions"
        ).fetchone()[0] == 0


def test_requires_explicit_disposable_database_path():
    with pytest.raises(ValueError, match="db_path is required"):
        create_answer_revision("", "FIRM-1", "INT-1", [], "user-1")
