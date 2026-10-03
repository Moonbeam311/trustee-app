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


WORKSPACE_NOTES_REQUIRED_COLUMNS = (
    "note_id",
    "workspace_id",
    "section_name",
    "content",
    "firm_id",
    "created_at",
)

WORKSPACE_NOTES_ADDITIVE_COLUMN_DEFINITIONS = {
    "workspace_id": "TEXT",
    "section_name": "TEXT",
    "content": "TEXT",
    "firm_id": "TEXT",
    "created_at": "TEXT",
}


def _workspace_note_column_names(
    connection: sqlite3.Connection,
) -> set[str]:
    return {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(workspace_notes)"
        ).fetchall()
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

        notes_table_exists = bool(
            connection.execute(
                '''
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = 'workspace_notes'
                '''
            ).fetchone()
        )

        workspace_notes_table_created = False
        workspace_notes_columns_added: list[str] = []
        legacy_note_rows_preserved = 0

        if not notes_table_exists:
            connection.execute(
                '''
                CREATE TABLE workspace_notes (
                    note_id TEXT PRIMARY KEY,
                    workspace_id TEXT,
                    section_name TEXT,
                    content TEXT,
                    firm_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )
            workspace_notes_table_created = True

        else:
            before_note_count = connection.execute(
                "SELECT COUNT(*) FROM workspace_notes"
            ).fetchone()[0]

            existing_note_columns = _workspace_note_column_names(
                connection
            )

            if "note_id" not in existing_note_columns:
                raise WorkspaceSchemaMigrationError(
                    "existing workspace_notes table lacks note_id; "
                    "destructive repair is prohibited"
                )

            for column_name in WORKSPACE_NOTES_REQUIRED_COLUMNS:
                if column_name in existing_note_columns:
                    continue

                if column_name == "note_id":
                    continue

                column_definition = (
                    WORKSPACE_NOTES_ADDITIVE_COLUMN_DEFINITIONS[
                        column_name
                    ]
                )

                connection.execute(
                    f'''
                    ALTER TABLE workspace_notes
                    ADD COLUMN {column_name} {column_definition}
                    '''
                )
                workspace_notes_columns_added.append(column_name)

            after_note_count = connection.execute(
                "SELECT COUNT(*) FROM workspace_notes"
            ).fetchone()[0]

            if after_note_count != before_note_count:
                raise WorkspaceSchemaMigrationError(
                    "legacy workspace note row count changed "
                    "during additive migration"
                )

            legacy_note_rows_preserved = after_note_count

        final_note_columns = _workspace_note_column_names(connection)

        missing_note_columns = [
            column_name
            for column_name in WORKSPACE_NOTES_REQUIRED_COLUMNS
            if column_name not in final_note_columns
        ]

        if missing_note_columns:
            raise WorkspaceSchemaMigrationError(
                "canonical workspace_notes schema remains incomplete: "
                + ", ".join(missing_note_columns)
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
            "workspace_notes_table_created": workspace_notes_table_created,
            "workspace_notes_columns_added": workspace_notes_columns_added,
            "legacy_note_rows_preserved": legacy_note_rows_preserved,
        }

    except WorkspaceSchemaMigrationError:
        connection.rollback()
        raise

    except sqlite3.DatabaseError as exc:
        connection.rollback()
        raise WorkspaceSchemaMigrationError(str(exc)) from exc

    finally:
        connection.close()
