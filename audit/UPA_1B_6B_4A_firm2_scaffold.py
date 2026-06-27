from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

print("=== UPA-1B-6B-4A — FIRM 2 ISOLATED RUNTIME PROFILE SCAFFOLD ===")

ROOT = Path(".").resolve()
AUDIT_DIR = ROOT / "audit"
LIVE_DB = ROOT / "trustee_app.db"

INSTANCE_ROOT = ROOT / "instances" / "firm2"
DATA_DIR = INSTANCE_ROOT / "data"
UPLOAD_DIR = INSTANCE_ROOT / "uploads"
EXPORT_DIR = INSTANCE_ROOT / "exports"
ARCHIVE_DIR = INSTANCE_ROOT / "archives"
BACKUP_DIR = INSTANCE_ROOT / "backups"
GENERATED_DIR = INSTANCE_ROOT / "generated"
EVIDENCE_DIR = INSTANCE_ROOT / "evidence"
TEMP_DIR = INSTANCE_ROOT / "tmp"

FIRM2_DB = DATA_DIR / "trustee_app_firm2.db"
ENV_FILE = INSTANCE_ROOT / ".env.firm2.local"
LAUNCHER = ROOT / "run_firm2.sh"
PROFILE_README = INSTANCE_ROOT / "README.md"

AUDIT_DIR.mkdir(exist_ok=True)

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
JSON_PATH = AUDIT_DIR / f"UPA-1B-6B-4A_firm2_profile_scaffold_{STAMP}.json"
MD_PATH = AUDIT_DIR / f"UPA-1B-6B-4A_firm2_profile_scaffold_{STAMP}.md"

if not LIVE_DB.exists():
    raise SystemExit(f"ERROR: Live database not found: {LIVE_DB}")

def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() or result.stderr.strip()

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def sqlite_backup(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        raise SystemExit(
            "ERROR: Firm 2 candidate database already exists. "
            "This script will not overwrite it automatically:\n"
            f"{destination}"
        )

    source_conn = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    destination_conn = sqlite3.connect(destination)

    try:
        source_conn.backup(destination_conn)
        destination_conn.commit()
    finally:
        destination_conn.close()
        source_conn.close()

def qident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'

def table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [
        row[1]
        for row in conn.execute(
            f"PRAGMA table_info({qident(table)})"
        ).fetchall()
    ]

def table_foreign_keys(
    conn: sqlite3.Connection,
    table: str,
) -> list[dict[str, Any]]:
    return [
        {
            "id": row[0],
            "sequence": row[1],
            "parent_table": row[2],
            "from_column": row[3],
            "to_column": row[4],
            "on_update": row[5],
            "on_delete": row[6],
        }
        for row in conn.execute(
            f"PRAGMA foreign_key_list({qident(table)})"
        ).fetchall()
    ]

def inspect_database(path: Path) -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    tables = [
        row[0]
        for row in conn.execute(
            '''
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            '''
        ).fetchall()
    ]

    table_inventory = []
    firm_totals = Counter()
    null_firm_total = 0
    scoped_tables = []
    unscoped_tables = []
    dependent_unscoped_tables = []
    standalone_unscoped_tables = []

    for table in tables:
        columns = table_columns(conn, table)
        foreign_keys = table_foreign_keys(conn, table)
        row_count = conn.execute(
            f"SELECT COUNT(*) FROM {qident(table)}"
        ).fetchone()[0]

        has_firm_id = "firm_id" in columns
        firm_counts = {}

        if has_firm_id:
            scoped_tables.append(table)

            rows = conn.execute(
                f'''
                SELECT firm_id, COUNT(*) AS row_count
                FROM {qident(table)}
                GROUP BY firm_id
                '''
            ).fetchall()

            for row in rows:
                value = row["firm_id"]
                count = int(row["row_count"])

                if value is None or not str(value).strip():
                    null_firm_total += count
                    firm_counts["[NULL]"] = count
                else:
                    firm = str(value).strip()
                    firm_counts[firm] = count
                    firm_totals[firm] += count
        else:
            unscoped_tables.append(table)

            if foreign_keys:
                dependent_unscoped_tables.append(table)
            else:
                standalone_unscoped_tables.append(table)

        table_inventory.append(
            {
                "table": table,
                "row_count": row_count,
                "columns": columns,
                "has_firm_id": has_firm_id,
                "firm_counts": firm_counts,
                "foreign_keys": foreign_keys,
            }
        )

    conn.close()

    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "tables": len(tables),
        "table_inventory": table_inventory,
        "scoped_tables": scoped_tables,
        "unscoped_tables": unscoped_tables,
        "dependent_unscoped_tables": dependent_unscoped_tables,
        "standalone_unscoped_tables": standalone_unscoped_tables,
        "firm_totals": dict(firm_totals),
        "null_firm_rows": null_firm_total,
    }

live_hash_before = sha256_file(LIVE_DB)

for directory in [
    INSTANCE_ROOT,
    DATA_DIR,
    UPLOAD_DIR,
    EXPORT_DIR,
    ARCHIVE_DIR,
    BACKUP_DIR,
    GENERATED_DIR,
    EVIDENCE_DIR,
    TEMP_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)

sqlite_backup(LIVE_DB, FIRM2_DB)

firm2_secret = secrets.token_urlsafe(48)

env_text = "\n".join(
    [
        "# Firm 2 standalone testing profile",
        "# Local-only configuration. Do not commit this file.",
        "",
        "APP_INSTANCE=FIRM2_TEST",
        "INSTANCE_ID=firm2",
        "FIRM_ID=FIRM-002",
        "DEFAULT_FIRM_ID=FIRM-002",
        f"DB_PATH={FIRM2_DB.as_posix()}",
        "SESSION_COOKIE_NAME=trustee_firm2_session",
        f"SECRET_KEY={firm2_secret}",
        f"UPLOAD_FOLDER={UPLOAD_DIR.as_posix()}",
        f"EXPORT_FOLDER={EXPORT_DIR.as_posix()}",
        f"ARCHIVE_FOLDER={ARCHIVE_DIR.as_posix()}",
        f"BACKUP_FOLDER={BACKUP_DIR.as_posix()}",
        f"GENERATED_FOLDER={GENERATED_DIR.as_posix()}",
        f"EVIDENCE_FOLDER={EVIDENCE_DIR.as_posix()}",
        f"TEMP_FOLDER={TEMP_DIR.as_posix()}",
        "PORT=5002",
        "FLASK_ENV=development",
        "",
    ]
)

ENV_FILE.write_text(env_text, encoding="utf-8")

launcher_text = '''#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PROFILE="instances/firm2/.env.firm2.local"

if [[ ! -f "$PROFILE" ]]; then
    echo "ERROR: Firm 2 profile not found: $PROFILE"
    exit 1
fi

set -a
source "$PROFILE"
set +a

echo "=== FIRM 2 TESTING INSTANCE ==="
echo "APP_INSTANCE=$APP_INSTANCE"
echo "FIRM_ID=$FIRM_ID"
echo "DB_PATH=$DB_PATH"
echo "SESSION_COOKIE_NAME=$SESSION_COOKIE_NAME"
echo "UPLOAD_FOLDER=$UPLOAD_FOLDER"
echo "EXPORT_FOLDER=$EXPORT_FOLDER"
echo "ARCHIVE_FOLDER=$ARCHIVE_FOLDER"
echo "PORT=$PORT"
echo

python - <<'CHECK'
import os
from pathlib import Path

db_path = Path(os.environ["DB_PATH"]).resolve()

print("Resolved DB_PATH:", db_path)
print("Database exists:", db_path.exists())

if os.environ.get("FIRM_ID") != "FIRM-002":
    raise SystemExit(
        "ERROR: Firm 2 launcher is not bound to FIRM-002."
    )

if not db_path.exists():
    raise SystemExit(
        "ERROR: Firm 2 database does not exist."
    )
CHECK

python app.py
'''

LAUNCHER.write_text(launcher_text, encoding="utf-8")

PROFILE_README.write_text(
    '''# Firm 2 Testing Instance

This directory is the isolated testing profile for `FIRM-002`.

## Governing rules

- Firm 2 receives new development and migration testing first.
- Firm 1 remains the protected baseline.
- This instance must use its own database, sessions, uploads, exports,
  archives, backups, generated documents, evidence, and temporary files.
- The current Firm 2 database is only a copied candidate until the
  separation extraction phase is completed.
- Do not run the application from this profile until the extraction
  manifest confirms that Firm 1 records have been removed safely.

## Local launch command

```bash
bash run_firm2.sh
```

Do not use that command until UPA-1B-6B-4B is complete.
''',
    encoding="utf-8",
)

candidate_inventory = inspect_database(FIRM2_DB)

live_hash_after = sha256_file(LIVE_DB)
live_unchanged = live_hash_before == live_hash_after

candidate_is_still_mixed = (
    "FIRM-001" in candidate_inventory["firm_totals"]
    and "FIRM-002" in candidate_inventory["firm_totals"]
)

unsafe_simple_filter_tables = []

for item in candidate_inventory["table_inventory"]:
    if item["has_firm_id"] or item["row_count"] == 0:
        continue

    unsafe_simple_filter_tables.append(
        {
            "table": item["table"],
            "row_count": item["row_count"],
            "foreign_keys": item["foreign_keys"],
            "reason": (
                "Table contains rows but no firm_id. Ownership must be "
                "derived from parent relationships or classified as global "
                "before separation."
            ),
        }
    )

blockers = []

if candidate_is_still_mixed:
    blockers.append(
        "The Firm 2 candidate database is intentionally still a mixed copy. "
        "Firm 1 rows have not yet been removed."
    )

if unsafe_simple_filter_tables:
    blockers.append(
        f"{len(unsafe_simple_filter_tables)} populated tables lack firm_id "
        "and require ownership classification before extraction."
    )

if candidate_inventory["null_firm_rows"]:
    blockers.append(
        f"{candidate_inventory['null_firm_rows']} rows have null or blank firm_id."
    )

status = (
    "FIRM2_PROFILE_SCAFFOLDED_EXTRACTION_REQUIRED"
    if blockers
    else "FIRM2_PROFILE_READY"
)

output = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "governing_rule": {
        "testing_instance": "FIRM-002",
        "protected_baseline": "FIRM-001",
        "shared_codebase": True,
        "firm2_first": True,
    },
    "git": {
        "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "HEAD"),
        "status": git("status", "--short"),
    },
    "database_safety": {
        "live_database": str(LIVE_DB),
        "live_sha256_before": live_hash_before,
        "live_sha256_after": live_hash_after,
        "live_unchanged": live_unchanged,
        "firm2_candidate_database": str(FIRM2_DB),
        "firm2_candidate_sha256": candidate_inventory["sha256"],
    },
    "profile": {
        "instance_root": str(INSTANCE_ROOT),
        "environment_file": str(ENV_FILE),
        "launcher": str(LAUNCHER),
        "database": str(FIRM2_DB),
        "session_cookie_name": "trustee_firm2_session",
        "port": 5002,
    },
    "summary": {
        "database_tables": candidate_inventory["tables"],
        "firm_001_rows_in_candidate": candidate_inventory["firm_totals"].get(
            "FIRM-001", 0
        ),
        "firm_002_rows_in_candidate": candidate_inventory["firm_totals"].get(
            "FIRM-002", 0
        ),
        "null_firm_rows": candidate_inventory["null_firm_rows"],
        "scoped_tables": len(candidate_inventory["scoped_tables"]),
        "unscoped_tables": len(candidate_inventory["unscoped_tables"]),
        "populated_unscoped_tables": len(unsafe_simple_filter_tables),
        "blockers": len(blockers),
    },
    "candidate_inventory": candidate_inventory,
    "unsafe_simple_filter_tables": unsafe_simple_filter_tables,
    "blockers": blockers,
}

JSON_PATH.write_text(
    json.dumps(output, indent=2, default=str),
    encoding="utf-8",
)

lines = [
    "# UPA-1B-6B-4A — Firm 2 Isolated Runtime Profile Scaffold",
    "",
    f"Generated: {output['generated_at']}",
    f"Status: **{status}**",
    "",
    "## Database Safety",
    "",
    f"- Live database unchanged: **{live_unchanged}**",
    f"- Firm 2 candidate database: `{FIRM2_DB}`",
    "",
    "## Summary",
    "",
]

for key, value in output["summary"].items():
    lines.append(f"- {key.replace('_', ' ').title()}: **{value}**")

lines.extend(["", "## Blockers", ""])

if blockers:
    for blocker in blockers:
        lines.append(f"- {blocker}")
else:
    lines.append("- None.")

MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

print()
print("UPA-1B-6B-4A FIRM 2 PROFILE SCAFFOLD COMPLETE")
print(f"Status: {status}")
print(f"Live Database Unchanged: {live_unchanged}")
print(f"Firm 2 Candidate Database: {FIRM2_DB}")
print(
    "Firm 1 Rows In Candidate: "
    f"{candidate_inventory['firm_totals'].get('FIRM-001', 0)}"
)
print(
    "Firm 2 Rows In Candidate: "
    f"{candidate_inventory['firm_totals'].get('FIRM-002', 0)}"
)
print(f"Null-Firm Rows: {candidate_inventory['null_firm_rows']}")
print(f"Populated Unscoped Tables: {len(unsafe_simple_filter_tables)}")

print()
print("BLOCKERS:")
if blockers:
    for blocker in blockers:
        print(f"- {blocker}")
else:
    print("- None")

print()
print(f"JSON REPORT: {JSON_PATH.relative_to(ROOT)}")
print(f"MARKDOWN REPORT: {MD_PATH.relative_to(ROOT)}")
print("=== UPA-1B-6B-4A COMPLETE ===")
