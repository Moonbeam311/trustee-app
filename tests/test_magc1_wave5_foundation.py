import sqlite3

import pytest

from database.migrations_magc1_wave5 import TABLES, apply_magc1_wave5_schema
from services.services_document_clause_provenance import (
    build_clause_generation_provenance,
    record_clause_generation_event,
    record_template_clause_revision,
)
from services.services_trust_formation_assessment import (
    evaluate_trust_formation_readiness,
    record_trust_formation_assessment,
)


HASH_A = "a" * 64
HASH_B = "b" * 64


@pytest.fixture
def wave5_db(tmp_path):
    path = tmp_path / "wave5.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.executescript("""
        CREATE TABLE document_templates(template_id TEXT PRIMARY KEY,template_body TEXT);
        CREATE TABLE generated_documents(document_id TEXT PRIMARY KEY,trust_id TEXT,template_id TEXT);
        CREATE TABLE documents(document_id TEXT PRIMARY KEY,trust_id TEXT,firm_id TEXT);
        CREATE TABLE trusts(trust_id TEXT PRIMARY KEY,firm_id TEXT);
        CREATE TABLE matters(matter_id TEXT PRIMARY KEY,firm_id TEXT);
        CREATE TABLE intakes(intake_id TEXT PRIMARY KEY,firm_id TEXT);
        CREATE TABLE hub_programs(program_id TEXT PRIMARY KEY,firm_id TEXT);
        CREATE TABLE hub_program_source_references(source_reference_id TEXT PRIMARY KEY,program_id TEXT);
        CREATE TABLE hub_authority_applicability(applicability_id TEXT PRIMARY KEY,firm_id TEXT,context_type TEXT,context_id TEXT,source_reference_id TEXT,research_only INTEGER,generation_authorized INTEGER,independent_support_state TEXT);
        CREATE TABLE hub_authority_hierarchy_determinations(hierarchy_id TEXT PRIMARY KEY,firm_id TEXT,context_type TEXT,context_id TEXT,source_reference_id TEXT,hierarchy_state TEXT);
        CREATE TABLE hub_program_evidence_sufficiency_assessments(sufficiency_id TEXT PRIMARY KEY,firm_id TEXT,target_use TEXT,sufficiency_state TEXT);
        CREATE TABLE hub_jurisdiction_module_certifications(certification_id TEXT PRIMARY KEY,firm_id TEXT,context_type TEXT,context_id TEXT,certification_state TEXT);
        CREATE TABLE document_template_portability_assessments(portability_id TEXT PRIMARY KEY,firm_id TEXT,template_id TEXT,portability_state TEXT);
        CREATE TABLE document_legal_state_events(legal_state_event_id TEXT PRIMARY KEY,firm_id TEXT,trust_id TEXT,document_object_type TEXT,document_object_id TEXT,legal_state TEXT);
        CREATE TABLE successor_acceptances(acceptance_id TEXT PRIMARY KEY,firm_id TEXT,trust_id TEXT);
        CREATE TABLE trust_asset_control_determinations(asset_control_id TEXT PRIMARY KEY,firm_id TEXT,trust_id TEXT);
        INSERT INTO document_templates VALUES('TPL-1','secret body'),('TPL-2','other body');
        INSERT INTO trusts VALUES('TR-1','F-1'),('TR-2','F-1');
        INSERT INTO matters VALUES('MAT-1','F-1');
        INSERT INTO intakes VALUES('INT-1','F-1');
        INSERT INTO hub_programs VALUES('PRG-1','F-1');
        INSERT INTO hub_program_source_references VALUES('SRC-1','PRG-1');
        INSERT INTO hub_authority_applicability VALUES('APP-1','F-1','TRUST','TR-1','SRC-1',0,1,'YES');
        INSERT INTO hub_authority_hierarchy_determinations VALUES('HIER-1','F-1','TRUST','TR-1','SRC-1','CONTROLLING');
        INSERT INTO hub_program_evidence_sufficiency_assessments VALUES('SUF-1','F-1','GENERATION','SUFFICIENT');
        INSERT INTO hub_jurisdiction_module_certifications VALUES('CERT-1','F-1','TRUST','TR-1','CERTIFIED');
        INSERT INTO document_template_portability_assessments VALUES('PORT-1','F-1','TPL-1','PORTABLE');
        INSERT INTO documents VALUES('DOC-1','TR-1','F-1');
        INSERT INTO document_legal_state_events VALUES('LEGAL-1','F-1','TR-1','DOCUMENT','DOC-1','EFFECTIVE_RECORDED');
        INSERT INTO successor_acceptances VALUES('ACC-1','F-1','TR-1');
        INSERT INTO trust_asset_control_determinations VALUES('ASSET-1','F-1','TR-1');
        """)
    apply_magc1_wave5_schema(path)
    return path


def _revision(path, **changes):
    values = dict(template_id="TPL-1",clause_id="CLAUSE-1",clause_key="distribution",
                  revision_label="v1",revision_state="APPROVED",content_sha256=HASH_A,
                  source_reference_id="SRC-1",basis="reviewed",provenance="professional review",
                  decision_origin="PROFESSIONAL",human_confirmed=True,actor="lawyer",actor_capacity="Attorney")
    values.update(changes)
    return record_template_clause_revision(path, **values)


def _generation(path, revision_id, **changes):
    values = dict(firm_id="F-1",context_type="TRUST",context_id="TR-1",trust_id="TR-1",
                  template_id="TPL-1",clause_revision_id=revision_id,generation_state="AUTHORIZED",
                  applicability_id="APP-1",hierarchy_id="HIER-1",evidence_sufficiency_id="SUF-1",
                  jurisdiction_certification_id="CERT-1",portability_id="PORT-1",basis="authorized",
                  provenance="human decision",decision_origin="PROFESSIONAL",human_confirmed=True,
                  actor="lawyer",actor_capacity="Attorney")
    values.update(changes)
    return record_clause_generation_event(path, **values)


def test_migration_exact_empty_idempotent_append_only_and_no_body_columns(tmp_path):
    path = tmp_path / "schema.sqlite3"
    first = apply_magc1_wave5_schema(path); second = apply_magc1_wave5_schema(path)
    assert first["records_created"] == second["records_created"] == 0
    assert first["rows"] == second["rows"] == {table: 0 for table in TABLES}
    with sqlite3.connect(path) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        assert tables == set(TABLES)
        assert not any("registry" in table for table in tables)
        for table in TABLES:
            columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
            assert not {"clause_text","clause_body","template_body","trust_name","trust_title","trust_terms"} & columns
            connection.execute(f"INSERT INTO {table} ({next(iter(columns))}) VALUES (NULL)") if False else None
        connection.execute("INSERT INTO document_template_clause_revisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",('R','T','C','K','V','DRAFT',HASH_A,None,'b','p','SYSTEM_SUGGESTED',0,'a','c',None,'now'))
        with pytest.raises(sqlite3.IntegrityError): connection.execute("UPDATE document_template_clause_revisions SET clause_key='x'")
        with pytest.raises(sqlite3.IntegrityError): connection.execute("DELETE FROM document_template_clause_revisions")


def test_clause_revision_owner_identity_predecessor_and_human_rules(wave5_db):
    with pytest.raises(ValueError, match="template"): _revision(wave5_db,template_id="missing")
    with pytest.raises(ValueError, match="source_reference"): _revision(wave5_db,source_reference_id="missing")
    with pytest.raises(ValueError, match="machine"): _revision(wave5_db,decision_origin="SYSTEM_SUGGESTED",human_confirmed=False)
    with pytest.raises(ValueError, match="human"): _revision(wave5_db,human_confirmed=False)
    first = _revision(wave5_db)
    with pytest.raises(ValueError, match="predecessor"): _revision(wave5_db,revision_label="v2",content_sha256=HASH_B)
    with pytest.raises(ValueError, match="identity"): _revision(wave5_db,clause_key="changed",revision_label="v2",content_sha256=HASH_B,prior_clause_revision_id=first)
    second = _revision(wave5_db,revision_label="v2",content_sha256=HASH_B,prior_clause_revision_id=first)
    with pytest.raises(ValueError, match="scope|predecessor"): _revision(wave5_db,template_id="TPL-2",prior_clause_revision_id=second)


def test_generation_authority_gates_applied_owner_and_read_only_builder(wave5_db):
    revision = _revision(wave5_db)
    with pytest.raises(ValueError, match="machine"): _generation(wave5_db,revision,decision_origin="SYSTEM_SUGGESTED",human_confirmed=False)
    with pytest.raises(ValueError, match="human"): _generation(wave5_db,revision,human_confirmed=False)
    gates = (("APP-1","generation_authorized",0,"applicability"),("HIER-1","hierarchy_state","PERSUASIVE","hierarchy"),("SUF-1","sufficiency_state","INSUFFICIENT","evidence"),("CERT-1","certification_state","REVIEW_REQUIRED","jurisdiction"),("PORT-1","portability_state","NOT_PORTABLE","portable"))
    table_ids = {"APP-1":("hub_authority_applicability","applicability_id"),"HIER-1":("hub_authority_hierarchy_determinations","hierarchy_id"),"SUF-1":("hub_program_evidence_sufficiency_assessments","sufficiency_id"),"CERT-1":("hub_jurisdiction_module_certifications","certification_id"),"PORT-1":("document_template_portability_assessments","portability_id")}
    for record_id,column,bad,message in gates:
        table,key = table_ids[record_id]
        with sqlite3.connect(wave5_db) as connection:
            old = connection.execute(f"SELECT {column} FROM {table} WHERE {key}=?",(record_id,)).fetchone()[0]
            connection.execute(f"UPDATE {table} SET {column}=? WHERE {key}=?",(bad,record_id))
        with pytest.raises(ValueError, match=message): _generation(wave5_db,revision)
        with sqlite3.connect(wave5_db) as connection: connection.execute(f"UPDATE {table} SET {column}=? WHERE {key}=?",(old,record_id))
    with sqlite3.connect(wave5_db) as connection: connection.execute("UPDATE hub_authority_hierarchy_determinations SET source_reference_id='OTHER'")
    with pytest.raises(ValueError, match="source"): _generation(wave5_db,revision)
    with sqlite3.connect(wave5_db) as connection: connection.execute("UPDATE hub_authority_hierarchy_determinations SET source_reference_id='SRC-1'")
    before = sqlite3.connect(wave5_db).execute("SELECT COUNT(*) FROM generated_documents").fetchone()[0]
    event = _generation(wave5_db,revision)
    assert build_clause_generation_provenance(wave5_db,event)["clause_revision"]["clause_revision_id"] == revision
    assert sqlite3.connect(wave5_db).execute("SELECT COUNT(*) FROM generated_documents").fetchone()[0] == before
    with pytest.raises(ValueError, match="generated_document"): _generation(wave5_db,revision,generation_state="APPLIED",prior_clause_generation_event_id=event)


def test_formation_is_extension_only_validates_links_and_never_infers(wave5_db):
    owner_tables = ("trusts","matters","intakes","documents","successor_acceptances","trust_asset_control_determinations")
    with sqlite3.connect(wave5_db) as connection: before = {t:connection.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in owner_tables}
    with pytest.raises(ValueError, match="context"): record_trust_formation_assessment(wave5_db,firm_id="F-1",formation_state="UNRESOLVED",readiness_state="UNRESOLVED",basis="b",provenance="p",decision_origin="SYSTEM_SUGGESTED",human_confirmed=False,actor="system",actor_capacity="system")
    common = dict(firm_id="F-1",trust_id="TR-1",basis="reviewed",provenance="record",decision_origin="PROFESSIONAL",human_confirmed=True,actor="lawyer",actor_capacity="Attorney")
    with pytest.raises(ValueError, match="machine"): record_trust_formation_assessment(wave5_db,formation_state="FORMATION_RECORDED",readiness_state="READY_FOR_ACTIVATION",decision_origin="SYSTEM_SUGGESTED",human_confirmed=False,governing_document_type="DOCUMENT",governing_document_id="DOC-1",legal_state_event_id="LEGAL-1",jurisdiction_certification_id="CERT-1",**{k:v for k,v in common.items() if k not in ('decision_origin','human_confirmed')})
    with pytest.raises(ValueError, match="instrument"): record_trust_formation_assessment(wave5_db,formation_state="DRAFTING",readiness_state="REVIEW_REQUIRED",governing_document_type="INSTRUMENT",governing_document_id="DOC-1",**common)
    with pytest.raises(ValueError, match="acceptance"): record_trust_formation_assessment(wave5_db,formation_state="DRAFTING",readiness_state="REVIEW_REQUIRED",trustee_acceptance_id="missing",**common)
    with pytest.raises(ValueError, match="asset_control"): record_trust_formation_assessment(wave5_db,formation_state="DRAFTING",readiness_state="REVIEW_REQUIRED",asset_control_id="missing",**common)
    assessment = record_trust_formation_assessment(wave5_db,formation_state="FORMATION_RECORDED",readiness_state="READY_FOR_ACTIVATION",governing_document_type="DOCUMENT",governing_document_id="DOC-1",legal_state_event_id="LEGAL-1",jurisdiction_certification_id="CERT-1",trustee_acceptance_id="ACC-1",asset_control_id="ASSET-1",**common)
    result = evaluate_trust_formation_readiness(wave5_db,firm_id="F-1",trust_id="TR-1")
    assert result["assessment"]["formation_assessment_id"] == assessment
    assert result["legal_existence_determined"] is result["validity_determined"] is False
    unresolved = evaluate_trust_formation_readiness(wave5_db,firm_id="F-1",trust_id="TR-2")
    assert unresolved["formation_state"] == "UNRESOLVED" and unresolved["legal_existence_determined"] is False
    with sqlite3.connect(wave5_db) as connection: after = {t:connection.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in owner_tables}
    assert after == before
