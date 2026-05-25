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
