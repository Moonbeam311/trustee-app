"""Deterministic, read-only Guide interpretation of successor Handoff data."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from services.guide_foundation import classify_interpretation
from services.services_handoff_package_adapter import (
    build_successor_handoff_package_descriptor,
)


GUIDE_OUTPUT_CLASSES = (
    "recorded_fact",
    "system_status",
    "source_supported_relationship",
    "inference",
    "conflict",
    "recommendation",
    "proposed_action",
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _reference(owner: str, record_id: Any) -> str:
    return f"{owner}:{_text(record_id) or 'NOT DOCUMENTED'}"


def _item(
    classification: str,
    summary: str,
    basis: str,
    *,
    source_owner: str,
    source_reference: str,
    status: str | None = None,
    recommended_next_action: str | None = None,
    proposed_action: str | None = None,
) -> dict[str, Any]:
    if classification not in GUIDE_OUTPUT_CLASSES:
        raise ValueError(f"Guide Handoff adapter cannot emit {classification!r}.")
    interpretation = classify_interpretation(
        classification, summary, basis, source_reference
    )
    value = asdict(interpretation)
    value.update({
        "label": interpretation.label,
        "source_owner": source_owner,
        "status": status,
        "recommended_next_action": recommended_next_action,
        "proposed_action": proposed_action,
    })
    return value


def _gap_items(gap: dict[str, Any], trust_id: str) -> list[dict[str, Any]]:
    code = _text(gap.get("code")) or "not_documented"
    owner = _text(gap.get("source_domain")) or "TrustSuccessorHandoffContext"
    record_id = _text(gap.get("source_record_id")) or trust_id
    source = _reference(owner, record_id)
    readable = code.replace("_", " ")
    items = [_item(
        "system_status",
        f"Handoff gap: {readable}.",
        "The canonical Handoff readiness contract reports this unresolved gap.",
        source_owner=owner,
        source_reference=source,
        status=code,
    )]
    if any(token in code.lower() for token in ("conflict", "disputed", "inconsistent")):
        items.append(_item(
            "conflict",
            "Recorded sources require reconciliation.",
            f"The canonical Handoff gap is classified as {code}; the Guide does not select a controlling source.",
            source_owner=owner,
            source_reference=source,
            status=code,
        ))
    elif code == "unresolved_authority_source":
        items.append(_item(
            "inference",
            "The recorded authority-source gap may require review before operational transition.",
            "This is an inference from an unresolved canonical authority-evidence status, not a legal-authority conclusion.",
            source_owner=owner,
            source_reference=source,
            status=code,
        ))
    recommendation = {
        "unresolved_authority_source": "Review the recorded authority-source evidence.",
        "successor_acceptance_not_recorded": "Review the governed Successor Acceptance context.",
        "no_continuity_profile": "Review whether an authorized Continuity workflow is appropriate.",
        "continuity_readiness_gaps": "Review the recorded Continuity readiness gaps.",
        "missing_fiduciary_authority_record": "Review the Fiduciary source records for this Trust.",
    }.get(code, "Review the canonical source record associated with this gap.")
    items.extend((
        _item(
            "recommendation",
            recommendation,
            f"The recommendation is triggered by canonical gap {code} and performs no institutional action.",
            source_owner=owner,
            source_reference=source,
            status=code,
            recommended_next_action=recommendation,
        ),
        _item(
            "proposed_action",
            f"Consider resolving {readable} through its established governed workflow.",
            "This is a proposed action for operator consideration; the Guide cannot invoke the write service.",
            source_owner=owner,
            source_reference=source,
            status=code,
            proposed_action=f"Operator review of {source}",
        ),
    ))
    return items


def build_successor_handoff_guide_interpretation(
    trust_id: Any,
    *,
    db_path: str | Path,
    trust_authorization_check,
    continuity_authorization_check,
    fiduciary_authorization_check,
    governance_authorization_check,
    acceptance_authorization_check=None,
    execution_id: Any = None,
    transfer_id: Any = None,
) -> dict[str, Any] | None:
    """Interpret one authorized canonical Handoff package without mutation."""
    package = build_successor_handoff_package_descriptor(
        trust_id,
        db_path=db_path,
        trust_authorization_check=trust_authorization_check,
        continuity_authorization_check=continuity_authorization_check,
        fiduciary_authorization_check=fiduciary_authorization_check,
        governance_authorization_check=governance_authorization_check,
        acceptance_authorization_check=acceptance_authorization_check,
        execution_id=execution_id,
        transfer_id=transfer_id,
    )
    if package is None:
        return None

    root = package["root_trust_id"]
    sections = package["sections"]
    items: list[dict[str, Any]] = []
    trust = sections["trust_identity"]["content"].get("trust") or {}
    items.append(_item(
        "recorded_fact",
        f"Trust {_text(trust.get('trust_name')) or root} is the root of this Handoff context.",
        "The canonical Trust section records the Trust identity.",
        source_owner="Trust", source_reference=_reference("Trust", root),
        status=_text(trust.get("status")) or "NOT DOCUMENTED",
    ))

    fiduciary = sections["fiduciary_authority"]["content"]
    items.append(_item(
        "system_status",
        f"Fiduciary authority evidence is {fiduciary.get('state', 'NOT DOCUMENTED')}.",
        "This reports canonical evidence status and is not a legal-authority determination.",
        source_owner="Fiduciary", source_reference=_reference("Fiduciary", root),
        status=_text(fiduciary.get("state")) or "NOT DOCUMENTED",
    ))

    acceptance = sections["successor_acceptance"]["content"]
    acceptance_status = _text(acceptance.get("display_state")) or "NOT DOCUMENTED / NO ACCEPTANCE EVIDENCE"
    acceptance_records = acceptance.get("records") or []
    acceptance_ref = (
        _reference("SuccessorAcceptance", acceptance_records[0].get("acceptance_id"))
        if acceptance_records else _reference("SuccessorAcceptance", root)
    )
    acceptance_class = "recorded_fact" if acceptance_status == "ACCEPTANCE RECORDED" else "system_status"
    items.append(_item(
        acceptance_class,
        f"Successor Acceptance status: {acceptance_status}.",
        "The certified Acceptance read contract supplies this status; designation or document presence is not Acceptance.",
        source_owner="SuccessorAcceptance", source_reference=acceptance_ref,
        status=acceptance_status,
    ))

    continuity = sections["continuity"]["content"]
    profiles = continuity.get("profiles") or []
    if profiles:
        for profile in profiles:
            profile_id = profile.get("continuity_profile_id")
            items.append(_item(
                "source_supported_relationship",
                f"Continuity Profile {profile_id} is linked to Trust {root}.",
                "The canonical Trust-Continuity context adapter records this relationship.",
                source_owner="Continuity", source_reference=_reference("Continuity", profile_id),
                status=_text(continuity.get("state")) or "AVAILABLE",
            ))
            readiness = profile.get("readiness") or {}
            items.append(_item(
                "system_status",
                f"Continuity readiness is {_text(readiness.get('classification')) or 'NOT DOCUMENTED'}.",
                "Readiness is system evidence status, not legal validity, activation, or responsibility assignment.",
                source_owner="Continuity", source_reference=_reference("Continuity", profile_id),
                status=_text(readiness.get("classification")) or "NOT DOCUMENTED",
            ))
    else:
        items.append(_item(
            "system_status", "No linked Continuity Profile is documented.",
            "The canonical Continuity section is unlinked or unavailable; the Guide does not create a relationship.",
            source_owner="Continuity", source_reference=_reference("Continuity", root),
            status=_text(continuity.get("state")) or "NOT DOCUMENTED",
        ))

    for key, owner in (
        ("governance", "Governance"), ("execution", "Execution"),
        ("documents", "Document"), ("archive", "Archive"),
    ):
        section = sections[key]
        items.append(_item(
            "system_status",
            f"{owner} package content is {section['classification']}.",
            f"The package descriptor references canonical {owner} data and does not own or mutate it.",
            source_owner=owner, source_reference=_reference(owner, root),
            status=section["classification"],
        ))

    for gap in package["readiness"].get("gaps", []):
        items.extend(_gap_items(gap, root))

    result = {
        "contract_version": "V3-THO-GUIDE-1",
        "interpretation_type": "TrustSuccessorHandoffGuideInterpretation",
        "interpretation_id": f"guide-successor-handoff:{root}",
        "root_trust_id": root,
        "source_package": {
            "descriptor_id": package["descriptor_id"],
            "aggregate_id": package["source_aggregate"]["aggregate_id"],
        },
        "items": items,
        "classifications_emitted": sorted({item["classification"] for item in items}),
        "provenance": package["sections"]["provenance"]["content"],
        "boundaries": {
            "operator_authorized_institutional_action_emitted": False,
            "institutional_record_mutated": False,
            "acceptance_changed": False,
            "continuity_activated": False,
            "responsibility_assigned": False,
            "fiduciary_authority_changed": False,
            "execution_advanced": False,
            "document_changed": False,
            "archive_changed": False,
            "application_access_changed": False,
        },
        "mutation_performed": False,
        "disclaimer": (
            "Guide output interprets recorded institutional evidence. It is not legal advice, "
            "legal validity, operator authorization, or a governed institutional action."
        ),
    }
    return result
