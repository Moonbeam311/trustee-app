import inspect
import sqlite3

import pytest

import database.db as database_db
import services.services_trust_contract as trust_contract


@pytest.fixture()
def trust_db(monkeypatch, tmp_path):
    path = tmp_path / "trust-read-contract.db"
    connection = sqlite3.connect(path)
    connection.execute(
        """CREATE TABLE trusts (
            trust_id TEXT PRIMARY KEY,
            trust_name TEXT NOT NULL,
            status TEXT,
            firm_id TEXT NOT NULL
        )"""
    )
    connection.executemany(
        "INSERT INTO trusts (trust_id,trust_name,status,firm_id) VALUES (?,?,?,?)",
        [
            ("TR-ACTIVE", "Active Trust", "Active", "FIRM-A"),
            ("TR-DRAFT", "Draft Trust", "Draft", "FIRM-A"),
            ("TR-OTHER", "Other Firm Trust", "Active", "FIRM-B"),
        ],
    )
    connection.commit()
    connection.close()

    active_firm = {"id": "FIRM-A"}
    monkeypatch.setattr(database_db, "DB_PATH", path)
    monkeypatch.setattr(
        database_db, "get_current_firm_id", lambda: active_firm["id"]
    )
    return path, active_firm


def _allow_all(_trust_id):
    return True


def _snapshot(path):
    connection = sqlite3.connect(path)
    try:
        schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='trusts'"
        ).fetchone()[0]
        rows = connection.execute(
            "SELECT trust_id,trust_name,status,firm_id FROM trusts ORDER BY trust_id"
        ).fetchall()
        return schema, rows
    finally:
        connection.close()


def test_same_firm_missing_draft_and_existing_caller_pattern(trust_db):
    path, _active_firm = trust_db
    before = _snapshot(path)

    trust = trust_contract.get_trust_by_id(
        "TR-ACTIVE", authorization_check=_allow_all
    )
    assert trust["trust_name"] == "Active Trust"
    assert trust_contract.get_trust_by_id(
        "TR-MISSING", authorization_check=_allow_all
    ) is None
    assert trust_contract.get_trust_by_id(
        "TR-DRAFT", authorization_check=_allow_all
    )["status"] == "Draft"

    allowed_ids = {"TR-ACTIVE"}
    caller_gate = lambda trust_id: trust_id in allowed_ids
    assert trust_contract.get_trust_by_id(
        "TR-ACTIVE", authorization_check=caller_gate
    )["trust_id"] == "TR-ACTIVE"
    assert trust_contract.get_trust_by_id(
        "TR-DRAFT", authorization_check=caller_gate
    ) is None
    assert _snapshot(path) == before


def test_cross_firm_and_list_are_fail_closed_and_firm_scoped(trust_db):
    _path, active_firm = trust_db
    assert trust_contract.get_trust_by_id(
        "TR-OTHER", authorization_check=_allow_all
    ) is None
    assert [
        row["trust_id"]
        for row in trust_contract.list_trusts(authorization_check=_allow_all)
    ] == ["TR-ACTIVE", "TR-DRAFT"]

    active_firm["id"] = "FIRM-B"
    assert trust_contract.get_trust_by_id(
        "TR-ACTIVE", authorization_check=_allow_all
    ) is None
    assert [
        row["trust_id"]
        for row in trust_contract.list_trusts(authorization_check=_allow_all)
    ] == ["TR-OTHER"]


def test_authorization_is_required_and_denial_does_not_disclose(trust_db):
    with pytest.raises(trust_contract.TrustReadContractError, match="authorization"):
        trust_contract.get_trust_by_id("TR-ACTIVE", authorization_check=None)
    with pytest.raises(trust_contract.TrustReadContractError, match="authorization"):
        trust_contract.list_trusts(authorization_check=None)
    assert trust_contract.get_trust_by_id(
        "TR-ACTIVE", authorization_check=lambda _trust_id: False
    ) is None
    assert not trust_contract.trust_is_accessible(
        "TR-ACTIVE", authorization_check=lambda _trust_id: False
    )


def test_legacy_unscoped_schema_fails_without_migration(monkeypatch, tmp_path):
    path = tmp_path / "legacy-unscoped.db"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE trusts (trust_id TEXT PRIMARY KEY)")
    connection.execute("INSERT INTO trusts (trust_id) VALUES ('TR-LEGACY')")
    connection.commit()
    connection.close()
    monkeypatch.setattr(database_db, "DB_PATH", path)

    with pytest.raises(
        trust_contract.TrustReadContractError, match="firm-scoped trusts schema"
    ):
        trust_contract.get_trust_by_id(
            "TR-LEGACY", authorization_check=_allow_all
        )

    connection = sqlite3.connect(path)
    try:
        columns = [
            row[1] for row in connection.execute("PRAGMA table_info(trusts)").fetchall()
        ]
    finally:
        connection.close()
    assert columns == ["trust_id"]


def test_contract_exports_no_trust_write_boundary():
    public_functions = {
        name
        for name, value in inspect.getmembers(trust_contract, inspect.isfunction)
        if not name.startswith("_")
    }
    assert public_functions == {
        "get_trust_by_id",
        "list_trusts",
        "trust_is_accessible",
    }
    assert not any(
        token in name
        for name in public_functions
        for token in ("create", "update", "delete", "transition")
    )
