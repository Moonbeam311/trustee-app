"""Canonical producer/adapter contract for derived, transient document output."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any
import json
import re
import uuid
from datetime import datetime, timezone

import database.db as document_db
import services.services_trust_contract as trust_contract


AuthorizationCheck = Callable[[str], bool]
SUPPORTED_TRANSIENT_FORMATS = {"txt": "text/plain; charset=utf-8", "json": "application/json"}
PROHIBITED_KEYS = {
    "password", "password_value", "pin", "token", "access_token",
    "authentication_token", "recovery_code", "recovery_codes", "backup_code",
    "backup_codes", "secret_answer", "security_answer", "security_answers",
    "encryption_key", "private_key", "card_number", "cvv", "cvc",
}
SECRET_VALUE_PATTERN = re.compile(
    r"(?i)\b(password|passcode|recovery code|secret answer|private key)\s*[:=]"
)
TRUST_SOURCE_FIELDS = (
    "trust_id", "trust_name", "short_name", "jurisdiction", "effective_date",
    "trust_type", "trust_purpose", "settlor_name", "trustee_name",
    "successor_trustee_name", "beneficiary_name", "status", "firm_id",
)
DOCUMENT_REFERENCE_FIELDS = (
    "document_id", "trust_id", "property_id", "account_id",
    "document_category", "document_title", "notes", "original_filename",
    "stored_filename", "file_path", "firm_id",
)


class DocumentContractError(RuntimeError):
    """Raised when production or rendering cannot proceed safely."""


DOCUMENT_LEGAL_STATES = (
    "UNRESOLVED", "DRAFT_RECORDED", "EXECUTION_RECORDED",
    "EFFECTIVE_RECORDED", "SUPERSEDED_RECORDED", "REVOKED_RECORDED",
    "EXPIRED_RECORDED",
)
DOCUMENT_OBJECT_TYPES = ("DOCUMENT", "GENERATED_DOCUMENT")
DECISION_ORIGINS = ("SYSTEM_SUGGESTED", "OPERATOR_OR_FIDUCIARY", "PROFESSIONAL")
FINAL_DOCUMENT_LEGAL_STATES = {
    "EFFECTIVE_RECORDED", "SUPERSEDED_RECORDED", "REVOKED_RECORDED",
    "EXPIRED_RECORDED",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _legal_state_row(connection, event_id):
    row = connection.execute(
        "SELECT * FROM document_legal_state_events WHERE legal_state_event_id=?",
        (event_id,),
    ).fetchone()
    return dict(row) if row else None


def _canonical_document_scope(connection, object_type, object_id, firm_id, trust_id):
    if object_type not in DOCUMENT_OBJECT_TYPES:
        if object_type == "INSTRUMENT":
            raise DocumentContractError("INSTRUMENT is not a canonical document object type.")
        raise DocumentContractError("Unsupported document object type.")
    table = "documents" if object_type == "DOCUMENT" else "generated_documents"
    columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
    if not {"document_id", "trust_id"}.issubset(columns):
        raise DocumentContractError("Canonical document owner schema is unavailable.")
    row = connection.execute(
        f"SELECT * FROM {table} WHERE document_id=?", (object_id,)
    ).fetchone()
    if row is None:
        raise DocumentContractError("Canonical document object is unavailable in context.")
    data = dict(row)
    if _text(data.get("trust_id")) != trust_id:
        raise DocumentContractError("Canonical document object is unavailable in context.")
    if "firm_id" in columns:
        if _text(data.get("firm_id")) != firm_id:
            raise DocumentContractError("Canonical document object is unavailable in context.")
    else:
        trust = connection.execute(
            "SELECT firm_id FROM trusts WHERE trust_id=?", (trust_id,)
        ).fetchone()
        if trust is None or _text(trust["firm_id"]) != firm_id:
            raise DocumentContractError("Document firm scope cannot be established.")


def record_document_legal_state(
    *, firm_id, trust_id, document_object_type, document_object_id,
    legal_state, effective_at=None, basis=None, provenance=None,
    decision_origin, human_confirmed, actor, actor_capacity,
    prior_legal_state_event_id=None,
):
    """Append a recorded legal-state observation, not a legal-validity ruling."""
    firm_id, trust_id = _text(firm_id), _text(trust_id)
    object_type, object_id = _text(document_object_type).upper(), _text(document_object_id)
    actor, actor_capacity = _text(actor), _text(actor_capacity)
    if not all((firm_id, trust_id, object_id, actor, actor_capacity)):
        raise DocumentContractError("Document legal-state scope and actor are required.")
    if legal_state not in DOCUMENT_LEGAL_STATES:
        raise DocumentContractError("Unsupported document legal state.")
    if decision_origin not in DECISION_ORIGINS:
        raise DocumentContractError("Unsupported decision origin.")
    if decision_origin == "SYSTEM_SUGGESTED" and legal_state not in {"UNRESOLVED", "DRAFT_RECORDED"}:
        raise DocumentContractError("A machine suggestion cannot record substantive legal state.")
    if legal_state in FINAL_DOCUMENT_LEGAL_STATES:
        if decision_origin not in {"OPERATOR_OR_FIDUCIARY", "PROFESSIONAL"} or not human_confirmed:
            raise DocumentContractError("Final substantive state requires explicit human confirmation.")
        if not _text(basis) or not _text(provenance):
            raise DocumentContractError("Final substantive state requires basis and provenance.")
    connection = document_db.get_connection()
    try:
        _canonical_document_scope(connection, object_type, object_id, firm_id, trust_id)
        prior = _legal_state_row(connection, _text(prior_legal_state_event_id)) if prior_legal_state_event_id else None
        if prior_legal_state_event_id and (
            prior is None or any(prior[key] != value for key, value in (
                ("firm_id", firm_id), ("trust_id", trust_id),
                ("document_object_type", object_type), ("document_object_id", object_id),
            ))
        ):
            raise DocumentContractError("Predecessor is unavailable in document context.")
        if legal_state == "SUPERSEDED_RECORDED" and prior is None:
            raise DocumentContractError("Supersession requires a valid predecessor.")
        event_id = "DLS-" + uuid.uuid4().hex[:10].upper()
        connection.execute(
            """INSERT INTO document_legal_state_events
            (legal_state_event_id,firm_id,trust_id,document_object_type,document_object_id,
             legal_state,effective_at,basis,provenance,decision_origin,human_confirmed,
             actor,actor_capacity,prior_legal_state_event_id,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (event_id, firm_id, trust_id, object_type, object_id, legal_state,
             _text(effective_at) or None, _text(basis) or None, _text(provenance) or None,
             decision_origin, int(bool(human_confirmed)), actor, actor_capacity,
             _text(prior_legal_state_event_id) or None, datetime.now(timezone.utc).isoformat()),
        )
        connection.commit()
        return event_id
    finally:
        connection.close()


def get_document_legal_state_event(legal_state_event_id):
    connection = document_db.get_connection()
    try:
        return _legal_state_row(connection, _text(legal_state_event_id))
    finally:
        connection.close()


def get_document_legal_state_history(*, firm_id, trust_id, document_object_type, document_object_id):
    connection = document_db.get_connection()
    try:
        rows = connection.execute(
            """SELECT * FROM document_legal_state_events
               WHERE firm_id=? AND trust_id=? AND document_object_type=? AND document_object_id=?
               ORDER BY created_at, legal_state_event_id""",
            (_text(firm_id), _text(trust_id), _text(document_object_type).upper(), _text(document_object_id)),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def _assert_no_secret_material(value: Any, path: str = "context") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = _text(key).lower().replace("-", "_").replace(" ", "_")
            if normalized in PROHIBITED_KEYS:
                raise DocumentContractError(f"Secret field is prohibited at {path}.{key}.")
            _assert_no_secret_material(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _assert_no_secret_material(item, f"{path}[{index}]")
    elif isinstance(value, str) and SECRET_VALUE_PATTERN.search(value):
        raise DocumentContractError(f"Secret material is prohibited at {path}.")


def _require_document_schema() -> None:
    connection = document_db.get_connection()
    try:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='documents'"
        ).fetchone()
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(documents)").fetchall()
        }
    finally:
        connection.close()
    if exists is None or not {"document_id", "trust_id", "firm_id"}.issubset(columns):
        raise DocumentContractError(
            "Document references require an existing firm-scoped documents schema."
        )


def produce_trust_document_context(
    trust_id: Any,
    document_type: Any,
    *,
    authorization_check: AuthorizationCheck | None,
    generated_by: Any = None,
    generated_at: Any = None,
) -> dict[str, Any] | None:
    """Produce safe source context from one canonical, authorized Trust read."""
    source = trust_contract.get_trust_by_id(
        trust_id, authorization_check=authorization_check
    )
    if source is None:
        return None
    output_type = _text(document_type)
    if not output_type:
        raise DocumentContractError("A documented output type is required.")
    source_data = {field: source[field] if field in source.keys() else None for field in TRUST_SOURCE_FIELDS}
    missing_fields = [field for field, value in source_data.items() if value in (None, "")]
    context = {
        "contract_version": "V3-SVC-DOC-1",
        "document_type": output_type,
        "source": {
            "object_type": "trust",
            "object_id": _text(source["trust_id"]),
            "firm_id": source_data.get("firm_id"),
            "authoritative_record": True,
        },
        "source_data": source_data,
        "missing_optional_fields": missing_fields,
        "provenance": {
            "generated_by": _text(generated_by) or "NOT DOCUMENTED",
            "generated_at": _text(generated_at) or "NOT DOCUMENTED",
            "producer": "services.services_document_contract",
        },
        "output_state": {
            "derived_output": True,
            "persisted": False,
            "archived": False,
            "finality": "not_established",
        },
    }
    _assert_no_secret_material(context)
    return context


def _build_persistent_generated_document_attribution(
    trust_id: Any,
    *,
    authorization_check: AuthorizationCheck | None,
    generated_by: Any = None,
    firm_id: Any = None,
) -> dict[str, Any]:
    """Resolve attribution for the existing generated_documents lane.

    This function derives attribution only. It does not create, update,
    delete, finalize, archive, or otherwise mutate a generated-document row.
    """

    firm_id = _text(firm_id) or _text(document_db.get_current_firm_id())
    if not firm_id:
        raise DocumentContractError(
            "Generated-document firm scope is unavailable."
        )

    actor = _text(generated_by) or "NOT DOCUMENTED"
    source_id = _text(trust_id)

    if not source_id:
        attribution = {
            "firm_id": firm_id,
            "source_record_type": None,
            "source_record_id": None,
            "generation_basis": "SOURCE_ATTRIBUTION_NOT_ESTABLISHED",
            "generated_by": actor,
        }
        _assert_no_secret_material(attribution)
        return attribution

    if authorization_check is None:
        raise DocumentContractError(
            "An explicit Trust authorization check is required."
        )

    context = produce_trust_document_context(
        source_id,
        "persistent_generated_document",
        authorization_check=authorization_check,
        generated_by=actor,
    )

    if context is None:
        raise DocumentContractError(
            "Trust source is unavailable or not authorized."
        )

    source = context.get("source") or {}

    resolved_type = _text(source.get("object_type"))
    resolved_id = _text(source.get("object_id"))
    resolved_firm = _text(source.get("firm_id"))

    if (
        resolved_type != "trust"
        or resolved_id != source_id
        or not resolved_firm
        or resolved_firm != firm_id
    ):
        raise DocumentContractError(
            "Trust source is unavailable or not authorized."
        )

    attribution = {
        "firm_id": resolved_firm,
        "source_record_type": "trust",
        "source_record_id": resolved_id,
        "generation_basis": "CANONICAL_TRUST_CONTEXT",
        "generated_by": actor,
    }

    _assert_no_secret_material(attribution)
    return attribution


def describe_output_capabilities() -> dict[str, Any]:
    """Describe only formats implemented by this transient adapter boundary."""
    return {
        "transient_formats": dict(SUPPORTED_TRANSIENT_FORMATS),
        "persistent_rendering": False,
        "pdf": "legacy_generator_owned",
        "html": "legacy_route_template_owned",
        "csv": "producer_specific_not_documented",
        "zip": "packet_export_owned",
    }


def render_document(context: Mapping[str, Any], output_format: Any) -> bytes:
    """Render canonical context to transient UTF-8 TXT or JSON bytes."""
    if not isinstance(context, Mapping) or context.get("contract_version") != "V3-SVC-DOC-1":
        raise DocumentContractError("Canonical document context is required.")
    _assert_no_secret_material(context)
    format_name = _text(output_format).lower()
    if format_name not in SUPPORTED_TRANSIENT_FORMATS:
        raise DocumentContractError(f"Unsupported transient output format: {format_name or 'blank'}.")
    if format_name == "json":
        return json.dumps(context, sort_keys=True, ensure_ascii=False, indent=2).encode("utf-8")
    source = context.get("source") or {}
    data = context.get("source_data") or {}
    lines = [
        str(context.get("document_type") or ""),
        f"Source: {source.get('object_type') or ''} {source.get('object_id') or ''}",
        f"Trust Name: {data.get('trust_name') or ''}",
        f"Trust Type: {data.get('trust_type') or ''}",
        f"Status: {data.get('status') or ''}",
        "Derived Output: Yes",
        "Source Record Remains Authoritative: Yes",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_delivery_metadata(
    context: Mapping[str, Any], output_format: Any
) -> dict[str, str]:
    """Return safe transient response metadata without writing an export record."""
    format_name = _text(output_format).lower()
    if format_name not in SUPPORTED_TRANSIENT_FORMATS:
        raise DocumentContractError("Delivery metadata requires a supported format.")
    source_id = _text((context.get("source") or {}).get("object_id")) or "source"
    doc_type = _text(context.get("document_type")) or "document"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", f"{doc_type}-{source_id}").strip("-.") or "document"
    return {
        "filename": f"{stem}.{format_name}",
        "content_type": SUPPORTED_TRANSIENT_FORMATS[format_name],
        "content_disposition": f'attachment; filename="{stem}.{format_name}"',
        "persistence": "none",
    }


def list_document_references(
    trust_id: Any, *, authorization_check: AuthorizationCheck | None
) -> list[dict[str, Any]]:
    """List persisted metadata references without rendering or creating output."""
    trust = trust_contract.get_trust_by_id(trust_id, authorization_check=authorization_check)
    if trust is None:
        return []
    _require_document_schema()
    connection = document_db.get_connection()
    try:
        rows = connection.execute(
            "SELECT * FROM documents WHERE trust_id=? AND firm_id=? ORDER BY document_id",
            (_text(trust_id), document_db.get_current_firm_id()),
        ).fetchall()
    finally:
        connection.close()
    return [
        {**{field: dict(row).get(field) for field in DOCUMENT_REFERENCE_FIELDS}, "source": "documents"}
        for row in rows
    ]


def get_document_reference(
    document_id: Any,
    trust_id: Any,
    *,
    authorization_check: AuthorizationCheck | None,
) -> dict[str, Any] | None:
    """Return one persisted metadata reference in exact firm/Trust scope."""
    record_id = _text(document_id)
    if not record_id or trust_contract.get_trust_by_id(
        trust_id, authorization_check=authorization_check
    ) is None:
        return None
    _require_document_schema()
    connection = document_db.get_connection()
    try:
        row = connection.execute(
            """SELECT * FROM documents
               WHERE document_id=? AND trust_id=? AND firm_id=?""",
            (record_id, _text(trust_id), document_db.get_current_firm_id()),
        ).fetchone()
    finally:
        connection.close()
    return (
        {**{field: dict(row).get(field) for field in DOCUMENT_REFERENCE_FIELDS}, "source": "documents"}
        if row else None
    )
