from pathlib import Path
import subprocess
import sys

from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "ios_workspaces" / "archive.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_CERTIFIED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"
ALLOWED_BRANCHES = {"post-v2-planning"}

MARKER = (
    "POST-V2-14B.2 ARCHIVE WORKSPACE "
    "READ-ONLY STATUS PANEL RENDERING"
)

REQUIRED_PANEL_KEYS = [
    "evidence",
    "certification",
    "completion",
    "archive_intake",
    "manifest",
    "integrity",
    "exceptions",
    "backup",
    "continuity",
    "recovery",
    "replication",
]

REQUIRED_RENDER_FIELDS = [
    "panel.label",
    "panel.status",
    "panel.detail",
    "panel.route",
]

PROTECTED_EXPOSURES = [
    "/system/recovery/run",
    "/system/recovery/reseed-permissions",
    "/execution/sessions/<execution_id>/freeze",
    "restore_database",
    "run_system_recovery",
    "reseed_permissions",
]

ALLOWED_STATUS_PATHS = {
    "templates/ios_workspaces/archive.html",
    "scripts/audit_archive_workspace_read_only_status_rendering_14b2.py",
    "scripts/audit_archive_workspace_minimal_read_only_context_wiring_14b1.py",
    "scripts/audit_archive_workspace_read_only_status_panels_14b.py",
    "scripts/audit_archive_workspace_operator_information_architecture_14a.py",
    "scripts/audit_institutional_archive_workspace_consolidation_14.py",
    "scripts/audit_institutional_archive_recovery_continuity_13.py",
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


print(
    "POST-V2-14B.2 ARCHIVE WORKSPACE "
    "READ-ONLY STATUS PANEL RENDERING AUDIT"
)
print("=" * 88)

branch = git("branch", "--show-current")
record(
    "branch allowed",
    branch in ALLOWED_BRANCHES,
    branch or "unknown",
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
    "Archive Workspace template readable",
    TEMPLATE.exists(),
    str(TEMPLATE),
)

text = TEMPLATE.read_text(encoding="utf-8") if TEMPLATE.exists() else ""

record(
    "14B.2 rendering marker present",
    MARKER in text,
    "present" if MARKER in text else "missing",
)

try:
    Environment().parse(text)
    jinja_valid = True
    jinja_detail = "valid"
except Exception as exc:
    jinja_valid = False
    jinja_detail = str(exc)

record(
    "Archive Workspace Jinja syntax valid",
    jinja_valid,
    jinja_detail,
)

missing_panels = [
    key
    for key in REQUIRED_PANEL_KEYS
    if f'"{key}"' not in text
]

record(
    "all eleven certified panels represented",
    not missing_panels,
    "all present" if not missing_panels else str(missing_panels),
)

missing_fields = [
    field
    for field in REQUIRED_RENDER_FIELDS
    if field not in text
]

record(
    "approved panel fields rendered",
    not missing_fields,
    "all present" if not missing_fields else str(missing_fields),
)

record(
    "rendering requires read-only contract",
    "archive_status.read_only" in text,
    "present" if "archive_status.read_only" in text else "missing",
)

record(
    "panel links conditional on route",
    "{% if panel.route %}" in text,
    "present" if "{% if panel.route %}" in text else "missing",
)

record(
    "status-only fallback retained",
    "Status only" in text
    and "originating record context required" in text,
    "present",
)

record(
    "no forms added to Archive Workspace",
    "<form" not in text.lower(),
    "none" if "<form" not in text.lower() else "form found",
)

record(
    "no POST controls added",
    'method="post"' not in text.lower()
    and "method='post'" not in text.lower(),
    "none",
)

exposed_protected = [
    value
    for value in PROTECTED_EXPOSURES
    if value in text
]

record(
    "protected recovery operations remain unexposed",
    not exposed_protected,
    "none" if not exposed_protected else str(exposed_protected),
)

record(
    "recovery and replication can remain route-less",
    "{% if panel.route %}" in text
    and "Status only" in text,
    "conditional route boundary present",
)

migration_changes = [
    line
    for line in (git("status", "--short") or "").splitlines()
    if "migration" in line.lower()
]

record(
    "no migration added for 14B.2",
    not migration_changes,
    "none" if not migration_changes else str(migration_changes),
)

unexpected_status = []

for line in (git("status", "--short") or "").splitlines():
    normalized = line.replace("\\", "/")

    if not any(
        allowed_path in normalized
        for allowed_path in ALLOWED_STATUS_PATHS
    ):
        unexpected_status.append(line)

record(
    "working tree limited to POST-V2-14B.2 files",
    not unexpected_status,
    "14B.2 files only"
    if not unexpected_status
    else "\n".join(unexpected_status),
)

for name, passed, detail in checks:
    print(
        f"{'PASS' if passed else 'FAIL'}: "
        f"{name} — {detail}"
    )

print()
print("SUMMARY")
print("-" * 88)
print(f"checks_total: {len(checks)}")
print(
    "checks_passed:",
    sum(1 for _, passed, _ in checks if passed),
)
print(f"checks_failed: {len(failures)}")
print()
print("RESULT:", "PASS" if not failures else "FAIL")

sys.exit(1 if failures else 0)
