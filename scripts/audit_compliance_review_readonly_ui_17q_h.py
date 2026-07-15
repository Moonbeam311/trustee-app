import hashlib
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "trustee_app.db"
EXPECTED_SHA = "EF19D33AF0B77E6854CE45538D6DDE30948A6FF8D563F4C7CEBC3CFEDBAEDC13"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def run(args, env=None):
    merged = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(env or {})}
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=180, env=merged)


def normal_counts():
    con = sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        cur = con.cursor()
        return {
            "audit": cur.execute("SELECT count(*), coalesce(max(id),0) FROM audit_log").fetchone(),
            "roles": cur.execute("SELECT count(*) FROM role_permissions").fetchone()[0],
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


def check(results, name, condition, detail=""):
    print(("PASS" if condition else "FAIL") + " - " + name + ((" | " + str(detail)[:240]) if detail and not condition else ""))
    results.append(bool(condition))


def main():
    results = []
    before_sha = sha(DB)
    before_counts = normal_counts()
    temp_root = Path(tempfile.mkdtemp(prefix="trustee_h_readonly_"))
    temp_db = temp_root / "unactivated.db"
    shutil.copy2(DB, temp_db)
    try:
        env = {"DB_PATH": str(temp_db)}
        code = r'''
import hashlib
import os
import pathlib
import re
import sys
from datetime import datetime, timezone
from unittest.mock import patch

root = pathlib.Path(sys.argv[1])
db = pathlib.Path(os.environ["DB_PATH"])
before = hashlib.sha256(db.read_bytes()).hexdigest().upper()
sys.path.insert(0, str(root))
import app as app_module

app = app_module.app
app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()

def auth(firm="FIRM-002"):
    with client.session_transaction() as sess:
        sess.clear()
        sess["username"] = "h-readonly"
        sess["user_id"] = "h-readonly"
        sess["role"] = "Compliance"
        sess["firm_id"] = firm
        sess["_csrf_token"] = "csrf-h"
        sess["last_activity"] = datetime.now(timezone.utc).timestamp()

rules = [r for r in app.url_map.iter_rules() if r.rule.startswith("/compliance/reviews")]
route_summary = sorted((r.endpoint, r.rule, tuple(sorted(r.methods))) for r in rules)
auth()
registry = client.get("/compliance/reviews")
detail = client.get("/compliance/reviews/CMP-2026-0001")
create = client.get("/compliance/reviews/new")
post = client.post("/compliance/reviews", data={"_csrf_token": "csrf-h", "firm_id": "FIRM-002"})
unauth = app.test_client().get("/compliance/reviews")
after = hashlib.sha256(db.read_bytes()).hexdigest().upper()
app_source = (root / "app.py").read_text(encoding="utf-8")
route_block = app_source[app_source.index("def _compliance_review_read_scope"):app_source.index("def _system_observation_read_scope")]
registry_source = (root / "templates/compliance_reviews/registry.html").read_text(encoding="utf-8")
detail_source = (root / "templates/compliance_reviews/detail.html").read_text(encoding="utf-8")
create_source = (root / "templates/compliance_reviews/create.html").read_text(encoding="utf-8")
print({
    "registry": registry.status_code,
    "detail": detail.status_code,
    "create": create.status_code,
    "post": post.status_code,
    "unauth_redirect": unauth.status_code in {301,302,303,307,308},
    "db_unchanged": before == after,
    "route_summary": route_summary,
    "csrf_exempt": "@csrf.exempt" in route_block,
    "migration_call": bool(re.search(r"\b(migrate|migration|upgrade)\s*\(", route_block)),
    "schema_call": "create_all" in route_block or "ensure_compliance_review_foundation" in route_block,
    "raw_sql": bool(re.search(r"\b(INSERT|DELETE)\b", route_block, re.I)),
    "registry_safe": "<form" not in registry_source.lower() and "csrf" not in registry_source.lower(),
    "detail_controls": "<form" in detail_source.lower() and "expected_version" in detail_source and "csrf_token()" in detail_source,
    "create_controls": "<form" in create_source.lower() and "csrf_token()" in create_source,
    "escapes": "|safe" not in registry_source.replace(" ", "").lower() and "|safe" not in detail_source.replace(" ", "").lower(),
})
'''
        proc = run([sys.executable, "-c", code, str(ROOT)], env=env)
        output = proc.stdout + proc.stderr
        print(output)
        check(results, "isolated route probe exits clean", proc.returncode == 0, output)
        check(results, "unactivated registry and detail remain 503", "'registry': 503" in output and "'detail': 503" in output, output)
        check(results, "unactivated create and write fail closed", "'create': 503" in output and "'post': 503" in output, output)
        check(results, "authentication still required", "'unauth_redirect': True" in output, output)
        check(results, "route probe database unchanged", "'db_unchanged': True" in output, output)
        check(results, "no Compliance route CSRF exemption", "'csrf_exempt': False" in output, output)
        check(results, "no Compliance route migration or schema creation", "'migration_call': False" in output and "'schema_call': False" in output, output)
        check(results, "no raw Compliance INSERT/DELETE in route layer", "'raw_sql': False" in output, output)
        check(results, "registry remains read-only", "'registry_safe': True" in output, output)
        check(results, "H.6D forms expose request controls", "'detail_controls': True" in output and "'create_controls': True" in output, output)
        check(results, "templates avoid safe filter", "'escapes': True" in output, output)

        app_text = (ROOT / "app.py").read_text(encoding="utf-8")
        public_match = re.search(r"public_endpoints\s*=\s*\{(.*?)\}", app_text, re.S)
        public_text = public_match.group(1) if public_match else ""
        check(results, "Compliance endpoints are not public", "compliance_review_" not in public_text, public_text)
        check(results, "normal database sha preserved", sha(DB) == before_sha == EXPECTED_SHA, sha(DB))
        check(results, "normal database content preserved", normal_counts() == before_counts, normal_counts())
        staged = run(["git", "diff", "--cached", "--name-only"])
        check(results, "staging empty", staged.stdout.strip() == "")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
    print("TEMP_ARTIFACTS_REMOVED=" + str(not temp_root.exists()))
    print("POST-V2-17Q-H RESULT")
    if not all(results):
        print("FAIL")
        return 1
    print("PASS - Compliance Review unavailable-state reads remain bounded and non-mutating while H.6D temporary write-route controls are present only behind authenticated, CSRF-protected service routes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
