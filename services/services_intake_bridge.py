"""Focused Intake -> Canonical Person -> Guided Intake bridge service.

The bridge is deliberately explicit:

    Focused identity intake
        -> canonical Person
        -> optional Full Guided intake

This module never selects a production database implicitly.  Every direct
database operation requires ``db_path``.  Guided-session creation is injected
because the existing Guided intake service owns application-global database
state.

No name-based Person deduplication is performed.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Callable
import uuid

from database.intake_bridge_migration import BRIDGE_TABLE
from services.services_person_identity import (
    create_person_identity,
    generate_person_identity_id,
    get_person_identity,
)


class IntakeBridgeError(ValueError):
    """Raised when an intake bridge request violates the bridge contract."""


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect(db_path: str | Path) -> sqlite3.Connection:
    if db_path is None or not str(db_path).strip():
        raise IntakeBridgeError("db_path is required.")

    con = sqlite3.connect(str(Path(db_path).expanduser()))
    con.row_factory = sqlite3.Row
    return con


def _require_scope(
    owner_id: str,
    firm_id: str,
) -> tuple[str, str]:
    owner = _clean(owner_id)
    firm = _clean(firm_id)

    if not owner:
        raise IntakeBridgeError("owner_id is required.")

    if not firm:
        raise IntakeBridgeError("firm_id is required.")

    return owner, firm


def _require_bridge_table(
    con: sqlite3.Connection,
) -> None:
    row = con.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (BRIDGE_TABLE,),
    ).fetchone()

    if row is None:
        raise IntakeBridgeError(
            "Intake bridge table is not initialized."
        )


def get_intake_bridge(
    db_path: str | Path,
    firm_id: str,
    focused_intake_id: str,
) -> dict[str, Any] | None:
    """Return one bridge inside the explicit firm/focused-intake scope."""

    firm = _clean(firm_id)
    focused_id = _clean(focused_intake_id)

    if not firm or not focused_id:
        raise IntakeBridgeError(
            "firm_id and focused_intake_id are required."
        )

    con = _connect(db_path)

    try:
        _require_bridge_table(con)

        row = con.execute(
            f"""
            SELECT *
            FROM {BRIDGE_TABLE}
            WHERE firm_id = ?
              AND focused_intake_id = ?
            """,
            (firm, focused_id),
        ).fetchone()

        return dict(row) if row else None
    finally:
        con.close()


def _get_focused_identity(
    db_path: str | Path,
    firm_id: str,
    focused_intake_id: str,
) -> dict[str, Any]:
    """Load one Focused identity without modifying it."""

    con = _connect(db_path)

    try:
        row = con.execute(
            """
            SELECT *
            FROM identity_intake
            WHERE firm_id = ?
              AND intake_id = ?
            """,
            (
                _clean(firm_id),
                _clean(focused_intake_id),
            ),
        ).fetchone()

        if row is None:
            raise IntakeBridgeError(
                "Focused identity intake was not found "
                "inside the requested firm scope."
            )

        return dict(row)
    finally:
        con.close()


def establish_person_bridge(
    db_path: str | Path,
    *,
    owner_id: str,
    firm_id: str,
    focused_intake_id: str,
    created_by: str,
) -> dict[str, Any]:
    """Create or reuse the canonical Person side of one bridge.

    Idempotency is keyed by ``firm_id + focused_intake_id``.
    Existing Persons are never selected by display-name matching.
    """

    owner, firm = _require_scope(owner_id, firm_id)
    focused_id = _clean(focused_intake_id)
    actor = _clean(created_by)

    if not focused_id:
        raise IntakeBridgeError(
            "focused_intake_id is required."
        )

    if not actor:
        raise IntakeBridgeError(
            "created_by is required."
        )

    existing = get_intake_bridge(
        db_path,
        firm,
        focused_id,
    )

    if existing is not None:
        person = get_person_identity(
            db_path,
            existing["person_id"],
            owner,
            firm,
        )

        if person is None:
            raise IntakeBridgeError(
                "Bridge references a missing canonical Person."
            )

        return existing

    focused = _get_focused_identity(
        db_path,
        firm,
        focused_id,
    )

    person_id = generate_person_identity_id()

    create_person_identity(
        db_path,
        {
            "person_id": person_id,
            "owner_id": owner,
            "firm_id": firm,
            "display_name": _clean(
                focused.get("primary_full_name")
            ),
            "sort_name": None,
            "notes": None,
            "created_by": actor,
        },
    )

    bridge_id = "IBR-" + uuid.uuid4().hex[:20].upper()
    now = _now()

    provenance = {
        "bridge_contract": "FOCUSED_CANONICAL_GUIDED",
        "focused_model": "identity_intake",
        "focused_intake_id": focused_id,
        "canonical_person_id": person_id,
    }

    con = _connect(db_path)

    try:
        _require_bridge_table(con)

        try:
            con.execute(
                f"""
                INSERT INTO {BRIDGE_TABLE} (
                    bridge_id,
                    firm_id,
                    focused_intake_id,
                    person_id,
                    guided_intake_id,
                    guided_lane_key,
                    bridge_status,
                    provenance_json,
                    created_by,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?)
                """,
                (
                    bridge_id,
                    firm,
                    focused_id,
                    person_id,
                    "person_linked",
                    json.dumps(
                        provenance,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    actor,
                    now,
                    now,
                ),
            )

            con.commit()

        except sqlite3.IntegrityError as exc:
            con.rollback()

            # A repeated operation may have raced with another valid
            # bridge creation.  Re-read the canonical bridge instead of
            # creating a second Guided relationship.
            winner = get_intake_bridge(
                db_path,
                firm,
                focused_id,
            )

            if winner is not None:
                return winner

            raise IntakeBridgeError(
                "Canonical Person bridge could not be created."
            ) from exc

    finally:
        con.close()

    created = get_intake_bridge(
        db_path,
        firm,
        focused_id,
    )

    if created is None:
        raise IntakeBridgeError(
            "Created intake bridge could not be reloaded."
        )

    return created


def attach_guided_intake(
    db_path: str | Path,
    *,
    firm_id: str,
    focused_intake_id: str,
    guided_intake_id: str,
    guided_lane_key: str,
) -> dict[str, Any]:
    """Attach one already-created Guided intake to an existing bridge."""

    firm = _clean(firm_id)
    focused_id = _clean(focused_intake_id)
    guided_id = _clean(guided_intake_id)
    lane = _clean(guided_lane_key)

    if not all((firm, focused_id, guided_id, lane)):
        raise IntakeBridgeError(
            "firm_id, focused_intake_id, guided_intake_id, "
            "and guided_lane_key are required."
        )

    bridge = get_intake_bridge(
        db_path,
        firm,
        focused_id,
    )

    if bridge is None:
        raise IntakeBridgeError(
            "Canonical Person bridge must exist before "
            "Guided intake attachment."
        )

    current_guided = _clean(
        bridge.get("guided_intake_id")
    )
    current_lane = _clean(
        bridge.get("guided_lane_key")
    )

    if current_guided:
        if current_guided != guided_id:
            raise IntakeBridgeError(
                "A different Guided intake is already linked."
            )

        if current_lane != lane:
            raise IntakeBridgeError(
                "A different Guided lane is already linked."
            )

        return bridge

    con = _connect(db_path)

    try:
        _require_bridge_table(con)

        guided = con.execute(
            """
            SELECT intake_id, firm_id, intake_lane
            FROM intake_sessions
            WHERE intake_id = ?
              AND firm_id = ?
            """,
            (guided_id, firm),
        ).fetchone()

        if guided is None:
            raise IntakeBridgeError(
                "Guided intake was not found inside "
                "the requested firm scope."
            )

        if _clean(guided["intake_lane"]) != lane:
            raise IntakeBridgeError(
                "Guided lane does not match the Guided intake."
            )

        now = _now()

        try:
            cur = con.execute(
                f"""
                UPDATE {BRIDGE_TABLE}
                SET guided_intake_id = ?,
                    guided_lane_key = ?,
                    bridge_status = ?,
                    updated_at = ?
                WHERE firm_id = ?
                  AND focused_intake_id = ?
                  AND guided_intake_id IS NULL
                """,
                (
                    guided_id,
                    lane,
                    "guided_linked",
                    now,
                    firm,
                    focused_id,
                ),
            )

            if cur.rowcount != 1:
                con.rollback()
                raise IntakeBridgeError(
                    "Guided intake attachment did not modify "
                    "exactly one bridge."
                )

            con.commit()

        except sqlite3.IntegrityError as exc:
            con.rollback()
            raise IntakeBridgeError(
                "Guided intake is already linked elsewhere "
                "inside this firm scope."
            ) from exc

    finally:
        con.close()

    result = get_intake_bridge(
        db_path,
        firm,
        focused_id,
    )

    if result is None:
        raise IntakeBridgeError(
            "Updated intake bridge could not be reloaded."
        )

    return result


def create_or_reuse_guided_intake(
    db_path: str | Path,
    *,
    firm_id: str,
    focused_intake_id: str,
    guided_lane_key: str,
    created_by: str,
    guided_session_factory: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    """Create one Guided session through an injected factory, or reuse it.

    The factory is deliberately external because the existing Guided intake
    service uses application-global database state.

    ``client_id`` is explicitly passed as ``None``.  Person identity is carried
    by this bridge and is never smuggled into legacy ``client_id`` semantics.
    """

    firm = _clean(firm_id)
    focused_id = _clean(focused_intake_id)
    lane = _clean(guided_lane_key)
    actor = _clean(created_by)

    if not callable(guided_session_factory):
        raise IntakeBridgeError(
            "guided_session_factory must be callable."
        )

    bridge = get_intake_bridge(
        db_path,
        firm,
        focused_id,
    )

    if bridge is None:
        raise IntakeBridgeError(
            "Canonical Person bridge must exist before "
            "Guided intake creation."
        )

    existing_guided = _clean(
        bridge.get("guided_intake_id")
    )
    existing_lane = _clean(
        bridge.get("guided_lane_key")
    )

    if existing_guided:
        if existing_lane != lane:
            raise IntakeBridgeError(
                "A different Guided lane is already linked."
            )

        return bridge

    created = guided_session_factory(
        lane_key=lane,
        client_id=None,
        created_by=actor,
    )

    guided_id = _clean(
        (created or {}).get("intake_id")
    )
    created_lane = _clean(
        (created or {}).get("intake_lane")
    )

    if not guided_id:
        raise IntakeBridgeError(
            "Guided-session factory did not return an intake_id."
        )

    if created_lane and created_lane != lane:
        raise IntakeBridgeError(
            "Guided-session factory returned a different lane."
        )

    return attach_guided_intake(
        db_path,
        firm_id=firm,
        focused_intake_id=focused_id,
        guided_intake_id=guided_id,
        guided_lane_key=lane,
    )


def build_identity_carry_forward(
    focused_identity: dict[str, Any],
    guided_question_keys: set[str] | list[str] | tuple[str, ...],
) -> dict[str, Any]:
    """Build a conservative identity-only carry-forward descriptor.

    Mapping occurs only when the Guided question key is explicitly recognized
    as semantically equivalent.  Planning goals, fiduciary candidates, notes,
    and other non-equivalent fields are intentionally excluded.
    """

    focused = dict(focused_identity or {})
    allowed = {
        _clean(key)
        for key in guided_question_keys
        if _clean(key)
    }

    # Deliberately conservative.  These are exact semantic equivalents only.
    candidates = {
        "primary_full_name": (
            "primary_full_name",
        ),
        "preferred_name": (
            "preferred_name",
        ),
        "marital_status": (
            "marital_status",
        ),
        "state_jurisdiction": (
            "state_jurisdiction",
        ),
        "has_spouse": (
            "has_spouse",
        ),
        "has_children": (
            "has_children",
        ),
    }

    answers: dict[str, Any] = {}
    provenance: dict[str, Any] = {}

    source_intake_id = _clean(
        focused.get("intake_id")
    )

    for source_field, possible_targets in candidates.items():
        value = focused.get(source_field)

        if value is None or _clean(value) == "":
            continue

        target = next(
            (
                key
                for key in possible_targets
                if key in allowed
            ),
            None,
        )

        if target is None:
            continue

        answers[target] = value
        provenance[target] = {
            "source_model": "identity_intake",
            "source_intake_id": source_intake_id,
            "source_field": source_field,
            "carry_forward_mode": "exact_semantic_equivalence",
        }

    return {
        "answers": answers,
        "provenance": provenance,
        "excluded_source_fields": [
            "trustee_candidate",
            "successor_trustee_candidate",
            "primary_goal",
            "secondary_goal",
            "notes",
        ],
    }
