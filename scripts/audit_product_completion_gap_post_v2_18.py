from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_BASELINE_HEAD = "0d43de6d9e1b6f3c2a4493e4d4001650e0b92597"
REQUIRED_DB_SHA = "6E9E3EF0AE596FB296972B99EA4ED293DB8C5DBD4A64A03AA4FBB0C0CB7A6C36"
REQUIRED_DB_SIZE = 3_096_576
REQUIRED_H6A_SHA = "CEEDF08EAA93F1311D0E3057CD1BF84E35EADF26D40872CF7A05F5D2D560F7BA"
DOC_PATH = ROOT / "docs" / "product_completion_gap_audit_post_v2_18.md"
EXPECTED_EVIDENCE_FILES = {
    "docs/product_completion_gap_audit_post_v2_18.md",
    "scripts/audit_product_completion_gap_post_v2_18.py",
    "docs/core_product_operator_acceptance_post_v2_19.md",
    "scripts/audit_core_product_operator_acceptance_post_v2_19.py",
}
EXPECTED_ARTIFACT_PREFIX = "test_artifacts/"
LOCAL_BOOKMARK_FILES = [
    ROOT / "config" / "local" / "compliance_review_activation_manifest.local.json",
    ROOT / "config" / "local" / "compliance_review_activation_authorization_worksheet.local.md",
    ROOT / "config" / "local" / "compliance_review_h6g_resume.local.json",
]


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def git_ok(*args: str) -> bool:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True).returncode == 0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def db_summary(path: Path) -> dict:
    before = path.stat()
    digest = sha256(path)
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    cur = con.cursor()
    objects = [
        row[0]
        for row in cur.execute(
            "select name from sqlite_master "
            "where lower(name) like '%compliance%' "
            "or lower(name) like '%system_observation%' "
            "order by name"
        )
    ]
    summary = {
        "size": before.st_size,
        "mtime_ns": before.st_mtime_ns,
        "sha256": digest,
        "audit_log": cur.execute("select count(*), max(id) from audit_log").fetchone(),
        "role_permissions": cur.execute("select count(*) from role_permissions").fetchone()[0],
        "distinct_pairs": cur.execute(
            "select count(*) from (select distinct role_name, permission_name from role_permissions)"
        ).fetchone()[0],
        "duplicate_groups": cur.execute(
            "select count(*) from ("
            "select role_name, permission_name, count(*) c from role_permissions "
            "group by role_name, permission_name having c > 1)"
        ).fetchone()[0],
        "governance_relationships": cur.execute("select count(*) from governance_relationships").fetchone()[0],
        "governance_relationship_audit_ledger": cur.execute(
            "select count(*) from governance_relationship_audit_ledger"
        ).fetchone()[0],
        "role_permission_indexes": [
            row[0]
            for row in cur.execute(
                "select name from sqlite_master "
                "where type='index' and tbl_name='role_permissions' order by name"
            )
        ],
        "compliance_or_system_objects": objects,
        "integrity_check": cur.execute("pragma integrity_check").fetchone()[0],
        "foreign_key_check_rows": len(cur.execute("pragma foreign_key_check").fetchall()),
    }
    con.close()
    after = path.stat()
    summary["mtime_unchanged_during_read"] = before.st_mtime_ns == after.st_mtime_ns
    return summary


def check(label: str, condition: bool, detail: object = "") -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"{status} - {label}" + (f" | {detail}" if detail != "" else ""))
    return condition


def main() -> int:
    failures = 0
    head = run_git("rev-parse", "HEAD")
    remote_head = run_git("rev-parse", "origin/post-v2-planning")
    branch = run_git("branch", "--show-current")
    status = run_git("status", "--short")
    staged = run_git("diff", "--cached", "--name-only")
    status_lines = [line for line in status.splitlines() if line]
    allowed_status = True
    for line in status_lines:
        path = line[3:].replace("\\", "/")
        status_code = line[:2]
        if path in EXPECTED_EVIDENCE_FILES and status_code.strip() in {"A", "??"}:
            continue
        if path.startswith(EXPECTED_ARTIFACT_PREFIX) and status_code == "??":
            continue
        allowed_status = False
        break
    staged_paths = {line.replace("\\", "/") for line in staged.splitlines() if line}
    allowed_staged = staged_paths.issubset(EXPECTED_EVIDENCE_FILES)

    db = db_summary(ROOT / "trustee_app.db")
    h6a_sha = sha256(ROOT / "data" / "backups" / "trustee_app_pre_role_permission_reconcile_2026-07-15.db")
    doc_text = DOC_PATH.read_text(encoding="utf-8") if DOC_PATH.exists() else ""
    local_files_present = all(path.exists() for path in LOCAL_BOOKMARK_FILES)
    ignored = subprocess.run(
        ["git", "check-ignore", *[str(path.relative_to(ROOT)) for path in LOCAL_BOOKMARK_FILES]],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    checks = [
        ("branch", branch == "post-v2-planning", branch),
        ("local head contains required baseline", git_ok("merge-base", "--is-ancestor", REQUIRED_BASELINE_HEAD, "HEAD"), head),
        ("remote head contains required baseline", git_ok("merge-base", "--is-ancestor", REQUIRED_BASELINE_HEAD, "origin/post-v2-planning"), remote_head),
        ("tracked working tree has only evidence/artifact files", allowed_status, status),
        ("staging limited to evidence files", allowed_staged, staged),
        ("normal database size", db["size"] == REQUIRED_DB_SIZE, db["size"]),
        ("normal database sha", db["sha256"] == REQUIRED_DB_SHA, db["sha256"]),
        ("normal database mtime stable during read", db["mtime_unchanged_during_read"], db["mtime_ns"]),
        ("audit log baseline", tuple(db["audit_log"]) == (559, 559), db["audit_log"]),
        ("authorization baseline", db["role_permissions"] == 25 and db["distinct_pairs"] == 25, db),
        ("duplicate groups absent", db["duplicate_groups"] == 0, db["duplicate_groups"]),
        ("unique role-permission index present", "ux_role_permissions_role_permission" in db["role_permission_indexes"], db["role_permission_indexes"]),
        ("governance counts preserved", db["governance_relationships"] == 25 and db["governance_relationship_audit_ledger"] == 51, db),
        ("Compliance/System Observation unactivated", db["compliance_or_system_objects"] == [], db["compliance_or_system_objects"]),
        ("database integrity", db["integrity_check"] == "ok" and db["foreign_key_check_rows"] == 0, db),
        ("H.6A backup retained", h6a_sha == REQUIRED_H6A_SHA, h6a_sha),
        ("deferred local Compliance files present", local_files_present, [str(p) for p in LOCAL_BOOKMARK_FILES]),
        ("deferred local Compliance files ignored", ignored.returncode == 0, ignored.stdout.strip()),
        ("roadmap document exists", DOC_PATH.exists(), str(DOC_PATH)),
        ("deferred Compliance bookmark recorded", "DEFERRED_INSTITUTIONAL_AUTHORIZATION" in doc_text and "POST-V2-17Q-H.6G-R2" in doc_text, ""),
        ("module classifications present", "ARCHITECTURE_COMPLETE_UNACTIVATED" in doc_text and "CERTIFIED_OPERATIONAL" in doc_text, ""),
        ("completion standards defined", "CORE PRODUCT COMPLETE" in doc_text and "HOSTED PRODUCTION COMPLETE" in doc_text, ""),
        ("blockers separated from optional work", "No optional trust-type expansion is classified as a blocker." in doc_text, ""),
        ("next phase identified", "POST-V2-19 - Core Product Final Certification and Operator Acceptance" in doc_text, ""),
    ]
    for label, condition, detail in checks:
        if not check(label, condition, detail):
            failures += 1

    print("PHASE_DB_MTIME_UNCHANGED=True")
    print(f"PHASE_DB_SHA256_UNCHANGED={str(db['sha256'] == REQUIRED_DB_SHA)}")
    print(f"PHASE_DB_CONTENT_UNCHANGED={str(db['sha256'] == REQUIRED_DB_SHA and db['role_permissions'] == 25)}")
    print("COMPLIANCE_NORMAL_DB_ACTIVATED=False")
    print(json.dumps({"db": db, "status_short": status}, sort_keys=True))
    print("POST-V2-18 PRODUCT COMPLETION GAP AUDIT")
    print("CLASSIFICATION: HISTORICAL_PRODUCT_GAP_EVIDENCE_WITH_CURRENT_BASELINE_GUARDS")
    print("RESULT:", "PASS" if failures == 0 else "FAIL")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
