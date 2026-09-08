"""Additive canonical Execution task schema completeness repair."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class ExecutionTaskSchemaMigrationError(RuntimeError):
    """Raised when canonical Execution task schema cannot be installed safely."""


REQUIRED_COLUMNS = (
    "task_id",
    "workspace_id",
    "trust_id",
    "title",
    "task_type",
    "description",
    "related_form",
    "related_report",
    "priority",
    "status",
    "due_date",
    "assigned_to",
    "owner_id",
    "created_at",
    "updated_at",
    "firm_id",
)


ADDITIVE_COLUMN_DEFINITIONS = {
    "task_id": "TEXT",
    "workspace_id": "TEXT",
    "trust_id": "TEXT",
    "title": "TEXT",
    "task_type": "TEXT",
    "description": "TEXT",
    "related_form": "TEXT",
    "related_report": "TEXT",
    "priority": "TEXT",
    "status": "TEXT",
    "due_date": "TEXT",
    "assigned_to": "TEXT",
    "owner_id": "TEXT",
    "created_at": "TEXT",
    "updated_at": "TEXT",
    "firm_id": "TEXT",
}


def _column_names(connection: sqlite3.Connection) -> set[str]:
    return {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(execution_tasks)"
        ).fetchall()
    }


def apply_execution_task_schema(
    db_path: str | Path,
) -> dict[str, object]:
    """
    Install the canonical operator Execution task schema additively.

    Fresh databases receive the complete current application contract plus the
    historical integer autoincrement compatibility id. Existing tables are
    never dropped or recreated; missing nullable application columns are added
    without rewriting, deleting, or backfilling legacy rows.
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
                  AND name = 'execution_tasks'
                """
            ).fetchone()
        )

        table_created = False
        columns_added: list[str] = []
        legacy_rows_preserved = 0

        if not table_exists:
            connection.execute(
                """
                CREATE TABLE execution_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    workspace_id TEXT,
                    trust_id TEXT,
                    title TEXT,
                    task_type TEXT,
                    description TEXT,
                    related_form TEXT,
                    related_report TEXT,
                    priority TEXT,
                    status TEXT,
                    due_date TEXT,
                    assigned_to TEXT,
                    owner_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    firm_id TEXT
                )
                """
            )
            table_created = True

        else:
            before_count = connection.execute(
                "SELECT COUNT(*) FROM execution_tasks"
            ).fetchone()[0]

            existing_columns = _column_names(connection)

            for column_name in REQUIRED_COLUMNS:
                if column_name in existing_columns:
                    continue

                column_definition = ADDITIVE_COLUMN_DEFINITIONS[column_name]

                connection.execute(
                    f"""
                    ALTER TABLE execution_tasks
                    ADD COLUMN {column_name} {column_definition}
                    """
                )
                columns_added.append(column_name)

            after_count = connection.execute(
                "SELECT COUNT(*) FROM execution_tasks"
            ).fetchone()[0]

            if after_count != before_count:
                raise ExecutionTaskSchemaMigrationError(
                    "legacy execution task row count changed during additive "
                    "migration"
                )

            legacy_rows_preserved = after_count

        final_columns = _column_names(connection)

        missing = [
            column_name
            for column_name in REQUIRED_COLUMNS
            if column_name not in final_columns
        ]

        if missing:
            raise ExecutionTaskSchemaMigrationError(
                "canonical execution task schema remains incomplete: "
                + ", ".join(missing)
            )

        if table_created:
            id_info = next(
                (
                    row
                    for row in connection.execute(
                        "PRAGMA table_info(execution_tasks)"
                    ).fetchall()
                    if row[1] == "id"
                ),
                None,
            )
            if id_info is None or id_info[2].upper() != "INTEGER" or id_info[5] != 1:
                raise ExecutionTaskSchemaMigrationError(
                    "fresh execution_tasks table lacks legacy integer primary "
                    "key compatibility"
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

    except ExecutionTaskSchemaMigrationError:
        connection.rollback()
        raise

    except sqlite3.DatabaseError as exc:
        connection.rollback()
        raise ExecutionTaskSchemaMigrationError(str(exc)) from exc

    finally:
        connection.close()
