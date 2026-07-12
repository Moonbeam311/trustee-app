from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
ARCHIVE_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "archive.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_CERTIFIED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"
ALLOWED_BRANCHES = {"post-v2-planning"}

MARKER = "POST-V2-14A ARCHIVE WORKSPACE OPERATOR INFORMATION ARCHITECTURE"

REQUIRED_SECTIONS = [
    'data-archive-section="readiness-summary"',
    'data-archive-section="evidence-certification"',
    'data-archive-section="manifest-integrity"',
    'data-archive-section="continuity-verification"',
    'data-archive-section="controlled-backup"',
    'data-archive-section="contextual-records"',
    'data-archive-section="protected-boundary"',
]

REQUIRED_OPERATOR_SIGNALS = [
    "Archive Readiness Summary",
    "Evidence and Certification",
    "Manifest and Integrity Review",
    "Continuity Certificate Verification",
    "Controlled Database Backup",
    "Contextual Archive Records",
    "Protected Recovery Boundary",
    "Return to Admin Dashboard",
    "Open Governance Workspace",
]

REQUIRED_SAFE_LINKS = [
    "/governance/evidence-exports",
    "/governance/evidence-exports/completion-gate",
    "/governance/evidence-exports/archive-intake",
    "/governance/evidence-exports/certification",
    "/governance/v2-certification",
    "/governance/evidence-exports/manifest",
    "/governance/evidence-exports/integrity",
    "/governance/evidence-exports/exceptions",
    "/continuity/certificates/verify",
    "/admin/backup/database.zip",
    "/admin",
    "/admin/workspace/governance",
]

PROHIBITED_LINKS = [
    "/system/recovery/run",
    "/system/recovery/reseed-permissions",
    "/execution/sessions/<execution_id>/freeze",
    "/property/<property_id>/archive-packet/finalize",
]

REQUIRED_CONTEXTUAL_LABELS = [
    "Execution Continuity",
    "Transfer Archive Handoff",
    "Property Archive",
    "Final Record Archive",
]

checks = []
failures = []


def record(name, passed, detail):
    checks.append((name, passed, detail))
    print(f"{'PASS' if passed else 'FAIL'}: {name} — {detail}")
    if not passed:
        failures.append(name)


def git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


print("POST-V2-14A ARCHIVE WORKSPACE OPERATOR INFORMATION ARCHITECTURE AUDIT")
print("=" * 88)

branch = git("branch", "--show-current")
record(
    "branch allowed",
    branch in ALLOWED_BRANCHES,
    branch or "unavailable",
)

tag_commit = git("rev-parse", f"{CERTIFIED_TAG}^{{commit}}")
record(
    "certified V2 tag protected",
    tag_commit == EXPECTED_CERTIFIED_COMMIT,
    tag_commit or "unavailable",
)

record("app.py readable", APP.exists(), str(APP))
record(
    "archive workspace template readable",
    ARCHIVE_TEMPLATE.exists(),
    str(ARCHIVE_TEMPLATE),
)

app_text = APP.read_text(encoding="utf-8", errors="ignore") if APP.exists() else ""
archive_text = (
    ARCHIVE_TEMPLATE.read_text(encoding="utf-8", errors="ignore")
    if ARCHIVE_TEMPLATE.exists()
    else ""
)

record(
    "14A architecture marker present",
    MARKER in archive_text,
    "present" if MARKER in archive_text else "missing",
)

missing_sections = [
    section for section in REQUIRED_SECTIONS
    if section not in archive_text
]
record(
    "required archive workspace sections present",
    not missing_sections,
    "all present" if not missing_sections else f"missing={missing_sections}",
)

missing_signals = [
    signal for signal in REQUIRED_OPERATOR_SIGNALS
    if signal.casefold() not in archive_text.casefold()
]
record(
    "operator information architecture signals present",
    not missing_signals,
    "all present" if not missing_signals else f"missing={missing_signals}",
)

raw_template_links = re.findall(r'href=["\']([^"\']+)["\']', archive_text)
template_links = sorted(set(
    link for link in raw_template_links
    if not any(marker in link for marker in ("{{", "}}", "{%", "%}"))
))

missing_links = [
    route for route in REQUIRED_SAFE_LINKS
    if route not in template_links
]
record(
    "required safe archive links present",
    not missing_links,
    "all present" if not missing_links else f"missing={missing_links}",
)

exposed_protected_links = [
    route for route in PROHIBITED_LINKS
    if route in template_links or route in archive_text
]
record(
    "protected recovery actions remain unexposed",
    not exposed_protected_links,
    "none"
    if not exposed_protected_links
    else f"exposed={exposed_protected_links}",
)

missing_contextual_labels = [
    label for label in REQUIRED_CONTEXTUAL_LABELS
    if label.casefold() not in archive_text.casefold()
]
record(
    "contextual archive families identified",
    not missing_contextual_labels,
    "all present"
    if not missing_contextual_labels
    else f"missing={missing_contextual_labels}",
)

def route_retained(route):
    if route in app_text:
        return True

    if route.startswith("/admin/workspace/"):
        return "/admin/workspace/<workspace_key>" in app_text

    return False


required_routes_missing_from_app = [
    route for route in REQUIRED_SAFE_LINKS
    if not route_retained(route)
]
record(
    "linked routes retained in app.py",
    not required_routes_missing_from_app,
    "all retained"
    if not required_routes_missing_from_app
    else f"missing={required_routes_missing_from_app}",
)

record(
    "controlled backup warning retained",
    "MEDIUM RISK" in archive_text
    and "CONFIRMATION REQUIRED" in archive_text
    and "/admin/backup/database.zip" in archive_text,
    "present",
)

record(
    "recovery boundary described as intentional",
    "intentionally not exposed" in archive_text.casefold()
    and "safety control" in archive_text.casefold(),
    "present",
)

status = git("status", "--short") or ""

modified_db = [
    line for line in status.splitlines()
    if ".db" in line.lower()
]
record(
    "runtime database not modified",
    not modified_db,
    "none" if not modified_db else str(modified_db),
)

allowed_paths = {
    "templates/ios_workspaces/archive.html",
    "templates/ios_workspaces/archive.html.pre_POST_V2_14A.bak",
    "scripts/audit_archive_workspace_operator_information_architecture_14a.py",
    "scripts/audit_institutional_archive_workspace_consolidation_14.py",
    "scripts/audit_institutional_archive_recovery_continuity_13.py",
    "app.py",
    "services/services_governance.py",
    "scripts/audit_archive_workspace_minimal_read_only_context_wiring_14b1.py",
    "app.py.pre_POST_V2_14B1.bak",
    "services/services_governance.py.pre_POST_V2_14B1.bak",
    "scripts/audit_archive_workspace_read_only_status_panels_14b.py",
    "scripts/audit_archive_workspace_read_only_status_rendering_14b2.py",
}

unexpected_status = []
for line in status.splitlines():
    normalized = line.replace("\\", "/")
    if not any(path in normalized for path in allowed_paths):
        unexpected_status.append(line)

record(
    "working tree limited to POST-V2-14A files",
    not unexpected_status,
    "14A files only"
    if not unexpected_status
    else "\\n".join(unexpected_status),
)

print()
print("ARCHIVE WORKSPACE LINK INVENTORY")
print("-" * 88)
for link in template_links:
    print(link)

print()
print("SUMMARY")
print("-" * 88)
print(f"required_sections: {len(REQUIRED_SECTIONS)}")
print(f"required_safe_links: {len(REQUIRED_SAFE_LINKS)}")
print(f"visible_template_links: {len(template_links)}")
print(f"protected_links_exposed: {len(exposed_protected_links)}")
print(f"checks_total: {len(checks)}")
print(f"checks_passed: {sum(1 for _, passed, _ in checks if passed)}")
print(f"checks_failed: {len(failures)}")
print()
print("RESULT:", "PASS" if not failures else "FAIL")

sys.exit(1 if failures else 0)
