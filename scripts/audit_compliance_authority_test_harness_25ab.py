"""STEP 25AB isolated Compliance authority test harness."""

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
ARTIFACT_DIR = ROOT / "test_artifacts" / "step25ab"
PERMISSION_MIGRATION = ROOT / "migrations" / "add_compliance_review_permissions.py"
PERMISSION_TOKEN = "H6E-TEMPORARY-PERMISSION-GOVERNANCE"
EXPECTED_BRANCH = "post-v2-planning"

sys.path.insert(0, str(ROOT))

from services.services_compliance_authorization import (  # noqa: E402
    PERMISSION_TO_AUTHORITIES,
    SENSITIVE_COMPLIANCE_PERMISSIONS,
    canonical_authority_for_action,
    evaluate_compliance_authority,
    evaluate_compliance_separation,
    map_compliance_permissions,
    source_permissions_for_authority,
    validate_mapping_completeness,
)
from scripts.support.compliance_authority_fixtures import (  # noqa: E402
    admin_create_only,
    admin_no_compliance,
    actor_with_permission,
    actor_with_unrelated_permission,
    authority_basis_only,
    explicit_global_reader,
    firm_one_actor,
    future_global_mutator,
    malformed_actor,
    master_admin_global_reader_no_mutation,
    trustee_no_compliance,
    unauthenticated_actor,
    username_admin_no_compliance,
    viewer_no_compliance,
)


failures: list[str] = []
results: list[dict[str, object]] = []


def write_report(report: dict[str, object]) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = ARTIFACT_DIR / "step25ab_report.json"
    try:
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
        return report_path
    except PermissionError:
        stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        fallback = ARTIFACT_DIR / f"step25ab_report_{stamp}.json"
        try:
            fallback.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
            return fallback
        except PermissionError:
            temp_fallback = Path(tempfile.gettempdir()) / f"step25ab_report_{stamp}.json"
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


def file_manifest(path: Path) -> dict[str, object]:
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


def run(cmd: list[str], *, env: dict[str, str] | None = None, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    merged = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        **(env or {}),
    }
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout, env=merged)


def check(name: str, condition: bool, detail: object = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"{status} - {name}" + (f" | {str(detail)[:500]}" if detail and not condition else ""))
    results.append({"name": name, "pass": bool(condition), "detail": detail})
    if not condition:
        failures.append(name)


def active_db_readonly_counts() -> dict[str, object]:
    con = sqlite3.connect(f"file:{ACTIVE_DB.as_posix()}?mode=ro", uri=True)
    try:
        cur = con.cursor()
        return {
            "audit_log": cur.execute("SELECT count(*), coalesce(max(id),0) FROM audit_log").fetchone(),
            "role_permissions": cur.execute("SELECT count(*) FROM role_permissions").fetchone()[0],
            "pairs": cur.execute("SELECT count(*) FROM (SELECT DISTINCT role_name, permission_name FROM role_permissions)").fetchone()[0],
            "compliance_objects": cur.execute("SELECT name FROM sqlite_master WHERE lower(name) LIKE '%compliance%' ORDER BY name").fetchall(),
            "integrity": cur.execute("PRAGMA integrity_check").fetchone()[0],
            "fk": cur.execute("PRAGMA foreign_key_check").fetchall(),
        }
    finally:
        con.close()


def git_output(args: list[str]) -> str:
    proc = run(["git", *args])
    return proc.stdout.strip()


def load_action_authorities() -> dict[str, str]:
    from services.services_compliance_reviews import H6C_ACTION_AUTHORITIES

    return dict(H6C_ACTION_AUTHORITIES)


def test_mapping(action_authorities: dict[str, str]) -> dict[str, object]:
    summary: dict[str, object] = {}
    check("empty permissions produce no authorities", map_compliance_permissions(()) == ())
    check("unknown permissions produce no authorities", map_compliance_permissions({"unknown"}) == ())
    check("Admin role alone maps no authorities", map_compliance_permissions(admin_no_compliance()["effective_permissions"]) == ())
    check("username admin alone maps no authorities", map_compliance_permissions(username_admin_no_compliance()["effective_permissions"]) == ())
    check("Master Admin alone maps no mutation authorities", map_compliance_permissions(master_admin_global_reader_no_mutation()["effective_permissions"]) == ())
    check("global read maps no mutation authorities", "create_review" not in map_compliance_permissions({"view_all_compliance_reviews"}))

    expected = {
        "create_compliance_review": ("create_review",),
        "edit_compliance_review": ("add_relationship", "add_subject", "edit_draft"),
        "assign_compliance_reviewer": ("assign_reviewer",),
        "add_compliance_evidence": ("add_evidence",),
        "verify_compliance_evidence": ("verify_evidence",),
        "issue_compliance_findings": ("issue_findings",),
        "acknowledge_compliance_findings": ("acknowledge_findings",),
        "manage_compliance_remediation": ("assign_remediation",),
        "submit_compliance_remediation": ("submit_remediation",),
        "verify_compliance_remediation": ("verify_remediation",),
        "request_compliance_exception": ("request_exception",),
        "approve_compliance_exception": ("approve_exception",),
        "approve_compliance_review": ("approve_review",),
        "certify_compliance_review": ("certify_review",),
        "close_compliance_review": ("close_review",),
        "reopen_compliance_review": ("reopen_review",),
        "supersede_compliance_review": ("supersede_review",),
        "archive_compliance_review": ("archive_review",),
        "open_compliance_review": ("open_review",),
    }
    for permission, authorities in expected.items():
        check(f"{permission} maps exactly", map_compliance_permissions({permission}) == tuple(sorted(authorities)))

    check("unrelated permission does not satisfy create", "create_review" not in map_compliance_permissions({"view_documents"}))
    check(
        "duplicate permissions deduplicate deterministically",
        map_compliance_permissions(["create_compliance_review", "create_compliance_review"]) == ("create_review",),
    )
    check("string input handled safely", map_compliance_permissions("create_compliance_review") == ("create_review",))

    alias_expectations = {
        "create": "create_review",
        "update": "edit_draft",
        "issue_finding": "issue_findings",
        "submit_for_approval": "approve_review",
        "approve": "approve_review",
        "certify": "certify_review",
        "archive": "archive_review",
    }
    for alias, canonical in alias_expectations.items():
        check(f"alias {alias} resolves", canonical_authority_for_action(alias, action_authorities) == canonical)

    completeness = validate_mapping_completeness(action_authorities)
    check("mapping completeness passes", completeness["ok"], completeness)
    synthetic_unmapped = dict(action_authorities)
    synthetic_unmapped["synthetic"] = "synthetic_unmapped_authority"
    check(
        "synthetic unmapped authority fails completeness",
        not validate_mapping_completeness(synthetic_unmapped)["ok"],
    )
    original = dict(PERMISSION_TO_AUTHORITIES)
    unknown_detected = "synthetic_unknown_authority" not in completeness["mapped_authorities"]
    check("synthetic unknown mapped authority can be detected", unknown_detected)
    summary["completeness"] = completeness
    summary["mapping_count"] = len(PERMISSION_TO_AUTHORITIES)
    summary["canonical_authority_count"] = len(completeness["canonical_service_authorities"])
    summary["sensitive_permissions"] = sorted(SENSITIVE_COMPLIANCE_PERMISSIONS)
    return summary


def test_authority_decisions(action_authorities: dict[str, str]) -> dict[str, object]:
    cases = {
        "missing identity denied": evaluate_compliance_authority(unauthenticated_actor(), "create", action_authorities=action_authorities),
        "missing firm denied": evaluate_compliance_authority(malformed_actor(), "create", action_authorities=action_authorities),
        "same firm exact authority allowed": evaluate_compliance_authority(actor_with_permission("create_compliance_review"), "create", target_firm_id="FIRM-001", action_authorities=action_authorities),
        "same firm Admin no permission denied": evaluate_compliance_authority(admin_no_compliance(), "create", target_firm_id="FIRM-001", action_authorities=action_authorities),
        "username admin no permission denied": evaluate_compliance_authority(username_admin_no_compliance(), "create", target_firm_id="FIRM-001", action_authorities=action_authorities),
        "master global reader no mutation denied": evaluate_compliance_authority(master_admin_global_reader_no_mutation(), "create", target_firm_id="FIRM-001", action_authorities=action_authorities),
        "unrelated authority denied": evaluate_compliance_authority(actor_with_unrelated_permission(), "create", target_firm_id="FIRM-001", action_authorities=action_authorities),
        "cross firm denied": evaluate_compliance_authority(firm_one_actor(), "create", target_firm_id="FIRM-002", action_authorities=action_authorities),
        "global reader cross firm mutation denied": evaluate_compliance_authority(explicit_global_reader(), "create", target_firm_id="FIRM-002", action_authorities=action_authorities),
        "future explicit global mutator allowed": evaluate_compliance_authority(future_global_mutator(), "create", target_firm_id="FIRM-002", action_authorities=action_authorities, require_global_mutation=True),
        "authority basis alone denied": evaluate_compliance_authority(authority_basis_only(), "create", target_firm_id="FIRM-001", action_authorities=action_authorities),
        "correct authority missing basis is documentation failure": evaluate_compliance_authority(
            actor_with_permission("create_compliance_review"),
            "create",
            target_firm_id="FIRM-001",
            action_authorities=action_authorities,
            require_authority_basis=True,
        ),
    }
    # Replace basis on this one after construction to prove documentation failure.
    missing_basis_actor = actor_with_permission("create_compliance_review")
    missing_basis_actor["authority_basis"] = ""
    cases["correct authority missing basis is documentation failure"] = evaluate_compliance_authority(
        missing_basis_actor,
        "create",
        target_firm_id="FIRM-001",
        action_authorities=action_authorities,
        require_authority_basis=True,
    )

    expected = {
        "missing identity denied": "authentication_required",
        "missing firm denied": "authentication_required",
        "same firm exact authority allowed": "allowed",
        "same firm Admin no permission denied": "permission_denied",
        "username admin no permission denied": "permission_denied",
        "master global reader no mutation denied": "permission_denied",
        "unrelated authority denied": "permission_denied",
        "cross firm denied": "firm_scope_denied",
        "global reader cross firm mutation denied": "firm_scope_denied",
        "future explicit global mutator allowed": "allowed",
        "authority basis alone denied": "permission_denied",
        "correct authority missing basis is documentation failure": "authority_basis_required",
    }
    for name, decision in cases.items():
        check(name, decision["category"] == expected[name], decision)
    return cases


def test_separation() -> dict[str, object]:
    record = {
        "created_by": "maker",
        "evidence_submitted_by": "maker",
        "finding_issued_by": "maker",
        "remediation_submitted_by": "maker",
        "exception_requested_by": "maker",
        "approval_submitted_by": "maker",
        "approved_by": "maker",
        "certified_by": "maker",
        "closed_by": "maker",
    }
    cases = {
        "creator approving own review": evaluate_compliance_separation("approve_review", "maker", record),
        "evidence submitter verifying own evidence": evaluate_compliance_separation("verify_evidence", "maker", record),
        "finding issuer acknowledging own finding": evaluate_compliance_separation("acknowledge_findings", "maker", record),
        "remediation submitter verifying own remediation": evaluate_compliance_separation("verify_remediation", "maker", record),
        "exception requester approving own exception": evaluate_compliance_separation("approve_exception", "maker", record),
        "approval submitter approving own review": evaluate_compliance_separation("approve_review", "maker", {"approval_submitted_by": "maker"}),
        "approver certifying same review": evaluate_compliance_separation("certify_review", "maker", record),
        "certifier archiving same review permissive with audit": evaluate_compliance_separation("archive_review", "maker", record),
        "certifier archiving same review strict policy": evaluate_compliance_separation("archive_review", "maker", record, allow_certifier_archive_with_audit=False),
        "closer reopening same review": evaluate_compliance_separation("reopen_review", "maker", record),
        "certifier reopening same review": evaluate_compliance_separation("reopen_review", "maker", {"certified_by": "maker"}),
    }
    expected_allowed = {
        "creator approving own review": False,
        "evidence submitter verifying own evidence": False,
        "finding issuer acknowledging own finding": False,
        "remediation submitter verifying own remediation": False,
        "exception requester approving own exception": False,
        "approval submitter approving own review": False,
        "approver certifying same review": False,
        "certifier archiving same review permissive with audit": True,
        "certifier archiving same review strict policy": False,
        "closer reopening same review": False,
        "certifier reopening same review": False,
    }
    for name, decision in cases.items():
        check(name, decision["allowed"] is expected_allowed[name], decision)
    return cases


def create_minimal_permission_db(path: Path) -> None:
    con = sqlite3.connect(path)
    try:
        con.executescript(
            """
            CREATE TABLE app_users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT,
                role_name TEXT,
                status TEXT,
                firm_id TEXT
            );
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
            CREATE TABLE user_permission_overrides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                permission_name TEXT,
                effect TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        con.executemany(
            "INSERT INTO app_users (user_id, username, role_name, status, firm_id) VALUES (?, ?, ?, 'active', ?)",
            [
                ("U1", "admin-no-compliance", "Admin", "FIRM-001"),
                ("U2", "admin-create", "Admin", "FIRM-001"),
                ("U3", "admin-unrelated", "Admin", "FIRM-001"),
                ("U4", "override-allow", "Viewer", "FIRM-001"),
                ("U5", "override-deny", "Admin", "FIRM-001"),
            ],
        )
        con.executemany(
            "INSERT INTO permissions (permission_id, permission_name, description) VALUES (?, ?, ?)",
            [
                ("P1", "create_compliance_review", "Create Compliance Review"),
                ("P2", "approve_compliance_review", "Approve Compliance Review"),
                ("P3", "view_documents", "Unrelated"),
            ],
        )
        con.executemany(
            "INSERT INTO role_permissions (role_name, permission_name) VALUES (?, ?)",
            [
                ("AdminCreate", "create_compliance_review"),
                ("AdminUnrelated", "view_documents"),
                ("Admin", "view_documents"),
            ],
        )
        con.execute("UPDATE app_users SET role_name='AdminCreate' WHERE username='admin-create'")
        con.execute("UPDATE app_users SET role_name='AdminUnrelated' WHERE username='admin-unrelated'")
        con.execute(
            "INSERT INTO user_permission_overrides (username, permission_name, effect) VALUES ('override-allow', 'create_compliance_review', 'allow')"
        )
        con.execute(
            "INSERT INTO user_permission_overrides (username, permission_name, effect) VALUES ('override-deny', 'view_documents', 'deny')"
        )
        con.commit()
    finally:
        con.close()


def test_effective_permission_helper(temp_root: Path) -> dict[str, object]:
    db = temp_root / "effective_permissions.db"
    create_minimal_permission_db(db)
    code = r"""
import json
import os
import sys
sys.path.insert(0, sys.argv[1])
from database.db import get_effective_permissions_for_user
from services.services_compliance_authorization import map_compliance_permissions
users = [
    "admin-no-compliance",
    "admin-create",
    "admin-unrelated",
    "override-allow",
    "override-deny",
]
result = {}
for username in users:
    permissions = sorted(get_effective_permissions_for_user(username))
    result[username] = {
        "permissions": permissions,
        "authorities": list(map_compliance_permissions(permissions)),
    }
print(json.dumps(result, sort_keys=True))
"""
    proc = run([sys.executable, "-c", code, str(ROOT)], env={"DB_PATH": str(db), "PYTHONPATH": str(ROOT)})
    check("effective permission helper subprocess exits", proc.returncode == 0, proc.stdout + proc.stderr)
    data = json.loads(proc.stdout) if proc.returncode == 0 else {}
    check("generic Admin with no Compliance maps none", data.get("admin-no-compliance", {}).get("authorities") == [])
    check("explicit create permission maps correctly", data.get("admin-create", {}).get("authorities") == ["create_review"])
    check("unrelated permission maps nothing relevant", data.get("admin-unrelated", {}).get("authorities") == [])
    check("user allow override maps correctly", data.get("override-allow", {}).get("authorities") == ["create_review"])
    check("user deny override preserves current semantics", data.get("override-deny", {}).get("permissions") == [])
    return {"path": str(db), "result": data}


def rehearse_permission_migration(temp_root: Path) -> dict[str, object]:
    db = temp_root / "permission_migration.db"
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
        permissions = [row[0] for row in con.execute("SELECT permission_name FROM permissions ORDER BY permission_name")]
        pairs = con.execute("SELECT COUNT(*) FROM role_permissions").fetchone()[0]
        duplicate_pairs = con.execute(
            "SELECT COUNT(*) FROM (SELECT role_name, permission_name, COUNT(*) c FROM role_permissions GROUP BY role_name, permission_name HAVING c > 1)"
        ).fetchone()[0]
    finally:
        con.close()
    registry_permissions = set(PERMISSION_TO_AUTHORITIES)
    migration_permissions = set(permissions)
    result = {
        "path": str(db),
        "dry_run_returncode": dry.returncode,
        "apply_returncode": apply.returncode,
        "repeat_returncode": repeat.returncode,
        "idempotent_repeat": after_apply == after_repeat,
        "permission_rows": len(permissions),
        "role_permission_rows": pairs,
        "duplicate_pairs": duplicate_pairs,
        "missing_from_migration": sorted(registry_permissions - migration_permissions),
        "extra_in_migration": sorted(migration_permissions - registry_permissions),
    }
    check("permission migration dry-run on temp DB succeeds", dry.returncode == 0, dry.stdout + dry.stderr)
    check("permission migration apply on temp DB succeeds", apply.returncode == 0, apply.stdout + apply.stderr)
    check("permission migration repeat idempotent", repeat.returncode == 0 and result["idempotent_repeat"], repeat.stdout + repeat.stderr)
    check("permission migration creates no duplicate pairs", duplicate_pairs == 0, duplicate_pairs)
    check("permission migration gap report generated", result["missing_from_migration"] == [], result)
    return result


def main() -> int:
    branch = git_output(["branch", "--show-current"])
    status_before = git_output(["status", "--short"])
    head = git_output(["rev-parse", "HEAD"])
    log = git_output(["log", "--oneline", "-5"])
    diff_check = run(["git", "diff", "--check"])
    check("branch is post-v2-planning", branch == EXPECTED_BRANCH, branch)
    check("diff check passes at baseline", diff_check.returncode == 0, diff_check.stdout + diff_check.stderr)
    check("active DB exists", ACTIVE_DB.exists(), ACTIVE_DB)

    active_before = file_manifest(ACTIVE_DB)
    policy_before = file_manifest(EXPORT_POLICY)
    active_counts_before = active_db_readonly_counts()
    action_authorities = load_action_authorities()

    temp_root = Path(tempfile.mkdtemp(prefix="trustee_25ab_"))
    print(f"temporary_root={temp_root}")
    os.environ["UPLOAD_FOLDER"] = str(temp_root / "uploads")
    os.environ["EXPORT_ROOT"] = str(temp_root / "exports")
    os.environ["PYTHONPYCACHEPREFIX"] = str(temp_root / "pycache")
    (temp_root / "uploads").mkdir(exist_ok=True)
    (temp_root / "exports").mkdir(exist_ok=True)

    report: dict[str, object] = {
        "baseline": {
            "branch": branch,
            "head": head,
            "log": log,
            "status_before": status_before,
        },
        "active_db_before": active_before,
        "policy_before": policy_before,
        "temporary_root": str(temp_root),
    }
    try:
        report["mapping"] = test_mapping(action_authorities)
        report["authority_decisions"] = test_authority_decisions(action_authorities)
        report["separation"] = test_separation()
        report["effective_permission_integration"] = test_effective_permission_helper(temp_root)
        report["migration_rehearsal"] = rehearse_permission_migration(temp_root)
    finally:
        temp_inventory = []
        if temp_root.exists():
            temp_inventory = [
                {"name": p.name, "size": p.stat().st_size, "sha256": sha(p)}
                for p in sorted(temp_root.glob("*.db"))
            ]
        shutil.rmtree(temp_root, ignore_errors=True)

    active_after = file_manifest(ACTIVE_DB)
    policy_after = file_manifest(EXPORT_POLICY)
    active_counts_after = active_db_readonly_counts()
    check("active DB hash unchanged", active_before == active_after, {"before": active_before, "after": active_after})
    check("active DB logical counts unchanged", active_counts_before == active_counts_after, {"before": active_counts_before, "after": active_counts_after})
    check("export policy unchanged", policy_before == policy_after, {"before": policy_before, "after": policy_after})
    check("temporary artifacts removed", not temp_root.exists(), temp_inventory)

    report.update({
        "active_db_after": active_after,
        "policy_after": policy_after,
        "active_counts_before": active_counts_before,
        "active_counts_after": active_counts_after,
        "temporary_database_inventory": temp_inventory,
        "temporary_artifacts_removed": not temp_root.exists(),
        "tests_passed": sum(1 for item in results if item["pass"]),
        "tests_failed": sum(1 for item in results if not item["pass"]),
        "failures": failures,
        "status_after": git_output(["status", "--short"]),
    })
    report_path = write_report(report)
    print(f"STEP25AB_REPORT={report_path}")
    print(f"TESTS_PASSED={report['tests_passed']}")
    print(f"TESTS_FAILED={report['tests_failed']}")
    print("POST-V2 STEP 25AB COMPLIANCE AUTHORITY TEST HARNESS")
    if failures:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
