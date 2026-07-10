"""
V2-HARDEN-3 — Governance Export Path Regression Test

Script-only hardening audit.

Purpose:
- Verify governance evidence HTML routes render.
- Verify governance evidence TXT routes return text/plain content.
- Verify governance evidence CSV routes return CSV-style content.
- Verify filtered DOC-TRUST-TR-022 context works.
- Verify key expected phrases appear in each response.
- Verify routes do not produce 404 / 500 errors.

This script uses Flask's local test client.
It does not intentionally mutate governance records, does not create certification records,
and does not tag Version 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@dataclass
class RouteCase:
    label: str
    path: str
    expected_status: int
    expected_contains: list[str]
    expected_content_type_contains: str | None = None


@dataclass
class Check:
    key: str
    status: str
    detail: str


def add(checks: list[Check], key: str, ok: bool, detail: str) -> None:
    checks.append(Check(key=key, status="PASS" if ok else "FAIL", detail=detail))


def decode_response(resp) -> str:
    try:
        return resp.get_data(as_text=True)
    except Exception:
        return ""


def run_case(client, checks: list[Check], case: RouteCase) -> None:
    resp = client.get(case.path)
    body = decode_response(resp)
    content_type = resp.headers.get("Content-Type", "")

    add(
        checks,
        f"status:{case.label}",
        resp.status_code == case.expected_status,
        f"{case.path} status={resp.status_code}",
    )

    if case.expected_content_type_contains:
        add(
            checks,
            f"content_type:{case.label}",
            case.expected_content_type_contains.lower() in content_type.lower(),
            f"{case.path} content_type={content_type}",
        )

    for phrase in case.expected_contains:
        add(
            checks,
            f"contains:{case.label}:{phrase[:40]}",
            phrase in body,
            f"{case.path} contains {phrase!r}",
        )

    add(
        checks,
        f"no_traceback:{case.label}",
        "Traceback (most recent call last)" not in body,
        case.path,
    )

    add(
        checks,
        f"no_internal_server_error:{case.label}",
        "Internal Server Error" not in body,
        case.path,
    )


def main() -> int:
    checks: list[Check] = []

    print("V2-HARDEN-3 GOVERNANCE EXPORT PATH REGRESSION AUDIT")
    print("=" * 76)
    print(f"Repo Root: {ROOT}")
    print("Mode: Flask test-client route regression")
    print("")

    try:
        from app import app
    except Exception as exc:
        add(checks, "import_app", False, f"{type(exc).__name__}: {exc}")
        for check in checks:
            print(f"{check.status}: {check.key} — {check.detail}")
        print("RESULT: FAIL")
        return 1

    add(checks, "import_app", True, "app imported")

    unfiltered_cases = [
        RouteCase(
            "index_html_unfiltered",
            "/governance/evidence-exports",
            200,
            ["Governance Evidence Export Index"],
            "text/html",
        ),
        RouteCase(
            "index_csv_combined_unfiltered",
            "/governance/evidence-exports.csv?packet_type=combined",
            200,
            ["packet_type"],
            "text/csv",
        ),
        RouteCase(
            "index_csv_relationships_unfiltered",
            "/governance/evidence-exports.csv?packet_type=relationships",
            200,
            ["relationship"],
            "text/csv",
        ),
        RouteCase(
            "index_csv_audits_unfiltered",
            "/governance/evidence-exports.csv?packet_type=audits",
            200,
            ["audit"],
            "text/csv",
        ),
        RouteCase(
            "manifest_html_unfiltered",
            "/governance/evidence-exports/manifest",
            200,
            ["Governance Evidence Export Manifest"],
            "text/html",
        ),
        RouteCase(
            "manifest_txt_unfiltered",
            "/governance/evidence-exports/manifest.txt",
            200,
            ["GOVERNANCE EVIDENCE EXPORT MANIFEST", "CUSTODY NOTICE"],
            "text/plain",
        ),
        RouteCase(
            "integrity_html_unfiltered",
            "/governance/evidence-exports/integrity",
            200,
            ["Governance Export Integrity Digest"],
            "text/html",
        ),
        RouteCase(
            "integrity_txt_unfiltered",
            "/governance/evidence-exports/integrity.txt",
            200,
            ["GOVERNANCE EXPORT INTEGRITY DIGEST", "CUSTODY NOTICE"],
            "text/plain",
        ),
        RouteCase(
            "archive_html_unfiltered",
            "/governance/evidence-exports/archive-intake",
            200,
            ["Governance Export Archive Intake"],
            "text/html",
        ),
        RouteCase(
            "archive_txt_unfiltered",
            "/governance/evidence-exports/archive-intake.txt",
            200,
            ["GOVERNANCE EXPORT ARCHIVE INTAKE", "CUSTODY NOTICE"],
            "text/plain",
        ),
        RouteCase(
            "certification_html_unfiltered",
            "/governance/evidence-exports/certification",
            200,
            ["Governance Evidence Certification Dashboard"],
            "text/html",
        ),
        RouteCase(
            "certification_txt_unfiltered",
            "/governance/evidence-exports/certification.txt",
            200,
            ["GOVERNANCE EVIDENCE CERTIFICATION DASHBOARD", "CUSTODY NOTICE"],
            "text/plain",
        ),
        RouteCase(
            "exceptions_html_unfiltered",
            "/governance/evidence-exports/exceptions",
            200,
            ["Governance Evidence Exception Panel"],
            "text/html",
        ),
        RouteCase(
            "exceptions_txt_unfiltered",
            "/governance/evidence-exports/exceptions.txt",
            200,
            ["GOVERNANCE EVIDENCE EXCEPTION PANEL", "CUSTODY NOTICE"],
            "text/plain",
        ),
        RouteCase(
            "completion_html_unfiltered",
            "/governance/evidence-exports/completion-gate",
            200,
            ["Governance Evidence Completion Gate"],
            "text/html",
        ),
        RouteCase(
            "completion_txt_unfiltered",
            "/governance/evidence-exports/completion-gate.txt",
            200,
            ["GOVERNANCE EVIDENCE COMPLETION GATE", "CUSTODY NOTICE"],
            "text/plain",
        ),
    ]

    filtered_query = "object_type=Document&object_id=DOC-TRUST-TR-022"

    filtered_cases = [
        RouteCase(
            "index_html_filtered",
            f"/governance/evidence-exports?{filtered_query}",
            200,
            ["DOC-TRUST-TR-022"],
            "text/html",
        ),
        RouteCase(
            "csv_combined_filtered",
            f"/governance/evidence-exports.csv?packet_type=combined&{filtered_query}",
            200,
            ["DOC-TRUST-TR-022"],
            "text/csv",
        ),
        RouteCase(
            "manifest_html_filtered",
            f"/governance/evidence-exports/manifest?{filtered_query}",
            200,
            ["DOC-TRUST-TR-022"],
            "text/html",
        ),
        RouteCase(
            "manifest_txt_filtered",
            f"/governance/evidence-exports/manifest.txt?{filtered_query}",
            200,
            ["DOC-TRUST-TR-022", "CUSTODY NOTICE"],
            "text/plain",
        ),
        RouteCase(
            "integrity_html_filtered",
            f"/governance/evidence-exports/integrity?{filtered_query}",
            200,
            ["DOC-TRUST-TR-022"],
            "text/html",
        ),
        RouteCase(
            "integrity_txt_filtered",
            f"/governance/evidence-exports/integrity.txt?{filtered_query}",
            200,
            ["DOC-TRUST-TR-022", "CUSTODY NOTICE"],
            "text/plain",
        ),
        RouteCase(
            "archive_html_filtered",
            f"/governance/evidence-exports/archive-intake?{filtered_query}",
            200,
            ["DOC-TRUST-TR-022"],
            "text/html",
        ),
        RouteCase(
            "archive_txt_filtered",
            f"/governance/evidence-exports/archive-intake.txt?{filtered_query}",
            200,
            ["DOC-TRUST-TR-022", "CUSTODY NOTICE"],
            "text/plain",
        ),
        RouteCase(
            "certification_html_filtered",
            f"/governance/evidence-exports/certification?{filtered_query}",
            200,
            ["DOC-TRUST-TR-022"],
            "text/html",
        ),
        RouteCase(
            "certification_txt_filtered",
            f"/governance/evidence-exports/certification.txt?{filtered_query}",
            200,
            ["DOC-TRUST-TR-022", "CUSTODY NOTICE"],
            "text/plain",
        ),
        RouteCase(
            "exceptions_html_filtered",
            f"/governance/evidence-exports/exceptions?{filtered_query}",
            200,
            ["DOC-TRUST-TR-022"],
            "text/html",
        ),
        RouteCase(
            "exceptions_txt_filtered",
            f"/governance/evidence-exports/exceptions.txt?{filtered_query}",
            200,
            ["DOC-TRUST-TR-022", "CUSTODY NOTICE"],
            "text/plain",
        ),
        RouteCase(
            "completion_html_filtered",
            f"/governance/evidence-exports/completion-gate?{filtered_query}",
            200,
            ["DOC-TRUST-TR-022"],
            "text/html",
        ),
        RouteCase(
            "completion_txt_filtered",
            f"/governance/evidence-exports/completion-gate.txt?{filtered_query}",
            200,
            ["DOC-TRUST-TR-022", "CUSTODY NOTICE"],
            "text/plain",
        ),
    ]

    print("RUNNING ROUTE CASES")
    print("-" * 76)

    with app.test_client() as client:
        # Preserve authenticated/admin session assumptions used by local browser work.
        from datetime import datetime, timezone

        with client.session_transaction() as sess:
            sess["user"] = "admin123"
            sess["user_id"] = "admin123"
            sess["username"] = "admin123"
            sess["role"] = "Admin"
            sess["is_master_admin"] = True
            sess["firm_id"] = "FIRM-002"
            sess["last_activity"] = datetime.now(timezone.utc).timestamp()

        for case in unfiltered_cases + filtered_cases:
            print(f"CHECK: {case.label} -> {case.path}")
            run_case(client, checks, case)

    print("")
    print("SUMMARY")
    print("-" * 76)

    pass_count = sum(1 for c in checks if c.status == "PASS")
    fail_count = sum(1 for c in checks if c.status == "FAIL")

    for check in checks:
        print(f"{check.status}: {check.key} — {check.detail}")

    print("")
    print(f"checks_total: {len(checks)}")
    print(f"checks_passed: {pass_count}")
    print(f"checks_failed: {fail_count}")

    if fail_count:
        print("")
        print("RESULT: FAIL")
        return 1

    print("")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
