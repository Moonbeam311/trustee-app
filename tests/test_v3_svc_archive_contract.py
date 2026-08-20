import sqlite3

import database.db as db
import services.services_account_asset_contract as aa_contract
import services.services_archive_contract as contract
import services.services_document_contract as document_contract
import services.services_execution_contract as execution_contract
import services.services_fiduciary_authority as fiduciary_contract
import services.services_trust_contract as trust_contract


def _database(tmp_path, monkeypatch):
    path = tmp_path / "archive-contract.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    monkeypatch.setattr(db, "get_current_firm_id", lambda: "FIRM-A")
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE trusts (trust_id TEXT PRIMARY KEY, trust_name TEXT, firm_id TEXT);
        CREATE TABLE transfers (
          id INTEGER PRIMARY KEY, trust_id TEXT, transfer_id TEXT UNIQUE, firm_id TEXT,
          status TEXT, asset_name TEXT, transfer_type TEXT, assignment_confirmed INTEGER,
          trustee_decision TEXT, control_change_status TEXT, records_complete INTEGER,
          external_verified INTEGER);
        CREATE TABLE transfer_archive_handoff (
          id INTEGER PRIMARY KEY, handoff_id TEXT UNIQUE, transfer_id TEXT, trust_id TEXT,
          firm_id TEXT, archive_status TEXT, custody_classification TEXT, seal_reference TEXT,
          handoff_by TEXT, handoff_capacity TEXT, ledger_verified TEXT, minute_verified TEXT,
          finalization_verified TEXT, archive_notes TEXT, created_at TEXT, updated_at TEXT);
        CREATE TABLE transfer_archive_handoff_corrections (
          id INTEGER PRIMARY KEY, correction_id TEXT UNIQUE, handoff_id TEXT, transfer_id TEXT,
          trust_id TEXT, firm_id TEXT, corrected_archive_status TEXT,
          corrected_custody_classification TEXT, corrected_seal_reference TEXT,
          corrected_handoff_capacity TEXT, corrected_archive_notes TEXT, correction_reason TEXT,
          corrected_by TEXT, correction_capacity TEXT, created_at TEXT, updated_at TEXT);
        CREATE TABLE archive_export_history (
          id INTEGER PRIMARY KEY, export_id TEXT UNIQUE, export_type TEXT, transfer_id TEXT,
          trust_id TEXT, firm_id TEXT, generated_by TEXT, generated_at TEXT, export_scope TEXT,
          export_hash TEXT, filename TEXT, route_path TEXT, created_at TEXT);
        INSERT INTO trusts VALUES ('TR-A','Alpha','FIRM-A'), ('TR-X','Other','FIRM-X');
        INSERT INTO transfers VALUES
          (1,'TR-A','TX-A','FIRM-A','draft','Asset','assignment',1,'accepted','recorded',1,1),
          (2,'TR-X','TX-X','FIRM-X','draft','Other','assignment',1,'accepted','recorded',1,1),
          (3,'TR-A','TX-W','FIRM-X','draft','Wrong','assignment',1,'accepted','recorded',1,1);
        INSERT INTO transfer_archive_handoff VALUES
          (1,'HO-A','TX-A','TR-A','FIRM-A','handoff_prepared','internal_record','SEAL-A','admin','fiduciary','yes','yes','yes','note','2026-08-20T10:00:00',NULL),
          (2,'HO-X','TX-X','TR-X','FIRM-X','handoff_prepared','internal_record','SEAL-X','other','fiduciary','yes','yes','yes',NULL,'2026-08-20T10:00:00',NULL),
          (3,'HO-W','TX-W','TR-A','FIRM-X','handoff_prepared','internal_record','SEAL-W','other','fiduciary','yes','yes','yes',NULL,'2026-08-20T10:00:00',NULL);
        INSERT INTO transfer_archive_handoff_corrections VALUES
          (1,'COR-A','HO-A','TX-A','TR-A','FIRM-A','archived','controlled','SEAL-B','fiduciary','corrected','clarification','admin','fiduciary','2026-08-20T11:00:00',NULL);
        INSERT INTO archive_export_history VALUES
          (1,'EXP-A','ZIP','TX-A','TR-A','FIRM-A','admin','2026-08-20T12:00:00','Transfer Archive Handoff Export Package','abc123','archive_TX-A.zip','/export','2026-08-20T12:00:00');
    """)
    connection.commit()
    connection.close()
    return path


def _snapshot(path):
    connection = sqlite3.connect(path)
    try:
        return {
            table: connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in (
                "transfer_archive_handoff",
                "transfer_archive_handoff_corrections",
                "archive_export_history",
                "transfers",
            )
        }
    finally:
        connection.close()


def allow(_trust_id):
    return True


def test_same_firm_descriptor_reads_only_recorded_items(tmp_path, monkeypatch):
    path = _database(tmp_path, monkeypatch)
    before = _snapshot(path)
    descriptor = contract.describe_transfer_archive_package(
        "TX-A", "TR-A", authorization_check=allow, handoff_id="HO-A"
    )
    assert descriptor["package_id"] == "HO-A"
    assert [item["item_id"] for item in descriptor["items"]] == ["HO-A", "COR-A", "EXP-A"]
    assert descriptor["integrity"]["recorded_hashes"] == [{
        "export_id": "EXP-A", "hash_value": "abc123",
        "hash_semantics": "recorded_export_hash", "verified_by_descriptor": False,
    }]
    assert descriptor["finalization"] == {
        "recorded_status": "handoff_prepared",
        "semantics": "handoff_state_not_package_certification",
        "certified_by_descriptor": False,
    }
    assert all(value is False for value in descriptor["boundaries"].values())
    assert _snapshot(path) == before
    assert list(tmp_path.iterdir()) == [path]


def test_missing_cross_firm_and_source_mismatch_are_not_exposed(tmp_path, monkeypatch):
    _database(tmp_path, monkeypatch)
    assert contract.describe_transfer_archive_package(
        "missing", "TR-A", authorization_check=allow
    ) is None
    assert contract.describe_transfer_archive_package(
        "TX-X", "TR-X", authorization_check=allow
    ) is None
    assert contract.describe_transfer_archive_package(
        "TX-A", "TR-A", authorization_check=allow, handoff_id="HO-X"
    ) is None
    assert contract.describe_transfer_archive_package(
        "TX-W", "TR-A", authorization_check=allow, handoff_id="HO-W"
    ) is None


def test_list_is_exactly_firm_and_trust_scoped(tmp_path, monkeypatch):
    _database(tmp_path, monkeypatch)
    rows = contract.list_transfer_archive_packages("TR-A", authorization_check=allow)
    assert [row["package_id"] for row in rows] == ["HO-A"]
    assert contract.list_transfer_archive_packages("TR-X", authorization_check=allow) == []


def test_authorization_required_and_prior_contracts_remain_compatible(tmp_path, monkeypatch):
    _database(tmp_path, monkeypatch)
    try:
        contract.describe_transfer_archive_package("TX-A", "TR-A", authorization_check=None)
        assert False, "explicit authorization must be required"
    except trust_contract.TrustReadContractError:
        pass
    assert callable(trust_contract.get_trust_by_id)
    assert callable(fiduciary_contract.evaluate_authority_evidence)
    assert callable(aa_contract.aggregate_trust_inventory)
    assert callable(document_contract.produce_trust_document_context)
    assert callable(execution_contract.get_execution_session)
