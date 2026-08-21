"""Read-only Continuity view of separately owned successor Acceptance evidence."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import services.services_successor_acceptance as acceptance_contract
import services.services_successor_acceptance_evidence as evidence_contract
import services.services_trust_continuity_context as context_contract


TrustAuthorizationCheck = Callable[[str], bool]
ContinuityAuthorizationCheck = Callable[[str], bool]
FiduciaryAuthorizationCheck = Callable[[str, str | None], bool]
AcceptanceAuthorizationCheck = Callable[[str, str], bool]

NOT_DOCUMENTED = "NOT DOCUMENTED"
DOCUMENTED = "DOCUMENTED"
MISSING = "MISSING"
PENDING = "PENDING"
UNRESOLVED = "UNRESOLVED"


class ContinuityAcceptanceEvidenceError(RuntimeError):
    """Raised when the evidence boundary cannot prove a safe scoped read."""


def _text(value: Any) -> str:
    return str(value or "").strip()


def _require_checks(*checks: Any) -> None:
    if any(check is None for check in checks):
        raise ContinuityAcceptanceEvidenceError(
            "Explicit Trust, Continuity, Fiduciary, Acceptance, and Document "
            "authorization checks are required."
        )


def _evidence_state(records: list[dict[str, Any]]) -> tuple[str, str]:
    states = {_text(record.get("acceptance_status")) for record in records}
    if "ACCEPTED_RECORDED" in states:
        return DOCUMENTED, "ACCEPTANCE RECORDED"
    if "PENDING_EVIDENCE" in states:
        return PENDING, "ACCEPTANCE PENDING REVIEW"
    if states:
        return UNRESOLVED, " / ".join(sorted(states))
    return MISSING, "DESIGNATED / ACCEPTANCE NOT RECORDED"


def get_continuity_acceptance_evidence(
    continuity_profile_id: Any,
    *,
    db_path: str | Path,
    expected_trust_id: Any,
    expected_fiduciary_id: Any | None = None,
    trust_authorization_check: TrustAuthorizationCheck | None,
    continuity_authorization_check: ContinuityAuthorizationCheck | None,
    fiduciary_authorization_check: FiduciaryAuthorizationCheck | None,
    acceptance_authorization_check: AcceptanceAuthorizationCheck | None,
    document_authorization_check: TrustAuthorizationCheck | None,
) -> dict[str, Any] | None:
    """Expose canonical Acceptance evidence without changing Continuity.

    The current Continuity contract has no structured source that can declare
    successor Acceptance an activation requirement.  The returned requirement
    and readiness contribution therefore remain explicitly non-blocking and
    ``NOT DOCUMENTED``.
    """
    _require_checks(
        trust_authorization_check,
        continuity_authorization_check,
        fiduciary_authorization_check,
        acceptance_authorization_check,
        document_authorization_check,
    )
    profile_id = _text(continuity_profile_id)
    trust_id = _text(expected_trust_id)
    fiduciary_id = _text(expected_fiduciary_id)
    if not profile_id or not trust_id:
        return None

    context = context_contract.resolve_trust_context_for_continuity(
        profile_id,
        db_path=db_path,
        trust_authorization_check=trust_authorization_check,
        continuity_authorization_check=continuity_authorization_check,
    )
    if (
        context is None
        or context.get("relationship_state") != context_contract.LINKED
        or _text((context.get("trust") or {}).get("trust_id")) != trust_id
    ):
        return None

    try:
        records = acceptance_contract.list_successor_acceptances_for_trust(
            trust_id, authorization_check=acceptance_authorization_check
        )
    except acceptance_contract.SuccessorAcceptanceReadContractError:
        records = []

    scoped_records: list[dict[str, Any]] = []
    for record in records:
        record_fiduciary = _text(record.get("fiduciary_id"))
        if fiduciary_id and record_fiduciary != fiduciary_id:
            continue
        if not fiduciary_authorization_check(record_fiduciary, trust_id):  # type: ignore[misc]
            continue
        evidence = evidence_contract.describe_acceptance_evidence(
            record["acceptance_id"],
            expected_trust_id=trust_id,
            expected_fiduciary_id=record_fiduciary,
            acceptance_authorization_check=acceptance_authorization_check,
            document_authorization_check=document_authorization_check,
        )
        scoped_records.append(
            {
                "acceptance_id": record["acceptance_id"],
                "acceptance_status": record["acceptance_status"],
                "fiduciary_id": record_fiduciary,
                "appointment_reference": record["appointment_reference"],
                "role_capacity": record["role_capacity"],
                "appointment_source_reference": record[
                    "appointment_source_reference"
                ],
                "accepted_at": record.get("accepted_at"),
                "provenance": record.get("provenance"),
                "evidence": evidence or {"evidence_items": []},
            }
        )

    evidence_state, display_state = _evidence_state(scoped_records)
    return {
        "contract_version": "V3-THO-ACC-1E",
        "continuity_profile_id": profile_id,
        "trust_id": trust_id,
        "fiduciary_id": fiduciary_id or None,
        "acceptance_evidence": {
            "state": evidence_state,
            "display_state": display_state,
            "records": scoped_records,
        },
        "activation_requirement": {
            "status": NOT_DOCUMENTED,
            "required": None,
            "authoritative_source": None,
            "software_default_required": False,
        },
        "readiness_contribution": {
            "classification": NOT_DOCUMENTED,
            "effect": "INFORMATIONAL ONLY",
            "blocks_activation": False,
            "changes_continuity_readiness": False,
        },
        "institutional_effects": {
            "continuity_profile_created": False,
            "continuity_activated": False,
            "continuity_event_created": False,
            "responsibility_assigned": False,
            "fiduciary_authority_changed": False,
            "application_access_changed": False,
        },
        "disclaimer": (
            "Acceptance is separately governed evidence. It is not a universal "
            "Continuity prerequisite and does not activate Continuity, assign "
            "responsibility, establish Fiduciary authority, or grant application access."
        ),
        "mutation_performed": False,
    }
