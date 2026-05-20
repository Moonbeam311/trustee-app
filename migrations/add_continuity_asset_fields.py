import sqlite3
from pathlib import Path

db_path = Path("trustee_app.db")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# ===================================================
# PROPERTY / ASSET CONTINUITY FIELDS
# Target table: properties
# ===================================================

target_table = "properties"

cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
    (target_table,)
)

if not cur.fetchone():
    raise RuntimeError(f"Required table not found: {target_table}")

fields = [
    ("continuity_classification", "TEXT"),
    ("custody_classification", "TEXT"),
    ("continuity_priority", "INTEGER DEFAULT 0"),
    ("heritage_significance", "TEXT"),
    ("preservation_requirements", "TEXT"),
    ("restricted_access_level", "TEXT"),
    ("lineage_association", "TEXT"),
    ("memorial_status", "INTEGER DEFAULT 0"),
    ("sacred_status", "INTEGER DEFAULT 0"),
    ("continuity_notes", "TEXT")
]

cur.execute(f"PRAGMA table_info({target_table})")
existing = [row[1] for row in cur.fetchall()]

for field_name, field_type in fields:
    if field_name in existing:
        print(f"SKIP: {field_name} already exists.")
        continue

    cur.execute(
        f"ALTER TABLE {target_table} ADD COLUMN {field_name} {field_type}"
    )

    print(f"ADDED: {field_name}")

conn.commit()
conn.close()

print("SUCCESS: AC-1 continuity property fields installed.")
