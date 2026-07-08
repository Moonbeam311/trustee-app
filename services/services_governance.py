from datetime import datetime
from uuid import uuid4

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


def _truthy(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "required"}


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
            approved_by TEXT,
            approved_at TEXT,
            effective_at TEXT,
            retired_at TEXT,
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
        "policy": ["policy_area", "approved_by", "approved_at", "effective_at", "retired_at"],
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

    conn.close()
    return {
        "record_type_counts": record_type_counts,
        "lifecycle_counts": [
            {"status": status, "count": count}
            for status, count in lifecycle_counts.items()
        ],
        "recent_directives": [dict(row) for row in recent_directives],
        "pending_approvals": [dict(row) for row in pending_approvals],
        "implementation_activity": [dict(row) for row in implementation_activity],
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
