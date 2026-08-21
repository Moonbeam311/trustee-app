"""Scoped evidence/document adapter for canonical successor Acceptance records."""

from __future__ import annotations

from typing import Any

import database.db as database_db
from services import services_document_contract as document_contract
from services import services_fiduciary_authority as fiduciary_contract
from services import services_successor_acceptance as acceptance_read
from services import services_successor_acceptance_lifecycle as lifecycle
from services import services_trust_contract as trust_contract


class SuccessorAcceptanceEvidenceError(RuntimeError):
    """Raised when an evidence relationship is missing, mismatched, or denied."""


def _text(value: Any) -> str:
    return str(value or "").strip()


def _acceptance_context(
    acceptance_id: Any,
    *,
    expected_trust_id: Any,
    expected_fiduciary_id: Any,
    acceptance_authorization_check,
) -> dict[str, Any]:
    record = acceptance_read.get_successor_acceptance(
        acceptance_id, authorization_check=acceptance_authorization_check
    )
    if record is None:
        raise SuccessorAcceptanceEvidenceError(
            "Acceptance is missing or not accessible."
        )
    expected_trust = _text(expected_trust_id)
    expected_fiduciary = _text(expected_fiduciary_id)
    if not expected_trust or record["trust_id"] != expected_trust:
        raise SuccessorAcceptanceEvidenceError(
            "Acceptance Trust context does not match the requested evidence context."
        )
    if not expected_fiduciary or record["fiduciary_id"] != expected_fiduciary:
        raise SuccessorAcceptanceEvidenceError(
            "Acceptance Fiduciary context does not match the requested evidence context."
        )
    return record


def link_acceptance_document_evidence(
    acceptance_id: Any,
    *,
    document_id: Any,
    expected_trust_id: Any,
    expected_fiduciary_id: Any,
    maker_actor_id: Any,
    reason: Any,
    acceptance_authorization_check,
    document_authorization_check,
) -> dict[str, Any]:
    """Link a scoped Document reference through the maker-authorized 1B service."""
    record = _acceptance_context(
        acceptance_id,
        expected_trust_id=expected_trust_id,
        expected_fiduciary_id=expected_fiduciary_id,
        acceptance_authorization_check=acceptance_authorization_check,
    )
    document = document_contract.get_document_reference(
        document_id,
        record["trust_id"],
        authorization_check=document_authorization_check,
    )
    if document is None:
        raise SuccessorAcceptanceEvidenceError(
            "Document evidence is missing or outside the Acceptance Trust and firm."
        )
    attachment = lifecycle.attach_acceptance_evidence(
        record["acceptance_id"],
        maker_actor_id=maker_actor_id,
        evidence_document_id=document["document_id"],
        reason=reason,
        document_authorization_check=document_authorization_check,
    )
    return {
        "acceptance_id": record["acceptance_id"],
        "evidence": {
            "identifier": document["document_id"],
            "source_type": "DOCUMENT_REFERENCE",
            "source_owner": "DOCUMENT",
            "relationship": "SUPPORTS_ACCEPTANCE_REVIEW",
            "document": document,
            "execution_finalization_status": "NOT DOCUMENTED",
        },
        "attachment_event_id": attachment["event_id"],
        "acceptance_finalized": False,
    }


def link_acceptance_external_evidence(
    acceptance_id: Any,
    *,
    external_reference: Any,
    expected_trust_id: Any,
    expected_fiduciary_id: Any,
    maker_actor_id: Any,
    reason: Any,
    acceptance_authorization_check,
) -> dict[str, Any]:
    """Link an opaque governed external reference without creating shadow storage."""
    record = _acceptance_context(
        acceptance_id,
        expected_trust_id=expected_trust_id,
        expected_fiduciary_id=expected_fiduciary_id,
        acceptance_authorization_check=acceptance_authorization_check,
    )
    reference = _text(external_reference)
    if not reference:
        raise SuccessorAcceptanceEvidenceError(
            "A governed external evidence reference is required."
        )
    attachment = lifecycle.attach_acceptance_evidence(
        record["acceptance_id"],
        maker_actor_id=maker_actor_id,
        external_evidence_reference=reference,
        reason=reason,
    )
    return {
        "acceptance_id": record["acceptance_id"],
        "evidence": {
            "identifier": reference,
            "source_type": "EXTERNAL_GOVERNED_REFERENCE",
            "source_owner": "EXTERNAL / NOT DOCUMENTED",
            "relationship": "SUPPORTS_ACCEPTANCE_REVIEW",
            "execution_finalization_status": "NOT DOCUMENTED",
        },
        "attachment_event_id": attachment["event_id"],
        "acceptance_finalized": False,
    }


def describe_acceptance_evidence(
    acceptance_id: Any,
    *,
    expected_trust_id: Any,
    expected_fiduciary_id: Any,
    acceptance_authorization_check,
    document_authorization_check,
) -> dict[str, Any] | None:
    """Describe linked evidence and its immutable maker/reviewer provenance."""
    try:
        record = _acceptance_context(
            acceptance_id,
            expected_trust_id=expected_trust_id,
            expected_fiduciary_id=expected_fiduciary_id,
            acceptance_authorization_check=acceptance_authorization_check,
        )
    except SuccessorAcceptanceEvidenceError:
        return None
    events = lifecycle.list_acceptance_events(
        record["acceptance_id"], authorization_check=acceptance_authorization_check
    )
    references: list[tuple[str, str]] = []
    document_id = _text(record["evidence"].get("document_id"))
    external_reference = _text(record["evidence"].get("external_reference"))
    if document_id:
        references.append(("DOCUMENT_REFERENCE", document_id))
    if external_reference:
        references.append(("EXTERNAL_GOVERNED_REFERENCE", external_reference))
    for event in events:
        event_document = _text(event.get("evidence_document_id"))
        event_external = _text(event.get("external_evidence_reference"))
        if event_document and ("DOCUMENT_REFERENCE", event_document) not in references:
            references.append(("DOCUMENT_REFERENCE", event_document))
        if event_external and ("EXTERNAL_GOVERNED_REFERENCE", event_external) not in references:
            references.append(("EXTERNAL_GOVERNED_REFERENCE", event_external))

    items: list[dict[str, Any]] = []
    for source_type, identifier in references:
        related = [
            event for event in events
            if identifier in {
                _text(event.get("evidence_document_id")),
                _text(event.get("external_evidence_reference")),
            }
        ]
        finalized = [
            event for event in related
            if event.get("event_type") == "TRANSITION_FINALIZED"
        ]
        document = None
        if source_type == "DOCUMENT_REFERENCE":
            document = document_contract.get_document_reference(
                identifier,
                record["trust_id"],
                authorization_check=document_authorization_check,
            )
            if document is None:
                continue
        items.append(
            {
                "identifier": identifier,
                "source_type": source_type,
                "source_owner": (
                    "DOCUMENT"
                    if source_type == "DOCUMENT_REFERENCE"
                    else "EXTERNAL / NOT DOCUMENTED"
                ),
                "relationship": "SUPPORTS_ACCEPTANCE_REVIEW",
                "document": document,
                "execution_finalization_status": "NOT DOCUMENTED",
                "acceptance_review_status": (
                    "RELIED_ON_IN_FINALIZED_TRANSITION"
                    if finalized
                    else "ATTACHED / NOT FINALIZED"
                ),
                "maker_actor_ids": sorted(
                    {_text(event.get("maker_actor_id")) for event in related}
                    - {""}
                ),
                "reviewer_actor_ids": sorted(
                    {_text(event.get("reviewer_actor_id")) for event in finalized}
                    - {""}
                ),
                "event_references": [event["event_id"] for event in related],
            }
        )
    return {
        "acceptance_id": record["acceptance_id"],
        "firm_id": record["firm_id"],
        "trust_id": record["trust_id"],
        "fiduciary_id": record["fiduciary_id"],
        "acceptance_status": record["acceptance_status"],
        "evidence_items": items,
        "legal_validity_established": False,
        "document_presence_records_acceptance": False,
    }


def build_acceptance_document_source_context(
    acceptance_id: Any,
    *,
    expected_trust_id: Any,
    expected_fiduciary_id: Any,
    acceptance_authorization_check,
    trust_authorization_check,
    fiduciary_authorization_check,
) -> dict[str, Any] | None:
    """Build producer-ready canonical source context without rendering or persistence."""
    try:
        acceptance = _acceptance_context(
            acceptance_id,
            expected_trust_id=expected_trust_id,
            expected_fiduciary_id=expected_fiduciary_id,
            acceptance_authorization_check=acceptance_authorization_check,
        )
    except SuccessorAcceptanceEvidenceError:
        return None
    trust = trust_contract.get_trust_by_id(
        acceptance["trust_id"], authorization_check=trust_authorization_check
    )
    fiduciary = fiduciary_contract.get_fiduciary_by_id(
        acceptance["fiduciary_id"], authorization_check=fiduciary_authorization_check
    )
    if trust is None or fiduciary is None:
        return None
    return {
        "document_context_type": "SUCCESSOR_ACCEPTANCE_SOURCE_CONTEXT",
        "sources": {
            "acceptance": acceptance,
            "trust": {
                "trust_id": trust["trust_id"],
                "trust_name": trust["trust_name"],
                "firm_id": trust["firm_id"],
            },
            "fiduciary": {
                "fiduciary_id": fiduciary["fiduciary_id"],
                "full_name": fiduciary["full_name"],
                "role_title": fiduciary["role_title"],
                "firm_id": fiduciary["firm_id"],
            },
        },
        "output_state": {
            "generated": False,
            "executed": False,
            "persisted": False,
            "acceptance_transition_performed": False,
        },
        "institutional_disclaimer": (
            "Acceptance is recorded evidence and does not establish legal validity, "
            "Continuity activation, Fiduciary authority, or application access."
        ),
    }


def describe_legacy_acceptance_document(
    document_id: Any,
    trust_id: Any,
    *,
    document_authorization_check,
) -> dict[str, Any] | None:
    """Describe an unlinked legacy document without promoting Acceptance state."""
    document = document_contract.get_document_reference(
        document_id, trust_id, authorization_check=document_authorization_check
    )
    if document is None:
        return None
    connection = database_db.get_connection()
    try:
        linked = connection.execute(
            """SELECT acceptance_id FROM successor_acceptances
               WHERE firm_id=? AND trust_id=? AND evidence_document_id=? LIMIT 1""",
            (database_db.get_current_firm_id(), _text(trust_id), _text(document_id)),
        ).fetchone()
    finally:
        connection.close()
    return {
        "document": document,
        "linked_acceptance_id": linked["acceptance_id"] if linked else None,
        "classification": (
            "STRUCTURED ACCEPTANCE EVIDENCE REFERENCE"
            if linked
            else acceptance_read.LEGACY_DOCUMENT_CLASSIFICATION
        ),
        "acceptance_created": False,
    }
