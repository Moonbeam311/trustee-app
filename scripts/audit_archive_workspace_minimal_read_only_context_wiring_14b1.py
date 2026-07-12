from pathlib import Path
import ast
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
SERVICE = ROOT / "services" / "services_governance.py"
ARCHIVE_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "archive.html"

CERTIFIED_TAG = "v2-certified-baseline-2026-07-10"
EXPECTED_CERTIFIED_COMMIT = "607eb174354510b64804f8dd8e4b87756f25f366"
ALLOWED_BRANCHES = {"post-v2-planning"}

HELPER = "build_archive_workspace_read_only_status"
MARKER = "POST-V2-14B.1 ARCHIVE WORKSPACE MINIMAL READ-ONLY CONTEXT WIRING"

REQUIRED_BUILDERS = [
    "build_governance_evidence_export_index",
    "build_governance_evidence_certification_dashboard",
    "build_governance_evidence_export_manifest",
    "build_governance_export_integrity_digest_index",
    "build_governance_evidence_exception_panel",
    "build_governance_evidence_completion_gate",
    "build_governance_export_archive_intake_preview",
]

REQUIRED_PANELS = [
    '"evidence"',
    '"certification"',
    '"manifest"',
    '"integrity"',
    '"exceptions"',
    '"completion"',
    '"archive_intake"',
    '"backup"',
    '"continuity"',
    '"recovery"',
    '"replication"',
]

PROHIBITED_HELPER_CALLS = [
    "build_continuity_dashboard_profile(",
    "list_institutional_certifications(",
    "create_",
    "insert_",
    "update_",
    "delete_",
    "commit(",
]

ALLOWED_STATUS_PATHS = {
    "app.py",
    "services/services_governance.py",
    "scripts/audit_archive_workspace_minimal_read_only_context_wiring_14b1.py",
    "app.py.pre_POST_V2_14B1.bak",
    "services/services_governance.py.pre_POST_V2_14B1.bak",
    "scripts/audit_archive_workspace_read_only_status_panels_14b.py",
    "scripts/audit_archive_workspace_operator_information_architecture_14a.py",
    "scripts/audit_institutional_archive_workspace_consolidation_14.py",
    "scripts/audit_institutional_archive_recovery_continuity_13.py",
}

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


def read(path):
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def function_source(text, name):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ""

    lines = text.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            start = node.lineno - 1
            end = node.end_lineno or node.lineno
            return "\n".join(lines[start:end])

    return ""


print("POST-V2-14B.1 ARCHIVE WORKSPACE MINIMAL READ-ONLY CONTEXT WIRING AUDIT")
print("=" * 92)

branch = git("branch", "--show-current")
record("branch allowed", branch in ALLOWED_BRANCHES, branch or "unavailable")

tag_commit = git("rev-parse", f"{CERTIFIED_TAG}^{{commit}}")
record(
    "certified V2 tag protected",
    tag_commit == EXPECTED_CERTIFIED_COMMIT,
    tag_commit or "unavailable",
)

for label, path in [
    ("app.py readable", APP),
    ("governance service readable", SERVICE),
    ("Archive Workspace template readable", ARCHIVE_TEMPLATE),
]:
    record(label, path.exists(), str(path))

app_text = read(APP)
service_text = read(SERVICE)
archive_text = read(ARCHIVE_TEMPLATE)
helper_source = function_source(service_text, HELPER)

record(
    "14B.1 helper marker present",
    MARKER in service_text,
    "present" if MARKER in service_text else "missing",
)

record(
    "read-only aggregation helper present",
    bool(helper_source),
    "present" if helper_source else "missing",
)

missing_builders = [
    builder for builder in REQUIRED_BUILDERS
    if f"{builder}()" not in helper_source
]
record(
    "seven approved governance builders reused",
    not missing_builders,
    "all present" if not missing_builders else f"missing={missing_builders}",
)

missing_panels = [
    panel for panel in REQUIRED_PANELS
    if panel not in helper_source
]
record(
    "required display panels present",
    not missing_panels,
    "all present" if not missing_panels else f"missing={missing_panels}",
)

record(
    "helper explicitly read-only",
    '"read_only": True' in helper_source,
    "present",
)

record(
    "continuity remains Context Required",
    '"continuity"' in helper_source
    and '"status": "Context Required"' in helper_source,
    "retained",
)

record(
    "recovery remains Protected",
    '"recovery"' in helper_source
    and '"status": "Protected"' in helper_source,
    "retained",
)

record(
    "replication remains Context Required",
    '"replication"' in helper_source
    and helper_source.count('"status": "Context Required"') >= 2,
    "retained",
)

prohibited_calls = [
    token for token in PROHIBITED_HELPER_CALLS
    if token in helper_source
]
record(
    "mutation-capable and unverified central helpers absent",
    not prohibited_calls,
    "none" if not prohibited_calls else f"found={prohibited_calls}",
)

record(
    "Archive Workspace route conditionally builds status",
    'if workspace_key == "archive":' in app_text
    and "build_archive_workspace_read_only_status" in app_text,
    "present",
)

record(
    "archive_status passed to template context",
    "archive_status=archive_status" in app_text,
    "present",
)

record(
    "non-Archive workspaces receive no live Archive status",
    "archive_status = None" in app_text,
    "present",
)

record(
    "14A Archive Workspace template unchanged in scope",
    "POST-V2-14A ARCHIVE WORKSPACE OPERATOR INFORMATION ARCHITECTURE"
    in archive_text,
    "retained",
)

record(
    "no migration added for 14B.1",
    not any(
        path.name.lower().find("14b1") >= 0
        for path in (ROOT / "migrations").glob("*")
    ),
    "none",
)

status = git("status", "--short") or ""
unexpected = []

for line in status.splitlines():
    normalized = line.replace("\\", "/")
    if not any(path in normalized for path in ALLOWED_STATUS_PATHS):
        unexpected.append(line)

record(
    "working tree limited to POST-V2-14B.1 files",
    not unexpected,
    "14B.1 files only" if not unexpected else "\\n".join(unexpected),
)

print()
print("SUMMARY")
print("-" * 92)
print(f"checks_total: {len(checks)}")
print(f"checks_passed: {len(checks) - len(failures)}")
print(f"checks_failed: {len(failures)}")
print("RESULT: PASS" if not failures else "RESULT: FAIL")

sys.exit(1 if failures else 0)
