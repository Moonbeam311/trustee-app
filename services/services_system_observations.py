from datetime import datetime, UTC
import re

from database.db import get_connection
from migrations.add_system_observation_registry import ensure_system_observation_registry
from models.models_system_observations import (
    CLOSED_STATES,
    CONDITION_CODE_REGISTRY,
    CONTEXT_SCOPES,
    EVENT_TYPES,
    LIFECYCLE_STATES,
    OBSERVATION_TYPES,
    OPEN_STATES,
    PANEL_TYPE_MAP,
    PERSISTENCE_TRIGGERS,
)


SUMMARY_LIMIT = 1000
SCALAR_LIMIT = 120
IDEMPOTENCY_LIMIT = 120
READ_LIMIT = 250
PUBLIC_OBSERVATION_ID_RE = re.compile(r"^SYSOBS-\d{4}-\d{6}$")
ALLOWED_RELATED_RECORD_TYPES = {
    "Archive",
    "Compliance",
    "Governance",
    "Matter",
    "People",
    "Restricted Procedure Governance",
    "System Audit",
}
SENSITIVE_MARKERS = {
    "password",
    "password_hash",
    "credential",
    "token",
    "cookie",
    "session id",
    "traceback",
    "stack trace",
    "database path",
    "connection string",
    "permission matrix",
    "repair command",
    "bootstrap credential",
    "reset credential",
}

OBSERVATION_TYPE_LABELS = {
    key: key.replace("_", " ").title()
    for key in OBSERVATION_TYPES
}
PANEL_LABELS = {
    "protected_user_accounts": "Protected User Accounts",
    "application_permission_controls": "Application Permission Controls",
    "authentication_session_security": "Authentication and Session Security",
    "audit_security_oversight": "Audit and Security Oversight",
    "backup_data_preservation": "Backup and Data Preservation",
    "deployment_production_health": "Deployment and Production Health",
    "database_migration_posture": "Database and Migration Posture",
    "feature_flags_operating_policy": "Feature Flags and Operating Policy",
    "institutional_role_assignments": "Institutional Role Assignments",
    "recovery_repair_controls": "Recovery and Repair Controls",
}
CONTEXT_SCOPE_LABELS = {
    "platform_scoped": "Platform-Wide Observation",
    "deployment_scoped": "Deployment-Scoped Observation",
    "firm_scoped": "Firm-Scoped Observation",
    "institution_scoped": "Institution-Scoped Observation",
    "trust_scoped": "Trust-Scoped Observation",
    "matter_scoped": "Matter-Scoped Observation",
}

TRANSITIONS = {
    ("acknowledged", "under_review", "investigation_started"): {
        "requires_reason": True,
        "requires_related": False,
    },
    ("under_review", "deferred", "deferred"): {
        "requires_reason": True,
        "requires_related": False,
    },
    ("deferred", "under_review", "investigation_started"): {
        "requires_reason": True,
        "requires_related": False,
    },
    ("acknowledged", "closed_no_action", "closed_no_action"): {
        "requires_reason": True,
        "requires_related": False,
    },
    ("under_review", "closed_resolved", "closed_resolved"): {
        "requires_reason": True,
        "requires_related": True,
    },
    ("closed_no_action", "under_review", "reopened"): {
        "requires_reason": True,
        "requires_related": False,
    },
    ("closed_resolved", "under_review", "reopened"): {
        "requires_reason": True,
        "requires_related": False,
    },
    ("acknowledged", "superseded", "superseded"): {
        "requires_reason": True,
        "requires_related": False,
    },
    ("under_review", "superseded", "superseded"): {
        "requires_reason": True,
        "requires_related": False,
    },
    ("deferred", "superseded", "superseded"): {
        "requires_reason": True,
        "requires_related": False,
    },
    ("routed", "superseded", "superseded"): {
        "requires_reason": True,
        "requires_related": False,
    },
}


def _now():
    return datetime.now(UTC).isoformat(timespec="seconds")


def _result(ok, status, message="", observation=None, event=None, events=None):
    data = {"ok": bool(ok), "status": status}
    if message:
        data["message"] = message
    if observation is not None:
        data["observation"] = observation
    if event is not None:
        data["event"] = event
    if events is not None:
        data["events"] = events
    return data


def _scalar(value, field, required=False, max_length=SCALAR_LIMIT, lowercase=False, uppercase=False):
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
    if uppercase:
        text = text.upper()
    return text


def _summary(value, field, required=False):
    text = _scalar(value, field, required=required, max_length=SUMMARY_LIMIT)
    if text is None:
        return ""
    lowered = text.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        raise ValueError(f"{field}_sensitive")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _actor(actor_context):
    if not isinstance(actor_context, dict):
        raise ValueError("actor_required")
    actor_id = _scalar(actor_context.get("actor_id"), "actor_id", required=True)
    actor_label = _scalar(actor_context.get("actor_label") or actor_id, "actor_label", required=True, max_length=255)
    return actor_id, actor_label


def _normalize_context(context):
    if not isinstance(context, dict):
        raise ValueError("context_required")
    scope = _scalar(context.get("context_scope"), "context_scope", required=True, lowercase=True)
    if scope not in CONTEXT_SCOPES:
        raise ValueError("context_scope_invalid")

    values = {
        "firm_id": _scalar(context.get("firm_id"), "firm_id"),
        "institution_id": _scalar(context.get("institution_id"), "institution_id"),
        "trust_id": _scalar(context.get("trust_id"), "trust_id"),
        "matter_id": _scalar(context.get("matter_id"), "matter_id"),
        "deployment_key": _scalar(context.get("deployment_key"), "deployment_key"),
    }

    allowed = {
        "platform_scoped": set(),
        "deployment_scoped": {"deployment_key"},
        "firm_scoped": {"firm_id"},
        "institution_scoped": {"institution_id"},
        "trust_scoped": {"trust_id"},
        "matter_scoped": {"matter_id"},
    }[scope]
    required = next(iter(allowed), None)

    for key, value in values.items():
        if value and key not in allowed:
            raise ValueError("context_conflict")
    if required and not values.get(required):
        raise ValueError("context_required_identifier")

    context_id = values.get(required) if required else "platform"
    return {
        "context_scope": scope,
        "context_id": context_id,
        **values,
    }


def _active_duplicate_key(observation_type, condition_code, context):
    return "|".join(
        [
            observation_type,
            condition_code,
            context["context_scope"],
            context["context_id"] or "",
        ]
    )


def _row_dict(row):
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def _public_observation(row):
    data = _row_dict(row)
    if not data:
        return None
    data.pop("id", None)
    return data


def _public_event(row):
    data = _row_dict(row)
    if not data:
        return None
    data.pop("id", None)
    return data


def _allocate_public_id(conn, namespace):
    if namespace not in {"SYSOBS", "SYSEVT"}:
        raise ValueError("namespace_invalid")
    year = datetime.now(UTC).year
    conn.execute(
        """
        INSERT OR IGNORE INTO system_observation_number_sequences
            (namespace, sequence_year, last_number, created_at, updated_at)
        VALUES (?, ?, 0, ?, ?)
        """,
        (namespace, year, _now(), _now()),
    )
    conn.execute(
        """
        UPDATE system_observation_number_sequences
        SET last_number = last_number + 1, updated_at = ?
        WHERE namespace = ? AND sequence_year = ?
        """,
        (_now(), namespace, year),
    )
    row = conn.execute(
        """
        SELECT last_number
        FROM system_observation_number_sequences
        WHERE namespace = ? AND sequence_year = ?
        """,
        (namespace, year),
    ).fetchone()
    return f"{namespace}-{year}-{int(row['last_number']):06d}"


def _insert_event(
    conn,
    observation_id,
    event_type,
    prior_state,
    resulting_state,
    actor_id,
    actor_label,
    event_summary="",
    reason_code=None,
    authority_record_type=None,
    authority_record_id=None,
    related_record_type=None,
    related_record_id=None,
    idempotency_key=None,
):
    event_id = _allocate_public_id(conn, "SYSEVT")
    created_at = _now()
    conn.execute(
        """
        INSERT INTO system_observation_events (
            observation_event_id, observation_id, event_type, prior_state,
            resulting_state, actor_id, actor_label, authority_record_type,
            authority_record_id, event_summary, reason_code, related_record_type,
            related_record_id, idempotency_key, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            observation_id,
            event_type,
            prior_state,
            resulting_state,
            actor_id,
            actor_label,
            authority_record_type,
            authority_record_id,
            event_summary,
            reason_code,
            related_record_type,
            related_record_id,
            idempotency_key,
            created_at,
        ),
    )
    return event_id


def _update_observation_projection(conn, observation_id, target_state, actor_id, active_duplicate_key, expected_version):
    row = conn.execute(
        "SELECT version FROM system_observations WHERE observation_id = ?",
        (observation_id,),
    ).fetchone()
    if not row or int(row["version"]) != int(expected_version):
        raise RuntimeError("stale_version")
    conn.execute(
        """
        UPDATE system_observations
        SET current_state = ?,
            active_duplicate_key = ?,
            version = version + 1,
            last_observed_at = ?,
            updated_by = ?,
            updated_at = ?
        WHERE observation_id = ? AND version = ?
        """,
        (target_state, active_duplicate_key, _now(), actor_id, _now(), observation_id, expected_version),
    )
    if conn.total_changes < 1:
        raise RuntimeError("stale_version")


def ensure_system_observation_tables():
    return ensure_system_observation_registry()


def validate_public_observation_id(observation_id):
    value = _scalar(observation_id, "observation_id", required=True, uppercase=True)
    if not re.fullmatch(r"SYSOBS-\d{4}-\d{6}", value):
        raise ValueError("observation_id_invalid")
    return value


def _validate_foundation_fields(observation_type, panel_key, condition_code, persistence_trigger, context):
    observation_type = _scalar(observation_type, "observation_type", required=True, lowercase=True)
    panel_key = _scalar(panel_key, "panel_key", required=True, lowercase=True)
    condition_code = _scalar(condition_code, "condition_code", required=True, lowercase=True)
    persistence_trigger = _scalar(persistence_trigger, "persistence_trigger", required=True, lowercase=True)
    if observation_type not in OBSERVATION_TYPES:
        raise ValueError("observation_type_invalid")
    if PANEL_TYPE_MAP.get(panel_key) != observation_type:
        raise ValueError("panel_type_mismatch")
    condition = CONDITION_CODE_REGISTRY.get(condition_code)
    if not condition or condition["observation_type"] != observation_type:
        raise ValueError("condition_code_invalid")
    if persistence_trigger not in PERSISTENCE_TRIGGERS:
        raise ValueError("persistence_trigger_invalid")
    if persistence_trigger not in condition["persistence_triggers"]:
        raise ValueError("persistence_trigger_not_allowed")
    if context["context_scope"] not in condition["context_scopes"]:
        raise ValueError("context_scope_not_allowed")
    return observation_type, panel_key, condition_code, persistence_trigger


def _check_idempotency(conn, idempotency_key, observation_id=None, event_type=None, resulting_state=None, event_summary=None, reason_code=None):
    if not idempotency_key:
        return None
    row = conn.execute(
        """
        SELECT *
        FROM system_observation_events
        WHERE idempotency_key = ?
        """,
        (idempotency_key,),
    ).fetchone()
    if not row:
        return None
    if observation_id and row["observation_id"] != observation_id:
        raise RuntimeError("idempotency_conflict")
    if event_type and row["event_type"] != event_type:
        raise RuntimeError("idempotency_conflict")
    if resulting_state and row["resulting_state"] != resulting_state:
        raise RuntimeError("idempotency_conflict")
    if event_summary is not None and (row["event_summary"] or "") != event_summary:
        raise RuntimeError("idempotency_conflict")
    if reason_code is not None and (row["reason_code"] or "") != (reason_code or ""):
        raise RuntimeError("idempotency_conflict")
    return row


def create_system_observation(
    *,
    observation_type,
    condition_code,
    panel_key,
    persistence_trigger,
    context,
    sanitized_summary,
    actor_context,
    initial_state="acknowledged",
    idempotency_key=None,
    prior_occurrence_id=None,
):
    ensure_system_observation_tables()
    conn = get_connection()
    try:
        actor_id, actor_label = _actor(actor_context)
        context_data = _normalize_context(context)
        observation_type, panel_key, condition_code, persistence_trigger = _validate_foundation_fields(
            observation_type,
            panel_key,
            condition_code,
            persistence_trigger,
            context_data,
        )
        initial_state = _scalar(initial_state, "initial_state", required=True, lowercase=True)
        if initial_state not in OPEN_STATES:
            raise ValueError("initial_state_invalid")
        sanitized_summary = _summary(sanitized_summary, "sanitized_summary", required=True)
        idempotency_key = _scalar(idempotency_key, "idempotency_key", max_length=IDEMPOTENCY_LIMIT)
        prior_occurrence_id = (
            validate_public_observation_id(prior_occurrence_id)
            if prior_occurrence_id
            else None
        )
        duplicate_key = _active_duplicate_key(observation_type, condition_code, context_data)

        conn.execute("BEGIN IMMEDIATE")
        try:
            replay = _check_idempotency(conn, idempotency_key, event_type="observation_created")
            if replay:
                observation = get_system_observation(replay["observation_id"], connection=conn)
                conn.commit()
                return _result(True, "idempotent_replay", observation=observation, event=_public_event(replay))

            duplicate = conn.execute(
                """
                SELECT *
                FROM system_observations
                WHERE active_duplicate_key = ?
                """,
                (duplicate_key,),
            ).fetchone()
            if duplicate:
                conn.commit()
                return _result(
                    False,
                    "duplicate_observation",
                    "An open observation already exists for this condition and context.",
                    observation=_public_observation(duplicate),
                )

            observation_id = _allocate_public_id(conn, "SYSOBS")
            now = _now()
            conn.execute(
                """
                INSERT INTO system_observations (
                    observation_id, observation_type, panel_key, condition_code,
                    current_state, persistence_trigger, context_scope, context_id,
                    firm_id, institution_id, trust_id, matter_id, deployment_key,
                    sanitized_summary, first_observed_at, last_observed_at,
                    prior_occurrence_id, superseded_by_observation_id,
                    active_duplicate_key, version, created_by, created_at,
                    updated_by, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, 1, ?, ?, ?, ?)
                """,
                (
                    observation_id,
                    observation_type,
                    panel_key,
                    condition_code,
                    initial_state,
                    persistence_trigger,
                    context_data["context_scope"],
                    context_data["context_id"],
                    context_data["firm_id"],
                    context_data["institution_id"],
                    context_data["trust_id"],
                    context_data["matter_id"],
                    context_data["deployment_key"],
                    sanitized_summary,
                    now,
                    now,
                    prior_occurrence_id,
                    duplicate_key,
                    actor_id,
                    now,
                    actor_id,
                    now,
                ),
            )
            event_id = _insert_event(
                conn,
                observation_id,
                "observation_created",
                None,
                initial_state,
                actor_id,
                actor_label,
                event_summary=sanitized_summary,
                idempotency_key=idempotency_key,
            )
            observation = get_system_observation(observation_id, connection=conn)
            event = _public_event(
                conn.execute(
                    "SELECT * FROM system_observation_events WHERE observation_event_id = ?",
                    (event_id,),
                ).fetchone()
            )
            conn.commit()
            return _result(True, "created", observation=observation, event=event)
        except Exception:
            conn.rollback()
            raise
    except ValueError as exc:
        return _result(False, "invalid_input", str(exc))
    except RuntimeError as exc:
        return _result(False, "conflict", str(exc))
    except Exception:
        return _result(False, "unexpected_failure", "System observation could not be created.")
    finally:
        conn.close()


def transition_system_observation(
    *,
    observation_id,
    target_state,
    event_type,
    expected_version,
    actor_context,
    reason=None,
    event_summary="",
    idempotency_key=None,
    authority_record_type=None,
    authority_record_id=None,
    related_record_type=None,
    related_record_id=None,
    superseded_by_observation_id=None,
):
    ensure_system_observation_tables()
    conn = get_connection()
    try:
        actor_id, actor_label = _actor(actor_context)
        observation_id = validate_public_observation_id(observation_id)
        target_state = _scalar(target_state, "target_state", required=True, lowercase=True)
        event_type = _scalar(event_type, "event_type", required=True, lowercase=True)
        reason = _scalar(reason, "reason_code", max_length=SCALAR_LIMIT, lowercase=True)
        event_summary = _summary(event_summary, "event_summary")
        idempotency_key = _scalar(idempotency_key, "idempotency_key", max_length=IDEMPOTENCY_LIMIT)
        authority_record_type = _scalar(authority_record_type, "authority_record_type")
        authority_record_id = _scalar(authority_record_id, "authority_record_id")
        related_record_type = _scalar(related_record_type, "related_record_type")
        related_record_id = _scalar(related_record_id, "related_record_id")
        if event_type not in EVENT_TYPES:
            raise ValueError("event_type_invalid")
        if target_state not in LIFECYCLE_STATES:
            raise ValueError("target_state_invalid")
        expected_version = int(expected_version)
        superseded_by_observation_id = (
            validate_public_observation_id(superseded_by_observation_id)
            if superseded_by_observation_id
            else None
        )

        conn.execute("BEGIN IMMEDIATE")
        try:
            observation = conn.execute(
                "SELECT * FROM system_observations WHERE observation_id = ?",
                (observation_id,),
            ).fetchone()
            if not observation:
                conn.rollback()
                return _result(False, "not_found", "Observation not found.")

            replay = _check_idempotency(
                conn,
                idempotency_key,
                observation_id=observation_id,
                event_type=event_type,
                resulting_state=target_state,
                event_summary=event_summary,
                reason_code=reason,
            )
            if replay:
                conn.commit()
                return _result(
                    True,
                    "idempotent_replay",
                    observation=get_system_observation(observation_id, connection=conn),
                    event=_public_event(replay),
                )

            prior_state = observation["current_state"]
            rule = TRANSITIONS.get((prior_state, target_state, event_type))
            if not rule:
                conn.rollback()
                return _result(False, "invalid_transition", "Transition is not allowed.")
            if int(observation["version"]) != expected_version:
                conn.rollback()
                return _result(False, "stale_version", "Observation changed before this transition.")
            if rule["requires_reason"] and not reason:
                raise ValueError("reason_required")
            if rule["requires_related"] and not (related_record_type and related_record_id):
                raise ValueError("related_record_required")

            active_key = observation["active_duplicate_key"]
            if target_state in CLOSED_STATES:
                active_key = None
            elif target_state in OPEN_STATES and not active_key:
                active_key = _active_duplicate_key(
                    observation["observation_type"],
                    observation["condition_code"],
                    {
                        "context_scope": observation["context_scope"],
                        "context_id": observation["context_id"],
                    },
                )

            event_id = _insert_event(
                conn,
                observation_id,
                event_type,
                prior_state,
                target_state,
                actor_id,
                actor_label,
                event_summary=event_summary,
                reason_code=reason,
                authority_record_type=authority_record_type,
                authority_record_id=authority_record_id,
                related_record_type=related_record_type,
                related_record_id=related_record_id,
                idempotency_key=idempotency_key,
            )
            if event_type == "superseded" and superseded_by_observation_id:
                conn.execute(
                    """
                    UPDATE system_observations
                    SET superseded_by_observation_id = ?
                    WHERE observation_id = ?
                    """,
                    (superseded_by_observation_id, observation_id),
                )
            _update_observation_projection(
                conn,
                observation_id,
                target_state,
                actor_id,
                active_key,
                expected_version,
            )
            observation_after = get_system_observation(observation_id, connection=conn)
            event = _public_event(
                conn.execute(
                    "SELECT * FROM system_observation_events WHERE observation_event_id = ?",
                    (event_id,),
                ).fetchone()
            )
            conn.commit()
            return _result(True, "transitioned", observation=observation_after, event=event)
        except Exception:
            conn.rollback()
            raise
    except ValueError as exc:
        return _result(False, "invalid_input", str(exc))
    except RuntimeError as exc:
        if str(exc) == "stale_version":
            return _result(False, "stale_version", "Observation changed before this transition.")
        if str(exc) == "idempotency_conflict":
            return _result(False, "conflict", "Idempotency key conflicts with a prior operation.")
        return _result(False, "unexpected_failure", "System observation could not be transitioned.")
    except Exception:
        return _result(False, "unexpected_failure", "System observation could not be transitioned.")
    finally:
        conn.close()


def get_system_observation(observation_id, connection=None):
    owns = connection is None
    conn = connection or get_connection()
    try:
        observation_id = validate_public_observation_id(observation_id)
        row = conn.execute(
            "SELECT * FROM system_observations WHERE observation_id = ?",
            (observation_id,),
        ).fetchone()
        return _public_observation(row)
    except ValueError:
        return None
    finally:
        if owns:
            conn.close()


def list_system_observation_events(observation_id):
    ensure_system_observation_tables()
    conn = get_connection()
    try:
        observation_id = validate_public_observation_id(observation_id)
        rows = conn.execute(
            """
            SELECT *
            FROM system_observation_events
            WHERE observation_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (observation_id,),
        ).fetchall()
        return [_public_event(row) for row in rows]
    except ValueError:
        return []
    finally:
        conn.close()


def find_open_duplicate(observation_type, condition_code, context):
    ensure_system_observation_tables()
    conn = get_connection()
    try:
        context_data = _normalize_context(context)
        observation_type = _scalar(observation_type, "observation_type", required=True, lowercase=True)
        condition_code = _scalar(condition_code, "condition_code", required=True, lowercase=True)
        duplicate_key = _active_duplicate_key(observation_type, condition_code, context_data)
        row = conn.execute(
            "SELECT * FROM system_observations WHERE active_duplicate_key = ?",
            (duplicate_key,),
        ).fetchone()
        return _public_observation(row)
    except ValueError:
        return None
    finally:
        conn.close()


def list_system_observations(filters=None, limit=100):
    ensure_system_observation_tables()
    filters = filters or {}
    limit = max(1, min(int(limit or 100), 250))
    allowed_filters = {
        "observation_type",
        "condition_code",
        "current_state",
        "context_scope",
        "firm_id",
        "trust_id",
        "matter_id",
    }
    where = []
    params = []
    for key in sorted(set(filters) & allowed_filters):
        value = _scalar(filters.get(key), key)
        if value:
            where.append(f"{key} = ?")
            params.append(value)
    sql = "SELECT * FROM system_observations"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC, observation_id DESC LIMIT ?"
    params.append(limit)
    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [_public_observation(row) for row in rows]
    finally:
        conn.close()


def _tables_available(conn):
    names = {
        row["name"]
        for row in conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name IN ('system_observations', 'system_observation_events')
            """
        ).fetchall()
    }
    return {
        "available": names == {"system_observations", "system_observation_events"},
        "missing": sorted({"system_observations", "system_observation_events"} - names),
    }


def system_observation_registry_available():
    conn = get_connection()
    try:
        return _tables_available(conn)
    except Exception:
        return {
            "available": False,
            "missing": ["system_observations", "system_observation_events"],
        }
    finally:
        conn.close()


def _label_key(value):
    return (value or "").replace("_", " ").title()


def _bounded_reference_type(value):
    text = _scalar(value, "related_record_type")
    if not text:
        return None
    for allowed in ALLOWED_RELATED_RECORD_TYPES:
        if text.lower() == allowed.lower():
            return allowed
    return None


def _record_reference(record_type, record_id):
    safe_type = _bounded_reference_type(record_type)
    safe_id = _scalar(record_id, "related_record_id")
    if not (safe_type and safe_id):
        return None
    return {
        "type": safe_type,
        "record_id": safe_id,
        "link": None,
        "caution": "Review the governed destination record for authoritative status and scope.",
    }


def _context_values(observation):
    scope = observation.get("context_scope")
    if scope == "platform_scoped":
        return {
            "scope": scope,
            "scope_label": CONTEXT_SCOPE_LABELS.get(scope, _label_key(scope)),
            "display": "Platform-wide observation",
            "items": [],
        }

    candidates = [
        ("firm_id", "Firm"),
        ("institution_id", "Institution"),
        ("trust_id", "Trust"),
        ("matter_id", "Matter"),
        ("deployment_key", "Deployment"),
    ]
    items = [
        {"label": label, "value": observation.get(key)}
        for key, label in candidates
        if observation.get(key)
    ]
    display = " / ".join(item["value"] for item in items) if items else "Bounded context"
    return {
        "scope": scope,
        "scope_label": CONTEXT_SCOPE_LABELS.get(scope, _label_key(scope)),
        "display": display,
        "items": items,
    }


def _state_rank(state):
    if state in OPEN_STATES:
        return 0
    if state in CLOSED_STATES:
        return 1
    return 2


def _observation_visible(observation, scope=None):
    if not observation:
        return False
    scope = scope or {}
    if scope.get("global"):
        return True

    allowed_firm_id = _scalar(scope.get("firm_id"), "firm_id")
    if not allowed_firm_id:
        return False

    observation_firm = observation.get("firm_id")
    if observation_firm:
        return observation_firm == allowed_firm_id

    if observation.get("context_scope") == "firm_scoped":
        return observation.get("context_id") == allowed_firm_id

    return False


def _view_observation(observation):
    if not observation:
        return None
    condition = CONDITION_CODE_REGISTRY.get(observation.get("condition_code"), {})
    context = _context_values(observation)
    return {
        "observation_id": observation.get("observation_id"),
        "observation_type": observation.get("observation_type"),
        "observation_type_label": OBSERVATION_TYPE_LABELS.get(
            observation.get("observation_type"),
            _label_key(observation.get("observation_type")),
        ),
        "panel_key": observation.get("panel_key"),
        "panel_label": PANEL_LABELS.get(
            observation.get("panel_key"),
            _label_key(observation.get("panel_key")),
        ),
        "condition_code": observation.get("condition_code"),
        "condition_label": condition.get("label") or _label_key(observation.get("condition_code")),
        "current_state": observation.get("current_state"),
        "current_state_label": _label_key(observation.get("current_state")),
        "persistence_trigger": observation.get("persistence_trigger"),
        "persistence_trigger_label": _label_key(observation.get("persistence_trigger")),
        "context": context,
        "context_scope": observation.get("context_scope"),
        "context_display": context.get("display"),
        "sanitized_summary": observation.get("sanitized_summary") or "",
        "first_observed_at": observation.get("first_observed_at"),
        "last_observed_at": observation.get("last_observed_at"),
        "version": observation.get("version"),
        "prior_occurrence_id": observation.get("prior_occurrence_id"),
        "superseded_by_observation_id": observation.get("superseded_by_observation_id"),
        "created_by": observation.get("created_by"),
        "created_at": observation.get("created_at"),
        "updated_by": observation.get("updated_by"),
        "updated_at": observation.get("updated_at"),
    }


def _view_event(event):
    reference = _record_reference(event.get("related_record_type"), event.get("related_record_id"))
    authority = _record_reference(event.get("authority_record_type"), event.get("authority_record_id"))
    return {
        "observation_event_id": event.get("observation_event_id"),
        "event_type": event.get("event_type"),
        "event_type_label": _label_key(event.get("event_type")),
        "prior_state": event.get("prior_state"),
        "prior_state_label": _label_key(event.get("prior_state")),
        "resulting_state": event.get("resulting_state"),
        "resulting_state_label": _label_key(event.get("resulting_state")),
        "actor_label": event.get("actor_label"),
        "actor_id": event.get("actor_id"),
        "authority_record_type": authority.get("type") if authority else None,
        "authority_record_id": authority.get("record_id") if authority else None,
        "authority_reference": authority,
        "event_summary": event.get("event_summary") or "",
        "reason_code": event.get("reason_code"),
        "reason_code_label": _label_key(event.get("reason_code")),
        "related_record_type": reference.get("type") if reference else None,
        "related_record_id": reference.get("record_id") if reference else None,
        "related_reference": reference,
        "created_at": event.get("created_at"),
    }


def list_system_observations_for_registry(filters=None, limit=100, scope=None):
    filters = filters or {}
    limit = max(1, min(int(limit or 100), READ_LIMIT))
    allowed_filters = {
        "observation_type",
        "condition_code",
        "current_state",
        "context_scope",
        "panel_key",
    }
    where = []
    params = []
    for key in sorted(set(filters) & allowed_filters):
        value = _scalar(filters.get(key), key)
        if value:
            where.append(f"{key} = ?")
            params.append(value)

    conn = get_connection()
    try:
        availability = _tables_available(conn)
        if not availability["available"]:
            return {
                "available": False,
                "missing": availability["missing"],
                "observations": [],
            }

        sql = "SELECT * FROM system_observations"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += """
            ORDER BY
                CASE
                    WHEN current_state IN ('acknowledged', 'under_review', 'deferred', 'routed') THEN 0
                    WHEN current_state IN ('closed_no_action', 'closed_resolved', 'superseded') THEN 1
                    ELSE 2
                END ASC,
                COALESCE(last_observed_at, created_at, '') DESC,
                observation_id DESC
            LIMIT ?
        """
        params.append(limit)
        rows = [_public_observation(row) for row in conn.execute(sql, params).fetchall()]
        visible = [row for row in rows if _observation_visible(row, scope)]
        return {
            "available": True,
            "missing": [],
            "observations": [_view_observation(row) for row in visible],
        }
    except Exception:
        return {
            "available": False,
            "missing": ["system_observations", "system_observation_events"],
            "observations": [],
        }
    finally:
        conn.close()


def get_system_observation_detail(observation_id, scope=None):
    try:
        observation_id = validate_public_observation_id(observation_id)
    except ValueError:
        return {"available": True, "status": "not_found", "observation": None, "events": []}

    conn = get_connection()
    try:
        availability = _tables_available(conn)
        if not availability["available"]:
            return {
                "available": False,
                "status": "unavailable",
                "missing": availability["missing"],
                "observation": None,
                "events": [],
            }

        observation = _public_observation(
            conn.execute(
                "SELECT * FROM system_observations WHERE observation_id = ?",
                (observation_id,),
            ).fetchone()
        )
        if not _observation_visible(observation, scope):
            return {"available": True, "status": "not_found", "observation": None, "events": []}

        event_rows = conn.execute(
            """
            SELECT *
            FROM system_observation_events
            WHERE observation_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (observation_id,),
        ).fetchall()
        events = [_view_event(_public_event(row)) for row in event_rows]

        prior = None
        if observation.get("prior_occurrence_id"):
            prior_row = _public_observation(
                conn.execute(
                    "SELECT * FROM system_observations WHERE observation_id = ?",
                    (observation.get("prior_occurrence_id"),),
                ).fetchone()
            )
            prior = _view_observation(prior_row) if _observation_visible(prior_row, scope) else None

        superseded_by = None
        if observation.get("superseded_by_observation_id"):
            superseded_row = _public_observation(
                conn.execute(
                    "SELECT * FROM system_observations WHERE observation_id = ?",
                    (observation.get("superseded_by_observation_id"),),
                ).fetchone()
            )
            superseded_by = (
                _view_observation(superseded_row)
                if _observation_visible(superseded_row, scope)
                else None
            )

        reopened = any(event.get("event_type") == "reopened" for event in events)
        return {
            "available": True,
            "status": "found",
            "observation": _view_observation(observation),
            "events": events,
            "prior_occurrence": prior,
            "superseded_by": superseded_by,
            "has_reopened_history": reopened,
        }
    except Exception:
        return {
            "available": False,
            "status": "unavailable",
            "missing": ["system_observations", "system_observation_events"],
            "observation": None,
            "events": [],
        }
    finally:
        conn.close()


__all__ = [
    "CONDITION_CODE_REGISTRY",
    "CONTEXT_SCOPES",
    "EVENT_TYPES",
    "LIFECYCLE_STATES",
    "OBSERVATION_TYPES",
    "OPEN_STATES",
    "PANEL_TYPE_MAP",
    "PERSISTENCE_TRIGGERS",
    "TRANSITIONS",
    "create_system_observation",
    "ensure_system_observation_tables",
    "find_open_duplicate",
    "get_system_observation_detail",
    "get_system_observation",
    "list_system_observation_events",
    "list_system_observations_for_registry",
    "list_system_observations",
    "system_observation_registry_available",
    "transition_system_observation",
    "validate_public_observation_id",
]
