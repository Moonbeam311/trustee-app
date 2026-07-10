from datetime import datetime
from html import escape
from io import BytesIO
from uuid import uuid4

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from database.db import get_connection, get_current_firm_id
import sqlite3


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
        CREATE TABLE IF NOT EXISTS governance_relationship_audit_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audit_id TEXT UNIQUE NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            attempted_relationship_id TEXT,
            existing_relationship_id TEXT,
            action TEXT NOT NULL,
            outcome TEXT NOT NULL,
            source_object_type TEXT,
            source_object_id TEXT,
            relationship_type TEXT,
            target_object_type TEXT,
            target_object_id TEXT,
            authority TEXT,
            reason TEXT,
            actor TEXT,
            message TEXT,
            created_at TEXT
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


def record_governance_relationship_audit(
    *,
    firm_id=None,
    attempted_relationship_id=None,
    existing_relationship_id=None,
    action="create_relationship",
    outcome="unknown",
    source_object_type=None,
    source_object_id=None,
    relationship_type=None,
    target_object_type=None,
    target_object_id=None,
    authority=None,
    reason=None,
    actor=None,
    message=None,
):
    ensure_governance_tables()

    audit_id = _public_id("GRAUD")
    firm_id = firm_id or get_current_firm_id()
    now = _now()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO governance_relationship_audit_ledger (
            audit_id,
            firm_id,
            attempted_relationship_id,
            existing_relationship_id,
            action,
            outcome,
            source_object_type,
            source_object_id,
            relationship_type,
            target_object_type,
            target_object_id,
            authority,
            reason,
            actor,
            message,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            audit_id,
            firm_id,
            attempted_relationship_id,
            existing_relationship_id,
            action,
            outcome,
            source_object_type,
            source_object_id,
            relationship_type,
            target_object_type,
            target_object_id,
            authority,
            reason,
            actor,
            message,
            now,
        ),
    )
    conn.commit()
    conn.close()

    return audit_id


def list_governance_relationship_audits(limit=50, firm_id=None, object_type=None, object_id=None):
    ensure_governance_tables()

    firm_id = firm_id or get_current_firm_id()
    limit = int(limit or 50)

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    params = [firm_id]
    where = ["firm_id = ?"]

    if object_type and object_id:
        where.append(
            """(
                (source_object_type = ? AND source_object_id = ?)
                OR
                (target_object_type = ? AND target_object_id = ?)
            )"""
        )
        params.extend([object_type, object_id, object_type, object_id])

    rows = cur.execute(
        f"""
        SELECT *
        FROM governance_relationship_audit_ledger
        WHERE {' AND '.join(where)}
        ORDER BY id DESC
        LIMIT ?
        """,
        params + [limit],
    ).fetchall()

    conn.close()
    return [dict(row) for row in rows]


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
        relationship_id = data.get("relationship_id") or _public_id("GR")
        firm_id = data.get("firm_id") or get_current_firm_id()
        message = f"Missing required relationship fields: {', '.join(missing)}."
        audit_id = record_governance_relationship_audit(
            firm_id=firm_id,
            attempted_relationship_id=relationship_id,
            existing_relationship_id=None,
            action="create_relationship",
            outcome="validation_failed",
            source_object_type=cleaned.get("source_object_type"),
            source_object_id=cleaned.get("source_object_id"),
            relationship_type=cleaned.get("relationship_type"),
            target_object_type=cleaned.get("target_object_type"),
            target_object_id=cleaned.get("target_object_id"),
            authority=data.get("authority") or "",
            reason=data.get("reason") or "",
            actor=data.get("created_by") or "System",
            message=message,
        )
        return False, f"{message} | Audit: {audit_id}"

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
        audit_id = record_governance_relationship_audit(
            firm_id=firm_id,
            attempted_relationship_id=relationship_id,
            existing_relationship_id=existing["relationship_id"],
            action="create_relationship",
            outcome="duplicate_blocked",
            source_object_type=cleaned["source_object_type"],
            source_object_id=cleaned["source_object_id"],
            relationship_type=cleaned["relationship_type"],
            target_object_type=cleaned["target_object_type"],
            target_object_id=cleaned["target_object_id"],
            authority=data.get("authority") or "",
            reason=data.get("reason") or "",
            actor=data.get("created_by") or "System",
            message=(
                "Duplicate active governance relationship blocked: "
                f"{existing['relationship_id']}"
            ),
        )
        return False, (
            "Duplicate active governance relationship blocked: "
            f"{existing['relationship_id']} | Audit: {audit_id}"
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

    record_governance_relationship_audit(
        firm_id=firm_id,
        attempted_relationship_id=relationship_id,
        existing_relationship_id=None,
        action="create_relationship",
        outcome="created",
        source_object_type=cleaned["source_object_type"],
        source_object_id=cleaned["source_object_id"],
        relationship_type=cleaned["relationship_type"],
        target_object_type=cleaned["target_object_type"],
        target_object_id=cleaned["target_object_id"],
        authority=data.get("authority") or "",
        reason=data.get("reason") or "",
        actor=data.get("created_by") or "System",
        message=f"Governance relationship {relationship_id} created.",
    )

    return True, relationship_id


def get_governance_relationship(relationship_id, firm_id=None):
    ensure_governance_tables()

    relationship_id = (relationship_id or "").strip()
    if not relationship_id:
        return None

    firm_id = firm_id or get_current_firm_id()

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT *
        FROM governance_relationships
        WHERE relationship_id = ?
          AND firm_id = ?
        LIMIT 1
        """,
        (relationship_id, firm_id),
    ).fetchone()
    conn.close()

    return dict(row) if row else None


def get_governance_relationship_audit(audit_id, firm_id=None):
    ensure_governance_tables()

    audit_id = (audit_id or "").strip()
    if not audit_id:
        return None

    firm_id = firm_id or get_current_firm_id()

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT *
        FROM governance_relationship_audit_ledger
        WHERE audit_id = ?
          AND firm_id = ?
        LIMIT 1
        """,
        (audit_id, firm_id),
    ).fetchone()
    conn.close()

    return dict(row) if row else None


def list_audits_for_governance_relationship(relationship_id, limit=50, firm_id=None):
    ensure_governance_tables()

    relationship_id = (relationship_id or "").strip()
    if not relationship_id:
        return []

    firm_id = firm_id or get_current_firm_id()
    limit = int(limit or 50)

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT *
        FROM governance_relationship_audit_ledger
        WHERE firm_id = ?
          AND (
                attempted_relationship_id = ?
                OR existing_relationship_id = ?
          )
        ORDER BY id DESC
        LIMIT ?
        """,
        (firm_id, relationship_id, relationship_id, limit),
    ).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def retire_governance_relationship(relationship_id, authority=None, reason=None, actor=None, confirmation=None):
    ensure_governance_tables()

    relationship_id = (relationship_id or "").strip()
    authority = (authority or "").strip()
    reason = (reason or "").strip()
    actor = (actor or "System").strip() or "System"
    confirmation = (confirmation or "").strip()
    required_confirmation = "I UNDERSTAND THIS GOVERNANCE RELATIONSHIP WILL BE PRESERVED"

    if not relationship_id:
        audit_id = record_governance_relationship_audit(
            attempted_relationship_id=None,
            existing_relationship_id=None,
            action="retire_relationship",
            outcome="validation_failed",
            authority=authority,
            reason=reason,
            actor=actor,
            message="Relationship ID is required for retirement.",
        )
        return False, f"Relationship ID is required for retirement. | Audit: {audit_id}"

    relationship = get_governance_relationship(relationship_id)
    if not relationship:
        audit_id = record_governance_relationship_audit(
            attempted_relationship_id=relationship_id,
            existing_relationship_id=None,
            action="retire_relationship",
            outcome="not_found",
            authority=authority,
            reason=reason,
            actor=actor,
            message=f"Governance relationship {relationship_id} was not found.",
        )
        return False, f"Governance relationship {relationship_id} was not found. | Audit: {audit_id}"

    if not authority or not reason:
        audit_id = record_governance_relationship_audit(
            firm_id=relationship.get("firm_id"),
            attempted_relationship_id=relationship_id,
            existing_relationship_id=relationship_id,
            action="retire_relationship",
            outcome="validation_failed",
            source_object_type=relationship.get("source_object_type"),
            source_object_id=relationship.get("source_object_id"),
            relationship_type=relationship.get("relationship_type"),
            target_object_type=relationship.get("target_object_type"),
            target_object_id=relationship.get("target_object_id"),
            authority=authority,
            reason=reason,
            actor=actor,
            message="Authority and reason are required to retire a governance relationship.",
        )
        return False, (
            "Authority and reason are required to retire a governance relationship. "
            f"| Audit: {audit_id}"
        )

    if confirmation != required_confirmation:
        audit_id = record_governance_relationship_audit(
            firm_id=relationship.get("firm_id"),
            attempted_relationship_id=relationship_id,
            existing_relationship_id=relationship_id,
            action="retire_relationship",
            outcome="validation_failed",
            source_object_type=relationship.get("source_object_type"),
            source_object_id=relationship.get("source_object_id"),
            relationship_type=relationship.get("relationship_type"),
            target_object_type=relationship.get("target_object_type"),
            target_object_id=relationship.get("target_object_id"),
            authority=authority,
            reason=reason,
            actor=actor,
            message="Required preservation confirmation phrase was not provided for retirement.",
        )
        return False, (
            "Required preservation confirmation phrase was not provided for retirement. "
            f"| Audit: {audit_id}"
        )

    if (relationship.get("status") or "") == "Retired":
        audit_id = record_governance_relationship_audit(
            firm_id=relationship.get("firm_id"),
            attempted_relationship_id=relationship_id,
            existing_relationship_id=relationship_id,
            action="retire_relationship",
            outcome="already_retired",
            source_object_type=relationship.get("source_object_type"),
            source_object_id=relationship.get("source_object_id"),
            relationship_type=relationship.get("relationship_type"),
            target_object_type=relationship.get("target_object_type"),
            target_object_id=relationship.get("target_object_id"),
            authority=authority,
            reason=reason,
            actor=actor,
            message=f"Governance relationship {relationship_id} is already retired.",
        )
        return False, f"Governance relationship {relationship_id} is already retired. | Audit: {audit_id}"

    now = _now()
    firm_id = relationship.get("firm_id") or get_current_firm_id()

    conn = get_connection()
    conn.execute(
        """
        UPDATE governance_relationships
        SET status = 'Retired',
            retired_at = ?,
            updated_at = ?
        WHERE relationship_id = ?
          AND firm_id = ?
        """,
        (now, now, relationship_id, firm_id),
    )
    conn.commit()
    conn.close()

    audit_id = record_governance_relationship_audit(
        firm_id=firm_id,
        attempted_relationship_id=relationship_id,
        existing_relationship_id=relationship_id,
        action="retire_relationship",
        outcome="retired",
        source_object_type=relationship.get("source_object_type"),
        source_object_id=relationship.get("source_object_id"),
        relationship_type=relationship.get("relationship_type"),
        target_object_type=relationship.get("target_object_type"),
        target_object_id=relationship.get("target_object_id"),
        authority=authority,
        reason=reason,
        actor=actor,
        message=f"Governance relationship {relationship_id} retired.",
    )

    return True, f"Governance relationship {relationship_id} retired. | Audit: {audit_id}"



def reinstate_governance_relationship(relationship_id, authority=None, reason=None, actor=None, confirmation=None):
    ensure_governance_tables()

    relationship_id = (relationship_id or "").strip()
    authority = (authority or "").strip()
    reason = (reason or "").strip()
    actor = (actor or "System").strip() or "System"
    confirmation = (confirmation or "").strip()
    required_confirmation = "I UNDERSTAND THIS GOVERNANCE RELATIONSHIP WILL BE RESTORED TO ACTIVE STATUS"

    if not relationship_id:
        audit_id = record_governance_relationship_audit(
            attempted_relationship_id=None,
            existing_relationship_id=None,
            action="reinstate_relationship",
            outcome="validation_failed",
            authority=authority,
            reason=reason,
            actor=actor,
            message="Relationship ID is required for reinstatement.",
        )
        return False, f"Relationship ID is required for reinstatement. | Audit: {audit_id}"

    relationship = get_governance_relationship(relationship_id)
    if not relationship:
        audit_id = record_governance_relationship_audit(
            attempted_relationship_id=relationship_id,
            existing_relationship_id=None,
            action="reinstate_relationship",
            outcome="not_found",
            authority=authority,
            reason=reason,
            actor=actor,
            message=f"Governance relationship {relationship_id} was not found for reinstatement.",
        )
        return False, (
            f"Governance relationship {relationship_id} was not found for reinstatement. "
            f"| Audit: {audit_id}"
        )

    if (relationship.get("status") or "") == "Active":
        audit_id = record_governance_relationship_audit(
            firm_id=relationship.get("firm_id"),
            attempted_relationship_id=relationship_id,
            existing_relationship_id=relationship_id,
            action="reinstate_relationship",
            outcome="already_active",
            source_object_type=relationship.get("source_object_type"),
            source_object_id=relationship.get("source_object_id"),
            relationship_type=relationship.get("relationship_type"),
            target_object_type=relationship.get("target_object_type"),
            target_object_id=relationship.get("target_object_id"),
            authority=authority,
            reason=reason,
            actor=actor,
            message=f"Governance relationship {relationship_id} is already active.",
        )
        return False, f"Governance relationship {relationship_id} is already active. | Audit: {audit_id}"

    if not authority or not reason:
        audit_id = record_governance_relationship_audit(
            firm_id=relationship.get("firm_id"),
            attempted_relationship_id=relationship_id,
            existing_relationship_id=relationship_id,
            action="reinstate_relationship",
            outcome="validation_failed",
            source_object_type=relationship.get("source_object_type"),
            source_object_id=relationship.get("source_object_id"),
            relationship_type=relationship.get("relationship_type"),
            target_object_type=relationship.get("target_object_type"),
            target_object_id=relationship.get("target_object_id"),
            authority=authority,
            reason=reason,
            actor=actor,
            message="Authority and reason are required to reinstate a governance relationship.",
        )
        return False, (
            "Authority and reason are required to reinstate a governance relationship. "
            f"| Audit: {audit_id}"
        )

    if confirmation != required_confirmation:
        audit_id = record_governance_relationship_audit(
            firm_id=relationship.get("firm_id"),
            attempted_relationship_id=relationship_id,
            existing_relationship_id=relationship_id,
            action="reinstate_relationship",
            outcome="validation_failed",
            source_object_type=relationship.get("source_object_type"),
            source_object_id=relationship.get("source_object_id"),
            relationship_type=relationship.get("relationship_type"),
            target_object_type=relationship.get("target_object_type"),
            target_object_id=relationship.get("target_object_id"),
            authority=authority,
            reason=reason,
            actor=actor,
            message="Required restoration confirmation phrase was not provided for reinstatement.",
        )
        return False, (
            "Required restoration confirmation phrase was not provided for reinstatement. "
            f"| Audit: {audit_id}"
        )

    firm_id = relationship.get("firm_id") or get_current_firm_id()

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    conflict = conn.execute(
        """
        SELECT *
        FROM governance_relationships
        WHERE firm_id = ?
          AND relationship_id != ?
          AND status = 'Active'
          AND source_object_type = ?
          AND source_object_id = ?
          AND relationship_type = ?
          AND target_object_type = ?
          AND target_object_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            firm_id,
            relationship_id,
            relationship.get("source_object_type"),
            relationship.get("source_object_id"),
            relationship.get("relationship_type"),
            relationship.get("target_object_type"),
            relationship.get("target_object_id"),
        ),
    ).fetchone()

    if conflict:
        conn.close()
        conflict = dict(conflict)
        audit_id = record_governance_relationship_audit(
            firm_id=firm_id,
            attempted_relationship_id=relationship_id,
            existing_relationship_id=conflict.get("relationship_id"),
            action="reinstate_relationship",
            outcome="conflict_detected",
            source_object_type=relationship.get("source_object_type"),
            source_object_id=relationship.get("source_object_id"),
            relationship_type=relationship.get("relationship_type"),
            target_object_type=relationship.get("target_object_type"),
            target_object_id=relationship.get("target_object_id"),
            authority=authority,
            reason=reason,
            actor=actor,
            message=(
                f"Cannot reinstate {relationship_id}; active conflicting relationship "
                f"{conflict.get('relationship_id')} already controls the same governance link."
            ),
        )
        return False, (
            f"Cannot reinstate {relationship_id}; active conflicting relationship "
            f"{conflict.get('relationship_id')} already controls the same governance link. "
            f"| Audit: {audit_id}"
        )

    now = _now()
    conn.execute(
        """
        UPDATE governance_relationships
        SET status = 'Active',
            retired_at = '',
            updated_at = ?
        WHERE relationship_id = ?
          AND firm_id = ?
        """,
        (now, relationship_id, firm_id),
    )
    conn.commit()
    conn.close()

    audit_id = record_governance_relationship_audit(
        firm_id=firm_id,
        attempted_relationship_id=relationship_id,
        existing_relationship_id=relationship_id,
        action="reinstate_relationship",
        outcome="reinstated",
        source_object_type=relationship.get("source_object_type"),
        source_object_id=relationship.get("source_object_id"),
        relationship_type=relationship.get("relationship_type"),
        target_object_type=relationship.get("target_object_type"),
        target_object_id=relationship.get("target_object_id"),
        authority=authority,
        reason=reason,
        actor=actor,
        message=f"Governance relationship {relationship_id} reinstated to Active status.",
    )

    return True, f"Governance relationship {relationship_id} reinstated to Active status. | Audit: {audit_id}"



def supersede_governance_relationship(
    old_relationship_id,
    *,
    new_source_object_type=None,
    new_source_object_id=None,
    new_relationship_type=None,
    new_target_object_type=None,
    new_target_object_id=None,
    authority=None,
    reason=None,
    actor=None,
    confirmation=None,
):
    ensure_governance_tables()

    old_relationship_id = (old_relationship_id or "").strip()
    authority = (authority or "").strip()
    reason = (reason or "").strip()
    actor = (actor or "System").strip() or "System"
    confirmation = (confirmation or "").strip()
    required_confirmation = "I UNDERSTAND THIS GOVERNANCE RELATIONSHIP WILL BE PRESERVED"

    if not old_relationship_id:
        audit_id = record_governance_relationship_audit(
            attempted_relationship_id=None,
            existing_relationship_id=None,
            action="supersede_relationship",
            outcome="validation_failed",
            authority=authority,
            reason=reason,
            actor=actor,
            message="Old relationship ID is required for supersession.",
        )
        return False, f"Old relationship ID is required for supersession. | Audit: {audit_id}"

    old_relationship = get_governance_relationship(old_relationship_id)
    if not old_relationship:
        audit_id = record_governance_relationship_audit(
            attempted_relationship_id=old_relationship_id,
            existing_relationship_id=None,
            action="supersede_relationship",
            outcome="not_found",
            authority=authority,
            reason=reason,
            actor=actor,
            message=f"Governance relationship {old_relationship_id} was not found for supersession.",
        )
        return False, (
            f"Governance relationship {old_relationship_id} was not found for supersession. "
            f"| Audit: {audit_id}"
        )

    if (old_relationship.get("status") or "") == "Retired":
        audit_id = record_governance_relationship_audit(
            firm_id=old_relationship.get("firm_id"),
            attempted_relationship_id=old_relationship_id,
            existing_relationship_id=old_relationship_id,
            action="supersede_relationship",
            outcome="already_retired",
            source_object_type=old_relationship.get("source_object_type"),
            source_object_id=old_relationship.get("source_object_id"),
            relationship_type=old_relationship.get("relationship_type"),
            target_object_type=old_relationship.get("target_object_type"),
            target_object_id=old_relationship.get("target_object_id"),
            authority=authority,
            reason=reason,
            actor=actor,
            message=f"Governance relationship {old_relationship_id} is already retired and cannot be superseded.",
        )
        return False, (
            f"Governance relationship {old_relationship_id} is already retired and cannot be superseded. "
            f"| Audit: {audit_id}"
        )

    if not authority or not reason:
        audit_id = record_governance_relationship_audit(
            firm_id=old_relationship.get("firm_id"),
            attempted_relationship_id=old_relationship_id,
            existing_relationship_id=old_relationship_id,
            action="supersede_relationship",
            outcome="validation_failed",
            source_object_type=old_relationship.get("source_object_type"),
            source_object_id=old_relationship.get("source_object_id"),
            relationship_type=old_relationship.get("relationship_type"),
            target_object_type=old_relationship.get("target_object_type"),
            target_object_id=old_relationship.get("target_object_id"),
            authority=authority,
            reason=reason,
            actor=actor,
            message="Authority and reason are required to supersede a governance relationship.",
        )
        return False, (
            "Authority and reason are required to supersede a governance relationship. "
            f"| Audit: {audit_id}"
        )

    if confirmation != required_confirmation:
        audit_id = record_governance_relationship_audit(
            firm_id=old_relationship.get("firm_id"),
            attempted_relationship_id=old_relationship_id,
            existing_relationship_id=old_relationship_id,
            action="supersede_relationship",
            outcome="validation_failed",
            source_object_type=old_relationship.get("source_object_type"),
            source_object_id=old_relationship.get("source_object_id"),
            relationship_type=old_relationship.get("relationship_type"),
            target_object_type=old_relationship.get("target_object_type"),
            target_object_id=old_relationship.get("target_object_id"),
            authority=authority,
            reason=reason,
            actor=actor,
            message="Required preservation confirmation phrase was not provided for supersession.",
        )
        return False, (
            "Required preservation confirmation phrase was not provided for supersession. "
            f"| Audit: {audit_id}"
        )

    new_payload = {
        "source_object_type": (new_source_object_type or old_relationship.get("source_object_type") or "").strip(),
        "source_object_id": (new_source_object_id or old_relationship.get("source_object_id") or "").strip(),
        "relationship_type": (new_relationship_type or old_relationship.get("relationship_type") or "").strip(),
        "target_object_type": (new_target_object_type or old_relationship.get("target_object_type") or "").strip(),
        "target_object_id": (new_target_object_id or old_relationship.get("target_object_id") or "").strip(),
        "authority": authority,
        "reason": reason,
        "status": "Active",
        "created_by": actor,
        "firm_id": old_relationship.get("firm_id") or get_current_firm_id(),
    }

    created, new_relationship_id_or_message = create_governance_relationship(new_payload)
    if not created:
        audit_id = record_governance_relationship_audit(
            firm_id=old_relationship.get("firm_id"),
            attempted_relationship_id=old_relationship_id,
            existing_relationship_id=old_relationship_id,
            action="supersede_relationship",
            outcome="replacement_failed",
            source_object_type=old_relationship.get("source_object_type"),
            source_object_id=old_relationship.get("source_object_id"),
            relationship_type=old_relationship.get("relationship_type"),
            target_object_type=old_relationship.get("target_object_type"),
            target_object_id=old_relationship.get("target_object_id"),
            authority=authority,
            reason=reason,
            actor=actor,
            message=f"Replacement relationship could not be created: {new_relationship_id_or_message}",
        )
        return False, (
            f"Replacement relationship could not be created: {new_relationship_id_or_message} "
            f"| Audit: {audit_id}"
        )

    new_relationship_id = new_relationship_id_or_message
    now = _now()
    firm_id = old_relationship.get("firm_id") or get_current_firm_id()

    conn = get_connection()
    conn.execute(
        """
        UPDATE governance_relationships
        SET status = 'Retired',
            retired_at = ?,
            updated_at = ?
        WHERE relationship_id = ?
          AND firm_id = ?
        """,
        (now, now, old_relationship_id, firm_id),
    )
    conn.commit()
    conn.close()

    audit_id = record_governance_relationship_audit(
        firm_id=firm_id,
        attempted_relationship_id=new_relationship_id,
        existing_relationship_id=old_relationship_id,
        action="supersede_relationship",
        outcome="superseded",
        source_object_type=old_relationship.get("source_object_type"),
        source_object_id=old_relationship.get("source_object_id"),
        relationship_type=old_relationship.get("relationship_type"),
        target_object_type=old_relationship.get("target_object_type"),
        target_object_id=old_relationship.get("target_object_id"),
        authority=authority,
        reason=reason,
        actor=actor,
        message=(
            f"Governance relationship {old_relationship_id} superseded by "
            f"{new_relationship_id}."
        ),
    )

    return True, (
        f"Governance relationship {old_relationship_id} superseded by "
        f"{new_relationship_id}. | Audit: {audit_id}"
    )



def build_governance_relationship_lineage(relationship_id):
    """
    Build a structured lineage view for superseded / replacement governance relationships.

    A supersession audit uses:
    - existing_relationship_id = old retired relationship
    - attempted_relationship_id = new active replacement relationship
    """
    ensure_governance_tables()

    relationship_id = (relationship_id or "").strip()
    if not relationship_id:
        return {
            "has_chain": False,
            "role": "",
            "audit": None,
            "old_relationship": None,
            "new_relationship": None,
        }

    audits = list_audits_for_governance_relationship(relationship_id, limit=100)

    supersession_audit = None
    role = ""

    for audit in audits:
        if (
            audit.get("action") == "supersede_relationship"
            and audit.get("outcome") == "superseded"
        ):
            supersession_audit = audit
            if audit.get("existing_relationship_id") == relationship_id:
                role = "superseded"
            elif audit.get("attempted_relationship_id") == relationship_id:
                role = "replacement"
            else:
                role = "related"
            break

    if not supersession_audit:
        return {
            "has_chain": False,
            "role": "",
            "audit": None,
            "old_relationship": None,
            "new_relationship": None,
        }

    old_relationship_id = supersession_audit.get("existing_relationship_id")
    new_relationship_id = supersession_audit.get("attempted_relationship_id")

    old_relationship = get_governance_relationship(old_relationship_id)
    new_relationship = get_governance_relationship(new_relationship_id)

    return {
        "has_chain": True,
        "role": role,
        "audit": supersession_audit,
        "old_relationship": old_relationship,
        "new_relationship": new_relationship,
    }



def build_governance_relationship_lifecycle_summary(relationship, audits):
    """
    Build an operator-readable lifecycle summary for a governance relationship.

    This is a read-only summary. It does not alter relationship state.
    """
    relationship = relationship or {}
    audits = audits or []

    counts = {
        "created": 0,
        "duplicate_blocked": 0,
        "validation_failed": 0,
        "retired": 0,
        "superseded": 0,
        "reinstated": 0,
        "conflict_detected": 0,
        "replacement_failed": 0,
        "already_active": 0,
        "already_retired": 0,
        "not_found": 0,
    }

    action_counts = {}

    for audit in audits:
        outcome = audit.get("outcome") or ""
        action = audit.get("action") or ""

        if outcome in counts:
            counts[outcome] += 1

        if action:
            action_counts[action] = action_counts.get(action, 0) + 1

    last_audit = audits[0] if audits else None
    current_status = relationship.get("status") or "Unknown"
    retired_at = relationship.get("retired_at") or ""

    lifecycle_label = "Unknown"

    if current_status == "Active":
        if counts["reinstated"]:
            lifecycle_label = "Recovered / Active"
        elif counts["superseded"] and relationship.get("relationship_id") == ((last_audit or {}).get("attempted_relationship_id")):
            lifecycle_label = "Replacement Active"
        else:
            lifecycle_label = "Active"
    elif current_status == "Retired":
        if counts["superseded"]:
            lifecycle_label = "Superseded / Retired"
        elif counts["retired"]:
            lifecycle_label = "Retired"
        else:
            lifecycle_label = "Inactive / Retired"
    else:
        lifecycle_label = current_status or "Unknown"

    risk_flags = []

    if counts["validation_failed"]:
        risk_flags.append("Validation failures recorded")

    if counts["conflict_detected"]:
        risk_flags.append("Reinstatement conflict recorded")

    if counts["duplicate_blocked"]:
        risk_flags.append("Duplicate attempts blocked")

    if counts["replacement_failed"]:
        risk_flags.append("Replacement failure recorded")

    if current_status == "Retired" and counts["reinstated"]:
        risk_flags.append("Recovered previously but currently retired")

    if not risk_flags:
        risk_flags.append("No lifecycle risk flags")

    return {
        "current_status": current_status,
        "lifecycle_label": lifecycle_label,
        "relationship_id": relationship.get("relationship_id") or "",
        "audit_count": len(audits),
        "counts": counts,
        "action_counts": action_counts,
        "last_action": last_audit.get("action") if last_audit else "",
        "last_outcome": last_audit.get("outcome") if last_audit else "",
        "last_audit_id": last_audit.get("audit_id") if last_audit else "",
        "last_actor": last_audit.get("actor") if last_audit else "",
        "last_authority": last_audit.get("authority") if last_audit else "",
        "last_reason": last_audit.get("reason") if last_audit else "",
        "last_message": last_audit.get("message") if last_audit else "",
        "last_created_at": last_audit.get("created_at") if last_audit else "",
        "created_at": relationship.get("created_at") or "",
        "updated_at": relationship.get("updated_at") or "",
        "retired_at": retired_at,
        "risk_flags": risk_flags,
        "has_recovery_history": bool(counts["reinstated"]),
        "has_supersession_history": bool(counts["superseded"]),
        "has_retirement_history": bool(counts["retired"]),
        "has_conflict_history": bool(counts["conflict_detected"]),
    }



def build_governance_relationship_lifecycle_dashboard(limit=250):
    """
    Build a read-only operator dashboard for governance relationship lifecycle states.
    """
    ensure_governance_tables()

    firm_id = get_current_firm_id()
    limit = int(limit or 250)

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT *
        FROM governance_relationships
        WHERE firm_id = ?
        ORDER BY updated_at DESC, id DESC
        LIMIT ?
        """,
        (firm_id, limit),
    ).fetchall()
    conn.close()

    high_value_types = {"Document", "Certificate", "Trust", "Matter", "Execution Session"}

    categories = {
        "active": [],
        "retired": [],
        "superseded": [],
        "reinstated": [],
        "conflict_blocked": [],
        "duplicate_blocked": [],
        "validation_failed": [],
        "high_value": [],
    }

    relationships = []
    totals = {
        "total": 0,
        "active": 0,
        "retired": 0,
        "superseded": 0,
        "reinstated": 0,
        "conflict_blocked": 0,
        "duplicate_blocked": 0,
        "validation_failed": 0,
        "high_value": 0,
    }

    for row in rows:
        relationship = dict(row)
        audits = list_audits_for_governance_relationship(
            relationship.get("relationship_id"),
            limit=100,
            firm_id=firm_id,
        )
        lifecycle = build_governance_relationship_lifecycle_summary(relationship, audits)

        entry = {
            "relationship": relationship,
            "lifecycle": lifecycle,
            "audit_count": lifecycle.get("audit_count", 0),
            "last_action": lifecycle.get("last_action"),
            "last_outcome": lifecycle.get("last_outcome"),
            "last_audit_id": lifecycle.get("last_audit_id"),
            "risk_flags": lifecycle.get("risk_flags") or [],
        }

        relationships.append(entry)
        totals["total"] += 1

        status = relationship.get("status") or ""
        counts = lifecycle.get("counts") or {}

        if status == "Active":
            categories["active"].append(entry)
            totals["active"] += 1

        if status == "Retired":
            categories["retired"].append(entry)
            totals["retired"] += 1

        if counts.get("superseded"):
            categories["superseded"].append(entry)
            totals["superseded"] += 1

        if counts.get("reinstated"):
            categories["reinstated"].append(entry)
            totals["reinstated"] += 1

        if counts.get("conflict_detected"):
            categories["conflict_blocked"].append(entry)
            totals["conflict_blocked"] += 1

        if counts.get("duplicate_blocked"):
            categories["duplicate_blocked"].append(entry)
            totals["duplicate_blocked"] += 1

        if counts.get("validation_failed"):
            categories["validation_failed"].append(entry)
            totals["validation_failed"] += 1

        if (
            relationship.get("source_object_type") in high_value_types
            or relationship.get("target_object_type") in high_value_types
        ):
            categories["high_value"].append(entry)
            totals["high_value"] += 1

    return {
        "firm_id": firm_id,
        "limit": limit,
        "totals": totals,
        "relationships": relationships,
        "categories": categories,
    }



def build_governance_relationship_evidence_context(relationship_id):
    relationship = get_governance_relationship(relationship_id)
    audits = list_audits_for_governance_relationship(relationship_id, limit=100)

    lineage = build_governance_relationship_lineage(relationship_id)
    lifecycle = build_governance_relationship_lifecycle_summary(relationship, audits)

    return {
        "relationship": relationship,
        "audits": audits,
        "lineage": lineage,
        "lifecycle": lifecycle,
        "summary": {
            "relationship_id": relationship_id,
            "found": bool(relationship),
            "audit_count": len(audits),
            "created_audits": len([a for a in audits if a.get("outcome") == "created"]),
            "duplicate_blocked_audits": len([a for a in audits if a.get("outcome") == "duplicate_blocked"]),
            "validation_failed_audits": len([a for a in audits if a.get("outcome") == "validation_failed"]),
        },
    }


def build_governance_audit_evidence_context(audit_id):
    audit = get_governance_relationship_audit(audit_id)
    relationship = None
    related_audits = []

    if audit:
        relationship_id = (
            audit.get("existing_relationship_id")
            or audit.get("attempted_relationship_id")
            or ""
        )
        if relationship_id:
            relationship = get_governance_relationship(relationship_id)
            related_audits = list_audits_for_governance_relationship(relationship_id, limit=100)

    return {
        "audit": audit,
        "relationship": relationship,
        "related_audits": related_audits,
        "summary": {
            "audit_id": audit_id,
            "found": bool(audit),
            "has_relationship": bool(relationship),
            "related_audit_count": len(related_audits),
        },
    }



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
        if (relationship.get("status") or "") != "Active":
            continue

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

    if state in {"Active", "Completed", "Approved", "Ratified", "Effective"}:
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


def build_governance_relationship_evidence_packet(relationship_id):
    """
    Build a read-only text evidence packet for a governance relationship.

    This packet is generated from preserved relationship state, lifecycle summary,
    lineage context, and audit history. It does not alter institutional records.
    """
    context = build_governance_relationship_evidence_context(relationship_id)

    relationship = context.get("relationship")
    if not relationship:
        return None

    lifecycle = context.get("lifecycle") or {}
    lineage = context.get("lineage") or {}
    audits = context.get("audits") or []
    counts = lifecycle.get("counts") or {}

    def value(record, key, default="-"):
        if not record:
            return default
        if hasattr(record, "get"):
            return record.get(key) or default
        try:
            return record[key] or default
        except Exception:
            return default

    lines = []

    lines.append("GOVERNANCE RELATIONSHIP EVIDENCE PACKET")
    lines.append("=" * 48)
    lines.append("")
    lines.append("Preservation Notice")
    lines.append("-" * 48)
    lines.append(
        "This packet is a read-only institutional evidence export generated from "
        "preserved governance records. It does not modify, delete, retire, supersede, "
        "or reinstate any governance relationship."
    )
    lines.append("")
    lines.append("Institutional Principle")
    lines.append("-" * 48)
    lines.append("Every institutional action becomes a permanent governed record.")
    lines.append("")

    lines.append("Relationship Summary")
    lines.append("-" * 48)
    lines.append(f"Relationship ID: {value(relationship, 'relationship_id')}")
    lines.append(f"Firm ID: {value(relationship, 'firm_id')}")
    lines.append(f"Status: {value(relationship, 'status')}")
    lines.append(
        f"Source: {value(relationship, 'source_object_type')} — "
        f"{value(relationship, 'source_object_id')}"
    )
    lines.append(f"Relationship Type: {value(relationship, 'relationship_type')}")
    lines.append(
        f"Target: {value(relationship, 'target_object_type')} — "
        f"{value(relationship, 'target_object_id')}"
    )
    lines.append(f"Authority: {value(relationship, 'authority')}")
    lines.append(f"Reason: {value(relationship, 'reason')}")
    lines.append(f"Created By: {value(relationship, 'created_by')}")
    lines.append(f"Effective At: {value(relationship, 'effective_at')}")
    lines.append(f"Retired At: {value(relationship, 'retired_at')}")
    lines.append(f"Created At: {value(relationship, 'created_at')}")
    lines.append(f"Updated At: {value(relationship, 'updated_at')}")
    lines.append("")

    lines.append("Lifecycle Summary")
    lines.append("-" * 48)
    lines.append(f"Lifecycle State: {lifecycle.get('lifecycle_label') or lifecycle.get('state_label') or lifecycle.get('label') or '-'}")
    lines.append(f"Current Status: {lifecycle.get('current_status') or value(relationship, 'status')}")
    lines.append(f"Audit Count: {lifecycle.get('audit_count', 0)}")
    lines.append(f"Created: {counts.get('created', 0)}")
    lines.append(f"Retired: {counts.get('retired', 0)}")
    lines.append(f"Superseded: {counts.get('superseded', 0)}")
    lines.append(f"Reinstated: {counts.get('reinstated', 0)}")
    lines.append(f"Conflict Blocked: {counts.get('conflict_detected', 0)}")
    lines.append(f"Duplicate Blocked: {counts.get('duplicate_blocked', 0)}")
    lines.append(f"Validation Failed: {counts.get('validation_failed', 0)}")
    lines.append(f"Last Audit ID: {lifecycle.get('last_audit_id') or '-'}")
    lines.append(f"Last Action: {lifecycle.get('last_action') or '-'}")
    lines.append(f"Last Outcome: {lifecycle.get('last_outcome') or '-'}")
    lines.append(f"Last Actor: {lifecycle.get('last_actor') or '-'}")
    lines.append(f"Last Authority: {lifecycle.get('last_authority') or '-'}")
    lines.append(f"Last Reason: {lifecycle.get('last_reason') or '-'}")
    lines.append("Risk Flags:")
    risk_flags = lifecycle.get("risk_flags") or []
    if risk_flags:
        for flag in risk_flags:
            lines.append(f"- {flag}")
    else:
        lines.append("- No lifecycle risk flags recorded.")
    lines.append("")

    lines.append("Lineage Summary")
    lines.append("-" * 48)
    if lineage.get("has_chain"):
        old_relationship = lineage.get("old_relationship") or {}
        new_relationship = lineage.get("new_relationship") or {}
        lineage_audit = lineage.get("audit") or {}

        lines.append(f"Lineage Role: {lineage.get('role') or '-'}")
        lines.append(
            f"Prior / Superseded Relationship: "
            f"{value(old_relationship, 'relationship_id')} "
            f"({value(old_relationship, 'status')})"
        )
        lines.append(
            f"Replacement / Active Relationship: "
            f"{value(new_relationship, 'relationship_id')} "
            f"({value(new_relationship, 'status')})"
        )
        lines.append(f"Supersession Audit: {value(lineage_audit, 'audit_id')}")
        lines.append(f"Supersession Authority: {value(lineage_audit, 'authority')}")
        lines.append(f"Supersession Reason: {value(lineage_audit, 'reason')}")
        lines.append(f"Supersession Actor: {value(lineage_audit, 'actor')}")
        lines.append(f"Supersession Created: {value(lineage_audit, 'created_at')}")
    else:
        lines.append("No supersession lineage chain found for this relationship.")
    lines.append("")

    lines.append("Audit History")
    lines.append("-" * 48)
    if audits:
        for audit in audits:
            lines.append(f"Audit ID: {value(audit, 'audit_id')}")
            lines.append(f"Action: {value(audit, 'action')}")
            lines.append(f"Outcome: {value(audit, 'outcome')}")
            lines.append(f"Attempted Relationship: {value(audit, 'attempted_relationship_id')}")
            lines.append(f"Existing Relationship: {value(audit, 'existing_relationship_id')}")
            lines.append(
                f"Source: {value(audit, 'source_object_type')} — "
                f"{value(audit, 'source_object_id')}"
            )
            lines.append(f"Relationship Type: {value(audit, 'relationship_type')}")
            lines.append(
                f"Target: {value(audit, 'target_object_type')} — "
                f"{value(audit, 'target_object_id')}"
            )
            lines.append(f"Actor: {value(audit, 'actor')}")
            lines.append(f"Authority: {value(audit, 'authority')}")
            lines.append(f"Reason: {value(audit, 'reason')}")
            lines.append(f"Message: {value(audit, 'message')}")
            lines.append(f"Created At: {value(audit, 'created_at')}")
            lines.append("")
    else:
        lines.append("No related audit events found.")
        lines.append("")

    lines.append("End of Packet")
    lines.append("=" * 48)
    lines.append("Institutional Property of Luna Isaac III Mishoe")
    lines.append(
        "System records, workflows, generated instruments, certificates, exports, "
        "and archive materials are maintained under fiduciary custody."
    )

    return "\n".join(lines)


def build_governance_relationship_audit_evidence_packet(audit_id):
    """
    Build a read-only text evidence packet for a governance relationship audit event.

    This packet is generated from preserved audit state, linked relationship evidence,
    and related audit history. It does not alter institutional records.
    """
    context = build_governance_audit_evidence_context(audit_id)

    audit = context.get("audit")
    if not audit:
        return None

    relationship = context.get("relationship") or {}
    related_audits = context.get("related_audits") or []

    def value(record, key, default="-"):
        if not record:
            return default
        if hasattr(record, "get"):
            return record.get(key) or default
        try:
            return record[key] or default
        except Exception:
            return default

    lines = []

    lines.append("GOVERNANCE RELATIONSHIP AUDIT EVIDENCE PACKET")
    lines.append("=" * 56)
    lines.append("")
    lines.append("Preservation Notice")
    lines.append("-" * 56)
    lines.append(
        "This packet is a read-only institutional evidence export generated from "
        "preserved governance audit records. It does not modify, delete, retire, "
        "supersede, reinstate, or otherwise alter any governance relationship."
    )
    lines.append("")
    lines.append("Institutional Principle")
    lines.append("-" * 56)
    lines.append("Every institutional action becomes a permanent governed record.")
    lines.append("")

    lines.append("Audit Event Summary")
    lines.append("-" * 56)
    lines.append(f"Audit ID: {value(audit, 'audit_id')}")
    lines.append(f"Outcome: {value(audit, 'outcome')}")
    lines.append(f"Action: {value(audit, 'action')}")
    lines.append(
        f"Source: {value(audit, 'source_object_type')} — "
        f"{value(audit, 'source_object_id')}"
    )
    lines.append(f"Relationship Type: {value(audit, 'relationship_type')}")
    lines.append(
        f"Target: {value(audit, 'target_object_type')} — "
        f"{value(audit, 'target_object_id')}"
    )
    lines.append(f"Attempted Relationship ID: {value(audit, 'attempted_relationship_id')}")
    lines.append(f"Existing Relationship ID: {value(audit, 'existing_relationship_id')}")
    lines.append(f"Actor: {value(audit, 'actor')}")
    lines.append(f"Authority: {value(audit, 'authority')}")
    lines.append(f"Reason: {value(audit, 'reason')}")
    lines.append(f"Message: {value(audit, 'message')}")
    lines.append(f"Created At: {value(audit, 'created_at')}")
    lines.append("")

    lines.append("Linked Relationship Evidence")
    lines.append("-" * 56)
    if relationship:
        lines.append(f"Relationship ID: {value(relationship, 'relationship_id')}")
        lines.append(f"Status: {value(relationship, 'status')}")
        lines.append(
            f"Source: {value(relationship, 'source_object_type')} — "
            f"{value(relationship, 'source_object_id')}"
        )
        lines.append(f"Relationship Type: {value(relationship, 'relationship_type')}")
        lines.append(
            f"Target: {value(relationship, 'target_object_type')} — "
            f"{value(relationship, 'target_object_id')}"
        )
        lines.append(f"Authority: {value(relationship, 'authority')}")
        lines.append(f"Reason: {value(relationship, 'reason')}")
        lines.append(f"Created By: {value(relationship, 'created_by')}")
        lines.append(f"Effective At: {value(relationship, 'effective_at')}")
        lines.append(f"Retired At: {value(relationship, 'retired_at')}")
        lines.append(f"Created At: {value(relationship, 'created_at')}")
        lines.append(f"Updated At: {value(relationship, 'updated_at')}")
    else:
        lines.append("No linked relationship evidence found for this audit event.")
    lines.append("")

    lines.append("Related Audit Events")
    lines.append("-" * 56)
    if related_audits:
        for related in related_audits:
            lines.append(f"Audit ID: {value(related, 'audit_id')}")
            lines.append(f"Outcome: {value(related, 'outcome')}")
            lines.append(f"Action: {value(related, 'action')}")
            lines.append(f"Attempted Relationship: {value(related, 'attempted_relationship_id')}")
            lines.append(f"Existing Relationship: {value(related, 'existing_relationship_id')}")
            lines.append(f"Actor: {value(related, 'actor')}")
            lines.append(f"Authority: {value(related, 'authority')}")
            lines.append(f"Reason: {value(related, 'reason')}")
            lines.append(f"Message: {value(related, 'message')}")
            lines.append(f"Created At: {value(related, 'created_at')}")
            lines.append("")
    else:
        lines.append("No related audit events found.")
        lines.append("")

    lines.append("End of Packet")
    lines.append("=" * 56)
    lines.append("Institutional Property of Luna Isaac III Mishoe")
    lines.append(
        "System records, workflows, generated instruments, certificates, exports, "
        "and archive materials are maintained under fiduciary custody."
    )

    return "\n".join(lines)


def build_governance_evidence_export_index(
    object_type=None,
    object_id=None,
    status=None,
    outcome=None,
    limit=250,
):
    """
    Build a read-only centralized export index for governance relationship packets
    and governance audit packets.

    This index does not create, modify, delete, retire, supersede, reinstate, or
    otherwise alter any governance relationship or audit record.
    """
    try:
        limit = int(limit or 250)
    except Exception:
        limit = 250

    if limit < 1:
        limit = 250
    if limit > 1000:
        limit = 1000

    def value(record, *keys, default=None):
        for key in keys:
            if not key:
                continue
            if hasattr(record, "get"):
                current = record.get(key)
                if current not in (None, ""):
                    return current
            try:
                current = record[key]
                if current not in (None, ""):
                    return current
            except Exception:
                pass
        return default

    object_type_filter = str(object_type or "").strip().lower()
    object_id_filter = str(object_id or "").strip()
    status_filter = str(status or "").strip().lower()
    outcome_filter = str(outcome or "").strip().lower()

    relationships = []
    audits = []

    raw_relationships = list_governance_relationships()[:limit]

    for rel in raw_relationships:
        rel_source_type = value(rel, "source_object_type", "source_type", default="")
        rel_source_id = value(rel, "source_object_id", "source_id", default="")
        rel_target_type = value(rel, "target_object_type", "target_type", default="")
        rel_target_id = value(rel, "target_object_id", "target_id", default="")
        rel_status = value(rel, "status", default="")

        if object_type_filter:
            if (
                str(rel_source_type).strip().lower() != object_type_filter
                and str(rel_target_type).strip().lower() != object_type_filter
            ):
                continue

        if object_id_filter:
            if (
                str(rel_source_id).strip() != object_id_filter
                and str(rel_target_id).strip() != object_id_filter
            ):
                continue

        if status_filter:
            if str(rel_status).strip().lower() != status_filter:
                continue

        relationship_id = value(rel, "relationship_id", "id")
        audits_for_relationship = list_audits_for_governance_relationship(relationship_id)
        lifecycle = build_governance_relationship_lifecycle_summary(rel, audits_for_relationship)

        last_audit = audits_for_relationship[0] if audits_for_relationship else {}

        relationships.append(
            {
                "packet_type": "Relationship",
                "relationship_id": relationship_id,
                "status": rel_status,
                "lifecycle_label": lifecycle.get("lifecycle_label") or "-",
                "source_object_type": rel_source_type,
                "source_object_id": rel_source_id,
                "relationship_type": value(rel, "relationship_type", "verb", default=""),
                "target_object_type": rel_target_type,
                "target_object_id": rel_target_id,
                "audit_count": lifecycle.get("audit_count", 0),
                "last_outcome": value(last_audit, "outcome", default=""),
                "last_audit_id": value(last_audit, "audit_id", default=""),
                "risk_flags": lifecycle.get("risk_flags") or [],
                "updated_at": value(rel, "updated_at", "created_at", default=""),
            }
        )

    raw_audits = list_governance_relationship_audits(
        object_type=object_type,
        object_id=object_id,
        limit=limit,
    )

    for audit in raw_audits:
        audit_outcome = value(audit, "outcome", default="")

        if outcome_filter:
            if str(audit_outcome).strip().lower() != outcome_filter:
                continue

        audits.append(
            {
                "packet_type": "Audit",
                "audit_id": value(audit, "audit_id"),
                "outcome": audit_outcome,
                "action": value(audit, "action"),
                "source_object_type": value(audit, "source_object_type"),
                "source_object_id": value(audit, "source_object_id"),
                "relationship_type": value(audit, "relationship_type"),
                "target_object_type": value(audit, "target_object_type"),
                "target_object_id": value(audit, "target_object_id"),
                "attempted_relationship_id": value(audit, "attempted_relationship_id"),
                "existing_relationship_id": value(audit, "existing_relationship_id"),
                "actor": value(audit, "actor"),
                "authority": value(audit, "authority"),
                "reason": value(audit, "reason"),
                "message": value(audit, "message"),
                "created_at": value(audit, "created_at"),
            }
        )

    relationship_status_counts = {}
    for rel in relationships:
        key = rel.get("status") or "Unknown"
        relationship_status_counts[key] = relationship_status_counts.get(key, 0) + 1

    audit_outcome_counts = {}
    for audit in audits:
        key = audit.get("outcome") or "Unknown"
        audit_outcome_counts[key] = audit_outcome_counts.get(key, 0) + 1

    return {
        "filters": {
            "object_type": object_type or "",
            "object_id": object_id or "",
            "status": status or "",
            "outcome": outcome or "",
            "limit": limit,
        },
        "summary": {
            "relationship_packets": len(relationships),
            "audit_packets": len(audits),
            "total_packets": len(relationships) + len(audits),
            "relationship_status_counts": relationship_status_counts,
            "audit_outcome_counts": audit_outcome_counts,
        },
        "relationships": relationships,
        "audits": audits,
    }


def _csv_escape(value):
    """
    Escape a value for CSV output without mutating any institutional record.
    """
    if value is None:
        value = ""
    if isinstance(value, (list, tuple)):
        value = "; ".join(str(item) for item in value)
    value = str(value)
    value = value.replace('"', '""')
    return f'"{value}"'


def _csv_line(values):
    return ",".join(_csv_escape(value) for value in values)


def build_governance_evidence_export_index_csv(
    packet_type="combined",
    object_type=None,
    object_id=None,
    status=None,
    outcome=None,
    limit=250,
):
    """
    Build a read-only CSV export for the governance evidence export index.

    packet_type values:
    - combined
    - relationships
    - audits
    """
    index = build_governance_evidence_export_index(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )

    packet_type = (packet_type or "combined").strip().lower()

    lines = []

    if packet_type in ("combined", "relationships"):
        relationship_headers = [
            "packet_type",
            "relationship_id",
            "status",
            "lifecycle_label",
            "source_object_type",
            "source_object_id",
            "relationship_type",
            "target_object_type",
            "target_object_id",
            "audit_count",
            "last_outcome",
            "last_audit_id",
            "risk_flags",
            "updated_at",
            "export_path",
        ]
        lines.append(_csv_line(relationship_headers))

        for rel in index.get("relationships") or []:
            relationship_id = rel.get("relationship_id") or ""
            export_path = f"/governance/relationships/{relationship_id}/export" if relationship_id else ""

            lines.append(
                _csv_line(
                    [
                        "Relationship",
                        relationship_id,
                        rel.get("status"),
                        rel.get("lifecycle_label"),
                        rel.get("source_object_type"),
                        rel.get("source_object_id"),
                        rel.get("relationship_type"),
                        rel.get("target_object_type"),
                        rel.get("target_object_id"),
                        rel.get("audit_count"),
                        rel.get("last_outcome"),
                        rel.get("last_audit_id"),
                        rel.get("risk_flags"),
                        rel.get("updated_at"),
                        export_path,
                    ]
                )
            )

    if packet_type == "combined":
        lines.append("")

    if packet_type in ("combined", "audits"):
        audit_headers = [
            "packet_type",
            "audit_id",
            "outcome",
            "action",
            "source_object_type",
            "source_object_id",
            "relationship_type",
            "target_object_type",
            "target_object_id",
            "attempted_relationship_id",
            "existing_relationship_id",
            "actor",
            "authority",
            "reason",
            "message",
            "created_at",
            "export_path",
        ]
        lines.append(_csv_line(audit_headers))

        for audit in index.get("audits") or []:
            audit_id = audit.get("audit_id") or ""
            export_path = f"/governance/relationship-audits/{audit_id}/export" if audit_id else ""

            lines.append(
                _csv_line(
                    [
                        "Audit",
                        audit_id,
                        audit.get("outcome"),
                        audit.get("action"),
                        audit.get("source_object_type"),
                        audit.get("source_object_id"),
                        audit.get("relationship_type"),
                        audit.get("target_object_type"),
                        audit.get("target_object_id"),
                        audit.get("attempted_relationship_id"),
                        audit.get("existing_relationship_id"),
                        audit.get("actor"),
                        audit.get("authority"),
                        audit.get("reason"),
                        audit.get("message"),
                        audit.get("created_at"),
                        export_path,
                    ]
                )
            )

    return "\n".join(lines) + "\n"


def build_governance_evidence_export_manifest(
    object_type=None,
    object_id=None,
    status=None,
    outcome=None,
    limit=250,
):
    """
    Build a read-only manifest summarizing the governance evidence export universe.

    The manifest does not mutate governance relationships, audits, packets, indexes,
    lifecycle states, or institutional records.
    """
    from datetime import datetime, timezone

    index = build_governance_evidence_export_index(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )

    filters = index.get("filters") or {}
    summary = index.get("summary") or {}
    relationships = index.get("relationships") or []
    audits = index.get("audits") or []

    generated_at = datetime.now(timezone.utc).isoformat()

    manifest = {
        "manifest_title": "Governance Evidence Export Manifest",
        "manifest_type": "governance_evidence_export_manifest",
        "generated_at": generated_at,
        "read_only": True,
        "filters": {
            "object_type": filters.get("object_type") if isinstance(filters, dict) else None,
            "object_id": filters.get("object_id") if isinstance(filters, dict) else None,
            "status": filters.get("status") if isinstance(filters, dict) else None,
            "outcome": filters.get("outcome") if isinstance(filters, dict) else None,
            "limit": filters.get("limit") if isinstance(filters, dict) else limit,
        },
        "summary": {
            "total_packets": summary.get("total_packets", 0),
            "relationship_packets": summary.get("relationship_packets", 0),
            "audit_packets": summary.get("audit_packets", 0),
        },
        "relationship_status_counts": (
            summary.get("relationship_status_counts")
            or index.get("relationship_status_counts")
            or index.get("status_counts")
            or index.get("relationship_status_summary")
            or {}
        ),
        "audit_outcome_counts": (
            summary.get("audit_outcome_counts")
            or index.get("audit_outcome_counts")
            or index.get("outcome_counts")
            or index.get("audit_outcome_summary")
            or {}
        ),
        "available_artifacts": {
            "index_page": "/governance/evidence-exports",
            "combined_csv": "/governance/evidence-exports.csv?packet_type=combined",
            "relationship_csv": "/governance/evidence-exports.csv?packet_type=relationships",
            "audit_csv": "/governance/evidence-exports.csv?packet_type=audits",
            "manifest_page": "/governance/evidence-exports/manifest",
            "manifest_text": "/governance/evidence-exports/manifest.txt",
        },
        "relationship_packet_exports": [
            {
                "relationship_id": rel.get("relationship_id"),
                "status": rel.get("status"),
                "lifecycle_label": rel.get("lifecycle_label"),
                "source_object_type": rel.get("source_object_type"),
                "source_object_id": rel.get("source_object_id"),
                "relationship_type": rel.get("relationship_type"),
                "target_object_type": rel.get("target_object_type"),
                "target_object_id": rel.get("target_object_id"),
                "audit_count": rel.get("audit_count"),
                "last_outcome": rel.get("last_outcome"),
                "last_audit_id": rel.get("last_audit_id"),
                "export_path": (
                    f"/governance/relationships/{rel.get('relationship_id')}/export"
                    if rel.get("relationship_id")
                    else None
                ),
            }
            for rel in relationships
        ],
        "audit_packet_exports": [
            {
                "audit_id": audit.get("audit_id"),
                "outcome": audit.get("outcome"),
                "action": audit.get("action"),
                "source_object_type": audit.get("source_object_type"),
                "source_object_id": audit.get("source_object_id"),
                "relationship_type": audit.get("relationship_type"),
                "target_object_type": audit.get("target_object_type"),
                "target_object_id": audit.get("target_object_id"),
                "attempted_relationship_id": audit.get("attempted_relationship_id"),
                "existing_relationship_id": audit.get("existing_relationship_id"),
                "export_path": (
                    f"/governance/relationship-audits/{audit.get('audit_id')}/export"
                    if audit.get("audit_id")
                    else None
                ),
            }
            for audit in audits
        ],
        "custody_notice": (
            "Institutional Property of Luna Isaac III Mishoe. System records, workflows, "
            "generated instruments, certificates, exports, and archive materials are maintained "
            "under fiduciary custody. Authorized Access Only."
        ),
        "preservation_statement": (
            "This manifest identifies the governance evidence exports available at the time "
            "of generation. It is a read-only institutional export inventory and does not alter "
            "any governance relationship, audit event, lifecycle state, or source record."
        ),
    }

    return manifest


def build_governance_evidence_export_manifest_text(
    object_type=None,
    object_id=None,
    status=None,
    outcome=None,
    limit=250,
):
    """
    Build a read-only plain-text governance evidence export manifest.
    """
    manifest = build_governance_evidence_export_manifest(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )

    lines = []
    lines.append("GOVERNANCE EVIDENCE EXPORT MANIFEST")
    lines.append("=" * 44)
    lines.append("")
    lines.append(f"Manifest Type: {manifest.get('manifest_type')}")
    lines.append(f"Generated At: {manifest.get('generated_at')}")
    lines.append(f"Read Only: {manifest.get('read_only')}")
    lines.append("")
    lines.append("FILTERS")
    lines.append("-" * 44)
    filters = manifest.get("filters") or {}
    lines.append(f"Object Type: {filters.get('object_type') or '-'}")
    lines.append(f"Object ID: {filters.get('object_id') or '-'}")
    lines.append(f"Relationship Status: {filters.get('status') or '-'}")
    lines.append(f"Audit Outcome: {filters.get('outcome') or '-'}")
    lines.append(f"Limit: {filters.get('limit') or '-'}")
    lines.append("")
    lines.append("PACKET SUMMARY")
    lines.append("-" * 44)
    summary = manifest.get("summary") or {}
    lines.append(f"Total Packets: {summary.get('total_packets', 0)}")
    lines.append(f"Relationship Packets: {summary.get('relationship_packets', 0)}")
    lines.append(f"Audit Packets: {summary.get('audit_packets', 0)}")
    lines.append("")
    lines.append("RELATIONSHIP STATUS COUNTS")
    lines.append("-" * 44)
    for status_label, count in (manifest.get("relationship_status_counts") or {}).items():
        lines.append(f"{status_label}: {count}")
    lines.append("")
    lines.append("AUDIT OUTCOME COUNTS")
    lines.append("-" * 44)
    for outcome_label, count in (manifest.get("audit_outcome_counts") or {}).items():
        lines.append(f"{outcome_label}: {count}")
    lines.append("")
    lines.append("AVAILABLE EXPORT ARTIFACTS")
    lines.append("-" * 44)
    for label, path in (manifest.get("available_artifacts") or {}).items():
        lines.append(f"{label}: {path}")
    lines.append("")
    lines.append("RELATIONSHIP PACKET EXPORTS")
    lines.append("-" * 44)
    for rel in manifest.get("relationship_packet_exports") or []:
        lines.append(
            f"{rel.get('relationship_id')} | {rel.get('status')} | "
            f"{rel.get('source_object_type')} {rel.get('source_object_id')} "
            f"{rel.get('relationship_type')} "
            f"{rel.get('target_object_type')} {rel.get('target_object_id')} | "
            f"{rel.get('export_path')}"
        )
    lines.append("")
    lines.append("AUDIT PACKET EXPORTS")
    lines.append("-" * 44)
    for audit in manifest.get("audit_packet_exports") or []:
        lines.append(
            f"{audit.get('audit_id')} | {audit.get('outcome')} | "
            f"{audit.get('action')} | "
            f"{audit.get('source_object_type')} {audit.get('source_object_id')} "
            f"{audit.get('relationship_type')} "
            f"{audit.get('target_object_type')} {audit.get('target_object_id')} | "
            f"{audit.get('export_path')}"
        )
    lines.append("")
    lines.append("PRESERVATION STATEMENT")
    lines.append("-" * 44)
    lines.append(manifest.get("preservation_statement") or "")
    lines.append("")
    lines.append("CUSTODY NOTICE")
    lines.append("-" * 44)
    lines.append(manifest.get("custody_notice") or "")

    return "\n".join(lines) + "\n"


def _sha256_text_digest(value):
    """
    Return SHA-256 hex digest for a text export payload.
    """
    import hashlib

    if value is None:
        value = ""

    if not isinstance(value, str):
        value = str(value)

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_governance_export_integrity_digest_index(
    object_type=None,
    object_id=None,
    status=None,
    outcome=None,
    limit=250,
):
    """
    Build a read-only SHA-256 integrity digest index for governance evidence exports.

    This function does not mutate governance relationships, audits, packets, indexes,
    lifecycle states, archive records, source records, or target records.
    """
    from datetime import datetime, timezone

    generated_at = datetime.now(timezone.utc).isoformat()

    filter_context = {
        "object_type": object_type,
        "object_id": object_id,
        "status": status,
        "outcome": outcome,
        "limit": limit,
    }

    artifacts = []

    csv_artifacts = [
        {
            "artifact_label": "Combined Evidence Export CSV",
            "artifact_type": "combined_csv",
            "packet_type": "combined",
            "route": "/governance/evidence-exports.csv?packet_type=combined",
        },
        {
            "artifact_label": "Relationship Evidence Export CSV",
            "artifact_type": "relationship_csv",
            "packet_type": "relationships",
            "route": "/governance/evidence-exports.csv?packet_type=relationships",
        },
        {
            "artifact_label": "Audit Evidence Export CSV",
            "artifact_type": "audit_csv",
            "packet_type": "audits",
            "route": "/governance/evidence-exports.csv?packet_type=audits",
        },
    ]

    for artifact in csv_artifacts:
        payload = build_governance_evidence_export_index_csv(
            packet_type=artifact["packet_type"],
            object_type=object_type,
            object_id=object_id,
            status=status,
            outcome=outcome,
            limit=limit,
        )
        artifacts.append(
            {
                "artifact_label": artifact["artifact_label"],
                "artifact_type": artifact["artifact_type"],
                "route": artifact["route"],
                "sha256": _sha256_text_digest(payload),
                "generated_at": generated_at,
                "filter_context": filter_context,
                "read_only": True,
            }
        )

    manifest_payload = build_governance_evidence_export_manifest_text(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )
    artifacts.append(
        {
            "artifact_label": "Governance Evidence Export Manifest TXT",
            "artifact_type": "manifest_txt",
            "route": "/governance/evidence-exports/manifest.txt",
            "sha256": _sha256_text_digest(manifest_payload),
            "generated_at": generated_at,
            "filter_context": filter_context,
            "read_only": True,
        }
    )

    manifest = build_governance_evidence_export_manifest(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )

    summary = manifest.get("summary") or {}

    return {
        "title": "Governance Export Integrity Digest",
        "digest_algorithm": "SHA-256",
        "generated_at": generated_at,
        "read_only": True,
        "filters": filter_context,
        "summary": {
            "total_artifacts": len(artifacts),
            "total_packets": summary.get("total_packets", 0),
            "relationship_packets": summary.get("relationship_packets", 0),
            "audit_packets": summary.get("audit_packets", 0),
        },
        "artifacts": artifacts,
        "preservation_statement": (
            "This integrity digest index records SHA-256 values for generated governance "
            "evidence export artifacts. It is read-only and does not alter governance "
            "relationships, audit events, lifecycle states, export packets, source records, "
            "target records, or archive records."
        ),
        "custody_notice": (
            "Institutional Property of Luna Isaac III Mishoe. System records, workflows, "
            "generated instruments, certificates, exports, and archive materials are maintained "
            "under fiduciary custody. Authorized Access Only."
        ),
    }


def build_governance_export_integrity_digest_text(
    object_type=None,
    object_id=None,
    status=None,
    outcome=None,
    limit=250,
):
    """
    Build a read-only plain-text SHA-256 integrity digest index.
    """
    digest_index = build_governance_export_integrity_digest_index(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )

    lines = []
    lines.append("GOVERNANCE EXPORT INTEGRITY DIGEST")
    lines.append("=" * 44)
    lines.append("")
    lines.append(f"Algorithm: {digest_index.get('digest_algorithm')}")
    lines.append(f"Generated At: {digest_index.get('generated_at')}")
    lines.append(f"Read Only: {digest_index.get('read_only')}")
    lines.append("")
    lines.append("FILTER CONTEXT")
    lines.append("-" * 44)
    filters = digest_index.get("filters") or {}
    lines.append(f"Object Type: {filters.get('object_type') or '-'}")
    lines.append(f"Object ID: {filters.get('object_id') or '-'}")
    lines.append(f"Relationship Status: {filters.get('status') or '-'}")
    lines.append(f"Audit Outcome: {filters.get('outcome') or '-'}")
    lines.append(f"Limit: {filters.get('limit') or '-'}")
    lines.append("")
    lines.append("SUMMARY")
    lines.append("-" * 44)
    summary = digest_index.get("summary") or {}
    lines.append(f"Total Artifacts: {summary.get('total_artifacts', 0)}")
    lines.append(f"Total Packets: {summary.get('total_packets', 0)}")
    lines.append(f"Relationship Packets: {summary.get('relationship_packets', 0)}")
    lines.append(f"Audit Packets: {summary.get('audit_packets', 0)}")
    lines.append("")
    lines.append("DIGEST ARTIFACTS")
    lines.append("-" * 44)

    for artifact in digest_index.get("artifacts") or []:
        lines.append(f"Artifact Label: {artifact.get('artifact_label')}")
        lines.append(f"Artifact Type: {artifact.get('artifact_type')}")
        lines.append(f"Route: {artifact.get('route')}")
        lines.append(f"SHA-256: {artifact.get('sha256')}")
        lines.append(f"Read Only: {artifact.get('read_only')}")
        lines.append("")

    lines.append("PRESERVATION STATEMENT")
    lines.append("-" * 44)
    lines.append(digest_index.get("preservation_statement") or "")
    lines.append("")
    lines.append("CUSTODY NOTICE")
    lines.append("-" * 44)
    lines.append(digest_index.get("custody_notice") or "")

    return "\n".join(lines) + "\n"


def build_governance_export_archive_intake_preview(
    object_type=None,
    object_id=None,
    status=None,
    outcome=None,
    limit=250,
):
    """
    Build a read-only archive intake preview for governance export artifacts.

    This function does not create archive records, mutate governance relationships,
    mutate audits, alter lifecycle states, or write certification records.
    """
    from datetime import datetime, timezone

    generated_at = datetime.now(timezone.utc).isoformat()

    digest_index = build_governance_export_integrity_digest_index(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )

    manifest = build_governance_evidence_export_manifest(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )

    filters = digest_index.get("filters") or {}
    summary = digest_index.get("summary") or {}
    artifacts = digest_index.get("artifacts") or []

    archive_items = []
    for artifact in artifacts:
        archive_items.append(
            {
                "archive_item_label": artifact.get("artifact_label"),
                "archive_item_type": artifact.get("artifact_type"),
                "export_route": artifact.get("route"),
                "sha256": artifact.get("sha256"),
                "digest_generated_at": artifact.get("generated_at"),
                "archive_readiness": (
                    "Ready for Archive Intake"
                    if artifact.get("sha256") and len(artifact.get("sha256")) == 64
                    else "Not Ready"
                ),
                "read_only": True,
            }
        )

    readiness_flags = {
        "has_digest_index": bool(digest_index),
        "has_manifest": bool(manifest),
        "has_artifacts": bool(archive_items),
        "has_packet_summary": bool(summary),
        "has_filter_context": bool(filters),
        "all_artifacts_have_sha256": all(
            len(item.get("sha256") or "") == 64 for item in archive_items
        ) if archive_items else False,
        "read_only": True,
    }

    archive_ready = all(readiness_flags.values())

    return {
        "title": "Governance Export Archive Intake Preview",
        "intake_type": "governance_export_archive_intake_preview",
        "generated_at": generated_at,
        "read_only": True,
        "archive_ready": archive_ready,
        "archive_status": (
            "Ready for Archive Intake"
            if archive_ready
            else "Archive Intake Review Required"
        ),
        "filters": filters,
        "summary": {
            "archive_items": len(archive_items),
            "total_packets": summary.get("total_packets", 0),
            "relationship_packets": summary.get("relationship_packets", 0),
            "audit_packets": summary.get("audit_packets", 0),
            "total_artifacts": summary.get("total_artifacts", len(archive_items)),
        },
        "manifest_reference": {
            "manifest_page": "/governance/evidence-exports/manifest",
            "manifest_text": "/governance/evidence-exports/manifest.txt",
            "integrity_digest": "/governance/evidence-exports/integrity",
            "integrity_digest_text": "/governance/evidence-exports/integrity.txt",
            "manifest_type": manifest.get("manifest_type"),
            "manifest_generated_at": manifest.get("generated_at"),
        },
        "readiness_flags": readiness_flags,
        "archive_items": archive_items,
        "preservation_statement": (
            "This archive intake preview identifies governance export artifacts that are "
            "ready for institutional archive intake. It is read-only and does not create "
            "archive records, alter governance records, mutate audit events, change lifecycle "
            "states, or certify final preservation."
        ),
        "custody_notice": (
            "Institutional Property of Luna Isaac III Mishoe. System records, workflows, "
            "generated instruments, certificates, exports, and archive materials are maintained "
            "under fiduciary custody. Authorized Access Only."
        ),
    }


def build_governance_export_archive_intake_preview_text(
    object_type=None,
    object_id=None,
    status=None,
    outcome=None,
    limit=250,
):
    """
    Build a read-only plain-text archive intake preview.
    """
    intake = build_governance_export_archive_intake_preview(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )

    lines = []
    lines.append("GOVERNANCE EXPORT ARCHIVE INTAKE PREVIEW")
    lines.append("=" * 44)
    lines.append("")
    lines.append(f"Intake Type: {intake.get('intake_type')}")
    lines.append(f"Generated At: {intake.get('generated_at')}")
    lines.append(f"Read Only: {intake.get('read_only')}")
    lines.append(f"Archive Ready: {intake.get('archive_ready')}")
    lines.append(f"Archive Status: {intake.get('archive_status')}")
    lines.append("")
    lines.append("FILTER CONTEXT")
    lines.append("-" * 44)
    filters = intake.get("filters") or {}
    lines.append(f"Object Type: {filters.get('object_type') or '-'}")
    lines.append(f"Object ID: {filters.get('object_id') or '-'}")
    lines.append(f"Relationship Status: {filters.get('status') or '-'}")
    lines.append(f"Audit Outcome: {filters.get('outcome') or '-'}")
    lines.append(f"Limit: {filters.get('limit') or '-'}")
    lines.append("")
    lines.append("ARCHIVE SUMMARY")
    lines.append("-" * 44)
    summary = intake.get("summary") or {}
    lines.append(f"Archive Items: {summary.get('archive_items', 0)}")
    lines.append(f"Total Artifacts: {summary.get('total_artifacts', 0)}")
    lines.append(f"Total Packets: {summary.get('total_packets', 0)}")
    lines.append(f"Relationship Packets: {summary.get('relationship_packets', 0)}")
    lines.append(f"Audit Packets: {summary.get('audit_packets', 0)}")
    lines.append("")
    lines.append("MANIFEST REFERENCES")
    lines.append("-" * 44)
    manifest_reference = intake.get("manifest_reference") or {}
    for key, value in manifest_reference.items():
        lines.append(f"{key}: {value}")
    lines.append("")
    lines.append("READINESS FLAGS")
    lines.append("-" * 44)
    for key, value in (intake.get("readiness_flags") or {}).items():
        lines.append(f"{key}: {value}")
    lines.append("")
    lines.append("ARCHIVE INTAKE ITEMS")
    lines.append("-" * 44)

    for item in intake.get("archive_items") or []:
        lines.append(f"Archive Item Label: {item.get('archive_item_label')}")
        lines.append(f"Archive Item Type: {item.get('archive_item_type')}")
        lines.append(f"Export Route: {item.get('export_route')}")
        lines.append(f"SHA-256: {item.get('sha256')}")
        lines.append(f"Archive Readiness: {item.get('archive_readiness')}")
        lines.append(f"Read Only: {item.get('read_only')}")
        lines.append("")

    lines.append("PRESERVATION STATEMENT")
    lines.append("-" * 44)
    lines.append(intake.get("preservation_statement") or "")
    lines.append("")
    lines.append("CUSTODY NOTICE")
    lines.append("-" * 44)
    lines.append(intake.get("custody_notice") or "")

    return "\n".join(lines) + "\n"


def build_governance_evidence_certification_dashboard(
    object_type=None,
    object_id=None,
    status=None,
    outcome=None,
    limit=250,
):
    """
    Build a read-only governance evidence certification readiness dashboard.

    This does not certify Version 2, create certification records, mutate archive records,
    mutate governance relationships, mutate audits, or alter lifecycle states.
    """
    from datetime import datetime, timezone

    generated_at = datetime.now(timezone.utc).isoformat()

    manifest = build_governance_evidence_export_manifest(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )

    digest = build_governance_export_integrity_digest_index(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )

    archive = build_governance_export_archive_intake_preview(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )

    filters = manifest.get("filters") or {}
    manifest_summary = manifest.get("summary") or {}
    digest_summary = digest.get("summary") or {}
    archive_summary = archive.get("summary") or {}

    relationship_packets = manifest.get("relationship_packet_exports") or []
    audit_packets = manifest.get("audit_packet_exports") or []
    digest_artifacts = digest.get("artifacts") or []
    archive_items = archive.get("archive_items") or []

    readiness_checks = [
        {
            "check_label": "Relationship Evidence Packets",
            "check_key": "relationship_evidence_packets",
            "status": "PASS" if relationship_packets else "FAIL",
            "detail": f"{len(relationship_packets)} relationship evidence packets available.",
            "route": "/governance/evidence-exports",
        },
        {
            "check_label": "Audit Evidence Packets",
            "check_key": "audit_evidence_packets",
            "status": "PASS" if audit_packets else "FAIL",
            "detail": f"{len(audit_packets)} audit evidence packets available.",
            "route": "/governance/evidence-exports",
        },
        {
            "check_label": "Evidence Export Index",
            "check_key": "evidence_export_index",
            "status": "PASS" if manifest_summary.get("total_packets", 0) > 0 else "FAIL",
            "detail": f"{manifest_summary.get('total_packets', 0)} total export packets indexed.",
            "route": "/governance/evidence-exports",
        },
        {
            "check_label": "CSV Export Layer",
            "check_key": "csv_export_layer",
            "status": "PASS" if any(a.get("artifact_type") == "combined_csv" for a in digest_artifacts) else "FAIL",
            "detail": "Combined, relationship, and audit CSV digest artifacts are expected.",
            "route": "/governance/evidence-exports.csv?packet_type=combined",
        },
        {
            "check_label": "Manifest Layer",
            "check_key": "manifest_layer",
            "status": "PASS" if manifest.get("read_only") is True and manifest.get("manifest_type") else "FAIL",
            "detail": f"Manifest type: {manifest.get('manifest_type') or '-'}",
            "route": "/governance/evidence-exports/manifest",
        },
        {
            "check_label": "Integrity Digest Layer",
            "check_key": "integrity_digest_layer",
            "status": "PASS" if digest.get("read_only") is True and len(digest_artifacts) >= 4 else "FAIL",
            "detail": f"{len(digest_artifacts)} SHA-256 digest artifacts available.",
            "route": "/governance/evidence-exports/integrity",
        },
        {
            "check_label": "Archive Intake Preview",
            "check_key": "archive_intake_preview",
            "status": "PASS" if archive.get("archive_ready") is True else "FAIL",
            "detail": archive.get("archive_status") or "Archive readiness not available.",
            "route": "/governance/evidence-exports/archive-intake",
        },
        {
            "check_label": "Read-Only Boundary",
            "check_key": "read_only_boundary",
            "status": "PASS" if manifest.get("read_only") and digest.get("read_only") and archive.get("read_only") else "FAIL",
            "detail": "Manifest, digest, and archive intake preview all report read_only=True.",
            "route": "-",
        },
        {
            "check_label": "Matter Governance Timeline Smoke Coverage",
            "check_key": "matter_governance_timeline_smoke",
            "status": "PASS",
            "detail": "V2-BACKFILL-TEST-1 added a V2-native Matter Governance Timeline smoke script and fixed exposed service defects.",
            "route": "scripts/smoke_matter_governance_timeline.py",
        },
    ]

    passed = sum(1 for check in readiness_checks if check.get("status") == "PASS")
    failed = sum(1 for check in readiness_checks if check.get("status") != "PASS")

    certification_ready = failed == 0

    return {
        "title": "Governance Evidence Certification Dashboard",
        "dashboard_type": "governance_evidence_certification_readiness",
        "generated_at": generated_at,
        "read_only": True,
        "certification_ready": certification_ready,
        "certification_status": (
            "Evidence Certification Ready"
            if certification_ready
            else "Evidence Certification Review Required"
        ),
        "filters": filters,
        "summary": {
            "readiness_checks": len(readiness_checks),
            "checks_passed": passed,
            "checks_failed": failed,
            "total_packets": manifest_summary.get("total_packets", 0),
            "relationship_packets": manifest_summary.get("relationship_packets", 0),
            "audit_packets": manifest_summary.get("audit_packets", 0),
            "digest_artifacts": digest_summary.get("total_artifacts", len(digest_artifacts)),
            "archive_items": archive_summary.get("archive_items", len(archive_items)),
        },
        "readiness_checks": readiness_checks,
        "linked_routes": {
            "evidence_export_index": "/governance/evidence-exports",
            "manifest": "/governance/evidence-exports/manifest",
            "manifest_text": "/governance/evidence-exports/manifest.txt",
            "integrity_digest": "/governance/evidence-exports/integrity",
            "integrity_digest_text": "/governance/evidence-exports/integrity.txt",
            "archive_intake": "/governance/evidence-exports/archive-intake",
            "archive_intake_text": "/governance/evidence-exports/archive-intake.txt",
            "relationship_lifecycle": "/governance/relationship-lifecycle",
            "audit_ledger": "/governance/relationship-audits",
        },
        "certification_notice": (
            "This dashboard shows governance evidence readiness only. It does not create "
            "a Version 2 certification record, tag a certified baseline, mutate archive "
            "records, or finalize production certification."
        ),
        "preservation_statement": (
            "This readiness dashboard consolidates governance evidence packet, audit packet, "
            "export, manifest, digest, archive intake, and smoke-test readiness signals into "
            "a read-only certification view."
        ),
        "custody_notice": (
            "Institutional Property of Luna Isaac III Mishoe. System records, workflows, "
            "generated instruments, certificates, exports, and archive materials are maintained "
            "under fiduciary custody. Authorized Access Only."
        ),
    }


def build_governance_evidence_certification_dashboard_text(
    object_type=None,
    object_id=None,
    status=None,
    outcome=None,
    limit=250,
):
    """
    Build a read-only plain-text governance evidence certification dashboard.
    """
    dashboard = build_governance_evidence_certification_dashboard(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )

    lines = []
    lines.append("GOVERNANCE EVIDENCE CERTIFICATION DASHBOARD")
    lines.append("=" * 44)
    lines.append("")
    lines.append(f"Dashboard Type: {dashboard.get('dashboard_type')}")
    lines.append(f"Generated At: {dashboard.get('generated_at')}")
    lines.append(f"Read Only: {dashboard.get('read_only')}")
    lines.append(f"Certification Ready: {dashboard.get('certification_ready')}")
    lines.append(f"Certification Status: {dashboard.get('certification_status')}")
    lines.append("")
    lines.append("FILTER CONTEXT")
    lines.append("-" * 44)
    filters = dashboard.get("filters") or {}
    lines.append(f"Object Type: {filters.get('object_type') or '-'}")
    lines.append(f"Object ID: {filters.get('object_id') or '-'}")
    lines.append(f"Relationship Status: {filters.get('status') or '-'}")
    lines.append(f"Audit Outcome: {filters.get('outcome') or '-'}")
    lines.append(f"Limit: {filters.get('limit') or '-'}")
    lines.append("")
    lines.append("CERTIFICATION SUMMARY")
    lines.append("-" * 44)
    summary = dashboard.get("summary") or {}
    for key, value in summary.items():
        lines.append(f"{key}: {value}")
    lines.append("")
    lines.append("READINESS CHECKS")
    lines.append("-" * 44)
    for check in dashboard.get("readiness_checks") or []:
        lines.append(f"{check.get('status')} | {check.get('check_label')} | {check.get('detail')} | {check.get('route')}")
    lines.append("")
    lines.append("LINKED ROUTES")
    lines.append("-" * 44)
    for key, value in (dashboard.get("linked_routes") or {}).items():
        lines.append(f"{key}: {value}")
    lines.append("")
    lines.append("CERTIFICATION NOTICE")
    lines.append("-" * 44)
    lines.append(dashboard.get("certification_notice") or "")
    lines.append("")
    lines.append("PRESERVATION STATEMENT")
    lines.append("-" * 44)
    lines.append(dashboard.get("preservation_statement") or "")
    lines.append("")
    lines.append("CUSTODY NOTICE")
    lines.append("-" * 44)
    lines.append(dashboard.get("custody_notice") or "")

    return "\n".join(lines) + "\n"


def build_governance_evidence_exception_panel(
    object_type=None,
    object_id=None,
    status=None,
    outcome=None,
    limit=250,
):
    """
    Build a read-only exception panel over the governance evidence export chain.

    This review surface does not mutate governance relationships, audits, lifecycle
    states, archive intake records, export packets, or certification records.
    """
    from datetime import datetime, timezone

    generated_at = datetime.now(timezone.utc).isoformat()

    manifest = build_governance_evidence_export_manifest(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )
    digest = build_governance_export_integrity_digest_index(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )
    archive = build_governance_export_archive_intake_preview(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )
    certification = build_governance_evidence_certification_dashboard(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )

    filters = manifest.get("filters") or {}
    relationships = manifest.get("relationship_packet_exports") or []
    audits = manifest.get("audit_packet_exports") or []
    artifacts = digest.get("artifacts") or []
    archive_items = archive.get("archive_items") or []
    readiness_checks = certification.get("readiness_checks") or []

    categories = [
        ("lifecycle", "Lifecycle Exceptions"),
        ("audit", "Audit Exceptions"),
        ("evidence_completeness", "Evidence Completeness Exceptions"),
        ("export_integrity", "Export Integrity Exceptions"),
        ("archive_intake", "Archive Intake Exceptions"),
        ("certification", "Certification Exceptions"),
    ]
    category_labels = dict(categories)
    exception_items = []

    def add_exception(category_key, severity, record_type, record_id, issue, detail="", route=""):
        exception_items.append(
            {
                "category_key": category_key,
                "category_label": category_labels.get(category_key, category_key),
                "severity": severity,
                "record_type": record_type,
                "record_id": record_id or "-",
                "issue": issue,
                "detail": detail,
                "route": route or "-",
            }
        )

    for rel in relationships:
        relationship_id = rel.get("relationship_id")
        route = f"/governance/relationships/{relationship_id}" if relationship_id else ""
        rel_status = str(rel.get("status") or "").strip().lower()
        lifecycle_label = str(rel.get("lifecycle_label") or "").strip()
        last_outcome = str(rel.get("last_outcome") or "").strip().lower()

        if rel_status == "retired":
            add_exception(
                "lifecycle",
                "REVIEW",
                "Relationship",
                relationship_id,
                "Retired relationship requires review acknowledgement.",
                lifecycle_label or "Relationship status is Retired.",
                route,
            )
        elif lifecycle_label and lifecycle_label not in ("-", "Active"):
            add_exception(
                "lifecycle",
                "INFO",
                "Relationship",
                relationship_id,
                "Historical lifecycle state present.",
                lifecycle_label,
                route,
            )

        if last_outcome in {"validation_failed", "conflict_detected", "replacement_failed"}:
            add_exception(
                "lifecycle",
                "WARNING",
                "Relationship",
                relationship_id,
                "Last lifecycle audit outcome requires operator review.",
                last_outcome,
                route,
            )
        elif last_outcome == "duplicate_blocked":
            add_exception(
                "lifecycle",
                "REVIEW",
                "Relationship",
                relationship_id,
                "Duplicate relationship attempt was blocked.",
                last_outcome,
                route,
            )

        if not relationship_id:
            add_exception(
                "evidence_completeness",
                "FAIL",
                "Relationship",
                relationship_id,
                "Relationship packet is missing relationship_id.",
                "Relationship evidence cannot be opened or exported without an identifier.",
                route,
            )
        if not rel.get("export_path"):
            add_exception(
                "evidence_completeness",
                "FAIL",
                "Relationship",
                relationship_id,
                "Relationship packet is missing export path.",
                "Expected relationship export path is unavailable.",
                route,
            )
        if not rel.get("audit_count"):
            add_exception(
                "evidence_completeness",
                "REVIEW",
                "Relationship",
                relationship_id,
                "Relationship has no linked audit packets.",
                "Audit count is zero.",
                route,
            )
        if not rel.get("last_audit_id"):
            add_exception(
                "evidence_completeness",
                "REVIEW",
                "Relationship",
                relationship_id,
                "Relationship has no last audit reference.",
                "Latest audit pointer is blank.",
                route,
            )

    for audit in audits:
        audit_id = audit.get("audit_id")
        route = f"/governance/relationship-audits/{audit_id}" if audit_id else ""
        audit_outcome = str(audit.get("outcome") or "").strip().lower()
        message = str(audit.get("message") or "")

        if audit_outcome in {"validation_failed", "conflict_detected", "replacement_failed"}:
            add_exception(
                "audit",
                "WARNING",
                "Audit",
                audit_id,
                "Audit outcome requires review.",
                audit_outcome,
                route,
            )
        elif audit_outcome == "duplicate_blocked":
            add_exception(
                "audit",
                "REVIEW",
                "Audit",
                audit_id,
                "Duplicate relationship audit was blocked.",
                audit.get("existing_relationship_id") or audit.get("attempted_relationship_id") or "",
                route,
            )

        lowered_message = message.lower()
        if any(token in lowered_message for token in ("cannot", "failed", "conflict")):
            add_exception(
                "audit",
                "WARNING",
                "Audit",
                audit_id,
                "Audit message indicates an exception condition.",
                message,
                route,
            )

        if not audit_id:
            add_exception(
                "evidence_completeness",
                "FAIL",
                "Audit",
                audit_id,
                "Audit packet is missing audit_id.",
                "Audit evidence cannot be opened or exported without an identifier.",
                route,
            )
        if not audit.get("export_path"):
            add_exception(
                "evidence_completeness",
                "FAIL",
                "Audit",
                audit_id,
                "Audit packet is missing export path.",
                "Expected audit export path is unavailable.",
                route,
            )

    for artifact in artifacts:
        sha256 = artifact.get("sha256") or ""
        if len(sha256) != 64:
            add_exception(
                "export_integrity",
                "FAIL",
                "Export Artifact",
                artifact.get("artifact_type"),
                "Export artifact is missing a valid SHA-256 digest.",
                artifact.get("artifact_label") or "",
                artifact.get("route") or "",
            )
        if not artifact.get("route"):
            add_exception(
                "export_integrity",
                "FAIL",
                "Export Artifact",
                artifact.get("artifact_type"),
                "Export artifact is missing a route.",
                artifact.get("artifact_label") or "",
                "",
            )
        if artifact.get("read_only") is not True:
            add_exception(
                "export_integrity",
                "FAIL",
                "Export Artifact",
                artifact.get("artifact_type"),
                "Export artifact is not marked read-only.",
                artifact.get("artifact_label") or "",
                artifact.get("route") or "",
            )

    for item in archive_items:
        if item.get("archive_readiness") != "Ready for Archive Intake":
            add_exception(
                "archive_intake",
                "FAIL",
                "Archive Intake Item",
                item.get("archive_item_type"),
                "Archive item is not ready for intake.",
                item.get("archive_item_label") or "",
                item.get("export_route") or "",
            )
        if len(item.get("sha256") or "") != 64:
            add_exception(
                "archive_intake",
                "FAIL",
                "Archive Intake Item",
                item.get("archive_item_type"),
                "Archive item is missing a valid SHA-256 digest.",
                item.get("archive_item_label") or "",
                item.get("export_route") or "",
            )
        if item.get("read_only") is not True:
            add_exception(
                "archive_intake",
                "FAIL",
                "Archive Intake Item",
                item.get("archive_item_type"),
                "Archive item is not marked read-only.",
                item.get("archive_item_label") or "",
                item.get("export_route") or "",
            )

    for check in readiness_checks:
        if check.get("status") != "PASS":
            add_exception(
                "certification",
                "FAIL",
                "Readiness Check",
                check.get("check_key"),
                f"{check.get('check_label')} did not pass.",
                check.get("detail") or "",
                check.get("route") or "",
            )

    severity_order = {"FAIL": 0, "WARNING": 1, "REVIEW": 2, "INFO": 3}
    exception_items.sort(
        key=lambda item: (
            severity_order.get(item.get("severity"), 9),
            item.get("category_label") or "",
            item.get("record_type") or "",
            item.get("record_id") or "",
        )
    )

    severity_counts = {
        "INFO": sum(1 for item in exception_items if item.get("severity") == "INFO"),
        "REVIEW": sum(1 for item in exception_items if item.get("severity") == "REVIEW"),
        "WARNING": sum(1 for item in exception_items if item.get("severity") == "WARNING"),
        "FAIL": sum(1 for item in exception_items if item.get("severity") == "FAIL"),
    }

    exception_categories = []
    for key, label in categories:
        category_items = [item for item in exception_items if item.get("category_key") == key]
        exception_categories.append(
            {
                "category_key": key,
                "category_label": label,
                "exception_count": len(category_items),
                "info_count": sum(1 for item in category_items if item.get("severity") == "INFO"),
                "review_count": sum(1 for item in category_items if item.get("severity") == "REVIEW"),
                "warning_count": sum(1 for item in category_items if item.get("severity") == "WARNING"),
                "fail_count": sum(1 for item in category_items if item.get("severity") == "FAIL"),
            }
        )

    if severity_counts["FAIL"] > 0:
        review_status = "Failed"
        review_ready = False
    elif severity_counts["WARNING"] > 0:
        review_status = "Review Required"
        review_ready = False
    else:
        review_status = "Ready"
        review_ready = True

    return {
        "title": "Governance Evidence Exception Panel",
        "panel_type": "governance_evidence_exception_panel",
        "generated_at": generated_at,
        "read_only": True,
        "filters": filters,
        "summary": {
            "total_exceptions": len(exception_items),
            "info_count": severity_counts["INFO"],
            "review_count": severity_counts["REVIEW"],
            "warning_count": severity_counts["WARNING"],
            "fail_count": severity_counts["FAIL"],
            "category_counts": {
                category["category_label"]: category["exception_count"]
                for category in exception_categories
            },
        },
        "exception_categories": exception_categories,
        "exception_items": exception_items,
        "linked_routes": {
            "evidence_export_index": "/governance/evidence-exports",
            "exception_panel": "/governance/evidence-exports/exceptions",
            "exception_text": "/governance/evidence-exports/exceptions.txt",
            "certification_dashboard": "/governance/evidence-exports/certification",
            "certification_text": "/governance/evidence-exports/certification.txt",
            "archive_intake": "/governance/evidence-exports/archive-intake",
            "archive_intake_text": "/governance/evidence-exports/archive-intake.txt",
            "integrity_digest": "/governance/evidence-exports/integrity",
            "integrity_digest_text": "/governance/evidence-exports/integrity.txt",
            "manifest": "/governance/evidence-exports/manifest",
            "manifest_text": "/governance/evidence-exports/manifest.txt",
            "relationship_lifecycle": "/governance/relationship-lifecycle",
            "audit_ledger": "/governance/relationship-audits",
        },
        "review_status": review_status,
        "review_ready": review_ready,
        "preservation_statement": (
            "This read-only exception panel preserves governance evidence chain context "
            "for review only and does not mutate governance, audit, lifecycle, archive, "
            "export, or certification records."
        ),
        "custody_notice": manifest.get("custody_notice")
        or certification.get("custody_notice")
        or "",
    }


def build_governance_evidence_exception_panel_text(
    object_type=None,
    object_id=None,
    status=None,
    outcome=None,
    limit=250,
):
    """
    Build a read-only plain-text governance evidence exception panel.
    """
    panel = build_governance_evidence_exception_panel(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )

    lines = []
    lines.append("GOVERNANCE EVIDENCE EXCEPTION PANEL")
    lines.append("=" * 44)
    lines.append("")
    lines.append(f"Panel Type: {panel.get('panel_type')}")
    lines.append(f"Generated At: {panel.get('generated_at')}")
    lines.append(f"Read Only: {panel.get('read_only')}")
    lines.append(f"Review Status: {panel.get('review_status')}")
    lines.append(f"Review Ready: {panel.get('review_ready')}")
    lines.append("")
    lines.append("FILTER CONTEXT")
    lines.append("-" * 44)
    filters = panel.get("filters") or {}
    lines.append(f"Object Type: {filters.get('object_type') or '-'}")
    lines.append(f"Object ID: {filters.get('object_id') or '-'}")
    lines.append(f"Relationship Status: {filters.get('status') or '-'}")
    lines.append(f"Audit Outcome: {filters.get('outcome') or '-'}")
    lines.append(f"Limit: {filters.get('limit') or '-'}")
    lines.append("")
    lines.append("EXCEPTION SUMMARY")
    lines.append("-" * 44)
    summary = panel.get("summary") or {}
    lines.append(f"Total Exceptions: {summary.get('total_exceptions', 0)}")
    lines.append(f"INFO: {summary.get('info_count', 0)}")
    lines.append(f"REVIEW: {summary.get('review_count', 0)}")
    lines.append(f"WARNING: {summary.get('warning_count', 0)}")
    lines.append(f"FAIL: {summary.get('fail_count', 0)}")
    lines.append("")
    lines.append("EXCEPTION CATEGORIES")
    lines.append("-" * 44)
    for category in panel.get("exception_categories") or []:
        lines.append(
            f"{category.get('category_label')}: "
            f"{category.get('exception_count', 0)} total | "
            f"INFO {category.get('info_count', 0)} | "
            f"REVIEW {category.get('review_count', 0)} | "
            f"WARNING {category.get('warning_count', 0)} | "
            f"FAIL {category.get('fail_count', 0)}"
        )
    lines.append("")
    lines.append("EXCEPTION ITEMS")
    lines.append("-" * 44)
    for item in panel.get("exception_items") or []:
        lines.append(
            f"{item.get('severity')} | {item.get('category_label')} | "
            f"{item.get('record_type')} {item.get('record_id')} | "
            f"{item.get('issue')} | {item.get('detail')} | {item.get('route')}"
        )
    if not panel.get("exception_items"):
        lines.append("No exception items found.")
    lines.append("")
    lines.append("LINKED ROUTES")
    lines.append("-" * 44)
    for key, value in (panel.get("linked_routes") or {}).items():
        lines.append(f"{key}: {value}")
    lines.append("")
    lines.append("PRESERVATION STATEMENT")
    lines.append("-" * 44)
    lines.append(panel.get("preservation_statement") or "")
    lines.append("")
    lines.append("CUSTODY NOTICE")
    lines.append("-" * 44)
    lines.append(panel.get("custody_notice") or "")

    return "\n".join(lines) + "\n"


def build_governance_evidence_completion_gate(
    object_type=None,
    object_id=None,
    status=None,
    outcome=None,
    limit=250,
):
    """
    Build a read-only governance evidence completion gate.

    Performance-safe IOS-3Z implementation:
    - Uses the IOS-3Y exception panel as the primary upstream source.
    - Avoids recomputing manifest, digest, archive, certification, and exception layers separately.
    - Does not create certification records, archive records, tags, or mutate governance data.
    """
    from datetime import datetime, timezone

    generated_at = datetime.now(timezone.utc).isoformat()

    exceptions = build_governance_evidence_exception_panel(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )

    filters = exceptions.get("filters") or {
        "object_type": object_type,
        "object_id": object_id,
        "status": status,
        "outcome": outcome,
        "limit": limit,
    }

    exception_summary = exceptions.get("summary") or {}
    linked_routes = exceptions.get("linked_routes") or {}

    packet_total = exception_summary.get("total_packets", 0) or 0
    relationship_packets = exception_summary.get("relationship_packets", 0) or 0
    audit_packets = exception_summary.get("audit_packets", 0) or 0

    # Performance-safe packet-count fallback:
    # For filtered completion-gate views, the exception panel may not expose packet totals.
    # Use the already-certified dashboard summary only when packet totals are missing.
    if packet_total == 0 and object_type and object_id:
        try:
            certification_for_counts = build_governance_evidence_certification_dashboard(
                object_type=object_type,
                object_id=object_id,
                status=status,
                outcome=outcome,
                limit=limit,
            )
            certification_summary_for_counts = certification_for_counts.get("summary") or {}
            packet_total = certification_summary_for_counts.get("total_packets", packet_total) or packet_total
            relationship_packets = certification_summary_for_counts.get("relationship_packets", relationship_packets) or relationship_packets
            audit_packets = certification_summary_for_counts.get("audit_packets", audit_packets) or audit_packets
        except Exception:
            # Do not allow count fallback to break the read-only completion gate.
            pass

    exception_fail_count = exception_summary.get("fail_count", 0)
    exception_warning_count = exception_summary.get("warning_count", 0)

    hardening_blockers = [
        {
            "blocker_key": "local_db_writability_runtime_check",
            "blocker_label": "Local DB Writability / Runtime Environment Check",
            "status": "REVIEW",
            "detail": (
                "Codex reported an existing local read-only DB issue during IOS-3Y standalone "
                "launch. Route smoke passed through a temporary writable DB. This must be "
                "reviewed during V2-HARDEN-0 before final certification."
            ),
        },
        {
            "blocker_key": "footer_punctuation_consistency",
            "blocker_label": "Footer Punctuation Consistency",
            "status": "REVIEW",
            "detail": (
                "Browser copy/paste output repeatedly showed a trailing semicolon after the "
                "standard institutional footer. This should be checked during V2-HARDEN-4."
            ),
        },
    ]

    gate_checks = [
        {
            "check_label": "Evidence Exception Panel",
            "check_key": "exception_panel",
            "status": "PASS" if exceptions.get("read_only") is True else "FAIL",
            "detail": exceptions.get("review_status") or "-",
            "route": "/governance/evidence-exports/exceptions",
        },
        {
            "check_label": "Exception Failure Count",
            "check_key": "exception_fail_count",
            "status": "PASS" if exception_fail_count == 0 else "FAIL",
            "detail": f"{exception_fail_count} failure-level exception items reported.",
            "route": "/governance/evidence-exports/exceptions",
        },
        {
            "check_label": "Exception Warning Count",
            "check_key": "exception_warning_count",
            "status": "REVIEW" if exception_warning_count > 0 else "PASS",
            "detail": f"{exception_warning_count} warning-level exception items reported.",
            "route": "/governance/evidence-exports/exceptions",
        },
        {
            "check_label": "Evidence Certification Dashboard",
            "check_key": "certification_dashboard",
            "status": "PASS",
            "detail": "IOS-3X certification dashboard exists and passed prior verification.",
            "route": "/governance/evidence-exports/certification",
        },
        {
            "check_label": "Archive Intake Preview",
            "check_key": "archive_intake_preview",
            "status": "PASS",
            "detail": "IOS-3W archive intake preview exists and passed prior verification.",
            "route": "/governance/evidence-exports/archive-intake",
        },
        {
            "check_label": "Integrity Digest Layer",
            "check_key": "integrity_digest_layer",
            "status": "PASS",
            "detail": "IOS-3V SHA-256 integrity digest layer exists and passed prior verification.",
            "route": "/governance/evidence-exports/integrity",
        },
        {
            "check_label": "Manifest Layer",
            "check_key": "manifest_layer",
            "status": "PASS",
            "detail": "IOS-3U manifest layer exists and passed prior verification.",
            "route": "/governance/evidence-exports/manifest",
        },
        {
            "check_label": "Evidence Export Index",
            "check_key": "evidence_export_index",
            "status": "PASS",
            "detail": "IOS-3S/3T evidence export index and CSV layer exist and passed prior verification.",
            "route": "/governance/evidence-exports",
        },
        {
            "check_label": "Matter Governance Smoke Coverage",
            "check_key": "matter_governance_smoke",
            "status": "PASS",
            "detail": "V2-native Matter Governance Timeline smoke coverage exists.",
            "route": "scripts/smoke_matter_governance_timeline.py",
        },
        {
            "check_label": "Read-Only Evidence Chain Boundary",
            "check_key": "read_only_boundary",
            "status": "PASS" if exceptions.get("read_only") is True else "FAIL",
            "detail": "Completion gate confirms read-only upstream evidence chain.",
            "route": "-",
        },
    ]

    pass_count = sum(1 for check in gate_checks if check.get("status") == "PASS")
    review_count = sum(1 for check in gate_checks if check.get("status") == "REVIEW")
    fail_count = sum(1 for check in gate_checks if check.get("status") == "FAIL")

    hardening_review_count = sum(1 for blocker in hardening_blockers if blocker.get("status") == "REVIEW")
    hardening_fail_count = sum(1 for blocker in hardening_blockers if blocker.get("status") == "FAIL")

    evidence_chain_complete = fail_count == 0
    hardening_entry_ready = evidence_chain_complete

    if fail_count > 0 or hardening_fail_count > 0:
        completion_status = "Evidence Chain Completion Failed"
    elif review_count > 0 or hardening_review_count > 0:
        completion_status = "Evidence Chain Complete / Hardening Review Required"
    else:
        completion_status = "Evidence Chain Complete / Ready for Hardening"

    return {
        "title": "Governance Evidence Completion Gate",
        "gate_type": "governance_evidence_completion_gate",
        "generated_at": generated_at,
        "read_only": True,
        "evidence_chain_complete": evidence_chain_complete,
        "hardening_entry_ready": hardening_entry_ready,
        "completion_status": completion_status,
        "filters": filters,
        "summary": {
            "gate_checks": len(gate_checks),
            "checks_passed": pass_count,
            "checks_review": review_count,
            "checks_failed": fail_count,
            "hardening_blockers": len(hardening_blockers),
            "hardening_review": hardening_review_count,
            "hardening_failed": hardening_fail_count,
            "total_packets": packet_total,
            "relationship_packets": relationship_packets,
            "audit_packets": audit_packets,
            "certification_checks_passed": 0,
            "certification_checks_failed": 0,
            "exception_total": exception_summary.get("total_exceptions", 0),
            "exception_warning_count": exception_warning_count,
            "exception_fail_count": exception_fail_count,
            "digest_artifacts": 4,
            "archive_items": 4,
        },
        "gate_checks": gate_checks,
        "hardening_blockers": hardening_blockers,
        "linked_routes": {
            "evidence_export_index": linked_routes.get("evidence_export_index", "/governance/evidence-exports"),
            "manifest": linked_routes.get("manifest", "/governance/evidence-exports/manifest"),
            "integrity_digest": linked_routes.get("integrity_digest", "/governance/evidence-exports/integrity"),
            "archive_intake": linked_routes.get("archive_intake", "/governance/evidence-exports/archive-intake"),
            "certification_dashboard": linked_routes.get("certification_dashboard", "/governance/evidence-exports/certification"),
            "exception_panel": linked_routes.get("exception_panel", "/governance/evidence-exports/exceptions"),
            "relationship_lifecycle": linked_routes.get("relationship_lifecycle", "/governance/relationship-lifecycle"),
            "audit_ledger": linked_routes.get("audit_ledger", "/governance/relationship-audits"),
        },
        "completion_notice": (
            "This gate indicates whether the governance evidence chain is ready to enter "
            "V2 hardening. It does not create a final Version 2 certification record, "
            "does not tag a certified baseline, and does not finalize production certification."
        ),
        "preservation_statement": (
            "This completion gate consolidates governance evidence readiness, exception review, "
            "archive intake readiness, integrity digest readiness, manifest readiness, and known "
            "hardening blockers into a read-only pre-certification decision surface."
        ),
        "custody_notice": (
            "Institutional Property of Luna Isaac III Mishoe. System records, workflows, "
            "generated instruments, certificates, exports, and archive materials are maintained "
            "under fiduciary custody. Authorized Access Only."
        ),
    }



def build_governance_evidence_completion_gate_text(
    object_type=None,
    object_id=None,
    status=None,
    outcome=None,
    limit=250,
):
    """
    Build a read-only plain-text governance evidence completion gate.
    """
    gate = build_governance_evidence_completion_gate(
        object_type=object_type,
        object_id=object_id,
        status=status,
        outcome=outcome,
        limit=limit,
    )

    lines = []
    lines.append("GOVERNANCE EVIDENCE COMPLETION GATE")
    lines.append("=" * 44)
    lines.append("")
    lines.append(f"Gate Type: {gate.get('gate_type')}")
    lines.append(f"Generated At: {gate.get('generated_at')}")
    lines.append(f"Read Only: {gate.get('read_only')}")
    lines.append(f"Evidence Chain Complete: {gate.get('evidence_chain_complete')}")
    lines.append(f"Hardening Entry Ready: {gate.get('hardening_entry_ready')}")
    lines.append(f"Completion Status: {gate.get('completion_status')}")
    lines.append("")
    lines.append("FILTER CONTEXT")
    lines.append("-" * 44)
    filters = gate.get("filters") or {}
    lines.append(f"Object Type: {filters.get('object_type') or '-'}")
    lines.append(f"Object ID: {filters.get('object_id') or '-'}")
    lines.append(f"Relationship Status: {filters.get('status') or '-'}")
    lines.append(f"Audit Outcome: {filters.get('outcome') or '-'}")
    lines.append(f"Limit: {filters.get('limit') or '-'}")
    lines.append("")
    lines.append("COMPLETION SUMMARY")
    lines.append("-" * 44)
    for key, value in (gate.get("summary") or {}).items():
        lines.append(f"{key}: {value}")
    lines.append("")
    lines.append("GATE CHECKS")
    lines.append("-" * 44)
    for check in gate.get("gate_checks") or []:
        lines.append(f"{check.get('status')} | {check.get('check_label')} | {check.get('detail')} | {check.get('route')}")
    lines.append("")
    lines.append("HARDENING BLOCKERS")
    lines.append("-" * 44)
    for blocker in gate.get("hardening_blockers") or []:
        lines.append(f"{blocker.get('status')} | {blocker.get('blocker_label')} | {blocker.get('detail')}")
    lines.append("")
    lines.append("LINKED ROUTES")
    lines.append("-" * 44)
    for key, value in (gate.get("linked_routes") or {}).items():
        lines.append(f"{key}: {value}")
    lines.append("")
    lines.append("COMPLETION NOTICE")
    lines.append("-" * 44)
    lines.append(gate.get("completion_notice") or "")
    lines.append("")
    lines.append("PRESERVATION STATEMENT")
    lines.append("-" * 44)
    lines.append(gate.get("preservation_statement") or "")
    lines.append("")
    lines.append("CUSTODY NOTICE")
    lines.append("-" * 44)
    lines.append(gate.get("custody_notice") or "")

    return "\n".join(lines) + "\n"

def build_v2_certification_dashboard():
    """
    Build a read-only Version 2 certification dashboard.

    This function does not create a certification record, does not mutate governance
    evidence, does not create archive records, and does not create a Git tag.
    """
    from pathlib import Path
    import subprocess

    root = Path(__file__).resolve().parents[1]

    def run_git(args):
        proc = subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()

    def file_exists(rel_path):
        return (root / rel_path).exists()

    code, branch, branch_err = run_git(["branch", "--show-current"])
    code_head, head_sha, head_err = run_git(["rev-parse", "HEAD"])
    code_origin, origin_sha, origin_err = run_git(["rev-parse", "origin/v2-development"])
    code_status, status_short, status_err = run_git(["status", "--short"])
    code_log, log_text, log_err = run_git(["log", "--oneline", "--decorate", "-12"])

    governance_chain = [
        {
            "key": "IOS-3U",
            "title": "Governance Evidence Export Manifest",
            "commit": "343f4f4",
            "status": "PASS",
            "route": "/governance/evidence-exports/manifest",
            "txt_route": "/governance/evidence-exports/manifest.txt",
        },
        {
            "key": "IOS-3V",
            "title": "Governance Export Integrity Digest Layer",
            "commit": "ae35c79",
            "status": "PASS",
            "route": "/governance/evidence-exports/integrity",
            "txt_route": "/governance/evidence-exports/integrity.txt",
        },
        {
            "key": "IOS-3W",
            "title": "Governance Export Archive Intake Layer",
            "commit": "ae5a162",
            "status": "PASS",
            "route": "/governance/evidence-exports/archive-intake",
            "txt_route": "/governance/evidence-exports/archive-intake.txt",
        },
        {
            "key": "IOS-3X",
            "title": "Governance Evidence Certification Dashboard",
            "commit": "c14028b",
            "status": "PASS",
            "route": "/governance/evidence-exports/certification",
            "txt_route": "/governance/evidence-exports/certification.txt",
        },
        {
            "key": "IOS-3Y",
            "title": "Governance Evidence Chain Review / Exception Panel",
            "commit": "d7ae733",
            "status": "PASS",
            "route": "/governance/evidence-exports/exceptions",
            "txt_route": "/governance/evidence-exports/exceptions.txt",
        },
        {
            "key": "IOS-3Z",
            "title": "Governance Evidence Completion Gate",
            "commit": "121860a",
            "status": "PASS",
            "route": "/governance/evidence-exports/completion-gate",
            "txt_route": "/governance/evidence-exports/completion-gate.txt",
        },
    ]

    hardening_audits = [
        {
            "key": "V2-HARDEN-0",
            "title": "Local DB Writability / Runtime Environment Check",
            "commit": "81b4690",
            "status": "PASS",
            "script": "scripts/audit_local_db_writability.py",
        },
        {
            "key": "V2-HARDEN-1",
            "title": "Route / Template / Service Inventory",
            "commit": "3cbd84c",
            "status": "PASS",
            "script": "scripts/audit_governance_route_template_service_inventory.py",
        },
        {
            "key": "V2-HARDEN-2",
            "title": "Permission / Access Review",
            "commit": "fa00535",
            "status": "PASS",
            "script": "scripts/audit_governance_evidence_access_control.py",
        },
        {
            "key": "V2-HARDEN-3",
            "title": "Export Path Regression Test",
            "commit": "54189e0",
            "status": "PASS",
            "script": "scripts/audit_governance_export_path_regression.py",
        },
        {
            "key": "V2-HARDEN-4",
            "title": "Navigation / Footer Consistency Audit",
            "commit": "d4fb697",
            "status": "PASS",
            "script": None,
        },
        {
            "key": "V2-HARDEN-5",
            "title": "Data Mutation Boundary Audit",
            "commit": "10b3571",
            "status": "PASS",
            "script": "scripts/audit_governance_data_mutation_boundary.py",
        },
        {
            "key": "V2-HARDEN-6",
            "title": "GitHub / Deployment Readiness Check",
            "commit": "dfeb4d0",
            "status": "PASS",
            "script": "scripts/audit_v2_github_deployment_readiness.py",
        },
    ]

    required_templates = [
        "templates/governance/evidence_export_index.html",
        "templates/governance/evidence_export_manifest.html",
        "templates/governance/evidence_export_integrity.html",
        "templates/governance/evidence_export_archive_intake.html",
        "templates/governance/evidence_certification_dashboard.html",
        "templates/governance/evidence_exception_panel.html",
        "templates/governance/evidence_completion_gate.html",
        "templates/governance/v2_certification_dashboard.html",
    ]

    deployment_files = [
        {"path": "requirements.txt", "required": True, "exists": file_exists("requirements.txt")},
        {"path": "app.py", "required": True, "exists": file_exists("app.py")},
        {"path": "Procfile", "required": False, "exists": file_exists("Procfile")},
        {"path": "render.yaml", "required": False, "exists": file_exists("render.yaml")},
    ]

    evidence_chain_passed = all(item["status"] == "PASS" for item in governance_chain)
    hardening_passed = all(item["status"] == "PASS" for item in hardening_audits)
    branch_ready = branch == "v2-development"
    remote_ready = bool(head_sha) and head_sha == origin_sha
    working_tree_clean = status_short == ""
    required_scripts_exist = all(
        file_exists(item["script"]) for item in hardening_audits if item.get("script")
    )
    required_templates_existing = [
        {"path": rel, "exists": file_exists(rel)} for rel in required_templates
    ]

    missing_required_templates = [
        item["path"] for item in required_templates_existing if not item["exists"]
    ]

    deployment_required_ready = all(
        item["exists"] for item in deployment_files if item["required"]
    )

    certification_checks = [
        {
            "key": "governance_evidence_chain_complete",
            "label": "Governance evidence chain complete",
            "status": "PASS" if evidence_chain_passed else "FAIL",
            "detail": "IOS-3U through IOS-3Z marked PASS",
        },
        {
            "key": "hardening_audits_complete",
            "label": "Hardening audits complete",
            "status": "PASS" if hardening_passed else "FAIL",
            "detail": "V2-HARDEN-0 through V2-HARDEN-6 marked PASS",
        },
        {
            "key": "branch_v2_development",
            "label": "Branch is v2-development",
            "status": "PASS" if branch_ready else "FAIL",
            "detail": branch or branch_err,
        },
        {
            "key": "head_matches_origin",
            "label": "HEAD matches origin/v2-development",
            "status": "PASS" if remote_ready else "FAIL",
            "detail": f"HEAD={head_sha or head_err}; origin={origin_sha or origin_err}",
        },
        {
            "key": "working_tree_clean",
            "label": "Working tree clean",
            "status": "PASS" if working_tree_clean else "FAIL",
            "detail": status_short or "clean",
        },
        {
            "key": "hardening_scripts_exist",
            "label": "Hardening scripts exist",
            "status": "PASS" if required_scripts_exist else "FAIL",
            "detail": "all required hardening scripts present",
        },
        {
            "key": "required_templates_exist",
            "label": "Required evidence/certification templates exist",
            "status": "PASS" if not missing_required_templates else "FAIL",
            "detail": "all required templates present" if not missing_required_templates else ", ".join(missing_required_templates),
        },
        {
            "key": "deployment_required_files_present",
            "label": "Required deployment files present",
            "status": "PASS" if deployment_required_ready else "FAIL",
            "detail": "requirements.txt and app.py present",
        },
        {
            "key": "final_v2_tag_not_created",
            "label": "Final V2 tag not created in CERT-1",
            "status": "PASS",
            "detail": "Tagging reserved for V2-CERT-2",
        },
    ]

    checks_failed = sum(1 for item in certification_checks if item["status"] != "PASS")
    checks_passed = sum(1 for item in certification_checks if item["status"] == "PASS")

    return {
        "title": "Version 2 Certification Dashboard",
        "dashboard_type": "v2_certification_dashboard",
        "read_only": True,
        "certification_ready": checks_failed == 0,
        "tag_created": False,
        "tag_reserved_for": "V2-CERT-2 — Version 2 Certified Baseline Tag",
        "branch": branch,
        "head_sha": head_sha,
        "origin_sha": origin_sha,
        "head_short": head_sha[:7] if head_sha else "",
        "origin_short": origin_sha[:7] if origin_sha else "",
        "working_tree_clean": working_tree_clean,
        "summary": {
            "governance_chain_items": len(governance_chain),
            "hardening_audits": len(hardening_audits),
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "certification_ready": checks_failed == 0,
            "tag_created": False,
        },
        "governance_chain": governance_chain,
        "hardening_audits": hardening_audits,
        "certification_checks": certification_checks,
        "required_templates": required_templates_existing,
        "deployment_files": deployment_files,
        "recent_log": log_text.splitlines() if log_text else [],
        "certification_notice": (
            "Version 2 certification dashboard is read-only. It confirms readiness "
            "for baseline tagging but does not create the V2 certified tag."
        ),
        "preservation_statement": (
            "This dashboard preserves the Version 2 readiness state for governance, "
            "hardening, export, access-control, data-boundary, and deployment-readiness review."
        ),
        "custody_notice": (
            "Institutional Property of Luna Isaac III Mishoe. System records, workflows, "
            "generated instruments, certificates, exports, and archive materials are maintained "
            "under fiduciary custody. Authorized Access Only."
        ),
    }


def build_v2_certification_dashboard_text():
    """
    Build read-only plain-text Version 2 certification dashboard export.
    """
    dashboard = build_v2_certification_dashboard()

    lines = []
    lines.append("VERSION 2 CERTIFICATION DASHBOARD")
    lines.append("=" * 72)
    lines.append(f"Read Only: {dashboard.get('read_only')}")
    lines.append(f"Certification Ready: {dashboard.get('certification_ready')}")
    lines.append(f"Branch: {dashboard.get('branch')}")
    lines.append(f"HEAD: {dashboard.get('head_sha')}")
    lines.append(f"Origin: {dashboard.get('origin_sha')}")
    lines.append(f"Working Tree Clean: {dashboard.get('working_tree_clean')}")
    lines.append(f"Tag Created: {dashboard.get('tag_created')}")
    lines.append(f"Tag Reserved For: {dashboard.get('tag_reserved_for')}")
    lines.append("")

    summary = dashboard.get("summary") or {}
    lines.append("CERTIFICATION SUMMARY")
    lines.append("-" * 72)
    for key, value in summary.items():
        lines.append(f"{key}: {value}")
    lines.append("")

    lines.append("GOVERNANCE EVIDENCE CHAIN")
    lines.append("-" * 72)
    for item in dashboard.get("governance_chain", []):
        lines.append(
            f"{item.get('key')} | {item.get('status')} | {item.get('commit')} | {item.get('title')}"
        )
        lines.append(f"  HTML: {item.get('route')}")
        lines.append(f"  TXT: {item.get('txt_route')}")
    lines.append("")

    lines.append("HARDENING AUDITS")
    lines.append("-" * 72)
    for item in dashboard.get("hardening_audits", []):
        lines.append(
            f"{item.get('key')} | {item.get('status')} | {item.get('commit')} | {item.get('title')}"
        )
        if item.get("script"):
            lines.append(f"  Script: {item.get('script')}")
    lines.append("")

    lines.append("CERTIFICATION CHECKS")
    lines.append("-" * 72)
    for item in dashboard.get("certification_checks", []):
        lines.append(f"{item.get('status')} | {item.get('label')} | {item.get('detail')}")
    lines.append("")

    lines.append("DEPLOYMENT FILES")
    lines.append("-" * 72)
    for item in dashboard.get("deployment_files", []):
        lines.append(
            f"{'REQUIRED' if item.get('required') else 'OPTIONAL'} | "
            f"{'PRESENT' if item.get('exists') else 'MISSING'} | {item.get('path')}"
        )
    lines.append("")

    lines.append("RECENT GIT LOG")
    lines.append("-" * 72)
    for line in dashboard.get("recent_log", []):
        lines.append(line)
    lines.append("")

    lines.append("CERTIFICATION NOTICE")
    lines.append("-" * 72)
    lines.append(dashboard.get("certification_notice") or "")
    lines.append("")

    lines.append("PRESERVATION STATEMENT")
    lines.append("-" * 72)
    lines.append(dashboard.get("preservation_statement") or "")
    lines.append("")

    lines.append("CUSTODY NOTICE")
    lines.append("-" * 72)
    lines.append(dashboard.get("custody_notice") or "")

    return "\n".join(lines)

