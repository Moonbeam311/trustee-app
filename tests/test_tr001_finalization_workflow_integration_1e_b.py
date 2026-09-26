import json
import sqlite3

import pytest

import services.services_tr001_property_finalization as finalization_service

from services.services_tr001_property_finalization import (
    build_schedule_a_draft_text,
    get_property_finalization_snapshot,
)


@pytest.fixture
def finalization_db(tmp_path):
    path = tmp_path / "tr001-read-model.sqlite3"
    with sqlite3.connect(path) as con:
        con.executescript("""
        CREATE TABLE properties(property_id TEXT PRIMARY KEY,trust_id TEXT,firm_id TEXT,property_name TEXT,status TEXT);
        CREATE TABLE property_attestations(attestation_id TEXT PRIMARY KEY,property_id TEXT,trust_id TEXT,firm_id TEXT,attestation_type TEXT,subject_field_or_fact TEXT,attested_value TEXT,actor_id TEXT,actor_capacity TEXT,basis TEXT,attested_at TEXT,status TEXT,supersedes_attestation_id TEXT,created_at TEXT);
        CREATE TABLE property_identification_revisions(revision_id TEXT PRIMARY KEY,property_id TEXT,trust_id TEXT,firm_id TEXT,revision_number INTEGER,prior_identification_json TEXT,resulting_identification_json TEXT,revision_basis TEXT,actor_id TEXT,actor_capacity TEXT,status TEXT,created_at TEXT);
        CREATE TABLE media_records(media_id TEXT PRIMARY KEY,trust_id TEXT,firm_id TEXT,related_entity_type TEXT,related_entity_id TEXT,media_type TEXT,file_path TEXT,description TEXT,created_at TEXT);
        CREATE TABLE continuity_custody_log(custody_event_id TEXT PRIMARY KEY,property_id TEXT,trust_id TEXT,firm_id TEXT,event_date TEXT);
        CREATE TABLE transfers(transfer_id TEXT PRIMARY KEY,property_id TEXT,trust_id TEXT,firm_id TEXT,status TEXT,assignment_confirmed INTEGER,transfer_complete INTEGER,trustee_decision TEXT,created_at TEXT);
        CREATE TABLE successor_acceptances(acceptance_id TEXT PRIMARY KEY,trust_id TEXT,firm_id TEXT,acceptance_status TEXT,recorded_at TEXT);
        CREATE TABLE trust_asset_control_determinations(asset_control_id TEXT PRIMARY KEY,firm_id TEXT,trust_id TEXT,asset_object_type TEXT,asset_object_id TEXT,related_transfer_id TEXT,funding_state TEXT,ownership_state TEXT,control_state TEXT,created_at TEXT);
        CREATE TABLE trusts(trust_id TEXT PRIMARY KEY,firm_id TEXT,execution_status TEXT);
        CREATE TABLE execution_tasks(task_id TEXT PRIMARY KEY,firm_id TEXT,trust_id TEXT,status TEXT);
        CREATE TABLE professional_review_issues(issue_id TEXT PRIMARY KEY,firm_id TEXT,status TEXT,disposition TEXT);
        CREATE TABLE generated_documents(document_id TEXT PRIMARY KEY,trust_id TEXT);
        INSERT INTO properties VALUES('P-ASE-2014','TR-001','F-1','2014 American Silver Eagle','proposed');
        INSERT INTO trusts VALUES('TR-001','F-1','awaiting_execution');
        INSERT INTO property_attestations VALUES('A-P0','P-ASE-2014','TR-001','F-1','possession','physical possession','past','SET-1','settlor','personal knowledge','2026-01-01','recorded',NULL,'2026-01-01');
        INSERT INTO property_attestations VALUES('A-P1','P-ASE-2014','TR-001','F-1','possession','physical possession','present','SET-1','settlor','personal knowledge','2026-02-01','recorded','A-P0','2026-02-01');
        INSERT INTO property_attestations VALUES('A-O1','P-ASE-2014','TR-001','F-1','ownership','personal ownership','asserted','SET-1','settlor','personal knowledge','2026-02-01','recorded',NULL,'2026-02-01');
        INSERT INTO property_identification_revisions VALUES('R-1','P-ASE-2014','TR-001','F-1',1,'{}','{"name":"silver coin"}','photo review','SET-1','settlor','recorded','2026-01-01');
        INSERT INTO property_identification_revisions VALUES('R-2','P-ASE-2014','TR-001','F-1',2,'{}','{"name":"2014 American Silver Eagle","face_value":"ONE DOLLAR","metal":"1 OZ. FINE SILVER","mint_mark":"not visible"}','photo review','SET-1','settlor','recorded','2026-02-01');
        INSERT INTO media_records VALUES('M-1','TR-001','F-1','property','P-ASE-2014','photo','fixture/front.jpg','supplied photo','2026-02-01');
        INSERT INTO media_records VALUES('M-X','TR-001','F-1','attestation','A-P1','photo','fixture/other.jpg','not property-linked','2026-02-01');
        INSERT INTO execution_tasks VALUES('Task36','F-1','TR-001','OPEN');
        INSERT INTO professional_review_issues VALUES('PRI-TEST','F-1','OPEN','open');
        """)
    return path


def snap(path):
    return get_property_finalization_snapshot(path, "F-1", "TR-001", "P-ASE-2014", task_id="Task36", professional_review_issue_id="PRI-TEST")


def counts_and_schema(path):
    with sqlite3.connect(path) as con:
        tables = tuple(r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        counts = {t: con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}
    return tables, counts


def test_identity_current_independent_attestations_latest_revision_and_media(finalization_db):
    value = snap(finalization_db)
    assert value["property"]["property_name"] == "2014 American Silver Eagle"
    assert [r["attestation_id"] for r in value["current_possession_attestations"]] == ["A-P1"]
    assert [r["attestation_id"] for r in value["current_ownership_attestations"]] == ["A-O1"]
    assert value["attestation_history_count"] == 3
    assert value["latest_identification_revision"]["revision_id"] == "R-2"
    assert value["identification_revision_count"] == 2
    assert [r["media_id"] for r in value["property_evidence_media"]] == ["M-1"]


def test_certified_1e_a_read_apis_are_reused(finalization_db, monkeypatch):
    called = []
    for name in (
        "list_property_attestations", "list_current_property_attestations",
        "list_property_identification_revisions", "get_latest_property_identification_revision",
    ):
        original = getattr(finalization_service, name)
        def wrapper(*args, _name=name, _original=original, **kwargs):
            called.append(_name)
            return _original(*args, **kwargs)
        monkeypatch.setattr(finalization_service, name, wrapper)
    snap(finalization_db)
    assert set(called) == {
        "list_property_attestations", "list_current_property_attestations",
        "list_property_identification_revisions", "get_latest_property_identification_revision",
    }


def test_facts_do_not_infer_transfer_acceptance_execution_or_funding(finalization_db):
    value = snap(finalization_db)
    assert value["derived_workflow_state"] == "PROFESSIONAL_REVIEW_REQUIRED"
    assert value["transfer_complete"] is False
    assert value["trustee_acceptance_complete"] is False
    assert value["funding_complete"] is False
    assert value["execution_complete"] is False
    assert value["execution_state"] == "awaiting_execution"


def test_draft_schedule_a_exists_without_legal_effect(finalization_db):
    value = snap(finalization_db)
    context = value["schedule_a_draft_context"]
    assert context["schedule_a_draft_eligible"] == "YES"
    assert context["output_status"] == "DRAFT_PROSPECTIVE"
    assert context["transfer_complete"] == context["trustee_acceptance_complete"] == "NO"
    assert context["execution_complete"] == context["funding_complete"] == "NO"
    rendered = build_schedule_a_draft_text(value)
    assert "Schedule A Entry" in rendered["text"]
    assert "2014 American Silver Eagle" in rendered["text"]
    assert rendered["context"]["legal_effect"] == "NONE_INFERRED"


def test_transfer_acceptance_and_funding_advance_only_from_explicit_facts(finalization_db):
    with sqlite3.connect(finalization_db) as con:
        con.execute("INSERT INTO transfers VALUES('X-1','P-ASE-2014','TR-001','F-1','draft',0,0,NULL,'2026-03-01')")
    assert snap(finalization_db)["transfer_complete"] is False
    with sqlite3.connect(finalization_db) as con:
        con.execute("UPDATE transfers SET status='TRANSFERRED',assignment_confirmed=1,transfer_complete=1 WHERE transfer_id='X-1'")
    value = snap(finalization_db)
    assert value["transfer_complete"] is True
    assert value["trustee_acceptance_complete"] is False
    with sqlite3.connect(finalization_db) as con:
        con.execute("INSERT INTO successor_acceptances VALUES('ACC-1','TR-001','F-1','ACCEPTED_RECORDED','2026-03-02')")
    value = snap(finalization_db)
    assert value["trustee_acceptance_complete"] is False
    assert value["fiduciary_authority_context"]["acceptance_id"] == "ACC-1"
    assert value["funding_complete"] is False
    with sqlite3.connect(finalization_db) as con:
        con.execute("UPDATE transfers SET trustee_decision='ACCEPTED' WHERE transfer_id='X-1'")
        con.execute("INSERT INTO trust_asset_control_determinations VALUES('CTL-1','F-1','TR-001','PROPERTY','P-ASE-2014','X-1','FUNDED_RECORDED','TRUST_TITLE_RECORDED','TRUSTEE_CONTROL_RECORDED','2026-03-03')")
    value = snap(finalization_db)
    assert value["funding_complete"] is True
    assert value["derived_workflow_state"] == "PROFESSIONAL_REVIEW_REQUIRED"  # blocker overlays, facts remain


def test_transfer_acceptance_does_not_require_successor_acceptance(finalization_db):
    with sqlite3.connect(finalization_db) as con:
        con.execute("INSERT INTO transfers VALUES('X-2','P-ASE-2014','TR-001','F-1','TRANSFERRED',1,1,'ACCEPTED','2026-03-01')")
    value = snap(finalization_db)
    assert value["trustee_acceptance_complete"] is True
    assert value["fiduciary_authority_context"]["state"] == "UNAVAILABLE"


def test_cross_firm_task_and_pri_are_unavailable_not_blockers(finalization_db):
    with sqlite3.connect(finalization_db) as con:
        con.execute("INSERT INTO execution_tasks VALUES('OTHER-TASK','F-2','TR-001','OPEN')")
        con.execute("INSERT INTO professional_review_issues VALUES('OTHER-PRI','F-2','OPEN','open')")
    value = get_property_finalization_snapshot(
        finalization_db, "F-1", "TR-001", "P-ASE-2014",
        task_id="OTHER-TASK", professional_review_issue_id="OTHER-PRI",
    )
    assert value["task_state"]["state"] == "UNAVAILABLE"
    assert value["professional_review_issue_state"]["state"] == "UNAVAILABLE"
    assert not any(b["reason"] == "OPEN" for b in value["blocker_reasons"] if b["type"] in {"TASK", "PROFESSIONAL_REVIEW"})


def test_missing_property_scope_is_explicitly_rejected(tmp_path):
    path = tmp_path / "unscoped.sqlite3"
    with sqlite3.connect(path) as con:
        con.execute("CREATE TABLE properties(property_id TEXT PRIMARY KEY,property_name TEXT)")
        con.execute("INSERT INTO properties VALUES('P-ASE-2014','Coin')")
    from services.services_tr001_property_finalization import PropertyFinalizationReadError
    with pytest.raises(PropertyFinalizationReadError, match="does not support firm/trust scoping"):
        get_property_finalization_snapshot(path, "F-1", "TR-001", "P-ASE-2014")


def test_open_task_and_pri_surface_without_mutation(finalization_db):
    before = counts_and_schema(finalization_db)
    value = snap(finalization_db)
    assert value["task_state"]["status"] == "OPEN"
    assert value["professional_review_issue_state"]["status"] == "OPEN"
    assert {b["type"] for b in value["blocker_reasons"]} >= {"TASK", "PROFESSIONAL_REVIEW", "DOCUMENT_EXECUTION"}
    assert counts_and_schema(finalization_db) == before


def test_repeatable_read_model_creates_no_records_or_schema(finalization_db):
    before = counts_and_schema(finalization_db)
    first = snap(finalization_db)
    second = snap(finalization_db)
    assert first == second
    assert counts_and_schema(finalization_db) == before
    assert set(before[0]) == {
        "continuity_custody_log", "execution_tasks", "generated_documents", "media_records",
        "professional_review_issues", "properties", "property_attestations",
        "property_identification_revisions", "successor_acceptances",
        "trust_asset_control_determinations", "transfers", "trusts",
    }
