import sqlite3

import pytest

import database.db as database_db
from database.migrations_intake_trust_bridge import migrate_intake_trust_bridge
from database.migrations_successor_acceptance import apply_successor_acceptance_schema
from services import services_continuity_acceptance_evidence as boundary
from services import services_successor_acceptance as acceptance_read
from services import services_successor_acceptance_evidence as evidence_adapter


def allow_trust(trust_id):
    return trust_id == "TR-A"


def allow_continuity(profile_id):
    return profile_id == "CP-A"


def allow_fiduciary(fiduciary_id, trust_id):
    return fiduciary_id == "FID-A" and trust_id == "TR-A"


def allow_acceptance(_acceptance_id, trust_id):
    return trust_id == "TR-A"


@pytest.fixture()
def continuity_database(monkeypatch, tmp_path):
    path = tmp_path / "continuity-acceptance.db"
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
        """
    )
    connection.executemany("INSERT INTO trusts VALUES (?,?,?,?)", [
        ("TR-A", "Trust A", "Alex", "FIRM-A"),
        ("TR-X", "Trust X", "Xavier", "FIRM-X"),
    ])
    connection.executemany("INSERT INTO fiduciaries VALUES (?,?,?,?,?,?,?,?,?,?)", [
        ("FID-A", "Alex", "Successor Trustee", "Recorded", "TR-A", None, None,
         "Appointed", None, "FIRM-A"),
        ("FID-X", "Xavier", "Successor Trustee", "Recorded", "TR-X", None, None,
         "Appointed", None, "FIRM-X"),
    ])
    connection.execute("INSERT INTO documents VALUES (?,?,?,?)",
                       ("DOC-A", "TR-A", "Executed evidence", "FIRM-A"))
    connection.commit()
    connection.close()
    migrate_intake_trust_bridge(path)
    apply_successor_acceptance_schema(path)
    connection = sqlite3.connect(path)
    connection.execute(
        """INSERT INTO continuity_profiles
           (continuity_profile_id,firm_id,subject_name,subject_type,subject_capacities,
            status,primary_purpose,trust_id,readiness_status,created_by,updated_by,
            created_at,updated_at)
           VALUES ('CP-A','FIRM-A','Alex','person','Successor Trustee','draft',
                   'Continuity','TR-A','needs_review','maker','maker','2026-08-21','2026-08-21')"""
    )
    connection.execute(
        """INSERT INTO continuity_profiles
           (continuity_profile_id,firm_id,subject_name,subject_type,subject_capacities,
            status,primary_purpose,trust_id,readiness_status,created_by,updated_by,
            created_at,updated_at)
           VALUES ('CP-X','FIRM-X','Xavier','person','Successor Trustee','draft',
                   'Continuity','TR-X','needs_review','maker','maker','2026-08-21','2026-08-21')"""
    )
    connection.commit()
    connection.close()
    monkeypatch.setattr(database_db, "DB_PATH", path)
    monkeypatch.setattr(database_db, "get_current_firm_id", lambda: "FIRM-A")
    return path


def insert_acceptance(path, status="ACCEPTED_RECORDED", fiduciary_id="FID-A"):
    fingerprint = acceptance_read.derive_acceptance_context_fingerprint(
        firm_id="FIRM-A", trust_id="TR-A", fiduciary_id=fiduciary_id,
        appointment_reference="APT-A", role_capacity="Successor Trustee",
        appointment_source_reference="Instrument:TR-A")
    connection = sqlite3.connect(path)
    connection.execute(
        """INSERT INTO successor_acceptances
           (acceptance_id,firm_id,trust_id,fiduciary_id,appointment_reference,
            role_capacity,appointment_source_reference,acceptance_status,accepted_at,
            acceptance_method,evidence_document_id,recorded_by,recorded_at,
            provenance_source,context_fingerprint)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("ACC-A", "FIRM-A", "TR-A", fiduciary_id, "APT-A", "Successor Trustee",
         "Instrument:TR-A", status,
         "2026-08-21T12:00:00Z" if status == "ACCEPTED_RECORDED" else None,
         "EXECUTED_DOCUMENT", "DOC-A", "maker", "2026-08-21T11:00:00Z",
         "OPERATOR_RECORDED", fingerprint),
    )
    connection.commit()
    connection.close()


def call_boundary(path, **overrides):
    values = dict(
        db_path=path, expected_trust_id="TR-A", expected_fiduciary_id="FID-A",
        trust_authorization_check=allow_trust,
        continuity_authorization_check=allow_continuity,
        fiduciary_authorization_check=allow_fiduciary,
        acceptance_authorization_check=allow_acceptance,
        document_authorization_check=allow_trust,
    )
    values.update(overrides)
    return boundary.get_continuity_acceptance_evidence("CP-A", **values)


def snapshot(path):
    connection = sqlite3.connect(path)
    try:
        tables = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return {table: connection.execute(f'SELECT * FROM "{table}" ORDER BY 1').fetchall()
                for table in tables}
    finally:
        connection.close()


def test_accepted_evidence_is_documented_but_never_an_activation_requirement(continuity_database):
    insert_acceptance(continuity_database)
    result = call_boundary(continuity_database)
    assert result["acceptance_evidence"]["state"] == "DOCUMENTED"
    assert result["acceptance_evidence"]["records"][0]["acceptance_id"] == "ACC-A"
    assert result["activation_requirement"] == {
        "status": "NOT DOCUMENTED", "required": None,
        "authoritative_source": None, "software_default_required": False}
    assert result["readiness_contribution"]["blocks_activation"] is False
    assert result["institutional_effects"]["continuity_activated"] is False


def test_pending_and_noncurrent_states_remain_distinct(continuity_database):
    insert_acceptance(continuity_database, "PENDING_EVIDENCE")
    result = call_boundary(continuity_database)
    assert result["acceptance_evidence"]["state"] == "PENDING"
    assert result["acceptance_evidence"]["display_state"] == "ACCEPTANCE PENDING REVIEW"


def test_missing_and_legacy_document_do_not_become_acceptance(continuity_database):
    connection = sqlite3.connect(continuity_database)
    connection.execute("INSERT INTO documents VALUES (?,?,?,?)",
                       ("DOC-LEGACY", "TR-A", "Legacy acceptance", "FIRM-A"))
    connection.commit()
    connection.close()
    legacy = evidence_adapter.describe_legacy_acceptance_document(
        "DOC-LEGACY", "TR-A", document_authorization_check=allow_trust)
    result = call_boundary(continuity_database)
    assert legacy["acceptance_created"] is False
    assert result["acceptance_evidence"]["state"] == "MISSING"
    assert result["acceptance_evidence"]["records"] == []
    assert result["readiness_contribution"]["blocks_activation"] is False


def test_cross_firm_wrong_trust_and_fiduciary_context_fail_closed(continuity_database):
    assert boundary.get_continuity_acceptance_evidence(
        "CP-X", db_path=continuity_database, expected_trust_id="TR-X",
        expected_fiduciary_id="FID-X", trust_authorization_check=lambda _: False,
        continuity_authorization_check=lambda _: False,
        fiduciary_authorization_check=lambda *_: False,
        acceptance_authorization_check=lambda *_: False,
        document_authorization_check=lambda _: False) is None
    assert call_boundary(continuity_database, expected_trust_id="TR-X") is None
    insert_acceptance(continuity_database)
    assert call_boundary(continuity_database, expected_fiduciary_id="FID-X")[
        "acceptance_evidence"]["records"] == []


def test_read_is_non_mutating_across_continuity_authority_and_access(continuity_database):
    insert_acceptance(continuity_database)
    before = snapshot(continuity_database)
    result = call_boundary(continuity_database)
    after = snapshot(continuity_database)
    assert after == before
    assert result["mutation_performed"] is False
    assert all(value is False for value in result["institutional_effects"].values())


def test_all_authorization_decisions_are_required(continuity_database):
    with pytest.raises(boundary.ContinuityAcceptanceEvidenceError, match="authorization"):
        call_boundary(continuity_database, acceptance_authorization_check=None)
