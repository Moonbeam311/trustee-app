"""POST-V2-19 core product operator acceptance audit.

Prepared mode verifies the acceptance package and protected baseline before
manual browser testing. Confirmed mode is intentionally strict and requires
operator-supplied results that are not present in the prepared package.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BRANCH = "post-v2-planning"
BASELINE_HEAD = "0d43de6d9e1b6f3c2a4493e4d4001650e0b92597"
REMOTE_REF = "origin/post-v2-planning"
DB = REPO / "trustee_app.db"
DB_SIZE = 3_096_576
DB_MTIME_NS = 1_784_378_870_854_649_900
DB_SHA = "7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525"
H6A_BACKUP = REPO / "data" / "backups" / "trustee_app_pre_role_permission_reconcile_2026-07-15.db"
H6A_BACKUP_SHA = "CEEDF08EAA93F1311D0E3057CD1BF84E35EADF26D40872CF7A05F5D2D560F7BA"
POST_V18_DOC = REPO / "docs" / "product_completion_gap_audit_post_v2_18.md"
POST_V18_SCRIPT = REPO / "scripts" / "audit_product_completion_gap_post_v2_18.py"
ACCEPTANCE_DOC = REPO / "docs" / "core_product_operator_acceptance_post_v2_19.md"
ACCEPTANCE_SCRIPT = REPO / "scripts" / "audit_core_product_operator_acceptance_post_v2_19.py"

EXPECTED_UNTRACKED = {
    "docs/product_completion_gap_audit_post_v2_18.md",
    "scripts/audit_product_completion_gap_post_v2_18.py",
    "docs/core_product_operator_acceptance_post_v2_19.md",
    "scripts/audit_core_product_operator_acceptance_post_v2_19.py",
}

EXPECTED_EVIDENCE_FILES = EXPECTED_UNTRACKED
APPROVED_LATER_REPOSITORY_PATHS = {
    ".gitignore",
    "app.py",
    "docs/audit_expected_active_state_reconciliation_25al_r1.md",
    "docs/core_product_manual_operator_acceptance_25al.md",
    "docs/reports_pdf_runtime_repair_25am.md",
    "docs/operator_friction_acceptance_closure_25an.md",
    "pdf_utils.py",
    "scripts/audit_core_product_manual_operator_acceptance_25al.py",
    "scripts/audit_expected_active_state_reconciliation_25al_r1.py",
    "scripts/audit_reports_pdf_runtime_repair_25am.py",
    "scripts/audit_reports_pdf_runtime_repair_evidence_25am.py",
    "scripts/audit_operator_friction_acceptance_closure_25an.py",
    "docs/post_v2_gap_closure_prioritization_25ak.md",
    "scripts/audit_post_v2_gap_closure_prioritization_25ak.py",
    "scripts/audit_product_completion_gap_post_v2_18.py",
    "scripts/audit_transfer_helper_contract_post_v2_19_r1.py",
    "scripts/audit_core_product_operator_acceptance_post_v2_19.py",
    "test_artifacts/README.md",
}
GENERATED_LOCAL_ARTIFACT_FILES = {
    "test_artifacts/step25ab/step25ab_report.json",
    "test_artifacts/step25ac/step25ac_report.json",
    "test_artifacts/step25ad/step25ad_report.json",
    "test_artifacts/step25ae/step25ae_master_report.json",
}
ACTIVE_STATE_FILES = {
    "trustee_app.db",
    "database.db",
    "data/database.db",
    "data/export_policy.json",
}

H6G_LOCAL_FILES = [
    REPO / "config" / "local" / "compliance_review_activation_manifest.local.json",
    REPO / "config" / "local" / "compliance_review_activation_authorization_worksheet.local.md",
    REPO / "config" / "local" / "compliance_review_h6g_resume.local.json",
]

REQUIRED_WORKFLOWS = [
    "Login",
    "Institutional shell",
    "Intake",
    "Matter",
    "Trust",
    "Fiduciaries or people",
    "Property or assets",
    "Documents or instruments",
    "Execution",
    "Funding or transfer",
    "Certificates",
    "Governance",
    "Reports",
    "Archive",
    "Continuity",
    "Recovery",
    "Admin",
    "Audit",
    "Roles and Permissions",
    "Reverse-navigation continuity",
    "Logout",
]

REQUIRED_URLS = [
    "http://127.0.0.1:5000/login",
    "http://127.0.0.1:5000/admin",
    "http://127.0.0.1:5000/intake/dashboard",
    "http://127.0.0.1:5000/matters/MAT-000001",
    "http://127.0.0.1:5000/trust/TR-001",
    "http://127.0.0.1:5000/fiduciaries",
    "http://127.0.0.1:5000/assets",
    "http://127.0.0.1:5000/documents",
    "http://127.0.0.1:5000/execution",
    "http://127.0.0.1:5000/execution/transfers/T-0001",
    "http://127.0.0.1:5000/certificates",
    "http://127.0.0.1:5000/governance",
    "http://127.0.0.1:5000/reports",
    "http://127.0.0.1:5000/archive",
    "http://127.0.0.1:5000/continuity",
    "http://127.0.0.1:5000/recovery",
    "http://127.0.0.1:5000/audit",
    "http://127.0.0.1:5000/admin/roles",
    "http://127.0.0.1:5000/logout",
]

COMPLIANCE_BOOKMARK_TERMS = [
    "POST-V2-17Q-H.6G - Compliance Review Controlled Local Activation Execution and Post-Activation Certification",
    "POST-V2-17Q-H.6G-R2 - Authorization Field and Sign-Off Completion",
    "DEFERRED_INSTITUTIONAL_AUTHORIZATION",
]


class AuditFailure(RuntimeError):
    pass


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        cmd,
        cwd=REPO,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AuditFailure(f"{' '.join(cmd)} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.rstrip("\n")


def git_ok(*args: str) -> bool:
    return subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True).returncode == 0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def pass_line(label: str, detail: object = "") -> None:
    print(f"PASS - {label}" + (f" | {detail}" if detail != "" else ""))


def fail_if(condition: bool, message: str) -> None:
    if condition:
        raise AuditFailure(message)


def git_status() -> tuple[list[str], list[str], list[str]]:
    porcelain = run(["git", "status", "--porcelain=v1"]).splitlines()
    staged: list[str] = []
    unstaged: list[str] = []
    untracked: list[str] = []
    for line in porcelain:
        if not line:
            continue
        status = line[:2]
        path = line[3:].replace("\\", "/")
        if status == "??":
            untracked.append(path)
        else:
            if status[0] != " ":
                staged.append(line)
            if status[1] != " ":
                unstaged.append(line)
    return staged, unstaged, untracked


def normalize_repo_path(path: str) -> str:
    return path.strip().strip('"').replace("\\", "/")


def parse_status_line(line: str) -> tuple[str, str]:
    status_code = line[:2]
    path = normalize_repo_path(line[2:].strip())
    if " -> " in path:
        path = normalize_repo_path(path.split(" -> ", 1)[1])
    return status_code, path


def classify_repository_shape(
    staged: list[str],
    unstaged: list[str],
    untracked: list[str],
    tracked_generated_artifacts: set[str],
) -> dict[str, object]:
    original_expected: list[str] = []
    approved_later: list[str] = []
    generated_local_output: list[str] = []
    unauthorized: list[str] = []

    for line in staged + unstaged:
        status_code, path = parse_status_line(line)
        compact_status = status_code.strip()
        if path in GENERATED_LOCAL_ARTIFACT_FILES:
            unauthorized.append(f"{status_code} {path}")
        elif path in EXPECTED_EVIDENCE_FILES and compact_status in {"A", "M"}:
            original_expected.append(path)
        elif path in APPROVED_LATER_REPOSITORY_PATHS and compact_status in {"A", "M"}:
            approved_later.append(path)
        else:
            unauthorized.append(f"{status_code} {path}")

    for path in untracked:
        normalized = normalize_repo_path(path)
        if normalized in GENERATED_LOCAL_ARTIFACT_FILES:
            generated_local_output.append(normalized)
        elif normalized in EXPECTED_EVIDENCE_FILES:
            original_expected.append(normalized)
        elif normalized in APPROVED_LATER_REPOSITORY_PATHS:
            approved_later.append(normalized)
        else:
            unauthorized.append(f"?? {normalized}")

    staged_paths = {parse_status_line(line)[1] for line in staged}
    unauthorized_staged = sorted(
        path
        for path in staged_paths
        if path not in EXPECTED_EVIDENCE_FILES and path not in APPROVED_LATER_REPOSITORY_PATHS
    )
    generated_staged = sorted(path for path in staged_paths if path in GENERATED_LOCAL_ARTIFACT_FILES)
    unauthorized_tracked_artifacts = sorted(
        path for path in tracked_generated_artifacts if path in GENERATED_LOCAL_ARTIFACT_FILES
    )
    active_state_changes = sorted(
        path
        for path in staged_paths
        | {parse_status_line(line)[1] for line in unstaged}
        | {normalize_repo_path(path) for path in untracked}
        if path in ACTIVE_STATE_FILES
    )

    unauthorized.extend(f"staged:{path}" for path in unauthorized_staged)
    unauthorized.extend(f"staged-generated:{path}" for path in generated_staged)
    unauthorized.extend(f"tracked-generated:{path}" for path in unauthorized_tracked_artifacts)
    unauthorized.extend(f"active-state:{path}" for path in active_state_changes)

    return {
        "allowed": not unauthorized,
        "original_expected": sorted(set(original_expected)),
        "approved_later": sorted(set(approved_later)),
        "generated_local_output": sorted(set(generated_local_output)),
        "unauthorized": sorted(set(unauthorized)),
    }


def repository_shape_self_tests() -> dict[str, bool]:
    cases = [
        ("pass_no_later_additions", [], [], [], set(), True),
        ("pass_gitignore_only", ["M  .gitignore"], [], [], set(), True),
        (
            "pass_post_v2_18_reconciliation_only",
            ["M  scripts/audit_product_completion_gap_post_v2_18.py"],
            [],
            [],
            set(),
            True,
        ),
        (
            "pass_post_v2_19_reconciliation_only",
            ["M  scripts/audit_core_product_operator_acceptance_post_v2_19.py"],
            [],
            [],
            set(),
            True,
        ),
        ("pass_readme_only", ["A  test_artifacts/README.md"], [], [], set(), True),
        (
            "pass_step_25ak_plan_only",
            [],
            [],
            ["docs/post_v2_gap_closure_prioritization_25ak.md"],
            set(),
            True,
        ),
        (
            "pass_step_25ak_audit_only",
            [],
            [],
            ["scripts/audit_post_v2_gap_closure_prioritization_25ak.py"],
            set(),
            True,
        ),
        (
            "pass_step_25ak_package",
            [],
            [],
            [
                "docs/post_v2_gap_closure_prioritization_25ak.md",
                "scripts/audit_post_v2_gap_closure_prioritization_25ak.py",
            ],
            set(),
            True,
        ),
        (
            "pass_all_four_approved_paths",
            [
                "M  .gitignore",
                "M  scripts/audit_product_completion_gap_post_v2_18.py",
                "M  scripts/audit_core_product_operator_acceptance_post_v2_19.py",
                "A  test_artifacts/README.md",
            ],
            [],
            [],
            set(),
            True,
        ),
        (
            "pass_prior_approved_plus_step_25ak",
            [
                "M  .gitignore",
                "M  scripts/audit_product_completion_gap_post_v2_18.py",
                "M  scripts/audit_core_product_operator_acceptance_post_v2_19.py",
                "A  test_artifacts/README.md",
                "A  docs/post_v2_gap_closure_prioritization_25ak.md",
                "A  scripts/audit_post_v2_gap_closure_prioritization_25ak.py",
            ],
            [],
            [],
            set(),
            True,
        ),
        (
            "pass_step_25al_r1_package",
            [],
            [],
            [
                "docs/audit_expected_active_state_reconciliation_25al_r1.md",
                "docs/core_product_manual_operator_acceptance_25al.md",
                "scripts/audit_expected_active_state_reconciliation_25al_r1.py",
                "scripts/audit_core_product_manual_operator_acceptance_25al.py",
            ],
            set(),
            True,
        ),
        (
            "pass_step_25am_repair_package",
            ["M  app.py"],
            [" M pdf_utils.py"],
            [
                "docs/reports_pdf_runtime_repair_25am.md",
                "scripts/audit_reports_pdf_runtime_repair_25am.py",
                "scripts/audit_reports_pdf_runtime_repair_evidence_25am.py",
            ],
            set(),
            True,
        ),
        (
            "pass_step_25an_acceptance_closure_package",
            [],
            [],
            [
                "docs/operator_friction_acceptance_closure_25an.md",
                "scripts/audit_operator_friction_acceptance_closure_25an.py",
            ],
            set(),
            True,
        ),
        (
            "pass_step_25al_r1_current_reference_update",
            [" M scripts/audit_transfer_helper_contract_post_v2_19_r1.py"],
            [],
            [],
            set(),
            True,
        ),
        (
            "pass_ignored_known_reports_untracked",
            [],
            [],
            ["test_artifacts/step25ab/step25ab_report.json"],
            set(),
            True,
        ),
        ("fail_modified_template", [], [" M templates/report_center.html"], [], set(), False),
        ("fail_arbitrary_service", ["A  services/new_service.py"], [], [], set(), False),
        ("fail_unknown_doc", [], [], ["docs/new_report.md"], set(), False),
        ("fail_unknown_script", ["A  scripts/new_audit.py"], [], [], set(), False),
        (
            "fail_tracked_raw_json",
            [],
            [],
            [],
            {"test_artifacts/step25ab/step25ab_report.json"},
            False,
        ),
        (
            "fail_staged_raw_json",
            ["A  test_artifacts/step25ab/step25ab_report.json"],
            [],
            [],
            set(),
            False,
        ),
        ("fail_database_added", ["A  trustee_app.db"], [], [], set(), False),
        ("fail_policy_modified", [], [" M data/export_policy.json"], [], set(), False),
        ("fail_unknown_untracked", [], [], ["scratch.tmp"], set(), False),
        ("fail_broad_new_directory", [], [], ["new_area/readme.md"], set(), False),
        (
            "fail_step_25ak_plan_copy",
            [],
            [],
            ["docs/post_v2_gap_closure_prioritization_25ak_copy.md"],
            set(),
            False,
        ),
        (
            "fail_step_25ak_audit_copy",
            [],
            [],
            ["scripts/audit_post_v2_gap_closure_prioritization_25ak_copy.py"],
            set(),
            False,
        ),
        (
            "fail_step_25al_r1_reconciliation_doc_copy",
            [],
            [],
            ["docs/audit_expected_active_state_reconciliation_25al_r1_copy.md"],
            set(),
            False,
        ),
        (
            "fail_step_25al_r1_reconciliation_audit_copy",
            [],
            [],
            ["scripts/audit_expected_active_state_reconciliation_25al_r1_copy.py"],
            set(),
            False,
        ),
        (
            "fail_step_25al_acceptance_doc_copy",
            [],
            [],
            ["docs/core_product_manual_operator_acceptance_25al_copy.md"],
            set(),
            False,
        ),
        (
            "fail_step_25al_acceptance_audit_copy",
            [],
            [],
            ["scripts/audit_core_product_manual_operator_acceptance_25al_copy.py"],
            set(),
            False,
        ),
        (
            "fail_step_25am_repair_doc_copy",
            [],
            [],
            ["docs/reports_pdf_runtime_repair_25am_copy.md"],
            set(),
            False,
        ),
        (
            "fail_step_25am_runtime_audit_copy",
            [],
            [],
            ["scripts/audit_reports_pdf_runtime_repair_25am_copy.py"],
            set(),
            False,
        ),
        (
            "fail_step_25am_evidence_audit_copy",
            [],
            [],
            ["scripts/audit_reports_pdf_runtime_repair_evidence_25am_copy.py"],
            set(),
            False,
        ),
        (
            "fail_step_25an_closure_doc_copy",
            [],
            [],
            ["docs/operator_friction_acceptance_closure_25an_copy.md"],
            set(),
            False,
        ),
        (
            "fail_step_25an_closure_audit_copy",
            [],
            [],
            ["scripts/audit_operator_friction_acceptance_closure_25an_copy.py"],
            set(),
            False,
        ),
    ]
    results: dict[str, bool] = {}
    for name, staged, unstaged, untracked, tracked_artifacts, expected in cases:
        result = classify_repository_shape(staged, unstaged, untracked, tracked_artifacts)
        results[name] = result["allowed"] == expected
    return results


def port_closed(port: int = 5000) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def db_manifest(path: Path) -> dict[str, object]:
    stat = path.stat()
    manifest: dict[str, object] = {
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256(path),
    }
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*), COALESCE(MAX(id), 0) FROM audit_log")
        manifest["audit_log"] = tuple(cur.fetchone())
        cur.execute("SELECT COUNT(*) FROM role_permissions")
        manifest["role_permissions"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM (SELECT role_name, permission_name FROM role_permissions GROUP BY role_name, permission_name)")
        manifest["distinct_pairs"] = cur.fetchone()[0]
        cur.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT role_name, permission_name
                FROM role_permissions
                GROUP BY role_name, permission_name
                HAVING COUNT(*) > 1
            )
            """
        )
        manifest["duplicate_groups"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM governance_relationships")
        manifest["governance_relationships"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM governance_relationship_audit_ledger")
        manifest["governance_relationship_audit_ledger"] = cur.fetchone()[0]
        cur.execute("SELECT name, type FROM sqlite_master WHERE LOWER(name) LIKE '%compliance%' OR LOWER(name) LIKE '%system_observation%' ORDER BY type, name")
        manifest["compliance_or_system_objects"] = [dict(row) for row in cur.fetchall()]
        cur.execute("SELECT permission_name FROM role_permissions WHERE LOWER(permission_name) LIKE '%compliance%' ORDER BY permission_name")
        manifest["compliance_permissions"] = [row[0] for row in cur.fetchall()]
        cur.execute("PRAGMA integrity_check")
        manifest["integrity_check"] = cur.fetchone()[0]
        cur.execute("PRAGMA foreign_key_check")
        manifest["foreign_key_check_rows"] = len(cur.fetchall())
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cur.fetchall()]
        counts = {}
        for table in tables:
            cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            counts[table] = cur.fetchone()[0]
        manifest["table_counts"] = counts
    return manifest


def assert_db_baseline(manifest: dict[str, object]) -> None:
    fail_if(manifest["size"] != DB_SIZE, f"database size changed: {manifest['size']}")
    fail_if(manifest["mtime_ns"] != DB_MTIME_NS, f"database mtime changed: {manifest['mtime_ns']}")
    fail_if(manifest["sha256"] != DB_SHA, f"database sha changed: {manifest['sha256']}")
    fail_if(tuple(manifest["audit_log"]) != (569, 569), f"audit_log baseline changed: {manifest['audit_log']}")
    fail_if(manifest["role_permissions"] != 25, f"role_permissions changed: {manifest['role_permissions']}")
    fail_if(manifest["distinct_pairs"] != 25, f"distinct pairs changed: {manifest['distinct_pairs']}")
    fail_if(manifest["duplicate_groups"] != 0, f"duplicate groups changed: {manifest['duplicate_groups']}")
    fail_if(manifest["governance_relationships"] != 25, "governance_relationships changed")
    fail_if(manifest["governance_relationship_audit_ledger"] != 51, "governance audit ledger changed")
    fail_if(manifest["compliance_or_system_objects"], f"unexpected Compliance/System objects: {manifest['compliance_or_system_objects']}")
    fail_if(manifest["compliance_permissions"], f"unexpected Compliance permissions: {manifest['compliance_permissions']}")
    fail_if(manifest["integrity_check"] != "ok", f"integrity failure: {manifest['integrity_check']}")
    fail_if(manifest["foreign_key_check_rows"] != 0, f"foreign key failures: {manifest['foreign_key_check_rows']}")


def assert_repo_baseline() -> tuple[list[str], list[str], list[str]]:
    fail_if(Path.cwd().resolve() != REPO, f"wrong repository path: {Path.cwd()}")
    pass_line("repository path", REPO)
    fail_if(run(["git", "branch", "--show-current"]) != BRANCH, "branch mismatch")
    pass_line("branch", BRANCH)
    head = run(["git", "rev-parse", "HEAD"])
    remote_head = run(["git", "rev-parse", REMOTE_REF])
    fail_if(not git_ok("merge-base", "--is-ancestor", BASELINE_HEAD, "HEAD"), "local HEAD does not contain POST-V2-19 R1 baseline")
    pass_line("local head contains baseline", head)
    fail_if(not git_ok("merge-base", "--is-ancestor", BASELINE_HEAD, REMOTE_REF), "remote HEAD does not contain POST-V2-19 R1 baseline")
    pass_line("remote head contains baseline", remote_head)
    staged, unstaged, untracked = git_status()
    tracked_generated_artifacts = {
        normalize_repo_path(line)
        for line in run(["git", "ls-files", *sorted(GENERATED_LOCAL_ARTIFACT_FILES)]).splitlines()
        if line
    }
    repository_shape = classify_repository_shape(staged, unstaged, untracked, tracked_generated_artifacts)
    shape_self_tests = repository_shape_self_tests()
    fail_if(not repository_shape["allowed"], f"unauthorized repository paths: {repository_shape}")
    fail_if(not all(shape_self_tests.values()), f"repository shape self-tests failed: {shape_self_tests}")
    pass_line("repository shape limited to expected and approved later paths", repository_shape)
    pass_line("repository shape negative self-tests", shape_self_tests)
    fail_if(not port_closed(), "port 5000 is open")
    pass_line("port 5000 closed")
    sidecars = [str(p.relative_to(REPO)) for p in REPO.glob("trustee_app.db-*")]
    fail_if(sidecars, f"unexpected SQLite sidecars: {sidecars}")
    pass_line("no SQLite sidecars")
    return staged, unstaged, untracked


def assert_bookmark_and_h6g() -> None:
    fail_if(not POST_V18_DOC.exists(), "POST-V2-18 document missing")
    fail_if(not POST_V18_SCRIPT.exists(), "POST-V2-18 audit script missing")
    fail_if(not H6A_BACKUP.exists(), "H.6A backup missing")
    fail_if(sha256(H6A_BACKUP) != H6A_BACKUP_SHA, "H.6A backup SHA mismatch")
    v18_text = POST_V18_DOC.read_text(encoding="utf-8")
    v19_text = ACCEPTANCE_DOC.read_text(encoding="utf-8")
    for term in COMPLIANCE_BOOKMARK_TERMS:
        fail_if(term not in v18_text, f"Compliance bookmark term missing from POST-V2-18 doc: {term}")
        fail_if(term not in v19_text, f"Compliance bookmark term missing from POST-V2-19 doc: {term}")
    for path in H6G_LOCAL_FILES:
        fail_if(not path.exists(), f"deferred H.6G local file missing: {path}")
        ignored = subprocess.run(["git", "check-ignore", str(path)], cwd=REPO, text=True, capture_output=True, check=False)
        fail_if(ignored.returncode != 0, f"deferred H.6G file is not ignored: {path}")
    pass_line("deferred Compliance bookmark preserved")
    pass_line("deferred H.6G local files present and ignored")


def assert_acceptance_doc_prepared() -> None:
    fail_if(not ACCEPTANCE_DOC.exists(), "acceptance document missing")
    text = ACCEPTANCE_DOC.read_text(encoding="utf-8")
    for workflow in REQUIRED_WORKFLOWS:
        fail_if(workflow not in text, f"workflow missing: {workflow}")
    for url in REQUIRED_URLS:
        fail_if(url not in text, f"URL missing: {url}")
    fail_if("cd ~/Desktop/trustee-app-clean" not in text, "start command missing")
    fail_if("flask run" not in text, "flask run command missing")
    fail_if(text.count("____") < 40, "blank result fields missing")
    prohibited = [
        "manual browser pass",
        "operator acceptance passed",
        "operator sign-off: signed",
    ]
    lowered = text.lower()
    for term in prohibited:
        fail_if(term in lowered, f"false manual confirmation found: {term}")
    pass_line("acceptance document prepared", ACCEPTANCE_DOC)


def run_route_smoke_on_copy() -> None:
    with tempfile.TemporaryDirectory(prefix="post_v2_19_route_") as tmp:
        tmp_path = Path(tmp)
        db_copy = tmp_path / "trustee_app_route_smoke.db"
        shutil.copy2(DB, db_copy)
        env = os.environ.copy()
        env["DB_PATH"] = str(db_copy)
        env["PYTHONPATH"] = str(REPO)
        env["PYTHONPYCACHEPREFIX"] = str(tmp_path / "pycache")
        code = r"""
from datetime import datetime, UTC
from app import app

routes = [
    "/admin",
    "/intake/dashboard",
    "/matters/MAT-000001",
    "/trust/TR-001",
    "/fiduciaries",
    "/assets",
    "/documents",
    "/execution",
    "/execution/transfers/T-0001",
    "/certificates",
    "/governance",
    "/reports",
    "/archive",
    "/continuity",
    "/recovery",
    "/audit",
    "/admin/roles",
    "/admin/permissions",
]

client = app.test_client()
login = client.get("/admin")
assert login.status_code in {302, 303, 401, 403}, login.status_code
with client.session_transaction() as session:
    session["username"] = "admin123"
    session["role"] = "Admin"
    session["user_role"] = "Admin"
    session["is_master_admin"] = True
    session["firm_id"] = "FIRM-002"
    session["last_activity"] = datetime.now(UTC).timestamp()
for route in routes:
    response = client.get(route)
    assert response.status_code < 500, (route, response.status_code)
response = client.get("/compliance/reviews")
assert response.status_code in {404, 503}, response.status_code
response = client.get("/system/observations")
assert response.status_code in {404, 503}, response.status_code
response = client.get("/logout")
assert response.status_code in {200, 302, 303}, response.status_code
print("route smoke on temporary database PASS")
"""
        output = run([sys.executable, "-c", code], env=env)
        fail_if(sha256(DB) != DB_SHA, "normal DB changed during temporary route smoke")
        pass_line("representative GET route tests on temporary database", output)


def run_import_readonly() -> None:
    before = db_manifest(DB)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO)
    with tempfile.TemporaryDirectory(prefix="post_v2_19_import_") as tmp:
        env["PYTHONPYCACHEPREFIX"] = str(Path(tmp) / "pycache")
        run([sys.executable, "-c", "import app; print('import app PASS')"], env=env)
    after = db_manifest(DB)
    fail_if(before != after, "application import changed normal database")
    pass_line("application import read-only")


def run_automated_gates() -> None:
    compile_targets = [
        "app.py",
        "services/services_compliance_reviews.py",
        "services/services_governance.py",
        "scripts/audit_core_product_operator_acceptance_post_v2_19.py",
    ]
    with tempfile.TemporaryDirectory(prefix="post_v2_19_compile_") as tmp:
        env = os.environ.copy()
        env["PYTHONPYCACHEPREFIX"] = str(Path(tmp) / "pycache")
        run([sys.executable, "-m", "py_compile", *compile_targets], env=env)
    pass_line("Python compile checks", compile_targets)
    run_import_readonly()
    run_route_smoke_on_copy()
    run(["git", "diff", "--check"])
    pass_line("git diff --check")


def confirmed_mode() -> None:
    text = ACCEPTANCE_DOC.read_text(encoding="utf-8") if ACCEPTANCE_DOC.exists() else ""
    required_markers = [
        "Operator identity:",
        "Database post-test hash:",
        "Acceptance determination:",
        "Operator sign-off:",
    ]
    for marker in required_markers:
        fail_if(marker not in text, f"confirmed marker missing: {marker}")
    fail_if("Operator sign-off: ____" in text, "operator sign-off is still blank")
    fail_if("Acceptance determination: ____" in text, "acceptance determination is still blank")
    fail_if("Database post-test hash: ____" in text, "post-test hash is still blank")
    fail_if("PASS/FAIL" in text, "manual PASS/FAIL fields remain unresolved")
    raise AuditFailure("confirmed mode requires a later post-browser reconciliation script before it can pass")


def prepared_mode() -> None:
    assert_repo_baseline()
    manifest_before = db_manifest(DB)
    assert_db_baseline(manifest_before)
    pass_line("normal database baseline", {k: manifest_before[k] for k in manifest_before if k != "table_counts"})
    assert_bookmark_and_h6g()
    assert_acceptance_doc_prepared()
    run_automated_gates()
    manifest_after = db_manifest(DB)
    assert_db_baseline(manifest_after)
    fail_if(manifest_before != manifest_after, "normal database changed during audit")
    print("AUTOMATED_PRE_BROWSER_GATES_PASS=True")
    print("PRE_BROWSER_DB_UNCHANGED=True")
    print("COMPLIANCE_NORMAL_DB_ACTIVATED=False")
    print(json.dumps({"db": {k: manifest_after[k] for k in manifest_after if k != "table_counts"}, "untracked": sorted(EXPECTED_UNTRACKED)}, sort_keys=True))
    print("POST-V2-19 CORE PRODUCT OPERATOR ACCEPTANCE PREPARED")
    print("RESULT: PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["prepared", "confirmed"], default="prepared")
    args = parser.parse_args()
    try:
        if args.mode == "prepared":
            prepared_mode()
        else:
            confirmed_mode()
    except AuditFailure as exc:
        print(f"FAIL - {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
