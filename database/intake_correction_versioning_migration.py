"""Additive schema foundation for Guided Intake correction provenance.

This migration is intentionally explicit and non-automatic. Importing this
module never opens a database, and callers must provide the database path to
``apply_intake_correction_versioning_schema``.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any


NEW_TABLES = (
    "intake_answer_revisions",
    "intake_answer_revision_items",
    "intake_snapshot_versions",
    "intake_snapshot_translation_items",
    "intake_snapshot_proposed_tasks",
)

_CREATE_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS intake_answer_revisions (
        answer_revision_id TEXT PRIMARY KEY,
        intake_id TEXT NOT NULL,
        firm_id TEXT NOT NULL,
        answer_revision_no INTEGER NOT NULL,
        revision_status TEXT NOT NULL
            CHECK (revision_status IN (
                'draft',
                'awaiting_confirmation',
                'confirmed',
                'superseded'
            )),
        supersedes_revision_id TEXT,
        created_at TEXT NOT NULL,
        created_by TEXT,
        confirmed_at TEXT,
        confirmed_by TEXT,
        UNIQUE (firm_id, intake_id, answer_revision_no),
        FOREIGN KEY (supersedes_revision_id)
            REFERENCES intake_answer_revisions(answer_revision_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS intake_answer_revision_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        answer_revision_id TEXT NOT NULL,
        question_key TEXT NOT NULL,
        answer_key TEXT NOT NULL,
        answer_label TEXT,
        created_at TEXT NOT NULL,
        created_by TEXT,
        UNIQUE (answer_revision_id, question_key, answer_key),
        FOREIGN KEY (answer_revision_id)
            REFERENCES intake_answer_revisions(answer_revision_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS intake_snapshot_versions (
        snapshot_version_id TEXT PRIMARY KEY,
        intake_id TEXT NOT NULL,
        firm_id TEXT NOT NULL,
        answer_revision_id TEXT NOT NULL,
        snapshot_version_no INTEGER NOT NULL,
        generation_batch_id TEXT NOT NULL,
        confirmation_status TEXT NOT NULL
            CHECK (confirmation_status IN (
                'awaiting_confirmation',
                'confirmed',
                'superseded'
            )),
        supersedes_snapshot_id TEXT,
        generated_at TEXT NOT NULL,
        generated_by TEXT,
        confirmed_at TEXT,
        confirmed_by TEXT,
        UNIQUE (firm_id, intake_id, snapshot_version_no),
        FOREIGN KEY (answer_revision_id)
            REFERENCES intake_answer_revisions(answer_revision_id),
        FOREIGN KEY (supersedes_snapshot_id)
            REFERENCES intake_snapshot_versions(snapshot_version_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS intake_snapshot_translation_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_version_id TEXT NOT NULL,
        source_key TEXT NOT NULL,
        system_category TEXT,
        system_meaning TEXT,
        module_trigger TEXT,
        document_request TEXT,
        next_session TEXT,
        risk_flag TEXT,
        created_at TEXT NOT NULL,
        created_by TEXT,
        FOREIGN KEY (snapshot_version_id)
            REFERENCES intake_snapshot_versions(snapshot_version_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS intake_snapshot_proposed_tasks (
        proposed_task_id TEXT PRIMARY KEY,
        snapshot_version_id TEXT NOT NULL,
        generation_batch_id TEXT NOT NULL,
        task_type TEXT,
        priority TEXT,
        title TEXT,
        description TEXT,
        source TEXT,
        operational_status TEXT
            CHECK (operational_status IS NULL OR operational_status IN (
                'open',
                'pending_client',
                'pending_staff',
                'pending_professional'
            )),
        proposal_status TEXT NOT NULL DEFAULT 'proposed'
            CHECK (proposal_status IN (
                'proposed',
                'materialized',
                'superseded'
            )),
        materialized_followup_task_id TEXT,
        created_at TEXT NOT NULL,
        created_by TEXT,
        materialized_at TEXT,
        FOREIGN KEY (snapshot_version_id)
            REFERENCES intake_snapshot_versions(snapshot_version_id)
    )
    """,
)

_FOLLOWUP_PROVENANCE_COLUMNS = {
    "snapshot_version_id": "TEXT",
    "generation_batch_id": "TEXT",
}

_PROPOSED_TASK_COLUMNS = {
    "operational_status": (
        "TEXT CHECK (operational_status IS NULL OR operational_status IN ("
        "'open', 'pending_client', 'pending_staff', 'pending_professional'))"
    ),
}


class IntakeCorrectionVersioningMigrationError(RuntimeError):
    """Raised when the additive correction-versioning migration fails."""


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone() is not None


def apply_intake_correction_versioning_schema(
    db_path: str | Path,
) -> dict[str, Any]:
    """Apply the append-only schema to the explicitly supplied SQLite DB.

    Existing Guided Intake tables and rows are not rewritten. The two nullable
    provenance columns are added only when ``intake_followup_tasks`` already
    exists.
    """

    if db_path is None or str(db_path).strip() == "":
        raise ValueError("db_path is required")

    connection = sqlite3.connect(str(Path(db_path)))

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN")

        for statement in _CREATE_STATEMENTS:
            connection.execute(statement)

        added_columns = []
        proposed_task_columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(intake_snapshot_proposed_tasks)"
            )
        }
        for column_name, column_definition in _PROPOSED_TASK_COLUMNS.items():
            if column_name not in proposed_task_columns:
                connection.execute(
                    "ALTER TABLE intake_snapshot_proposed_tasks "
                    f"ADD COLUMN {column_name} {column_definition}"
                )

        if _table_exists(connection, "intake_followup_tasks"):
            existing_columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(intake_followup_tasks)"
                )
            }
            for column_name, column_type in _FOLLOWUP_PROVENANCE_COLUMNS.items():
                if column_name not in existing_columns:
                    connection.execute(
                        "ALTER TABLE intake_followup_tasks "
                        f"ADD COLUMN {column_name} {column_type}"
                    )
                    added_columns.append(column_name)

        connection.commit()
        return {
            "schema_complete": True,
            "tables": NEW_TABLES,
            "followup_columns_added": tuple(added_columns),
        }
    except sqlite3.Error as exc:
        connection.rollback()
        raise IntakeCorrectionVersioningMigrationError(str(exc)) from exc
    finally:
        connection.close()
