import sqlite3
from pathlib import Path

db_path = Path("trustee_app.db")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS trust_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id TEXT UNIQUE,
    title TEXT NOT NULL,
    category TEXT,
    article_type TEXT,
    content TEXT NOT NULL,
    is_required INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS trust_article_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trust_id TEXT NOT NULL,
    article_id TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS trust_template_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code TEXT UNIQUE,
    template_name TEXT NOT NULL,
    description TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS trust_article_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id TEXT NOT NULL,
    condition_key TEXT,
    condition_operator TEXT,
    condition_value TEXT
)
""")

conn.commit()
conn.close()

print("SUCCESS: ARE-1 tables created.")
