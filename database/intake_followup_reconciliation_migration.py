"""Additive ledger schema for intake follow-up duplicate reconciliation."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any


class IntakeFollowupReconciliationMigrationError(RuntimeError):
    """Raised when the reconciliation ledger cannot be installed safely."""


REQUIRED_FOLLOWUP_COLUMNS = {
    "id", "firm_id", "intake_id", "snapshot_version_id", "generation_batch_id",
}


def apply_intake_followup_reconciliation_schema(
    db_path: str | Path,
) -> dict[str, Any]:
    if db_path is None or not str(db_path).strip():
        raise ValueError("db_path is required")

    connection = sqlite3.connect(str(Path(db_path)))
    connection.row_factory = sqlite3.Row
    try:
        source_exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' "
            "AND name='intake_followup_tasks'"
        ).fetchone()
        if source_exists is None:
            raise IntakeFollowupReconciliationMigrationError(
                "intake_followup_tasks table is required"
            )
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(intake_followup_tasks)")
        }
        missing = REQUIRED_FOLLOWUP_COLUMNS - columns
        if missing:
            raise IntakeFollowupReconciliationMigrationError(
                "intake_followup_tasks is missing required columns: "
                + ", ".join(sorted(missing))
            )

        existed = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' "
            "AND name='intake_followup_reconciliations'"
        ).fetchone() is not None
        connection.execute("BEGIN")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS intake_followup_reconciliations (
                reconciliation_id TEXT PRIMARY KEY,
                firm_id TEXT NOT NULL,
                intake_id TEXT NOT NULL,
                superseded_followup_task_id INTEGER NOT NULL UNIQUE,
                replacement_followup_task_id INTEGER NOT NULL,
                reconciliation_type TEXT NOT NULL
                    CHECK (reconciliation_type = 'superseded_duplicate'),
                reason TEXT NOT NULL,
                reconciled_at TEXT NOT NULL,
                reconciled_by TEXT NOT NULL,
                CHECK (superseded_followup_task_id != replacement_followup_task_id),
                FOREIGN KEY (superseded_followup_task_id)
                    REFERENCES intake_followup_tasks(id),
                FOREIGN KEY (replacement_followup_task_id)
                    REFERENCES intake_followup_tasks(id)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_intake_followup_reconciliation_scope
            ON intake_followup_reconciliations(firm_id, intake_id, reconciled_at)
            """
        )
        count = connection.execute(
            "SELECT COUNT(*) FROM intake_followup_reconciliations"
        ).fetchone()[0]
        connection.commit()
        return {
            "schema_complete": True,
            "table_created": not existed,
            "reconciliation_rows": count,
            "records_created": 0,
        }
    except IntakeFollowupReconciliationMigrationError:
        raise
    except sqlite3.Error as exc:
        connection.rollback()
        raise IntakeFollowupReconciliationMigrationError(str(exc)) from exc
    finally:
        connection.close()
