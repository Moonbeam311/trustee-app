DOCUMENT_TEMPLATES = [
    {
        "template_id": "DTPL-000001",
        "name": "Institutional Standard Document",
        "category": "core",
        "description": "Default institutional document layout with title block, governance metadata, execution references, and footer.",
        "engine": "Universal Document Renderer",
        "page_size": "Letter",
        "supports_seal": True,
        "supports_signature": True,
        "supports_qr": True,
        "supports_barcode": True,
        "supports_watermark": True,
        "supports_packet_cover": True,
        "default_for": "Trust",
        "status": "ACTIVE",
    },
    {
        "template_id": "DTPL-000002",
        "name": "Execution Instrument",
        "category": "execution",
        "description": "Layout for signed instruments, minutes, resolutions, transfer instruments, and fiduciary execution records.",
        "engine": "Universal Document Renderer",
        "page_size": "Letter",
        "supports_seal": True,
        "supports_signature": True,
        "supports_qr": True,
        "supports_barcode": True,
        "supports_watermark": True,
        "supports_packet_cover": True,
        "default_for": "Trust Minute",
        "status": "ACTIVE",
    },
    {
        "template_id": "DTPL-000003",
        "name": "Evidence Packet Cover",
        "category": "packet",
        "description": "Cover sheet for document evidence packets, manifests, verification reports, and archive bundles.",
        "engine": "Document Packet Engine",
        "page_size": "Letter",
        "supports_seal": True,
        "supports_signature": False,
        "supports_qr": True,
        "supports_barcode": True,
        "supports_watermark": True,
        "supports_packet_cover": True,
        "default_for": "Packet",
        "status": "ACTIVE",
    },
    {
        "template_id": "DTPL-000004",
        "name": "Public Verification Document",
        "category": "verification",
        "description": "Externally shareable document verification layout with limited internal metadata disclosure.",
        "engine": "Universal Document Renderer",
        "page_size": "Letter",
        "supports_seal": True,
        "supports_signature": False,
        "supports_qr": True,
        "supports_barcode": True,
        "supports_watermark": False,
        "supports_packet_cover": True,
        "default_for": "Certificate",
        "status": "ACTIVE",
    },
    {
        "template_id": "DTPL-000005",
        "name": "Private Internal Document",
        "category": "visibility",
        "description": "Internal/private institutional document layout for trustee, firm, governance, and audit review.",
        "engine": "Universal Document Renderer",
        "page_size": "Letter",
        "supports_seal": True,
        "supports_signature": True,
        "supports_qr": True,
        "supports_barcode": True,
        "supports_watermark": True,
        "supports_packet_cover": False,
        "default_for": "Governance",
        "status": "ACTIVE",
    },
]


def list_document_templates():
    return DOCUMENT_TEMPLATES


def assign_document_template(document_object):
    doc_type = document_object.get("identity", {}).get("document_type")

    for template in DOCUMENT_TEMPLATES:
        if template.get("default_for") == doc_type:
            return template

    return DOCUMENT_TEMPLATES[0]


def document_template_manager_status(document_objects):
    assignments = []

    for obj in document_objects:
        template = assign_document_template(obj)
        assignments.append({
            "document_id": obj["identity"]["document_id"],
            "document_type": obj["identity"]["document_type"],
            "title": obj["identity"]["title"],
            "module": obj["identity"]["module_name"],
            "assigned_template_id": template["template_id"],
            "assigned_template_name": template["name"],
            "engine": template["engine"],
            "status": template["status"],
        })

    return {
        "templates": DOCUMENT_TEMPLATES,
        "assignments": assignments,
        "template_count": len(DOCUMENT_TEMPLATES),
        "active_template_count": len([t for t in DOCUMENT_TEMPLATES if t["status"] == "ACTIVE"]),
        "assignment_count": len(assignments),
    }
