from __future__ import annotations

from datetime import datetime
from typing import Any

from models.models_transfer import Transfer, TransferAction, TransferRecord, db
from database.db import get_media_by_entity


STEP_ORDER = [
    "asset",
    "classification",
    "assignment",
    "trustee_acceptance",
    "control_evidence",
    "records",
    "review",
]


def generate_transfer_id() -> str:
    count = db.session.query(Transfer).count() + 1
    return f"T-{count:04d}"


def add_transfer_action(
    transfer: Transfer,
    action_type: str,
    performed_by: str | None = None,
    capacity_used: str | None = None,
    notes: str | None = None,
    commit: bool = False,
) -> TransferAction:
    action = TransferAction(
        transfer_id_fk=transfer.id,
        action_type=action_type,
        performed_by=performed_by,
        capacity_used=capacity_used,
        notes=notes,
    )
    db.session.add(action)
    if commit:
        db.session.commit()
    return action


def get_transfer_progress(transfer: Transfer) -> dict[str, Any]:
    completed_steps: list[str] = []

    if transfer.asset_name:
        completed_steps.append("asset")
    if transfer.transfer_type:
        completed_steps.append("classification")
    if transfer.assignment_confirmed:
        completed_steps.append("assignment")
    if transfer.trustee_decision:
        completed_steps.append("trustee_acceptance")
    if transfer.control_change_status:
        completed_steps.append("control_evidence")
    if transfer.records_complete:
        completed_steps.append("records")

    percent = int((len(completed_steps) / max(len(STEP_ORDER) - 1, 1)) * 100)

    return {
        "completed_steps": completed_steps,
        "pending_steps": [s for s in STEP_ORDER if s not in completed_steps],
        "percent_complete": min(percent, 100),
    }


def validate_capacity_for_step(step_name: str, capacity: str) -> bool:
    rules = {
        "assignment": {"individual"},
        "trustee_acceptance": {"trustee"},
        "asset": {"individual", "fiduciary", "trustee"},
        "classification": {"individual", "fiduciary", "trustee"},
        "control_evidence": {"individual", "fiduciary", "trustee"},
        "records": {"fiduciary", "trustee"},
        "review": {"individual", "fiduciary", "trustee"},
    }
    allowed = rules.get(step_name, {"individual", "fiduciary", "trustee"})
    return capacity in allowed


def build_assignment_text(transfer: Transfer) -> str:
    return (
        "Assignment of Property\n\n"
        f"Transfer ID: {transfer.transfer_id}\n"
        f"Trust ID: {transfer.trust_id}\n"
        f"Asset: {transfer.asset_name or ''}\n"
        f"Description: {transfer.asset_description or ''}\n"
        f"Estimated Value: {transfer.estimated_value or ''}\n"
        f"Current Owner: {transfer.current_owner or ''}\n"
        f"Transfer Type: {transfer.transfer_type or ''}\n"
        f"Consideration: {transfer.consideration_text or ''}\n"
    )


def build_schedule_a_text(transfer: Transfer) -> str:
    return (
        "Schedule A Entry\n"
        f"Asset: {transfer.asset_name or ''}\n"
        f"Description: {transfer.asset_description or ''}\n"
        f"Estimated Value: {transfer.estimated_value or ''}\n"
        f"Date Added: {datetime.utcnow().strftime('%Y-%m-%d')}\n"
        f"Transfer ID: {transfer.transfer_id}\n"
    )


def build_transfer_log_text(transfer: Transfer, recorded_by: str | None = None) -> str:
    return (
        "Transfer Log\n"
        f"Transfer ID: {transfer.transfer_id}\n"
        f"Trust ID: {transfer.trust_id}\n"
        f"Asset: {transfer.asset_name or ''}\n"
        f"Transfer Type: {transfer.transfer_type or ''}\n"
        f"Mode: {transfer.mode}\n"
        f"Recorded By: {recorded_by or transfer.created_by or ''}\n"
        f"Recorded On: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )


def build_minutes_text(
    transfer: Transfer,
    trustee_name: str = "",
    meeting_date: str = "",
    notes: str = "",
) -> str:
    return (
        "Minutes\n"
        f"Meeting Date: {meeting_date or datetime.utcnow().strftime('%Y-%m-%d')}\n"
        f"Trustee: {trustee_name or transfer.trustee_name or ''}\n"
        f"Business Discussed: Transfer packet review for {transfer.asset_name or ''}\n"
        f"Action Taken: {transfer.trustee_decision or 'Pending'}\n"
        f"Notes: {notes}\n"
    )


def calculate_control_strength(control_change_status: str | None) -> str:
    if not control_change_status:
        return "none"

    weak = {"intent_only"}
    moderate = {"physical_separation", "trustee_possession"}
    strong = {"account_retitled", "signer_changed", "ownership_docs_updated"}

    if control_change_status in weak:
        return "weak"
    if control_change_status in moderate:
        return "moderate"
    if control_change_status in strong:
        return "strong"
    return "unknown"


def get_or_create_transfer_record(transfer: Transfer) -> TransferRecord:
    if transfer.record_bundle:
        return transfer.record_bundle

    record = TransferRecord(transfer_id_fk=transfer.id)
    db.session.add(record)
    db.session.flush()
    return record


def populate_transfer_record_bundle(
    transfer: Transfer,
    trustee_name: str = "",
    meeting_date: str = "",
    notes: str = "",
    recorded_by: str | None = None,
) -> TransferRecord:
    record = get_or_create_transfer_record(transfer)
    record.schedule_a_text = build_schedule_a_text(transfer)
    record.transfer_log_text = build_transfer_log_text(
        transfer,
        recorded_by=recorded_by,
    )
    record.minutes_text = build_minutes_text(
        transfer,
        trustee_name=trustee_name,
        meeting_date=meeting_date,
        notes=notes,
    )

    transfer.records_complete = True
    return record


def can_finalize_transfer(transfer: Transfer) -> tuple[bool, list[str]]:
    missing: list[str] = []

    if not transfer.asset_name:
        missing.append("asset")
    if not transfer.transfer_type:
        missing.append("classification")
    if not transfer.assignment_confirmed:
        missing.append("assignment")
    if not transfer.trustee_decision:
        missing.append("trustee_acceptance")
    if not transfer.control_change_status:
        missing.append("control_evidence")
    if not transfer.records_complete:
        missing.append("records")

    # === II-A SOFT HYBRID ENFORCEMENT ===
    # Require at least one external execution proof before finalization.
    # Full ledger enforcement comes after ledger timing is redesigned.
    proof_count = 0
    try:
        proof_count = len(get_media_by_entity("transfer", transfer.transfer_id))
    except Exception:
        proof_count = 0

    external_ok = bool(getattr(transfer, "external_verified", False))
    proof_ok = proof_count > 0

    if not (external_ok or proof_ok):
        missing.append("external_verification_or_proof")

    return (len(missing) == 0, missing)


def finalize_transfer(
    transfer: Transfer,
    performed_by: str | None = None,
    capacity_used: str | None = None,
    commit: bool = False,
) -> tuple[bool, list[str]]:
    allowed, missing = can_finalize_transfer(transfer)
    if not allowed:
        return False, missing

    transfer.status = "completed"
    transfer.finalized_at = datetime.utcnow()
    transfer.finalized_by = performed_by
    transfer.finalized_capacity = capacity_used

    add_transfer_action(
        transfer=transfer,
        action_type="finalized_transfer",
        performed_by=performed_by,
        capacity_used=capacity_used,
        notes="Transfer packet finalized.",
        commit=False,
    )

    if commit:
        db.session.commit()

    return True, []
