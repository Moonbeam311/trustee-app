"""First-class genealogy relationship assertion schema.

A genealogy relationship assertion is a directional, explicitly recorded
connection between two canonical Person identities.

This schema does not:
- infer relationships from names;
- read or transform legacy parent_1, parent_2, or spouse text;
- create inverse or reciprocal relationships automatically;
- create Person identities;
- create institutional role/capacity links;
- create a second media/evidence subsystem;
- repurpose P09 authority/claim verification;
- establish inheritance, ownership, citizenship, legal status,
  authority, entitlement, or genealogical truth.

Evidence remains attachable through the existing Media Evidence mechanism
using the relationship assertion as the related entity. Human-governed
review/status workflows are separate later layers.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


GENEALOGY_RELATIONSHIP_REQUIRED_COLUMNS = {
    "assertion_id",
    "owner_id",
    "firm_id",
    "subject_person_id",
    "relationship_type",
    "related_person_id",
    "trust_id",
    "legacy_genealogy_id",
    "assertion_status",
    "assertion_basis",
    "notes",
    "created_by",
    "created_at",
    "updated_at",
}


GENEALOGY_RELATIONSHIP_STATUSES = (
    "USER_ASSERTED",
    "REVIEW_REQUIRED",
    "CONFIRMED",
    "CONFLICTING",
    "UNRESOLVED",
)


class GenealogyRelationshipMigrationError(RuntimeError):
    pass


def _columns(
    connection: sqlite3.Connection,
    table: str,
) -> set[str]:
    return {
        row[1]
        for row in connection.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    }


def _count(
    connection: sqlite3.Connection,
    table: str,
) -> int:
    return int(
        connection.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
    )


def apply_genealogy_relationship_schema(
    db_path: str | Path,
) -> dict[str, Any]:
    """Create the additive genealogy relationship assertion table only."""

    connection = sqlite3.connect(str(Path(db_path)))

    try:
        exists = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type='table'
              AND name='genealogy_relationship_assertions'
            """
        ).fetchone() is not None

        before = (
            _count(
                connection,
                "genealogy_relationship_assertions",
            )
            if exists
            else 0
        )

        if exists:
            missing = (
                GENEALOGY_RELATIONSHIP_REQUIRED_COLUMNS
                - _columns(
                    connection,
                    "genealogy_relationship_assertions",
                )
            )

            if missing:
                raise GenealogyRelationshipMigrationError(
                    "existing genealogy_relationship_assertions table "
                    "missing required columns: "
                    + ", ".join(sorted(missing))
                )

        connection.execute("BEGIN")

        created = not exists

        if created:
            connection.execute(
                """
                CREATE TABLE genealogy_relationship_assertions (
                    assertion_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    firm_id TEXT NOT NULL,
                    subject_person_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    related_person_id TEXT NOT NULL,
                    trust_id TEXT,
                    legacy_genealogy_id TEXT,
                    assertion_status TEXT NOT NULL
                        DEFAULT 'USER_ASSERTED'
                        CHECK (
                            assertion_status IN (
                                'USER_ASSERTED',
                                'REVIEW_REQUIRED',
                                'CONFIRMED',
                                'CONFLICTING',
                                'UNRESOLVED'
                            )
                        ),
                    assertion_basis TEXT,
                    notes TEXT,
                    created_by TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_genealogy_relationship_scope_subject
                ON genealogy_relationship_assertions(
                    owner_id,
                    firm_id,
                    subject_person_id
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_genealogy_relationship_scope_related
                ON genealogy_relationship_assertions(
                    owner_id,
                    firm_id,
                    related_person_id
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_genealogy_relationship_scope_status
                ON genealogy_relationship_assertions(
                    owner_id,
                    firm_id,
                    assertion_status
                )
                """
            )

        after = _count(
            connection,
            "genealogy_relationship_assertions",
        )

        if after != before:
            raise GenealogyRelationshipMigrationError(
                "genealogy relationship assertion row count changed "
                "during additive migration"
            )

        connection.commit()

        return {
            "schema_complete": True,
            "deferred": False,
            "reason": None,
            "genealogy_relationship_table_created": created,
            "genealogy_relationship_rows_preserved": before,
            "genealogy_relationship_rows_backfilled": 0,
            "records_created": 0,
        }

    except GenealogyRelationshipMigrationError:
        connection.rollback()
        raise
    except sqlite3.Error as exc:
        connection.rollback()
        raise GenealogyRelationshipMigrationError(
            str(exc)
        ) from exc
    finally:
        connection.close()
