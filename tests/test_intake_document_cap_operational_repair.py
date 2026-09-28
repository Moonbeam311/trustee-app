from pathlib import Path

import services.services_intake as intake_service
from services.services_intake_correction_versioning_adapter import (
    build_governed_proposed_tasks,
)


ROOT = Path(__file__).resolve().parents[1]


def _canonical_requests():
    return [
        "deed",
        "mortgage_statement",
        "property_tax_bill",
        "survey_if_available",
        "homeowners_insurance",
        "beneficiary_designation_form",
        "bank_statement",
        "retirement_statement",
        "brokerage_statement",
        "operating_agreement",
        "existing_will",
        "power_of_attorney",
        "trust_document",
        "estate_authority_document",
        "trust_document",
    ]


def _result():
    return {
        "intake_id": "INT-TEST",
        "summary": {
            "document_requests": _canonical_requests(),
            "risk_flags": ["tax_review_flag"],
            "next_sessions": ["document_collection_review"],
        },
        "scores": {"urgency_level": "Medium"},
    }


def test_display_cap_and_uncapped_operational_tasks_preserve_snapshot_semantics():
    result = _result()
    snapshot = intake_service.build_client_snapshot(result)
    operational = intake_service.build_operational_document_requests(
        result["summary"]["document_requests"]
    )

    assert len(snapshot["documents_to_gather"]) == 12
    assert operational[:12] == snapshot["documents_to_gather"]
    assert operational[12:] == ["Trust document", "Estate authority document"]
    assert operational.count("Trust document") == 1

    tasks = build_governed_proposed_tasks(
        snapshot, operational_documents=operational
    )
    titles = [task["title"] for task in tasks]
    assert "Gather document: Trust document" in titles
    assert "Gather document: Estate authority document" in titles
    assert [task["title"] for task in tasks if task["task_type"] != "document"] == [
        "Review flag: Tax records should be reviewed by a qualified professional",
        "Prepare next session: Gather missing documents before deeper review",
    ]
    assert snapshot["review_flags"] == [
        "Tax records should be reviewed by a qualified professional"
    ]
    assert snapshot["recommended_next_session"] == (
        "Gather missing documents before deeper review"
    )


def test_legacy_explicit_operational_documents_are_idempotent(monkeypatch):
    snapshot = intake_service.build_client_snapshot(_result())
    operational = intake_service.build_operational_document_requests(
        _canonical_requests()
    )
    stored = set()

    monkeypatch.setattr(
        intake_service, "ensure_intake_followup_task_tables", lambda: None
    )
    monkeypatch.setattr(
        intake_service,
        "task_exists",
        lambda intake_id, title, task_type=None, source=None: title in stored,
    )

    def create(**task):
        stored.add(task["title"])
        return task

    monkeypatch.setattr(intake_service, "create_intake_followup_task", create)

    first = intake_service.auto_generate_followup_tasks_from_snapshot(
        "INT-TEST", snapshot, operational_documents=operational
    )
    second = intake_service.auto_generate_followup_tasks_from_snapshot(
        "INT-TEST", snapshot, operational_documents=operational
    )
    assert "Gather document: Estate authority document" in {
        task["title"] for task in first
    }
    assert second == []


def test_packet_is_operationally_uncapped_but_nested_snapshot_stays_capped(
    monkeypatch,
):
    result = _result()
    snapshot = intake_service.build_client_snapshot(result)
    monkeypatch.setattr(
        intake_service,
        "get_saved_client_snapshot",
        lambda intake_id: (snapshot, result),
    )
    monkeypatch.setattr(intake_service, "list_intake_followup_tasks", lambda _: [])
    monkeypatch.setattr(intake_service, "list_intake_review_notes", lambda _: [])

    packet = intake_service.build_intake_followup_packet("INT-TEST")
    assert len(packet["snapshot"]["documents_to_gather"]) == 12
    assert packet["documents"][-2:] == [
        "Trust document",
        "Estate authority document",
    ]
    signals = intake_service._collect_recommendation_signal_text({
        **packet,
        "snapshot": {**packet["snapshot"], "documents_to_gather": []},
    })
    assert "Estate authority document" in signals


def test_routes_thread_operational_documents_without_schema_or_extra_lookup():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    service = (ROOT / "services/services_intake.py").read_text(encoding="utf-8")
    saved_start = app.index("def intake_saved_snapshot")
    saved_end = app.index("def intake_confirm_snapshot", saved_start)
    saved = app[saved_start:saved_end]
    enabled = saved.split("else:", 1)[0]

    assert "build_operational_document_requests(" in saved
    assert saved.count("get_saved_client_snapshot_for_firm(") == 1
    assert "operational_documents=operational_documents" in saved
    assert "auto_generate_followup_tasks_from_snapshot(" not in enabled
    assert "CREATE TABLE" not in service[service.index(
        "def build_operational_document_requests"
    ):service.index("def determine_primary_next_session")]
    assert "migrations" not in app[saved_start:saved_end].lower()
