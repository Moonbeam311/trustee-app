"""Phase 2 additive canonical Person identity schema.

This migration creates identity records only.

It does not:
- infer a person from a beneficiary, fiduciary, genealogy, signature, or other role record;
- merge records because names match;
- establish genealogical relationships;
- establish verification, authority, entitlement, ownership, or legal status;
- create role/capacity links;
- update existing operational records.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


PERSON_REQUIRED_COLUMNS = {
    "person_id",
    "owner_id",
    "firm_id",
    "display_name",
    "sort_name",
    "notes",
    "created_by",
    "created_at",
    "updated_at",
}


class PersonIdentityMigrationError(RuntimeError):
    pass


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {
        row[1]
        for row in connection.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    }


def _count(connection: sqlite3.Connection, table: str) -> int:
    return int(
        connection.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
    )


def apply_person_identity_schema(
    db_path: str | Path,
) -> dict[str, Any]:
    """Create the canonical Person identity table without inferring records."""

    connection = sqlite3.connect(str(Path(db_path)))

    try:
        exists = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type='table' AND name='persons'
            """
        ).fetchone() is not None

        before = _count(connection, "persons") if exists else 0

        if exists:
            missing = PERSON_REQUIRED_COLUMNS - _columns(
                connection,
                "persons",
            )
            if missing:
                raise PersonIdentityMigrationError(
                    "existing persons table missing required columns: "
                    + ", ".join(sorted(missing))
                )

        connection.execute("BEGIN")

        created = not exists

        if created:
            connection.execute(
                """
                CREATE TABLE persons (
                    person_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    firm_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    sort_name TEXT,
                    notes TEXT,
                    created_by TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_persons_scope
                ON persons(owner_id, firm_id)
                """
            )

        after = _count(connection, "persons")

        if after != before:
            raise PersonIdentityMigrationError(
                "person row count changed during additive migration"
            )

        connection.commit()

        return {
            "schema_complete": True,
            "deferred": False,
            "reason": None,
            "persons_table_created": created,
            "person_rows_preserved": before,
            "person_rows_backfilled": 0,
            "records_created": 0,
        }

    except PersonIdentityMigrationError:
        connection.rollback()
        raise
    except sqlite3.Error as exc:
        connection.rollback()
        raise PersonIdentityMigrationError(str(exc)) from exc
    finally:
        connection.close()
