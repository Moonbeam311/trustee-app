from datetime import datetime, UTC
import hashlib
import json
import re

from database.db import get_connection
from models.models_compliance_reviews import (
    COMPLIANCE_REQUIREMENT_TYPES,
    COMPLIANCE_REVIEW_PRIORITIES,
    COMPLIANCE_REVIEW_RISK_LEVELS,
    COMPLIANCE_REVIEW_TRANSITIONS,
    COMPLIANCE_REVIEW_TYPES,
    COMPLIANCE_SOURCE_TYPES,
    INTERNAL_COMPLIANCE_REQUIREMENT_TYPES,
    OPEN_COMPLIANCE_REVIEW_STATES,
    RESERVED_COMPLIANCE_REVIEW_ACTIONS,
)


SUMMARY_LIMIT = 1000
SCALAR_LIMIT = 255
ID_LIMIT = 120
IDEMPOTENCY_LIMIT = 160
PUBLIC_REVIEW_ID_RE = re.compile(r"^CMP-\d{4}-\d{4}$")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,119}$")
SENSITIVE_MARKERS = {
    "password",
    "password_hash",
    "credential",
    "token",
    "cookie",
    "session id",
    "connection string",
    "private key",
    "secret",
    "bootstrap credential",
}
PROHIBITED_CREATE_FIELDS = {
    "approved_by",
    "approved_at",
    "finding",
    "disposition",
    "disposition_basis",
    "required_follow_up",
    "completed_at",
    "version",
    "status",
}
PROHIBITED_TRANSITION_FIELDS = {
    "target_status",
    "resulting_status",
    "event_type",
    "approved_by",
    "approved_at",
    "finding",
    "disposition",
    "disposition_basis",
    "required_follow_up",
    "completed_at",
    "superseded_by_id",
}
READ_LIMIT_MAX = 250
REQUIRED_READ_TABLES = {
    "compliance_reviews",
    "compliance_review_events",
    "compliance_review_relationships",
}
ACTIVATION_TABLE = "compliance_review_activation_registry"
H6C_IDENTIFIER_WIDTH = 6
IDENTIFIER_NAMESPACES = {
    "review": "CMP",
    "evidence": "CEV",
    "finding": "CFN",
    "remediation": "CRM",
    "approval": "CAP",
    "certification": "CCT",
    "relationship": "CRL",
    "audit": "CAL",
    "activation": "CAR",
}
H6C_TRANSITIONS = {
    ("draft", "open"): ("opened", "compliance_review_opened"),
    ("opened", "start_review"): ("under_review", "compliance_review_started"),
    ("under_review", "issue_findings"): ("findings_issued", "compliance_findings_issued"),
    ("findings_issued", "require_remediation"): ("remediation_required", "compliance_remediation_required"),
    ("remediation_required", "start_remediation"): ("remediation_in_progress", "compliance_remediation_started"),
    ("remediation_in_progress", "submit_for_verification"): ("pending_verification", "compliance_remediation_submitted"),
    ("pending_verification", "submit_for_approval"): ("pending_approval", "compliance_review_submitted_for_approval"),
    ("pending_approval", "approve"): ("approved", "compliance_review_approved"),
    ("approved", "certify"): ("certified", "compliance_review_certified"),
    ("certified", "close"): ("closed", "compliance_review_closed"),
    ("closed", "reopen"): ("reopened", "compliance_review_reopened"),
    ("reopened", "start_review"): ("under_review", "compliance_review_reopened_review_started"),
    ("closed", "archive"): ("archived", "compliance_review_archived"),
    ("draft", "supersede"): ("superseded", "compliance_review_superseded"),
    ("opened", "supersede"): ("superseded", "compliance_review_superseded"),
    ("under_review", "supersede"): ("superseded", "compliance_review_superseded"),
    ("findings_issued", "supersede"): ("superseded", "compliance_review_superseded"),
    ("remediation_required", "supersede"): ("superseded", "compliance_review_superseded"),
    ("remediation_in_progress", "supersede"): ("superseded", "compliance_review_superseded"),
    ("pending_verification", "supersede"): ("superseded", "compliance_review_superseded"),
    ("pending_approval", "supersede"): ("superseded", "compliance_review_superseded"),
    ("approved", "supersede"): ("superseded", "compliance_review_superseded"),
    ("certified", "supersede"): ("superseded", "compliance_review_superseded"),
}
H6C_TERMINAL_STATES = {"archived", "superseded", "cancelled"}
H6C_ACTION_AUTHORITIES = {
    "create": "create_review",
    "update": "edit_draft",
    "assign_reviewer": "assign_reviewer",
    "add_subject": "add_subject",
    "add_relationship": "add_relationship",
    "add_evidence": "add_evidence",
    "verify_evidence": "verify_evidence",
    "issue_finding": "issue_findings",
    "acknowledge_finding": "acknowledge_findings",
    "assign_remediation": "assign_remediation",
    "submit_remediation": "submit_remediation",
    "verify_remediation": "verify_remediation",
    "request_exception": "request_exception",
    "approve_exception": "approve_exception",
    "submit_approval": "approve_review",
    "approve_review": "approve_review",
    "certify_review": "certify_review",
    "close_review": "close_review",
    "reopen_review": "reopen_review",
    "supersede_review": "supersede_review",
    "archive_review": "archive_review",
    "open": "open_review",
    "start_review": "open_review",
    "issue_findings": "issue_findings",
    "require_remediation": "assign_remediation",
    "start_remediation": "assign_remediation",
    "submit_for_verification": "submit_remediation",
    "submit_for_approval": "approve_review",
    "approve": "approve_review",
    "certify": "certify_review",
    "close": "close_review",
    "reopen": "reopen_review",
    "supersede": "supersede_review",
    "archive": "archive_review",
}
FOUNDATION_UNAVAILABLE_MESSAGE = (
    "Compliance Review persistence is not currently available because the "
    "institutional foundation for this registry has not been activated. "
    "No review record was created, no migration occurred, and changing "
    "operator permissions will not activate the registry. Authorized "
    "institutional activation is required."
)
PUBLIC_REVIEW_FIELDS = (
    "compliance_review_id", "firm_id", "institution_id", "trust_id", "matter_id",
    "deployment_key", "title", "review_type", "question_presented",
    "governing_requirement_type", "governing_requirement_id",
    "governing_requirement_label", "source_type", "source_id", "source_label",
    "scope_summary", "status", "priority", "risk_level", "review_owner",
    "assigned_to", "authority_basis", "approval_required", "opened_at", "due_at",
    "completed_at", "created_by", "created_at", "updated_by", "updated_at", "version",
)
PUBLIC_EVENT_FIELDS = (
    "event_id", "compliance_review_id", "event_sequence", "event_type", "actor_id",
    "actor_label", "prior_status", "resulting_status", "summary", "reason",
    "related_record_type", "related_record_id", "expected_version", "created_at",
)
PUBLIC_RELATIONSHIP_FIELDS = (
    "relationship_id", "compliance_review_id", "relationship_type",
    "related_record_type", "related_record_id", "direction", "status", "created_by",
    "created_at",
)


def _now():
    return datetime.now(UTC).isoformat(timespec="seconds")


def _result(ok, status, message="", review=None, event=None, events=None):
    data = {"ok": bool(ok), "status": status}
    if message:
        data["message"] = message
    if review is not None:
        data["review"] = review
    if event is not None:
        data["event"] = event
    if events is not None:
        data["events"] = events
    return data


def _scalar(value, field, required=False, max_length=SCALAR_LIMIT, lowercase=False):
    if value is None:
        if required:
            raise ValueError(f"{field}_required")
        return None
    if isinstance(value, (list, tuple, dict, set)):
        raise ValueError(f"{field}_invalid")
    text = str(value).strip()
    if not text:
        if required:
            raise ValueError(f"{field}_required")
        return None
    if "\x00" in text or "<" in text or ">" in text:
        raise ValueError(f"{field}_invalid")
    if len(text) > max_length:
        raise ValueError(f"{field}_too_long")
    if lowercase:
        text = text.lower()
    return text


def _summary(value, field, required=False):
    text = _scalar(value, field, required=required, max_length=SUMMARY_LIMIT)
    if text is None:
        return ""
    lowered = text.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        raise ValueError(f"{field}_sensitive")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _safe_id(value, field, required=False):
    text = _scalar(value, field, required=required, max_length=ID_LIMIT)
    if text is None:
        return None
    if not SAFE_ID_RE.fullmatch(text):
        raise ValueError(f"{field}_invalid")
    blocked = ("://", "/", "\\", "?", "#", "--", ";", "'", '"')
    if any(marker in text for marker in blocked):
        raise ValueError(f"{field}_invalid")
    return text


def _choice(value, field, choices, required=True):
    text = _scalar(value, field, required=required, max_length=80, lowercase=True)
    if text is None:
        return None
    text = text.replace(" ", "_")
    if text not in choices:
        raise ValueError(f"{field}_invalid")
    return text


def _actor(actor_context):
    actor_context = actor_context or {}
    actor_id = _scalar(
        actor_context.get("actor_id") or actor_context.get("username"),
        "actor_id",
        required=True,
        max_length=255,
    )
    actor_label = _scalar(
        actor_context.get("actor_label") or actor_context.get("display_name") or actor_id,
        "actor_label",
        required=True,
        max_length=255,
    )
    return actor_id, actor_label


def _actor_scope(actor_context):
    actor_context = actor_context or {}
    scope = actor_context.get("scope") or {}
    return {
        "global": bool(scope.get("global") or actor_context.get("global")),
        "firm_id": scope.get("firm_id") or actor_context.get("firm_id"),
    }


def _actor_can_access_firm(actor_context, firm_id):
    scope = _actor_scope(actor_context)
    return bool(scope["global"] or (firm_id and scope["firm_id"] and firm_id == scope["firm_id"]))


def _actor_authorities(actor_context):
    actor_context = actor_context or {}
    values = actor_context.get("authorities") or actor_context.get("permissions") or ()
    if isinstance(values, str):
        values = {values}
    return {str(value).strip() for value in values if str(value).strip()}


def _actor_has_authority(actor_context, action):
    required = H6C_ACTION_AUTHORITIES.get(action, action)
    authorities = _actor_authorities(actor_context)
    return bool(
        actor_context
        and (
            actor_context.get("global_authority")
            or actor_context.get("role") == "Admin"
            or actor_context.get("actor_id") == "admin"
            or "compliance_admin" in authorities
            or required in authorities
            or action in authorities
        )
    )


def _require_authority(actor_context, action, authority_basis=None):
    _actor(actor_context)
    if not _actor_has_authority(actor_context, action):
        raise PermissionError("authorization_denied")
    if not _summary(authority_basis or actor_context.get("authority_basis"), "authority_basis", required=True):
        raise ValueError("authority_basis_required")


def _review_visible_to_actor(review, actor_context):
    return bool(review and _actor_can_access_firm(actor_context, review["firm_id"]))


def _review_mutable(review):
    return bool(review and review["status"] not in H6C_TERMINAL_STATES)


def _payload_hash(payload):
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def validate_public_compliance_review_id(compliance_review_id):
    value = _scalar(compliance_review_id, "compliance_review_id", required=True, max_length=64)
    if not PUBLIC_REVIEW_ID_RE.fullmatch(value):
        raise ValueError("compliance_review_id_invalid")
    return value


def validate_compliance_review_scope(payload, actor_context=None):
    firm_id = _safe_id(payload.get("firm_id"), "firm_id", required=True)
    institution_id = _safe_id(payload.get("institution_id"), "institution_id")
    trust_id = _safe_id(payload.get("trust_id"), "trust_id")
    matter_id = _safe_id(payload.get("matter_id"), "matter_id")
    deployment_key = _safe_id(payload.get("deployment_key"), "deployment_key")

    if not _actor_can_access_firm(actor_context, firm_id):
        raise ValueError("firm_scope_denied")
    if trust_id and matter_id:
        raise ValueError("trust_matter_scope_requires_authoritative_link")

    return {
        "firm_id": firm_id,
        "institution_id": institution_id,
        "trust_id": trust_id,
        "matter_id": matter_id,
        "deployment_key": deployment_key,
    }


def _public_review(row):
    if not row:
        return None
    record = dict(row)
    record["approval_required"] = bool(record.get("approval_required"))
    return record


def _public_event(row):
    return dict(row) if row else None


def _selected_fields(fields):
    return ", ".join(fields)


def _row_record(cursor, row, fields):
    if row is None:
        return None
    if hasattr(row, "keys"):
        return {field: row[field] for field in fields}
    names = [column[0] for column in cursor.description]
    values = dict(zip(names, row))
    return {field: values.get(field) for field in fields}


def _serialize_review(record):
    if record is not None:
        record["approval_required"] = bool(record.get("approval_required"))
    return record


def _read_scope(scope):
    if not isinstance(scope, dict):
        return None
    if scope.get("global") is True:
        return {"global": True, "firm_id": None}
    try:
        firm_id = _safe_id(scope.get("firm_id"), "firm_id", required=True)
    except ValueError:
        return None
    return {"global": False, "firm_id": firm_id}


def _read_limit(limit, default):
    if limit is None:
        limit = default
    if isinstance(limit, bool):
        raise ValueError("limit_invalid")
    try:
        value = int(limit)
    except (TypeError, ValueError) as exc:
        raise ValueError("limit_invalid") from exc
    if value < 1 or value > READ_LIMIT_MAX:
        raise ValueError("limit_invalid")
    return value


def _existing_tables(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    return {row[0] for row in rows}


def _read_schema_available(conn):
    return REQUIRED_READ_TABLES <= _existing_tables(conn)


def foundation_available(connection=None):
    owns = connection is None
    conn = connection or get_connection()
    try:
        return _read_schema_available(conn)
    finally:
        if owns:
            conn.close()


def activation_status(connection=None):
    owns = connection is None
    conn = connection or get_connection()
    try:
        if ACTIVATION_TABLE not in _existing_tables(conn):
            return {"available": False, "status": "not_activated", "message": FOUNDATION_UNAVAILABLE_MESSAGE}
        row = conn.execute(
            """
            SELECT module_key, schema_version, status, verification_status, completed_at
            FROM compliance_review_activation_registry
            WHERE module_key = 'compliance_reviews'
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
        if not row:
            return {"available": False, "status": "not_activated", "message": FOUNDATION_UNAVAILABLE_MESSAGE}
        status = row["status"] if hasattr(row, "keys") else row[2]
        return {
            "available": status == "activation_verified",
            "status": status,
            "module_key": row["module_key"] if hasattr(row, "keys") else row[0],
            "schema_version": row["schema_version"] if hasattr(row, "keys") else row[1],
            "verification_status": row["verification_status"] if hasattr(row, "keys") else row[3],
            "completed_at": row["completed_at"] if hasattr(row, "keys") else row[4],
        }
    finally:
        if owns:
            conn.close()


def _write_foundation_available(conn):
    status = activation_status(connection=conn)
    return bool(status.get("available") and _read_schema_available(conn))


def _allocate_public_id(conn):
    year = datetime.now(UTC).year
    row = conn.execute(
        """
        SELECT last_number
        FROM compliance_review_number_sequences
        WHERE namespace = 'CMP' AND sequence_year = ?
        """,
        (year,),
    ).fetchone()
    if row:
        next_number = int(row["last_number"]) + 1
        conn.execute(
            """
            UPDATE compliance_review_number_sequences
            SET last_number = ?, updated_at = ?
            WHERE namespace = 'CMP' AND sequence_year = ?
            """,
            (next_number, _now(), year),
        )
    else:
        next_number = 1
        conn.execute(
            """
            INSERT INTO compliance_review_number_sequences (
                namespace, sequence_year, last_number, created_at, updated_at
            ) VALUES ('CMP', ?, ?, ?, ?)
            """,
            (year, next_number, _now(), _now()),
        )
    return f"CMP-{year}-{next_number:04d}"


def _allocate_identifier(conn, namespace, width=H6C_IDENTIFIER_WIDTH):
    year = datetime.now(UTC).year
    row = conn.execute(
        """
        SELECT last_number
        FROM compliance_review_number_sequences
        WHERE namespace = ? AND sequence_year = ?
        """,
        (namespace, year),
    ).fetchone()
    if row:
        next_number = int(row["last_number"]) + 1
        conn.execute(
            """
            UPDATE compliance_review_number_sequences
            SET last_number = ?, updated_at = ?
            WHERE namespace = ? AND sequence_year = ?
            """,
            (next_number, _now(), namespace, year),
        )
    else:
        next_number = 1
        conn.execute(
            """
            INSERT INTO compliance_review_number_sequences (
                namespace, sequence_year, last_number, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (namespace, year, next_number, _now(), _now()),
        )
    return f"{namespace}-{year}-{next_number:0{width}d}"


def _audit_hash(payload):
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _append_audit_entry(
    conn,
    *,
    compliance_review_id,
    entity_type,
    entity_id,
    action,
    actor_context,
    authority_basis,
    previous_state=None,
    new_state=None,
    note="",
):
    actor_id, _actor_label = _actor(actor_context)
    review = None
    if compliance_review_id:
        review = conn.execute(
            "SELECT firm_id FROM compliance_reviews WHERE compliance_review_id = ?",
            (compliance_review_id,),
        ).fetchone()
    firm_id = (review["firm_id"] if review else None) or _actor_scope(actor_context).get("firm_id")
    if not firm_id:
        raise ValueError("firm_id_required")
    previous = conn.execute(
        """
        SELECT entry_hash
        FROM compliance_review_audit_ledger
        WHERE firm_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (firm_id,),
    ).fetchone()
    previous_hash = previous["entry_hash"] if previous else None
    audit_id = _allocate_identifier(conn, IDENTIFIER_NAMESPACES["audit"])
    payload = {
        "compliance_audit_id": audit_id,
        "compliance_review_id": compliance_review_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "previous_state": previous_state,
        "new_state": new_state,
        "note": _summary(note, "note"),
        "actor_id": actor_id,
        "actor_role": _scalar((actor_context or {}).get("actor_role") or (actor_context or {}).get("role"), "actor_role"),
        "authority_basis": _summary(authority_basis, "authority_basis", required=True),
        "created_at": _now(),
        "previous_hash": previous_hash,
        "firm_id": firm_id,
    }
    payload["entry_hash"] = _audit_hash(payload)
    conn.execute(
        """
        INSERT INTO compliance_review_audit_ledger (
            compliance_audit_id, compliance_review_id, entity_type, entity_id,
            action, previous_state, new_state, note, actor_id, actor_role,
            authority_basis, created_at, previous_hash, entry_hash, hash_algorithm,
            firm_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'SHA-256', ?)
        """,
        (
            payload["compliance_audit_id"],
            compliance_review_id,
            entity_type,
            entity_id,
            action,
            previous_state,
            new_state,
            payload["note"],
            payload["actor_id"],
            payload["actor_role"],
            payload["authority_basis"],
            payload["created_at"],
            payload["previous_hash"],
            payload["entry_hash"],
            payload["firm_id"],
        ),
    )
    return payload


def list_compliance_audit_entries(compliance_review_id, *, scope=None, connection=None):
    review_id = validate_public_compliance_review_id(compliance_review_id)
    read_scope = _read_scope(scope)
    if read_scope is None:
        return []
    owns = connection is None
    conn = connection or get_connection()
    try:
        if "compliance_review_audit_ledger" not in _existing_tables(conn):
            return []
        params = [review_id]
        firm_clause = ""
        if not read_scope["global"]:
            firm_clause = " AND firm_id = ?"
            params.append(read_scope["firm_id"])
        return [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT *
                FROM compliance_review_audit_ledger
                WHERE compliance_review_id = ?{firm_clause}
                ORDER BY id ASC
                """,
                tuple(params),
            ).fetchall()
        ]
    finally:
        if owns:
            conn.close()


def verify_compliance_audit_chain(*, firm_id, connection=None):
    owns = connection is None
    conn = connection or get_connection()
    try:
        rows = conn.execute(
            """
            SELECT *
            FROM compliance_review_audit_ledger
            WHERE firm_id = ?
            ORDER BY id ASC
            """,
            (firm_id,),
        ).fetchall()
        previous_hash = None
        for row in rows:
            payload = {
                "compliance_audit_id": row["compliance_audit_id"],
                "compliance_review_id": row["compliance_review_id"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "action": row["action"],
                "previous_state": row["previous_state"],
                "new_state": row["new_state"],
                "note": row["note"],
                "actor_id": row["actor_id"],
                "actor_role": row["actor_role"],
                "authority_basis": row["authority_basis"],
                "created_at": row["created_at"],
                "previous_hash": row["previous_hash"],
                "firm_id": row["firm_id"],
            }
            if row["previous_hash"] != previous_hash:
                return {"ok": False, "status": "broken_previous_hash", "audit_id": row["compliance_audit_id"]}
            if _audit_hash(payload) != row["entry_hash"]:
                return {"ok": False, "status": "entry_hash_mismatch", "audit_id": row["compliance_audit_id"]}
            previous_hash = row["entry_hash"]
        return {"ok": True, "status": "verified", "count": len(rows)}
    finally:
        if owns:
            conn.close()


def _next_event_sequence(conn, compliance_review_id):
    row = conn.execute(
        """
        SELECT COALESCE(MAX(event_sequence), 0) AS max_sequence
        FROM compliance_review_events
        WHERE compliance_review_id = ?
        """,
        (compliance_review_id,),
    ).fetchone()
    return int(row["max_sequence"] or 0) + 1


def _event_id(compliance_review_id, event_sequence):
    return f"CMPEVT-{compliance_review_id[4:]}-{int(event_sequence):04d}"


def _insert_event(
    conn,
    *,
    compliance_review_id,
    event_type,
    actor_id,
    actor_label,
    prior_status=None,
    resulting_status=None,
    summary="",
    reason="",
    related_record_type=None,
    related_record_id=None,
    idempotency_key=None,
    payload_hash=None,
    expected_version=None,
):
    sequence = _next_event_sequence(conn, compliance_review_id)
    event_id = _event_id(compliance_review_id, sequence)
    conn.execute(
        """
        INSERT INTO compliance_review_events (
            event_id, compliance_review_id, event_sequence, event_type,
            actor_id, actor_label, prior_status, resulting_status,
            summary, reason, related_record_type, related_record_id,
            idempotency_key, payload_hash, expected_version, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            compliance_review_id,
            sequence,
            event_type,
            actor_id,
            actor_label,
            prior_status,
            resulting_status,
            summary,
            reason,
            related_record_type,
            related_record_id,
            idempotency_key,
            payload_hash,
            expected_version,
            _now(),
        ),
    )
    return event_id


def _duplicate_active_review(conn, data):
    return conn.execute(
        """
        SELECT *
        FROM compliance_reviews
        WHERE firm_id = ?
          AND review_type = ?
          AND governing_requirement_type = ?
          AND COALESCE(governing_requirement_id, '') = COALESCE(?, '')
          AND source_type = ?
          AND COALESCE(source_id, '') = COALESCE(?, '')
          AND status IN ('draft', 'opened', 'under_review', 'awaiting_information', 'ready_for_disposition')
        LIMIT 1
        """,
        (
            data["firm_id"],
            data["review_type"],
            data["governing_requirement_type"],
            data.get("governing_requirement_id"),
            data["source_type"],
            data.get("source_id"),
        ),
    ).fetchone()


def _get_creation_replay(conn, idempotency_key):
    if not idempotency_key:
        return None
    return conn.execute(
        "SELECT * FROM compliance_reviews WHERE idempotency_key = ? LIMIT 1",
        (idempotency_key,),
    ).fetchone()


def _get_transition_replay(conn, compliance_review_id, idempotency_key):
    if not idempotency_key:
        return None
    return conn.execute(
        """
        SELECT *
        FROM compliance_review_events
        WHERE compliance_review_id = ? AND idempotency_key = ?
        LIMIT 1
        """,
        (compliance_review_id, idempotency_key),
    ).fetchone()


def _normalize_create_payload(payload, actor_context):
    payload = payload or {}
    extra = PROHIBITED_CREATE_FIELDS.intersection(payload)
    if extra:
        raise ValueError(f"prohibited_create_fields:{','.join(sorted(extra))}")
    scope = validate_compliance_review_scope(payload, actor_context=actor_context)
    review_type = _choice(payload.get("review_type"), "review_type", COMPLIANCE_REVIEW_TYPES)
    requirement_type = _choice(
        payload.get("governing_requirement_type"),
        "governing_requirement_type",
        COMPLIANCE_REQUIREMENT_TYPES,
    )
    source_type = _choice(payload.get("source_type"), "source_type", COMPLIANCE_SOURCE_TYPES)
    requirement_id = _safe_id(payload.get("governing_requirement_id"), "governing_requirement_id")
    source_id = _safe_id(payload.get("source_id"), "source_id")
    if requirement_type in INTERNAL_COMPLIANCE_REQUIREMENT_TYPES and not requirement_id:
        raise ValueError("governing_requirement_id_required")
    if source_type not in {"manual_institutional_review", "external_reference"} and not source_id:
        raise ValueError("source_id_required")

    data = {
        **scope,
        "title": _scalar(payload.get("title"), "title", required=True, max_length=255),
        "review_type": review_type,
        "question_presented": _summary(payload.get("question_presented"), "question_presented", required=True),
        "governing_requirement_type": requirement_type,
        "governing_requirement_id": requirement_id,
        "governing_requirement_label": _scalar(payload.get("governing_requirement_label"), "governing_requirement_label", max_length=255),
        "source_type": source_type,
        "source_id": source_id,
        "source_label": _scalar(payload.get("source_label"), "source_label", max_length=255),
        "scope_summary": _summary(payload.get("scope_summary"), "scope_summary"),
        "priority": _choice(payload.get("priority") or "normal", "priority", COMPLIANCE_REVIEW_PRIORITIES),
        "risk_level": _choice(payload.get("risk_level") or "moderate", "risk_level", COMPLIANCE_REVIEW_RISK_LEVELS),
        "review_owner": _scalar(payload.get("review_owner"), "review_owner", max_length=255),
        "assigned_to": _scalar(payload.get("assigned_to"), "assigned_to", max_length=255),
        "authority_basis": _summary(payload.get("authority_basis"), "authority_basis"),
        "approval_required": 1 if bool(payload.get("approval_required")) else 0,
        "due_at": _scalar(payload.get("due_at"), "due_at", max_length=80),
    }
    return data


def _get_compliance_review_internal(compliance_review_id, connection=None):
    owns = connection is None
    conn = connection or get_connection()
    try:
        return _public_review(
            conn.execute(
                "SELECT * FROM compliance_reviews WHERE compliance_review_id = ? LIMIT 1",
                (compliance_review_id,),
            ).fetchone()
        )
    finally:
        if owns:
            conn.close()


def list_compliance_reviews(*, scope=None, limit=100, connection=None):
    read_scope = _read_scope(scope)
    if read_scope is None:
        return {
            "available": False,
            "status": "invalid_scope",
            "message": "A valid firm scope is required to view Compliance Reviews.",
            "reviews": [],
            "count": 0,
        }
    limit = _read_limit(limit, 100)
    owns = connection is None
    conn = connection or get_connection()
    try:
        if not _read_schema_available(conn):
            return {
                "available": False,
                "status": "schema_missing",
                "message": FOUNDATION_UNAVAILABLE_MESSAGE,
                "reviews": [],
                "count": 0,
            }
        params = []
        where = ""
        if not read_scope["global"]:
            where = "WHERE firm_id = ?"
            params.append(read_scope["firm_id"])
        params.append(limit)
        cursor = conn.execute(
            f"""
            SELECT {_selected_fields(PUBLIC_REVIEW_FIELDS)}
            FROM compliance_reviews
            {where}
            ORDER BY updated_at DESC, created_at DESC, compliance_review_id DESC
            LIMIT ?
            """,
            tuple(params),
        )
        reviews = [
            _serialize_review(_row_record(cursor, row, PUBLIC_REVIEW_FIELDS))
            for row in cursor.fetchall()
        ]
        return {
            "available": True,
            "status": "ok",
            "message": "Compliance Review records are available.",
            "reviews": reviews,
            "count": len(reviews),
        }
    except Exception:
        return {
            "available": False,
            "status": "read_failure",
            "message": "Compliance Review records could not be read.",
            "reviews": [],
            "count": 0,
        }
    finally:
        if owns:
            conn.close()


def get_compliance_review(compliance_review_id, *, scope=None, connection=None):
    compliance_review_id = validate_public_compliance_review_id(compliance_review_id)
    read_scope = _read_scope(scope)
    if read_scope is None:
        return None
    owns = connection is None
    conn = connection or get_connection()
    try:
        if not _read_schema_available(conn):
            return None
        params = [compliance_review_id]
        firm_clause = ""
        if not read_scope["global"]:
            firm_clause = " AND firm_id = ?"
            params.append(read_scope["firm_id"])
        cursor = conn.execute(
            f"""
            SELECT {_selected_fields(PUBLIC_REVIEW_FIELDS)}
            FROM compliance_reviews
            WHERE compliance_review_id = ?{firm_clause}
            LIMIT 1
            """,
            tuple(params),
        )
        return _serialize_review(
            _row_record(cursor, cursor.fetchone(), PUBLIC_REVIEW_FIELDS)
        )
    except Exception:
        return None
    finally:
        if owns:
            conn.close()


def get_compliance_review_by_public_id(compliance_review_id, *, scope=None, connection=None):
    return get_compliance_review(compliance_review_id, scope=scope, connection=connection)


def get_compliance_review_by_id(id, *, scope=None, connection=None):
    read_scope = _read_scope(scope)
    if read_scope is None:
        return None
    owns = connection is None
    conn = connection or get_connection()
    try:
        if not _read_schema_available(conn):
            return None
        params = [id]
        firm_clause = ""
        if not read_scope["global"]:
            firm_clause = " AND firm_id = ?"
            params.append(read_scope["firm_id"])
        cursor = conn.execute(
            f"""
            SELECT {_selected_fields(PUBLIC_REVIEW_FIELDS)}
            FROM compliance_reviews
            WHERE id = ?{firm_clause}
            LIMIT 1
            """,
            tuple(params),
        )
        return _serialize_review(
            _row_record(cursor, cursor.fetchone(), PUBLIC_REVIEW_FIELDS)
        )
    except Exception:
        return None
    finally:
        if owns:
            conn.close()


def list_compliance_review_events(
    compliance_review_id, *, scope=None, limit=READ_LIMIT_MAX, connection=None
):
    compliance_review_id = validate_public_compliance_review_id(compliance_review_id)
    read_scope = _read_scope(scope)
    if read_scope is None:
        return []
    limit = _read_limit(limit, READ_LIMIT_MAX)
    owns = connection is None
    conn = connection or get_connection()
    try:
        if not _read_schema_available(conn):
            return []
        params = [compliance_review_id]
        firm_clause = ""
        if not read_scope["global"]:
            firm_clause = " AND firm_id = ?"
            params.append(read_scope["firm_id"])
        visible = conn.execute(
            f"SELECT 1 FROM compliance_reviews WHERE compliance_review_id = ?{firm_clause} LIMIT 1",
            tuple(params),
        ).fetchone()
        if not visible:
            return []
        cursor = conn.execute(
            f"""
            SELECT {_selected_fields(PUBLIC_EVENT_FIELDS)}
            FROM compliance_review_events
            WHERE compliance_review_id = ?
            ORDER BY event_sequence ASC
            LIMIT ?
            """,
            (compliance_review_id, limit),
        )
        return [
            _row_record(cursor, row, PUBLIC_EVENT_FIELDS) for row in cursor.fetchall()
        ]
    except Exception:
        return []
    finally:
        if owns:
            conn.close()


def list_compliance_review_relationships(
    compliance_review_id, *, scope=None, limit=READ_LIMIT_MAX, connection=None
):
    compliance_review_id = validate_public_compliance_review_id(compliance_review_id)
    read_scope = _read_scope(scope)
    if read_scope is None:
        return []
    limit = _read_limit(limit, READ_LIMIT_MAX)
    owns = connection is None
    conn = connection or get_connection()
    try:
        if not _read_schema_available(conn):
            return []
        params = [compliance_review_id]
        firm_clause = ""
        if not read_scope["global"]:
            firm_clause = " AND firm_id = ?"
            params.append(read_scope["firm_id"])
        visible = conn.execute(
            f"SELECT 1 FROM compliance_reviews WHERE compliance_review_id = ?{firm_clause} LIMIT 1",
            tuple(params),
        ).fetchone()
        if not visible:
            return []
        cursor = conn.execute(
            f"""
            SELECT {_selected_fields(PUBLIC_RELATIONSHIP_FIELDS)}
            FROM compliance_review_relationships
            WHERE compliance_review_id = ?
            ORDER BY created_at ASC, relationship_id ASC
            LIMIT ?
            """,
            (compliance_review_id, limit),
        )
        return [
            _row_record(cursor, row, PUBLIC_RELATIONSHIP_FIELDS)
            for row in cursor.fetchall()
        ]
    except Exception:
        return []
    finally:
        if owns:
            conn.close()

def create_compliance_review(*, payload, actor_context, idempotency_key=None):
    conn = get_connection()
    try:
        if not _write_foundation_available(conn):
            return _result(False, "foundation_unavailable", FOUNDATION_UNAVAILABLE_MESSAGE)
        actor_id, actor_label = _actor(actor_context)
        _require_authority(actor_context, "create", (payload or {}).get("authority_basis"))
        data = _normalize_create_payload(payload, actor_context)
        idempotency_key = _scalar(idempotency_key, "idempotency_key", max_length=IDEMPOTENCY_LIMIT)
        payload_hash = _payload_hash({**data, "actor_id": actor_id})

        conn.execute("BEGIN IMMEDIATE")
        try:
            replay = _get_creation_replay(conn, idempotency_key)
            if replay:
                review = _public_review(replay)
                if review.get("payload_hash") != payload_hash:
                    conn.rollback()
                    return _result(False, "conflict", "Idempotency key conflicts with a prior create request.")
                event = conn.execute(
                    """
                    SELECT *
                    FROM compliance_review_events
                    WHERE compliance_review_id = ? AND event_type = 'compliance_review_created'
                    ORDER BY event_sequence ASC
                    LIMIT 1
                    """,
                    (review["compliance_review_id"],),
                ).fetchone()
                conn.commit()
                return _result(True, "idempotent_replay", review=review, event=_public_event(event))

            duplicate = _duplicate_active_review(conn, data)
            if duplicate:
                conn.rollback()
                return _result(
                    False,
                    "duplicate_active_review",
                    "An active Compliance Review already exists for this requirement and source.",
                    review=_public_review(duplicate),
                )

            review_id = _allocate_public_id(conn)
            now = _now()
            conn.execute(
                """
                INSERT INTO compliance_reviews (
                    compliance_review_id, firm_id, institution_id, trust_id, matter_id,
                    deployment_key, title, review_type, question_presented,
                    governing_requirement_type, governing_requirement_id,
                    governing_requirement_label, source_type, source_id, source_label,
                    scope_summary, status, priority, risk_level, review_owner,
                    assigned_to, authority_basis, approval_required, due_at,
                    created_by, created_at, updated_by, updated_at, version,
                    idempotency_key, payload_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    review_id,
                    data["firm_id"],
                    data["institution_id"],
                    data["trust_id"],
                    data["matter_id"],
                    data["deployment_key"],
                    data["title"],
                    data["review_type"],
                    data["question_presented"],
                    data["governing_requirement_type"],
                    data["governing_requirement_id"],
                    data["governing_requirement_label"],
                    data["source_type"],
                    data["source_id"],
                    data["source_label"],
                    data["scope_summary"],
                    data["priority"],
                    data["risk_level"],
                    data["review_owner"],
                    data["assigned_to"],
                    data["authority_basis"],
                    data["approval_required"],
                    data["due_at"],
                    actor_id,
                    now,
                    actor_id,
                    now,
                    idempotency_key,
                    payload_hash,
                ),
            )
            primary_subject_type = _scalar(
                payload.get("primary_subject_type") or payload.get("related_object_type") or data["source_type"],
                "primary_subject_type",
                required=True,
                max_length=80,
            )
            primary_subject_id = _safe_id(
                payload.get("primary_subject_id") or payload.get("related_object_id") or data.get("source_id"),
                "primary_subject_id",
            )
            primary_subject_label = _scalar(
                payload.get("primary_subject_label") or payload.get("related_object_label") or data.get("source_label"),
                "primary_subject_label",
                max_length=255,
            )
            subject_id = _allocate_identifier(conn, "CSB")
            conn.execute(
                """
                INSERT INTO compliance_review_subjects (
                    compliance_subject_id, compliance_review_id, firm_id, subject_role,
                    subject_type, subject_id, subject_label, relationship_verb,
                    direction, status, created_by, created_at
                ) VALUES (?, ?, ?, 'primary', ?, ?, ?, 'reviews', 'outbound', 'active', ?, ?)
                """,
                (
                    subject_id,
                    review_id,
                    data["firm_id"],
                    primary_subject_type,
                    primary_subject_id,
                    primary_subject_label,
                    actor_id,
                    now,
                ),
            )
            event_id = _insert_event(
                conn,
                compliance_review_id=review_id,
                event_type="compliance_review_created",
                actor_id=actor_id,
                actor_label=actor_label,
                prior_status=None,
                resulting_status="draft",
                summary=data["question_presented"],
                reason=data["authority_basis"],
                idempotency_key=None,
                payload_hash=payload_hash,
            )
            _append_audit_entry(
                conn,
                compliance_review_id=review_id,
                entity_type="compliance_review",
                entity_id=review_id,
                action="review_created",
                actor_context=actor_context,
                authority_basis=data["authority_basis"],
                previous_state=None,
                new_state="draft",
                note=data["title"],
            )
            review = _get_compliance_review_internal(review_id, connection=conn)
            event = conn.execute(
                "SELECT * FROM compliance_review_events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
            conn.commit()
            return _result(True, "created", review=review, event=_public_event(event))
        except Exception:
            conn.rollback()
            raise
    except PermissionError as exc:
        return _result(False, "authorization_denied", str(exc) or "Compliance Review creation is not authorized.")
    except ValueError as exc:
        return _result(False, "invalid_input", str(exc))
    except Exception:
        return _result(False, "unexpected_failure", "Compliance Review could not be created.")
    finally:
        conn.close()


def validate_review_transition(current_status, action):
    action = (action or "").strip().lower().replace(" ", "_")
    existing = COMPLIANCE_REVIEW_TRANSITIONS.get((current_status, action))
    if existing:
        return existing
    h6c = H6C_TRANSITIONS.get((current_status, action))
    if not h6c:
        return None
    resulting_status, event_type = h6c
    return {
        "resulting_status": resulting_status,
        "event_type": event_type,
        "requires_reason": True,
        "requires_summary": True,
    }


def generate_compliance_review_id(connection=None):
    owns = connection is None
    conn = connection or get_connection()
    try:
        return _allocate_public_id(conn)
    finally:
        if owns:
            conn.close()


def transition_compliance_review(
    *,
    compliance_review_id,
    action,
    expected_version,
    actor_context,
    reason,
    summary,
    idempotency_key=None,
    related_record_type=None,
    related_record_id=None,
    **client_fields,
):
    conn = get_connection()
    try:
        if not _write_foundation_available(conn):
            return _result(False, "foundation_unavailable", FOUNDATION_UNAVAILABLE_MESSAGE)
        actor_id, actor_label = _actor(actor_context)
        review_id = validate_public_compliance_review_id(compliance_review_id)
        action = _scalar(action, "action", required=True, max_length=80, lowercase=True)
        action = action.replace(" ", "_")
        if action in (RESERVED_COMPLIANCE_REVIEW_ACTIONS - {"close", "reopen", "supersede"}):
            return _result(False, "reserved_workflow_not_active", "This Compliance Review workflow is reserved for a later milestone.")
        try:
            expected_version = int(expected_version)
        except Exception as exc:
            raise ValueError("expected_version_invalid") from exc
        reason = _summary(reason, "reason", required=True)
        summary = _summary(summary, "summary", required=True)
        _require_authority(actor_context, action, reason)
        related_record_type = _scalar(related_record_type, "related_record_type", max_length=80)
        related_record_id = _safe_id(related_record_id, "related_record_id")
        idempotency_key = _scalar(idempotency_key, "idempotency_key", max_length=IDEMPOTENCY_LIMIT)
        extra = PROHIBITED_TRANSITION_FIELDS.intersection({key for key, value in client_fields.items() if value is not None})
        if extra:
            raise ValueError(f"prohibited_transition_fields:{','.join(sorted(extra))}")
        payload_hash = _payload_hash(
            {
                "compliance_review_id": review_id,
                "action": action,
                "expected_version": expected_version,
                "reason": reason,
                "summary": summary,
                "related_record_type": related_record_type,
                "related_record_id": related_record_id,
                "actor_id": actor_id,
            }
        )

        conn.execute("BEGIN IMMEDIATE")
        try:
            review = _public_review(
                conn.execute(
                    "SELECT * FROM compliance_reviews WHERE compliance_review_id = ? LIMIT 1",
                    (review_id,),
                ).fetchone()
            )
            if not review:
                conn.rollback()
                return _result(False, "not_found", "Compliance Review not found.")
            if not _actor_can_access_firm(actor_context, review["firm_id"]):
                conn.rollback()
                return _result(False, "not_found", "Compliance Review not found.")

            replay = _get_transition_replay(conn, review_id, idempotency_key)
            if replay:
                if replay["payload_hash"] != payload_hash:
                    conn.rollback()
                    return _result(False, "conflict", "Idempotency key conflicts with a prior transition.")
                conn.commit()
                return _result(True, "idempotent_replay", review=_get_compliance_review_internal(review_id), event=_public_event(replay))

            current_status = review["status"]
            transition = validate_review_transition(current_status, action)
            if not transition:
                _append_audit_entry(
                    conn,
                    compliance_review_id=review_id,
                    entity_type="compliance_review",
                    entity_id=review_id,
                    action="invalid_transition_attempted",
                    actor_context=actor_context,
                    authority_basis=reason,
                    previous_state=current_status,
                    new_state=action,
                    note=summary,
                )
                conn.commit()
                return _result(False, "invalid_transition", "Compliance Review transition is not allowed.")
            if current_status in H6C_TERMINAL_STATES:
                conn.rollback()
                return _result(False, "closed_record", "Closed Compliance Reviews cannot be changed in this milestone.")
            if int(review["version"]) != expected_version:
                conn.rollback()
                return _result(False, "stale_version", "Compliance Review changed before transition.")

            resulting_status = transition["resulting_status"]
            now = _now()
            conn.execute(
                """
                UPDATE compliance_reviews
                SET status = ?,
                    opened_at = CASE WHEN ? = 'opened' AND opened_at IS NULL THEN ? ELSE opened_at END,
                    version = version + 1,
                    updated_by = ?,
                    updated_at = ?
                WHERE compliance_review_id = ? AND version = ?
                """,
                (resulting_status, resulting_status, now, actor_id, now, review_id, expected_version),
            )
            if conn.total_changes < 1:
                conn.rollback()
                return _result(False, "stale_version", "Compliance Review changed before transition.")

            event_id = _insert_event(
                conn,
                compliance_review_id=review_id,
                event_type=transition["event_type"],
                actor_id=actor_id,
                actor_label=actor_label,
                prior_status=current_status,
                resulting_status=resulting_status,
                summary=summary,
                reason=reason,
                related_record_type=related_record_type,
                related_record_id=related_record_id,
                idempotency_key=idempotency_key,
                payload_hash=payload_hash,
                expected_version=expected_version,
            )
            _append_audit_entry(
                conn,
                compliance_review_id=review_id,
                entity_type="compliance_review",
                entity_id=review_id,
                action=transition["event_type"],
                actor_context=actor_context,
                authority_basis=reason,
                previous_state=current_status,
                new_state=resulting_status,
                note=summary,
            )
            updated = _get_compliance_review_internal(review_id, connection=conn)
            event = conn.execute(
                "SELECT * FROM compliance_review_events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
            conn.commit()
            return _result(True, "transitioned", review=updated, event=_public_event(event))
        except Exception:
            conn.rollback()
            raise
    except ValueError as exc:
        return _result(False, "invalid_input", str(exc))
    except Exception:
        return _result(False, "unexpected_failure", "Compliance Review transition could not be completed.")
    finally:
        conn.close()


def _workflow_result(fn):
    try:
        return fn()
    except PermissionError as exc:
        return _result(False, "authorization_denied", str(exc) or "Compliance Review action is not authorized.")
    except ValueError as exc:
        return _result(False, "invalid_input", str(exc))
    except Exception:
        return _result(False, "unexpected_failure", "Compliance Review action could not be completed.")


def _load_review_for_update(conn, compliance_review_id, actor_context):
    review_id = validate_public_compliance_review_id(compliance_review_id)
    review = _public_review(
        conn.execute(
            "SELECT * FROM compliance_reviews WHERE compliance_review_id = ? LIMIT 1",
            (review_id,),
        ).fetchone()
    )
    if not review:
        raise LookupError("not_found")
    if not _review_visible_to_actor(review, actor_context):
        raise PermissionError("wrong_firm")
    if not _review_mutable(review):
        raise ValueError("archived_or_terminal_record")
    return review


def _run_workflow(action, *, compliance_review_id, actor_context, authority_basis, handler):
    conn = get_connection()
    try:
        if not _write_foundation_available(conn):
            return _result(False, "foundation_unavailable", FOUNDATION_UNAVAILABLE_MESSAGE)
        _require_authority(actor_context, action, authority_basis)
        conn.execute("BEGIN IMMEDIATE")
        try:
            review = _load_review_for_update(conn, compliance_review_id, actor_context)
            result = handler(conn, review)
            conn.commit()
            return result
        except LookupError:
            conn.rollback()
            return _result(False, "not_found", "Compliance Review not found.")
        except Exception:
            conn.rollback()
            raise
    finally:
        conn.close()


def _touch_review(conn, review_id, actor_id, status=None):
    if status:
        conn.execute(
            """
            UPDATE compliance_reviews
            SET status = ?, version = version + 1, updated_by = ?, updated_at = ?
            WHERE compliance_review_id = ?
            """,
            (status, actor_id, _now(), review_id),
        )
    else:
        conn.execute(
            """
            UPDATE compliance_reviews
            SET version = version + 1, updated_by = ?, updated_at = ?
            WHERE compliance_review_id = ?
            """,
            (actor_id, _now(), review_id),
        )


def update_compliance_review(*, compliance_review_id, payload, actor_context, authority_basis):
    def work():
        actor_id, _label = _actor(actor_context)
        return _run_workflow(
            "update",
            compliance_review_id=compliance_review_id,
            actor_context=actor_context,
            authority_basis=authority_basis,
            handler=lambda conn, review: _update_review_handler(conn, review, payload or {}, actor_context, actor_id, authority_basis),
        )
    return _workflow_result(work)


def _update_review_handler(conn, review, payload, actor_context, actor_id, authority_basis):
    if review["status"] != "draft":
        raise ValueError("draft_required")
    fields = []
    params = []
    for key in ("title", "purpose", "scope", "review_standard", "jurisdiction", "risk_level", "priority", "confidentiality_level", "due_date"):
        if key in payload:
            fields.append(f"{key} = ?")
            params.append(_scalar(payload.get(key), key, max_length=255))
    if fields:
        fields.extend(["version = version + 1", "updated_by = ?", "updated_at = ?"])
        params.extend([actor_id, _now(), review["compliance_review_id"]])
        conn.execute(f"UPDATE compliance_reviews SET {', '.join(fields)} WHERE compliance_review_id = ?", tuple(params))
    _append_audit_entry(conn, compliance_review_id=review["compliance_review_id"], entity_type="compliance_review", entity_id=review["compliance_review_id"], action="review_updated", actor_context=actor_context, authority_basis=authority_basis, previous_state=review["status"], new_state=review["status"], note="Draft review updated.")
    return _result(True, "updated", review=_get_compliance_review_internal(review["compliance_review_id"], connection=conn))


def assign_reviewer(*, compliance_review_id, assigned_reviewer, actor_context, authority_basis):
    def handler(conn, review):
        actor_id, _label = _actor(actor_context)
        reviewer = _scalar(assigned_reviewer, "assigned_reviewer", required=True, max_length=255)
        conn.execute(
            "UPDATE compliance_reviews SET assigned_reviewer = ?, assigned_to = ?, version = version + 1, updated_by = ?, updated_at = ? WHERE compliance_review_id = ?",
            (reviewer, reviewer, actor_id, _now(), review["compliance_review_id"]),
        )
        _append_audit_entry(conn, compliance_review_id=review["compliance_review_id"], entity_type="compliance_review", entity_id=review["compliance_review_id"], action="reviewer_assigned", actor_context=actor_context, authority_basis=authority_basis, previous_state=review.get("assigned_reviewer"), new_state=reviewer, note="Reviewer assigned.")
        return _result(True, "assigned", review=_get_compliance_review_internal(review["compliance_review_id"], connection=conn))
    return _workflow_result(lambda: _run_workflow("assign_reviewer", compliance_review_id=compliance_review_id, actor_context=actor_context, authority_basis=authority_basis, handler=handler))


def add_review_subject(*, compliance_review_id, subject_type, subject_id=None, subject_label=None, subject_role="secondary", actor_context, authority_basis):
    def handler(conn, review):
        actor_id, _label = _actor(actor_context)
        sid = _allocate_identifier(conn, "CSB")
        conn.execute(
            """
            INSERT INTO compliance_review_subjects (
                compliance_subject_id, compliance_review_id, firm_id, subject_role,
                subject_type, subject_id, subject_label, relationship_verb, direction,
                status, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'relates_to', 'outbound', 'active', ?, ?)
            """,
            (sid, review["compliance_review_id"], review["firm_id"], _scalar(subject_role, "subject_role", required=True, max_length=80), _scalar(subject_type, "subject_type", required=True, max_length=80), _safe_id(subject_id, "subject_id"), _scalar(subject_label, "subject_label", max_length=255), actor_id, _now()),
        )
        _append_audit_entry(conn, compliance_review_id=review["compliance_review_id"], entity_type="compliance_review_subject", entity_id=sid, action="subject_added", actor_context=actor_context, authority_basis=authority_basis, new_state="active", note=subject_label or subject_type)
        return _result(True, "subject_added", event={"compliance_subject_id": sid})
    return _workflow_result(lambda: _run_workflow("add_subject", compliance_review_id=compliance_review_id, actor_context=actor_context, authority_basis=authority_basis, handler=handler))


def add_review_relationship(*, compliance_review_id, related_record_type, related_record_id, relationship_type="related_to", direction="outbound", actor_context, authority_basis):
    def handler(conn, review):
        actor_id, _label = _actor(actor_context)
        rid = _allocate_identifier(conn, IDENTIFIER_NAMESPACES["relationship"])
        conn.execute(
            """
            INSERT INTO compliance_review_relationships (
                relationship_id, compliance_review_id, relationship_type,
                related_record_type, related_record_id, direction, status,
                created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
            """,
            (rid, review["compliance_review_id"], _scalar(relationship_type, "relationship_type", required=True, max_length=80), _scalar(related_record_type, "related_record_type", required=True, max_length=80), _safe_id(related_record_id, "related_record_id", required=True), _scalar(direction, "direction", required=True, max_length=40), actor_id, _now()),
        )
        _append_audit_entry(conn, compliance_review_id=review["compliance_review_id"], entity_type="compliance_review_relationship", entity_id=rid, action="relationship_added", actor_context=actor_context, authority_basis=authority_basis, new_state="active", note=relationship_type)
        return _result(True, "relationship_added", event={"relationship_id": rid})
    return _workflow_result(lambda: _run_workflow("add_relationship", compliance_review_id=compliance_review_id, actor_context=actor_context, authority_basis=authority_basis, handler=handler))


def add_review_evidence(*, compliance_review_id, evidence_type, source_type, source_id=None, source_label=None, description="", relevance="", actor_context, authority_basis):
    def handler(conn, review):
        actor_id, _label = _actor(actor_context)
        eid = _allocate_identifier(conn, IDENTIFIER_NAMESPACES["evidence"])
        conn.execute(
            """
            INSERT INTO compliance_review_evidence (
                compliance_evidence_id, compliance_review_id, evidence_type,
                source_type, source_id, source_label, description, relevance,
                evidence_status, verification_status, added_by, added_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'received', 'unverified', ?, ?)
            """,
            (eid, review["compliance_review_id"], _scalar(evidence_type, "evidence_type", required=True, max_length=80), _scalar(source_type, "source_type", required=True, max_length=80), _safe_id(source_id, "source_id"), _scalar(source_label, "source_label", max_length=255), _summary(description, "description"), _summary(relevance, "relevance"), actor_id, _now()),
        )
        _append_audit_entry(conn, compliance_review_id=review["compliance_review_id"], entity_type="compliance_review_evidence", entity_id=eid, action="evidence_added", actor_context=actor_context, authority_basis=authority_basis, new_state="received", note=description or evidence_type)
        return _result(True, "evidence_added", event={"compliance_evidence_id": eid})
    return _workflow_result(lambda: _run_workflow("add_evidence", compliance_review_id=compliance_review_id, actor_context=actor_context, authority_basis=authority_basis, handler=handler))


def verify_review_evidence(*, compliance_review_id, compliance_evidence_id, verification_status="verified", verification_basis="", actor_context, authority_basis):
    def handler(conn, review):
        actor_id, _label = _actor(actor_context)
        basis = _summary(verification_basis, "verification_basis", required=True)
        eid = _safe_id(compliance_evidence_id, "compliance_evidence_id", required=True)
        row = conn.execute("SELECT added_by FROM compliance_review_evidence WHERE compliance_evidence_id = ? AND compliance_review_id = ?", (eid, review["compliance_review_id"])).fetchone()
        if not row:
            raise ValueError("evidence_not_found")
        if row["added_by"] == actor_id:
            raise PermissionError("self_verification_denied")
        status = _scalar(verification_status, "verification_status", required=True, max_length=80)
        conn.execute(
            "UPDATE compliance_review_evidence SET verification_status = ?, evidence_status = CASE WHEN ? = 'verified' THEN 'verified' ELSE evidence_status END, verified_by = ?, verified_at = ?, integrity_reference = ? WHERE compliance_evidence_id = ?",
            (status, status, actor_id, _now(), basis, eid),
        )
        _append_audit_entry(conn, compliance_review_id=review["compliance_review_id"], entity_type="compliance_review_evidence", entity_id=eid, action="evidence_verified", actor_context=actor_context, authority_basis=authority_basis, new_state=status, note=basis)
        return _result(True, "evidence_verified", event={"compliance_evidence_id": eid, "verification_status": status})
    return _workflow_result(lambda: _run_workflow("verify_evidence", compliance_review_id=compliance_review_id, actor_context=actor_context, authority_basis=authority_basis, handler=handler))


def issue_review_finding(*, compliance_review_id, finding_type, title, description="", evidence_basis="", severity="medium", risk_level="moderate", actor_context, authority_basis):
    def handler(conn, review):
        actor_id, _label = _actor(actor_context)
        basis = _summary(evidence_basis, "evidence_basis", required=True)
        row = conn.execute("SELECT COALESCE(MAX(finding_number), 0) + 1 FROM compliance_review_findings WHERE compliance_review_id = ?", (review["compliance_review_id"],)).fetchone()
        number = int(row[0])
        fid = _allocate_identifier(conn, IDENTIFIER_NAMESPACES["finding"])
        conn.execute(
            """
            INSERT INTO compliance_review_findings (
                compliance_finding_id, compliance_review_id, finding_number,
                finding_type, title, description, requirement_or_standard,
                evidence_basis, severity, risk_level, status, disputed,
                issued_by, issued_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'issued', 0, ?, ?, ?, ?)
            """,
            (fid, review["compliance_review_id"], number, _scalar(finding_type, "finding_type", required=True, max_length=80), _scalar(title, "title", required=True, max_length=255), _summary(description, "description"), authority_basis, basis, _scalar(severity, "severity", required=True, max_length=40), _scalar(risk_level, "risk_level", required=True, max_length=40), actor_id, _now(), _now(), _now()),
        )
        _touch_review(conn, review["compliance_review_id"], actor_id, status="findings_issued")
        _append_audit_entry(conn, compliance_review_id=review["compliance_review_id"], entity_type="compliance_review_finding", entity_id=fid, action="finding_issued", actor_context=actor_context, authority_basis=authority_basis, previous_state=review["status"], new_state="findings_issued", note=title)
        return _result(True, "finding_issued", review=_get_compliance_review_internal(review["compliance_review_id"], connection=conn), event={"compliance_finding_id": fid, "finding_number": number})
    return _workflow_result(lambda: _run_workflow("issue_finding", compliance_review_id=compliance_review_id, actor_context=actor_context, authority_basis=authority_basis, handler=handler))


def acknowledge_review_finding(*, compliance_review_id, compliance_finding_id, actor_context, authority_basis, dispute_basis=None):
    def handler(conn, review):
        actor_id, _label = _actor(actor_context)
        fid = _safe_id(compliance_finding_id, "compliance_finding_id", required=True)
        disputed = 1 if dispute_basis else 0
        status = "disputed" if disputed else "acknowledged"
        conn.execute("UPDATE compliance_review_findings SET status = ?, disputed = ?, dispute_basis = ?, acknowledged_by = ?, acknowledged_at = ?, updated_at = ? WHERE compliance_finding_id = ? AND compliance_review_id = ?", (status, disputed, _summary(dispute_basis, "dispute_basis"), actor_id, _now(), _now(), fid, review["compliance_review_id"]))
        if conn.total_changes < 1:
            raise ValueError("finding_not_found")
        _append_audit_entry(conn, compliance_review_id=review["compliance_review_id"], entity_type="compliance_review_finding", entity_id=fid, action="finding_acknowledged", actor_context=actor_context, authority_basis=authority_basis, new_state=status, note=dispute_basis or "Finding acknowledged.")
        return _result(True, status, event={"compliance_finding_id": fid})
    return _workflow_result(lambda: _run_workflow("acknowledge_finding", compliance_review_id=compliance_review_id, actor_context=actor_context, authority_basis=authority_basis, handler=handler))


def assign_remediation(*, compliance_review_id, compliance_finding_id, required_action, responsible_party_type, responsible_party_id=None, responsible_party_label=None, due_date=None, actor_context, authority_basis):
    def handler(conn, review):
        actor_id, _label = _actor(actor_context)
        row = conn.execute("SELECT COALESCE(MAX(action_number), 0) + 1 FROM compliance_review_remediations WHERE compliance_review_id = ?", (review["compliance_review_id"],)).fetchone()
        number = int(row[0])
        rid = _allocate_identifier(conn, IDENTIFIER_NAMESPACES["remediation"])
        conn.execute(
            """
            INSERT INTO compliance_review_remediations (
                compliance_remediation_id, compliance_review_id, compliance_finding_id,
                action_number, required_action, responsible_party_type,
                responsible_party_id, responsible_party_label, due_date, status,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'assigned', ?, ?)
            """,
            (rid, review["compliance_review_id"], _safe_id(compliance_finding_id, "compliance_finding_id"), number, _summary(required_action, "required_action", required=True), _scalar(responsible_party_type, "responsible_party_type", required=True, max_length=80), _safe_id(responsible_party_id, "responsible_party_id"), _scalar(responsible_party_label, "responsible_party_label", max_length=255), _scalar(due_date, "due_date", max_length=80), _now(), _now()),
        )
        _touch_review(conn, review["compliance_review_id"], actor_id, status="remediation_required")
        _append_audit_entry(conn, compliance_review_id=review["compliance_review_id"], entity_type="compliance_review_remediation", entity_id=rid, action="remediation_assigned", actor_context=actor_context, authority_basis=authority_basis, previous_state=review["status"], new_state="remediation_required", note=required_action)
        return _result(True, "remediation_assigned", review=_get_compliance_review_internal(review["compliance_review_id"], connection=conn), event={"compliance_remediation_id": rid, "action_number": number})
    return _workflow_result(lambda: _run_workflow("assign_remediation", compliance_review_id=compliance_review_id, actor_context=actor_context, authority_basis=authority_basis, handler=handler))


def submit_remediation(*, compliance_review_id, compliance_remediation_id, completion_evidence, actor_context, authority_basis):
    def handler(conn, review):
        actor_id, _label = _actor(actor_context)
        rid = _safe_id(compliance_remediation_id, "compliance_remediation_id", required=True)
        evidence = _summary(completion_evidence, "completion_evidence", required=True)
        conn.execute("UPDATE compliance_review_remediations SET status = 'submitted_for_verification', completion_evidence = ?, completed_by = ?, completed_at = ?, updated_at = ? WHERE compliance_remediation_id = ? AND compliance_review_id = ?", (evidence, actor_id, _now(), _now(), rid, review["compliance_review_id"]))
        if conn.total_changes < 1:
            raise ValueError("remediation_not_found")
        _touch_review(conn, review["compliance_review_id"], actor_id, status="pending_verification")
        _append_audit_entry(conn, compliance_review_id=review["compliance_review_id"], entity_type="compliance_review_remediation", entity_id=rid, action="remediation_submitted", actor_context=actor_context, authority_basis=authority_basis, new_state="submitted_for_verification", note=evidence)
        return _result(True, "remediation_submitted", review=_get_compliance_review_internal(review["compliance_review_id"], connection=conn))
    return _workflow_result(lambda: _run_workflow("submit_remediation", compliance_review_id=compliance_review_id, actor_context=actor_context, authority_basis=authority_basis, handler=handler))


def verify_remediation(*, compliance_review_id, compliance_remediation_id, verification_result="verified", actor_context, authority_basis):
    def handler(conn, review):
        actor_id, _label = _actor(actor_context)
        rid = _safe_id(compliance_remediation_id, "compliance_remediation_id", required=True)
        row = conn.execute("SELECT completed_by, completion_evidence FROM compliance_review_remediations WHERE compliance_remediation_id = ? AND compliance_review_id = ?", (rid, review["compliance_review_id"])).fetchone()
        if not row:
            raise ValueError("remediation_not_found")
        if not row["completion_evidence"]:
            raise ValueError("completion_evidence_required")
        if row["completed_by"] == actor_id:
            raise PermissionError("self_verification_denied")
        result = _scalar(verification_result, "verification_result", required=True, max_length=80)
        status = "verified" if result == "verified" else "rejected"
        conn.execute("UPDATE compliance_review_remediations SET status = ?, verified_by = ?, verified_at = ?, verification_result = ?, updated_at = ? WHERE compliance_remediation_id = ?", (status, actor_id, _now(), result, _now(), rid))
        _touch_review(conn, review["compliance_review_id"], actor_id, status="pending_approval" if status == "verified" else "remediation_in_progress")
        _append_audit_entry(conn, compliance_review_id=review["compliance_review_id"], entity_type="compliance_review_remediation", entity_id=rid, action="remediation_verified" if status == "verified" else "remediation_rejected", actor_context=actor_context, authority_basis=authority_basis, new_state=status, note=result)
        return _result(True, status, review=_get_compliance_review_internal(review["compliance_review_id"], connection=conn))
    return _workflow_result(lambda: _run_workflow("verify_remediation", compliance_review_id=compliance_review_id, actor_context=actor_context, authority_basis=authority_basis, handler=handler))


def request_exception(*, compliance_review_id, compliance_remediation_id, exception_basis, actor_context, authority_basis):
    def handler(conn, review):
        rid = _safe_id(compliance_remediation_id, "compliance_remediation_id", required=True)
        basis = _summary(exception_basis, "exception_basis", required=True)
        conn.execute("UPDATE compliance_review_remediations SET exception_requested = 1, exception_basis = ?, status = 'waived', updated_at = ? WHERE compliance_remediation_id = ? AND compliance_review_id = ?", (basis, _now(), rid, review["compliance_review_id"]))
        if conn.total_changes < 1:
            raise ValueError("remediation_not_found")
        _append_audit_entry(conn, compliance_review_id=review["compliance_review_id"], entity_type="compliance_review_remediation", entity_id=rid, action="exception_requested", actor_context=actor_context, authority_basis=authority_basis, new_state="exception_requested", note=basis)
        return _result(True, "exception_requested", event={"compliance_remediation_id": rid})
    return _workflow_result(lambda: _run_workflow("request_exception", compliance_review_id=compliance_review_id, actor_context=actor_context, authority_basis=authority_basis, handler=handler))


def approve_exception(*, compliance_review_id, compliance_remediation_id, actor_context, authority_basis):
    def handler(conn, review):
        actor_id, _label = _actor(actor_context)
        rid = _safe_id(compliance_remediation_id, "compliance_remediation_id", required=True)
        row = conn.execute("SELECT completed_by, exception_requested FROM compliance_review_remediations WHERE compliance_remediation_id = ? AND compliance_review_id = ?", (rid, review["compliance_review_id"])).fetchone()
        if not row:
            raise ValueError("remediation_not_found")
        if not row["exception_requested"]:
            raise ValueError("exception_request_required")
        if row["completed_by"] == actor_id:
            raise PermissionError("self_exception_approval_denied")
        conn.execute("UPDATE compliance_review_remediations SET status = 'exception_approved', exception_approved_by = ?, exception_approved_at = ?, updated_at = ? WHERE compliance_remediation_id = ?", (actor_id, _now(), _now(), rid))
        _append_audit_entry(conn, compliance_review_id=review["compliance_review_id"], entity_type="compliance_review_remediation", entity_id=rid, action="exception_approved", actor_context=actor_context, authority_basis=authority_basis, new_state="exception_approved", note="Exception approved.")
        return _result(True, "exception_approved", event={"compliance_remediation_id": rid})
    return _workflow_result(lambda: _run_workflow("approve_exception", compliance_review_id=compliance_review_id, actor_context=actor_context, authority_basis=authority_basis, handler=handler))


def submit_review_for_approval(*, compliance_review_id, actor_context, authority_basis):
    return transition_compliance_review(compliance_review_id=compliance_review_id, action="submit_for_approval", expected_version=_get_compliance_review_internal(compliance_review_id)["version"], actor_context=actor_context, reason=authority_basis, summary="Review submitted for approval.")


def approve_review(*, compliance_review_id, actor_context, authority_basis, approved=True):
    def handler(conn, review):
        actor_id, _label = _actor(actor_context)
        if review["created_by"] == actor_id:
            raise PermissionError("self_approval_denied")
        status = "approved" if approved else "approval_denied"
        conn.execute("INSERT INTO compliance_review_approvals (compliance_approval_id, compliance_review_id, approval_type, requested_by, requested_at, approved_by, approved_at, approval_status, authority_basis, maker_actor_id, checker_actor_id, note) VALUES (?, ?, 'review_approval', ?, ?, ?, ?, ?, ?, ?, ?, ?)", (_allocate_identifier(conn, IDENTIFIER_NAMESPACES["approval"]), review["compliance_review_id"], review["updated_by"], _now(), actor_id, _now(), status, authority_basis, review["created_by"], actor_id, "Review approval decision."))
        _touch_review(conn, review["compliance_review_id"], actor_id, status="approved" if approved else review["status"])
        _append_audit_entry(conn, compliance_review_id=review["compliance_review_id"], entity_type="compliance_review", entity_id=review["compliance_review_id"], action="approval_granted" if approved else "approval_denied", actor_context=actor_context, authority_basis=authority_basis, previous_state=review["status"], new_state="approved" if approved else review["status"], note="Review approval decision.")
        return _result(True, status, review=_get_compliance_review_internal(review["compliance_review_id"], connection=conn))
    return _workflow_result(lambda: _run_workflow("approve_review", compliance_review_id=compliance_review_id, actor_context=actor_context, authority_basis=authority_basis, handler=handler))


def certify_review(*, compliance_review_id, certification_statement, actor_context, authority_basis, effective_date=None, expiration_date=None):
    def handler(conn, review):
        actor_id, _label = _actor(actor_context)
        if review["created_by"] == actor_id or review.get("assigned_reviewer") == actor_id:
            raise PermissionError("self_certification_denied")
        cid = _allocate_identifier(conn, IDENTIFIER_NAMESPACES["certification"])
        conn.execute("INSERT INTO compliance_review_certifications (certification_id, compliance_review_id, certification_type, certification_statement, certified_by, authority_basis, certified_at, effective_date, expiration_date, certification_status) VALUES (?, ?, 'review_certification', ?, ?, ?, ?, ?, ?, 'active')", (cid, review["compliance_review_id"], _summary(certification_statement, "certification_statement", required=True), actor_id, authority_basis, _now(), _scalar(effective_date, "effective_date", max_length=80), _scalar(expiration_date, "expiration_date", max_length=80)))
        _touch_review(conn, review["compliance_review_id"], actor_id, status="certified")
        _append_audit_entry(conn, compliance_review_id=review["compliance_review_id"], entity_type="compliance_review_certification", entity_id=cid, action="certification_issued", actor_context=actor_context, authority_basis=authority_basis, previous_state=review["status"], new_state="certified", note=certification_statement)
        return _result(True, "certified", review=_get_compliance_review_internal(review["compliance_review_id"], connection=conn), event={"certification_id": cid})
    return _workflow_result(lambda: _run_workflow("certify_review", compliance_review_id=compliance_review_id, actor_context=actor_context, authority_basis=authority_basis, handler=handler))


def close_review(*, compliance_review_id, actor_context, authority_basis):
    return transition_compliance_review(compliance_review_id=compliance_review_id, action="close", expected_version=_get_compliance_review_internal(compliance_review_id)["version"], actor_context=actor_context, reason=authority_basis, summary="Review closed.")


def reopen_review(*, compliance_review_id, reason, actor_context, authority_basis):
    try:
        if not _summary(reason, "reason", required=True):
            return _result(False, "invalid_input", "reason_required")
    except ValueError as exc:
        return _result(False, "invalid_input", str(exc))
    if not _summary(reason, "reason", required=True):
        return _result(False, "invalid_input", "reason_required")
    return transition_compliance_review(compliance_review_id=compliance_review_id, action="reopen", expected_version=_get_compliance_review_internal(compliance_review_id)["version"], actor_context=actor_context, reason=authority_basis, summary=reason)


def supersede_review(*, compliance_review_id, successor_review_id, actor_context, authority_basis):
    def handler(conn, review):
        actor_id, _label = _actor(actor_context)
        successor = validate_public_compliance_review_id(successor_review_id)
        conn.execute("UPDATE compliance_reviews SET superseded_by = ?, status = 'superseded', is_active = 0, version = version + 1, updated_by = ?, updated_at = ? WHERE compliance_review_id = ?", (successor, actor_id, _now(), review["compliance_review_id"]))
        _append_audit_entry(conn, compliance_review_id=review["compliance_review_id"], entity_type="compliance_review", entity_id=review["compliance_review_id"], action="review_superseded", actor_context=actor_context, authority_basis=authority_basis, previous_state=review["status"], new_state="superseded", note=successor)
        return _result(True, "superseded", review=_get_compliance_review_internal(review["compliance_review_id"], connection=conn))
    return _workflow_result(lambda: _run_workflow("supersede_review", compliance_review_id=compliance_review_id, actor_context=actor_context, authority_basis=authority_basis, handler=handler))


def archive_review(*, compliance_review_id, actor_context, authority_basis):
    return transition_compliance_review(compliance_review_id=compliance_review_id, action="archive", expected_version=_get_compliance_review_internal(compliance_review_id)["version"], actor_context=actor_context, reason=authority_basis, summary="Review archived.")


def append_compliance_audit_entry(*, compliance_review_id, entity_type, entity_id, action, actor_context, authority_basis, previous_state=None, new_state=None, note=""):
    def handler(conn, review):
        entry = _append_audit_entry(conn, compliance_review_id=review["compliance_review_id"], entity_type=entity_type, entity_id=entity_id, action=action, actor_context=actor_context, authority_basis=authority_basis, previous_state=previous_state, new_state=new_state, note=note)
        return _result(True, "audit_appended", event=entry)
    return _workflow_result(lambda: _run_workflow("add_relationship", compliance_review_id=compliance_review_id, actor_context=actor_context, authority_basis=authority_basis, handler=handler))


def generate_compliance_evidence_id(connection=None):
    return _generate_external_identifier("evidence", connection)


def generate_compliance_finding_id(connection=None):
    return _generate_external_identifier("finding", connection)


def generate_compliance_remediation_id(connection=None):
    return _generate_external_identifier("remediation", connection)


def generate_compliance_approval_id(connection=None):
    return _generate_external_identifier("approval", connection)


def generate_compliance_certification_id(connection=None):
    return _generate_external_identifier("certification", connection)


def generate_compliance_relationship_id(connection=None):
    return _generate_external_identifier("relationship", connection)


def generate_compliance_audit_id(connection=None):
    return _generate_external_identifier("audit", connection)


def _generate_external_identifier(kind, connection=None):
    owns = connection is None
    conn = connection or get_connection()
    try:
        return _allocate_identifier(conn, IDENTIFIER_NAMESPACES[kind])
    finally:
        if owns:
            conn.close()


__all__ = [
    "activation_status",
    "add_review_evidence",
    "add_review_relationship",
    "add_review_subject",
    "append_compliance_audit_entry",
    "approve_exception",
    "approve_review",
    "archive_review",
    "assign_remediation",
    "assign_reviewer",
    "certify_review",
    "close_review",
    "create_compliance_review",
    "foundation_available",
    "generate_compliance_approval_id",
    "generate_compliance_audit_id",
    "generate_compliance_certification_id",
    "generate_compliance_evidence_id",
    "generate_compliance_finding_id",
    "generate_compliance_relationship_id",
    "generate_compliance_remediation_id",
    "generate_compliance_review_id",
    "get_compliance_review",
    "get_compliance_review_by_id",
    "get_compliance_review_by_public_id",
    "issue_review_finding",
    "acknowledge_review_finding",
    "list_compliance_audit_entries",
    "list_compliance_review_events",
    "list_compliance_review_relationships",
    "list_compliance_reviews",
    "reopen_review",
    "request_exception",
    "submit_remediation",
    "submit_review_for_approval",
    "supersede_review",
    "transition_compliance_review",
    "update_compliance_review",
    "validate_review_transition",
    "validate_compliance_review_scope",
    "validate_public_compliance_review_id",
    "verify_compliance_audit_chain",
    "verify_remediation",
    "verify_review_evidence",
]
