from datetime import datetime
from database.db import get_connection, get_current_firm_id

def ensure_matter_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS matters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matter_id TEXT UNIQUE NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            title TEXT NOT NULL,
            matter_type TEXT NOT NULL,
            status TEXT DEFAULT 'Open',
            priority TEXT DEFAULT 'Normal',
            jurisdiction TEXT,
            lead_fiduciary TEXT,
            governance_state TEXT DEFAULT 'Intake',
            risk_level TEXT DEFAULT 'Unrated',
            archive_status TEXT DEFAULT 'Not Archived',
            purpose TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS matter_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            matter_id TEXT NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            event_type TEXT NOT NULL,
            actor TEXT,
            authority_basis TEXT,
            description TEXT NOT NULL,
            linked_record_type TEXT,
            linked_record_id TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS matter_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            relationship_id TEXT NOT NULL UNIQUE,
            matter_id TEXT NOT NULL,
            firm_id TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            linked_record_id TEXT NOT NULL,
            display_label TEXT NOT NULL,
            purpose_basis TEXT,
            created_by TEXT,
            status TEXT NOT NULL DEFAULT 'Active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_matter_relationships_matter_firm
        ON matter_relationships (matter_id, firm_id)
        """
    )

    cur.execute("PRAGMA table_info(matter_relationships)")
    relationship_columns = {
        row[1] for row in cur.fetchall()
    }

    if "verification_status" not in relationship_columns:
        cur.execute(
            """
            ALTER TABLE matter_relationships
            ADD COLUMN verification_status TEXT
            NOT NULL DEFAULT 'Unverified'
            """
        )

    if "verification_basis" not in relationship_columns:
        cur.execute(
            """
            ALTER TABLE matter_relationships
            ADD COLUMN verification_basis TEXT
            """
        )

    if "verified_by" not in relationship_columns:
        cur.execute(
            """
            ALTER TABLE matter_relationships
            ADD COLUMN verified_by TEXT
            """
        )

    if "verified_at" not in relationship_columns:
        cur.execute(
            """
            ALTER TABLE matter_relationships
            ADD COLUMN verified_at TEXT
            """
        )

    cur.execute("PRAGMA table_info(matter_relationships)")
    relationship_columns = {
        row[1] for row in cur.fetchall()
    }

    if "link_validation_status" not in relationship_columns:
        cur.execute(
            """
            ALTER TABLE matter_relationships
            ADD COLUMN link_validation_status TEXT
            NOT NULL DEFAULT 'Not Checked'
            """
        )

    if "link_validation_message" not in relationship_columns:
        cur.execute(
            """
            ALTER TABLE matter_relationships
            ADD COLUMN link_validation_message TEXT
            """
        )

    if "link_validated_by" not in relationship_columns:
        cur.execute(
            """
            ALTER TABLE matter_relationships
            ADD COLUMN link_validated_by TEXT
            """
        )

    if "link_validated_at" not in relationship_columns:
        cur.execute(
            """
            ALTER TABLE matter_relationships
            ADD COLUMN link_validated_at TEXT
            """
        )

    conn.commit()
    conn.close()

def _next_id(prefix, table, column):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0] + 1
    conn.close()
    return f"{prefix}-{count:06d}"

def create_matter(data):
    ensure_matter_tables()
    now = datetime.utcnow().isoformat(timespec="seconds")
    matter_id = _next_id("MAT", "matters", "matter_id")
    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO matters (
            matter_id, firm_id, title, matter_type, status, priority,
            jurisdiction, lead_fiduciary, governance_state, risk_level,
            archive_status, purpose, notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        matter_id,
        firm_id,
        data.get("title", "").strip(),
        data.get("matter_type", "").strip(),
        data.get("status", "Open"),
        data.get("priority", "Normal"),
        data.get("jurisdiction", "").strip(),
        data.get("lead_fiduciary", "").strip(),
        data.get("governance_state", "Intake"),
        data.get("risk_level", "Unrated"),
        data.get("archive_status", "Not Archived"),
        data.get("purpose", "").strip(),
        data.get("notes", "").strip(),
        now,
        now
    ))
    conn.commit()
    conn.close()

    add_matter_event(
        matter_id=matter_id,
        event_type="Matter Created",
        actor=data.get("lead_fiduciary", ""),
        authority_basis="Initial institutional intake",
        description=f"Matter created: {data.get('title', '').strip()}",
    )

    return matter_id

def add_matter_event(matter_id, event_type, actor="", authority_basis="", description="", linked_record_type="", linked_record_id=""):
    ensure_matter_tables()
    now = datetime.utcnow().isoformat(timespec="seconds")
    event_id = _next_id("MEV", "matter_events", "event_id")
    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO matter_events (
            event_id, matter_id, firm_id, event_type, actor, authority_basis,
            description, linked_record_type, linked_record_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id, matter_id, firm_id, event_type, actor, authority_basis,
        description, linked_record_type, linked_record_id, now
    ))

    cur.execute("UPDATE matters SET updated_at = ? WHERE matter_id = ? AND firm_id = ?", (now, matter_id, firm_id))
    conn.commit()
    conn.close()
    return event_id

def list_matters():
    ensure_matter_tables()
    firm_id = get_current_firm_id()
    conn = get_connection()
    conn.row_factory = None
    cur = conn.cursor()
    cur.execute("""
        SELECT matter_id, title, matter_type, status, priority, governance_state, risk_level, archive_status, updated_at
        FROM matters
        WHERE firm_id = ?
        ORDER BY updated_at DESC
    """, (firm_id,))
    rows = cur.fetchall()
    conn.close()
    return rows



def update_governance_state(matter_id, new_state, actor="", authority_basis=""):
    ensure_matter_tables()

    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT governance_state FROM matters WHERE matter_id = ? AND firm_id = ?",
        (matter_id, firm_id)
    )

    row = cur.fetchone()

    if not row:
        conn.close()
        return False

    old_state = row[0]

    cur.execute(
        """
        UPDATE matters
        SET governance_state = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE matter_id = ?
        AND firm_id = ?
        """,
        (
            new_state,
            matter_id,
            firm_id
        )
    )

    conn.commit()
    conn.close()

    add_matter_event(
        matter_id=matter_id,
        event_type="Governance State Changed",
        actor=actor,
        authority_basis=authority_basis,
        description=f"Governance State: {old_state} → {new_state}"
    )

    return True




def update_matter_risk(
    matter_id,
    new_risk,
    assessment_note,
    actor="",
    authority_basis=""
):
    ensure_matter_tables()

    allowed_risks = {
        "Unrated",
        "Low",
        "Moderate",
        "High",
        "Critical",
    }

    new_risk = (new_risk or "").strip()
    assessment_note = (assessment_note or "").strip()

    if new_risk not in allowed_risks:
        return False, "Invalid risk level."

    if not assessment_note:
        return False, "Risk assessment note is required."

    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT risk_level
        FROM matters
        WHERE matter_id = ?
          AND firm_id = ?
        """,
        (matter_id, firm_id)
    )

    row = cur.fetchone()

    if not row:
        conn.close()
        return False, "Matter not found."

    old_risk = row[0] or "Unrated"

    if old_risk == new_risk:
        conn.close()
        return False, "Select a different risk level."

    cur.execute(
        """
        UPDATE matters
        SET risk_level = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE matter_id = ?
          AND firm_id = ?
        """,
        (new_risk, matter_id, firm_id)
    )

    if cur.rowcount != 1:
        conn.rollback()
        conn.close()
        return False, "Risk update failed."

    conn.commit()
    conn.close()

    add_matter_event(
        matter_id=matter_id,
        event_type="Risk Level Changed",
        actor=actor or "System",
        authority_basis=authority_basis or "Matter Risk Assessment",
        description=(
            f"Risk Level: {old_risk} → {new_risk}. "
            f"Assessment: {assessment_note}"
        ),
        linked_record_type="matter",
        linked_record_id=matter_id,
    )

    return True, new_risk




def _next_relationship_id():
    ensure_matter_tables()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT relationship_id
        FROM matter_relationships
        ORDER BY id DESC
        LIMIT 1
        """
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        return "MRL-000001"

    try:
        next_number = int(str(row[0]).split("-")[-1]) + 1
    except (TypeError, ValueError):
        next_number = 1

    return f"MRL-{next_number:06d}"


def add_matter_relationship(
    matter_id,
    relationship_type,
    linked_record_id,
    display_label,
    purpose_basis="",
    created_by="",
    status="Active",
):
    ensure_matter_tables()

    allowed_types = {
        "Trust",
        "Person",
        "Asset",
        "Document",
        "Transfer",
        "Media",
        "Minute",
        "Intake Record",
        "Other",
    }

    relationship_type = (relationship_type or "").strip()
    linked_record_id = (linked_record_id or "").strip()
    display_label = (display_label or "").strip()
    purpose_basis = (purpose_basis or "").strip()
    created_by = (created_by or "").strip() or "System"
    status = (status or "").strip() or "Active"

    if relationship_type not in allowed_types:
        return False, "Invalid relationship type."

    if not linked_record_id:
        return False, "Linked record ID is required."

    if not display_label:
        return False, "Display label is required."

    if status not in {"Active", "Inactive"}:
        return False, "Invalid relationship status."

    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 1
        FROM matters
        WHERE matter_id = ?
          AND firm_id = ?
        """,
        (matter_id, firm_id)
    )

    if not cur.fetchone():
        conn.close()
        return False, "Matter not found."

    cur.execute(
        """
        SELECT relationship_id
        FROM matter_relationships
        WHERE matter_id = ?
          AND firm_id = ?
          AND relationship_type = ?
          AND linked_record_id = ?
          AND status = 'Active'
        """,
        (
            matter_id,
            firm_id,
            relationship_type,
            linked_record_id,
        )
    )

    if cur.fetchone():
        conn.close()
        return False, "An active relationship to this record already exists."

    relationship_id = _next_relationship_id()

    cur.execute(
        """
        INSERT INTO matter_relationships (
            relationship_id,
            matter_id,
            firm_id,
            relationship_type,
            linked_record_id,
            display_label,
            purpose_basis,
            created_by,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            relationship_id,
            matter_id,
            firm_id,
            relationship_type,
            linked_record_id,
            display_label,
            purpose_basis,
            created_by,
            status,
        )
    )

    conn.commit()
    conn.close()

    add_matter_event(
        matter_id=matter_id,
        event_type="Relationship Added",
        actor=created_by,
        authority_basis=purpose_basis or "Matter Relationship Review",
        description=(
            f"{relationship_type} relationship added: "
            f"{display_label} ({linked_record_id})"
        ),
        linked_record_type=relationship_type.lower(),
        linked_record_id=linked_record_id,
    )

    return True, relationship_id




def update_matter_relationship_status(
    matter_id,
    relationship_id,
    new_status,
    reason,
    actor="",
    authority_basis="Matter Relationship Review",
):
    ensure_matter_tables()

    new_status = (new_status or "").strip()
    reason = (reason or "").strip()
    actor = (actor or "").strip() or "System"
    authority_basis = (
        (authority_basis or "").strip()
        or "Matter Relationship Review"
    )

    if new_status not in {"Active", "Inactive"}:
        return False, "Invalid relationship status."

    if not reason:
        return False, "Status-change reason is required."

    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            relationship_type,
            linked_record_id,
            display_label,
            status
        FROM matter_relationships
        WHERE relationship_id = ?
          AND matter_id = ?
          AND firm_id = ?
        """,
        (
            relationship_id,
            matter_id,
            firm_id,
        )
    )

    row = cur.fetchone()

    if not row:
        conn.close()
        return False, "Matter relationship not found."

    relationship_type = row[0]
    linked_record_id = row[1]
    display_label = row[2]
    old_status = row[3] or "Active"

    if old_status == new_status:
        conn.close()
        return False, f"Relationship is already {new_status}."

    cur.execute(
        """
        UPDATE matter_relationships
        SET status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE relationship_id = ?
          AND matter_id = ?
          AND firm_id = ?
        """,
        (
            new_status,
            relationship_id,
            matter_id,
            firm_id,
        )
    )

    if cur.rowcount != 1:
        conn.rollback()
        conn.close()
        return False, "Relationship status update failed."

    conn.commit()
    conn.close()

    event_type = (
        "Relationship Reactivated"
        if new_status == "Active"
        else "Relationship Deactivated"
    )

    add_matter_event(
        matter_id=matter_id,
        event_type=event_type,
        actor=actor,
        authority_basis=authority_basis,
        description=(
            f"{relationship_type} relationship "
            f"{relationship_id} changed from "
            f"{old_status} → {new_status}: "
            f"{display_label} ({linked_record_id}). "
            f"Reason: {reason}"
        ),
        linked_record_type=relationship_type.lower(),
        linked_record_id=linked_record_id,
    )

    return True, new_status




def get_matter_relationship(matter_id, relationship_id):
    ensure_matter_tables()

    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            relationship_id,
            matter_id,
            relationship_type,
            linked_record_id,
            display_label,
            purpose_basis,
            created_by,
            status,
            created_at,
            updated_at,
            verification_status,
            verification_basis,
            verified_by,
            verified_at,
            link_validation_status,
            link_validation_message,
            link_validated_by,
            link_validated_at
        FROM matter_relationships
        WHERE relationship_id = ?
          AND matter_id = ?
          AND firm_id = ?
        """,
        (
            relationship_id,
            matter_id,
            firm_id,
        )
    )

    row = cur.fetchone()
    conn.close()
    return row


def update_matter_relationship_verification(
    matter_id,
    relationship_id,
    verification_status,
    verification_basis,
    actor="",
):
    ensure_matter_tables()

    allowed_statuses = {
        "Unverified",
        "Pending",
        "Verified",
        "Rejected",
    }

    verification_status = (
        verification_status or ""
    ).strip()

    verification_basis = (
        verification_basis or ""
    ).strip()

    actor = (actor or "").strip() or "System"

    if verification_status not in allowed_statuses:
        return False, "Invalid verification status."

    if not verification_basis:
        return False, "Verification basis is required."

    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            relationship_type,
            linked_record_id,
            display_label,
            verification_status
        FROM matter_relationships
        WHERE relationship_id = ?
          AND matter_id = ?
          AND firm_id = ?
        """,
        (
            relationship_id,
            matter_id,
            firm_id,
        )
    )

    row = cur.fetchone()

    if not row:
        conn.close()
        return False, "Matter relationship not found."

    relationship_type = row[0]
    linked_record_id = row[1]
    display_label = row[2]
    old_status = row[3] or "Unverified"

    if old_status == verification_status:
        conn.close()
        return False, (
            f"Verification status is already "
            f"{verification_status}."
        )

    verified_at_value = (
        "CURRENT_TIMESTAMP"
        if verification_status in {"Verified", "Rejected"}
        else "NULL"
    )

    cur.execute(
        f"""
        UPDATE matter_relationships
        SET verification_status = ?,
            verification_basis = ?,
            verified_by = ?,
            verified_at = {verified_at_value},
            updated_at = CURRENT_TIMESTAMP
        WHERE relationship_id = ?
          AND matter_id = ?
          AND firm_id = ?
        """,
        (
            verification_status,
            verification_basis,
            actor,
            relationship_id,
            matter_id,
            firm_id,
        )
    )

    if cur.rowcount != 1:
        conn.rollback()
        conn.close()
        return False, "Verification update failed."

    conn.commit()
    conn.close()

    add_matter_event(
        matter_id=matter_id,
        event_type="Relationship Verification Changed",
        actor=actor,
        authority_basis="Relationship Verification Review",
        description=(
            f"{relationship_type} relationship "
            f"{relationship_id} verification changed "
            f"from {old_status} → {verification_status}: "
            f"{display_label} ({linked_record_id}). "
            f"Basis: {verification_basis}"
        ),
        linked_record_type=relationship_type.lower(),
        linked_record_id=linked_record_id,
    )

    return True, verification_status




def validate_matter_relationship_link(
    matter_id,
    relationship_id,
    actor="",
):
    ensure_matter_tables()

    actor = (actor or "").strip() or "System"
    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            relationship_type,
            linked_record_id,
            display_label,
            verification_status
        FROM matter_relationships
        WHERE relationship_id = ?
          AND matter_id = ?
          AND firm_id = ?
        """,
        (
            relationship_id,
            matter_id,
            firm_id,
        )
    )

    row = cur.fetchone()

    if not row:
        conn.close()
        return False, "Matter relationship not found.", None

    relationship_type = row[0]
    linked_record_id = row[1]
    display_label = row[2]
    verification_status = row[3] or "Unverified"

    validation_map = {
        "Trust": ("trusts", "trust_id"),
        "Document": ("documents", "document_id"),
        "Transfer": ("transfers", "transfer_id"),
        "Media": ("media_records", "media_id"),
        "Minute": ("trust_minutes", "minute_id"),
        "Intake Record": ("intake_sessions", "intake_id"),
    }

    if relationship_type not in validation_map:
        validation_status = "Unsupported"
        validation_message = (
            f"No direct system-record validator is configured "
            f"for relationship type {relationship_type}."
        )
    else:
        table_name, id_column = validation_map[relationship_type]

        cur.execute(
            f"""
            SELECT 1
            FROM {table_name}
            WHERE {id_column} = ?
              AND firm_id = ?
            LIMIT 1
            """,
            (
                linked_record_id,
                firm_id,
            )
        )

        exists = cur.fetchone() is not None

        if exists:
            validation_status = "Found"
            validation_message = (
                f"{relationship_type} record "
                f"{linked_record_id} exists in the active firm."
            )
        else:
            validation_status = "Missing"
            validation_message = (
                f"{relationship_type} record "
                f"{linked_record_id} was not found in the active firm."
            )

    cur.execute(
        """
        UPDATE matter_relationships
        SET link_validation_status = ?,
            link_validation_message = ?,
            link_validated_by = ?,
            link_validated_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE relationship_id = ?
          AND matter_id = ?
          AND firm_id = ?
        """,
        (
            validation_status,
            validation_message,
            actor,
            relationship_id,
            matter_id,
            firm_id,
        )
    )

    conn.commit()
    conn.close()

    add_matter_event(
        matter_id=matter_id,
        event_type="Linked Record Validation",
        actor=actor,
        authority_basis="Linked Record Validation Review",
        description=(
            f"{relationship_type} relationship "
            f"{relationship_id} link validation: "
            f"{validation_status}. "
            f"{validation_message} "
            f"Verification status remains "
            f"{verification_status}."
        ),
        linked_record_type=relationship_type.lower(),
        linked_record_id=linked_record_id,
    )

    return True, validation_status, validation_message


def list_matter_relationships(matter_id):
    ensure_matter_tables()

    firm_id = get_current_firm_id()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            relationship_id,
            relationship_type,
            linked_record_id,
            display_label,
            purpose_basis,
            created_by,
            status,
            created_at,
            verification_status
        FROM matter_relationships
        WHERE matter_id = ?
          AND firm_id = ?
        ORDER BY id DESC
        """,
        (matter_id, firm_id)
    )

    rows = cur.fetchall()
    conn.close()
    return rows


def get_matter(matter_id):
    ensure_matter_tables()
    firm_id = get_current_firm_id()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM matters WHERE matter_id = ? AND firm_id = ?", (matter_id, firm_id))
    matter = cur.fetchone()
    cur.execute("""
        SELECT event_id, event_type, actor, authority_basis, description, linked_record_type, linked_record_id, created_at
        FROM matter_events
        WHERE matter_id = ? AND firm_id = ?
        ORDER BY created_at ASC
    """, (matter_id, firm_id))
    events = cur.fetchall()
    conn.close()
    return matter, events
