import sqlite3

import pytest

import database.db as database_db
from database.migrations_magc1_wave3 import TABLES, apply_magc1_wave3_schema
import services.services_document_contract as documents
import services.services_execution_contract as execution
import services.services_fiduciary_authority as fiduciary
import services.services_work_learning_authority as authority


@pytest.fixture()
def wave3_database(monkeypatch, tmp_path):
    path = tmp_path / "wave3.db"
    connection = sqlite3.connect(path)
    connection.executescript("""
    CREATE TABLE trusts (trust_id TEXT PRIMARY KEY, firm_id TEXT NOT NULL);
    CREATE TABLE documents (document_id TEXT PRIMARY KEY, trust_id TEXT, status TEXT);
    CREATE TABLE generated_documents (document_id TEXT PRIMARY KEY, trust_id TEXT, firm_id TEXT, status TEXT);
    CREATE TABLE hub_programs (program_id TEXT PRIMARY KEY, workspace_id TEXT, firm_id TEXT, owner_id TEXT);
    CREATE TABLE hub_program_issues (issue_id TEXT PRIMARY KEY, program_id TEXT);
    CREATE TABLE hub_program_authority_claims (claim_id TEXT PRIMARY KEY, program_id TEXT, issue_id TEXT);
    CREATE TABLE hub_program_authority_evidence (evidence_id TEXT PRIMARY KEY, program_id TEXT, claim_id TEXT);
    CREATE TABLE hub_program_authority_verifications (verification_id TEXT PRIMARY KEY, program_id TEXT, claim_id TEXT, evidence_id TEXT);
    CREATE TABLE fiduciaries (fiduciary_id TEXT PRIMARY KEY, firm_id TEXT, trust_id TEXT);
    CREATE TABLE successor_acceptances (acceptance_id TEXT PRIMARY KEY, firm_id TEXT, trust_id TEXT, fiduciary_id TEXT);
    CREATE TABLE fiduciary_authority_capabilities (authority_grant_id TEXT PRIMARY KEY, firm_id TEXT, trust_id TEXT, fiduciary_id TEXT);
    CREATE TABLE properties (property_id TEXT PRIMARY KEY, trust_id TEXT, firm_id TEXT, assignment_confirmed INTEGER);
    CREATE TABLE accounts (account_id TEXT PRIMARY KEY, trust_id TEXT, firm_id TEXT);
    CREATE TABLE transfers (transfer_id TEXT PRIMARY KEY, firm_id TEXT, trust_id TEXT, status TEXT, external_verified INTEGER);
    """)
    connection.execute("INSERT INTO trusts VALUES ('TR-A','FIRM-A')")
    connection.execute("INSERT INTO trusts VALUES ('TR-B','FIRM-B')")
    connection.execute("INSERT INTO documents VALUES ('DOC-A','TR-A','executed')")
    connection.execute("INSERT INTO generated_documents VALUES ('GEN-A','TR-A','FIRM-A','final')")
    connection.execute("INSERT INTO hub_programs VALUES ('PRG-A','WS-A','FIRM-A','OWNER-A')")
    connection.execute("INSERT INTO hub_program_issues VALUES ('ISS-A','PRG-A')")
    connection.execute("INSERT INTO hub_program_authority_claims VALUES ('CLM-A','PRG-A','ISS-A')")
    connection.execute("INSERT INTO hub_program_authority_evidence VALUES ('EVD-A','PRG-A','CLM-A')")
    connection.execute("INSERT INTO hub_program_authority_verifications VALUES ('VER-A','PRG-A','CLM-A','EVD-A')")
    connection.execute("INSERT INTO fiduciaries VALUES ('FID-A','FIRM-A','TR-A')")
    connection.execute("INSERT INTO successor_acceptances VALUES ('ACC-A','FIRM-A','TR-A','FID-A')")
    connection.execute("INSERT INTO fiduciary_authority_capabilities VALUES ('CAP-A','FIRM-A','TR-A','FID-A')")
    connection.execute("INSERT INTO properties VALUES ('PROP-A','TR-A','FIRM-A',1)")
    connection.execute("INSERT INTO accounts VALUES ('ACCT-A','TR-A','FIRM-A')")
    connection.execute("INSERT INTO transfers VALUES ('TX-A','FIRM-A','TR-A','completed',1)")
    connection.commit(); connection.close()
    monkeypatch.setattr(database_db, "DB_PATH", path)
    monkeypatch.setattr(database_db, "get_current_firm_id", lambda: "FIRM-A")
    return path


def _counts(path, tables):
    connection = sqlite3.connect(path)
    try: return {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in tables}
    finally: connection.close()


def test_migration_is_additive_idempotent_empty_and_exact(wave3_database):
    before = _counts(wave3_database, ("documents","hub_program_authority_evidence","fiduciaries","properties","accounts","transfers"))
    assert apply_magc1_wave3_schema(wave3_database)["records_created"] == 0
    assert apply_magc1_wave3_schema(wave3_database)["records_created"] == 0
    assert _counts(wave3_database, TABLES) == {table: 0 for table in TABLES}
    assert _counts(wave3_database, before) == before
    connection = sqlite3.connect(wave3_database)
    names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    connection.close()
    assert set(TABLES).issubset(names)
    assert not {"document_legal_registry","evidence_sufficiency_registry","fiduciary_authority_registry","asset_control_registry"}.intersection(names)


def test_all_wave3_tables_are_append_only(wave3_database):
    apply_magc1_wave3_schema(wave3_database)
    doc_id = documents.record_document_legal_state(firm_id="FIRM-A",trust_id="TR-A",document_object_type="DOCUMENT",document_object_id="DOC-A",legal_state="UNRESOLVED",decision_origin="SYSTEM_SUGGESTED",human_confirmed=False,actor="system",actor_capacity="suggestion")
    suf_id = authority.record_evidence_sufficiency_assessment(program_id="PRG-A",firm_id="FIRM-A",issue_id="ISS-A",claim_id="CLM-A",target_use="RESEARCH",sufficiency_state="UNRESOLVED",decision_origin="SYSTEM_SUGGESTED",human_confirmed=False,actor="system",actor_capacity="suggestion")
    fid_id = fiduciary.record_fiduciary_authority_lifecycle(firm_id="FIRM-A",trust_id="TR-A",fiduciary_id="FID-A",authority_state="UNRESOLVED",decision_origin="SYSTEM_SUGGESTED",human_confirmed=False,actor="system",actor_capacity="suggestion")
    asset_id = execution.record_trust_asset_control_determination(firm_id="FIRM-A",trust_id="TR-A",asset_object_type="PROPERTY",asset_object_id="PROP-A",decision_origin="SYSTEM_SUGGESTED",human_confirmed=False,actor="system",actor_capacity="suggestion")
    for table, key, value in zip(TABLES,("legal_state_event_id","sufficiency_id","authority_lifecycle_id","asset_control_id"),(doc_id,suf_id,fid_id,asset_id)):
        connection = sqlite3.connect(wave3_database)
        with pytest.raises(sqlite3.IntegrityError, match="wave3_append_only"):
            connection.execute(f"UPDATE {table} SET created_at='changed' WHERE {key}=?",(value,))
        with pytest.raises(sqlite3.IntegrityError, match="wave3_append_only"):
            connection.execute(f"DELETE FROM {table} WHERE {key}=?",(value,))
        connection.close()


def test_document_state_is_explicit_scoped_and_human_gated(wave3_database):
    apply_magc1_wave3_schema(wave3_database)
    assert documents.get_document_legal_state_history(firm_id="FIRM-A",trust_id="TR-A",document_object_type="DOCUMENT",document_object_id="DOC-A") == []
    for object_type, object_id in (("INSTRUMENT","DOC-A"),("DOCUMENT","missing")):
        with pytest.raises(documents.DocumentContractError):
            documents.record_document_legal_state(firm_id="FIRM-A",trust_id="TR-A",document_object_type=object_type,document_object_id=object_id,legal_state="UNRESOLVED",decision_origin="SYSTEM_SUGGESTED",human_confirmed=False,actor="system",actor_capacity="suggestion")
    with pytest.raises(documents.DocumentContractError):
        documents.record_document_legal_state(firm_id="FIRM-A",trust_id="TR-A",document_object_type="DOCUMENT",document_object_id="DOC-A",legal_state="EFFECTIVE_RECORDED",decision_origin="SYSTEM_SUGGESTED",human_confirmed=False,actor="system",actor_capacity="suggestion")
    first = documents.record_document_legal_state(firm_id="FIRM-A",trust_id="TR-A",document_object_type="DOCUMENT",document_object_id="DOC-A",legal_state="EFFECTIVE_RECORDED",basis="signed copy reviewed",provenance="operator review",decision_origin="OPERATOR_OR_FIDUCIARY",human_confirmed=True,actor="operator",actor_capacity="trustee")
    second = documents.record_document_legal_state(firm_id="FIRM-A",trust_id="TR-A",document_object_type="DOCUMENT",document_object_id="DOC-A",legal_state="SUPERSEDED_RECORDED",basis="replacement reviewed",provenance="operator review",decision_origin="OPERATOR_OR_FIDUCIARY",human_confirmed=True,actor="operator",actor_capacity="trustee",prior_legal_state_event_id=first)
    assert [r["legal_state_event_id"] for r in documents.get_document_legal_state_history(firm_id="FIRM-A",trust_id="TR-A",document_object_type="DOCUMENT",document_object_id="DOC-A")] == [first,second]


def test_sufficiency_never_follows_evidence_or_verification_automatically(wave3_database):
    apply_magc1_wave3_schema(wave3_database)
    assert authority.get_evidence_sufficiency_history(program_id="PRG-A",firm_id="FIRM-A",issue_id="ISS-A",claim_id="CLM-A",target_use="FINALIZATION") == []
    with pytest.raises(ValueError, match="machine"):
        authority.record_evidence_sufficiency_assessment(program_id="PRG-A",firm_id="FIRM-A",issue_id="ISS-A",claim_id="CLM-A",target_use="FINALIZATION",sufficiency_state="SUFFICIENT",evidence_ids=["EVD-A"],verification_ids=["VER-A"],decision_origin="SYSTEM_SUGGESTED",human_confirmed=False,actor="system",actor_capacity="suggestion")
    with pytest.raises(ValueError, match="evidence"):
        authority.record_evidence_sufficiency_assessment(program_id="PRG-A",firm_id="FIRM-A",issue_id="ISS-A",claim_id="CLM-A",target_use="RESEARCH",sufficiency_state="SUFFICIENT",decision_origin="PROFESSIONAL",human_confirmed=True,actor="lawyer",actor_capacity="professional")
    sid = authority.record_evidence_sufficiency_assessment(program_id="PRG-A",firm_id="FIRM-A",issue_id="ISS-A",claim_id="CLM-A",target_use="FINALIZATION",sufficiency_state="SUFFICIENT",evidence_ids=["EVD-A"],verification_ids=["VER-A"],basis="reviewed",provenance="professional review",decision_origin="PROFESSIONAL",human_confirmed=True,actor="lawyer",actor_capacity="professional")
    assert authority.get_evidence_sufficiency_assessment(sid)["sufficiency_state"] == "SUFFICIENT"


def test_lifecycle_is_separate_latest_only_and_does_not_mutate_sources(wave3_database):
    apply_magc1_wave3_schema(wave3_database)
    source_before = _counts(wave3_database,("fiduciaries","successor_acceptances","fiduciary_authority_capabilities"))
    assert fiduciary.get_fiduciary_authority_lifecycle_history(firm_id="FIRM-A",trust_id="TR-A",fiduciary_id="FID-A") == []
    with pytest.raises(fiduciary.FiduciaryAuthorityContractError, match="machine"):
        fiduciary.record_fiduciary_authority_lifecycle(firm_id="FIRM-A",trust_id="TR-A",fiduciary_id="FID-A",authority_state="ACTIVE_RECORDED",decision_origin="SYSTEM_SUGGESTED",human_confirmed=False,actor="system",actor_capacity="suggestion")
    first = fiduciary.record_fiduciary_authority_lifecycle(firm_id="FIRM-A",trust_id="TR-A",fiduciary_id="FID-A",authority_state="ACTIVE_RECORDED",authority_basis="appointment reviewed",provenance="operator review",source_reference="instrument-1",decision_origin="OPERATOR_OR_FIDUCIARY",human_confirmed=True,actor="operator",actor_capacity="trustee",successor_acceptance_id="ACC-A")
    with pytest.raises(fiduciary.FiduciaryAuthorityContractError, match="predecessor"):
        fiduciary.record_fiduciary_authority_lifecycle(firm_id="FIRM-A",trust_id="TR-A",fiduciary_id="FID-A",authority_state="RESIGNED_RECORDED",authority_basis="notice reviewed",provenance="operator review",source_reference="notice-1",decision_origin="OPERATOR_OR_FIDUCIARY",human_confirmed=True,actor="operator",actor_capacity="trustee")
    fiduciary.record_fiduciary_authority_lifecycle(firm_id="FIRM-A",trust_id="TR-A",fiduciary_id="FID-A",authority_state="RESIGNED_RECORDED",authority_basis="notice reviewed",provenance="operator review",source_reference="notice-1",decision_origin="OPERATOR_OR_FIDUCIARY",human_confirmed=True,actor="operator",actor_capacity="trustee",prior_authority_lifecycle_id=first)
    assert _counts(wave3_database,source_before) == source_before


def test_asset_control_is_explicit_scoped_latest_only_and_non_mutating(wave3_database):
    apply_magc1_wave3_schema(wave3_database)
    before = sqlite3.connect(wave3_database).execute("SELECT * FROM properties").fetchall()
    assert execution.get_trust_asset_control_history(firm_id="FIRM-A",trust_id="TR-A",asset_object_type="PROPERTY",asset_object_id="PROP-A") == []
    with pytest.raises(execution.ExecutionContractError, match="machine"):
        execution.record_trust_asset_control_determination(firm_id="FIRM-A",trust_id="TR-A",asset_object_type="PROPERTY",asset_object_id="PROP-A",funding_state="FUNDED_RECORDED",decision_origin="SYSTEM_SUGGESTED",human_confirmed=False,actor="system",actor_capacity="suggestion")
    first = execution.record_trust_asset_control_determination(firm_id="FIRM-A",trust_id="TR-A",asset_object_type="PROPERTY",asset_object_id="PROP-A",funding_state="FUNDED_RECORDED",ownership_state="TRUST_TITLE_RECORDED",control_state="TRUSTEE_CONTROL_RECORDED",related_transfer_id="TX-A",evidence_reference="deed-1",basis="reviewed",provenance="operator review",decision_origin="OPERATOR_OR_FIDUCIARY",human_confirmed=True,actor="operator",actor_capacity="trustee")
    with pytest.raises(execution.ExecutionContractError, match="predecessor"):
        execution.record_trust_asset_control_determination(firm_id="FIRM-A",trust_id="TR-A",asset_object_type="PROPERTY",asset_object_id="PROP-A",funding_state="IN_PROCESS",decision_origin="OPERATOR_OR_FIDUCIARY",human_confirmed=True,actor="operator",actor_capacity="trustee")
    assert execution.get_trust_asset_control_determination(first)["funding_state"] == "FUNDED_RECORDED"
    connection=sqlite3.connect(wave3_database); after=connection.execute("SELECT * FROM properties").fetchall(); connection.close()
    assert after == before
