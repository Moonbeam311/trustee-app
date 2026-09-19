import sqlite3

import pytest

from services.services_intake_correction_versioning import (
    IntakeCorrectionVersioningError,
    get_latest_governed_answer_selections,
)


SCHEMA = """
CREATE TABLE intake_sessions (
    intake_id TEXT PRIMARY KEY,
    firm_id TEXT NOT NULL
);
CREATE TABLE intake_answer_revisions (
    answer_revision_id TEXT PRIMARY KEY,
    intake_id TEXT NOT NULL,
    firm_id TEXT NOT NULL,
    answer_revision_no INTEGER NOT NULL
);
CREATE TABLE intake_answer_revision_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    answer_revision_id TEXT NOT NULL,
    question_key TEXT NOT NULL,
    answer_key TEXT NOT NULL
);
CREATE TABLE intake_snapshot_versions (
    snapshot_version_id TEXT PRIMARY KEY
);
CREATE TABLE intake_snapshot_proposed_tasks (
    proposed_task_id TEXT PRIMARY KEY
);
CREATE TABLE intake_followup_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intake_id TEXT NOT NULL,
    title TEXT NOT NULL
);
INSERT INTO intake_sessions VALUES ('INT-1', 'FIRM-1');
INSERT INTO intake_sessions VALUES ('INT-2', 'FIRM-2');
INSERT INTO intake_answer_revisions VALUES ('REV-OLD', 'INT-1', 'FIRM-1', 1);
INSERT INTO intake_answer_revisions VALUES ('REV-LATEST', 'INT-1', 'FIRM-1', 2);
INSERT INTO intake_answer_revision_items
    (answer_revision_id, question_key, answer_key)
VALUES
    ('REV-OLD', 'assets', 'old_asset'),
    ('REV-OLD', 'decision_style', 'old_style'),
    ('REV-LATEST', 'assets', 'home'),
    ('REV-LATEST', 'assets', 'business'),
    ('REV-LATEST', 'decision_style', 'shared');
INSERT INTO intake_snapshot_versions VALUES ('SNAP-1');
INSERT INTO intake_snapshot_proposed_tasks VALUES ('PROPOSAL-1');
"""


@pytest.fixture
def governed_db(tmp_path):
    path = tmp_path / "correction-prefill.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
    return path


def test_latest_revision_is_firm_scoped_and_preserves_all_selections(governed_db):
    selections = get_latest_governed_answer_selections(
        governed_db, "FIRM-1", "INT-1"
    )

    assert selections == {
        "assets": ["home", "business"],
        "decision_style": ["shared"],
    }
    assert "old_asset" not in selections["assets"]
    with pytest.raises(IntakeCorrectionVersioningError):
        get_latest_governed_answer_selections(governed_db, "FIRM-2", "INT-1")
    assert get_latest_governed_answer_selections(
        governed_db, "FIRM-2", "INT-2"
    ) == {}


def _counts(path):
    with sqlite3.connect(path) as connection:
        return connection.execute(
            """
            SELECT
              (SELECT COUNT(*) FROM intake_answer_revisions),
              (SELECT COUNT(*) FROM intake_snapshot_versions),
              (SELECT COUNT(*) FROM intake_followup_tasks)
            """
        ).fetchone()


def test_correction_get_prefills_without_creating_governed_or_operational_rows(
    governed_db, monkeypatch
):
    import app as app_module

    questions = {
        "assets": {
            "label": "Assets",
            "input_type": "multi",
            "options": {"home": "Home", "business": "Business", "cash": "Cash"},
        },
        "decision_style": {
            "label": "Decision style",
            "input_type": "single",
            "options": {"solo": "Solo", "shared": "Shared"},
        },
    }
    monkeypatch.setattr(app_module, "DB_PATH", governed_db)
    monkeypatch.setattr(app_module, "HINDSFOOT_INTAKE_VERSIONING_1E_ENABLED", True)
    monkeypatch.setattr(app_module, "ensure_intake_translation_tables", lambda: None)
    monkeypatch.setattr(
        app_module,
        "get_intake_session",
        lambda intake_id: {"intake_id": intake_id, "intake_lane": "guided"},
    )
    monkeypatch.setattr(app_module, "get_universal_intake_questions", lambda: questions)
    app_module.app.config.update(TESTING=True, SECRET_KEY="test")
    before = _counts(governed_db)
    with app_module.app.test_request_context(
        "/intake/INT-1/universal-profile?correction=1"
    ):
        app_module.session["firm_id"] = "FIRM-1"
        html = app_module.intake_universal_profile("INT-1")
    after = _counts(governed_db)

    assert 'value="home" checked' in html
    assert 'value="business" checked' in html
    assert 'value="shared" checked' in html
    assert 'value="cash" checked' not in html
    assert 'value="solo" checked' not in html
    assert "Correction mode" in html
    assert after == before


def test_non_correction_get_is_not_prefilled_from_governed_state(
    governed_db, monkeypatch
):
    import app as app_module

    monkeypatch.setattr(app_module, "DB_PATH", governed_db)
    monkeypatch.setattr(app_module, "HINDSFOOT_INTAKE_VERSIONING_1E_ENABLED", True)
    monkeypatch.setattr(app_module, "ensure_intake_translation_tables", lambda: None)
    monkeypatch.setattr(
        app_module,
        "get_intake_session",
        lambda intake_id: {"intake_id": intake_id, "intake_lane": "guided"},
    )
    monkeypatch.setattr(
        app_module,
        "get_universal_intake_questions",
        lambda: {
            "assets": {
                "label": "Assets",
                "input_type": "multi",
                "options": {"home": "Home", "business": "Business"},
            }
        },
    )
    app_module.app.config.update(TESTING=True, SECRET_KEY="test")
    with app_module.app.test_request_context("/intake/INT-1/universal-profile"):
        app_module.session["firm_id"] = "FIRM-1"
        html = app_module.intake_universal_profile("INT-1")

    assert " checked" not in html
