"""Controlled Compliance Review permission migration for H.6E rehearsal.

This migration is explicit-only. During H.6E it refuses the repository normal
database and is validated only on temporary production-like database copies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NORMAL_DB = (ROOT / "trustee_app.db").resolve()
MIGRATION_NAME = "add_compliance_review_permissions_h6e"
REQUIRED_TOKEN = "H6E-TEMPORARY-PERMISSION-GOVERNANCE"

PERMISSIONS = [
    ("PERM-CMP-001", "view_compliance_workspace", "View Compliance workspace shell"),
    ("PERM-CMP-002", "view_compliance_reviews", "View Compliance Review registry and detail"),
    ("PERM-CMP-003", "create_compliance_review", "Create Compliance Review records"),
    ("PERM-CMP-004", "edit_compliance_review", "Edit draft Compliance Review records"),
    ("PERM-CMP-005", "assign_compliance_reviewer", "Assign Compliance Review reviewer"),
    ("PERM-CMP-006", "add_compliance_evidence", "Add Compliance Review evidence"),
    ("PERM-CMP-007", "verify_compliance_evidence", "Verify Compliance Review evidence"),
    ("PERM-CMP-008", "issue_compliance_findings", "Issue Compliance Review findings"),
    ("PERM-CMP-009", "manage_compliance_remediation", "Create and manage Compliance remediation"),
    ("PERM-CMP-010", "submit_compliance_remediation", "Submit Compliance remediation"),
    ("PERM-CMP-011", "verify_compliance_remediation", "Verify Compliance remediation"),
    ("PERM-CMP-012", "approve_compliance_exception", "Approve Compliance remediation exceptions"),
    ("PERM-CMP-013", "approve_compliance_review", "Approve Compliance Reviews"),
    ("PERM-CMP-014", "certify_compliance_review", "Certify Compliance Reviews"),
    ("PERM-CMP-015", "close_compliance_review", "Close Compliance Reviews"),
    ("PERM-CMP-016", "reopen_compliance_review", "Reopen Compliance Reviews"),
    ("PERM-CMP-017", "supersede_compliance_review", "Supersede Compliance Reviews"),
    ("PERM-CMP-018", "archive_compliance_review", "Archive Compliance Reviews"),
    ("PERM-CMP-019", "view_compliance_audit", "View Compliance Review audit trail"),
    ("PERM-CMP-020", "activate_compliance_foundation", "Authorize Compliance foundation activation"),
    ("PERM-CMP-021", "execute_compliance_migration", "Execute Compliance Review migrations"),
    ("PERM-CMP-022", "acknowledge_compliance_findings", "Acknowledge Compliance Review findings"),
    ("PERM-CMP-023", "open_compliance_review", "Open Compliance Review records"),
    ("PERM-CMP-024", "request_compliance_exception", "Request Compliance remediation exceptions"),
    ("PERM-CMP-025", "view_all_compliance_reviews", "View Compliance Review records across firm scope"),
]

ROLE_ASSIGNMENTS = {
    "Admin": [
        "view_compliance_workspace",
        "view_compliance_reviews",
        "create_compliance_review",
        "edit_compliance_review",
        "assign_compliance_reviewer",
        "add_compliance_evidence",
        "issue_compliance_findings",
        "manage_compliance_remediation",
        "submit_compliance_remediation",
        "open_compliance_review",
        "close_compliance_review",
        "view_compliance_audit",
    ],
    "Trustee": [
        "view_compliance_workspace",
        "view_compliance_reviews",
        "create_compliance_review",
        "edit_compliance_review",
        "add_compliance_evidence",
        "manage_compliance_remediation",
        "submit_compliance_remediation",
        "open_compliance_review",
    ],
    "Viewer": [
        "view_compliance_workspace",
        "view_compliance_reviews",
    ],
}

MANUAL_INSTITUTIONAL_ASSIGNMENT_REQUIRED = {
    "approve_compliance_exception",
    "approve_compliance_review",
    "acknowledge_compliance_findings",
    "certify_compliance_review",
    "request_compliance_exception",
    "verify_compliance_evidence",
    "verify_compliance_remediation",
    "reopen_compliance_review",
    "supersede_compliance_review",
    "archive_compliance_review",
    "activate_compliance_foundation",
    "execute_compliance_migration",
    "view_all_compliance_reviews",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _resolve_database(value: str) -> Path:
    if not value:
        raise SystemExit("ERROR explicit --database PATH is required")
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"ERROR database does not exist: {path}")
    if path == NORMAL_DB:
        raise SystemExit("ERROR trustee_app.db is refused during H.6E permission rehearsal")
    return path


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _validate_schema(conn: sqlite3.Connection) -> None:
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('permissions','role_permissions')"
        )
    }
    if tables != {"permissions", "role_permissions"}:
        raise RuntimeError("authorization_schema_missing")
    role_columns = {row["name"] for row in conn.execute("PRAGMA table_info(role_permissions)")}
    permission_columns = {row["name"] for row in conn.execute("PRAGMA table_info(permissions)")}
    if not {"id", "role_name", "permission_name"}.issubset(role_columns):
        raise RuntimeError("role_permissions_schema_conflict")
    if not {"permission_id", "permission_name", "description"}.issubset(permission_columns):
        raise RuntimeError("permissions_schema_conflict")
    duplicate = conn.execute(
        """
        SELECT role_name, permission_name, COUNT(*) AS count
        FROM role_permissions
        GROUP BY role_name, permission_name
        HAVING COUNT(*) > 1
        LIMIT 1
        """
    ).fetchone()
    if duplicate:
        raise RuntimeError("role_permissions_duplicate_pairs")
    index = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='ux_role_permissions_role_permission'"
    ).fetchone()
    if not index:
        raise RuntimeError("role_permissions_unique_index_missing")
    index_columns = [
        row["name"]
        for row in conn.execute("PRAGMA index_info(ux_role_permissions_role_permission)")
    ]
    if index_columns != ["role_name", "permission_name"]:
        raise RuntimeError("role_permissions_unique_index_conflict")


def _planned_additions(conn: sqlite3.Connection) -> dict:
    existing_permissions = {
        row["permission_name"]
        for row in conn.execute("SELECT permission_name FROM permissions")
    }
    existing_pairs = {
        (row["role_name"], row["permission_name"])
        for row in conn.execute("SELECT role_name, permission_name FROM role_permissions")
    }
    permission_additions = [
        item for item in PERMISSIONS if item[1] not in existing_permissions
    ]
    role_additions = []
    for role_name, permission_names in ROLE_ASSIGNMENTS.items():
        for permission_name in permission_names:
            if (role_name, permission_name) not in existing_pairs:
                role_additions.append((role_name, permission_name))
    return {
        "permissions": permission_additions,
        "role_permissions": role_additions,
        "manual_assignment_required": sorted(MANUAL_INSTITUTIONAL_ASSIGNMENT_REQUIRED),
    }


def _manifest(path: Path, before_hash: str, after_hash: str | None, additions: dict) -> dict:
    return {
        "migration": MIGRATION_NAME,
        "database": str(path),
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "before_sha256": before_hash,
        "after_sha256": after_hash,
        "permission_count": len(PERMISSIONS),
        "role_permission_count": sum(len(v) for v in ROLE_ASSIGNMENTS.values()),
        "permission_names": [name for _, name, _ in PERMISSIONS],
        "default_role_assignments": ROLE_ASSIGNMENTS,
        "manual_institutional_assignment_required": sorted(MANUAL_INSTITUTIONAL_ASSIGNMENT_REQUIRED),
        "planned_additions": additions,
        "rollback_instruction": "Remove only the listed permission and role_permission rows if and only if no production records depend on them.",
    }


def apply_migration(path: Path, dry_run: bool) -> dict:
    before_hash = _sha256(path)
    conn = _connect(path)
    try:
        _validate_schema(conn)
        additions = _planned_additions(conn)
        manifest = _manifest(path, before_hash, None, additions)
        if dry_run:
            return {"status": "dry_run", "manifest": manifest}
        conn.execute("BEGIN IMMEDIATE")
        try:
            for permission_id, permission_name, description in additions["permissions"]:
                conn.execute(
                    """
                    INSERT INTO permissions (permission_id, permission_name, description)
                    VALUES (?, ?, ?)
                    """,
                    (permission_id, permission_name, description),
                )
            for role_name, permission_name in additions["role_permissions"]:
                conn.execute(
                    """
                    INSERT INTO role_permissions (role_name, permission_name)
                    VALUES (?, ?)
                    """,
                    (role_name, permission_name),
                )
            if os.environ.get("H6E_FORCE_PERMISSION_MIGRATION_FAILURE") == "after_inserts":
                raise RuntimeError("forced_permission_migration_failure")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    finally:
        conn.close()
    after_hash = _sha256(path)
    verify = _connect(path)
    try:
        _validate_schema(verify)
        remaining = _planned_additions(verify)
        if remaining["permissions"] or remaining["role_permissions"]:
            raise RuntimeError("permission_migration_incomplete")
    finally:
        verify.close()
    return {
        "status": "applied",
        "manifest": _manifest(path, before_hash, after_hash, additions),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add Compliance Review permissions to an explicitly authorized temporary database copy."
    )
    parser.add_argument("--database", required=True, help="Explicit SQLite database path.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Print planned changes without writing.")
    mode.add_argument("--apply", action="store_true", help="Apply planned changes transactionally.")
    parser.add_argument("--authorization-token", required=True, help="Explicit H.6E temporary authorization token.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.authorization_token != REQUIRED_TOKEN:
        raise SystemExit("ERROR invalid H.6E permission migration authorization token")
    path = _resolve_database(args.database)
    result = apply_migration(path, dry_run=args.dry_run)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
