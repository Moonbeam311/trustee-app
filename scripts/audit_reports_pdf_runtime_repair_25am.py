from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.support.operational_authority import (
    OperationalAuthorityError,
    assert_snapshot_unchanged,
    authority_snapshot,
    resolve_operational_authority,
)


EXPECTED_OPERATIONAL_BRANCH = "post-v2-planning"
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


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise OperationalAuthorityError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def resolve_report_audit_authority():
    if (ROOT / "trustee_app.db").exists():
        raise OperationalAuthorityError("source-local trustee_app.db unexpectedly present")
    authority = resolve_operational_authority(ROOT)
    if authority.mode != "EXTERNAL_OPERATIONAL":
        raise OperationalAuthorityError("source-only report audit requires explicit external operational authority")
    branch = git(authority.repository_root, "branch", "--show-current")
    if branch != EXPECTED_OPERATIONAL_BRANCH:
        raise OperationalAuthorityError(
            f"operational branch mismatch: {branch}; expected {EXPECTED_OPERATIONAL_BRANCH}"
        )
    root = authority.repository_root.resolve()
    database = authority.database_path.resolve()
    if not database.is_relative_to(root):
        raise OperationalAuthorityError("operational database escapes authorized repository")
    return authority


def sqlite_read_only_backup(source_path: Path, target_path: Path) -> None:
    with closing(sqlite3.connect(f"file:{source_path.as_posix()}?mode=ro", uri=True)) as source:
        with closing(sqlite3.connect(target_path)) as target:
            source.backup(target)


def _quoted(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _normalized_sql(sql: str | None) -> str | None:
    if sql is None:
        return None
    return re.sub(r"\s+", " ", sql.replace("\r\n", "\n").replace("\r", "\n")).strip()


def schema_objects(connection: sqlite3.Connection) -> list[tuple[str, str, str, str | None]]:
    rows = connection.execute(
        """
        SELECT type, name, tbl_name, sql
        FROM sqlite_schema
        WHERE type IN ('table', 'index', 'trigger', 'view')
          AND name NOT LIKE 'sqlite_%'
          AND NOT (type = 'index' AND sql IS NULL)
        ORDER BY type, name, tbl_name
        """
    ).fetchall()
    return [(row[0], row[1], row[2], _normalized_sql(row[3])) for row in rows]


def normalized_schema_fingerprint(connection: sqlite3.Connection) -> str:
    payload = json.dumps(schema_objects(connection), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def user_table_counts(connection: sqlite3.Connection) -> dict[str, int]:
    names = [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    return {name: connection.execute(f"SELECT count(*) FROM {_quoted(name)}").fetchone()[0] for name in names}


def _digest_value(value: object) -> bytes:
    if value is None:
        payload = b""
        tag = b"N"
    elif isinstance(value, bytes):
        payload = value
        tag = b"B"
    elif isinstance(value, int):
        payload = str(value).encode("ascii")
        tag = b"I"
    elif isinstance(value, float):
        payload = value.hex().encode("ascii")
        tag = b"R"
    else:
        payload = str(value).encode("utf-8")
        tag = b"T"
    return tag + len(payload).to_bytes(8, "big") + payload


def critical_table_digest(connection: sqlite3.Connection, table: str) -> str:
    columns = connection.execute(f"PRAGMA table_info({_quoted(table)})").fetchall()
    if not columns:
        raise ValueError(f"critical table missing: {table}")
    names = [row[1] for row in columns]
    primary_key = [row[1] for row in sorted(columns, key=lambda row: row[5]) if row[5]]
    order = primary_key or names
    projection = ", ".join(_quoted(name) for name in names)
    ordering = ", ".join(_quoted(name) for name in order)
    digest = hashlib.sha256()
    digest.update(json.dumps(names, separators=(",", ":")).encode("utf-8"))
    for row in connection.execute(
        f"SELECT {projection} FROM {_quoted(table)} ORDER BY {ordering}"
    ):
        digest.update(b"ROW")
        for value in row:
            digest.update(_digest_value(value))
    return digest.hexdigest().upper()


def critical_table_digests(connection: sqlite3.Connection) -> dict[str, str]:
    present = {
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_schema WHERE type='table'")
    }
    required = [*BUSINESS_TABLES, "audit_log"]
    return {table: critical_table_digest(connection, table) for table in required if table in present}


def logical_equivalence_snapshot(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with closing(sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = len(connection.execute("PRAGMA foreign_key_check").fetchall())
        counts = user_table_counts(connection)
        return {
            "sha": sha256(path),
            "schema_version": connection.execute("PRAGMA schema_version").fetchone()[0],
            "integrity": integrity,
            "foreign_keys": foreign_keys,
            "schema_fingerprint": normalized_schema_fingerprint(connection),
            "user_table_counts": counts,
            "critical_table_digests": critical_table_digests(connection),
            "audit_log": counts.get("audit_log"),
            "transfers": counts.get("transfers"),
        }


def logical_equivalence_failures(source: dict[str, object], clone: dict[str, object]) -> list[str]:
    failures: list[str] = []
    if source.get("integrity") != "ok" or clone.get("integrity") != "ok":
        failures.append("integrity")
    if source.get("foreign_keys") != 0 or clone.get("foreign_keys") != 0:
        failures.append("foreign_keys")
    for key in (
        "schema_fingerprint",
        "user_table_counts",
        "critical_table_digests",
        "audit_log",
        "transfers",
    ):
        if source.get(key) != clone.get(key):
            failures.append(key)
    return failures


def clone_preservation_failures(before: dict[str, object], after: dict[str, object]) -> list[str]:
    keys = (
        "integrity",
        "foreign_keys",
        "schema_fingerprint",
        "user_table_counts",
        "critical_table_digests",
        "audit_log",
        "transfers",
    )
    return [key for key in keys if before.get(key) != after.get(key)]


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


def info(label: str, detail: object) -> None:
    print(f"INFO - {label} | {detail}")


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
    authority = resolve_report_audit_authority()
    active_db = authority.database_path
    policy = authority.policy_path
    authority_before = authority_snapshot(authority)
    active_before = {
        "db_sha": sha256(active_db),
        "db_size": active_db.stat().st_size,
        "db_mtime_ns": active_db.stat().st_mtime_ns,
        "audit_log": db_count(active_db, "audit_log"),
        "policy_sha": sha256(policy),
        "policy_size": policy.stat().st_size,
        "policy_mtime_ns": policy.stat().st_mtime_ns,
    }
    failures += 0 if record("active DB continuity SHA", active_before["db_sha"] == REQUIRED_DB_SHA, active_before) else 1
    failures += 0 if record("active audit baseline", active_before["audit_log"] == REQUIRED_AUDIT_COUNT, active_before["audit_log"]) else 1
    failures += 0 if record("policy continuity SHA", active_before["policy_sha"] == REQUIRED_POLICY_SHA, active_before["policy_sha"]) else 1

    with tempfile.TemporaryDirectory(prefix="trustee_25am_pdf_", ignore_cleanup_errors=True) as tmp:
        temporary_root = Path(tmp).resolve()
        clone = temporary_root / "step25am_reports_clone.db"
        sqlite_read_only_backup(active_db, clone)
        failures += 0 if record("clone isolated in temporary directory", clone.parent == temporary_root) else 1
        failures += 0 if record("clone differs from operational database", clone.resolve() != active_db.resolve()) else 1
        failures += 0 if record("clone outside source repository", not clone.resolve().is_relative_to(ROOT.resolve())) else 1
        failures += 0 if record("clone outside operational repository", not clone.resolve().is_relative_to(authority.repository_root.resolve())) else 1
        os.environ["DB_PATH"] = str(clone)
        source_logical = logical_equivalence_snapshot(active_db)
        clone_logical_before = logical_equivalence_snapshot(clone)
        info("source database SHA", source_logical["sha"])
        info("SQLite backup clone SHA", clone_logical_before["sha"])
        info("clone byte identity", "SAME" if source_logical["sha"] == clone_logical_before["sha"] else "DIFFERENT_EXPECTED")
        info("source schema_version", source_logical["schema_version"])
        info("clone schema_version", clone_logical_before["schema_version"])
        info("schema_version identity", "NOT_REQUIRED")
        logical_failures = logical_equivalence_failures(source_logical, clone_logical_before)
        failures += 0 if record("source and clone logical equivalence", not logical_failures, logical_failures) else 1
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
        clone_logical_after = logical_equivalence_snapshot(clone)
        clone_changes = clone_preservation_failures(clone_logical_before, clone_logical_after)
        failures += 0 if record("clone logical state unchanged", not clone_changes, clone_changes) else 1

    active_after = {
        "db_sha": sha256(active_db),
        "db_size": active_db.stat().st_size,
        "db_mtime_ns": active_db.stat().st_mtime_ns,
        "audit_log": db_count(active_db, "audit_log"),
        "policy_sha": sha256(policy),
        "policy_size": policy.stat().st_size,
        "policy_mtime_ns": policy.stat().st_mtime_ns,
    }
    failures += 0 if record("ACTIVE_UNCHANGED=True", active_after == active_before, {"before": active_before, "after": active_after}) else 1
    failures += 0 if record("POLICY_UNCHANGED=True", active_after["policy_sha"] == REQUIRED_POLICY_SHA and active_after["policy_mtime_ns"] == active_before["policy_mtime_ns"], active_after) else 1
    try:
        assert_snapshot_unchanged(authority_before, authority_snapshot(authority))
        authority_unchanged = True
    except OperationalAuthorityError:
        authority_unchanged = False
    failures += 0 if record("OPERATIONAL_AUTHORITY_UNCHANGED=True", authority_unchanged) else 1

    print("STEP 25AM REPORTS PDF RUNTIME REPAIR AUDIT")
    print("RESULT:", "PASS" if failures == 0 else "FAIL")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
