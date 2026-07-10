"""
POST-V2-2 — Deployment Hardening Audit

Script-only audit for production/deployment readiness after the V2 certified baseline.

This script is read-only. It does not deploy, does not mutate the database,
does not create tags, and does not modify application logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_CERTIFIED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"

ALLOWED_BRANCHES = {
    "post-v2-planning",
    "post-v2-deployment-hardening",
}

REQUIRED_FILES = [
    "app.py",
    "requirements.txt",
]

OPTIONAL_DEPLOYMENT_FILES = [
    "Procfile",
    "render.yaml",
]

RUNTIME_DB_PATHS = [
    "data/trustee_app.db",
    "trustee_app.db",
    "database.db",
    "data/database.db",
]

LOCAL_ONLY_PATH_MARKERS = [
    "C:\\\\Users\\\\",
    "C:/Users/",
    "\\\\Desktop\\\\",
    "/Desktop/",
    "sqlite:///C:",
]

EXPECTED_ENV_MARKERS = [
    "os.environ",
    "os.getenv",
    "SECRET_KEY",
    "DB_PATH",
    "UPLOAD_FOLDER",
    "EXPORT_ROOT",
]


@dataclass
class Check:
    key: str
    status: str
    detail: str


def add(checks: list[Check], key: str, ok: bool, detail: str) -> None:
    checks.append(Check(key=key, status="PASS" if ok else "FAIL", detail=detail))


def run_git(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def read_text(rel_path: str) -> str:
    path = ROOT / rel_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def file_exists(rel_path: str) -> bool:
    return (ROOT / rel_path).exists()


def main() -> int:
    checks: list[Check] = []

    print("POST-V2-2 DEPLOYMENT HARDENING AUDIT")
    print("=" * 76)
    print(f"Repo Root: {ROOT}")
    print(f"Certified Tag: {CERTIFIED_TAG}")
    print(f"Expected Certified Commit: {EXPECTED_CERTIFIED_COMMIT}")
    print("Mode: read-only deployment hardening audit")
    print("")

    code, branch, err = run_git(["branch", "--show-current"])
    add(checks, "current_branch_detected", code == 0, branch or err)
    add(
        checks,
        "current_branch_allowed_for_deployment_hardening",
        branch in ALLOWED_BRANCHES,
        f"{branch}; allowed={sorted(ALLOWED_BRANCHES)}",
    )

    code, status_short, err = run_git(["status", "--short"])
    add(checks, "git_status_available", code == 0, err or "ok")

    allowed_untracked = {
        "?? scripts/audit_post_v2_deployment_hardening.py",
        "?? POST_V2_DEPLOYMENT_HARDENING_PROTOCOL.md",
    }
    status_lines = [line for line in status_short.splitlines() if line.strip()]
    effective_status_lines = [
        line for line in status_lines if line.strip() not in allowed_untracked
    ]

    add(
        checks,
        "working_tree_clean_or_only_deployment_hardening_files_untracked",
        effective_status_lines == [],
        "\\n".join(effective_status_lines) if effective_status_lines else "clean or only POST-V2 deployment hardening files untracked",
    )

    code, head_commit, err = run_git(["rev-parse", "HEAD"])
    add(checks, "head_commit_available", code == 0, head_commit or err)

    code, local_tag_commit, err = run_git(["rev-parse", f"{CERTIFIED_TAG}^{{commit}}"])
    add(checks, "certified_tag_exists_locally", code == 0, local_tag_commit or err)
    add(
        checks,
        "certified_tag_matches_expected_commit",
        local_tag_commit == EXPECTED_CERTIFIED_COMMIT,
        f"local_tag_commit={local_tag_commit}",
    )

    code, remote_tag_raw, err = run_git(["ls-remote", "--tags", "origin", f"refs/tags/{CERTIFIED_TAG}"])
    add(checks, "certified_tag_exists_remotely", code == 0 and bool(remote_tag_raw), remote_tag_raw or err)

    for rel in REQUIRED_FILES:
        add(checks, f"required_file_exists:{rel}", file_exists(rel), rel)

    deployment_file_presence = {rel: file_exists(rel) for rel in OPTIONAL_DEPLOYMENT_FILES}
    add(
        checks,
        "deployment_descriptor_present",
        any(deployment_file_presence.values()),
        str(deployment_file_presence),
    )

    app_text = read_text("app.py")
    requirements_text = read_text("requirements.txt")
    procfile_text = read_text("Procfile")
    render_text = read_text("render.yaml")
    protocol_text = read_text("POST_V2_CERTIFIED_BASELINE_PROTECTION_PROTOCOL.md")

    add(
        checks,
        "app_uses_environment_configuration",
        any(marker in app_text for marker in EXPECTED_ENV_MARKERS),
        "found env/config markers" if any(marker in app_text for marker in EXPECTED_ENV_MARKERS) else "missing expected env/config markers",
    )

    add(
        checks,
        "secret_key_configuration_detected",
        "SECRET_KEY" in app_text or "secret_key" in app_text,
        "SECRET_KEY or secret_key detected",
    )

    add(
        checks,
        "db_path_configuration_detected",
        "DB_PATH" in app_text or "trustee_app.db" in app_text,
        "DB_PATH or trustee_app.db detected",
    )

    add(
        checks,
        "upload_folder_configuration_detected",
        "UPLOAD_FOLDER" in app_text or "upload" in app_text.lower(),
        "UPLOAD_FOLDER or upload handling detected",
    )

    add(
        checks,
        "export_root_configuration_detected",
        "EXPORT_ROOT" in app_text or "export" in app_text.lower(),
        "EXPORT_ROOT or export handling detected",
    )

    local_only_hits = []
    for rel in ["app.py", "Procfile", "render.yaml", ".env.example"]:
        text = read_text(rel)
        for marker in LOCAL_ONLY_PATH_MARKERS:
            if marker in text:
                local_only_hits.append(f"{rel}:{marker}")

    add(
        checks,
        "no_local_only_deployment_paths_detected",
        not local_only_hits,
        "none" if not local_only_hits else "; ".join(local_only_hits),
    )

    staged_or_modified_runtime_db = []
    for line in status_lines:
        cleaned = line.strip()
        for db_path in RUNTIME_DB_PATHS:
            if cleaned.endswith(db_path):
                staged_or_modified_runtime_db.append(cleaned)

    add(
        checks,
        "runtime_db_not_modified_or_staged",
        not staged_or_modified_runtime_db,
        "none" if not staged_or_modified_runtime_db else "\\n".join(staged_or_modified_runtime_db),
    )

    required_packages = ["Flask"]
    missing_packages = [
        pkg for pkg in required_packages if pkg.lower() not in requirements_text.lower()
    ]

    add(
        checks,
        "requirements_include_flask",
        not missing_packages,
        "Flask present" if not missing_packages else f"missing={missing_packages}",
    )

    startup_text = "\\n".join([procfile_text, render_text])
    startup_markers = ["gunicorn", "python app.py", "app:app", "flask"]
    found_startup_markers = [marker for marker in startup_markers if marker.lower() in startup_text.lower()]

    add(
        checks,
        "deployment_startup_command_detected",
        bool(found_startup_markers),
        f"found={found_startup_markers}" if found_startup_markers else "no startup command markers found",
    )

    add(
        checks,
        "baseline_protection_protocol_present",
        file_exists("POST_V2_CERTIFIED_BASELINE_PROTECTION_PROTOCOL.md"),
        "POST_V2_CERTIFIED_BASELINE_PROTECTION_PROTOCOL.md",
    )

    add(
        checks,
        "rollback_instruction_preserved",
        CERTIFIED_TAG in protocol_text and "git checkout" in protocol_text,
        "rollback instruction references certified tag",
    )

    add(
        checks,
        "deployment_hardening_protocol_present_or_pending",
        file_exists("POST_V2_DEPLOYMENT_HARDENING_PROTOCOL.md"),
        "POST_V2_DEPLOYMENT_HARDENING_PROTOCOL.md",
    )

    print("DEPLOYMENT FILE PRESENCE")
    print("-" * 76)
    for rel in REQUIRED_FILES:
        print(f"REQUIRED | {'PRESENT' if file_exists(rel) else 'MISSING'} | {rel}")
    for rel in OPTIONAL_DEPLOYMENT_FILES:
        print(f"OPTIONAL | {'PRESENT' if file_exists(rel) else 'MISSING'} | {rel}")

    print("")
    print("CURRENT STATE")
    print("-" * 76)
    print(f"branch: {branch}")
    print(f"head_commit: {head_commit}")
    print(f"certified_tag_commit: {local_tag_commit}")
    print(f"working_tree_effective_clean: {effective_status_lines == []}")

    print("")
    print("SUMMARY")
    print("-" * 76)

    pass_count = sum(1 for c in checks if c.status == "PASS")
    fail_count = sum(1 for c in checks if c.status == "FAIL")

    for check in checks:
        print(f"{check.status}: {check.key} — {check.detail}")

    print("")
    print(f"checks_total: {len(checks)}")
    print(f"checks_passed: {pass_count}")
    print(f"checks_failed: {fail_count}")

    if fail_count:
        print("")
        print("RESULT: FAIL")
        return 1

    print("")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
