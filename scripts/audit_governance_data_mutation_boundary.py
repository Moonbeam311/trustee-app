"""
V2-HARDEN-5 — Governance Data Mutation Boundary Audit

Script-only hardening audit.

Purpose:
- Verify governance evidence/export/certification routes are read-only.
- Snapshot key governance-related table counts before route calls.
- Exercise HTML, TXT, and CSV evidence routes through Flask test client.
- Snapshot the same tables after route calls.
- Fail if any protected route mutates table counts.
- Fail if routes generate 404/500 errors.
- Fail if database integrity_check fails.

This script does not intentionally create, update, delete, certify, archive, or mutate
governance records. It uses Flask's local test client and a simulated Admin session.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@dataclass
class Check:
    key: str
    status: str
    detail: str


def add(checks: list[Check], key: str, ok: bool, detail: str) -> None:
    checks.append(Check(key=key, status="PASS" if ok else "FAIL", detail=detail))


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def count_table(conn: sqlite3.Connection, table_name: str) -> int | None:
    if not table_exists(conn, table_name):
        return None
    row = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    return int(row[0]) if row else 0


def snapshot_counts(db_path: Path, tables: list[str]) -> dict[str, int | None]:
    conn = sqlite3.connect(str(db_path))
    try:
        return {table: count_table(conn, table) for table in tables}
    finally:
        conn.close()


def integrity_check(db_path: Path) -> str:
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute("PRAGMA integrity_check").fetchone()
        return str(row[0]) if row else ""
    finally:
        conn.close()


def response_is_success(resp) -> bool:
    return 200 <= resp.status_code < 300


def main() -> int:
    checks: list[Check] = []

    print("V2-HARDEN-5 GOVERNANCE DATA MUTATION BOUNDARY AUDIT")
    print("=" * 76)
    print(f"Repo Root: {ROOT}")
    print("Mode: Flask test-client read-only mutation boundary audit")
    print("")

    try:
        from app import app, DB_PATH
    except Exception as exc:
        add(checks, "import_app", False, f"{type(exc).__name__}: {exc}")
        for check in checks:
            print(f"{check.status}: {check.key} — {check.detail}")
        print("RESULT: FAIL")
        return 1

    db_path = Path(DB_PATH)
    print(f"Resolved DB Path: {db_path}")

    add(checks, "import_app", True, "app imported")
    add(checks, "db_path_exists", db_path.exists(), str(db_path))

    if not db_path.exists():
        for check in checks:
            print(f"{check.status}: {check.key} — {check.detail}")
        print("RESULT: FAIL")
        return 1

    governance_tables = [
        # Known governance/evidence lineage tables.
        "governance_relationships",
        "governance_relationship_audits",
        "governance_directives",
        "governance_policies",
        "governance_events",
        "matter_events",
        "matters",
        "trusts",
        "execution_sessions",
        "archive_packets",
        "archive_packet_items",
        "archive_custody_log",
        "institutional_assets",
        "audit_log",
        "security_events",
        "exports",
        "export_history",
        "module_ledger",
    ]

    before_integrity = integrity_check(db_path)
    add(checks, "db_integrity_before", before_integrity == "ok", before_integrity)

    before = snapshot_counts(db_path, governance_tables)

    print("")
    print("BEFORE SNAPSHOT")
    print("-" * 76)
    for table, count in before.items():
        status = "missing" if count is None else count
        print(f"{table}: {status}")

    filtered_query = "object_type=Document&object_id=DOC-TRUST-TR-022"

    route_paths = [
        "/governance/evidence-exports",
        "/governance/evidence-exports.csv?packet_type=combined",
        "/governance/evidence-exports.csv?packet_type=relationships",
        "/governance/evidence-exports.csv?packet_type=audits",
        "/governance/evidence-exports/manifest",
        "/governance/evidence-exports/manifest.txt",
        "/governance/evidence-exports/integrity",
        "/governance/evidence-exports/integrity.txt",
        "/governance/evidence-exports/archive-intake",
        "/governance/evidence-exports/archive-intake.txt",
        "/governance/evidence-exports/certification",
        "/governance/evidence-exports/certification.txt",
        "/governance/evidence-exports/exceptions",
        "/governance/evidence-exports/exceptions.txt",
        "/governance/evidence-exports/completion-gate",
        "/governance/evidence-exports/completion-gate.txt",
        f"/governance/evidence-exports?{filtered_query}",
        f"/governance/evidence-exports.csv?packet_type=combined&{filtered_query}",
        f"/governance/evidence-exports/manifest?{filtered_query}",
        f"/governance/evidence-exports/manifest.txt?{filtered_query}",
        f"/governance/evidence-exports/integrity?{filtered_query}",
        f"/governance/evidence-exports/integrity.txt?{filtered_query}",
        f"/governance/evidence-exports/archive-intake?{filtered_query}",
        f"/governance/evidence-exports/archive-intake.txt?{filtered_query}",
        f"/governance/evidence-exports/certification?{filtered_query}",
        f"/governance/evidence-exports/certification.txt?{filtered_query}",
        f"/governance/evidence-exports/exceptions?{filtered_query}",
        f"/governance/evidence-exports/exceptions.txt?{filtered_query}",
        f"/governance/evidence-exports/completion-gate?{filtered_query}",
        f"/governance/evidence-exports/completion-gate.txt?{filtered_query}",
    ]

    print("")
    print("ROUTE EXERCISE")
    print("-" * 76)

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = "admin123"
            sess["user_id"] = "admin123"
            sess["username"] = "admin123"
            sess["role"] = "Admin"
            sess["is_master_admin"] = True
            sess["firm_id"] = "FIRM-002"
            sess["last_activity"] = datetime.now(timezone.utc).timestamp()

        for path in route_paths:
            resp = client.get(path)
            print(f"{resp.status_code}: {path}")
            add(checks, f"route_success:{path}", response_is_success(resp), f"status={resp.status_code}")
            body = resp.get_data(as_text=True)
            add(checks, f"route_no_traceback:{path}", "Traceback (most recent call last)" not in body, path)
            add(checks, f"route_no_internal_server_error:{path}", "Internal Server Error" not in body, path)

    after_integrity = integrity_check(db_path)
    add(checks, "db_integrity_after", after_integrity == "ok", after_integrity)

    after = snapshot_counts(db_path, governance_tables)

    print("")
    print("AFTER SNAPSHOT")
    print("-" * 76)
    for table, count in after.items():
        status = "missing" if count is None else count
        print(f"{table}: {status}")

    print("")
    print("MUTATION COMPARISON")
    print("-" * 76)
    for table in governance_tables:
        before_count = before.get(table)
        after_count = after.get(table)
        unchanged = before_count == after_count
        detail = f"before={before_count}, after={after_count}"
        print(f"{'PASS' if unchanged else 'FAIL'}: {table} — {detail}")
        add(checks, f"count_unchanged:{table}", unchanged, detail)

    print("")
    print("SUMMARY")
    print("-" * 76)

    pass_count = sum(1 for c in checks if c.status == "PASS")
    fail_count = sum(1 for c in checks if c.status == "FAIL")

    for check in checks:
        print(f"{check.status}: {check.key} — {check.detail}")

    print("")
    print(f"checks_total: {len(checks)}")
    print(f"checks_passed: {pass_count}")
    print(f"checks_failed: {fail_count}")

    if fail_count:
        print("")
        print("RESULT: FAIL")
        return 1

    print("")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
