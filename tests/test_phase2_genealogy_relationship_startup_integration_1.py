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


def test_startup_creates_empty_genealogy_relationship_schema_without_inference(
    tmp_path,
):
    db_path = tmp_path / "genealogy-startup.db"

    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE genealogy_records (
                genealogy_id TEXT,
                full_name TEXT,
                parent_1 TEXT,
                parent_2 TEXT,
                spouse TEXT
            )
            """
        )
        con.execute(
            """
            INSERT INTO genealogy_records
            VALUES (
                'GEN-START-001',
                'Example Person',
                'Parent One',
                'Parent Two',
                'Spouse Example'
            )
            """
        )
        con.commit()
    finally:
        con.close()

    result = run_additive_startup_migrations(db_path)
    genealogy = result["genealogy_relationship_schema"]

    assert genealogy["schema_complete"] is True
    assert genealogy["deferred"] is False
    assert genealogy["genealogy_relationship_table_created"] is True
    assert genealogy["genealogy_relationship_rows_backfilled"] == 0
    assert genealogy["records_created"] == 0

    assert _table_exists(
        db_path,
        "genealogy_relationship_assertions",
    )
    assert _count(
        db_path,
        "genealogy_relationship_assertions",
    ) == 0

    assert _count(db_path, "genealogy_records") == 1


def test_repeated_startup_keeps_genealogy_relationship_schema_idempotent(
    tmp_path,
):
    db_path = tmp_path / "genealogy-repeat.db"

    first = run_additive_startup_migrations(db_path)
    second = run_additive_startup_migrations(db_path)

    first_genealogy = first["genealogy_relationship_schema"]
    second_genealogy = second["genealogy_relationship_schema"]

    assert first_genealogy["schema_complete"] is True
    assert first_genealogy[
        "genealogy_relationship_table_created"
    ] is True

    assert second_genealogy["schema_complete"] is True
    assert second_genealogy["deferred"] is False
    assert second_genealogy[
        "genealogy_relationship_table_created"
    ] is False
    assert second_genealogy[
        "genealogy_relationship_rows_backfilled"
    ] == 0
    assert second_genealogy["records_created"] == 0

    assert _count(
        db_path,
        "genealogy_relationship_assertions",
    ) == 0


def test_startup_defers_malformed_genealogy_relationship_schema(
    tmp_path,
):
    db_path = tmp_path / "genealogy-malformed.db"

    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE genealogy_relationship_assertions (
                assertion_id TEXT PRIMARY KEY,
                subject_person_id TEXT
            )
            """
        )
        con.execute(
            """
            INSERT INTO genealogy_relationship_assertions
            VALUES (
                'GRA-LEGACY-001',
                'PER-LEGACY-001'
            )
            """
        )
        con.commit()
    finally:
        con.close()

    result = run_additive_startup_migrations(db_path)
    genealogy = result["genealogy_relationship_schema"]

    assert genealogy["schema_complete"] is False
    assert genealogy["deferred"] is True
    assert genealogy[
        "genealogy_relationship_table_created"
    ] is False
    assert genealogy[
        "genealogy_relationship_rows_backfilled"
    ] == 0
    assert genealogy["records_created"] == 0

    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT assertion_id, subject_person_id
            FROM genealogy_relationship_assertions
            WHERE assertion_id='GRA-LEGACY-001'
            """
        ).fetchone()
    finally:
        con.close()

    assert row == (
        "GRA-LEGACY-001",
        "PER-LEGACY-001",
    )
