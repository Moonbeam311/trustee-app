import sqlite3

import pytest

from database.migrations_magc1_wave4 import TABLES, apply_magc1_wave4_schema
from services.services_document_portability import record_template_portability_assessment
from services.services_jurisdiction_certification import record_jurisdiction_module_certification
from services.services_professional_review_boundary import evaluate_professional_review_boundary


@pytest.fixture
def wave4_db(tmp_path):
    path = tmp_path / "wave4.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.executescript("""
        CREATE TABLE document_templates(template_id TEXT PRIMARY KEY,name TEXT,category TEXT,description TEXT,template_body TEXT);
        INSERT INTO document_templates VALUES('TPL-1','Canonical','legal','owner','body');
        CREATE TABLE hub_authority_applicability(applicability_id TEXT PRIMARY KEY,firm_id TEXT,context_type TEXT,context_id TEXT,subject TEXT,source_reference_id TEXT,applicability_jurisdiction TEXT,trust_type_applicability TEXT,legal_scope TEXT,research_only INTEGER,generation_authorized INTEGER,independent_support_state TEXT);
        CREATE TABLE hub_authority_hierarchy_determinations(hierarchy_id TEXT PRIMARY KEY,firm_id TEXT,context_type TEXT,context_id TEXT,subject TEXT,hierarchy_kind TEXT,source_reference_id TEXT,hierarchy_state TEXT,applicability_jurisdiction TEXT);
        CREATE TABLE hub_program_evidence_sufficiency_assessments(sufficiency_id TEXT PRIMARY KEY,program_id TEXT,firm_id TEXT,issue_id TEXT,claim_id TEXT);
        INSERT INTO hub_authority_applicability VALUES('APP-1','F-1','TRUST','T-1','administration','SRC-1','VA','revocable','ADMINISTRATION',0,1,'YES');
        INSERT INTO hub_authority_hierarchy_determinations VALUES('HIER-1','F-1','TRUST','T-1','administration','CONTROLLING_LAW','SRC-1','CONTROLLING','VA');
        """)
    apply_magc1_wave4_schema(path)
    return path


def _cert(path, **changes):
    values = dict(firm_id="F-1", context_type="TRUST", context_id="T-1",
                  jurisdiction="VA", subject="administration", legal_scope="ADMINISTRATION",
                  applicability_id="APP-1", hierarchy_id="HIER-1",
                  certification_state="CERTIFIED", basis="explicit analysis",
                  provenance="professional record", decision_origin="PROFESSIONAL",
                  human_confirmed=True, actor="lawyer", actor_capacity="Attorney")
    values.update(changes)
    return record_jurisdiction_module_certification(path, **values)


def test_migration_is_exact_empty_idempotent_and_append_only(tmp_path):
    path = tmp_path / "schema.sqlite3"
    first = apply_magc1_wave4_schema(path); second = apply_magc1_wave4_schema(path)
    assert first["records_created"] == second["records_created"] == 0
    assert first["rows"] == second["rows"] == {table: 0 for table in TABLES}
    with sqlite3.connect(path) as connection:
        tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        assert tables == set(TABLES)
        assert not any("registry" in name or "professional_review" in name for name in tables)
        for table in TABLES:
            columns = [r[1] for r in connection.execute(f"PRAGMA table_info({table})")]
            assert "template_body" not in columns
            triggers = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name=?", (table,))}
            assert triggers == {f"w4_{table}_no_update", f"w4_{table}_no_delete"}


def test_certification_fails_closed_and_machine_cannot_finalize(wave4_db):
    with pytest.raises(ValueError, match="applicability"):
        _cert(wave4_db, applicability_id="missing")
    with pytest.raises(ValueError, match="hierarchy"):
        _cert(wave4_db, hierarchy_id="missing")
    with pytest.raises(ValueError, match="machine"):
        _cert(wave4_db, decision_origin="SYSTEM_SUGGESTED")
    with pytest.raises(ValueError, match="human"):
        _cert(wave4_db, human_confirmed=False)
    with pytest.raises(ValueError, match="jurisdiction"):
        _cert(wave4_db, jurisdiction="MD")
    assert _cert(wave4_db).startswith("JCRT-")


def test_certification_requires_generation_authorized_controlling_p09(wave4_db):
    with sqlite3.connect(wave4_db) as connection:
        connection.execute("UPDATE hub_authority_applicability SET generation_authorized=0")
    with pytest.raises(ValueError, match="generation"):
        _cert(wave4_db)


def test_portability_requires_template_certification_and_human_decision(wave4_db):
    certification_id = _cert(wave4_db)
    common = dict(firm_id="F-1", template_id="TPL-1", target_jurisdiction="VA",
                  target_trust_type="revocable", legal_scope="ADMINISTRATION",
                  jurisdiction_certification_id=certification_id, basis="reviewed",
                  provenance="record", decision_origin="PROFESSIONAL", human_confirmed=True,
                  actor="lawyer", actor_capacity="Attorney")
    with pytest.raises(ValueError, match="template"):
        record_template_portability_assessment(wave4_db, portability_state="PORTABLE", **(common | {"template_id":"missing"}))
    with pytest.raises(ValueError, match="machine"):
        record_template_portability_assessment(wave4_db, portability_state="PORTABLE", **(common | {"decision_origin":"SYSTEM_SUGGESTED"}))
    portability_id = record_template_portability_assessment(wave4_db, portability_state="PORTABLE", **common)
    with sqlite3.connect(wave4_db) as connection:
        columns = {r[1] for r in connection.execute("PRAGMA table_info(document_template_portability_assessments)")}
        assert not {"name","category","description","template_body"} & columns
        assert connection.execute("SELECT COUNT(*) FROM document_templates").fetchone()[0] == 1
    assert portability_id.startswith("PORT-")


def test_professional_boundary_is_read_only_and_lane_isolated(wave4_db):
    before = wave4_db.stat().st_size
    unresolved = evaluate_professional_review_boundary(wave4_db, firm_id="F-1")
    assert unresolved["overall_state"] == "UNRESOLVED"
    result = evaluate_professional_review_boundary(wave4_db, firm_id="F-1", intake_id="I-1", required_lanes=["INTAKE_PROFESSIONAL_REVIEW"])
    assert result["overall_state"] == "UNRESOLVED"
    assert wave4_db.stat().st_size == before


def test_open_intake_issue_blocks_and_other_lane_does_not_satisfy(wave4_db):
    with sqlite3.connect(wave4_db) as connection:
        connection.execute("CREATE TABLE professional_review_issues(id INTEGER PRIMARY KEY,issue_id TEXT,intake_id TEXT,firm_id TEXT,status TEXT,disposition TEXT,resolved_by TEXT,resolved_capacity TEXT,resolved_at TEXT)")
        connection.execute("INSERT INTO professional_review_issues VALUES(1,'PRI-1','I-1','F-1','open',NULL,NULL,NULL,NULL)")
    result = evaluate_professional_review_boundary(wave4_db, firm_id="F-1", intake_id="I-1", program_id="P-1", required_lanes=["INTAKE_PROFESSIONAL_REVIEW","P09_AUTHORITY_PROFESSIONAL_REVIEW"])
    assert result["overall_state"] == "BLOCKED"
    assert [lane["state"] for lane in result["lane_results"]] == ["BLOCKED", "UNRESOLVED"]
