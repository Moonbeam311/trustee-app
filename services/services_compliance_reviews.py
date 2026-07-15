from datetime import datetime, UTC
import hashlib
import json
import re

from database.db import get_connection
from migrations.add_compliance_review_foundation import ensure_compliance_review_foundation
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


def _read_schema_available(conn):
    placeholders = ", ".join("?" for _ in REQUIRED_READ_TABLES)
    rows = conn.execute(
        f"SELECT name FROM sqlite_master WHERE type = 'table' AND name IN ({placeholders})",
        tuple(sorted(REQUIRED_READ_TABLES)),
    ).fetchall()
    names = {row[0] for row in rows}
    return names == REQUIRED_READ_TABLES


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
                "message": (
                    "Compliance Review persistence is not currently available because the "
                    "institutional foundation for this registry has not been activated. "
                    "No review record was created, no migration occurred, and changing "
                    "operator permissions will not activate the registry. Authorized "
                    "institutional activation is required."
                ),
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
    ensure_compliance_review_foundation()
    conn = get_connection()
    try:
        actor_id, actor_label = _actor(actor_context)
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
    except ValueError as exc:
        return _result(False, "invalid_input", str(exc))
    except Exception:
        return _result(False, "unexpected_failure", "Compliance Review could not be created.")
    finally:
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
    ensure_compliance_review_foundation()
    conn = get_connection()
    try:
        actor_id, actor_label = _actor(actor_context)
        review_id = validate_public_compliance_review_id(compliance_review_id)
        action = _scalar(action, "action", required=True, max_length=80, lowercase=True)
        action = action.replace(" ", "_")
        if action in RESERVED_COMPLIANCE_REVIEW_ACTIONS:
            return _result(False, "reserved_workflow_not_active", "This Compliance Review workflow is reserved for a later milestone.")
        try:
            expected_version = int(expected_version)
        except Exception as exc:
            raise ValueError("expected_version_invalid") from exc
        reason = _summary(reason, "reason", required=True)
        summary = _summary(summary, "summary", required=True)
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
            transition = COMPLIANCE_REVIEW_TRANSITIONS.get((current_status, action))
            if not transition:
                conn.rollback()
                return _result(False, "invalid_transition", "Compliance Review transition is not allowed.")
            if current_status not in OPEN_COMPLIANCE_REVIEW_STATES:
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


__all__ = [
    "create_compliance_review",
    "ensure_compliance_review_foundation",
    "get_compliance_review",
    "get_compliance_review_by_id",
    "get_compliance_review_by_public_id",
    "list_compliance_review_events",
    "list_compliance_review_relationships",
    "list_compliance_reviews",
    "transition_compliance_review",
    "validate_compliance_review_scope",
    "validate_public_compliance_review_id",
]
