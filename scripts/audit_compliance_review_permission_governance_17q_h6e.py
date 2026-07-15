import ast
import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "trustee_app.db"
DOC = ROOT / "docs" / "compliance_review_production_activation_plan_h6e.md"
MIGRATION = ROOT / "migrations" / "add_compliance_review_permissions.py"
EXPECTED_SHA = "EF19D33AF0B77E6854CE45538D6DDE30948A6FF8D563F4C7CEBC3CFEDBAEDC13"

failures = []


def check(name, condition, detail=""):
    print(("PASS" if condition else "FAIL") + " - " + name + ((" | " + str(detail)[:260]) if detail and not condition else ""))
    if not condition:
        failures.append(name)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def q(sql):
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def main():
    doc = DOC.read_text(encoding="utf-8") if DOC.exists() else ""
    migration = MIGRATION.read_text(encoding="utf-8") if MIGRATION.exists() else ""
    check("H.6E plan exists", DOC.exists())
    check("permission migration exists", MIGRATION.exists())

    required_permissions = [
        "view_compliance_workspace", "view_compliance_reviews", "create_compliance_review",
        "edit_compliance_review", "assign_compliance_reviewer", "add_compliance_evidence",
        "verify_compliance_evidence", "issue_compliance_findings", "manage_compliance_remediation",
        "submit_compliance_remediation", "verify_compliance_remediation",
        "approve_compliance_exception", "approve_compliance_review", "certify_compliance_review",
        "close_compliance_review", "reopen_compliance_review", "supersede_compliance_review",
        "archive_compliance_review", "view_compliance_audit", "activate_compliance_foundation",
        "execute_compliance_migration",
    ]
    for permission in required_permissions:
        check("permission defined: " + permission, permission in doc and permission in migration)

    for marker in (
        "MANUAL_INSTITUTIONAL_ASSIGNMENT_REQUIRED",
        "Activation and migration permissions must never be granted",
        "Role membership alone is never institutional authority",
        "Two-person approval is mandatory",
        "Permissions allow a person to attempt an action",
    ):
        check("governance marker: " + marker, marker in doc)

    tree = ast.parse(migration)
    check("migration has no top-level execution call", not [
        node for node in tree.body if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
    ])
    check("requires explicit database", "--database" in migration and "required=True" in migration)
    check("requires explicit dry-run/apply", "add_mutually_exclusive_group(required=True)" in migration)
    check("requires explicit token", "--authorization-token" in migration and "REQUIRED_TOKEN" in migration)
    check("refuses normal database", "trustee_app.db is refused during H.6E" in migration)
    check("validates unique role-permission index", "ux_role_permissions_role_permission" in migration)
    check("migration transactional", "BEGIN IMMEDIATE" in migration and "conn.rollback()" in migration)
    check("migration idempotent", "additions[\"permissions\"]" in migration and "additions[\"role_permissions\"]" in migration and "INSERT OR IGNORE" not in migration)
    check("reversible manifest", "rollback_instruction" in migration)

    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        roles = [row["role_name"] for row in con.execute("SELECT DISTINCT role_name FROM app_users ORDER BY role_name")]
        permissions = [row["permission_name"] for row in con.execute("SELECT permission_name FROM permissions ORDER BY permission_name")]
        pairs = [
            (row["role_name"], row["permission_name"])
            for row in con.execute("SELECT role_name, permission_name FROM role_permissions ORDER BY role_name, permission_name")
        ]
    finally:
        con.close()
    print("existing_roles=" + json.dumps(roles))
    print("existing_permissions=" + json.dumps(permissions))
    print("existing_role_permissions=" + json.dumps(pairs))
    check("current roles inventoried in plan", all(role in doc for role in roles), roles)
    check("normal DB has no Compliance permissions", not any("compliance" in p for p in permissions), permissions)
    check("normal DB sha preserved", sha(DB) == EXPECTED_SHA, sha(DB))
    staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True, capture_output=True)
    check("staging empty", staged.stdout.strip() == "")

    print("POST-V2-17Q-H.6E PERMISSION GOVERNANCE AUDIT")
    if failures:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
