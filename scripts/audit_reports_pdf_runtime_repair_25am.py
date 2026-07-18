from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ACTIVE_DB = ROOT / "trustee_app.db"
POLICY = ROOT / "data" / "export_policy.json"
REQUIRED_DB_SHA = "7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525"
REQUIRED_AUDIT_COUNT = 569
REQUIRED_POLICY_SHA = "660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361"
PDF_ROUTES = [
    "/reports/portfolio.pdf",
    "/reports/fiduciaries.pdf",
    "/reports/audit.pdf",
    "/reports/trust/TR-022/summary.pdf",
]
BUSINESS_TABLES = [
    "trusts",
    "matters",
    "transfers",
    "app_users",
    "institutional_certifications",
    "fiduciaries",
    "role_permissions",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def db_count(path: Path, table: str) -> int | None:
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        cur = con.cursor()
        try:
            return cur.execute(f"select count(*) from {table}").fetchone()[0]
        except sqlite3.OperationalError:
            return None
    finally:
        con.close()


def db_counts(path: Path) -> dict[str, int | None]:
    return {table: db_count(path, table) for table in BUSINESS_TABLES}


def record(label: str, ok: bool, detail: object = "") -> bool:
    print(("PASS" if ok else "FAIL") + f" - {label}" + (f" | {detail}" if detail != "" else ""))
    return ok


def install_admin_session(client) -> None:
    with client.session_transaction() as session:
        session.clear()
        session["username"] = "admin"
        session["role"] = "Admin"
        session["user_role"] = "Admin"
        session["is_master_admin"] = True
        session["firm_id"] = "FIRM-002"
        session["last_activity"] = datetime.now(UTC).timestamp()


def assert_pdf_response(label: str, response, failures: int) -> int:
    body = response.get_data()
    checks = [
        (f"{label} HTTP 200", response.status_code == 200, response.status_code),
        (f"{label} content type PDF", "application/pdf" in (response.headers.get("Content-Type") or ""), response.headers.get("Content-Type")),
        (f"{label} PDF signature", body.startswith(b"%PDF-"), body[:16]),
        (f"{label} nontrivial length", len(body) > 1_000, len(body)),
    ]
    for check_label, ok, detail in checks:
        failures += 0 if record(check_label, ok, detail) else 1
    return failures


def make_sqlite_row() -> sqlite3.Row:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("create table sample (trust_id text, trust_name text, full_name text, role_title text, status text, effective_date text)")
    cur.execute(
        "insert into sample values (?, ?, ?, ?, ?, ?)",
        ("TR-ROW", "Row Trust", "Row Fiduciary", "Trustee", "Active", "2026-07-18"),
    )
    row = cur.execute("select * from sample").fetchone()
    con.close()
    return row


def main() -> int:
    failures = 0
    active_before = {
        "db_sha": sha256(ACTIVE_DB),
        "db_mtime_ns": ACTIVE_DB.stat().st_mtime_ns,
        "audit_log": db_count(ACTIVE_DB, "audit_log"),
        "policy_sha": sha256(POLICY),
        "policy_mtime_ns": POLICY.stat().st_mtime_ns,
    }
    failures += 0 if record("active DB continuity SHA", active_before["db_sha"] == REQUIRED_DB_SHA, active_before) else 1
    failures += 0 if record("active audit baseline", active_before["audit_log"] == REQUIRED_AUDIT_COUNT, active_before["audit_log"]) else 1
    failures += 0 if record("policy continuity SHA", active_before["policy_sha"] == REQUIRED_POLICY_SHA, active_before["policy_sha"]) else 1

    with tempfile.TemporaryDirectory(prefix="trustee_25am_pdf_", ignore_cleanup_errors=True) as tmp:
        clone = Path(tmp) / "step25am_reports_clone.db"
        shutil.copy2(ACTIVE_DB, clone)
        os.environ["DB_PATH"] = str(clone)
        failures += 0 if record("clone starts from active SHA", sha256(clone) == REQUIRED_DB_SHA, sha256(clone)) else 1
        clone_counts_before = db_counts(clone)

        from app import app, get_portfolio_summary
        from pdf_utils import build_pdf_response, fiduciary_report_story, portfolio_report_story

        client = app.test_client()
        unauth = app.test_client().get("/reports/portfolio.pdf")
        failures += 0 if record("unauthenticated portfolio report redirects", unauth.status_code == 302 and "/login" in (unauth.headers.get("Location") or ""), (unauth.status_code, unauth.headers.get("Location"))) else 1
        unauth_fid = app.test_client().get("/reports/fiduciaries.pdf")
        failures += 0 if record("unauthenticated fiduciary report redirects", unauth_fid.status_code == 302 and "/login" in (unauth_fid.headers.get("Location") or ""), (unauth_fid.status_code, unauth_fid.headers.get("Location"))) else 1

        install_admin_session(client)
        portfolio, totals = get_portfolio_summary()
        expected_keys = {"trust_id", "trust_name", "gross_total", "taxable_total", "principal_total", "count"}
        failures += 0 if record("portfolio returns list rows", isinstance(portfolio, list), type(portfolio).__name__) else 1
        failures += 0 if record("portfolio row contract", not portfolio or expected_keys.issubset(portfolio[0]), portfolio[0] if portfolio else {}) else 1
        failures += 0 if record("portfolio totals contract", {"gross_total", "taxable_total", "principal_total", "trust_count"}.issubset(totals), totals) else 1
        failures += 0 if record("portfolio firm context FIRM-002", all(str(row.get("trust_id", "")).startswith("TR-") for row in portfolio), len(portfolio)) else 1
        story = portfolio_report_story([], {"gross_total": 0, "taxable_total": 0, "principal_total": 0, "trust_count": 0})
        with app.app_context():
            empty_pdf = build_pdf_response("empty_portfolio.pdf", story)
        failures = assert_pdf_response("empty portfolio PDF story", empty_pdf, failures)

        fiduciary_dict_story = fiduciary_report_story(
            trusts=[{"trust_id": "TR-DICT", "trust_name": "Dictionary Trust"}],
            fiduciaries=[{"fiduciary_id": "F-DICT", "full_name": "Dictionary Fiduciary", "role_title": "Trustee", "trust_id": "TR-DICT", "status": "Active"}],
            selected_trust_id="TR-DICT",
        )
        failures += 0 if record("fiduciary dict input supported", bool(fiduciary_dict_story), len(fiduciary_dict_story)) else 1

        row = make_sqlite_row()
        fiduciary_row_story = fiduciary_report_story(trusts=[row], fiduciaries=[row], selected_trust_id="TR-ROW")
        failures += 0 if record("fiduciary sqlite3.Row input supported", bool(fiduciary_row_story), len(fiduciary_row_story)) else 1
        missing_selection = fiduciary_report_story(trusts=[row], fiduciaries=[row], selected_trust_id="TR-MISSING")
        failures += 0 if record("fiduciary missing selected trust handled", bool(missing_selection), len(missing_selection)) else 1
        with app.app_context():
            empty_fiduciary = build_pdf_response("empty_fiduciary.pdf", fiduciary_report_story([], [], selected_trust_id="TR-EMPTY"))
        failures = assert_pdf_response("empty fiduciary PDF story", empty_fiduciary, failures)
        try:
            fiduciary_report_story(trusts=[object()], fiduciaries=[], selected_trust_id=None)
            malformed_failed = False
        except TypeError:
            malformed_failed = True
        failures += 0 if record("malformed fiduciary input fails clearly", malformed_failed) else 1

        for route in PDF_ROUTES:
            failures = assert_pdf_response(route, client.get(route), failures)

        selected = client.get("/reports/fiduciaries.pdf?trust_id=TR-022")
        failures = assert_pdf_response("/reports/fiduciaries.pdf selected trust", selected, failures)

        reports = client.get("/reports")
        failures += 0 if record("/reports authorized workspace HTTP 200", reports.status_code == 200, reports.status_code) else 1
        invalid = client.get("/portfolio.pdf")
        failures += 0 if record("/portfolio.pdf remains unsupported", invalid.status_code == 404, invalid.status_code) else 1

        clone_counts_after = db_counts(clone)
        failures += 0 if record("clone business tables unchanged", clone_counts_after == clone_counts_before, {"before": clone_counts_before, "after": clone_counts_after}) else 1
        failures += 0 if record("clone schema unchanged", db_count(clone, "audit_log") == db_count(clone, "audit_log")) else 1

    active_after = {
        "db_sha": sha256(ACTIVE_DB),
        "db_mtime_ns": ACTIVE_DB.stat().st_mtime_ns,
        "audit_log": db_count(ACTIVE_DB, "audit_log"),
        "policy_sha": sha256(POLICY),
        "policy_mtime_ns": POLICY.stat().st_mtime_ns,
    }
    failures += 0 if record("ACTIVE_UNCHANGED=True", active_after == active_before, {"before": active_before, "after": active_after}) else 1
    failures += 0 if record("POLICY_UNCHANGED=True", active_after["policy_sha"] == REQUIRED_POLICY_SHA and active_after["policy_mtime_ns"] == active_before["policy_mtime_ns"], active_after) else 1

    print("STEP 25AM REPORTS PDF RUNTIME REPAIR AUDIT")
    print("RESULT:", "PASS" if failures == 0 else "FAIL")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
