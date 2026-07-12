from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_CERTIFIED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"
ALLOWED_BRANCHES = {"post-v2-planning"}

REQUIRED_TEMPLATES = [
    "templates/ios_workspaces/archive.html",
    "templates/admin_backup_database_confirm.html",
    "templates/execution_continuity_dashboard.html",
    "templates/execution_document_manifest.html",
    "templates/execution_document_recovery.html",
    "templates/execution_document_replication.html",
    "templates/final_record_archive_gate.html",
    "templates/property_archive_packet.html",
    "templates/property_archive_integrity.html",
    "templates/property_continuity_profile.html",
    "templates/transfer_archive_handoff.html",
    "templates/transfer_archive_handoff_audit_trail.html",
    "templates/governance/evidence_export_index.html",
    "templates/governance/evidence_export_manifest.html",
    "templates/governance/evidence_export_integrity.html",
    "templates/governance/evidence_export_archive_intake.html",
    "templates/governance/evidence_certification_dashboard.html",
    "templates/governance/evidence_completion_gate.html",
    "templates/governance/v2_certification_dashboard.html",
]

REQUIRED_ROUTES = [
    "/admin/workspace/<workspace_key>",
    "/admin/backup/database",
    "/admin/backup/database.zip",
    "/execution/sessions/<execution_id>/continuity",
    "/execution/sessions/<execution_id>/manifest",
    "/execution/sessions/<execution_id>/recovery",
    "/execution/sessions/<execution_id>/replication",
    "/execution/sessions/<execution_id>/freeze",
    "/execution/transfers/<transfer_id>/archive-handoff",
    "/execution/transfers/<transfer_id>/archive-handoff/audit-trail",
    "/execution/transfers/<transfer_id>/archive-handoff/audit-trail/export.txt",
    "/execution/transfers/<transfer_id>/archive-handoff/audit-trail/export.pdf",
    "/execution/transfers/<transfer_id>/archive-handoff/export-package.zip",
    "/property/<property_id>/archive-packet",
    "/property/<property_id>/archive-packet/integrity",
    "/property/<property_id>/archive-packet/manifest/pdf",
    "/property/<property_id>/archive-packet/zip",
    "/property/<property_id>/continuity",
    "/final-archive/<event_id>",
    "/continuity/certificates/verify",
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
    "/system/recovery/run",
    "/system/recovery/reseed-permissions",
]

PRIOR_AUDITS = [
    "scripts/audit_admin_database_backup_confirmation_gate_9c.py",
    "scripts/audit_admin_system_control_final_closure_9e.py",
    "scripts/audit_governance_workspace_certification_10c.py",
    "scripts/audit_governance_continuity_closure_11d.py",
    "scripts/audit_evidence_certification_export_continuity_12.py",
    "scripts/audit_evidence_certification_export_usability_12a.py",
    "scripts/audit_evidence_certification_closure_12b.py",
]

ARCHIVE_TEMPLATE_SIGNALS = [
    "Archive",
    "Return to Admin",
]

BACKUP_CONFIRMATION_SIGNALS = [
    "MEDIUM RISK",
    "confirmed",
]

PROTECTED_POST_ROUTES = [
    "/system/recovery/run",
    "/system/recovery/reseed-permissions",
    "/execution/sessions/<execution_id>/freeze",
]

checks = []
failures = []


def record(name, passed, detail):
    checks.append((name, passed, detail))
    status = "PASS" if passed else "FAIL"
    print(f"{status}: {name} — {detail}")
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


print("POST-V2-13 INSTITUTIONAL ARCHIVE / RECOVERY CONTINUITY AUDIT")
print("=" * 72)

branch = git("branch", "--show-current")
record(
    "branch allowed",
    branch in ALLOWED_BRANCHES,
    branch or "unavailable",
)

tag_commit = git("rev-parse", f"{CERTIFIED_TAG}^{{commit}}")
record(
    "certified tag protected",
    tag_commit == EXPECTED_CERTIFIED_COMMIT,
    tag_commit or "unavailable",
)

record(
    "app.py readable",
    APP.exists() and APP.is_file(),
    str(APP),
)

app_text = APP.read_text(encoding="utf-8", errors="ignore") if APP.exists() else ""

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
            item.strip().strip("'\"")
            for item in methods_raw.split(",")
            if item.strip()
        }
    else:
        methods = {"GET"}
    route_methods[route] = methods

record(
    "route inventory available",
    len(route_methods) > 0,
    f"count={len(route_methods)}",
)

missing_routes = [route for route in REQUIRED_ROUTES if route not in route_methods]
record(
    "required archive and recovery routes retained",
    not missing_routes,
    "all present" if not missing_routes else f"missing={missing_routes}",
)

missing_templates = [
    path for path in REQUIRED_TEMPLATES
    if not (ROOT / path).exists()
]
record(
    "required archive and recovery templates retained",
    not missing_templates,
    "all present" if not missing_templates else f"missing={missing_templates}",
)

missing_audits = [
    path for path in PRIOR_AUDITS
    if not (ROOT / path).exists()
]
record(
    "prior closure audit chain retained",
    not missing_audits,
    "all present" if not missing_audits else f"missing={missing_audits}",
)

archive_template = ROOT / "templates" / "ios_workspaces" / "archive.html"
archive_text = (
    archive_template.read_text(encoding="utf-8", errors="ignore")
    if archive_template.exists()
    else ""
)

missing_archive_signals = [
    signal for signal in ARCHIVE_TEMPLATE_SIGNALS
    if signal.casefold() not in archive_text.casefold()
]
record(
    "archive workspace operator signals retained",
    not missing_archive_signals,
    "all present"
    if not missing_archive_signals
    else f"missing={missing_archive_signals}",
)

backup_template = ROOT / "templates" / "admin_backup_database_confirm.html"
backup_text = (
    backup_template.read_text(encoding="utf-8", errors="ignore")
    if backup_template.exists()
    else ""
)

missing_backup_signals = [
    signal for signal in BACKUP_CONFIRMATION_SIGNALS
    if signal.lower() not in backup_text.lower()
]
record(
    "database backup confirmation boundary retained",
    not missing_backup_signals,
    "all present"
    if not missing_backup_signals
    else f"missing={missing_backup_signals}",
)

wrong_method_routes = []
for route in PROTECTED_POST_ROUTES:
    methods = route_methods.get(route, set())
    if "POST" not in methods:
        wrong_method_routes.append((route, sorted(methods)))

record(
    "protected recovery and freeze routes require POST",
    not wrong_method_routes,
    "all protected"
    if not wrong_method_routes
    else f"incorrect={wrong_method_routes}",
)

backup_methods = route_methods.get("/admin/backup/database.zip", set())
record(
    "database ZIP route remains read-only GET",
    backup_methods == {"GET"},
    f"methods={sorted(backup_methods)}",
)

active_backup_artifacts = [
    path.relative_to(ROOT).as_posix()
    for path in ROOT.glob("templates/**/*")
    if path.is_file()
    and (
        path.name.endswith(".bak")
        or ".bak_" in path.name
        or path.name.endswith("_backup")
        or ".backup" in path.name
    )
]

print()
print("ARCHIVE / RECOVERY CONTINUITY INVENTORY")
print("-" * 72)
print(f"routes_total: {len(route_methods)}")
print(f"required_routes_reviewed: {len(REQUIRED_ROUTES)}")
print(f"required_templates_reviewed: {len(REQUIRED_TEMPLATES)}")
print(f"prior_audits_reviewed: {len(PRIOR_AUDITS)}")
print(f"protected_post_routes_reviewed: {len(PROTECTED_POST_ROUTES)}")
print(f"repository_backup_artifacts: {active_backup_artifacts}")

db_candidates = [
    ROOT / "trustee_app.db",
    ROOT / "instance" / "trustee_app.db",
]

modified_db = []
status = git("status", "--short") or ""
for line in status.splitlines():
    lowered = line.lower()
    if lowered.endswith(".db") or ".db " in lowered:
        modified_db.append(line)

record(
    "runtime database not modified",
    not modified_db,
    "none" if not modified_db else str(modified_db),
)

status = git("status", "--short") or ""

allowed_status_paths = {
    "scripts/audit_institutional_archive_recovery_continuity_13.py",
    "app.py",
    "services/services_governance.py",
    "scripts/audit_archive_workspace_minimal_read_only_context_wiring_14b1.py",
    "scripts/audit_archive_workspace_read_only_status_panels_14b.py",
    "scripts/audit_archive_workspace_operator_information_architecture_14a.py",
    "scripts/audit_institutional_archive_workspace_consolidation_14.py",
    "app.py.pre_POST_V2_14B1.bak",
    "services/services_governance.py.pre_POST_V2_14B1.bak",
}

unexpected_status = []

for line in status.splitlines():
    normalized = line.replace("\\", "/")

    if not any(
        allowed_path in normalized
        for allowed_path in allowed_status_paths
    ):
        unexpected_status.append(line)

record(
    "working tree limited to approved Archive hardening files",
    not unexpected_status,
    "approved Archive files only"
    if not unexpected_status
    else "\\n".join(unexpected_status),
)

print()
print("SUMMARY")
print("-" * 72)
print(f"checks_total: {len(checks)}")
print(f"checks_passed: {sum(1 for _, passed, _ in checks if passed)}")
print(f"checks_failed: {len(failures)}")
print()
print("RESULT:", "PASS" if not failures else "FAIL")

sys.exit(1 if failures else 0)
