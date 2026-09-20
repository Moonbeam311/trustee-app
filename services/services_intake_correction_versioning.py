"""Transactional service foundation for governed Guided Intake corrections.

The module is deliberately independent of Flask and repository-global database
helpers.  Every public operation requires an explicit SQLite database path.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any, Iterable, Mapping
from uuid import uuid4

from services.services_intake_followup_reconciliation import (
    IntakeFollowupReconciliationError,
    reconcile_governed_snapshot_followup_successors_in_transaction,
)


class IntakeCorrectionVersioningError(RuntimeError):
    """Raised when a governed correction/versioning invariant is violated."""


_OPERATIONAL_STATUSES = {
    "open",
    "pending_client",
    "pending_staff",
    "pending_professional",
}


def _required(value: Any, name: str) -> str:
    if value is None or not str(value).strip():
        raise ValueError(f"{name} is required")
    return str(value).strip()


def _db_path(db_path: str | Path) -> Path:
    return Path(_required(db_path, "db_path"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _connect(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(_db_path(db_path)))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _connect_read_only(db_path: str | Path) -> sqlite3.Connection:
    path = _db_path(db_path).resolve()
    try:
        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        raise IntakeCorrectionVersioningError(
            f"governed intake database is not readable: {exc}"
        ) from exc
    connection.row_factory = sqlite3.Row
    return connection


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone() is not None


_GOVERNED_TABLES = {
    "intake_answer_revisions",
    "intake_answer_revision_items",
    "intake_snapshot_versions",
    "intake_snapshot_translation_items",
    "intake_snapshot_proposed_tasks",
}


def assert_intake_correction_versioning_schema_ready(
    db_path: str | Path,
) -> bool:
    """Verify the governed schema without creating or altering any objects."""

    connection = _connect_read_only(db_path)
    try:
        missing = sorted(
            table for table in _GOVERNED_TABLES
            if not _table_exists(connection, table)
        )
        if missing:
            raise IntakeCorrectionVersioningError(
                "governed intake schema is not ready; missing tables: "
                + ", ".join(missing)
            )
        if not _table_exists(connection, "intake_followup_tasks"):
            raise IntakeCorrectionVersioningError(
                "governed intake schema is not ready; missing table: "
                "intake_followup_tasks"
            )
        proposed_columns = {
            row["name"] for row in connection.execute(
                "PRAGMA table_info(intake_snapshot_proposed_tasks)"
            )
        }
        followup_columns = {
            row["name"] for row in connection.execute(
                "PRAGMA table_info(intake_followup_tasks)"
            )
        }
        missing_columns = []
        if "operational_status" not in proposed_columns:
            missing_columns.append(
                "intake_snapshot_proposed_tasks.operational_status"
            )
        for column in ("snapshot_version_id", "generation_batch_id"):
            if column not in followup_columns:
                missing_columns.append(f"intake_followup_tasks.{column}")
        if missing_columns:
            raise IntakeCorrectionVersioningError(
                "governed intake schema is not ready; missing columns: "
                + ", ".join(missing_columns)
            )
        return True
    finally:
        connection.close()


def _validate_intake_scope(
    connection: sqlite3.Connection, firm_id: str, intake_id: str
) -> None:
    if not _table_exists(connection, "intake_sessions"):
        raise IntakeCorrectionVersioningError(
            "intake_sessions is required to validate firm/intake scope"
        )
    row = connection.execute(
        "SELECT firm_id FROM intake_sessions WHERE intake_id = ?", (intake_id,)
    ).fetchone()
    if row is None or row["firm_id"] != firm_id:
        raise IntakeCorrectionVersioningError("firm_id and intake_id do not identify the same intake")


def _items(items: Iterable[Mapping[str, Any]], required: tuple[str, ...]) -> list[dict[str, Any]]:
    if items is None:
        raise ValueError("items are required")
    normalized = []
    for item in items:
        if not isinstance(item, Mapping):
            raise ValueError("each item must be a mapping")
        copy = dict(item)
        for key in required:
            copy[key] = _required(copy.get(key), key)
        normalized.append(copy)
    return normalized


def _row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def get_latest_governed_answer_selections(
    db_path: str | Path,
    firm_id: str,
    intake_id: str,
) -> dict[str, list[str]]:
    """Return the latest governed selections, grouped by question key."""

    firm_id = _required(firm_id, "firm_id")
    intake_id = _required(intake_id, "intake_id")
    connection = _connect_read_only(db_path)
    try:
        _validate_intake_scope(connection, firm_id, intake_id)
        revision = connection.execute(
            """
            SELECT answer_revision_id
            FROM intake_answer_revisions
            WHERE firm_id = ? AND intake_id = ?
            ORDER BY answer_revision_no DESC
            LIMIT 1
            """,
            (firm_id, intake_id),
        ).fetchone()
        if revision is None:
            return {}

        selections: dict[str, list[str]] = {}
        rows = connection.execute(
            """
            SELECT question_key, answer_key
            FROM intake_answer_revision_items
            WHERE answer_revision_id = ?
            ORDER BY id
            """,
            (revision["answer_revision_id"],),
        ).fetchall()
        for row in rows:
            selections.setdefault(row["question_key"], []).append(row["answer_key"])
        return selections
    finally:
        connection.close()


def get_intake_revision_history(
    db_path: str | Path,
    firm_id: str,
    intake_id: str,
) -> list[dict[str, Any]]:
    """Return immutable governed revisions and read-time selection changes."""

    firm_id = _required(firm_id, "firm_id")
    intake_id = _required(intake_id, "intake_id")
    connection = _connect_read_only(db_path)
    try:
        _validate_intake_scope(connection, firm_id, intake_id)
        revisions = connection.execute(
            """
            SELECT *
            FROM intake_answer_revisions
            WHERE firm_id = ? AND intake_id = ?
            ORDER BY answer_revision_no
            """,
            (firm_id, intake_id),
        ).fetchall()

        history: list[dict[str, Any]] = []
        previous: dict[str, set[str]] = {}
        for revision_row in revisions:
            revision = dict(revision_row)
            items = [
                dict(row) for row in connection.execute(
                    """
                    SELECT *
                    FROM intake_answer_revision_items
                    WHERE answer_revision_id = ?
                    ORDER BY id
                    """,
                    (revision["answer_revision_id"],),
                ).fetchall()
            ]
            snapshot_row = connection.execute(
                """
                SELECT *
                FROM intake_snapshot_versions
                WHERE firm_id = ? AND intake_id = ? AND answer_revision_id = ?
                ORDER BY snapshot_version_no DESC
                LIMIT 1
                """,
                (firm_id, intake_id, revision["answer_revision_id"]),
            ).fetchone()

            current: dict[str, set[str]] = {}
            for item in items:
                current.setdefault(item["question_key"], set()).add(
                    item["answer_key"]
                )

            additions: list[dict[str, str]] = []
            removals: list[dict[str, str]] = []
            if history:
                for question_key in sorted(set(previous) | set(current)):
                    for answer_key in sorted(
                        current.get(question_key, set())
                        - previous.get(question_key, set())
                    ):
                        additions.append({
                            "question_key": question_key,
                            "answer_key": answer_key,
                        })
                    for answer_key in sorted(
                        previous.get(question_key, set())
                        - current.get(question_key, set())
                    ):
                        removals.append({
                            "question_key": question_key,
                            "answer_key": answer_key,
                        })

            revision["items"] = items
            revision["snapshot_version"] = _row_dict(snapshot_row)
            revision["changes"] = {
                "additions": additions,
                "removals": removals,
            }
            history.append(revision)
            previous = current
        return history
    finally:
        connection.close()


def create_answer_revision(
    db_path: str | Path,
    firm_id: str,
    intake_id: str,
    answer_items: Iterable[Mapping[str, Any]],
    created_by: str | None,
) -> dict[str, Any]:
    """Create an immutable revision from caller-supplied answer items."""

    firm_id = _required(firm_id, "firm_id")
    intake_id = _required(intake_id, "intake_id")
    answers = _items(answer_items, ("question_key", "answer_key"))
    identities = [(item["question_key"], item["answer_key"]) for item in answers]
    if len(identities) != len(set(identities)):
        raise IntakeCorrectionVersioningError("duplicate answer item in revision")

    connection = _connect(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        _validate_intake_scope(connection, firm_id, intake_id)
        prior = connection.execute(
            """
            SELECT * FROM intake_answer_revisions
            WHERE firm_id = ? AND intake_id = ?
            ORDER BY answer_revision_no DESC LIMIT 1
            """,
            (firm_id, intake_id),
        ).fetchone()
        revision_no = 1 if prior is None else prior["answer_revision_no"] + 1
        revision_id = f"IAR-{uuid4()}"
        created_at = _now()
        supersedes_id = prior["answer_revision_id"] if prior is not None else None

        if prior is not None and prior["revision_status"] in (
            "draft", "awaiting_confirmation"
        ):
            connection.execute(
                "UPDATE intake_answer_revisions SET revision_status = 'superseded' "
                "WHERE answer_revision_id = ?",
                (prior["answer_revision_id"],),
            )

        # A correction makes every still-unconfirmed derivation from the old
        # answers ineligible for confirmation, even before a replacement
        # snapshot is generated.
        pending_snapshots = connection.execute(
            """
            SELECT snapshot_version_id FROM intake_snapshot_versions
            WHERE firm_id = ? AND intake_id = ?
              AND confirmation_status = 'awaiting_confirmation'
            """,
            (firm_id, intake_id),
        ).fetchall()
        for pending in pending_snapshots:
            connection.execute(
                "UPDATE intake_snapshot_versions SET confirmation_status = 'superseded' "
                "WHERE snapshot_version_id = ?",
                (pending["snapshot_version_id"],),
            )
            connection.execute(
                """
                UPDATE intake_snapshot_proposed_tasks SET proposal_status = 'superseded'
                WHERE snapshot_version_id = ? AND proposal_status = 'proposed'
                """,
                (pending["snapshot_version_id"],),
            )

        connection.execute(
            """
            INSERT INTO intake_answer_revisions (
                answer_revision_id, intake_id, firm_id, answer_revision_no,
                revision_status, supersedes_revision_id, created_at, created_by
            ) VALUES (?, ?, ?, ?, 'awaiting_confirmation', ?, ?, ?)
            """,
            (
                revision_id, intake_id, firm_id, revision_no, supersedes_id,
                created_at, created_by,
            ),
        )
        connection.executemany(
            """
            INSERT INTO intake_answer_revision_items (
                answer_revision_id, question_key, answer_key, answer_label,
                created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    revision_id, item["question_key"], item["answer_key"],
                    item.get("answer_label"), created_at, created_by,
                )
                for item in answers
            ],
        )
        connection.commit()
        return {
            "answer_revision_id": revision_id,
            "firm_id": firm_id,
            "intake_id": intake_id,
            "answer_revision_no": revision_no,
            "revision_status": "awaiting_confirmation",
            "supersedes_revision_id": supersedes_id,
            "created_at": created_at,
            "created_by": created_by,
            "answer_items": answers,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def create_snapshot_version(
    db_path: str | Path,
    firm_id: str,
    intake_id: str,
    answer_revision_id: str,
    translation_items: Iterable[Mapping[str, Any]],
    proposed_tasks: Iterable[Mapping[str, Any]],
    generated_by: str | None,
) -> dict[str, Any]:
    """Create an immutable snapshot and proposed tasks without materializing work."""

    firm_id = _required(firm_id, "firm_id")
    intake_id = _required(intake_id, "intake_id")
    answer_revision_id = _required(answer_revision_id, "answer_revision_id")
    translations = _items(translation_items, ("source_key",))
    tasks = _items(proposed_tasks, ("title",))
    for task in tasks:
        operational_status = task.get("operational_status")
        if operational_status is None or not str(operational_status).strip():
            operational_status = "open"
        else:
            operational_status = str(operational_status).strip()
        if operational_status not in _OPERATIONAL_STATUSES:
            raise IntakeCorrectionVersioningError(
                f"unsupported operational_status: {operational_status}"
            )
        task["operational_status"] = operational_status

    connection = _connect(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        _validate_intake_scope(connection, firm_id, intake_id)
        revision = connection.execute(
            """
            SELECT * FROM intake_answer_revisions
            WHERE answer_revision_id = ? AND firm_id = ? AND intake_id = ?
            """,
            (answer_revision_id, firm_id, intake_id),
        ).fetchone()
        if revision is None:
            raise IntakeCorrectionVersioningError(
                "answer revision does not belong to the supplied firm/intake"
            )
        latest_revision = connection.execute(
            """
            SELECT answer_revision_id FROM intake_answer_revisions
            WHERE firm_id = ? AND intake_id = ?
            ORDER BY answer_revision_no DESC LIMIT 1
            """,
            (firm_id, intake_id),
        ).fetchone()
        if (
            latest_revision is None
            or revision["answer_revision_id"] != latest_revision["answer_revision_id"]
        ):
            raise IntakeCorrectionVersioningError(
                "cannot snapshot an older/non-current answer revision"
            )
        if revision["revision_status"] != "awaiting_confirmation":
            raise IntakeCorrectionVersioningError(
                "current answer revision is not awaiting confirmation"
            )

        prior = connection.execute(
            """
            SELECT * FROM intake_snapshot_versions
            WHERE firm_id = ? AND intake_id = ?
            ORDER BY snapshot_version_no DESC LIMIT 1
            """,
            (firm_id, intake_id),
        ).fetchone()
        version_no = 1 if prior is None else prior["snapshot_version_no"] + 1
        supersedes_id = prior["snapshot_version_id"] if prior is not None else None
        if prior is not None and prior["confirmation_status"] == "awaiting_confirmation":
            connection.execute(
                "UPDATE intake_snapshot_versions SET confirmation_status = 'superseded' "
                "WHERE snapshot_version_id = ?",
                (prior["snapshot_version_id"],),
            )
            connection.execute(
                """
                UPDATE intake_snapshot_proposed_tasks SET proposal_status = 'superseded'
                WHERE snapshot_version_id = ? AND proposal_status = 'proposed'
                """,
                (prior["snapshot_version_id"],),
            )

        snapshot_id = f"ISV-{uuid4()}"
        batch_id = f"IGB-{uuid4()}"
        generated_at = _now()
        connection.execute(
            """
            INSERT INTO intake_snapshot_versions (
                snapshot_version_id, intake_id, firm_id, answer_revision_id,
                snapshot_version_no, generation_batch_id, confirmation_status,
                supersedes_snapshot_id, generated_at, generated_by
            ) VALUES (?, ?, ?, ?, ?, ?, 'awaiting_confirmation', ?, ?, ?)
            """,
            (
                snapshot_id, intake_id, firm_id, answer_revision_id, version_no,
                batch_id, supersedes_id, generated_at, generated_by,
            ),
        )
        connection.executemany(
            """
            INSERT INTO intake_snapshot_translation_items (
                snapshot_version_id, source_key, system_category, system_meaning,
                module_trigger, document_request, next_session, risk_flag,
                created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    snapshot_id, item["source_key"], item.get("system_category"),
                    item.get("system_meaning"), item.get("module_trigger"),
                    item.get("document_request"), item.get("next_session"),
                    item.get("risk_flag"), generated_at, generated_by,
                )
                for item in translations
            ],
        )
        connection.executemany(
            """
            INSERT INTO intake_snapshot_proposed_tasks (
                proposed_task_id, snapshot_version_id, generation_batch_id,
                task_type, priority, title, description, source,
                operational_status, proposal_status, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'proposed', ?, ?)
            """,
            [
                (
                    f"IPT-{uuid4()}", snapshot_id, batch_id,
                    item.get("task_type"), item.get("priority"), item["title"],
                    item.get("description"), item.get("source"),
                    item["operational_status"], generated_at, generated_by,
                )
                for item in tasks
            ],
        )
        connection.commit()
        return {
            "snapshot_version_id": snapshot_id,
            "firm_id": firm_id,
            "intake_id": intake_id,
            "answer_revision_id": answer_revision_id,
            "snapshot_version_no": version_no,
            "generation_batch_id": batch_id,
            "confirmation_status": "awaiting_confirmation",
            "supersedes_snapshot_id": supersedes_id,
            "generated_at": generated_at,
            "generated_by": generated_by,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _followup_columns(connection: sqlite3.Connection) -> set[str]:
    if not _table_exists(connection, "intake_followup_tasks"):
        raise IntakeCorrectionVersioningError("intake_followup_tasks table is required")
    return {
        row["name"]
        for row in connection.execute("PRAGMA table_info(intake_followup_tasks)")
    }


def confirm_snapshot(
    db_path: str | Path,
    firm_id: str,
    intake_id: str,
    snapshot_version_id: str,
    confirmed_by: str | None,
) -> dict[str, Any]:
    """Confirm one awaiting snapshot and atomically materialize its proposals."""

    firm_id = _required(firm_id, "firm_id")
    intake_id = _required(intake_id, "intake_id")
    snapshot_version_id = _required(snapshot_version_id, "snapshot_version_id")
    confirmed_by = _required(confirmed_by, "confirmed_by")
    connection = _connect(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        _validate_intake_scope(connection, firm_id, intake_id)
        snapshot = connection.execute(
            """
            SELECT * FROM intake_snapshot_versions
            WHERE snapshot_version_id = ? AND firm_id = ? AND intake_id = ?
            """,
            (snapshot_version_id, firm_id, intake_id),
        ).fetchone()
        if snapshot is None:
            raise IntakeCorrectionVersioningError(
                "snapshot does not belong to the supplied firm/intake"
            )
        if snapshot["confirmation_status"] == "superseded":
            raise IntakeCorrectionVersioningError("superseded snapshot cannot be confirmed")
        if snapshot["confirmation_status"] == "confirmed":
            count = connection.execute(
                "SELECT COUNT(*) FROM intake_snapshot_proposed_tasks "
                "WHERE snapshot_version_id = ? AND proposal_status = 'materialized'",
                (snapshot_version_id,),
            ).fetchone()[0]
            connection.commit()
            return {
                "snapshot_version_id": snapshot_version_id,
                "confirmation_status": "confirmed",
                "materialized_task_count": count,
                "already_confirmed": True,
            }

        revision = connection.execute(
            "SELECT revision_status FROM intake_answer_revisions "
            "WHERE answer_revision_id = ?",
            (snapshot["answer_revision_id"],),
        ).fetchone()
        if revision is None or revision["revision_status"] != "awaiting_confirmation":
            raise IntakeCorrectionVersioningError(
                "snapshot answer revision is not awaiting confirmation"
            )

        columns = _followup_columns(connection)
        if not {"snapshot_version_id", "generation_batch_id"}.issubset(columns):
            raise IntakeCorrectionVersioningError(
                "intake_followup_tasks lacks required provenance columns"
            )
        proposals = connection.execute(
            """
            SELECT * FROM intake_snapshot_proposed_tasks
            WHERE snapshot_version_id = ? AND proposal_status = 'proposed'
            ORDER BY rowid
            """,
            (snapshot_version_id,),
        ).fetchall()
        confirmed_at = _now()
        materialized = 0
        for proposal in proposals:
            values = {
                "intake_id": intake_id,
                "firm_id": firm_id,
                "task_type": proposal["task_type"] or "staff_action",
                "priority": proposal["priority"] or "normal",
                "status": proposal["operational_status"] or "open",
                "title": proposal["title"],
                "description": proposal["description"],
                "source": proposal["source"] or "guided_intake_snapshot",
                "created_at": confirmed_at,
                "updated_at": confirmed_at,
                "created_by": confirmed_by,
                "snapshot_version_id": snapshot_version_id,
                "generation_batch_id": snapshot["generation_batch_id"],
            }
            insert_columns = [name for name in values if name in columns]
            cursor = connection.execute(
                f"INSERT INTO intake_followup_tasks ({', '.join(insert_columns)}) "
                f"VALUES ({', '.join('?' for _ in insert_columns)})",
                tuple(values[name] for name in insert_columns),
            )
            connection.execute(
                """
                UPDATE intake_snapshot_proposed_tasks
                SET proposal_status = 'materialized',
                    materialized_followup_task_id = ?, materialized_at = ?
                WHERE proposed_task_id = ?
                """,
                (str(cursor.lastrowid), confirmed_at, proposal["proposed_task_id"]),
            )
            materialized += 1

        connection.execute(
            """
            UPDATE intake_snapshot_versions
            SET confirmation_status = 'confirmed', confirmed_at = ?, confirmed_by = ?
            WHERE snapshot_version_id = ?
            """,
            (confirmed_at, confirmed_by, snapshot_version_id),
        )
        connection.execute(
            """
            UPDATE intake_answer_revisions
            SET revision_status = 'confirmed', confirmed_at = ?, confirmed_by = ?
            WHERE answer_revision_id = ?
            """,
            (confirmed_at, confirmed_by, snapshot["answer_revision_id"]),
        )
        if (
            snapshot["supersedes_snapshot_id"] is not None
            and _table_exists(connection, "intake_followup_reconciliations")
        ):
            try:
                reconcile_governed_snapshot_followup_successors_in_transaction(
                    connection,
                    firm_id,
                    intake_id,
                    snapshot["supersedes_snapshot_id"],
                    snapshot_version_id,
                    confirmed_by,
                )
            except IntakeFollowupReconciliationError as exc:
                raise IntakeCorrectionVersioningError(
                    f"governed follow-up succession failed: {exc}"
                ) from exc
        connection.commit()
        return {
            "snapshot_version_id": snapshot_version_id,
            "confirmation_status": "confirmed",
            "materialized_task_count": materialized,
            "already_confirmed": False,
            "confirmed_at": confirmed_at,
            "confirmed_by": confirmed_by,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_intake_correction_versioning_state(
    db_path: str | Path, firm_id: str, intake_id: str
) -> dict[str, Any]:
    """Return only the governed current state for one firm/intake pair."""

    firm_id = _required(firm_id, "firm_id")
    intake_id = _required(intake_id, "intake_id")
    connection = _connect_read_only(db_path)
    try:
        _validate_intake_scope(connection, firm_id, intake_id)
        revision = connection.execute(
            """
            SELECT * FROM intake_answer_revisions
            WHERE firm_id = ? AND intake_id = ?
            ORDER BY answer_revision_no DESC LIMIT 1
            """,
            (firm_id, intake_id),
        ).fetchone()
        latest_snapshot = connection.execute(
            """
            SELECT * FROM intake_snapshot_versions
            WHERE firm_id = ? AND intake_id = ?
            ORDER BY snapshot_version_no DESC LIMIT 1
            """,
            (firm_id, intake_id),
        ).fetchone()
        current_snapshot = None
        if revision is not None:
            current_snapshot = connection.execute(
                """
                SELECT * FROM intake_snapshot_versions
                WHERE firm_id = ? AND intake_id = ? AND answer_revision_id = ?
                ORDER BY snapshot_version_no DESC LIMIT 1
                """,
                (firm_id, intake_id, revision["answer_revision_id"]),
            ).fetchone()
        revision_data = _row_dict(revision)
        snapshot_data = _row_dict(latest_snapshot)
        current_snapshot_data = _row_dict(current_snapshot)
        latest_snapshot_matches_latest_revision = bool(
            latest_snapshot is not None
            and revision is not None
            and latest_snapshot["answer_revision_id"] == revision["answer_revision_id"]
        )
        can_confirm = bool(
            current_snapshot is not None
            and current_snapshot["confirmation_status"] == "awaiting_confirmation"
            and revision is not None
            and revision["revision_status"] == "awaiting_confirmation"
        )
        return {
            "firm_id": firm_id,
            "intake_id": intake_id,
            "latest_answer_revision": revision_data,
            "latest_snapshot_version": snapshot_data,
            "current_snapshot_version": current_snapshot_data,
            "latest_snapshot_matches_latest_revision": (
                latest_snapshot_matches_latest_revision
            ),
            "answer_revision_no": revision["answer_revision_no"] if revision else None,
            "snapshot_version_no": (
                latest_snapshot["snapshot_version_no"] if latest_snapshot else None
            ),
            "confirmation_state": (
                current_snapshot["confirmation_status"]
                if current_snapshot
                else "not_generated"
            ),
            "correction_allowed": True,
            "confirmation_allowed": can_confirm,
        }
    finally:
        connection.close()


def list_snapshot_proposed_tasks(
    db_path: str | Path,
    firm_id: str,
    intake_id: str,
    snapshot_version_id: str,
) -> list[dict[str, Any]]:
    """Read proposed tasks for exactly one scoped governed snapshot."""

    firm_id = _required(firm_id, "firm_id")
    intake_id = _required(intake_id, "intake_id")
    snapshot_version_id = _required(snapshot_version_id, "snapshot_version_id")
    connection = _connect_read_only(db_path)
    try:
        _validate_intake_scope(connection, firm_id, intake_id)
        snapshot = connection.execute(
            "SELECT 1 FROM intake_snapshot_versions "
            "WHERE snapshot_version_id = ? AND firm_id = ? AND intake_id = ?",
            (snapshot_version_id, firm_id, intake_id),
        ).fetchone()
        if snapshot is None:
            raise IntakeCorrectionVersioningError(
                "snapshot does not belong to the supplied firm/intake"
            )
        rows = connection.execute(
            "SELECT * FROM intake_snapshot_proposed_tasks "
            "WHERE snapshot_version_id = ? ORDER BY rowid",
            (snapshot_version_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


# A concise alias for callers that prefer a read-oriented name.
read_intake_correction_versioning_state = get_intake_correction_versioning_state
