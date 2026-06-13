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
