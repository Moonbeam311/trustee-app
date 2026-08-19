#!/usr/bin/env python3

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


MANIFEST_PATH = Path("config/v3_control_manifest.json")
LEDGER_PATH = Path("docs/V3_ACTIVE_EXECUTION_LEDGER.md")

AUTHORITY_REF = "origin/system-1-annual-evaluation"
AUTHORITY_MANIFEST = "config/v3_control_manifest.json"


def git_result(*args):
    return subprocess.run(
        ["git", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def run_git(*args):
    result = git_result(*args)
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(path.read_bytes())


def canonical_text_bytes(path):
    data = path.read_bytes()
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def sha256_control_text(path):
    return sha256_bytes(canonical_text_bytes(path))


def fail(reasons):
    print("V3_CONTROL_GUARD=STOP")
    for reason in reasons:
        print(f"REASON={reason}")
    return 2


def remote_manifest():
    result = git_result(
        "show",
        f"{AUTHORITY_REF}:{AUTHORITY_MANIFEST}",
    )
    if result.returncode != 0:
        return None

    try:
        return json.loads(result.stdout)
    except Exception:
        return "__INVALID_REMOTE_JSON__"


def load_working_manifest():
    try:
        return json.loads(
            MANIFEST_PATH.read_text(encoding="utf-8")
        )
    except Exception as exc:
        raise RuntimeError(str(exc))


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help=(
            "Validate the first uncommitted control root. "
            "Bootstrap mode never authorizes feature work."
        ),
    )

    parser.add_argument(
        "--authorize",
        help="Require exact next_authorized_action.",
    )

    parser.add_argument(
        "--allow-local-ahead",
        action="store_true",
    )

    args = parser.parse_args()
    reasons = []

    if not MANIFEST_PATH.is_file():
        return fail(["CONTROL_MANIFEST_MISSING"])

    try:
        working_manifest = load_working_manifest()
    except Exception as exc:
        return fail([f"CONTROL_MANIFEST_INVALID:{exc}"])

    authority = remote_manifest()

    if args.bootstrap:
        if authority is not None:
            return fail([
                "BOOTSTRAP_FORBIDDEN:"
                "REMOTE_CONTROL_ROOT_ALREADY_EXISTS"
            ])
        manifest = working_manifest

    else:
        if authority is None:
            return fail([
                "REMOTE_CONTROL_ROOT_MISSING:"
                + AUTHORITY_REF
            ])

        if authority == "__INVALID_REMOTE_JSON__":
            return fail([
                "REMOTE_CONTROL_ROOT_INVALID_JSON:"
                + AUTHORITY_REF
            ])

        if working_manifest != authority:
            return fail([
                "CONTROL_MANIFEST_DIFFERS_FROM_AUTHORITY:"
                + AUTHORITY_REF
            ])

        manifest = authority

    required = (
        "control_version",
        "repository",
        "branch",
        "certified_head",
        "remote_ref",
        "source_db",
        "protected_paths",
        "protected_sha256",
        "certified_phases",
        "active_phase",
        "allowed_dirty_paths",
        "next_authorized_action",
        "control_files",
    )

    for key in required:
        if key not in manifest:
            reasons.append(f"MANIFEST_FIELD_MISSING:{key}")

    if reasons:
        return fail(reasons)

    if manifest["remote_ref"] != AUTHORITY_REF:
        reasons.append(
            "AUTHORITY_REF_MISMATCH:"
            f"expected={AUTHORITY_REF}:"
            f"manifest={manifest['remote_ref']}"
        )

    certified_phases = manifest["certified_phases"]
    active_phase = manifest["active_phase"]
    suspended = manifest.get("suspended_feature_phase")

    if active_phase in certified_phases:
        reasons.append(
            "CERTIFIED_PHASE_CANNOT_BE_ACTIVE:"
            + active_phase
        )

    if suspended and suspended in certified_phases:
        reasons.append(
            "CERTIFIED_PHASE_CANNOT_BE_SUSPENDED:"
            + suspended
        )

    for raw, expected in manifest["control_files"].items():
        path = Path(raw)

        if not path.is_file():
            reasons.append(f"CONTROL_FILE_MISSING:{raw}")
            continue

        actual = sha256_control_text(path)

        if actual != expected:
            reasons.append(
                f"CONTROL_FILE_HASH_MISMATCH:{raw}:"
                f"expected={expected}:actual={actual}"
            )

    try:
        repo_root = Path(
            run_git("rev-parse", "--show-toplevel")
        ).resolve()
        branch = run_git("branch", "--show-current")
        head = run_git("rev-parse", "HEAD")
        remote_head = run_git("rev-parse", AUTHORITY_REF)
    except Exception as exc:
        return fail([f"GIT_STATE_UNAVAILABLE:{exc}"])

    if repo_root.name != manifest["repository"]:
        reasons.append(
            "REPOSITORY_MISMATCH:"
            f"expected={manifest['repository']}:"
            f"actual={repo_root.name}"
        )

    if branch != manifest["branch"]:
        reasons.append(
            "BRANCH_MISMATCH:"
            f"expected={manifest['branch']}:"
            f"actual={branch}"
        )

    certified_head = manifest["certified_head"]

    object_check = git_result(
        "cat-file",
        "-e",
        f"{certified_head}^{{commit}}",
    )

    if object_check.returncode != 0:
        reasons.append(
            f"CERTIFIED_HEAD_MISSING:{certified_head}"
        )
    else:
        ancestor = git_result(
            "merge-base",
            "--is-ancestor",
            certified_head,
            head,
        )
        if ancestor.returncode != 0:
            reasons.append(
                "CERTIFIED_HEAD_NOT_ANCESTOR:"
                + certified_head
            )

    for phase, commit in certified_phases.items():
        try:
            resolved = run_git(
                "rev-parse",
                f"{commit}^{{commit}}",
            )
        except Exception:
            reasons.append(
                f"CERTIFIED_PHASE_COMMIT_MISSING:"
                f"{phase}:{commit}"
            )
            continue

        ancestor = git_result(
            "merge-base",
            "--is-ancestor",
            resolved,
            head,
        )

        if ancestor.returncode != 0:
            reasons.append(
                f"CERTIFIED_PHASE_NOT_IN_HISTORY:"
                f"{phase}:{resolved}"
            )

    try:
        divergence = run_git(
            "rev-list",
            "--left-right",
            "--count",
            f"HEAD...{AUTHORITY_REF}",
        )

        ahead, behind = [
            int(value)
            for value in divergence.split()
        ]

        if behind != 0:
            reasons.append(f"REMOTE_AHEAD:behind={behind}")

        if ahead != 0 and not args.allow_local_ahead:
            reasons.append(f"LOCAL_AHEAD:ahead={ahead}")

    except Exception as exc:
        reasons.append(
            f"REMOTE_DIVERGENCE_UNAVAILABLE:{exc}"
        )

    staged = run_git(
        "diff",
        "--cached",
        "--name-only",
    ).splitlines()

    for path in staged:
        if path:
            reasons.append(
                f"UNEXPECTED_STAGED_PATH:{path}"
            )

    allowed_dirty = set(manifest["allowed_dirty_paths"])
    protected = set(manifest["protected_paths"])

    status_result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if status_result.returncode != 0:
        reasons.append("WORKTREE_STATUS_UNAVAILABLE")
    else:
        entries = [
            item.decode("utf-8", errors="replace")
            for item in status_result.stdout.split(b"\0")
            if item
        ]

        for entry in entries:
            if len(entry) < 4:
                reasons.append(
                    f"UNPARSEABLE_STATUS:{entry}"
                )
                continue

            path = entry[3:]

            if " -> " in path:
                path = path.split(" -> ", 1)[1]

            if path in protected:
                continue

            if path not in allowed_dirty:
                reasons.append(
                    f"UNEXPECTED_DIRTY_PATH:{path}"
                )

    for raw in manifest["protected_paths"]:
        path = Path(raw)
        expected = manifest["protected_sha256"].get(raw)

        if not path.is_file():
            reasons.append(
                f"PROTECTED_PATH_MISSING:{raw}"
            )
            continue

        if not expected:
            reasons.append(
                f"PROTECTED_HASH_NOT_RECORDED:{raw}"
            )
            continue

        actual = sha256_file(path)

        if actual != expected:
            reasons.append(
                f"PROTECTED_HASH_MISMATCH:{raw}:"
                f"expected={expected}:actual={actual}"
            )

    db = manifest["source_db"]
    db_path = Path(db["path"])

    if not db_path.is_file():
        reasons.append(
            f"SOURCE_DB_MISSING:{db['path']}"
        )
    else:
        actual = sha256_file(db_path)

        if actual != db["sha256"]:
            reasons.append(
                "SOURCE_DB_HASH_MISMATCH:"
                f"expected={db['sha256']}:"
                f"actual={actual}"
            )

    if not LEDGER_PATH.is_file():
        reasons.append(
            f"LEDGER_MISSING:{LEDGER_PATH}"
        )

    if args.bootstrap and args.authorize:
        reasons.append(
            "BOOTSTRAP_FEATURE_AUTHORIZATION_FORBIDDEN"
        )
    elif args.authorize:
        expected_action = manifest[
            "next_authorized_action"
        ]

        if args.authorize != expected_action:
            reasons.append(
                "UNAUTHORIZED_NEXT_ACTION:"
                f"expected={expected_action}:"
                f"requested={args.authorize}"
            )

    if reasons:
        return fail(reasons)

    if args.bootstrap:
        print("V3_CONTROL_GUARD=BOOTSTRAP_PASS")
        print("FEATURE_AUTHORIZATION=DENIED")
        print("CONTROL_ROOT_STATE=UNCOMMITTED")
    else:
        print("V3_CONTROL_GUARD=PASS")
        print("CONTROL_ROOT_STATE=REMOTE_GIT_ANCHORED")

    print(f"REPOSITORY={repo_root}")
    print(f"BRANCH={branch}")
    print(f"HEAD={head}")
    print(f"REMOTE_HEAD={remote_head}")
    print(f"CERTIFIED_BASELINE={certified_head}")
    print(f"ACTIVE_PHASE={active_phase}")
    print(
        "SUSPENDED_FEATURE_PHASE="
        + str(suspended or "NONE")
    )
    print(
        "AUTHORIZED_NEXT_ACTION="
        + manifest["next_authorized_action"]
    )
    print("SOURCE_DB_HASH=PASS")
    print("PROTECTED_RECORD_HASHES=PASS")
    print("CONTROL_FILE_HASHES=PASS")
    print("STAGING=EMPTY")
    print("WORKTREE_SCOPE=AUTHORIZED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
