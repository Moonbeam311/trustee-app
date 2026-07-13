import re

from database.db import get_connection


DESTINATION_LABELS = {
    "system_audit": "System Audit",
    "governance": "Governance",
    "compliance": "Compliance",
    "archive": "Archive",
    "people": "People",
    "matter": "Matter",
    "restricted_procedure_governance": "Restricted Procedure Governance",
}

DESTINATION_RECORD_TYPES = {
    "governance": {
        "Institutional Directive",
        "Institutional Policy",
    },
    "matter": {"Matter"},
}

DESTINATION_RECORD_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,119}$")
GOVERNANCE_ID_RE = re.compile(r"^(DIR|POL)-\d{4}-\d{4}$")
MATTER_ID_RE = re.compile(r"^MAT-[A-Za-z0-9][A-Za-z0-9_.:-]{0,115}$")
SUPPORTED_DESTINATIONS = {"governance", "matter"}
ACTIVE_GOVERNANCE_STATUSES = {"Draft", "Issued", "Active", "Completed"}
ACTIVE_MATTER_STATUSES = {"Open", "Active", "Review", "Intake"}


def _bounded(value, limit=200):
    text = str(value or "").strip()
    if "\x00" in text or "<" in text or ">" in text:
        return ""
    if len(text) > limit:
        text = text[:limit].rstrip()
    return text


def _failure(status, message):
    return {
        "ok": False,
        "status": status,
        "message": message,
    }


def _verified(
    *,
    destination_type,
    record_id,
    record_type,
    display_label,
    firm_id=None,
    institution_id=None,
    trust_id=None,
    matter_id=None,
    deployment_key=None,
    record_status=None,
    detail_url=None,
):
    return {
        "ok": True,
        "status": "verified",
        "destination_type": destination_type,
        "record_id": record_id,
        "record_type": record_type,
        "display_label": _bounded(display_label) or f"{record_type} {record_id}",
        "firm_id": firm_id,
        "institution_id": institution_id,
        "trust_id": trust_id,
        "matter_id": matter_id,
        "deployment_key": deployment_key,
        "record_status": _bounded(record_status, 80),
        "detail_url": detail_url,
    }


def _normalize_destination_key(destination_type):
    key = str(destination_type or "").strip().lower()
    if key not in DESTINATION_LABELS:
        return None
    return key


def _safe_record_id(record_id):
    value = _bounded(record_id, 120)
    if not value or not DESTINATION_RECORD_ID_RE.fullmatch(value):
        return None
    lowered = value.lower()
    blocked = ("://", "/", "\\", "?", "#", "--", ";", "'", '"')
    if any(marker in lowered for marker in blocked):
        return None
    return value


def _table_exists(conn, table_name):
    return bool(
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
    )


def _actor_can_access_firm(actor_context, firm_id):
    actor_context = actor_context or {}
    scope = actor_context.get("scope") or {}
    if scope.get("global"):
        return True
    scope_firm = scope.get("firm_id") or actor_context.get("firm_id")
    return bool(firm_id and scope_firm and firm_id == scope_firm)


def validate_destination_context(observation, destination, actor_context=None):
    if not observation or not destination:
        return _failure("context_mismatch", "Observation and destination context could not be compared.")

    observation_firm = observation.get("firm_id")
    destination_firm = destination.get("firm_id")
    if observation_firm and destination_firm and observation_firm != destination_firm:
        return _failure("cross_firm_destination", "Destination record is outside observation firm scope.")
    if destination_firm and not _actor_can_access_firm(actor_context, destination_firm):
        return _failure("destination_access_denied", "Destination record is outside operator scope.")

    scope = observation.get("context_scope")
    if scope == "platform_scoped":
        if destination.get("firm_id") or destination.get("institution_id") or destination.get("trust_id") or destination.get("matter_id"):
            return _failure("context_mismatch", "Platform-scoped observations cannot be narrowed to a firm-owned destination.")
    elif scope == "deployment_scoped":
        if destination.get("deployment_key") and observation.get("deployment_key") != destination.get("deployment_key"):
            return _failure("context_mismatch", "Destination deployment does not match observation deployment.")
        if destination.get("firm_id") or destination.get("matter_id") or destination.get("trust_id"):
            return _failure("context_mismatch", "Deployment-scoped observations cannot be narrowed to an arbitrary institutional record.")
    elif scope == "institution_scoped":
        if destination.get("institution_id") and observation.get("institution_id") != destination.get("institution_id"):
            return _failure("context_mismatch", "Destination institution does not match observation institution.")
    elif scope == "trust_scoped":
        if destination.get("trust_id") != observation.get("trust_id"):
            return _failure("context_mismatch", "Destination trust context does not match observation trust context.")
    elif scope == "matter_scoped":
        if destination.get("matter_id") != observation.get("matter_id"):
            return _failure("context_mismatch", "Destination matter context does not match observation matter context.")

    return {"ok": True, "status": "verified"}


def _governance_config_for_id(record_id):
    if record_id.startswith("DIR-"):
        return {
            "record_type_key": "directive",
            "record_type": "Institutional Directive",
            "table": "institutional_directives",
            "id_column": "directive_id",
            "type_column": "directive_type",
            "detail_prefix": "/governance/directives/",
        }
    if record_id.startswith("POL-"):
        return {
            "record_type_key": "policy",
            "record_type": "Institutional Policy",
            "table": "institutional_policies",
            "id_column": "policy_id",
            "type_column": "policy_area",
            "detail_prefix": "/governance/policies/",
        }
    return None


def verify_governance_destination(record_id, observation=None, actor_context=None, connection=None):
    record_id = _safe_record_id(record_id)
    if not record_id:
        return _failure("invalid_record_id", "Governance destination ID is not supported.")
    if record_id.startswith("GOV-"):
        return _failure("destination_unavailable", "Generic Governance IDs are not authoritative routable records.")
    if not GOVERNANCE_ID_RE.fullmatch(record_id):
        return _failure("record_type_mismatch", "Governance record type is not routable.")
    config = _governance_config_for_id(record_id)
    if not config:
        return _failure("record_type_mismatch", "Governance record type is not routable.")

    owns = connection is None
    conn = connection or get_connection()
    try:
        if not _table_exists(conn, config["table"]):
            return _failure("destination_unavailable", "Governance registry is unavailable.")
        row = conn.execute(
            f"SELECT * FROM {config['table']} WHERE {config['id_column']} = ? LIMIT 1",
            (record_id,),
        ).fetchone()
        if not row:
            return _failure("destination_not_found", "Governance record could not be verified.")
        record = dict(row)
        status = record.get("status") or "Draft"
        if status not in ACTIVE_GOVERNANCE_STATUSES:
            return _failure("destination_inactive", "Governance record is not active or eligible.")

        destination = _verified(
            destination_type="governance",
            record_id=record_id,
            record_type=config["record_type"],
            display_label=record.get("title") or record_id,
            firm_id=record.get("firm_id"),
            record_status=status,
            detail_url=f"{config['detail_prefix']}{record_id}",
        )
        context = validate_destination_context(observation, destination, actor_context)
        if not context.get("ok"):
            return context
        return destination
    except Exception:
        return _failure("unexpected_failure", "Governance destination could not be verified.")
    finally:
        if owns:
            conn.close()


def verify_matter_destination(record_id, observation=None, actor_context=None, connection=None):
    record_id = _safe_record_id(record_id)
    if not record_id or not MATTER_ID_RE.fullmatch(record_id):
        return _failure("invalid_record_id", "Matter destination ID is not supported.")

    owns = connection is None
    conn = connection or get_connection()
    try:
        if not _table_exists(conn, "matters"):
            return _failure("destination_unavailable", "Matter registry is unavailable.")
        row = conn.execute(
            "SELECT * FROM matters WHERE matter_id = ? LIMIT 1",
            (record_id,),
        ).fetchone()
        if not row:
            return _failure("destination_not_found", "Matter record could not be verified.")
        record = dict(row)
        status = record.get("status") or "Open"
        if status not in ACTIVE_MATTER_STATUSES:
            return _failure("destination_inactive", "Matter record is not active or eligible.")

        destination = _verified(
            destination_type="matter",
            record_id=record_id,
            record_type="Matter",
            display_label=record.get("title") or record_id,
            firm_id=record.get("firm_id"),
            matter_id=record_id,
            record_status=status,
            detail_url=f"/matters/{record_id}",
        )
        context = validate_destination_context(observation, destination, actor_context)
        if not context.get("ok"):
            return context
        return destination
    except Exception:
        return _failure("unexpected_failure", "Matter destination could not be verified.")
    finally:
        if owns:
            conn.close()


def verify_system_audit_destination(record_id, observation=None, actor_context=None, connection=None):
    return _failure(
        "destination_unavailable",
        "No authoritative routable System Audit destination registry is available.",
    )


def verify_compliance_destination(record_id, observation=None, actor_context=None, connection=None):
    return _failure(
        "destination_unavailable",
        "No authoritative routable Compliance destination registry is available.",
    )


def verify_archive_destination(record_id, observation=None, actor_context=None, connection=None):
    return _failure(
        "destination_unavailable",
        "No authoritative routable Archive destination registry is available.",
    )


def verify_people_destination(record_id, observation=None, actor_context=None, connection=None):
    return _failure(
        "destination_unavailable",
        "No authoritative routable People destination registry is available.",
    )


def verify_restricted_procedure_destination(record_id, observation=None, actor_context=None, connection=None):
    return _failure(
        "restricted_destination_unavailable",
        "No approved restricted-procedure authority destination is available.",
    )


DESTINATION_VERIFIERS = {
    "system_audit": verify_system_audit_destination,
    "governance": verify_governance_destination,
    "compliance": verify_compliance_destination,
    "archive": verify_archive_destination,
    "people": verify_people_destination,
    "matter": verify_matter_destination,
    "restricted_procedure_governance": verify_restricted_procedure_destination,
}


def verify_destination_record(destination_type, record_id, observation=None, actor_context=None, connection=None):
    key = _normalize_destination_key(destination_type)
    if not key:
        return _failure("invalid_destination_type", "Destination type is not supported.")
    verifier = DESTINATION_VERIFIERS.get(key)
    if not verifier:
        return _failure("invalid_destination_type", "Destination verifier is not configured.")
    return verifier(record_id, observation=observation, actor_context=actor_context, connection=connection)


def resolve_destination_reference(record_type, record_id, observation=None, actor_context=None, connection=None):
    label_to_key = {label.lower(): key for key, label in DESTINATION_LABELS.items()}
    record_type_key = str(record_type or "").strip().lower()
    record_type_to_key = {
        "institutional directive": "governance",
        "institutional policy": "governance",
        "matter": "matter",
    }
    key = label_to_key.get(record_type_key) or record_type_to_key.get(record_type_key)
    if not key:
        return {
            "type": _bounded(record_type, 80),
            "record_id": _bounded(record_id, 120),
            "status": "destination_unavailable",
            "display_label": _bounded(record_id, 120),
            "detail_url": None,
            "record_type": _bounded(record_type, 80),
        }
    result = verify_destination_record(
        key,
        record_id,
        observation=observation,
        actor_context=actor_context,
        connection=connection,
    )
    if result.get("ok"):
        return {
            "type": DESTINATION_LABELS[key],
            "record_id": result.get("record_id"),
            "status": result.get("status"),
            "display_label": result.get("display_label"),
            "detail_url": result.get("detail_url"),
            "record_type": result.get("record_type"),
            "record_status": result.get("record_status"),
            "caution": "Review the governed destination record for authoritative status and scope.",
        }
    return {
        "type": DESTINATION_LABELS.get(key, _bounded(record_type, 80)),
        "record_id": _bounded(record_id, 120),
        "status": result.get("status"),
        "display_label": _bounded(record_id, 120),
        "detail_url": None,
        "record_type": DESTINATION_LABELS.get(key, _bounded(record_type, 80)),
        "caution": result.get("message") or "Destination could not be verified for display.",
    }


def get_routable_destination_options(destination_keys):
    options = []
    for key in sorted(set(destination_keys or [])):
        if key in SUPPORTED_DESTINATIONS:
            options.append(
                {
                    "key": key,
                    "label": DESTINATION_LABELS[key],
                    "record_types": sorted(DESTINATION_RECORD_TYPES.get(key, set())),
                }
            )
    return options


def destination_registry_report():
    return {
        "system_audit": {
            "authoritative_registry": "None identified as routable",
            "verifier": "verify_system_audit_destination",
            "supported_record_types": [],
            "stable_public_id": None,
            "implementation_status": "bounded_unavailable",
        },
        "governance": {
            "authoritative_registry": "institutional_directives, institutional_policies",
            "verifier": "verify_governance_destination",
            "supported_record_types": sorted(DESTINATION_RECORD_TYPES["governance"]),
            "stable_public_id": "DIR-YYYY-NNNN, POL-YYYY-NNNN",
            "implementation_status": "verified_supported",
        },
        "compliance": {
            "authoritative_registry": "None identified as routable",
            "verifier": "verify_compliance_destination",
            "supported_record_types": [],
            "stable_public_id": None,
            "implementation_status": "bounded_unavailable",
        },
        "archive": {
            "authoritative_registry": "None identified as routable",
            "verifier": "verify_archive_destination",
            "supported_record_types": [],
            "stable_public_id": None,
            "implementation_status": "bounded_unavailable",
        },
        "people": {
            "authoritative_registry": "None identified as routable",
            "verifier": "verify_people_destination",
            "supported_record_types": [],
            "stable_public_id": None,
            "implementation_status": "bounded_unavailable",
        },
        "matter": {
            "authoritative_registry": "matters",
            "verifier": "verify_matter_destination",
            "supported_record_types": sorted(DESTINATION_RECORD_TYPES["matter"]),
            "stable_public_id": "MAT-*",
            "implementation_status": "verified_supported",
        },
        "restricted_procedure_governance": {
            "authoritative_registry": "None identified as approved restricted authority",
            "verifier": "verify_restricted_procedure_destination",
            "supported_record_types": [],
            "stable_public_id": None,
            "implementation_status": "bounded_unavailable",
        },
    }


__all__ = [
    "DESTINATION_LABELS",
    "DESTINATION_RECORD_TYPES",
    "DESTINATION_VERIFIERS",
    "SUPPORTED_DESTINATIONS",
    "destination_registry_report",
    "get_routable_destination_options",
    "resolve_destination_reference",
    "validate_destination_context",
    "verify_destination_record",
]
