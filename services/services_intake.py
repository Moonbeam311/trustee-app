from datetime import datetime
from database.db import get_connection, get_current_firm_id


INTAKE_LANES = {
    "new_planning": {
        "label": "I want to start organizing my estate, trust, or family plan.",
        "posture": "planning",
        "default_depth": "standard",
        "risk_posture": "unknown",
        "professional_review_recommended": False,
        "automation_limits": "standard",
        "next_screen": "universal_profile",
    },
    "document_review": {
        "label": "I already have documents and want them reviewed or updated.",
        "posture": "review",
        "default_depth": "document_focused",
        "risk_posture": "unknown",
        "professional_review_recommended": False,
        "automation_limits": "standard",
        "next_screen": "document_inventory",
    },
    "administration": {
        "label": "I am responsible for a trust, estate, or fiduciary role.",
        "posture": "fiduciary",
        "default_depth": "administrative",
        "risk_posture": "unknown",
        "professional_review_recommended": False,
        "automation_limits": "standard",
        "next_screen": "fiduciary_role_check",
    },
    "asset_funding": {
        "label": "I want to organize, transfer, or fund assets into a trust or structure.",
        "posture": "execution_preparation",
        "default_depth": "asset_focused",
        "risk_posture": "unknown",
        "professional_review_recommended": False,
        "automation_limits": "standard",
        "next_screen": "asset_snapshot",
    },
    "business_continuity": {
        "label": "I own or manage a business and want continuity or protection planning.",
        "posture": "business_owner",
        "default_depth": "business_focused",
        "risk_posture": "unknown",
        "professional_review_recommended": False,
        "automation_limits": "standard",
        "next_screen": "business_profile",
    },
    "urgent_triage": {
        "label": "Something urgent or complicated is happening.",
        "posture": "crisis_or_pressure",
        "default_depth": "triage",
        "risk_posture": "elevated",
        "professional_review_recommended": True,
        "automation_limits": "high",
        "next_screen": "triage_precheck",
    },
    "education": {
        "label": "I am just learning and want guidance.",
        "posture": "exploratory",
        "default_depth": "light",
        "risk_posture": "low",
        "professional_review_recommended": False,
        "automation_limits": "low",
        "next_screen": "guided_orientation",
    },
}


def ensure_intake_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS intake_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intake_id TEXT UNIQUE NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            client_id TEXT,
            intake_lane TEXT NOT NULL,
            user_posture TEXT,
            default_depth TEXT,
            risk_posture TEXT,
            professional_review_recommended INTEGER DEFAULT 0,
            automation_limits TEXT,
            next_screen TEXT,
            status TEXT DEFAULT 'lane_selected',
            created_at TEXT,
            updated_at TEXT,
            completed_at TEXT,
            created_by TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS intake_lane_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intake_id TEXT NOT NULL,
            firm_id TEXT DEFAULT 'FIRM-001',
            event_type TEXT,
            event_label TEXT,
            event_value TEXT,
            created_at TEXT,
            created_by TEXT
        )
    """)

    conn.commit()
    conn.close()


def get_intake_lanes():
    return INTAKE_LANES


def get_lane_config(lane_key):
    return INTAKE_LANES.get(lane_key)


def _next_intake_id(cur):
    cur.execute("SELECT intake_id FROM intake_sessions ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if not row:
        return "INTAKE-0001"

    last = row["intake_id"] if hasattr(row, "keys") else row[0]
    try:
        number = int(str(last).split("-")[-1])
    except Exception:
        number = 0
    return f"INTAKE-{number + 1:04d}"


def create_intake_session(lane_key, client_id=None, created_by=None):
    ensure_intake_tables()

    lane = get_lane_config(lane_key)
    if not lane:
        raise ValueError(f"Invalid intake lane: {lane_key}")

    now = datetime.utcnow().isoformat(timespec="seconds")
    firm_id = get_current_firm_id()

    conn = get_connection()
    conn.row_factory = None
    cur = conn.cursor()

    intake_id = _next_intake_id(cur)

    cur.execute("""
        INSERT INTO intake_sessions (
            intake_id, firm_id, client_id, intake_lane, user_posture,
            default_depth, risk_posture, professional_review_recommended,
            automation_limits, next_screen, status, created_at, updated_at,
            created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        intake_id,
        firm_id,
        client_id,
        lane_key,
        lane["posture"],
        lane["default_depth"],
        lane["risk_posture"],
        1 if lane["professional_review_recommended"] else 0,
        lane["automation_limits"],
        lane["next_screen"],
        "lane_selected",
        now,
        now,
        created_by,
    ))

    cur.execute("""
        INSERT INTO intake_lane_events (
            intake_id, firm_id, event_type, event_label, event_value,
            created_at, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        intake_id,
        firm_id,
        "lane_selected",
        "Intake lane selected",
        lane_key,
        now,
        created_by,
    ))

    conn.commit()
    conn.close()

    return {
        "intake_id": intake_id,
        "intake_lane": lane_key,
        "user_posture": lane["posture"],
        "default_depth": lane["default_depth"],
        "risk_posture": lane["risk_posture"],
        "professional_review_recommended": lane["professional_review_recommended"],
        "automation_limits": lane["automation_limits"],
        "next_screen": lane["next_screen"],
    }
