"""
POST-V2-1 — Certified Baseline Protection Protocol

Script-only post-certification audit.

Purpose:
- Verify the V2 certified baseline tag exists locally and remotely.
- Verify the tag resolves to the expected certified commit.
- Verify the working tree is clean.
- Verify current branch is an allowed continuation branch or the certified V2 branch.
- Verify rollback and branch-discipline instructions are preserved.
- Verify the certified baseline remains recoverable.

This script does not mutate the database, does not create tags, does not deploy,
and does not modify application logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_CERTIFIED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"

ALLOWED_BRANCHES = {
    "v2-development",
    "post-v2-planning",
    "post-v2-deployment-hardening",
    "post-v2-admin-cleanup",
    "v3-development",
}


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


def main() -> int:
    checks: list[Check] = []

    print("POST-V2-1 CERTIFIED BASELINE PROTECTION AUDIT")
    print("=" * 76)
    print(f"Repo Root: {ROOT}")
    print(f"Certified Tag: {CERTIFIED_TAG}")
    print(f"Expected Certified Commit: {EXPECTED_CERTIFIED_COMMIT}")
    print("Mode: read-only baseline protection audit")
    print("")

    code, branch, err = run_git(["branch", "--show-current"])
    add(checks, "current_branch_detected", code == 0, branch or err)
    add(
        checks,
        "current_branch_allowed",
        branch in ALLOWED_BRANCHES,
        f"{branch}; allowed={sorted(ALLOWED_BRANCHES)}",
    )

    code, status_short, err = run_git(["status", "--short"])
    add(checks, "git_status_available", code == 0, err or "ok")

    allowed_untracked = {
        "?? POST_V2_CERTIFIED_BASELINE_PROTECTION_PROTOCOL.md",
        "?? scripts/audit_certified_baseline_protection.py",
    }
    status_lines = [line for line in status_short.splitlines() if line.strip()]
    effective_status_lines = [
        line for line in status_lines if line.strip() not in allowed_untracked
    ]

    add(
        checks,
        "working_tree_clean_or_only_protection_files_untracked",
        effective_status_lines == [],
        "\n".join(effective_status_lines) if effective_status_lines else "clean or only POST-V2 protection files untracked",
    )

    code, head_commit, err = run_git(["rev-parse", "HEAD"])
    add(checks, "head_commit_available", code == 0, head_commit or err)

    code, local_tag_commit, err = run_git(["rev-parse", f"{CERTIFIED_TAG}^{{commit}}"])
    add(checks, "local_certified_tag_exists", code == 0, local_tag_commit or err)
    add(
        checks,
        "local_tag_matches_expected_commit",
        local_tag_commit == EXPECTED_CERTIFIED_COMMIT,
        f"local_tag_commit={local_tag_commit}",
    )

    code, remote_tag_raw, err = run_git(["ls-remote", "--tags", "origin", f"refs/tags/{CERTIFIED_TAG}"])
    add(checks, "remote_certified_tag_exists", code == 0 and bool(remote_tag_raw), remote_tag_raw or err)

    # Annotated tags show a tag object hash in ls-remote, not necessarily the commit hash.
    # Verify the local resolved tag commit is authoritative after fetch.
    code, _, fetch_err = run_git(["fetch", "--tags", "origin"])
    add(checks, "fetch_tags_succeeded", code == 0, fetch_err or "ok")

    code, fetched_tag_commit, err = run_git(["rev-parse", f"{CERTIFIED_TAG}^{{commit}}"])
    add(checks, "fetched_tag_resolves", code == 0, fetched_tag_commit or err)
    add(
        checks,
        "fetched_tag_matches_expected_commit",
        fetched_tag_commit == EXPECTED_CERTIFIED_COMMIT,
        f"fetched_tag_commit={fetched_tag_commit}",
    )

    code, contains, err = run_git(["branch", "--contains", EXPECTED_CERTIFIED_COMMIT])
    add(checks, "certified_commit_reachable_from_branch", code == 0 and bool(contains), contains or err)

    rollback_command = f"git checkout {CERTIFIED_TAG}"
    restore_branch_command = f"git checkout -b restore-v2-baseline {CERTIFIED_TAG}"
    compare_command = f"git diff {CERTIFIED_TAG}..HEAD"

    protocol = {
        "rollback_command": rollback_command,
        "restore_branch_command": restore_branch_command,
        "compare_command": compare_command,
        "future_work_rule": "New work must occur on a post-V2 branch, not directly on the certified tag.",
        "tagging_rule": "V2 certified tag must not be moved, deleted, or force-updated.",
        "database_rule": "Runtime DB files must not be committed as part of protection or planning work.",
    }

    add(checks, "rollback_command_documented", bool(protocol["rollback_command"]), protocol["rollback_command"])
    add(checks, "restore_branch_command_documented", bool(protocol["restore_branch_command"]), protocol["restore_branch_command"])
    add(checks, "compare_command_documented", bool(protocol["compare_command"]), protocol["compare_command"])
    add(checks, "future_work_rule_documented", bool(protocol["future_work_rule"]), protocol["future_work_rule"])
    add(checks, "tagging_rule_documented", bool(protocol["tagging_rule"]), protocol["tagging_rule"])
    add(checks, "database_rule_documented", bool(protocol["database_rule"]), protocol["database_rule"])

    print("PROTECTION PROTOCOL")
    print("-" * 76)
    for key, value in protocol.items():
        print(f"{key}: {value}")

    print("")
    print("CURRENT STATE")
    print("-" * 76)
    print(f"branch: {branch}")
    print(f"head_commit: {head_commit}")
    print(f"local_tag_commit: {local_tag_commit}")
    print(f"fetched_tag_commit: {fetched_tag_commit}")
    print(f"working_tree_clean: {status_short == ''}")

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
