"""
ICP-5H — Certificate Packet Engine

Creates unified certificate evidence packets from the ICP-5C object model.
"""

from io import BytesIO
import json
import zipfile

from services.services_certificate_interface import (
    build_certificate_object,
    build_certificate_pdf_buffer,
)


def _json_bytes(data):
    return json.dumps(data, indent=2, default=str).encode("utf-8")


def build_certificate_verification_report(certificate_object):
    identity = certificate_object.get("identity", {})
    verification = certificate_object.get("verification", {})
    status = certificate_object.get("status", {})

    return {
        "report_type": "certificate_verification_report",
        "certificate_id": identity.get("certificate_id"),
        "certificate_type": identity.get("certificate_type"),
        "verification_status": status.get("verification_status"),
        "verified": verification.get("verified"),
        "hash_algorithm": verification.get("hash_algorithm"),
        "certificate_hash": verification.get("certificate_hash"),
        "stored_hash": verification.get("stored_hash"),
        "recalculated_hash": verification.get("recalculated_hash"),
        "dashboard_hash": verification.get("dashboard_hash"),
        "expected_hash": verification.get("expected_hash"),
        "observed_hash": verification.get("observed_hash"),
        "validation_id": verification.get("validation_id"),
    }


def build_certificate_lifecycle_report(certificate_object):
    return {
        "report_type": "certificate_lifecycle_report",
        "identity": certificate_object.get("identity"),
        "status": certificate_object.get("status"),
        "governance": certificate_object.get("governance"),
        "timeline": certificate_object.get("timeline"),
    }


def build_certificate_relationship_report(certificate_object):
    return {
        "report_type": "certificate_relationship_report",
        "identity": certificate_object.get("identity"),
        "relationships": certificate_object.get("relationships"),
    }


def build_certificate_chain_report(certificate_object):
    return {
        "report_type": "certificate_chain_report",
        "identity": certificate_object.get("identity"),
        "status": certificate_object.get("status"),
        "chain": certificate_object.get("chain"),
    }


def build_certificate_evidence_packet(certificate_id, certificate_type="Continuity"):
    certificate_object = build_certificate_object(certificate_id, certificate_type)

    if not certificate_object.get("found"):
        return None

    pdf_buffer = build_certificate_pdf_buffer(certificate_id, certificate_type)

    identity = certificate_object.get("identity", {})
    safe_id = identity.get("certificate_id") or certificate_id
    safe_type = (identity.get("certificate_type") or certificate_type).replace(" ", "_")

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
        if pdf_buffer:
            z.writestr(
                f"{safe_id}/certificate.pdf",
                pdf_buffer.getvalue()
            )

        z.writestr(
            f"{safe_id}/certificate_object.json",
            _json_bytes(certificate_object)
        )

        z.writestr(
            f"{safe_id}/verification_report.json",
            _json_bytes(build_certificate_verification_report(certificate_object))
        )

        z.writestr(
            f"{safe_id}/lifecycle_report.json",
            _json_bytes(build_certificate_lifecycle_report(certificate_object))
        )

        z.writestr(
            f"{safe_id}/relationship_report.json",
            _json_bytes(build_certificate_relationship_report(certificate_object))
        )

        z.writestr(
            f"{safe_id}/chain_report.json",
            _json_bytes(build_certificate_chain_report(certificate_object))
        )

        manifest = {
            "packet_type": "institutional_certificate_evidence_packet",
            "certificate_id": safe_id,
            "certificate_type": safe_type,
            "included_files": [
                "certificate.pdf",
                "certificate_object.json",
                "verification_report.json",
                "lifecycle_report.json",
                "relationship_report.json",
                "chain_report.json",
            ],
        }

        z.writestr(
            f"{safe_id}/manifest.json",
            _json_bytes(manifest)
        )

    zip_buffer.seek(0)

    return {
        "buffer": zip_buffer,
        "filename": f"{safe_type}_{safe_id}_certificate_packet.zip",
        "certificate_object": certificate_object,
    }
