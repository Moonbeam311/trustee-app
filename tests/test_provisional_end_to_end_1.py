import json
import sqlite3

import pytest

import database.db as db
import services.services_intake as intake


ISSUE_ID = "PRI-5C42BFAE8B"
INTAKE_ID = "INT-PROVISIONAL-1"
FIRM_ID = "FIRM-TEST"


@pytest.fixture
def isolated_review(monkeypatch, tmp_path):
    path = tmp_path / "provisional.sqlite3"
    monkeypatch.setattr(db, "get_connection", lambda: sqlite3.connect(path))
    db.ensure_professional_review_issue_tables()
    with sqlite3.connect(path) as connection:
        connection.execute("""
            CREATE TABLE intake_followup_tasks (
                id INTEGER PRIMARY KEY, intake_id TEXT, firm_id TEXT,
                status TEXT, title TEXT
            )
        """)
        connection.execute(
            "INSERT INTO intake_followup_tasks VALUES (36, ?, ?, 'open', ?)",
            (INTAKE_ID, FIRM_ID, "Verify governing instrument / trustee authority"),
        )
        connection.execute("""
            INSERT INTO professional_review_issues (
                issue_id, intake_id, firm_id, workflow_key, issue_source,
                issue_category, severity, issue_title, issue_description,
                linked_record_type, linked_record_id, status
            ) VALUES (?, ?, ?, 'professional_review_checklist', 'draft_packet_open_issue',
                      'Professional Review', 'major', ?, ?,
                      'intake_followup_task', '36', 'open')
        """, (
            ISSUE_ID, INTAKE_ID, FIRM_ID,
            "Governing-instrument / trustee-authority verification",
            "Authority verification remains required.",
        ))
    return path


def _row(path, sql, params=()):
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(sql, params).fetchone()


def test_pending_review_and_build_assumption_coexist_without_legal_effect(isolated_review):
    event_id = db.record_professional_review_build_assumption(
        ISSUE_ID, FIRM_ID, "Exercise the complete non-final product build.",
        "build-operator", "Developer",
    )
    state = db.get_professional_review_issue_build_assumption(ISSUE_ID, FIRM_ID)
    readiness = intake.evaluate_nonfinal_build_readiness(INTAKE_ID, FIRM_ID)
    issue = _row(isolated_review, "SELECT * FROM professional_review_issues")
    task = _row(isolated_review, "SELECT * FROM intake_followup_tasks WHERE id=36")

    assert event_id.startswith("PRIE-")
    assert issue["status"] == "open" and issue["disposition"] is None
    assert issue["resolved_at"] is None and task["status"] == "open"
    assert state["professional_review_status"] == "PENDING_PROFESSIONAL_REVIEW"
    assert state["build_assumption_status"] == "ASSUMED_FOR_BUILD"
    assert state["latest_event"]["professional_approval"] is False
    assert state["latest_event"]["legal_verification"] is False
    assert state["latest_event"]["linked_record_id"] == "36"
    assert readiness["build_test_progression_allowed"] is True
    assert readiness["gate_scope"] == "NON_FINAL_BUILD_AND_TEST_ONLY"
    assert readiness["professional_legal_verification"] is False
    assert readiness["final_professional_readiness"] is False


def test_history_is_append_only_and_professional_resolution_reconciles(isolated_review):
    first = db.record_professional_review_build_assumption(
        ISSUE_ID, FIRM_ID, "Initial build hypothesis.", "operator-a", "Developer"
    )
    second = db.record_professional_review_build_assumption(
        ISSUE_ID, FIRM_ID, "Corrected build hypothesis.", "operator-b", "Developer"
    )
    before = db.get_professional_review_issue_build_assumption(ISSUE_ID, FIRM_ID)
    assert len(before["history"]) == 2
    assert before["history"][1]["supersedes_event_id"] == first
    assert before["history"][1]["event_id"] == second

    db.update_professional_review_issue(
        ISSUE_ID, FIRM_ID, "resolved", "Authorized review completed.",
        "professional", "Counsel",
    )
    after = db.get_professional_review_issue_build_assumption(ISSUE_ID, FIRM_ID)
    assert len(after["history"]) == 3 and after["active"] is False
    assert after["latest_event"]["assumption_status"] == "RECONCILED"
    assert after["latest_event"]["supersedes_event_id"] == second


def test_without_assumption_existing_blocking_behavior_is_unchanged(isolated_review):
    state = db.get_professional_review_issue_build_assumption(ISSUE_ID, FIRM_ID)
    readiness = intake.evaluate_nonfinal_build_readiness(INTAKE_ID, FIRM_ID)
    assert state["active"] is False and state["history"] == []
    assert readiness["build_test_progression_allowed"] is False
    assert readiness["unassumed_issue_ids"] == [ISSUE_ID]


def test_event_payload_has_identity_actor_timestamp_and_version(isolated_review):
    db.record_professional_review_build_assumption(
        ISSUE_ID, FIRM_ID, "Build/test purpose.", "operator", "Developer"
    )
    event = _row(
        isolated_review,
        "SELECT * FROM professional_review_issue_events WHERE issue_id = ?",
        (ISSUE_ID,),
    )
    payload = json.loads(event["event_notes"])
    assert event["event_id"] and event["issue_id"] == ISSUE_ID
    assert event["actor"] == "operator" and event["created_at"]
    assert payload["assumption_status"] == "ASSUMED_FOR_BUILD"
    assert payload["purpose"] == "non_final_product_build_and_test"
