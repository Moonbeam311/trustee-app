"""Canonical read-only boundary for structured successor-acceptance facts."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Callable
from typing import Any

import database.db as acceptance_db


AuthorizationCheck = Callable[[str, str], bool]
ACCEPTANCE_STATES = {
    "PENDING_EVIDENCE",
    "ACCEPTED_RECORDED",
    "DECLINED_RECORDED",
    "WITHDRAWN_RECORDED",
    "SUPERSEDED",
}
LEGACY_DOCUMENT_CLASSIFICATION = (
    "LEGACY DOCUMENT / ACCEPTANCE STATE NOT STRUCTURALLY VERIFIED"
)


class SuccessorAcceptanceReadContractError(RuntimeError):
    """Raised when the scoped read contract cannot operate safely."""


def _text(value: Any) -> str:
    return str(value or "").strip()


def _identity_text(value: Any) -> str:
    normalized = unicodedata.normalize("NFKC", _text(value))
    return " ".join(normalized.split()).casefold()


def _require_authorization(check: AuthorizationCheck | None) -> AuthorizationCheck:
    if check is None:
        raise SuccessorAcceptanceReadContractError(
            "An explicit successor-acceptance authorization check is required."
        )
    return check


def _require_schema() -> None:
    connection = acceptance_db.get_connection()
    try:
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='successor_acceptances'"
        ).fetchone()
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(successor_acceptances)"
            ).fetchall()
        }
    finally:
        connection.close()
    required = {
        "acceptance_id", "firm_id", "trust_id", "fiduciary_id",
        "appointment_reference", "role_capacity",
        "appointment_source_reference", "acceptance_status", "recorded_by",
        "recorded_at", "provenance_source", "context_fingerprint",
    }
    if table is None or not required.issubset(columns):
        raise SuccessorAcceptanceReadContractError(
            "The acceptance boundary requires the canonical firm-scoped schema."
        )


def derive_acceptance_context_fingerprint(
    *,
    firm_id: Any,
    trust_id: Any,
    fiduciary_id: Any,
    appointment_reference: Any,
    role_capacity: Any,
    appointment_source_reference: Any,
) -> str:
    """Derive the canonical institutional duplicate-prevention identity."""
    context = {
        "appointment_reference": _identity_text(appointment_reference),
        "appointment_source_reference": _identity_text(
            appointment_source_reference
        ),
        "fiduciary_id": _identity_text(fiduciary_id),
        "firm_id": _identity_text(firm_id),
        "role_capacity": _identity_text(role_capacity),
        "trust_id": _identity_text(trust_id),
    }
    if not all(context.values()):
        raise SuccessorAcceptanceReadContractError(
            "Every canonical acceptance-context component is required."
        )
    encoded = json.dumps(
        context, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _record(row: Any) -> dict[str, Any]:
    data = dict(row)
    return {
        "acceptance_id": data["acceptance_id"],
        "firm_id": data["firm_id"],
        "trust_id": data["trust_id"],
        "fiduciary_id": data["fiduciary_id"],
        "appointment_reference": data["appointment_reference"],
        "role_capacity": data["role_capacity"],
        "appointment_source_reference": data["appointment_source_reference"],
        "acceptance_status": data["acceptance_status"],
        "accepted_at": data.get("accepted_at"),
        "acceptance_method": data.get("acceptance_method"),
        "evidence": {
            "document_id": data.get("evidence_document_id"),
            "external_reference": data.get("external_evidence_reference"),
        },
        "provenance": {
            "source": data["provenance_source"],
            "recorded_by": data["recorded_by"],
            "recorded_at": data["recorded_at"],
            "supersedes_acceptance_id": data.get("supersedes_acceptance_id"),
            "governed_explanation": data.get("governed_explanation"),
        },
        "context_fingerprint": data["context_fingerprint"],
        "institutional_effects": {
            "legal_validity_established": False,
            "fiduciary_authority_changed": False,
            "continuity_activated": False,
            "responsibility_assigned": False,
            "application_access_granted": False,
            "execution_authority_granted": False,
            "handoff_acknowledged": False,
        },
    }


def get_successor_acceptance(
    acceptance_id: Any, *, authorization_check: AuthorizationCheck | None
) -> dict[str, Any] | None:
    """Return one authorized active-firm acceptance, or a safe absent result."""
    record_id = _text(acceptance_id)
    if not record_id:
        return None
    check = _require_authorization(authorization_check)
    _require_schema()
    connection = acceptance_db.get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM successor_acceptances WHERE acceptance_id=? AND firm_id=?",
            (record_id, acceptance_db.get_current_firm_id()),
        ).fetchone()
    finally:
        connection.close()
    if row is None or not check(record_id, _text(row["trust_id"])):
        return None
    return _record(row)


def get_successor_acceptance_for_context(
    *,
    trust_id: Any,
    fiduciary_id: Any,
    appointment_reference: Any,
    role_capacity: Any,
    appointment_source_reference: Any,
    authorization_check: AuthorizationCheck | None,
) -> dict[str, Any] | None:
    """Return the acceptance for one exact canonical context, if visible."""
    check = _require_authorization(authorization_check)
    firm_id = acceptance_db.get_current_firm_id()
    fingerprint = derive_acceptance_context_fingerprint(
        firm_id=firm_id,
        trust_id=trust_id,
        fiduciary_id=fiduciary_id,
        appointment_reference=appointment_reference,
        role_capacity=role_capacity,
        appointment_source_reference=appointment_source_reference,
    )
    _require_schema()
    connection = acceptance_db.get_connection()
    try:
        row = connection.execute(
            """SELECT * FROM successor_acceptances
               WHERE context_fingerprint=? AND firm_id=? AND trust_id=?""",
            (fingerprint, firm_id, _text(trust_id)),
        ).fetchone()
    finally:
        connection.close()
    if row is None or not check(_text(row["acceptance_id"]), _text(row["trust_id"])):
        return None
    return _record(row)


def list_successor_acceptances_for_trust(
    trust_id: Any, *, authorization_check: AuthorizationCheck | None
) -> list[dict[str, Any]]:
    """List visible acceptance facts for one Trust in the active firm."""
    scoped_trust = _text(trust_id)
    if not scoped_trust:
        return []
    check = _require_authorization(authorization_check)
    _require_schema()
    connection = acceptance_db.get_connection()
    try:
        rows = connection.execute(
            """SELECT * FROM successor_acceptances
               WHERE firm_id=? AND trust_id=?
               ORDER BY recorded_at, acceptance_id""",
            (acceptance_db.get_current_firm_id(), scoped_trust),
        ).fetchall()
    finally:
        connection.close()
    return [
        _record(row)
        for row in rows
        if check(_text(row["acceptance_id"]), scoped_trust)
    ]
