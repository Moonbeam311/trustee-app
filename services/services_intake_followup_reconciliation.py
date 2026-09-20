"""Provenance-preserving reconciliation of exact follow-up task duplicates."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4


class IntakeFollowupReconciliationError(RuntimeError):
    """Raised when reconciliation invariants are not satisfied."""


def _required(value: Any, name: str) -> str:
    if value is None or not str(value).strip():
        raise ValueError(f"{name} is required")
    return str(value).strip()


def _connect(db_path: str | Path, read_only: bool = False) -> sqlite3.Connection:
    path = Path(_required(db_path, "db_path")).resolve()
    target = f"file:{path.as_posix()}?mode=ro" if read_only else str(path)
    connection = sqlite3.connect(target, uri=read_only)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").split()).casefold()


def _signature(row: sqlite3.Row) -> tuple[str, str, str, str, str]:
    return tuple(
        _normalize(row[column])
        for column in ("task_type", "priority", "status", "title", "description")
    )


def reconcile_followup_duplicate(
    db_path: str | Path,
    firm_id: str,
    intake_id: str,
    superseded_followup_task_id: int,
    replacement_followup_task_id: int,
    reconciled_by: str,
    reason: str = "Exact legacy/governed operational follow-up duplicate",
) -> dict[str, Any]:
    """Record one explicitly identified duplicate pair after full validation."""

    firm_id = _required(firm_id, "firm_id")
    intake_id = _required(intake_id, "intake_id")
    reconciled_by = _required(reconciled_by, "reconciled_by")
    reason = _required(reason, "reason")
    connection = _connect(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        rows = connection.execute(
            """
            SELECT id, firm_id, intake_id, task_type, priority, status, title,
                   description, snapshot_version_id, generation_batch_id
            FROM intake_followup_tasks WHERE id IN (?, ?)
            """,
            (superseded_followup_task_id, replacement_followup_task_id),
        ).fetchall()
        by_id = {row["id"]: row for row in rows}
        if set(by_id) != {superseded_followup_task_id, replacement_followup_task_id}:
            raise IntakeFollowupReconciliationError("both follow-up task IDs must exist")
        superseded = by_id[superseded_followup_task_id]
        replacement = by_id[replacement_followup_task_id]
        if any(row["firm_id"] != firm_id or row["intake_id"] != intake_id for row in rows):
            raise IntakeFollowupReconciliationError(
                "both follow-up tasks must belong to the supplied firm and intake"
            )
        if not (
            superseded["snapshot_version_id"] is None
            and superseded["generation_batch_id"] is None
        ):
            raise IntakeFollowupReconciliationError("superseded task must be legacy")
        if not (
            replacement["snapshot_version_id"] is not None
            and replacement["generation_batch_id"] is not None
        ):
            raise IntakeFollowupReconciliationError("replacement task must be governed")
        signature = _signature(superseded)
        if signature != _signature(replacement):
            raise IntakeFollowupReconciliationError("tasks are not exact duplicates")
        candidates = connection.execute(
            """
            SELECT id, task_type, priority, status, title, description,
                   snapshot_version_id, generation_batch_id
            FROM intake_followup_tasks WHERE firm_id = ? AND intake_id = ?
            """,
            (firm_id, intake_id),
        ).fetchall()
        legacy_matches = [
            row for row in candidates
            if row["snapshot_version_id"] is None
            and row["generation_batch_id"] is None
            and _signature(row) == signature
        ]
        governed_matches = [
            row for row in candidates
            if row["snapshot_version_id"] is not None
            and row["generation_batch_id"] is not None
            and _signature(row) == signature
        ]
        if len(legacy_matches) != 1 or len(governed_matches) != 1:
            raise IntakeFollowupReconciliationError("duplicate match is ambiguous")
        existing = connection.execute(
            "SELECT replacement_followup_task_id FROM intake_followup_reconciliations "
            "WHERE superseded_followup_task_id = ?",
            (superseded_followup_task_id,),
        ).fetchone()
        if existing is not None:
            if existing[0] != replacement_followup_task_id:
                raise IntakeFollowupReconciliationError(
                    "legacy task is already reconciled to another replacement"
                )
            connection.commit()
            return {"records_created": 0}
        reconciliation_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        )
        connection.execute(
            """
            INSERT INTO intake_followup_reconciliations (
                reconciliation_id, firm_id, intake_id,
                superseded_followup_task_id, replacement_followup_task_id,
                reconciliation_type, reason, reconciled_at, reconciled_by
            ) VALUES (?, ?, ?, ?, ?, 'superseded_duplicate', ?, ?, ?)
            """,
            (reconciliation_id, firm_id, intake_id, superseded_followup_task_id,
             replacement_followup_task_id, reason, now, reconciled_by),
        )
        connection.commit()
        return {"records_created": 1, "reconciliation_id": reconciliation_id}
    except (ValueError, IntakeFollowupReconciliationError):
        connection.rollback()
        raise
    except sqlite3.Error as exc:
        connection.rollback()
        raise IntakeFollowupReconciliationError(str(exc)) from exc
    finally:
        connection.close()


def reconcile_exact_followup_duplicates(
    db_path: str | Path,
    firm_id: str,
    intake_id: str,
    reconciled_by: str,
    reason: str = "Exact legacy/governed operational follow-up duplicate",
) -> dict[str, Any]:
    """Ledger only unambiguous one-to-one exact legacy/governed matches."""

    firm_id = _required(firm_id, "firm_id")
    intake_id = _required(intake_id, "intake_id")
    reconciled_by = _required(reconciled_by, "reconciled_by")
    reason = _required(reason, "reason")
    connection = _connect(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' "
            "AND name='intake_followup_reconciliations'"
        ).fetchone() is None:
            raise IntakeFollowupReconciliationError(
                "intake_followup_reconciliations table is not installed"
            )
        rows = connection.execute(
            """
            SELECT id, firm_id, intake_id, task_type, priority, status, title,
                   description, snapshot_version_id, generation_batch_id
            FROM intake_followup_tasks
            WHERE firm_id = ? AND intake_id = ?
            """,
            (firm_id, intake_id),
        ).fetchall()
        legacy: dict[tuple[str, ...], list[sqlite3.Row]] = {}
        governed: dict[tuple[str, ...], list[sqlite3.Row]] = {}
        for row in rows:
            if row["snapshot_version_id"] is None and row["generation_batch_id"] is None:
                legacy.setdefault(_signature(row), []).append(row)
            elif row["snapshot_version_id"] is not None and row["generation_batch_id"] is not None:
                governed.setdefault(_signature(row), []).append(row)

        existing = {
            row[0] for row in connection.execute(
                "SELECT superseded_followup_task_id "
                "FROM intake_followup_reconciliations"
            )
        }
        created = []
        now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        )
        for signature in sorted(set(legacy) & set(governed)):
            legacy_rows = legacy[signature]
            governed_rows = governed[signature]
            # Anything other than a unique pair is ambiguous and remains untouched.
            if len(legacy_rows) != 1 or len(governed_rows) != 1:
                continue
            superseded = legacy_rows[0]
            replacement = governed_rows[0]
            if superseded["id"] in existing:
                continue
            reconciliation_id = str(uuid4())
            connection.execute(
                """
                INSERT INTO intake_followup_reconciliations (
                    reconciliation_id, firm_id, intake_id,
                    superseded_followup_task_id, replacement_followup_task_id,
                    reconciliation_type, reason, reconciled_at, reconciled_by
                ) VALUES (?, ?, ?, ?, ?, 'superseded_duplicate', ?, ?, ?)
                """,
                (
                    reconciliation_id, firm_id, intake_id, superseded["id"],
                    replacement["id"], reason, now, reconciled_by,
                ),
            )
            created.append(reconciliation_id)
        connection.commit()
        return {"records_created": len(created), "reconciliation_ids": created}
    except (ValueError, IntakeFollowupReconciliationError):
        connection.rollback()
        raise
    except sqlite3.Error as exc:
        connection.rollback()
        raise IntakeFollowupReconciliationError(str(exc)) from exc
    finally:
        connection.close()


def reconcile_governed_snapshot_followup_successors(
    db_path: str | Path,
    firm_id: str,
    intake_id: str,
    predecessor_snapshot_version_id: str,
    successor_snapshot_version_id: str,
    reconciled_by: str,
) -> dict[str, Any]:
    """Ledger unique exact task successors across two governed snapshots."""

    connection = _connect(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        result = reconcile_governed_snapshot_followup_successors_in_transaction(
            connection,
            firm_id,
            intake_id,
            predecessor_snapshot_version_id,
            successor_snapshot_version_id,
            reconciled_by,
        )
        connection.commit()
        return result
    except (ValueError, IntakeFollowupReconciliationError):
        connection.rollback()
        raise
    except sqlite3.Error as exc:
        connection.rollback()
        raise IntakeFollowupReconciliationError(str(exc)) from exc
    finally:
        connection.close()


def reconcile_governed_snapshot_followup_successors_in_transaction(
    connection: sqlite3.Connection,
    firm_id: str,
    intake_id: str,
    predecessor_snapshot_version_id: str,
    successor_snapshot_version_id: str,
    reconciled_by: str,
) -> dict[str, Any]:
    """Ledger governed successors using a caller-owned SQLite transaction."""

    firm_id = _required(firm_id, "firm_id")
    intake_id = _required(intake_id, "intake_id")
    predecessor_snapshot_version_id = _required(
        predecessor_snapshot_version_id, "predecessor_snapshot_version_id"
    )
    successor_snapshot_version_id = _required(
        successor_snapshot_version_id, "successor_snapshot_version_id"
    )
    reconciled_by = _required(reconciled_by, "reconciled_by")
    try:
        if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' "
            "AND name='intake_followup_reconciliations'"
        ).fetchone() is None:
            raise IntakeFollowupReconciliationError(
                "intake_followup_reconciliations table is not installed"
            )

        snapshots = connection.execute(
            """
            SELECT snapshot_version_id, firm_id, intake_id, snapshot_version_no,
                   generation_batch_id, confirmation_status,
                   supersedes_snapshot_id
            FROM intake_snapshot_versions
            WHERE snapshot_version_id IN (?, ?)
            """,
            (predecessor_snapshot_version_id, successor_snapshot_version_id),
        ).fetchall()
        by_id = {row["snapshot_version_id"]: row for row in snapshots}
        if set(by_id) != {
            predecessor_snapshot_version_id, successor_snapshot_version_id
        }:
            raise IntakeFollowupReconciliationError("both snapshots must exist")
        predecessor = by_id[predecessor_snapshot_version_id]
        successor = by_id[successor_snapshot_version_id]
        if any(
            row["firm_id"] != firm_id or row["intake_id"] != intake_id
            for row in snapshots
        ):
            raise IntakeFollowupReconciliationError(
                "both snapshots must belong to the supplied firm and intake"
            )
        if any(
            row["snapshot_version_id"] is None
            or row["generation_batch_id"] is None
            for row in snapshots
        ):
            raise IntakeFollowupReconciliationError(
                "both snapshots must have governed generation provenance"
            )
        if successor["supersedes_snapshot_id"] != predecessor["snapshot_version_id"]:
            raise IntakeFollowupReconciliationError(
                "successor must directly supersede predecessor"
            )
        if successor["confirmation_status"] != "confirmed":
            raise IntakeFollowupReconciliationError(
                "successor snapshot must be confirmed"
            )
        if successor["snapshot_version_no"] <= predecessor["snapshot_version_no"]:
            raise IntakeFollowupReconciliationError(
                "successor snapshot version must be newer"
            )

        existing_rows = connection.execute(
            """
            SELECT superseded_followup_task_id, replacement_followup_task_id
            FROM intake_followup_reconciliations
            """
        ).fetchall()
        reconciled_predecessors = {row[0] for row in existing_rows}
        used_replacements = {row[1] for row in existing_rows}
        tasks = connection.execute(
            """
            SELECT id, firm_id, intake_id, task_type, priority, status, title,
                   description, completed_at, completed_by,
                   snapshot_version_id, generation_batch_id
            FROM intake_followup_tasks
            WHERE firm_id = ? AND intake_id = ?
              AND snapshot_version_id IN (?, ?)
            """,
            (
                firm_id, intake_id, predecessor_snapshot_version_id,
                successor_snapshot_version_id,
            ),
        ).fetchall()
        predecessor_tasks: dict[tuple[str, ...], list[sqlite3.Row]] = {}
        successor_tasks: dict[tuple[str, ...], list[sqlite3.Row]] = {}
        for task in tasks:
            if (
                task["snapshot_version_id"] == predecessor_snapshot_version_id
                and task["generation_batch_id"] == predecessor["generation_batch_id"]
                and task["id"] not in reconciled_predecessors
                and _normalize(task["status"]) != "completed"
                and task["completed_at"] is None
                and task["completed_by"] is None
            ):
                predecessor_tasks.setdefault(_signature(task), []).append(task)
            elif (
                task["snapshot_version_id"] == successor_snapshot_version_id
                and task["generation_batch_id"] == successor["generation_batch_id"]
            ):
                successor_tasks.setdefault(_signature(task), []).append(task)

        created = []
        now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        )
        reason = "Exact governed snapshot operational follow-up succession"
        for signature in sorted(set(predecessor_tasks) & set(successor_tasks)):
            prior_matches = predecessor_tasks[signature]
            successor_matches = successor_tasks[signature]
            if len(prior_matches) != 1 or len(successor_matches) != 1:
                continue
            if successor_matches[0]["id"] in used_replacements:
                continue
            reconciliation_id = str(uuid4())
            connection.execute(
                """
                INSERT INTO intake_followup_reconciliations (
                    reconciliation_id, firm_id, intake_id,
                    superseded_followup_task_id, replacement_followup_task_id,
                    reconciliation_type, reason, reconciled_at, reconciled_by
                ) VALUES (?, ?, ?, ?, ?, 'superseded_duplicate', ?, ?, ?)
                """,
                (
                    reconciliation_id, firm_id, intake_id,
                    prior_matches[0]["id"], successor_matches[0]["id"],
                    reason, now, reconciled_by,
                ),
            )
            created.append(reconciliation_id)
        return {"records_created": len(created), "reconciliation_ids": created}
    except (ValueError, IntakeFollowupReconciliationError):
        raise
    except sqlite3.Error as exc:
        raise IntakeFollowupReconciliationError(str(exc)) from exc


def get_intake_followup_reconciliation_history(
    db_path: str | Path, firm_id: str, intake_id: str
) -> list[dict[str, Any]]:
    """Return ledger history for one firm/intake scope without mutating it."""

    firm_id = _required(firm_id, "firm_id")
    intake_id = _required(intake_id, "intake_id")
    connection = _connect(db_path, read_only=True)
    try:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' "
            "AND name='intake_followup_reconciliations'"
        ).fetchone()
        if exists is None:
            return []
        return [
            dict(row) for row in connection.execute(
                """
                SELECT reconciliation_id, firm_id, intake_id,
                       superseded_followup_task_id, replacement_followup_task_id,
                       reconciliation_type, reason, reconciled_at, reconciled_by
                FROM intake_followup_reconciliations
                WHERE firm_id = ? AND intake_id = ?
                ORDER BY reconciled_at, reconciliation_id
                """,
                (firm_id, intake_id),
            )
        ]
    finally:
        connection.close()
