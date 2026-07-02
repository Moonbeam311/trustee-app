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


DOCUMENT_ADAPTERS = {
    "Trust": TrustDocumentAdapter(),
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
