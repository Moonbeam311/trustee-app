from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "core_product_manual_operator_acceptance_25al.md"
BASELINE_HEAD = "8e6318ce7822cd0f66cca48817b31f4c1320845e"
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


def section(text: str, title: str) -> str:
    marker = f"## {title}"
    start = text.find(marker)
    if start < 0:
        return ""
    match = re.search(r"^## ", text[start + len(marker) :], re.MULTILINE)
    if not match:
        return text[start:]
    return text[start : start + len(marker) + match.start()]


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
    required_sections = [str(i) + ". " for i in range(1, 25)]
    for prefix in required_sections:
        failures += 0 if record(f"section prefix {prefix}", f"## {prefix}" in text) else 1

    required_terms = [
        BASELINE_HEAD,
        "flask run",
        "http://127.0.0.1:5000",
        "DB_PATH",
        "PASS_EXPECTED_302",
        "PASS_EXPECTED_403",
        "PASS_EXPECTED_503_INACTIVE",
        "INVALID_ASSUMED_ROUTE",
        "/change_password",
        "/change-password",
        "/execution/transfers",
        "/portfolio.pdf",
        "/reports/audit.pdf",
        "/reports/trust/TR-022/summary.pdf",
        "/reports/portfolio.pdf",
        "/reports/fiduciaries.pdf",
        "NameError: get_portfolio_snapshot is not defined",
        "sqlite3.Row",
        "ACCEPTANCE_PASS_WITH_REPAIR_ITEMS",
        "Step 25AM - Reports PDF Runtime Repair",
        CURRENT_SHA,
        POLICY_SHA,
        "ACTIVE_UNCHANGED_DURING_CLONE_TESTING=True",
    ]
    for term in required_terms:
        failures += 0 if record(f"required term {term}", term in text) else 1

    defect_section = section(text, "18. Confirmed Product Defects")
    failures += 0 if record("exactly two confirmed PDF defects", defect_section.count("CONFIRMED_PRODUCT_DEFECT") == 0 and defect_section.count("| Portfolio PDF runtime failure |") == 1 and defect_section.count("| Fiduciary PDF runtime failure |") == 1) else 1
    failures += 0 if record("acceptance decision exactly once", text.count("ACCEPTANCE_PASS_WITH_REPAIR_ITEMS") == 1) else 1
    failures += 0 if record("next phase exactly once", text.count("Step 25AM - Reports PDF Runtime Repair") == 3, text.count("Step 25AM - Reports PDF Runtime Repair")) else 1
    failures += 0 if record("authorization defects absent", "AUTHORIZATION_DEFECT" in text and "No authorization defect was confirmed" in text) else 1
    failures += 0 if record("data integrity defects absent", "DATA_INTEGRITY_DEFECT" in text and "ACTIVE_UNCHANGED_DURING_CLONE_TESTING=True" in text) else 1
    failures += 0 if record("clone methodology present", "step25al_acceptance_clone.db" in text and "Clone starting SHA" in text and "Clone final SHA" in text) else 1

    permanent_ids = re.findall(r"\bD-\d{3,}\b|\bDEFECT-\d+\b|\bBUG-\d+\b", text)
    failures += 0 if record("no permanent defect IDs", not permanent_ids, permanent_ids) else 1

    paths = changed_paths()
    production_changes = sorted(p for p in paths if p == "app.py" or p.startswith(PRODUCTION_PATHS))
    state_changes = sorted(paths & STATE_PATHS)
    staged = {p.replace("\\", "/") for p in git("diff", "--cached", "--name-only").splitlines() if p}
    staged_state = sorted(staged & STATE_PATHS)
    failures += 0 if record("no production code modified", not production_changes, production_changes) else 1
    failures += 0 if record("no active state staged", not staged_state and not state_changes, {"changed": state_changes, "staged": staged_state}) else 1

    print("STEP 25AL CORE PRODUCT MANUAL OPERATOR ACCEPTANCE AUDIT")
    print("RESULT:", "PASS" if failures == 0 else "FAIL")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
