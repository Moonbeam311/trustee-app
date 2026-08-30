import inspect
import sqlite3

import pytest

import database.db as database_db
import services.services_fiduciary_authority as fiduciary
from database.migrations_governed_program_promotion import apply_governed_program_promotion_schema


@pytest.fixture()
def fiduciary_database(monkeypatch, tmp_path):
    path = tmp_path / "fiduciary-authority.db"
    connection = sqlite3.connect(path)
    connection.execute(
        """CREATE TABLE fiduciaries (
            fiduciary_id TEXT PRIMARY KEY, full_name TEXT, role_title TEXT,
            authority_scope TEXT, trust_id TEXT, appointment_date TEXT,
            effective_date TEXT, status TEXT, notes TEXT, firm_id TEXT
        )"""
    )
    connection.executemany(
        """INSERT INTO fiduciaries VALUES (?,?,?,?,?,?,?,?,?,?)""",
        [
            ("FID-001", "Alex Record", "Trustee", "Manage recorded trust administration", "TR-A", "2026-01-01", "2026-01-02", "Active", "Evidence only", "FIRM-A"),
            ("FID-002", "Blair Missing", "Successor Trustee", None, "TR-A", None, None, "Active", None, "FIRM-A"),
            ("FID-003", "Casey Inactive", "Trustee", "Historical scope", "TR-B", None, None, "Revoked", None, "FIRM-A"),
            ("FID-004", "Dana Other", "Trustee", "Other-firm scope", "TR-A", None, None, "Active", None, "FIRM-B"),
        ],
    )
    connection.commit()
    connection.close()
    active_firm = {"id": "FIRM-A"}
    monkeypatch.setattr(database_db, "DB_PATH", path)
    monkeypatch.setattr(database_db, "get_current_firm_id", lambda: active_firm["id"])
    return path, active_firm


def allow_all(_fiduciary_id, _trust_id):
    return True


def snapshot(path):
    connection = sqlite3.connect(path)
    try:
        return connection.execute(
            "SELECT * FROM fiduciaries ORDER BY fiduciary_id"
        ).fetchall()
    finally:
        connection.close()


def test_same_firm_read_missing_cross_firm_and_compatibility(fiduciary_database):
    path, _active_firm = fiduciary_database
    before = snapshot(path)
    record = fiduciary.get_fiduciary_by_id("FID-001", authorization_check=allow_all)
    assert record["full_name"] == "Alex Record"
    assert record["role_title"] == "Trustee"
    assert fiduciary.get_fiduciary_by_id("FID-999", authorization_check=allow_all) is None
    assert fiduciary.get_fiduciary_by_id("FID-004", authorization_check=allow_all) is None
    assert [row["fiduciary_id"] for row in fiduciary.list_fiduciaries(authorization_check=allow_all)] == ["FID-001", "FID-002", "FID-003"]
    assert snapshot(path) == before


def test_trust_scope_and_authorization_are_independent(fiduciary_database):
    _path, _active_firm = fiduciary_database
    assert [row["fiduciary_id"] for row in fiduciary.list_fiduciaries_for_trust("TR-A", authorization_check=allow_all)] == ["FID-001", "FID-002"]
    assert [row["fiduciary_id"] for row in fiduciary.list_fiduciaries_for_trust("TR-B", authorization_check=allow_all)] == ["FID-003"]
    gate = lambda fiduciary_id, trust_id: fiduciary_id == "FID-001" and trust_id == "TR-A"
    assert fiduciary.get_fiduciary_by_id("FID-001", authorization_check=gate)
    assert fiduciary.get_fiduciary_by_id("FID-002", authorization_check=gate) is None
    with pytest.raises(fiduciary.FiduciaryAuthorityContractError, match="authorization"):
        fiduciary.list_fiduciaries(authorization_check=None)


def test_authority_scope_is_evidence_not_legal_or_system_authority(fiduciary_database):
    decision = fiduciary.evaluate_authority_evidence(
        "FID-001", trust_id="TR-A", capability="approve transfer", authorization_check=allow_all
    )
    assert decision["authority_evidence_state"] == "recorded"
    assert decision["recorded_authority_scope"] == "Manage recorded trust administration"
    assert decision["capability_state"] == "unresolved"
    assert decision["acceptance_state"] == "not_documented"
    assert decision["system_permission_granted"] is False


def test_missing_scope_inactive_and_wrong_trust_remain_unresolved(fiduciary_database):
    missing_scope = fiduciary.evaluate_authority_evidence("FID-002", trust_id="TR-A", authorization_check=allow_all)
    assert missing_scope["authority_evidence_state"] == "unresolved"
    assert missing_scope["scope_state"] == "unresolved"
    inactive = fiduciary.evaluate_authority_evidence("FID-003", trust_id="TR-B", authorization_check=allow_all)
    assert inactive["recorded_status"] == "Revoked"
    assert inactive["authority_evidence_state"] == "unresolved"
    wrong_trust = fiduciary.evaluate_authority_evidence("FID-001", trust_id="TR-B", authorization_check=allow_all)
    assert wrong_trust["record_state"] == "missing_or_not_visible"
    assert wrong_trust["system_permission_granted"] is False


def test_public_contract_contains_no_write_or_permission_mutation():
    public = {
        name for name, value in inspect.getmembers(fiduciary, inspect.isfunction)
        if not name.startswith("_")
    }
    assert public == {"get_fiduciary_by_id", "list_fiduciaries", "list_fiduciaries_for_trust", "evaluate_authority_evidence", "resolve_promotion_approval_capability"}
    assert not any(token in name for name in public for token in ("create", "update", "delete", "grant", "transition"))


def test_structured_p07_capability_is_same_firm_same_trust_and_event_derived(
    fiduciary_database,
):
    path, active_firm = fiduciary_database
    apply_governed_program_promotion_schema(path)
    connection = sqlite3.connect(path)
    connection.execute(
        """INSERT INTO fiduciary_authority_capabilities VALUES
           (?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("AUTH-1", "FIRM-A", "TR-A", "FID-001", "approver", fiduciary.PROMOTION_APPROVAL_CAPABILITY,
         "Recorded appointment", "SRC-1", "2026-01-01T00:00:00+00:00", None, "registrar", "2026-01-01T00:00:00+00:00"),
    )
    connection.execute(
        "INSERT INTO fiduciary_authority_capability_events VALUES (?,?,?,?,?,?,?)",
        ("AE-1", "AUTH-1", "GRANTED", "registrar", "Recorded grant", "2026-01-01T00:00:00+00:00", "grant-1"),
    )
    connection.commit()
    connection.close()
    assert fiduciary.resolve_promotion_approval_capability(
        "approver", firm_id="FIRM-A", trust_id="TR-A"
    )["authority_grant_id"] == "AUTH-1"
    assert fiduciary.resolve_promotion_approval_capability(
        "approver", firm_id="FIRM-A", trust_id="TR-B"
    ) is None
    active_firm["id"] = "FIRM-B"
    assert fiduciary.resolve_promotion_approval_capability(
        "approver", firm_id="FIRM-B", trust_id="TR-A"
    ) is None


def test_revoked_p07_capability_fails_closed(fiduciary_database):
    path, _ = fiduciary_database
    apply_governed_program_promotion_schema(path)
    connection = sqlite3.connect(path)
    connection.execute(
        "INSERT INTO fiduciary_authority_capabilities VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        ("AUTH-2", "FIRM-A", "TR-A", "FID-001", "approver", fiduciary.PROMOTION_APPROVAL_CAPABILITY,
         "Recorded appointment", "SRC-2", "2026-01-01T00:00:00+00:00", None, "registrar", "2026-01-01T00:00:00+00:00"),
    )
    connection.executemany(
        "INSERT INTO fiduciary_authority_capability_events VALUES (?,?,?,?,?,?,?)",
        [("AE-2", "AUTH-2", "GRANTED", "registrar", "Grant", "2026-01-01T00:00:00+00:00", "grant-2"),
         ("AE-3", "AUTH-2", "REVOKED", "registrar", "Revoked", "2026-02-01T00:00:00+00:00", "revoke-2")],
    )
    connection.commit()
    connection.close()
    assert fiduciary.resolve_promotion_approval_capability(
        "approver", firm_id="FIRM-A", trust_id="TR-A"
    ) is None
