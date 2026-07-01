from services.services_certificate_policies import get_certificate_type_policy
from services.services_certificate_relationships import list_certificate_relationships
"""
ICP-5B — Shared Certificate Service Interface

Framework-facing service layer for institutional certificates.
This does not replace existing certificate engines yet.
It provides a stable contract for ICP-5C+ migration.
"""

from services.services_certificate_registry import get_certificate_type
from services.services_certifications import (
    get_institutional_certification,
    verify_institutional_certification,
    get_certificate_lifecycle,
    get_certificate_chain,
    list_certificate_lifecycle_events,
)


def get_certificate_definition(certificate_type):
    """
    Returns framework definition for a certificate type.
    """
    return get_certificate_type(certificate_type)


def get_certificate_record(certificate_id, certificate_type="Continuity"):
    """
    Returns certificate record using the current type adapter.

    Continuity is the first supported adapter.
    Additional certificate types will be added in ICP-5C+.
    """
    if certificate_type == "Continuity":
        return get_institutional_certification(certificate_id)

    return None


def verify_certificate(certificate_id, certificate_type="Continuity"):
    """
    Shared verification interface.
    """
    if certificate_type == "Continuity":
        return verify_institutional_certification(certificate_id)

    return {
        "verified": False,
        "verification_status": "unsupported",
        "message": f"No verification adapter registered for {certificate_type}.",
    }


def get_certificate_lifecycle_profile(certificate_id, certificate_type="Continuity"):
    """
    Shared lifecycle interface.
    """
    if certificate_type == "Continuity":
        return get_certificate_lifecycle(certificate_id)

    return None


def get_certificate_timeline(certificate_id, certificate_type="Continuity"):
    """
    Shared timeline interface.
    """
    if certificate_type == "Continuity":
        return list_certificate_lifecycle_events(certificate_id)

    return []


def get_certificate_chain_profile(certificate_id, certificate_type="Continuity"):
    """
    Shared chain interface.
    """
    if certificate_type == "Continuity":
        return get_certificate_chain(certificate_id)

    return {
        "certificate": None,
        "supersedes": None,
        "superseded_by": None,
    }


def build_certificate_detail_context(certificate_id, certificate_type="Continuity"):
    """
    Shared detail context builder.

    This becomes the canonical data envelope for unified detail views.
    """
    definition = get_certificate_definition(certificate_type)
    record = get_certificate_record(certificate_id, certificate_type)
    verification = verify_certificate(certificate_id, certificate_type)
    lifecycle = get_certificate_lifecycle_profile(certificate_id, certificate_type)
    timeline = get_certificate_timeline(certificate_id, certificate_type)
    chain = get_certificate_chain_profile(certificate_id, certificate_type)

    return {
        "certificate_type": certificate_type,
        "definition": definition,
        "record": record,
        "verification": verification,
        "lifecycle": lifecycle,
        "timeline": timeline,
        "chain": chain,
        "supported": bool(definition),
    }


def certificate_interface_status():
    """
    Lightweight health check for ICP-5B.
    """
    continuity_definition = get_certificate_definition("Continuity")

    return {
        "interface": "Institutional Certificate Service Interface",
        "status": "ready" if continuity_definition else "registry_missing",
        "reference_type": "Continuity",
        "reference_type_registered": bool(continuity_definition),
        "supported_adapters": ["Continuity"],
    }


def build_certificate_object(certificate_id, certificate_type="Continuity"):
    """
    ICP-5C:
    Canonical institutional certificate object model.

    This creates one normalized object envelope regardless of certificate type.
    Continuity is the reference adapter.
    """
    context = build_certificate_detail_context(certificate_id, certificate_type)

    record = context.get("record") or {}
    definition = context.get("definition") or {}
    verification = context.get("verification") or {}
    lifecycle = context.get("lifecycle") or {}
    chain = context.get("chain") or {}
    timeline = context.get("timeline") or []
    policy = get_certificate_type_policy(definition)

    if not record:
        return {
            "found": False,
            "certificate_id": certificate_id,
            "certificate_type": certificate_type,
            "message": "Certificate record not found.",
        }

    return {
        "found": True,

        "identity": {
            "certificate_id": record.get("certification_id"),
            "certificate_type": certificate_type,
            "display_name": definition.get("display_name"),
            "module_name": definition.get("module_name"),
            "certificate_version": record.get("certificate_version"),
            "execution_id": record.get("execution_id"),
        },

        "status": {
            "certification_status": record.get("certification_status"),
            "verification_status": verification.get("verification_status"),
            "lifecycle_status": lifecycle.get("lifecycle_status"),
            "revocation_status": record.get("revocation_status"),
            "chain_status": lifecycle.get("chain_status"),
        },

        "governance": {
            "issuance_reason": lifecycle.get("issuance_reason"),
            "issuance_authority": lifecycle.get("issuance_authority"),
            "generation_engine": lifecycle.get("generation_engine"),
            "governance_policy": definition.get("governance_policy"),
            "retention_policy": definition.get("retention_policy"),
            "lifecycle_notes": lifecycle.get("lifecycle_notes"),
        },

        "verification": {
            "verified": verification.get("verified"),
            "stored_hash": verification.get("stored_hash"),
            "recalculated_hash": verification.get("recalculated_hash"),
            "certificate_hash": record.get("certificate_hash"),
            "dashboard_hash": record.get("dashboard_hash"),
            "expected_hash": record.get("expected_hash"),
            "observed_hash": record.get("observed_hash"),
            "validation_id": record.get("validation_id"),
            "hash_algorithm": "SHA-256",
        },

        "chain": {
            "supersedes_certification_id": record.get("supersedes_certification_id"),
            "superseded_by_certification_id": record.get("superseded_by_certification_id"),
            "supersedes": chain.get("supersedes"),
            "superseded_by": chain.get("superseded_by"),
        },

        "timeline": {
            "event_count": len(timeline),
            "events": timeline,
        },

        "capabilities": {
            "supports_lifecycle": bool(definition.get("supports_lifecycle")),
            "supports_timeline": bool(definition.get("supports_timeline")),
            "supports_chain": bool(definition.get("supports_chain")),
            "supports_pdf": bool(definition.get("supports_pdf")),
            "supports_packet": bool(definition.get("supports_packet")),
            "supports_supersession": bool(definition.get("supports_supersession")),
            "supports_relationships": bool(definition.get("supports_relationships")),
            "supports_provenance": bool(definition.get("supports_provenance")),
        },

        "relationships": {
            "count": len(list_certificate_relationships(record.get("certification_id"))),
            "items": list_certificate_relationships(record.get("certification_id")),
        },

        "policy": {
            "policy_id": policy.get("policy_id") if policy else None,
            "policy_name": policy.get("policy_name") if policy else definition.get("governance_policy"),
            "display_name": policy.get("display_name") if policy else definition.get("governance_policy"),
            "policy_category": policy.get("policy_category") if policy else None,
            "description": policy.get("description") if policy else None,
            "allows_edit": bool(policy.get("allows_edit")) if policy else False,
            "allows_delete": bool(policy.get("allows_delete")) if policy else False,
            "allows_supersession": bool(policy.get("allows_supersession")) if policy else bool(definition.get("supports_supersession")),
            "allows_revocation": bool(policy.get("allows_revocation")) if policy else False,
            "requires_lifecycle_event": bool(policy.get("requires_lifecycle_event")) if policy else True,
            "requires_reason": bool(policy.get("requires_reason")) if policy else True,
            "requires_authority": bool(policy.get("requires_authority")) if policy else True,
            "retention_rule": policy.get("retention_rule") if policy else definition.get("retention_policy"),
        },

        "payload": {
            "raw_record": record,
        },
    }


def certificate_object_model_status():
    """
    ICP-5C health check.
    """
    obj = build_certificate_object("CERT-000003", "Continuity")

    return {
        "interface": "Institutional Certificate Object Model",
        "status": "ready" if obj.get("found") else "record_missing",
        "reference_type": "Continuity",
        "reference_certificate": "CERT-000003",
        "object_sections": [
            "identity",
            "status",
            "governance",
            "verification",
            "chain",
            "timeline",
            "capabilities",
            "relationships",
            "policy",
            "payload",
        ],
        "reference_found": obj.get("found"),
    }


def build_certificate_pdf_buffer(certificate_id, certificate_type="Continuity"):
    """
    ICP-5D:
    Shared PDF interface using the unified PDF builder.
    """
    from services.services_certificate_pdf_builder import build_unified_certificate_pdf

    certificate_object = build_certificate_object(certificate_id, certificate_type)

    if not certificate_object.get("found"):
        return None

    return build_unified_certificate_pdf(certificate_object)


def list_unified_certificate_objects():
    """
    ICP-5F:
    Unified registry object list.

    Continuity certificates are the first adapter-backed certificate records.
    Trust Minute certificates and other types will be added in later migrations.
    """
    from services.services_certifications import list_institutional_certifications

    objects = []

    for row in list_institutional_certifications():
        cert_id = row.get("certification_id")
        cert_type = row.get("certificate_type") or "Continuity"

        obj = build_certificate_object(cert_id, cert_type)

        if obj.get("found"):
            objects.append(obj)

    return objects


def unified_certificate_registry_summary():
    """
    ICP-5F:
    Summary metrics for unified certificate registry dashboard.
    """
    objects = list_unified_certificate_objects()

    current = 0
    superseded = 0
    verified = 0

    type_counts = {}

    for obj in objects:
        cert_type = obj["identity"].get("certificate_type") or "Unknown"
        type_counts[cert_type] = type_counts.get(cert_type, 0) + 1

        if str(obj["status"].get("chain_status") or "").lower() == "superseded":
            superseded += 1
        else:
            current += 1

        if obj["verification"].get("verified"):
            verified += 1

    return {
        "total": len(objects),
        "current": current,
        "superseded": superseded,
        "verified": verified,
        "type_counts": type_counts,
    }
