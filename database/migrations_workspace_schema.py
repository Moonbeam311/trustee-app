"""Additive canonical workspace schema completeness repair."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class WorkspaceSchemaMigrationError(RuntimeError):
    """Raised when canonical workspace schema cannot be installed safely."""


REQUIRED_COLUMNS = (
    "workspace_id",
    "title",
    "workspace_type",
    "trust_type_focus",
    "purpose",
    "owner",
    "status",
    "owner_id",
    "firm_id",
    "created_at",
    "updated_at",
)


ADDITIVE_COLUMN_DEFINITIONS = {
    "title": "TEXT",
    "workspace_type": "TEXT",
    "trust_type_focus": "TEXT",
    "purpose": "TEXT",
    "owner": "TEXT",
    "status": "TEXT",
    "owner_id": "TEXT",
    "firm_id": "TEXT",
    "created_at": "TEXT",
    "updated_at": "TEXT",
}


def _column_names(connection: sqlite3.Connection) -> set[str]:
    return {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(workspaces)"
        ).fetchall()
    }


def apply_workspace_schema(
    db_path: str | Path,
) -> dict[str, object]:
    """
    Install the canonical Work & Learning Hub workspace schema additively.

    Fresh databases receive the complete canonical table. Existing workspace
    tables are never dropped or recreated; missing nullable columns are added
    without rewriting or backfilling legacy rows.
    """

    resolved = Path(db_path).expanduser().resolve()
    connection = sqlite3.connect(str(resolved))

    try:
        table_exists = bool(
            connection.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = 'workspaces'
                """
            ).fetchone()
        )

        table_created = False
        columns_added: list[str] = []
        legacy_rows_preserved = 0

        if not table_exists:
            connection.execute(
                """
                CREATE TABLE workspaces (
                    workspace_id TEXT PRIMARY KEY,
                    title TEXT,
                    workspace_type TEXT,
                    trust_type_focus TEXT,
                    purpose TEXT,
                    owner TEXT,
                    status TEXT,
                    owner_id TEXT,
                    firm_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            table_created = True

        else:
            before_count = connection.execute(
                "SELECT COUNT(*) FROM workspaces"
            ).fetchone()[0]

            existing_columns = _column_names(connection)

            if "workspace_id" not in existing_columns:
                raise WorkspaceSchemaMigrationError(
                    "existing workspaces table lacks workspace_id; "
                    "destructive repair is prohibited"
                )

            for column_name in REQUIRED_COLUMNS:
                if column_name in existing_columns:
                    continue

                if column_name == "workspace_id":
                    continue

                column_definition = ADDITIVE_COLUMN_DEFINITIONS[column_name]

                connection.execute(
                    f"""
                    ALTER TABLE workspaces
                    ADD COLUMN {column_name} {column_definition}
                    """
                )
                columns_added.append(column_name)

            after_count = connection.execute(
                "SELECT COUNT(*) FROM workspaces"
            ).fetchone()[0]

            if after_count != before_count:
                raise WorkspaceSchemaMigrationError(
                    "legacy workspace row count changed during additive migration"
                )

            legacy_rows_preserved = after_count

        final_columns = _column_names(connection)

        missing = [
            column_name
            for column_name in REQUIRED_COLUMNS
            if column_name not in final_columns
        ]

        if missing:
            raise WorkspaceSchemaMigrationError(
                "canonical workspace schema remains incomplete: "
                + ", ".join(missing)
            )

        connection.commit()

        return {
            "schema_complete": True,
            "deferred": False,
            "table_created": table_created,
            "columns_added": columns_added,
            "legacy_rows_preserved": legacy_rows_preserved,
            "legacy_rows_updated": 0,
            "records_created": 0,
        }

    except WorkspaceSchemaMigrationError:
        connection.rollback()
        raise

    except sqlite3.DatabaseError as exc:
        connection.rollback()
        raise WorkspaceSchemaMigrationError(str(exc)) from exc

    finally:
        connection.close()
