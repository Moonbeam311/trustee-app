from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

APP = ROOT / "app.py"
REPORTS_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "reports.html"
PRIOR_AUDIT = ROOT / "scripts" / "audit_reports_route_classification_exposure_boundary_15a.py"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_CERTIFIED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"
REQUIRED_ANCESTOR = "79da300"
ALLOWED_BRANCHES = {"post-v2-planning"}

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

REQUIRED_LINKS = {
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

PROHIBITED_LINK_PREFIXES = (
    "/api/",
    "/debug/",
    "/system/recovery",
    "/admin/diag/",
    "/admin/repair/",
)

PROHIBITED_LINKS = {
    "/reports",
    "/certificates/backfill",
    "/admin/export-policy/toggle",
    "/execution/sessions/<execution_id>/export/generate",
    "/hosted-repair-admin-access-once",
}

PROTECTED_TEXT_SIGNALS = [
    "APIs",
    "diagnostics",
    "builders",
    "recovery",
    "permission reseeding",
    "approval",
    "finalization",
    "destructive",
]

CONTEXT_TEXT_SIGNALS = [
    "Trust",
    "Property",
    "Execution Session",
    "Transfer",
    "Intake",
    "Certificate",
    "Instrument",
    "Governance",
    "originating institutional record",
]

CONTROLLED_TEXT_SIGNALS = [
    "Generated PDFs",
    "CSV files",
    "ZIP packages",
    "authorization",
    "export policy",
    "verification",
    "workflow completion",
]

ALLOWED_STATUS_PATHS = {
    "templates/ios_workspaces/reports.html",
    "scripts/audit_reports_workspace_operator_information_architecture_15b.py",
    "scripts/audit_reports_route_classification_exposure_boundary_15a.py",
    "scripts/audit_reports_workspace_consolidation_operator_15.py",
}

PARAMETERIZED_ROUTE_RESOLUTION = {
    "/admin/workspace/governance": {
        "route": "/admin/workspace/<workspace_key>",
        "workspace_key": "governance",
    },
    "/admin/workspace/archive": {
        "route": "/admin/workspace/<workspace_key>",
        "workspace_key": "archive",
    },
}

checks = []
failures = []


def git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def record(name, passed, detail):
    checks.append((name, passed, detail))

    if not passed:
        failures.append(name)


def route_retained(route):
    resolution = PARAMETERIZED_ROUTE_RESOLUTION.get(route)

    if resolution:
        workspace_key = resolution["workspace_key"]
        return (
            resolution["route"] in app_text
            and f'"{workspace_key}"' in app_text
            and "IOS_WORKSPACE_META" in app_text
        )

    return route in app_text


print("POST-V2-15B REPORTS WORKSPACE OPERATOR INFORMATION ARCHITECTURE AUDIT")
print("=" * 92)

branch = git("branch", "--show-current")

record(
    "branch allowed",
    branch in ALLOWED_BRANCHES,
    branch or "unknown",
)

ancestor = subprocess.run(
    ["git", "merge-base", "--is-ancestor", REQUIRED_ANCESTOR, "HEAD"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    check=False,
)

record(
    "POST-V2-15A retained in ancestry",
    ancestor.returncode == 0,
    git("rev-parse", "HEAD") or "missing",
)

certified_commit = git(
    "rev-parse",
    f"{CERTIFIED_TAG}^{{commit}}",
)

record(
    "certified V2 tag protected",
    certified_commit == EXPECTED_CERTIFIED_COMMIT,
    certified_commit or "missing",
)

record(
    "app.py readable",
    APP.exists(),
    str(APP),
)

record(
    "Reports Workspace template readable",
    REPORTS_TEMPLATE.exists(),
    str(REPORTS_TEMPLATE),
)

record(
    "POST-V2-15A classification audit retained",
    PRIOR_AUDIT.exists(),
    str(PRIOR_AUDIT),
)

app_text = APP.read_text(encoding="utf-8") if APP.exists() else ""
template_text = (
    REPORTS_TEMPLATE.read_text(encoding="utf-8")
    if REPORTS_TEMPLATE.exists()
    else ""
)

record(
    "15B architecture marker present",
    "POST-V2-15B REPORTS WORKSPACE OPERATOR INFORMATION ARCHITECTURE"
    in template_text,
    "present",
)

missing_sections = [
    section
    for section in REQUIRED_SECTIONS
    if section not in template_text
]

record(
    "required Reports Workspace sections present",
    not missing_sections,
    "all present" if not missing_sections else str(missing_sections),
)

literal_links = sorted(
    {
        href
        for href in re.findall(
            r'href\s*=\s*["\']([^"\']+)["\']',
            template_text,
            flags=re.IGNORECASE,
        )
        if "{{" not in href
        and "}}" not in href
        and "{%" not in href
        and "%}" not in href
    }
)

missing_links = sorted(
    REQUIRED_LINKS - set(literal_links)
)

unexpected_links = sorted(
    set(literal_links) - REQUIRED_LINKS
)

record(
    "all approved central Reports links present",
    not missing_links,
    "all present" if not missing_links else str(missing_links),
)

record(
    "Reports Workspace exposure limited to approved links",
    not unexpected_links,
    "approved links only"
    if not unexpected_links
    else str(unexpected_links),
)

prohibited_links = [
    link
    for link in literal_links
    if link in PROHIBITED_LINKS
    or link.startswith(PROHIBITED_LINK_PREFIXES)
]

record(
    "protected and technical routes remain unexposed",
    not prohibited_links,
    "none" if not prohibited_links else str(prohibited_links),
)

parameterized_links = [
    link
    for link in literal_links
    if "<" in link or ">" in link
]

record(
    "no parameterized record links exposed",
    not parameterized_links,
    "none" if not parameterized_links else str(parameterized_links),
)

record(
    "Reports Workspace contains no POST form",
    "<form" not in template_text.lower()
    and 'method="post"' not in template_text.lower()
    and "method='post'" not in template_text.lower(),
    "none",
)

record(
    "ADR-9B placeholder removed",
    "ADR-9B placeholder" not in template_text,
    "removed",
)

missing_protected_signals = [
    signal
    for signal in PROTECTED_TEXT_SIGNALS
    if signal not in template_text
]

record(
    "protected boundary described",
    not missing_protected_signals,
    "all present"
    if not missing_protected_signals
    else str(missing_protected_signals),
)

missing_context_signals = [
    signal
    for signal in CONTEXT_TEXT_SIGNALS
    if signal not in template_text
]

record(
    "contextual report boundary described",
    not missing_context_signals,
    "all present"
    if not missing_context_signals
    else str(missing_context_signals),
)

missing_controlled_signals = [
    signal
    for signal in CONTROLLED_TEXT_SIGNALS
    if signal not in template_text
]

record(
    "controlled export boundary described",
    not missing_controlled_signals,
    "all present"
    if not missing_controlled_signals
    else str(missing_controlled_signals),
)

app_changes = [
    line
    for line in (git("status", "--short") or "").splitlines()
    if "app.py" in line.replace("\\", "/")
]

record(
    "app.py unchanged for 15B",
    not app_changes,
    "unchanged" if not app_changes else str(app_changes),
)

migration_changes = [
    line
    for line in (git("status", "--short") or "").splitlines()
    if "migration" in line.lower()
]

record(
    "no migration added for 15B",
    not migration_changes,
    "none" if not migration_changes else str(migration_changes),
)

runtime_database_changed = any(
    "trustee_app.db" in line.replace("\\", "/")
    for line in (git("status", "--short") or "").splitlines()
)

record(
    "runtime database not modified",
    not runtime_database_changed,
    "none",
)

unexpected_status = []

for line in (git("status", "--short") or "").splitlines():
    normalized = line.replace("\\", "/")

    if not any(
        path in normalized
        for path in ALLOWED_STATUS_PATHS
    ):
        unexpected_status.append(line)

record(
    "working tree limited to POST-V2-15B files",
    not unexpected_status,
    "15B files only"
    if not unexpected_status
    else "\n".join(unexpected_status),
)

for route in REQUIRED_LINKS:
    record(
        f"route retained: {route}",
        route_retained(route),
        "present" if route_retained(route) else "missing",
    )

print()
print("REPORTS WORKSPACE LINK INVENTORY")
print("-" * 92)

for link in literal_links:
    print(link)

print()
print("SUMMARY")
print("-" * 92)
print(f"required_sections: {len(REQUIRED_SECTIONS)}")
print(f"required_links: {len(REQUIRED_LINKS)}")
print(f"visible_template_links: {len(literal_links)}")
print(f"checks_total: {len(checks)}")
print(
    "checks_passed:",
    sum(1 for _, passed, _ in checks if passed),
)
print(f"checks_failed: {len(failures)}")

print()
for name, passed, detail in checks:
    print(
        f"{'PASS' if passed else 'FAIL'}: "
        f"{name} — {detail}"
    )

print()
print("RESULT:", "PASS" if not failures else "FAIL")

sys.exit(1 if failures else 0)
