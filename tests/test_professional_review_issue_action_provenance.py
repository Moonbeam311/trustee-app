import sqlite3
from pathlib import Path

import pytest

import app as app_module
import database.db as db
import services.services_intake as intake


ISSUE_ID = "PRI-ROUTE-1"
INTAKE_ID = "INT-PROVENANCE-1"
FIRM_ID = "FIRM-TEST"


@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    database_path = tmp_path / "professional-review.sqlite3"
    monkeypatch.setattr(db, "get_connection", lambda: sqlite3.connect(database_path))
    db.ensure_professional_review_issue_tables()
    return database_path


def _issue_row(**overrides):
    issue = {
        "issue_id": ISSUE_ID,
        "intake_id": INTAKE_ID,
        "firm_id": FIRM_ID,
        "issue_category": "Professional Review",
        "severity": "major",
        "status": "open",
        "issue_source": "test",
        "linked_record_type": None,
        "linked_record_id": None,
        "issue_description": "Review this item.",
        "recommended_action": "Review it.",
        "reviewer_notes": None,
    }
    issue.update(overrides)
    return issue


@pytest.fixture
def route_client(monkeypatch):
    calls = []
    monkeypatch.setattr(db, "get_professional_review_issue", lambda *args, **kwargs: _issue_row())
    monkeypatch.setattr(
        db,
        "update_professional_review_issue",
        lambda **kwargs: calls.append(kwargs) or "PRIE-TEST",
    )
    monkeypatch.setattr(app_module, "log_change", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module, "get_export_policy", lambda: {"allow_exports": True, "read_only_mode": False})
    app_module.app.config.update(TESTING=True, SECRET_KEY="test-secret")
    def post(form, issue_id=ISSUE_ID):
        with app_module.app.test_request_context(
            f"/intake/professional-review/issues/{issue_id}", method="POST", data=form
        ):
            app_module.session["user_id"] = "USER-1"
            app_module.session["username"] = "reviewer"
            app_module.session["firm_id"] = FIRM_ID
            app_module.session["role"] = "Admin"
            response = app_module.professional_review_issue_detail(issue_id)
            flashes = list(app_module.session.get("_flashes", []))
            return response, flashes

    return post, calls


def _seed(packet, *, actor="tester"):
    return db.seed_professional_review_issues_from_packet(
        INTAKE_ID, FIRM_ID, "estate_plan", packet, actor=actor
    )


def _fetch_all(database_path, table):
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    conn.close()
    return rows


def test_detail_template_requires_neutral_choice_before_nondefault_resolve():
    template = Path("templates/intake/professional_review_issue_detail.html").read_text(encoding="utf-8")
    placeholder = '<option value="" selected disabled>Select disposition</option>'
    resolve = '<option value="resolved">Resolve</option>'
    assert placeholder in template
    assert template.index(placeholder) < template.index(resolve)
    assert '<select name="disposition" required>' in template
    assert 'value="resolved" selected' not in template


@pytest.mark.parametrize("form", [{}, {"disposition": "invented"}])
def test_route_rejects_missing_or_invalid_disposition_without_update(route_client, form):
    post, calls = route_client
    response, flashes = post(form)
    assert response.status_code == 302
    assert any("Select a valid disposition" in message for _, message in flashes)
    assert calls == []


def test_route_accepts_resolved_with_notes(route_client):
    post, calls = route_client
    response, _ = post({"disposition": "resolved", "reviewer_notes": "Substantive review completed."})
    assert response.status_code == 302
    assert calls[0]["disposition"] == "resolved"
    assert calls[0]["reviewer_notes"] == "Substantive review completed."


def test_route_rejects_resolved_without_notes(route_client):
    post, calls = route_client
    _, flashes = post({"disposition": "resolved", "reviewer_notes": "   "})
    assert any("Reviewer notes are required" in message for _, message in flashes)
    assert calls == []


def test_database_owner_rejects_unsupported_disposition_before_any_database_access(monkeypatch):
    monkeypatch.setattr(db, "get_connection", lambda: pytest.fail("database must not be accessed"))
    with pytest.raises(ValueError, match="Unsupported"):
        db.update_professional_review_issue(ISSUE_ID, FIRM_ID, "unknown", "note", "actor", "capacity")


def test_legacy_string_and_aggregate_seed_without_fabricated_provenance(isolated_db):
    result = _seed({"open_issues": ["3 open follow-up task(s) remain before final drafting."]})
    rows = _fetch_all(isolated_db, "professional_review_issues")
    assert result["created"] == 1
    assert result["skipped"] == 0
    assert result["provenance_enriched"] == 0
    assert result["semantic_updated"] == 0
    assert result["source_cleared"] == 0
    assert result["source_reappeared"] == 0
    assert result["source_issue_count"] == 1
    assert result["normalized_issue_count"] == 1
    assert rows[0]["issue_title"] == "3 open follow-up task(s) remain before final drafting."
    assert rows[0]["linked_record_type"] is None
    assert rows[0]["linked_record_id"] is None


@pytest.mark.parametrize(
    "record, expected",
    [
        ({"linked_record_type": "followup_task", "linked_record_id": "TASK-42"}, ("followup_task", "TASK-42")),
        ({"linked_record_type": "followup_task", "linked_record_id": ""}, (None, None)),
    ],
)
def test_structured_seed_stores_only_complete_provenance_pairs(isolated_db, record, expected):
    record.update({"issue_title": "Canonical source issue", "issue_description": "Canonical source issue"})
    result = _seed({"open_issue_records": [record], "open_issues": ["ignored legacy fallback"]})
    row = _fetch_all(isolated_db, "professional_review_issues")[0]
    assert (row["linked_record_type"], row["linked_record_id"]) == expected
    assert result["created"] == 1
    assert isinstance(result["skipped"], int)
    assert isinstance(result["provenance_enriched"], int)


def test_resync_enriches_only_blank_provenance_without_state_or_event_changes(isolated_db):
    _seed({"open_issues": ["Stable issue"]})
    conn = sqlite3.connect(isolated_db)
    conn.execute(
        "UPDATE professional_review_issues SET status='escalated', disposition='escalated', reviewer_notes='Keep me'"
    )
    conn.commit()
    conn.close()

    result = _seed({"open_issue_records": [{
        "issue_title": "Stable issue",
        "linked_record_type": "canonical_case",
        "linked_record_id": "CASE-7",
    }]})
    row = _fetch_all(isolated_db, "professional_review_issues")[0]
    events = _fetch_all(isolated_db, "professional_review_issue_events")
    assert result["created"] == 0
    assert result["skipped"] == 1
    assert result["provenance_enriched"] == 1
    assert (row["linked_record_type"], row["linked_record_id"]) == ("canonical_case", "CASE-7")
    assert (row["status"], row["disposition"], row["reviewer_notes"]) == ("escalated", "escalated", "Keep me")
    assert events == []


def test_resync_does_not_overwrite_conflicting_existing_provenance(isolated_db):
    packet = {"open_issue_records": [{
        "issue_title": "Stable issue",
        "linked_record_type": "canonical_case",
        "linked_record_id": "CASE-7",
    }]}
    _seed(packet)
    packet["open_issue_records"][0].update(linked_record_type="other_type", linked_record_id="OTHER-9")
    result = _seed(packet)
    row = _fetch_all(isolated_db, "professional_review_issues")[0]
    assert result["provenance_enriched"] == 0
    assert (row["linked_record_type"], row["linked_record_id"]) == ("canonical_case", "CASE-7")


def test_draft_packet_preserves_legacy_list_and_exposes_truthful_sidecar(monkeypatch):
    bridge = {
        "workflow_key": "estate_plan",
        "answers": [{"answer": "not sure"}],
        "launch": {
            "packet": {},
            "open_tasks": [{"task_id": "TASK-1"}],
            "review_flags": ["Tax review"],
            "documents": ["Trust instrument"],
        },
    }
    monkeypatch.setattr(intake, "build_workflow_bridge_summary", lambda *_: bridge)
    packet = intake.build_workflow_draft_packet(INTAKE_ID, "estate_plan")
    assert packet["open_issues"]
    assert all(isinstance(issue, str) for issue in packet["open_issues"])
    assert [record["issue_description"] for record in packet["open_issue_records"]] == packet["open_issues"]
    assert all(record["linked_record_type"] is None for record in packet["open_issue_records"])
    assert all(record["linked_record_id"] is None for record in packet["open_issue_records"])

# PRI-APPEND-ONLY-NOTE-1A
def _insert_append_only_note_test_issue(
    db_module,
    issue_id,
    firm_id="FIRM-001",
):
    db_module.ensure_professional_review_issue_tables()

    conn = db_module.get_connection()

    conn.execute(
        """
        INSERT INTO professional_review_issues (
            issue_id,
            intake_id,
            firm_id,
            workflow_key,
            issue_source,
            issue_category,
            severity,
            issue_title,
            issue_description,
            linked_record_type,
            linked_record_id,
            recommended_action,
            status,
            disposition,
            reviewer_notes,
            resolved_by,
            resolved_capacity,
            resolved_at,
            created_by,
            updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,
        (
            issue_id,
            "INTAKE-NOTE-TEST",
            firm_id,
            "professional_review_checklist",
            "draft_packet_open_issue",
            "Professional Review",
            "major",
            "Authority documents should be verified",
            "Authority documents should be verified",
            "intake_followup_task",
            "36",
            "Review this issue.",
            "escalated",
            "escalated",
            "Original governed reviewer notes.",
            "personal-admin",
            "Admin Reviewer",
            "2026-10-04T21:48:01.244231+00:00",
            "personal-admin",
            "2026-10-04T21:48:01.244231+00:00",
        ),
    )

    conn.commit()
    conn.close()


def _append_only_note_issue_state(
    db_module,
    issue_id,
    firm_id="FIRM-001",
):
    conn = db_module.get_connection()

    row = conn.execute(
        """
        SELECT
            status,
            disposition,
            reviewer_notes,
            resolved_by,
            resolved_capacity,
            resolved_at,
            updated_at
        FROM professional_review_issues
        WHERE issue_id = ?
          AND firm_id = ?
        """,
        (issue_id, firm_id),
    ).fetchone()

    conn.close()

    return tuple(row)


def test_issue_note_helper_is_append_only_and_state_neutral(
    isolated_db,
):
    from database import db as db_module

    issue_id = "PRI-NOTE-HELPER-TEST"
    firm_id = "FIRM-001"

    note_text = (
        "Administrative clarification.\n"
        "Second line preserved exactly."
    )

    _insert_append_only_note_test_issue(
        db_module,
        issue_id,
        firm_id,
    )

    before = _append_only_note_issue_state(
        db_module,
        issue_id,
        firm_id,
    )

    event_id = db_module.record_professional_review_issue_note(
        issue_id=issue_id,
        firm_id=firm_id,
        note_text=note_text,
        actor="personal-admin",
        actor_capacity="Admin Reviewer",
    )

    after = _append_only_note_issue_state(
        db_module,
        issue_id,
        firm_id,
    )

    assert before == after
    assert event_id
    assert event_id.startswith("PRIE-")

    conn = db_module.get_connection()

    event = conn.execute(
        """
        SELECT
            event_type,
            event_notes,
            actor,
            actor_capacity
        FROM professional_review_issue_events
        WHERE event_id = ?
        """,
        (event_id,),
    ).fetchone()

    conn.close()

    assert tuple(event) == (
        "issue_note_added",
        note_text,
        "personal-admin",
        "Admin Reviewer",
    )

    notes = db_module.get_professional_review_issue_notes(
        issue_id,
        firm_id,
    )

    assert len(notes) == 1
    assert notes[0]["event_id"] == event_id
    assert notes[0]["event_notes"] == note_text


def test_issue_note_helper_rejects_blank_without_event(
    isolated_db,
):
    import pytest
    from database import db as db_module

    issue_id = "PRI-NOTE-BLANK-TEST"
    firm_id = "FIRM-001"

    _insert_append_only_note_test_issue(
        db_module,
        issue_id,
        firm_id,
    )

    with pytest.raises(ValueError):
        db_module.record_professional_review_issue_note(
            issue_id=issue_id,
            firm_id=firm_id,
            note_text="   ",
            actor="personal-admin",
            actor_capacity="Admin Reviewer",
        )

    conn = db_module.get_connection()

    count = conn.execute(
        """
        SELECT COUNT(*)
        FROM professional_review_issue_events
        WHERE issue_id = ?
          AND firm_id = ?
        """,
        (issue_id, firm_id),
    ).fetchone()[0]

    conn.close()

    assert count == 0


def test_route_add_issue_note_does_not_reassert_disposition(
    route_client,
    isolated_db,
):
    from database import db as db_module

    issue_id = "PRI-NOTE-ROUTE-TEST"
    firm_id = FIRM_ID
    note_text = "Route-level append-only clarification."

    _insert_append_only_note_test_issue(
        db_module,
        issue_id,
        firm_id,
    )

    before = _append_only_note_issue_state(
        db_module,
        issue_id,
        firm_id,
    )

    post, calls = route_client

    response, _ = post(
        {
            "action": "add_issue_note",
            "issue_note": note_text,
            "note_actor_capacity": "Admin Reviewer",
        },
        issue_id=issue_id,
    )

    assert response.status_code in (302, 303)
    assert calls == []

    after = _append_only_note_issue_state(
        db_module,
        issue_id,
        firm_id,
    )

    assert before == after

    conn = db_module.get_connection()

    events = conn.execute(
        """
        SELECT event_type, event_notes
        FROM professional_review_issue_events
        WHERE issue_id = ?
          AND firm_id = ?
        ORDER BY id
        """,
        (issue_id, firm_id),
    ).fetchall()

    conn.close()

    assert [tuple(row) for row in events] == [
        ("issue_note_added", note_text),
    ]


def test_detail_template_has_separate_blank_append_only_note_form():
    from pathlib import Path

    text = Path(
        "templates/intake/"
        "professional_review_issue_detail.html"
    ).read_text(
        encoding="utf-8"
    )

    start = text.index(
        "<h2>Issue Clarification / Note</h2>"
    )

    end = text.index(
        "<h2>Reviewer Action</h2>"
    )

    block = text[start:end]

    assert (
        'name="action"'
        in block
    )

    assert (
        'value="add_issue_note"'
        in block
    )

    assert (
        'name="issue_note"'
        in block
    )

    assert (
        'name="note_actor_capacity"'
        in block
    )

    assert (
        'issue["reviewer_notes"]'
        not in block
    )
