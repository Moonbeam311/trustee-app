"""STEP 25AE Compliance lineage registry validator."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "scripts" / "compliance_audit_lineage_registry.json"
INTEGRITY_PATH = ROOT / "scripts" / "compliance_historical_audit_integrity.json"
COVERAGE_PATH = ROOT / "scripts" / "compliance_current_control_coverage.json"

VALID_CLASSIFICATIONS = {
    "HISTORICAL_CERTIFICATION",
    "CURRENT_ACTIVE",
    "SUPERSEDED",
    "OBSOLETE",
    "UNSAFE_ACTIVE_STATE",
    "DUPLICATE",
    "SUPPORTING_FIXTURE",
    "MIGRATION_REHEARSAL",
}
REQUIRED_CONTROL_ORDER = [
    "authentication",
    "authorization",
    "firm_scope",
    "route_integration",
    "service_enforcement",
    "separation_of_duties",
    "attribution",
    "permissions_and_migration",
    "activation_boundary",
    "audit_integrity",
]
REQUIRED_CONTROLS = set(REQUIRED_CONTROL_ORDER)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_registry(registry: dict, *, check_files: bool = True) -> list[str]:
    errors: list[str] = []
    audits = registry.get("audits") or []
    if not audits:
        fail(errors, "registry_has_no_audits")
        return errors

    ids = [item.get("audit_id") for item in audits]
    paths = [item.get("path") for item in audits]
    if len(ids) != len(set(ids)):
        fail(errors, "duplicate_audit_ids")
    duplicates = {path for path in paths if paths.count(path) > 1}
    if duplicates:
        fail(errors, "duplicate_paths:" + ",".join(sorted(duplicates)))

    audit_by_id = {item.get("audit_id"): item for item in audits}
    for item in audits:
        audit_id = item.get("audit_id")
        classification = item.get("classification")
        path = item.get("path")
        controls = item.get("controls") or []
        if classification not in VALID_CLASSIFICATIONS:
            fail(errors, f"unknown_classification:{audit_id}")
        if not controls:
            fail(errors, f"missing_controls:{audit_id}")
        if check_files and path and not (ROOT / path).exists():
            fail(errors, f"missing_file:{audit_id}:{path}")
        if classification == "CURRENT_ACTIVE" and not item.get("safe_to_run_currently"):
            fail(errors, f"current_marked_unsafe:{audit_id}")
        if classification == "HISTORICAL_CERTIFICATION" and not item.get("immutable"):
            fail(errors, f"historical_not_immutable:{audit_id}")
        if classification in {"HISTORICAL_CERTIFICATION", "SUPERSEDED"}:
            successors = item.get("successors") or []
            if not successors:
                fail(errors, f"missing_successor:{audit_id}")
            for successor in successors:
                if successor not in audit_by_id:
                    fail(errors, f"missing_successor_target:{audit_id}->{successor}")
        for successor in item.get("successors") or []:
            target = audit_by_id.get(successor)
            if target and target.get("classification") == "OBSOLETE":
                fail(errors, f"obsolete_successor:{audit_id}->{successor}")

    suite = registry.get("current_suite_order") or []
    for audit_id in suite:
        item = audit_by_id.get(audit_id)
        if not item:
            fail(errors, f"suite_missing_audit:{audit_id}")
            continue
        if item.get("classification") != "CURRENT_ACTIVE":
            fail(errors, f"non_current_in_suite:{audit_id}")

    def visit(audit_id: str, stack: list[str]) -> None:
        if audit_id in stack:
            fail(errors, "successor_cycle:" + "->".join(stack + [audit_id]))
            return
        item = audit_by_id.get(audit_id)
        if not item:
            return
        for successor in item.get("successors") or []:
            visit(successor, stack + [audit_id])

    for audit_id in audit_by_id:
        visit(audit_id, [])
    return errors


def validate_integrity(manifest: dict) -> list[str]:
    errors: list[str] = []
    for item in manifest.get("files") or []:
        path = ROOT / item["path"]
        if not path.exists():
            fail(errors, f"integrity_missing_file:{item['path']}")
            continue
        if sha256(path) != item["sha256"]:
            fail(errors, f"integrity_hash_mismatch:{item['path']}")
        if path.stat().st_size != int(item["size"]):
            fail(errors, f"integrity_size_mismatch:{item['path']}")
    return errors


def validate_coverage(coverage: dict, registry: dict) -> list[str]:
    errors: list[str] = []
    audit_ids = {item["audit_id"] for item in registry.get("audits") or []}
    controls = coverage.get("controls") or []
    control_ids = [item.get("control_id") for item in controls]
    if control_ids != REQUIRED_CONTROL_ORDER:
        fail(errors, "coverage_order_nondeterministic")
    missing = sorted(REQUIRED_CONTROLS - set(control_ids))
    if missing:
        fail(errors, "coverage_missing_required:" + ",".join(missing))
    unknown = sorted(set(control_ids) - REQUIRED_CONTROLS)
    if unknown:
        fail(errors, "coverage_unknown_controls:" + ",".join(unknown))
    for item in controls:
        if item.get("status") != "covered":
            fail(errors, f"coverage_not_current:{item.get('control_id')}")
        if not item.get("current_audits"):
            fail(errors, f"coverage_missing_current_audit:{item.get('control_id')}")
        for audit_id in item.get("current_audits") or []:
            if audit_id not in audit_ids:
                fail(errors, f"coverage_unknown_audit:{item.get('control_id')}->{audit_id}")
    return errors


def synthetic_validation_tests(registry: dict, coverage: dict) -> list[str]:
    errors: list[str] = []

    cases = []
    duplicate_id = copy.deepcopy(registry)
    duplicate_id["audits"][1]["audit_id"] = duplicate_id["audits"][0]["audit_id"]
    cases.append(("synthetic_duplicate_id", validate_registry(duplicate_id, check_files=False)))

    unknown_class = copy.deepcopy(registry)
    unknown_class["audits"][0]["classification"] = "NOPE"
    cases.append(("synthetic_unknown_classification", validate_registry(unknown_class, check_files=False)))

    missing_file = copy.deepcopy(registry)
    missing_file["audits"][0]["path"] = "scripts/does_not_exist.py"
    cases.append(("synthetic_missing_file", validate_registry(missing_file, check_files=True)))

    missing_successor = copy.deepcopy(registry)
    missing_successor["audits"][0]["successors"] = ["MISSING"]
    cases.append(("synthetic_missing_successor", validate_registry(missing_successor, check_files=False)))

    cycle = copy.deepcopy(registry)
    cycle["audits"][0]["successors"] = [cycle["audits"][1]["audit_id"]]
    cycle["audits"][1]["successors"] = [cycle["audits"][0]["audit_id"]]
    cases.append(("synthetic_successor_cycle", validate_registry(cycle, check_files=False)))

    unsafe_current = copy.deepcopy(registry)
    for item in unsafe_current["audits"]:
        if item["classification"] == "CURRENT_ACTIVE":
            item["safe_to_run_currently"] = false_value = False
            break
    cases.append(("synthetic_current_unsafe", validate_registry(unsafe_current, check_files=False)))

    historical_in_suite = copy.deepcopy(registry)
    historical_in_suite["current_suite_order"].append(historical_in_suite["audits"][0]["audit_id"])
    cases.append(("synthetic_historical_in_suite", validate_registry(historical_in_suite, check_files=False)))

    missing_coverage = copy.deepcopy(coverage)
    missing_coverage["controls"] = missing_coverage["controls"][:-1]
    cases.append(("synthetic_missing_coverage", validate_coverage(missing_coverage, registry)))

    for name, case_errors in cases:
        if not case_errors:
            errors.append(name + "_did_not_fail")
    return errors


def main() -> int:
    registry = load_json(REGISTRY_PATH)
    integrity = load_json(INTEGRITY_PATH)
    coverage = load_json(COVERAGE_PATH)
    errors = []
    errors.extend(validate_registry(registry))
    errors.extend(validate_integrity(integrity))
    errors.extend(validate_coverage(coverage, registry))
    errors.extend(synthetic_validation_tests(registry, coverage))

    print(f"REGISTRY={REGISTRY_PATH}")
    print(f"INTEGRITY={INTEGRITY_PATH}")
    print(f"COVERAGE={COVERAGE_PATH}")
    if errors:
        print("RESULT: FAIL")
        for error in errors:
            print("ERROR - " + error)
        return 1
    print("TESTS_PASSED=registry,integrity,coverage,synthetic-invalid-cases")
    print("TESTS_FAILED=0")
    print("TRUSTEE APP STEP 25AE LINEAGE VALIDATION")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
