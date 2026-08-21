"""Canonical read-only aggregate for a Trust successor-handoff context.

This facade composes established domain contracts.  It owns no persistence,
performs no governed transition, and never treats institutional evidence as an
application-permission or legal-authority decision.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import database.db as handoff_db
import services.services_account_asset_contract as account_asset_contract
import services.services_archive_contract as archive_contract
import services.services_document_contract as document_contract
import services.services_execution_contract as execution_contract
import services.services_fiduciary_authority as fiduciary_contract
import services.services_governance as governance_contract
import services.services_successor_acceptance as acceptance_contract
import services.services_successor_acceptance_evidence as acceptance_evidence_contract
import services.services_trust_contract as trust_contract
import services.services_trust_continuity_context as context_contract
from services.services_intake_trust_bridge import (
    BridgeError,
    get_continuity_profile,
    validate_no_secret_material,
)


TrustAuthorizationCheck = Callable[[str], bool]
ContinuityAuthorizationCheck = Callable[[str], bool]
FiduciaryAuthorizationCheck = Callable[[str, str | None], bool]
GovernanceAuthorizationCheck = Callable[[str], bool]
AcceptanceAuthorizationCheck = Callable[[str, str], bool]

AVAILABLE = "AVAILABLE"
UNLINKED = "UNLINKED"
MISSING = "MISSING"
UNRESOLVED = "UNRESOLVED"
NOT_DOCUMENTED = "NOT DOCUMENTED"
NOT_APPLICABLE = "NOT APPLICABLE"


def _acceptance_section(
    trust: dict[str, Any],
    *,
    acceptance_check: AcceptanceAuthorizationCheck,
    document_check: TrustAuthorizationCheck,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Compose canonical Acceptance reads without requiring write permissions."""
    trust_id = _text(trust.get("trust_id"))
    try:
        records = acceptance_contract.list_successor_acceptances_for_trust(
            trust_id, authorization_check=acceptance_check
        )
    except acceptance_contract.SuccessorAcceptanceReadContractError:
        return ({
            "state": NOT_DOCUMENTED,
            "display_state": "NOT DOCUMENTED / NO ACCEPTANCE EVIDENCE",
            "records": [],
            "legacy_documents": [],
            "write_controls_available": False,
        }, [])

    items = []
    provenance = []
    for record in records:
        evidence = acceptance_evidence_contract.describe_acceptance_evidence(
            record["acceptance_id"],
            expected_trust_id=trust_id,
            expected_fiduciary_id=record["fiduciary_id"],
            acceptance_authorization_check=acceptance_check,
            document_authorization_check=document_check,
        )
        items.append({**record, "evidence_visibility": evidence or {"evidence_items": []}})
        provenance.append(_source("SuccessorAcceptance", record["acceptance_id"]))

    states = {item["acceptance_status"] for item in items}
    if "ACCEPTED_RECORDED" in states:
        display_state = "ACCEPTANCE RECORDED"
    elif "PENDING_EVIDENCE" in states:
        display_state = "ACCEPTANCE PENDING REVIEW"
    elif states:
        display_state = " / ".join(sorted(states))
    elif _text(trust.get("successor_trustee_name")):
        display_state = "DESIGNATED / ACCEPTANCE NOT RECORDED"
    else:
        display_state = "NOT DOCUMENTED / NO ACCEPTANCE EVIDENCE"
    return ({
        "state": AVAILABLE if items else MISSING,
        "display_state": display_state,
        "records": items,
        "legacy_documents": [],
        "write_controls_available": False,
        "legal_validity_established": False,
        "appointment_validity_established": False,
        "continuity_activated": False,
        "responsibility_assigned": False,
        "application_access_granted": False,
        "handoff_acknowledged": False,
    }, provenance)

TRUST_FIELDS = (
    "trust_id", "trust_name", "short_name", "jurisdiction", "effective_date",
    "trust_type", "trust_purpose", "settlor_name", "trustee_name",
    "successor_trustee_name", "beneficiary_name", "status", "firm_id",
)
RESPONSIBILITY_FIELDS = (
    "responsibility_id", "continuity_profile_id", "category", "description",
    "current_responsible_party", "successor_responsible_party", "authority_source",
    "supporting_document_reference", "status", "created_at", "updated_at",
)
DIGITAL_ACCESS_FIELDS = (
    "digital_account_id", "continuity_profile_id", "institution_service",
    "institution", "service_name", "account_category", "account_label",
    "login_identifier", "vault_reference", "recovery_procedure", "mfa_method",
    "mfa_device_custodian", "emergency_access_authorization",
    "current_responsible_party", "responsible_party",
    "successor_responsible_party", "supporting_authority", "access_restrictions",
    "last_verified_date", "status", "created_at", "updated_at",
)
RECEIVABLE_FIELDS = (
    "receivable_id", "continuity_profile_id", "payer_debtor", "description",
    "amount", "currency", "due_date_frequency", "supporting_document_reference",
    "payment_method_description", "receiving_account_reference", "current_collector",
    "successor_collector", "delinquency_instructions", "escalation_instructions",
    "priority", "status", "last_verified_date", "notes", "created_at", "updated_at",
)
PAYABLE_FIELDS = (
    "payable_id", "continuity_profile_id", "creditor_payee", "description",
    "account_reference", "amount", "due_date_frequency", "autopay_status",
    "payment_source_reference", "current_responsible_party",
    "successor_responsible_party", "priority", "consequence_nonpayment",
    "continuity_instruction", "supporting_document_reference", "status",
    "last_verified_date", "notes", "created_at", "updated_at",
)
ACTIVATION_FIELDS = (
    "activation_plan_id", "continuity_profile_id", "continuity_subject",
    "triggering_event", "required_evidence", "authorized_recognizer",
    "primary_successor", "alternate_successors", "authority_source",
    "immediate_actions", "affected_responsibilities", "affected_accounts_obligations",
    "essential_payments", "expected_receivables", "notifications",
    "controlled_access_release_procedure", "restrictions",
    "review_escalation_procedure", "restoration_transfer_closure_procedure",
    "status", "activation_basis", "authorized_by", "authorized_at", "created_at",
    "updated_at",
)


class HandoffReadAggregateError(RuntimeError):
    """Raised when explicit aggregate authorization is unavailable."""


def _text(value: Any) -> str:
    return str(value or "").strip()


def _require_checks(
    trust_check: TrustAuthorizationCheck | None,
    continuity_check: ContinuityAuthorizationCheck | None,
    fiduciary_check: FiduciaryAuthorizationCheck | None,
    governance_check: GovernanceAuthorizationCheck | None,
) -> tuple[TrustAuthorizationCheck, ContinuityAuthorizationCheck,
           FiduciaryAuthorizationCheck, GovernanceAuthorizationCheck]:
    if any(check is None for check in (
        trust_check, continuity_check, fiduciary_check, governance_check
    )):
        raise HandoffReadAggregateError(
            "Explicit Trust, Continuity, Fiduciary, and Governance authorization checks are required."
        )
    return trust_check, continuity_check, fiduciary_check, governance_check  # type: ignore[return-value]


def _select(record: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: record.get(field) for field in fields if field in record}


def _source(domain: str, record_id: Any) -> dict[str, Any]:
    return {"source_domain": domain, "source_record_id": _text(record_id) or NOT_DOCUMENTED}


def _continuity_sections(
    contexts: dict[str, Any], *, db_path: str | Path,
    continuity_check: ContinuityAuthorizationCheck,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    firm_id = handoff_db.get_current_firm_id()
    profiles, provenance, security_gaps = [], [], []
    for summary in contexts.get("continuity_profiles", []):
        profile_id = _text(summary.get("continuity_profile_id"))
        if not profile_id or not continuity_check(profile_id):
            continue
        bundle = get_continuity_profile(db_path, profile_id, firm_id)
        if bundle is None:
            continue
        digital_accounts = []
        for record in bundle.get("digital_accounts", []):
            safe_record = _select(record, DIGITAL_ACCESS_FIELDS)
            try:
                validate_no_secret_material(safe_record)
            except BridgeError:
                security_gaps.append({
                    "code": "prohibited_secret_material_withheld",
                    **_source("Continuity", record.get("digital_account_id")),
                })
                continue
            digital_accounts.append(safe_record)
        profile = bundle["profile"]
        profiles.append({
            "continuity_profile_id": profile_id,
            "profile": {
                key: profile.get(key) for key in (
                    "continuity_profile_id", "subject_name", "subject_type",
                    "subject_capacities", "status", "trust_id", "intake_id",
                    "matter_id", "bridge_id", "readiness_status", "last_reviewed_date",
                    "next_review_date", "created_at", "updated_at",
                )
            },
            "readiness": bundle.get("readiness") or {},
            "responsibilities": [
                _select(row, RESPONSIBILITY_FIELDS)
                for row in bundle.get("responsibilities", [])
            ],
            "digital_access_metadata": digital_accounts,
            "receivables": [
                _select(row, RECEIVABLE_FIELDS) for row in bundle.get("receivables", [])
            ],
            "payables": [
                _select(row, PAYABLE_FIELDS) for row in bundle.get("payables", [])
            ],
            "activation_plans": [
                _select(row, ACTIVATION_FIELDS)
                for row in bundle.get("activation_plans", [])
            ],
        })
        provenance.append(_source("Continuity", profile_id))
    return ({
        "state": AVAILABLE if profiles else UNLINKED,
        "relationship_cardinality": contexts.get("relationship_cardinality", "ZERO_OR_MANY"),
        "profiles": profiles,
        "profile_count": len(profiles),
    }, provenance, security_gaps)


def _readiness_gaps(
    trust: dict[str, Any], fiduciaries: list[dict[str, Any]],
    continuity: dict[str, Any], inventory: dict[str, Any],
    execution: dict[str, Any], documents: list[dict[str, Any]],
    archives: list[dict[str, Any]], security_gaps: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    gaps = list(security_gaps)
    if not _text(trust.get("successor_trustee_name")):
        gaps.append({"code": "missing_successor_identity", **_source("Trust", trust.get("trust_id"))})
    if not fiduciaries:
        gaps.append({"code": "missing_fiduciary_authority_record", **_source("Fiduciary", trust.get("trust_id"))})
    for record in fiduciaries:
        evidence = record.get("authority_evidence") or {}
        if evidence.get("authority_evidence_state") != "recorded":
            gaps.append({"code": "unresolved_authority_source", **_source("Fiduciary", record.get("fiduciary_id"))})
    if continuity["state"] == UNLINKED:
        gaps.append({"code": "no_continuity_profile", **_source("TrustContinuity", trust.get("trust_id"))})
    for item in continuity.get("profiles", []):
        readiness = item.get("readiness") or {}
        if readiness.get("classification") != "ready_for_review":
            gaps.append({
                "code": "continuity_readiness_gaps",
                "gap_count": readiness.get("gap_count"),
                **_source("Continuity", item.get("continuity_profile_id")),
            })
    unresolved_links = (inventory.get("summary") or {}).get(
        "unresolved_account_property_references", 0
    )
    if unresolved_links:
        gaps.append({"code": "unresolved_account_asset_references", "count": unresolved_links,
                     **_source("AccountAsset", trust.get("trust_id"))})
    for blocker in ((execution.get("orchestration") or {}).get("execution") or {}).get("blockers", []):
        gaps.append({"code": "execution_blocker", "evidence": blocker, **_source("Execution", execution.get("execution_id"))})
    transfer = (execution.get("orchestration") or {}).get("transfer") or {}
    for blocker in transfer.get("pending_requirements", []):
        gaps.append({"code": "transfer_requirement_pending", "evidence": blocker, **_source("Execution", execution.get("transfer_id"))})
    # Document and Archive requirements are not universal policy. Their absence is
    # represented in their section state, not promoted into a required gap.
    _ = documents, archives
    return ("needs_attention" if gaps else "ready_for_review", gaps)


def build_trust_successor_handoff_context(
    trust_id: Any,
    *,
    db_path: str | Path,
    trust_authorization_check: TrustAuthorizationCheck | None,
    continuity_authorization_check: ContinuityAuthorizationCheck | None,
    fiduciary_authorization_check: FiduciaryAuthorizationCheck | None,
    governance_authorization_check: GovernanceAuthorizationCheck | None,
    acceptance_authorization_check: AcceptanceAuthorizationCheck | None = None,
    execution_id: Any = None,
    transfer_id: Any = None,
) -> dict[str, Any] | None:
    """Build a source-attributed handoff snapshot without persistence or transition.

    Missing, inaccessible, and cross-firm Trust roots share the safe ``None``
    result. Optional Execution identifiers are interpreted only by the existing
    canonical orchestration contract.
    """
    trust_check, continuity_check, fiduciary_check, governance_check = _require_checks(
        trust_authorization_check, continuity_authorization_check,
        fiduciary_authorization_check, governance_authorization_check,
    )
    trust_key = _text(trust_id)
    trust_row = trust_contract.get_trust_by_id(
        trust_key, authorization_check=trust_check
    )
    if trust_row is None:
        return None
    trust = _select(dict(trust_row), TRUST_FIELDS)
    acceptance_check = acceptance_authorization_check or (
        lambda _acceptance_id, candidate_trust: (
            candidate_trust == trust_key and trust_check(candidate_trust)
        )
    )

    contexts = context_contract.resolve_continuity_contexts_for_trust(
        trust_key, db_path=db_path, trust_authorization_check=trust_check,
        continuity_authorization_check=continuity_check,
    )
    if contexts is None:
        return None
    continuity, provenance, security_gaps = _continuity_sections(
        contexts, db_path=db_path, continuity_check=continuity_check
    )

    fiduciaries = []
    for record in fiduciary_contract.list_fiduciaries_for_trust(
        trust_key, authorization_check=fiduciary_check
    ):
        evidence = fiduciary_contract.evaluate_authority_evidence(
            record.get("fiduciary_id"), trust_id=trust_key,
            authorization_check=fiduciary_check,
        )
        fiduciaries.append({**record, "authority_evidence": evidence})
        provenance.append(_source("Fiduciary", record.get("fiduciary_id")))

    inventory = account_asset_contract.aggregate_trust_inventory(
        trust_key, authorization_check=trust_check
    )
    if inventory is None:
        return None

    governance = {"state": UNRESOLVED, "links": [], "summary": NOT_DOCUMENTED}
    if governance_check(trust_key):
        links = governance_contract.build_trust_governance_links(trust_key)
        summary = governance_contract.build_trust_governance_summary(trust_key)
        governance = {
            "state": AVAILABLE if links else MISSING,
            "links": links,
            "summary": summary,
        }
        provenance.extend(
            _source("Governance", link.get("governance_id")) for link in links
        )

    documents = document_contract.list_document_references(
        trust_key, authorization_check=trust_check
    )
    acceptance, acceptance_provenance = _acceptance_section(
        trust, acceptance_check=acceptance_check, document_check=trust_check
    )
    provenance.extend(acceptance_provenance)
    orchestration = execution_contract.build_orchestration_context(
        trust_key, authorization_check=trust_check,
        execution_id=execution_id, transfer_id=transfer_id,
    )
    if orchestration is None:
        return None
    execution = {
        "state": AVAILABLE if _text(execution_id) or _text(transfer_id) else NOT_APPLICABLE,
        "execution_id": _text(execution_id) or None,
        "transfer_id": _text(transfer_id) or None,
        "orchestration": orchestration,
        "acceptance_persistence_contract": NOT_DOCUMENTED,
    }
    archives = archive_contract.list_transfer_archive_packages(
        trust_key, authorization_check=trust_check
    )

    provenance.insert(0, _source("Trust", trust_key))
    provenance.append(_source("AccountAsset", trust_key))
    provenance.extend(_source("Document", item.get("document_id")) for item in documents)
    provenance.extend(_source("Archive", item.get("package_id")) for item in archives)
    if _text(execution_id):
        provenance.append(_source("Execution", execution_id))
    if _text(transfer_id):
        provenance.append(_source("Execution", transfer_id))

    readiness, gaps = _readiness_gaps(
        trust, fiduciaries, continuity, inventory, execution,
        documents, archives, security_gaps,
    )
    if acceptance["display_state"] != "ACCEPTANCE RECORDED":
        gaps.append({
            "code": "successor_acceptance_not_recorded",
            "evidence": acceptance["display_state"],
            **_source("SuccessorAcceptance", trust_key),
        })
        readiness = "needs_attention"
    result = {
        "contract_version": "V3-THO-AGG-1",
        "aggregate_type": "TrustSuccessorHandoffContext",
        "aggregate_id": f"trust-successor-handoff:{trust_key}",
        "root_trust_id": trust_key,
        "identity": {
            "state": AVAILABLE,
            "trust": trust,
            "current_trustee": trust.get("trustee_name"),
            "successor_trustee": trust.get("successor_trustee_name"),
        },
        "fiduciary_authority": {
            "state": AVAILABLE if fiduciaries else MISSING,
            "records": fiduciaries,
            "legal_authority_conclusion": False,
            "system_permission_granted": False,
        },
        "successor_acceptance": acceptance,
        "continuity": continuity,
        "accounts_assets": inventory,
        "governance": governance,
        "execution": execution,
        "documents": {
            "state": AVAILABLE if documents else MISSING,
            "references": documents,
            "output_generated": False,
        },
        "archive": {
            "state": AVAILABLE if archives else MISSING,
            "descriptors": archives,
            "handoff_or_export_created": False,
        },
        "readiness": {
            "status": readiness,
            "gaps": gaps,
            "gap_count": len(gaps),
            "disclaimer": (
                "Readiness is not legal validity, appointment, incapacity, "
                "financial certification, completion, or application access."
            ),
        },
        "provenance": provenance,
        "boundaries": {
            "persistent_aggregate_created": False,
            "source_record_copied": False,
            "event_created": False,
            "permission_changed": False,
            "continuity_transition_performed": False,
            "document_generated": False,
            "archive_or_handoff_created": False,
        },
        "mutation_performed": False,
    }
    validate_no_secret_material(result)
    return result
