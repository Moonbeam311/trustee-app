from __future__ import annotations

import hashlib
import re
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "operator_friction_acceptance_closure_25an.md"
STARTING_HEAD = "7524a3b4d724cabc6f473bc3e92f14b281794174"
ACTIVE_DB_SHA = "7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525"
POLICY_SHA = "660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361"
ALLOWED_CHANGED = {
    "docs/operator_friction_acceptance_closure_25an.md",
    "scripts/audit_operator_friction_acceptance_closure_25an.py",
    "scripts/audit_post_v2_gap_closure_prioritization_25ak.py",
    "scripts/audit_product_completion_gap_post_v2_18.py",
    "scripts/audit_core_product_operator_acceptance_post_v2_19.py",
    "docs/v2_certification_candidate_readiness_25ao.md",
    "scripts/audit_v2_certification_candidate_readiness_25ao.py",
}
PRODUCTION_PREFIXES = (
    "app.py",
    "pdf_utils.py",
    "services_",
    "templates/",
    "static/",
    "database/",
    "migrations/",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args],
        cwd=ROOT,
        text=True,
    ).strip()


def check(label: str, condition: bool, detail: object = "") -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"{status} {label}: {detail}")
    return condition


def active_db_counts() -> dict[str, int]:
    with sqlite3.connect(f"file:{(ROOT / 'trustee_app.db').as_posix()}?mode=ro", uri=True) as conn:
        cur = conn.cursor()
        return {
            "audit_log": cur.execute("select count(*) from audit_log").fetchone()[0],
            "transfers": cur.execute("select count(*) from transfers").fetchone()[0],
            "trusts": cur.execute("select count(*) from trusts").fetchone()[0],
            "matters": cur.execute("select count(*) from matters").fetchone()[0],
            "app_users": cur.execute("select count(*) from app_users").fetchone()[0],
            "permissions": cur.execute("select count(*) from permissions").fetchone()[0],
            "institutional_certifications": cur.execute(
                "select count(*) from institutional_certifications"
            ).fetchone()[0],
        }


def repository_changed_paths() -> set[str]:
    status = git("status", "--porcelain=v1")
    paths: set[str] = set()
    for line in status.splitlines():
        if not line:
            continue
        path = line[2:].strip().replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.add(path)
    return paths


def has_all(text: str, needles: list[str]) -> bool:
    return all(needle in text for needle in needles)


def single_decision(text: str) -> bool:
    decisions = re.findall(r"Decision: `([^`]+)`", text)
    return decisions == ["ACCEPTANCE_CLOSED_WITH_NONBLOCKING_FRICTION"]


def main() -> int:
    failures = 0
    text = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
    changed_paths = repository_changed_paths()
    unauthorized = changed_paths - ALLOWED_CHANGED
    production_changes = [
        path
        for path in changed_paths
        if path not in ALLOWED_CHANGED and path.startswith(PRODUCTION_PREFIXES)
    ]
    counts = active_db_counts()

    checks = [
        ("report exists", REPORT.exists(), REPORT.relative_to(ROOT).as_posix()),
        ("starting head recorded", STARTING_HEAD in text, STARTING_HEAD),
        ("current head at or after starting head", git("merge-base", "--is-ancestor", STARTING_HEAD, "HEAD") == "", "ancestor"),
        ("branch recorded", "`post-v2-planning`" in text, git("branch", "--show-current")),
        ("clone path recorded", "audit/runtime_sandbox/STEP-25AN/step25an_acceptance_clone.db" in text, "clone"),
        ("runtime command recorded", "`flask run`" in text and "`DB_PATH`" in text, "flask clone"),
        ("browser address recorded", "http://127.0.0.1:5000" in text, "browser"),
        (
            "required sections present",
            has_all(
                text,
                [
                    "## 1. Purpose",
                    "## 2. Baseline",
                    "## 3. Remaining Items from Step 25AL",
                    "## 4. Preview Page 1 Result",
                    "## 5. Preview Page 2 Result",
                    "## 6. Reports Re-Acceptance",
                    "## 7. Credential POST Assessment",
                    "## 8. Authorization Spot Check",
                    "## 9. Inactive Module Spot Check",
                    "## 10. Clone-State Integrity",
                    "## 11. Active-State Integrity",
                    "## 12. Remaining Operator Friction",
                    "## 13. Acceptance Closure Decision",
                    "## 14. Recommended Next Phase",
                ],
            ),
            "sections",
        ),
        (
            "preview pages classified as indirect clear return",
            has_all(
                text,
                [
                    "/trust/TR-022/packet-preview",
                    "Packet Preview TR-022",
                    "/trust/TR-022/articles-preview",
                    "Articles Preview TR-022",
                    "`PASS_INDIRECT_CLEAR_RETURN`",
                    "Clicks from preview page to Admin: `2`",
                    "Trust context preserved: `TR-022`",
                ],
            ),
            "preview classifications",
        ),
        (
            "no broken navigation conclusion",
            "Blocking operator friction: none found." in text
            and "Future UX enhancement: add a direct Admin return shortcut" in text,
            "operator friction",
        ),
        (
            "pdf evidence complete",
            has_all(
                text,
                [
                    "/reports/portfolio.pdf",
                    "/reports/fiduciaries.pdf",
                    "/reports/audit.pdf",
                    "/reports/trust/TR-022/summary.pdf",
                    "`application/pdf`",
                    "`%PDF-`",
                ],
            ),
            "pdf routes",
        ),
        (
            "credential post closed without password evidence",
            has_all(text, ["/login` POST", "`302`", "`ALREADY_VERIFIED_BY_LOGIN`", "No password is recorded"])
            and "password:" not in text.lower(),
            "credential",
        ),
        (
            "authorization evidence complete",
            has_all(
                text,
                [
                    "/admin/workspace/reports",
                    "/reports",
                    "/admin/audit-log",
                    "`permission_denied`",
                    "/execution/transfers/T-0014",
                    "`transfer_firm_access_denied`",
                ],
            ),
            "authorization",
        ),
        (
            "inactive module evidence complete",
            has_all(
                text,
                [
                    "/admin/workspace/compliance",
                    "/compliance/reviews",
                    "/admin/workspace/system",
                    "/system/observations",
                    "`PASS_EXPECTED_503_INACTIVE`",
                ],
            ),
            "inactive modules",
        ),
        (
            "clone audit-only delta recorded",
            has_all(
                text,
                [
                    "Clone audit rows: `569 -> 572`",
                    "No checked business table counts changed.",
                    "`570`: `auth`",
                    "`571`: `security`",
                    "`572`: `security`",
                ],
            ),
            "clone integrity",
        ),
        (
            "active state recorded unchanged",
            has_all(text, [ACTIVE_DB_SHA, POLICY_SHA, "`ACTIVE_UNCHANGED=True`", "`POLICY_UNCHANGED=True`"]),
            "active integrity",
        ),
        ("single closure decision", single_decision(text), "decision"),
        (
            "next phase recorded",
            "`Step 25AO - V2 Certification Candidate Readiness Audit`" in text,
            "next phase",
        ),
        ("no defect ids invented", "DEFECT-" not in text and "BUG-" not in text, "defect ids"),
        (
            "no machine absolute paths in report",
            "C:\\Users\\" not in text and "C:/Users/" not in text,
            "portable evidence",
        ),
        (
            "active database hash unchanged",
            sha256(ROOT / "trustee_app.db") == ACTIVE_DB_SHA,
            sha256(ROOT / "trustee_app.db"),
        ),
        ("active audit count unchanged", counts["audit_log"] == 569, counts),
        ("active transfer count unchanged", counts["transfers"] == 14, counts),
        ("policy hash unchanged", sha256(ROOT / "data" / "export_policy.json") == POLICY_SHA, POLICY_SHA),
        ("repository changes limited to Step 25AN evidence and guard updates", not unauthorized, sorted(unauthorized)),
        ("no production code changed", not production_changes, production_changes),
    ]

    for label, condition, detail in checks:
        if not check(label, condition, detail):
            failures += 1

    if failures:
        print(f"Step 25AN acceptance closure audit failed: {failures} failure(s)")
        return 1
    print("Step 25AN acceptance closure audit PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
