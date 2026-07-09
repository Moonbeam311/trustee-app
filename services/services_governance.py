from datetime import datetime
from html import escape
from io import BytesIO
from uuid import uuid4

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from database.db import get_connection, get_current_firm_id


COMMON_GOVERNANCE_FIELDS = [
    "firm_id",
    "title",
    "status",
    "authority",
    "summary",
    "rationale",
    "version_label",
    "supersedes_id",
    "superseded_by_id",
    "created_by",
    "created_at",
    "updated_at",
    "effective_at",
    "retired_at",
]

GOVERNANCE_LIFECYCLE_STATES = [
    "Draft",
    "Issued",
    "Active",
    "Completed",
    "Superseded",
    "Retired",
]

GOVERNANCE_LIFECYCLE_TRANSITIONS = {
    "Draft": ["Issued", "Retired"],
    "Issued": ["Active", "Superseded", "Retired"],
    "Active": ["Completed", "Superseded", "Retired"],
    "Completed": ["Superseded", "Retired"],
    "Superseded": ["Retired"],
    "Retired": [],
}

GOVERNANCE_RELATIONSHIP_TYPES = [
    "authorizes",
    "implements",
    "supersedes",
    "depends_on",
    "governs",
    "references",
]

GOVERNANCE_RELATIONSHIP_TARGET_TYPES = [
    "Directive",
    "Policy",
    "Decision",
    "Resolution",
    "Memorandum",
    "Opinion",
    "Precedent",
    "Matter",
    "Trust",
    "Certificate",
    "Execution Session",
    "Continuity Asset",
    "Genealogy Record",
    "Document",
]

GOVERNANCE_DIRECTIVE_SOURCE_TYPES = [
    "Matter",
    "Trust",
    "Certificate",
    "Document",
    "Upload",
    "Execution Session",
    "External Reference",
]

GOVERNANCE_POLICY_SOURCE_TYPES = GOVERNANCE_DIRECTIVE_SOURCE_TYPES

GOVERNANCE_OBJECTS = {
    "directive": {
        "table": "institutional_directives",
        "id_column": "directive_id",
        "prefix": "DIR",
        "text_column": "instruction",
        "record_label": "Directive",
        "type_column": "directive_type",
        "actor_column": "issued_by",
        "actor_label": "Issued By",
    },
    "decision": {
        "table": "institutional_decisions",
        "id_column": "decision_id",
        "prefix": "DEC",
        "text_column": "decision_text",
        "record_label": "Decision",
        "type_column": "decision_type",
        "actor_column": "decided_by",
        "actor_label": "Decided By",
    },
    "policy": {
        "table": "institutional_policies",
        "id_column": "policy_id",
        "prefix": "POL",
        "text_column": "policy_text",
        "record_label": "Policy",
        "type_column": "policy_area",
        "actor_column": "approved_by",
        "actor_label": "Approved By",
    },
    "resolution": {
        "table": "institutional_resolutions",
        "id_column": "resolution_id",
        "prefix": "RES",
        "text_column": "resolution_text",
        "record_label": "Resolution",
        "type_column": None,
        "actor_column": "resolved_by",
        "actor_label": "Resolved By",
    },
    "memorandum": {
        "table": "institutional_memoranda",
        "id_column": "memorandum_id",
        "prefix": "MEM",
        "text_column": "memorandum_text",
        "record_label": "Memorandum",
        "type_column": None,
        "actor_column": "authored_by",
        "actor_label": "Authored By",
    },
    "opinion": {
        "table": "institutional_opinions",
        "id_column": "opinion_id",
        "prefix": "OPN",
        "text_column": "opinion_text",
        "record_label": "Opinion",
        "type_column": "opinion_type",
        "actor_column": "authored_by",
        "actor_label": "Authored By",
    },
    "precedent": {
        "table": "institutional_precedents",
        "id_column": "precedent_id",
        "prefix": "PRE",
        "text_column": "precedent_text",
        "record_label": "Precedent",
        "type_column": "precedent_type",
        "actor_column": "source_object_type",
        "actor_label": "Source Object",
    },
}


def _now():
    return datetime.utcnow().isoformat(timespec="seconds")


def _public_id(prefix):
    return f"{prefix}-{uuid4().hex[:10].upper()}"


def _normalize_status(status):
    cleaned = (status or "Draft").strip()
    if cleaned not in GOVERNANCE_LIFECYCLE_STATES:
        return "Draft"
    return cleaned


def _normalize_relationship_type(relationship_type):
    cleaned = (relationship_type or "").strip()
    if cleaned not in GOVERNANCE_RELATIONSHIP_TYPES:
        return ""
    return cleaned


def _normalize_directive_source_type(source_type):
    cleaned = (source_type or "").strip()
    if not cleaned:
        return ""
    if cleaned not in GOVERNANCE_DIRECTIVE_SOURCE_TYPES:
        return ""
    return cleaned


def _normalize_policy_source_type(source_type):
    cleaned = (source_type or "").strip()
    if not cleaned:
        return ""
    if cleaned not in GOVERNANCE_POLICY_SOURCE_TYPES:
        return ""
    return cleaned


def _truthy(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "required"}


def _pdf_text(value):
    return escape(str(value if value not in (None, "") else "-"))


def _next_governance_number(conn, prefix, firm_id):
    year = datetime.utcnow().year
    cur = conn.cursor()
    row = cur.execute(
        """
        SELECT last_number
        FROM governance_number_sequences
        WHERE firm_id = ?
          AND prefix = ?
          AND sequence_year = ?
        """,
        (firm_id, prefix, year),
    ).fetchone()

    if row:
        next_number = int(row["last_number"]) + 1
        cur.execute(
            """
            UPDATE governance_number_sequences
            SET last_number = ?,
                updated_at = ?
            WHERE firm_id = ?
              AND prefix = ?
              AND sequence_year = ?
            """,
            (next_number, _now(), firm_id, prefix, year),
        )
    else:
        next_number = 1
        cur.execute(
            """
            INSERT INTO governance_number_sequences (
                firm_id,
                prefix,
                sequence_year,
                last_number,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (firm_id, prefix, year, next_number, _now(), _now()),
        )

    return f"{prefix}-{year}-{next_number:04d}"


def get_governance_config(record_type):
    return GOVERNANCE_OBJECTS.get(record_type)


def get_governance_record_types():
    return [
        {"key": key, **config}
        for key, config in GOVERNANCE_OBJECTS.items()
    ]


def get_governance_relationship_types():
    return GOVERNANCE_RELATIONSHIP_TYPES


def get_governance_relationship_target_types():
    return GOVERNANCE_RELATIONSHIP_TARGET_TYPES


def get_governance_directive_source_types():
    return GOVERNANCE_DIRECTIVE_SOURCE_TYPES


def get_governance_policy_source_types():
    return GOVERNANCE_POLICY_SOURCE_TYPES


def allowed_governance_transitions(status):
    return GOVERNANCE_LIFECYCLE_TRANSITIONS.get(status or "Draft", [])


def build_governance_metadata(record_type, record):
    config = get_governance_config(record_type)
    if not config or not record:
        return {}

    type_column = config.get("type_column")
    actor_column = config.get("actor_column")
    return {
        "record_type": record_type,
        "record_label": config["record_label"],
        "record_id": record.get(config["id_column"]),
        "record_number": record.get(config["id_column"]),
        "prefix": config["prefix"],
        "title": record.get("title"),
        "status": record.get("status") or "Draft",
        "allowed_transitions": allowed_governance_transitions(record.get("status")),
        "authority": record.get("authority"),
        "issuing_authority": record.get("issuing_authority"),
        "authority_basis": record.get("authority_basis"),
        "approval_required": _truthy(record.get("approval_required")),
        "approved_by": record.get("approved_by"),
        "approved_at": record.get("approved_at"),
        "approval_status": (
            "Approved"
            if record.get("approved_at")
            else "Approval Required"
            if _truthy(record.get("approval_required"))
            else "Not Required"
        ),
        "source_type": record.get("source_type"),
        "source_id": record.get("source_id"),
        "source_label": record.get("source_label"),
        "source_notes": record.get("source_notes"),
        "has_source": bool(
            record.get("source_type")
            or record.get("source_id")
            or record.get("source_label")
            or record.get("source_notes")
        ),
        "summary": record.get("summary"),
        "rationale": record.get("rationale"),
        "version_label": record.get("version_label"),
        "type_label": type_column.replace("_", " ").title() if type_column else "Type",
        "type_value": record.get(type_column) if type_column else "",
        "actor_label": config.get("actor_label") or "Actor",
        "actor_value": record.get(actor_column) if actor_column else "",
        "created_by": record.get("created_by"),
        "created_at": record.get("created_at"),
        "updated_at": record.get("updated_at"),
        "effective_at": record.get("effective_at"),
        "retired_at": record.get("retired_at"),
        "supersedes_id": record.get("supersedes_id"),
        "superseded_by_id": record.get("superseded_by_id"),
    }


def ensure_governance_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS governance_number_sequences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firm_id TEXT DEFAULT 'FIRM-001',
            prefix TEXT NOT NULL,
            sequence_year INTEGER NOT NULL,
            last_number INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(firm_id, prefix, sequence_year)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS institutional_directives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            directive_id TEXT UNIQUE NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            directive_code TEXT,
            title TEXT NOT NULL,
            directive_type TEXT DEFAULT 'Governance Directive',
            status TEXT DEFAULT 'Draft',
            authority TEXT,
            issuing_authority TEXT,
            authority_basis TEXT,
            approval_required INTEGER DEFAULT 0,
            approved_by TEXT,
            approved_at TEXT,
            source_type TEXT,
            source_id TEXT,
            source_label TEXT,
            source_notes TEXT,
            issued_by TEXT,
            issued_at TEXT,
            effective_at TEXT,
            retired_at TEXT,
            summary TEXT,
            instruction TEXT,
            rationale TEXT,
            scope TEXT,
            milestone_plan TEXT,
            completion_record TEXT,
            version_label TEXT DEFAULT 'v1',
            supersedes_id TEXT,
            superseded_by_id TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    directive_columns = {
        row["name"]
        for row in cur.execute("PRAGMA table_info(institutional_directives)").fetchall()
    }
    directive_column_specs = {
        "issuing_authority": "TEXT",
        "authority_basis": "TEXT",
        "approval_required": "INTEGER DEFAULT 0",
        "approved_by": "TEXT",
        "approved_at": "TEXT",
        "source_type": "TEXT",
        "source_id": "TEXT",
        "source_label": "TEXT",
        "source_notes": "TEXT",
    }
    for column_name, column_spec in directive_column_specs.items():
        if column_name not in directive_columns:
            cur.execute(
                f"ALTER TABLE institutional_directives ADD COLUMN {column_name} {column_spec}"
            )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS institutional_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_id TEXT UNIQUE NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            title TEXT NOT NULL,
            decision_type TEXT DEFAULT 'Governance Decision',
            status TEXT DEFAULT 'Draft',
            authority TEXT,
            decided_by TEXT,
            decided_at TEXT,
            effective_at TEXT,
            retired_at TEXT,
            summary TEXT,
            decision_text TEXT,
            rationale TEXT,
            approval_history TEXT,
            version_label TEXT DEFAULT 'v1',
            supersedes_id TEXT,
            superseded_by_id TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS institutional_policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_id TEXT UNIQUE NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            title TEXT NOT NULL,
            policy_area TEXT,
            status TEXT DEFAULT 'Draft',
            authority TEXT,
            issuing_authority TEXT,
            authority_basis TEXT,
            approval_required INTEGER DEFAULT 0,
            approved_by TEXT,
            approved_at TEXT,
            effective_at TEXT,
            retired_at TEXT,
            source_type TEXT,
            source_id TEXT,
            source_label TEXT,
            source_notes TEXT,
            summary TEXT,
            policy_text TEXT,
            rationale TEXT,
            version_label TEXT DEFAULT 'v1',
            supersedes_id TEXT,
            superseded_by_id TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    policy_columns = {
        row["name"]
        for row in cur.execute("PRAGMA table_info(institutional_policies)").fetchall()
    }
    policy_column_specs = {
        "issuing_authority": "TEXT",
        "authority_basis": "TEXT",
        "approval_required": "INTEGER DEFAULT 0",
        "source_type": "TEXT",
        "source_id": "TEXT",
        "source_label": "TEXT",
        "source_notes": "TEXT",
    }
    for column_name, column_spec in policy_column_specs.items():
        if column_name not in policy_columns:
            cur.execute(
                f"ALTER TABLE institutional_policies ADD COLUMN {column_name} {column_spec}"
            )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS institutional_resolutions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resolution_id TEXT UNIQUE NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            title TEXT NOT NULL,
            status TEXT DEFAULT 'Draft',
            authority TEXT,
            resolved_by TEXT,
            resolved_at TEXT,
            effective_at TEXT,
            retired_at TEXT,
            summary TEXT,
            resolution_text TEXT,
            recitals TEXT,
            approval_history TEXT,
            version_label TEXT DEFAULT 'v1',
            supersedes_id TEXT,
            superseded_by_id TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS institutional_memoranda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memorandum_id TEXT UNIQUE NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            title TEXT NOT NULL,
            status TEXT DEFAULT 'Draft',
            authority TEXT,
            authored_by TEXT,
            issued_at TEXT,
            effective_at TEXT,
            retired_at TEXT,
            summary TEXT,
            memorandum_text TEXT,
            rationale TEXT,
            version_label TEXT DEFAULT 'v1',
            supersedes_id TEXT,
            superseded_by_id TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS institutional_opinions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opinion_id TEXT UNIQUE NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            title TEXT NOT NULL,
            opinion_type TEXT DEFAULT 'Governance Opinion',
            status TEXT DEFAULT 'Draft',
            authority TEXT,
            authored_by TEXT,
            issued_at TEXT,
            effective_at TEXT,
            retired_at TEXT,
            summary TEXT,
            opinion_text TEXT,
            findings TEXT,
            rationale TEXT,
            version_label TEXT DEFAULT 'v1',
            supersedes_id TEXT,
            superseded_by_id TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS institutional_precedents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            precedent_id TEXT UNIQUE NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            title TEXT NOT NULL,
            precedent_type TEXT DEFAULT 'Governance Precedent',
            status TEXT DEFAULT 'Active',
            authority TEXT,
            source_object_type TEXT,
            source_object_id TEXT,
            established_at TEXT,
            effective_at TEXT,
            retired_at TEXT,
            summary TEXT,
            precedent_text TEXT,
            rationale TEXT,
            version_label TEXT DEFAULT 'v1',
            supersedes_id TEXT,
            superseded_by_id TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS governance_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            relationship_id TEXT UNIQUE NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            source_object_type TEXT NOT NULL,
            source_object_id TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            target_object_type TEXT NOT NULL,
            target_object_id TEXT NOT NULL,
            authority TEXT,
            reason TEXT,
            status TEXT DEFAULT 'Active',
            effective_at TEXT,
            retired_at TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS directive_implementation_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id TEXT UNIQUE NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            directive_id TEXT NOT NULL,
            action_type TEXT,
            action_summary TEXT NOT NULL,
            performed_by TEXT,
            performed_at TEXT,
            result_status TEXT DEFAULT 'Recorded',
            evidence_reference TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS policy_activity_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id TEXT UNIQUE NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            policy_id TEXT NOT NULL,
            action_type TEXT,
            action_summary TEXT NOT NULL,
            performed_by TEXT,
            performed_at TEXT,
            result_status TEXT DEFAULT 'Recorded',
            evidence_reference TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    index_specs = [
        ("idx_governance_number_sequences_scope", "governance_number_sequences", "firm_id, prefix, sequence_year"),
        ("idx_institutional_directives_firm_status", "institutional_directives", "firm_id, status"),
        ("idx_institutional_decisions_firm_status", "institutional_decisions", "firm_id, status"),
        ("idx_institutional_policies_firm_status", "institutional_policies", "firm_id, status"),
        ("idx_institutional_resolutions_firm_status", "institutional_resolutions", "firm_id, status"),
        ("idx_institutional_memoranda_firm_status", "institutional_memoranda", "firm_id, status"),
        ("idx_institutional_opinions_firm_status", "institutional_opinions", "firm_id, status"),
        ("idx_institutional_precedents_firm_status", "institutional_precedents", "firm_id, status"),
        ("idx_governance_relationships_source", "governance_relationships", "firm_id, source_object_type, source_object_id"),
        ("idx_governance_relationships_target", "governance_relationships", "firm_id, target_object_type, target_object_id"),
        ("idx_governance_relationships_type", "governance_relationships", "firm_id, relationship_type, status"),
        ("idx_directive_implementation_entries_directive", "directive_implementation_entries", "firm_id, directive_id, performed_at"),
        ("idx_policy_activity_entries_policy", "policy_activity_entries", "firm_id, policy_id, performed_at"),
    ]

    for index_name, table_name, columns in index_specs:
        cur.execute(
            f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns})"
        )

    conn.commit()
    conn.close()


def create_governance_record(record_type, data):
    ensure_governance_tables()

    config = get_governance_config(record_type)
    if not config:
        return False, "Unsupported governance record type."

    title = (data.get("title") or "").strip()
    if not title:
        return False, "Title is required."

    if record_type == "directive":
        source_type = _normalize_directive_source_type(data.get("source_type"))
        has_source_data = any(
            (data.get(key) or "").strip()
            for key in ["source_type", "source_id", "source_label", "source_notes"]
        )
        if has_source_data and not source_type:
            return False, "Unsupported Directive source type."
        if source_type and not (data.get("source_id") or "").strip():
            return False, "Source ID is required when a source type is selected."
        data = {**data, "source_type": source_type}
    elif record_type == "policy":
        source_type = _normalize_policy_source_type(data.get("source_type"))
        has_source_data = any(
            (data.get(key) or "").strip()
            for key in ["source_type", "source_id", "source_label", "source_notes"]
        )
        if has_source_data and not source_type:
            return False, "Unsupported Policy source type."
        if source_type and not (data.get("source_id") or "").strip():
            return False, "Source ID is required when a source type is selected."
        data = {**data, "source_type": source_type}

    now = _now()
    firm_id = data.get("firm_id") or get_current_firm_id()
    text_column = config["text_column"]
    status = _normalize_status(data.get("status"))

    conn = get_connection()
    cur = conn.cursor()
    record_id = data.get(config["id_column"]) or _next_governance_number(
        conn,
        config["prefix"],
        firm_id,
    )

    base_columns = [
        config["id_column"],
        "firm_id",
        "title",
        "status",
        "authority",
        "summary",
        text_column,
        "rationale",
        "version_label",
        "supersedes_id",
        "superseded_by_id",
        "created_by",
        "created_at",
        "updated_at",
    ]

    values = [
        record_id,
        firm_id,
        title,
        status,
        data.get("authority") or "",
        data.get("summary") or "",
        data.get("body") or data.get(text_column) or "",
        data.get("rationale") or "",
        data.get("version_label") or "v1",
        data.get("supersedes_id") or "",
        data.get("superseded_by_id") or "",
        data.get("created_by") or "System",
        now,
        now,
    ]

    extra_map = {
        "directive": ["directive_code", "directive_type", "issuing_authority", "authority_basis", "approval_required", "approved_by", "approved_at", "source_type", "source_id", "source_label", "source_notes", "issued_by", "issued_at", "effective_at", "retired_at", "scope", "milestone_plan", "completion_record"],
        "decision": ["decision_type", "decided_by", "decided_at", "effective_at", "retired_at", "approval_history"],
        "policy": ["policy_area", "issuing_authority", "authority_basis", "approval_required", "approved_by", "approved_at", "source_type", "source_id", "source_label", "source_notes", "effective_at", "retired_at"],
        "resolution": ["resolved_by", "resolved_at", "effective_at", "retired_at", "recitals", "approval_history"],
        "memorandum": ["authored_by", "issued_at", "effective_at", "retired_at"],
        "opinion": ["opinion_type", "authored_by", "issued_at", "effective_at", "retired_at", "findings"],
        "precedent": ["precedent_type", "source_object_type", "source_object_id", "established_at", "effective_at", "retired_at"],
    }

    for column in extra_map.get(record_type, []):
        base_columns.append(column)
        if column == "approval_required":
            values.append(1 if _truthy(data.get(column)) else 0)
        else:
            values.append(data.get(column) or "")

    placeholders = ", ".join("?" for _ in base_columns)
    column_sql = ", ".join(base_columns)

    cur.execute(
        f"INSERT INTO {config['table']} ({column_sql}) VALUES ({placeholders})",
        values,
    )
    conn.commit()
    conn.close()

    return True, record_id


def approve_governance_directive(directive_id, approved_by, authority_basis=""):
    ensure_governance_tables()

    record = get_governance_record("directive", directive_id)
    if not record:
        return False, "Directive not found."

    basis = (authority_basis or record.get("authority_basis") or "").strip()
    if not basis:
        return False, "Authority basis is required before approval."

    approver = (approved_by or "").strip() or "System"
    now = _now()
    conn = get_connection()
    conn.execute(
        """
        UPDATE institutional_directives
        SET authority_basis = ?,
            approval_required = 1,
            approved_by = ?,
            approved_at = ?,
            updated_at = ?
        WHERE directive_id = ?
          AND firm_id = ?
        """,
        (
            basis,
            approver,
            now,
            now,
            directive_id,
            get_current_firm_id(),
        ),
    )
    conn.commit()
    conn.close()
    return True, directive_id


def approve_governance_policy(policy_id, approved_by, authority_basis=""):
    ensure_governance_tables()

    record = get_governance_record("policy", policy_id)
    if not record:
        return False, "Policy not found."

    basis = (authority_basis or record.get("authority_basis") or "").strip()
    if not basis:
        return False, "Authority basis is required before approval."

    approver = (approved_by or "").strip() or "System"
    now = _now()
    conn = get_connection()
    conn.execute(
        """
        UPDATE institutional_policies
        SET authority_basis = ?,
            approval_required = 1,
            approved_by = ?,
            approved_at = ?,
            updated_at = ?
        WHERE policy_id = ?
          AND firm_id = ?
        """,
        (
            basis,
            approver,
            now,
            now,
            policy_id,
            get_current_firm_id(),
        ),
    )
    conn.commit()
    conn.close()
    return True, policy_id


def create_directive_implementation_entry(directive_id, data):
    ensure_governance_tables()

    directive = get_governance_record("directive", directive_id)
    if not directive:
        return False, "Directive not found."

    action_summary = (data.get("action_summary") or "").strip()
    if not action_summary:
        return False, "Action summary is required."

    now = _now()
    entry_id = data.get("entry_id") or _public_id("DIL")
    performed_at = (data.get("performed_at") or "").strip() or now

    conn = get_connection()
    conn.execute(
        """
        INSERT INTO directive_implementation_entries (
            entry_id,
            firm_id,
            directive_id,
            action_type,
            action_summary,
            performed_by,
            performed_at,
            result_status,
            evidence_reference,
            notes,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entry_id,
            get_current_firm_id(),
            directive_id,
            data.get("action_type") or "",
            action_summary,
            data.get("performed_by") or "System",
            performed_at,
            data.get("result_status") or "Recorded",
            data.get("evidence_reference") or "",
            data.get("notes") or "",
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()
    return True, entry_id


def list_directive_implementation_entries(directive_id):
    ensure_governance_tables()

    conn = get_connection()
    rows = conn.execute(
        """
        SELECT *
        FROM directive_implementation_entries
        WHERE firm_id = ?
          AND directive_id = ?
        ORDER BY performed_at DESC, id DESC
        """,
        (get_current_firm_id(), directive_id),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_policy_activity_entry(policy_id, data):
    ensure_governance_tables()

    policy = get_governance_record("policy", policy_id)
    if not policy:
        return False, "Policy not found."

    action_summary = (data.get("action_summary") or "").strip()
    if not action_summary:
        return False, "Action summary is required."

    now = _now()
    entry_id = data.get("entry_id") or _public_id("PAL")
    performed_at = (data.get("performed_at") or "").strip() or now

    conn = get_connection()
    conn.execute(
        """
        INSERT INTO policy_activity_entries (
            entry_id,
            firm_id,
            policy_id,
            action_type,
            action_summary,
            performed_by,
            performed_at,
            result_status,
            evidence_reference,
            notes,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entry_id,
            get_current_firm_id(),
            policy_id,
            data.get("action_type") or "",
            action_summary,
            data.get("performed_by") or "System",
            performed_at,
            data.get("result_status") or "Recorded",
            data.get("evidence_reference") or "",
            data.get("notes") or "",
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()
    return True, entry_id


def list_policy_activity_entries(policy_id):
    ensure_governance_tables()

    conn = get_connection()
    rows = conn.execute(
        """
        SELECT *
        FROM policy_activity_entries
        WHERE firm_id = ?
          AND policy_id = ?
        ORDER BY performed_at DESC, id DESC
        """,
        (get_current_firm_id(), policy_id),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def build_governance_dashboard_summary():
    ensure_governance_tables()

    firm_id = get_current_firm_id()
    conn = get_connection()

    record_type_counts = []
    lifecycle_counts = {state: 0 for state in GOVERNANCE_LIFECYCLE_STATES}
    for record_type, config in GOVERNANCE_OBJECTS.items():
        count_row = conn.execute(
            f"SELECT COUNT(*) AS count FROM {config['table']} WHERE firm_id = ?",
            (firm_id,),
        ).fetchone()
        record_type_counts.append(
            {
                "record_type": record_type,
                "record_label": config["record_label"],
                "prefix": config["prefix"],
                "count": count_row["count"] if count_row else 0,
            }
        )

        state_rows = conn.execute(
            f"""
            SELECT status, COUNT(*) AS count
            FROM {config['table']}
            WHERE firm_id = ?
            GROUP BY status
            """,
            (firm_id,),
        ).fetchall()
        for row in state_rows:
            status = row["status"] or "Draft"
            lifecycle_counts[status] = lifecycle_counts.get(status, 0) + row["count"]

    recent_directives = conn.execute(
        """
        SELECT directive_id, directive_code, title, status, approved_by, approved_at, updated_at
        FROM institutional_directives
        WHERE firm_id = ?
        ORDER BY updated_at DESC, id DESC
        LIMIT 10
        """,
        (firm_id,),
    ).fetchall()

    recent_policies = conn.execute(
        """
        SELECT policy_id, policy_area, title, status, approved_by, approved_at, updated_at
        FROM institutional_policies
        WHERE firm_id = ?
        ORDER BY updated_at DESC, id DESC
        LIMIT 10
        """,
        (firm_id,),
    ).fetchall()

    pending_approvals = conn.execute(
        """
        SELECT directive_id, directive_code, title, status, authority_basis, updated_at
        FROM institutional_directives
        WHERE firm_id = ?
          AND COALESCE(approval_required, 0) = 1
          AND COALESCE(approved_at, '') = ''
        ORDER BY updated_at DESC, id DESC
        LIMIT 10
        """,
        (firm_id,),
    ).fetchall()

    pending_policy_approvals = conn.execute(
        """
        SELECT policy_id, policy_area, title, status, authority_basis, updated_at
        FROM institutional_policies
        WHERE firm_id = ?
          AND COALESCE(approval_required, 0) = 1
          AND COALESCE(approved_at, '') = ''
        ORDER BY updated_at DESC, id DESC
        LIMIT 10
        """,
        (firm_id,),
    ).fetchall()

    implementation_activity = conn.execute(
        """
        SELECT
            d.directive_id,
            d.directive_code,
            d.title,
            d.status,
            COUNT(e.id) AS entry_count,
            MAX(e.performed_at) AS latest_activity
        FROM institutional_directives d
        INNER JOIN directive_implementation_entries e
            ON e.directive_id = d.directive_id
           AND e.firm_id = d.firm_id
        WHERE d.firm_id = ?
        GROUP BY d.directive_id, d.directive_code, d.title, d.status
        ORDER BY latest_activity DESC, entry_count DESC
        LIMIT 10
        """,
        (firm_id,),
    ).fetchall()

    policy_activity = conn.execute(
        """
        SELECT
            p.policy_id,
            p.policy_area,
            p.title,
            p.status,
            COUNT(e.id) AS entry_count,
            MAX(e.performed_at) AS latest_activity
        FROM institutional_policies p
        INNER JOIN policy_activity_entries e
            ON e.policy_id = p.policy_id
           AND e.firm_id = p.firm_id
        WHERE p.firm_id = ?
        GROUP BY p.policy_id, p.policy_area, p.title, p.status
        ORDER BY latest_activity DESC, entry_count DESC
        LIMIT 10
        """,
        (firm_id,),
    ).fetchall()

    conn.close()
    return {
        "record_type_counts": record_type_counts,
        "lifecycle_counts": [
            {"status": status, "count": count}
            for status, count in lifecycle_counts.items()
        ],
        "recent_directives": [dict(row) for row in recent_directives],
        "recent_policies": [dict(row) for row in recent_policies],
        "pending_approvals": [dict(row) for row in pending_approvals],
        "pending_policy_approvals": [dict(row) for row in pending_policy_approvals],
        "implementation_activity": [dict(row) for row in implementation_activity],
        "policy_activity": [dict(row) for row in policy_activity],
    }


def create_governance_relationship(data):
    ensure_governance_tables()

    required = [
        "source_object_type",
        "source_object_id",
        "relationship_type",
        "target_object_type",
        "target_object_id",
    ]

    cleaned = {key: (data.get(key) or "").strip() for key in required}
    cleaned["relationship_type"] = _normalize_relationship_type(
        cleaned["relationship_type"]
    )
    missing = [key for key, value in cleaned.items() if not value]
    if missing:
        return False, f"Missing required relationship fields: {', '.join(missing)}."

    now = _now()
    relationship_id = data.get("relationship_id") or _public_id("GR")
    firm_id = data.get("firm_id") or get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    existing = cur.execute(
        """
        SELECT relationship_id
        FROM governance_relationships
        WHERE firm_id = ?
          AND source_object_type = ?
          AND source_object_id = ?
          AND relationship_type = ?
          AND target_object_type = ?
          AND target_object_id = ?
          AND status = 'Active'
        LIMIT 1
        """,
        (
            firm_id,
            cleaned["source_object_type"],
            cleaned["source_object_id"],
            cleaned["relationship_type"],
            cleaned["target_object_type"],
            cleaned["target_object_id"],
        ),
    ).fetchone()

    if existing:
        conn.close()
        return False, (
            "Duplicate active governance relationship blocked: "
            f"{existing['relationship_id']}"
        )

    cur.execute(
        """
        INSERT INTO governance_relationships (
            relationship_id,
            firm_id,
            source_object_type,
            source_object_id,
            relationship_type,
            target_object_type,
            target_object_id,
            authority,
            reason,
            status,
            effective_at,
            retired_at,
            created_by,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            relationship_id,
            firm_id,
            cleaned["source_object_type"],
            cleaned["source_object_id"],
            cleaned["relationship_type"],
            cleaned["target_object_type"],
            cleaned["target_object_id"],
            data.get("authority") or "",
            data.get("reason") or "",
            data.get("status") or "Active",
            data.get("effective_at") or "",
            data.get("retired_at") or "",
            data.get("created_by") or "System",
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()

    return True, relationship_id


def list_governance_records(record_type, status=None):
    ensure_governance_tables()

    config = get_governance_config(record_type)
    if not config:
        return []

    firm_id = get_current_firm_id()
    params = [firm_id]
    sql = (
        f"SELECT * FROM {config['table']} "
        "WHERE firm_id = ?"
    )

    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY updated_at DESC, id DESC"

    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_governance_record(record_type, record_id):
    ensure_governance_tables()

    config = get_governance_config(record_type)
    if not config:
        return None

    firm_id = get_current_firm_id()
    conn = get_connection()
    row = conn.execute(
        f"""
        SELECT *
        FROM {config['table']}
        WHERE {config['id_column']} = ?
          AND firm_id = ?
        """,
        (record_id, firm_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def transition_governance_record(record_type, record_id, new_status, actor="System"):
    ensure_governance_tables()

    config = get_governance_config(record_type)
    if not config:
        return False, "Unsupported governance record type."

    record = get_governance_record(record_type, record_id)
    if not record:
        return False, "Governance record not found."

    current_status = record.get("status") or "Draft"
    target_status = _normalize_status(new_status)
    if target_status not in allowed_governance_transitions(current_status):
        return False, f"{current_status} records cannot move to {target_status}."

    now = _now()
    retired_at = now if target_status == "Retired" else record.get("retired_at") or ""
    conn = get_connection()
    conn.execute(
        f"""
        UPDATE {config['table']}
        SET status = ?,
            retired_at = ?,
            updated_at = ?,
            created_by = COALESCE(NULLIF(created_by, ''), ?)
        WHERE {config['id_column']} = ?
          AND firm_id = ?
        """,
        (
            target_status,
            retired_at,
            now,
            actor or "System",
            record_id,
            get_current_firm_id(),
        ),
    )
    conn.commit()
    conn.close()
    return True, target_status


def list_governance_relationships(object_type=None, object_id=None):
    ensure_governance_tables()

    firm_id = get_current_firm_id()
    params = [firm_id]
    sql = "SELECT * FROM governance_relationships WHERE firm_id = ?"

    if object_type and object_id:
        sql += (
            " AND ("
            "(source_object_type = ? AND source_object_id = ?) OR "
            "(target_object_type = ? AND target_object_id = ?)"
            ")"
        )
        params.extend([object_type, object_id, object_type, object_id])

    sql += " ORDER BY updated_at DESC, id DESC"

    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_outgoing_governance_relationships(object_type, object_id):
    ensure_governance_tables()

    firm_id = get_current_firm_id()
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT *
        FROM governance_relationships
        WHERE firm_id = ?
          AND source_object_type = ?
          AND source_object_id = ?
        ORDER BY updated_at DESC, id DESC
        """,
        (firm_id, object_type, object_id),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_incoming_governance_relationships(object_type, object_id):
    ensure_governance_tables()

    firm_id = get_current_firm_id()
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT *
        FROM governance_relationships
        WHERE firm_id = ?
          AND target_object_type = ?
          AND target_object_id = ?
        ORDER BY updated_at DESC, id DESC
        """,
        (firm_id, object_type, object_id),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def build_governance_links_for_object(object_type, object_id):
    ensure_governance_tables()

    relationships = list_governance_relationships(object_type, object_id)
    links = []

    type_map = {
        "Directive": "directive",
        "Policy": "policy",
    }

    for relationship in relationships:
        source_type = relationship.get("source_object_type")
        source_id = relationship.get("source_object_id")
        target_type = relationship.get("target_object_type")
        target_id = relationship.get("target_object_id")

        if source_type == object_type and source_id == object_id:
            governance_type = target_type
            governance_id = target_id
            direction = f"{object_type} to Governance"
        elif target_type == object_type and target_id == object_id:
            governance_type = source_type
            governance_id = source_id
            direction = f"Governance to {object_type}"
        else:
            continue

        record_type = type_map.get(governance_type)
        if not record_type:
            continue

        record = get_governance_record(record_type, governance_id)
        if not record:
            continue

        links.append(
            {
                "relationship": relationship,
                "direction": direction,
                "record_type": record_type,
                "governance_type": governance_type,
                "governance_id": governance_id,
                "record": record,
            }
        )

    return links


def build_trust_governance_links(trust_id):
    return build_governance_links_for_object("Trust", trust_id)


def build_matter_governance_links(matter_id):
    return build_governance_links_for_object("Matter", matter_id)


def _governance_display_date(record, relationship):
    for key in ("approved_at", "effective_date", "effective_at", "updated_at", "created_at"):
        value = record.get(key) if record else None
        if value:
            return value
    return relationship.get("created_at") if relationship else None


def _governance_number_for_link(link):
    record = link.get("record") or {}
    if link.get("record_type") == "directive":
        return record.get("governance_number") or record.get("directive_id")
    if link.get("record_type") == "policy":
        return record.get("governance_number") or record.get("policy_id")
    return link.get("governance_id")


def _governance_impact_for_record(record, relationship):
    state = (record.get("lifecycle_state") or record.get("status") or "").strip()
    relationship_type = (relationship.get("relationship_type") or "").strip()
    approval_required = record.get("approval_required") in ("Yes", "yes", "1", 1, True)
    approved_at = record.get("approved_at")

    if state in {"Superseded", "Archived", "Retired"}:
        return "Superseded / Retired"

    if approval_required and not approved_at:
        return "Awaiting Approval"

    if state in {"Draft", "Submitted", "Under Review", "Pending Approval"}:
        return "Pending Governance"

    if state in {"Implemented"}:
        return "Fully Implemented"

    if state in {"Approved", "Ratified", "Effective"}:
        if relationship_type == "governs":
            return "Governs Current Workflow"
        if relationship_type == "authorizes":
            return "Authorizes Action"
        if relationship_type == "implements":
            return "Requires Implementation"
        if relationship_type == "depends_on":
            return "Dependency"
        if relationship_type == "references":
            return "Reference Authority"
        return "Active Governance"

    return "Review Needed"


def _matter_governance_health(summary):
    if summary.get("total", 0) == 0:
        return {
            "status": "No Governance Links",
            "level": "neutral",
            "description": "No Directive or Policy governance records are linked to this Matter.",
        }

    if summary.get("superseded_or_retired", 0):
        return {
            "status": "Governance Conflict",
            "level": "red",
            "description": "One or more linked governance records are superseded, retired, or archived.",
        }

    if summary.get("pending_approval", 0) or summary.get("pending_governance", 0):
        return {
            "status": "Pending Governance",
            "level": "yellow",
            "description": "One or more linked governance records require approval, review, or completion.",
        }

    return {
        "status": "Compliant",
        "level": "green",
        "description": "Linked governance records are active, approved, effective, or implemented.",
    }


def _trust_governance_impact_for_record(record, relationship):
    state = (record.get("lifecycle_state") or record.get("status") or "").strip()
    relationship_type = (relationship.get("relationship_type") or "").strip()
    approval_required = record.get("approval_required") in ("Yes", "yes", "1", 1, True)
    approved_at = record.get("approved_at")

    if state in {"Superseded", "Archived", "Retired"}:
        return "Superseded / Retired"

    if approval_required and not approved_at:
        return "Awaiting Approval"

    if state in {"Draft", "Submitted", "Under Review", "Pending Approval"}:
        return "Pending Governance"

    if state == "Implemented":
        return "Fully Implemented"

    if relationship_type in {"authorizes", "governs", "implements"} and state in {"Issued", "Approved", "Ratified", "Effective"}:
        return "Active Governance"

    if relationship_type in {"depends_on", "references"}:
        return "Reference / Dependency"

    if relationship_type == "supersedes":
        return "Superseding Authority"

    return "Governance Linked"


def build_document_governance_summary(document_id):
    links = build_governance_links_for_object("Document", document_id)

    directive_count = 0
    policy_count = 0
    pending_count = 0
    approved_count = 0
    active_count = 0

    for link in links:
        record = link.get("record") or {}
        record_type = link.get("record_type")
        status = record.get("status") or "Draft"
        relationship = link.get("relationship") or {}

        if record_type == "directive":
            directive_count += 1
        elif record_type == "policy":
            policy_count += 1

        if status in {"Draft", "Issued"}:
            pending_count += 1

        if status in {"Active", "Completed", "Approved", "Ratified", "Effective", "Implemented"}:
            approved_count += 1

        if relationship.get("status") == "Active":
            active_count += 1

    if not links:
        health = "No Governance Links"
    elif pending_count:
        health = "Governance Pending"
    else:
        health = "Governed"

    return {
        "total_links": len(links),
        "directives": directive_count,
        "policies": policy_count,
        "pending_governance": pending_count,
        "approved_governance": approved_count,
        "active_relationships": active_count,
        "health": health,
    }


def build_document_governance_impact(document_id, document_object=None):
    links = build_governance_links_for_object("Document", document_id)

    document_title = ""
    document_type = ""
    document_status = ""
    verification_status = ""
    lifecycle_status = ""
    governance_policy = ""
    retention_policy = ""
    allows_edit = None
    allows_delete = None
    requires_reason = None
    requires_authority = None

    if document_object:
        identity = document_object.get("identity") or {}
        status_block = document_object.get("status") or {}
        governance_block = document_object.get("governance") or {}

        document_title = identity.get("title") or ""
        document_type = identity.get("document_type") or ""
        document_status = status_block.get("status") or ""
        verification_status = status_block.get("verification_status") or ""
        lifecycle_status = status_block.get("lifecycle_status") or ""
        governance_policy = governance_block.get("governance_policy") or ""
        retention_policy = governance_block.get("retention_policy") or ""
        allows_edit = governance_block.get("allows_edit")
        allows_delete = governance_block.get("allows_delete")
        requires_reason = governance_block.get("requires_reason")
        requires_authority = governance_block.get("requires_authority")

    findings = []
    risks = []
    controls = []

    pending_count = 0
    approved_count = 0
    active_relationships = 0

    for link in links:
        record = link.get("record") or {}
        relationship = link.get("relationship") or {}
        status = record.get("status") or "Draft"
        governance_type = link.get("governance_type")
        governance_id = link.get("governance_id")
        relationship_type = relationship.get("relationship_type") or "references"

        if status in {"Draft", "Issued"}:
            pending_count += 1
            risks.append(
                {
                    "level": "Moderate",
                    "risk": f"{governance_type} {governance_id} linked but remains {status}.",
                    "impact": "Document is governed by a record that is not Active or Completed.",
                }
            )

        if status in {"Active", "Completed", "Approved", "Ratified", "Effective", "Implemented"}:
            approved_count += 1

        if relationship.get("status") == "Active":
            active_relationships += 1
            controls.append(
                {
                    "control": f"{relationship_type} {governance_type} {governance_id}",
                    "status": "Active",
                    "basis": relationship.get("reason") or "Governance relationship recorded.",
                }
            )

    if not links:
        findings.append("Document has no linked Directive or Policy governance records.")
        risks.append(
            {
                "level": "Low",
                "risk": "No document-specific governance links are recorded.",
                "impact": "Document may rely only on general platform governance unless a specific Directive or Policy is linked.",
            }
        )
        impact_status = "No Governance Links"
    elif pending_count:
        findings.append("Document workspace has linked governance records, but one or more remain Draft or Issued.")
        impact_status = "Governance Pending"
    else:
        findings.append("Document workspace has active governance coverage.")
        impact_status = "Governed"

    if verification_status:
        controls.append(
            {
                "control": f"Verification Status {verification_status}",
                "status": verification_status,
                "basis": "Document object model verification field.",
            }
        )

    if lifecycle_status:
        controls.append(
            {
                "control": f"Lifecycle Status {lifecycle_status}",
                "status": lifecycle_status,
                "basis": "Document object model lifecycle field.",
            }
        )

    if retention_policy:
        controls.append(
            {
                "control": f"Retention Policy {retention_policy}",
                "status": "Recorded",
                "basis": "Document governance block retention policy.",
            }
        )

    if allows_delete is True:
        risks.append(
            {
                "level": "High",
                "risk": "Document allows deletion.",
                "impact": "Institutional record custody may be weakened unless deletion is separately controlled.",
            }
        )
    elif allows_delete is False:
        controls.append(
            {
                "control": "Delete Restriction",
                "status": "Protected",
                "basis": "Document governance block disallows deletion.",
            }
        )

    if requires_reason is True:
        controls.append(
            {
                "control": "Reason Requirement",
                "status": "Required",
                "basis": "Document governance block requires reason for governed actions.",
            }
        )

    if requires_authority is True:
        controls.append(
            {
                "control": "Authority Requirement",
                "status": "Required",
                "basis": "Document governance block requires authority for governed actions.",
            }
        )

    return {
        "impact_status": impact_status,
        "document_id": document_id,
        "document_title": document_title,
        "document_type": document_type,
        "document_status": document_status,
        "verification_status": verification_status,
        "lifecycle_status": lifecycle_status,
        "governance_policy": governance_policy,
        "retention_policy": retention_policy,
        "allows_edit": allows_edit,
        "allows_delete": allows_delete,
        "requires_reason": requires_reason,
        "requires_authority": requires_authority,
        "total_links": len(links),
        "pending_count": pending_count,
        "approved_count": approved_count,
        "active_relationships": active_relationships,
        "findings": findings,
        "risks": risks,
        "controls": controls,
    }


def build_document_governance_timeline(document_id):
    timeline = []

    for link in build_governance_links_for_object("Document", document_id):
        relationship = link.get("relationship") or {}
        record = link.get("record") or {}

        timeline.append(
            {
                "date": (
                    record.get("approved_at")
                    or record.get("effective_at")
                    or relationship.get("created_at")
                    or record.get("updated_at")
                    or record.get("created_at")
                    or ""
                ),
                "governance_type": link.get("governance_type"),
                "governance_id": link.get("governance_id"),
                "title": record.get("title"),
                "status": record.get("status") or "Draft",
                "relationship_type": relationship.get("relationship_type"),
                "relationship_status": relationship.get("status"),
                "direction": link.get("direction"),
                "authority": relationship.get("authority"),
                "reason": relationship.get("reason"),
                "relationship_id": relationship.get("relationship_id"),
            }
        )

    return sorted(
        timeline,
        key=lambda item: item.get("date") or "",
        reverse=True,
    )


def build_certificate_governance_summary(certificate_id):
    links = build_governance_links_for_object("Certificate", certificate_id)

    directive_count = 0
    policy_count = 0
    pending_count = 0
    approved_count = 0
    active_count = 0

    for link in links:
        record = link.get("record") or {}
        record_type = link.get("record_type")
        status = record.get("status") or "Draft"

        if record_type == "directive":
            directive_count += 1
        elif record_type == "policy":
            policy_count += 1

        if status in {"Draft", "Issued"}:
            pending_count += 1
        if record.get("approved_at"):
            approved_count += 1
        if (link.get("relationship") or {}).get("status") == "Active":
            active_count += 1

    if not links:
        health = "No Governance Linked"
    elif pending_count:
        health = "Governance Pending"
    else:
        health = "Governance Active"

    return {
        "total_links": len(links),
        "directives": directive_count,
        "policies": policy_count,
        "pending_governance": pending_count,
        "approved_governance": approved_count,
        "active_relationships": active_count,
        "health": health,
    }


def build_certificate_governance_impact(certificate_id, certificate_object=None):
    links = build_governance_links_for_object("Certificate", certificate_id)

    certificate_status = ""
    verification_status = ""
    lifecycle_status = ""
    chain_status = ""

    if certificate_object:
        status_block = certificate_object.get("status") or {}
        certificate_status = status_block.get("certification_status") or ""
        verification_status = status_block.get("verification_status") or ""
        lifecycle_status = status_block.get("lifecycle_status") or ""
        chain_status = status_block.get("chain_status") or ""

    findings = []
    risks = []
    controls = []

    directive_count = 0
    policy_count = 0
    pending_count = 0
    active_relationship_count = 0
    approved_count = 0

    for link in links:
        record = link.get("record") or {}
        relationship = link.get("relationship") or {}
        record_type = link.get("record_type")
        record_status = record.get("status") or "Draft"
        relationship_status = relationship.get("status") or ""

        if record_type == "directive":
            directive_count += 1
        elif record_type == "policy":
            policy_count += 1

        if relationship_status == "Active":
            active_relationship_count += 1

        if record.get("approved_at"):
            approved_count += 1

        if record_status in {"Draft", "Issued"}:
            pending_count += 1
            risks.append({
                "level": "Moderate",
                "issue": f"{record_type.title()} {link.get('governance_id')} is linked but remains {record_status}.",
                "impact": "Certificate is governed by a record that has not reached Active or Completed state.",
            })

        if relationship.get("relationship_type") in {"governs", "authorizes"}:
            controls.append({
                "control": relationship.get("relationship_type"),
                "record": link.get("governance_id"),
                "effect": f"{record_type.title()} provides governance authority over this certificate workspace.",
            })

    if not links:
        impact_status = "Ungoverned"
        findings.append("No institutional Directive or Policy is linked to this certificate workspace.")
        risks.append({
            "level": "High",
            "issue": "Certificate workspace has no linked governance records.",
            "impact": "Certificate lifecycle actions may lack an explicit governance basis.",
        })
    elif pending_count:
        impact_status = "Governance Pending"
        findings.append("Certificate workspace has linked governance records, but one or more remain Draft or Issued.")
    else:
        impact_status = "Governance Controlled"
        findings.append("Certificate workspace has active governance coverage.")

    if certificate_status == "Certified" and verification_status == "verified":
        findings.append("Certificate is certified and verified while governance coverage is present.")
    elif certificate_status or verification_status:
        findings.append(
            f"Certificate status is {certificate_status or '-'} and verification status is {verification_status or '-'}."
        )

    if lifecycle_status == "Issued":
        controls.append({
            "control": "Issued Lifecycle",
            "record": certificate_id,
            "effect": "Certificate is in issued lifecycle state and should remain governed by immutable certificate policy.",
        })

    if chain_status == "Current":
        controls.append({
            "control": "Current Chain Position",
            "record": certificate_id,
            "effect": "Certificate is the current chain record and should be protected from unauthorized supersession.",
        })

    return {
        "impact_status": impact_status,
        "certificate_status": certificate_status,
        "verification_status": verification_status,
        "lifecycle_status": lifecycle_status,
        "chain_status": chain_status,
        "total_links": len(links),
        "directive_count": directive_count,
        "policy_count": policy_count,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "active_relationship_count": active_relationship_count,
        "findings": findings,
        "risks": risks,
        "controls": controls,
    }


def build_certificate_governance_timeline(certificate_id):
    links = build_governance_links_for_object("Certificate", certificate_id)
    timeline = []

    for link in links:
        relationship = link.get("relationship") or {}
        record = link.get("record") or {}
        record_type = link.get("record_type") or ""
        governance_id = link.get("governance_id") or ""

        timeline.append(
            {
                "date": _governance_display_date(record, relationship),
                "record_type": record_type.title(),
                "record_id": governance_id,
                "title": record.get("title") or governance_id,
                "status": record.get("status") or "Draft",
                "relationship_type": relationship.get("relationship_type") or "",
                "relationship_status": relationship.get("status") or "",
                "direction": link.get("direction") or "",
                "authority": relationship.get("authority") or record.get("authority") or "",
                "reason": relationship.get("reason") or record.get("rationale") or "",
            }
        )

    timeline.sort(key=lambda item: item.get("date") or "", reverse=True)
    return timeline


def build_trust_governance_summary(trust_id):
    links = build_trust_governance_links(trust_id)
    summary = {
        "total": len(links),
        "directives": 0,
        "policies": 0,
        "pending_approval": 0,
        "approved_or_ratified": 0,
        "effective": 0,
        "implemented": 0,
        "pending_governance": 0,
        "requires_implementation": 0,
        "superseded_or_retired": 0,
        "active_governance": 0,
        "latest_activity": None,
        "health": "No Governance Links",
        "health_note": "No Directive or Policy governance records are linked to this Trust.",
    }

    pending_states = {"Draft", "Submitted", "Under Review", "Pending Approval"}
    approved_states = {"Approved", "Ratified"}
    effective_states = {"Effective"}
    implemented_states = {"Implemented"}

    for link in links:
        record = link.get("record") or {}
        state = record.get("lifecycle_state") or record.get("status") or ""

        if link.get("record_type") == "directive":
            summary["directives"] += 1
        elif link.get("record_type") == "policy":
            summary["policies"] += 1

        if state in pending_states or (record.get("approval_required") in ("Yes", "yes", "1", 1, True) and not record.get("approved_at")):
            summary["pending_approval"] += 1
        if state in approved_states or record.get("approved_at"):
            summary["approved_or_ratified"] += 1
        if state in effective_states:
            summary["effective"] += 1
        if state in implemented_states:
            summary["implemented"] += 1

        impact = _trust_governance_impact_for_record(record, link.get("relationship") or {})
        if impact in {"Awaiting Approval", "Pending Governance"}:
            summary["pending_governance"] += 1
        if impact in {"Active Governance", "Governance Linked", "Superseding Authority"}:
            summary["requires_implementation"] += 1
        if impact == "Superseded / Retired":
            summary["superseded_or_retired"] += 1
        if impact == "Active Governance":
            summary["active_governance"] += 1

        display_date = _governance_display_date(record, link.get("relationship"))
        if display_date and (not summary["latest_activity"] or str(display_date) > str(summary["latest_activity"])):
            summary["latest_activity"] = display_date

    if summary["total"] == 0:
        return summary

    if summary["pending_governance"]:
        summary["health"] = "Governance Pending"
        summary["health_note"] = "One or more linked governance records are still pending approval, issuance, or ratification."
    elif summary["superseded_or_retired"] == summary["total"]:
        summary["health"] = "Governance Retired"
        summary["health_note"] = "All linked governance records are superseded, retired, or archived."
    elif summary["active_governance"]:
        summary["health"] = "Governance Active"
        summary["health_note"] = "At least one active governance record currently governs this Trust."
    else:
        summary["health"] = "Governance Linked"
        summary["health_note"] = "Governance records are linked, but no active governing record is currently detected."

    return summary


def build_trust_governance_timeline(trust_id):
    timeline = []

    for link in build_trust_governance_links(trust_id):
        record = link.get("record") or {}
        relationship = link.get("relationship") or {}
        record_type = link.get("record_type")
        governance_id = link.get("governance_id")

        if record_type == "directive":
            record_label = "Directive"
            detail_endpoint = "governance_directive_detail"
        elif record_type == "policy":
            record_label = "Policy"
            detail_endpoint = "governance_policy_detail"
        else:
            continue

        timeline.append({
            "governance_number": _governance_number_for_link(link),
            "governance_id": governance_id,
            "record_type": record_type,
            "record_label": record_label,
            "detail_endpoint": detail_endpoint,
            "title": record.get("title") or "Untitled governance record",
            "lifecycle_state": record.get("lifecycle_state") or record.get("status") or "Unspecified",
            "relationship_id": relationship.get("relationship_id"),
            "relationship_type": relationship.get("relationship_type"),
            "direction": link.get("direction"),
            "impact": _trust_governance_impact_for_record(record, relationship),
            "created_at": record.get("created_at"),
            "effective_at": record.get("effective_date") or record.get("effective_at"),
            "approved_at": record.get("approved_at"),
            "display_date": _governance_display_date(record, relationship),
        })

    timeline.sort(key=lambda item: str(item.get("display_date") or ""), reverse=True)
    return timeline


def build_matter_governance_summary(matter_id):
    links = build_matter_governance_links(matter_id)
    summary = {
        "total": len(links),
        "directives": 0,
        "policies": 0,
        "pending_approval": 0,
        "approved_or_ratified": 0,
        "effective": 0,
        "implemented": 0,
        "latest_activity": None,
        "pending_governance": 0,
        "superseded_or_retired": 0,
        "requires_implementation": 0,
        "active_governance": 0,
        "governance_health": {},
    }

    pending_states = {"Draft", "Submitted", "Under Review", "Pending Approval"}
    approved_states = {"Approved", "Ratified"}
    effective_states = {"Effective"}
    implemented_states = {"Implemented"}

    for link in links:
        record = link.get("record") or {}
        state = record.get("lifecycle_state") or record.get("status") or ""

        if link.get("record_type") == "directive":
            summary["directives"] += 1
        elif link.get("record_type") == "policy":
            summary["policies"] += 1

        if state in pending_states or (record.get("approval_required") in ("Yes", "yes", "1", 1, True) and not record.get("approved_at")):
            summary["pending_approval"] += 1
        if state in approved_states or record.get("approved_at"):
            summary["approved_or_ratified"] += 1
        if state in effective_states:
            summary["effective"] += 1
        if state in implemented_states:
            summary["implemented"] += 1

        impact = _governance_impact_for_record(record, link.get("relationship") or {})
        if impact in {"Awaiting Approval", "Pending Governance"}:
            summary["pending_governance"] += 1
        elif impact == "Superseded / Retired":
            summary["superseded_or_retired"] += 1
        elif impact == "Requires Implementation":
            summary["requires_implementation"] += 1
        elif impact in {"Active Governance", "Governs Current Workflow", "Authorizes Action", "Fully Implemented"}:
            summary["active_governance"] += 1

        display_date = _governance_display_date(record, link.get("relationship"))
        if display_date and (not summary["latest_activity"] or str(display_date) > str(summary["latest_activity"])):
            summary["latest_activity"] = display_date

    summary["governance_health"] = _matter_governance_health(summary)
    return summary


def build_matter_governance_timeline(matter_id):
    timeline = []

    for link in build_matter_governance_links(matter_id):
        record = link.get("record") or {}
        relationship = link.get("relationship") or {}
        record_type = link.get("record_type")
        governance_id = link.get("governance_id")

        if record_type == "directive":
            record_label = "Directive"
        elif record_type == "policy":
            record_label = "Policy"
        else:
            continue

        timeline.append({
            "governance_number": _governance_number_for_link(link),
            "governance_id": governance_id,
            "record_type": record_type,
            "record_label": record_label,
            "title": record.get("title") or "Untitled governance record",
            "lifecycle_state": record.get("lifecycle_state") or record.get("status") or "Unspecified",
            "relationship_id": relationship.get("relationship_id"),
            "relationship_type": relationship.get("relationship_type"),
            "direction": link.get("direction"),
            "created_at": record.get("created_at"),
            "effective_at": record.get("effective_date") or record.get("effective_at"),
            "approved_at": record.get("approved_at"),
            "display_date": _governance_display_date(record, relationship),
            "impact": _governance_impact_for_record(record, relationship),
        })

    timeline.sort(key=lambda item: str(item.get("display_date") or ""), reverse=True)
    return timeline


def generate_directive_governance_packet_pdf(directive_id):
    ensure_governance_tables()

    directive = get_governance_record("directive", directive_id)
    if not directive:
        return None

    metadata = build_governance_metadata("directive", directive)
    outgoing_relationships = list_outgoing_governance_relationships(
        "Directive",
        directive_id,
    )
    incoming_relationships = list_incoming_governance_relationships(
        "Directive",
        directive_id,
    )
    implementation_entries = list_directive_implementation_entries(directive_id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = getSampleStyleSheet()
    story = []

    def heading(text):
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>{_pdf_text(text)}</b>", styles["Heading2"]))

    def body(text):
        story.append(Paragraph(_pdf_text(text), styles["BodyText"]))

    def table(rows, widths=None):
        if not rows:
            body("No records.")
            return
        tbl = Table(rows, colWidths=widths, repeatRows=1 if len(rows) > 1 else 0)
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(tbl)

    def pair_rows(pairs):
        return [
            [
                Paragraph(f"<b>{_pdf_text(label)}</b>", styles["BodyText"]),
                Paragraph(_pdf_text(value), styles["BodyText"]),
            ]
            for label, value in pairs
        ]

    story.append(Paragraph("Directive Governance Packet", styles["Title"]))
    body(
        "Read-only governance packet generated from the IOS-3A Directive record, "
        "relationships, approval data, provenance, and implementation ledger."
    )

    heading("Directive Identity")
    table(
        pair_rows(
            [
                ("Governance Number", directive.get("directive_id")),
                ("Directive Code", directive.get("directive_code")),
                ("Title", directive.get("title")),
                ("Directive Type", directive.get("directive_type")),
                ("Lifecycle State", directive.get("status")),
                ("Version", directive.get("version_label")),
                ("Created By", directive.get("created_by")),
                ("Created At", directive.get("created_at")),
                ("Updated At", directive.get("updated_at")),
            ]
        ),
        [150, 360],
    )

    heading("Authority / Approval")
    table(
        pair_rows(
            [
                ("Authority", directive.get("authority")),
                ("Issuing Authority", directive.get("issuing_authority")),
                ("Authority Basis", directive.get("authority_basis")),
                ("Approval Status", metadata.get("approval_status")),
                ("Approval Required", "Yes" if metadata.get("approval_required") else "No"),
                ("Approved By", directive.get("approved_by")),
                ("Approved At", directive.get("approved_at")),
            ]
        ),
        [150, 360],
    )

    heading("Source / Provenance")
    table(
        pair_rows(
            [
                ("Source Type", directive.get("source_type")),
                ("Source ID", directive.get("source_id")),
                ("Source Label", directive.get("source_label")),
                ("Source Notes", directive.get("source_notes")),
            ]
        ),
        [150, 360],
    )

    heading("Directive Substance")
    table(
        pair_rows(
            [
                ("Summary", directive.get("summary")),
                ("Instruction", directive.get("instruction")),
                ("Rationale", directive.get("rationale")),
                ("Scope", directive.get("scope")),
                ("Milestone Plan", directive.get("milestone_plan")),
                ("Completion Record", directive.get("completion_record")),
            ]
        ),
        [150, 360],
    )

    heading("Outgoing Relationships")
    table(
        [[
            Paragraph("<b>Relationship</b>", styles["BodyText"]),
            Paragraph("<b>Type</b>", styles["BodyText"]),
            Paragraph("<b>Target</b>", styles["BodyText"]),
            Paragraph("<b>Status</b>", styles["BodyText"]),
            Paragraph("<b>Authority / Reason</b>", styles["BodyText"]),
        ]]
        + [
            [
                Paragraph(_pdf_text(row.get("relationship_id")), styles["BodyText"]),
                Paragraph(_pdf_text(row.get("relationship_type")), styles["BodyText"]),
                Paragraph(
                    _pdf_text(f"{row.get('target_object_type')} {row.get('target_object_id')}"),
                    styles["BodyText"],
                ),
                Paragraph(_pdf_text(row.get("status")), styles["BodyText"]),
                Paragraph(
                    _pdf_text(f"{row.get('authority') or '-'} / {row.get('reason') or '-'}"),
                    styles["BodyText"],
                ),
            ]
            for row in outgoing_relationships
        ],
        [88, 70, 115, 55, 182],
    )

    heading("Incoming Relationships")
    table(
        [[
            Paragraph("<b>Relationship</b>", styles["BodyText"]),
            Paragraph("<b>Type</b>", styles["BodyText"]),
            Paragraph("<b>Source</b>", styles["BodyText"]),
            Paragraph("<b>Status</b>", styles["BodyText"]),
            Paragraph("<b>Authority / Reason</b>", styles["BodyText"]),
        ]]
        + [
            [
                Paragraph(_pdf_text(row.get("relationship_id")), styles["BodyText"]),
                Paragraph(_pdf_text(row.get("relationship_type")), styles["BodyText"]),
                Paragraph(
                    _pdf_text(f"{row.get('source_object_type')} {row.get('source_object_id')}"),
                    styles["BodyText"],
                ),
                Paragraph(_pdf_text(row.get("status")), styles["BodyText"]),
                Paragraph(
                    _pdf_text(f"{row.get('authority') or '-'} / {row.get('reason') or '-'}"),
                    styles["BodyText"],
                ),
            ]
            for row in incoming_relationships
        ],
        [88, 70, 115, 55, 182],
    )

    heading("Implementation Ledger")
    table(
        [[
            Paragraph("<b>Entry</b>", styles["BodyText"]),
            Paragraph("<b>Action</b>", styles["BodyText"]),
            Paragraph("<b>Performed</b>", styles["BodyText"]),
            Paragraph("<b>Status</b>", styles["BodyText"]),
            Paragraph("<b>Evidence / Notes</b>", styles["BodyText"]),
        ]]
        + [
            [
                Paragraph(_pdf_text(row.get("entry_id")), styles["BodyText"]),
                Paragraph(
                    _pdf_text(f"{row.get('action_type') or 'Action'}: {row.get('action_summary')}"),
                    styles["BodyText"],
                ),
                Paragraph(
                    _pdf_text(f"{row.get('performed_by') or 'System'} / {row.get('performed_at') or '-'}"),
                    styles["BodyText"],
                ),
                Paragraph(_pdf_text(row.get("result_status")), styles["BodyText"]),
                Paragraph(
                    _pdf_text(f"{row.get('evidence_reference') or '-'} / {row.get('notes') or '-'}"),
                    styles["BodyText"],
                ),
            ]
            for row in implementation_entries
        ],
        [80, 140, 110, 60, 120],
    )

    story.append(Spacer(1, 12))
    body(
        f"Packet generated at {_now()}. This packet is read-only evidence of recorded governance data."
    )

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_policy_governance_packet_pdf(policy_id):
    ensure_governance_tables()

    policy = get_governance_record("policy", policy_id)
    if not policy:
        return None

    metadata = build_governance_metadata("policy", policy)
    outgoing_relationships = list_outgoing_governance_relationships("Policy", policy_id)
    incoming_relationships = list_incoming_governance_relationships("Policy", policy_id)
    activity_entries = list_policy_activity_entries(policy_id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = getSampleStyleSheet()
    story = []

    def heading(text):
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>{_pdf_text(text)}</b>", styles["Heading2"]))

    def body(text):
        story.append(Paragraph(_pdf_text(text), styles["BodyText"]))

    def table(rows, widths=None):
        if not rows:
            body("No records.")
            return
        tbl = Table(rows, colWidths=widths, repeatRows=1 if len(rows) > 1 else 0)
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(tbl)

    def pair_rows(pairs):
        return [
            [
                Paragraph(f"<b>{_pdf_text(label)}</b>", styles["BodyText"]),
                Paragraph(_pdf_text(value), styles["BodyText"]),
            ]
            for label, value in pairs
        ]

    story.append(Paragraph("Policy Governance Packet", styles["Title"]))
    body(
        "Read-only governance packet generated from the IOS-3B Policy record, "
        "relationships, approval data, provenance, and activity ledger."
    )

    heading("Policy Identity")
    table(
        pair_rows(
            [
                ("Governance Number", policy.get("policy_id")),
                ("Title", policy.get("title")),
                ("Policy Area", policy.get("policy_area")),
                ("Lifecycle State", policy.get("status")),
                ("Version", policy.get("version_label")),
                ("Created By", policy.get("created_by")),
                ("Created At", policy.get("created_at")),
                ("Updated At", policy.get("updated_at")),
            ]
        ),
        [150, 360],
    )

    heading("Authority / Approval")
    table(
        pair_rows(
            [
                ("Authority", policy.get("authority")),
                ("Issuing Authority", policy.get("issuing_authority")),
                ("Authority Basis", policy.get("authority_basis")),
                ("Approval Status", metadata.get("approval_status")),
                ("Approval Required", "Yes" if metadata.get("approval_required") else "No"),
                ("Approved By", policy.get("approved_by")),
                ("Approved At", policy.get("approved_at")),
            ]
        ),
        [150, 360],
    )

    heading("Source / Provenance")
    table(
        pair_rows(
            [
                ("Source Type", policy.get("source_type")),
                ("Source ID", policy.get("source_id")),
                ("Source Label", policy.get("source_label")),
                ("Source Notes", policy.get("source_notes")),
            ]
        ),
        [150, 360],
    )

    heading("Policy Substance")
    table(
        pair_rows(
            [
                ("Summary", policy.get("summary")),
                ("Policy Text", policy.get("policy_text")),
                ("Rationale", policy.get("rationale")),
            ]
        ),
        [150, 360],
    )

    heading("Outgoing Relationships")
    table(
        [[
            Paragraph("<b>Relationship</b>", styles["BodyText"]),
            Paragraph("<b>Type</b>", styles["BodyText"]),
            Paragraph("<b>Target</b>", styles["BodyText"]),
            Paragraph("<b>Status</b>", styles["BodyText"]),
            Paragraph("<b>Authority / Reason</b>", styles["BodyText"]),
        ]]
        + [
            [
                Paragraph(_pdf_text(row.get("relationship_id")), styles["BodyText"]),
                Paragraph(_pdf_text(row.get("relationship_type")), styles["BodyText"]),
                Paragraph(_pdf_text(f"{row.get('target_object_type')} {row.get('target_object_id')}"), styles["BodyText"]),
                Paragraph(_pdf_text(row.get("status")), styles["BodyText"]),
                Paragraph(_pdf_text(f"{row.get('authority') or '-'} / {row.get('reason') or '-'}"), styles["BodyText"]),
            ]
            for row in outgoing_relationships
        ],
        [88, 70, 115, 55, 182],
    )

    heading("Incoming Relationships")
    table(
        [[
            Paragraph("<b>Relationship</b>", styles["BodyText"]),
            Paragraph("<b>Type</b>", styles["BodyText"]),
            Paragraph("<b>Source</b>", styles["BodyText"]),
            Paragraph("<b>Status</b>", styles["BodyText"]),
            Paragraph("<b>Authority / Reason</b>", styles["BodyText"]),
        ]]
        + [
            [
                Paragraph(_pdf_text(row.get("relationship_id")), styles["BodyText"]),
                Paragraph(_pdf_text(row.get("relationship_type")), styles["BodyText"]),
                Paragraph(_pdf_text(f"{row.get('source_object_type')} {row.get('source_object_id')}"), styles["BodyText"]),
                Paragraph(_pdf_text(row.get("status")), styles["BodyText"]),
                Paragraph(_pdf_text(f"{row.get('authority') or '-'} / {row.get('reason') or '-'}"), styles["BodyText"]),
            ]
            for row in incoming_relationships
        ],
        [88, 70, 115, 55, 182],
    )

    heading("Policy Activity Ledger")
    table(
        [[
            Paragraph("<b>Entry</b>", styles["BodyText"]),
            Paragraph("<b>Action</b>", styles["BodyText"]),
            Paragraph("<b>Performed</b>", styles["BodyText"]),
            Paragraph("<b>Status</b>", styles["BodyText"]),
            Paragraph("<b>Evidence / Notes</b>", styles["BodyText"]),
        ]]
        + [
            [
                Paragraph(_pdf_text(row.get("entry_id")), styles["BodyText"]),
                Paragraph(_pdf_text(f"{row.get('action_type') or 'Action'}: {row.get('action_summary')}"), styles["BodyText"]),
                Paragraph(_pdf_text(f"{row.get('performed_by') or 'System'} / {row.get('performed_at') or '-'}"), styles["BodyText"]),
                Paragraph(_pdf_text(row.get("result_status")), styles["BodyText"]),
                Paragraph(_pdf_text(f"{row.get('evidence_reference') or '-'} / {row.get('notes') or '-'}"), styles["BodyText"]),
            ]
            for row in activity_entries
        ],
        [80, 140, 110, 60, 120],
    )

    story.append(Spacer(1, 12))
    body(
        f"Packet generated at {_now()}. This packet is read-only evidence of recorded governance data."
    )

    doc.build(story)
    buffer.seek(0)
    return buffer
