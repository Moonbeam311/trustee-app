import inspect
import sqlite3

import pytest

import database.db as database_db
from database.migrations_successor_acceptance import (
    ACCEPTANCE_STATES,
    apply_successor_acceptance_schema,
)
import services.services_successor_acceptance as acceptance


def allow_all(_acceptance_id, _trust_id):
    return True


@pytest.fixture()
def acceptance_database(monkeypatch, tmp_path):
    path = tmp_path / "successor-acceptance.db"
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE trusts (
            trust_id TEXT PRIMARY KEY,
            trust_name TEXT,
            successor_trustee_name TEXT,
            firm_id TEXT NOT NULL
        );
        CREATE TABLE fiduciaries (
            fiduciary_id TEXT PRIMARY KEY,
            full_name TEXT,
            role_title TEXT,
            authority_scope TEXT,
            trust_id TEXT,
            status TEXT,
            firm_id TEXT NOT NULL
        );
        CREATE TABLE documents (
            document_id TEXT PRIMARY KEY,
            trust_id TEXT,
            document_title TEXT,
            firm_id TEXT
        );
        """
    )
    connection.executemany(
        "INSERT INTO trusts VALUES (?,?,?,?)",
        [
            ("TR-A", "Trust A", "Alex Successor", "FIRM-A"),
            ("TR-B", "Trust B", "Blair Successor", "FIRM-A"),
            ("TR-X", "Trust X", "Xavier Successor", "FIRM-B"),
        ],
    )
    connection.executemany(
        "INSERT INTO fiduciaries VALUES (?,?,?,?,?,?,?)",
        [
            ("FID-A", "Alex Successor", "Successor Trustee", "Recorded scope A", "TR-A", "Appointed", "FIRM-A"),
            ("FID-B", "Blair Successor", "Successor Trustee", "Recorded scope B", "TR-B", "Appointed", "FIRM-A"),
            ("FID-X", "Xavier Successor", "Successor Trustee", "Other scope", "TR-X", "Appointed", "FIRM-B"),
        ],
    )
    connection.execute(
        "INSERT INTO documents VALUES (?,?,?,?)",
        ("DOC-LEGACY", "TR-A", "Legacy Successor Acceptance", "FIRM-A"),
    )
    connection.commit()
    connection.close()

    active_firm = {"id": "FIRM-A"}
    monkeypatch.setattr(database_db, "DB_PATH", path)
    monkeypatch.setattr(database_db, "get_current_firm_id", lambda: active_firm["id"])
    return path, active_firm


def context_fingerprint(firm="FIRM-A", trust="TR-A", fiduciary="FID-A", appointment="APT-A"):
    return acceptance.derive_acceptance_context_fingerprint(
        firm_id=firm,
        trust_id=trust,
        fiduciary_id=fiduciary,
        appointment_reference=appointment,
        role_capacity="Successor Trustee",
        appointment_source_reference=f"Instrument:{trust}",
    )


def insert_acceptance(
    path,
    *,
    acceptance_id="ACC-A",
    firm_id="FIRM-A",
    trust_id="TR-A",
    fiduciary_id="FID-A",
    appointment_reference="APT-A",
    status="ACCEPTED_RECORDED",
    fingerprint=None,
):
    fingerprint = fingerprint or context_fingerprint(
        firm_id, trust_id, fiduciary_id, appointment_reference
    )
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            """INSERT INTO successor_acceptances (
                acceptance_id, firm_id, trust_id, fiduciary_id,
                appointment_reference, role_capacity,
                appointment_source_reference, acceptance_status,
                recorded_by, recorded_at, provenance_source,
                context_fingerprint, accepted_at, acceptance_method,
                evidence_document_id
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                acceptance_id, firm_id, trust_id, fiduciary_id,
                appointment_reference, "Successor Trustee", f"Instrument:{trust_id}",
                status, "operator-a", "2026-08-21T12:00:00Z", "OPERATOR_RECORDED",
                fingerprint,
                "2026-08-21T11:30:00Z" if status == "ACCEPTED_RECORDED" else None,
                "EXECUTED_DOCUMENT" if status == "ACCEPTED_RECORDED" else None,
                "DOC-EVIDENCE" if status == "ACCEPTED_RECORDED" else None,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def database_snapshot(path):
    connection = sqlite3.connect(path)
    try:
        return {
            table: connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in ("trusts", "fiduciaries", "documents", "successor_acceptances")
        }
    finally:
        connection.close()


def test_additive_schema_is_idempotent_and_creates_no_acceptance(acceptance_database):
    path, _active_firm = acceptance_database
    first = apply_successor_acceptance_schema(path)
    second = apply_successor_acceptance_schema(path)
    assert first["schema_complete"] is True
    assert second["schema_complete"] is True
    assert first["acceptance_rows"] == second["acceptance_rows"] == 0
    assert set(ACCEPTANCE_STATES) == acceptance.ACCEPTANCE_STATES

    connection = sqlite3.connect(path)
    try:
        columns = {
            row[1]: (row[2], row[3])
            for row in connection.execute("PRAGMA table_info(successor_acceptances)")
        }
    finally:
        connection.close()
    for required in (
        "acceptance_id", "firm_id", "trust_id", "fiduciary_id",
        "appointment_reference", "role_capacity", "appointment_source_reference",
        "acceptance_status", "recorded_by", "recorded_at", "provenance_source",
        "context_fingerprint",
    ):
        assert columns[required][1] == 1 or required == "acceptance_id"


def test_context_fingerprint_is_normalized_deterministic_and_context_specific():
    canonical = context_fingerprint()
    normalized = acceptance.derive_acceptance_context_fingerprint(
        firm_id="  firm-a ", trust_id="TR-A", fiduciary_id="fid-a",
        appointment_reference="APT-A", role_capacity=" successor   trustee ",
        appointment_source_reference="INSTRUMENT:TR-A",
    )
    assert canonical == normalized
    assert canonical != context_fingerprint(appointment="APT-NEW")
    assert canonical != context_fingerprint(trust="TR-B", fiduciary="FID-B")
    with pytest.raises(acceptance.SuccessorAcceptanceReadContractError):
        acceptance.derive_acceptance_context_fingerprint(
            firm_id="FIRM-A", trust_id="", fiduciary_id="FID-A",
            appointment_reference="APT-A", role_capacity="Successor Trustee",
            appointment_source_reference="Instrument:TR-A",
        )


def test_unique_context_and_source_scope_constraints(acceptance_database):
    path, _active_firm = acceptance_database
    apply_successor_acceptance_schema(path)
    insert_acceptance(path)
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
        insert_acceptance(path, acceptance_id="ACC-DUP")
    insert_acceptance(
        path, acceptance_id="ACC-B", trust_id="TR-B", fiduciary_id="FID-B",
        appointment_reference="APT-B", status="PENDING_EVIDENCE",
    )
    with pytest.raises(sqlite3.IntegrityError, match="scoped"):
        insert_acceptance(
            path, acceptance_id="ACC-WRONG", trust_id="TR-A", fiduciary_id="FID-B",
            appointment_reference="APT-WRONG", status="PENDING_EVIDENCE",
        )


def test_accepted_state_requires_time_and_evidence(acceptance_database):
    path, _active_firm = acceptance_database
    apply_successor_acceptance_schema(path)
    connection = sqlite3.connect(path)
    try:
        with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
            connection.execute(
                """INSERT INTO successor_acceptances (
                    acceptance_id, firm_id, trust_id, fiduciary_id,
                    appointment_reference, role_capacity, appointment_source_reference,
                    acceptance_status, recorded_by, recorded_at, provenance_source,
                    context_fingerprint
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("ACC-NO-EVIDENCE", "FIRM-A", "TR-A", "FID-A", "APT-A",
                 "Successor Trustee", "Instrument:TR-A", "ACCEPTED_RECORDED",
                 "operator-a", "2026-08-21T12:00:00Z", "OPERATOR_RECORDED",
                 context_fingerprint()),
            )
    finally:
        connection.close()


def test_scoped_reads_missing_authorization_and_no_mutation(acceptance_database):
    path, active_firm = acceptance_database
    apply_successor_acceptance_schema(path)
    insert_acceptance(path)
    insert_acceptance(
        path, acceptance_id="ACC-X", firm_id="FIRM-B", trust_id="TR-X",
        fiduciary_id="FID-X", appointment_reference="APT-X",
    )
    before = database_snapshot(path)

    record = acceptance.get_successor_acceptance(
        "ACC-A", authorization_check=allow_all
    )
    assert record["acceptance_status"] == "ACCEPTED_RECORDED"
    assert record["evidence"]["document_id"] == "DOC-EVIDENCE"
    assert all(value is False for value in record["institutional_effects"].values())
    assert acceptance.get_successor_acceptance("MISSING", authorization_check=allow_all) is None
    assert acceptance.get_successor_acceptance("ACC-X", authorization_check=allow_all) is None
    assert [row["acceptance_id"] for row in acceptance.list_successor_acceptances_for_trust("TR-A", authorization_check=allow_all)] == ["ACC-A"]
    assert acceptance.list_successor_acceptances_for_trust("TR-X", authorization_check=allow_all) == []

    deny = lambda _acceptance_id, _trust_id: False
    assert acceptance.get_successor_acceptance("ACC-A", authorization_check=deny) is None
    with pytest.raises(acceptance.SuccessorAcceptanceReadContractError, match="authorization"):
        acceptance.get_successor_acceptance("ACC-A", authorization_check=None)
    assert database_snapshot(path) == before
    active_firm["id"] = "FIRM-B"
    assert acceptance.get_successor_acceptance("ACC-X", authorization_check=allow_all)


def test_exact_context_read_and_context_immutability(acceptance_database):
    path, _active_firm = acceptance_database
    apply_successor_acceptance_schema(path)
    insert_acceptance(path)
    record = acceptance.get_successor_acceptance_for_context(
        trust_id="TR-A", fiduciary_id="FID-A", appointment_reference="APT-A",
        role_capacity="Successor Trustee",
        appointment_source_reference="Instrument:TR-A",
        authorization_check=allow_all,
    )
    assert record["acceptance_id"] == "ACC-A"
    assert acceptance.get_successor_acceptance_for_context(
        trust_id="TR-A", fiduciary_id="FID-A", appointment_reference="OTHER",
        role_capacity="Successor Trustee",
        appointment_source_reference="Instrument:TR-A",
        authorization_check=allow_all,
    ) is None
    connection = sqlite3.connect(path)
    try:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(
                "UPDATE successor_acceptances SET trust_id='TR-B' WHERE acceptance_id='ACC-A'"
            )
    finally:
        connection.close()


def test_legacy_document_does_not_create_acceptance_or_change_sources(acceptance_database):
    path, _active_firm = acceptance_database
    connection = sqlite3.connect(path)
    before_sources = {
        table: connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
        for table in ("trusts", "fiduciaries", "documents")
    }
    connection.close()
    result = apply_successor_acceptance_schema(path)
    assert result["acceptance_rows"] == 0
    assert acceptance.LEGACY_DOCUMENT_CLASSIFICATION == (
        "LEGACY DOCUMENT / ACCEPTANCE STATE NOT STRUCTURALLY VERIFIED"
    )
    connection = sqlite3.connect(path)
    try:
        after_sources = {
            table: connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in ("trusts", "fiduciaries", "documents")
        }
    finally:
        connection.close()
    assert after_sources == before_sources


def test_public_contract_has_no_acceptance_mutation_or_permission_api():
    public = {
        name for name, value in inspect.getmembers(acceptance, inspect.isfunction)
        if not name.startswith("_")
    }
    assert public == {
        "derive_acceptance_context_fingerprint",
        "get_successor_acceptance",
        "get_successor_acceptance_for_context",
        "list_successor_acceptances_for_trust",
    }
    assert not any(
        token in name
        for name in public
        for token in ("create", "record", "update", "delete", "grant", "activate", "assign", "transition")
    )
