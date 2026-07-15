import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "trustee_app.db"
MIGRATION = ROOT / "migrations" / "activate_compliance_review_foundation.py"
TOKEN = "H6B-TEMPORARY-ACTIVATION"
EXPECTED_SHA = "EF19D33AF0B77E6854CE45538D6DDE30948A6FF8D563F4C7CEBC3CFEDBAEDC13"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def run(args, env=None, timeout=180):
    merged = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(env or {})}
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=timeout, env=merged)


def make_temp_root():
    return Path(tempfile.mkdtemp(prefix="trustee_h6c_"))


def copy_normal(temp_root, name):
    target = temp_root / name
    shutil.copy2(DB, target)
    return target


def activate(path):
    return run([sys.executable, str(MIGRATION), "--database", str(path), "--apply", "--activation-token", TOKEN])


def sqlite_counts(path):
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        cur = con.cursor()
        return {
            "audit": cur.execute("SELECT count(*), coalesce(max(id),0) FROM audit_log").fetchone(),
            "role_permissions": cur.execute("SELECT count(*) FROM role_permissions").fetchone()[0],
            "distinct_pairs": cur.execute("SELECT count(*) FROM (SELECT DISTINCT role_name, permission_name FROM role_permissions)").fetchone()[0],
            "governance": cur.execute("SELECT count(*) FROM governance_relationships").fetchone()[0],
            "ledger": cur.execute("SELECT count(*) FROM governance_relationship_audit_ledger").fetchone()[0],
            "objects": cur.execute("SELECT type,name FROM sqlite_master WHERE lower(name) LIKE '%compliance%' OR lower(name) LIKE '%system_observation%' ORDER BY type,name").fetchall(),
            "integrity": cur.execute("PRAGMA integrity_check").fetchone()[0],
            "fk": cur.execute("PRAGMA foreign_key_check").fetchall(),
        }
    finally:
        con.close()


def actor(actor_id, authorities=None, firm_id="FIRM-002", role=None):
    return {
        "actor_id": actor_id,
        "actor_label": actor_id.title(),
        "actor_role": role or "Compliance",
        "role": role,
        "firm_id": firm_id,
        "scope": {"firm_id": firm_id},
        "authorities": set(authorities or ()),
        "authority_basis": "H.6C temporary validation",
    }


def base_payload(**overrides):
    payload = {
        "firm_id": "FIRM-002",
        "title": "Temporary Trust Administration Review",
        "review_type": "governance_compliance",
        "question_presented": "Does the temporary trust administration workflow satisfy the governing control?",
        "governing_requirement_type": "institutional_policy",
        "governing_requirement_id": "GOV-H6C",
        "source_type": "governance_record",
        "source_id": "GOV-H6C",
        "source_label": "Temporary Governance Control",
        "authority_basis": "H.6C temporary validation authority",
        "primary_subject_type": "trust",
        "primary_subject_id": "TRUST-H6C",
        "primary_subject_label": "Temporary Trust Context",
        "priority": "high",
        "risk_level": "high",
    }
    payload.update(overrides)
    return payload


def authenticated_session(client, firm_id="FIRM-002", authorities=None, role="Compliance"):
    with client.session_transaction() as sess:
        sess.clear()
        sess["username"] = "h6c-user"
        sess["user_id"] = "h6c-user"
        sess["role"] = role
        sess["firm_id"] = firm_id
        sess["compliance_authorities"] = list(authorities or ())
        sess["last_activity"] = datetime.now(timezone.utc).timestamp()


def check(results, name, condition, detail=""):
    print(("PASS" if condition else "FAIL") + " - " + name + ((" | " + str(detail)[:240]) if detail and not condition else ""))
    results.append(bool(condition))


def main():
    results = []
    baseline_sha = sha(DB)
    baseline_counts = sqlite_counts(DB)
    temp_root = make_temp_root()
    print(f"temporary_root={temp_root}")
    try:
        unactivated = copy_normal(temp_root, "unactivated.db")
        activated = copy_normal(temp_root, "activated.db")
        dry = copy_normal(temp_root, "dry.db")
        dry_before = sha(dry)
        dry_proc = run([sys.executable, str(MIGRATION), "--database", str(dry), "--dry-run", "--activation-token", TOKEN])
        check(results, "dry-run read-only", dry_proc.returncode == 0 and sha(dry) == dry_before)
        bad_token = run([sys.executable, str(MIGRATION), "--database", str(copy_normal(temp_root, "bad_token.db")), "--apply", "--activation-token", "bad"])
        check(results, "invalid activation token refused", bad_token.returncode != 0)
        normal_refused = run([sys.executable, str(MIGRATION), "--database", str(DB), "--apply", "--activation-token", TOKEN])
        check(results, "normal database refused", normal_refused.returncode != 0)
        apply_proc = activate(activated)
        check(results, "temporary activation succeeds", apply_proc.returncode == 0, apply_proc.stdout + apply_proc.stderr)
        con = sqlite3.connect(f"file:{activated.as_posix()}?mode=ro", uri=True)
        try:
            activation = con.execute("SELECT status, verification_status FROM compliance_review_activation_registry").fetchone()
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'compliance_review%'")}
        finally:
            con.close()
        check(results, "activation registry verified", activation == ("activation_verified", "verified"), activation)
        check(results, "expected activated schema present", "compliance_review_audit_ledger" in tables and "compliance_review_evidence" in tables, tables)

        code = """
import hashlib, pathlib, os, sys
sys.path.insert(0, sys.argv[1])
p=pathlib.Path(os.environ['DB_PATH'])
b=hashlib.sha256(p.read_bytes()).hexdigest().upper()
import app
a=hashlib.sha256(p.read_bytes()).hexdigest().upper()
print(b==a)
"""
        for label, path in (("unactivated", unactivated), ("activated", activated)):
            proc = run([sys.executable, "-c", code, str(ROOT)], env={"DB_PATH": str(path)})
            check(results, f"import read-only {label}", proc.returncode == 0 and proc.stdout.strip().endswith("True"), proc.stdout + proc.stderr)

        route_code = """
import os, sys, hashlib, pathlib
from datetime import datetime, timezone
sys.path.insert(0, sys.argv[1])
import app as app_module
app = app_module.app
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
client = app.test_client()
def auth(authorities=None, firm='FIRM-002'):
    with client.session_transaction() as sess:
        sess.clear(); sess['username']='h6c-user'; sess['user_id']='h6c-user'; sess['role']='Compliance'; sess['firm_id']=firm; sess['compliance_authorities']=list(authorities or ()); sess['_csrf_token']='csrf-h6c'; sess['last_activity']=datetime.now(timezone.utc).timestamp()
payload={'_csrf_token':'csrf-h6c','firm_id':'FIRM-002','title':'Route Review','review_type':'governance_compliance','question_presented':'Q','governing_requirement_type':'institutional_policy','governing_requirement_id':'GOV','source_type':'governance_record','source_id':'GOV','authority_basis':'route','primary_subject_type':'trust','primary_subject_id':'TR'}
before=hashlib.sha256(pathlib.Path(os.environ['DB_PATH']).read_bytes()).hexdigest().upper()
auth(); print('post_unauthz', client.post('/compliance/reviews', json=payload).status_code)
auth({'create_review'}); print('post_invalid', client.post('/compliance/reviews', json={'_csrf_token':'csrf-h6c','firm_id':'FIRM-002'}).status_code)
auth({'create_review'}); created=client.post('/compliance/reviews', json=payload); print('post_valid', created.status_code); body=created.get_json(silent=True) or {}; rid=body.get('review',{}).get('compliance_review_id')
print('registry', client.get('/compliance/reviews').status_code)
print('detail', client.get('/compliance/reviews/'+rid).status_code if rid else 'missing')
print('missing', client.get('/compliance/reviews/CMP-2026-9999').status_code)
auth({'create_review'}, 'FIRM-003'); print('cross', client.get('/compliance/reviews/'+rid).status_code if rid else 'missing')
after=hashlib.sha256(pathlib.Path(os.environ['DB_PATH']).read_bytes()).hexdigest().upper()
print('changed', before != after)
"""
        route_unactivated = run([sys.executable, "-c", route_code, str(ROOT)], env={"DB_PATH": str(unactivated)})
        check(results, "route before activation bounded", "registry 503" in route_unactivated.stdout and "post_valid 503" in route_unactivated.stdout, route_unactivated.stdout + route_unactivated.stderr)
        route_activated = run([sys.executable, "-c", route_code, str(ROOT)], env={"DB_PATH": str(activated)})
        route_out = route_activated.stdout
        check(results, "route after activation semantics", all(token in route_out for token in ["post_unauthz 403", "post_invalid 400", "post_valid 201", "registry 200", "detail 200", "missing 404"]) and ("cross 404" in route_out or "cross 403" in route_out), route_out + route_activated.stderr)

        final_sha = sha(DB)
        final_counts = sqlite_counts(DB)
        check(results, "normal database sha preserved", final_sha == baseline_sha == EXPECTED_SHA, final_sha)
        check(results, "normal database content preserved", final_counts == baseline_counts, final_counts)
        check(results, "normal database unactivated", final_counts["objects"] == [], final_counts["objects"])
        staged = run(["git", "diff", "--cached", "--name-only"])
        check(results, "staging empty", staged.stdout.strip() == "")
        inventory = [(p.name, p.stat().st_size, sha(p)) for p in sorted(temp_root.glob("*.db"))]
        print("temporary_database_inventory=" + repr(inventory))
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
    print("TEMP_ARTIFACTS_REMOVED=" + str(not temp_root.exists()))
    print("POST-V2-17Q-H.6C TEMPORARY ACTIVATION AUDIT")
    if not all(results):
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
