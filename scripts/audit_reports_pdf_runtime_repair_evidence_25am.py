from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "reports_pdf_runtime_repair_25am.md"
STARTING_HEAD = "7b20ef7"
DB_SHA = "7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525"
POLICY_SHA = "660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361"
DECISIONS = ["REPAIR_PASS", "REPAIR_PASS_WITH_LIMITATIONS", "REPAIR_BLOCKED"]
NEXT_PHASES = [
    "Step 25AN - Remaining Operator Friction and Acceptance Evidence Closure",
    "Step 25AM - Reports PDF Runtime Repair",
]


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


def main() -> int:
    failures = 0
    text = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""

    required_sections = [
        "1. Purpose",
        "2. Baseline",
        "3. Confirmed Pre-Repair Failures",
        "4. Root Cause - Portfolio PDF",
        "5. Root Cause - Fiduciary PDF",
        "6. Repair",
        "7. Automated Regression Results",
        "8. Manual Browser Results",
        "9. Authorization and Firm Scope",
        "10. Clone-State Integrity",
        "11. Active-State Integrity",
        "12. Deferred Items",
        "13. Repair Decision",
        "14. Recommended Next Phase",
    ]
    failures += 0 if record("repair report exists", REPORT.exists(), REPORT) else 1
    for title in required_sections:
        failures += 0 if record(f"section {title}", f"## {title}" in text) else 1

    required_terms = [
        STARTING_HEAD,
        DB_SHA,
        POLICY_SHA,
        "/reports/portfolio.pdf",
        "/reports/fiduciaries.pdf",
        "/reports/audit.pdf",
        "/reports/trust/TR-022/summary.pdf",
        "NameError: get_portfolio_snapshot is not defined",
        "AttributeError: 'sqlite3.Row' object has no attribute 'get'",
        "get_portfolio_summary()",
        "DELETED_OR_MISSING_HELPER",
        "sqlite3.Row",
        "row-like mapping",
        "`app.py`",
        "`pdf_utils.py`",
        "HTTP 200",
        "`application/pdf`",
        "PDF Valid",
        "Firm scope",
        "Authorization",
        "DB_PATH",
        "ACTIVE_UNCHANGED=True",
        "POLICY_UNCHANGED=True",
        "Preview-page direct `/admin` return marker",
        "Successful credential POST testing",
        "/portfolio.pdf` remains HTTP 404",
    ]
    for term in required_terms:
        failures += 0 if record(f"required term {term}", term in text) else 1

    decision_hits = [decision for decision in DECISIONS if re.search(rf"(?m)^\s*{re.escape(decision)}\s*$", text)]
    failures += 0 if record("exactly one repair decision", len(decision_hits) == 1, decision_hits) else 1

    next_hits = [phase for phase in NEXT_PHASES if phase in text]
    failures += 0 if record("exactly one next phase", len(next_hits) == 1, next_hits) else 1

    manual = section(text, "8. Manual Browser Results")
    failures += 0 if record("browser limitation not overstated", "No existing authenticated browser session" in manual and "Credential POST testing remains deferred" in manual) else 1

    forbidden_patterns = [
        r"\bD-\d{3,}\b",
        r"\bDEFECT-\d+\b",
        r"\bBUG-\d+\b",
        r"C:\\",
        r"C:/Users/",
        r"/Users/",
    ]
    forbidden_hits = []
    for pattern in forbidden_patterns:
        forbidden_hits.extend(re.findall(pattern, text))
    failures += 0 if record("no permanent invented defect IDs or machine paths", not forbidden_hits, forbidden_hits) else 1

    repair = section(text, "6. Repair")
    failures += 0 if record("app.py change described", "`app.py`" in repair and "get_portfolio_summary()" in repair) else 1
    failures += 0 if record("pdf_utils.py change described", "`pdf_utils.py`" in repair and "normalizes" in repair) else 1

    active = section(text, "11. Active-State Integrity")
    failures += 0 if record("active DB unchanged recorded", "ACTIVE_UNCHANGED=True" in active and DB_SHA in active) else 1
    failures += 0 if record("policy unchanged recorded", "POLICY_UNCHANGED=True" in active and POLICY_SHA in active) else 1

    print("STEP 25AM REPORTS PDF REPAIR EVIDENCE AUDIT")
    print("RESULT:", "PASS" if failures == 0 else "FAIL")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
