import importlib
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

from database.migrations_intake_trust_bridge import migrate_intake_trust_bridge
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


def _seed_bridge_draft(db_path):
    connection = sqlite3.connect(db_path)
    trust_columns = {row[1] for row in connection.execute("PRAGMA table_info(trusts)")}
    if "firm_id" not in trust_columns:
        connection.execute("ALTER TABLE trusts ADD COLUMN firm_id TEXT")
    connection.execute(
        """CREATE TABLE IF NOT EXISTS intake_document_recommendations(
               id INTEGER PRIMARY KEY AUTOINCREMENT,intake_id TEXT,firm_id TEXT,
               workflow_key TEXT,title TEXT,reason TEXT,status TEXT,created_at TEXT,
               updated_at TEXT,created_by TEXT
           )"""
    )
    connection.commit()
    connection.close()
    migrate_intake_trust_bridge(db_path)
    connection = sqlite3.connect(db_path)
    connection.execute(
        """INSERT INTO trusts(
               trust_id,trust_name,short_name,jurisdiction,effective_date,
               trust_type,trust_purpose,status,firm_id
           ) VALUES(?,?,?,?,?,?,?,?,?)""",
        (
            "TR-DRAFT", "TPD Draft Trust", "TPD Draft", "Virginia", "2026-08-08",
            "Revocable living trust", "Draft review only", "Draft - Bridge Created", "FIRM-002",
        ),
    )
    recommendation_id = connection.execute(
        """INSERT INTO intake_document_recommendations(
               intake_id,firm_id,workflow_key,title,reason,status,created_at,updated_at,created_by
           ) VALUES(?,?,?,?,?,?,?,?,?)""",
        ("INT-DRAFT", "FIRM-002", "declaration_of_trust", "Declaration", "Test", "accepted", "v1", "v1", "operator"),
    ).lastrowid
    connection.execute(
        """INSERT INTO intake_trust_formation_bridges(
               bridge_id,firm_id,intake_id,recommendation_id,workflow_key,selected_instrument,
               source_status,source_version,source_fingerprint,bridge_status,
               professional_review_disposition,confirmation_state,trust_id,idempotency_key,
               prepared_by,confirmed_by,launched_by,prepared_at,confirmed_at,launched_at,created_at,updated_at
           ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "BRG-DRAFT", "FIRM-002", "INT-DRAFT", recommendation_id, "declaration_of_trust",
            "declaration_of_trust", "accepted", "v1", "fingerprint", "trust_created",
            "clear", "confirmed", "TR-DRAFT", "draft-idempotency", "operator", "operator",
            "operator", "v1", "v1", "v1", "v1", "v1",
        ),
    )
    connection.commit()
    connection.close()


def _database_counts(db_path):
    connection = sqlite3.connect(db_path)
    tables = [row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )]
    counts = {table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] for table in tables}
    status = connection.execute("SELECT status FROM trusts WHERE trust_id='TR-DRAFT'").fetchone()[0]
    bridge = connection.execute(
        "SELECT bridge_status,confirmation_state FROM intake_trust_formation_bridges WHERE bridge_id='BRG-DRAFT'"
    ).fetchone()
    connection.close()
    return counts, status, bridge


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
        assert f'id="confirmed-{field}"' in html
        assert f'name="confirmed_fields" value="{field}"' in html
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


def test_formation_preview_hub_identifies_draft_provenance_and_absent_profile():
    html = (Path(__file__).resolve().parents[1] / "templates" / "trust_formation_preview_hub.html").read_text(encoding="utf-8")
    assert "Draft Trust Created" in html
    assert "not finalized or executed" in html
    assert "source fingerprint" in html
    assert "No Continuity Profile is linked" in html
    assert "Profile creation remains a separate, explicit operator action" in html


def test_formation_preview_hub_renders_all_governed_values_and_only_one_deviation(monkeypatch, tmp_path):
    app, _routes = _load_isolated_app(monkeypatch, tmp_path)
    from flask import render_template
    values = {
        "effective_date": "2026-08-07", "jurisdiction": "New Jersey", "short_name": "Continuity Pilot",
        "trust_name": "Continuity Pilot Trust", "accounting_method": "cash", "grantor_contact": "alex.morgan@example.test",
        "grantor_name": "Alex Morgan", "grantor_type": "Individual", "trust_purpose": "Family continuity and records preservation",
        "trust_type": "Revocable living trust", "workflow_mode": "private_office", "beneficiary_name": "Jordan Morgan",
        "settlor_name": "Alex Morgan", "successor_trustee_name": "Taylor Morgan", "trustee_name": "Casey Morgan",
        "ai_explanations": "enabled", "recommended_guidance": "enabled", "record_visibility": "private",
        "workflow_mode_confirmed": "private_office", "asset_categories": "Real estate",
        "generate_schedule_recommendations": "yes", "initial_corpus_description": "Synthetic residential real-property interest",
        "property_mapping_timing": "later",
    }
    proposals = [{
        "target_field": field, "confirmed_value": value,
        "source_classification": "OPERATOR_DECISION",
        "deviation_indicator": field == "trust_purpose",
        "deviation_reason": "Expanded during operator review" if field == "trust_purpose" else None,
    } for field, value in values.items()]
    bridge_fixture_id = "ITFB-" + "FIXTURE-ROUTE"
    trust_fixture_id = "TR-" + "FIXTURE-ROUTE"
    planning = {
        "bridge": {"intake_id": "INT-TPD1C-001", "bridge_id": bridge_fixture_id, "workflow_key": "declaration_of_trust",
                   "source_version": "v1", "source_fingerprint": "fingerprint-1", "confirmed_at": "confirmed-at", "confirmed_by": "operator"},
        "profiles": [], "proposals": proposals, "deviation_count": 1,
    }
    with app.test_request_context(f"/trust/{trust_fixture_id}/formation-preview-hub"):
        rendered = render_template(
            "trust_formation_preview_hub.html", trust={"trust_id": trust_fixture_id, "status": "Draft - Bridge Created"},
            preview_context={}, document_readiness={}, packet_readiness={}, formation_provenance=lambda trust_id: planning,
        )
    for field, value in values.items():
        assert f'data-formation-field="{field}"' in rendered
        assert value in rendered
    assert rendered.count("Expanded during operator review") == 1
    for forbidden in ("Download Controlled Packet ZIP", "Final Surface", "Open Execution Dashboard", "Go to Execution Dashboard", "Go to Finalize step"):
        assert forbidden not in rendered
    assert "Draft review required" in rendered
    assert "Formation data is complete; lifecycle authorization is not." in rendered
    assert "No Continuity Profile is linked" in rendered


def test_bridge_created_draft_server_side_lifecycle_gate(monkeypatch, tmp_path):
    app, _routes = _load_isolated_app(monkeypatch, tmp_path)
    module = sys.modules["app"]
    trust_fixture_id = "TR-" + "FIXTURE-LIFECYCLE"
    draft = {"trust_id": trust_fixture_id, "status": "Draft - Bridge Created"}
    finalized = {"trust_id": trust_fixture_id, "status": "Finalized"}
    assert module.bridge_draft_lifecycle_blocked("trust_controlled_packet_export", draft)
    assert module.bridge_draft_lifecycle_blocked("trust_articles_output_surface", draft)
    assert module.bridge_draft_lifecycle_blocked("trust_articles_preview", draft)
    assert module.bridge_draft_lifecycle_blocked("trust_execution_dashboard", draft)
    assert module.bridge_draft_lifecycle_blocked("create_trust_step6", draft)
    assert module.bridge_draft_lifecycle_blocked("transfer_start", draft)
    assert not module.bridge_draft_lifecycle_blocked("trust_formation_preview_hub", draft)
    assert not module.bridge_draft_lifecycle_blocked("trust_controlled_packet_export", finalized)


def test_create_or_resume_route_security_and_idempotency(monkeypatch, tmp_path):
    app, routes = _load_isolated_app(monkeypatch, tmp_path)
    client = app.test_client()
    url = "/trust-formation-bridges/BRG-1/create-or-resume"
    # CSRF is evaluated before route authentication on mutating requests.
    assert client.post(url).status_code == 400
    _session(client)
    allowed = {"value": True}
    monkeypatch.setattr(routes, "user_has_effective_permission", lambda username, permission: allowed["value"] and permission == "create_trust")
    monkeypatch.setattr(routes, "get_bridge", lambda db_path, bridge_id, firm_id: {
        "bridge": {"bridge_id": bridge_id, "bridge_status": "confirmed", "intake_id": "INT-1", "workflow_key": "declaration_of_trust", "matter_id": None, "trust_id": None},
        "proposals": [], "events": [],
    })
    detail = client.get("/trust-formation-bridges/BRG-1")
    token = re.search(rb'name="_csrf_token" value="([^"]+)"', detail.data).group(1).decode()
    assert client.post(url).status_code == 400
    assert client.post(url, data={"_csrf_token": "invalid"}).status_code == 400
    calls = []
    trust_fixture_id = "TR-" + "FIXTURE-CREATE"
    monkeypatch.setattr(routes, "create_or_resume_trust", lambda db_path, bridge_id, firm_id, actor: calls.append((bridge_id, firm_id, actor)) or {"trust_id": trust_fixture_id, "resumed": len(calls) > 1})
    first = client.post(url, data={"_csrf_token": token})
    second = client.post(url, data={"_csrf_token": token})
    assert first.status_code == second.status_code == 302
    assert first.headers["Location"].endswith(f"/trust/{trust_fixture_id}")
    assert calls == [("BRG-1", "FIRM-1", "operator"), ("BRG-1", "FIRM-1", "operator")]
    allowed["value"] = False
    assert client.post(url, data={"_csrf_token": token}).status_code == 403
    allowed["value"] = True
    _session(client, firm="FIRM-2")
    def reject_cross_firm(db_path, bridge_id, firm_id, actor):
        raise routes.BridgeError("Bridge not found.")
    monkeypatch.setattr(routes, "create_or_resume_trust", reject_cross_firm)
    cross_firm = client.post(url, data={"_csrf_token": token})
    assert cross_firm.status_code == 302
    assert cross_firm.headers["Location"].endswith("/trust-formation-bridges/BRG-1")


def test_bridge_draft_all_direct_trust_endpoints_return_403_without_mutation(monkeypatch, tmp_path):
    app, routes = _load_isolated_app(monkeypatch, tmp_path)
    module = sys.modules["app"]
    db_path = tmp_path / "route-test.db"
    _seed_bridge_draft(db_path)
    client = app.test_client()
    _session(client, firm="FIRM-002")
    monkeypatch.setattr(module, "user_has_effective_permission", lambda username, permission: True)
    monkeypatch.setattr(routes, "user_has_effective_permission", lambda username, permission: True)

    token_page = client.get("/continuity-profiles/new")
    token = re.search(rb'name="_csrf_token" value="([^"]+)"', token_page.data).group(1).decode()
    before = _database_counts(db_path)
    values = {
        "trust_id": "TR-DRAFT", "beneficiary_id": "BEN-MISSING",
        "distribution_id": "DIST-MISSING", "tax_year": "2026",
    }
    tested = []
    adapter = app.url_map.bind("")
    for endpoint in sorted(module.BRIDGE_DRAFT_BLOCKED_ENDPOINTS):
        rules = [rule for rule in app.url_map.iter_rules(endpoint) if "trust_id" in rule.arguments]
        assert rules, endpoint
        for rule in rules:
            path = adapter.build(endpoint, {name: values.get(name, "MISSING") for name in rule.arguments})
            for method in sorted(set(rule.methods) - {"HEAD", "OPTIONS"}):
                data = {"_csrf_token": token} if method == "POST" else None
                response = client.open(path, method=method, data=data)
                assert response.status_code == 403, (endpoint, method, response.status_code)
                assert "governed intake bridge" in response.get_data(as_text=True)
                assert not response.location
                tested.append((rule.rule, method, endpoint))

    assert tested
    assert _database_counts(db_path) == before
    assert not any(path.is_file() for path in (tmp_path / "uploads").rglob("*"))
    assert not any(path.is_file() for path in (tmp_path / "exports").rglob("*"))


def test_bridge_draft_generic_and_bridge_dispatch_endpoints_return_403_without_mutation(monkeypatch, tmp_path):
    app, routes = _load_isolated_app(monkeypatch, tmp_path)
    module = sys.modules["app"]
    db_path = tmp_path / "route-test.db"
    _seed_bridge_draft(db_path)
    client = app.test_client()
    _session(client, firm="FIRM-002")
    monkeypatch.setattr(module, "user_has_effective_permission", lambda username, permission: True)
    monkeypatch.setattr(routes, "user_has_effective_permission", lambda username, permission: True)
    token_page = client.get("/continuity-profiles/new")
    token = re.search(rb'name="_csrf_token" value="([^"]+)"', token_page.data).group(1).decode()
    before = _database_counts(db_path)

    cases = [
        ("/financial_summary?trust_id=TR-DRAFT", "GET", {}),
        ("/tax_assistant?trust_id=TR-DRAFT", "GET", {}),
        ("/form1041?trust_id=TR-DRAFT", "GET", {}),
        ("/instruments?trust_id=TR-DRAFT", "GET", {}),
        ("/reports/fiduciaries.pdf?trust_id=TR-DRAFT", "GET", {}),
        ("/add_property?trust_id=TR-DRAFT", "GET", {}),
        ("/add_property", "POST", {"trust_id": "TR-DRAFT"}),
        ("/link_account?trust_id=TR-DRAFT", "GET", {}),
        ("/link_account", "POST", {"trust_id": "TR-DRAFT"}),
        ("/upload_document?trust_id=TR-DRAFT", "GET", {}),
        ("/upload_document", "POST", {"trust_id": "TR-DRAFT"}),
        ("/ledger_entry?trust_id=TR-DRAFT", "GET", {}),
        ("/ledger_entry", "POST", {"trust_id": "TR-DRAFT"}),
        ("/media/upload?trust_id=TR-DRAFT", "GET", {}),
        ("/media/upload", "POST", {"trust_id": "TR-DRAFT"}),
        ("/instruments/new?trust_id=TR-DRAFT", "GET", {}),
        ("/instruments/new", "POST", {"trust_id": "TR-DRAFT"}),
        ("/minutes/new?trust_id=TR-DRAFT", "GET", {}),
        ("/minutes/new", "POST", {"trust_id": "TR-DRAFT"}),
        ("/fiduciaries/new?trust_id=TR-DRAFT", "GET", {}),
        ("/fiduciaries/new", "POST", {"trust_id": "TR-DRAFT"}),
        ("/genealogy/new?trust_id=TR-DRAFT", "GET", {}),
        ("/genealogy/new", "POST", {"trust_id": "TR-DRAFT"}),
        ("/execution/tasks/new?trust_id=TR-DRAFT", "GET", {}),
        ("/execution/tasks/new", "POST", {"trust_id": "TR-DRAFT"}),
        ("/workspaces/MISSING/tasks/new?trust_id=TR-DRAFT", "GET", {}),
        ("/workspaces/MISSING/tasks/new", "POST", {"trust_id": "TR-DRAFT"}),
        ("/documents/generate?trust_id=TR-DRAFT", "GET", {}),
        ("/documents/generate", "POST", {"trust_id": "TR-DRAFT"}),
        ("/workspaces/MISSING/documents/generate?trust_id=TR-DRAFT", "GET", {}),
        ("/workspaces/MISSING/documents/generate", "POST", {"trust_id": "TR-DRAFT"}),
        ("/execution/sessions/new?trust_id=TR-DRAFT", "GET", {}),
        ("/execution/sessions/new", "POST", {"trust_id": "TR-DRAFT"}),
        ("/reports?trust_id=TR-DRAFT", "GET", {}),
        ("/reports", "POST", {"trust_id": "TR-DRAFT", "report_type": "trust_summary"}),
        ("/continuity-profiles/new?trust_id=TR-DRAFT", "GET", {}),
        ("/continuity-profiles/new", "POST", {"trust_id": "TR-DRAFT"}),
        ("/continuity-profiles/new?bridge_id=BRG-DRAFT", "GET", {}),
        ("/continuity-profiles/new", "POST", {"bridge_id": "BRG-DRAFT"}),
        ("/trust-formation-bridges/BRG-DRAFT/create-or-resume", "POST", {}),
        ("/trust-formation-bridges/BRG-DRAFT/continuity/link", "POST", {}),
    ]
    for path, method, data in cases:
        response = client.open(path, method=method, data={**data, "_csrf_token": token})
        assert response.status_code == 403, (path, response.status_code)
        assert "governed intake bridge" in response.get_data(as_text=True)
        assert not response.location

    assert _database_counts(db_path) == before
    assert not any(path.is_file() for path in (tmp_path / "uploads").rglob("*"))
    assert not any(path.is_file() for path in (tmp_path / "exports").rglob("*"))


def test_bridge_draft_review_surfaces_allowed_and_non_draft_not_blocked(monkeypatch, tmp_path):
    app, routes = _load_isolated_app(monkeypatch, tmp_path)
    module = sys.modules["app"]
    db_path = tmp_path / "route-test.db"
    _seed_bridge_draft(db_path)
    client = app.test_client()
    _session(client, firm="FIRM-002")
    monkeypatch.setattr(module, "user_has_effective_permission", lambda username, permission: True)
    monkeypatch.setattr(routes, "user_has_effective_permission", lambda username, permission: True)

    detail = client.get("/trust/TR-DRAFT")
    hub = client.get("/trust/TR-DRAFT/formation-preview-hub")
    assert detail.status_code == 200
    assert hub.status_code == 200
    assert "Draft review required" in hub.get_data(as_text=True)

    connection = sqlite3.connect(db_path)
    connection.execute("UPDATE trusts SET status='Finalized' WHERE trust_id='TR-DRAFT'")
    connection.commit(); connection.close()
    response = client.get("/trust/TR-DRAFT/packet-preview")
    assert response.status_code != 403


def test_bridge_draft_generic_cross_firm_target_keeps_access_denial(monkeypatch, tmp_path):
    app, routes = _load_isolated_app(monkeypatch, tmp_path)
    module = sys.modules["app"]
    db_path = tmp_path / "route-test.db"
    _seed_bridge_draft(db_path)
    client = app.test_client()
    _session(client, firm="FIRM-1")
    monkeypatch.setattr(module, "user_has_effective_permission", lambda username, permission: True)
    monkeypatch.setattr(routes, "user_has_effective_permission", lambda username, permission: True)
    token_page = client.get("/continuity-profiles/new")
    token = re.search(rb'name="_csrf_token" value="([^"]+)"', token_page.data).group(1).decode()
    before = _database_counts(db_path)
    response = client.post("/add_property", data={"trust_id": "TR-DRAFT", "_csrf_token": token})
    assert response.status_code == 403
    body = response.get_data(as_text=True)
    assert "not assigned" in body
    assert "governed intake bridge" not in body
    assert _database_counts(db_path) == before
