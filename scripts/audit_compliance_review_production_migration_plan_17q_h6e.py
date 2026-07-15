import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "trustee_app.db"
PERMISSION_MIGRATION = ROOT / "migrations" / "add_compliance_review_permissions.py"
ACTIVATION_MIGRATION = ROOT / "migrations" / "activate_compliance_review_foundation.py"
PERMISSION_TOKEN = "H6E-TEMPORARY-PERMISSION-GOVERNANCE"
ACTIVATION_TOKEN = "H6B-TEMPORARY-ACTIVATION"
EXPECTED_SHA = "EF19D33AF0B77E6854CE45538D6DDE30948A6FF8D563F4C7CEBC3CFEDBAEDC13"

failures = []


def check(name, condition, detail=""):
    print(("PASS" if condition else "FAIL") + " - " + name + ((" | " + str(detail)[:300]) if detail and not condition else ""))
    if not condition:
        failures.append(name)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def run(args, env=None, timeout=240):
    merged = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(env or {})}
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=timeout, env=merged)


def counts(path):
    con = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)
    try:
        cur = con.cursor()
        return {
            "audit": cur.execute("SELECT count(*), coalesce(max(id),0) FROM audit_log").fetchone(),
            "role_permissions": cur.execute("SELECT count(*) FROM role_permissions").fetchone()[0],
            "pairs": cur.execute("SELECT count(*) FROM (SELECT DISTINCT role_name, permission_name FROM role_permissions)").fetchone()[0],
            "dupes": cur.execute("SELECT count(*) FROM (SELECT role_name, permission_name, count(*) c FROM role_permissions GROUP BY role_name, permission_name HAVING c > 1)").fetchone()[0],
            "compliance_tables": cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'compliance_review%' ORDER BY name").fetchall(),
            "integrity": cur.execute("PRAGMA integrity_check").fetchone()[0],
            "fk": cur.execute("PRAGMA foreign_key_check").fetchall(),
        }
    finally:
        con.close()


def import_read_only(path):
    code = "import hashlib, os, pathlib, sys; p=pathlib.Path(os.environ['DB_PATH']); b=hashlib.sha256(p.read_bytes()).hexdigest().upper(); sys.path.insert(0, sys.argv[1]); import app; a=hashlib.sha256(p.read_bytes()).hexdigest().upper(); print(b==a)"
    proc = run([sys.executable, "-c", code, str(ROOT)], env={"DB_PATH": str(path)})
    return proc.returncode == 0 and proc.stdout.strip().endswith("True"), proc.stdout + proc.stderr


def route_check(path, activated):
    code = r'''
from datetime import datetime, timezone
import hashlib, os, pathlib, sys
sys.path.insert(0, sys.argv[1])
p = pathlib.Path(os.environ["DB_PATH"])
before = hashlib.sha256(p.read_bytes()).hexdigest().upper()
import app as app_module
app = app_module.app
app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()
with client.session_transaction() as sess:
    sess.clear()
    sess["username"] = "h6e-admin"
    sess["user_id"] = "h6e-admin"
    sess["role"] = "Admin"
    sess["firm_id"] = "FIRM-002"
    sess["compliance_authorities"] = ["create_review", "open_review"]
    sess["_csrf_token"] = "csrf-h6e"
    sess["last_activity"] = datetime.now(timezone.utc).timestamp()
print("registry", client.get("/compliance/reviews").status_code)
print("detail", client.get("/compliance/reviews/CMP-2026-9999").status_code)
payload = {
    "_csrf_token": "csrf-h6e",
    "firm_id": "FIRM-002",
    "title": "H6E Temporary Rehearsal Review",
    "review_type": "governance_compliance",
    "purpose": "Temporary H.6E production-like rehearsal.",
    "scope": "Temporary activated database only.",
    "review_standard": "H6E",
    "question_presented": "Does H6E temporary rehearsal work?",
    "governing_requirement_type": "institutional_policy",
    "governing_requirement_id": "GOV-H6E",
    "source_type": "governance_record",
    "source_id": "GOV-H6E",
    "authority_basis": "H6E rehearsal only",
    "primary_subject_type": "trust",
    "primary_subject_id": "TRUST-H6E",
    "primary_subject_label": "Temporary H6E trust context",
    "risk_level": "moderate",
    "priority": "normal",
    "confidentiality_level": "internal",
    "idempotency_key": "h6e-rehearsal",
}
created = client.post("/compliance/reviews", data=payload)
print("create", created.status_code)
after = hashlib.sha256(p.read_bytes()).hexdigest().upper()
print("db_changed", before != after)
'''
    proc = run([sys.executable, "-c", code, str(ROOT)], env={"DB_PATH": str(path)})
    out = proc.stdout + proc.stderr
    if activated:
        ok = proc.returncode == 0 and "registry 200" in out and "detail 404" in out and "create 201" in out and "db_changed True" in out
    else:
        ok = proc.returncode == 0 and "registry 503" in out and "detail 503" in out and ("create 503" in out or "create 400" in out)
    return ok, out


def main():
    baseline_sha = sha(DB)
    baseline_counts = counts(DB)
    temp_root = Path(tempfile.mkdtemp(prefix="trustee_h6e_plan_"))
    print("temporary_root=" + str(temp_root))
    inventory = []
    try:
        rehearsal = temp_root / "production_like.db"
        shutil.copy2(DB, rehearsal)
        before = sha(rehearsal)

        dry = run([sys.executable, str(PERMISSION_MIGRATION), "--database", str(rehearsal), "--dry-run", "--authorization-token", PERMISSION_TOKEN])
        check("permission dry-run succeeds", dry.returncode == 0, dry.stdout + dry.stderr)
        check("permission dry-run read-only", sha(rehearsal) == before)

        apply = run([sys.executable, str(PERMISSION_MIGRATION), "--database", str(rehearsal), "--apply", "--authorization-token", PERMISSION_TOKEN])
        check("permission apply succeeds", apply.returncode == 0, apply.stdout + apply.stderr)
        after_permission = counts(rehearsal)
        check("permission apply adds expected pairs", after_permission["role_permissions"] == 47 and after_permission["pairs"] == 47 and after_permission["dupes"] == 0, after_permission)

        repeat_before = sha(rehearsal)
        repeat = run([sys.executable, str(PERMISSION_MIGRATION), "--database", str(rehearsal), "--apply", "--authorization-token", PERMISSION_TOKEN])
        check("permission repeat succeeds", repeat.returncode == 0, repeat.stdout + repeat.stderr)
        check("permission repeat idempotent", sha(rehearsal) == repeat_before)

        activation_backup = temp_root / "activation_backup.db"
        shutil.copy2(rehearsal, activation_backup)
        check("activation backup created", activation_backup.exists() and sha(activation_backup) == sha(rehearsal))

        activate = run([sys.executable, str(ACTIVATION_MIGRATION), "--database", str(rehearsal), "--apply", "--activation-token", ACTIVATION_TOKEN])
        check("activation migration succeeds", activate.returncode == 0, activate.stdout + activate.stderr)
        activated_counts = counts(rehearsal)
        check("activation creates schema", len(activated_counts["compliance_tables"]) >= 10, activated_counts)
        check("activation preserves integrity", activated_counts["integrity"] == "ok" and activated_counts["fk"] == [], activated_counts)

        repeat_activation_before = sha(rehearsal)
        repeat_activation = run([sys.executable, str(ACTIVATION_MIGRATION), "--database", str(rehearsal), "--apply", "--activation-token", ACTIVATION_TOKEN])
        check("activation repeat succeeds", repeat_activation.returncode == 0, repeat_activation.stdout + repeat_activation.stderr)
        check("activation repeat idempotent", sha(rehearsal) == repeat_activation_before)

        ok, detail = import_read_only(rehearsal)
        check("activated import read-only", ok, detail)
        ok, detail = route_check(rehearsal, activated=True)
        check("activated route exposure and authorized create", ok, detail)
        ok, detail = route_check(activation_backup, activated=False)
        check("restored backup unavailable-state", ok, detail)

        refused = run([sys.executable, str(PERMISSION_MIGRATION), "--database", str(DB), "--dry-run", "--authorization-token", PERMISSION_TOKEN])
        check("permission migration refuses normal DB", refused.returncode != 0 and "trustee_app.db is refused" in (refused.stdout + refused.stderr))

        inventory = [(p.name, p.stat().st_size, sha(p)) for p in sorted(temp_root.glob("*.db"))]
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
    print("temporary_database_inventory=" + repr(inventory))
    print("TEMP_ARTIFACTS_REMOVED=" + str(not temp_root.exists()))

    check("normal database sha preserved", sha(DB) == baseline_sha == EXPECTED_SHA, sha(DB))
    check("normal database counts preserved", counts(DB) == baseline_counts, counts(DB))
    staged = run(["git", "diff", "--cached", "--name-only"])
    check("staging empty", staged.stdout.strip() == "")

    print("POST-V2-17Q-H.6E PRODUCTION MIGRATION PLAN AUDIT")
    if failures:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
