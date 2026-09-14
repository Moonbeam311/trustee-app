"""Phase 2 additive Person-to-role/capacity link schema.

This table records only explicit links between a canonical Person identity
and an existing institutional or operational role/capacity record.

It does not:
- infer links from matching names;
- create Person identities;
- alter beneficiary, fiduciary, genealogy, or other operational records;
- treat genealogy relationships as institutional role links;
- establish legal authority, ownership, entitlement, inheritance, or status;
- create or resolve family relationships.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


PERSON_ROLE_LINK_REQUIRED_COLUMNS = {
    "link_id",
    "owner_id",
    "firm_id",
    "person_id",
    "role_type",
    "role_record_id",
    "trust_id",
    "capacity_label",
    "notes",
    "created_by",
    "created_at",
    "updated_at",
}


class PersonRoleLinkMigrationError(RuntimeError):
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


def apply_person_role_link_schema(
    db_path: str | Path,
) -> dict[str, Any]:
    """Create the explicit Person role/capacity link table only."""

    connection = sqlite3.connect(str(Path(db_path)))

    try:
        exists = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type='table'
              AND name='person_role_links'
            """
        ).fetchone() is not None

        before = (
            _count(connection, "person_role_links")
            if exists
            else 0
        )

        if exists:
            missing = (
                PERSON_ROLE_LINK_REQUIRED_COLUMNS
                - _columns(connection, "person_role_links")
            )

            if missing:
                raise PersonRoleLinkMigrationError(
                    "existing person_role_links table "
                    "missing required columns: "
                    + ", ".join(sorted(missing))
                )

        connection.execute("BEGIN")

        created = not exists

        if created:
            connection.execute(
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
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_person_role_links_scope_person
                ON person_role_links(
                    owner_id,
                    firm_id,
                    person_id
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_person_role_links_scope_role
                ON person_role_links(
                    owner_id,
                    firm_id,
                    role_type,
                    role_record_id
                )
                """
            )

        after = _count(connection, "person_role_links")

        if after != before:
            raise PersonRoleLinkMigrationError(
                "person role-link row count changed "
                "during additive migration"
            )

        connection.commit()

        return {
            "schema_complete": True,
            "deferred": False,
            "reason": None,
            "person_role_links_table_created": created,
            "person_role_link_rows_preserved": before,
            "person_role_link_rows_backfilled": 0,
            "records_created": 0,
        }

    except PersonRoleLinkMigrationError:
        connection.rollback()
        raise
    except sqlite3.Error as exc:
        connection.rollback()
        raise PersonRoleLinkMigrationError(str(exc)) from exc
    finally:
        connection.close()
