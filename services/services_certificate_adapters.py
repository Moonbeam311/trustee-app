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




class ArchiveCertificateAdapter(CertificateAdapter):
    certificate_type = "Archive"

    def issue(self, payload=None, authority=None):
        return {
            "supported": False,
            "message": "Archive issuance remains controlled by the existing archive workflow.",
            "certificate_type": self.certificate_type,
            "payload": payload or {},
            "authority": authority,
        }

    def get(self, certificate_id):
        return None

    def verify(self, certificate_id):
        return {
            "verified": False,
            "verification_status": "not_found",
            "certificate_id": certificate_id,
            "certificate_type": self.certificate_type,
            "message": "Archive adapter installed; record discovery will be connected in the next pass.",
        }

    def object(self, certificate_id):
        return {
            "found": False,
            "certificate_id": certificate_id,
            "certificate_type": self.certificate_type,
            "message": "Archive adapter installed; no archive record resolved yet.",
        }

    def pdf(self, certificate_id):
        return None

    def packet(self, certificate_id):
        return None




class PropertyCertificateAdapter(CertificateAdapter):
    certificate_type = "Property"

    def issue(self, payload=None, authority=None):
        return {
            "supported": False,
            "message": "Property certificate issuance remains controlled by the existing property/archive workflow.",
            "certificate_type": self.certificate_type,
            "payload": payload or {},
            "authority": authority,
        }

    def get(self, certificate_id):
        from database.db import get_connection

        property_id = certificate_id.replace("CERT-PROP-", "PROP-") if certificate_id.startswith("CERT-PROP-") else certificate_id

        candidate_tables = ["properties", "property_records", "assets"]

        try:
            conn = get_connection()
            cur = conn.cursor()
            tables = {
                r["name"] if hasattr(r, "keys") else r[0]
                for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            }

            for table in candidate_tables:
                if table not in tables:
                    continue

                cols = [
                    r["name"] if hasattr(r, "keys") else r[1]
                    for r in cur.execute(f"PRAGMA table_info({table})").fetchall()
                ]

                checks = []
                params = []

                for col in ["property_id", "asset_id", "certificate_id", "id"]:
                    if col in cols:
                        checks.append(f"{col} = ?")
                        params.append(property_id)
                        checks.append(f"{col} = ?")
                        params.append(certificate_id)

                if not checks:
                    continue

                row = cur.execute(
                    f"SELECT * FROM {table} WHERE {' OR '.join(checks)} LIMIT 1",
                    params
                ).fetchone()

                if row:
                    record = dict(row)
                    record["_property_table"] = table
                    conn.close()
                    return record

            conn.close()
        except Exception:
            return None

        return None

    def verify(self, certificate_id):
        prop = self.get(certificate_id)

        if not prop:
            return {
                "verified": False,
                "verification_status": "not_found",
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "message": "Property record not found.",
            }

        return {
            "verified": True,
            "verification_status": "verified",
            "certificate_id": certificate_id,
            "certificate_type": self.certificate_type,
            "property_id": prop.get("property_id") or prop.get("asset_id") or prop.get("id"),
            "trust_id": prop.get("trust_id"),
            "source_table": prop.get("_property_table"),
            "message": "Property record exists and is adapter-visible.",
        }

    def object(self, certificate_id):
        prop = self.get(certificate_id)
        verification = self.verify(certificate_id)

        if not prop:
            return {
                "found": False,
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "message": "Property record not found.",
            }

        property_id = prop.get("property_id") or prop.get("asset_id") or prop.get("id") or certificate_id
        trust_id = prop.get("trust_id")
        title = prop.get("title") or prop.get("property_name") or prop.get("asset_name") or f"Property {property_id}"
        status = prop.get("status") or prop.get("property_status") or "Recorded"

        relationships = [{
            "relationship_id": f"PREL-{property_id}-PROPERTY",
            "certification_id": certificate_id,
            "certificate_type": self.certificate_type,
            "related_object_type": "property",
            "related_object_id": property_id,
            "relationship_type": "certifies",
            "relationship_label": title,
            "relationship_basis": "Property adapter exposes the existing property/asset record.",
            "relationship_status": "active",
        }]

        if trust_id:
            relationships.append({
                "relationship_id": f"PREL-{property_id}-TRUST",
                "certification_id": certificate_id,
                "certificate_type": self.certificate_type,
                "related_object_type": "trust",
                "related_object_id": trust_id,
                "relationship_type": "belongs_to",
                "relationship_label": f"Trust {trust_id}",
                "relationship_basis": "Property record is associated with this trust.",
                "relationship_status": "active",
            })

        return {
            "found": True,
            "identity": {
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "display_name": "Property Archive Certificate",
                "module_name": "Property / Archive",
                "certificate_version": "1.0",
                "execution_id": property_id,
            },
            "status": {
                "certification_status": status,
                "verification_status": verification.get("verification_status"),
                "lifecycle_status": status,
                "revocation_status": "active",
                "chain_status": "Current",
            },
            "governance": {
                "issuance_reason": "Property certificate generated from existing property or asset record.",
                "issuance_authority": prop.get("created_by") or prop.get("updated_by") or "Property Archive Engine",
                "generation_engine": "Property Certificate Adapter",
                "governance_policy": "Immutable",
                "retention_policy": "Permanent",
                "lifecycle_notes": "Property adapter object generated from existing property/archive data.",
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
                    "event_id": f"PRADAPT-{property_id}",
                    "event_type": "Adapter Object Built",
                    "event_status": status,
                    "event_reason": "Existing Property exposed through Universal Certificate Adapter.",
                    "event_authority": "Property Certificate Adapter",
                    "generation_engine": "Property Certificate Adapter",
                    "actor": prop.get("created_by") or "system",
                    "event_at": prop.get("updated_at") or prop.get("created_at"),
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
                "description": "Property certificate is treated as immutable evidence of property/archive record state.",
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
            "payload": {"raw_record": prop},
        }

    def pdf(self, certificate_id):
        return None

    def packet(self, certificate_id):
        return None




class FundingCertificateAdapter(CertificateAdapter):
    certificate_type = "Funding"

    def issue(self, payload=None, authority=None):
        return {
            "supported": False,
            "message": "Funding certificate issuance remains controlled by the existing funding or asset-transfer workflow.",
            "certificate_type": self.certificate_type,
            "payload": payload or {},
            "authority": authority,
        }

    def get(self, certificate_id):
        from database.db import get_connection

        funding_id = certificate_id.replace("CERT-FUND-", "FUND-") if certificate_id.startswith("CERT-FUND-") else certificate_id

        candidate_tables = [
            "funding_records",
            "trust_funding",
            "asset_funding",
            "transfer_records",
            "ledger_entries",
        ]

        try:
            conn = get_connection()
            cur = conn.cursor()

            tables = {
                r["name"] if hasattr(r, "keys") else r[0]
                for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            }

            for table in candidate_tables:
                if table not in tables:
                    continue

                cols = [
                    r["name"] if hasattr(r, "keys") else r[1]
                    for r in cur.execute(f"PRAGMA table_info({table})").fetchall()
                ]

                checks = []
                params = []

                for col in [
                    "funding_id",
                    "funding_record_id",
                    "certificate_id",
                    "transfer_id",
                    "ledger_id",
                    "entry_id",
                    "id",
                ]:
                    if col in cols:
                        checks.append(f"{col} = ?")
                        params.append(funding_id)
                        checks.append(f"{col} = ?")
                        params.append(certificate_id)

                if not checks:
                    continue

                row = cur.execute(
                    f"SELECT * FROM {table} WHERE {' OR '.join(checks)} LIMIT 1",
                    params
                ).fetchone()

                if row:
                    record = dict(row)
                    record["_funding_table"] = table
                    conn.close()
                    return record

            conn.close()
        except Exception:
            return None

        return None

    def verify(self, certificate_id):
        funding = self.get(certificate_id)

        if not funding:
            return {
                "verified": False,
                "verification_status": "not_found",
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "message": "Funding record not found.",
            }

        return {
            "verified": True,
            "verification_status": "verified",
            "certificate_id": certificate_id,
            "certificate_type": self.certificate_type,
            "funding_id": (
                funding.get("funding_id")
                or funding.get("funding_record_id")
                or funding.get("transfer_id")
                or funding.get("ledger_id")
                or funding.get("entry_id")
                or funding.get("id")
            ),
            "trust_id": funding.get("trust_id"),
            "source_table": funding.get("_funding_table"),
            "message": "Funding record exists and is adapter-visible.",
        }

    def object(self, certificate_id):
        funding = self.get(certificate_id)
        verification = self.verify(certificate_id)

        if not funding:
            return {
                "found": False,
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "message": "Funding record not found.",
            }

        funding_id = (
            funding.get("funding_id")
            or funding.get("funding_record_id")
            or funding.get("transfer_id")
            or funding.get("ledger_id")
            or funding.get("entry_id")
            or funding.get("id")
            or certificate_id
        )

        trust_id = funding.get("trust_id")
        asset_id = funding.get("asset_id") or funding.get("property_id")
        amount = funding.get("amount") or funding.get("value") or funding.get("funding_amount")
        status = funding.get("status") or funding.get("funding_status") or "Recorded"
        title = funding.get("title") or funding.get("description") or f"Funding Record {funding_id}"

        relationships = [{
            "relationship_id": f"FREL-{funding_id}-FUNDING",
            "certification_id": certificate_id,
            "certificate_type": self.certificate_type,
            "related_object_type": "funding_record",
            "related_object_id": funding_id,
            "relationship_type": "certifies",
            "relationship_label": title,
            "relationship_basis": "Funding adapter exposes the existing funding-related record.",
            "relationship_status": "active",
        }]

        if trust_id:
            relationships.append({
                "relationship_id": f"FREL-{funding_id}-TRUST",
                "certification_id": certificate_id,
                "certificate_type": self.certificate_type,
                "related_object_type": "trust",
                "related_object_id": trust_id,
                "relationship_type": "funds",
                "relationship_label": f"Trust {trust_id}",
                "relationship_basis": "Funding record is associated with this trust.",
                "relationship_status": "active",
            })

        if asset_id:
            relationships.append({
                "relationship_id": f"FREL-{funding_id}-ASSET",
                "certification_id": certificate_id,
                "certificate_type": self.certificate_type,
                "related_object_type": "asset",
                "related_object_id": asset_id,
                "relationship_type": "funds_with",
                "relationship_label": f"Asset {asset_id}",
                "relationship_basis": "Funding record references this asset/property.",
                "relationship_status": "active",
            })

        return {
            "found": True,
            "identity": {
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "display_name": "Funding Certificate",
                "module_name": "Funding",
                "certificate_version": "1.0",
                "execution_id": funding_id,
            },
            "status": {
                "certification_status": status,
                "verification_status": verification.get("verification_status"),
                "lifecycle_status": status,
                "revocation_status": "active",
                "chain_status": "Current",
            },
            "governance": {
                "issuance_reason": "Funding certificate generated from existing funding-related record.",
                "issuance_authority": funding.get("created_by") or funding.get("updated_by") or "Funding Engine",
                "generation_engine": "Funding Certificate Adapter",
                "governance_policy": "Immutable",
                "retention_policy": "Permanent",
                "lifecycle_notes": f"Funding adapter object generated from {funding.get('_funding_table') or 'funding source'}.",
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
                    "event_id": f"FUADAPT-{funding_id}",
                    "event_type": "Adapter Object Built",
                    "event_status": status,
                    "event_reason": "Existing Funding exposed through Universal Certificate Adapter.",
                    "event_authority": "Funding Certificate Adapter",
                    "generation_engine": "Funding Certificate Adapter",
                    "actor": funding.get("created_by") or "system",
                    "event_at": funding.get("updated_at") or funding.get("created_at") or funding.get("date"),
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
                "description": "Funding certificate is treated as immutable evidence of trust or asset funding activity.",
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
                "amount": amount,
                "raw_record": funding,
            },
        }

    def pdf(self, certificate_id):
        return None

    def packet(self, certificate_id):
        return None




class GovernanceCertificateAdapter(CertificateAdapter):
    certificate_type = "Governance"

    def issue(self, payload=None, authority=None):
        return {
            "supported": False,
            "message": "Governance certificate issuance remains controlled by existing governance workflows.",
            "certificate_type": self.certificate_type,
            "payload": payload or {},
            "authority": authority,
        }

    def get(self, certificate_id):
        from database.db import get_connection

        governance_id = certificate_id.replace("CERT-GOV-", "GOV-") if certificate_id.startswith("CERT-GOV-") else certificate_id

        candidate_tables = [
            "governance_records",
            "governance_events",
            "matter_events",
            "certificate_policies",
            "matter_relationships",
        ]

        try:
            conn = get_connection()
            cur = conn.cursor()

            tables = {
                r["name"] if hasattr(r, "keys") else r[0]
                for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            }

            for table in candidate_tables:
                if table not in tables:
                    continue

                cols = [
                    r["name"] if hasattr(r, "keys") else r[1]
                    for r in cur.execute(f"PRAGMA table_info({table})").fetchall()
                ]

                checks = []
                params = []

                for col in [
                    "governance_id",
                    "governance_record_id",
                    "event_id",
                    "matter_event_id",
                    "relationship_id",
                    "policy_id",
                    "certificate_id",
                    "id",
                ]:
                    if col in cols:
                        checks.append(f"{col} = ?")
                        params.append(governance_id)
                        checks.append(f"{col} = ?")
                        params.append(certificate_id)

                if not checks:
                    continue

                row = cur.execute(
                    f"SELECT * FROM {table} WHERE {' OR '.join(checks)} LIMIT 1",
                    params
                ).fetchone()

                if row:
                    record = dict(row)
                    record["_governance_table"] = table
                    conn.close()
                    return record

            conn.close()
        except Exception:
            return None

        return None

    def verify(self, certificate_id):
        governance = self.get(certificate_id)

        if not governance:
            return {
                "verified": False,
                "verification_status": "not_found",
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "message": "Governance record not found.",
            }

        return {
            "verified": True,
            "verification_status": "verified",
            "certificate_id": certificate_id,
            "certificate_type": self.certificate_type,
            "governance_id": (
                governance.get("governance_id")
                or governance.get("governance_record_id")
                or governance.get("event_id")
                or governance.get("matter_event_id")
                or governance.get("relationship_id")
                or governance.get("policy_id")
                or governance.get("id")
            ),
            "matter_id": governance.get("matter_id"),
            "trust_id": governance.get("trust_id"),
            "source_table": governance.get("_governance_table"),
            "message": "Governance record exists and is adapter-visible.",
        }

    def object(self, certificate_id):
        governance = self.get(certificate_id)
        verification = self.verify(certificate_id)

        if not governance:
            return {
                "found": False,
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "message": "Governance record not found.",
            }

        governance_id = (
            governance.get("governance_id")
            or governance.get("governance_record_id")
            or governance.get("event_id")
            or governance.get("matter_event_id")
            or governance.get("relationship_id")
            or governance.get("policy_id")
            or governance.get("id")
            or certificate_id
        )

        matter_id = governance.get("matter_id")
        trust_id = governance.get("trust_id")
        policy_id = governance.get("policy_id")
        status = governance.get("status") or governance.get("event_status") or governance.get("relationship_status") or "Recorded"
        title = governance.get("title") or governance.get("event_type") or governance.get("policy_name") or f"Governance Record {governance_id}"

        relationships = [{
            "relationship_id": f"GREL-{governance_id}-GOV",
            "certification_id": certificate_id,
            "certificate_type": self.certificate_type,
            "related_object_type": "governance_record",
            "related_object_id": governance_id,
            "relationship_type": "certifies",
            "relationship_label": title,
            "relationship_basis": "Governance adapter exposes the existing governance-related record.",
            "relationship_status": "active",
        }]

        if matter_id:
            relationships.append({
                "relationship_id": f"GREL-{governance_id}-MATTER",
                "certification_id": certificate_id,
                "certificate_type": self.certificate_type,
                "related_object_type": "matter",
                "related_object_id": matter_id,
                "relationship_type": "governs",
                "relationship_label": f"Matter {matter_id}",
                "relationship_basis": "Governance record is associated with this matter.",
                "relationship_status": "active",
            })

        if trust_id:
            relationships.append({
                "relationship_id": f"GREL-{governance_id}-TRUST",
                "certification_id": certificate_id,
                "certificate_type": self.certificate_type,
                "related_object_type": "trust",
                "related_object_id": trust_id,
                "relationship_type": "governs",
                "relationship_label": f"Trust {trust_id}",
                "relationship_basis": "Governance record is associated with this trust.",
                "relationship_status": "active",
            })

        if policy_id:
            relationships.append({
                "relationship_id": f"GREL-{governance_id}-POLICY",
                "certification_id": certificate_id,
                "certificate_type": self.certificate_type,
                "related_object_type": "policy",
                "related_object_id": policy_id,
                "relationship_type": "applies_policy",
                "relationship_label": f"Policy {policy_id}",
                "relationship_basis": "Governance record references this policy.",
                "relationship_status": "active",
            })

        return {
            "found": True,
            "identity": {
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "display_name": "Governance Certificate",
                "module_name": "Governance",
                "certificate_version": "1.0",
                "execution_id": governance_id,
            },
            "status": {
                "certification_status": status,
                "verification_status": verification.get("verification_status"),
                "lifecycle_status": status,
                "revocation_status": "active",
                "chain_status": "Current",
            },
            "governance": {
                "issuance_reason": "Governance certificate generated from existing governance-related record.",
                "issuance_authority": governance.get("created_by") or governance.get("actor") or governance.get("authority") or "Governance Engine",
                "generation_engine": "Governance Certificate Adapter",
                "governance_policy": "Immutable",
                "retention_policy": "Permanent",
                "lifecycle_notes": f"Governance adapter object generated from {governance.get('_governance_table') or 'governance source'}.",
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
                    "event_id": f"GVADAPT-{governance_id}",
                    "event_type": "Adapter Object Built",
                    "event_status": status,
                    "event_reason": "Existing Governance record exposed through Universal Certificate Adapter.",
                    "event_authority": "Governance Certificate Adapter",
                    "generation_engine": "Governance Certificate Adapter",
                    "actor": governance.get("created_by") or governance.get("actor") or "system",
                    "event_at": governance.get("updated_at") or governance.get("created_at") or governance.get("event_at"),
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
                "description": "Governance certificate is treated as immutable evidence of governance state, policy, relationship, or event.",
                "allows_edit": False,
                "allows_delete": False,
                "allows_supersession": True,
                "allows_revocation": False,
                "requires_lifecycle_event": True,
                "requires_reason": True,
                "requires_authority": True,
                "retention_rule": "Permanent",
            },
            "capabilities": {
                "supports_lifecycle": True,
                "supports_timeline": True,
                "supports_chain": True,
                "supports_pdf": True,
                "supports_packet": True,
                "supports_supersession": True,
                "supports_relationships": True,
                "supports_provenance": True,
            },
            "payload": {
                "raw_record": governance,
            },
        }

    def pdf(self, certificate_id):
        return None

    def packet(self, certificate_id):
        return None




class ComplianceCertificateAdapter(CertificateAdapter):
    certificate_type = "Compliance"

    def issue(self, payload=None, authority=None):
        return {
            "supported": False,
            "message": "Compliance certificate issuance remains controlled by existing compliance, audit, or review workflows.",
            "certificate_type": self.certificate_type,
            "payload": payload or {},
            "authority": authority,
        }

    def get(self, certificate_id):
        from database.db import get_connection

        compliance_id = certificate_id.replace("CERT-COMP-", "COMP-") if certificate_id.startswith("CERT-COMP-") else certificate_id

        candidate_tables = [
            "compliance_records",
            "compliance_events",
            "compliance_reviews",
            "audit_log",
            "audit_events",
            "risk_assessments",
            "review_gate_records",
        ]

        try:
            conn = get_connection()
            cur = conn.cursor()

            tables = {
                r["name"] if hasattr(r, "keys") else r[0]
                for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            }

            for table in candidate_tables:
                if table not in tables:
                    continue

                cols = [
                    r["name"] if hasattr(r, "keys") else r[1]
                    for r in cur.execute(f"PRAGMA table_info({table})").fetchall()
                ]

                checks = []
                params = []

                for col in [
                    "compliance_id",
                    "compliance_record_id",
                    "review_id",
                    "audit_id",
                    "event_id",
                    "risk_id",
                    "gate_id",
                    "certificate_id",
                    "id",
                ]:
                    if col in cols:
                        checks.append(f"{col} = ?")
                        params.append(compliance_id)
                        checks.append(f"{col} = ?")
                        params.append(certificate_id)

                if not checks:
                    continue

                row = cur.execute(
                    f"SELECT * FROM {table} WHERE {' OR '.join(checks)} LIMIT 1",
                    params
                ).fetchone()

                if row:
                    record = dict(row)
                    record["_compliance_table"] = table
                    conn.close()
                    return record

            conn.close()
        except Exception:
            return None

        return None

    def verify(self, certificate_id):
        compliance = self.get(certificate_id)

        if not compliance:
            return {
                "verified": False,
                "verification_status": "not_found",
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "message": "Compliance record not found.",
            }

        return {
            "verified": True,
            "verification_status": "verified",
            "certificate_id": certificate_id,
            "certificate_type": self.certificate_type,
            "compliance_id": (
                compliance.get("compliance_id")
                or compliance.get("compliance_record_id")
                or compliance.get("review_id")
                or compliance.get("audit_id")
                or compliance.get("event_id")
                or compliance.get("risk_id")
                or compliance.get("gate_id")
                or compliance.get("id")
            ),
            "matter_id": compliance.get("matter_id"),
            "trust_id": compliance.get("trust_id"),
            "source_table": compliance.get("_compliance_table"),
            "message": "Compliance record exists and is adapter-visible.",
        }

    def object(self, certificate_id):
        compliance = self.get(certificate_id)
        verification = self.verify(certificate_id)

        if not compliance:
            return {
                "found": False,
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "message": "Compliance record not found.",
            }

        compliance_id = (
            compliance.get("compliance_id")
            or compliance.get("compliance_record_id")
            or compliance.get("review_id")
            or compliance.get("audit_id")
            or compliance.get("event_id")
            or compliance.get("risk_id")
            or compliance.get("gate_id")
            or compliance.get("id")
            or certificate_id
        )

        matter_id = compliance.get("matter_id")
        trust_id = compliance.get("trust_id")
        status = compliance.get("status") or compliance.get("review_status") or compliance.get("risk_level") or "Recorded"
        title = compliance.get("title") or compliance.get("event_type") or compliance.get("review_type") or f"Compliance Record {compliance_id}"

        relationships = [{
            "relationship_id": f"CREL-{compliance_id}-COMP",
            "certification_id": certificate_id,
            "certificate_type": self.certificate_type,
            "related_object_type": "compliance_record",
            "related_object_id": compliance_id,
            "relationship_type": "certifies",
            "relationship_label": title,
            "relationship_basis": "Compliance adapter exposes the existing compliance/audit/review record.",
            "relationship_status": "active",
        }]

        if matter_id:
            relationships.append({
                "relationship_id": f"CREL-{compliance_id}-MATTER",
                "certification_id": certificate_id,
                "certificate_type": self.certificate_type,
                "related_object_type": "matter",
                "related_object_id": matter_id,
                "relationship_type": "reviews",
                "relationship_label": f"Matter {matter_id}",
                "relationship_basis": "Compliance record is associated with this matter.",
                "relationship_status": "active",
            })

        if trust_id:
            relationships.append({
                "relationship_id": f"CREL-{compliance_id}-TRUST",
                "certification_id": certificate_id,
                "certificate_type": self.certificate_type,
                "related_object_type": "trust",
                "related_object_id": trust_id,
                "relationship_type": "reviews",
                "relationship_label": f"Trust {trust_id}",
                "relationship_basis": "Compliance record is associated with this trust.",
                "relationship_status": "active",
            })

        return {
            "found": True,
            "identity": {
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "display_name": "Compliance Certificate",
                "module_name": "Compliance",
                "certificate_version": "1.0",
                "execution_id": compliance_id,
            },
            "status": {
                "certification_status": status,
                "verification_status": verification.get("verification_status"),
                "lifecycle_status": status,
                "revocation_status": "active",
                "chain_status": "Current",
            },
            "governance": {
                "issuance_reason": "Compliance certificate generated from existing compliance, audit, risk, or review record.",
                "issuance_authority": compliance.get("created_by") or compliance.get("actor") or compliance.get("reviewed_by") or "Compliance Engine",
                "generation_engine": "Compliance Certificate Adapter",
                "governance_policy": "Immutable",
                "retention_policy": "Permanent",
                "lifecycle_notes": f"Compliance adapter object generated from {compliance.get('_compliance_table') or 'compliance source'}.",
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
                    "event_id": f"COADAPT-{compliance_id}",
                    "event_type": "Adapter Object Built",
                    "event_status": status,
                    "event_reason": "Existing Compliance record exposed through Universal Certificate Adapter.",
                    "event_authority": "Compliance Certificate Adapter",
                    "generation_engine": "Compliance Certificate Adapter",
                    "actor": compliance.get("created_by") or compliance.get("actor") or "system",
                    "event_at": compliance.get("updated_at") or compliance.get("created_at") or compliance.get("event_at"),
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
                "description": "Compliance certificate is treated as immutable evidence of review, audit, risk, or compliance posture.",
                "allows_edit": False,
                "allows_delete": False,
                "allows_supersession": True,
                "allows_revocation": False,
                "requires_lifecycle_event": True,
                "requires_reason": True,
                "requires_authority": True,
                "retention_rule": "Permanent",
            },
            "capabilities": {
                "supports_lifecycle": True,
                "supports_timeline": True,
                "supports_chain": True,
                "supports_pdf": True,
                "supports_packet": True,
                "supports_supersession": True,
                "supports_relationships": True,
                "supports_provenance": True,
            },
            "payload": {
                "raw_record": compliance,
            },
        }

    def pdf(self, certificate_id):
        return None

    def packet(self, certificate_id):
        return None




class CertificateOfTrustAdapter(CertificateAdapter):
    certificate_type = "Certificate of Trust"

    def issue(self, payload=None, authority=None):
        return {
            "supported": False,
            "message": "Certificate of Trust issuance remains controlled by the existing trust output workflow.",
            "certificate_type": self.certificate_type,
            "payload": payload or {},
            "authority": authority,
        }

    def get(self, certificate_id):
        from database.db import get_connection

        trust_id = certificate_id.replace("CERT-TRUST-", "TR-") if certificate_id.startswith("CERT-TRUST-") else certificate_id

        candidate_tables = [
            "trusts",
            "trust_records",
            "generated_documents",
            "document_exports",
        ]

        try:
            conn = get_connection()
            cur = conn.cursor()

            tables = {
                r["name"] if hasattr(r, "keys") else r[0]
                for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            }

            for table in candidate_tables:
                if table not in tables:
                    continue

                cols = [
                    r["name"] if hasattr(r, "keys") else r[1]
                    for r in cur.execute(f"PRAGMA table_info({table})").fetchall()
                ]

                checks = []
                params = []

                for col in [
                    "trust_id",
                    "certificate_id",
                    "document_id",
                    "export_id",
                    "id",
                ]:
                    if col in cols:
                        checks.append(f"{col} = ?")
                        params.append(trust_id)
                        checks.append(f"{col} = ?")
                        params.append(certificate_id)

                if "document_type" in cols:
                    checks.append("document_type = ?")
                    params.append("Certificate of Trust")

                if not checks:
                    continue

                row = cur.execute(
                    f"SELECT * FROM {table} WHERE {' OR '.join(checks)} LIMIT 1",
                    params
                ).fetchone()

                if row:
                    record = dict(row)
                    record["_certificate_of_trust_table"] = table
                    conn.close()
                    return record

            conn.close()
        except Exception:
            return None

        return None

    def verify(self, certificate_id):
        record = self.get(certificate_id)

        if not record:
            return {
                "verified": False,
                "verification_status": "not_found",
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "message": "Certificate of Trust source record not found.",
            }

        return {
            "verified": True,
            "verification_status": "verified",
            "certificate_id": certificate_id,
            "certificate_type": self.certificate_type,
            "trust_id": record.get("trust_id"),
            "document_id": record.get("document_id"),
            "source_table": record.get("_certificate_of_trust_table"),
            "message": "Certificate of Trust source record exists and is adapter-visible.",
        }

    def object(self, certificate_id):
        record = self.get(certificate_id)
        verification = self.verify(certificate_id)

        if not record:
            return {
                "found": False,
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "message": "Certificate of Trust source record not found.",
            }

        trust_id = record.get("trust_id") or certificate_id
        document_id = record.get("document_id") or record.get("export_id") or f"COT-{trust_id}"
        title = record.get("title") or record.get("trust_name") or record.get("name") or "Certificate of Trust"
        status = record.get("status") or record.get("document_status") or "Available"

        relationships = [{
            "relationship_id": f"COTREL-{document_id}-DOC",
            "certification_id": certificate_id,
            "certificate_type": self.certificate_type,
            "related_object_type": "document",
            "related_object_id": document_id,
            "relationship_type": "certifies",
            "relationship_label": title,
            "relationship_basis": "Certificate of Trust adapter exposes an existing trust output/source record.",
            "relationship_status": "active",
        }]

        if trust_id:
            relationships.append({
                "relationship_id": f"COTREL-{document_id}-TRUST",
                "certification_id": certificate_id,
                "certificate_type": self.certificate_type,
                "related_object_type": "trust",
                "related_object_id": trust_id,
                "relationship_type": "summarizes",
                "relationship_label": f"Trust {trust_id}",
                "relationship_basis": "Certificate of Trust summarizes the trust record.",
                "relationship_status": "active",
            })

        return {
            "found": True,
            "identity": {
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "display_name": "Certificate of Trust",
                "module_name": "Trust Output",
                "certificate_version": "1.0",
                "execution_id": document_id,
            },
            "status": {
                "certification_status": status,
                "verification_status": verification.get("verification_status"),
                "lifecycle_status": status,
                "revocation_status": "active",
                "chain_status": "Current",
            },
            "governance": {
                "issuance_reason": "Certificate of Trust generated from existing trust output record.",
                "issuance_authority": record.get("created_by") or record.get("updated_by") or "Trust Output Engine",
                "generation_engine": "Certificate of Trust Adapter",
                "governance_policy": "Immutable",
                "retention_policy": "Permanent",
                "lifecycle_notes": f"Certificate of Trust adapter object generated from {record.get('_certificate_of_trust_table') or 'trust output source'}.",
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
                    "event_id": f"COTADAPT-{document_id}",
                    "event_type": "Adapter Object Built",
                    "event_status": status,
                    "event_reason": "Existing Certificate of Trust output exposed through Universal Certificate Adapter.",
                    "event_authority": "Certificate of Trust Adapter",
                    "generation_engine": "Certificate of Trust Adapter",
                    "actor": record.get("created_by") or "system",
                    "event_at": record.get("updated_at") or record.get("created_at"),
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
                "description": "Certificate of Trust is treated as immutable evidence summarizing selected trust facts.",
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
                "raw_record": record,
            },
        }

    def pdf(self, certificate_id):
        return None

    def packet(self, certificate_id):
        return None




class InstitutionCertificateAdapter(CertificateAdapter):
    certificate_type = "Institution"

    def issue(self, payload=None, authority=None):
        return {
            "supported": False,
            "message": "Institution certificate issuance remains controlled by existing institution / IOS governance workflow.",
            "certificate_type": self.certificate_type,
            "payload": payload or {},
            "authority": authority,
        }

    def get(self, certificate_id):
        if certificate_id in ("IOS", "INST-IOS", "CERT-INST-IOS"):
            return {
                "institution_id": "IOS",
                "institution_name": "Institutional Operating System",
                "status": "active",
                "_institution_table": "virtual_institution",
            }
        return None

    def verify(self, certificate_id):
        institution = self.get(certificate_id)

        if not institution:
            return {
                "verified": False,
                "verification_status": "not_found",
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "message": "Institution record not found.",
            }

        return {
            "verified": True,
            "verification_status": "verified",
            "certificate_id": certificate_id,
            "certificate_type": self.certificate_type,
            "institution_id": institution.get("institution_id"),
            "source_table": institution.get("_institution_table"),
            "message": "Institution record exists and is adapter-visible.",
        }

    def object(self, certificate_id):
        institution = self.get(certificate_id)
        verification = self.verify(certificate_id)

        if not institution:
            return {
                "found": False,
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "message": "Institution record not found.",
            }

        institution_id = institution.get("institution_id") or certificate_id
        title = institution.get("institution_name") or f"Institution {institution_id}"
        status = institution.get("status") or "active"

        return {
            "found": True,
            "identity": {
                "certificate_id": certificate_id,
                "certificate_type": self.certificate_type,
                "display_name": "Institutional Certificate",
                "module_name": "Institution",
                "certificate_version": "1.0",
                "execution_id": institution_id,
            },
            "status": {
                "certification_status": str(status),
                "verification_status": verification.get("verification_status"),
                "lifecycle_status": str(status),
                "revocation_status": "active",
                "chain_status": "Current",
            },
            "governance": {
                "issuance_reason": "Institution certificate generated from institutional framework record.",
                "issuance_authority": "Institutional Governance Engine",
                "generation_engine": "Institution Certificate Adapter",
                "governance_policy": "Immutable",
                "retention_policy": "Permanent",
                "lifecycle_notes": "Institution adapter object generated from IOS institutional framework.",
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
                    "event_id": f"IDADAPT-{institution_id}",
                    "event_type": "Adapter Object Built",
                    "event_status": str(status),
                    "event_reason": "Institution exposed through Universal Certificate Adapter.",
                    "event_authority": "Institution Certificate Adapter",
                    "generation_engine": "Institution Certificate Adapter",
                    "actor": "system",
                    "event_at": None,
                }],
            },
            "relationships": {
                "count": 1,
                "items": [{
                    "relationship_id": f"IREL-{institution_id}-INSTITUTION",
                    "certification_id": certificate_id,
                    "certificate_type": self.certificate_type,
                    "related_object_type": "institution",
                    "related_object_id": institution_id,
                    "relationship_type": "certifies",
                    "relationship_label": title,
                    "relationship_basis": "Institution adapter exposes the institutional framework record.",
                    "relationship_status": "active",
                }],
            },
            "policy": {
                "policy_id": None,
                "policy_name": "Immutable",
                "display_name": "Immutable Certificate",
                "policy_category": "Core",
                "description": "Institution certificate is treated as immutable evidence of institutional identity or authority.",
                "allows_edit": False,
                "allows_delete": False,
                "allows_supersession": True,
                "allows_revocation": False,
                "requires_lifecycle_event": True,
                "requires_reason": True,
                "requires_authority": True,
                "retention_rule": "Permanent",
            },
            "capabilities": {
                "supports_lifecycle": True,
                "supports_timeline": True,
                "supports_chain": True,
                "supports_pdf": True,
                "supports_packet": True,
                "supports_supersession": True,
                "supports_relationships": True,
                "supports_provenance": True,
            },
            "payload": {
                "raw_record": institution,
            },
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
    "Archive": ArchiveCertificateAdapter(),
    "Property": PropertyCertificateAdapter(),
    "Funding": FundingCertificateAdapter(),
    "Governance": GovernanceCertificateAdapter(),
    "Compliance": ComplianceCertificateAdapter(),
    "Certificate of Trust": CertificateOfTrustAdapter(),
    "Institution": InstitutionCertificateAdapter(),
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
