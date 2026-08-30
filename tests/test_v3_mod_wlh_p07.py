from __future__ import annotations

import sqlite3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest

import database.db as database_db
from database.migrations_governed_program_promotion import (
    apply_governed_program_promotion_schema,
)
import services.services_governed_program_promotion as promotion


ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")
DETAIL = (ROOT / "templates/workspace_program_detail.html").read_text(encoding="utf-8")
PROMOTION_TEMPLATE = (ROOT / "templates/workspace_program_promotion.html").read_text(encoding="utf-8")


@pytest.fixture()
def promotion_database(monkeypatch, tmp_path):
    path = tmp_path / "p07.db"
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE workspaces (
            workspace_id TEXT PRIMARY KEY, title TEXT, owner_id TEXT NOT NULL,
            firm_id TEXT NOT NULL
        );
        CREATE TABLE hub_programs (
            program_id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
            firm_id TEXT NOT NULL, owner_id TEXT NOT NULL, title TEXT,
            status TEXT, created_by TEXT, created_at TEXT, updated_at TEXT
        );
        CREATE TABLE hub_program_revisions (
            revision_id TEXT PRIMARY KEY, program_id TEXT NOT NULL,
            revision_number INTEGER NOT NULL, snapshot_json TEXT NOT NULL,
            revision_note TEXT, created_by TEXT, created_at TEXT
        );
        CREATE TABLE trusts (
            trust_id TEXT PRIMARY KEY, trust_name TEXT, firm_id TEXT NOT NULL
        );
        CREATE TABLE app_users (
            user_id TEXT PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT,
            role_name TEXT NOT NULL, status TEXT, firm_id TEXT NOT NULL
        );
        CREATE TABLE user_roles (
            role_id TEXT PRIMARY KEY, trust_id TEXT NOT NULL,
            full_name TEXT NOT NULL, role_name TEXT
        );
        CREATE TABLE fiduciaries (
            fiduciary_id TEXT PRIMARY KEY, full_name TEXT, role_title TEXT,
            authority_scope TEXT, trust_id TEXT, appointment_date TEXT,
            effective_date TEXT, status TEXT, notes TEXT, firm_id TEXT
        );
        INSERT INTO workspaces VALUES ('WS-A','Workspace A','owner-a','FIRM-A');
        INSERT INTO workspaces VALUES ('WS-B','Workspace B','owner-b','FIRM-B');
        INSERT INTO hub_programs VALUES ('PRG-A','WS-A','FIRM-A','owner-a','Program A','draft','admin','2026','2026');
        INSERT INTO hub_programs VALUES ('PRG-B','WS-B','FIRM-B','owner-b','Program B','draft','admin-b','2026','2026');
        INSERT INTO hub_program_revisions VALUES ('REV-A1','PRG-A',1,'{"saved":1}','Saved A1','admin','2026');
        INSERT INTO hub_program_revisions VALUES ('REV-A2','PRG-A',2,'{"saved":2}','Saved A2','admin','2026');
        INSERT INTO trusts VALUES ('TR-A','Trust A','FIRM-A');
        INSERT INTO trusts VALUES ('TR-C','Trust C','FIRM-A');
        INSERT INTO trusts VALUES ('TR-B','Trust B','FIRM-B');
        INSERT INTO app_users VALUES ('U1','admin','x','Admin','Active','FIRM-A');
        INSERT INTO app_users VALUES ('U2','requester','x','Trustee','Active','FIRM-A');
        INSERT INTO app_users VALUES ('U3','approver','x','Trustee','Active','FIRM-A');
        INSERT INTO app_users VALUES ('U4','viewer','x','Viewer','Active','FIRM-A');
        INSERT INTO app_users VALUES ('U5','admin-b','x','Admin','Active','FIRM-B');
        INSERT INTO user_roles VALUES ('ROLE-1','TR-A','requester','Trustee');
        INSERT INTO user_roles VALUES ('ROLE-2','TR-A','approver','Trustee');
        INSERT INTO user_roles VALUES ('ROLE-3','TR-A','viewer','Viewer');
        INSERT INTO user_roles VALUES ('ROLE-4','TR-C','requester','Trustee');
        INSERT INTO fiduciaries VALUES ('FID-A','approver','Trustee','Governed promotion','TR-A',NULL,'2026','Active',NULL,'FIRM-A');
        """
    )
    connection.commit()
    connection.close()
    apply_governed_program_promotion_schema(path)
    connection = sqlite3.connect(path)
    connection.execute(
        "INSERT INTO fiduciary_authority_capabilities VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        ("AUTH-A", "FIRM-A", "TR-A", "FID-A", "approver",
         "APPROVE_GOVERNED_PROGRAM_PROMOTION", "Recorded fiduciary authority",
         "FIXTURE", "2026-01-01T00:00:00+00:00", None, "registrar",
         "2026-01-01T00:00:00+00:00"),
    )
    connection.execute(
        "INSERT INTO fiduciary_authority_capability_events VALUES (?,?,?,?,?,?,?)",
        ("AUTH-EVT-A", "AUTH-A", "GRANTED", "registrar", "Fixture grant",
         "2026-01-01T00:00:00+00:00", "AUTH-GRANT-A"),
    )
    connection.commit()
    connection.close()
    monkeypatch.setattr(database_db, "DB_PATH", path)
    monkeypatch.setattr(database_db, "get_current_firm_id", lambda: "FIRM-A")
    return path


def allow_trust_a(trust_id):
    return trust_id == "TR-A"


def create_request(**overrides):
    values = dict(
        workspace_id="WS-A", program_id="PRG-A", revision_id="REV-A1",
        trust_id="TR-A", firm_id="FIRM-A", owner_id="owner-a",
        actor="requester", role="Trustee", request_reason="Governed review",
        trust_authorization_check=allow_trust_a,
    )
    values.update(overrides)
    return promotion.create_promotion_request(**values)


def decide(request_id, **overrides):
    values = dict(
        request_id=request_id, actor="approver", role="Trustee",
        reason="Authority confirmed", firm_id="FIRM-A", owner_id="owner-a",
        workspace_id="WS-A", program_id="PRG-A",
        trust_authorization_check=allow_trust_a,
    )
    values.update(overrides)
    return promotion.approve_promotion_request(**values)


def execute(request_id, **overrides):
    values = dict(
        request_id=request_id, actor="admin", role="Admin", firm_id="FIRM-A",
        owner_id="owner-a", workspace_id="WS-A", program_id="PRG-A",
        trust_authorization_check=allow_trust_a,
    )
    values.update(overrides)
    return promotion.execute_promotion_request(**values)


def counts(path):
    connection = sqlite3.connect(path)
    try:
        return {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "hub_program_revisions", "governed_program_promotion_requests",
                "governed_program_promotions", "governed_program_promotion_events",
            )
        }
    finally:
        connection.close()


def test_authorized_request_approval_execution_exact_delta_and_retries(promotion_database):
    before = counts(promotion_database)
    request_row = create_request()
    assert request_row["request_status"] == "PENDING"
    assert create_request()["request_id"] == request_row["request_id"]
    approved = decide(request_row["request_id"])
    assert approved["request_status"] == "APPROVED"
    assert decide(request_row["request_id"])["request_status"] == "APPROVED"
    result = execute(request_row["request_id"])
    assert result["governance_state"] == "GOVERNED_RECORDED"
    assert execute(request_row["request_id"])["promotion_id"] == result["promotion_id"]
    after = counts(promotion_database)
    assert after["hub_program_revisions"] == before["hub_program_revisions"]
    assert after["governed_program_promotion_requests"] - before["governed_program_promotion_requests"] == 1
    assert after["governed_program_promotions"] - before["governed_program_promotions"] == 1
    assert after["governed_program_promotion_events"] - before["governed_program_promotion_events"] == 3


def test_viewer_admin_without_grant_and_self_approval_fail_without_delta(promotion_database):
    baseline = counts(promotion_database)
    with pytest.raises(promotion.PromotionForbidden):
        create_request(actor="viewer", role="Viewer")
    assert counts(promotion_database) == baseline
    request_row = create_request()
    after_request = counts(promotion_database)
    with pytest.raises(promotion.PromotionForbidden):
        decide(request_row["request_id"], actor="admin", role="Admin")
    with pytest.raises(promotion.PromotionForbidden):
        decide(request_row["request_id"], actor="requester", role="Trustee")
    assert counts(promotion_database) == after_request


@pytest.mark.parametrize("change", [
    {"firm_id": "FIRM-B"}, {"owner_id": "owner-b"}, {"workspace_id": "WS-B"},
    {"program_id": "PRG-B"}, {"revision_id": "MISSING"}, {"trust_id": "TR-B"},
])
def test_scope_revision_and_trust_mismatches_fail_closed(promotion_database, change):
    before = counts(promotion_database)
    with pytest.raises(promotion.PromotionError):
        create_request(**change)
    assert counts(promotion_database) == before


def test_rejection_is_terminal_and_execution_fails_closed(promotion_database):
    request_row = create_request(revision_id="REV-A2")
    rejected = promotion.reject_promotion_request(
        request_id=request_row["request_id"], actor="approver", role="Trustee",
        reason="Not approved", firm_id="FIRM-A", owner_id="owner-a",
        workspace_id="WS-A", program_id="PRG-A",
        trust_authorization_check=allow_trust_a,
    )
    assert rejected["request_status"] == "REJECTED"
    before = counts(promotion_database)
    with pytest.raises(promotion.PromotionConflict):
        execute(request_row["request_id"])
    assert counts(promotion_database) == before


def test_conflicting_second_target_is_denied(promotion_database):
    create_request()
    before = counts(promotion_database)
    with pytest.raises(promotion.PromotionConflict):
        create_request(trust_id="TR-C", trust_authorization_check=lambda _: True)
    assert counts(promotion_database) == before


def test_events_and_destination_are_immutable(promotion_database):
    request_row = create_request()
    decide(request_row["request_id"])
    result = execute(request_row["request_id"])
    connection = sqlite3.connect(promotion_database)
    with pytest.raises(sqlite3.IntegrityError, match="append_only"):
        connection.execute("UPDATE governed_program_promotion_events SET reason='changed'")
    with pytest.raises(sqlite3.IntegrityError, match="immutable_record"):
        connection.execute(
            "UPDATE governed_program_promotions SET executed_by='changed' WHERE promotion_id=?",
            (result["promotion_id"],),
        )
    connection.close()


def test_concurrent_execution_produces_one_destination_and_event(promotion_database):
    request_row = create_request()
    decide(request_row["request_id"])
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: execute(request_row["request_id"]), range(2)))
    assert results[0]["promotion_id"] == results[1]["promotion_id"]
    state = counts(promotion_database)
    assert state["governed_program_promotions"] == 1
    assert state["governed_program_promotion_events"] == 3


def test_registered_routes_security_order_and_no_direct_route_sql():
    for endpoint in (
        "workspace_program_promotion", "workspace_program_promotion_request",
        "workspace_program_promotion_approve", "workspace_program_promotion_reject",
        "workspace_program_promotion_execute", "workspace_program_promotion_result",
    ):
        assert f'def {endpoint}' in APP_SOURCE
    route_block = APP_SOURCE[
        APP_SOURCE.index("def _p07_actor_context"):
        APP_SOURCE.index('@app.route("/workspaces/<workspace_id>/edit"')
    ]
    assert "validate_csrf_token()" in route_block
    assert "request.form.keys()" in route_block
    assert "INSERT INTO" not in route_block
    assert "UPDATE governed_" not in route_block
    assert '"workspace_program_promotion": {"Admin", "Trustee", "Viewer"}' in APP_SOURCE
    assert '"workspace_program_promotion_execute": {"Admin", "Trustee"}' in APP_SOURCE


def test_templates_preserve_p06_and_program_detail_seven_token_contract():
    assert DETAIL.count('value="{{ wtf_csrf_token() }}"') == 7
    assert "Open Governed Promotion Status" in DETAIL
    for phrase in (
        "CURRENT state", "attribution, not verification", "Viewer access is read-only",
        "GOVERNED_RECORDED", "establish legal validity", "P08 state",
        "P06 remains preparation only",
    ):
        assert phrase in PROMOTION_TEMPLATE
    assert "workspace_program_handoff.html" not in APP_SOURCE[
        APP_SOURCE.index("def _p07_actor_context"):
        APP_SOURCE.index('@app.route("/workspaces/<workspace_id>/edit"')
    ]
