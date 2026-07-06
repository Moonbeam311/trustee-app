"""
RC2-0D2 — Institutional Identity Propagation Engine

Central service for deriving canonical institutional identity from parent records.
This module does not write database records by itself.
"""

CANONICAL_IDENTITY_FIELDS = [
    "institution_id",
    "firm_id",
    "trust_id",
    "matter_id",
    "transfer_id",
    "minute_id",
    "certificate_id",
    "archive_id",
    "handoff_id",
    "created_by",
    "created_at",
    "updated_by",
    "updated_at",
    "capacity",
    "status",
    "record_version",
]


def _safe_get(record, key, default=None):
    if record is None:
        return default

    if isinstance(record, dict):
        return record.get(key, default)

    try:
        return record[key]
    except Exception:
        return getattr(record, key, default)


def transfer_identity_context(transfer):
    """
    Build canonical identity from a transfer record.
    Accepts SQLAlchemy model, sqlite Row, or dict-like record.
    """
    finalized_capacity = _safe_get(transfer, "finalized_capacity")
    current_capacity = _safe_get(transfer, "current_capacity")
    capacity = finalized_capacity or current_capacity

    return {
        "firm_id": _safe_get(transfer, "firm_id"),
        "trust_id": _safe_get(transfer, "trust_id"),
        "matter_id": _safe_get(transfer, "matter_id"),
        "transfer_id": _safe_get(transfer, "transfer_id"),
        "created_by": _safe_get(transfer, "created_by"),
        "created_at": _safe_get(transfer, "created_at"),
        "updated_by": _safe_get(transfer, "finalized_by") or _safe_get(transfer, "updated_by"),
        "updated_at": _safe_get(transfer, "finalized_at") or _safe_get(transfer, "updated_at"),
        "capacity": capacity,
        "status": _safe_get(transfer, "status"),
        "record_version": _safe_get(transfer, "record_version") or "1.0",
    }


def child_identity_context(parent_context, child_type, overrides=None):
    """
    Derive child identity from a parent context and child record type.
    """
    overrides = overrides or {}

    context = {
        "firm_id": parent_context.get("firm_id"),
        "trust_id": parent_context.get("trust_id"),
        "matter_id": parent_context.get("matter_id"),
        "transfer_id": parent_context.get("transfer_id"),
        "created_by": parent_context.get("created_by"),
        "created_at": parent_context.get("created_at"),
        "updated_by": parent_context.get("updated_by"),
        "updated_at": parent_context.get("updated_at"),
        "capacity": parent_context.get("capacity"),
        "status": overrides.get("status"),
        "record_version": parent_context.get("record_version") or "1.0",
    }

    if child_type == "transfer_action":
        context["status"] = overrides.get("status", "recorded")
    elif child_type == "transfer_record":
        context["status"] = overrides.get("status", "generated")
    elif child_type == "ledger_entry":
        context["status"] = overrides.get("status", "posted")
    elif child_type == "trust_minute":
        context["status"] = overrides.get("status")
    elif child_type == "archive_handoff":
        context["status"] = overrides.get("archive_status") or overrides.get("status")
        context["handoff_id"] = overrides.get("handoff_id")
        context["certificate_id"] = overrides.get("certificate_id")
        context["minute_id"] = overrides.get("minute_id")
    elif child_type == "archive_export":
        context["status"] = overrides.get("status", "exported")
        context["handoff_id"] = overrides.get("handoff_id")
        context["certificate_id"] = overrides.get("certificate_id")
        context["minute_id"] = overrides.get("minute_id")

    context.update({k: v for k, v in overrides.items() if v not in (None, "")})
    return context


def apply_identity_defaults(target, context):
    """
    Return a copy of target with blank identity fields filled from context.
    Does not overwrite populated values.
    """
    result = dict(target or {})

    for field in CANONICAL_IDENTITY_FIELDS:
        if field not in result:
            result[field] = context.get(field)
        elif result.get(field) in (None, "") and context.get(field) not in (None, ""):
            result[field] = context[field]

    return result


def missing_identity_fields(record, required_fields):
    """
    Return required identity fields missing from record.
    """
    return [
        field for field in required_fields
        if _safe_get(record, field) in (None, "")
    ]
