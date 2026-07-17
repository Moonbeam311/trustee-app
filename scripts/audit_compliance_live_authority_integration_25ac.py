"""STEP 25AC live Compliance authority integration audit.

All route and workflow checks run against disposable temporary databases.
The repository active database and active policy file are inspected read-only.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ACTIVE_DB = ROOT / "trustee_app.db"
EXPORT_POLICY = ROOT / "data" / "export_policy.json"
PERMISSION_MIGRATION = ROOT / "migrations" / "add_compliance_review_permissions.py"
ACTIVATION_MIGRATION = ROOT / "migrations" / "activate_compliance_review_foundation.py"
PERMISSION_TOKEN = "H6E-TEMPORARY-PERMISSION-GOVERNANCE"
ACTIVATION_TOKEN = "H6B-TEMPORARY-ACTIVATION"
ARTIFACT_DIR = ROOT / "test_artifacts" / "step25ac"

failures: list[str] = []
results: list[dict[str, object]] = []


def write_report(report: dict[str, object]) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = ARTIFACT_DIR / "step25ac_report.json"
    try:
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
        return report_path
    except PermissionError:
        stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        fallback = ARTIFACT_DIR / f"step25ac_report_{stamp}.json"
        try:
            fallback.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
            return fallback
        except PermissionError:
            temp_fallback = Path(tempfile.gettempdir()) / f"step25ac_report_{stamp}.json"
            temp_fallback.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
            return temp_fallback


def sha(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def manifest(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"path": str(path), "exists": False}
    stat = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha(path),
    }


def active_counts() -> dict[str, object]:
    con = sqlite3.connect(f"file:{ACTIVE_DB.as_posix()}?mode=ro", uri=True)
    try:
        cur = con.cursor()
        return {
            "audit_log": cur.execute("SELECT count(*), coalesce(max(id),0) FROM audit_log").fetchone(),
            "permissions": cur.execute("SELECT count(*) FROM permissions").fetchone()[0],
            "role_permissions": cur.execute("SELECT count(*) FROM role_permissions").fetchone()[0],
            "user_permission_overrides": cur.execute("SELECT count(*) FROM user_permission_overrides").fetchone()[0],
            "compliance_objects": cur.execute("SELECT name FROM sqlite_master WHERE lower(name) LIKE '%compliance%' ORDER BY name").fetchall(),
            "integrity": cur.execute("PRAGMA integrity_check").fetchone()[0],
            "fk": cur.execute("PRAGMA foreign_key_check").fetchall(),
        }
    finally:
        con.close()


def run(cmd: list[str], *, env: dict[str, str] | None = None, timeout: int = 240) -> subprocess.CompletedProcess[str]:
    merged = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(env or {})}
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout, env=merged)


def check(name: str, condition: bool, detail: object = "") -> None:
    print(("PASS" if condition else "FAIL") + " - " + name + ((" | " + str(detail)[:700]) if detail and not condition else ""))
    results.append({"name": name, "pass": bool(condition), "detail": detail})
    if not condition:
        failures.append(name)


def prepare_activated_db(temp_root: Path) -> Path:
    db = temp_root / "live_authority.db"
    shutil.copy2(ACTIVE_DB, db)
    activation = run([
        sys.executable,
        str(ACTIVATION_MIGRATION),
        "--database",
        str(db),
        "--apply",
        "--activation-token",
        ACTIVATION_TOKEN,
    ])
    if activation.returncode != 0:
        raise RuntimeError(activation.stdout + activation.stderr)
    return db


def seed_live_authority_users(db: Path) -> None:
    con = sqlite3.connect(db)
    try:
        con.executemany(
            """
            INSERT OR REPLACE INTO permissions (permission_id, permission_name, description)
            VALUES (?, ?, ?)
            """,
            [
                ("T25AC-001", "view_all_compliance_reviews", "Temp global read"),
                ("T25AC-002", "create_compliance_review", "Temp create"),
                ("T25AC-003", "open_compliance_review", "Temp open"),
                ("T25AC-004", "approve_compliance_review", "Temp approve"),
                ("T25AC-005", "certify_compliance_review", "Temp certify"),
                ("T25AC-006", "close_compliance_review", "Temp close"),
                ("T25AC-007", "reopen_compliance_review", "Temp reopen"),
                ("T25AC-008", "supersede_compliance_review", "Temp supersede"),
                ("T25AC-009", "archive_compliance_review", "Temp archive"),
                ("T25AC-010", "add_compliance_evidence", "Temp evidence"),
                ("T25AC-011", "verify_compliance_evidence", "Temp verify evidence"),
                ("T25AC-012", "issue_compliance_findings", "Temp finding"),
                ("T25AC-013", "acknowledge_compliance_findings", "Temp acknowledge"),
                ("T25AC-014", "manage_compliance_remediation", "Temp remediation"),
                ("T25AC-015", "submit_compliance_remediation", "Temp submit"),
                ("T25AC-016", "verify_compliance_remediation", "Temp verify remediation"),
                ("T25AC-017", "request_compliance_exception", "Temp request exception"),
                ("T25AC-018", "approve_compliance_exception", "Temp approve exception"),
                ("T25AC-019", "view_documents", "Temp unrelated"),
            ],
        )
        users = [
            ("U25-001", "viewer-none", "Viewer", "FIRM-001"),
            ("U25-002", "trustee-none", "Trustee", "FIRM-001"),
            ("U25-003", "admin-none", "Admin", "FIRM-001"),
            ("U25-004", "admin", "Admin", "FIRM-001"),
            ("U25-005", "master-reader", "Admin", "FIRM-001"),
            ("U25-006", "creator", "ComplianceCreator", "FIRM-001"),
            ("U25-007", "wrong-perm", "ComplianceWrong", "FIRM-001"),
            ("U25-008", "approver", "ComplianceApprover", "FIRM-001"),
            ("U25-009", "certifier", "ComplianceCertifier", "FIRM-001"),
            ("U25-010", "closer", "ComplianceCloser", "FIRM-001"),
            ("U25-011", "firm2-creator", "ComplianceCreator", "FIRM-002"),
            ("U25-012", "inactive", "ComplianceCreator", "FIRM-001"),
            ("U25-013", "opener", "ComplianceOpener", "FIRM-001"),
            ("U25-014", "archiver", "ComplianceArchiver", "FIRM-001"),
        ]
        con.executemany(
            """
            INSERT OR REPLACE INTO app_users (user_id, username, role_name, status, firm_id)
            VALUES (?, ?, ?, CASE WHEN ? = 'inactive' THEN 'inactive' ELSE 'active' END, ?)
            """,
            [(uid, username, role, username, firm) for uid, username, role, firm in users],
        )
        role_permissions = [
            ("ComplianceCreator", "create_compliance_review"),
            ("ComplianceOpener", "open_compliance_review"),
            ("ComplianceWrong", "view_documents"),
            ("ComplianceApprover", "approve_compliance_review"),
            ("ComplianceCertifier", "certify_compliance_review"),
            ("ComplianceCloser", "close_compliance_review"),
            ("ComplianceCloser", "reopen_compliance_review"),
            ("ComplianceCloser", "supersede_compliance_review"),
            ("ComplianceArchiver", "archive_compliance_review"),
            ("Admin", "view_documents"),
        ]
        con.executemany(
            "INSERT OR IGNORE INTO role_permissions (role_name, permission_name) VALUES (?, ?)",
            role_permissions,
        )
        con.execute(
            "INSERT OR IGNORE INTO user_permission_overrides (username, permission_name, effect) VALUES ('master-reader', 'view_all_compliance_reviews', 'allow')"
        )
        con.commit()
    finally:
        con.close()


def migration_rehearsal(temp_root: Path) -> dict[str, object]:
    db = temp_root / "permission_rehearsal.db"
    con = sqlite3.connect(db)
    try:
        con.executescript(
            """
            CREATE TABLE permissions (
                permission_id TEXT PRIMARY KEY,
                permission_name TEXT UNIQUE,
                description TEXT
            );
            CREATE TABLE role_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT,
                permission_name TEXT
            );
            CREATE UNIQUE INDEX ux_role_permissions_role_permission
                ON role_permissions(role_name, permission_name);
            """
        )
        con.commit()
    finally:
        con.close()
    dry = run([sys.executable, str(PERMISSION_MIGRATION), "--database", str(db), "--dry-run", "--authorization-token", PERMISSION_TOKEN])
    apply = run([sys.executable, str(PERMISSION_MIGRATION), "--database", str(db), "--apply", "--authorization-token", PERMISSION_TOKEN])
    after_apply = sha(db)
    repeat = run([sys.executable, str(PERMISSION_MIGRATION), "--database", str(db), "--apply", "--authorization-token", PERMISSION_TOKEN])
    after_repeat = sha(db)
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        permission_names = [row[0] for row in con.execute("SELECT permission_name FROM permissions ORDER BY permission_name")]
        role_pairs = [tuple(row) for row in con.execute("SELECT role_name, permission_name FROM role_permissions ORDER BY role_name, permission_name")]
    finally:
        con.close()
    sensitive_defaults = [
        pair for pair in role_pairs
        if pair[1] in {
            "verify_compliance_evidence",
            "acknowledge_compliance_findings",
            "verify_compliance_remediation",
            "request_compliance_exception",
            "approve_compliance_exception",
            "approve_compliance_review",
            "certify_compliance_review",
            "reopen_compliance_review",
            "supersede_compliance_review",
            "archive_compliance_review",
            "view_all_compliance_reviews",
        }
    ]
    required = {
        "acknowledge_compliance_findings",
        "open_compliance_review",
        "request_compliance_exception",
        "view_all_compliance_reviews",
    }
    result = {
        "dry_run": dry.returncode,
        "apply": apply.returncode,
        "repeat": repeat.returncode,
        "idempotent": after_apply == after_repeat,
        "permission_count": len(permission_names),
        "role_pair_count": len(role_pairs),
        "required_present": sorted(required.intersection(permission_names)),
        "sensitive_defaults": sensitive_defaults,
    }
    check("permission migration dry-run succeeds", dry.returncode == 0, dry.stdout + dry.stderr)
    check("permission migration apply succeeds", apply.returncode == 0, apply.stdout + apply.stderr)
    check("permission migration repeat idempotent", repeat.returncode == 0 and result["idempotent"], result)
    check("aligned permissions present", required.issubset(set(permission_names)), result)
    check("no sensitive default grants", sensitive_defaults == [], result)
    return result


def route_and_service_tests(db: Path, temp_root: Path) -> dict[str, object]:
    code = r"""
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, sys.argv[1])
from app import app

app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False
client = app.test_client()

def auth(username, role=None, firm="FIRM-001", master=False, csrf=True):
    with client.session_transaction() as sess:
        sess.clear()
        sess["username"] = username
        sess["role"] = role or "Admin"
        sess["firm_id"] = firm
        sess["last_activity"] = datetime.now(timezone.utc).timestamp()
        if master:
            sess["is_master_admin"] = True
        if csrf:
            sess["_csrf_token"] = "csrf-25ac"

def payload(**extra):
    data = {
        "_csrf_token": "csrf-25ac",
        "firm_id": "FIRM-001",
        "title": "25AC Live Authority Review",
        "review_type": "governance_compliance",
        "question_presented": "Does 25AC enforce authority?",
        "governing_requirement_type": "institutional_policy",
        "governing_requirement_id": "GOV-25AC",
        "source_type": "governance_record",
        "source_id": "GOV-25AC",
        "authority_basis": "25AC isolated authority",
        "idempotency_key": extra.pop("idempotency_key", "25ac-create"),
    }
    data.update(extra)
    return data

def create_as(username, *, role="Admin", firm="FIRM-001", master=False, data=None):
    auth(username, role=role, firm=firm, master=master)
    return client.post("/compliance/reviews", data=data or payload(), follow_redirects=False)

results = {}
for name in ["viewer-none", "trustee-none", "admin-none", "admin"]:
    response = create_as(name)
    results[f"{name}_create"] = response.status_code

results["master_reader_create"] = create_as("master-reader", master=True).status_code
results["wrong_permission_create"] = create_as("wrong-perm").status_code
results["authority_basis_only_denied"] = create_as("admin-none", data=payload(authority_basis="I assert authority")).status_code
results["missing_basis"] = create_as("creator", role="ComplianceCreator", data=payload(authority_basis="")).status_code
results["cross_firm_create"] = create_as("creator", role="ComplianceCreator", data=payload(firm_id="FIRM-002", idempotency_key="25ac-cross")).status_code
results["inactive_create"] = create_as("inactive", role="ComplianceCreator").status_code

created = create_as("creator", role="ComplianceCreator", data=payload(idempotency_key="25ac-ok"))
results["creator_create"] = created.status_code
body = created.get_json(silent=True) or {}
rid = body.get("review", {}).get("compliance_review_id")
results["created_id_present"] = bool(rid)

auth("opener", role="ComplianceOpener")
open_response = client.post(f"/compliance/reviews/{rid}/open", data={"_csrf_token": "csrf-25ac", "expected_version": "1", "authority_basis": "25AC open"}, follow_redirects=False)
results["open_with_permission"] = open_response.status_code
repeat_open = client.post(f"/compliance/reviews/{rid}/open", data={"_csrf_token": "csrf-25ac", "expected_version": "2", "authority_basis": "25AC open again"}, follow_redirects=False)
results["invalid_lifecycle_open_again_form_redirect"] = repeat_open.status_code
repeat_open_json = client.post(f"/compliance/reviews/{rid}/open", json={"_csrf_token": "csrf-25ac", "expected_version": "2", "authority_basis": "25AC open again"}, follow_redirects=False)
results["invalid_lifecycle_open_again"] = repeat_open_json.status_code

auth("creator", role="ComplianceCreator")
approve_self = client.post(f"/compliance/reviews/{rid}/approve", data={"_csrf_token": "csrf-25ac", "expected_version": "2", "authority_basis": "25AC self approve", "confirm_action": "approve"}, follow_redirects=False)
results["creator_approve_without_permission"] = approve_self.status_code

auth("approver", role="ComplianceApprover")
approval = client.post(f"/compliance/reviews/{rid}/approve", data={"_csrf_token": "csrf-25ac", "expected_version": "2", "authority_basis": "25AC approve", "confirm_action": "approve"}, follow_redirects=False)
results["approve_with_permission"] = approval.status_code
missing_confirm = client.post(f"/compliance/reviews/{rid}/approve", data={"_csrf_token": "csrf-25ac", "expected_version": "3", "authority_basis": "25AC missing confirm"}, follow_redirects=False)
results["missing_confirmation"] = missing_confirm.status_code

auth("approver", role="ComplianceApprover")
certify_same = client.post(f"/compliance/reviews/{rid}/certify", data={"_csrf_token": "csrf-25ac", "expected_version": "3", "authority_basis": "25AC certify", "certification_statement": "certify", "confirm_action": "certify"}, follow_redirects=False)
results["approver_certify_denied"] = certify_same.status_code

auth("certifier", role="ComplianceCertifier")
certify = client.post(f"/compliance/reviews/{rid}/certify", data={"_csrf_token": "csrf-25ac", "expected_version": "3", "authority_basis": "25AC certify", "certification_statement": "certify", "confirm_action": "certify"}, follow_redirects=False)
results["certify_with_permission"] = certify.status_code

auth("closer", role="ComplianceCloser")
close = client.post(f"/compliance/reviews/{rid}/close", data={"_csrf_token": "csrf-25ac", "expected_version": "4", "authority_basis": "25AC close", "confirm_action": "close"}, follow_redirects=False)
results["close_with_permission"] = close.status_code

auth("creator", role="ComplianceCreator")
terminal_mutation = client.post(f"/compliance/reviews/{rid}/evidence", data={"_csrf_token": "csrf-25ac", "expected_version": "5", "authority_basis": "25AC late", "evidence_type": "document", "source_type": "document", "source_id": "DOC"}, follow_redirects=False)
results["terminal_mutation_blocked"] = terminal_mutation.status_code

auth("creator", role="ComplianceCreator", csrf=False)
csrf = client.post("/compliance/reviews", data=payload(idempotency_key="25ac-csrf"), follow_redirects=False)
results["csrf_required"] = csrf.status_code

auth("master-reader", role="Admin", master=True)
registry = client.get("/compliance/reviews")
results["global_read_registry"] = registry.status_code
print(json.dumps(results, sort_keys=True))
"""
    proc = run(
        [sys.executable, "-c", code, str(ROOT)],
        env={
            "DB_PATH": str(db),
            "UPLOAD_FOLDER": str(temp_root / "uploads"),
            "EXPORT_ROOT": str(temp_root / "exports"),
            "PYTHONPYCACHEPREFIX": str(temp_root / "pycache"),
        },
    )
    if proc.returncode != 0:
        check("live route subprocess exits", False, proc.stdout + proc.stderr)
        return {"error": proc.stdout + proc.stderr}
    data = json.loads(proc.stdout)
    expectations = {
        "viewer-none_create": 403,
        "trustee-none_create": 403,
        "admin-none_create": 403,
        "admin_create": 403,
        "master_reader_create": 403,
        "wrong_permission_create": 403,
        "authority_basis_only_denied": 403,
        "missing_basis": 400,
        "cross_firm_create": 400,
        "inactive_create": 403,
        "creator_create": 201,
        "created_id_present": True,
        "open_with_permission": 302,
        "invalid_lifecycle_open_again_form_redirect": 302,
        "invalid_lifecycle_open_again": 409,
        "creator_approve_without_permission": 403,
        "approve_with_permission": 302,
        "missing_confirmation": 400,
        "approver_certify_denied": 403,
        "certify_with_permission": 302,
        "close_with_permission": 302,
        "terminal_mutation_blocked": 403,
        "csrf_required": 400,
        "global_read_registry": 200,
    }
    for key, expected in expectations.items():
        check(f"live auth {key}", data.get(key) == expected, data)
    return data


def main() -> int:
    active_before = manifest(ACTIVE_DB)
    policy_before = manifest(EXPORT_POLICY)
    counts_before = active_counts()
    temp_root = Path(tempfile.mkdtemp(prefix="trustee_25ac_"))
    print(f"temporary_root={temp_root}")
    report: dict[str, object] = {
        "active_before": active_before,
        "policy_before": policy_before,
        "counts_before": counts_before,
        "temporary_root": str(temp_root),
    }
    try:
        report["migration_rehearsal"] = migration_rehearsal(temp_root)
        db = prepare_activated_db(temp_root)
        seed_live_authority_users(db)
        report["live_route_tests"] = route_and_service_tests(db, temp_root)
        report["temporary_db_sha"] = sha(db)
    finally:
        inventory = []
        if temp_root.exists():
            inventory = [
                {"name": p.name, "size": p.stat().st_size, "sha256": sha(p)}
                for p in sorted(temp_root.glob("*.db"))
            ]
        shutil.rmtree(temp_root, ignore_errors=True)

    active_after = manifest(ACTIVE_DB)
    policy_after = manifest(EXPORT_POLICY)
    counts_after = active_counts()
    check("active DB file unchanged", active_before == active_after, {"before": active_before, "after": active_after})
    check("active DB logical counts unchanged", counts_before == counts_after, {"before": counts_before, "after": counts_after})
    check("export policy unchanged", policy_before == policy_after, {"before": policy_before, "after": policy_after})
    check("temporary artifacts removed", not temp_root.exists(), inventory)

    report.update({
        "active_after": active_after,
        "policy_after": policy_after,
        "counts_after": counts_after,
        "temporary_database_inventory": inventory,
        "temporary_artifacts_removed": not temp_root.exists(),
        "tests_passed": sum(1 for item in results if item["pass"]),
        "tests_failed": sum(1 for item in results if not item["pass"]),
        "failures": failures,
    })
    report_path = write_report(report)
    print(f"STEP25AC_REPORT={report_path}")
    print(f"TESTS_PASSED={report['tests_passed']}")
    print(f"TESTS_FAILED={report['tests_failed']}")
    print("TRUSTEE APP STEP 25AC LIVE AUTHORITY INTEGRATION AUDIT")
    if failures:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
