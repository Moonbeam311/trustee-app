import importlib
import sqlite3
import sys
import time

from services import services_handoff_read_aggregate as aggregate_contract


def _acceptance(status="ACCEPTED_RECORDED"):
    return {
        "acceptance_id": "ACC-A", "firm_id": "FIRM-A", "trust_id": "TR-A",
        "fiduciary_id": "FID-A", "appointment_reference": "APT-A",
        "role_capacity": "Successor Trustee",
        "appointment_source_reference": "Instrument:TR-A",
        "acceptance_status": status, "accepted_at": "2026-08-21T10:00:00Z",
        "acceptance_method": "EXECUTED_DOCUMENT",
        "evidence": {"document_id": "DOC-ACC", "external_reference": None},
        "provenance": {"source": "OPERATOR_RECORDED", "recorded_by": "maker",
                       "recorded_at": "2026-08-21T09:00:00Z",
                       "supersedes_acceptance_id": None, "governed_explanation": None},
        "institutional_effects": {}, "context_fingerprint": "not-for-display",
    }


def _evidence():
    return {"evidence_items": [{
        "identifier": "DOC-ACC", "source_type": "DOCUMENT_REFERENCE",
        "source_owner": "DOCUMENT", "relationship": "SUPPORTS_ACCEPTANCE_REVIEW",
        "execution_finalization_status": "NOT DOCUMENTED",
        "acceptance_review_status": "RELIED_ON_IN_FINALIZED_TRANSITION",
        "maker_actor_ids": ["maker"], "reviewer_actor_ids": ["reviewer"],
        "event_references": ["EV-1", "EV-2"], "document": {"document_id": "DOC-ACC"},
    }]}


def test_aggregate_acceptance_composition_uses_canonical_contracts(monkeypatch):
    monkeypatch.setattr(aggregate_contract.acceptance_contract,
                        "list_successor_acceptances_for_trust",
                        lambda trust_id, authorization_check: [_acceptance()] if authorization_check("ACC-A", trust_id) else [])
    monkeypatch.setattr(aggregate_contract.acceptance_evidence_contract,
                        "describe_acceptance_evidence", lambda *_args, **_kwargs: _evidence())
    section, provenance = aggregate_contract._acceptance_section(
        {"trust_id": "TR-A", "successor_trustee_name": "Successor Trustee"},
        acceptance_check=lambda acceptance_id, trust_id: acceptance_id == "ACC-A" and trust_id == "TR-A",
        document_check=lambda trust_id: trust_id == "TR-A")
    assert section["display_state"] == "ACCEPTANCE RECORDED"
    assert section["records"][0]["evidence_visibility"]["evidence_items"][0]["reviewer_actor_ids"] == ["reviewer"]
    assert section["write_controls_available"] is False
    assert provenance == [{"source_domain": "SuccessorAcceptance", "source_record_id": "ACC-A"}]


def test_aggregate_acceptance_missing_pending_and_cross_scope_states(monkeypatch):
    monkeypatch.setattr(aggregate_contract.acceptance_contract,
                        "list_successor_acceptances_for_trust",
                        lambda *_args, **_kwargs: [])
    missing, _ = aggregate_contract._acceptance_section(
        {"trust_id": "TR-A", "successor_trustee_name": "Successor Trustee"},
        acceptance_check=lambda *_: True, document_check=lambda *_: True)
    assert missing["display_state"] == "DESIGNATED / ACCEPTANCE NOT RECORDED"
    monkeypatch.setattr(aggregate_contract.acceptance_contract,
                        "list_successor_acceptances_for_trust",
                        lambda trust_id, authorization_check: [_acceptance("PENDING_EVIDENCE")] if authorization_check("ACC-A", trust_id) else [])
    monkeypatch.setattr(aggregate_contract.acceptance_evidence_contract,
                        "describe_acceptance_evidence", lambda *_args, **_kwargs: {"evidence_items": []})
    pending, _ = aggregate_contract._acceptance_section(
        {"trust_id": "TR-A", "successor_trustee_name": "Successor Trustee"},
        acceptance_check=lambda _acceptance_id, trust_id: trust_id == "TR-A",
        document_check=lambda *_: True)
    assert pending["display_state"] == "ACCEPTANCE PENDING REVIEW"
    denied, _ = aggregate_contract._acceptance_section(
        {"trust_id": "TR-X", "successor_trustee_name": "Other"},
        acceptance_check=lambda *_: False, document_check=lambda *_: False)
    assert denied["records"] == []


def _load_isolated_app(monkeypatch, tmp_path):
    db_path = tmp_path / "handoff-acceptance-ui.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path / "uploads"))
    monkeypatch.setenv("EXPORT_ROOT", str(tmp_path / "exports"))
    for name in ("app", "routes_tpd1c", "database.db"):
        sys.modules.pop(name, None)
    app_module = importlib.import_module("app")
    routes = importlib.import_module("routes_tpd1c")
    app_module.app.config.update(TESTING=True, SECRET_KEY="acc-1d-isolated")
    return app_module.app, routes, db_path


def _session(client):
    with client.session_transaction() as session:
        session.update(username="operator", user_id="USR-1", firm_id="FIRM-A",
                       role="Admin", last_activity=time.time())


def _handoff(status="ACCEPTED_RECORDED", linked=True):
    record = _acceptance(status)
    record["evidence_visibility"] = _evidence()
    return {
        "root_trust_id": "TR-A",
        "identity": {"trust": {"trust_name": "Alpha Trust", "status": "Active"},
                     "current_trustee": "Current", "successor_trustee": "Successor"},
        "fiduciary_authority": {"state": "AVAILABLE", "records": []},
        "successor_acceptance": {"state": "AVAILABLE", "display_state": (
            "ACCEPTANCE RECORDED" if status == "ACCEPTED_RECORDED" else "ACCEPTANCE PENDING REVIEW"),
            "records": [record], "legacy_documents": [], "write_controls_available": False},
        "continuity": {"state": "AVAILABLE" if linked else "UNLINKED", "profiles": []},
        "accounts_assets": {"accounts": [], "assets": []},
        "governance": {"state": "MISSING", "links": []},
        "execution": {"state": "NOT APPLICABLE", "orchestration": {"recommended_next_action": "NOT DOCUMENTED", "execution": None, "transfer": None}},
        "documents": {"state": "MISSING", "references": []},
        "archive": {"state": "MISSING", "descriptors": []},
        "readiness": {"status": "needs_attention", "gap_count": 0, "gaps": [],
                      "disclaimer": "Readiness is not legal validity."},
        "provenance": [{"source_domain": "SuccessorAcceptance", "source_record_id": "ACC-A"}],
    }


def _snapshot(path):
    connection = sqlite3.connect(path)
    try:
        tables = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return {table: connection.execute(f'SELECT * FROM "{table}" ORDER BY 1').fetchall() for table in tables}
    finally:
        connection.close()


def test_workspace_renders_acceptance_evidence_provenance_and_no_controls(monkeypatch, tmp_path):
    app, routes, db_path = _load_isolated_app(monkeypatch, tmp_path)
    client = app.test_client()
    _session(client)
    monkeypatch.setattr(routes, "user_has_effective_permission", lambda *_: True)
    monkeypatch.setattr(routes, "build_trust_successor_handoff_context", lambda *_args, **_kwargs: _handoff())
    before = _snapshot(db_path)
    response = client.get("/trust/TR-A/successor-handoff")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    for text in ("Successor Acceptance", "ACCEPTANCE RECORDED", "DOC-ACC",
                 "RELIED_ON_IN_FINALIZED_TRANSITION", "Maker: maker", "Reviewer: reviewer",
                 "does not establish legal or appointment validity"):
        assert text in html
    assert "not-for-display" not in html
    assert "<form" not in html.lower() and "<button" not in html.lower()
    assert _snapshot(db_path) == before


def test_workspace_pending_and_unlinked_continuity_remain_distinct(monkeypatch, tmp_path):
    app, routes, _ = _load_isolated_app(monkeypatch, tmp_path)
    client = app.test_client()
    _session(client)
    monkeypatch.setattr(routes, "user_has_effective_permission", lambda *_: True)
    monkeypatch.setattr(routes, "build_trust_successor_handoff_context", lambda *_args, **_kwargs: _handoff("PENDING_EVIDENCE", linked=False))
    html = client.get("/trust/TR-A/successor-handoff").get_data(as_text=True)
    assert "ACCEPTANCE PENDING REVIEW" in html
    assert "No Continuity Profile linked" in html
    assert "activate Continuity" in html


def test_route_passes_trust_scoped_acceptance_authorization(monkeypatch, tmp_path):
    app, routes, _ = _load_isolated_app(monkeypatch, tmp_path)
    client = app.test_client()
    _session(client)
    monkeypatch.setattr(routes, "user_has_effective_permission", lambda *_: True)
    seen = {}
    def build(trust_id, **kwargs):
        seen["same"] = kwargs["acceptance_authorization_check"]("ACC-A", trust_id)
        seen["other"] = kwargs["acceptance_authorization_check"]("ACC-X", "TR-X")
        return _handoff()
    monkeypatch.setattr(routes, "build_trust_successor_handoff_context", build)
    assert client.get("/trust/TR-A/successor-handoff").status_code == 200
    assert seen == {"same": True, "other": False}
