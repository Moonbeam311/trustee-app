import sqlite3

import pytest

from database.migrations_genealogy_relationship_review_schema import (
    ASSERTION_STATUSES,
    DECISION_ORIGINS,
    GenealogyRelationshipReviewMigrationError,
    apply_genealogy_relationship_review_schema,
)
from database.migrations_genealogy_relationship_schema import (
    apply_genealogy_relationship_schema,
)


def _count(db_path, table):
    con = sqlite3.connect(db_path)

    try:
        return con.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
    finally:
        con.close()


def _columns(db_path, table):
    con = sqlite3.connect(db_path)

    try:
        return {
            row[1]
            for row in con.execute(
                f"PRAGMA table_info({table})"
            ).fetchall()
        }
    finally:
        con.close()


def test_review_schema_is_additive_empty_and_idempotent(
    tmp_path,
):
    db_path = tmp_path / "genealogy-review.db"

    apply_genealogy_relationship_schema(db_path)

    first = apply_genealogy_relationship_review_schema(
        db_path
    )
    second = apply_genealogy_relationship_review_schema(
        db_path
    )

    assert first["schema_complete"] is True
    assert first[
        "genealogy_relationship_review_table_created"
    ] is True
    assert first[
        "genealogy_relationship_review_rows_backfilled"
    ] == 0
    assert first["records_created"] == 0

    assert second["schema_complete"] is True
    assert second[
        "genealogy_relationship_review_table_created"
    ] is False
    assert second[
        "genealogy_relationship_review_rows_backfilled"
    ] == 0
    assert second["records_created"] == 0

    assert _count(
        db_path,
        "genealogy_relationship_reviews",
    ) == 0

    assert {
        "review_id",
        "owner_id",
        "firm_id",
        "assertion_id",
        "prior_review_id",
        "prior_status",
        "new_status",
        "review_basis",
        "provenance",
        "decision_origin",
        "human_confirmed",
        "actor",
        "actor_capacity",
        "professional_authority",
        "created_at",
    } <= _columns(
        db_path,
        "genealogy_relationship_reviews",
    )

    assert ASSERTION_STATUSES == (
        "USER_ASSERTED",
        "REVIEW_REQUIRED",
        "CONFIRMED",
        "CONFLICTING",
        "UNRESOLVED",
    )

    assert DECISION_ORIGINS == (
        "SYSTEM_SUGGESTED",
        "OPERATOR_OR_FIDUCIARY",
        "PROFESSIONAL",
    )


def test_existing_assertions_do_not_create_review_history(
    tmp_path,
):
    db_path = tmp_path / "no-auto-review.db"

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
                "GRA-001",
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

    apply_genealogy_relationship_review_schema(
        db_path
    )

    assert _count(
        db_path,
        "genealogy_relationship_assertions",
    ) == 1

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
            WHERE assertion_id='GRA-001'
            """
        ).fetchone()[0]
    finally:
        con.close()

    assert status == "USER_ASSERTED"


def test_existing_explicit_review_record_is_preserved(
    tmp_path,
):
    db_path = tmp_path / "preserve-review.db"

    apply_genealogy_relationship_schema(db_path)
    apply_genealogy_relationship_review_schema(
        db_path
    )

    con = sqlite3.connect(db_path)

    try:
        con.execute(
            """
            INSERT INTO genealogy_relationship_reviews (
                review_id,
                owner_id,
                firm_id,
                assertion_id,
                prior_review_id,
                prior_status,
                new_status,
                review_basis,
                provenance,
                decision_origin,
                human_confirmed,
                actor,
                actor_capacity,
                professional_authority
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "GRR-KEEP-001",
                "OWNER-A",
                "FIRM-A",
                "GRA-001",
                None,
                "USER_ASSERTED",
                "REVIEW_REQUIRED",
                "Review requested",
                "Operator review record",
                "OPERATOR_OR_FIDUCIARY",
                1,
                "operator-a",
                "Trustee",
                None,
            ),
        )
        con.commit()
    finally:
        con.close()

    result = apply_genealogy_relationship_review_schema(
        db_path
    )

    assert result[
        "genealogy_relationship_review_rows_preserved"
    ] == 1
    assert result["records_created"] == 0

    con = sqlite3.connect(db_path)

    try:
        row = con.execute(
            """
            SELECT
                review_id,
                prior_status,
                new_status,
                actor,
                actor_capacity
            FROM genealogy_relationship_reviews
            WHERE review_id='GRR-KEEP-001'
            """
        ).fetchone()
    finally:
        con.close()

    assert row == (
        "GRR-KEEP-001",
        "USER_ASSERTED",
        "REVIEW_REQUIRED",
        "operator-a",
        "Trustee",
    )


def test_review_history_is_append_only(
    tmp_path,
):
    db_path = tmp_path / "append-only-review.db"

    apply_genealogy_relationship_review_schema(
        db_path
    )

    con = sqlite3.connect(db_path)

    try:
        con.execute(
            """
            INSERT INTO genealogy_relationship_reviews (
                review_id,
                owner_id,
                firm_id,
                assertion_id,
                prior_status,
                new_status,
                review_basis,
                provenance,
                decision_origin,
                human_confirmed,
                actor,
                actor_capacity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "GRR-001",
                "OWNER-A",
                "FIRM-A",
                "GRA-001",
                "USER_ASSERTED",
                "REVIEW_REQUIRED",
                "Review requested",
                "Test provenance",
                "OPERATOR_OR_FIDUCIARY",
                1,
                "operator-a",
                "Trustee",
            ),
        )
        con.commit()

        with pytest.raises(
            sqlite3.IntegrityError,
            match="append-only",
        ):
            con.execute(
                """
                UPDATE genealogy_relationship_reviews
                SET review_basis='changed'
                WHERE review_id='GRR-001'
                """
            )

        con.rollback()

        with pytest.raises(
            sqlite3.IntegrityError,
            match="append-only",
        ):
            con.execute(
                """
                DELETE FROM genealogy_relationship_reviews
                WHERE review_id='GRR-001'
                """
            )

        con.rollback()

    finally:
        con.close()

    assert _count(
        db_path,
        "genealogy_relationship_reviews",
    ) == 1


def test_malformed_existing_review_table_is_rejected(
    tmp_path,
):
    db_path = tmp_path / "malformed-review.db"

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
        con.commit()
    finally:
        con.close()

    with pytest.raises(
        GenealogyRelationshipReviewMigrationError,
        match="missing required columns",
    ):
        apply_genealogy_relationship_review_schema(
            db_path
        )
