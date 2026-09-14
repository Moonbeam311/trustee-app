import sqlite3

from database.startup_migrations import (
    run_additive_startup_migrations,
)


def _count(db_path, table):
    con = sqlite3.connect(db_path)
    try:
        return con.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
    finally:
        con.close()


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


def test_startup_registers_person_identity_without_inferred_rows(
    tmp_path,
):
    db_path = tmp_path / "person-startup.db"

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
            """
            INSERT INTO beneficiaries
            VALUES ('BEN-P1', 'Example Person')
            """
        )
        con.execute(
            """
            INSERT INTO fiduciaries
            VALUES ('FID-P1', 'Example Person')
            """
        )
        con.execute(
            """
            INSERT INTO genealogy_records
            VALUES ('GEN-P1', 'Example Person')
            """
        )
        con.commit()
    finally:
        con.close()

    result = run_additive_startup_migrations(db_path)
    person = result["person_identity_schema"]

    assert person["schema_complete"] is True
    assert person["deferred"] is False
    assert person["persons_table_created"] is True
    assert person["person_rows_backfilled"] == 0
    assert person["records_created"] == 0

    assert _table_exists(db_path, "persons")
    assert _count(db_path, "persons") == 0

    assert _count(db_path, "beneficiaries") == 1
    assert _count(db_path, "fiduciaries") == 1
    assert _count(db_path, "genealogy_records") == 1


def test_repeated_startup_keeps_person_identity_idempotent(
    tmp_path,
):
    db_path = tmp_path / "person-repeat.db"

    first = run_additive_startup_migrations(db_path)
    second = run_additive_startup_migrations(db_path)

    first_person = first["person_identity_schema"]
    second_person = second["person_identity_schema"]

    assert first_person["schema_complete"] is True
    assert first_person["persons_table_created"] is True

    assert second_person["schema_complete"] is True
    assert second_person["deferred"] is False
    assert second_person["persons_table_created"] is False
    assert second_person["person_rows_backfilled"] == 0
    assert second_person["records_created"] == 0

    assert _count(db_path, "persons") == 0


def test_startup_defers_malformed_existing_person_schema(
    tmp_path,
):
    db_path = tmp_path / "person-malformed.db"

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
        con.execute(
            """
            INSERT INTO persons
                (person_id, display_name)
            VALUES
                ('PER-LEGACY-001', 'Legacy Person')
            """
        )
        con.commit()
    finally:
        con.close()

    result = run_additive_startup_migrations(db_path)
    person = result["person_identity_schema"]

    assert person["schema_complete"] is False
    assert person["deferred"] is True
    assert person["persons_table_created"] is False
    assert person["person_rows_backfilled"] == 0
    assert person["records_created"] == 0

    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT person_id, display_name
            FROM persons
            WHERE person_id='PER-LEGACY-001'
            """
        ).fetchone()
    finally:
        con.close()

    assert row == (
        "PER-LEGACY-001",
        "Legacy Person",
    )
