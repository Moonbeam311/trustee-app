import sqlite3

from database.migrations_genealogy_relationship_schema import (
    apply_genealogy_relationship_schema,
)
from database.startup_migrations import run_additive_startup_migrations


def _count(db_path, table):
    con = sqlite3.connect(db_path)

    try:
        return con.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
    finally:
        con.close()


def test_startup_creates_empty_review_history_without_status_inference(
    tmp_path,
):
    db_path = tmp_path / "review-startup.db"

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
                assertion_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "GRA-STARTUP-001",
                "OWNER-A",
                "FIRM-A",
                "PER-A",
                "PARENT_OF",
                "PER-B",
                "USER_ASSERTED",
            ),
        )
        con.commit()
    finally:
        con.close()

    result = run_additive_startup_migrations(str(db_path))

    review = result[
        "genealogy_relationship_review_schema"
    ]

    assert review["schema_complete"] is True
    assert review["deferred"] is False
    assert review[
        "genealogy_relationship_review_table_created"
    ] is True
    assert review[
        "genealogy_relationship_review_rows_backfilled"
    ] == 0
    assert review["records_created"] == 0

    assert _count(
        db_path,
        "genealogy_relationship_reviews",
    ) == 0

    con = sqlite3.connect(db_path)

    try:
        status = con.execute(
            """
            SELECT assertion_status
            FROM genealogy_relationship_assertions
            WHERE assertion_id='GRA-STARTUP-001'
            """
        ).fetchone()[0]
    finally:
        con.close()

    assert status == "USER_ASSERTED"


def test_review_history_startup_is_idempotent(
    tmp_path,
):
    db_path = tmp_path / "review-startup-repeat.db"

    first = run_additive_startup_migrations(str(db_path))
    second = run_additive_startup_migrations(str(db_path))

    first_review = first[
        "genealogy_relationship_review_schema"
    ]
    second_review = second[
        "genealogy_relationship_review_schema"
    ]

    assert first_review[
        "genealogy_relationship_review_table_created"
    ] is True

    assert second_review[
        "genealogy_relationship_review_table_created"
    ] is False

    assert second_review[
        "genealogy_relationship_review_rows_preserved"
    ] == 0

    assert second_review[
        "genealogy_relationship_review_rows_backfilled"
    ] == 0

    assert second_review["records_created"] == 0

    assert _count(
        db_path,
        "genealogy_relationship_reviews",
    ) == 0


def test_malformed_review_table_is_deferred_and_preserved(
    tmp_path,
):
    db_path = tmp_path / "review-startup-malformed.db"

    con = sqlite3.connect(db_path)

    try:
        con.execute(
            """
            CREATE TABLE genealogy_relationship_reviews (
                review_id TEXT PRIMARY KEY,
                assertion_id TEXT
            )
            """
        )

        con.execute(
            """
            INSERT INTO genealogy_relationship_reviews (
                review_id,
                assertion_id
            ) VALUES (?, ?)
            """,
            (
                "GRR-MALFORMED-KEEP",
                "GRA-KEEP",
            ),
        )

        con.commit()
    finally:
        con.close()

    result = run_additive_startup_migrations(str(db_path))

    review = result[
        "genealogy_relationship_review_schema"
    ]

    assert review["schema_complete"] is False
    assert review["deferred"] is True
    assert (
        "missing required columns"
        in review["reason"]
    )

    con = sqlite3.connect(db_path)

    try:
        row = con.execute(
            """
            SELECT review_id, assertion_id
            FROM genealogy_relationship_reviews
            """
        ).fetchone()
    finally:
        con.close()

    assert row == (
        "GRR-MALFORMED-KEEP",
        "GRA-KEEP",
    )
