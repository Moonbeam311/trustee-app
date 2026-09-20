import json
import sqlite3

import pytest

import database.db as db
import services.services_intake as intake


INTAKE_ID = "INT-SOURCE-1"
FIRM_ID = "FIRM-SOURCE-1"
ISSUE_ID = "PRI-SOURCE-1"


@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    path = tmp_path / "source-transition.sqlite3"
    monkeypatch.setattr(db, "get_connection", lambda: sqlite3.connect(path))
    db.ensure_professional_review_issue_tables()
    with sqlite3.connect(path) as connection:
        connection.execute("""
            CREATE TABLE intake_followup_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intake_id TEXT NOT NULL,
                firm_id TEXT,
                status TEXT,
                title TEXT,
                updated_at TEXT,
                completed_at TEXT,
                completed_by TEXT
            )
        """)
    return path


def _insert_source(path, *, status="completed", issue_disposition=None,
                   issue_intake=INTAKE_ID, issue_firm=FIRM_ID,
                   linked_type="intake_followup_task", linked_id="1"):
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO intake_followup_tasks "
            "(id, intake_id, firm_id, status, title) VALUES (1, ?, ?, ?, ?)",
            (INTAKE_ID, FIRM_ID, status, "Review flag: Exact flag"),
        )
        connection.execute("""
            INSERT INTO professional_review_issues (
                issue_id, intake_id, firm_id, issue_title, status, disposition,
                reviewer_notes, linked_record_type, linked_record_id
            ) VALUES (?, ?, ?, ?, 'open', ?, 'preserve me', ?, ?)
        """, (
            ISSUE_ID, issue_intake, issue_firm, "Review flag: Exact flag",
            issue_disposition, linked_type, linked_id,
        ))


def _rows(path, table):
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()


def _review_record(bridge):
    return next(
        record for record in intake.build_draft_packet_open_issue_records("estate_plan", bridge)
        if record["issue_title"] == "Review flag: Exact flag"
    )


@pytest.mark.parametrize("collection,status", [("open_tasks", "open"), ("completed_tasks", "completed")])
def test_review_flag_links_exact_unique_canonical_task(collection, status):
    bridge = {"launch": {
        "review_flags": [{"label": "Exact flag"}],
        collection: [{"id": 42, "title": "Review flag: Exact flag", "status": status}],
    }}
    record = _review_record(bridge)
    assert (record["linked_record_type"], record["linked_record_id"]) == (
        "intake_followup_task", "42"
    )


def test_ambiguous_review_flag_and_other_issue_classes_stay_unlinked():
    bridge = {
        "question_summaries": [{"answers": [{"answer_label": "not sure"}]}],
        "launch": {
            "review_flags": [{"label": "Exact flag"}],
            "open_tasks": [
                {"id": 1, "title": "Review flag: Exact flag"},
                {"id": 2, "title": "Review flag: Exact flag"},
            ],
            "documents": [{"id": 9}],
        },
    }
    records = intake.build_draft_packet_open_issue_records("estate_plan", bridge)
    assert any("open follow-up" in record["issue_title"] for record in records)
    assert any("Document checklist" in record["issue_title"] for record in records)
    assert any("uncertainty" in record["issue_title"] for record in records)
    assert all(record["linked_record_type"] is None for record in records)
    assert all(record["linked_record_id"] is None for record in records)


def test_blank_seed_provenance_is_enriched_from_structured_record(isolated_db):
    packet = {"open_issues": ["Review flag: Exact flag"]}
    db.seed_professional_review_issues_from_packet(INTAKE_ID, FIRM_ID, "estate_plan", packet)
    result = db.seed_professional_review_issues_from_packet(INTAKE_ID, FIRM_ID, "estate_plan", {
        "open_issue_records": [{
            "issue_title": "Review flag: Exact flag",
            "linked_record_type": "intake_followup_task",
            "linked_record_id": "1",
        }]
    })
    row = _rows(isolated_db, "professional_review_issues")[0]
    assert result["provenance_enriched"] == 1
    assert (row["linked_record_type"], row["linked_record_id"]) == (
        "intake_followup_task", "1"
    )


def test_completed_source_transitions_once_with_provenance(isolated_db):
    _insert_source(isolated_db)
    first = db.reconcile_professional_review_issue_source_state_for_task(1, actor="reviewer")
    second = db.reconcile_professional_review_issue_source_state_for_task(1, actor="reviewer")
    issue = _rows(isolated_db, "professional_review_issues")[0]
    events = _rows(isolated_db, "professional_review_issue_events")
    assert first["transitioned"] is True
    assert first["source_status"] == "completed"
    assert first["source_state"] == "source_completed"
    assert second["transitioned"] is False
    assert (issue["status"], issue["disposition"]) == ("resolved", "source_completed")
    assert issue["resolved_by"] == "reviewer"
    assert issue["resolved_capacity"] == "Source-Derived"
    assert issue["resolved_at"]
    assert issue["reviewer_notes"] == "preserve me"
    assert len(events) == 1 and events[0]["event_type"] == "source_task_completed"
    assert events[0]["actor_capacity"] == "Source-Derived"
    assert json.loads(events[0]["event_notes"]) == {
        "source_record_id": "1",
        "source_record_type": "intake_followup_task",
        "source_status": "completed",
    }


def test_source_completed_issue_reopens_once_when_task_reactivated(isolated_db):
    _insert_source(isolated_db)
    db.reconcile_professional_review_issue_source_state_for_task(1)
    with sqlite3.connect(isolated_db) as connection:
        connection.execute("UPDATE intake_followup_tasks SET status='pending_staff' WHERE id=1")
    first = db.reconcile_professional_review_issue_source_state_for_task(1)
    second = db.reconcile_professional_review_issue_source_state_for_task(1)
    issue = _rows(isolated_db, "professional_review_issues")[0]
    events = _rows(isolated_db, "professional_review_issue_events")
    assert first["transitioned"] is True and second["transitioned"] is False
    assert (issue["status"], issue["disposition"]) == ("open", "source_reopened")
    assert issue["resolved_by"] is None
    assert issue["resolved_capacity"] is None
    assert issue["resolved_at"] is None
    assert issue["reviewer_notes"] == "preserve me"
    assert [event["event_type"] for event in events] == [
        "source_task_completed", "source_task_reactivated"
    ]
    assert json.loads(events[1]["event_notes"])["source_status"] == "pending_staff"


@pytest.mark.parametrize("disposition", ["resolved", "accepted_risk", "escalated", "reopened"])
def test_human_dispositions_are_never_overwritten(isolated_db, disposition):
    _insert_source(isolated_db, issue_disposition=disposition)
    result = db.reconcile_professional_review_issue_source_state_for_task(1)
    issue = _rows(isolated_db, "professional_review_issues")[0]
    assert result["transitioned"] is False
    assert issue["disposition"] == disposition
    assert issue["reviewer_notes"] == "preserve me"
    assert _rows(isolated_db, "professional_review_issue_events") == []


def test_superseded_source_fails_closed(isolated_db):
    _insert_source(isolated_db)
    with sqlite3.connect(isolated_db) as connection:
        connection.execute("""
            CREATE TABLE intake_followup_reconciliations (
                superseded_followup_task_id INTEGER, intake_id TEXT, firm_id TEXT
            )
        """)
        connection.execute(
            "INSERT INTO intake_followup_reconciliations VALUES (1, ?, ?)",
            (INTAKE_ID, FIRM_ID),
        )
    result = db.reconcile_professional_review_issue_source_state_for_task(1)
    assert result["reason"] == "superseded_source_task"
    assert _rows(isolated_db, "professional_review_issue_events") == []


@pytest.mark.parametrize(
    "kwargs,task_id",
    [
        ({"issue_intake": "OTHER"}, 1),
        ({"issue_firm": "OTHER"}, 1),
        ({"linked_type": "wrong_type"}, 1),
        ({"linked_id": "not-an-id"}, 1),
        ({}, 999),
    ],
)
def test_wrong_scope_malformed_or_missing_source_fails_closed(isolated_db, kwargs, task_id):
    _insert_source(isolated_db, **kwargs)
    result = db.reconcile_professional_review_issue_source_state_for_task(task_id)
    assert result["transitioned"] is False
    assert _rows(isolated_db, "professional_review_issue_events") == []


def test_task_update_reconciles_after_update_on_same_connection(monkeypatch, isolated_db):
    _insert_source(isolated_db, status="open")
    connection = sqlite3.connect(isolated_db)
    calls = []
    monkeypatch.setattr(intake, "ensure_intake_followup_task_tables", lambda: None)
    monkeypatch.setattr(intake, "get_connection", lambda: connection)

    def reconcile(task_id, actor=None, connection=None):
        status = connection.execute(
            "SELECT status FROM intake_followup_tasks WHERE id=?", (task_id,)
        ).fetchone()[0]
        calls.append((task_id, actor, connection, status))
        return {"transitioned": False, "source_state": status}

    monkeypatch.setattr(intake, "reconcile_professional_review_issue_source_state_for_task", reconcile)
    intake.update_intake_followup_task_status(1, "completed", updated_by="operator")
    assert calls == [(1, "operator", connection, "completed")]
    with sqlite3.connect(isolated_db) as check:
        assert check.execute("SELECT status FROM intake_followup_tasks WHERE id=1").fetchone()[0] == "completed"


def test_final_draft_actions_expose_distinct_persisted_ids(monkeypatch, isolated_db):
    monkeypatch.setattr(intake, "ensure_final_draft_resolution_tables", lambda: None)
    monkeypatch.setattr(intake, "get_connection", lambda: sqlite3.connect(isolated_db))
    monkeypatch.setattr(intake, "get_current_firm_id", lambda: FIRM_ID)
    monkeypatch.setattr(intake, "upsert_final_draft_prep_gate", lambda **kwargs: None)
    with sqlite3.connect(isolated_db) as connection:
        connection.execute("""
            CREATE TABLE intake_final_draft_gate_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT,
                workflow_key TEXT, document_key TEXT, firm_id TEXT,
                action_key TEXT, action_label TEXT, note TEXT,
                created_at TEXT, created_by TEXT
            )
        """)
    first = intake.record_final_draft_resolution_actions(
        INTAKE_ID, "estate_plan", "draft", ["required_documents_acknowledged"]
    )[0]
    second = intake.record_final_draft_resolution_actions(
        INTAKE_ID, "estate_plan", "draft", ["required_documents_acknowledged"]
    )[0]
    listed = intake.list_final_draft_resolution_actions(INTAKE_ID, "estate_plan", "draft")
    assert first["id"] != second["id"]
    assert [row["id"] for row in listed] == [second["id"], first["id"]]


def test_document_issue_is_not_linked_without_persisted_acknowledgment():
    records = intake.build_draft_packet_open_issue_records("estate_plan", {
        "launch": {"documents": [{"name": "Trust"}]}
    })
    document_issue = next(row for row in records if "Document checklist" in row["issue_title"])
    assert document_issue["linked_record_type"] is None
    assert document_issue["linked_record_id"] is None


@pytest.mark.parametrize("disposition", ["source_completed", "source_reopened"])
def test_source_dispositions_are_not_manual_inputs(monkeypatch, disposition):
    monkeypatch.setattr(db, "get_connection", lambda: pytest.fail("must reject before DB access"))
    with pytest.raises(ValueError, match="Unsupported"):
        db.update_professional_review_issue(
            ISSUE_ID, FIRM_ID, disposition, "notes", "actor", "capacity"
        )
