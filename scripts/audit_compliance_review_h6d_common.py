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
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def run(args, env=None, timeout=180):
    merged = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(env or {})}
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=timeout, env=merged)


def db_counts(path):
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
            "objects": cur.execute("SELECT type,name FROM sqlite_master WHERE lower(name) LIKE '%compliance%' OR lower(name) LIKE '%system_observation%' ORDER BY type,name").fetchall(),
            "integrity": cur.execute("PRAGMA integrity_check").fetchone()[0],
            "fk": cur.execute("PRAGMA foreign_key_check").fetchall(),
        }
    finally:
        con.close()


def print_check(results, name, condition, detail=""):
    print(("PASS" if condition else "FAIL") + " - " + name + ((" | " + str(detail)[:300]) if detail and not condition else ""))
    results.append(bool(condition))


def _scenario_code():
    return r'''
import hashlib
import os
import pathlib
import re
import sqlite3
import sys
from datetime import datetime, timezone

sys.path.insert(0, sys.argv[1])
import app as app_module

app = app_module.app
app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()
db_path = pathlib.Path(os.environ["DB_PATH"])

def digest():
    return hashlib.sha256(db_path.read_bytes()).hexdigest().upper()

def auth(authorities=None, firm="FIRM-002", user="h6d-maker", role="Compliance"):
    with client.session_transaction() as sess:
        sess.clear()
        sess["username"] = user
        sess["user_id"] = user
        sess["role"] = role
        sess["firm_id"] = firm
        sess["compliance_authorities"] = list(authorities or ())
        sess["_csrf_token"] = "csrf-h6d"
        sess["last_activity"] = datetime.now(timezone.utc).timestamp()

def post(path, data, authorities=None, firm="FIRM-002", user="h6d-maker"):
    auth(authorities or {"compliance_admin"}, firm=firm, user=user)
    payload = {"_csrf_token": "csrf-h6d", **data}
    return client.post(path, data=payload, follow_redirects=False)

def create_review(user="h6d-maker", title="H6D Temporary Review"):
    data = {
        "firm_id": "FIRM-002",
        "title": title,
        "review_type": "governance_compliance",
        "purpose": "Temporary H.6D request workflow validation.",
        "scope": "Temporary activated database only.",
        "review_standard": "H6D",
        "question_presented": "Does the temporary operator workflow preserve governed controls?",
        "governing_requirement_type": "institutional_policy",
        "governing_requirement_id": "GOV-H6D",
        "source_type": "governance_record",
        "source_id": "GOV-H6D",
        "authority_basis": "H6D temporary authority",
        "primary_subject_type": "trust",
        "primary_subject_id": "TRUST-H6D",
        "primary_subject_label": "Temporary trust context",
        "risk_level": "high",
        "priority": "high",
        "confidentiality_level": "internal",
        "idempotency_key": title.lower().replace(" ", "-"),
    }
    response = post("/compliance/reviews", data, {"create_review"}, user=user)
    body = response.get_json(silent=True) or {}
    return response, body.get("review", {}).get("compliance_review_id")

def token_from(body):
    match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', body)
    return match.group(1) if match else None

results = {}
before = digest()

auth({"create_review"})
results["registry_get"] = client.get("/compliance/reviews").status_code
results["new_get"] = client.get("/compliance/reviews/new").status_code
results["create_has_csrf"] = 'name="_csrf_token"' in client.get("/compliance/reviews/new").get_data(as_text=True)
results["missing_csrf"] = client.post("/compliance/reviews", data={"firm_id": "FIRM-002"}).status_code
bad = post("/compliance/reviews", {"firm_id": "FIRM-002", "authority_basis": "H6D"}, {"create_review"})
results["invalid_create"] = bad.status_code
created, rid = create_review()
results["valid_create"] = created.status_code
results["detail_get"] = client.get(f"/compliance/reviews/{rid}").status_code
detail_body = client.get(f"/compliance/reviews/{rid}").get_data(as_text=True)
results["detail_has_forms"] = "<form" in detail_body and "expected_version" in detail_body and "confirm_action" in detail_body
auth({"create_review"}, firm="FIRM-003")
results["wrong_firm"] = client.get(f"/compliance/reviews/{rid}").status_code

version = "1"
results["stale_update"] = post(f"/compliance/reviews/{rid}/update", {"expected_version": "0", "title": "stale", "authority_basis": "H6D"}, {"edit_draft"}).status_code
results["valid_update"] = post(f"/compliance/reviews/{rid}/update", {"expected_version": version, "title": "H6D Updated Review", "authority_basis": "H6D"}, {"edit_draft"}).status_code
version = "2"
results["assign"] = post(f"/compliance/reviews/{rid}/assign", {"expected_version": version, "assigned_reviewer": "h6d-reviewer", "authority_basis": "H6D"}, {"assign_reviewer"}).status_code
version = "3"
results["open"] = post(f"/compliance/reviews/{rid}/open", {"expected_version": version, "authority_basis": "H6D"}, {"open_review"}).status_code

import services.services_compliance_reviews as svc
review = svc.get_compliance_review(rid, scope={"firm_id": "FIRM-002"})
results["add_subject"] = post(f"/compliance/reviews/{rid}/subjects", {"expected_version": str(review["version"]), "subject_type": "Matter", "subject_id": "MAT-H6D", "subject_label": "Matter context", "authority_basis": "H6D"}, {"add_subject"}).status_code
review = svc.get_compliance_review(rid, scope={"firm_id": "FIRM-002"})
results["add_relationship"] = post(f"/compliance/reviews/{rid}/relationships", {"expected_version": str(review["version"]), "related_record_type": "Governance", "related_record_id": "GOV-H6D", "relationship_type": "documents", "authority_basis": "H6D"}, {"add_relationship"}).status_code
review = svc.get_compliance_review(rid, scope={"firm_id": "FIRM-002"})
results["add_evidence"] = post(f"/compliance/reviews/{rid}/evidence", {"expected_version": str(review["version"]), "evidence_type": "Document", "source_type": "Governance", "source_id": "GOV-H6D", "description": "Evidence package", "authority_basis": "H6D"}, {"add_evidence"}).status_code
review = svc.get_compliance_review(rid, scope={"firm_id": "FIRM-002"})
con = sqlite3.connect(os.environ["DB_PATH"])
con.row_factory = sqlite3.Row
evidence = con.execute("SELECT compliance_evidence_id FROM compliance_review_evidence WHERE compliance_review_id=?", (rid,)).fetchone()["compliance_evidence_id"]
con.close()
results["self_evidence_verify"] = post(f"/compliance/reviews/{rid}/evidence/{evidence}/verify", {"expected_version": str(review["version"]), "verification_basis": "basis", "authority_basis": "H6D"}, {"verify_evidence"}, user="h6d-maker").status_code
results["verify_evidence"] = post(f"/compliance/reviews/{rid}/evidence/{evidence}/verify", {"expected_version": str(review["version"]), "verification_basis": "basis", "authority_basis": "H6D"}, {"verify_evidence"}, user="h6d-checker").status_code
results["start_review"] = post(f"/compliance/reviews/{rid}/open", {"expected_version": str(review["version"]), "authority_basis": "H6D"}, {"open_review"}).status_code

review = svc.get_compliance_review(rid, scope={"firm_id": "FIRM-002"})
finding_payload = {"expected_version": str(review["version"]), "finding_type": "Documentation Gap", "title": "Gap", "evidence_basis": evidence, "severity": "medium", "risk_level": "moderate", "authority_basis": "H6D", "confirm_action": "issue"}
results["issue_finding"] = post(f"/compliance/reviews/{rid}/findings", finding_payload, {"issue_findings"}).status_code
con = sqlite3.connect(os.environ["DB_PATH"]); con.row_factory = sqlite3.Row
finding = con.execute("SELECT compliance_finding_id FROM compliance_review_findings WHERE compliance_review_id=?", (rid,)).fetchone()["compliance_finding_id"]
con.close()
review = svc.get_compliance_review(rid, scope={"firm_id": "FIRM-002"})
results["ack_finding"] = post(f"/compliance/reviews/{rid}/findings/{finding}/acknowledge", {"expected_version": str(review["version"]), "authority_basis": "H6D"}, {"acknowledge_findings"}).status_code
review = svc.get_compliance_review(rid, scope={"firm_id": "FIRM-002"})
results["assign_remediation"] = post(f"/compliance/reviews/{rid}/remediations", {"expected_version": str(review["version"]), "compliance_finding_id": finding, "required_action": "Upload missing evidence", "responsible_party_type": "operator", "authority_basis": "H6D"}, {"assign_remediation"}).status_code
con = sqlite3.connect(os.environ["DB_PATH"]); con.row_factory = sqlite3.Row
remediation = con.execute("SELECT compliance_remediation_id FROM compliance_review_remediations WHERE compliance_review_id=?", (rid,)).fetchone()["compliance_remediation_id"]
con.close()
review = svc.get_compliance_review(rid, scope={"firm_id": "FIRM-002"})
results["submit_remediation"] = post(f"/compliance/reviews/{rid}/remediations/{remediation}/submit", {"expected_version": str(review["version"]), "completion_evidence": "Completed evidence", "authority_basis": "H6D"}, {"submit_remediation"}, user="h6d-submitter").status_code
review = svc.get_compliance_review(rid, scope={"firm_id": "FIRM-002"})
results["self_remediation_verify"] = post(f"/compliance/reviews/{rid}/remediations/{remediation}/verify", {"expected_version": str(review["version"]), "authority_basis": "H6D"}, {"verify_remediation"}, user="h6d-submitter").status_code
results["verify_remediation"] = post(f"/compliance/reviews/{rid}/remediations/{remediation}/verify", {"expected_version": str(review["version"]), "authority_basis": "H6D"}, {"verify_remediation"}, user="h6d-checker").status_code
review = svc.get_compliance_review(rid, scope={"firm_id": "FIRM-002"})
results["missing_confirm_approval"] = post(f"/compliance/reviews/{rid}/approve", {"expected_version": str(review["version"]), "authority_basis": "H6D"}, {"approve_review"}, user="h6d-checker").status_code
results["approve"] = post(f"/compliance/reviews/{rid}/approve", {"expected_version": str(review["version"]), "authority_basis": "H6D", "confirm_action": "approve"}, {"approve_review"}, user="h6d-checker").status_code
review = svc.get_compliance_review(rid, scope={"firm_id": "FIRM-002"})
results["certify"] = post(f"/compliance/reviews/{rid}/certify", {"expected_version": str(review["version"]), "certification_statement": "Certified for temporary validation.", "authority_basis": "H6D", "confirm_action": "certify"}, {"certify_review"}, user="h6d-certifier").status_code
review = svc.get_compliance_review(rid, scope={"firm_id": "FIRM-002"})
results["close"] = post(f"/compliance/reviews/{rid}/close", {"expected_version": str(review["version"]), "authority_basis": "H6D", "confirm_action": "close"}, {"close_review"}, user="h6d-closer").status_code
review = svc.get_compliance_review(rid, scope={"firm_id": "FIRM-002"})
results["reopen_no_reason"] = post(f"/compliance/reviews/{rid}/reopen", {"expected_version": str(review["version"]), "authority_basis": "H6D", "confirm_action": "reopen"}, {"reopen_review"}, user="h6d-closer").status_code
results["reopen"] = post(f"/compliance/reviews/{rid}/reopen", {"expected_version": str(review["version"]), "reason": "New evidence", "authority_basis": "H6D", "confirm_action": "reopen"}, {"reopen_review"}, user="h6d-closer").status_code
created2, rid2 = create_review(user="h6d-other", title="H6D Successor Review")
review = svc.get_compliance_review(rid, scope={"firm_id": "FIRM-002"})
results["supersede"] = post(f"/compliance/reviews/{rid}/supersede", {"expected_version": str(review["version"]), "successor_review_id": rid2, "authority_basis": "H6D", "confirm_action": "supersede"}, {"supersede_review"}, user="h6d-closer").status_code
results["archived_mutation"] = post(f"/compliance/reviews/{rid}/update", {"expected_version": str(int(review["version"])+1), "title": "blocked", "authority_basis": "H6D"}, {"edit_draft"}, user="h6d-closer").status_code
results["audit_chain"] = svc.verify_compliance_audit_chain(firm_id="FIRM-002").get("ok")
after = digest()
results["db_changed"] = before != after
print(results)
'''


def execute_h6d_scenario(temp_root, activated_db):
    proc = run([sys.executable, "-c", _scenario_code(), str(ROOT)], env={"DB_PATH": str(activated_db)}, timeout=240)
    return proc


def prepare_temp_db():
    temp_root = Path(tempfile.mkdtemp(prefix="trustee_h6d_"))
    activated = temp_root / "activated.db"
    shutil.copy2(DB, activated)
    proc = run([sys.executable, str(MIGRATION), "--database", str(activated), "--apply", "--activation-token", TOKEN])
    return temp_root, activated, proc


def cleanup(temp_root):
    inventory = []
    if temp_root.exists():
        inventory = [(p.name, p.stat().st_size, sha(p)) for p in sorted(temp_root.glob("*.db"))]
    shutil.rmtree(temp_root, ignore_errors=True)
    return inventory, not temp_root.exists()


def normal_db_ok():
    counts = db_counts(DB)
    return (
        sha(DB) == EXPECTED_SHA
        and counts["audit"] == (513, 513)
        and counts["role_permissions"] == 25
        and counts["pairs"] == 25
        and counts["dupes"] == 0
        and counts["governance"] == 25
        and counts["ledger"] == 51
        and counts["objects"] == []
        and counts["integrity"] == "ok"
        and counts["fk"] == []
    )


def run_audit(label, extra_checks):
    results = []
    baseline_sha = sha(DB)
    baseline_counts = db_counts(DB)
    temp_root, activated, activation = prepare_temp_db()
    print(f"temporary_root={temp_root}")
    try:
        print_check(results, "temporary activation succeeds", activation.returncode == 0, activation.stdout + activation.stderr)
        proc = execute_h6d_scenario(temp_root, activated)
        output = proc.stdout + proc.stderr
        print(output)
        print_check(results, "request scenario process exits clean", proc.returncode == 0, output)
        for name, predicate in extra_checks.items():
            print_check(results, name, predicate(output), output)
        print_check(results, "normal database sha preserved", sha(DB) == baseline_sha == EXPECTED_SHA, sha(DB))
        print_check(results, "normal database content preserved", db_counts(DB) == baseline_counts and normal_db_ok(), db_counts(DB))
        staged = run(["git", "diff", "--cached", "--name-only"])
        print_check(results, "staging empty", staged.stdout.strip() == "")
        inventory, removed = cleanup(temp_root)
        print("temporary_database_inventory=" + repr(inventory))
        print("TEMP_ARTIFACTS_REMOVED=" + str(removed))
        print(f"POST-V2-17Q-H.6D {label}")
        if not all(results):
            print("RESULT: FAIL")
            return 1
        print("RESULT: PASS")
        return 0
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, ignore_errors=True)
