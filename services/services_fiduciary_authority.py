"""Canonical read/decision boundary for recorded Fiduciary authority evidence."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from datetime import datetime, timezone

import database.db as fiduciary_db


AuthorizationCheck = Callable[[str, str | None], bool]
ACTIVE_RECORDED_STATUSES = {
    "Active",
    "Current",
    "Appointed",
    "Authorized",
    "Accepted",
    "Verified",
}
PROMOTION_APPROVAL_CAPABILITY = "APPROVE_GOVERNED_PROGRAM_PROMOTION"


class FiduciaryAuthorityContractError(RuntimeError):
    """Raised when a scoped, authorized read cannot be performed safely."""


def _text(value: Any) -> str:
    return str(value or "").strip()


def _require_authorization(check: AuthorizationCheck | None) -> AuthorizationCheck:
    if check is None:
        raise FiduciaryAuthorityContractError(
            "An explicit Fiduciary authorization check is required."
        )
    return check


def _require_scoped_schema() -> None:
    connection = fiduciary_db.get_connection()
    try:
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='fiduciaries'"
        ).fetchone()
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(fiduciaries)").fetchall()
        }
    finally:
        connection.close()
    required = {"fiduciary_id", "firm_id", "trust_id"}
    if table is None or not required.issubset(columns):
        raise FiduciaryAuthorityContractError(
            "The Fiduciary boundary requires an existing firm-scoped fiduciary schema."
        )


def _record(row) -> dict[str, Any]:
    data = dict(row)
    return {
        "fiduciary_id": data.get("fiduciary_id"),
        "full_name": data.get("full_name"),
        "role_title": data.get("role_title"),
        "authority_scope": data.get("authority_scope"),
        "trust_id": data.get("trust_id"),
        "appointment_date": data.get("appointment_date"),
        "effective_date": data.get("effective_date"),
        "status": data.get("status"),
        "notes": data.get("notes"),
        "firm_id": data.get("firm_id"),
        "appointment_basis": None,
        "acceptance_status": None,
        "provenance": {
            "source": "fiduciaries",
            "audit_reference": "NOT DOCUMENTED",
        },
    }


def get_fiduciary_by_id(
    fiduciary_id: Any, *, authorization_check: AuthorizationCheck | None
) -> dict[str, Any] | None:
    """Return one authorized active-firm record, or a safe not-visible result."""
    record_id = _text(fiduciary_id)
    if not record_id:
        return None
    check = _require_authorization(authorization_check)
    _require_scoped_schema()
    firm_id = fiduciary_db.get_current_firm_id()
    connection = fiduciary_db.get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM fiduciaries WHERE fiduciary_id=? AND firm_id=?",
            (record_id, firm_id),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return None
    record = _record(row)
    if not check(record_id, _text(record.get("trust_id")) or None):
        return None
    return record


def list_fiduciaries(
    *, authorization_check: AuthorizationCheck | None
) -> list[dict[str, Any]]:
    """List authorized records for the active firm."""
    check = _require_authorization(authorization_check)
    _require_scoped_schema()
    connection = fiduciary_db.get_connection()
    try:
        rows = connection.execute(
            "SELECT * FROM fiduciaries WHERE firm_id=? ORDER BY full_name",
            (fiduciary_db.get_current_firm_id(),),
        ).fetchall()
    finally:
        connection.close()
    records = [_record(row) for row in rows]
    return [
        record
        for record in records
        if check(
            _text(record.get("fiduciary_id")),
            _text(record.get("trust_id")) or None,
        )
    ]


def list_fiduciaries_for_trust(
    trust_id: Any, *, authorization_check: AuthorizationCheck | None
) -> list[dict[str, Any]]:
    """List authorized active-firm Fiduciary records for exactly one Trust."""
    scoped_trust_id = _text(trust_id)
    if not scoped_trust_id:
        return []
    check = _require_authorization(authorization_check)
    _require_scoped_schema()
    connection = fiduciary_db.get_connection()
    try:
        rows = connection.execute(
            """SELECT * FROM fiduciaries
               WHERE trust_id=? AND firm_id=? ORDER BY full_name""",
            (scoped_trust_id, fiduciary_db.get_current_firm_id()),
        ).fetchall()
    finally:
        connection.close()
    records = [_record(row) for row in rows]
    return [
        record
        for record in records
        if check(_text(record.get("fiduciary_id")), scoped_trust_id)
    ]


def evaluate_authority_evidence(
    fiduciary_id: Any,
    *,
    trust_id: Any = None,
    capability: Any = None,
    authorization_check: AuthorizationCheck | None,
) -> dict[str, Any]:
    """Describe recorded evidence without producing a legal or permission verdict."""
    requested_trust = _text(trust_id) or None
    requested_capability = _text(capability) or None
    record = get_fiduciary_by_id(
        fiduciary_id, authorization_check=authorization_check
    )
    if record is None or (
        requested_trust and _text(record.get("trust_id")) != requested_trust
    ):
        return {
            "record_state": "missing_or_not_visible",
            "authority_evidence_state": "missing",
            "scope_state": "unresolved",
            "capability_state": "unresolved" if requested_capability else "not_requested",
            "acceptance_state": "not_documented",
            "system_permission_granted": False,
            "fiduciary": None,
        }

    authority_scope = _text(record.get("authority_scope"))
    status = _text(record.get("status"))
    active = status in ACTIVE_RECORDED_STATUSES
    evidence_state = "recorded" if active and authority_scope else "unresolved"
    return {
        "record_state": "recorded",
        "authority_evidence_state": evidence_state,
        "scope_state": "recorded" if authority_scope else "unresolved",
        "capability_state": "unresolved" if requested_capability else "not_requested",
        "acceptance_state": "not_documented",
        "system_permission_granted": False,
        "requested_capability": requested_capability,
        "recorded_status": status or None,
        "recorded_role_title": record.get("role_title"),
        "recorded_authority_scope": record.get("authority_scope"),
        "fiduciary": record,
    }


def resolve_promotion_approval_capability(
    principal_username: Any,
    *,
    firm_id: Any,
    trust_id: Any,
    at_time: datetime | None = None,
) -> dict[str, Any] | None:
    """Resolve active, immutable P07 approval evidence for one principal.

    This is evidence resolution only. It neither grants authority nor writes
    promotion state. The caller must independently enforce application role,
    object scope, requester separation, and lifecycle state.
    """
    principal = _text(principal_username)
    firm = _text(firm_id)
    trust = _text(trust_id)
    if not all((principal, firm, trust)):
        return None

    now = (at_time or datetime.now(timezone.utc)).isoformat()
    connection = fiduciary_db.get_connection()
    try:
        required = {
            "fiduciary_authority_capabilities",
            "fiduciary_authority_capability_events",
        }
        present = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if not required.issubset(present):
            raise FiduciaryAuthorityContractError(
                "The structured P07 capability schema is required."
            )
        row = connection.execute(
            """
            SELECT capability.*
            FROM fiduciary_authority_capabilities AS capability
            WHERE capability.firm_id = ?
              AND capability.trust_id = ?
              AND lower(capability.principal_username) = lower(?)
              AND capability.capability = ?
              AND capability.effective_at <= ?
              AND (capability.expires_at IS NULL OR capability.expires_at > ?)
              AND EXISTS (
                  SELECT 1
                  FROM fiduciary_authority_capability_events AS granted
                  WHERE granted.authority_grant_id = capability.authority_grant_id
                    AND granted.event_type = 'GRANTED'
              )
              AND NOT EXISTS (
                  SELECT 1
                  FROM fiduciary_authority_capability_events AS revoked
                  WHERE revoked.authority_grant_id = capability.authority_grant_id
                    AND revoked.event_type = 'REVOKED'
                    AND revoked.event_at <= ?
              )
            ORDER BY capability.effective_at DESC, capability.authority_grant_id
            LIMIT 1
            """,
            (firm, trust, principal, PROMOTION_APPROVAL_CAPABILITY, now, now, now),
        ).fetchone()
    finally:
        connection.close()
    return dict(row) if row else None
