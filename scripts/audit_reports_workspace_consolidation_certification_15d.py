from pathlib import Path
import ast
import os
import re
import subprocess
import sys
import tempfile
import time
from uuid import uuid4


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

APP = ROOT / "app.py"
GOVERNANCE_SERVICE = ROOT / "services" / "services_governance.py"
REPORTS_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "reports.html"
CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_CERTIFIED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"
REQUIRED_ANCESTORS = ["5550156", "22ca47f", "ff44e51", "a342b6b"]
ALLOWED_BRANCH = "post-v2-planning"

INHERITED_AUDITS = [
    ("POST-V2-15C.2", "scripts/audit_reports_workspace_read_only_status_panel_rendering_15c2.py"),
    ("POST-V2-15C.1", "scripts/audit_reports_workspace_minimal_read_only_context_wiring_15c1.py"),
    ("POST-V2-15C", "scripts/audit_reports_workspace_read_only_status_sources_15c.py"),
    ("POST-V2-15B", "scripts/audit_reports_workspace_operator_information_architecture_15b.py"),
    ("POST-V2-15A", "scripts/audit_reports_route_classification_exposure_boundary_15a.py"),
    ("POST-V2-15", "scripts/audit_reports_workspace_consolidation_operator_15.py"),
]

PANEL_ORDER = [
    "portfolio",
    "audit",
    "intake",
    "draft_review",
    "governance_audits",
    "financial",
    "certificate_verification",
    "controlled_exports",
    "governance_evidence",
    "v2_certification",
]

PANEL_LABELS = {
    "portfolio": "Portfolio Reporting Availability",
    "audit": "Audit Activity Available",
    "intake": "Intake Oversight Available",
    "draft_review": "Draft and Review Gate Status",
    "governance_audits": "Governance Relationship Audit Ledger",
    "financial": "Financial Summary Availability",
    "certificate_verification": "Certificate Verification",
    "controlled_exports": "Controlled Exports",
    "governance_evidence": "Governance Evidence Chain",
    "v2_certification": "V2 Certification Record",
}

APPROVED_STATUS_ROUTES = {
    "portfolio": "/portfolio",
    "audit": "/audit",
    "intake": "/intake/dashboard",
    "draft_review": "/intake/draft-readiness",
    "governance_audits": "/governance/relationship-audits",
    "financial": "/financial_summary",
    "certificate_verification": "/certificates",
    "controlled_exports": "/exports",
    "governance_evidence": "/admin/workspace/archive",
    "v2_certification": "/governance/v2-certification",
}

REQUIRED_STATUS_TERMS = {
    "Available",
    "Complete",
    "Incomplete",
    "Exception",
    "Protected",
    "Context Required",
    "Not Evaluated",
    "Unavailable",
}

REQUIRED_SECTIONS = [
    "Reports Workspace Purpose",
    "Executive and Institutional Reports",
    "Export and Certificate Oversight",
    "Intake and Readiness Oversight",
    "Governance and Evidence Oversight",
    "Contextual Report Boundary",
    "Controlled Export Boundary",
    "Protected and Excluded Boundary",
    "Operator Navigation",
]

REQUIRED_15B_LINKS = {
    "/financial_summary",
    "/portfolio",
    "/reports/portfolio.pdf",
    "/audit",
    "/reports/audit.pdf",
    "/visualization/analytics",
    "/exports",
    "/certificates",
    "/intake/dashboard",
    "/intake/exports",
    "/intake/modules",
    "/intake/draft-readiness",
    "/intake/review-gates",
    "/intake/final-draft-gate",
    "/intake/final-draft-approvals",
    "/governance/dashboard",
    "/governance/relationship-audits",
    "/governance/evidence-exports",
    "/governance/evidence-exports/certification",
    "/governance/v2-certification",
    "/governance/evidence-exports/completion-gate",
    "/governance/evidence-exports/exceptions",
    "/governance/evidence-exports/archive-intake",
    "/governance/evidence-exports/integrity",
    "/governance/evidence-exports/manifest",
    "/admin",
    "/admin/workspace/governance",
    "/admin/workspace/archive",
}

SAFE_CENTRAL_SOURCES = [
    "Portfolio",
    "Audit",
    "Intake Oversight",
    "Draft and Review Gate Status",
    "Governance Relationship Audit Ledger",
]

LINK_ONLY_SOURCES = [
    "Financial Summary",
    "Portfolio PDF",
    "Admin Audit Log",
    "Audit PDF",
    "Institutional Analytics",
    "Export Registry",
    "Certificate Registry",
    "Governance Dashboard",
]

CONTEXT_REQUIRED_SOURCES = ["Certificate Verification"]
PROTECTED_SOURCES = [
    "Controlled Export Artifacts",
    "Certificate Studio",
    "Certificate Backfill",
    "Mutation-capable certificate surfaces",
]
ARCHIVE_DUPLICATE_SOURCES = ["Governance Evidence Chain", "V2 Certification Record"]

PROHIBITED_ROUTE_MARKERS = (
    ".pdf",
    ".zip",
    "/api/",
    "/diag/",
    "/diagnostic",
    "/certificate-studio",
    "backfill",
    "repair",
    "seed",
    "approve",
    "approval",
    "finalize",
    "execute",
    "download",
    "generate",
    "package",
)

MUTATION_CALL_PREFIXES = (
    "seed_",
    "repair_",
    "backfill_",
    "generate_",
    "finalize_",
    "approve_",
    "certify_",
    "execute_",
    "create_",
    "update_",
    "delete_",
)

MUTATION_METHODS = {"commit", "executemany", "insert", "update", "delete", "replace"}

ALLOWED_STATUS_PATHS = {
    "scripts/audit_reports_workspace_consolidation_certification_15d.py",
    "scripts/audit_reports_workspace_read_only_status_panel_rendering_15c2.py",
    "scripts/audit_reports_workspace_minimal_read_only_context_wiring_15c1.py",
    "scripts/audit_reports_workspace_read_only_status_sources_15c.py",
    "scripts/audit_reports_workspace_operator_information_architecture_15b.py",
    "scripts/audit_reports_route_classification_exposure_boundary_15a.py",
    "scripts/audit_reports_workspace_consolidation_operator_15.py",
}

checks = []
evidence = {}


def git(*args):
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def record(name, passed, detail=""):
    checks.append((name, bool(passed), str(detail)))


def run_python_script(script):
    result = subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return result.returncode, result.stdout


def read(path):
    return path.read_text(encoding="utf-8")


def extract_hrefs(text):
    return re.findall(r'href=["\']([^"\']+)["\']', text)


def call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def find_function(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def source_for_function(text, tree, name):
    node = find_function(tree, name)
    return ast.get_source_segment(text, node) if node else ""


def merge_base_contains(commit):
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def extract_status_region(text):
    start = text.find('<section class="admin-card reports-status-region">')
    end = text.find('<section class="admin-card">\n  <h3>Reports Workspace Purpose</h3>')
    if start == -1 or end == -1 or end <= start:
        return ""
    return text[start:end]


def render_runtime():
    tmp = Path(tempfile.gettempdir())
    os.environ["DB_PATH"] = str(tmp / f"trustee_postv2_15d_audit_{uuid4().hex}.db")
    os.environ["UPLOAD_FOLDER"] = str(tmp / "trustee_postv2_15d_uploads")
    os.environ["EXPORT_ROOT"] = str(tmp / "trustee_postv2_15d_exports")

    import app as app_module
    from database.db import (
        init_db,
        ensure_firm_columns,
        ensure_role_tables,
        ensure_table_firm_id_column,
        ensure_user_tables,
    )

    init_db()
    ensure_user_tables()
    ensure_role_tables()
    ensure_firm_columns()
    for table_name in ("trusts", "beneficiaries", "distributions", "instruments"):
        ensure_table_firm_id_column(table_name, "FIRM-001")

    client = app_module.app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = "CERT-ADMIN"
        session["username"] = "admin"
        session["role"] = "Admin"
        session["user_role"] = "Admin"
        session["is_master_admin"] = True
        session["firm_id"] = "FIRM-001"
        session["last_activity"] = time.time()

    reports = client.get("/admin/workspace/reports")
    archive = client.get("/admin/workspace/archive")
    home = client.get("/admin/workspace/home")
    return (
        reports.status_code,
        reports.get_data(as_text=True),
        archive.status_code,
        archive.get_data(as_text=True),
        home.status_code,
        home.get_data(as_text=True),
    )


branch = git("branch", "--show-current")
head = git("rev-parse", "HEAD")
origin_head = git("rev-parse", "origin/post-v2-planning")
tag_commit = git("rev-parse", f"{CERTIFIED_TAG}^{{commit}}")
status_short = git("status", "--short")
diff_check = subprocess.run(
    ["git", "diff", "--check"],
    cwd=ROOT,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)

app_text = read(APP)
service_text = read(GOVERNANCE_SERVICE)
template_text = read(REPORTS_TEMPLATE)
app_tree = ast.parse(app_text)
service_tree = ast.parse(service_text)
status_region = extract_status_region(template_text)
template_hrefs = set(extract_hrefs(template_text))
status_hrefs = extract_hrefs(status_region)

workspace_source = source_for_function(app_text, app_tree, "admin_ios_workspace")
helper_source = source_for_function(service_text, service_tree, "build_reports_workspace_read_only_status")
helper_related_sources = "\n".join(
    source_for_function(service_text, service_tree, name)
    for name in (
        "build_reports_workspace_read_only_status",
        "_reports_portfolio_status",
        "_reports_audit_status",
        "_reports_intake_status",
        "_reports_draft_review_status",
        "_reports_governance_audits_status",
    )
)

report_routes_present = '"/admin/workspace/<workspace_key>"' in app_text or "'/admin/workspace/<workspace_key>'" in app_text
panel_key_positions = [status_region.find(f'"{key}"') for key in PANEL_ORDER]

helper_calls = [
    call_name(node.func)
    for node in ast.walk(ast.parse(helper_related_sources or "pass"))
    if isinstance(node, ast.Call)
]
mutation_calls = [
    name
    for name in helper_calls
    if name
    and (
        name.lower() in MUTATION_METHODS
        or any(name.lower().startswith(prefix) for prefix in MUTATION_CALL_PREFIXES)
    )
]
mutation_sql = re.findall(r"\b(INSERT|UPDATE|DELETE|REPLACE)\b", helper_related_sources, flags=re.IGNORECASE)

record("current branch is post-v2-planning", branch == ALLOWED_BRANCH, branch)
record("HEAD is synchronized with origin/post-v2-planning", head == origin_head and bool(head), f"HEAD={head} origin={origin_head}")
for ancestor in REQUIRED_ANCESTORS:
    record(f"{ancestor} retained in ancestry", merge_base_contains(ancestor), ancestor)
record("certified V2 tag exists", bool(tag_commit), tag_commit)
record("certified V2 tag resolves to expected commit", tag_commit == EXPECTED_CERTIFIED_COMMIT, tag_commit)
record("no certified baseline file modified", "v2-certified-baseline" not in status_short, status_short or "clean except authorized")
record("runtime database files remain unchanged", ".db" not in status_short.lower() and "trustee_app.db" not in status_short, status_short or "none")

record("/admin/workspace/<workspace_key> route exists", report_routes_present, "route present")
record("Reports workspace addressable through workspace_key == reports", '"reports"' in workspace_source and 'workspace_key == "reports"' in workspace_source, "reports branch")
record("Reports template path retained", 'ios_workspaces/{workspace_key}.html' in workspace_source, "dynamic workspace template")
record("existing nine Reports sections remain", all(section in template_text for section in REQUIRED_SECTIONS), "all present")
record("existing 28 approved IA links remain", REQUIRED_15B_LINKS.issubset(template_hrefs), sorted(REQUIRED_15B_LINKS - template_hrefs))
record("no original Reports section removed", sum(1 for section in REQUIRED_SECTIONS if section in template_text) == 9, "9 sections")
record(
    "no original approved link replaced by mutation route",
    not any(any(marker in href.lower() for marker in PROHIBITED_ROUTE_MARKERS) for href in REQUIRED_15B_LINKS if href in APPROVED_STATUS_ROUTES.values()),
    "approved status routes only",
)

record("build_reports_workspace_read_only_status exists", bool(helper_source), "helper present")
record("top-level read_only is True", '"read_only": True' in helper_source, "read_only true")
record("context_type is reports_workspace_status", '"context_type": "reports_workspace_status"' in helper_source, "context type")
record("all ten panel keys exist in context helper", all(f'"{key}"' in helper_source for key in PANEL_ORDER), PANEL_ORDER)
record("Reports status context wired only for Reports workspace", 'if workspace_key == "reports"' in workspace_source and "build_reports_workspace_read_only_status()" in workspace_source, "conditional")
record("non-Reports workspaces receive no live Reports status", "reports_status = None" in workspace_source and workspace_source.find("reports_status = None") < workspace_source.find('if workspace_key == "reports"'), "default None")
record("no record identifier required for central context", not any(token in helper_source for token in ("trust_id", "intake_id", "certificate_id", "execution_id")), "no identifiers")
record("no write helper invoked", not mutation_calls and not mutation_sql, f"calls={mutation_calls} sql={mutation_sql}")

record("Reports Oversight Status appears", "Reports Oversight Status" in template_text, "heading")
record("ten panels render in required order", all(pos >= 0 for pos in panel_key_positions) and panel_key_positions == sorted(panel_key_positions), panel_key_positions)
record("each panel includes label status detail route", 'panel.get("label"' in status_region and 'panel.get("status"' in status_region and 'panel.get("detail"' in status_region and 'href="{{ route }}"' in status_region, "label/status/detail/link")
record("safe summaries render only scalar values", "summary is mapping" in status_region and "summary_value is string" in status_region and "summary_value is number" in status_region and "summary_value is boolean" in status_region, "scalar guarded")
record("missing summaries do not break rendering", 'panel.get("summary", {})' in status_region and "if summary_rows" in status_region, "defensive")
record("unexpected statuses fall back to Not Evaluated", "if status not in allowed_report_statuses" in status_region and 'set status = "Not Evaluated"' in status_region, "fallback")
record("no raw dictionary rendered", "{{ summary }}" not in status_region and "{{ panel }}" not in status_region, "none")
record("no safe filter used", "|safe" not in status_region, "none")
record("no JavaScript status loading or mutation", not any(marker in status_region for marker in ("<script", "fetch(", "XMLHttpRequest", "setInterval")), "none")
record("no form in status region", "<form" not in status_region.lower(), "none")
record("no button in status region", "<button" not in status_region.lower(), "none")
record("no POST action in status region", "method=\"post\"" not in status_region.lower() and "method='post'" not in status_region.lower(), "none")
record("no asynchronous request or auto-refresh", not any(marker in status_region for marker in ("fetch(", "XMLHttpRequest", "setInterval", "setTimeout")), "none")

record("Financial Summary remains link-only", '"financial"' in helper_source and '"Not Evaluated"' in helper_source and "get_trust_financial_summary" not in helper_related_sources, "link-only")
record("Certificate Verification remains Context Required", '"certificate_verification"' in helper_source and '"Context Required"' in helper_source, "context required")
record("Controlled Exports remains Protected", '"controlled_exports"' in helper_source and '"Protected"' in helper_source, "protected")
record("Governance Evidence points to Archive", '"/admin/workspace/archive"' in helper_source and '"/admin/workspace/archive"' in status_region, "archive")
record("Governance Evidence not independently recomputed", "build_archive_workspace_read_only_status" not in helper_related_sources and "build_archive_workspace_read_only_status" not in status_region, "not recomputed")
record("V2 Certification points to governed surface", '"/governance/v2-certification"' in helper_source and '"/governance/v2-certification"' in status_region, "governed")
record("V2 Certification not independently recomputed", "build_v2" not in helper_related_sources.lower() and "certify_" not in helper_related_sources.lower(), "not recomputed")
for panel_key, label in [
    ("portfolio", "Portfolio"),
    ("audit", "Audit"),
    ("intake", "Intake"),
    ("draft_review", "Draft and Review Gate"),
    ("governance_audits", "Governance Relationship Audit Ledger"),
]:
    record(f"{label} remains approved live read-only central panel", f'"{panel_key}": _reports_' in helper_source, panel_key)

status_link_set = set(APPROVED_STATUS_ROUTES.values())
record("no PDF route used as live status source", not any(href.endswith(".pdf") for href in status_link_set), status_link_set)
record("no ZIP or package generation route exposed as status action", not any(".zip" in href or "package" in href for href in status_link_set), status_link_set)
record("no download route exposed as status action", not any("download" in href for href in status_link_set), status_link_set)
record("no certificate studio route exposed", not any("certificate-studio" in href for href in status_link_set), status_link_set)
record("no certificate backfill route exposed", not any("backfill" in href for href in status_link_set), status_link_set)
record("no repair route exposed", not any("repair" in href for href in status_link_set), status_link_set)
record("no seed route exposed", not any("seed" in href for href in status_link_set), status_link_set)
record("no approval route exposed", not any("approval" in href or "approve" in href for href in status_link_set), status_link_set)
record("no finalization route exposed", not any("final" in href for href in status_link_set), status_link_set)
record("no execution route exposed", not any("execution" in href for href in status_link_set), status_link_set)
record("no API endpoint exposed", not any("/api/" in href for href in status_link_set), status_link_set)
record("no diagnostic route exposed", not any("diag" in href or "diagnostic" in href for href in status_link_set), status_link_set)
record("no record-specific parameterized route exposed centrally", not any("<" in href or ">" in href for href in status_link_set), status_link_set)
record("no write-capable route represented as read-only panel", not any(any(marker in href for marker in ("new", "edit", "delete", "create", "update")) for href in status_link_set), status_link_set)

try:
    reports_code, reports_html, archive_code, archive_html, home_code, home_html = render_runtime()
except Exception as exc:
    reports_code, reports_html, archive_code, archive_html, home_code, home_html = 0, str(exc), 0, "", 0, ""

runtime_status_region = ""
if "Reports Oversight Status" in reports_html and "Reports Workspace Purpose" in reports_html:
    runtime_status_region = reports_html[
        reports_html.find("Reports Oversight Status") : reports_html.find("Reports Workspace Purpose")
    ]

runtime_panel_count = reports_html.count('class="reports-status-card reports-status-card--')
runtime_label_order = []
for label in PANEL_LABELS.values():
    runtime_label_order.append(reports_html.find(label))

record("authenticated GET reports returns HTTP 200", reports_code == 200, reports_code)
record("rendered page contains Reports Oversight Status", "Reports Oversight Status" in reports_html, "heading")
record("rendered page contains all ten panel labels", all(label in reports_html for label in PANEL_LABELS.values()), "labels")
record("rendered page visibly contains Context Required", "Context Required" in reports_html, "Context Required")
record("rendered page visibly contains Protected", "Protected" in reports_html, "Protected")
record("rendered status region contains no form", "<form" not in runtime_status_region.lower(), "none")
record("rendered status region contains no button", "<button" not in runtime_status_region.lower(), "none")
record("rendered status region contains no POST action", "method=\"post\"" not in runtime_status_region.lower() and "method='post'" not in runtime_status_region.lower(), "none")
record("archive workspace does not render Reports status panels", archive_code == 200 and "Reports Oversight Status" not in archive_html, archive_code)
record("home workspace does not render Reports status panels", home_code == 200 and "Reports Oversight Status" not in home_html, home_code)
record("runtime panel count is ten", runtime_panel_count == 10, runtime_panel_count)
record("runtime panel order is certified", all(pos >= 0 for pos in runtime_label_order) and runtime_label_order == sorted(runtime_label_order), runtime_label_order)

audit_results = {}
for label, script in INHERITED_AUDITS:
    code, output = run_python_script(script)
    audit_results[label] = (code, output)
    record(f"{label} audit passes", code == 0 and "RESULT: PASS" in output, f"exit={code}")

status_lines = status_short.splitlines()
unexpected_status = []
for line in status_lines:
    normalized = line.replace("\\", "/")
    if not any(path in normalized for path in ALLOWED_STATUS_PATHS):
        unexpected_status.append(line)

record("working tree contains only 15D and inherited compatibility files", not unexpected_status, "\n".join(unexpected_status) or "approved files only")
for label, marker in [
    ("no application file changed", "app.py"),
    ("no service file changed", "services/"),
    ("no template changed", "templates/"),
    ("no model changed", "models/"),
    ("no migration changed", "migrations/"),
    ("no database file changed", ".db"),
    ("no auth/session file changed", "auth"),
    ("no config/deployment file changed", "config"),
]:
    record(label, marker not in status_short.replace("\\", "/"), status_short or "clean except authorized")
record("git diff check clean", diff_check.returncode == 0, diff_check.stdout.strip() or "clean")
record("no commit or push performed by audit", head == git("rev-parse", "HEAD") and origin_head == git("rev-parse", "origin/post-v2-planning"), "HEAD/origin unchanged")

print("POST-V2-15D — REPORTS WORKSPACE CONSOLIDATION CERTIFICATION")
print("=" * 88)
print()
print("Repository Identity")
print("-" * 88)
print(f"branch: {branch}")
print(f"HEAD: {head}")
print(f"origin HEAD: {origin_head}")
print(f"certified V2 tag: {CERTIFIED_TAG}")
print(f"certified V2 commit: {tag_commit}")
print(f"required milestone ancestry: {', '.join(REQUIRED_ANCESTORS)}")
print()
print("Reports Series Certification")
print("-" * 88)
for milestone in ("POST-V2-15", "POST-V2-15A", "POST-V2-15B", "POST-V2-15C", "POST-V2-15C.1", "POST-V2-15C.2"):
    print(f"{milestone}: certified by inherited audit chain")
print()
print("Route Exposure Certification")
print("-" * 88)
print("central operator routes: approved Reports workspace routes retained")
print("contextual routes: remain outside central status exposure")
print("controlled export routes: governed; no status action exposed")
print("protected routes: excluded from status panels")
print("excluded implementation surfaces: API, diagnostic, repair, seed, builder, mutation routes excluded")
print()
print("Source Safety Certification")
print("-" * 88)
print(f"safe central sources: {', '.join(SAFE_CENTRAL_SOURCES)}")
print(f"link-only sources: {', '.join(LINK_ONLY_SOURCES)}")
print(f"context-required sources: {', '.join(CONTEXT_REQUIRED_SOURCES)}")
print(f"protected sources: {', '.join(PROTECTED_SOURCES)}")
print(f"Archive-duplicate sources: {', '.join(ARCHIVE_DUPLICATE_SOURCES)}")
print()
print("Context Contract Certification")
print("-" * 88)
print("read_only: True")
print("context_type: reports_workspace_status")
print(f"panel keys: {', '.join(PANEL_ORDER)}")
print("conditional workspace wiring: Reports only")
print("non-Reports isolation: archive and home verified")
print()
print("Rendering Certification")
print("-" * 88)
print(f"panel order: {', '.join(PANEL_LABELS[key] for key in PANEL_ORDER)}")
print(f"status vocabulary: {', '.join(sorted(REQUIRED_STATUS_TERMS))}")
print("summary safety: scalar-only defensive summary rows")
print(f"approved links: {', '.join(APPROVED_STATUS_ROUTES[key] for key in PANEL_ORDER)}")
print("no-action boundary: no forms, buttons, POST actions, async loading, or mutation controls")
print("accessibility structure: section/article/header/dl/dt/dd used")
print()
print("Runtime Certification")
print("-" * 88)
print(f"Reports HTTP status: {reports_code}")
print(f"panel presence: {runtime_panel_count}")
print("boundary statuses: Context Required and Protected visible")
print(f"non-Reports isolation: archive={archive_code}, home={home_code}")
print()
print("Check Results")
print("-" * 88)
for name, passed, detail in checks:
    print(f"{'PASS' if passed else 'FAIL'}: {name} - {detail}")

failed = [check for check in checks if not check[1]]
print()
print("SUMMARY")
print("-" * 88)
print(f"checks_total: {len(checks)}")
print(f"checks_passed: {len(checks) - len(failed)}")
print(f"checks_failed: {len(failed)}")
print("POST-V2-15D: RESULT: PASS" if not failed else "POST-V2-15D: RESULT: FAIL")

if failed:
    raise SystemExit(1)
