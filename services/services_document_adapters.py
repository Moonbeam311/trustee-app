from services.services_document_object_model import build_document_object


class DocumentAdapter:
    document_type = None

    def list_objects(self):
        return []


class TrustDocumentAdapter(DocumentAdapter):
    document_type = "Trust"

    def _trust_rows(self):
        from database.db import get_connection

        candidate_tables = ["trusts", "trust_records"]
        conn = get_connection()
        cur = conn.cursor()

        tables = {
            r["name"] if hasattr(r, "keys") else r[0]
            for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }

        rows = []

        for table in candidate_tables:
            if table not in tables:
                continue

            for row in cur.execute(f"SELECT * FROM {table}").fetchall():
                record = dict(row)
                record["_source_table"] = table
                rows.append(record)

        conn.close()
        return rows

    def list_objects(self):
        objects = []

        for trust in self._trust_rows():
            trust_id = trust.get("trust_id") or trust.get("id") or trust.get("record_id")
            if not trust_id:
                continue

            title = trust.get("trust_name") or trust.get("name") or trust.get("title") or f"Trust {trust_id}"
            status = trust.get("status") or trust.get("trust_status") or "recorded"

            objects.append(build_document_object(
                document_id=f"DOC-TRUST-{trust_id}",
                document_type="Trust",
                title=title,
                module_name="Trust Registry",
                source_record_type="trust",
                source_record_id=trust_id,
                status=status,
                lifecycle_status=status,
                governance_policy="Controlled",
                retention_policy="Permanent",
                relationships=[{
                    "relationship_id": f"DREL-{trust_id}-TRUST",
                    "related_object_type": "trust",
                    "related_object_id": trust_id,
                    "relationship_type": "represents",
                    "relationship_label": title,
                    "relationship_basis": "Trust document adapter exposes this trust record as a universal document object.",
                    "relationship_status": "active",
                }],
                timeline=[{
                    "event_id": f"DADAPT-TRUST-{trust_id}",
                    "event_type": "Trust Document Adapter Object Built",
                    "event_status": status,
                    "event_reason": "Existing trust record exposed through Universal Document Adapter.",
                    "actor": trust.get("created_by") or "system",
                }],
                verification={
                    "verified": True,
                    "verification_status": "adapter-visible",
                },
                payload={
                    "raw_record": trust,
                    "source_table": trust.get("_source_table"),
                },
            ))

        return objects





class TrustMinuteDocumentAdapter(DocumentAdapter):
    document_type = "Trust Minute"

    def _minute_rows(self):
        from database.db import get_connection

        candidate_tables = ["trust_minutes", "minutes", "trust_minute_records"]

        conn = get_connection()
        cur = conn.cursor()

        tables = {
            r["name"] if hasattr(r, "keys") else r[0]
            for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }

        rows = []

        for table in candidate_tables:
            if table not in tables:
                continue

            try:
                for row in cur.execute(f"SELECT * FROM {table}").fetchall():
                    record = dict(row)
                    record["_source_table"] = table
                    rows.append(record)
            except Exception:
                continue

        conn.close()
        return rows

    def list_objects(self):
        objects = []

        for minute in self._minute_rows():
            minute_id = (
                minute.get("minute_id")
                or minute.get("id")
                or minute.get("record_id")
            )

            if not minute_id:
                continue

            title = (
                minute.get("title")
                or minute.get("minute_title")
                or minute.get("subject")
                or f"Trust Minute {minute_id}"
            )

            status = (
                minute.get("status")
                or minute.get("minute_status")
                or minute.get("execution_status")
                or "recorded"
            )

            trust_id = minute.get("trust_id")

            relationships = [{
                "relationship_id": f"DREL-{minute_id}-MINUTE",
                "related_object_type": "trust_minute",
                "related_object_id": minute_id,
                "relationship_type": "represents",
                "relationship_label": title,
                "relationship_basis": "Trust Minute document adapter exposes this minute record as a universal document object.",
                "relationship_status": "active",
            }]

            if trust_id:
                relationships.append({
                    "relationship_id": f"DREL-{minute_id}-TRUST",
                    "related_object_type": "trust",
                    "related_object_id": trust_id,
                    "relationship_type": "belongs_to",
                    "relationship_label": f"Trust {trust_id}",
                    "relationship_basis": "Trust Minute record is associated with this trust.",
                    "relationship_status": "active",
                })

            objects.append(build_document_object(
                document_id=f"DOC-MIN-{minute_id}",
                document_type="Trust Minute",
                title=title,
                module_name="Trust Minutes",
                source_record_type="trust_minute",
                source_record_id=minute_id,
                status=status,
                lifecycle_status=status,
                governance_policy="Controlled",
                retention_policy="Permanent",
                relationships=relationships,
                timeline=[{
                    "event_id": f"DADAPT-MIN-{minute_id}",
                    "event_type": "Trust Minute Document Adapter Object Built",
                    "event_status": status,
                    "event_reason": "Existing trust minute record exposed through Universal Document Adapter.",
                    "actor": minute.get("created_by") or minute.get("actor") or "system",
                }],
                verification={
                    "verified": True,
                    "verification_status": "adapter-visible",
                },
                payload={
                    "raw_record": minute,
                    "source_table": minute.get("_source_table"),
                },
            ))

        return objects





class CertificateDocumentAdapter(DocumentAdapter):
    document_type = "Certificate"

    def list_objects(self):
        objects = []

        try:
            from services.services_certificate_api import CertificateAPI
            registry = CertificateAPI.registry()
            cert_objects = registry.get("objects", [])
        except Exception:
            cert_objects = []

        for cert in cert_objects:
            identity = cert.get("identity", {})
            status = cert.get("status", {})
            governance = cert.get("governance", {})
            verification = cert.get("verification", {})
            relationships_src = cert.get("relationships", {}).get("items", [])
            timeline_src = cert.get("timeline", {}).get("events", [])

            cert_id = identity.get("certificate_id")
            if not cert_id:
                continue

            cert_type = identity.get("certificate_type") or "Certificate"
            title = identity.get("display_name") or f"Certificate {cert_id}"
            module = identity.get("module_name") or "Certificate Studio"

            relationships = [{
                "relationship_id": f"DREL-{cert_id}-CERT",
                "related_object_type": "certificate",
                "related_object_id": cert_id,
                "relationship_type": "represents",
                "relationship_label": title,
                "relationship_basis": "Certificate document adapter exposes this certificate object as a universal document object.",
                "relationship_status": "active",
            }]

            for rel in relationships_src:
                relationships.append({
                    "relationship_id": f"DREL-{cert_id}-{rel.get('relationship_id')}",
                    "related_object_type": rel.get("related_object_type"),
                    "related_object_id": rel.get("related_object_id"),
                    "relationship_type": rel.get("relationship_type"),
                    "relationship_label": rel.get("relationship_label"),
                    "relationship_basis": rel.get("relationship_basis"),
                    "relationship_status": rel.get("relationship_status") or "active",
                })

            timeline = []

            if timeline_src:
                for event in timeline_src:
                    timeline.append({
                        "event_id": f"DADAPT-CERT-{event.get('event_id')}",
                        "event_type": event.get("event_type") or "Certificate Event",
                        "event_status": event.get("event_status") or status.get("lifecycle_status"),
                        "event_reason": event.get("event_reason") or "Certificate event exposed through document adapter.",
                        "actor": event.get("actor") or "system",
                    })
            else:
                timeline.append({
                    "event_id": f"DADAPT-CERT-{cert_id}",
                    "event_type": "Certificate Document Adapter Object Built",
                    "event_status": status.get("lifecycle_status") or status.get("certification_status") or "recorded",
                    "event_reason": "Existing certificate object exposed through Universal Document Adapter.",
                    "actor": governance.get("issuance_authority") or "system",
                })

            objects.append(build_document_object(
                document_id=f"DOC-CERT-{cert_id}",
                document_type="Certificate",
                title=title,
                module_name=module,
                source_record_type="certificate",
                source_record_id=cert_id,
                status=status.get("certification_status") or "Certified",
                lifecycle_status=status.get("lifecycle_status") or "Issued",
                governance_policy=governance.get("governance_policy") or "Immutable",
                retention_policy=governance.get("retention_policy") or "Permanent",
                relationships=relationships,
                timeline=timeline,
                verification={
                    "verified": bool(verification.get("verified")),
                    "verification_status": status.get("verification_status") or verification.get("verification_status") or "unknown",
                },
                payload={
                    "raw_certificate_object": cert,
                    "certificate_type": cert_type,
                },
            ))

        return objects


DOCUMENT_ADAPTERS = {
    "Trust": TrustDocumentAdapter(),
    "Trust Minute": TrustMinuteDocumentAdapter(),
    "Certificate": CertificateDocumentAdapter(),
}


def list_document_adapter_objects():
    objects = []
    for adapter in DOCUMENT_ADAPTERS.values():
        objects.extend(adapter.list_objects())
    return objects


def document_adapter_status():
    return {
        "interface": "Universal Document Adapter Interface",
        "status": "ready",
        "registered_adapters": len(DOCUMENT_ADAPTERS),
        "implemented_adapters": len(DOCUMENT_ADAPTERS),
        "adapters": [
            {
                "document_type": doc_type,
                "adapter_class": adapter.__class__.__name__,
                "implemented": True,
            }
            for doc_type, adapter in DOCUMENT_ADAPTERS.items()
        ],
    }
