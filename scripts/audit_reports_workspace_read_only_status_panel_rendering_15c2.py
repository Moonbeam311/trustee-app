from pathlib import Path
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
REPORTS_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "reports.html"
CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_CERTIFIED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"
REQUIRED_ANCESTOR = "ff44e51"
ALLOWED_BRANCHES = {"post-v2-planning"}

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

PROHIBITED_STATUS_LINK_MARKERS = (
    ".pdf",
    ".zip",
    "/api/",
    "/diag/",
    "/diagnostic",
    "/certificate-studio",
    "backfill",
    "repair",
    "approve",
    "approval",
    "finalize",
    "execute",
    "download",
    "generate",
)

PROHIBITED_ACTION_TEXT = (
    "Generate",
    "Run",
    "Execute",
    "Approve",
    "Certify",
    "Download",
    "Build",
    "Repair",
    "Backfill",
    "Finalize",
)

ALLOWED_STATUS_PATHS = {
    "templates/ios_workspaces/reports.html",
    "scripts/audit_reports_workspace_read_only_status_panel_rendering_15c2.py",
    "scripts/audit_reports_workspace_minimal_read_only_context_wiring_15c1.py",
    "scripts/audit_reports_workspace_read_only_status_sources_15c.py",
    "scripts/audit_reports_workspace_operator_information_architecture_15b.py",
    "scripts/audit_reports_route_classification_exposure_boundary_15a.py",
    "scripts/audit_reports_workspace_consolidation_operator_15.py",
}


checks = []


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


def extract_status_region(template_text):
    start = template_text.find('<section class="admin-card reports-status-region">')
    end = template_text.find("<section class=\"admin-card\">\n  <h3>Reports Workspace Purpose</h3>")
    if start == -1 or end == -1 or end <= start:
        return ""
    return template_text[start:end]


def extract_href_values(text):
    return re.findall(r'href=["\']([^"\']+)["\']', text)


branch = git("branch", "--show-current")
head = git("rev-parse", "HEAD")
tag_commit = git("rev-parse", f"{CERTIFIED_TAG}^{{commit}}")
ancestor = subprocess.run(
    ["git", "merge-base", "--is-ancestor", REQUIRED_ANCESTOR, "HEAD"],
    cwd=ROOT,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

template_text = REPORTS_TEMPLATE.read_text(encoding="utf-8")
status_region = extract_status_region(template_text)
template_hrefs = set(extract_href_values(template_text))
status_hrefs = extract_href_values(status_region)

record("correct branch", branch in ALLOWED_BRANCHES, branch)
record("POST-V2-15C.1 retained in ancestry", ancestor.returncode == 0, head)
record("certified V2 tag unchanged", tag_commit == EXPECTED_CERTIFIED_COMMIT, tag_commit)
record("Reports template contains Reports Oversight Status", "Reports Oversight Status" in template_text, "heading present")
record(
    "read-only context contract is checked before rendering",
    'reports_status.get("read_only") == True' in status_region
    and 'reports_status.get("context_type") == "reports_workspace_status"' in status_region,
    "contract guard",
)
record("all ten panel keys represented", all(f'"{key}"' in status_region for key in PANEL_ORDER), PANEL_ORDER)

order_positions = [status_region.find(f'"{key}"') for key in PANEL_ORDER]
record("panel order is correct", all(pos >= 0 for pos in order_positions) and order_positions == sorted(order_positions), order_positions)
record("required status vocabulary is enforced", all(f'"{term}"' in status_region for term in REQUIRED_STATUS_TERMS), sorted(REQUIRED_STATUS_TERMS))
record(
    "unexpected statuses fall back to Not Evaluated",
    "if status not in allowed_report_statuses" in status_region
    and 'set status = "Not Evaluated"' in status_region,
    "fallback present",
)
record(
    "all panels render label, status, detail, and route link",
    'panel.get("label"' in status_region
    and 'panel.get("status"' in status_region
    and 'panel.get("detail"' in status_region
    and 'href="{{ route }}"' in status_region,
    "label/status/detail/link",
)
record(
    "safe summaries are rendered defensively",
    'panel.get("summary", {})' in status_region
    and "summary is mapping" in status_region
    and "summary_value is string" in status_region
    and "summary_value is number" in status_region,
    "defensive scalar summary",
)
record("no raw dictionary rendering", "{{ summary }}" not in status_region and "{{ panel }}" not in status_region, "no raw dict output")
record("no safe filter", "|safe" not in status_region, "none")
record(
    "no service or database calls from Jinja",
    not any(marker in status_region for marker in ("services.", "database.", "get_connection", "build_reports_workspace")),
    "none",
)
record("no forms", "<form" not in status_region.lower(), "none")
record("no buttons", "<button" not in status_region.lower(), "none")
record("no POST actions", "method=\"post\"" not in status_region.lower() and "method='post'" not in status_region.lower(), "none")
record(
    "no JavaScript mutation or async status loading",
    "<script" not in status_region.lower()
    and "fetch(" not in status_region
    and "XMLHttpRequest" not in status_region
    and "setInterval" not in status_region,
    "none",
)
record(
    "no prohibited status links",
    not any(any(marker in href.lower() for marker in PROHIBITED_STATUS_LINK_MARKERS) for href in status_hrefs),
    status_hrefs,
)
record("existing nine Reports sections remain", all(section in template_text for section in REQUIRED_SECTIONS), "all present")
record("existing 28 approved links remain", REQUIRED_15B_LINKS.issubset(template_hrefs), sorted(REQUIRED_15B_LINKS - template_hrefs))
record(
    "status links limited to approved routes",
    'href="{{ route }}"' in status_region
    and all(f'"{route}"' in status_region for route in APPROVED_STATUS_ROUTES.values()),
    sorted(APPROVED_STATUS_ROUTES.values()),
)
record(
    "financial summary remains link-only",
    '"financial"' in status_region
    and '"/financial_summary"' in status_region
    and "Central status computation" not in status_region,
    "financial panel route only",
)
record(
    "certificate verification remains Context Required",
    '"certificate_verification"' in status_region and '"Context Required"' in status_region,
    "context required",
)
record(
    "controlled exports remains Protected",
    '"controlled_exports"' in status_region and '"Protected"' in status_region,
    "protected",
)
record(
    "governance evidence points to Archive without recomputation",
    '"governance_evidence"' in status_region
    and '"/admin/workspace/archive"' in status_region
    and "build_archive_workspace_read_only_status" not in status_region,
    "archive link",
)
record(
    "V2 certification points to governed source without recomputation",
    '"v2_certification"' in status_region
    and '"/governance/v2-certification"' in status_region
    and "build_v2" not in status_region.lower(),
    "certification link",
)

status_lines = (git("status", "--short") or "").splitlines()
out_of_scope_changes = [
    line
    for line in status_lines
    if any(
        blocked in line.replace("\\", "/")
        for blocked in (
            "app.py",
            "services/",
            "models/",
            "migrations/",
            "database/",
            "auth",
            "session",
            ".db",
        )
    )
]
record("no app, service, model, migration, auth, session, or database changes", not out_of_scope_changes, "\n".join(out_of_scope_changes) or "none")

unexpected_status = []
for line in status_lines:
    normalized = line.replace("\\", "/")
    if not any(path in normalized for path in ALLOWED_STATUS_PATHS):
        unexpected_status.append(line)
record("working tree limited to approved 15C.2 files", not unexpected_status, "\n".join(unexpected_status) or "approved files only")


def render_reports_workspace():
    tmp = Path(tempfile.gettempdir())
    db_path = tmp / f"trustee_postv2_15c2_audit_{uuid4().hex}.db"
    os.environ["DB_PATH"] = str(db_path)
    os.environ["UPLOAD_FOLDER"] = str(tmp / "trustee_postv2_15c2_uploads")
    os.environ["EXPORT_ROOT"] = str(tmp / "trustee_postv2_15c2_exports")

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
        session["user_id"] = "AUDIT-ADMIN"
        session["username"] = "admin"
        session["role"] = "Admin"
        session["user_role"] = "Admin"
        session["is_master_admin"] = True
        session["firm_id"] = "FIRM-001"
        session["last_activity"] = time.time()

    reports_response = client.get("/admin/workspace/reports")
    archive_response = client.get("/admin/workspace/archive")
    return (
        reports_response.status_code,
        reports_response.get_data(as_text=True),
        archive_response.status_code,
        archive_response.get_data(as_text=True),
    )


try:
    reports_status_code, reports_html, archive_status_code, archive_html = render_reports_workspace()
except Exception as exc:
    reports_status_code, reports_html, archive_status_code, archive_html = 0, str(exc), 0, ""

rendered_panel_count = reports_html.count('class="reports-status-card reports-status-card--')
status_region_match = re.search(
    r'<section class="admin-card reports-status-region">.*?</section>',
    reports_html,
    flags=re.DOTALL,
)
rendered_status_region = status_region_match.group(0) if status_region_match else ""

record("runtime route returns HTTP 200", reports_status_code == 200, reports_html if reports_status_code == 0 else reports_status_code)
record("rendered page visibly contains ten status panels", rendered_panel_count == 10, rendered_panel_count)
record("rendered page contains no status action controls", not any(marker in rendered_status_region.lower() for marker in ("<form", "<button", "method=\"post\"", "method='post'")), "none")
record("archive workspace does not render Reports status region", archive_status_code == 200 and "Reports Oversight Status" not in archive_html, archive_status_code)
record("all ten panel labels render", all(label in reports_html for label in PANEL_LABELS.values()), "labels present")
record("boundary statuses render", "Context Required" in reports_html and "Protected" in reports_html, "visible")

print("POST-V2-15C.2 REPORTS WORKSPACE READ-ONLY STATUS PANEL RENDERING AUDIT")
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
print("RESULT: PASS" if not failed else "RESULT: FAIL")

if failed:
    raise SystemExit(1)
