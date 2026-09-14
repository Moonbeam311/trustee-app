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


def test_startup_creates_empty_role_link_schema_without_inference(
    tmp_path,
):
    db_path = tmp_path / "role-link-startup.db"

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
            VALUES ('BEN-RL1', 'Same Name')
            """
        )
        con.execute(
            """
            INSERT INTO fiduciaries
            VALUES ('FID-RL1', 'Same Name')
            """
        )
        con.execute(
            """
            INSERT INTO genealogy_records
            VALUES ('GEN-RL1', 'Same Name')
            """
        )
        con.commit()
    finally:
        con.close()

    result = run_additive_startup_migrations(db_path)
    role_link = result["person_role_link_schema"]

    assert role_link["schema_complete"] is True
    assert role_link["deferred"] is False
    assert role_link["person_role_links_table_created"] is True
    assert role_link["person_role_link_rows_backfilled"] == 0
    assert role_link["records_created"] == 0

    assert _table_exists(db_path, "person_role_links")
    assert _count(db_path, "person_role_links") == 0

    assert _count(db_path, "beneficiaries") == 1
    assert _count(db_path, "fiduciaries") == 1
    assert _count(db_path, "genealogy_records") == 1


def test_repeated_startup_keeps_role_link_schema_idempotent(
    tmp_path,
):
    db_path = tmp_path / "role-link-repeat.db"

    first = run_additive_startup_migrations(db_path)
    second = run_additive_startup_migrations(db_path)

    first_role = first["person_role_link_schema"]
    second_role = second["person_role_link_schema"]

    assert first_role["schema_complete"] is True
    assert first_role["person_role_links_table_created"] is True

    assert second_role["schema_complete"] is True
    assert second_role["deferred"] is False
    assert second_role["person_role_links_table_created"] is False
    assert second_role["person_role_link_rows_backfilled"] == 0
    assert second_role["records_created"] == 0

    assert _count(db_path, "person_role_links") == 0


def test_startup_defers_malformed_role_link_schema(
    tmp_path,
):
    db_path = tmp_path / "role-link-malformed.db"

    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE person_role_links (
                link_id TEXT PRIMARY KEY,
                person_id TEXT
            )
            """
        )
        con.execute(
            """
            INSERT INTO person_role_links
            VALUES ('PRL-LEGACY-001', 'PER-LEGACY-001')
            """
        )
        con.commit()
    finally:
        con.close()

    result = run_additive_startup_migrations(db_path)
    role_link = result["person_role_link_schema"]

    assert role_link["schema_complete"] is False
    assert role_link["deferred"] is True
    assert role_link["person_role_links_table_created"] is False
    assert role_link["person_role_link_rows_backfilled"] == 0
    assert role_link["records_created"] == 0

    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT link_id, person_id
            FROM person_role_links
            WHERE link_id='PRL-LEGACY-001'
            """
        ).fetchone()
    finally:
        con.close()

    assert row == (
        "PRL-LEGACY-001",
        "PER-LEGACY-001",
    )
