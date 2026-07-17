"""STEP 25AE Compliance audit lineage and current successor suite."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ACTIVE_DB = ROOT / "trustee_app.db"
EXPORT_POLICY = ROOT / "data" / "export_policy.json"
LINEAGE_DOC = ROOT / "docs" / "compliance_audit_lineage_25ae.md"
ARTIFACT_DIR = ROOT / "test_artifacts" / "step25ae"

CURRENT_SUCCESSORS = [
    "scripts/audit_compliance_authority_test_harness_25ab.py",
    "scripts/audit_compliance_live_authority_integration_25ac.py",
    "scripts/audit_compliance_attribution_persistence_and_audit_modernization_25ad.py",
]

HISTORICAL_H6_AUDITS = [
    "scripts/audit_authorization_baseline_reconciliation_17q_h6a_r6.py",
    "scripts/audit_compliance_review_temporary_activation_17q_h6c.py",
    "scripts/audit_compliance_review_service_workflow_17q_h6c.py",
    "scripts/audit_compliance_review_lifecycle_authorization_17q_h6c.py",
    "scripts/audit_compliance_review_audit_ledger_17q_h6c.py",
    "scripts/audit_compliance_review_h6d_common.py",
    "scripts/audit_compliance_review_write_routes_17q_h6d.py",
    "scripts/audit_compliance_review_route_authorization_17q_h6d.py",
    "scripts/audit_compliance_review_operator_ui_17q_h6d.py",
    "scripts/audit_compliance_review_form_controls_17q_h6d.py",
    "scripts/audit_compliance_review_concurrency_idempotency_17q_h6d.py",
    "scripts/audit_compliance_review_permission_governance_17q_h6e.py",
    "scripts/audit_compliance_review_production_migration_plan_17q_h6e.py",
    "scripts/audit_compliance_review_activation_readiness_17q_h6e.py",
    "scripts/audit_compliance_review_rollback_plan_17q_h6e.py",
    "scripts/audit_compliance_review_go_no_go_17q_h6e.py",
    "scripts/audit_compliance_review_pre_activation_certification_17q_h6f.py",
    "scripts/audit_compliance_review_h6b_h6f_publication_scope.py",
]

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
            "integrity": cur.execute("PRAGMA integrity_check").fetchone()[0],
            "fk": cur.execute("PRAGMA foreign_key_check").fetchall(),
        }
    finally:
        con.close()


def check(name: str, condition: bool, detail: object = "") -> None:
    print(("PASS" if condition else "FAIL") + " - " + name + ((" | " + str(detail)[:700]) if detail and not condition else ""))
    results.append({"name": name, "pass": bool(condition), "detail": detail})
    if not condition:
        failures.append(name)


def run(cmd: list[str], *, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)


def write_report(report: dict[str, object]) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    paths = [Path(tempfile.gettempdir()) / f"step25ae_report_{stamp}.json"]
    try:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        paths.insert(0, ARTIFACT_DIR / f"step25ae_report_{stamp}.json")
        paths.insert(0, ARTIFACT_DIR / "step25ae_report.json")
    except PermissionError:
        pass
    payload = json.dumps(report, indent=2, sort_keys=True, default=str)
    for path in paths:
        try:
            path.write_text(payload, encoding="utf-8")
            return path
        except PermissionError:
            continue
    raise PermissionError("step25ae_report_write_failed")


def classify_lineage() -> dict[str, object]:
    doc_text = LINEAGE_DOC.read_text(encoding="utf-8") if LINEAGE_DOC.exists() else ""
    classifications = {}
    for audit in HISTORICAL_H6_AUDITS:
        path = ROOT / audit
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        markers = {
            "exists": path.exists(),
            "fixed_sha": "EXPECTED_SHA" in text,
            "legacy_compliance_admin": "compliance_admin" in text,
            "listed_in_lineage": audit in doc_text,
        }
        classifications[audit] = markers
        check(f"historical audit classified {audit}", all(markers.values()) or (markers["exists"] and markers["listed_in_lineage"]), markers)
    for audit in CURRENT_SUCCESSORS:
        check(f"current successor exists {audit}", (ROOT / audit).exists(), audit)
        check(f"current successor listed {audit}", audit in doc_text, audit)
    return classifications


def run_successors() -> dict[str, object]:
    outputs = {}
    for audit in CURRENT_SUCCESSORS:
        proc = run([sys.executable, audit])
        outputs[audit] = {
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
        }
        check(f"current successor passes {audit}", proc.returncode == 0, outputs[audit])
    return outputs


def main() -> int:
    branch = run(["git", "branch", "--show-current"])
    check("branch is post-v2-planning", branch.stdout.strip() == "post-v2-planning", branch.stdout)
    check("lineage document exists", LINEAGE_DOC.exists(), LINEAGE_DOC)
    active_before = manifest(ACTIVE_DB)
    policy_before = manifest(EXPORT_POLICY)
    counts_before = active_counts()

    report: dict[str, object] = {
        "active_before": active_before,
        "policy_before": policy_before,
        "counts_before": counts_before,
        "current_successors": CURRENT_SUCCESSORS,
        "historical_h6_audits": HISTORICAL_H6_AUDITS,
    }
    report["lineage_classification"] = classify_lineage()
    report["successor_outputs"] = run_successors()

    active_after = manifest(ACTIVE_DB)
    policy_after = manifest(EXPORT_POLICY)
    counts_after = active_counts()
    check("active DB file unchanged", active_before == active_after, {"before": active_before, "after": active_after})
    check("active DB logical counts unchanged", counts_before == counts_after, {"before": counts_before, "after": counts_after})
    check("export policy unchanged", policy_before == policy_after, {"before": policy_before, "after": policy_after})

    report.update({
        "active_after": active_after,
        "policy_after": policy_after,
        "counts_after": counts_after,
        "tests_passed": sum(1 for item in results if item["pass"]),
        "tests_failed": sum(1 for item in results if not item["pass"]),
        "failures": failures,
    })
    report_path = write_report(report)
    print(f"STEP25AE_REPORT={report_path}")
    print(f"TESTS_PASSED={report['tests_passed']}")
    print(f"TESTS_FAILED={report['tests_failed']}")
    print("TRUSTEE APP STEP 25AE COMPLIANCE CURRENT SUCCESSOR SUITE")
    if failures:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
