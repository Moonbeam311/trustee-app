import sqlite3

import pytest

from database.migrations_person_identity_schema import (
    PERSON_REQUIRED_COLUMNS,
    PersonIdentityMigrationError,
    apply_person_identity_schema,
)


def _table_exists(db_path, table):
    con = sqlite3.connect(db_path)
    try:
        return con.execute(
            """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type='table' AND name=?
            """,
            (table,),
        ).fetchone()[0] == 1
    finally:
        con.close()


def _columns(db_path, table):
    con = sqlite3.connect(db_path)
    try:
        return {
            row[1]
            for row in con.execute(
                f"PRAGMA table_info({table})"
            )
        }
    finally:
        con.close()


def test_person_identity_schema_is_additive_and_idempotent(tmp_path):
    db_path = tmp_path / "fresh.db"

    first = apply_person_identity_schema(db_path)
    second = apply_person_identity_schema(db_path)

    assert first["schema_complete"] is True
    assert first["persons_table_created"] is True
    assert first["person_rows_backfilled"] == 0
    assert first["records_created"] == 0

    assert second["schema_complete"] is True
    assert second["persons_table_created"] is False
    assert second["person_rows_backfilled"] == 0
    assert second["records_created"] == 0

    assert _table_exists(db_path, "persons")
    assert PERSON_REQUIRED_COLUMNS <= _columns(db_path, "persons")

    con = sqlite3.connect(db_path)
    try:
        assert con.execute(
            "SELECT COUNT(*) FROM persons"
        ).fetchone()[0] == 0
    finally:
        con.close()


def test_existing_person_identity_rows_are_preserved(tmp_path):
    db_path = tmp_path / "existing.db"

    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE persons (
                person_id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                firm_id TEXT NOT NULL,
                display_name TEXT NOT NULL,
                sort_name TEXT,
                notes TEXT,
                created_by TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        con.execute(
            """
            INSERT INTO persons (
                person_id,
                owner_id,
                firm_id,
                display_name,
                sort_name,
                notes,
                created_by,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "PER-KEEP-001",
                "OWNER-KEEP",
                "FIRM-KEEP",
                "Existing Person",
                "Person, Existing",
                "sentinel",
                "tester",
                "2026-09-14T00:00:00",
                "2026-09-14T00:00:00",
            ),
        )
        con.commit()

        before = con.execute(
            "SELECT * FROM persons WHERE person_id='PER-KEEP-001'"
        ).fetchone()
    finally:
        con.close()

    result = apply_person_identity_schema(db_path)

    con = sqlite3.connect(db_path)
    try:
        after = con.execute(
            "SELECT * FROM persons WHERE person_id='PER-KEEP-001'"
        ).fetchone()
    finally:
        con.close()

    assert result["persons_table_created"] is False
    assert result["person_rows_preserved"] == 1
    assert result["person_rows_backfilled"] == 0
    assert result["records_created"] == 0
    assert after == before


def test_person_identity_does_not_infer_from_role_or_genealogy_records(
    tmp_path,
):
    db_path = tmp_path / "roles.db"

    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE beneficiaries (
                beneficiary_id TEXT,
                full_name TEXT
            )
            """
        )
        con.execute(
            """
            CREATE TABLE fiduciaries (
                fiduciary_id TEXT,
                full_name TEXT
            )
            """
        )
        con.execute(
            """
            CREATE TABLE genealogy_records (
                genealogy_id TEXT,
                full_name TEXT
            )
            """
        )

        con.execute(
            "INSERT INTO beneficiaries VALUES ('BEN-1', 'Same Name')"
        )
        con.execute(
            "INSERT INTO fiduciaries VALUES ('FID-1', 'Same Name')"
        )
        con.execute(
            "INSERT INTO genealogy_records VALUES ('GEN-1', 'Same Name')"
        )
        con.commit()
    finally:
        con.close()

    result = apply_person_identity_schema(db_path)

    con = sqlite3.connect(db_path)
    try:
        person_count = con.execute(
            "SELECT COUNT(*) FROM persons"
        ).fetchone()[0]

        beneficiary_count = con.execute(
            "SELECT COUNT(*) FROM beneficiaries"
        ).fetchone()[0]

        fiduciary_count = con.execute(
            "SELECT COUNT(*) FROM fiduciaries"
        ).fetchone()[0]

        genealogy_count = con.execute(
            "SELECT COUNT(*) FROM genealogy_records"
        ).fetchone()[0]
    finally:
        con.close()

    assert result["person_rows_backfilled"] == 0
    assert result["records_created"] == 0
    assert person_count == 0

    assert beneficiary_count == 1
    assert fiduciary_count == 1
    assert genealogy_count == 1


def test_malformed_existing_person_table_is_rejected(tmp_path):
    db_path = tmp_path / "malformed.db"

    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE persons (
                person_id TEXT PRIMARY KEY,
                display_name TEXT
            )
            """
        )
        con.commit()
    finally:
        con.close()

    with pytest.raises(
        PersonIdentityMigrationError,
        match="existing persons table missing required columns",
    ):
        apply_person_identity_schema(db_path)
