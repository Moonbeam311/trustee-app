import sqlite3

import pytest

from database.migrations_tr001_finalization_workflow_1e import apply_property_fact_schema
from database.startup_migrations import run_additive_startup_migrations
from services.services_property_attestations import (
    PropertyFactServiceError,
    create_property_attestation,
    create_property_identification_revision,
    get_latest_property_identification_revision,
    list_current_property_attestations,
    list_property_attestations,
    list_property_identification_revisions,
)


@pytest.fixture
def fact_db(tmp_path):
    path = tmp_path / "property-facts.sqlite3"
    with sqlite3.connect(path) as con:
        con.executescript("""
            CREATE TABLE properties (
                property_id TEXT PRIMARY KEY, trust_id TEXT NOT NULL, firm_id TEXT NOT NULL,
                property_name TEXT
            );
            CREATE TABLE transfers (transfer_id TEXT PRIMARY KEY, property_id TEXT);
            CREATE TABLE continuity_custody_log (custody_event_id TEXT PRIMARY KEY, property_id TEXT);
            CREATE TABLE media_records (
                media_id TEXT PRIMARY KEY, trust_id TEXT, firm_id TEXT,
                related_entity_type TEXT, related_entity_id TEXT, created_at TEXT
            );
            INSERT INTO properties VALUES ('P-1','T-1','F-1','Coin');
            INSERT INTO properties VALUES ('P-2','T-1','F-1','Other Coin');
            INSERT INTO properties VALUES ('P-T2','T-2','F-1','Other Trust Coin');
            INSERT INTO properties VALUES ('P-F2','T-1','F-2','Other Firm Coin');
            INSERT INTO media_records VALUES ('M-1','T-1','F-1','property','P-1','2026-01-01');
            INSERT INTO media_records VALUES ('M-2','T-1','F-1','attestation','A-1','2026-01-02');
        """)
    apply_property_fact_schema(path)
    return path


def _attestation(kind, identifier):
    return {
        "attestation_id": identifier,
        "property_id": "P-1",
        "trust_id": "T-1",
        "firm_id": "F-1",
        "attestation_type": kind,
        "subject_field_or_fact": kind,
        "attested_value": "present",
        "actor_id": "ACT-1",
        "actor_capacity": "settlor",
        "basis": "personal knowledge",
        "attested_at": "2026-09-26T12:00:00Z",
    }


def _scoped_attestation(kind, identifier, property_id, trust_id, firm_id):
    return {
        **_attestation(kind, identifier),
        "property_id": property_id,
        "trust_id": trust_id,
        "firm_id": firm_id,
    }


def _counts(path):
    with sqlite3.connect(path) as con:
        return tuple(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in
                     ("transfers", "continuity_custody_log"))


def test_fresh_schema_contains_both_canonical_tables(tmp_path):
    path = tmp_path / "fresh.sqlite3"
    result = apply_property_fact_schema(path)
    with sqlite3.connect(path) as con:
        tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert result["schema_complete"] is True
    assert {"property_attestations", "property_identification_revisions"} <= tables


def test_partial_schema_upgrade_preserves_existing_property(tmp_path):
    path = tmp_path / "partial.sqlite3"
    with sqlite3.connect(path) as con:
        con.execute("CREATE TABLE properties (property_id TEXT PRIMARY KEY, property_name TEXT)")
        con.execute("INSERT INTO properties VALUES ('LEGACY-1','Preserved')")
    apply_property_fact_schema(path)
    apply_property_fact_schema(path)
    with sqlite3.connect(path) as con:
        assert con.execute("SELECT * FROM properties").fetchall() == [("LEGACY-1", "Preserved")]


def test_attestations_coexist_and_do_not_cross_infer_or_mutate_other_owners(fact_db):
    before = _counts(fact_db)
    create_property_attestation(fact_db, _attestation("possession", "A-P"))
    possession = list_property_attestations(fact_db, "P-1", "T-1", "F-1", "possession")
    ownership = list_property_attestations(fact_db, "P-1", "T-1", "F-1", "ownership")
    assert len(possession) == 1
    assert ownership == []

    create_property_attestation(fact_db, _attestation("ownership", "A-O"))
    assert len(list_property_attestations(fact_db, "P-1", "T-1", "F-1")) == 2
    assert len(list_property_attestations(fact_db, "P-1", "T-1", "F-1", "possession")) == 1
    assert len(list_property_attestations(fact_db, "P-1", "T-1", "F-1", "ownership")) == 1
    assert _counts(fact_db) == before


def test_new_attestation_supersedes_prior_without_mutating_it(fact_db):
    before_counts = _counts(fact_db)
    first = create_property_attestation(fact_db, _attestation("possession", "A-P1"))
    second_payload = {
        **_attestation("possession", "A-P2"),
        "attested_value": "not present",
        "supersedes_attestation_id": "A-P1",
    }
    second = create_property_attestation(fact_db, second_payload)

    all_rows = list_property_attestations(fact_db, "P-1", "T-1", "F-1", "possession")
    current = list_current_property_attestations(fact_db, "P-1", "T-1", "F-1", "possession")
    assert all_rows[0] == first
    assert all_rows[0]["supersedes_attestation_id"] is None
    assert second["supersedes_attestation_id"] == "A-P1"
    assert [row["attestation_id"] for row in current] == ["A-P2"]
    assert first["status"] == second["status"] == "recorded"
    assert _counts(fact_db) == before_counts


@pytest.mark.parametrize(
    ("prior", "replacement"),
    [
        (_scoped_attestation("possession", "A-OTHER-P", "P-2", "T-1", "F-1"),
         _attestation("possession", "A-NEW-P")),
        (_scoped_attestation("possession", "A-OTHER-T", "P-T2", "T-2", "F-1"),
         _attestation("possession", "A-NEW-T")),
        (_scoped_attestation("possession", "A-OTHER-F", "P-F2", "T-1", "F-2"),
         _attestation("possession", "A-NEW-F")),
        (_attestation("ownership", "A-OWN"), _attestation("possession", "A-NEW-TYPE")),
    ],
    ids=("property", "trust", "firm", "type"),
)
def test_cross_scope_or_type_supersession_is_rejected(fact_db, prior, replacement):
    create_property_attestation(fact_db, prior)
    replacement["supersedes_attestation_id"] = prior["attestation_id"]
    with pytest.raises(PropertyFactServiceError, match="same property, trust, firm, type, and subject"):
        create_property_attestation(fact_db, replacement)


def test_cross_subject_supersession_is_rejected(fact_db):
    create_property_attestation(fact_db, _attestation("possession", "A-SUBJECT-1"))
    replacement = {
        **_attestation("possession", "A-SUBJECT-2"),
        "subject_field_or_fact": "physical_location",
        "supersedes_attestation_id": "A-SUBJECT-1",
    }
    with pytest.raises(PropertyFactServiceError, match="same property, trust, firm, type, and subject"):
        create_property_attestation(fact_db, replacement)


def test_two_identification_revisions_are_preserved_without_transfer(fact_db):
    before = _counts(fact_db)
    base = {"property_id": "P-1", "trust_id": "T-1", "firm_id": "F-1",
            "revision_basis": "clarification", "actor_id": "ACT-1", "actor_capacity": "settlor"}
    first = create_property_identification_revision(
        fact_db, {**base, "revision_id": "R-1", "prior_identification_json": {},
                  "resulting_identification_json": {"name": "Silver Eagle"}}
    )
    first_snapshot = dict(first)
    second = create_property_identification_revision(
        fact_db, {**base, "revision_id": "R-2", "prior_identification_json": {"name": "Silver Eagle"},
                  "resulting_identification_json": {"name": "2014 Silver Eagle"}}
    )
    rows = list_property_identification_revisions(fact_db, "P-1", "T-1", "F-1")
    assert (first["revision_number"], second["revision_number"]) == (1, 2)
    assert [row["revision_id"] for row in rows] == ["R-1", "R-2"]
    assert rows[0] == first_snapshot
    assert rows[0]["status"] == rows[1]["status"] == "recorded"
    assert get_latest_property_identification_revision(fact_db, "P-1", "T-1", "F-1")["revision_id"] == "R-2"
    assert _counts(fact_db) == before


def test_scope_is_validated(fact_db):
    with pytest.raises(PropertyFactServiceError, match="scope"):
        create_property_attestation(fact_db, {**_attestation("possession", "A-X"), "firm_id": "OTHER"})


def test_property_media_relationship_remains_canonical(fact_db, monkeypatch):
    import database.db as db
    import services.services_continuity_assets as continuity

    monkeypatch.setattr(db, "DB_PATH", fact_db)
    rows = continuity.get_evidence_media_for_property("P-1")
    assert [row["media_id"] for row in rows] == ["M-1"]
    assert rows[0]["related_entity_type"] == "property"


def test_rows_are_database_enforced_append_only(fact_db):
    create_property_attestation(fact_db, _attestation("possession", "A-P"))
    with sqlite3.connect(fact_db) as con, pytest.raises(sqlite3.IntegrityError, match="append_only"):
        con.execute("UPDATE property_attestations SET attested_value='changed' WHERE attestation_id='A-P'")
    with sqlite3.connect(fact_db) as con, pytest.raises(sqlite3.IntegrityError, match="append_only"):
        con.execute("DELETE FROM property_attestations WHERE attestation_id='A-P'")


def test_identification_revisions_are_database_enforced_append_only(fact_db):
    base = {"property_id": "P-1", "trust_id": "T-1", "firm_id": "F-1",
            "revision_basis": "clarification", "actor_id": "ACT-1", "actor_capacity": "settlor",
            "prior_identification_json": {}, "resulting_identification_json": {"name": "Coin"}}
    create_property_identification_revision(fact_db, {**base, "revision_id": "R-IMMUTABLE-1"})
    create_property_identification_revision(
        fact_db,
        {**base, "revision_id": "R-IMMUTABLE-2", "prior_identification_json": {"name": "Coin"},
         "resulting_identification_json": {"name": "Specific Coin"}},
    )
    with sqlite3.connect(fact_db) as con, pytest.raises(sqlite3.IntegrityError, match="append_only"):
        con.execute("UPDATE property_identification_revisions SET status='changed' WHERE revision_id='R-IMMUTABLE-1'")
    with sqlite3.connect(fact_db) as con, pytest.raises(sqlite3.IntegrityError, match="append_only"):
        con.execute("DELETE FROM property_identification_revisions WHERE revision_id='R-IMMUTABLE-2'")


def test_startup_migration_is_additive_and_idempotent(fact_db):
    first = run_additive_startup_migrations(fact_db)["property_fact_schema"]
    second = run_additive_startup_migrations(fact_db)["property_fact_schema"]
    assert first["records_created"] == second["records_created"] == 0
    assert second["tables_created"] == []
    with sqlite3.connect(fact_db) as con:
        tables = [row[0] for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?,?)",
            ("property_attestations", "property_identification_revisions"),
        )]
    assert sorted(tables) == ["property_attestations", "property_identification_revisions"]
