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
MIGRATION = ROOT / "migrations" / "activate_compliance_review_foundation.py"
TOKEN = "H6B-TEMPORARY-ACTIVATION"
EXPECTED_NORMAL_SHA = "EF19D33AF0B77E6854CE45538D6DDE30948A6FF8D563F4C7CEBC3CFEDBAEDC13"
EXPECTED_TABLES = {
    "compliance_review_number_sequences", "compliance_reviews", "compliance_review_subjects",
    "compliance_review_evidence", "compliance_review_findings", "compliance_review_remediations",
    "compliance_review_approvals", "compliance_review_certifications", "compliance_review_relationships",
    "compliance_review_audit_ledger", "compliance_review_events", "compliance_review_activation_registry",
}
failures = []
TEMP_ROOT = None


def check(name, condition, detail=""):
    print(("PASS" if condition else "FAIL") + " - " + name + ((" | " + str(detail)[:240]) if detail and not condition else ""))
    if not condition:
        failures.append(name)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def run(args, env=None):
    merged = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(env or {})}
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=180, env=merged)


def copy_db(name):
    path = Path(TEMP_ROOT) / name
    shutil.copy2(DB, path)
    return path


def objects(path):
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        return {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'compliance_review%'")}
    finally:
        con.close()


def counts(path):
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        return {
            "audit": con.execute("SELECT count(*), coalesce(max(id),0) FROM audit_log").fetchone(),
            "role_permissions": con.execute("SELECT count(*) FROM role_permissions").fetchone()[0],
            "distinct_pairs": con.execute("SELECT count(*) FROM (SELECT DISTINCT role_name, permission_name FROM role_permissions)").fetchone()[0],
            "governance": con.execute("SELECT count(*) FROM governance_relationships").fetchone()[0],
            "ledger": con.execute("SELECT count(*) FROM governance_relationship_audit_ledger").fetchone()[0],
            "integrity": con.execute("PRAGMA integrity_check").fetchone()[0],
            "fk": con.execute("PRAGMA foreign_key_check").fetchall(),
        }
    finally:
        con.close()


def request_check(path, activated):
    code = r'''
from datetime import datetime, timezone
from pathlib import Path
import hashlib, os, sys
sys.path.insert(0, sys.argv[1])
before = hashlib.sha256(Path(os.environ["DB_PATH"]).read_bytes()).hexdigest().upper()
import app as app_module
app = app_module.app
app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()
with client.session_transaction() as sess:
    sess.clear(); sess["username"]="admin"; sess["role"]="Admin"; sess["user_id"]="USR-H6B"; sess["firm_id"]="FIRM-002"; sess["last_activity"]=datetime.now(timezone.utc).timestamp()
registry = client.get("/compliance/reviews")
detail = client.get("/compliance/reviews/CMP-2026-9999")
post = client.post("/compliance/reviews")
after = hashlib.sha256(Path(os.environ["DB_PATH"]).read_bytes()).hexdigest().upper()
print("registry", registry.status_code)
print("detail", detail.status_code)
print("post", post.status_code)
print("read_only", before == after)
'''
    proc = run([sys.executable, "-c", code, str(ROOT)], env={"DB_PATH": str(path)})
    output = proc.stdout
    if activated:
        return proc.returncode == 0 and "registry 200" in output and "detail 404" in output and "post 400" in output and "read_only True" in output, output
    return proc.returncode == 0 and "registry 503" in output and "detail 503" in output and ("post 503" in output or "post 400" in output) and "read_only True" in output, output


def service_check(path):
    code = r'''
import os, sys
sys.path.insert(0, sys.argv[1])
from services.services_compliance_reviews import create_compliance_review, transition_compliance_review, validate_review_transition, activation_status
actor={"actor_id":"USR-H6B","actor_label":"H6B Auditor","firm_id":"FIRM-002","scope":{"firm_id":"FIRM-002"},"authorities":{"compliance_admin"}}
payload={"firm_id":"FIRM-002","title":"Temporary Compliance Review","review_type":"governance_compliance","question_presented":"Does the temporary activation boundary work?","governing_requirement_type":"institutional_policy","governing_requirement_id":"GOV-H6B","source_type":"governance_record","source_id":"GOV-H6B","priority":"normal","risk_level":"moderate","authority_basis":"H.6B temporary validation"}
print("activation", activation_status().get("status"))
created=create_compliance_review(payload=payload, actor_context=actor, idempotency_key="h6b-create")
print("created", created.get("status"), bool(created.get("review")))
review=created.get("review") or {}
invalid=transition_compliance_review(compliance_review_id=review.get("compliance_review_id","CMP-2026-0000"), action="certify", expected_version=1, actor_context=actor, reason="invalid", summary="invalid", idempotency_key="h6b-invalid")
print("invalid", invalid.get("status"))
valid=transition_compliance_review(compliance_review_id=review.get("compliance_review_id","CMP-2026-0000"), action="open", expected_version=1, actor_context=actor, reason="open", summary="open", idempotency_key="h6b-open")
print("valid", valid.get("status"), valid.get("review",{}).get("status"))
print("validator", validate_review_transition("draft","open")["resulting_status"])
'''
    proc = run([sys.executable, "-c", code, str(ROOT)], env={"DB_PATH": str(path)})
    out = proc.stdout
    ok = proc.returncode == 0 and "activation activation_verified" in out and "created created True" in out and "invalid invalid_transition" in out and "valid transitioned opened" in out and "validator opened" in out
    return ok, out + proc.stderr


def import_read_only(path):
    code = "import hashlib, pathlib, os, sys; p=pathlib.Path(os.environ['DB_PATH']); b=hashlib.sha256(p.read_bytes()).hexdigest().upper(); sys.path.insert(0, sys.argv[1]); import app; a=hashlib.sha256(p.read_bytes()).hexdigest().upper(); print(b); print(a); print(b==a)"
    proc = run([sys.executable, "-c", code, str(ROOT)], env={"DB_PATH": str(path)})
    return proc.returncode == 0 and proc.stdout.strip().endswith("True"), proc.stdout + proc.stderr


def main():
    global TEMP_ROOT
    TEMP_ROOT = tempfile.mkdtemp(prefix="trustee_h6b_")
    print("temporary_root=" + TEMP_ROOT)
    baseline_sha = sha(DB)
    baseline_counts = counts(DB)
    check("normal database baseline sha", baseline_sha == EXPECTED_NORMAL_SHA, baseline_sha)
    check("normal database has no compliance objects", not objects(DB), objects(DB))

    dry = copy_db("dry_run.db")
    dry_before = sha(dry)
    proc = run([sys.executable, str(MIGRATION), "--database", str(dry), "--dry-run", "--activation-token", TOKEN])
    check("dry-run exits clean", proc.returncode == 0, proc.stdout + proc.stderr)
    check("dry-run read-only", sha(dry) == dry_before)
    check("dry-run reports schema", "expected_tables=" in proc.stdout)

    apply_db = copy_db("apply.db")
    proc = run([sys.executable, str(MIGRATION), "--database", str(apply_db), "--apply", "--activation-token", TOKEN])
    check("apply exits clean", proc.returncode == 0, proc.stdout + proc.stderr)
    check("all expected tables created", EXPECTED_TABLES <= objects(apply_db), objects(apply_db))
    c = counts(apply_db)
    check("apply preserves unrelated counts", c["audit"] == baseline_counts["audit"] and c["role_permissions"] == 25 and c["governance"] == 25 and c["ledger"] == 51, c)
    check("apply integrity ok", c["integrity"] == "ok" and c["fk"] == [], c)
    con = sqlite3.connect(f"file:{apply_db.as_posix()}?mode=ro", uri=True)
    try:
        samples = con.execute("SELECT count(*) FROM compliance_reviews").fetchone()[0]
        activation = con.execute("SELECT status, verification_status FROM compliance_review_activation_registry").fetchone()
    finally:
        con.close()
    check("no sample review records", samples == 0, samples)
    check("activation metadata verified", activation == ("activation_verified", "verified"), activation)

    repeat_before = sha(apply_db)
    proc = run([sys.executable, str(MIGRATION), "--database", str(apply_db), "--apply", "--activation-token", TOKEN])
    check("repeat apply idempotent exit", proc.returncode == 0, proc.stdout + proc.stderr)
    check("repeat apply unchanged", sha(apply_db) == repeat_before)

    rollback_db = copy_db("rollback.db")
    proc = run([sys.executable, str(MIGRATION), "--database", str(rollback_db), "--apply", "--activation-token", TOKEN], env={"H6B_FORCE_MIGRATION_FAILURE":"after_tables"})
    check("forced rollback fails", proc.returncode != 0, proc.stdout + proc.stderr)
    check("forced rollback leaves no tables", not objects(rollback_db), objects(rollback_db))

    partial_db = copy_db("partial.db")
    con = sqlite3.connect(partial_db)
    con.execute("CREATE TABLE compliance_reviews (id INTEGER PRIMARY KEY)")
    con.commit(); con.close()
    partial_before = sha(partial_db)
    proc = run([sys.executable, str(MIGRATION), "--database", str(partial_db), "--apply", "--activation-token", TOKEN])
    check("partial schema refused", proc.returncode != 0 and "partial_schema_conflict" in proc.stdout, proc.stdout + proc.stderr)
    check("partial schema unchanged", sha(partial_db) == partial_before)

    refused = run([sys.executable, str(MIGRATION), "--database", str(DB), "--dry-run", "--activation-token", TOKEN])
    check("normal trustee_app.db refused", refused.returncode != 0 and "trustee_app.db is refused" in (refused.stdout + refused.stderr))
    missing_token = run([sys.executable, str(MIGRATION), "--database", str(dry), "--dry-run", "--activation-token", "wrong"])
    check("bad activation token refused", missing_token.returncode != 0)

    unactivated = copy_db("unactivated_import.db")
    ok, detail = import_read_only(unactivated)
    check("import read-only unactivated", ok, detail)
    ok, detail = import_read_only(apply_db)
    check("import read-only activated", ok, detail)
    ok, detail = request_check(unactivated, activated=False)
    check("request behavior before activation", ok, detail)
    ok, detail = request_check(apply_db, activated=True)
    check("request behavior after temp activation", ok, detail)
    ok, detail = service_check(apply_db)
    check("temporary service lifecycle validation", ok, detail)

    final_sha = sha(DB)
    final_counts = counts(DB)
    check("normal database sha preserved", final_sha == baseline_sha == EXPECTED_NORMAL_SHA, final_sha)
    check("normal counts preserved", final_counts == baseline_counts, final_counts)
    check("normal compliance objects absent", not objects(DB), objects(DB))
    staged = run(["git", "diff", "--cached", "--name-only"])
    check("staging empty", staged.stdout.strip() == "")

    inventory = []
    for p in sorted(Path(TEMP_ROOT).glob("*.db")):
        inventory.append((p.name, p.stat().st_size, sha(p)))
    print("temporary_database_inventory=" + repr(inventory))
    shutil.rmtree(TEMP_ROOT, ignore_errors=True)
    print("TEMP_ARTIFACTS_REMOVED=" + str(not Path(TEMP_ROOT).exists()))

    print("POST-V2-17Q-H.6B GOVERNED MIGRATION AUDIT")
    if failures:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
