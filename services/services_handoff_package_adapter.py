"""Derived successor Handoff package descriptor over canonical read contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.services_handoff_read_aggregate import (
    build_trust_successor_handoff_context,
)
from services.services_intake_trust_bridge import validate_no_secret_material


INCLUDED = "INCLUDED"
REFERENCE_ONLY = "REFERENCE ONLY"
NOT_AVAILABLE = "NOT AVAILABLE"
NOT_DOCUMENTED = "NOT DOCUMENTED"
NOT_APPLICABLE = "NOT APPLICABLE"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _validate_secret_tree(value: Any) -> None:
    if isinstance(value, dict):
        validate_no_secret_material(value)
        for item in value.values():
            _validate_secret_tree(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _validate_secret_tree(item)


def _classification(section: dict[str, Any], *, reference_only: bool = False) -> str:
    state = _text(section.get("state")).upper()
    if state == "NOT APPLICABLE":
        return NOT_APPLICABLE
    if state == "NOT DOCUMENTED":
        return NOT_DOCUMENTED
    if state in {"MISSING", "UNLINKED"}:
        return NOT_AVAILABLE
    return REFERENCE_ONLY if reference_only else INCLUDED


def _manifest(aggregate: dict[str, Any], sections: dict[str, Any]) -> list[dict[str, Any]]:
    classifications = {
        "Trust": sections["trust_identity"]["classification"],
        "Fiduciary": sections["fiduciary_authority"]["classification"],
        "SuccessorAcceptance": sections["successor_acceptance"]["classification"],
        "Continuity": sections["continuity"]["classification"],
        "AccountAsset": sections["accounts_assets"]["classification"],
        "Governance": sections["governance"]["classification"],
        "Execution": sections["execution"]["classification"],
        "Document": sections["documents"]["classification"],
        "Archive": sections["archive"]["classification"],
    }
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for source in aggregate.get("provenance", []):
        owner = _text(source.get("source_domain")) or NOT_DOCUMENTED
        record_id = _text(source.get("source_record_id")) or NOT_DOCUMENTED
        key = (owner, record_id)
        if key in seen:
            continue
        seen.add(key)
        classification = classifications.get(owner, REFERENCE_ONLY)
        items.append({
            "canonical_object_id": record_id,
            "object_type": owner,
            "source_owner": owner,
            "status": classification,
            "included": classification == INCLUDED,
            "reference_only": classification == REFERENCE_ONLY,
            "provenance_reference": {"source_domain": owner, "source_record_id": record_id},
        })
    return sorted(items, key=lambda item: (item["source_owner"], item["canonical_object_id"]))


def build_successor_handoff_package_descriptor(
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
    """Assemble one ephemeral package descriptor without files or persistence."""
    aggregate = build_trust_successor_handoff_context(
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
    if aggregate is None:
        return None

    sections = {
        "trust_identity": {
            "classification": INCLUDED,
            "source_owner": "Trust",
            "content": aggregate["identity"],
        },
        "fiduciary_authority": {
            "classification": _classification(aggregate["fiduciary_authority"]),
            "source_owner": "Fiduciary",
            "content": aggregate["fiduciary_authority"],
        },
        "successor_acceptance": {
            "classification": _classification(aggregate["successor_acceptance"]),
            "source_owner": "SuccessorAcceptance",
            "content": aggregate["successor_acceptance"],
        },
        "continuity": {
            "classification": _classification(aggregate["continuity"]),
            "source_owner": "Continuity",
            "content": aggregate["continuity"],
        },
        "accounts_assets": {
            "classification": INCLUDED,
            "source_owner": "AccountAsset",
            "content": aggregate["accounts_assets"],
        },
        "governance": {
            "classification": _classification(aggregate["governance"]),
            "source_owner": "Governance",
            "content": aggregate["governance"],
        },
        "execution": {
            "classification": _classification(aggregate["execution"], reference_only=True),
            "source_owner": "Execution",
            "content": aggregate["execution"],
        },
        "documents": {
            "classification": _classification(aggregate["documents"], reference_only=True),
            "source_owner": "Document",
            "content": aggregate["documents"],
        },
        "archive": {
            "classification": _classification(aggregate["archive"], reference_only=True),
            "source_owner": "Archive",
            "content": aggregate["archive"],
        },
        "unresolved_gaps": {
            "classification": INCLUDED,
            "source_owner": "TrustSuccessorHandoffContext",
            "content": aggregate["readiness"],
        },
        "provenance": {
            "classification": REFERENCE_ONLY,
            "source_owner": "Canonical source contracts",
            "content": aggregate["provenance"],
        },
    }
    descriptor = {
        "contract_version": "V3-THO-PKG-1",
        "descriptor_type": "TrustSuccessorHandoffPackageDescriptor",
        "descriptor_id": f"successor-handoff-package-descriptor:{aggregate['root_trust_id']}",
        "root_trust_id": aggregate["root_trust_id"],
        "source_aggregate": {
            "aggregate_id": aggregate["aggregate_id"],
            "contract_version": aggregate["contract_version"],
        },
        "sections": sections,
        "content_index": _manifest(aggregate, sections),
        "readiness": {
            "status": aggregate["readiness"]["status"],
            "gap_count": aggregate["readiness"]["gap_count"],
            "gaps": aggregate["readiness"]["gaps"],
            "package_required_item_policy": NOT_DOCUMENTED,
            "package_complete": False,
            "legally_certified": False,
        },
        "generation": {
            "generated_at": NOT_DOCUMENTED,
            "manifest_generated": False,
            "file_generated": False,
            "archive_record_created": False,
            "package_record_created": False,
        },
        "institutional_effects": {
            "legal_certification_created": False,
            "acceptance_changed": False,
            "continuity_activated": False,
            "responsibility_assigned": False,
            "fiduciary_authority_changed": False,
            "execution_advanced": False,
            "application_access_changed": False,
            "handoff_acknowledged": False,
        },
        "disclaimer": (
            "This is a derived package descriptor, not an archived, finalized, "
            "certified, activated, acknowledged, or legally sufficient package."
        ),
        "mutation_performed": False,
    }
    _validate_secret_tree(descriptor)
    return descriptor
