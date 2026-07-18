from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "audit_expected_active_state_reconciliation_25al_r1.md"
HISTORICAL_SHA = "6E9E3EF0AE596FB296972B99EA4ED293DB8C5DBD4A64A03AA4FBB0C0CB7A6C36"
CURRENT_SHA = "7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525"
POLICY_SHA = "660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361"
PRODUCTION_PATHS = ("app.py", "pdf_utils.py", "templates/", "services/", "models/", "migrations/")
STATE_PATHS = {"trustee_app.db", "database.db", "data/database.db", "data/export_policy.json"}


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def record(label: str, ok: bool, detail: object = "") -> bool:
    print(("PASS" if ok else "FAIL") + f" - {label}" + (f" | {detail}" if detail != "" else ""))
    return ok


def changed_paths() -> set[str]:
    paths: set[str] = set()
    for line in git("status", "--porcelain=v1").splitlines():
        if not line:
            continue
        path = line[2:].strip().strip('"').replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip('"').replace("\\", "/")
        paths.add(path)
    return paths


def main() -> int:
    failures = 0
    text = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
    required_sections = [
        "1. Purpose",
        "2. Baselines",
        "3. Comparison Method",
        "4. Schema Comparison",
        "5. Non-Audit Table Comparison",
        "6. Audit-Log Delta",
        "7. Existing Audit-Row Integrity",
        "8. Policy Integrity",
        "9. Reconciliation Decision",
        "10. New Active Continuity Baseline",
        "11. Safe Clone Test Method",
        "12. Clone Test Delta",
        "13. Active DB Preservation During Clone Testing",
        "14. Limitations",
        "15. Decision",
    ]
    for section in required_sections:
        failures += 0 if record(f"section {section}", f"## {section}" in text) else 1

    checks = [
        ("historical SHA present", HISTORICAL_SHA in text),
        ("current SHA present", CURRENT_SHA in text),
        ("audit count delta present", "`559`" in text and "`569`" in text and "559" in text and "569" in text),
        ("ten audit rows classified", "TEN_NEW_AUDIT_ROWS_CLASSIFIED=10" in text),
        ("four transfer denials", "TRANSFER_DENIAL_ROWS=4" in text and text.count("EXPECTED_TRANSFER_FIRM_SCOPE_DENIAL") == 4),
        ("six restricted viewer denials", "RESTRICTED_VIEWER_DENIAL_ROWS=6" in text and text.count("EXPECTED_RESTRICTED_USER_DENIAL") == 6),
        ("zero unexplained audit events", "UNEXPLAINED_AUDIT_EVENTS=0" in text),
        ("policy unchanged", POLICY_SHA in text and "Policy Integrity" in text),
        ("reconciliation decision present", "RECONCILED_CONSTRAINED_PROOF" in text or "RECONCILED_FULL_PROOF" in text),
        ("new active baseline present", "NEW ACTIVE DB CONTINUITY BASELINE" in text and CURRENT_SHA in text),
        ("clone method documented", "DB_PATH" in text and "step25al_acceptance_clone.db" in text and "flask run" in text),
        ("active unchanged during clone", "ACTIVE_UNCHANGED_DURING_CLONE_TESTING=True" in text),
        ("no deletion or rollback claimed", "not deleted" in text and "not claim RECONCILED_FULL_PROOF" in text),
    ]
    for label, ok in checks:
        failures += 0 if record(label, ok) else 1

    paths = changed_paths()
    production_changes = sorted(p for p in paths if p == "app.py" or p.startswith(PRODUCTION_PATHS))
    state_changes = sorted(paths & STATE_PATHS)
    staged = {p.replace("\\", "/") for p in git("diff", "--cached", "--name-only").splitlines() if p}
    staged_state = sorted(staged & STATE_PATHS)
    failures += 0 if record("no production code modified", not production_changes, production_changes) else 1
    failures += 0 if record("no active state staged", not staged_state and not state_changes, {"changed": state_changes, "staged": staged_state}) else 1

    permanent_ids = re.findall(r"\bD-\d{3,}\b|\bDEFECT-\d+\b|\bBUG-\d+\b", text)
    failures += 0 if record("no permanent defect IDs", not permanent_ids, permanent_ids) else 1

    print("STEP 25AL-R1 ACTIVE STATE RECONCILIATION AUDIT")
    print("RESULT:", "PASS" if failures == 0 else "FAIL")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
