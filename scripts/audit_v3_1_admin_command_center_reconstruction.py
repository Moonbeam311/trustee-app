from __future__ import annotations

import hashlib
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
OPERATIONAL_DB = ROOT / "trustee_app.db"
POLICY = ROOT / "data" / "export_policy.json"
EXPECTED_BRANCH = "post-v2-successor"
EXPECTED_HEAD = "0047fc053c4dfecaa4103af9b20c3811a0f564ad"
EXPECTED_DB_SHA = "7958cafe5afbed418a093a32dada9e07fca8a87d90a0f3d23bf81c9b1c565525"
EXPECTED_POLICY_SHA = "660ed85445bb8672e2082c410772f53c76d1aa0732ff62a6bfb68b04fe544361"
ALLOWED_PATHS = {
    "app.py",
    "templates/admin_index.html",
    "scripts/audit_v3_1_admin_command_center_reconstruction.py",
    "docs/v3_1_admin_command_center_reconstruction.md",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_snapshot(path: Path) -> tuple[str, int, int]:
    stat = path.stat()
    return sha256(path), stat.st_size, stat.st_mtime_ns


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8"
    ).strip()


def db_facts(path: Path) -> dict[str, object]:
    uri = f"file:{path.as_posix()}?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        return {
            "integrity": connection.execute("PRAGMA integrity_check").fetchone()[0],
            "foreign_keys": len(connection.execute("PRAGMA foreign_key_check").fetchall()),
            "schema_version": connection.execute("PRAGMA schema_version").fetchone()[0],
            "tables": connection.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0],
            "audits": connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0],
            "transfers": connection.execute("SELECT COUNT(*) FROM transfers").fetchone()[0],
        }


def record(label: str, condition: bool, detail: object = "") -> None:
    print(f"{'PASS' if condition else 'FAIL'} - {label} | {detail}")
    if not condition:
        FAILURES.append(label)


FAILURES: list[str] = []
before_db = file_snapshot(OPERATIONAL_DB)
before_policy = file_snapshot(POLICY)
before_facts = db_facts(OPERATIONAL_DB)
sidecars = [Path(f"{OPERATIONAL_DB}{suffix}") for suffix in ("-wal", "-shm", "-journal")]

record("repository root", ROOT == Path.cwd().resolve(), ROOT)
record("successor branch", git("branch", "--show-current") == EXPECTED_BRANCH, git("branch", "--show-current"))
record("starting HEAD", git("rev-parse", "HEAD") == EXPECTED_HEAD, git("rev-parse", "HEAD"))
record("certified tag object", git("rev-parse", "v2-certified-baseline-2026-07-18") == "8ae024087cda06724bb3676960aaf8cdbbba9b67")
record("certified tag commit", git("rev-parse", "v2-certified-baseline-2026-07-18^{commit}") == "e9907e1b9a13cd47c2b0acd4ad06d434c8a4fa46")
record("post-v2-planning preserved", git("rev-parse", "post-v2-planning") == EXPECTED_HEAD)
record("operational database SHA", before_db[0] == EXPECTED_DB_SHA, before_db[0])
record("operational database facts", before_facts == {"integrity": "ok", "foreign_keys": 0, "schema_version": 404, "tables": 132, "audits": 569, "transfers": 14}, before_facts)
record("operational sidecars absent", not any(path.exists() for path in sidecars))
record("policy SHA", before_policy[0] == EXPECTED_POLICY_SHA, before_policy[0])

template_path = ROOT / "templates" / "admin_index.html"
template = template_path.read_text(encoding="utf-8")
required_sections = [
    "Institutional Command Center",
    "Attention and readiness",
    "Create",
    "Administer",
    "Govern",
    "Execute",
    "Document and certify",
    "Preserve",
    "Learn and research",
    "System administration",
    "Continue work",
    "Recent institutional activity",
]
for heading in required_sections:
    record(f"section renders: {heading}", heading in template)

required_entries = [
    "New Intake", "New or Existing Matter", "New Trust", "Trusts", "Portfolio",
    "Property", "Accounts", "Ledger", "Transfers", "Fiduciaries", "Beneficiaries",
    "People", "Genealogy", "Governance Workspace", "Directives", "Decisions",
    "Policies", "Resolutions", "Memoranda", "Opinions", "Precedents", "Signatures",
    "Execution Objects", "Documents", "Certificate Studio", "Certificate Registry",
    "Reports", "Audit", "Archive", "Continuity Assets", "Learning", "Articles",
    "Research", "Media", "Security", "Users", "Roles", "Permissions", "Exports",
    "Developer Tools",
]
for entry in required_entries:
    record(f"entry point preserved: {entry}", f">{entry}<" in template)

record("protected restore action absent", "/admin/recovery/restore" not in template)
record("protected reset action absent", "/admin/recovery/reset" not in template)
record("recent activity bounded", "get_audit_log(8)" in (ROOT / "app.py").read_text(encoding="utf-8"))

status_paths = set()
status_output = subprocess.check_output(
    ["git", "status", "--short"], cwd=ROOT, text=True, encoding="utf-8"
)
for line in status_output.splitlines():
    if line:
        status_paths.add(line[3:].replace("\\", "/"))
record("bounded file inventory", status_paths <= ALLOWED_PATHS, sorted(status_paths))
record("no migration changed", not any("migration" in path.lower() for path in status_paths))

with tempfile.TemporaryDirectory(prefix="v3_1_admin_audit_", ignore_cleanup_errors=True) as temporary:
    clone = Path(temporary) / "trustee_app_v3_1_admin.db"
    shutil.copy2(OPERATIONAL_DB, clone)
    os.environ["DB_PATH"] = str(clone)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.path.insert(0, str(ROOT))

    from app import app  # noqa: E402

    app.config.update(TESTING=True)
    client = app.test_client()
    unauthenticated = client.get("/admin")
    record("unauthenticated Admin protected", unauthenticated.status_code in {302, 401, 403}, unauthenticated.status_code)

    with client.session_transaction() as session:
        session.clear()
        session["username"] = "admin123"
        session["role"] = "Admin"
        session["user_role"] = "Admin"
        session["firm_id"] = "FIRM-002"
        session["is_master_admin"] = True
        session["last_activity"] = datetime.now(UTC).timestamp()
    response = client.get("/admin")
    body = response.get_data(as_text=True)
    record("authorized Admin returns HTTP 200", response.status_code == 200, response.status_code)
    record("firm context visible", "FIRM-002" in body)
    record("operator role visible", "Admin" in body)
    record("raw sqlite row absent", "sqlite3.Row" not in body and "<sqlite3.Row" not in body)
    record("memory address absent", re.search(r"0x[0-9a-fA-F]{8,}", body) is None)

    ids = re.findall(r'\bid=["\']([^"\']+)["\']', body)
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    record("no duplicate HTML IDs", not duplicates, duplicates)

    adapter = app.url_map.bind("localhost")
    broken: list[str] = []
    rendered_paths: list[str] = []
    for href in re.findall(r'href=["\']([^"\']+)["\']', body):
        if href.startswith(("#", "mailto:", "tel:", "javascript:", "http://", "https://")):
            continue
        path = urlsplit(href).path
        rendered_paths.append(path)
        try:
            adapter.match(path, method="GET")
        except Exception:
            broken.append(path)
    record("rendered internal routes resolve", not broken, sorted(set(broken)))
    record("route continuity breadth", len(set(rendered_paths)) >= 50, len(set(rendered_paths)))

    with client.session_transaction() as session:
        session.clear()
        session["username"] = "authorized.user"
        session["role"] = "Viewer"
        session["user_role"] = "Viewer"
        session["firm_id"] = "FIRM-002"
        session["last_activity"] = datetime.now(UTC).timestamp()
    ordinary = client.get("/admin")
    ordinary_body = ordinary.get_data(as_text=True)
    record("ordinary user remains authorization governed", ordinary.status_code in {200, 302, 403}, ordinary.status_code)
    record("system controls hidden from ordinary role", "System administration" not in ordinary_body)
    record("users link hidden from ordinary role", ">Users<" not in ordinary_body)
    record("permissions link hidden from ordinary role", ">Permissions<" not in ordinary_body)

    clone_facts_after = db_facts(clone)
    record("disposable clone remains logically valid", clone_facts_after["integrity"] == "ok" and clone_facts_after["foreign_keys"] == 0, clone_facts_after)

after_db = file_snapshot(OPERATIONAL_DB)
after_policy = file_snapshot(POLICY)
after_facts = db_facts(OPERATIONAL_DB)
record("operational database unchanged", before_db == after_db and before_facts == after_facts)
record("policy unchanged", before_policy == after_policy)
record("operational sidecars remain absent", not any(path.exists() for path in sidecars))

diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=False)
record("git diff check", diff_check.returncode == 0, diff_check.returncode)

print("\nV3-1 ADMIN COMMAND CENTER RECONSTRUCTION AUDIT")
print(f"RESULT: {'PASS' if not FAILURES else 'FAIL'}")
if FAILURES:
    print("FAILURES: " + ", ".join(FAILURES))
raise SystemExit(0 if not FAILURES else 1)
