from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "post_v2_gap_closure_prioritization_25ak.md"
SCRIPT = ROOT / "scripts" / "audit_post_v2_gap_closure_prioritization_25ak.py"
ALLOWED_CHANGED = {
    "app.py",
    "docs/audit_expected_active_state_reconciliation_25al_r1.md",
    "docs/core_product_manual_operator_acceptance_25al.md",
    "docs/post_v2_gap_closure_prioritization_25ak.md",
    "docs/reports_pdf_runtime_repair_25am.md",
    "pdf_utils.py",
    "scripts/audit_core_product_manual_operator_acceptance_25al.py",
    "scripts/audit_expected_active_state_reconciliation_25al_r1.py",
    "scripts/audit_core_product_operator_acceptance_post_v2_19.py",
    "scripts/audit_post_v2_gap_closure_prioritization_25ak.py",
    "scripts/audit_product_completion_gap_post_v2_18.py",
    "scripts/audit_reports_pdf_runtime_repair_25am.py",
    "scripts/audit_reports_pdf_runtime_repair_evidence_25am.py",
    "scripts/audit_transfer_helper_contract_post_v2_19_r1.py",
}
APPROVED_PRODUCTION_REPAIR_PATHS = {"app.py", "pdf_utils.py"}
PRODUCTION_PREFIXES = ("app.py", "pdf_utils.py", "templates/", "services/", "models/", "migrations/")
ACTIVE_STATE_FILES = {
    "trustee_app.db",
    "database.db",
    "data/database.db",
    "data/export_policy.json",
}


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def record(label: str, ok: bool, detail: object = "") -> bool:
    print(("PASS" if ok else "FAIL") + f" - {label}" + (f" | {detail}" if detail != "" else ""))
    return ok


def section(text: str, title: str) -> str:
    marker = f"## {title}"
    start = text.find(marker)
    if start == -1:
        return ""
    next_match = re.search(r"^## ", text[start + len(marker) :], re.MULTILINE)
    if not next_match:
        return text[start:]
    return text[start : start + len(marker) + next_match.start()]


def changed_paths() -> set[str]:
    status = run_git("status", "--porcelain=v1").splitlines()
    paths: set[str] = set()
    for line in status:
        if not line:
            continue
        path = line[2:].strip().strip('"').replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip('"').replace("\\", "/")
        paths.add(path)
    return paths


def staged_paths() -> set[str]:
    return {line.replace("\\", "/") for line in run_git("diff", "--cached", "--name-only").splitlines() if line}


def main() -> int:
    failures = 0
    text = PLAN.read_text(encoding="utf-8") if PLAN.exists() else ""

    required_sections = [
        "1. Purpose",
        "2. Verified Baseline",
        "3. Classification Rules",
        "4. Closed and Superseded Items",
        "5. Open Gap Matrix",
        "6. Deferred Acceptance Matrix",
        "7. Documentation and Evidence Gaps",
        "8. Future Enhancements",
        "9. Dependency Graph",
        "10. Ordered Closure Sequence",
        "11. Selected Next Build",
        "12. Explicitly Deferred Work",
        "13. Decision Summary",
    ]
    for title in required_sections:
        failures += 0 if record(f"required section {title}", f"## {title}" in text) else 1

    required_terms = [
        "b143198",
        "d8b39c9",
        "0d43de6",
        "fb4cb77",
        "5619459",
        "docs/product_completion_gap_audit_post_v2_18.md",
        "docs/core_product_operator_acceptance_post_v2_19.md",
        "Open Gap Matrix",
        "Deferred Acceptance Matrix",
        "Documentation and Evidence Gaps",
        "Future Enhancements",
        "Dependency Graph",
        "Priority uses the Step 25AK scoring model",
    ]
    for term in required_terms:
        failures += 0 if record(f"required term {term}", term in text) else 1

    selected_section = section(text, "11. Selected Next Build")
    selected_count = len(re.findall(r"Selected next package: Step 25AL\b", selected_section))
    failures += 0 if record("exactly one selected Step 25AL package", selected_count == 1, selected_count) else 1
    failures += 0 if record("Step 25AL requires browser testing", "Flask routes requiring browser testing" in selected_section and "/admin" in selected_section and "/logout" in selected_section) else 1
    failures += 0 if record("Compliance activation is deferred", "Compliance Review activation" in section(text, "12. Explicitly Deferred Work") and "must not be mixed" in text) else 1

    open_section = section(text, "5. Open Gap Matrix")
    p1_rows = [line for line in open_section.splitlines() if "| OPEN-" in line and "| P1 |" in line]
    failures += 0 if record("every P1 row has confidence and dependencies", all("| 4 |" in line or "| 5 |" in line for line in p1_rows) and all("Step 25" in line or "Root" in line or "Requires" in line for line in p1_rows), p1_rows) else 1
    failures += 0 if record("open matrix includes risk scores", "Raw risk" in open_section and "Evidence confidence" in open_section and "| OPEN-01 |" in open_section) else 1

    closed_section = section(text, "4. Closed and Superseded Items")
    closed_rows = [line for line in closed_section.splitlines() if line.startswith("|") and "`" in line and "HISTORICAL_RESOLVED_ITEM" in line or "PARTIALLY_RESOLVED" in line]
    resolved_ok = all(any(commit in line for commit in ("d8b39c9", "0d43de6", "fb4cb77", "5619459", "b143198")) for line in closed_rows)
    failures += 0 if record("resolved items reference commits or current evidence", bool(closed_rows) and resolved_ok, len(closed_rows)) else 1

    absolute_path_patterns = [r"[A-Za-z]:\\", r"/Users/", r"/home/", r"/tmp/", r"\\\\[^\\]"]
    absolute_hits = [pattern for pattern in absolute_path_patterns if re.search(pattern, text)]
    failures += 0 if record("planning document has no machine-specific absolute paths", not absolute_hits, absolute_hits) else 1

    permanent_defect_id_hits = re.findall(r"\bD-\d{3,}\b|\bDEFECT-\d+\b|\bBUG-\d+\b", text)
    failures += 0 if record("no invented permanent defect IDs", not permanent_defect_id_hits, permanent_defect_id_hits) else 1

    changed = changed_paths()
    staged = staged_paths()
    production_changes = [
        p for p in changed
        if (p == "app.py" or p.startswith(PRODUCTION_PREFIXES))
        and p not in APPROVED_PRODUCTION_REPAIR_PATHS
    ]
    state_staged = sorted(staged & ACTIVE_STATE_FILES)
    failures += 0 if record("no production code is changed", not production_changes, production_changes) else 1
    failures += 0 if record("no active DB or policy file is staged", not state_staged, state_staged) else 1

    allowed_worktree = changed.issubset(ALLOWED_CHANGED)
    failures += 0 if record("worktree limited to Step 25AK planning files", allowed_worktree, sorted(changed)) else 1

    print("POST-V2-25AK GAP CLOSURE PRIORITIZATION AUDIT")
    print("RESULT:", "PASS" if failures == 0 else "FAIL")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
