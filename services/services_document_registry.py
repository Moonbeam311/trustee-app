from services.services_document_adapters import list_document_adapter_objects
from services.services_document_object_model import build_document_object


DOCUMENT_TYPES = [
    {"document_type": "Trust", "module_name": "Trust Registry"},
    {"document_type": "Trust Minute", "module_name": "Trust Minutes"},
    {"document_type": "Certificate", "module_name": "Certificate Studio"},
    {"document_type": "Transfer", "module_name": "Execution Transfers"},
    {"document_type": "Property", "module_name": "Property / Archive"},
    {"document_type": "Funding", "module_name": "Funding"},
    {"document_type": "Governance", "module_name": "Governance"},
    {"document_type": "Compliance", "module_name": "Compliance"},
    {"document_type": "Certificate of Trust", "module_name": "Trust Output"},
    {"document_type": "Institution", "module_name": "Institution"},
    {"document_type": "Archive", "module_name": "Archive"},
]


def list_registered_document_types():
    return DOCUMENT_TYPES


def list_universal_document_objects():
    objects = []

    for row in DOCUMENT_TYPES:
        doc_type = row["document_type"]
        module = row["module_name"]

        objects.append(build_document_object(
            document_id=f"DOC-TYPE-{doc_type.upper().replace(' ', '-')}",
            document_type=doc_type,
            title=f"{doc_type} Document Class",
            module_name=module,
            source_record_type="document_type_registry",
            source_record_id=doc_type,
            status="registered",
            lifecycle_status="available",
            governance_policy="Controlled",
            retention_policy="Permanent",
            relationships=[],
            timeline=[{
                "event_id": f"DEVT-{doc_type.upper().replace(' ', '-')}",
                "event_type": "Document Type Registered",
                "event_status": "available",
                "event_reason": "Document type exposed through Universal Document Registry.",
                "actor": "system",
            }],
            verification={
                "verified": True,
                "verification_status": "registered",
            },
            payload={
                "registered_type": row,
            },
        ))

    return objects


def universal_document_registry_summary(objects=None):
    if objects is None:
        objects = list_universal_document_objects()
        objects.extend(list_document_adapter_objects())

    by_type = {}
    by_module = {}
    by_status = {}
    verified = 0

    for obj in objects:
        doc_type = obj["identity"]["document_type"]
        module = obj["identity"]["module_name"]
        status = obj["status"]["status"]

        by_type[doc_type] = by_type.get(doc_type, 0) + 1
        by_module[module] = by_module.get(module, 0) + 1
        by_status[status] = by_status.get(status, 0) + 1

        if obj["verification"].get("verified"):
            verified += 1

    return {
        "total": len(objects),
        "verified": verified,
        "by_type": by_type,
        "by_module": by_module,
        "by_status": by_status,
    }


class DocumentAPI:
    @staticmethod
    def registry():
        objects = list_universal_document_objects()
        objects.extend(list_document_adapter_objects())

        return {
            "summary": universal_document_registry_summary(objects),
            "objects": objects,
        }

    @staticmethod
    def object(document_id):
        for obj in list_universal_document_objects():
            if obj["identity"]["document_id"] == document_id:
                return obj

        return {
            "found": False,
            "document_id": document_id,
            "message": "Document object not found in Universal Document Registry.",
        }

    @staticmethod
    def search(query=None, document_type=None, module_name=None):
        objects = list_universal_document_objects()
        objects.extend(list_document_adapter_objects())

        if document_type:
            objects = [
                o for o in objects
                if o["identity"]["document_type"] == document_type
            ]

        if module_name:
            objects = [
                o for o in objects
                if o["identity"]["module_name"] == module_name
            ]

        if query:
            q = query.lower()
            objects = [
                o for o in objects
                if q in o["identity"]["document_id"].lower()
                or q in o["identity"]["document_type"].lower()
                or q in o["identity"]["title"].lower()
                or q in o["identity"]["module_name"].lower()
            ]

        return objects
