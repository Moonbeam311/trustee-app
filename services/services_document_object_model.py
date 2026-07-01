"""
ICP-8A — Universal Document Object Model

Read-only foundation for treating institutional documents as canonical objects.
This does not replace existing document generation.
"""

def build_document_object(
    document_id,
    document_type,
    title=None,
    module_name=None,
    source_record_id=None,
    source_record_type=None,
    status="draft",
    lifecycle_status="created",
    governance_policy="Controlled",
    retention_policy="Permanent",
    relationships=None,
    timeline=None,
    verification=None,
    payload=None,
):
    return {
        "found": True,
        "identity": {
            "document_id": document_id,
            "document_type": document_type,
            "title": title or document_id,
            "module_name": module_name or "Institutional Documents",
            "source_record_id": source_record_id,
            "source_record_type": source_record_type,
        },
        "classification": {
            "document_family": "Institutional Document",
            "document_type": document_type,
            "module_name": module_name or "Institutional Documents",
        },
        "status": {
            "status": status,
            "lifecycle_status": lifecycle_status,
            "verification_status": (verification or {}).get("verification_status", "unverified"),
            "record_status": "active",
        },
        "governance": {
            "governance_policy": governance_policy,
            "retention_policy": retention_policy,
            "allows_edit": status not in ("final", "executed", "archived"),
            "allows_delete": False,
            "requires_reason": True,
            "requires_authority": True,
        },
        "relationships": {
            "count": len(relationships or []),
            "items": relationships or [],
        },
        "timeline": {
            "event_count": len(timeline or []),
            "events": timeline or [],
        },
        "verification": verification or {
            "verified": False,
            "verification_status": "unverified",
        },
        "rendering": {
            "supports_pdf": True,
            "supports_docx": True,
            "supports_packet": True,
            "supports_template": True,
        },
        "capabilities": {
            "supports_lifecycle": True,
            "supports_timeline": True,
            "supports_relationships": True,
            "supports_verification": True,
            "supports_governance": True,
            "supports_packet": True,
            "supports_exports": True,
        },
        "payload": payload or {},
    }


def document_object_model_status():
    return {
        "interface": "Universal Document Object Model",
        "status": "ready",
        "sections": [
            "identity",
            "classification",
            "status",
            "governance",
            "relationships",
            "timeline",
            "verification",
            "rendering",
            "capabilities",
            "payload",
        ],
    }
