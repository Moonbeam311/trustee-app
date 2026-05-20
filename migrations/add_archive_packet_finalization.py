import sqlite3
from pathlib import Path

db_path = Path("trustee_app.db")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS archive_packet_finalization (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    finalization_id TEXT UNIQUE,
    property_id TEXT NOT NULL,
    trust_id TEXT,
    packet_status TEXT,
    integrity_status TEXT,
    resolution_status TEXT,
    archive_badge TEXT,
    finalized_status TEXT,
    finalized_by TEXT,
    finalized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    firm_id TEXT
)
""")

conn.commit()
conn.close()

print("SUCCESS: archive_packet_finalization table installed.")
