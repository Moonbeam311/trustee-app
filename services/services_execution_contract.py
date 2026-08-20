"""Canonical read-only Execution and transfer orchestration boundary.

This facade interprets recorded state but never creates or advances governed
execution, transfer, archive, or recovery records.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import database.db as execution_db
import services.services_trust_contract as trust_contract


AuthorizationCheck = Callable[[str], bool]


class ExecutionContractError(RuntimeError):
    """Raised when the boundary cannot prove a safe read contract."""


SESSION_TABLES = {
    "institutional_execution_sessions",
    "institutional_signature_records",
    "institutional_witness_notary_records",
    "institutional_seal_ledger",
    "institutional_execution_ledger",
    "institutional_archive_freezes",
}
TRANSFER_REQUIREMENTS = (
    ("asset", "asset_name"),
    ("classification", "transfer_type"),
    ("assignment", "assignment_confirmed"),
    ("trustee_acceptance", "trustee_decision"),
    ("control_evidence", "control_change_status"),
    ("records", "records_complete"),
    ("external_verification", "external_verified"),
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _require_tables(required: set[str]) -> None:
    """Check existing schema without invoking legacy schema-creation helpers."""
    connection = execution_db.get_connection()
    try:
        present = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        connection.close()
    missing = sorted(required - present)
    if missing:
        raise ExecutionContractError(
            "Required read schema is unavailable: " + ", ".join(missing)
        )


def _accessible_trust(trust_id: Any, authorization_check: AuthorizationCheck | None):
    normalized = _text(trust_id)
    if not normalized:
        return None
    return trust_contract.get_trust_by_id(
        normalized, authorization_check=authorization_check
    )


def get_execution_session(
    execution_id: Any, *, authorization_check: AuthorizationCheck | None
) -> dict[str, Any] | None:
    """Return a firm-authorized execution session and its recorded evidence."""
    record_id = _text(execution_id)
    if not record_id:
        return None
    _require_tables(SESSION_TABLES)
    connection = execution_db.get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM institutional_execution_sessions WHERE execution_id=?",
            (record_id,),
        ).fetchone()
        if row is None or _accessible_trust(
            row["trust_id"], authorization_check
        ) is None:
            return None
        related = {}
        for key, table, order in (
            ("signatures", "institutional_signature_records", "signature_id"),
            ("participants", "institutional_witness_notary_records", "record_id"),
            ("seals", "institutional_seal_ledger", "seal_event_id"),
            ("ledger", "institutional_execution_ledger", "event_sequence, ledger_id"),
            ("archive_freezes", "institutional_archive_freezes", "freeze_id"),
        ):
            related[key] = [
                dict(item)
                for item in connection.execute(
                    f"SELECT * FROM {table} WHERE execution_id=? ORDER BY {order}",
                    (record_id,),
                ).fetchall()
            ]
    finally:
        connection.close()
    return {
        "contract_version": "V3-SVC-EXEC-1",
        "session": dict(row),
        **related,
        "scope": {"firm_scope": "inherited_from_canonical_trust", "trust_id": row["trust_id"]},
        "mutation_performed": False,
    }


def summarize_execution_readiness(
    execution_id: Any, *, authorization_check: AuthorizationCheck | None
) -> dict[str, Any] | None:
    """Interpret recorded session evidence without claiming lifecycle completion."""
    context = get_execution_session(
        execution_id, authorization_check=authorization_check
    )
    if context is None:
        return None
    session = context["session"]
    pending_signatures = [
        row["signature_id"]
        for row in context["signatures"]
        if _text(row.get("signature_status")).lower() not in {"signed", "complete", "completed"}
    ]
    blockers = [
        {"code": "pending_signature", "record_id": signature_id}
        for signature_id in pending_signatures
    ]
    next_action = (
        "review_pending_signatures"
        if blockers
        else "review_current_execution_state"
    )
    if _text(session.get("archive_freeze_status")).lower() == "frozen":
        next_action = "review_archived_execution"
    return {
        "execution_id": session["execution_id"],
        "trust_id": session["trust_id"],
        "current_state": session.get("ceremony_status"),
        "current_step": session.get("current_step"),
        "readiness_status": "attention_required" if blockers else "recorded_state_only",
        "blockers": blockers,
        "recommended_next_action": next_action,
        "archive_handoff_status": session.get("archive_freeze_status"),
        "completion_or_certification_claimed": False,
        "mutation_performed": False,
    }


def get_transfer(
    transfer_id: Any,
    trust_id: Any,
    *,
    authorization_check: AuthorizationCheck | None,
) -> dict[str, Any] | None:
    """Return one transfer only in exact active-firm and Trust scope."""
    transfer_key, trust_key = _text(transfer_id), _text(trust_id)
    if not transfer_key or _accessible_trust(trust_key, authorization_check) is None:
        return None
    _require_tables({"transfers"})
    connection = execution_db.get_connection()
    try:
        row = connection.execute(
            """SELECT * FROM transfers
               WHERE transfer_id=? AND trust_id=? AND firm_id=?""",
            (transfer_key, trust_key, execution_db.get_current_firm_id()),
        ).fetchone()
    finally:
        connection.close()
    return dict(row) if row is not None else None


def summarize_transfer_readiness(
    transfer_id: Any,
    trust_id: Any,
    *,
    authorization_check: AuthorizationCheck | None,
) -> dict[str, Any] | None:
    """Represent existing transfer requirements without invoking finalization."""
    transfer = get_transfer(
        transfer_id, trust_id, authorization_check=authorization_check
    )
    if transfer is None:
        return None
    completed, blockers = [], []
    for requirement, field in TRANSFER_REQUIREMENTS:
        value = transfer.get(field)
        satisfied = bool(value)
        if satisfied:
            completed.append(requirement)
        else:
            blockers.append({"code": f"missing_{requirement}", "source_field": field})
    return {
        "transfer_id": transfer["transfer_id"],
        "trust_id": transfer["trust_id"],
        "current_state": transfer.get("status"),
        "readiness_status": "ready_for_existing_finalization_review" if not blockers else "blocked",
        "completed_requirements": completed,
        "pending_requirements": blockers,
        "recommended_next_action": "review_existing_finalization" if not blockers else f"resolve_{blockers[0]['code'][8:]}",
        "mutation_performed": False,
    }


def build_orchestration_context(
    trust_id: Any,
    *,
    authorization_check: AuthorizationCheck | None,
    execution_id: Any = None,
    transfer_id: Any = None,
) -> dict[str, Any] | None:
    """Combine independent read results; never execute the recommendation."""
    trust_key = _text(trust_id)
    if _accessible_trust(trust_key, authorization_check) is None:
        return None
    execution = (
        summarize_execution_readiness(execution_id, authorization_check=authorization_check)
        if _text(execution_id)
        else None
    )
    transfer = (
        summarize_transfer_readiness(
            transfer_id, trust_key, authorization_check=authorization_check
        )
        if _text(transfer_id)
        else None
    )
    if execution is not None and execution["trust_id"] != trust_key:
        return None
    return {
        "contract_version": "V3-SVC-EXEC-1",
        "trust_id": trust_key,
        "execution": execution,
        "transfer": transfer,
        "recommended_next_action": (
            transfer["recommended_next_action"] if transfer and transfer["pending_requirements"]
            else execution["recommended_next_action"] if execution
            else transfer["recommended_next_action"] if transfer
            else "NOT DOCUMENTED"
        ),
        "recommendation_executed": False,
        "mutation_performed": False,
    }
