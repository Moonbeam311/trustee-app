import sqlite3

import pytest

import database.db as db
from database.migrations_intake_trust_bridge import migrate_intake_trust_bridge
import services.services_governance as governance
import services.services_handoff_read_aggregate as contract
from services.services_intake_trust_bridge import (
    add_continuity_record,
    create_continuity_profile,
)


def allow(_identifier):
    return True


def allow_fiduciary(_identifier, _trust_id):
    return True


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
            table: connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in tables
        }
    finally:
        connection.close()


def _database(tmp_path, monkeypatch):
    path = tmp_path / "handoff-aggregate.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    monkeypatch.setattr(db, "get_current_firm_id", lambda: "FIRM-A")
    monkeypatch.setattr(governance, "get_current_firm_id", lambda: "FIRM-A")
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE trusts (
          trust_id TEXT PRIMARY KEY, trust_name TEXT, short_name TEXT,
          jurisdiction TEXT, effective_date TEXT, trust_type TEXT,
          trust_purpose TEXT, settlor_name TEXT, trustee_name TEXT,
          successor_trustee_name TEXT, beneficiary_name TEXT, status TEXT,
          firm_id TEXT);
        CREATE TABLE fiduciaries (
          fiduciary_id TEXT PRIMARY KEY, full_name TEXT, role_title TEXT,
          authority_scope TEXT, trust_id TEXT, appointment_date TEXT,
          effective_date TEXT, status TEXT, notes TEXT, firm_id TEXT);
        CREATE TABLE accounts (
          account_id TEXT PRIMARY KEY, trust_id TEXT, property_id TEXT,
          account_type TEXT, institution TEXT, account_label TEXT,
          masked_number TEXT, purpose TEXT, firm_id TEXT);
        CREATE TABLE properties (
          property_id TEXT PRIMARY KEY, trust_id TEXT, property_name TEXT,
          property_type TEXT, address_or_identifier TEXT, status TEXT,
          responsible_party TEXT, custodian TEXT, firm_id TEXT);
        CREATE TABLE documents (
          document_id TEXT PRIMARY KEY, trust_id TEXT, property_id TEXT,
          account_id TEXT, document_category TEXT, document_title TEXT,
          notes TEXT, original_filename TEXT, stored_filename TEXT,
          file_path TEXT, firm_id TEXT);
        CREATE TABLE transfers (
          id INTEGER PRIMARY KEY, trust_id TEXT, transfer_id TEXT UNIQUE,
          firm_id TEXT, status TEXT, asset_name TEXT, transfer_type TEXT,
          assignment_confirmed INTEGER, trustee_decision TEXT,
          control_change_status TEXT, records_complete INTEGER,
          external_verified INTEGER);
        CREATE TABLE transfer_archive_handoff (
          id INTEGER PRIMARY KEY, handoff_id TEXT UNIQUE, transfer_id TEXT,
          trust_id TEXT, firm_id TEXT, archive_status TEXT,
          custody_classification TEXT, seal_reference TEXT, handoff_by TEXT,
          handoff_capacity TEXT, created_at TEXT);
        CREATE TABLE transfer_archive_handoff_corrections (
          id INTEGER PRIMARY KEY, correction_id TEXT UNIQUE, handoff_id TEXT,
          transfer_id TEXT, trust_id TEXT, firm_id TEXT,
          corrected_archive_status TEXT, created_at TEXT);
        CREATE TABLE archive_export_history (
          id INTEGER PRIMARY KEY, export_id TEXT UNIQUE, transfer_id TEXT,
          trust_id TEXT, firm_id TEXT, export_hash TEXT, filename TEXT,
          generated_at TEXT);
        INSERT INTO trusts VALUES
          ('TR-A','Alpha Trust','Alpha','NY','2024-01-01','revocable','Family','Settlor','Current Trustee','Successor Trustee','Beneficiary','Active','FIRM-A'),
          ('TR-U','Unlinked Trust','Unlinked','NY','2024-01-01','revocable','Family','Settlor','Current Trustee',NULL,'Beneficiary','Active','FIRM-A'),
          ('TR-X','Other Trust','Other','NY','2024-01-01','revocable','Family','Settlor','Other Trustee','Other Successor','Other','Active','FIRM-X');
        INSERT INTO fiduciaries VALUES
          ('FID-A','Successor Trustee','Successor Trustee','Recorded instrument','TR-A',NULL,NULL,'Active',NULL,'FIRM-A'),
          ('FID-X','Other Fiduciary','Trustee','Other scope','TR-X',NULL,NULL,'Active',NULL,'FIRM-X');
        INSERT INTO properties VALUES
          ('PROP-A','TR-A','Residence','real_property','Address','Active','Current Trustee','Custodian','FIRM-A'),
          ('PROP-X','TR-X','Other','real_property','Other','Active','Other','Other','FIRM-X');
        INSERT INTO accounts VALUES
          ('ACC-A','TR-A','PROP-A','deposit','Bank','Operating','****1234','Administration','FIRM-A'),
          ('ACC-X','TR-X','PROP-X','deposit','Other Bank','Other','****9999','Other','FIRM-X');
        INSERT INTO documents VALUES
          ('DOC-A','TR-A',NULL,NULL,'governance','Trust instrument',NULL,'trust.pdf','trust.pdf','safe/path','FIRM-A'),
          ('DOC-X','TR-X',NULL,NULL,'governance','Other',NULL,'other.pdf','other.pdf','other/path','FIRM-X');
        INSERT INTO transfers VALUES
          (1,'TR-A','TX-A','FIRM-A','draft','Residence','assignment',0,NULL,NULL,0,0),
          (2,'TR-X','TX-X','FIRM-X','draft','Other','assignment',0,NULL,NULL,0,0);
        INSERT INTO transfer_archive_handoff VALUES
          (1,'HO-A','TX-A','TR-A','FIRM-A','prepared','internal','SEAL-A','admin','fiduciary','2026-08-20T10:00:00'),
          (2,'HO-X','TX-X','TR-X','FIRM-X','prepared','internal','SEAL-X','other','fiduciary','2026-08-20T10:00:00');
    """)
    connection.commit()
    connection.close()

    migrate_intake_trust_bridge(path)
    profile_id = create_continuity_profile(
        path, "FIRM-A", "Successor Context", "person", "successor",
        "Trust continuity", "tester", trust_id="TR-A",
    )
    add_continuity_record(path, "continuity_responsibilities", profile_id, "FIRM-A", "tester", {
        "category": "administration", "description": "Administer Trust",
        "current_responsible_party": "Current Trustee",
        "successor_responsible_party": "Successor Trustee",
        "authority_source": "Recorded instrument",
        "supporting_document_reference": "DOC-A",
    })
    add_continuity_record(path, "continuity_digital_accounts", profile_id, "FIRM-A", "tester", {
        "institution_service": "Bank portal", "account_label": "Operating",
        "account_category": "financial administration",
        "login_identifier": "safe-user", "vault_reference": "VAULT-1",
        "recovery_procedure": "Contact custodian", "mfa_method": "hardware key",
        "responsible_party": "Current Trustee",
        "successor_responsible_party": "Successor Trustee",
        "last_verified_date": "2026-08-20",
    })
    add_continuity_record(path, "continuity_receivables", profile_id, "FIRM-A", "tester", {
        "payer_debtor": "Tenant", "description": "Rent",
        "successor_collector": "Successor Trustee",
        "delinquency_instructions": "Review lease",
    })
    add_continuity_record(path, "continuity_payables", profile_id, "FIRM-A", "tester", {
        "creditor_payee": "Insurer", "description": "Premium",
        "successor_responsible_party": "Successor Trustee",
        "continuity_instruction": "Maintain coverage",
    })

    governance.ensure_governance_tables()
    created, directive_id = governance.create_governance_record(
        "directive", {"title": "Preserve Trust", "created_by": "tester"}
    )
    assert created
    related, _ = governance.create_governance_relationship({
        "source_object_type": "Directive", "source_object_id": directive_id,
        "relationship_type": "governs", "target_object_type": "Trust",
        "target_object_id": "TR-A", "created_by": "tester",
    })
    assert related
    return path, profile_id


def _build(path, trust_id="TR-A", **overrides):
    arguments = {
        "db_path": path,
        "trust_authorization_check": allow,
        "continuity_authorization_check": allow,
        "fiduciary_authorization_check": allow_fiduciary,
        "governance_authorization_check": allow,
    }
    arguments.update(overrides)
    return contract.build_trust_successor_handoff_context(trust_id, **arguments)


def test_linked_same_firm_aggregate_composes_canonical_sources_without_mutation(tmp_path, monkeypatch):
    path, profile_id = _database(tmp_path, monkeypatch)
    before = _snapshot(path)
    result = _build(path)
    assert result["aggregate_type"] == "TrustSuccessorHandoffContext"
    assert result["identity"]["successor_trustee"] == "Successor Trustee"
    assert result["fiduciary_authority"]["records"][0]["authority_evidence"]["authority_evidence_state"] == "recorded"
    assert result["fiduciary_authority"]["system_permission_granted"] is False
    assert result["continuity"]["profiles"][0]["continuity_profile_id"] == profile_id
    assert result["accounts_assets"]["summary"] == {
        "account_count": 1, "asset_count": 1,
        "unresolved_account_property_references": 0,
        "scope": "active_firm_and_trust", "completeness": "accounts_and_properties_only",
    }
    assert len(result["continuity"]["profiles"][0]["receivables"]) == 1
    assert len(result["continuity"]["profiles"][0]["payables"]) == 1
    assert result["governance"]["state"] == contract.AVAILABLE
    assert [row["document_id"] for row in result["documents"]["references"]] == ["DOC-A"]
    assert [row["package_id"] for row in result["archive"]["descriptors"]] == ["HO-A"]
    assert result["execution"]["state"] == contract.NOT_APPLICABLE
    assert all(value is False for value in result["boundaries"].values())
    assert result["mutation_performed"] is False
    assert _snapshot(path) == before


def test_unlinked_trust_is_safe_and_does_not_create_profile_or_event(tmp_path, monkeypatch):
    path, _ = _database(tmp_path, monkeypatch)
    before = _snapshot(path)
    result = _build(path, "TR-U")
    assert result["continuity"] == {
        "state": contract.UNLINKED, "relationship_cardinality": "ZERO_OR_MANY",
        "profiles": [], "profile_count": 0,
    }
    assert "no_continuity_profile" in {gap["code"] for gap in result["readiness"]["gaps"]}
    assert _snapshot(path) == before


def test_missing_cross_firm_and_denied_roots_do_not_disclose(tmp_path, monkeypatch):
    path, _ = _database(tmp_path, monkeypatch)
    assert _build(path, "missing") is None
    assert _build(path, "TR-X") is None
    assert _build(path, trust_authorization_check=lambda _trust_id: False) is None


def test_sections_do_not_leak_cross_firm_records(tmp_path, monkeypatch):
    path, _ = _database(tmp_path, monkeypatch)
    result = _build(path)
    serialized = repr(result)
    for prohibited in ("TR-X", "FID-X", "ACC-X", "PROP-X", "DOC-X", "HO-X", "Other Bank"):
        assert prohibited not in serialized


def test_digital_access_is_allowlisted_and_prohibited_secret_fields_never_flow(tmp_path, monkeypatch):
    path, _ = _database(tmp_path, monkeypatch)
    original = contract.get_continuity_profile

    def injected(*args, **kwargs):
        bundle = original(*args, **kwargs)
        bundle["digital_accounts"][0]["password"] = "never-output"
        bundle["digital_accounts"][0]["private_key"] = "never-output"
        bundle["digital_accounts"][0]["security_answer"] = "never-output"
        return bundle

    monkeypatch.setattr(contract, "get_continuity_profile", injected)
    result = _build(path)
    metadata = result["continuity"]["profiles"][0]["digital_access_metadata"][0]
    assert metadata["vault_reference"] == "VAULT-1"
    assert metadata["login_identifier"] == "safe-user"
    assert not {"password", "private_key", "security_answer"} & metadata.keys()
    assert "never-output" not in repr(result)


def test_explicit_domain_authorization_is_required_and_denial_is_safe(tmp_path, monkeypatch):
    path, _ = _database(tmp_path, monkeypatch)
    with pytest.raises(contract.HandoffReadAggregateError):
        _build(path, governance_authorization_check=None)
    denied = _build(path, governance_authorization_check=lambda _trust_id: False)
    assert denied["governance"] == {
        "state": contract.UNRESOLVED, "links": [], "summary": contract.NOT_DOCUMENTED,
    }
    denied_continuity = _build(path, continuity_authorization_check=lambda _profile_id: False)
    assert denied_continuity["continuity"]["state"] == contract.UNLINKED
    denied_fiduciary = _build(path, fiduciary_authorization_check=lambda _fid, _trust: False)
    assert denied_fiduciary["fiduciary_authority"]["state"] == contract.MISSING


def test_optional_execution_context_reports_existing_state_without_advancing_it(tmp_path, monkeypatch):
    path, _ = _database(tmp_path, monkeypatch)
    before = _snapshot(path)
    result = _build(path, transfer_id="TX-A")
    assert result["execution"]["state"] == contract.AVAILABLE
    transfer = result["execution"]["orchestration"]["transfer"]
    assert transfer["readiness_status"] == "blocked"
    assert transfer["mutation_performed"] is False
    assert result["execution"]["orchestration"]["recommendation_executed"] is False
    assert _snapshot(path) == before
