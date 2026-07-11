from pathlib import Path
import re
import subprocess
import sys
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
ARCHIVE_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "archive.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_CERTIFIED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"
ALLOWED_BRANCHES = {"post-v2-planning"}

ARCHIVE_FAMILIES = {
    "Archive Workspace": [
        "/admin/workspace/<workspace_key>",
    ],
    "Administrative Backup": [
        "/admin/backup/database",
        "/admin/backup/database.zip",
    ],
    "Execution Continuity": [
        "/execution/sessions/<execution_id>/continuity",
        "/execution/sessions/<execution_id>/manifest",
        "/execution/sessions/<execution_id>/recovery",
        "/execution/sessions/<execution_id>/replication",
        "/execution/sessions/<execution_id>/freeze",
    ],
    "Transfer Archive Handoff": [
        "/execution/transfers/<transfer_id>/archive-handoff",
        "/execution/transfers/<transfer_id>/archive-handoff/audit-trail",
        "/execution/transfers/<transfer_id>/archive-handoff/audit-trail/export.txt",
        "/execution/transfers/<transfer_id>/archive-handoff/audit-trail/export.pdf",
        "/execution/transfers/<transfer_id>/archive-handoff/export-package.zip",
    ],
    "Property Archive": [
        "/property/<property_id>/archive-packet",
        "/property/<property_id>/archive-packet/integrity",
        "/property/<property_id>/archive-packet/integrity/pdf",
        "/property/<property_id>/archive-packet/manifest/pdf",
        "/property/<property_id>/archive-packet/zip",
        "/property/<property_id>/archive-packet/finalize",
        "/property/<property_id>/continuity",
        "/property/<property_id>/continuity/pdf",
    ],
    "Governance Evidence": [
        "/governance/evidence-exports",
        "/governance/evidence-exports.csv",
        "/governance/evidence-exports/manifest",
        "/governance/evidence-exports/manifest.txt",
        "/governance/evidence-exports/integrity",
        "/governance/evidence-exports/integrity.txt",
        "/governance/evidence-exports/archive-intake",
        "/governance/evidence-exports/archive-intake.txt",
        "/governance/evidence-exports/certification",
        "/governance/evidence-exports/certification.txt",
        "/governance/evidence-exports/completion-gate",
        "/governance/evidence-exports/completion-gate.txt",
        "/governance/v2-certification",
        "/governance/v2-certification.txt",
    ],
    "Continuity Certificates": [
        "/continuity/certificates/verify",
        "/continuity/certificates/<certification_id>",
        "/continuity/certificates/<certification_id>/pdf",
        "/continuity/certificates/<certification_id>/verify",
    ],
    "Final Archive": [
        "/final-archive/<event_id>",
    ],
    "System Recovery": [
        "/system/recovery/run",
        "/system/recovery/reseed-permissions",
    ],
}

CENTRAL_STATUS_CANDIDATES = {
    "Archive Workspace",
    "Administrative Backup",
    "Governance Evidence",
    "Continuity Certificates",
}

CONTEXTUAL_FAMILIES = {
    "Execution Continuity",
    "Transfer Archive Handoff",
    "Property Archive",
    "Final Archive",
}

PROTECTED_FAMILIES = {
    "System Recovery",
}

PROTECTED_ACTION_ROUTES = {
    "/system/recovery/run",
    "/system/recovery/reseed-permissions",
    "/execution/sessions/<execution_id>/freeze",
    "/property/<property_id>/archive-packet/finalize",
}

EXPECTED_TEMPLATE_SIGNALS = [
    "ARCHIVE Workspace",
    "Return to Admin",
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


print("POST-V2-14 INSTITUTIONAL ARCHIVE WORKSPACE CONSOLIDATION AUDIT")
print("=" * 80)

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

record(
    "app.py readable",
    APP.exists(),
    str(APP),
)

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

route_pattern = re.compile(
    r'@app\.route\(\s*[\'"]([^\'"]+)[\'"]'
    r'(?:\s*,\s*methods\s*=\s*\[([^\]]+)\])?',
    re.MULTILINE,
)

route_methods = {}
for match in route_pattern.finditer(app_text):
    route = match.group(1)
    methods_raw = match.group(2)
    if methods_raw:
        methods = {
            value.strip().strip("'\"")
            for value in methods_raw.split(",")
            if value.strip()
        }
    else:
        methods = {"GET"}
    route_methods[route] = methods

record(
    "route inventory available",
    bool(route_methods),
    f"count={len(route_methods)}",
)

all_required_routes = [
    route
    for routes in ARCHIVE_FAMILIES.values()
    for route in routes
]

missing_routes = [
    route for route in all_required_routes
    if route not in route_methods
]

record(
    "archive family routes retained",
    not missing_routes,
    "all present" if not missing_routes else f"missing={missing_routes}",
)

missing_template_signals = [
    signal for signal in EXPECTED_TEMPLATE_SIGNALS
    if signal.casefold() not in archive_text.casefold()
]

record(
    "archive workspace baseline signals retained",
    not missing_template_signals,
    "all present"
    if not missing_template_signals
    else f"missing={missing_template_signals}",
)

visible_archive_links = sorted(set(re.findall(r'href=["\']([^"\']+)["\']', archive_text)))

record(
    "archive workspace remains minimally exposed",
    len(visible_archive_links) <= 3,
    f"visible_links={visible_archive_links}",
)

wrong_protected_methods = []
for route in sorted(PROTECTED_ACTION_ROUTES):
    methods = route_methods.get(route, set())
    if "POST" not in methods:
        wrong_protected_methods.append((route, sorted(methods)))

record(
    "protected archive and recovery actions require POST",
    not wrong_protected_methods,
    "all protected"
    if not wrong_protected_methods
    else f"incorrect={wrong_protected_methods}",
)

unexpected_protected_links = [
    route for route in PROTECTED_ACTION_ROUTES
    if route in archive_text
]

record(
    "protected recovery controls absent from Archive Workspace",
    not unexpected_protected_links,
    "none"
    if not unexpected_protected_links
    else f"exposed={unexpected_protected_links}",
)

print()
print("ARCHIVE FAMILY CONSOLIDATION MATRIX")
print("-" * 80)

family_counts = {}
for family, routes in ARCHIVE_FAMILIES.items():
    present = [route for route in routes if route in route_methods]
    missing = [route for route in routes if route not in route_methods]
    family_counts[family] = len(present)

    if family in CENTRAL_STATUS_CANDIDATES:
        disposition = "CENTRAL READ-ONLY STATUS CANDIDATE"
    elif family in CONTEXTUAL_FAMILIES:
        disposition = "RETAIN CONTEXTUAL; LINK FROM STATUS SUMMARY"
    elif family in PROTECTED_FAMILIES:
        disposition = "KEEP HIDDEN / PROTECTED"
    else:
        disposition = "REVIEW"

    print()
    print(f"{family} | {disposition}")
    print(f"  routes_present: {len(present)}/{len(routes)}")

    for route in present:
        print(f"  PRESENT | {route} | methods={sorted(route_methods[route])}")

    for route in missing:
        print(f"  MISSING | {route}")

print()
print("PROPOSED ARCHIVE WORKSPACE INFORMATION ARCHITECTURE")
print("-" * 80)
print("1. Archive Readiness Summary")
print("2. Evidence and Certification Status")
print("3. Backup Status and Controlled Download")
print("4. Integrity and Manifest Status")
print("5. Continuity Certificate Verification")
print("6. Contextual Archive Records by Module")
print("7. Replication and Recovery Readiness — status only")
print("8. Return to Admin / Governance / originating record")
print()
print("Controls that must remain hidden or contextual:")
print("- system recovery execution")
print("- permission reseeding")
print("- execution freeze action")
print("- property archive finalization action")
print("- restore or destructive operations")

archive_terms = {
    "archive": len(re.findall(r"archive", app_text, re.IGNORECASE)),
    "recovery": len(re.findall(r"recovery", app_text, re.IGNORECASE)),
    "continuity": len(re.findall(r"continuity", app_text, re.IGNORECASE)),
    "integrity": len(re.findall(r"integrity", app_text, re.IGNORECASE)),
    "manifest": len(re.findall(r"manifest", app_text, re.IGNORECASE)),
    "replication": len(re.findall(r"replication", app_text, re.IGNORECASE)),
    "backup": len(re.findall(r"backup", app_text, re.IGNORECASE)),
    "certification": len(re.findall(r"certification", app_text, re.IGNORECASE)),
}

print()
print("ARCHIVE TERMINOLOGY INVENTORY")
print("-" * 80)
for term, count in archive_terms.items():
    print(f"{term}: {count}")

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

allowed_self = "scripts/audit_institutional_archive_workspace_consolidation_14.py"
unexpected_status = [
    line for line in status.splitlines()
    if allowed_self not in line.replace("\\", "/")
]

record(
    "working tree clean or only POST-V2-14 audit untracked",
    not unexpected_status,
    "clean/self-only"
    if not unexpected_status
    else "\\n".join(unexpected_status),
)

print()
print("SUMMARY")
print("-" * 80)
print(f"archive_families_reviewed: {len(ARCHIVE_FAMILIES)}")
print(f"archive_routes_reviewed: {len(all_required_routes)}")
print(f"central_status_candidates: {sorted(CENTRAL_STATUS_CANDIDATES)}")
print(f"contextual_families: {sorted(CONTEXTUAL_FAMILIES)}")
print(f"protected_families: {sorted(PROTECTED_FAMILIES)}")
print(f"checks_total: {len(checks)}")
print(f"checks_passed: {sum(1 for _, passed, _ in checks if passed)}")
print(f"checks_failed: {len(failures)}")
print()
print("RESULT:", "PASS" if not failures else "FAIL")

sys.exit(1 if failures else 0)
