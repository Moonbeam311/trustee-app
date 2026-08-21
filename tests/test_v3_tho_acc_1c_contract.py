import sqlite3

import pytest

import database.db as database_db
from database.migrations_successor_acceptance import apply_successor_acceptance_schema
from services import services_successor_acceptance as acceptance_read
from services import services_successor_acceptance_evidence as evidence_adapter
from services import services_successor_acceptance_lifecycle as lifecycle


def allow_trust(_trust_id):
    return True


def allow_fiduciary(_fiduciary_id, _trust_id):
    return True


def allow_acceptance(_acceptance_id, _trust_id):
    return True


@pytest.fixture()
def evidence_database(monkeypatch, tmp_path):
    path = tmp_path / "acceptance-evidence.db"
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE trusts (trust_id TEXT PRIMARY KEY, trust_name TEXT,
          successor_trustee_name TEXT, firm_id TEXT NOT NULL);
        CREATE TABLE fiduciaries (fiduciary_id TEXT PRIMARY KEY, full_name TEXT,
          role_title TEXT, authority_scope TEXT, trust_id TEXT, appointment_date TEXT,
          effective_date TEXT, status TEXT, notes TEXT, firm_id TEXT NOT NULL);
        CREATE TABLE documents (document_id TEXT PRIMARY KEY, trust_id TEXT,
          document_title TEXT, firm_id TEXT NOT NULL);
        CREATE TABLE app_users (user_id TEXT PRIMARY KEY, username TEXT UNIQUE,
          password_hash TEXT, role_name TEXT, status TEXT, firm_id TEXT, owner_id TEXT);
        CREATE TABLE continuity_profiles (continuity_profile_id TEXT PRIMARY KEY,
          firm_id TEXT, trust_id TEXT, readiness_status TEXT, status TEXT);
        CREATE TABLE continuity_responsibilities (responsibility_id TEXT PRIMARY KEY,
          continuity_profile_id TEXT, firm_id TEXT, current_responsible_party TEXT,
          successor_responsible_party TEXT, acceptance_status TEXT);
        """
    )
    connection.executemany("INSERT INTO trusts VALUES (?,?,?,?)", [
        ("TR-A", "Trust A", "Alex", "FIRM-A"), ("TR-B", "Trust B", "Blair", "FIRM-A"),
        ("TR-X", "Trust X", "Xavier", "FIRM-X")])
    connection.executemany("INSERT INTO fiduciaries VALUES (?,?,?,?,?,?,?,?,?,?)", [
        ("FID-A", "Alex", "Successor Trustee", "Scope A", "TR-A", None, None, "Appointed", None, "FIRM-A"),
        ("FID-B", "Blair", "Successor Trustee", "Scope B", "TR-B", None, None, "Appointed", None, "FIRM-A"),
        ("FID-X", "Xavier", "Successor Trustee", "Scope X", "TR-X", None, None, "Appointed", None, "FIRM-X")])
    connection.executemany("INSERT INTO documents VALUES (?,?,?,?)", [
        ("DOC-A", "TR-A", "Executed evidence", "FIRM-A"),
        ("DOC-B", "TR-B", "Wrong Trust evidence", "FIRM-A"),
        ("DOC-X", "TR-X", "Wrong firm evidence", "FIRM-X"),
        ("DOC-LEGACY", "TR-A", "Generated legacy acceptance", "FIRM-A")])
    connection.executemany("INSERT INTO app_users VALUES (?,?,?,?,?,?,?)", [
        ("USR-M", "maker", "x", "Admin", "Active", "FIRM-A", None),
        ("USR-R", "reviewer", "x", "Admin", "Active", "FIRM-A", None),
        ("USR-V", "viewer", "x", "Viewer", "Active", "FIRM-A", None)])
    connection.execute("INSERT INTO continuity_profiles VALUES (?,?,?,?,?)", ("CP-A", "FIRM-A", "TR-A", "needs_review", "draft"))
    connection.execute("INSERT INTO continuity_responsibilities VALUES (?,?,?,?,?,?)", ("RESP-A", "CP-A", "FIRM-A", "Current", "Alex", "designated"))
    connection.commit()
    connection.close()
    monkeypatch.setattr(database_db, "DB_PATH", path)
    monkeypatch.setattr(database_db, "get_current_firm_id", lambda: "FIRM-A")
    database_db.ensure_role_tables()
    database_db.ensure_user_permission_override_tables()
    apply_successor_acceptance_schema(path)
    return path


def propose(*, evidence=None):
    return lifecycle.propose_successor_acceptance(
        trust_id="TR-A", fiduciary_id="FID-A", appointment_reference="APT-A",
        role_capacity="Successor Trustee", appointment_source_reference="Instrument:TR-A",
        proposed_status="ACCEPTED_RECORDED", maker_actor_id="maker",
        provenance_source="OPERATOR_RECORDED", evidence_document_id=evidence,
        reason="Reported acceptance", trust_authorization_check=allow_trust,
        fiduciary_authorization_check=allow_fiduciary,
        document_authorization_check=allow_trust)


def snapshot(path):
    connection = sqlite3.connect(path)
    try:
        return {table: connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
                for table in ("trusts", "fiduciaries", "documents", "app_users",
                              "role_permissions", "continuity_profiles",
                              "continuity_responsibilities")}
    finally:
        connection.close()


def test_document_link_is_scoped_nonfinalizing_and_readable(evidence_database):
    result = propose()
    linked = evidence_adapter.link_acceptance_document_evidence(
        result["acceptance_id"], document_id="DOC-A", expected_trust_id="TR-A",
        expected_fiduciary_id="FID-A", maker_actor_id="maker", reason="Evidence received",
        acceptance_authorization_check=allow_acceptance, document_authorization_check=allow_trust)
    assert linked["acceptance_finalized"] is False
    record = acceptance_read.get_successor_acceptance(result["acceptance_id"], authorization_check=allow_acceptance)
    assert record["acceptance_status"] == "PENDING_EVIDENCE"
    described = evidence_adapter.describe_acceptance_evidence(
        result["acceptance_id"], expected_trust_id="TR-A", expected_fiduciary_id="FID-A",
        acceptance_authorization_check=allow_acceptance, document_authorization_check=allow_trust)
    assert described["evidence_items"][0]["identifier"] == "DOC-A"
    assert described["evidence_items"][0]["maker_actor_ids"] == ["maker"]
    assert described["document_presence_records_acceptance"] is False


@pytest.mark.parametrize("document_id", ["MISSING", "DOC-B", "DOC-X"])
def test_missing_cross_trust_and_cross_firm_documents_fail_closed(evidence_database, document_id):
    result = propose()
    with pytest.raises(evidence_adapter.SuccessorAcceptanceEvidenceError, match="missing|outside"):
        evidence_adapter.link_acceptance_document_evidence(
            result["acceptance_id"], document_id=document_id, expected_trust_id="TR-A",
            expected_fiduciary_id="FID-A", maker_actor_id="maker", reason="Evidence",
            acceptance_authorization_check=allow_acceptance, document_authorization_check=allow_trust)


def test_context_mismatch_and_unauthorized_maker_fail_closed(evidence_database):
    result = propose()
    with pytest.raises(evidence_adapter.SuccessorAcceptanceEvidenceError, match="Fiduciary"):
        evidence_adapter.link_acceptance_document_evidence(
            result["acceptance_id"], document_id="DOC-A", expected_trust_id="TR-A",
            expected_fiduciary_id="FID-B", maker_actor_id="maker", reason="Evidence",
            acceptance_authorization_check=allow_acceptance, document_authorization_check=allow_trust)
    with pytest.raises(lifecycle.SuccessorAcceptanceLifecycleError, match="permission"):
        evidence_adapter.link_acceptance_document_evidence(
            result["acceptance_id"], document_id="DOC-A", expected_trust_id="TR-A",
            expected_fiduciary_id="FID-A", maker_actor_id="viewer", reason="Evidence",
            acceptance_authorization_check=allow_acceptance, document_authorization_check=allow_trust)


def test_reviewer_reliance_is_traceable_and_independent(evidence_database):
    result = propose()
    evidence_adapter.link_acceptance_document_evidence(
        result["acceptance_id"], document_id="DOC-A", expected_trust_id="TR-A",
        expected_fiduciary_id="FID-A", maker_actor_id="maker", reason="Attached",
        acceptance_authorization_check=allow_acceptance, document_authorization_check=allow_trust)
    lifecycle.review_acceptance_transition(
        result["acceptance_id"], proposal_event_id=result["proposal_event_id"],
        reviewer_actor_id="reviewer", approve=True, reason="Evidence verified")
    item = evidence_adapter.describe_acceptance_evidence(
        result["acceptance_id"], expected_trust_id="TR-A", expected_fiduciary_id="FID-A",
        acceptance_authorization_check=allow_acceptance,
        document_authorization_check=allow_trust)["evidence_items"][0]
    assert item["acceptance_review_status"] == "RELIED_ON_IN_FINALIZED_TRANSITION"
    assert item["reviewer_actor_ids"] == ["reviewer"]
    assert item["execution_finalization_status"] == "NOT DOCUMENTED"


def test_source_context_and_legacy_document_do_not_record_acceptance(evidence_database):
    before = acceptance_read.list_successor_acceptances_for_trust("TR-A", authorization_check=allow_trust)
    legacy = evidence_adapter.describe_legacy_acceptance_document("DOC-LEGACY", "TR-A", document_authorization_check=allow_trust)
    assert legacy["classification"] == acceptance_read.LEGACY_DOCUMENT_CLASSIFICATION
    assert legacy["acceptance_created"] is False
    assert acceptance_read.list_successor_acceptances_for_trust("TR-A", authorization_check=allow_trust) == before
    result = propose()
    context = evidence_adapter.build_acceptance_document_source_context(
        result["acceptance_id"], expected_trust_id="TR-A", expected_fiduciary_id="FID-A",
        acceptance_authorization_check=allow_acceptance, trust_authorization_check=allow_trust,
        fiduciary_authorization_check=allow_fiduciary)
    assert not any(context["output_state"].values())
    assert acceptance_read.get_successor_acceptance(result["acceptance_id"], authorization_check=allow_acceptance)["acceptance_status"] == "PENDING_EVIDENCE"


def test_external_reference_and_inspection_do_not_mutate_other_domains(evidence_database):
    result = propose()
    before = snapshot(evidence_database)
    evidence_adapter.link_acceptance_external_evidence(
        result["acceptance_id"], external_reference="EXT-EXECUTED-1",
        expected_trust_id="TR-A", expected_fiduciary_id="FID-A", maker_actor_id="maker",
        reason="External governed evidence", acceptance_authorization_check=allow_acceptance)
    assert snapshot(evidence_database) == before
    evidence_adapter.describe_acceptance_evidence(
        result["acceptance_id"], expected_trust_id="TR-A", expected_fiduciary_id="FID-A",
        acceptance_authorization_check=allow_acceptance, document_authorization_check=allow_trust)
    assert snapshot(evidence_database) == before
