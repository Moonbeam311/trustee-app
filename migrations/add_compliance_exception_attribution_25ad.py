"""Add Compliance remediation exception requester attribution.

This migration is explicit-only and is intended for temporary database
rehearsal until Compliance activation is approved for the normal database.
"""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
NORMAL_DB = (ROOT / "trustee_app.db").resolve()
REQUIRED_TOKEN = "25AD-TEMPORARY-ATTRIBUTION"
MIGRATION_NAME = "add_compliance_exception_attribution_25ad"

REMEDIATION_COLUMNS = {
    "exception_requested_by": "TEXT",
    "exception_requested_by_label": "TEXT",
    "exception_requested_at": "TEXT",
    "exception_request_basis": "TEXT",
    "exception_request_status": "TEXT",
}

AUDIT_COLUMNS = {
    "actor_label": "TEXT",
    "target_firm_id": "TEXT",
    "canonical_authority": "TEXT",
    "source_permission": "TEXT",
    "exception_requested_by": "TEXT",
    "exception_approved_by": "TEXT",
    "sod_result": "TEXT",
    "override_used": "INTEGER NOT NULL DEFAULT 0",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def resolve_database(value: str) -> Path:
    if not value:
        raise SystemExit("ERROR explicit --database PATH is required")
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"ERROR database does not exist: {path}")
    if path == NORMAL_DB:
        raise SystemExit("ERROR trustee_app.db is refused during 25AD attribution rehearsal")
    return path


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def table_columns(conn: sqlite3.Connection, table_name: str) -> dict[str, str]:
    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    if not table:
        raise RuntimeError(f"{table_name}_missing")
    return {
        row["name"]: (row["type"] or "").upper()
        for row in conn.execute(f"PRAGMA table_info({table_name})")
    }


def planned_columns(conn: sqlite3.Connection) -> dict[str, dict[str, str]]:
    remediation_existing = table_columns(conn, "compliance_review_remediations")
    audit_existing = table_columns(conn, "compliance_review_audit_ledger")
    return {
        "compliance_review_remediations": {
            name: column_type
            for name, column_type in REMEDIATION_COLUMNS.items()
            if name not in remediation_existing
        },
        "compliance_review_audit_ledger": {
            name: column_type
            for name, column_type in AUDIT_COLUMNS.items()
            if name not in audit_existing
        },
    }


def manifest(path: Path, before_hash: str, after_hash: str | None, additions: dict[str, dict[str, str]]) -> dict:
    return {
        "migration": MIGRATION_NAME,
        "database": str(path),
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "before_sha256": before_hash,
        "after_sha256": after_hash,
        "planned_columns": additions,
        "required_columns": {
            "compliance_review_remediations": REMEDIATION_COLUMNS,
            "compliance_review_audit_ledger": AUDIT_COLUMNS,
        },
        "legacy_row_policy": "Rows with NULL requester attribution require supervisory review and fail requester/approver SOD checks.",
    }


def apply_migration(path: Path, dry_run: bool) -> dict:
    before_hash = sha256(path)
    conn = connect(path)
    try:
        additions = planned_columns(conn)
        if dry_run:
            return {"status": "dry_run", "manifest": manifest(path, before_hash, None, additions)}
        conn.execute("BEGIN IMMEDIATE")
        try:
            for table_name, columns in additions.items():
                for name, column_type in columns.items():
                    conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {name} {column_type}")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    finally:
        conn.close()

    after_hash = sha256(path)
    verify = connect(path)
    try:
        remaining = planned_columns(verify)
        if any(remaining.values()):
            raise RuntimeError("attribution_migration_incomplete")
    finally:
        verify.close()
    return {"status": "applied", "manifest": manifest(path, before_hash, after_hash, additions)}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add Compliance exception requester attribution to a temporary database.")
    parser.add_argument("--database", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--authorization-token", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.authorization_token != REQUIRED_TOKEN:
        raise SystemExit("ERROR explicit 25AD attribution authorization token is required")
    path = resolve_database(args.database)
    result = apply_migration(path, dry_run=args.dry_run)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
