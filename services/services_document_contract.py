"""Canonical producer/adapter contract for derived, transient document output."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any
import json
import re

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


def _text(value: Any) -> str:
    return str(value or "").strip()


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
