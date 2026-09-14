import sqlite3

import pytest

from database.migrations_person_role_link_schema import (
    PERSON_ROLE_LINK_REQUIRED_COLUMNS,
    PersonRoleLinkMigrationError,
    apply_person_role_link_schema,
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


def test_role_link_schema_is_additive_and_idempotent(
    tmp_path,
):
    db_path = tmp_path / "fresh.db"

    first = apply_person_role_link_schema(db_path)
    second = apply_person_role_link_schema(db_path)

    assert first["schema_complete"] is True
    assert first["person_role_links_table_created"] is True
    assert first["person_role_link_rows_backfilled"] == 0
    assert first["records_created"] == 0

    assert second["schema_complete"] is True
    assert second["person_role_links_table_created"] is False
    assert second["person_role_link_rows_backfilled"] == 0
    assert second["records_created"] == 0

    assert _table_exists(
        db_path,
        "person_role_links",
    )

    assert (
        PERSON_ROLE_LINK_REQUIRED_COLUMNS
        <= _columns(db_path, "person_role_links")
    )

    con = sqlite3.connect(db_path)
    try:
        assert con.execute(
            "SELECT COUNT(*) FROM person_role_links"
        ).fetchone()[0] == 0
    finally:
        con.close()


def test_existing_explicit_role_link_is_preserved(
    tmp_path,
):
    db_path = tmp_path / "existing.db"

    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE person_role_links (
                link_id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                firm_id TEXT NOT NULL,
                person_id TEXT NOT NULL,
                role_type TEXT NOT NULL,
                role_record_id TEXT NOT NULL,
                trust_id TEXT,
                capacity_label TEXT,
                notes TEXT,
                created_by TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )

        con.execute(
            """
            INSERT INTO person_role_links (
                link_id,
                owner_id,
                firm_id,
                person_id,
                role_type,
                role_record_id,
                trust_id,
                capacity_label,
                notes,
                created_by,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "PRL-KEEP-001",
                "OWNER-KEEP",
                "FIRM-KEEP",
                "PER-KEEP-001",
                "fiduciary",
                "FID-KEEP-001",
                "TR-KEEP",
                "Trustee",
                "sentinel",
                "tester",
                "2026-09-14T00:00:00",
                "2026-09-14T00:00:00",
            ),
        )

        con.commit()

        before = con.execute(
            """
            SELECT *
            FROM person_role_links
            WHERE link_id='PRL-KEEP-001'
            """
        ).fetchone()
    finally:
        con.close()

    result = apply_person_role_link_schema(db_path)

    con = sqlite3.connect(db_path)
    try:
        after = con.execute(
            """
            SELECT *
            FROM person_role_links
            WHERE link_id='PRL-KEEP-001'
            """
        ).fetchone()
    finally:
        con.close()

    assert result["person_role_links_table_created"] is False
    assert result["person_role_link_rows_preserved"] == 1
    assert result["person_role_link_rows_backfilled"] == 0
    assert result["records_created"] == 0
    assert after == before


def test_role_links_are_not_inferred_from_existing_roles(
    tmp_path,
):
    db_path = tmp_path / "roles.db"

    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE persons (
                person_id TEXT,
                display_name TEXT
            )
            """
        )

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
            INSERT INTO persons
            VALUES ('PER-1', 'Same Name')
            """
        )

        con.execute(
            """
            INSERT INTO beneficiaries
            VALUES ('BEN-1', 'Same Name')
            """
        )

        con.execute(
            """
            INSERT INTO fiduciaries
            VALUES ('FID-1', 'Same Name')
            """
        )

        con.execute(
            """
            INSERT INTO genealogy_records
            VALUES ('GEN-1', 'Same Name')
            """
        )

        con.commit()
    finally:
        con.close()

    result = apply_person_role_link_schema(db_path)

    con = sqlite3.connect(db_path)
    try:
        link_count = con.execute(
            "SELECT COUNT(*) FROM person_role_links"
        ).fetchone()[0]

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

    assert result["person_role_link_rows_backfilled"] == 0
    assert result["records_created"] == 0
    assert link_count == 0

    assert person_count == 1
    assert beneficiary_count == 1
    assert fiduciary_count == 1
    assert genealogy_count == 1


def test_malformed_existing_role_link_table_is_rejected(
    tmp_path,
):
    db_path = tmp_path / "malformed.db"

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
        con.commit()
    finally:
        con.close()

    with pytest.raises(
        PersonRoleLinkMigrationError,
        match=(
            "existing person_role_links table "
            "missing required columns"
        ),
    ):
        apply_person_role_link_schema(db_path)
