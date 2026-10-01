import sqlite3

import pytest

from database import db
from database import migrations_trust_field_revisions as revision_migration
from database.migrations_trust_field_revisions import (
    TrustFieldRevisionMigrationError,
    apply_trust_field_revision_schema,
)


@pytest.fixture
def revision_db(tmp_path, monkeypatch):
    path = tmp_path / "trust-field-revisions.sqlite3"
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE trusts (
            trust_id TEXT PRIMARY KEY,
            firm_id TEXT NOT NULL,
            owner_id TEXT NOT NULL,
            trust_name TEXT,
            jurisdiction TEXT,
            notes TEXT
        );
        INSERT INTO trusts VALUES
            ('TR-1', 'FIRM-1', 'OWNER-1', 'Original', 'VA', NULL),
            ('TR-2', 'FIRM-2', 'OWNER-2', 'Other', 'MD', '');
        """
    )
    connection.close()
    apply_trust_field_revision_schema(path)
    monkeypatch.setattr(db, "DB_PATH", path)
    return path


def _update(**overrides):
    arguments = {
        "trust_id": "TR-1",
        "updates": {"trust_name": "Changed"},
        "firm_id": "FIRM-1",
        "owner_id": "OWNER-1",
        "revision_basis": "operator correction",
        "provenance": "reviewed intake record",
        "decision_origin": "OPERATOR_OR_FIDUCIARY",
        "human_confirmed": True,
        "actor_id": "USER-1",
        "actor_capacity": "fiduciary",
    }
    arguments.update(overrides)
    return db.update_trust_fields_with_provenance_in_scope(**arguments)


def _rows(path, sql, parameters=()):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        return connection.execute(sql, parameters).fetchall()
    finally:
        connection.close()


def _direct_revision(
    connection,
    revision_id,
    revision_number,
    prior_revision_id=None,
    *,
    firm_id="FIRM-1",
    owner_id="OWNER-1",
    trust_id="TR-1",
    field_name="trust_name",
):
    connection.execute(
        """
        INSERT INTO trust_field_revisions (
            revision_id, firm_id, owner_id, trust_id, field_name,
            revision_number, prior_value, resulting_value, revision_basis,
            provenance, decision_origin, human_confirmed, actor_id,
            actor_capacity, prior_revision_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            revision_id, firm_id, owner_id, trust_id, field_name,
            revision_number, "before", "after", "basis", "source",
            "PROFESSIONAL", 1, "ACTOR", "attorney", prior_revision_id,
            "2026-01-01T00:00:00Z",
        ),
    )


@pytest.fixture
def direct_revision_connection(revision_db):
    connection = sqlite3.connect(revision_db)
    assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 0
    try:
        yield connection
    finally:
        connection.close()


def test_migration_is_additive_idempotent_and_preserves_existing_trust(tmp_path):
    path = tmp_path / "migration.sqlite3"
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE trusts (trust_id TEXT, firm_id TEXT, owner_id TEXT, trust_name TEXT)"
    )
    connection.execute(
        "INSERT INTO trusts VALUES ('TR-1', 'FIRM-1', 'OWNER-1', 'Untouched')"
    )
    connection.commit()
    before = connection.execute("SELECT * FROM trusts").fetchall()
    connection.close()

    apply_trust_field_revision_schema(path)
    apply_trust_field_revision_schema(path)

    assert [tuple(row) for row in _rows(path, "SELECT * FROM trusts")] == before
    assert len(_rows(path, "PRAGMA index_list(trust_field_revisions)")) >= 2


@pytest.mark.parametrize(
    "schema",
    ["", "CREATE TABLE trusts (trust_id TEXT, firm_id TEXT)"],
)
def test_migration_fails_safely_without_required_trust_schema(tmp_path, schema):
    path = tmp_path / "bad-prerequisite.sqlite3"
    if schema:
        connection = sqlite3.connect(path)
        connection.execute(schema)
        connection.close()
    with pytest.raises(TrustFieldRevisionMigrationError):
        apply_trust_field_revision_schema(path)
    assert not _rows(
        path,
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name='trust_field_revisions'",
    )


def test_migration_rolls_back_all_ddl_when_trigger_creation_fails(
    tmp_path, monkeypatch
):
    path = tmp_path / "trigger-denied.sqlite3"
    real_connect = sqlite3.connect
    connection = real_connect(path)
    connection.execute(
        "CREATE TABLE trusts (trust_id TEXT, firm_id TEXT, owner_id TEXT)"
    )
    connection.commit()
    connection.close()

    def connect_with_trigger_denied(*args, **kwargs):
        guarded = real_connect(*args, **kwargs)
        guarded.set_authorizer(
            lambda action, _arg1, _arg2, _database, _source: (
                sqlite3.SQLITE_DENY
                if action == sqlite3.SQLITE_CREATE_TRIGGER
                else sqlite3.SQLITE_OK
            )
        )
        return guarded

    monkeypatch.setattr(revision_migration.sqlite3, "connect", connect_with_trigger_denied)
    with pytest.raises(TrustFieldRevisionMigrationError):
        apply_trust_field_revision_schema(path)

    connection = real_connect(path)
    objects = connection.execute(
        "SELECT type, name FROM sqlite_master "
        "WHERE name = 'trust_field_revisions' "
        "OR name LIKE 'idx_trust_field_revisions_%' "
        "OR name LIKE 'trust_field_revisions_%'"
    ).fetchall()
    connection.close()
    assert objects == []


def test_direct_revision_rejects_nonpositive_number_with_foreign_keys_off(
    direct_revision_connection,
):
    with pytest.raises(sqlite3.IntegrityError, match="invalid_prior_revision"):
        _direct_revision(direct_revision_connection, "REV-ZERO", 0)


def test_direct_revision_rejects_bogus_prior_with_foreign_keys_off(
    direct_revision_connection,
):
    with pytest.raises(sqlite3.IntegrityError, match="invalid_prior_revision"):
        _direct_revision(
            direct_revision_connection, "REV-BOGUS", 2, "DOES-NOT-EXIST"
        )


def test_direct_revision_two_rejects_null_prior_with_foreign_keys_off(
    direct_revision_connection,
):
    with pytest.raises(sqlite3.IntegrityError, match="invalid_prior_revision"):
        _direct_revision(direct_revision_connection, "REV-NULL-SECOND", 2)


def test_direct_revision_one_rejects_nonnull_prior_with_foreign_keys_off(
    direct_revision_connection,
):
    _direct_revision(direct_revision_connection, "REV-1", 1)
    with pytest.raises(sqlite3.IntegrityError, match="invalid_prior_revision"):
        _direct_revision(
            direct_revision_connection, "REV-FIRST-WITH-PRIOR", 1, "REV-1"
        )


def test_direct_revision_rejects_wrong_field_prior_with_foreign_keys_off(
    direct_revision_connection,
):
    _direct_revision(
        direct_revision_connection,
        "REV-OTHER-FIELD",
        1,
        field_name="jurisdiction",
    )
    with pytest.raises(sqlite3.IntegrityError, match="invalid_prior_revision"):
        _direct_revision(
            direct_revision_connection, "REV-WRONG-FIELD", 2, "REV-OTHER-FIELD"
        )


def test_direct_legitimate_revision_chain_succeeds_with_foreign_keys_off(
    direct_revision_connection,
):
    _direct_revision(direct_revision_connection, "REV-1", 1)
    _direct_revision(direct_revision_connection, "REV-2", 2, "REV-1")
    direct_revision_connection.commit()
    assert direct_revision_connection.execute(
        "SELECT revision_id FROM trust_field_revisions "
        "WHERE field_name = 'trust_name' ORDER BY revision_number"
    ).fetchall() == [("REV-1",), ("REV-2",)]


def test_revision_rows_are_append_only(revision_db):
    _update()
    revision_id = _rows(
        revision_db, "SELECT revision_id FROM trust_field_revisions"
    )[0]["revision_id"]
    connection = sqlite3.connect(revision_db)
    with pytest.raises(sqlite3.IntegrityError, match="append_only"):
        connection.execute(
            "UPDATE trust_field_revisions SET provenance='altered' WHERE revision_id=?",
            (revision_id,),
        )
    with pytest.raises(sqlite3.IntegrityError, match="append_only"):
        connection.execute(
            "DELETE FROM trust_field_revisions WHERE revision_id=?", (revision_id,)
        )
    connection.close()


def test_mismatched_scope_revision_insert_is_rejected(revision_db):
    connection = sqlite3.connect(revision_db)
    with pytest.raises(sqlite3.IntegrityError, match="scope_mismatch"):
        connection.execute(
            """
            INSERT INTO trust_field_revisions VALUES (
                'REV-X', 'FIRM-X', 'OWNER-1', 'TR-1', 'trust_name', 1,
                'Original', 'Changed', 'basis', 'source',
                'PROFESSIONAL', 1, 'ACTOR', 'attorney', NULL, '2026-01-01T00:00:00Z'
            )
            """
        )
    connection.close()


def test_first_and_second_same_field_revisions_are_chained(revision_db):
    assert _update()
    assert _update(updates={"trust_name": "Changed Again"})
    revisions = _rows(
        revision_db,
        "SELECT * FROM trust_field_revisions ORDER BY revision_number",
    )
    assert [row["revision_number"] for row in revisions] == [1, 2]
    assert revisions[0]["prior_revision_id"] is None
    assert revisions[1]["prior_revision_id"] == revisions[0]["revision_id"]
    assert revisions[0]["prior_value"] == "Original"
    assert revisions[1]["prior_value"] == "Changed"
    assert revisions[1]["resulting_value"] == "Changed Again"
    assert revisions[0]["created_at"]


def test_multi_field_update_records_each_change_and_preserves_null(revision_db):
    assert _update(
        updates={"trust_name": "Changed", "jurisdiction": "DC", "notes": ""}
    )
    revisions = _rows(
        revision_db,
        "SELECT field_name, prior_value, resulting_value, revision_number "
        "FROM trust_field_revisions ORDER BY field_name",
    )
    assert len(revisions) == 3
    assert {row["field_name"] for row in revisions} == {
        "trust_name", "jurisdiction", "notes"
    }
    notes = next(row for row in revisions if row["field_name"] == "notes")
    assert notes["prior_value"] is None
    assert notes["resulting_value"] == ""
    assert all(row["revision_number"] == 1 for row in revisions)


def test_unchanged_values_create_no_revisions(revision_db):
    assert not _update(updates={"trust_name": "Original", "notes": None})
    assert not _rows(revision_db, "SELECT * FROM trust_field_revisions")


@pytest.mark.parametrize("field", ["firm_id", "owner_id", "trust_id"])
def test_identity_mutation_is_prohibited_without_mutation(revision_db, field):
    with pytest.raises(ValueError, match="identity fields cannot change"):
        _update(updates={field: "DIFFERENT"})
    assert _rows(revision_db, "SELECT trust_name FROM trusts WHERE trust_id='TR-1'")[0][0] == "Original"
    assert not _rows(revision_db, "SELECT * FROM trust_field_revisions")


@pytest.mark.parametrize(
    "metadata_name",
    ["revision_basis", "provenance", "actor_id", "actor_capacity"],
)
def test_missing_provenance_metadata_fails_without_mutation(revision_db, metadata_name):
    with pytest.raises(ValueError, match="missing provenance metadata"):
        _update(**{metadata_name: ""})
    assert not _rows(revision_db, "SELECT * FROM trust_field_revisions")
    assert _rows(revision_db, "SELECT trust_name FROM trusts WHERE trust_id='TR-1'")[0][0] == "Original"


def test_system_suggested_and_unconfirmed_mutations_fail(revision_db):
    with pytest.raises(ValueError, match="SYSTEM_SUGGESTED"):
        _update(decision_origin="SYSTEM_SUGGESTED")
    with pytest.raises(ValueError, match="human confirmation"):
        _update(human_confirmed=False)
    assert not _rows(revision_db, "SELECT * FROM trust_field_revisions")
    assert _rows(revision_db, "SELECT trust_name FROM trusts WHERE trust_id='TR-1'")[0][0] == "Original"


@pytest.mark.parametrize(
    "scope",
    [{"firm_id": "FIRM-2"}, {"owner_id": "OWNER-2"}],
)
def test_cross_scope_update_fails_without_mutation(revision_db, scope):
    with pytest.raises(LookupError, match="not found"):
        _update(**scope)
    assert not _rows(revision_db, "SELECT * FROM trust_field_revisions")
    assert _rows(revision_db, "SELECT trust_name FROM trusts WHERE trust_id='TR-1'")[0][0] == "Original"


def test_unknown_trust_field_is_rejected_without_mutation(revision_db):
    with pytest.raises(ValueError, match="unknown Trust columns"):
        _update(updates={"not_a_trust_field": "value"})
    assert not _rows(revision_db, "SELECT * FROM trust_field_revisions")
    assert _rows(revision_db, "SELECT trust_name FROM trusts WHERE trust_id='TR-1'")[0][0] == "Original"


def test_forced_second_revision_failure_rolls_back_everything(revision_db):
    connection = sqlite3.connect(revision_db)
    connection.execute(
        """
        CREATE TRIGGER deterministic_revision_failure
        BEFORE INSERT ON trust_field_revisions
        WHEN NEW.field_name = 'jurisdiction'
        BEGIN
            SELECT RAISE(ABORT, 'forced_revision_failure');
        END
        """
    )
    connection.close()

    with pytest.raises(sqlite3.IntegrityError, match="forced_revision_failure"):
        _update(updates={"trust_name": "Changed", "jurisdiction": "DC"})

    assert not _rows(revision_db, "SELECT * FROM trust_field_revisions")
    trust = _rows(
        revision_db,
        "SELECT trust_name, jurisdiction FROM trusts WHERE trust_id='TR-1'",
    )[0]
    assert tuple(trust) == ("Original", "VA")


def test_forced_trust_update_failure_rolls_back_all_revisions(revision_db):
    connection = sqlite3.connect(revision_db)
    connection.execute(
        """
        CREATE TRIGGER deterministic_trust_update_failure
        BEFORE UPDATE ON trusts
        BEGIN
            SELECT RAISE(ABORT, 'forced_trust_update_failure');
        END
        """
    )
    connection.close()

    with pytest.raises(sqlite3.IntegrityError, match="forced_trust_update_failure"):
        _update(updates={"trust_name": "Changed", "jurisdiction": "DC"})

    assert not _rows(revision_db, "SELECT * FROM trust_field_revisions")
    trust = _rows(
        revision_db,
        "SELECT trust_name, jurisdiction FROM trusts WHERE trust_id='TR-1'",
    )[0]
    assert tuple(trust) == ("Original", "VA")
