import ast
import hashlib
import json
import os
import re
import sqlite3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "trustee_app.db"
BACKUP = ROOT / "data" / "backups" / "trustee_app_pre_role_permission_reconcile_2026-07-15.db"
EXPECTED_DB_SHA = "EF19D33AF0B77E6854CE45538D6DDE30948A6FF8D563F4C7CEBC3CFEDBAEDC13"
EXPECTED_BACKUP_SHA = "CEEDF08EAA93F1311D0E3057CD1BF84E35EADF26D40872CF7A05F5D2D560F7BA"

APPROVED_PATHS = {
    "app.py",
    "services/services_compliance_reviews.py",
    "templates/compliance_reviews/registry.html",
    "templates/compliance_reviews/detail.html",
    "templates/compliance_reviews/create.html",
    "docs/compliance_review_activation_architecture_h6b.md",
    "docs/compliance_review_production_activation_plan_h6e.md",
    "docs/compliance_review_controlled_execution_authorization_h6f.md",
    "config/compliance_review_activation_manifest.example.json",
    "config/compliance_review_activation_manifest.schema.json",
    "migrations/activate_compliance_review_foundation.py",
    "migrations/add_compliance_review_permissions.py",
    "scripts/audit_system_observation_foundation_17m.py",
    "scripts/audit_compliance_review_foundation_17q_g.py",
    "scripts/audit_compliance_review_readonly_ui_17q_h.py",
    "scripts/audit_authorization_baseline_reconciliation_17q_h6a_r6.py",
    "scripts/audit_compliance_review_activation_architecture_17q_h6b.py",
    "scripts/audit_compliance_review_governed_migration_17q_h6b.py",
    "scripts/audit_compliance_review_temporary_activation_17q_h6c.py",
    "scripts/audit_compliance_review_service_workflow_17q_h6c.py",
    "scripts/audit_compliance_review_lifecycle_authorization_17q_h6c.py",
    "scripts/audit_compliance_review_audit_ledger_17q_h6c.py",
    "scripts/audit_compliance_review_h6d_common.py",
    "scripts/audit_compliance_review_write_routes_17q_h6d.py",
    "scripts/audit_compliance_review_form_controls_17q_h6d.py",
    "scripts/audit_compliance_review_operator_ui_17q_h6d.py",
    "scripts/audit_compliance_review_route_authorization_17q_h6d.py",
    "scripts/audit_compliance_review_concurrency_idempotency_17q_h6d.py",
    "scripts/audit_compliance_review_permission_governance_17q_h6e.py",
    "scripts/audit_compliance_review_activation_readiness_17q_h6e.py",
    "scripts/audit_compliance_review_production_migration_plan_17q_h6e.py",
    "scripts/audit_compliance_review_rollback_plan_17q_h6e.py",
    "scripts/audit_compliance_review_go_no_go_17q_h6e.py",
    "scripts/audit_compliance_review_pre_activation_certification_17q_h6f.py",
    "scripts/audit_compliance_review_h6b_h6f_publication_scope.py",
}

CLASSIFICATIONS = {
    "app.py": "PRODUCTION_APPLICATION_CODE",
    "services/services_compliance_reviews.py": "PRODUCTION_SERVICE_CODE",
    "templates/compliance_reviews/registry.html": "PRODUCTION_TEMPLATE",
    "templates/compliance_reviews/detail.html": "PRODUCTION_TEMPLATE",
    "templates/compliance_reviews/create.html": "PRODUCTION_TEMPLATE",
    "docs/compliance_review_activation_architecture_h6b.md": "ARCHITECTURE_DOCUMENTATION",
    "docs/compliance_review_production_activation_plan_h6e.md": "ACTIVATION_PLANNING_DOCUMENTATION",
    "docs/compliance_review_controlled_execution_authorization_h6f.md": "ACTIVATION_PLANNING_DOCUMENTATION",
    "config/compliance_review_activation_manifest.example.json": "NONSECRET_CONFIGURATION_EXAMPLE",
    "config/compliance_review_activation_manifest.schema.json": "NONSECRET_CONFIGURATION_EXAMPLE",
    "migrations/activate_compliance_review_foundation.py": "GOVERNED_MIGRATION",
    "migrations/add_compliance_review_permissions.py": "PERMISSION_MIGRATION",
}

failures = []


def check(name, condition, detail=""):
    print(("PASS" if condition else "FAIL") + " - " + name + ((" | " + str(detail)[:300]) if detail and not condition else ""))
    if not condition:
        failures.append(name)


def run_git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    return result.stdout.strip()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def file_state(path):
    if path in set(run_git("ls-files").splitlines()):
        return "tracked"
    if path in set(run_git("ls-files", "--others", "--exclude-standard").splitlines()):
        return "untracked"
    return "absent"


def dirty_paths():
    modified = set(run_git("diff", "--name-only").splitlines())
    untracked = set(run_git("ls-files", "--others", "--exclude-standard").splitlines())
    return {p for p in modified | untracked if p}


def staged_paths():
    return {p for p in run_git("diff", "--cached", "--name-only").splitlines() if p}


def head_paths():
    out = run_git("show", "--pretty=", "--name-only", "HEAD")
    return {p for p in out.splitlines() if p}


def candidate_paths():
    staged = staged_paths()
    if staged:
        return "staged", staged
    dirty = dirty_paths()
    if dirty:
        return "dirty", dirty
    return "head", head_paths()


def db_summary(path):
    con = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)
    try:
        cur = con.cursor()
        return {
            "audit": cur.execute("SELECT count(*), coalesce(max(id),0) FROM audit_log").fetchone(),
            "role_permissions": cur.execute("SELECT count(*) FROM role_permissions").fetchone()[0],
            "pairs": cur.execute("SELECT count(*) FROM (SELECT DISTINCT role_name, permission_name FROM role_permissions)").fetchone()[0],
            "dupes": cur.execute("SELECT count(*) FROM (SELECT role_name, permission_name, count(*) c FROM role_permissions GROUP BY role_name, permission_name HAVING c > 1)").fetchone()[0],
            "governance": cur.execute("SELECT count(*) FROM governance_relationships").fetchone()[0],
            "ledger": cur.execute("SELECT count(*) FROM governance_relationship_audit_ledger").fetchone()[0],
            "objects": cur.execute("SELECT type,name FROM sqlite_master WHERE lower(name) LIKE '%compliance%' OR lower(name) LIKE '%system_observation%' OR lower(name) LIKE '%observation%' ORDER BY type,name").fetchall(),
            "integrity": cur.execute("PRAGMA integrity_check").fetchone()[0],
            "fk": cur.execute("PRAGMA foreign_key_check").fetchall(),
        }
    finally:
        con.close()


def backup_summary():
    con = sqlite3.connect(f"file:{BACKUP.as_posix()}?mode=ro", uri=True)
    try:
        cur = con.cursor()
        return {
            "audit": cur.execute("SELECT count(*), coalesce(max(id),0) FROM audit_log").fetchone(),
            "role_permissions": cur.execute("SELECT count(*) FROM role_permissions").fetchone()[0],
            "pairs": cur.execute("SELECT count(*) FROM (SELECT DISTINCT role_name, permission_name FROM role_permissions)").fetchone()[0],
            "integrity": cur.execute("PRAGMA integrity_check").fetchone()[0],
            "fk": cur.execute("PRAGMA foreign_key_check").fetchall(),
        }
    finally:
        con.close()


def secret_free(path, text):
    if path.endswith(".db") or path.endswith(".sqlite"):
        return False
    if path == "config/compliance_review_activation_manifest.example.json":
        return "REPLACE_WITH" in text and "REFERENCE_ONLY_NO_SECRET_VALUE" in text and "H6B-TEMPORARY" not in text and "H6E-TEMPORARY" not in text
    dangerous_patterns = [
        r"BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY",
        r"api[_-]?secret\s*[:=]\s*['\"][^'\"]+['\"]",
        r"password\s*[:=]\s*['\"][^'\"]+['\"]",
        r"activation[_-]?token\s*[:=]\s*['\"](?!REFERENCE_ONLY_NO_SECRET_VALUE|H6B-TEMPORARY-ACTIVATION|H6E-TEMPORARY-PERMISSION-GOVERNANCE)[^'\"]+['\"]",
    ]
    return not any(re.search(pattern, text, re.I) for pattern in dangerous_patterns)


def validate_manifest():
    manifest_path = ROOT / "config" / "compliance_review_activation_manifest.example.json"
    schema_path = ROOT / "config" / "compliance_review_activation_manifest.schema.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    required = set(schema["required"])
    missing = sorted(required - set(manifest))
    wrong_types = []
    for name in required:
        expected = schema["properties"].get(name, {}).get("type")
        if expected == "boolean" and not isinstance(manifest.get(name), bool):
            wrong_types.append(name)
        if expected == "integer" and not isinstance(manifest.get(name), int):
            wrong_types.append(name)
        if expected == "string" and not isinstance(manifest.get(name), str):
            wrong_types.append(name)
    return not missing and not wrong_types, {"missing": missing, "wrong_types": wrong_types}


def migration_safety(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    tree = ast.parse(text)
    top_calls = [node for node in tree.body if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)]
    return {
        "explicit_database": "--database" in text and "required=True" in text,
        "explicit_mode": "add_mutually_exclusive_group(required=True)" in text,
        "explicit_token": "--activation-token" in text or "--authorization-token" in text,
        "transactional": "BEGIN IMMEDIATE" in text and "rollback()" in text,
        "normal_refusal": "trustee_app.db is refused" in text,
        "no_top_call": not top_calls,
    }


def main():
    mode, candidates = candidate_paths()
    print("candidate_mode=" + mode)
    print("candidate_paths=" + json.dumps(sorted(candidates)))

    check("all approved files exist", all((ROOT / p).exists() for p in APPROVED_PATHS), sorted(p for p in APPROVED_PATHS if not (ROOT / p).exists()))
    check("candidate scope exact", candidates == APPROVED_PATHS, sorted(candidates ^ APPROVED_PATHS))
    check("no runtime database in candidate", not any(re.search(r"(?i)(\\.db$|\\.sqlite$|\\.db-wal$|\\.db-shm$|\\.db-journal$)", p) for p in candidates), sorted(candidates))
    check("no backup in candidate", not any("backup" in p.lower() or "data/backups" in p.lower() for p in candidates), sorted(candidates))
    check("no cache in candidate", not any("__pycache__" in p or p.endswith(".pyc") for p in candidates), sorted(candidates))

    for path in sorted(APPROVED_PATHS):
        p = ROOT / path
        text = p.read_text(encoding="utf-8", errors="replace")
        print(json.dumps({
            "path": path,
            "state": file_state(path),
            "line_count": len(text.splitlines()),
            "sha256": sha(p),
            "classification": CLASSIFICATIONS.get(path, "BEHAVIORAL_AUDIT" if path.startswith("scripts/") else "UNKNOWN"),
        }, sort_keys=True))
        check("secret-free: " + path, secret_free(path, text), path)

    app_text = (ROOT / "app.py").read_text(encoding="utf-8", errors="replace")
    service_text = (ROOT / "services" / "services_compliance_reviews.py").read_text(encoding="utf-8")
    combined = app_text + service_text
    check("no browser activation route", "activate_compliance_review" not in app_text and "activation-token" not in app_text)
    check("no import-time migration call", "activate_compliance_review_foundation" not in combined and "add_compliance_review_permissions" not in combined)
    check("no request-time migration call", "subprocess" not in service_text and "migrations/" not in service_text)
    check("production routes do not grant unconditional authority", "compliance_authorities" in app_text and "global_authority" in app_text)

    permission_safety = migration_safety("migrations/add_compliance_review_permissions.py")
    activation_safety = migration_safety("migrations/activate_compliance_review_foundation.py")
    for key, value in permission_safety.items():
        check("permission migration " + key, value, permission_safety)
    for key, value in activation_safety.items():
        check("activation migration " + key, value, activation_safety)
    check("permission and activation migrations separated", "add_compliance_review_permissions.py" in json.dumps(sorted(APPROVED_PATHS)) and "activate_compliance_review_foundation.py" in json.dumps(sorted(APPROVED_PATHS)))

    auth_doc = (ROOT / "docs" / "compliance_review_controlled_execution_authorization_h6f.md").read_text(encoding="utf-8")
    for marker in (
        "Module Identity", "Required Database Baseline", "Backup Requirements",
        "Institutional Authority", "Operational Confirmations", "Explicit Non-Authorization Statement",
    ):
        check("authorization package marker: " + marker, marker in auth_doc)
    check("authorization package is placeholder-only", "REPLACE_WITH" in auth_doc and "PENDING" in auth_doc)

    ok, detail = validate_manifest()
    check("manifest schema validates required fields", ok, detail)
    manifest_text = (ROOT / "config" / "compliance_review_activation_manifest.example.json").read_text(encoding="utf-8")
    check("manifest no actual token", "H6B-TEMPORARY" not in manifest_text and "H6E-TEMPORARY" not in manifest_text and "REFERENCE_ONLY_NO_SECRET_VALUE" in manifest_text)

    plan = (ROOT / "docs" / "compliance_review_production_activation_plan_h6e.md").read_text(encoding="utf-8")
    permissions = re.findall(r"`([a-z_]+compliance[a-z_]+)`", plan)
    check("21 permissions documented", len(set(permissions)) >= 21, sorted(set(permissions)))
    check("manual activation/migration assignment documented", "activate_compliance_foundation" in plan and "execute_compliance_migration" in plan and "MANUAL_INSTITUTIONAL_ASSIGNMENT_REQUIRED" in plan)

    db = db_summary(DB)
    check("normal DB sha", sha(DB) == EXPECTED_DB_SHA, sha(DB))
    check("normal DB invariants", db["audit"] == (513, 513) and db["role_permissions"] == 25 and db["pairs"] == 25 and db["dupes"] == 0 and db["governance"] == 25 and db["ledger"] == 51 and db["objects"] == [] and db["integrity"] == "ok" and db["fk"] == [], db)
    backup = backup_summary()
    check("H.6A backup certified", sha(BACKUP) == EXPECTED_BACKUP_SHA and backup["audit"] == (513, 513) and backup["role_permissions"] == 48381 and backup["pairs"] == 25 and backup["integrity"] == "ok" and backup["fk"] == [], backup)

    check("normal DB ignored", subprocess.run(["git", "check-ignore", "-q", "trustee_app.db"], cwd=ROOT).returncode == 0)
    check("backup ignored", subprocess.run(["git", "check-ignore", "-q", "data/backups/trustee_app_pre_role_permission_reconcile_2026-07-15.db"], cwd=ROOT).returncode == 0)
    check("staging exact when staged", mode != "staged" or candidates == APPROVED_PATHS)

    print("POST-V2-17Q-H.6F PRE-ACTIVATION CERTIFICATION AUDIT")
    if failures:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
