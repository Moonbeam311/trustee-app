import sqlite3
from pathlib import Path

db_path = Path("trustee_app.db")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS continuity_custody_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    custody_event_id TEXT UNIQUE,
    property_id TEXT NOT NULL,
    trust_id TEXT,
    event_date TEXT,
    custody_action TEXT,
    from_party TEXT,
    to_party TEXT,
    acting_capacity TEXT,
    location_reference TEXT,
    supporting_document_reference TEXT,
    notes TEXT,
    recorded_by TEXT,
    firm_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("SUCCESS: AC-1 continuity custody log table installed.")
