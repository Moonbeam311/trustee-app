"""
V2-HARDEN-0 — Local DB Writability / Runtime Environment Check

Purpose:
- Identify the active SQLite DB path.
- Confirm parent directory exists and is writable.
- Confirm DB file exists or can be opened.
- Confirm controlled CREATE / INSERT / SELECT / DELETE / DROP lifecycle works.
- Confirm WAL/journal behavior does not fail.
- Do not mutate production governance records.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


def resolve_db_path() -> Path:
    candidates = []

    env_db = os.environ.get("DB_PATH")
    if env_db:
        candidates.append(Path(env_db))

    # Common local project defaults.
    candidates.extend(
        [
            Path("data/trustee_app.db"),
            Path("trustee_app.db"),
            Path("instance/trustee_app.db"),
            Path("app/data/trustee_app.db"),
        ]
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    # If none exist, prefer DB_PATH if set, otherwise data/trustee_app.db.
    if env_db:
        return Path(env_db).resolve()

    return Path("data/trustee_app.db").resolve()


def main() -> int:
    print("V2-HARDEN-0 LOCAL DB WRITABILITY AUDIT")
    print("=" * 50)

    db_path = resolve_db_path()
    db_parent = db_path.parent

    print(f"Resolved DB Path: {db_path}")
    print(f"DB Exists: {db_path.exists()}")
    print(f"Parent Directory: {db_parent}")
    print(f"Parent Exists: {db_parent.exists()}")

    if not db_parent.exists():
        print("FAIL: DB parent directory does not exist.")
        return 1

    print(f"Parent Writable: {os.access(db_parent, os.W_OK)}")
    if db_path.exists():
        print(f"DB File Writable: {os.access(db_path, os.W_OK)}")
        print(f"DB File Readable: {os.access(db_path, os.R_OK)}")
    else:
        print("DB File Writable: DB file does not yet exist")

    if not os.access(db_parent, os.W_OK):
        print("FAIL: DB parent directory is not writable.")
        return 1

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("PRAGMA database_list")
        dbs = cur.fetchall()
        print("PRAGMA database_list:")
        for row in dbs:
            print(dict(row))

        cur.execute("PRAGMA journal_mode")
        journal_mode = cur.fetchone()[0]
        print(f"PRAGMA journal_mode before: {journal_mode}")

        table_name = "_v2_harden0_writability_probe"
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                probe_key TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        probe_key = f"V2-HARDEN-0-{datetime.now(timezone.utc).isoformat()}"
        cur.execute(
            f"INSERT INTO {table_name} (probe_key, created_at) VALUES (?, ?)",
            (probe_key, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()

        cur.execute(f"SELECT probe_key FROM {table_name} WHERE probe_key = ?", (probe_key,))
        found = cur.fetchone()
        if not found:
            print("FAIL: Probe row was not readable after insert.")
            return 1

        cur.execute(f"DELETE FROM {table_name} WHERE probe_key = ?", (probe_key,))
        conn.commit()

        cur.execute(f"SELECT COUNT(*) FROM {table_name} WHERE probe_key = ?", (probe_key,))
        remaining = cur.fetchone()[0]
        if remaining != 0:
            print("FAIL: Probe row was not deleted.")
            return 1

        cur.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()

        cur.execute("PRAGMA integrity_check")
        integrity = cur.fetchone()[0]
        print(f"PRAGMA integrity_check: {integrity}")

        conn.close()

        if integrity.lower() != "ok":
            print("FAIL: SQLite integrity check did not return ok.")
            return 1

        print("PASS: Controlled CREATE / INSERT / SELECT / DELETE / DROP succeeded.")
        print("PASS: Local DB is writable for runtime operations.")
        return 0

    except sqlite3.OperationalError as exc:
        print(f"FAIL: sqlite3 OperationalError: {exc}")
        return 1
    except Exception as exc:
        print(f"FAIL: unexpected exception: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
