from __future__ import annotations

import hashlib
import json
import sqlite3
import zipfile

import pytest

from database.migrations_hindsfoot_review_repair_1c_r3 import apply_hindsfoot_review_repair_r3_schema
from services.services_document_clause_provenance import (
    DocumentClauseProvenanceError, register_clause_revision_content,
)
from services.services_document_evidence import (
    DocumentEvidenceError, create_document_evidence_relationship,
    register_document_integrity, resolve_document_evidence,
)
from services.services_professional_review_bundles import (
    TR001_BUNDLE, WILL_BUNDLE, generate_review_bundle,
)


BASE = """
PRAGMA foreign_keys=ON;
CREATE TABLE documents (document_id TEXT PRIMARY KEY, trust_id TEXT, matter_id TEXT, firm_id TEXT, document_title TEXT, original_filename TEXT);
CREATE TABLE document_template_clause_revisions (
 clause_revision_id TEXT PRIMARY KEY,template_id TEXT,clause_id TEXT,clause_key TEXT,
 revision_state TEXT,content_sha256 TEXT,source_reference_id TEXT,prior_clause_revision_id TEXT);
CREATE TABLE document_clause_generation_events (
 clause_generation_event_id TEXT PRIMARY KEY,firm_id TEXT,context_type TEXT,context_id TEXT,
 intake_id TEXT,matter_id TEXT,template_id TEXT,clause_revision_id TEXT,generation_state TEXT,
 human_confirmed INTEGER,provenance TEXT,prior_clause_generation_event_id TEXT);
CREATE TABLE generated_documents (
 document_id TEXT PRIMARY KEY,workspace_id TEXT,trust_id TEXT,template_id TEXT,title TEXT,
 content TEXT,status TEXT,created_by TEXT,created_at TEXT,updated_at TEXT,owner_id TEXT,
 firm_id TEXT,source_record_type TEXT,source_record_id TEXT,generation_basis TEXT);
CREATE TABLE intake_sessions (intake_id TEXT PRIMARY KEY,firm_id TEXT,status TEXT,known_name TEXT);
CREATE TABLE trusts (trust_id TEXT PRIMARY KEY,firm_id TEXT,trust_name TEXT,jurisdiction TEXT,status TEXT,execution_status TEXT,funding_status TEXT);
CREATE TABLE matters (matter_id TEXT PRIMARY KEY,firm_id TEXT,title TEXT);
CREATE TABLE intake_followup_tasks (id INTEGER PRIMARY KEY,intake_id TEXT,firm_id TEXT,status TEXT,title TEXT);
CREATE TABLE hub_programs (program_id TEXT PRIMARY KEY,workspace_id TEXT,firm_id TEXT,owner_id TEXT);
CREATE TABLE hub_program_source_references (source_reference_id TEXT PRIMARY KEY,program_id TEXT,issue_id TEXT);
CREATE TABLE professional_review_issues (
 issue_id TEXT PRIMARY KEY,intake_id TEXT,firm_id TEXT,linked_record_type TEXT,
 linked_record_id TEXT,status TEXT,disposition TEXT,reviewer_notes TEXT,
 resolved_by TEXT,resolved_capacity TEXT,resolved_at TEXT);
"""


def _base(path):
    with sqlite3.connect(path) as con:
        con.executescript(BASE)
        con.execute("INSERT INTO intake_sessions VALUES ('INT-1','F-1','draft','Known Person')")
        con.execute("INSERT INTO trusts VALUES ('TR-001','F-1','Synthetic Trust','New Jersey','pre-signing','not_started',NULL)")
        con.execute("INSERT INTO matters VALUES ('MAT-1','F-1','Synthetic Matter')")
        con.execute("INSERT INTO intake_followup_tasks VALUES (36,'INT-1','F-1','open','Professional review')")
        con.execute("INSERT INTO hub_programs VALUES ('PRG-1','W-1','F-1','U-1')")
        con.execute("INSERT INTO hub_program_source_references VALUES ('SRC-P05','PRG-1','')")
        con.execute("INSERT INTO professional_review_issues VALUES ('PRI-1','INT-1','F-1','intake_followup_task','36','open',NULL,NULL,NULL,NULL,NULL)")
    return apply_hindsfoot_review_repair_r3_schema(path)


def _clause(path, revision_id="CR-1", text="Exact synthetic canonical clause.", clause_id="C-1",
            prior_revision_id=None, event_id="GE-1"):
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    with sqlite3.connect(path) as con:
        con.execute("INSERT INTO document_template_clause_revisions VALUES (?,?,?,?,?,?,?,?)",
                    (revision_id,"TPL-WILL",clause_id,"synthetic_clause","APPROVED",digest,"SRC-1",prior_revision_id))
        con.execute("INSERT INTO document_clause_generation_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (event_id,"F-1","OTHER","INT-1","INT-1",None,"TPL-WILL",revision_id,
                     "AUTHORIZED",1,"synthetic governed provenance",None))
    return text


def test_clause_content_owner_hash_idempotency_and_immutability(tmp_path):
    db = tmp_path / "clause.db"; _base(db); text = _clause(db)
    first = register_clause_revision_content(db, clause_revision_id="CR-1", renderable_content=text, created_by="tester")
    second = register_clause_revision_content(db, clause_revision_id="CR-1", renderable_content=text, created_by="other")
    assert first == second
    with sqlite3.connect(db) as con:
        assert con.execute("SELECT COUNT(*) FROM document_clause_revision_content").fetchone()[0] == 1
        assert set(first) == {"clause_revision_id","renderable_content","content_format","created_by","created_at"}
    with pytest.raises(DocumentClauseProvenanceError, match="CLAUSE_CONTENT_HASH_MISMATCH"):
        _clause(db, revision_id="CR-BAD", text="expected", clause_id="C-2", event_id="GE-2")
        register_clause_revision_content(db, clause_revision_id="CR-BAD", renderable_content="different", created_by="tester")
    with pytest.raises(DocumentClauseProvenanceError, match="CLAUSE_REVISION_CONTENT_IMMUTABLE"):
        register_clause_revision_content(db, clause_revision_id="CR-1", renderable_content="different", created_by="tester")


def test_will_production_resolver_and_manifest(tmp_path):
    db = tmp_path / "will.db"; _base(db); text = _clause(db)
    register_clause_revision_content(db, clause_revision_id="CR-1", renderable_content=text, created_by="tester")
    result = generate_review_bundle(db,tmp_path/"out",bundle_type=WILL_BUNDLE,source_id="INT-1",
      firm_id="F-1",owner_id="U-1",generated_by="tester",bundle_id="B-W",generated_at="2026-01-01T00:00:00Z")
    assert result["canonical_content_resolution_status"] == "CANONICAL_CONTENT_RESOLVED_WITH_INTENTIONAL_PLACEHOLDERS"
    assert result["resolved_revision_ids"] == ["CR-1"]
    assert result["resolved_clause_content_bindings"][0]["content_sha256"] == hashlib.sha256(text.encode()).hexdigest()
    assert result["intentional_unresolved_items"][0]["state"] == "INTENTIONAL_UNRESOLVED"
    assert "TASK_36_PROFESSIONAL_REVIEW_LINK" not in result["missing_canonical_bindings"]
    with zipfile.ZipFile(result["package_path"]) as archive:
        assert text.encode("utf-8") in archive.read("word/document.xml") if "word/document.xml" in archive.namelist() else True
        docx = archive.read("Integrated_Will_Professional_Review_Candidate.docx")
        with zipfile.ZipFile(__import__('io').BytesIO(docx)) as document:
            assert text.encode("utf-8") in document.read("word/document.xml")


def test_will_missing_binding_and_conflict_are_not_content_complete(tmp_path):
    db = tmp_path / "missing.db"; _base(db); _clause(db)
    missing = generate_review_bundle(db,tmp_path/"m",bundle_type=WILL_BUNDLE,source_id="INT-1",
      firm_id="F-1",owner_id="U",generated_by="tester",bundle_id="B-M")
    assert missing["canonical_content_resolution_status"] == "MISSING_CANONICAL_BINDING"
    assert missing["resolved_clause_content_bindings"] == []
    db2 = tmp_path / "conflict.db"; _base(db2)
    for rid,eid,text in (("CR-A","GE-A","A"),("CR-B","GE-B","B")):
        _clause(db2,rid,text,"C-1",None,eid)
        register_clause_revision_content(db2,clause_revision_id=rid,renderable_content=text,created_by="tester")
    conflict = generate_review_bundle(db2,tmp_path/"c",bundle_type=WILL_BUNDLE,source_id="INT-1",
      firm_id="F-1",owner_id="U",generated_by="tester",bundle_id="B-C")
    assert conflict["canonical_content_resolution_status"] == "CANONICAL_SOURCE_CONFLICT"
    assert conflict["canonical_source_conflicts"]


def test_document_integrity_relationship_roles_lineage_and_tr001_resolution(tmp_path):
    db = tmp_path / "tr.db"; migration = _base(db)
    assert migration["records_created"] == 0
    roles = ("GOVERNING_PRE_SIGNING_MASTER","BENEFICIARY_SCHEDULE","INITIAL_TRUSTEE_ACCEPTANCE",
             "SCHEDULE_A","CLOSING_CONTROL_SHEET","HISTORICAL_PROFESSIONAL_REVIEW_REFERENCE")
    for index, role in enumerate(roles):
        doc = f"D-{index}"
        with sqlite3.connect(db) as con: con.execute("INSERT INTO documents(document_id,trust_id,firm_id) VALUES (?,?,?)",(doc,"TR-001","F-1"))
        integrity = register_document_integrity(db,document_id=doc,content_bytes=f"bytes-{index}".encode(),source_revision_id=f"REV-{index}",firm_id="F-1")
        assert integrity["verified_content_sha256"] == hashlib.sha256(f"bytes-{index}".encode()).hexdigest()
        create_document_evidence_relationship(db,firm_id="F-1",context_type="TRUST",context_id="TR-001",
          document_id=doc,evidence_role=role,relationship_state="ACTIVE",
          classification="HISTORICAL_REFERENCE" if role.startswith("HISTORICAL") else "SOURCE_EVIDENCE",
          basis="synthetic",provenance="fixture",decision_origin="PROFESSIONAL",human_confirmed=True,
          created_by="tester",actor_capacity="counsel",relationship_id=f"R-{index}")
    with pytest.raises(DocumentEvidenceError,match="HUMAN_CONFIRMATION_REQUIRED"):
        create_document_evidence_relationship(db,firm_id="F-1",context_type="TRUST",context_id="TR-001",
          document_id="D-0",evidence_role="SCHEDULE_A",relationship_state="ACTIVE",classification="SOURCE_EVIDENCE",
          basis="x",provenance="x",decision_origin="PROFESSIONAL",human_confirmed=False,created_by="x",actor_capacity="x")
    before = sqlite3.connect(db).execute("SELECT status FROM trusts WHERE trust_id='TR-001'").fetchone()[0]
    result = generate_review_bundle(db,tmp_path/"out",bundle_type=TR001_BUNDLE,source_id="TR-001",
      intake_id="INT-1",firm_id="F-1",owner_id="U",generated_by="tester",bundle_id="B-T")
    assert result["canonical_content_resolution_status"] == "CANONICAL_CONTENT_RESOLVED_WITH_INTENTIONAL_PLACEHOLDERS"
    assert {r["evidence_role"] for r in result["resolved_evidence_relationships"]} == set(roles)
    hist = next(r for r in result["resolved_evidence_relationships"] if r["evidence_role"].startswith("HISTORICAL"))
    assert hist["classification"] == "HISTORICAL_REFERENCE"
    assert {x["subject"] for x in result["intentional_unresolved_items"]} == {"PRI-1", "execution"}
    assert sqlite3.connect(db).execute("SELECT status FROM trusts WHERE trust_id='TR-001'").fetchone()[0] == before
    assert resolve_document_evidence(db,firm_id="F-1",context_type="TRUST",context_id="TR-001")["conflicts"] == []


def test_relationship_successor_and_competing_terminals(tmp_path):
    db = tmp_path / "lineage.db"; _base(db)
    for doc in ("D-A","D-B","D-C"):
        with sqlite3.connect(db) as con: con.execute("INSERT INTO documents(document_id,trust_id,firm_id) VALUES (?,?,?)",(doc,"TR-001","F-1"))
        register_document_integrity(db,document_id=doc,content_bytes=doc.encode(),source_revision_id="REV-"+doc,firm_id="F-1")
    common = dict(firm_id="F-1",context_type="TRUST",context_id="TR-001",
      evidence_role="SCHEDULE_A",relationship_state="ACTIVE",classification="SOURCE_EVIDENCE",
      basis="synthetic",provenance="fixture",decision_origin="PROFESSIONAL",human_confirmed=True,
      created_by="tester",actor_capacity="counsel")
    create_document_evidence_relationship(db,document_id="D-A",relationship_id="R-A",**common)
    create_document_evidence_relationship(db,document_id="D-B",relationship_id="R-B",prior_relationship_id="R-A",**common)
    resolved = resolve_document_evidence(db,firm_id="F-1",context_type="TRUST",context_id="TR-001")
    assert [r["relationship_id"] for r in resolved["relationships"]] == ["R-B"]
    create_document_evidence_relationship(db,document_id="D-C",relationship_id="R-C",**common)
    assert resolve_document_evidence(db,firm_id="F-1",context_type="TRUST",context_id="TR-001")["conflicts"] == ["SCHEDULE_A"]


def test_will_does_not_require_task_36_link_or_mutate_review_state(tmp_path):
    db = tmp_path / "task.db"; _base(db); text = _clause(db)
    register_clause_revision_content(db,clause_revision_id="CR-1",renderable_content=text,created_by="tester")
    with sqlite3.connect(db) as con:
        con.execute("UPDATE professional_review_issues SET linked_record_type=NULL,linked_record_id=NULL")
        before = con.execute("SELECT * FROM professional_review_issues").fetchone()
    result = generate_review_bundle(db,tmp_path/"task-out",bundle_type=WILL_BUNDLE,source_id="INT-1",
      firm_id="F-1",owner_id="U",generated_by="tester",bundle_id="B-TASK")
    assert "TASK_36_PROFESSIONAL_REVIEW_LINK" not in result["missing_canonical_bindings"]
    assert result["canonical_content_resolution_status"] == "CANONICAL_CONTENT_RESOLVED_WITH_INTENTIONAL_PLACEHOLDERS"
    with sqlite3.connect(db) as con: assert con.execute("SELECT * FROM professional_review_issues").fetchone() == before


@pytest.mark.parametrize("linked_type,linked_id,expected", [
    ("intake_followup_task", "36", True),
    ("unrelated_record", "36", False),
    ("intake_followup_task", "35", False),
])
def test_tr001_task_36_requires_exact_type_and_canonical_id(tmp_path, linked_type, linked_id, expected):
    db = tmp_path / f"task-{linked_type}-{linked_id}.db"; _base(db)
    with sqlite3.connect(db) as con:
        con.execute("UPDATE professional_review_issues SET linked_record_type=?,linked_record_id=?", (linked_type, linked_id))
        before_issue = con.execute("SELECT * FROM professional_review_issues").fetchone()
        before_task = con.execute("SELECT * FROM intake_followup_tasks WHERE id=36").fetchone()
    roles = ("GOVERNING_PRE_SIGNING_MASTER","BENEFICIARY_SCHEDULE","INITIAL_TRUSTEE_ACCEPTANCE",
             "SCHEDULE_A","CLOSING_CONTROL_SHEET","HISTORICAL_PROFESSIONAL_REVIEW_REFERENCE")
    for index, role in enumerate(roles):
        doc = f"D-{index}"
        with sqlite3.connect(db) as con: con.execute("INSERT INTO documents(document_id,trust_id,firm_id) VALUES (?,?,?)",(doc,"TR-001","F-1"))
        register_document_integrity(db,document_id=doc,content_bytes=doc.encode(),source_revision_id=f"REV-{index}",firm_id="F-1")
        create_document_evidence_relationship(db,firm_id="F-1",context_type="TRUST",context_id="TR-001",
          document_id=doc,evidence_role=role,relationship_state="ACTIVE",
          classification="HISTORICAL_REFERENCE" if role.startswith("HISTORICAL") else "SOURCE_EVIDENCE",
          basis="x",provenance="x",decision_origin="PROFESSIONAL",human_confirmed=True,
          created_by="x",actor_capacity="counsel")
    result = generate_review_bundle(db,tmp_path/f"out-{linked_type}-{linked_id}",bundle_type=TR001_BUNDLE,
      source_id="TR-001",intake_id="INT-1",firm_id="F-1",owner_id="U",generated_by="tester")
    assert ("TASK_36_PROFESSIONAL_REVIEW_LINK" not in result["missing_canonical_bindings"]) is expected
    assert (result["canonical_content_resolution_status"] != "MISSING_CANONICAL_BINDING") is expected
    with sqlite3.connect(db) as con:
        assert con.execute("SELECT * FROM professional_review_issues").fetchone() == before_issue
        assert con.execute("SELECT * FROM intake_followup_tasks WHERE id=36").fetchone() == before_task


def test_unresolved_items_come_from_active_canonical_state_and_disappear(tmp_path):
    db = tmp_path / "unresolved.db"; _base(db); text = _clause(db)
    register_clause_revision_content(db,clause_revision_id="CR-1",renderable_content=text,created_by="tester")
    first = generate_review_bundle(db,tmp_path/"u1",bundle_type=WILL_BUNDLE,source_id="INT-1",
      firm_id="F-1",owner_id="U",generated_by="tester",bundle_id="U-1")
    assert [x["blocker_id"] for x in first["intentional_unresolved_items"]] == ["PRI-1"]
    with sqlite3.connect(db) as con: con.execute("UPDATE professional_review_issues SET status='resolved'")
    second = generate_review_bundle(db,tmp_path/"u2",bundle_type=WILL_BUNDLE,source_id="INT-1",
      firm_id="F-1",owner_id="U",generated_by="tester",bundle_id="U-2")
    assert second["intentional_unresolved_items"] == []
    assert "execution_date" not in {x["subject"] for x in second["intentional_unresolved_items"]}


def test_context_and_p05_source_validation(tmp_path):
    db = tmp_path / "contexts.db"; _base(db)
    with sqlite3.connect(db) as con:
        con.execute("INSERT INTO trusts VALUES ('TR-B','F-1','B','NJ','draft',NULL,NULL)")
        con.execute("INSERT INTO trusts VALUES ('TR-X','F-X','X','NJ','draft',NULL,NULL)")
        con.execute("INSERT INTO matters VALUES ('MAT-X','F-X','Other')")
        con.execute("INSERT INTO hub_programs VALUES ('PRG-X','W-X','F-X','U-X')")
        con.execute("INSERT INTO hub_program_source_references VALUES ('SRC-X','PRG-X','')")
        con.execute("INSERT INTO documents(document_id,trust_id,firm_id) VALUES ('D-A','TR-001','F-1')")
        con.execute("INSERT INTO documents(document_id,firm_id) VALUES ('D-M','F-1')")
        con.execute("INSERT INTO documents(document_id,firm_id) VALUES ('D-X','F-X')")
    common = dict(evidence_role="SCHEDULE_A",relationship_state="ACTIVE",classification="SOURCE_EVIDENCE",
      basis="x",provenance="x",decision_origin="PROFESSIONAL",human_confirmed=True,created_by="x",actor_capacity="x")
    assert create_document_evidence_relationship(db,firm_id="F-1",context_type="TRUST",context_id="TR-001",document_id="D-A",**common)
    with pytest.raises(DocumentEvidenceError,match="CANONICAL_TRUST_CONTEXT_NOT_FOUND"):
        create_document_evidence_relationship(db,firm_id="F-1",context_type="TRUST",context_id="missing",document_id="D-A",**common)
    with pytest.raises(DocumentEvidenceError,match="TRUST_FIRM_MISMATCH"):
        create_document_evidence_relationship(db,firm_id="F-1",context_type="TRUST",context_id="TR-X",document_id="D-A",**common)
    with pytest.raises(DocumentEvidenceError,match="DOCUMENT_FIRM_MISMATCH"):
        create_document_evidence_relationship(db,firm_id="F-1",context_type="TRUST",context_id="TR-001",document_id="D-X",**common)
    with pytest.raises(DocumentEvidenceError,match="DOCUMENT_TRUST_CONTEXT_MISMATCH"):
        create_document_evidence_relationship(db,firm_id="F-1",context_type="TRUST",context_id="TR-B",document_id="D-A",**common)
    assert create_document_evidence_relationship(db,firm_id="F-1",context_type="MATTER",context_id="MAT-1",document_id="D-M",source_reference_id="SRC-P05",**common)
    with pytest.raises(DocumentEvidenceError,match="CANONICAL_MATTER_CONTEXT_NOT_FOUND"):
        create_document_evidence_relationship(db,firm_id="F-1",context_type="MATTER",context_id="missing",document_id="D-M",**common)
    with pytest.raises(DocumentEvidenceError,match="MATTER_FIRM_MISMATCH"):
        create_document_evidence_relationship(db,firm_id="F-1",context_type="MATTER",context_id="MAT-X",document_id="D-M",**common)
    assert create_document_evidence_relationship(db,firm_id="F-1",context_type="MATTER",context_id="MAT-1",document_id="D-M",**common)
    with pytest.raises(DocumentEvidenceError,match="INVALID_CANONICAL_SOURCE_REFERENCE"):
        create_document_evidence_relationship(db,firm_id="F-1",context_type="MATTER",context_id="MAT-1",document_id="D-M",source_reference_id="invented",**common)
    with pytest.raises(DocumentEvidenceError,match="INVALID_CANONICAL_SOURCE_REFERENCE"):
        create_document_evidence_relationship(db,firm_id="F-1",context_type="MATTER",context_id="MAT-1",document_id="D-M",source_reference_id="SRC-X",**common)


def test_migration_idempotent_preserves_rows_and_performs_no_backfill(tmp_path):
    db = tmp_path / "migration.db"
    with sqlite3.connect(db) as con:
        con.executescript(BASE)
        con.execute("INSERT INTO documents(document_id,document_title,original_filename) VALUES ('D','Schedule A','governing-master.pdf')")
    first = apply_hindsfoot_review_repair_r3_schema(db)
    second = apply_hindsfoot_review_repair_r3_schema(db)
    assert first["document_rows_preserved"] == second["document_rows_preserved"] == 1
    with sqlite3.connect(db) as con:
        assert con.execute("SELECT verified_content_sha256,source_revision_id FROM documents").fetchone() == (None,None)
        fk = con.execute("PRAGMA foreign_key_list(document_evidence_relationships)").fetchall()
        assert {row[2] for row in fk} >= {"documents","document_evidence_relationships"}
