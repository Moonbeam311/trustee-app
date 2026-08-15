import importlib
import re
import sys
import time

from services.services_intake_trust_bridge import FORMATION_FIELD_CONTROLS, REQUIRED_FIELDS


def _load_isolated_app(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "route-test.db"))
    monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path / "uploads"))
    monkeypatch.setenv("EXPORT_ROOT", str(tmp_path / "exports"))
    for name in ("app", "routes_tpd1c", "database.db"):
        sys.modules.pop(name, None)
    module = importlib.import_module("app")
    routes = importlib.import_module("routes_tpd1c")
    module.app.config.update(TESTING=True, SECRET_KEY="tpd1c-isolated-test")
    return module.app, routes


def _session(client, firm="FIRM-1"):
    with client.session_transaction() as session:
        session["username"] = "operator"
        session["user_id"] = "USR-1"
        session["firm_id"] = firm
        session["role"] = "Admin"
        session["last_activity"] = time.time()


def test_route_authentication_authorization_and_csrf(monkeypatch, tmp_path):
    app, routes = _load_isolated_app(monkeypatch, tmp_path)
    client = app.test_client()
    anonymous = client.get("/continuity-profiles/new")
    assert anonymous.status_code in (302, 303)

    _session(client)
    monkeypatch.setattr(routes, "user_has_effective_permission", lambda username, permission: False)
    assert client.get("/continuity-profiles/new").status_code in (302, 403)

    monkeypatch.setattr(routes, "user_has_effective_permission", lambda username, permission: permission in {"edit_trust", "create_trust"})
    assert client.get("/continuity-profiles/new").status_code in (200, 302)
    monkeypatch.setattr(routes, "evaluate_eligibility", lambda db_path, firm_id, intake_id: {"eligible": False, "reasons": ["Synthetic route test"]})
    assert client.get("/intake/UNKNOWN/recommendations/declaration_of_trust/trust-formation-bridge").status_code in (200, 302)
    assert client.post("/continuity-profiles/new", data={"subject_name": "Alex"}).status_code == 400


def test_blueprint_has_narrow_permission_decorators(monkeypatch, tmp_path):
    app, _routes = _load_isolated_app(monkeypatch, tmp_path)
    rules = {rule.rule: set(rule.methods) for rule in app.url_map.iter_rules() if rule.endpoint.startswith("tpd1c.")}
    assert "/trust-formation-bridges/<bridge_id>/confirm" in rules
    assert "POST" in rules["/trust-formation-bridges/<bridge_id>/confirm"]
    assert "/continuity-profiles/<profile_id>/activation/<plan_id>/transition" in rules


def test_prepare_bridge_signed_csrf_authorization_firm_scope_and_idempotency(monkeypatch, tmp_path):
    app, routes = _load_isolated_app(monkeypatch, tmp_path)
    client = app.test_client()
    _session(client)
    allowed = {"value": True}
    monkeypatch.setattr(
        routes,
        "user_has_effective_permission",
        lambda username, permission: allowed["value"] and permission == "create_trust",
    )
    monkeypatch.setattr(
        routes,
        "evaluate_eligibility",
        lambda db_path, firm_id, intake_id: {"eligible": True, "reasons": []},
    )
    calls = []

    def fake_prepare(db_path, firm_id, intake_id, actor, matter_id):
        calls.append((firm_id, intake_id, actor, matter_id))
        if firm_id != "FIRM-1":
            raise routes.BridgeError("Intake is not eligible in the active firm context.")
        return {"bridge_id": "BRG-TEST-001"}

    monkeypatch.setattr(routes, "prepare_bridge", fake_prepare)
    url = "/intake/INT-1/recommendations/declaration_of_trust/trust-formation-bridge"
    page = client.get(url)
    token = re.search(
        rb'name="_csrf_token" value="([^"]+)"', page.data
    ).group(1).decode()

    assert client.post(url, data={"matter_id": ""}).status_code == 400
    assert client.post(
        url, data={"_csrf_token": "invalid", "matter_id": ""}
    ).status_code == 400

    response = client.post(
        url, data={"_csrf_token": token, "matter_id": ""}
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/trust-formation-bridges/BRG-TEST-001"
    )
    repeated = client.post(
        url, data={"_csrf_token": token, "matter_id": ""}
    )
    assert repeated.status_code == 302
    assert len(calls) == 2
    assert calls[0] == calls[1] == (
        "FIRM-1", "INT-1", "operator", None
    )

    allowed["value"] = False
    assert client.post(
        url, data={"_csrf_token": token, "matter_id": ""}
    ).status_code == 403

    allowed["value"] = True
    _session(client, firm="FIRM-2")
    cross_firm = client.post(
        url, data={"_csrf_token": token, "matter_id": ""}
    )
    assert cross_firm.status_code == 302
    assert cross_firm.headers["Location"].endswith(
        "/intake/INT-1/recommendations"
    )


def test_formation_proposal_renders_aligned_usable_required_controls(monkeypatch, tmp_path):
    app, routes = _load_isolated_app(monkeypatch, tmp_path)
    client = app.test_client()
    _session(client)
    monkeypatch.setattr(routes, "user_has_effective_permission", lambda username, permission: permission == "create_trust")
    proposals = []
    for index, field in enumerate(FORMATION_FIELD_CONTROLS):
        proposals.append({
            "proposal_id": f"P-{index}", "target_field": field,
            "target_step": index // 5 + 1, "source_record_type": "operator",
            "source_field_id": field, "source_classification": "OPERATOR_DECISION",
            "confirmation_requirement": "REQUIRE_NEW_ENTRY",
            "original_source_value": "", "proposed_value": "",
            "confirmed_value": None, "confirmation_status": "pending",
            "deviation_reason": None,
        })
    monkeypatch.setattr(routes, "get_bridge", lambda db_path, bridge_id, firm_id: {
        "bridge": {"bridge_id": bridge_id, "bridge_status": "prepared", "intake_id": "INT-1", "workflow_key": "declaration_of_trust", "matter_id": None, "trust_id": None},
        "proposals": proposals, "events": [],
    })
    response = client.get("/trust-formation-bridges/BRG-1")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    for field, control in FORMATION_FIELD_CONTROLS.items():
        assert f'data-field="{field}"' in html
        assert f'name="{field}"' in html
        assert f'id="formation-{field}"' in html
        assert f'deviation_reason__{field}' in html
        if field in REQUIRED_FIELDS:
            assert f'id="formation-{field}"' in html and "required" in html[html.index(f'id="formation-{field}"'):html.index(f'id="formation-{field}"') + 300]
        for value, label in control.get("choices", ()):
            assert f'value="{value}"' in html
            assert label in html


def test_source_rebase_route_requires_csrf_permission_and_same_firm(monkeypatch, tmp_path):
    app, routes = _load_isolated_app(monkeypatch, tmp_path)
    client = app.test_client()
    _session(client)
    allowed = {"value": True}
    monkeypatch.setattr(routes, "user_has_effective_permission", lambda username, permission: allowed["value"] and permission == "create_trust")
    monkeypatch.setattr(routes, "get_bridge", lambda db_path, bridge_id, firm_id: {
        "bridge": {"bridge_id": bridge_id, "bridge_status": "needs_review", "intake_id": "INT-1", "workflow_key": "declaration_of_trust", "matter_id": None, "trust_id": None},
        "proposals": [], "events": [],
    })
    calls = []
    def fake_rebase(db_path, bridge_id, firm_id, actor):
        calls.append((bridge_id, firm_id, actor))
        if firm_id != "FIRM-1":
            raise routes.BridgeError("Bridge not found in the active firm context.")
        return {"bridge": {"bridge_id": bridge_id}}
    monkeypatch.setattr(routes, "acknowledge_source_rebase", fake_rebase)
    detail = client.get("/trust-formation-bridges/BRG-SELECTED")
    token = re.search(rb'name="_csrf_token" value="([^"]+)"', detail.data).group(1).decode()
    url = "/trust-formation-bridges/BRG-SELECTED/acknowledge-source"
    assert client.post(url).status_code == 400
    allowed["value"] = False
    assert client.post(url, data={"_csrf_token": token}).status_code == 403
    allowed["value"] = True
    assert client.post(url, data={"_csrf_token": token}).status_code == 302
    assert calls[-1] == ("BRG-SELECTED", "FIRM-1", "operator")
    _session(client, firm="FIRM-2")
    assert client.post(url, data={"_csrf_token": token}).status_code == 302
    assert calls[-1] == ("BRG-SELECTED", "FIRM-2", "operator")
