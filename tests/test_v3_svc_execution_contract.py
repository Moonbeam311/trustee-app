import sqlite3

import database.db as db
import services.services_account_asset_contract as aa_contract
import services.services_document_contract as document_contract
import services.services_execution_contract as contract
import services.services_fiduciary_authority as fiduciary_contract
import services.services_trust_contract as trust_contract


def _database(tmp_path, monkeypatch):
    path = tmp_path / "execution-contract.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    monkeypatch.setattr(db, "get_current_firm_id", lambda: "FIRM-A")
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE trusts (trust_id TEXT PRIMARY KEY, trust_name TEXT, firm_id TEXT);
        CREATE TABLE institutional_execution_sessions (
          execution_id TEXT PRIMARY KEY, object_type TEXT, object_id TEXT, matter_id TEXT,
          trust_id TEXT, document_type TEXT, document_title TEXT, ceremony_status TEXT,
          current_step TEXT, execution_date TEXT, execution_location TEXT, created_by TEXT,
          created_at TEXT, updated_at TEXT, archive_freeze_status TEXT, final_hash TEXT, notes TEXT);
        CREATE TABLE institutional_signature_records (
          signature_id TEXT PRIMARY KEY, execution_id TEXT, signature_status TEXT);
        CREATE TABLE institutional_witness_notary_records (
          record_id TEXT PRIMARY KEY, execution_id TEXT, verification_status TEXT);
        CREATE TABLE institutional_seal_ledger (
          seal_event_id TEXT PRIMARY KEY, execution_id TEXT, seal_status TEXT);
        CREATE TABLE institutional_execution_ledger (
          ledger_id TEXT PRIMARY KEY, execution_id TEXT, event_sequence INTEGER, event_type TEXT, provenance_hash TEXT);
        CREATE TABLE institutional_archive_freezes (
          freeze_id TEXT PRIMARY KEY, execution_id TEXT, archive_status TEXT);
        CREATE TABLE transfers (
          id INTEGER PRIMARY KEY, trust_id TEXT, transfer_id TEXT UNIQUE, firm_id TEXT,
          status TEXT, asset_name TEXT, transfer_type TEXT, assignment_confirmed INTEGER,
          trustee_decision TEXT, control_change_status TEXT, records_complete INTEGER,
          external_verified INTEGER);
        INSERT INTO trusts VALUES ('TR-A','Alpha','FIRM-A'), ('TR-X','Other','FIRM-X');
        INSERT INTO institutional_execution_sessions VALUES
          ('EX-A',NULL,NULL,NULL,'TR-A',NULL,NULL,'in_progress','signatures',NULL,NULL,NULL,NULL,NULL,'not_frozen',NULL,NULL),
          ('EX-X',NULL,NULL,NULL,'TR-X',NULL,NULL,'draft','prepared',NULL,NULL,NULL,NULL,NULL,'not_frozen',NULL,NULL);
        INSERT INTO institutional_signature_records VALUES ('SIG-A','EX-A','pending');
        INSERT INTO transfers VALUES
          (1,'TR-A','TX-A','FIRM-A','draft','Asset','assignment',1,'accepted','recorded',1,0),
          (2,'TR-X','TX-X','FIRM-X','draft','Other','assignment',1,'accepted','recorded',1,1),
          (3,'TR-A','TX-W','FIRM-X','draft','Wrong Firm','assignment',1,'accepted','recorded',1,1);
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
                "institutional_execution_sessions", "institutional_signature_records",
                "institutional_witness_notary_records", "institutional_seal_ledger",
                "institutional_execution_ledger", "institutional_archive_freezes", "transfers"
            )
        }
    finally:
        connection.close()


def allow(_trust_id):
    return True


def test_same_firm_reads_and_recorded_orchestration(tmp_path, monkeypatch):
    path = _database(tmp_path, monkeypatch)
    before = _snapshot(path)
    session = contract.get_execution_session("EX-A", authorization_check=allow)
    transfer = contract.get_transfer("TX-A", "TR-A", authorization_check=allow)
    context = contract.build_orchestration_context(
        "TR-A", execution_id="EX-A", transfer_id="TX-A", authorization_check=allow
    )
    assert session["session"]["current_step"] == "signatures"
    assert transfer["transfer_id"] == "TX-A"
    assert context["execution"]["blockers"] == [{"code": "pending_signature", "record_id": "SIG-A"}]
    assert context["transfer"]["pending_requirements"] == [
        {"code": "missing_external_verification", "source_field": "external_verified"}
    ]
    assert context["recommendation_executed"] is False
    assert _snapshot(path) == before


def test_missing_cross_firm_and_mismatched_scope_fail_closed(tmp_path, monkeypatch):
    _database(tmp_path, monkeypatch)
    assert contract.get_execution_session("missing", authorization_check=allow) is None
    assert contract.get_execution_session("EX-X", authorization_check=allow) is None
    assert contract.get_transfer("missing", "TR-A", authorization_check=allow) is None
    assert contract.get_transfer("TX-X", "TR-X", authorization_check=allow) is None
    assert contract.get_transfer("TX-W", "TR-A", authorization_check=allow) is None
    assert contract.build_orchestration_context(
        "TR-X", execution_id="EX-A", authorization_check=allow
    ) is None


def test_authorization_is_required_and_no_write_api_is_exposed(tmp_path, monkeypatch):
    _database(tmp_path, monkeypatch)
    try:
        contract.get_execution_session("EX-A", authorization_check=None)
        assert False, "explicit authorization must be required"
    except trust_contract.TrustReadContractError:
        pass
    public = {name for name in dir(contract) if not name.startswith("_")}
    assert not public.intersection({"create", "update", "advance", "finalize", "sign", "archive", "recover"})


def test_prior_contract_surfaces_remain_independent_and_callable():
    assert callable(trust_contract.get_trust_by_id)
    assert callable(fiduciary_contract.evaluate_authority_evidence)
    assert callable(aa_contract.aggregate_trust_inventory)
    assert callable(document_contract.produce_trust_document_context)
