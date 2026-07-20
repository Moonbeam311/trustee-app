from __future__ import annotations

import hashlib
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OPERATIONAL_ROOT = Path(os.environ.get("TRUSTEE_OPERATIONAL_REPO", ""))
SOURCE_DB = ROOT / "trustee_app.db"
REQUIRED_OPERATIONAL_SHA = "7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525"
FORBIDDEN = ("<sqlite3.Row object", "sqlite3.Row")
MEMORY_ADDRESS = re.compile(r"0x[0-9a-fA-F]{6,}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def record(label: str, ok: bool, detail: object = "") -> bool:
    print(("PASS" if ok else "FAIL") + f" - {label}" + (f" | {detail}" if detail != "" else ""))
    return ok


def make_rows() -> tuple[sqlite3.Connection, list[sqlite3.Row]]:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute(
        """
        CREATE TABLE audit_log (
            created_at TEXT,
            entity_type TEXT,
            entity_id TEXT,
            action TEXT,
            note TEXT
        )
        """
    )
    con.executemany(
        "INSERT INTO audit_log VALUES (?, ?, ?, ?, ?)",
        [
            ("2026-07-19 20:00:00", "trust", "TR-022", "viewed", "Stable audit detail"),
            (None, "auth", None, "login_success", None),
        ],
    )
    return con, con.execute("SELECT * FROM audit_log ORDER BY rowid").fetchall()


def visible_cell_text(value: object) -> str:
    if hasattr(value, "getPlainText"):
        return value.getPlainText()
    if value is None:
        return ""
    return str(value)


def table_payload(story: list[object]) -> list[list[str]]:
    tables = [item for item in story if hasattr(item, "_cellvalues")]
    if not tables:
        raise AssertionError("audit story contains no table payload")

    return [
        [visible_cell_text(value) for value in row]
        for row in tables[-1]._cellvalues
    ]


def install_admin_session(client) -> None:
    with client.session_transaction() as session:
        session.clear()
        session["username"] = "admin123"
        session["role"] = "Admin"
        session["user_role"] = "Admin"
        session["firm_id"] = "FIRM-002"
        session["last_activity"] = datetime.now(UTC).timestamp()


def extract_pdf_text(pdf_path: Path) -> str:
    executable = shutil.which("pdftotext")
    if not executable:
        raise RuntimeError("pdftotext is required for the focused audit PDF text regression")
    result = subprocess.run(
        [executable, "-layout", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout


def main() -> int:
    failures = 0
    failures += 0 if record("source repository remains source-only", not SOURCE_DB.exists()) else 1
    operational_db = OPERATIONAL_ROOT / "trustee_app.db"
    failures += 0 if record("explicit operational authority exists", operational_db.is_file(), operational_db) else 1
    if failures:
        return 1
    operational_before = (sha256(operational_db), operational_db.stat().st_mtime_ns)
    failures += 0 if record("operational authority SHA is exact", operational_before[0] == REQUIRED_OPERATIONAL_SHA, operational_before[0]) else 1

    from pdf_utils import audit_log_report_story

    con, fixture_rows = make_rows()
    try:
        story = audit_log_report_story(fixture_rows)
    finally:
        con.close()
    payload = table_payload(story)
    expected = [
        ["When", "Entity Type", "Entity ID", "Action", "Details"],
        ["2026-07-19 20:00:00", "trust", "TR-022", "viewed", "Stable audit detail"],
        ["", "auth", "", "login_success", ""],
    ]
    failures += 0 if record("sqlite3.Row fields populate ordered audit columns", payload == expected, payload) else 1
    payload_text = "\n".join(str(value) for row in payload for value in row)
    failures += 0 if record("payload contains no sqlite row representation", not any(token in payload_text for token in FORBIDDEN), payload_text) else 1
    failures += 0 if record("payload contains no raw memory address", not MEMORY_ADDRESS.search(payload_text), payload_text) else 1
    try:
        audit_log_report_story([object()])
        malformed_rejected = False
    except TypeError:
        malformed_rejected = True
    failures += 0 if record("ambiguous non-mapping rows fail clearly", malformed_rejected) else 1

    with tempfile.TemporaryDirectory(prefix="system1c_r1_audit_pdf_", ignore_cleanup_errors=True) as tmp:
        tmp_path = Path(tmp)
        clone = tmp_path / "audit_report_clone.db"
        with sqlite3.connect(f"file:{operational_db.as_posix()}?mode=ro", uri=True) as source:
            with sqlite3.connect(clone) as target:
                source.backup(target)
        clone_before = (sha256(clone), clone.stat().st_mtime_ns)
        os.environ["DB_PATH"] = str(clone)
        os.environ["UPLOAD_FOLDER"] = str(tmp_path / "uploads")
        os.environ["EXPORT_ROOT"] = str(tmp_path / "exports")

        from app import app

        client = app.test_client()
        install_admin_session(client)
        response = client.get("/reports/audit.pdf")
        body = response.get_data()
        pdf_path = tmp_path / "audit.pdf"
        pdf_path.write_bytes(body)
        pdf_text = extract_pdf_text(pdf_path)
        failures += 0 if record("audit PDF HTTP 200", response.status_code == 200, response.status_code) else 1
        failures += 0 if record("audit PDF content type", "application/pdf" in (response.headers.get("Content-Type") or ""), response.headers.get("Content-Type")) else 1
        failures += 0 if record("audit PDF signature and size", body.startswith(b"%PDF-") and len(body) > 1000, len(body)) else 1
        failures += 0 if record("audit PDF text has expected headings", all(value in pdf_text for value in ("When", "Entity Type", "Entity ID", "Action", "Details"))) else 1
        failures += 0 if record("audit PDF text contains real audit values", "login_success" in pdf_text and "auth" in pdf_text, pdf_text[:500]) else 1
        failures += 0 if record("audit PDF text contains no sqlite row representation", not any(token in pdf_text for token in FORBIDDEN)) else 1
        failures += 0 if record("audit PDF text contains no raw memory address", not MEMORY_ADDRESS.search(pdf_text)) else 1
        failures += 0 if record("read-only route leaves clone unchanged", (sha256(clone), clone.stat().st_mtime_ns) == clone_before) else 1

    operational_after = (sha256(operational_db), operational_db.stat().st_mtime_ns)
    failures += 0 if record("authoritative operational DB unchanged", operational_after == operational_before, {"before": operational_before, "after": operational_after}) else 1
    failures += 0 if record("source DB remains absent", not SOURCE_DB.exists()) else 1
    print("SYSTEM-1C-R1 AUDIT REPORT ROW NORMALIZATION REGRESSION")
    print("RESULT:", "PASS" if failures == 0 else "FAIL")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
