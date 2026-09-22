"""Canonical read-only Execution and transfer orchestration boundary.

This facade interprets recorded state but never creates or advances governed
execution, transfer, archive, or recovery records.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from datetime import datetime, timezone
import uuid

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
ASSET_OBJECT_TYPES = ("PROPERTY", "ACCOUNT")
FUNDING_STATES = ("UNRESOLVED", "PROPOSED", "IN_PROCESS", "FUNDED_RECORDED", "NOT_FUNDED_RECORDED")
OWNERSHIP_STATES = ("UNRESOLVED", "TRUST_TITLE_RECORDED", "BENEFICIAL_INTEREST_RECORDED", "THIRD_PARTY_TITLE_RECORDED")
CONTROL_STATES = ("UNRESOLVED", "TRUSTEE_CONTROL_RECORDED", "SHARED_CONTROL_RECORDED", "THIRD_PARTY_CONTROL_RECORDED")
DECISION_ORIGINS = ("SYSTEM_SUGGESTED", "OPERATOR_OR_FIDUCIARY", "PROFESSIONAL")


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


def record_trust_asset_control_determination(
    *, firm_id, trust_id, asset_object_type, asset_object_id,
    funding_state="UNRESOLVED", ownership_state="UNRESOLVED", control_state="UNRESOLVED",
    related_transfer_id=None, evidence_reference=None, basis=None, provenance=None,
    decision_origin, human_confirmed, actor, actor_capacity, prior_asset_control_id=None,
):
    """Append a documented determination without asserting automatic legal title."""
    firm_id, trust_id = _text(firm_id), _text(trust_id)
    object_type, object_id = _text(asset_object_type).upper(), _text(asset_object_id)
    if object_type not in ASSET_OBJECT_TYPES: raise ExecutionContractError("Unsupported asset object type.")
    if funding_state not in FUNDING_STATES: raise ExecutionContractError("Unsupported funding state.")
    if ownership_state not in OWNERSHIP_STATES: raise ExecutionContractError("Unsupported ownership state.")
    if control_state not in CONTROL_STATES: raise ExecutionContractError("Unsupported control state.")
    if decision_origin not in DECISION_ORIGINS: raise ExecutionContractError("Unsupported decision origin.")
    if not all((firm_id, trust_id, object_id, _text(actor), _text(actor_capacity))):
        raise ExecutionContractError("Asset-control scope and actor are required.")
    substantive = funding_state in {"FUNDED_RECORDED", "NOT_FUNDED_RECORDED"} or ownership_state != "UNRESOLVED" or control_state != "UNRESOLVED"
    if decision_origin == "SYSTEM_SUGGESTED" and (funding_state not in {"UNRESOLVED", "PROPOSED"} or ownership_state != "UNRESOLVED" or control_state != "UNRESOLVED"):
        raise ExecutionContractError("A machine suggestion cannot finalize asset control.")
    if substantive:
        if decision_origin not in {"OPERATOR_OR_FIDUCIARY", "PROFESSIONAL"} or not human_confirmed:
            raise ExecutionContractError("Substantive asset-control state requires human confirmation.")
        if not all(map(_text, (evidence_reference, basis, provenance))):
            raise ExecutionContractError("Substantive asset-control state requires evidence, basis, and provenance.")
    connection = execution_db.get_connection()
    try:
        table, key = ("properties", "property_id") if object_type == "PROPERTY" else ("accounts", "account_id")
        columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
        asset = connection.execute(f"SELECT * FROM {table} WHERE {key}=?", (object_id,)).fetchone()
        if asset is None or _text(asset["trust_id"]) != trust_id:
            raise ExecutionContractError("Canonical asset is unavailable in context.")
        if "firm_id" in columns:
            scoped = _text(asset["firm_id"]) == firm_id
        else:
            trust = connection.execute("SELECT firm_id FROM trusts WHERE trust_id=?", (trust_id,)).fetchone()
            scoped = trust is not None and _text(trust["firm_id"]) == firm_id
        if not scoped: raise ExecutionContractError("Canonical asset firm scope cannot be established.")
        transfer_id = _text(related_transfer_id) or None
        if transfer_id and connection.execute(
            "SELECT 1 FROM transfers WHERE transfer_id=? AND firm_id=? AND trust_id=?",
            (transfer_id, firm_id, trust_id),
        ).fetchone() is None:
            raise ExecutionContractError("Related transfer is unavailable in context.")
        latest_row = connection.execute(
            """SELECT * FROM trust_asset_control_determinations
               WHERE firm_id=? AND trust_id=? AND asset_object_type=? AND asset_object_id=?
               ORDER BY created_at DESC, asset_control_id DESC LIMIT 1""",
            (firm_id, trust_id, object_type, object_id),
        ).fetchone()
        latest = dict(latest_row) if latest_row else None
        prior_id = _text(prior_asset_control_id) or None
        if latest and prior_id != latest["asset_control_id"]: raise ExecutionContractError("Latest asset-control predecessor is required.")
        if not latest and prior_id: raise ExecutionContractError("Asset-control predecessor is unavailable in context.")
        record_id = "TAC-" + uuid.uuid4().hex[:10].upper()
        connection.execute(
            """INSERT INTO trust_asset_control_determinations
            (asset_control_id,firm_id,trust_id,asset_object_type,asset_object_id,related_transfer_id,
             funding_state,ownership_state,control_state,evidence_reference,basis,provenance,
             decision_origin,human_confirmed,actor,actor_capacity,prior_asset_control_id,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (record_id,firm_id,trust_id,object_type,object_id,transfer_id,funding_state,ownership_state,
             control_state,_text(evidence_reference) or None,_text(basis) or None,_text(provenance) or None,
             decision_origin,int(bool(human_confirmed)),_text(actor),_text(actor_capacity),prior_id,
             datetime.now(timezone.utc).isoformat()),
        )
        connection.commit(); return record_id
    finally:
        connection.close()


def get_trust_asset_control_determination(asset_control_id):
    connection = execution_db.get_connection()
    try:
        row = connection.execute("SELECT * FROM trust_asset_control_determinations WHERE asset_control_id=?", (_text(asset_control_id),)).fetchone()
        return dict(row) if row else None
    finally: connection.close()


def get_trust_asset_control_history(*, firm_id, trust_id, asset_object_type, asset_object_id):
    connection = execution_db.get_connection()
    try:
        rows = connection.execute("""SELECT * FROM trust_asset_control_determinations
            WHERE firm_id=? AND trust_id=? AND asset_object_type=? AND asset_object_id=?
            ORDER BY created_at,asset_control_id""",
            (_text(firm_id),_text(trust_id),_text(asset_object_type).upper(),_text(asset_object_id))).fetchall()
        return [dict(row) for row in rows]
    finally: connection.close()
