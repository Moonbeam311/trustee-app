import importlib
import re
import sqlite3
import sys
import time


def _load_isolated_app(monkeypatch, tmp_path):
    db_path = tmp_path / "handoff-ui.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path / "uploads"))
    monkeypatch.setenv("EXPORT_ROOT", str(tmp_path / "exports"))
    for name in ("app", "routes_tpd1c", "database.db"):
        sys.modules.pop(name, None)
    module = importlib.import_module("app")
    routes = importlib.import_module("routes_tpd1c")
    module.app.config.update(TESTING=True, SECRET_KEY="handoff-ui-isolated")
    return module.app, routes, db_path


def _session(client, role="Admin", firm="FIRM-A", username="operator"):
    with client.session_transaction() as session:
        session["username"] = username
        session["user_id"] = "USR-1"
        session["firm_id"] = firm
        session["role"] = role
        session["last_activity"] = time.time()


def _snapshot(path):
    connection = sqlite3.connect(path)
    try:
        tables = [
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        ]
        return {
            table: connection.execute(f'SELECT * FROM "{table}" ORDER BY 1').fetchall()
            for table in tables
        }
    finally:
        connection.close()


def _aggregate(linked=True):
    profiles = [{
        "continuity_profile_id": "CP-A",
        "profile": {"subject_name": "Successor Context"},
        "readiness": {"classification": "needs_attention"},
        "responsibilities": [{
            "description": "Administer Trust",
            "current_responsible_party": "Current Trustee",
            "successor_responsible_party": "Successor Trustee",
            "authority_source": "Recorded instrument",
            "supporting_document_reference": "DOC-A",
        }],
        "digital_access_metadata": [{
            "institution_service": "Bank portal", "account_category": "operations",
            "account_label": "Operating", "login_identifier": "safe-user",
            "vault_reference": "VAULT-1", "recovery_procedure": "Contact custodian",
            "mfa_method": "hardware key", "mfa_device_custodian": "Custodian",
            "emergency_access_authorization": "Recorded procedure",
            "successor_responsible_party": "Successor Trustee",
        }],
        "receivables": [{
            "payer_debtor": "Tenant", "description": "Rent",
            "successor_collector": "Successor Trustee", "status": "active",
        }],
        "payables": [{
            "creditor_payee": "Insurer", "description": "Premium",
            "successor_responsible_party": "Successor Trustee",
            "continuity_instruction": "Maintain coverage",
        }],
        "activation_plans": [{"status": "plan_drafted"}],
    }] if linked else []
    return {
        "root_trust_id": "TR-A",
        "identity": {
            "trust": {"trust_name": "Alpha Trust", "status": "Active"},
            "current_trustee": "Current Trustee",
            "successor_trustee": "Successor Trustee",
        },
        "fiduciary_authority": {
            "state": "AVAILABLE",
            "records": [{
                "fiduciary_id": "FID-A", "full_name": "Successor Trustee",
                "role_title": "Successor Trustee", "authority_scope": "Recorded instrument",
                "authority_evidence": {"authority_evidence_state": "recorded"},
            }],
        },
        "continuity": {
            "state": "AVAILABLE" if linked else "UNLINKED",
            "profiles": profiles,
        },
        "accounts_assets": {
            "accounts": [{"account_id": "ACC-A", "account_label": "Operating", "institution": "Bank", "masked_number": "****1234"}],
            "assets": [{"property_id": "PROP-A", "property_name": "Residence", "property_type": "real_property", "responsible_party": "Current Trustee"}],
        },
        "governance": {
            "state": "AVAILABLE",
            "links": [{
                "governance_id": "DIR-A", "governance_type": "Directive",
                "record": {"title": "Preserve Trust", "status": "Issued"},
                "relationship": {"relationship_type": "governs"},
            }],
        },
        "execution": {
            "state": "NOT APPLICABLE",
            "orchestration": {"recommended_next_action": "NOT DOCUMENTED", "execution": None, "transfer": None},
        },
        "documents": {
            "state": "AVAILABLE", "references": [{"document_id": "DOC-A", "document_title": "Trust instrument", "document_category": "governance"}],
        },
        "archive": {
            "state": "AVAILABLE", "descriptors": [{"package_id": "HO-A", "recorded_status": "prepared", "source_object_id": "TX-A"}],
        },
        "readiness": {
            "status": "needs_attention", "gap_count": 1,
            "gaps": [{"code": "continuity_readiness_gaps", "source_domain": "Continuity", "source_record_id": "CP-A"}],
            "disclaimer": "Readiness is not legal validity, appointment, incapacity, financial certification, completion, or application access.",
        },
        "provenance": [
            {"source_domain": "Trust", "source_record_id": "TR-A"},
            {"source_domain": "Continuity", "source_record_id": "CP-A"},
        ],
    }


def _authorize(routes, monkeypatch, assigned=True):
    monkeypatch.setattr(routes, "user_has_effective_permission", lambda _user, permission: permission == "view_dashboard")
    monkeypatch.setattr(
        routes, "get_roles_by_trust_id",
        lambda _trust_id: [{"full_name": "operator"}] if assigned else [],
    )


def test_workspace_requires_authentication_and_current_permission(monkeypatch, tmp_path):
    app, routes, _ = _load_isolated_app(monkeypatch, tmp_path)
    client = app.test_client()
    assert client.get("/trust/TR-A/successor-handoff").status_code == 302
    _session(client)
    monkeypatch.setattr(routes, "user_has_effective_permission", lambda *_args: False)
    assert client.get("/trust/TR-A/successor-handoff").status_code == 403


def test_workspace_calls_canonical_aggregate_and_renders_all_read_sections(monkeypatch, tmp_path):
    app, routes, db_path = _load_isolated_app(monkeypatch, tmp_path)
    client = app.test_client()
    _session(client)
    _authorize(routes, monkeypatch)
    calls = []

    def build(trust_id, **kwargs):
        calls.append((trust_id, kwargs))
        assert kwargs["trust_authorization_check"](trust_id)
        assert kwargs["governance_authorization_check"](trust_id)
        return _aggregate()

    monkeypatch.setattr(routes, "build_trust_successor_handoff_context", build)
    before = _snapshot(db_path)
    response = client.get("/trust/TR-A/successor-handoff")
    after = _snapshot(db_path)
    assert response.status_code == 200
    assert calls and calls[0][0] == "TR-A"
    html = response.get_data(as_text=True)
    for expected in (
        "Hindsfoot OS", "Successor Handoff", "Alpha Trust", "Return to Trust",
        "Continuity Profile CP-A", "Handoff readiness", "Successor and fiduciary authority",
        "Recorded authority scope", "Accounts and assets", "Access and operational continuity",
        "VAULT-1", "safe-user", "Receivables and payables", "Preserve Trust",
        "Execution", "Trust instrument", "Archive", "Source references",
    ):
        assert expected in html
    assert "legally authorized" not in html.lower()
    assert "active successor" not in html.lower()
    assert before == after


def test_workspace_has_no_mutation_controls_or_secret_material(monkeypatch, tmp_path):
    app, routes, _ = _load_isolated_app(monkeypatch, tmp_path)
    client = app.test_client()
    _session(client)
    _authorize(routes, monkeypatch)
    monkeypatch.setattr(
        routes, "build_trust_successor_handoff_context",
        lambda trust_id, **kwargs: (
            _aggregate() if kwargs["trust_authorization_check"](trust_id) else None
        ),
    )
    html = client.get("/trust/TR-A/successor-handoff").get_data(as_text=True)
    assert "<form" not in html.lower()
    assert "<button" not in html.lower()
    for secret in ("never-output", "private_key", "security_answer", "recovery_code", "card_number"):
        assert secret not in html
    for mutation_label in ("Generate packet", "Acknowledge successor", "Activate continuity", "Finalize archive"):
        assert mutation_label not in html


def test_missing_cross_firm_and_unassigned_trusts_fail_without_disclosure(monkeypatch, tmp_path):
    app, routes, _ = _load_isolated_app(monkeypatch, tmp_path)
    client = app.test_client()
    _session(client, role="Viewer")
    _authorize(routes, monkeypatch, assigned=False)

    def build(trust_id, **kwargs):
        return _aggregate() if kwargs["trust_authorization_check"](trust_id) else None

    monkeypatch.setattr(routes, "build_trust_successor_handoff_context", build)
    assert client.get("/trust/TR-X/successor-handoff").status_code == 404
    assert client.get("/trust/missing/successor-handoff").status_code == 404


def test_unlinked_trust_displays_safe_state_without_creation_action(monkeypatch, tmp_path):
    app, routes, _ = _load_isolated_app(monkeypatch, tmp_path)
    client = app.test_client()
    _session(client)
    _authorize(routes, monkeypatch)
    monkeypatch.setattr(routes, "build_trust_successor_handoff_context", lambda *_args, **_kwargs: _aggregate(linked=False))
    html = client.get("/trust/TR-A/successor-handoff").get_data(as_text=True)
    assert "UNLINKED" in html
    assert "No Continuity Profile linked" in html
    assert "Profile creation remains a separate governed action" in html
    assert "continuity-profiles/new" not in html


def test_admin_trustee_and_viewer_follow_existing_access_policy(monkeypatch, tmp_path):
    app, routes, _ = _load_isolated_app(monkeypatch, tmp_path)
    client = app.test_client()
    _authorize(routes, monkeypatch, assigned=True)
    monkeypatch.setattr(
        routes, "build_trust_successor_handoff_context",
        lambda trust_id, **kwargs: (
            _aggregate() if kwargs["trust_authorization_check"](trust_id) else None
        ),
    )
    for role in ("Admin", "Trustee", "Viewer"):
        _session(client, role=role)
        assert client.get("/trust/TR-A/successor-handoff").status_code == 200
    _authorize(routes, monkeypatch, assigned=False)
    for role in ("Trustee", "Viewer"):
        _session(client, role=role)
        assert client.get("/trust/TR-A/successor-handoff").status_code == 404


def test_trust_detail_contains_single_read_only_handoff_entry():
    from pathlib import Path

    html = (Path(__file__).resolve().parents[1] / "templates" / "trust_detail.html").read_text(encoding="utf-8")
    assert html.count("tpd1c.successor_handoff_workspace") == 1
    assert re.search(r"Successor Handoff", html)
