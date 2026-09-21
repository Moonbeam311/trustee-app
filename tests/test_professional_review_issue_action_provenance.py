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
    def post(form):
        with app_module.app.test_request_context(
            f"/intake/professional-review/issues/{ISSUE_ID}", method="POST", data=form
        ):
            app_module.session["user_id"] = "USER-1"
            app_module.session["username"] = "reviewer"
            app_module.session["firm_id"] = FIRM_ID
            app_module.session["role"] = "Admin"
            response = app_module.professional_review_issue_detail(ISSUE_ID)
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
