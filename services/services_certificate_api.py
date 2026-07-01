from services.services_certificate_adapters import get_certificate_adapter, certificate_adapter_status
from services.services_certificate_event_bus import emit_certificate_event
"""
ICP-5J — Institutional Certificate API

Single sanctioned API façade for institutional certificates.
Continuity is the first adapter. Future certificate types must plug into this API.
"""

from services.services_certificate_registry import (
    get_certificate_type,
    list_certificate_types,
)

from services.services_certificate_interface import (
    build_certificate_detail_context,
    build_certificate_object,
    build_certificate_pdf_buffer,
    list_unified_certificate_objects,
    unified_certificate_registry_summary,
)

from services.services_certificate_packet import build_certificate_evidence_packet
from services.services_certificate_relationships import list_certificate_relationships
from services.services_certifications import (
    get_institutional_certification,
    verify_institutional_certification,
    get_certificate_chain,
    get_certificate_lifecycle,
    list_certificate_lifecycle_events,
)



def list_trust_minute_adapter_objects():
    """
    ICP-7B-2:
    Pull existing Trust Minute certificate IDs into the universal certificate registry
    through the Trust Minute adapter, without changing legacy Trust Minute tables.
    """
    adapter = get_certificate_adapter("Trust Minute")
    if not adapter:
        return []

    try:
        from app import get_all_trust_minutes
        rows = get_all_trust_minutes()
    except Exception:
        return []

    objects = []

    for row in rows:
        try:
            minute = dict(row)
        except Exception:
            minute = row

        cert_id = minute.get("certificate_id")

        if not cert_id:
            continue

        obj = adapter.object(cert_id)

        if obj and obj.get("found"):
            objects.append(obj)

    return objects



def list_transfer_adapter_objects():
    adapter = get_certificate_adapter("Transfer")
    if not adapter:
        return []

    try:
        from database.db import get_connection
        conn = get_connection()
        cur = conn.cursor()
        rows = cur.execute("SELECT * FROM transfer_records").fetchall()
        conn.close()
    except Exception as e:
        print("TRANSFER ADAPTER LIST ERROR:", e)
        return []

    objects = []
    for row in rows:
        transfer = dict(row)
        transfer_id = transfer.get("transfer_id")
        if not transfer_id:
            continue

        cert_id = transfer.get("certificate_id") or f"CERT-TRF-{transfer_id.replace('TRF-', '')}"
        obj = adapter.object(cert_id)

        if obj and obj.get("found"):
            objects.append(obj)

    return objects

class CertificateAPI:
    """
    Institutional certificate API façade.
    """

    SUPPORTED_TYPES = {"Continuity"}

    @staticmethod
    def adapter_supported(certificate_type):
        return certificate_type in CertificateAPI.SUPPORTED_TYPES

    @staticmethod
    def definition(certificate_type):
        return get_certificate_type(certificate_type)

    @staticmethod
    def types(active_only=False):
        return list_certificate_types(active_only=active_only)

    @staticmethod
    def get(certificate_id, certificate_type="Continuity"):
        if certificate_type == "Continuity":
            return get_institutional_certification(certificate_id)
        return None

    @staticmethod
    def object(certificate_id, certificate_type="Continuity"):
        adapter = get_certificate_adapter(certificate_type)

        if adapter and certificate_type != "Continuity":
            return adapter.object(certificate_id)

        return build_certificate_object(certificate_id, certificate_type)

    @staticmethod
    def detail(certificate_id, certificate_type="Continuity"):
        return build_certificate_detail_context(certificate_id, certificate_type)

    @staticmethod
    def verify(certificate_id, certificate_type="Continuity"):
        adapter = get_certificate_adapter(certificate_type)

        if adapter and certificate_type != "Continuity":
            result = adapter.verify(certificate_id)
            emit_certificate_event(
                certification_id=certificate_id,
                certificate_type=certificate_type,
                event_category="verification",
                event_name="CertificateAPI.adapter_verify_observed",
                event_status=result.get("verification_status"),
                event_summary=f"{certificate_type} verification requested through adapter.",
                event_payload=result,
                actor="api",
                authority="Institutional Certificate API",
                source_engine=f"CertificateAPI.verify:{certificate_type}",
                severity="info" if result.get("verified") else "warning",
            )
            return result

        if certificate_type == "Continuity":
            result = verify_institutional_certification(certificate_id)

            emit_certificate_event(
                certification_id=certificate_id,
                certificate_type=certificate_type,
                event_category="verification",
                event_name="CertificateAPI.verify_observed",
                event_status=result.get("verification_status"),
                event_summary="Certificate verification requested through Institutional Certificate API.",
                event_payload=result,
                actor="api",
                authority="Institutional Certificate API",
                source_engine="CertificateAPI.verify",
                severity="info" if result.get("verified") else "warning",
            )

            return result

        result = {
            "verified": False,
            "verification_status": "unsupported",
            "message": f"No verification adapter registered for {certificate_type}.",
        }

        emit_certificate_event(
            certification_id=certificate_id,
            certificate_type=certificate_type,
            event_category="verification",
            event_name="CertificateAPI.verify_unsupported",
            event_status="unsupported",
            event_summary="Unsupported certificate verification requested.",
            event_payload=result,
            actor="api",
            authority="Institutional Certificate API",
            source_engine="CertificateAPI.verify",
            severity="warning",
        )

        return result

    @staticmethod
    def lifecycle(certificate_id, certificate_type="Continuity"):
        if certificate_type == "Continuity":
            return get_certificate_lifecycle(certificate_id)
        return None

    @staticmethod
    def timeline(certificate_id, certificate_type="Continuity"):
        if certificate_type == "Continuity":
            return list_certificate_lifecycle_events(certificate_id)
        return []

    @staticmethod
    def relationships(certificate_id, certificate_type="Continuity"):
        return list_certificate_relationships(certificate_id)

    @staticmethod
    def chain(certificate_id, certificate_type="Continuity"):
        if certificate_type == "Continuity":
            return get_certificate_chain(certificate_id)
        return {
            "certificate": None,
            "supersedes": None,
            "superseded_by": None,
        }

    @staticmethod
    def pdf(certificate_id, certificate_type="Continuity"):
        return build_certificate_pdf_buffer(certificate_id, certificate_type)

    @staticmethod
    def packet(certificate_id, certificate_type="Continuity"):
        packet = build_certificate_evidence_packet(certificate_id, certificate_type)

        emit_certificate_event(
            certification_id=certificate_id,
            certificate_type=certificate_type,
            event_category="packet",
            event_name="CertificateAPI.packet_generated",
            event_status="generated" if packet else "failed",
            event_summary="Certificate evidence packet requested through Institutional Certificate API.",
            event_payload={
                "filename": packet.get("filename") if packet else None,
                "generated": bool(packet),
            },
            actor="api",
            authority="Institutional Certificate API",
            source_engine="CertificateAPI.packet",
            severity="info" if packet else "error",
        )

        return packet

    @staticmethod
    def registry():
        objects = list_unified_certificate_objects()
        objects.extend(list_trust_minute_adapter_objects())
        objects.extend(list_transfer_adapter_objects())

        type_counts = {}
        verified = 0
        current = 0
        superseded = 0

        for obj in objects:
            cert_type = obj.get("identity", {}).get("certificate_type") or "Unknown"
            type_counts[cert_type] = type_counts.get(cert_type, 0) + 1

            if obj.get("status", {}).get("verification_status") == "verified":
                verified += 1

            chain_status = str(obj.get("status", {}).get("chain_status") or "").lower()
            if chain_status == "current":
                current += 1
            elif chain_status == "superseded":
                superseded += 1

        return {
            "summary": {
                "total": len(objects),
                "verified": verified,
                "current": current,
                "superseded": superseded,
                "type_counts": type_counts,
            },
            "objects": objects,
        }

    @staticmethod
    def search(query=None, certificate_type=None, verification_status=None, chain_status=None):
        objects = list_unified_certificate_objects()

        q = (query or "").strip().lower()
        filtered = []

        for obj in objects:
            if certificate_type and obj["identity"].get("certificate_type") != certificate_type:
                continue

            if verification_status and obj["status"].get("verification_status") != verification_status:
                continue

            if chain_status and str(obj["status"].get("chain_status") or "").lower() != chain_status.lower():
                continue

            haystack = " ".join([
                str(obj["identity"].get("certificate_id") or ""),
                str(obj["identity"].get("certificate_type") or ""),
                str(obj["identity"].get("display_name") or ""),
                str(obj["identity"].get("module_name") or ""),
                str(obj["status"].get("certification_status") or ""),
                str(obj["status"].get("verification_status") or ""),
                str(obj["status"].get("chain_status") or ""),
                str(obj["governance"].get("issuance_authority") or ""),
                str(obj["governance"].get("generation_engine") or ""),
                str(obj["governance"].get("issuance_reason") or ""),
            ]).lower()

            if q and q not in haystack:
                continue

            filtered.append(obj)

        return {
            "count": len(filtered),
            "objects": filtered,
        }

    @staticmethod
    def validate(certificate_id, certificate_type="Continuity"):
        record = CertificateAPI.get(certificate_id, certificate_type)
        definition = CertificateAPI.definition(certificate_type)
        verification = CertificateAPI.verify(certificate_id, certificate_type)

        issues = []

        if not definition:
            issues.append("Certificate type definition not registered.")

        if not CertificateAPI.adapter_supported(certificate_type):
            issues.append("Certificate adapter not supported.")

        if not record:
            issues.append("Certificate record not found.")

        if verification and not verification.get("verified"):
            issues.append("Certificate verification failed or is unsupported.")

        return {
            "certificate_id": certificate_id,
            "certificate_type": certificate_type,
            "valid": len(issues) == 0,
            "issues": issues,
            "verification": verification,
        }

    @staticmethod
    def revoke(certificate_id, certificate_type="Continuity", reason=None, authority=None):
        return {
            "supported": False,
            "message": "Revoke is reserved for later policy-controlled implementation.",
            "certificate_id": certificate_id,
            "certificate_type": certificate_type,
            "reason": reason,
            "authority": authority,
        }

    @staticmethod
    def supersede(certificate_id, certificate_type="Continuity", reason=None, authority=None):
        return {
            "supported": False,
            "message": "Supersede is reserved for later adapter-controlled implementation.",
            "certificate_id": certificate_id,
            "certificate_type": certificate_type,
            "reason": reason,
            "authority": authority,
        }

    @staticmethod
    def issue(certificate_type, payload=None, authority=None):
        return {
            "supported": False,
            "message": "Issue is reserved for later adapter-controlled implementation.",
            "certificate_type": certificate_type,
            "payload": payload or {},
            "authority": authority,
        }


def certificate_api_status():
    registry = CertificateAPI.registry()

    return {
        "api": "Institutional Certificate API",
        "status": "ready",
        "supported_types": sorted(CertificateAPI.SUPPORTED_TYPES),
        "registered_types": len(CertificateAPI.types()),
        "registry_objects": registry["summary"]["total"],
        "verified": registry["summary"]["verified"],
    }
