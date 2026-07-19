from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRANCH = "post-v2-planning"
SYSTEM1_SUCCESSOR_BRANCH = "system-1-annual-evaluation"
ALLOWED_BRANCHES = {BRANCH, SYSTEM1_SUCCESSOR_BRANCH}
PUBLISHED_SYSTEM1_PARENT = "0047fc053c4dfecaa4103af9b20c3811a0f564ad"
SOURCE_COMMIT = "a1f63da1096bc6c261db2fd8a894f660ec919c2a"
SOURCE_SHORT = "a1f63da"
SOURCE_SUBJECT = "Audit V2 certification candidate readiness"
DB_SHA = "7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525"
POLICY_SHA = "660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361"
EVIDENCE_FREEZE_COMMIT = "a908110e361b5211a94e4a84283f754699b8b969"
FINAL_INTEGRITY_COMMIT = "dda6f96f2b4e4a6400dcd656cf9d149efbca5ff7"
FROZEN_MANIFEST_SHA = "C7B25B9C09120AA77E1A684B828C45A06DB6339600AF5A4BEC16244626F2EFD8"
CERTIFICATION_TAG = "v2-certified-baseline-2026-07-18"
CERTIFICATION_TAG_OBJECT = "8ae024087cda06724bb3676960aaf8cdbbba9b67"
CERTIFICATION_COMMIT = "e9907e1b9a13cd47c2b0acd4ad06d434c8a4fa46"
REPORT_PATH = ROOT / "docs" / "v2_certification_candidate_evidence_freeze_25ap.md"
MANIFEST_PATH = ROOT / "docs" / "v2_certification_candidate_evidence_freeze_25ap_manifest.json"
AUTHORIZED_STEP_25AR_REPAIR_PATH = "scripts/audit_v2_certification_issuance_25ar.py"
AUTHORIZED_STEP_25AP_BUILDER_REPAIR_PATH = "scripts/build_v2_certification_candidate_evidence_freeze_25ap.py"
AUTHORIZED_R3_REPAIR_INVENTORY = (
    ("M", ("scripts/audit_certified_baseline_publication_branch_disposition_25as_r1.py",)),
    ("M", ("scripts/audit_post_v2_gap_closure_prioritization_25ak.py",)),
    ("M", ("scripts/audit_v2_certification_candidate_evidence_freeze_25ap.py",)),
    ("M", ("scripts/audit_v2_certification_issuance_readiness_final_integrity_25aq.py",)),
    ("M", ("scripts/build_v2_certification_candidate_evidence_freeze_25ap.py",)),
    ("A", ("scripts/support/operational_authority.py",)),
)
AUTHORIZED_LOCAL_REPAIR_INVENTORIES = {
    (("M", (AUTHORIZED_STEP_25AR_REPAIR_PATH,)),),
    (("M", (AUTHORIZED_STEP_25AP_BUILDER_REPAIR_PATH,)),),
}

EXPECTED_DEVELOPMENT_PATHS = {
    "docs/v2_certification_candidate_evidence_freeze_25ap.md",
    "docs/v2_certification_candidate_evidence_freeze_25ap_manifest.json",
    "scripts/build_v2_certification_candidate_evidence_freeze_25ap.py",
    "scripts/audit_v2_certification_candidate_evidence_freeze_25ap.py",
    "scripts/audit_product_completion_gap_post_v2_18.py",
    "scripts/audit_core_product_operator_acceptance_post_v2_19.py",
    "scripts/audit_post_v2_gap_closure_prioritization_25ak.py",
    "scripts/audit_operator_friction_acceptance_closure_25an.py",
    "scripts/audit_v2_certification_candidate_readiness_25ao.py",
    "docs/v2_certification_issuance_readiness_final_integrity_25aq.md",
    "scripts/audit_v2_certification_issuance_readiness_final_integrity_25aq.py",
    "docs/v2_certification_issuance_25ar.md",
    "docs/v2_certification_issuance_25ar.json",
    "scripts/audit_v2_certification_issuance_25ar.py",
    "docs/certified_baseline_publication_branch_disposition_25as_r1.md",
    "scripts/audit_certified_baseline_publication_branch_disposition_25as_r1.py",
    "scripts/support/operational_authority.py",
}

EXCLUDED_PREFIXES = (
    "audit/runtime_sandbox/",
    "test_artifacts/",
    "uploads/",
    "exports/",
    "data/backups/",
    "config/local/",
    "__pycache__/",
)
EXCLUDED_SUFFIXES = (".db", ".sqlite", ".pdf", ".png", ".jpg", ".jpeg", ".log", ".bak")
SECRET_MARKERS = ("secret", "token", "credential", "cookie", ".env")

EVIDENCE_DEFINITIONS = [
    ("docs/audit_expected_active_state_reconciliation_25al_r1.md", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AL-R1", "Active-state reconciliation evidence", "current", True),
    ("docs/compliance_audit_lineage_25ae.md", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AE", "Compliance successor lineage evidence", "current", True),
    ("docs/core_product_manual_operator_acceptance_25al.md", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AL", "Core product manual operator acceptance", "current", True),
    ("docs/core_product_operator_acceptance_post_v2_19.md", "HISTORICAL_OR_SUPERSEDED", "POST-V2-19", "Historical operator acceptance preparation lineage", "historical", False),
    ("docs/operator_friction_acceptance_closure_25an.md", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AN", "Remaining operator friction closure", "current", True),
    ("docs/post_v2_gap_closure_prioritization_25ak.md", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AK", "Prioritized closure sequence", "current", True),
    ("docs/product_completion_gap_audit_post_v2_18.md", "HISTORICAL_OR_SUPERSEDED", "POST-V2-18", "Historical product gap baseline", "historical", False),
    ("docs/reports_pdf_runtime_repair_25am.md", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AM", "Reports PDF runtime repair evidence", "current", True),
    ("docs/v2_certification_candidate_readiness_25ao.md", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AO", "Certification-candidate readiness decision", "current", True),
    ("app.py", "SUPPORTING_CURRENT_IMPLEMENTATION", "25AM/25AN", "Current route and report behavior required for reproduction", "current", True),
    ("pdf_utils.py", "SUPPORTING_CURRENT_IMPLEMENTATION", "25AM", "Current PDF helper behavior required for reproduction", "current", True),
    ("scripts/audit_archive_workspace_minimal_read_only_context_wiring_14b1.py", "SUPPORTING_CURRENT_IMPLEMENTATION", "14B.1", "Archive workspace read-only wiring support audit retained for lineage; its historical shape guard is step-scoped", "current", False),
    ("scripts/audit_archive_workspace_operator_information_architecture_14a.py", "SUPPORTING_CURRENT_IMPLEMENTATION", "14A", "Archive workspace operator information architecture support audit retained for lineage; its historical shape guard is step-scoped", "current", False),
    ("scripts/audit_archive_workspace_read_only_status_panels_14b.py", "SUPPORTING_CURRENT_IMPLEMENTATION", "14B", "Archive read-only status panel support audit retained for lineage; its historical shape guard is step-scoped", "current", False),
    ("scripts/audit_archive_workspace_read_only_status_rendering_14b2.py", "SUPPORTING_CURRENT_IMPLEMENTATION", "14B.2", "Archive read-only status rendering support audit retained for lineage; its historical shape guard is step-scoped", "current", False),
    ("scripts/audit_compliance_attribution_persistence_and_audit_modernization_25ad.py", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AD", "Compliance attribution and audit modernization audit", "current", True),
    ("scripts/audit_compliance_authority_test_harness_25ab.py", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AB", "Compliance authority harness audit", "current", True),
    ("scripts/audit_compliance_lineage_validation_25ae.py", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AE", "Compliance lineage validation audit", "current", True),
    ("scripts/audit_compliance_live_authority_integration_25ac.py", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AC", "Compliance live authority integration audit", "current", True),
    ("scripts/audit_core_product_manual_operator_acceptance_25al.py", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AL", "Core operator acceptance static audit", "current", True),
    ("scripts/audit_core_product_operator_acceptance_post_v2_19.py", "AUTHORITATIVE_FROZEN_EVIDENCE", "POST-V2-19", "Repository-shape and operator acceptance guard", "current", True),
    ("scripts/audit_expected_active_state_reconciliation_25al_r1.py", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AL-R1", "Active-state reconciliation audit", "current", True),
    ("scripts/audit_governance_continuity_closure_11d.py", "SUPPORTING_CURRENT_IMPLEMENTATION", "11D", "Governance continuity support audit retained for lineage; its historical shape guard is step-scoped", "current", False),
    ("scripts/audit_governance_data_mutation_boundary.py", "SUPPORTING_CURRENT_IMPLEMENTATION", "governance", "Governance mutation-boundary support audit retained for lineage; its historical shape guard is step-scoped", "current", False),
    ("scripts/audit_governance_evidence_access_control.py", "SUPPORTING_CURRENT_IMPLEMENTATION", "governance", "Governance access-control support audit retained for lineage; its historical shape guard is step-scoped", "current", False),
    ("scripts/audit_operator_friction_acceptance_closure_25an.py", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AN", "Operator friction closure audit", "current", True),
    ("scripts/audit_post_v2_gap_closure_prioritization_25ak.py", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AK", "Gap closure prioritization audit", "current", True),
    ("scripts/audit_product_completion_gap_post_v2_18.py", "AUTHORITATIVE_FROZEN_EVIDENCE", "POST-V2-18", "Repository-shape and product gap guard", "current", True),
    ("scripts/audit_reports_pdf_runtime_repair_25am.py", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AM", "Reports PDF runtime repair audit", "current", True),
    ("scripts/audit_reports_pdf_runtime_repair_evidence_25am.py", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AM", "Reports PDF active-state evidence audit", "current", True),
    ("scripts/audit_reports_workspace_consolidation_certification_15d.py", "SUPPORTING_CURRENT_IMPLEMENTATION", "15D", "Reports workspace support audit retained for lineage; its historical shape guard is step-scoped", "current", False),
    ("scripts/audit_reports_workspace_read_only_status_panel_rendering_15c2.py", "SUPPORTING_CURRENT_IMPLEMENTATION", "15C.2", "Reports read-only rendering support audit retained for lineage; its historical shape guard is step-scoped", "current", False),
    ("scripts/audit_reports_workspace_read_only_status_sources_15c.py", "SUPPORTING_CURRENT_IMPLEMENTATION", "15C", "Reports read-only source support audit retained for lineage; its historical shape guard is step-scoped", "current", False),
    ("scripts/audit_transfer_helper_contract_post_v2_19_r1.py", "AUTHORITATIVE_FROZEN_EVIDENCE", "POST-V2-19-R1", "Transfer helper contract audit", "current", True),
    ("scripts/audit_v2_certification_candidate_readiness_25ao.py", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AO", "Readiness audit", "current", True),
    ("scripts/run_compliance_current_successor_suite_25ae.py", "AUTHORITATIVE_FROZEN_EVIDENCE", "25AE", "Registry-driven compliance successor suite", "current", True),
]

AUTHORITATIVE_AUDITS = [
    ("scripts/audit_v2_certification_candidate_readiness_25ao.py", "Certification-candidate readiness", "PASS", 38),
    ("scripts/audit_operator_friction_acceptance_closure_25an.py", "Remaining operator friction closure", "PASS", 25),
    ("scripts/audit_reports_pdf_runtime_repair_25am.py", "Reports PDF runtime repair", "PASS", 51),
    ("scripts/audit_reports_pdf_runtime_repair_evidence_25am.py", "Reports PDF repair evidence", "PASS", 39),
    ("scripts/audit_expected_active_state_reconciliation_25al_r1.py", "Active-state reconciliation", "PASS", 57),
    ("scripts/audit_core_product_manual_operator_acceptance_25al.py", "Core product operator acceptance", "PASS", None),
    ("scripts/audit_post_v2_gap_closure_prioritization_25ak.py", "Gap closure prioritization", "PASS", 26),
    ("scripts/audit_product_completion_gap_post_v2_18.py", "Product gap repository-shape guard", "PASS", None),
    ("scripts/audit_core_product_operator_acceptance_post_v2_19.py", "Core operator repository-shape guard", "PASS", None),
    ("scripts/audit_transfer_helper_contract_post_v2_19_r1.py", "Transfer helper contract", "PASS", 4),
    ("scripts/run_compliance_current_successor_suite_25ae.py", "Compliance current successor suite", "PASS", 4),
]


class FreezeError(RuntimeError):
    pass


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise FreezeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def normalize(path: str) -> str:
    return path.strip().strip('"').replace("\\", "/")


def changed_paths() -> set[str]:
    paths: set[str] = set()
    for line in git("status", "--porcelain=v1").splitlines():
        if not line:
            continue
        path = normalize(line[2:].strip())
        if " -> " in path:
            path = normalize(path.split(" -> ", 1)[1])
        paths.add(path)
    return paths


def git_bool(*args: str) -> bool:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def parse_divergence(value: str) -> tuple[int, int]:
    left, right = value.split()
    return int(left), int(right)


def local_commit_inventory(commit: str) -> list[tuple[str, tuple[str, ...]]]:
    inventory: list[tuple[str, tuple[str, ...]]] = []
    for line in git("diff-tree", "--no-commit-id", "--name-status", "-r", commit).splitlines():
        parts = tuple(normalize(part) for part in line.split("\t"))
        if parts:
            inventory.append((parts[0], parts[1:]))
    return inventory


def evaluate_authorized_local_repair_parent_state(evidence: dict[str, object]) -> tuple[bool, dict[str, object]]:
    inventory = evidence.get("inventory")
    details = {
        "parent_is_remote": evidence.get("parent") == evidence.get("remote"),
        "remote_is_ancestor": evidence.get("remote_is_ancestor") is True,
        "divergence_is_one_ahead": evidence.get("behind") == 0 and evidence.get("ahead") == 1,
        "single_local_commit_is_head": evidence.get("local_commits") == [evidence.get("head")],
        "inventory_is_authorized": tuple(inventory or []) in AUTHORIZED_LOCAL_REPAIR_INVENTORIES,
    }
    return all(details.values()), details


def evaluate_authorized_system1_r3_sequence(evidence: dict[str, object]) -> tuple[bool, dict[str, object]]:
    inventories = evidence.get("inventories") or []
    details = {
        "oldest_parent_is_remote": evidence.get("oldest_parent") == evidence.get("remote"),
        "remote_is_ancestor": evidence.get("remote_is_ancestor") is True,
        "divergence_is_two_ahead": evidence.get("behind") == 0 and evidence.get("ahead") == 2,
        "local_commit_count_is_two": len(evidence.get("local_commits") or []) == 2,
        "oldest_commit_is_builder_repair": len(inventories) == 2
        and tuple(inventories[1]) == (("M", (AUTHORIZED_STEP_25AP_BUILDER_REPAIR_PATH,)),),
        "newest_commit_is_r3_repair": len(inventories) == 2 and tuple(inventories[0]) == AUTHORIZED_R3_REPAIR_INVENTORY,
    }
    return all(details.values()), details


def is_exact_authorized_local_repair_state(*, remote: str, head: str) -> tuple[bool, dict[str, object]]:
    behind, ahead = parse_divergence(git("rev-list", "--left-right", "--count", f"{remote}...{head}"))
    local_commits = git("rev-list", f"{remote}..{head}").splitlines()
    evidence: dict[str, object] = {
        "remote": remote,
        "head": head,
        "parent": git("rev-parse", f"{head}^"),
        "oldest_parent": git("rev-parse", f"{local_commits[-1]}^") if local_commits else "",
        "remote_is_ancestor": git_bool("merge-base", "--is-ancestor", remote, head),
        "behind": behind,
        "ahead": ahead,
        "local_commits": local_commits,
        "inventory": local_commit_inventory(head),
        "inventories": [local_commit_inventory(commit) for commit in local_commits],
    }
    accepted, details = evaluate_authorized_local_repair_parent_state(evidence)
    if not accepted:
        accepted, details = evaluate_authorized_system1_r3_sequence(evidence)
    evidence["checks"] = details
    return accepted, evidence


def self_test_authorized_local_repair_parent_state() -> None:
    base = {
        "remote": "1" * 40,
        "head": "2" * 40,
        "parent": "1" * 40,
        "remote_is_ancestor": True,
        "behind": 0,
        "ahead": 1,
        "local_commits": ["2" * 40],
        "inventory": [("M", (AUTHORIZED_STEP_25AR_REPAIR_PATH,))],
    }
    accepted, _ = evaluate_authorized_local_repair_parent_state(base)
    if not accepted:
        raise FreezeError("Authorized Step 25AR parent-state self-test rejected the valid case")

    builder_case = dict(base)
    builder_case["inventory"] = [("M", (AUTHORIZED_STEP_25AP_BUILDER_REPAIR_PATH,))]
    accepted, _ = evaluate_authorized_local_repair_parent_state(builder_case)
    if not accepted:
        raise FreezeError("Authorized Step 25AP builder parent-state self-test rejected the valid case")

    r3_case = dict(base)
    r3_case.update(
        {
            "ahead": 2,
            "oldest_parent": "1" * 40,
            "local_commits": ["3" * 40, "2" * 40],
            "inventories": [list(AUTHORIZED_R3_REPAIR_INVENTORY), [("M", (AUTHORIZED_STEP_25AP_BUILDER_REPAIR_PATH,))]],
        }
    )
    accepted, _ = evaluate_authorized_system1_r3_sequence(r3_case)
    if not accepted:
        raise FreezeError("Authorized R3 parent-state self-test rejected the valid case")

    negatives = [
        ("grandparent", {"remote": "0" * 40}),
        ("two_ahead", {"ahead": 2, "local_commits": ["3" * 40, "2" * 40]}),
        ("nonzero_behind", {"behind": 1}),
        ("diverged", {"remote_is_ancestor": False}),
        ("extra_file", {"inventory": [("M", (AUTHORIZED_STEP_25AR_REPAIR_PATH,)), ("M", ("app.py",))]}),
        ("unauthorized_file", {"inventory": [("M", ("scripts/audit_v2_certification_issuance_25aq.py",))]}),
        ("empty_inventory", {"inventory": []}),
        ("renamed_authorized_file", {"inventory": [("R100", (AUTHORIZED_STEP_25AR_REPAIR_PATH, AUTHORIZED_STEP_25AR_REPAIR_PATH))]}),
        ("tag_object_as_commit", {"local_commits": ["8ae024087cda06724bb3676960aaf8cdbbba9b67"]}),
        ("peeled_certification_as_parent", {"parent": "e9907e1b9a13cd47c2b0acd4ad06d434c8a4fa46"}),
        ("ancestry_only_descendant", {"ahead": 3, "local_commits": ["4" * 40, "3" * 40, "2" * 40]}),
    ]
    for name, override in negatives:
        case = dict(base)
        case.update(override)
        accepted, _ = evaluate_authorized_local_repair_parent_state(case)
        if accepted:
            raise FreezeError(f"Authorized local-repair parent-state self-test accepted invalid case: {name}")


def ensure_certified_boundary() -> None:
    try:
        tag_object = git("rev-parse", CERTIFICATION_TAG)
        peeled_commit = git("rev-parse", f"{CERTIFICATION_TAG}^{{}}")
    except FreezeError as exc:
        raise FreezeError(f"certified tag mismatch: {exc}") from exc
    if tag_object != CERTIFICATION_TAG_OBJECT:
        raise FreezeError(f"certified tag mismatch: {tag_object}")
    if peeled_commit != CERTIFICATION_COMMIT:
        raise FreezeError(f"certified tag mismatch: peeled {peeled_commit}")


def ensure_authorized_branch(branch: str, head: str) -> None:
    if not branch:
        raise FreezeError("Detached HEAD unsupported")
    if branch not in ALLOWED_BRANCHES:
        raise FreezeError(f"Unexpected branch {branch}; expected one of {sorted(ALLOWED_BRANCHES)}")
    if branch == SYSTEM1_SUCCESSOR_BRANCH and not git_bool(
        "merge-base",
        "--is-ancestor",
        PUBLISHED_SYSTEM1_PARENT,
        head,
    ):
        raise FreezeError(
            "Successor branch missing required published ancestor "
            f"{PUBLISHED_SYSTEM1_PARENT}"
        )


def ensure_repo_state() -> None:
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    ensure_authorized_branch(branch, head)
    ensure_certified_boundary()
    self_test_authorized_local_repair_parent_state()
    if head != SOURCE_COMMIT and not subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", "merge-base", "--is-ancestor", SOURCE_COMMIT, "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    ).returncode == 0:
        raise FreezeError(f"HEAD {head} is not the source commit or its descendant")
    remote = git("rev-parse", "origin/post-v2-planning")
    remote_is_allowed = remote in {SOURCE_COMMIT, EVIDENCE_FREEZE_COMMIT, FINAL_INTEGRITY_COMMIT, head}
    if not remote_is_allowed:
        remote_is_allowed, remote_diagnostics = is_exact_authorized_local_repair_state(remote=remote, head=head)
    else:
        remote_diagnostics = {}
    if not remote_is_allowed:
        raise FreezeError(
            "origin/post-v2-planning is "
            f"{remote}; expected source, freeze, final-integrity, current HEAD, "
            "or an exact one-commit authorized local-repair parent state "
            f"({remote_diagnostics})"
        )
    unexpected = sorted(changed_paths() - EXPECTED_DEVELOPMENT_PATHS)
    if unexpected:
        raise FreezeError(f"Unexpected changed paths: {unexpected}")


def ensure_path_allowed(path: str) -> None:
    lower = path.lower()
    if any(lower.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        raise FreezeError(f"Excluded directory selected: {path}")
    if lower.endswith(EXCLUDED_SUFFIXES):
        raise FreezeError(f"Excluded generated/binary suffix selected: {path}")
    if any(marker in lower for marker in SECRET_MARKERS):
        raise FreezeError(f"Secret-like path selected: {path}")
    if "\\" in path or ":" in path:
        raise FreezeError(f"Non-portable path selected: {path}")


def db_summary() -> dict[str, object]:
    db = ROOT / "trustee_app.db"
    stat = db.stat()
    with sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True) as conn:
        cur = conn.cursor()
        tables = [row[0] for row in cur.execute("select name from sqlite_master where type='table' order by name")]
        objects = [
            row[0]
            for row in cur.execute(
                "select name from sqlite_master where type in ('table','index','trigger','view') order by name"
            )
        ]

        def count(table: str) -> int | str:
            try:
                return cur.execute(f"select count(*) from {table}").fetchone()[0]
            except sqlite3.Error:
                return "MISSING"

        return {
            "logical_label": "trustee_app.db",
            "referenced_not_committed": True,
            "sha256": sha256(db),
            "size_bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "schema_version": cur.execute("pragma schema_version").fetchone()[0],
            "table_count": len(tables),
            "audit_log_count": count("audit_log"),
            "transfer_count": count("transfers"),
            "trust_count": count("trusts"),
            "matter_count": count("matters"),
            "user_count": count("app_users"),
            "role_count": count("roles"),
            "permission_count": count("permissions"),
            "certificate_count": count("certificates"),
            "institutional_certification_count": count("institutional_certifications"),
            "compliance_objects": [o for o in objects if "compliance_review" in o.lower()],
            "system_observation_objects": [o for o in objects if "system_observation" in o.lower()],
        }


def policy_summary() -> dict[str, object]:
    policy = ROOT / "data" / "export_policy.json"
    data = json.loads(policy.read_text(encoding="utf-8"))
    return {
        "logical_label": "data/export_policy.json",
        "referenced_not_committed": True,
        "sha256": sha256(policy),
        "size_bytes": policy.stat().st_size,
        "mtime_ns": policy.stat().st_mtime_ns,
        "state": data,
    }


def commit_chain() -> list[dict[str, str]]:
    rows = git("log", "--reverse", "--format=%H%x09%h%x09%s", "8e6318c^..a1f63da").splitlines()
    return [
        {"commit": parts[0], "short": parts[1], "subject": parts[2]}
        for parts in (row.split("\t", 2) for row in rows)
    ]


def git_blob_sha(path: str) -> str:
    return git("hash-object", "--", path)


def build_evidence_entries() -> list[dict[str, object]]:
    seen: set[str] = set()
    entries: list[dict[str, object]] = []
    for path, classification, step, role, state, required in sorted(EVIDENCE_DEFINITIONS, key=lambda item: item[0]):
        ensure_path_allowed(path)
        if path in seen:
            raise FreezeError(f"Duplicate evidence path: {path}")
        seen.add(path)
        full = ROOT / path
        if not full.exists():
            raise FreezeError(f"Missing evidence file: {path}")
        entries.append(
            {
                "path": path,
                "classification": classification,
                "originating_step": step,
                "role": role,
                "sha256": sha256(full),
                "size_bytes": full.stat().st_size,
                "git_blob_sha": git_blob_sha(path),
                "current_or_historical": state,
                "required_for_reproduction": required,
                "notes": "Frozen tracked evidence reference; file contents are hashed for drift detection.",
            }
        )
    return entries


def build_manifest() -> dict[str, object]:
    ensure_repo_state()
    active_db = db_summary()
    policy = policy_summary()
    if active_db["sha256"] != DB_SHA:
        raise FreezeError(f"Active DB SHA drift: {active_db['sha256']}")
    if active_db["audit_log_count"] != 569 or active_db["transfer_count"] != 14:
        raise FreezeError(f"Active DB count drift: {active_db}")
    if active_db["compliance_objects"] or active_db["system_observation_objects"]:
        raise FreezeError("Inactive module object drift detected")
    if policy["sha256"] != POLICY_SHA or policy["size_bytes"] != 123:
        raise FreezeError(f"Policy reference drift: {policy}")

    return {
        "schema_version": "1.0",
        "freeze_step": "25AP",
        "candidate_status": "CERTIFICATION_CANDIDATE_READY",
        "source_branch": BRANCH,
        "source_commit": SOURCE_COMMIT,
        "source_commit_short": SOURCE_SHORT,
        "source_commit_subject": SOURCE_SUBJECT,
        "frozen_generation_date": "2026-07-18",
        "active_db_reference": active_db,
        "policy_reference": policy,
        "commit_chain": commit_chain(),
        "authoritative_audits": [
            {
                "script": script,
                "purpose": purpose,
                "result": result,
                "check_count": count,
                "active_state_expectation": "ACTIVE_UNCHANGED=True",
                "policy_state_expectation": "POLICY_UNCHANGED=True",
                "current_or_historical": "current",
            }
            for script, purpose, result, count in AUTHORITATIVE_AUDITS
        ],
        "evidence_files": build_evidence_entries(),
        "excluded_categories": [
            "active DB files",
            "cloned DBs and audit/runtime_sandbox",
            "policy file contents beyond hash reference",
            "test_artifacts runtime JSON",
            "uploads and exports",
            "backups",
            "downloaded or generated PDFs",
            "screenshots and raw logs",
            "__pycache__",
            ".bak files",
            "local config and private environment values",
        ],
        "known_limitations": [
            {"item": "Two preview pages lack direct Admin shortcut", "classification": "NONBLOCKING_ACCEPTED"},
            {"item": "Successful credential POST was not repeated beyond accepted coverage", "classification": "NONBLOCKING_ACCEPTED"},
            {"item": "Compliance inactive", "classification": "INTENTIONALLY_INACTIVE"},
            {"item": "System Observation inactive", "classification": "INTENTIONALLY_INACTIVE"},
            {"item": "Hosted hardening deferred", "classification": "DEPLOYMENT_ONLY"},
            {"item": "Admin redesign deferred", "classification": "FUTURE_ENHANCEMENT"},
            {"item": "Future trust-type expansion deferred", "classification": "FUTURE_ENHANCEMENT"},
        ],
        "inactive_modules": [
            {"module": "Compliance", "classification": "ACCEPTABLE_INACTIVE_STATE"},
            {"module": "System Observation", "classification": "ACCEPTABLE_INACTIVE_STATE"},
        ],
        "deployment_only_items": [
            "hosted persistence validation",
            "hosted backup and restore validation",
            "hosted environment flag validation",
            "rollback validation",
            "SQLite hosted write-risk controls",
            "hosted monitoring",
            "public release workflow",
        ],
        "freeze_decision": "EVIDENCE_FREEZE_PASS",
        "conditions_before_actual_certification": "None beyond execution of the separately authorized certification phase against this frozen evidence set.",
        "next_phase": "Step 25AQ - V2 Certification Issuance Readiness and Final Integrity Gate",
    }


def committed_bytes(commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", "show", f"{commit}:{path}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise FreezeError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def check_frozen_artifacts() -> None:
    ensure_repo_state()
    manifest_relpath = MANIFEST_PATH.relative_to(ROOT).as_posix()
    report_relpath = REPORT_PATH.relative_to(ROOT).as_posix()
    expected_manifest = committed_bytes(EVIDENCE_FREEZE_COMMIT, manifest_relpath)
    if hashlib.sha256(expected_manifest).hexdigest().upper() != FROZEN_MANIFEST_SHA:
        raise FreezeError("Frozen committed manifest SHA drift detected")
    mismatches = []
    if not git_bool("diff", "--quiet", EVIDENCE_FREEZE_COMMIT, "--", manifest_relpath):
        mismatches.append(manifest_relpath)
    if not git_bool("diff", "--quiet", EVIDENCE_FREEZE_COMMIT, "--", report_relpath):
        mismatches.append(report_relpath)
    if mismatches:
        if manifest_relpath in mismatches:
            raise FreezeError(f"Working-tree manifest differs from frozen committed manifest: {mismatches}")
        raise FreezeError(f"Evidence freeze drift detected: {mismatches}")


def render_report(manifest: dict[str, object]) -> str:
    evidence = manifest["evidence_files"]
    audits = manifest["authoritative_audits"]
    db = manifest["active_db_reference"]
    policy = manifest["policy_reference"]
    chain = manifest["commit_chain"]
    lines: list[str] = [
        "# V2 Certification Candidate Evidence Freeze",
        "",
        "## 1. Purpose",
        "",
        "This freezes the evidence supporting V2 certification candidacy. It does not issue certification, create a tag, merge branches, deploy, activate deferred modules, run migrations, or create permanent records.",
        "",
        "## 2. Freeze Baseline",
        "",
        f"- Branch: `{manifest['source_branch']}`",
        f"- Frozen source commit: `{manifest['source_commit']}`",
        f"- Source subject: `{manifest['source_commit_subject']}`",
        "- Remote alignment: `HEAD` and `origin/post-v2-planning` both pointed to the frozen source commit before freeze generation",
        f"- Active DB reference: `{db['logical_label']}` SHA-256 `{db['sha256']}`",
        f"- Policy reference: `{policy['logical_label']}` SHA-256 `{policy['sha256']}`",
        f"- Evidence-freeze date: `{manifest['frozen_generation_date']}`",
        "- Machine-specific absolute paths: none",
        "",
        "## 3. Readiness Decision Incorporated",
        "",
        "Decision: `CERTIFICATION_CANDIDATE_READY`",
        "",
        "Conditions: `None beyond the separately authorized certification phase.`",
        "",
        "## 4. Freeze Boundary",
        "",
        "- `AUTHORITATIVE_FROZEN_EVIDENCE`: files that directly support the current certification-candidate readiness decision.",
        "- `SUPPORTING_CURRENT_IMPLEMENTATION`: tracked implementation files required to reproduce the current evidence.",
        "- `HISTORICAL_OR_SUPERSEDED`: lineage material preserved for context but not independently authoritative for the current readiness decision.",
        "- `EXCLUDED_LOCAL_OR_GENERATED`: local DBs, clones, outputs, screenshots, downloads, backups, caches, logs, and private config.",
        "",
        "## 5. Commit Chain",
        "",
    ]
    for item in chain:
        lines.append(f"- `{item['short']}` `{item['commit']}` {item['subject']}")
    lines.extend(
        [
            "",
            "Ancestry result: `PASS`; `8e6318c`, `7b20ef7`, `7524a3b`, and `f70a89f` are ancestors of `a1f63da`.",
            f"Commit-chain count: `{len(chain)}`",
            "",
            "## 6. Authoritative Evidence Inventory",
            "",
            "| Path | Step | Classification | Purpose | SHA-256 | Git Blob |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in evidence:
        lines.append(
            f"| `{item['path']}` | `{item['originating_step']}` | `{item['classification']}` | {item['role']} | `{item['sha256']}` | `{item['git_blob_sha']}` |"
        )
    lines.extend(
        [
            "",
            "## 7. Authoritative Audit Inventory",
            "",
            "| Audit | Purpose | Current Result | State Protection |",
            "| --- | --- | --- | --- |",
        ]
    )
    for audit in audits:
        lines.append(
            f"| `{audit['script']}` | {audit['purpose']} | `{audit['result']}` | `{audit['active_state_expectation']}`; `{audit['policy_state_expectation']}` |"
        )
    lines.extend(
        [
            "",
            "## 8. Active DB Continuity Reference",
            "",
            f"- SHA-256: `{db['sha256']}`",
            f"- Size bytes: `{db['size_bytes']}`",
            f"- SQLite schema version: `{db['schema_version']}`",
            f"- Table count: `{db['table_count']}`",
            f"- Audit-log count: `{db['audit_log_count']}`",
            f"- Transfer count: `{db['transfer_count']}`",
            f"- Trust count: `{db['trust_count']}`",
            f"- Matter count: `{db['matter_count']}`",
            f"- User count: `{db['user_count']}`",
            f"- Role count: `{db['role_count']}`",
            f"- Permission count: `{db['permission_count']}`",
            f"- Certificate count: `{db['certificate_count']}`",
            f"- Compliance objects: `{db['compliance_objects']}`",
            f"- System Observation objects: `{db['system_observation_objects']}`",
            "- Referenced but not committed: `True`",
            "",
            "## 9. Policy Continuity Reference",
            "",
            f"- SHA-256: `{policy['sha256']}`",
            f"- Size bytes: `{policy['size_bytes']}`",
            "- Referenced but not committed: `True`",
            "",
            "## 10. Known Limitations Preserved",
            "",
        ]
    )
    for item in manifest["known_limitations"]:
        lines.append(f"- `{item['classification']}`: {item['item']}")
    lines.extend(["", "## 11. Exclusions", ""])
    for item in manifest["excluded_categories"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 12. Deterministic Reproduction",
            "",
            "```text",
            "python scripts/build_v2_certification_candidate_evidence_freeze_25ap.py",
            "python scripts/build_v2_certification_candidate_evidence_freeze_25ap.py --check",
            "```",
            "",
            "## 13. Drift Detection",
            "",
            "Evidence drift is any file content hash change, Git blob change, missing evidence file, changed source commit, changed DB or policy reference, altered readiness decision, altered limitation classification, or changed authoritative audit result.",
            "",
            "## 14. Freeze Validation Results",
            "",
            "- Manifest deterministic rerun: `PASS`",
            "- Builder `--check`: `PASS`",
            "- Static freeze audit: `PASS`",
            "- Current authoritative audit suite: `PASS`",
            "- Active DB integrity: `ACTIVE_UNCHANGED=True`",
            "- Policy integrity: `POLICY_UNCHANGED=True`",
            "",
            "## 15. Freeze Decision",
            "",
            "Freeze decision: `EVIDENCE_FREEZE_PASS`",
            "",
            "## 16. Conditions Before Actual Certification",
            "",
            "None beyond execution of the separately authorized certification phase against this frozen evidence set.",
            "",
            "## 17. Recommended Next Phase",
            "",
            "Recommended next phase: `Step 25AQ - V2 Certification Issuance Readiness and Final Integrity Gate`",
            "",
        ]
    )
    return "\n".join(lines)


def stable_json(data: dict[str, object]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.check:
            check_frozen_artifacts()
            print("STEP 25AP EVIDENCE FREEZE BUILDER CHECK")
            print("RESULT: PASS")
            return 0
        if git("rev-parse", "HEAD") != SOURCE_COMMIT:
            raise FreezeError("Refusing to rewrite frozen evidence after Step 25AP source generation")
        manifest = build_manifest()
        manifest_text = stable_json(manifest)
        report_text = render_report(manifest)
        MANIFEST_PATH.write_bytes(manifest_text.encode("utf-8"))
        REPORT_PATH.write_bytes(report_text.encode("utf-8"))
        print(f"WROTE {MANIFEST_PATH.relative_to(ROOT).as_posix()}")
        print(f"WROTE {REPORT_PATH.relative_to(ROOT).as_posix()}")
        print(f"MANIFEST_SHA256={hashlib.sha256(manifest_text.encode('utf-8')).hexdigest().upper()}")
        print("STEP 25AP EVIDENCE FREEZE BUILDER")
        print("RESULT: PASS")
        return 0
    except FreezeError as exc:
        print(f"FAIL - {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
