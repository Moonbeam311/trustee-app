"""Registry-driven STEP 25AE Compliance current successor suite runner."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from audit_compliance_lineage_validation_25ae import (
    COVERAGE_PATH,
    INTEGRITY_PATH,
    REGISTRY_PATH,
    load_json,
    validate_coverage,
    validate_integrity,
    validate_registry,
)


ROOT = Path(__file__).resolve().parent.parent
ACTIVE_DB = ROOT / "trustee_app.db"
EXPORT_POLICY = ROOT / "data" / "export_policy.json"
ARTIFACT_DIR = ROOT / "test_artifacts" / "step25ae"


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


def write_report(report: dict[str, object]) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    paths = [Path(tempfile.gettempdir()) / f"step25ae_master_report_{stamp}.json"]
    try:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        paths.insert(0, ARTIFACT_DIR / f"step25ae_master_report_{stamp}.json")
        paths.insert(0, ARTIFACT_DIR / "step25ae_master_report.json")
    except PermissionError:
        pass
    payload = json.dumps(report, indent=2, sort_keys=True, default=str)
    for path in paths:
        try:
            path.write_text(payload, encoding="utf-8")
            return path
        except PermissionError:
            continue
    raise PermissionError("step25ae_master_report_write_failed")


def run_audit(audit: dict[str, object]) -> dict[str, object]:
    path = str(audit["path"])
    started = datetime.now(UTC).isoformat(timespec="seconds")
    start_time = time.monotonic()
    proc = subprocess.run(
        [sys.executable, path],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=420,
    )
    ended = datetime.now(UTC).isoformat(timespec="seconds")
    output = proc.stdout + "\n" + proc.stderr
    totals = {}
    for line in output.splitlines():
        if line.startswith("TESTS_PASSED="):
            totals["tests_passed"] = line.split("=", 1)[1].strip()
        elif line.startswith("TESTS_FAILED="):
            totals["tests_failed"] = line.split("=", 1)[1].strip()
        elif "REPORT=" in line:
            totals["report_path"] = line.split("=", 1)[1].strip()
    return {
        "audit_id": audit["audit_id"],
        "path": path,
        "started_at": started,
        "ended_at": ended,
        "duration_seconds": round(time.monotonic() - start_time, 3),
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
        "totals": totals,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def main() -> int:
    registry = load_json(REGISTRY_PATH)
    integrity = load_json(INTEGRITY_PATH)
    coverage = load_json(COVERAGE_PATH)
    validation_errors = []
    validation_errors.extend(validate_registry(registry))
    validation_errors.extend(validate_integrity(integrity))
    validation_errors.extend(validate_coverage(coverage, registry))

    audit_by_id = {item["audit_id"]: item for item in registry["audits"]}
    suite_ids = registry.get("current_suite_order") or []
    suite = []
    for audit_id in suite_ids:
        audit = audit_by_id.get(audit_id)
        if not audit:
            validation_errors.append(f"suite_missing_audit:{audit_id}")
            continue
        if audit.get("classification") != "CURRENT_ACTIVE":
            validation_errors.append(f"non_current_suite_member:{audit_id}")
            continue
        if audit_id == "STEP-25AE-MASTER":
            validation_errors.append("master_runner_must_not_execute_itself")
            continue
        suite.append(audit)

    active_before = manifest(ACTIVE_DB)
    policy_before = manifest(EXPORT_POLICY)
    counts_before = active_counts()

    results = []
    if not validation_errors:
        for audit in suite:
            result = run_audit(audit)
            results.append(result)
            print(("PASS" if result["passed"] else "FAIL") + f" - {result['audit_id']} {result['path']}")
            if not result["passed"]:
                break

    active_after = manifest(ACTIVE_DB)
    policy_after = manifest(EXPORT_POLICY)
    counts_after = active_counts()
    active_unchanged = active_before == active_after and counts_before == counts_after
    policy_unchanged = policy_before == policy_after

    report = {
        "registry": str(REGISTRY_PATH),
        "integrity": str(INTEGRITY_PATH),
        "coverage": str(COVERAGE_PATH),
        "suite_ids": suite_ids,
        "validation_errors": validation_errors,
        "results": results,
        "active_before": active_before,
        "active_after": active_after,
        "counts_before": counts_before,
        "counts_after": counts_after,
        "policy_before": policy_before,
        "policy_after": policy_after,
        "active_unchanged": active_unchanged,
        "policy_unchanged": policy_unchanged,
    }
    report_path = write_report(report)
    all_passed = not validation_errors and all(item["passed"] for item in results) and len(results) == len(suite) and active_unchanged and policy_unchanged
    print(f"STEP25AE_MASTER_REPORT={report_path}")
    print(f"CURRENT_AUDITS_RUN={len(results)}")
    print(f"VALIDATION_ERRORS={len(validation_errors)}")
    print(f"ACTIVE_UNCHANGED={active_unchanged}")
    print(f"POLICY_UNCHANGED={policy_unchanged}")
    if all_passed:
        print("TRUSTEE APP STEP 25AE MASTER CURRENT SUCCESSOR SUITE")
        print("RESULT: PASS")
        return 0
    print("TRUSTEE APP STEP 25AE MASTER CURRENT SUCCESSOR SUITE")
    print("RESULT: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
