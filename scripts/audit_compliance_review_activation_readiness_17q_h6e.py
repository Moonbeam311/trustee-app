import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "trustee_app.db"
DOC = ROOT / "docs" / "compliance_review_production_activation_plan_h6e.md"
MANIFEST = ROOT / "config" / "compliance_review_activation_manifest.example.json"
EXPECTED_SHA = "EF19D33AF0B77E6854CE45538D6DDE30948A6FF8D563F4C7CEBC3CFEDBAEDC13"
BACKUP = ROOT / "data" / "backups" / "trustee_app_pre_role_permission_reconcile_2026-07-15.db"
BACKUP_SHA = "CEEDF08EAA93F1311D0E3057CD1BF84E35EADF26D40872CF7A05F5D2D560F7BA"

failures = []


def check(name, condition, detail=""):
    print(("PASS" if condition else "FAIL") + " - " + name + ((" | " + str(detail)[:260]) if detail and not condition else ""))
    if not condition:
        failures.append(name)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def db_summary(path):
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        cur = con.cursor()
        return {
            "audit": cur.execute("SELECT count(*), coalesce(max(id),0) FROM audit_log").fetchone(),
            "role_permissions": cur.execute("SELECT count(*) FROM role_permissions").fetchone()[0],
            "pairs": cur.execute("SELECT count(*) FROM (SELECT DISTINCT role_name, permission_name FROM role_permissions)").fetchone()[0],
            "dupes": cur.execute("SELECT count(*) FROM (SELECT role_name, permission_name, count(*) c FROM role_permissions GROUP BY role_name, permission_name HAVING c > 1)").fetchone()[0],
            "governance": cur.execute("SELECT count(*) FROM governance_relationships").fetchone()[0],
            "ledger": cur.execute("SELECT count(*) FROM governance_relationship_audit_ledger").fetchone()[0],
            "objects": cur.execute("SELECT type,name FROM sqlite_master WHERE lower(name) LIKE '%compliance%' OR lower(name) LIKE '%system_observation%' ORDER BY type,name").fetchall(),
            "integrity": cur.execute("PRAGMA integrity_check").fetchone()[0],
            "fk": cur.execute("PRAGMA foreign_key_check").fetchall(),
        }
    finally:
        con.close()


def main():
    doc = DOC.read_text(encoding="utf-8") if DOC.exists() else ""
    manifest_text = MANIFEST.read_text(encoding="utf-8") if MANIFEST.exists() else "{}"
    manifest = json.loads(manifest_text)

    check("normal DB sha baseline", sha(DB) == EXPECTED_SHA, sha(DB))
    summary = db_summary(DB)
    check("normal DB unactivated", summary["objects"] == [], summary)
    check("normal DB role baseline", summary["role_permissions"] == 25 and summary["pairs"] == 25 and summary["dupes"] == 0, summary)
    check("normal DB integrity", summary["integrity"] == "ok" and summary["fk"] == [], summary)
    check("H.6A rollback backup retained", BACKUP.exists() and sha(BACKUP) == BACKUP_SHA, sha(BACKUP) if BACKUP.exists() else "missing")

    for marker in (
        "Activation Authority Model",
        "Two-person approval is mandatory",
        "Production Backup Plan",
        "Production Configuration Boundary",
        "If configuration and schema disagree, the system fails closed",
        "Production-Like Temporary Rehearsal",
        "Failure-Injection Rehearsal",
        "Post-Activation Certification Plan",
    ):
        check("readiness document covers " + marker, marker in doc)

    required_manifest_fields = [
        "module_key", "schema_version", "required_application_commit", "target_environment",
        "target_database_path", "expected_pre_migration_sha256",
        "expected_role_permission_count", "expected_permission_set_hash",
        "permission_migration", "activation_migration", "backup_path", "backup_sha256",
        "requested_by", "approved_by", "authority_basis", "migration_executor",
        "post_migration_verifier", "rollback_owner", "activation_window",
        "certification_owner", "token_reference",
    ]
    for field in required_manifest_fields:
        check("manifest field: " + field, field in manifest)
    check("manifest has no real secret", "H6B-TEMPORARY-ACTIVATION" not in manifest_text and "H6E-TEMPORARY-PERMISSION-GOVERNANCE" not in manifest_text)
    check("manifest is example-only", "REPLACE_WITH" in manifest_text and "REFERENCE_ONLY_NO_SECRET_VALUE" in manifest_text)

    staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True, capture_output=True)
    check("staging empty", staged.stdout.strip() == "")

    print("POST-V2-17Q-H.6E ACTIVATION READINESS AUDIT")
    if failures:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
