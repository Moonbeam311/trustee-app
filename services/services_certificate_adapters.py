class CertificateAdapter:
    certificate_type = None

    def issue(self, payload=None, authority=None):
        raise NotImplementedError

    def verify(self, certificate_id):
        raise NotImplementedError

    def get(self, certificate_id):
        raise NotImplementedError

    def object(self, certificate_id):
        raise NotImplementedError

    def pdf(self, certificate_id):
        raise NotImplementedError

    def packet(self, certificate_id):
        raise NotImplementedError


class ContinuityCertificateAdapter(CertificateAdapter):
    certificate_type = "Continuity"

    def issue(self, payload=None, authority=None):
        return {
            "supported": False,
            "message": "Continuity issuance remains controlled by the existing continuity certification engine.",
            "certificate_type": self.certificate_type,
            "payload": payload or {},
            "authority": authority,
        }

    def verify(self, certificate_id):
        from services.services_certifications import verify_institutional_certification
        return verify_institutional_certification(certificate_id)

    def get(self, certificate_id):
        from services.services_certifications import get_institutional_certification
        return get_institutional_certification(certificate_id)

    def object(self, certificate_id):
        from services.services_certificate_interface import build_certificate_object
        return build_certificate_object(certificate_id, self.certificate_type)

    def pdf(self, certificate_id):
        from services.services_certificate_interface import build_certificate_pdf_buffer
        return build_certificate_pdf_buffer(certificate_id, self.certificate_type)

    def packet(self, certificate_id):
        from services.services_certificate_packet import build_certificate_evidence_packet
        return build_certificate_evidence_packet(certificate_id, self.certificate_type)




class TrustMinuteCertificateAdapter(CertificateAdapter):
    certificate_type = "Trust Minute"

    def issue(self, payload=None, authority=None):
        return {
            "supported": False,
            "message": "Trust Minute issuance remains controlled by the existing Trust Minutes execution workflow.",
            "certificate_type": self.certificate_type,
            "payload": payload or {},
            "authority": authority,
        }

    def get(self, certificate_id):
        from app import get_trust_minute_by_certificate_id

        row = get_trust_minute_by_certificate_id(certificate_id)

        if row is None:
            return None

        return dict(row)

    def verify(self, certificate_id):
        minute = self.get(certificate_id)

        if not minute:
            return {
                "verified": False,
                "verification_status": "not_found",
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "message": "Trust Minute certificate record not found.",
            }

        return {
            "verified": True,
            "verification_status": "verified",
            "certificate_id": certificate_id,
            "certificate_type": self.certificate_type,
            "minute_id": minute.get("minute_id"),
            "trust_id": minute.get("trust_id"),
            "locked": minute.get("locked"),
            "execution_status": minute.get("execution_status") or minute.get("status"),
            "message": "Trust Minute certificate record exists and is adapter-visible.",
        }

    def object(self, certificate_id):
        minute = self.get(certificate_id)
        verification = self.verify(certificate_id)

        if not minute:
            return {
                "found": False,
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "message": "Trust Minute certificate record not found.",
            }

        minute_id = minute.get("minute_id")
        trust_id = minute.get("trust_id")
        title = minute.get("title") or "Trust Minute Certificate"
        status = minute.get("execution_status") or minute.get("status") or "Unknown"

        relationship_items = [
            {
                "relationship_id": f"TMREL-{minute_id}-MIN",
                "certification_id": certificate_id,
                "certificate_type": self.certificate_type,
                "related_object_type": "trust_minute",
                "related_object_id": minute_id,
                "relationship_type": "certifies",
                "relationship_label": title,
                "relationship_basis": "Certificate ID is attached to the Trust Minute record.",
                "relationship_status": "active",
            }
        ]

        if trust_id:
            relationship_items.append({
                "relationship_id": f"TMREL-{minute_id}-TRUST",
                "certification_id": certificate_id,
                "certificate_type": self.certificate_type,
                "related_object_type": "trust",
                "related_object_id": trust_id,
                "relationship_type": "belongs_to",
                "relationship_label": f"Trust {trust_id}",
                "relationship_basis": "Trust Minute record is associated with this trust.",
                "relationship_status": "active",
            })

        return {
            "found": True,
            "identity": {
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "display_name": "Trust Minute Certificate",
                "module_name": "Trust Minutes",
                "certificate_version": "1.0",
                "execution_id": minute_id,
            },
            "status": {
                "certification_status": status,
                "verification_status": verification.get("verification_status"),
                "lifecycle_status": status,
                "revocation_status": "active",
                "chain_status": "Current",
            },
            "governance": {
                "issuance_reason": "Trust Minute certificate generated from executed Trust Minute record.",
                "issuance_authority": minute.get("created_by") or minute.get("executed_by") or "Trust Minutes Engine",
                "generation_engine": "Trust Minute Certificate Adapter",
                "governance_policy": "Immutable",
                "retention_policy": "Permanent",
                "lifecycle_notes": "Trust Minute adapter object generated from existing trust_minutes record.",
            },
            "verification": verification,
            "chain": {
                "supersedes_certification_id": None,
                "superseded_by_certification_id": None,
                "supersedes": None,
                "superseded_by": None,
            },
            "timeline": {
                "event_count": 1,
                "events": [
                    {
                        "event_id": f"TMADAPT-{minute_id}",
                        "event_type": "Adapter Object Built",
                        "event_status": status,
                        "event_reason": "Existing Trust Minute exposed through Universal Certificate Adapter.",
                        "event_authority": "Trust Minute Certificate Adapter",
                        "generation_engine": "Trust Minute Certificate Adapter",
                        "actor": minute.get("created_by") or "system",
                        "event_at": minute.get("executed_at") or minute.get("created_at") or minute.get("updated_at"),
                    }
                ],
            },
            "relationships": {
                "count": len(relationship_items),
                "items": relationship_items,
            },
            "policy": {
                "policy_id": None,
                "policy_name": "Immutable",
                "display_name": "Immutable Certificate",
                "policy_category": "Core",
                "description": "Trust Minute certificate is treated as immutable once executed/locked.",
                "allows_edit": False,
                "allows_delete": False,
                "allows_supersession": False,
                "allows_revocation": False,
                "requires_lifecycle_event": True,
                "requires_reason": True,
                "requires_authority": True,
                "retention_rule": "Permanent",
            },
            "capabilities": {
                "supports_lifecycle": True,
                "supports_timeline": True,
                "supports_chain": False,
                "supports_pdf": True,
                "supports_packet": True,
                "supports_supersession": False,
                "supports_relationships": True,
                "supports_provenance": True,
            },
            "payload": {
                "raw_record": minute,
            },
        }

    def pdf(self, certificate_id):
        return None

    def packet(self, certificate_id):
        return None




class TransferCertificateAdapter(CertificateAdapter):
    certificate_type = "Transfer"

    def issue(self, payload=None, authority=None):
        return {
            "supported": False,
            "message": "Transfer certificate issuance remains controlled by the existing Transfer execution workflow.",
            "certificate_type": self.certificate_type,
            "payload": payload or {},
            "authority": authority,
        }

    def get(self, certificate_id):
        from database.db import get_connection

        transfer_id = certificate_id.replace("CERT-TRF-", "TRF-") if certificate_id.startswith("CERT-TRF-") else certificate_id

        conn = get_connection()
        cur = conn.cursor()

        row = cur.execute("""
            SELECT *
            FROM transfer_records
            WHERE transfer_id = ?
               OR certificate_id = ?
        """, (transfer_id, certificate_id)).fetchone()

        conn.close()

        return dict(row) if row else None

    def verify(self, certificate_id):
        transfer = self.get(certificate_id)

        if not transfer:
            return {
                "verified": False,
                "verification_status": "not_found",
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "message": "Transfer record not found.",
            }

        return {
            "verified": True,
            "verification_status": "verified",
            "certificate_id": certificate_id,
            "certificate_type": self.certificate_type,
            "transfer_id": transfer.get("transfer_id"),
            "trust_id": transfer.get("trust_id"),
            "message": "Transfer record exists and is adapter-visible.",
        }

    def object(self, certificate_id):
        transfer = self.get(certificate_id)
        verification = self.verify(certificate_id)

        if not transfer:
            return {
                "found": False,
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "message": "Transfer record not found.",
            }

        transfer_id = transfer.get("transfer_id") or certificate_id
        trust_id = transfer.get("trust_id")
        asset_id = transfer.get("asset_id")
        status = transfer.get("status") or transfer.get("transfer_status") or "Recorded"
        title = transfer.get("asset_name") or transfer.get("title") or "Transfer Certificate"

        relationships = [{
            "relationship_id": f"TREL-{transfer_id}-TRANSFER",
            "certification_id": certificate_id,
            "certificate_type": self.certificate_type,
            "related_object_type": "transfer",
            "related_object_id": transfer_id,
            "relationship_type": "certifies",
            "relationship_label": title,
            "relationship_basis": "Transfer certificate adapter exposes the existing transfer record.",
            "relationship_status": "active",
        }]

        if trust_id:
            relationships.append({
                "relationship_id": f"TREL-{transfer_id}-TRUST",
                "certification_id": certificate_id,
                "certificate_type": self.certificate_type,
                "related_object_type": "trust",
                "related_object_id": trust_id,
                "relationship_type": "belongs_to",
                "relationship_label": f"Trust {trust_id}",
                "relationship_basis": "Transfer record is associated with this trust.",
                "relationship_status": "active",
            })

        if asset_id:
            relationships.append({
                "relationship_id": f"TREL-{transfer_id}-ASSET",
                "certification_id": certificate_id,
                "certificate_type": self.certificate_type,
                "related_object_type": "asset",
                "related_object_id": asset_id,
                "relationship_type": "transfers",
                "relationship_label": f"Asset {asset_id}",
                "relationship_basis": "Transfer record identifies this asset as the transfer subject.",
                "relationship_status": "active",
            })

        return {
            "found": True,
            "identity": {
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "display_name": "Transfer Certificate",
                "module_name": "Execution Transfers",
                "certificate_version": "1.0",
                "execution_id": transfer_id,
            },
            "status": {
                "certification_status": status,
                "verification_status": verification.get("verification_status"),
                "lifecycle_status": status,
                "revocation_status": "active",
                "chain_status": "Current",
            },
            "governance": {
                "issuance_reason": "Transfer certificate generated from existing transfer execution record.",
                "issuance_authority": transfer.get("created_by") or transfer.get("updated_by") or "Transfer Execution Engine",
                "generation_engine": "Transfer Certificate Adapter",
                "governance_policy": "Immutable",
                "retention_policy": "Permanent",
                "lifecycle_notes": "Transfer adapter object generated from existing transfer record.",
            },
            "verification": verification,
            "chain": {
                "supersedes_certification_id": None,
                "superseded_by_certification_id": None,
                "supersedes": None,
                "superseded_by": None,
            },
            "timeline": {
                "event_count": 1,
                "events": [{
                    "event_id": f"TRADAPT-{transfer_id}",
                    "event_type": "Adapter Object Built",
                    "event_status": status,
                    "event_reason": "Existing Transfer exposed through Universal Certificate Adapter.",
                    "event_authority": "Transfer Certificate Adapter",
                    "generation_engine": "Transfer Certificate Adapter",
                    "actor": transfer.get("created_by") or "system",
                    "event_at": transfer.get("updated_at") or transfer.get("created_at"),
                }],
            },
            "relationships": {
                "count": len(relationships),
                "items": relationships,
            },
            "policy": {
                "policy_id": None,
                "policy_name": "Immutable",
                "display_name": "Immutable Certificate",
                "policy_category": "Core",
                "description": "Transfer certificate is treated as immutable evidence of a transfer execution record.",
                "allows_edit": False,
                "allows_delete": False,
                "allows_supersession": False,
                "allows_revocation": False,
                "requires_lifecycle_event": True,
                "requires_reason": True,
                "requires_authority": True,
                "retention_rule": "Permanent",
            },
            "capabilities": {
                "supports_lifecycle": True,
                "supports_timeline": True,
                "supports_chain": False,
                "supports_pdf": True,
                "supports_packet": True,
                "supports_supersession": False,
                "supports_relationships": True,
                "supports_provenance": True,
            },
            "payload": {"raw_record": transfer},
        }

    def pdf(self, certificate_id):
        return None

    def packet(self, certificate_id):
        return None


class PlaceholderCertificateAdapter(CertificateAdapter):
    def __init__(self, certificate_type):
        self.certificate_type = certificate_type

    def issue(self, payload=None, authority=None):
        return {
            "supported": False,
            "message": f"{self.certificate_type} adapter is registered as placeholder only.",
            "certificate_type": self.certificate_type,
            "payload": payload or {},
            "authority": authority,
        }

    def verify(self, certificate_id):
        return {
            "verified": False,
            "verification_status": "unsupported",
            "certificate_id": certificate_id,
            "certificate_type": self.certificate_type,
        }

    def get(self, certificate_id):
        return None

    def object(self, certificate_id):
        return {
            "found": False,
            "certificate_id": certificate_id,
            "certificate_type": self.certificate_type,
        }

    def pdf(self, certificate_id):
        return None

    def packet(self, certificate_id):
        return None


CERTIFICATE_ADAPTERS = {
    "Continuity": ContinuityCertificateAdapter(),
    "Trust Minute": TrustMinuteCertificateAdapter(),
    "Transfer": TransferCertificateAdapter(),
    "Archive": PlaceholderCertificateAdapter("Archive"),
    "Property": PlaceholderCertificateAdapter("Property"),
    "Funding": PlaceholderCertificateAdapter("Funding"),
    "Governance": PlaceholderCertificateAdapter("Governance"),
    "Compliance": PlaceholderCertificateAdapter("Compliance"),
    "Certificate of Trust": PlaceholderCertificateAdapter("Certificate of Trust"),
    "Institution": PlaceholderCertificateAdapter("Institution"),
}


def get_certificate_adapter(certificate_type):
    return CERTIFICATE_ADAPTERS.get(certificate_type)


def list_certificate_adapters():
    return [
        {
            "certificate_type": key,
            "adapter_class": adapter.__class__.__name__,
            "implemented": not isinstance(adapter, PlaceholderCertificateAdapter),
            "supports_issue": not isinstance(adapter, PlaceholderCertificateAdapter),
        }
        for key, adapter in CERTIFICATE_ADAPTERS.items()
    ]


def certificate_adapter_status():
    rows = list_certificate_adapters()

    return {
        "interface": "Universal Certificate Adapter Interface",
        "status": "ready",
        "registered_adapters": len(rows),
        "implemented_adapters": len([r for r in rows if r["implemented"]]),
        "placeholder_adapters": len([r for r in rows if not r["implemented"]]),
        "adapters": rows,
    }
