"""P08 derived unified provenance read model for Work & Learning Programs.

This module is read-only. It does not own persistence, migrations, permissions,
institutional authority, legal conclusions, or source-domain lifecycle events.
"""

from __future__ import annotations

from typing import Any, Callable

from services.services_work_learning_program_handoff import (
    SAVED_REVISION,
    WorkLearningProgramHandoffError,
    build_work_learning_program_handoff_descriptor,
)
from services.services_governed_program_promotion import (
    PromotionError,
    list_program_promotion_state,
)


AuthorizationCheck = Callable[[str], bool]


class WorkLearningProvenanceError(ValueError):
    """Fail-closed P08 read-model error."""


def _text(value: Any) -> str:
    return str(value or "").strip()


def _source_event(
    *,
    source_family: str,
    source_type: str,
    source_id: Any,
    event_type: str,
    occurred_at: Any = None,
    actor: Any = None,
    status: Any = None,
    trust_id: Any = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize a source-native fact without inventing missing facts."""
    return {
        "source_family": source_family,
        "source_type": source_type,
        "source_id": _text(source_id) or None,
        "event_type": _text(event_type),
        "occurred_at": _text(occurred_at) or None,
        "actor": _text(actor) or None,
        "status": _text(status) or None,
        "trust_id": _text(trust_id) or None,
        "details": dict(details or {}),
    }


def build_work_learning_provenance_descriptor(
    *,
    workspace_id: Any,
    program_id: Any,
    revision_id: Any,
    trust_id: Any,
    firm_id: Any,
    owner_id: Any,
    actor: Any,
    role: Any,
    db_path: Any,
    trust_authorization_check,
    continuity_authorization_check,
    fiduciary_authorization_check,
    governance_authorization_check,
    acceptance_authorization_check,
) -> dict[str, Any]:
    """Build one read-only unified provenance view from P06 and P07 sources.

    P06 and P07 remain canonical owners of their respective facts. P08 only
    normalizes authorized source-native facts for presentation.
    """

    workspace = _text(workspace_id)
    program = _text(program_id)
    revision = _text(revision_id)
    trust = _text(trust_id)
    firm = _text(firm_id)
    owner = _text(owner_id)
    principal = _text(actor)
    actor_role = _text(role)

    if not all(
        (workspace, program, revision, trust, firm, owner, principal, actor_role)
    ):
        raise WorkLearningProvenanceError("provenance_context_not_available")

    if db_path is None or not _text(db_path):
        raise WorkLearningProvenanceError("provenance_context_not_available")

    # P06 remains canonical for handoff/source-attribution context.
    try:
        handoff = build_work_learning_program_handoff_descriptor(
            program_id=program,
            workspace_id=workspace,
            firm_id=firm,
            owner_id=owner,
            state_mode=SAVED_REVISION,
            trust_id=trust,
            db_path=db_path,
            trust_authorization_check=trust_authorization_check,
            continuity_authorization_check=continuity_authorization_check,
            fiduciary_authorization_check=fiduciary_authorization_check,
            governance_authorization_check=governance_authorization_check,
            acceptance_authorization_check=acceptance_authorization_check,
            revision_id=revision,
        )
    except WorkLearningProgramHandoffError as exc:
        raise WorkLearningProvenanceError(
            "provenance_context_not_available"
        ) from exc

    if not handoff:
        raise WorkLearningProvenanceError("provenance_context_not_available")

    # Exact scope agreement is mandatory. P08 never combines data across firms,
    # owners, workspaces, programs, revisions, or Trusts.
    expected = {
        "workspace_id": workspace,
        "program_id": program,
        "revision_id": revision,
        "trust_id": trust,
        "firm_id": firm,
        "owner_id": owner,
    }
    for key, value in expected.items():
        if _text(handoff.get(key)) != value:
            raise WorkLearningProvenanceError(
                "provenance_context_not_available"
            )

    # P07 remains canonical for governed promotion state/events.
    try:
        promotion_state = list_program_promotion_state(
            workspace_id=workspace,
            program_id=program,
            trust_id=trust,
            firm_id=firm,
            owner_id=owner,
            actor=principal,
            role=actor_role,
            trust_authorization_check=trust_authorization_check,
        )
    except PromotionError as exc:
        raise WorkLearningProvenanceError(
            "provenance_context_not_available"
        ) from exc

    for key, value in (
        ("workspace", workspace),
        ("program", program),
        ("trust", trust),
    ):
        source = promotion_state.get(key) or {}
        identity_key = {
            "workspace": "workspace_id",
            "program": "program_id",
            "trust": "trust_id",
        }[key]
        if _text(source.get(identity_key)) != value:
            raise WorkLearningProvenanceError(
                "provenance_context_not_available"
            )

    revisions = [
        row
        for row in promotion_state.get("revisions", [])
        if _text(row.get("revision_id")) == revision
    ]
    if len(revisions) != 1:
        raise WorkLearningProvenanceError("provenance_context_not_available")

    selected_revision = revisions[0]

    timeline: list[dict[str, Any]] = []

    # Program saved revision: use only the timestamp actually stored by P05.
    timeline.append(
        _source_event(
            source_family="WORK_LEARNING_PROGRAM",
            source_type="PROGRAM_REVISION",
            source_id=revision,
            event_type="SAVED_REVISION_CAPTURED",
            occurred_at=selected_revision.get("created_at"),
            actor=selected_revision.get("created_by"),
            status="WORKING_RECORD",
            trust_id=trust,
            details={
                "revision_number": selected_revision.get("revision_number"),
                "label": selected_revision.get("revision_label"),
                "source_boundary": "Program working record",
            },
        )
    )

    # P05 source references are attribution, not verification.
    source_references = list(handoff.get("p05_source_references") or [])
    for reference in source_references:
        if not isinstance(reference, dict):
            continue
        timeline.append(
            _source_event(
                source_family="WORK_LEARNING_PROGRAM",
                source_type="SOURCE_REFERENCE",
                source_id=(
                    reference.get("source_reference_id")
                    or reference.get("reference_id")
                    or reference.get("source_reference")
                ),
                event_type="SOURCE_ATTRIBUTED",
                occurred_at=(
                    reference.get("created_at")
                    or reference.get("captured_at")
                ),
                actor=reference.get("created_by"),
                status="ATTRIBUTION_NOT_VERIFICATION",
                trust_id=trust,
                details={
                    "source_type": reference.get("source_type"),
                    "title": reference.get("title"),
                    "reference": reference.get("source_reference"),
                },
            )
        )

    # P07 events are already canonical domain events. P08 normalizes them once;
    # it does not manufacture, persist, or duplicate them.
    p07_events = []
    for event in promotion_state.get("events", []):
        if _text(event.get("program_revision_id")) != revision:
            continue
        if _text(event.get("firm_id")) != firm:
            raise WorkLearningProvenanceError(
                "provenance_context_not_available"
            )
        if _text(event.get("owner_id")) != owner:
            raise WorkLearningProvenanceError(
                "provenance_context_not_available"
            )
        if _text(event.get("workspace_id")) != workspace:
            raise WorkLearningProvenanceError(
                "provenance_context_not_available"
            )
        if _text(event.get("program_id")) != program:
            raise WorkLearningProvenanceError(
                "provenance_context_not_available"
            )
        if _text(event.get("trust_id")) != trust:
            raise WorkLearningProvenanceError(
                "provenance_context_not_available"
            )

        normalized = _source_event(
            source_family="GOVERNED_PROGRAM_PROMOTION",
            source_type="P07_EVENT",
            source_id=event.get("event_id"),
            event_type=event.get("event_type") or "P07_EVENT",
            occurred_at=event.get("event_at"),
            actor=event.get("actor_username"),
            status=event.get("resulting_state"),
            trust_id=trust,
            details={
                "request_id": event.get("request_id"),
                "prior_state": event.get("prior_state"),
                "resulting_state": event.get("resulting_state"),
                "authority_grant_id": event.get("authority_grant_id"),
                "destination_record_id": event.get(
                    "destination_record_id"
                ),
                "reason": event.get("reason"),
            },
        )
        p07_events.append(normalized)
        timeline.append(normalized)

    promotions = [
        row
        for row in promotion_state.get("promotions", [])
        if _text(row.get("program_revision_id")) == revision
        and _text(row.get("trust_id")) == trust
    ]

    requests = [
        row
        for row in promotion_state.get("requests", [])
        if _text(row.get("program_revision_id")) == revision
        and _text(row.get("trust_id")) == trust
    ]

    # Preserve source-native chronology. Missing timestamps remain None and are
    # never synthesized merely to force a total ordering.
    def sort_key(item: dict[str, Any]):
        return (
            item.get("occurred_at") is None,
            item.get("occurred_at") or "",
            item.get("source_family") or "",
            item.get("source_id") or "",
        )

    timeline.sort(key=sort_key)

    return {
        "descriptor_type": "WorkLearningProgramProvenanceDescriptor",
        "architecture": "DERIVED_UNIFIED_READ_MODEL",
        "read_only": True,
        "workspace_id": workspace,
        "program_id": program,
        "revision_id": revision,
        "trust_id": trust,
        "firm_id": firm,
        "owner_id": owner,
        "source_revision": selected_revision,
        "source_references": source_references,
        "handoff_descriptor": handoff,
        "promotion_requests": requests,
        "promotions": promotions,
        "promotion_events": p07_events,
        "timeline": timeline,
        "boundaries": {
            "source_attribution": "ATTRIBUTION_NOT_VERIFICATION",
            "p06": "READ_ONLY_CANONICAL_REFERENCE",
            "p07": "SOURCE_NATIVE_GOVERNED_EVENTS",
            "p08": "DERIVED_READ_MODEL_ONLY",
            "generic_audit_log_as_domain_truth": False,
            "new_persistence": False,
            "new_migration": False,
            "new_permission": False,
            "new_fiduciary_authority": False,
            "handoff_acknowledgement_created": False,
            "continuity_activated": False,
            "acceptance_created": False,
            "legal_validity_inferred": False,
        },
    }
