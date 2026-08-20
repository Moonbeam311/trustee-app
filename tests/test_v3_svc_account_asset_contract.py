import inspect
import sqlite3

import database.db as database_db
import services.services_account_asset_contract as contract


def _allow_all(_trust_id):
    return True


def _snapshot(path):
    connection = sqlite3.connect(path)
    try:
        return {
            table: connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in ("trusts", "accounts", "properties", "ledger_entries")
        }
    finally:
        connection.close()


def test_account_asset_read_aggregation(monkeypatch, tmp_path):
    path = tmp_path / "account-asset-contract.db"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE trusts (trust_id TEXT PRIMARY KEY, trust_name TEXT, status TEXT, firm_id TEXT)")
    connection.execute("""CREATE TABLE accounts (
        account_id TEXT PRIMARY KEY, trust_id TEXT, property_id TEXT,
        account_type TEXT, institution TEXT, account_label TEXT,
        masked_number TEXT, purpose TEXT, firm_id TEXT,
        password TEXT, pin TEXT, token TEXT
    )""")
    connection.execute("""CREATE TABLE properties (
        property_id TEXT PRIMARY KEY, trust_id TEXT, property_name TEXT,
        property_type TEXT, address_or_identifier TEXT, acquisition_date TEXT,
        status TEXT, asset_class TEXT, asset_subtype TEXT, responsible_party TEXT,
        custodian TEXT, continuity_classification TEXT,
        custody_classification TEXT, continuity_priority TEXT, firm_id TEXT
    )""")
    connection.execute("CREATE TABLE ledger_entries (entry_id TEXT PRIMARY KEY, trust_id TEXT, amount TEXT)")
    connection.executemany("INSERT INTO trusts VALUES (?,?,?,?)", [
        ("TR-A", "Trust A", "Active", "FIRM-A"),
        ("TR-B", "Trust B", "Active", "FIRM-A"),
        ("TR-X", "Trust X", "Active", "FIRM-B"),
    ])
    connection.executemany("INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [
        ("AC-A", "TR-A", "PR-A", "deposit", "Bank", "Operating", "***1234", "operations", "FIRM-A", "secret", "1234", "token"),
        ("AC-B", "TR-B", None, "deposit", "Bank", "Other Trust", "***2222", None, "FIRM-A", None, None, None),
        ("AC-X", "TR-A", None, "deposit", "Other", "Other Firm", "***9999", None, "FIRM-B", None, None, None),
    ])
    connection.executemany("INSERT INTO properties VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
        ("PR-A", "TR-A", "Residence", "real_property", "Parcel-1", None, "Active", "real_estate", None, "Steward", "Custodian", "family_continuity", "documented_custody", "high", "FIRM-A"),
        ("PR-B", "TR-B", "Other Asset", "personal_property", None, None, "Active", None, None, None, None, None, None, None, "FIRM-A"),
        ("PR-X", "TR-A", "Other Firm Asset", "real_property", None, None, "Active", None, None, None, None, None, None, None, "FIRM-B"),
    ])
    connection.execute("INSERT INTO ledger_entries VALUES ('LE-1','TR-A','500')")
    connection.commit()
    connection.close()

    active_firm = {"id": "FIRM-A"}
    monkeypatch.setattr(database_db, "DB_PATH", path)
    monkeypatch.setattr(database_db, "get_current_firm_id", lambda: active_firm["id"])
    before = _snapshot(path)

    accounts = contract.list_trust_accounts("TR-A", authorization_check=_allow_all)
    assets = contract.list_trust_assets("TR-A", authorization_check=_allow_all)
    assert [row["account_id"] for row in accounts] == ["AC-A"]
    assert [row["property_id"] for row in assets] == ["PR-A"]
    assert accounts[0]["masked_number"] == "***1234"
    assert not {"password", "pin", "token"}.intersection(accounts[0])
    assert assets[0]["continuity_classification"] == "family_continuity"
    assert assets[0]["source"] == "properties"

    assert contract.get_trust_account("AC-A", "TR-A", authorization_check=_allow_all)
    assert contract.get_trust_account("AC-MISSING", "TR-A", authorization_check=_allow_all) is None
    assert contract.get_trust_account("AC-B", "TR-A", authorization_check=_allow_all) is None
    assert contract.get_trust_account("AC-X", "TR-A", authorization_check=_allow_all) is None
    assert contract.get_trust_asset("PR-A", "TR-A", authorization_check=_allow_all)
    assert contract.get_trust_asset("PR-MISSING", "TR-A", authorization_check=_allow_all) is None
    assert contract.get_trust_asset("PR-B", "TR-A", authorization_check=_allow_all) is None
    assert contract.get_trust_asset("PR-X", "TR-A", authorization_check=_allow_all) is None

    aggregate = contract.aggregate_trust_inventory("TR-A", authorization_check=_allow_all)
    assert aggregate["trust"]["trust_name"] == "Trust A"
    assert aggregate["summary"] == {
        "account_count": 1,
        "asset_count": 1,
        "unresolved_account_property_references": 0,
        "scope": "active_firm_and_trust",
        "completeness": "accounts_and_properties_only",
    }
    assert "ledger_entries" in aggregate["excluded_sources"]

    active_firm["id"] = "FIRM-B"
    assert contract.aggregate_trust_inventory("TR-A", authorization_check=_allow_all) is None
    assert _snapshot(path) == before


def test_authorization_denial_and_public_api(monkeypatch, tmp_path):
    assert contract.list_trust_accounts("TR-A", authorization_check=lambda _trust_id: False) == []
    public = {
        name for name, value in inspect.getmembers(contract, inspect.isfunction)
        if not name.startswith("_")
    }
    assert public == {
        "list_trust_accounts", "get_trust_account", "list_trust_assets",
        "get_trust_asset", "aggregate_trust_inventory",
    }
    assert not any(token in name for name in public for token in ("create", "update", "delete", "link", "post", "seed"))
