"""
V2-HARDEN-6 — GitHub / Deployment Readiness Check

Script-only hardening audit.

Purpose:
- Verify active branch is v2-development.
- Verify working tree is clean.
- Verify local HEAD matches origin/v2-development.
- Verify required V2 hardening audit scripts exist.
- Verify required governance evidence templates exist.
- Verify key Python files compile.
- Verify no merge conflict markers exist in tracked source files.
- Verify no runtime DB file is staged or modified.
- Verify obvious deployment files are present.

This script does not deploy, does not mutate the database, does not tag Version 2,
and does not create certification records.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import py_compile
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


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


def compile_file(path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        return True, str(path.relative_to(ROOT))
    except Exception as exc:
        return False, f"{path.relative_to(ROOT)} — {type(exc).__name__}: {exc}"


def tracked_files() -> list[Path]:
    code, out, _ = run_git(["ls-files"])
    if code != 0:
        return []
    return [ROOT / line for line in out.splitlines() if line.strip()]


def has_conflict_marker(path: Path) -> bool:
    """
    Detect actual Git merge conflict markers.

    Separator lines containing ======= in handoffs, reports, markdown, JSON, or
    runbooks are not conflicts unless they appear as full-line Git conflict markers.
    """
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return False

    has_start = any(line.startswith("<<<<<<< ") for line in lines)
    has_middle = any(line.strip() == "=======" for line in lines)
    has_end = any(line.startswith(">>>>>>> ") for line in lines)

    return has_start and has_middle and has_end


def main() -> int:
    checks: list[Check] = []

    print("V2-HARDEN-6 GITHUB / DEPLOYMENT READINESS AUDIT")
    print("=" * 76)
    print(f"Repo Root: {ROOT}")
    print("Mode: read-only GitHub/deployment readiness audit")
    print("")

    code, branch, err = run_git(["branch", "--show-current"])
    add(checks, "git_branch_detected", code == 0, branch or err)
    add(checks, "branch_is_v2_development", branch == "v2-development", branch)

    code, status_short, err = run_git(["status", "--short"])
    add(checks, "git_status_short_available", code == 0, err or "ok")

    # During first execution of this audit, this script is expected to be untracked.
    # Treat the working tree as clean if this script is the only untracked path.
    ignored_self = "?? scripts/audit_v2_github_deployment_readiness.py"
    status_lines = [line for line in status_short.splitlines() if line.strip()]
    effective_status_lines = [line for line in status_lines if line.strip() != ignored_self]

    add(
        checks,
        "working_tree_clean_or_only_this_audit_untracked",
        effective_status_lines == [],
        "\n".join(effective_status_lines) if effective_status_lines else "clean or only this audit script untracked",
    )

    code, head_sha, err = run_git(["rev-parse", "HEAD"])
    add(checks, "head_sha_available", code == 0, head_sha or err)

    code, origin_sha, err = run_git(["rev-parse", "origin/v2-development"])
    add(checks, "origin_sha_available", code == 0, origin_sha or err)

    if head_sha and origin_sha:
        add(checks, "head_matches_origin_v2", head_sha == origin_sha, f"HEAD={head_sha}, origin={origin_sha}")

    code, top_log, err = run_git(["log", "--oneline", "--decorate", "-10"])
    add(checks, "git_log_available", code == 0, top_log.splitlines()[0] if top_log else err)

    required_scripts = [
        "scripts/audit_local_db_writability.py",
        "scripts/audit_governance_route_template_service_inventory.py",
        "scripts/audit_governance_evidence_access_control.py",
        "scripts/audit_governance_export_path_regression.py",
        "scripts/audit_governance_data_mutation_boundary.py",
        "scripts/audit_v2_github_deployment_readiness.py",
        "scripts/smoke_matter_governance_timeline.py",
    ]

    print("REQUIRED SCRIPT INVENTORY")
    print("-" * 76)
    for rel in required_scripts:
        path = ROOT / rel
        exists = path.exists()
        print(f"{'PASS' if exists else 'FAIL'}: {rel}")
        add(checks, f"required_script_exists:{rel}", exists, rel)

    required_templates = [
        "templates/governance/evidence_export_index.html",
        "templates/governance/evidence_export_manifest.html",
        "templates/governance/evidence_export_integrity.html",
        "templates/governance/evidence_export_archive_intake.html",
        "templates/governance/evidence_certification_dashboard.html",
        "templates/governance/evidence_exception_panel.html",
        "templates/governance/evidence_completion_gate.html",
    ]

    print("")
    print("REQUIRED TEMPLATE INVENTORY")
    print("-" * 76)
    for rel in required_templates:
        path = ROOT / rel
        exists = path.exists()
        print(f"{'PASS' if exists else 'FAIL'}: {rel}")
        add(checks, f"required_template_exists:{rel}", exists, rel)

    compile_targets = [
        "app.py",
        "services/services_governance.py",
        "scripts/audit_local_db_writability.py",
        "scripts/audit_governance_route_template_service_inventory.py",
        "scripts/audit_governance_evidence_access_control.py",
        "scripts/audit_governance_export_path_regression.py",
        "scripts/audit_governance_data_mutation_boundary.py",
        "scripts/audit_v2_github_deployment_readiness.py",
        "scripts/smoke_matter_governance_timeline.py",
    ]

    print("")
    print("PYTHON COMPILE CHECK")
    print("-" * 76)
    for rel in compile_targets:
        path = ROOT / rel
        if not path.exists():
            add(checks, f"compile_target_exists:{rel}", False, rel)
            print(f"FAIL: missing {rel}")
            continue
        ok, detail = compile_file(path)
        print(f"{'PASS' if ok else 'FAIL'}: {detail}")
        add(checks, f"py_compile:{rel}", ok, detail)

    deployment_candidates = [
        "requirements.txt",
        "app.py",
    ]

    optional_deployment_candidates = [
        "Procfile",
        "railway.json",
        "render.yaml",
        "Dockerfile",
        ".python-version",
        "runtime.txt",
    ]

    print("")
    print("DEPLOYMENT FILE INVENTORY")
    print("-" * 76)
    for rel in deployment_candidates:
        path = ROOT / rel
        exists = path.exists()
        print(f"{'PASS' if exists else 'FAIL'}: required {rel}")
        add(checks, f"deployment_required_exists:{rel}", exists, rel)

    optional_found = []
    for rel in optional_deployment_candidates:
        if (ROOT / rel).exists():
            optional_found.append(rel)

    add(
        checks,
        "deployment_optional_file_detected",
        True,
        ", ".join(optional_found) if optional_found else "No optional platform file detected; acceptable for local baseline.",
    )

    print("")
    print("RUNTIME DB / LARGE MUTATION GUARD")
    print("-" * 76)
    runtime_paths = [
        "data/trustee_app.db",
        "trustee_app.db",
        "database.db",
        "data/database.db",
    ]

    code, porcelain, _ = run_git(["status", "--porcelain"])
    for rel in runtime_paths:
        touched = any(line.endswith(rel) for line in porcelain.splitlines())
        print(f"{'FAIL' if touched else 'PASS'}: runtime path not modified/staged — {rel}")
        add(checks, f"runtime_path_not_touched:{rel}", not touched, rel)

    print("")
    print("CONFLICT MARKER SCAN")
    print("-" * 76)
    conflict_files = []
    allowed_suffixes = {
        ".py", ".html", ".txt", ".md", ".json", ".yaml", ".yml", ".css", ".js"
    }
    for path in tracked_files():
        if path.suffix.lower() not in allowed_suffixes:
            continue
        if has_conflict_marker(path):
            conflict_files.append(str(path.relative_to(ROOT)))

    add(
        checks,
        "no_conflict_markers",
        not conflict_files,
        ", ".join(conflict_files) if conflict_files else "none",
    )
    print(f"{'PASS' if not conflict_files else 'FAIL'}: conflict markers — {', '.join(conflict_files) if conflict_files else 'none'}")

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
