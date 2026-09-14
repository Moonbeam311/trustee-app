"""Additive genealogy relationship review-history schema.

This migration creates an append-only review ledger for deliberate review
of first-class genealogy relationship assertions.

It does not:
- change genealogy assertion status;
- create review records automatically;
- infer relationships from legacy genealogy text;
- create or duplicate Media Evidence;
- treat source attachment as confirmation;
- reuse P09 authority/claim review tables;
- establish genealogical truth, inheritance, ownership, citizenship,
  legal status, authority, or entitlement.

The later governed review service will decide which explicit human action
may update the assertion's current status.

A SYSTEM_SUGGESTED review record may exist as review context later, but
the schema itself does not authorize machine finalization or status
mutation.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class GenealogyRelationshipReviewMigrationError(RuntimeError):
    pass


REQUIRED_COLUMNS = {
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
}


ASSERTION_STATUSES = (
    "USER_ASSERTED",
    "REVIEW_REQUIRED",
    "CONFIRMED",
    "CONFLICTING",
    "UNRESOLVED",
)


DECISION_ORIGINS = (
    "SYSTEM_SUGGESTED",
    "OPERATOR_OR_FIDUCIARY",
    "PROFESSIONAL",
)


def _connection(
    db_path: str | Path,
) -> sqlite3.Connection:
    con = sqlite3.connect(str(Path(db_path)))
    con.row_factory = sqlite3.Row
    return con


def _columns(
    con: sqlite3.Connection,
    table: str,
) -> set[str]:
    rows = con.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    return {row["name"] for row in rows}


def _count(
    con: sqlite3.Connection,
    table: str,
) -> int:
    return int(
        con.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
    )


def apply_genealogy_relationship_review_schema(
    db_path: str | Path,
) -> dict[str, Any]:
    con = _connection(db_path)

    try:
        existing = (
            con.execute(
                """
                SELECT COUNT(*)
                FROM sqlite_master
                WHERE type='table'
                  AND name='genealogy_relationship_reviews'
                """
            ).fetchone()[0]
            == 1
        )

        before = (
            _count(
                con,
                "genealogy_relationship_reviews",
            )
            if existing
            else 0
        )

        if existing:
            missing = (
                REQUIRED_COLUMNS
                - _columns(
                    con,
                    "genealogy_relationship_reviews",
                )
            )

            if missing:
                raise GenealogyRelationshipReviewMigrationError(
                    "existing genealogy_relationship_reviews "
                    "table is missing required columns: "
                    + ", ".join(sorted(missing))
                )

        created = False

        con.execute("BEGIN")

        if not existing:
            con.execute(
                """
                CREATE TABLE genealogy_relationship_reviews (
                    review_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    firm_id TEXT NOT NULL,
                    assertion_id TEXT NOT NULL,
                    prior_review_id TEXT,
                    prior_status TEXT NOT NULL
                        CHECK (
                            prior_status IN (
                                'USER_ASSERTED',
                                'REVIEW_REQUIRED',
                                'CONFIRMED',
                                'CONFLICTING',
                                'UNRESOLVED'
                            )
                        ),
                    new_status TEXT NOT NULL
                        CHECK (
                            new_status IN (
                                'USER_ASSERTED',
                                'REVIEW_REQUIRED',
                                'CONFIRMED',
                                'CONFLICTING',
                                'UNRESOLVED'
                            )
                        ),
                    review_basis TEXT NOT NULL,
                    provenance TEXT NOT NULL,
                    decision_origin TEXT NOT NULL
                        CHECK (
                            decision_origin IN (
                                'SYSTEM_SUGGESTED',
                                'OPERATOR_OR_FIDUCIARY',
                                'PROFESSIONAL'
                            )
                        ),
                    human_confirmed INTEGER NOT NULL
                        DEFAULT 0
                        CHECK (
                            human_confirmed IN (0, 1)
                        ),
                    actor TEXT NOT NULL,
                    actor_capacity TEXT NOT NULL,
                    professional_authority TEXT,
                    created_at TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            created = True

        con.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_genealogy_review_scope_assertion
            ON genealogy_relationship_reviews(
                owner_id,
                firm_id,
                assertion_id,
                created_at
            )
            """
        )

        con.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_genealogy_review_prior
            ON genealogy_relationship_reviews(
                prior_review_id
            )
            """
        )

        con.execute(
            """
            CREATE TRIGGER IF NOT EXISTS
                trg_genealogy_relationship_reviews_no_update
            BEFORE UPDATE
            ON genealogy_relationship_reviews
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'genealogy relationship review history is append-only'
                );
            END
            """
        )

        con.execute(
            """
            CREATE TRIGGER IF NOT EXISTS
                trg_genealogy_relationship_reviews_no_delete
            BEFORE DELETE
            ON genealogy_relationship_reviews
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'genealogy relationship review history is append-only'
                );
            END
            """
        )

        after = _count(
            con,
            "genealogy_relationship_reviews",
        )

        if after != before:
            raise GenealogyRelationshipReviewMigrationError(
                "review-history row count changed during "
                "schema migration"
            )

        con.commit()

        return {
            "schema_complete": True,
            "deferred": False,
            "reason": None,
            "genealogy_relationship_review_table_created": (
                created
            ),
            "genealogy_relationship_review_rows_preserved": (
                before
            ),
            "genealogy_relationship_review_rows_backfilled": 0,
            "records_created": 0,
        }

    except GenealogyRelationshipReviewMigrationError:
        con.rollback()
        raise

    except sqlite3.Error as exc:
        con.rollback()
        raise GenealogyRelationshipReviewMigrationError(
            str(exc)
        ) from exc

    finally:
        con.close()
