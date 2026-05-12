import sqlite3
from pathlib import Path
import os

DB_PATH = Path(os.getenv("DB_PATH", "trustee_app.db")).resolve()

TABLES_WITH_FIRM_ID = [
    "trusts",
    "app_users",
    "audit_log",
    "transfers",
    "trust_minutes",
    "documents",
    "generated_documents",
    "media_records",
    "workspaces",
    "workspace_notes",
    "execution_tasks",
    "user_roles",
    "fiduciaries",
    "properties",
    "accounts",
    "beneficiaries",
    "distributions",
    "instruments",
    "ledger_entries",
]

def table_exists(cur, table):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None

def column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    return column in [row[1] for row in cur.fetchall()]

def add_column_if_missing(cur, table, column, column_type="TEXT"):
    if not table_exists(cur, table):
        print(f"SKIP missing table: {table}")
        return
    if column_exists(cur, table, column):
        print(f"SKIP existing column: {table}.{column}")
        return
    cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
    print(f"ADDED column: {table}.{column}")

def main():
    print(f"Running hosted firm-scope migration on: {DB_PATH}")

    if not DB_PATH.exists():
        raise SystemExit(f"ERROR: database file not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    for table in TABLES_WITH_FIRM_ID:
        add_column_if_missing(cur, table, "firm_id", "TEXT")

    conn.commit()

    # Default legacy hosted rows to FIRM-001.
    for table in TABLES_WITH_FIRM_ID:
        if not table_exists(cur, table) or not column_exists(cur, table, "firm_id"):
            continue
        cur.execute(f"""
            UPDATE {table}
            SET firm_id = 'FIRM-001'
            WHERE firm_id IS NULL OR TRIM(firm_id) = ''
        """)
        print(f"{table}: defaulted rows to FIRM-001:", cur.rowcount)

    conn.commit()

    # Ensure FIRM-002 test/admin users can exist if app_users table exists.
    if table_exists(cur, "app_users"):
        cur.execute("PRAGMA table_info(app_users)")
        cols = [r["name"] for r in cur.fetchall()]
        if "firm_id" in cols:
            cur.execute("""
                UPDATE app_users
                SET firm_id = 'FIRM-002'
                WHERE LOWER(username) IN ('admin123', 'testadmin1')
            """)
            print("app_users: assigned admin123/testadmin1 to FIRM-002:", cur.rowcount)

    conn.commit()

    print("\nVERIFY COUNTS BY FIRM")
    for table in TABLES_WITH_FIRM_ID:
        if not table_exists(cur, table) or not column_exists(cur, table, "firm_id"):
            continue
        print(f"\n--- {table} ---")
        cur.execute(f"""
            SELECT COALESCE(firm_id, 'NULL') AS firm_id, COUNT(*) AS count
            FROM {table}
            GROUP BY COALESCE(firm_id, 'NULL')
            ORDER BY firm_id
        """)
        for row in cur.fetchall():
            print(dict(row))

    conn.close()
    print("\nDONE")

if __name__ == "__main__":
    main()
