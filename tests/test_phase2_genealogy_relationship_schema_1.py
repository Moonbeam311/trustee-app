import sqlite3

import pytest

from database.migrations_genealogy_relationship_schema import (
    GENEALOGY_RELATIONSHIP_REQUIRED_COLUMNS,
    GENEALOGY_RELATIONSHIP_STATUSES,
    GenealogyRelationshipMigrationError,
    apply_genealogy_relationship_schema,
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


def test_relationship_schema_is_additive_and_idempotent(
    tmp_path,
):
    db_path = tmp_path / "fresh.db"

    first = apply_genealogy_relationship_schema(db_path)
    second = apply_genealogy_relationship_schema(db_path)

    assert first["schema_complete"] is True
    assert first["genealogy_relationship_table_created"] is True
    assert first["genealogy_relationship_rows_backfilled"] == 0
    assert first["records_created"] == 0

    assert second["schema_complete"] is True
    assert second["genealogy_relationship_table_created"] is False
    assert second["genealogy_relationship_rows_backfilled"] == 0
    assert second["records_created"] == 0

    assert _table_exists(
        db_path,
        "genealogy_relationship_assertions",
    )

    assert (
        GENEALOGY_RELATIONSHIP_REQUIRED_COLUMNS
        <= _columns(
            db_path,
            "genealogy_relationship_assertions",
        )
    )

    assert GENEALOGY_RELATIONSHIP_STATUSES == (
        "USER_ASSERTED",
        "REVIEW_REQUIRED",
        "CONFIRMED",
        "CONFLICTING",
        "UNRESOLVED",
    )

    con = sqlite3.connect(db_path)
    try:
        assert con.execute(
            """
            SELECT COUNT(*)
            FROM genealogy_relationship_assertions
            """
        ).fetchone()[0] == 0
    finally:
        con.close()


def test_existing_explicit_relationship_assertion_is_preserved(
    tmp_path,
):
    db_path = tmp_path / "existing.db"

    apply_genealogy_relationship_schema(db_path)

    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            INSERT INTO genealogy_relationship_assertions (
                assertion_id,
                owner_id,
                firm_id,
                subject_person_id,
                relationship_type,
                related_person_id,
                trust_id,
                legacy_genealogy_id,
                assertion_status,
                assertion_basis,
                notes,
                created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "GRA-KEEP-001",
                "OWNER-KEEP",
                "FIRM-KEEP",
                "PER-A",
                "PARENT_OF",
                "PER-B",
                "TR-KEEP",
                "GEN-KEEP",
                "USER_ASSERTED",
                "explicit operator assertion",
                "sentinel",
                "tester",
            ),
        )
        con.commit()

        before = con.execute(
            """
            SELECT *
            FROM genealogy_relationship_assertions
            WHERE assertion_id='GRA-KEEP-001'
            """
        ).fetchone()
    finally:
        con.close()

    result = apply_genealogy_relationship_schema(db_path)

    con = sqlite3.connect(db_path)
    try:
        after = con.execute(
            """
            SELECT *
            FROM genealogy_relationship_assertions
            WHERE assertion_id='GRA-KEEP-001'
            """
        ).fetchone()
    finally:
        con.close()

    assert result["genealogy_relationship_table_created"] is False
    assert result["genealogy_relationship_rows_preserved"] == 1
    assert result["genealogy_relationship_rows_backfilled"] == 0
    assert result["records_created"] == 0
    assert after == before


def test_legacy_parent_spouse_text_does_not_infer_relationships(
    tmp_path,
):
    db_path = tmp_path / "legacy.db"

    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE persons (
                person_id TEXT,
                owner_id TEXT,
                firm_id TEXT,
                display_name TEXT
            )
            """
        )

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
            INSERT INTO persons
            VALUES (
                'PER-1',
                'OWNER-A',
                'FIRM-A',
                'Same Name'
            )
            """
        )

        con.execute(
            """
            INSERT INTO genealogy_records
            VALUES (
                'GEN-1',
                'Same Name',
                'Parent One',
                'Parent Two',
                'Spouse Name'
            )
            """
        )

        con.commit()
    finally:
        con.close()

    result = apply_genealogy_relationship_schema(db_path)

    con = sqlite3.connect(db_path)
    try:
        assertion_count = con.execute(
            """
            SELECT COUNT(*)
            FROM genealogy_relationship_assertions
            """
        ).fetchone()[0]

        genealogy_row = con.execute(
            """
            SELECT
                genealogy_id,
                full_name,
                parent_1,
                parent_2,
                spouse
            FROM genealogy_records
            WHERE genealogy_id='GEN-1'
            """
        ).fetchone()
    finally:
        con.close()

    assert result["genealogy_relationship_rows_backfilled"] == 0
    assert result["records_created"] == 0
    assert assertion_count == 0

    assert genealogy_row == (
        "GEN-1",
        "Same Name",
        "Parent One",
        "Parent Two",
        "Spouse Name",
    )


def test_relationship_schema_does_not_create_duplicate_evidence_store(
    tmp_path,
):
    db_path = tmp_path / "evidence-boundary.db"

    apply_genealogy_relationship_schema(db_path)

    assert not _table_exists(
        db_path,
        "genealogy_relationship_evidence",
    )

    assert not _table_exists(
        db_path,
        "genealogy_media_records",
    )


def test_malformed_existing_relationship_table_is_rejected(
    tmp_path,
):
    db_path = tmp_path / "malformed.db"

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
        con.commit()
    finally:
        con.close()

    with pytest.raises(
        GenealogyRelationshipMigrationError,
        match=(
            "existing genealogy_relationship_assertions table "
            "missing required columns"
        ),
    ):
        apply_genealogy_relationship_schema(db_path)
