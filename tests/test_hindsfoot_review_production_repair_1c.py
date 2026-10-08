from __future__ import annotations

import hashlib
import json
import sqlite3
import zipfile

from services.services_document_registry import DOCUMENT_TYPES
from services.services_document_templates import assign_document_template
from services.services_document_object_model import build_document_object
from services.services_document_adapters import DOCUMENT_ADAPTERS
from services.services_professional_review_bundles import (
    TR001_BUNDLE, TR001_STATUS, TR001_TRUST_STATUS, WILL_BUNDLE, WILL_STATUS,
    generate_review_bundle,
)


SCHEMA = """
CREATE TABLE generated_documents (
 document_id TEXT PRIMARY KEY, workspace_id TEXT, trust_id TEXT, template_id TEXT,
 title TEXT, content TEXT, status TEXT, created_by TEXT, created_at TEXT,
 updated_at TEXT, owner_id TEXT, firm_id TEXT, source_record_type TEXT,
 source_record_id TEXT, generation_basis TEXT);
CREATE TABLE intake_sessions (intake_id TEXT PRIMARY KEY, firm_id TEXT, status TEXT, snapshot_revision_id TEXT);
CREATE TABLE trusts (trust_id TEXT PRIMARY KEY, firm_id TEXT, trust_name TEXT, trust_type TEXT, jurisdiction TEXT, status TEXT, revision_id TEXT);
CREATE TABLE professional_review_issues (
 issue_id TEXT PRIMARY KEY, intake_id TEXT, firm_id TEXT, linked_record_type TEXT,
 linked_record_id TEXT, status TEXT, disposition TEXT, reviewer_notes TEXT,
 resolved_by TEXT, resolved_capacity TEXT, resolved_at TEXT);
CREATE TABLE intake_followup_tasks (task_id TEXT PRIMARY KEY, intake_id TEXT, status TEXT);
"""


def _db(path):
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.execute("INSERT INTO intake_sessions VALUES ('INT-WILL','FIRM-1','draft','REV-W-1')")
    con.execute("INSERT INTO trusts VALUES ('TR-001','FIRM-1','Synthetic Trust','Revocable','New Jersey','pre-signing','REV-T-1')")
    con.execute("INSERT INTO professional_review_issues VALUES ('PRI-W','INT-WILL','FIRM-1','intake','INT-WILL','open',NULL,NULL,NULL,NULL,NULL)")
    con.execute("INSERT INTO professional_review_issues VALUES ('PRI-T','INT-TR','FIRM-1','trust','TR-001','escalated','escalated','Synthetic note','reviewer','Counsel',NULL)")
    con.execute("INSERT INTO intake_followup_tasks VALUES ('TASK-36','INT-WILL','open')")
    con.commit(); con.close()


def _snapshot(path):
    con = sqlite3.connect(path)
    value = (con.execute("SELECT * FROM professional_review_issues ORDER BY issue_id").fetchall(),
             con.execute("SELECT * FROM intake_followup_tasks ORDER BY task_id").fetchall(),
             con.execute("SELECT * FROM trusts ORDER BY trust_id").fetchall())
    con.close(); return value


def _verify(result):
    package = result["package_path"]
    assert hashlib.sha256(open(package, "rb").read()).hexdigest() == result["package_sha256"]
    with zipfile.ZipFile(package) as archive:
        names = set(archive.namelist())
        assert "component_sha256_manifest.sha256" in names
        for name, digest in result["component_sha256"].items():
            assert name in names
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest


def test_will_registered_exactly_once_without_pour_over_duplicate():
    names = [row["document_type"] for row in DOCUMENT_TYPES]
    assert names.count("Will") == 1
    assert "Pour-Over Will" not in names
    assert {"Trust", "Trust Minute", "Certificate", "Transfer", "Property", "Funding", "Governance", "Compliance", "Certificate of Trust", "Institution", "Archive"}.issubset(names)
    will = build_document_object(
        document_id="DOC-TYPE-WILL", document_type="Will", title="Will", module_name="Professional Review",
        source_record_type="document_type_registry", source_record_id="Will", status="registered",
        lifecycle_status="available", governance_policy="Controlled", retention_policy="Permanent",
        relationships=[], timeline=[], verification={"verified": True}, payload={},
    )
    assert assign_document_template(will)["template_id"] == "DTPL-WILL-REVIEW-001"
    assert list(DOCUMENT_ADAPTERS).count("Will") == 1


def test_will_bundle_is_attributed_hashed_linked_and_non_mutating(tmp_path):
    db = tmp_path / "will.db"; _db(db); before = _snapshot(db)
    result = generate_review_bundle(
        db, tmp_path / "out", bundle_type=WILL_BUNDLE, source_id="INT-WILL",
        intake_id="INT-WILL", matter_id="MAT-1", firm_id="FIRM-1", owner_id="USER-1",
        generated_by="tester", governed_clauses=[{"clause_id":"C-1","text":"Synthetic fixture only","revision_id":"CR-1"}],
        source_revision_ids=["REV-W-1","CR-1"], generated_at="2026-01-01T00:00:00+00:00",
        generation_batch_id="BATCH-W", bundle_id="BUNDLE-W",
    )
    assert result["lifecycle_review_classification"] == WILL_STATUS
    assert result["execution_status"] == "NON-EXECUTION"
    assert result["professional_review_issues"][0]["issue_id"] == "PRI-W"
    assert result["unresolved_blockers"] == ["PRI-W"]
    assert len(result["component_sha256"]) == 4
    assert len(result["manifest_sha256"]) == 64
    _verify(result); assert _snapshot(db) == before
    row = sqlite3.connect(db).execute("SELECT source_record_type,source_record_id,generation_basis,status FROM generated_documents").fetchone()
    assert row == ("intake", "INT-WILL", "CANONICAL_RECORD_PROFESSIONAL_REVIEW_BUNDLE", "PROFESSIONAL_REVIEW_NON_EXECUTION")


def test_tr001_bundle_preserves_trust_and_historical_provenance(tmp_path):
    db = tmp_path / "tr.db"; _db(db); before = _snapshot(db)
    historical = [{"artifact_id":"HIST-MJ-1","classification":"HISTORICAL_REFERENCE","jurisdictions":["NJ","NY"]}]
    result = generate_review_bundle(
        db, tmp_path / "out", bundle_type=TR001_BUNDLE, source_id="TR-001",
        intake_id="INT-TR", firm_id="FIRM-1", owner_id="USER-1", generated_by="tester",
        source_revision_ids=["REV-T-1"], historical_reference_provenance=historical,
        generated_at="2026-01-01T00:00:00+00:00", generation_batch_id="BATCH-T", bundle_id="BUNDLE-T",
    )
    assert result["lifecycle_review_classification"] == TR001_STATUS
    assert result["trust_status"] == TR001_TRUST_STATUS
    assert result["historical_reference_provenance"] == historical
    assert result["professional_review_issues"][0]["issue_id"] == "PRI-T"
    assert len(result["component_sha256"]) == 4
    _verify(result); assert _snapshot(db) == before


def test_identical_disposable_inputs_have_identical_content_hashes(tmp_path):
    results = []
    for suffix in ("a", "b"):
        db = tmp_path / f"{suffix}.db"; _db(db)
        results.append(generate_review_bundle(
            db, tmp_path / f"out-{suffix}", bundle_type=WILL_BUNDLE, source_id="INT-WILL",
            intake_id="INT-WILL", firm_id="FIRM-1", owner_id="USER-1", generated_by="tester",
            generated_at="2026-01-01T00:00:00+00:00", generation_batch_id="BATCH", bundle_id="BUNDLE",
        ))
    assert results[0]["component_sha256"] == results[1]["component_sha256"]
    assert results[0]["manifest_sha256"] == results[1]["manifest_sha256"]
    assert results[0]["package_sha256"] == results[1]["package_sha256"]
