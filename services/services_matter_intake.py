from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from database.migrations_matter_intake import (
    apply_matter_intake_bridge_schema,
)


LINK_TABLE = "matter_intake_links"
EVENT_TABLE = "matter_intake_link_events"

BRIDGE_PREFIX = "MIB"
EVENT_PREFIX = "MIBE"

VALID_LINK_TYPES = {
    "PRIMARY",
    "SUPPLEMENTAL",
    "RENEWAL",
    "CORRECTIVE",
    "HISTORICAL",
}

VALID_LINK_STATUSES = {
    "PROPOSED",
    "ACTIVE",
    "SUSPENDED",
    "ENDED",
    "REJECTED",
}

VALID_HANDOFF_STATUSES = {
    "PENDING",
    "ACCEPTED",
    "MODIFIED",
    "REJECTED",
    "SUPERSEDED",
}

VALID_RECOMMENDATION_DISPOSITIONS = {
    "PENDING",
    "ACCEPTED",
    "MODIFIED",
    "REJECTED",
    "PARTIALLY_ACCEPTED",
}

VALID_EVENT_TYPES = {
    "LINK_PROPOSED",
    "LINK_ACTIVATED",
    "HANDOFF_ACCEPTED",
    "HANDOFF_MODIFIED",
    "HANDOFF_REJECTED",
    "LINK_SUSPENDED",
    "LINK_ENDED",
    "PRIMARY_CHANGED",
    "CORRECTION_RECORDED",
}


class MatterIntakeServiceError(RuntimeError):
    """Base exception for Matter–Intake bridge service failures."""


class MatterIntakeNotFoundError(MatterIntakeServiceError):
    """Raised when a firm-scoped Matter, Intake, or bridge cannot be found."""


class MatterIntakeValidationError(MatterIntakeServiceError):
    """Raised when requested bridge data violates the service contract."""


class MatterIntakeConflictError(MatterIntakeServiceError):
    """Raised when an active bridge or primary-link conflict exists."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _connect(db_path: str | Path) -> sqlite3.Connection:
    resolved = Path(db_path).expanduser().resolve()

    if not resolved.exists():
        raise MatterIntakeServiceError(
            f"Database does not exist: {resolved}"
        )

    connection = sqlite3.connect(str(resolved))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")

    return connection


def _clean_required(value: Any, field_name: str) -> str:
    text = str(value or "").strip()

    if not text:
        raise MatterIntakeValidationError(
            f"{field_name} is required."
        )

    return text


def _normalize_choice(
    value: Any,
    field_name: str,
    valid_values: set[str],
) -> str:
    normalized = _clean_required(value, field_name).upper()

    if normalized not in valid_values:
        raise MatterIntakeValidationError(
            f"Invalid {field_name}: {normalized}. "
            f"Allowed values: {', '.join(sorted(valid_values))}."
        )

    return normalized


def _normalize_optional_choice(
    value: Any,
    field_name: str,
    valid_values: set[str],
) -> str | None:
    if value is None or str(value).strip() == "":
        return None

    return _normalize_choice(
        value,
        field_name,
        valid_values,
    )


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None

    return dict(row)


def _next_identifier(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    prefix: str,
) -> str:
    rows = connection.execute(
        f"""
        SELECT {column_name}
        FROM {table_name}
        WHERE {column_name} LIKE ?
        """,
        (f"{prefix}-%",),
    ).fetchall()

    highest = 0
    pattern = re.compile(
        rf"^{re.escape(prefix)}-(\d+)$",
        re.IGNORECASE,
    )

    for row in rows:
        value = str(row[0] or "")
        match = pattern.match(value)

        if match:
            highest = max(highest, int(match.group(1)))

    return f"{prefix}-{highest + 1:06d}"


def _assert_matter_exists(
    connection: sqlite3.Connection,
    firm_id: str,
    matter_id: str,
) -> None:
    row = connection.execute(
        """
        SELECT 1
        FROM matters
        WHERE firm_id = ?
          AND matter_id = ?
        LIMIT 1
        """,
        (firm_id, matter_id),
    ).fetchone()

    if row is None:
        raise MatterIntakeNotFoundError(
            f"Matter {matter_id} was not found in {firm_id}."
        )


def _assert_intake_exists(
    connection: sqlite3.Connection,
    firm_id: str,
    intake_id: str,
) -> None:
    row = connection.execute(
        """
        SELECT 1
        FROM intake_sessions
        WHERE firm_id = ?
          AND intake_id = ?
        LIMIT 1
        """,
        (firm_id, intake_id),
    ).fetchone()

    if row is None:
        raise MatterIntakeNotFoundError(
            f"Intake {intake_id} was not found in {firm_id}."
        )


def _get_link_for_update(
    connection: sqlite3.Connection,
    firm_id: str,
    bridge_id: str,
) -> sqlite3.Row:
    row = connection.execute(
        f"""
        SELECT *
        FROM {LINK_TABLE}
        WHERE firm_id = ?
          AND bridge_id = ?
        LIMIT 1
        """,
        (firm_id, bridge_id),
    ).fetchone()

    if row is None:
        raise MatterIntakeNotFoundError(
            f"Bridge {bridge_id} was not found in {firm_id}."
        )

    return row


def _record_event(
    connection: sqlite3.Connection,
    *,
    bridge_id: str,
    firm_id: str,
    event_type: str,
    actor_id: str,
    event_basis: str | None,
    previous_state: Mapping[str, Any] | None,
    new_state: Mapping[str, Any] | None,
) -> dict[str, Any]:
    normalized_event_type = _normalize_choice(
        event_type,
        "event_type",
        VALID_EVENT_TYPES,
    )

    event_id = _next_identifier(
        connection,
        EVENT_TABLE,
        "event_id",
        EVENT_PREFIX,
    )

    connection.execute(
        f"""
        INSERT INTO {EVENT_TABLE} (
            event_id,
            bridge_id,
            firm_id,
            event_type,
            actor_id,
            event_basis,
            previous_state_json,
            new_state_json,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            bridge_id,
            firm_id,
            normalized_event_type,
            _clean_required(actor_id, "actor_id"),
            str(event_basis).strip() if event_basis else None,
            json.dumps(
                dict(previous_state),
                sort_keys=True,
                default=str,
            )
            if previous_state is not None
            else None,
            json.dumps(
                dict(new_state),
                sort_keys=True,
                default=str,
            )
            if new_state is not None
            else None,
            utc_now(),
        ),
    )

    row = connection.execute(
        f"""
        SELECT *
        FROM {EVENT_TABLE}
        WHERE event_id = ?
        """,
        (event_id,),
    ).fetchone()

    return dict(row)


def create_matter_intake_link(
    db_path: str | Path,
    *,
    firm_id: str,
    matter_id: str,
    intake_id: str,
    created_by: str,
    link_type: str = "PRIMARY",
    link_status: str = "PROPOSED",
    is_primary: bool = False,
    handoff_status: str = "PENDING",
    recommendation_disposition: str | None = "PENDING",
    intake_snapshot_id: str | None = None,
    effective_at: str | None = None,
    correction_basis: str | None = None,
    event_basis: str | None = None,
) -> dict[str, Any]:
    apply_matter_intake_bridge_schema(db_path)

    firm_id = _clean_required(firm_id, "firm_id")
    matter_id = _clean_required(matter_id, "matter_id")
    intake_id = _clean_required(intake_id, "intake_id")
    actor = _clean_required(created_by, "created_by")

    link_type = _normalize_choice(
        link_type,
        "link_type",
        VALID_LINK_TYPES,
    )

    link_status = _normalize_choice(
        link_status,
        "link_status",
        VALID_LINK_STATUSES,
    )

    handoff_status = _normalize_choice(
        handoff_status,
        "handoff_status",
        VALID_HANDOFF_STATUSES,
    )

    recommendation_disposition = _normalize_optional_choice(
        recommendation_disposition,
        "recommendation_disposition",
        VALID_RECOMMENDATION_DISPOSITIONS,
    )

    if is_primary and link_type not in {
        "PRIMARY",
        "RENEWAL",
        "CORRECTIVE",
    }:
        raise MatterIntakeValidationError(
            "A primary link must use PRIMARY, RENEWAL, "
            "or CORRECTIVE link_type."
        )

    connection = _connect(db_path)

    try:
        connection.execute("BEGIN IMMEDIATE")

        _assert_matter_exists(
            connection,
            firm_id,
            matter_id,
        )

        _assert_intake_exists(
            connection,
            firm_id,
            intake_id,
        )

        bridge_id = _next_identifier(
            connection,
            LINK_TABLE,
            "bridge_id",
            BRIDGE_PREFIX,
        )

        now = utc_now()

        connection.execute(
            f"""
            INSERT INTO {LINK_TABLE} (
                bridge_id,
                firm_id,
                matter_id,
                intake_id,
                link_type,
                link_status,
                is_primary,
                handoff_status,
                recommendation_disposition,
                intake_snapshot_id,
                effective_at,
                correction_basis,
                created_by,
                created_at,
                updated_by,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bridge_id,
                firm_id,
                matter_id,
                intake_id,
                link_type,
                link_status,
                1 if is_primary else 0,
                handoff_status,
                recommendation_disposition,
                str(intake_snapshot_id).strip()
                if intake_snapshot_id
                else None,
                effective_at,
                str(correction_basis).strip()
                if correction_basis
                else None,
                actor,
                now,
                actor,
                now,
            ),
        )

        link_row = _get_link_for_update(
            connection,
            firm_id,
            bridge_id,
        )

        event_type = (
            "LINK_ACTIVATED"
            if link_status == "ACTIVE"
            else "LINK_PROPOSED"
        )

        event = _record_event(
            connection,
            bridge_id=bridge_id,
            firm_id=firm_id,
            event_type=event_type,
            actor_id=actor,
            event_basis=event_basis,
            previous_state=None,
            new_state=dict(link_row),
        )

        connection.commit()

        return {
            "link": dict(link_row),
            "event": event,
        }

    except sqlite3.IntegrityError as error:
        connection.rollback()
        raise MatterIntakeConflictError(str(error)) from error

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_matter_intake_link(
    db_path: str | Path,
    *,
    firm_id: str,
    bridge_id: str,
) -> dict[str, Any] | None:
    connection = _connect(db_path)

    try:
        row = connection.execute(
            f"""
            SELECT *
            FROM {LINK_TABLE}
            WHERE firm_id = ?
              AND bridge_id = ?
            LIMIT 1
            """,
            (
                _clean_required(firm_id, "firm_id"),
                _clean_required(bridge_id, "bridge_id"),
            ),
        ).fetchone()

        return _row_to_dict(row)

    finally:
        connection.close()


def list_links_for_matter(
    db_path: str | Path,
    *,
    firm_id: str,
    matter_id: str,
    include_ended: bool = False,
) -> list[dict[str, Any]]:
    connection = _connect(db_path)

    try:
        sql = f"""
            SELECT *
            FROM {LINK_TABLE}
            WHERE firm_id = ?
              AND matter_id = ?
        """

        parameters: list[Any] = [
            _clean_required(firm_id, "firm_id"),
            _clean_required(matter_id, "matter_id"),
        ]

        if not include_ended:
            sql += """
              AND link_status != 'ENDED'
            """

        sql += """
            ORDER BY
                is_primary DESC,
                created_at DESC,
                bridge_id DESC
        """

        rows = connection.execute(
            sql,
            parameters,
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def list_links_for_intake(
    db_path: str | Path,
    *,
    firm_id: str,
    intake_id: str,
    include_ended: bool = False,
) -> list[dict[str, Any]]:
    connection = _connect(db_path)

    try:
        sql = f"""
            SELECT *
            FROM {LINK_TABLE}
            WHERE firm_id = ?
              AND intake_id = ?
        """

        parameters: list[Any] = [
            _clean_required(firm_id, "firm_id"),
            _clean_required(intake_id, "intake_id"),
        ]

        if not include_ended:
            sql += """
              AND link_status != 'ENDED'
            """

        sql += """
            ORDER BY
                is_primary DESC,
                created_at DESC,
                bridge_id DESC
        """

        rows = connection.execute(
            sql,
            parameters,
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def list_link_events(
    db_path: str | Path,
    *,
    firm_id: str,
    bridge_id: str,
) -> list[dict[str, Any]]:
    connection = _connect(db_path)

    try:
        rows = connection.execute(
            f"""
            SELECT *
            FROM {EVENT_TABLE}
            WHERE firm_id = ?
              AND bridge_id = ?
            ORDER BY created_at, event_id
            """,
            (
                _clean_required(firm_id, "firm_id"),
                _clean_required(bridge_id, "bridge_id"),
            ),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def update_handoff(
    db_path: str | Path,
    *,
    firm_id: str,
    bridge_id: str,
    handoff_status: str,
    actor_id: str,
    recommendation_disposition: str | None = None,
    event_basis: str | None = None,
) -> dict[str, Any]:
    normalized_status = _normalize_choice(
        handoff_status,
        "handoff_status",
        {
            "ACCEPTED",
            "MODIFIED",
            "REJECTED",
        },
    )

    normalized_disposition = _normalize_optional_choice(
        recommendation_disposition,
        "recommendation_disposition",
        VALID_RECOMMENDATION_DISPOSITIONS,
    )

    actor = _clean_required(actor_id, "actor_id")
    firm_id = _clean_required(firm_id, "firm_id")
    bridge_id = _clean_required(bridge_id, "bridge_id")

    event_type = {
        "ACCEPTED": "HANDOFF_ACCEPTED",
        "MODIFIED": "HANDOFF_MODIFIED",
        "REJECTED": "HANDOFF_REJECTED",
    }[normalized_status]

    connection = _connect(db_path)

    try:
        connection.execute("BEGIN IMMEDIATE")

        previous = _get_link_for_update(
            connection,
            firm_id,
            bridge_id,
        )

        if previous["link_status"] == "ENDED":
            raise MatterIntakeConflictError(
                "An ended bridge cannot receive a handoff decision."
            )

        now = utc_now()

        link_status = previous["link_status"]

        if normalized_status == "ACCEPTED":
            link_status = "ACTIVE"
        elif normalized_status == "REJECTED":
            link_status = "REJECTED"

        connection.execute(
            f"""
            UPDATE {LINK_TABLE}
            SET handoff_status = ?,
                handoff_by = ?,
                handoff_at = ?,
                recommendation_disposition = COALESCE(?, recommendation_disposition),
                link_status = ?,
                updated_by = ?,
                updated_at = ?
            WHERE firm_id = ?
              AND bridge_id = ?
            """,
            (
                normalized_status,
                actor,
                now,
                normalized_disposition,
                link_status,
                actor,
                now,
                firm_id,
                bridge_id,
            ),
        )

        current = _get_link_for_update(
            connection,
            firm_id,
            bridge_id,
        )

        event = _record_event(
            connection,
            bridge_id=bridge_id,
            firm_id=firm_id,
            event_type=event_type,
            actor_id=actor,
            event_basis=event_basis,
            previous_state=dict(previous),
            new_state=dict(current),
        )

        connection.commit()

        return {
            "link": dict(current),
            "event": event,
        }

    except sqlite3.IntegrityError as error:
        connection.rollback()
        raise MatterIntakeConflictError(str(error)) from error

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def end_matter_intake_link(
    db_path: str | Path,
    *,
    firm_id: str,
    bridge_id: str,
    actor_id: str,
    event_basis: str,
) -> dict[str, Any]:
    firm_id = _clean_required(firm_id, "firm_id")
    bridge_id = _clean_required(bridge_id, "bridge_id")
    actor = _clean_required(actor_id, "actor_id")
    basis = _clean_required(event_basis, "event_basis")

    connection = _connect(db_path)

    try:
        connection.execute("BEGIN IMMEDIATE")

        previous = _get_link_for_update(
            connection,
            firm_id,
            bridge_id,
        )

        if previous["link_status"] == "ENDED":
            raise MatterIntakeConflictError(
                "Bridge is already ended."
            )

        now = utc_now()

        connection.execute(
            f"""
            UPDATE {LINK_TABLE}
            SET link_status = 'ENDED',
                is_primary = 0,
                ended_at = ?,
                updated_by = ?,
                updated_at = ?
            WHERE firm_id = ?
              AND bridge_id = ?
            """,
            (
                now,
                actor,
                now,
                firm_id,
                bridge_id,
            ),
        )

        current = _get_link_for_update(
            connection,
            firm_id,
            bridge_id,
        )

        event = _record_event(
            connection,
            bridge_id=bridge_id,
            firm_id=firm_id,
            event_type="LINK_ENDED",
            actor_id=actor,
            event_basis=basis,
            previous_state=dict(previous),
            new_state=dict(current),
        )

        connection.commit()

        return {
            "link": dict(current),
            "event": event,
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
