from __future__ import annotations

import importlib
import os
import re
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from werkzeug.security import generate_password_hash


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_BRANCHES = {
    "system-1-annual-evaluation",
    "hos-web-1e3-publication-safe",
}
EXPECTED_BASE_ANCESTOR = "74498ceb8180a0f21ae73b9e1d2604fc6b81b6a5"
ALLOWED_CHANGED_PATHS = {
    "app.py",
    "database/db.py",
    "database/migrations_intake_trust_bridge.py",
    "docs/tpd_ir_2_contract_inheritance_reverification.md",
    "routes_tpd1c.py",
    "services/services_intake_trust_bridge.py",
    "templates/admin_index.html",
    "templates/auth/login.html",
    "templates/trust_formation_preview_hub.html",
    "tests/test_tpd1c_bridge_continuity.py",
    "tests/test_tpd1c_routes.py",
    "tests/test_tpd_ir_1c_firm_identity.py",
    "static/branding/hindsfoot_os.css",
    "static/branding/hindsfoot_os_logo.png",
    "static/branding/",
    "templates/product_introduction.html",
    "templates/tpd1c/bridge_detail.html",
    "tests/test_hos_brand_1.py",
    "docs/v3_1_admin_command_center_reconstruction.md",
    "scripts/audit_v3_1_admin_command_center_reconstruction.py",
}


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8"
    ).strip()


def record(label: str, condition: bool, detail: object = "") -> None:
    print(f"{'PASS' if condition else 'FAIL'} - {label} | {detail}")
    if not condition:
        failures.append(label)


failures: list[str] = []
record("repository root", ROOT == Path.cwd().resolve(), ROOT)
record("target branch", git("branch", "--show-current") in ALLOWED_BRANCHES)
record(
    "verified baseline ancestry",
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", EXPECTED_BASE_ANCESTOR, "HEAD"],
        cwd=ROOT,
        check=False,
    ).returncode
    == 0,
)
record("staged files absent", not git("diff", "--cached", "--name-only"))

status_output = subprocess.check_output(
    ["git", "status", "--short"], cwd=ROOT, text=True, encoding="utf-8"
)
status_paths = {
    line[3:].replace("\\", "/")
    for line in status_output.splitlines()
    if line
}
record("bounded consolidated inventory", status_paths <= ALLOWED_CHANGED_PATHS, sorted(status_paths))
record("database excluded from changes", not any(path.endswith(".db") for path in status_paths))

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

app_text = (ROOT / "app.py").read_text(encoding="utf-8")
record("recent activity bounded", "get_audit_log(8)" in app_text)
record("TPD lifecycle guard preserved", "enforce_bridge_draft_lifecycle" in app_text)
record("Hindsfoot introduction preserved", 'render_template("product_introduction.html")' in app_text)
record("protected restore action absent", "/admin/recovery/restore" not in template)
record("protected reset action absent", "/admin/recovery/reset" not in template)

with tempfile.TemporaryDirectory(
    prefix="hos_brand_1e_v3_audit_", ignore_cleanup_errors=True
) as temporary:
    temporary_root = Path(temporary)
    os.environ["DB_PATH"] = str(temporary_root / "v3-admin.db")
    os.environ["UPLOAD_FOLDER"] = str(temporary_root / "uploads")
    os.environ["EXPORT_ROOT"] = str(temporary_root / "exports")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.path.insert(0, str(ROOT))
    for name in ("app", "routes_tpd1c", "database.db"):
        sys.modules.pop(name, None)

    module = importlib.import_module("app")
    database = importlib.import_module("database.db")
    module.app.config.update(TESTING=True, SECRET_KEY="v3-1-consolidation-audit")
    database.ensure_user_tables()
    database.ensure_role_tables()
    database.reseed_default_role_permissions()
    database.create_app_user({
        "user_id": database.get_next_user_id(),
        "username": "v3-audit-admin",
        "password_hash": generate_password_hash("audit-only-not-a-browser-credential"),
        "role_name": "Admin",
        "status": "Active",
        "firm_id": "FIRM-002",
    })
    database.create_app_user({
        "user_id": database.get_next_user_id(),
        "username": "v3-audit-trustee",
        "password_hash": generate_password_hash("audit-only-not-a-browser-credential"),
        "role_name": "Trustee",
        "status": "Active",
        "firm_id": "FIRM-002",
    })

    client = module.app.test_client()
    unauthenticated = client.get("/admin")
    record("unauthenticated Admin protected", unauthenticated.status_code in {302, 401, 403}, unauthenticated.status_code)

    with client.session_transaction() as session:
        session.clear()
        session.update({
            "username": "v3-audit-trustee",
            "role": "Trustee",
            "firm_id": "FIRM-002",
            "last_activity": datetime.now(UTC).timestamp(),
        })
    trustee = client.get("/admin")
    record("Trustee denied Admin", trustee.status_code == 403, trustee.status_code)

    with client.session_transaction() as session:
        session.clear()
        session.update({
            "username": "v3-audit-admin",
            "role": "Admin",
            "firm_id": "FIRM-002",
            "last_activity": datetime.now(UTC).timestamp(),
        })
    response = client.get("/admin")
    body = response.get_data(as_text=True)
    record("authorized Admin returns HTTP 200", response.status_code == 200, response.status_code)
    record("V3-1 title rendered", "Institutional Command Center" in body)
    record("firm context visible", "FIRM-002" in body)
    record("operator role visible", "Admin" in body)
    record("raw sqlite row absent", "sqlite3.Row" not in body and "<sqlite3.Row" not in body)
    record("memory address absent", re.search(r"0x[0-9a-fA-F]{8,}", body) is None)

    ids = re.findall(r'\bid=["\']([^"\']+)["\']', body)
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    record("no duplicate HTML IDs", not duplicates, duplicates)

    adapter = module.app.url_map.bind("localhost")
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

    generated_files = [path for path in temporary_root.rglob("*") if path.is_file()]
    record("runtime files isolated", all(temporary_root in path.parents for path in generated_files))

diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=False)
record("git diff check", diff_check.returncode == 0, diff_check.returncode)

print("\nV3-1 ADMIN COMMAND CENTER CONSOLIDATION AUDIT")
print(f"RESULT: {'PASS' if not failures else 'FAIL'}")
if failures:
    print("FAILURES: " + ", ".join(failures))
raise SystemExit(0 if not failures else 1)
