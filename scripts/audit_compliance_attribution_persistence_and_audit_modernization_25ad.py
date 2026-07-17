"""STEP 25AD Compliance attribution persistence and audit modernization audit."""

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
ACTIVATION_MIGRATION = ROOT / "migrations" / "activate_compliance_review_foundation.py"
ATTRIBUTION_MIGRATION = ROOT / "migrations" / "add_compliance_exception_attribution_25ad.py"
ACTIVATION_TOKEN = "H6B-TEMPORARY-ACTIVATION"
ATTRIBUTION_TOKEN = "25AD-TEMPORARY-ATTRIBUTION"
ARTIFACT_DIR = ROOT / "test_artifacts" / "step25ad"

failures: list[str] = []
results: list[dict[str, object]] = []


def sha(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def manifest(path: Path) -> dict[str, object]:
    stat = path.stat()
    return {
        "path": str(path),
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
            "tables": cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall(),
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


def write_report(report: dict[str, object]) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    paths = [Path(tempfile.gettempdir()) / f"step25ad_report_{stamp}.json"]
    try:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        paths.insert(0, ARTIFACT_DIR / f"step25ad_report_{stamp}.json")
        paths.insert(0, ARTIFACT_DIR / "step25ad_report.json")
    except PermissionError:
        pass
    data = json.dumps(report, indent=2, sort_keys=True, default=str)
    for path in paths:
        try:
            path.write_text(data, encoding="utf-8")
            return path
        except PermissionError:
            continue
    raise PermissionError("step25ad_report_write_failed")


def prepare_db(temp_root: Path) -> Path:
    db = temp_root / "step25ad.db"
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
    check("temporary activation succeeds", activation.returncode == 0, activation.stdout + activation.stderr)
    dry = run([
        sys.executable,
        str(ATTRIBUTION_MIGRATION),
        "--database",
        str(db),
        "--dry-run",
        "--authorization-token",
        ATTRIBUTION_TOKEN,
    ])
    first = run([
        sys.executable,
        str(ATTRIBUTION_MIGRATION),
        "--database",
        str(db),
        "--apply",
        "--authorization-token",
        ATTRIBUTION_TOKEN,
    ])
    after_first = sha(db)
    repeat = run([
        sys.executable,
        str(ATTRIBUTION_MIGRATION),
        "--database",
        str(db),
        "--apply",
        "--authorization-token",
        ATTRIBUTION_TOKEN,
    ])
    after_repeat = sha(db)
    check("attribution migration dry-run succeeds", dry.returncode == 0, dry.stdout + dry.stderr)
    check("attribution migration apply succeeds", first.returncode == 0, first.stdout + first.stderr)
    check("attribution migration repeat idempotent", repeat.returncode == 0 and after_first == after_repeat, repeat.stdout + repeat.stderr)
    return db


def migration_old_schema_rehearsal(temp_root: Path) -> dict[str, object]:
    db = temp_root / "old_schema_rehearsal.db"
    con = sqlite3.connect(db)
    try:
        con.executescript(
            """
            CREATE TABLE compliance_review_remediations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compliance_remediation_id TEXT NOT NULL UNIQUE,
                compliance_review_id TEXT NOT NULL,
                exception_requested INTEGER NOT NULL DEFAULT 0,
                exception_basis TEXT,
                exception_approved_by TEXT,
                exception_approved_at TEXT
            );
            CREATE TABLE compliance_review_audit_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compliance_audit_id TEXT NOT NULL UNIQUE,
                compliance_review_id TEXT,
                entity_type TEXT NOT NULL,
                entity_id TEXT,
                action TEXT NOT NULL,
                previous_state TEXT,
                new_state TEXT,
                note TEXT,
                actor_id TEXT NOT NULL,
                actor_role TEXT,
                authority_basis TEXT,
                created_at TEXT NOT NULL,
                previous_hash TEXT,
                entry_hash TEXT NOT NULL,
                hash_algorithm TEXT NOT NULL DEFAULT 'SHA-256',
                firm_id TEXT NOT NULL
            );
            """
        )
        con.commit()
    finally:
        con.close()
    first = run([sys.executable, str(ATTRIBUTION_MIGRATION), "--database", str(db), "--apply", "--authorization-token", ATTRIBUTION_TOKEN])
    after_first = sha(db)
    repeat = run([sys.executable, str(ATTRIBUTION_MIGRATION), "--database", str(db), "--apply", "--authorization-token", ATTRIBUTION_TOKEN])
    after_repeat = sha(db)
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        remediation_columns = [row[1] for row in con.execute("PRAGMA table_info(compliance_review_remediations)")]
        audit_columns = [row[1] for row in con.execute("PRAGMA table_info(compliance_review_audit_ledger)")]
    finally:
        con.close()
    required_remediation = {"exception_requested_by", "exception_requested_by_label", "exception_requested_at", "exception_request_basis", "exception_request_status"}
    required_audit = {"actor_label", "target_firm_id", "canonical_authority", "source_permission", "exception_requested_by", "exception_approved_by", "sod_result", "override_used"}
    result = {
        "apply": first.returncode,
        "repeat": repeat.returncode,
        "idempotent": after_first == after_repeat,
        "remediation_columns_present": sorted(required_remediation.intersection(remediation_columns)),
        "audit_columns_present": sorted(required_audit.intersection(audit_columns)),
    }
    check("old schema attribution migration succeeds", first.returncode == 0, first.stdout + first.stderr)
    check("old schema attribution migration idempotent", repeat.returncode == 0 and result["idempotent"], result)
    check("old schema remediation columns added", required_remediation.issubset(set(remediation_columns)), result)
    check("old schema audit columns added", required_audit.issubset(set(audit_columns)), result)
    return result


def service_rehearsal(db: Path, temp_root: Path) -> dict[str, object]:
    code = r'''
import json
import os
import sqlite3
import sys

sys.path.insert(0, sys.argv[1])

from services.services_compliance_authorization import build_test_actor_context
from services.services_compliance_reviews import (
    approve_exception,
    assign_remediation,
    create_compliance_review,
    issue_review_finding,
    request_exception,
)

DB = os.environ["DB_PATH"]

def actor(actor_id, permissions, *, role="Trustee", firm="FIRM-001", basis="25AD authority"):
    return build_test_actor_context(
        actor_id=actor_id,
        username=actor_id,
        actor_label=actor_id + " label",
        role=role,
        firm_id=firm,
        effective_permissions=permissions,
        authority_basis=basis,
        global_read=("view_all_compliance_reviews" in permissions),
    )

creator = actor("creator", ["create_compliance_review"], role="ComplianceCreator")
finder = actor("finder", ["issue_compliance_findings"], role="ComplianceFinder")
manager = actor("manager", ["manage_compliance_remediation"], role="ComplianceManager")
requester = actor("requester", ["request_compliance_exception", "approve_compliance_exception"], role="ComplianceRequester")
approver = actor("approver", ["approve_compliance_exception"], role="ComplianceApprover")
admin_none = actor("admin-none", [], role="Admin")
username_admin = actor("admin", [], role="Admin")
master_reader = actor("master-reader", ["view_all_compliance_reviews"], role="Admin")
wrong_firm_requester = actor("wrong-requester", ["request_compliance_exception"], role="ComplianceRequester", firm="FIRM-002")
wrong_firm_approver = actor("wrong-approver", ["approve_compliance_exception"], role="ComplianceApprover", firm="FIRM-002")
basis_only = actor("basis-only", [], role="ComplianceRequester")

payload = {
    "firm_id": "FIRM-001",
    "title": "25AD Attribution Review",
    "review_type": "governance_compliance",
    "question_presented": "Does exception attribution persist?",
    "governing_requirement_type": "institutional_policy",
    "governing_requirement_id": "GOV-25AD",
    "source_type": "governance_record",
    "source_id": "GOV-25AD",
    "authority_basis": "25AD create basis",
    "idempotency_key": "25ad-review",
}

results = {}
created = create_compliance_review(payload=payload, actor_context=creator)
results["create"] = created["status"]
rid = created["review"]["compliance_review_id"]

finding = issue_review_finding(
    compliance_review_id=rid,
    finding_type="control_gap",
    title="Exception control",
    description="Requires controlled exception path.",
    evidence_basis="temporary-db rehearsal",
    severity="medium",
    actor_context=finder,
    authority_basis="25AD finding basis",
)
results["finding"] = finding["status"]
fid = finding["event"]["compliance_finding_id"]

remediation = assign_remediation(
    compliance_review_id=rid,
    compliance_finding_id=fid,
    required_action="Resolve exception attribution",
    responsible_party_type="operator",
    responsible_party_id="operator-1",
    responsible_party_label="Operator",
    actor_context=manager,
    authority_basis="25AD remediation basis",
)
results["remediation"] = remediation["status"]
remid = remediation["event"]["compliance_remediation_id"]

for name, context in [
    ("admin_request", admin_none),
    ("username_admin_request", username_admin),
    ("master_reader_request", master_reader),
    ("basis_only_request", basis_only),
    ("cross_firm_request", wrong_firm_requester),
]:
    result = request_exception(
        compliance_review_id=rid,
        compliance_remediation_id=remid,
        exception_basis="25AD denied request",
        actor_context=context,
        authority_basis="25AD denied basis",
    )
    results[name] = result["status"]

requested = request_exception(
    compliance_review_id=rid,
    compliance_remediation_id=remid,
    exception_basis="25AD exception requested",
    actor_context=requester,
    authority_basis="25AD requester authority",
)
results["request"] = requested["status"]
repeat_request = request_exception(
    compliance_review_id=rid,
    compliance_remediation_id=remid,
    exception_basis="25AD repeat",
    actor_context=requester,
    authority_basis="25AD repeat basis",
)
results["repeat_request"] = repeat_request["status"]

self_approval = approve_exception(
    compliance_review_id=rid,
    compliance_remediation_id=remid,
    actor_context=requester,
    authority_basis="25AD self approval",
)
results["self_approval_status"] = self_approval["status"]
results["self_approval_message"] = self_approval.get("message")
wrong_approval = approve_exception(
    compliance_review_id=rid,
    compliance_remediation_id=remid,
    actor_context=wrong_firm_approver,
    authority_basis="25AD wrong firm approval",
)
results["cross_firm_approval"] = wrong_approval["status"]
approved = approve_exception(
    compliance_review_id=rid,
    compliance_remediation_id=remid,
    actor_context=approver,
    authority_basis="25AD approval basis",
)
results["approval"] = approved["status"]

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
row = con.execute(
    "SELECT * FROM compliance_review_remediations WHERE compliance_remediation_id = ?",
    (remid,),
).fetchone()
audit = [
    dict(item)
    for item in con.execute(
        """
        SELECT action, actor_id, actor_label, actor_role, firm_id, target_firm_id,
               canonical_authority, source_permission, authority_basis,
               exception_requested_by, exception_approved_by, sod_result,
               override_used, created_at
        FROM compliance_review_audit_ledger
        WHERE compliance_review_id = ?
          AND action IN ('exception_requested','exception_approved')
        ORDER BY id
        """,
        (rid,),
    ).fetchall()
]
legacy_id = "CRM-LEGACY-25AD"
con.execute(
    """
    INSERT INTO compliance_review_remediations (
        compliance_remediation_id, compliance_review_id, action_number,
        required_action, status, exception_requested, created_at, updated_at
    ) VALUES (?, ?, 99, 'legacy exception', 'waived', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """,
    (legacy_id, rid),
)
con.commit()
con.close()

legacy = approve_exception(
    compliance_review_id=rid,
    compliance_remediation_id=legacy_id,
    actor_context=approver,
    authority_basis="25AD legacy approval",
)
results["legacy_missing_requester"] = legacy["status"]
results["legacy_missing_requester_message"] = legacy.get("message")

results["row"] = dict(row)
results["audit"] = audit
print(json.dumps(results, sort_keys=True))
'''
    proc = run(
        [sys.executable, "-c", code, str(ROOT)],
        env={
            "DB_PATH": str(db),
            "UPLOAD_FOLDER": str(temp_root / "uploads"),
            "EXPORT_ROOT": str(temp_root / "exports"),
            "PYTHONPYCACHEPREFIX": str(temp_root / "pycache"),
        },
    )
    check("service rehearsal exits", proc.returncode == 0, proc.stdout + proc.stderr)
    if proc.returncode != 0:
        return {"error": proc.stdout + proc.stderr}
    data = json.loads(proc.stdout)
    expectations = {
        "create": "created",
        "finding": "finding_issued",
        "remediation": "remediation_assigned",
        "admin_request": "authorization_denied",
        "username_admin_request": "authorization_denied",
        "master_reader_request": "authorization_denied",
        "basis_only_request": "authorization_denied",
        "cross_firm_request": "authorization_denied",
        "request": "exception_requested",
        "repeat_request": "invalid_input",
        "self_approval_status": "separation_of_duties_denied",
        "cross_firm_approval": "authorization_denied",
        "approval": "exception_approved",
        "legacy_missing_requester": "separation_of_duties_denied",
    }
    for key, expected in expectations.items():
        check(f"25AD service {key}", data.get(key) == expected, data)
    row = data.get("row", {})
    check("requester id persisted", row.get("exception_requested_by") == "requester", row)
    check("requester label persisted", row.get("exception_requested_by_label") == "requester label", row)
    check("request timestamp persisted", bool(row.get("exception_requested_at")), row)
    check("request basis persisted", row.get("exception_request_basis") == "25AD requester authority", row)
    check("approval actor persisted", row.get("exception_approved_by") == "approver", row)
    check("approval timestamp persisted", bool(row.get("exception_approved_at")), row)
    check("exception status approved", row.get("exception_request_status") == "approved", row)
    check("requester cannot approve message precise", data.get("self_approval_message") == "exception_requester_cannot_approve", data)
    check("legacy missing requester fails closed", data.get("legacy_missing_requester_message") == "exception_requester_attribution_required", data)
    audit = data.get("audit", [])
    check("exception audit entries exist", len(audit) == 2, audit)
    if len(audit) == 2:
        request_audit, approval_audit = audit
        check("request audit metadata", request_audit.get("canonical_authority") == "request_exception" and request_audit.get("source_permission") == "request_compliance_exception" and request_audit.get("exception_requested_by") == "requester" and request_audit.get("override_used") == 0, request_audit)
        check("approval audit metadata", approval_audit.get("canonical_authority") == "approve_exception" and approval_audit.get("source_permission") == "approve_compliance_exception" and approval_audit.get("exception_requested_by") == "requester" and approval_audit.get("exception_approved_by") == "approver" and approval_audit.get("sod_result") == "requester_approver_separated", approval_audit)
    return data


def main() -> int:
    active_before = manifest(ACTIVE_DB)
    policy_before = manifest(EXPORT_POLICY)
    counts_before = active_counts()
    temp_root = Path(tempfile.mkdtemp(prefix="trustee_25ad_"))
    report: dict[str, object] = {
        "active_before": active_before,
        "policy_before": policy_before,
        "counts_before": counts_before,
        "temporary_root": str(temp_root),
    }
    try:
        report["old_schema_rehearsal"] = migration_old_schema_rehearsal(temp_root)
        db = prepare_db(temp_root)
        report["service_rehearsal"] = service_rehearsal(db, temp_root)
        report["temporary_db_sha"] = sha(db)
    finally:
        inventory = []
        if temp_root.exists():
            inventory = [{"name": p.name, "size": p.stat().st_size, "sha256": sha(p)} for p in sorted(temp_root.glob("*.db"))]
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
    print(f"STEP25AD_REPORT={report_path}")
    print(f"TESTS_PASSED={report['tests_passed']}")
    print(f"TESTS_FAILED={report['tests_failed']}")
    print("TRUSTEE APP STEP 25AD ATTRIBUTION PERSISTENCE AUDIT")
    if failures:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
