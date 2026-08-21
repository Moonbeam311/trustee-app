"""Governed maker/reviewer lifecycle service for successor acceptance."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any

import database.db as database_db
from services import services_fiduciary_authority as fiduciary_contract
from services import services_document_contract as document_contract
from services import services_successor_acceptance as acceptance_read
from services import services_trust_contract as trust_contract


MAKER_PERMISSION = "record_successor_acceptance"
REVIEWER_PERMISSION = "verify_successor_acceptance"
FINAL_STATES = {
    "ACCEPTED_RECORDED",
    "DECLINED_RECORDED",
    "WITHDRAWN_RECORDED",
    "SUPERSEDED",
}
ALLOWED_TRANSITIONS = {
    "PENDING_EVIDENCE": {"ACCEPTED_RECORDED", "DECLINED_RECORDED", "SUPERSEDED"},
    "ACCEPTED_RECORDED": {"WITHDRAWN_RECORDED", "SUPERSEDED"},
    "DECLINED_RECORDED": {"SUPERSEDED"},
    "WITHDRAWN_RECORDED": {"SUPERSEDED"},
    "SUPERSEDED": set(),
}


class SuccessorAcceptanceLifecycleError(RuntimeError):
    """Raised when a governed Acceptance write must fail closed."""


def _text(value: Any) -> str:
    return str(value or "").strip()


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds")


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex.upper()}"


def _require_actor_permission(actor_id: Any, permission_name: str) -> str:
    actor = _text(actor_id)
    if not actor:
        raise SuccessorAcceptanceLifecycleError("An explicit application actor is required.")
    connection = database_db.get_connection()
    try:
        user = connection.execute(
            """SELECT username, status, firm_id FROM app_users
               WHERE username=? AND firm_id=? LIMIT 1""",
            (actor, database_db.get_current_firm_id()),
        ).fetchone()
    finally:
        connection.close()
    if user is None or _text(user["status"]).casefold() not in {"active", "enabled"}:
        raise SuccessorAcceptanceLifecycleError("Actor is not available in the active firm.")
    if not database_db.user_has_effective_permission(actor, permission_name):
        raise SuccessorAcceptanceLifecycleError(
            f"Actor lacks required permission: {permission_name}."
        )
    return actor


def _validate_context(
    *,
    trust_id: Any,
    fiduciary_id: Any,
    role_capacity: Any,
    appointment_reference: Any,
    appointment_source_reference: Any,
    trust_authorization_check,
    fiduciary_authorization_check,
) -> tuple[str, str, str, str, str]:
    trust = _text(trust_id)
    fiduciary = _text(fiduciary_id)
    capacity = _text(role_capacity)
    appointment = _text(appointment_reference)
    source = _text(appointment_source_reference)
    if not all((trust, fiduciary, capacity, appointment, source)):
        raise SuccessorAcceptanceLifecycleError(
            "Trust, Fiduciary, appointment, capacity, and source context are required."
        )
    if trust_contract.get_trust_by_id(
        trust, authorization_check=trust_authorization_check
    ) is None:
        raise SuccessorAcceptanceLifecycleError("Trust context is missing or not accessible.")
    fiduciary_record = fiduciary_contract.get_fiduciary_by_id(
        fiduciary, authorization_check=fiduciary_authorization_check
    )
    if fiduciary_record is None or _text(fiduciary_record.get("trust_id")) != trust:
        raise SuccessorAcceptanceLifecycleError(
            "Fiduciary context is missing or not scoped to the Trust."
        )
    if _text(fiduciary_record.get("role_title")).casefold() != capacity.casefold():
        raise SuccessorAcceptanceLifecycleError(
            "Recorded Fiduciary capacity does not match the Acceptance context."
        )
    return trust, fiduciary, capacity, appointment, source


def _evidence_present(document_id: Any, external_reference: Any) -> bool:
    return bool(_text(document_id) or _text(external_reference))


def _validate_document_evidence(
    document_id: Any, trust_id: str, document_authorization_check
) -> None:
    reference = _text(document_id)
    if not reference:
        return
    if document_authorization_check is None or document_contract.get_document_reference(
        reference,
        trust_id,
        authorization_check=document_authorization_check,
    ) is None:
        raise SuccessorAcceptanceLifecycleError(
            "Document evidence is missing or not accessible in the Acceptance Trust."
        )


def _insert_event(
    connection: sqlite3.Connection,
    *,
    acceptance: sqlite3.Row,
    event_type: str,
    maker_actor_id: str,
    reviewer_actor_id: str | None = None,
    prior_state: str | None = None,
    resulting_state: str | None = None,
    evidence_document_id: Any = None,
    external_evidence_reference: Any = None,
    reason: Any = None,
    related_event_id: str | None = None,
) -> str:
    event_id = _new_id("ACCEVT")
    connection.execute(
        """INSERT INTO successor_acceptance_events (
            event_id, acceptance_id, firm_id, trust_id, fiduciary_id,
            event_type, maker_actor_id, reviewer_actor_id, prior_state,
            resulting_state, evidence_document_id, external_evidence_reference,
            reason, context_fingerprint, related_event_id, created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            event_id, acceptance["acceptance_id"], acceptance["firm_id"],
            acceptance["trust_id"], acceptance["fiduciary_id"], event_type,
            maker_actor_id, reviewer_actor_id, prior_state, resulting_state,
            _text(evidence_document_id) or None,
            _text(external_evidence_reference) or None, _text(reason) or None,
            acceptance["context_fingerprint"], related_event_id, _now(),
        ),
    )
    return event_id


def propose_successor_acceptance(
    *,
    trust_id: Any,
    fiduciary_id: Any,
    appointment_reference: Any,
    role_capacity: Any,
    appointment_source_reference: Any,
    proposed_status: str,
    maker_actor_id: Any,
    provenance_source: Any,
    trust_authorization_check,
    fiduciary_authorization_check,
    document_authorization_check=None,
    evidence_document_id: Any = None,
    external_evidence_reference: Any = None,
    acceptance_method: Any = None,
    reason: Any = None,
) -> dict[str, Any]:
    """Create an idempotent pending Acceptance proposal; never finalize it."""
    maker = _require_actor_permission(maker_actor_id, MAKER_PERMISSION)
    target = _text(proposed_status).upper()
    if target not in {"ACCEPTED_RECORDED", "DECLINED_RECORDED"}:
        raise SuccessorAcceptanceLifecycleError("Unsupported initial Acceptance target.")
    provenance = _text(provenance_source)
    if not provenance:
        raise SuccessorAcceptanceLifecycleError("Provenance source is required.")
    trust, fiduciary, capacity, appointment, source = _validate_context(
        trust_id=trust_id, fiduciary_id=fiduciary_id, role_capacity=role_capacity,
        appointment_reference=appointment_reference,
        appointment_source_reference=appointment_source_reference,
        trust_authorization_check=trust_authorization_check,
        fiduciary_authorization_check=fiduciary_authorization_check,
    )
    _validate_document_evidence(
        evidence_document_id, trust, document_authorization_check
    )
    firm = database_db.get_current_firm_id()
    fingerprint = acceptance_read.derive_acceptance_context_fingerprint(
        firm_id=firm, trust_id=trust, fiduciary_id=fiduciary,
        appointment_reference=appointment, role_capacity=capacity,
        appointment_source_reference=source,
    )
    connection = database_db.get_connection()
    try:
        existing = connection.execute(
            "SELECT * FROM successor_acceptances WHERE context_fingerprint=? AND firm_id=?",
            (fingerprint, firm),
        ).fetchone()
        if existing is not None:
            existing_target = _text(existing["acceptance_status"])
            if existing_target == "PENDING_EVIDENCE":
                initial_proposal = connection.execute(
                    """SELECT resulting_state FROM successor_acceptance_events
                       WHERE acceptance_id=? AND event_type='TRANSITION_PROPOSED'
                         AND prior_state IS NULL
                       ORDER BY created_at, event_id LIMIT 1""",
                    (existing["acceptance_id"],),
                ).fetchone()
                existing_target = (
                    _text(initial_proposal["resulting_state"])
                    if initial_proposal is not None
                    else ""
                )
            if existing_target != target:
                raise SuccessorAcceptanceLifecycleError(
                    "Canonical Acceptance context already has a different lifecycle meaning."
                )
            return {
                "created": False,
                "idempotent_replay": True,
                "acceptance_id": existing["acceptance_id"],
                "acceptance_status": existing["acceptance_status"],
                "context_fingerprint": fingerprint,
            }
        acceptance_id = _new_id("ACC")
        recorded_at = _now()
        connection.execute(
            """INSERT INTO successor_acceptances (
                acceptance_id, firm_id, trust_id, fiduciary_id,
                appointment_reference, role_capacity, appointment_source_reference,
                acceptance_status, recorded_by, recorded_at, provenance_source,
                context_fingerprint, acceptance_method, evidence_document_id,
                external_evidence_reference, governed_explanation
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                acceptance_id, firm, trust, fiduciary, appointment, capacity, source,
                "PENDING_EVIDENCE", maker, recorded_at, provenance, fingerprint,
                _text(acceptance_method) or None, _text(evidence_document_id) or None,
                _text(external_evidence_reference) or None, _text(reason) or None,
            ),
        )
        row = connection.execute(
            "SELECT * FROM successor_acceptances WHERE acceptance_id=?",
            (acceptance_id,),
        ).fetchone()
        event_id = _insert_event(
            connection, acceptance=row, event_type="TRANSITION_PROPOSED",
            maker_actor_id=maker, prior_state=None, resulting_state=target,
            evidence_document_id=evidence_document_id,
            external_evidence_reference=external_evidence_reference, reason=reason,
        )
        connection.commit()
        return {
            "created": True,
            "idempotent_replay": False,
            "acceptance_id": acceptance_id,
            "acceptance_status": "PENDING_EVIDENCE",
            "proposed_status": target,
            "proposal_event_id": event_id,
            "context_fingerprint": fingerprint,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def attach_acceptance_evidence(
    acceptance_id: Any,
    *,
    maker_actor_id: Any,
    evidence_document_id: Any = None,
    external_evidence_reference: Any = None,
    reason: Any = None,
    document_authorization_check=None,
) -> dict[str, Any]:
    """Attach non-finalizing evidence to a pending Acceptance context."""
    maker = _require_actor_permission(maker_actor_id, MAKER_PERMISSION)
    if not _evidence_present(evidence_document_id, external_evidence_reference):
        raise SuccessorAcceptanceLifecycleError("An evidence reference is required.")
    connection = database_db.get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM successor_acceptances WHERE acceptance_id=? AND firm_id=?",
            (_text(acceptance_id), database_db.get_current_firm_id()),
        ).fetchone()
        if row is None:
            raise SuccessorAcceptanceLifecycleError("Acceptance is missing or not accessible.")
        if row["acceptance_status"] != "PENDING_EVIDENCE":
            raise SuccessorAcceptanceLifecycleError(
                "Evidence attachment is limited to pending Acceptance records."
            )
        _validate_document_evidence(
            evidence_document_id, _text(row["trust_id"]), document_authorization_check
        )
        for existing, supplied in (
            (row["evidence_document_id"], evidence_document_id),
            (row["external_evidence_reference"], external_evidence_reference),
        ):
            if _text(existing) and _text(supplied) and _text(existing) != _text(supplied):
                raise SuccessorAcceptanceLifecycleError(
                    "Conflicting evidence requires a separately governed reconciliation."
                )
        connection.execute(
            """UPDATE successor_acceptances
               SET evidence_document_id=COALESCE(evidence_document_id, ?),
                   external_evidence_reference=COALESCE(external_evidence_reference, ?)
               WHERE acceptance_id=?""",
            (
                _text(evidence_document_id) or None,
                _text(external_evidence_reference) or None,
                row["acceptance_id"],
            ),
        )
        event_id = _insert_event(
            connection, acceptance=row, event_type="EVIDENCE_ATTACHED",
            maker_actor_id=maker, prior_state=row["acceptance_status"],
            resulting_state=row["acceptance_status"],
            evidence_document_id=evidence_document_id,
            external_evidence_reference=external_evidence_reference, reason=reason,
        )
        connection.commit()
        return {"acceptance_id": row["acceptance_id"], "event_id": event_id, "finalized": False}
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def propose_acceptance_transition(
    acceptance_id: Any,
    *,
    proposed_status: str,
    maker_actor_id: Any,
    reason: Any,
    evidence_document_id: Any = None,
    external_evidence_reference: Any = None,
    document_authorization_check=None,
) -> dict[str, Any]:
    """Propose withdrawal or supersession without changing current status."""
    maker = _require_actor_permission(maker_actor_id, MAKER_PERMISSION)
    target = _text(proposed_status).upper()
    connection = database_db.get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM successor_acceptances WHERE acceptance_id=? AND firm_id=?",
            (_text(acceptance_id), database_db.get_current_firm_id()),
        ).fetchone()
        if row is None:
            raise SuccessorAcceptanceLifecycleError("Acceptance is missing or not accessible.")
        if target not in ALLOWED_TRANSITIONS.get(row["acceptance_status"], set()):
            raise SuccessorAcceptanceLifecycleError("Invalid Acceptance lifecycle transition.")
        if target not in {"WITHDRAWN_RECORDED", "SUPERSEDED"}:
            raise SuccessorAcceptanceLifecycleError("Use the initial proposal for this transition.")
        if not _text(reason):
            raise SuccessorAcceptanceLifecycleError("A transition reason is required.")
        if not _evidence_present(evidence_document_id, external_evidence_reference):
            raise SuccessorAcceptanceLifecycleError("Transition evidence is required.")
        _validate_document_evidence(
            evidence_document_id, _text(row["trust_id"]), document_authorization_check
        )
        event_id = _insert_event(
            connection, acceptance=row, event_type="TRANSITION_PROPOSED",
            maker_actor_id=maker, prior_state=row["acceptance_status"],
            resulting_state=target, evidence_document_id=evidence_document_id,
            external_evidence_reference=external_evidence_reference, reason=reason,
        )
        connection.commit()
        return {
            "acceptance_id": row["acceptance_id"], "proposal_event_id": event_id,
            "current_status": row["acceptance_status"], "proposed_status": target,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def review_acceptance_transition(
    acceptance_id: Any,
    *,
    proposal_event_id: Any,
    reviewer_actor_id: Any,
    approve: bool,
    reason: Any,
) -> dict[str, Any]:
    """Independently finalize or reject one pending governed transition."""
    reviewer = _require_actor_permission(reviewer_actor_id, REVIEWER_PERMISSION)
    if not _text(reason):
        raise SuccessorAcceptanceLifecycleError("A review reason is required.")
    connection = database_db.get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM successor_acceptances WHERE acceptance_id=? AND firm_id=?",
            (_text(acceptance_id), database_db.get_current_firm_id()),
        ).fetchone()
        proposal = connection.execute(
            """SELECT * FROM successor_acceptance_events
               WHERE event_id=? AND acceptance_id=? AND firm_id=?
                 AND event_type='TRANSITION_PROPOSED'""",
            (
                _text(proposal_event_id), _text(acceptance_id),
                database_db.get_current_firm_id(),
            ),
        ).fetchone()
        if row is None or proposal is None:
            raise SuccessorAcceptanceLifecycleError("Transition proposal is missing or not accessible.")
        already_reviewed = connection.execute(
            """SELECT 1 FROM successor_acceptance_events
               WHERE related_event_id=? AND event_type IN ('TRANSITION_FINALIZED','REVIEW_REJECTED')""",
            (proposal["event_id"],),
        ).fetchone()
        if already_reviewed:
            raise SuccessorAcceptanceLifecycleError("Transition proposal has already been reviewed.")
        if _text(proposal["maker_actor_id"]).casefold() == reviewer.casefold():
            raise SuccessorAcceptanceLifecycleError(
                "The maker and reviewer must be different actors."
            )
        target = _text(proposal["resulting_state"])
        if target not in ALLOWED_TRANSITIONS.get(row["acceptance_status"], set()):
            raise SuccessorAcceptanceLifecycleError("Invalid Acceptance lifecycle transition.")
        if not approve:
            event_id = _insert_event(
                connection, acceptance=row, event_type="REVIEW_REJECTED",
                maker_actor_id=proposal["maker_actor_id"], reviewer_actor_id=reviewer,
                prior_state=row["acceptance_status"], resulting_state=target,
                evidence_document_id=proposal["evidence_document_id"],
                external_evidence_reference=proposal["external_evidence_reference"],
                reason=reason, related_event_id=proposal["event_id"],
            )
            connection.commit()
            return {
                "acceptance_id": row["acceptance_id"], "approved": False,
                "acceptance_status": row["acceptance_status"], "event_id": event_id,
            }
        evidence_document = _text(proposal["evidence_document_id"]) or _text(row["evidence_document_id"])
        external_evidence = _text(proposal["external_evidence_reference"]) or _text(row["external_evidence_reference"])
        if not _evidence_present(evidence_document, external_evidence):
            raise SuccessorAcceptanceLifecycleError("Verified transition evidence is required.")
        accepted_at = _now() if target == "ACCEPTED_RECORDED" else row["accepted_at"]
        connection.execute(
            """UPDATE successor_acceptances
               SET acceptance_status=?, accepted_at=?, governed_explanation=?
               WHERE acceptance_id=?""",
            (target, accepted_at, _text(reason), row["acceptance_id"]),
        )
        event_id = _insert_event(
            connection, acceptance=row, event_type="TRANSITION_FINALIZED",
            maker_actor_id=proposal["maker_actor_id"], reviewer_actor_id=reviewer,
            prior_state=row["acceptance_status"], resulting_state=target,
            evidence_document_id=evidence_document,
            external_evidence_reference=external_evidence, reason=reason,
            related_event_id=proposal["event_id"],
        )
        connection.commit()
        return {
            "acceptance_id": row["acceptance_id"], "approved": True,
            "prior_status": row["acceptance_status"], "acceptance_status": target,
            "event_id": event_id,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def list_acceptance_events(
    acceptance_id: Any, *, authorization_check
) -> list[dict[str, Any]]:
    """Return immutable lifecycle provenance through the existing read gate."""
    record = acceptance_read.get_successor_acceptance(
        acceptance_id, authorization_check=authorization_check
    )
    if record is None:
        return []
    connection = database_db.get_connection()
    try:
        rows = connection.execute(
            """SELECT * FROM successor_acceptance_events
               WHERE acceptance_id=? AND firm_id=? ORDER BY created_at, event_id""",
            (_text(acceptance_id), database_db.get_current_firm_id()),
        ).fetchall()
    finally:
        connection.close()
    return [dict(row) for row in rows]
