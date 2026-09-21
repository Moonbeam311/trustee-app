import sqlite3

import pytest

import database.db as db


INTAKE_ID = "INT-SOURCE-RECONCILIATION"
FIRM_ID = "FIRM-SOURCE-RECONCILIATION"
WORKFLOW_KEY = "estate_plan"


@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    path = tmp_path / "professional-review-source-disappearance.sqlite3"
    monkeypatch.setattr(db, "get_connection", lambda: sqlite3.connect(path))
    db.ensure_professional_review_issue_tables()
    return path


def _record(title, **extra):
    return {"issue_title": title, "issue_description": title, **extra}


def _sync(records):
    return db.seed_professional_review_issues_from_packet(
        INTAKE_ID,
        FIRM_ID,
        WORKFLOW_KEY,
        {"open_issue_records": records},
        actor="packet-sync",
    )


def _rows(path, table="professional_review_issues"):
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(
            f"SELECT * FROM {table} ORDER BY id"
        )]


def _events(path, issue_id, event_type):
    return [
        row for row in _rows(path, "professional_review_issue_events")
        if row["issue_id"] == issue_id and row["event_type"] == event_type
    ]


def test_missing_issue_clears_once_and_reappearance_reopens_same_row(isolated_db):
    disappearing = _record("Clarify source-controlled uncertainty")
    stable = _record("Still-current ordinary issue")
    created = _sync([disappearing, stable])
    original_rows = _rows(isolated_db)
    original = next(row for row in original_rows if row["issue_title"] == disappearing["issue_title"])
    stable_before = next(row for row in original_rows if row["issue_title"] == stable["issue_title"])

    cleared = _sync([stable])
    after_clear = next(row for row in _rows(isolated_db) if row["issue_id"] == original["issue_id"])
    assert (after_clear["status"], after_clear["disposition"], after_clear["resolved_capacity"]) == (
        "resolved", "source_cleared", "Source-Derived"
    )
    assert cleared["source_cleared"] == 1
    assert cleared["source_reappeared"] == 0
    clear_events = _events(isolated_db, original["issue_id"], "source_condition_cleared")
    assert len(clear_events) == 1
    assert "Source-derived reconciliation" in clear_events[0]["event_notes"]
    assert "absent" in clear_events[0]["event_notes"]

    repeated_clear = _sync([stable])
    assert repeated_clear["source_cleared"] == 0
    assert len(_events(isolated_db, original["issue_id"], "source_condition_cleared")) == 1

    reappeared = _sync([disappearing, stable])
    reopened = next(row for row in _rows(isolated_db) if row["issue_id"] == original["issue_id"])
    assert reopened["id"] == original["id"]
    assert (reopened["status"], reopened["disposition"]) == ("open", "source_reappeared")
    assert (reopened["resolved_by"], reopened["resolved_capacity"], reopened["resolved_at"]) == (
        None, None, None
    )
    assert reappeared["source_reappeared"] == 1
    assert len(_events(isolated_db, original["issue_id"], "source_condition_reappeared")) == 1

    repeated_reappearance = _sync([disappearing, stable])
    assert repeated_reappearance["source_reappeared"] == 0
    assert len(_events(isolated_db, original["issue_id"], "source_condition_reappeared")) == 1
    rows = _rows(isolated_db)
    assert len(rows) == len(original_rows)
    stable_after = next(row for row in rows if row["issue_id"] == stable_before["issue_id"])
    assert stable_after["status"] == "open"
    assert stable_after["disposition"] is None
    assert created["source_cleared"] == created["source_reappeared"] == 0


@pytest.mark.parametrize("disposition", ["resolved", "accepted_risk", "escalated"])
def test_human_dispositions_are_untouched_when_source_disappears(isolated_db, disposition):
    title = f"Human-governed {disposition} issue"
    _sync([_record(title)])
    with sqlite3.connect(isolated_db) as connection:
        connection.execute("""
            UPDATE professional_review_issues
            SET status = ?, disposition = ?, reviewer_notes = 'human notes',
                resolved_by = 'reviewer', resolved_capacity = 'Attorney',
                resolved_at = '2026-01-02T03:04:05Z'
            WHERE issue_title = ?
        """, (disposition, disposition, title))
    before = _rows(isolated_db)[0]

    result = _sync([])

    assert _rows(isolated_db)[0] == before
    assert result["source_cleared"] == 0
    assert _rows(isolated_db, "professional_review_issue_events") == []


def test_linked_issue_is_untouched_when_absent(isolated_db):
    _sync([_record("Task-governed issue")])
    with sqlite3.connect(isolated_db) as connection:
        connection.execute("""
            UPDATE professional_review_issues
            SET linked_record_type = 'intake_followup_task'
        """)
    before = _rows(isolated_db)[0]

    result = _sync([])

    assert _rows(isolated_db)[0] == before
    assert result["source_cleared"] == 0


def test_aggregate_identity_clears_and_reappears_without_duplication(isolated_db):
    aggregate_3 = _record(
        "3 open follow-up task(s) remain before final drafting.",
        issue_identity_key="open_followup_tasks_remaining",
    )
    _sync([aggregate_3])
    original = _rows(isolated_db)[0]

    cleared = _sync([])
    aggregate_2 = _record(
        "2 open follow-up task(s) remain before final drafting.",
        issue_identity_key="open_followup_tasks_remaining",
    )
    reopened = _sync([aggregate_2])
    repeated = _sync([aggregate_2])
    rows = _rows(isolated_db)

    assert cleared["source_cleared"] == 1
    assert reopened["source_reappeared"] == 1
    assert repeated["source_reappeared"] == 0
    assert len(rows) == 1
    assert rows[0]["issue_id"] == original["issue_id"]
    assert rows[0]["issue_title"].startswith("2 ")
    assert len(_events(isolated_db, original["issue_id"], "source_condition_cleared")) == 1
    assert len(_events(isolated_db, original["issue_id"], "source_condition_reappeared")) == 1
