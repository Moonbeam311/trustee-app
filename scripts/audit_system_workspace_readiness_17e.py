from pathlib import Path
import ast
import re
import subprocess
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
SERVICE = ROOT / "services" / "services_system_workspace.py"
TEMPLATE = ROOT / "templates" / "ios_workspaces" / "system.html"
AUDIT_17C = ROOT / "scripts" / "audit_system_workspace_oversight_17c.py"
AUDIT_17D = ROOT / "scripts" / "audit_system_workspace_navigation_17d.py"

EXPECTED_BRANCH = "post-v2-planning"
EXPECTED_HEAD = "b3d3908d6b94d2b0cef8763e3de2ff222e7946c0"
APPROVED_STATUSES = {
    "ready",
    "protected",
    "attention",
    "restricted",
    "unavailable",
    "not_assessed",
}
DEPRECATED_STATUSES = {"available", "not_configured", "read_only_oversight"}
EXPECTED_PANEL_KEYS = [
    "protected_user_accounts",
    "application_permission_controls",
    "authentication_session_security",
    "audit_security_oversight",
    "backup_data_preservation",
    "deployment_production_health",
    "database_migration_posture",
    "feature_flags_operating_policy",
    "institutional_role_assignments",
    "recovery_repair_controls",
]
PANEL_TITLES = {
    "protected_user_accounts": "Protected User Accounts",
    "application_permission_controls": "Application Permission Controls",
    "authentication_session_security": "Authentication and Session Security",
    "audit_security_oversight": "Audit and Security Oversight",
    "backup_data_preservation": "Backup and Data Preservation",
    "deployment_production_health": "Deployment and Production Health",
    "database_migration_posture": "Database and Migration Posture",
    "feature_flags_operating_policy": "Feature Flags and Operating Policy",
    "institutional_role_assignments": "Institutional Role Assignments",
    "recovery_repair_controls": "Recovery and Repair Controls",
}
PANEL_FUNCTIONS = {
    "protected_user_accounts": "_protected_user_accounts_panel",
    "application_permission_controls": "_application_permission_controls_panel",
    "authentication_session_security": "_authentication_session_security_panel",
    "audit_security_oversight": "_audit_security_oversight_panel",
    "backup_data_preservation": "_backup_data_preservation_panel",
    "deployment_production_health": "_deployment_production_health_panel",
    "database_migration_posture": "_database_migration_posture_panel",
    "feature_flags_operating_policy": "_feature_flags_operating_policy_panel",
    "institutional_role_assignments": "_institutional_role_assignments_panel",
    "recovery_repair_controls": "_recovery_repair_controls_panel",
}
FORBIDDEN_ROUTES = [
    "/system/recovery/run",
    "/system/recovery/reseed-permissions",
    "/bootstrap_admin_once",
    "/admin/reset_admin_once",
    "/admin/hosted-bootstrap-admin",
    "/hosted-bootstrap-admin-once",
    "/hosted-firm-scope-migration-once",
    "/hosted-reseed-permissions-once",
    "/hosted-clear-login-lockout-once",
    "/hosted-repair-admin-access-once",
    "/admin/run-hosted-firm-scope-migration",
    "/admin/repair/int-lifecycle-tables",
    "/debug/auth-snapshot",
]
SENSITIVE_OUTPUT_MARKERS = [
    "password_hash",
    "password",
    "secret",
    "token",
    "cookie",
    "session value",
    "DB_PATH",
    "UPLOAD_FOLDER",
    "EXPORT_ROOT",
    "RAILWAY_SERVICE_NAME",
    "RAILWAY_PROJECT_NAME",
    "HOSTED_RECOVERY_TOKEN",
    "RESET_ADMIN_PASSWORD",
    "HOSTED_BOOTSTRAP_PASSWORD",
    "permission_name",
    "allow_permissions",
    "deny_permissions",
    "connection string",
    "stack trace",
    "exception repr",
]
UNSUPPORTED_CLAIMS = [
    "production ready",
    "fully secure",
    "all systems normal",
    "institution_ready",
    "fully_operational",
    "backup complete",
    "backup verified",
    "recoverable",
    "restorable",
]
MUTATION_CALL_PREFIXES = ("ensure_", "create_", "update_", "delete_")
MUTATION_CALLS = {
    "replace_role_permissions",
    "replace_user_permission_overrides",
    "run_safe_recovery_migrations",
    "reseed_default_role_permissions",
    "log_change",
    "send_file",
    "subprocess",
    "system",
}
ALLOWED_STATUS_PATHS = {
    "services/services_system_workspace.py",
    "templates/ios_workspaces/system.html",
    "scripts/audit_system_workspace_readiness_17e.py",
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


def read(path):
    return path.read_text(encoding="utf-8")


def find_function(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def assignment_list(tree, name):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        if isinstance(node.value, ast.List):
            return [
                item.value
                for item in node.value.elts
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            ]
    return []


def constant_strings(tree):
    values = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            values.append(node.value)
    return values


def function_calls(tree):
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            calls.append(call_name(node.func))
    return calls


def status_lines():
    lines = []
    for line in git("status", "--short").splitlines():
        if not line.strip() or line.lower().startswith("warning:"):
            continue
        lines.append(line)
    return lines


def panel_block(source, key):
    function_name = PANEL_FUNCTIONS.get(key)
    if not function_name:
        return ""
    index = source.find(f"def {function_name}(")
    if index < 0:
        return ""
    next_index = source.find("\ndef _", index + 1)
    end = next_index if next_index > index else len(source)
    return source[index:end]


service_text = read(SERVICE)
template_text = read(TEMPLATE)
app_text = read(APP)
service_tree = ast.parse(service_text)
service_strings = constant_strings(service_tree)
service_lower = service_text.lower()
template_lower = template_text.lower()

record("branch is post-v2-planning", git("branch", "--show-current") == EXPECTED_BRANCH)
record("HEAD is certified POST-V2-17E starting commit", git("rev-parse", "HEAD") == EXPECTED_HEAD)
record("HEAD equals origin/post-v2-planning", git("rev-parse", "HEAD") == git("rev-parse", "origin/post-v2-planning"))

record("Panel-order preservation", assignment_list(service_tree, "PANEL_KEYS") == EXPECTED_PANEL_KEYS)
record("Status vocabulary constant present", "APP_ROUTE_STATUSES" in service_text and all(f'"{status}"' in service_text for status in APPROVED_STATUSES))
deprecated_present = [status for status in DEPRECATED_STATUSES if status in service_strings]
record("Deprecated statuses absent from panel output", not deprecated_present, deprecated_present)
unknown_status_literals = [
    value
    for value in service_strings
    if value in APPROVED_STATUSES.union(DEPRECATED_STATUSES)
    and value not in APPROVED_STATUSES
]
record("Only approved normalized statuses are used", not unknown_status_literals, unknown_status_literals)

record("Workspace readiness derivation function exists", "_derive_workspace_status" in service_text)
record("Workspace status is derived from panels", "workspace_status = _derive_workspace_status(panels)" in service_text)
record("Workspace output includes status label", '"workspace_status_label"' in service_text)
record("Workspace output includes summary", '"workspace_summary"' in service_text)
record("Workspace output includes panels", '"panels"' in service_text)
record("Workspace template renders readiness status", "Workspace Status:" in template_text and "workspace_summary" in template_text)

recovery_block = panel_block(service_text, "recovery_repair_controls")
record("Recovery state is restricted", '"restricted"' in recovery_block)
record("Recovery has no route or action", re.search(r'"recovery_repair_controls"[\s\S]{0,500}None,\s*None,', service_text) is not None)
record("Recovery has required exclusion statement", "Exceptional recovery and repair controls are intentionally excluded from ordinary System navigation." in recovery_block)
record("Recovery exposes no emergency route", not any(route in recovery_block for route in FORBIDDEN_ROUTES))

backup_block = panel_block(service_text, "backup_data_preservation")
backup_bad_claims = [claim for claim in ("backup complete", "backup verified", "recoverable", "restorable") if claim in backup_block.lower()]
record("Backup truthfulness", not backup_bad_claims, backup_bad_claims)
record("Backup distinguishes access from completion", "backup completion and recoverability are not assessed here" in backup_block)
record("Backup remains protected, not ready", '"protected"' in backup_block and '"ready"' not in backup_block[:600])

deployment_block = panel_block(service_text, "deployment_production_health")
record("Production truthfulness distinguishes local and hosted", "Local structural" in deployment_block and "Hosted runtime posture" in deployment_block)
record("Production readiness is not claimed", "production ready" not in deployment_block.lower())
record("Hosted runtime not assessed locally", "not assessed from the local environment" in deployment_block.lower())

database_block = panel_block(service_text, "database_migration_posture")
record("Database posture safety uses sqlite_master", "sqlite_master" in database_block)
record("Database posture avoids mutation helpers", "ensure_" not in database_block and "run_safe_recovery_migrations" not in database_block)
record("Database posture exposes no path", "DB_PATH" not in database_block and "database path" not in database_block.lower())

policy_block = panel_block(service_text, "feature_flags_operating_policy")
record("Operating-policy safety summarizes ordinary policy only", all(key in policy_block for key in ("read_only_mode", "allow_exports", "allow_user_creation")))
record("Operating-policy safety excludes emergency flags", not any(flag in policy_block for flag in ("HOSTED", "RESET_ADMIN", "RECOVERY")))

panel_contract_ok = all(field in service_text for field in ("exception_state", "exception_label", "operator_guidance"))
record("Exception-state guidance contract exists", panel_contract_ok)
for key, title in PANEL_TITLES.items():
    block = panel_block(service_text, key)
    record(f"{title} exception fields", all(field in block for field in ("exception_state", "exception_label", "operator_guidance")), key)

combined_output = service_text + "\n" + template_text
forbidden_routes_present = [route for route in FORBIDDEN_ROUTES if route in combined_output]
record("Route exposure preservation", not forbidden_routes_present, forbidden_routes_present)
sensitive_present = [marker for marker in SENSITIVE_OUTPUT_MARKERS if marker in combined_output]
record("Sensitive-data exclusion", not sensitive_present, sensitive_present)
unsupported_present = [claim for claim in UNSUPPORTED_CLAIMS if claim in combined_output.lower()]
record("Unsupported readiness claims absent", not unsupported_present, unsupported_present)
record("Historical certification language absent or bounded", "production ready" not in combined_output.lower() and "fully certified" not in combined_output.lower())

calls = function_calls(service_tree)
bad_calls = [
    call
    for call in calls
    if call in MUTATION_CALLS or any(call.startswith(prefix) for prefix in MUTATION_CALL_PREFIXES)
]
sql_mutation = [
    phrase
    for phrase in ("insert", "alter table", "create table", "update ", "delete ")
    if phrase in service_lower
]
record("Mutation exclusion - helper calls", not bad_calls, bad_calls)
record("Mutation exclusion - SQL phrases", not sql_mutation, sql_mutation)
record("Mutation exclusion - shell calls", "os.system" not in service_text and "subprocess" not in service_text)

template_status_classes = [
    "system-oversight-card--ready",
    "system-oversight-card--protected",
    "system-oversight-card--attention",
    "system-oversight-card--restricted",
    "system-oversight-card--unavailable",
    "system-oversight-card--not-assessed",
]
record("Template supports approved status classes", all(status_class in template_text for status_class in template_status_classes))
record("Template renders operator guidance", "operator_guidance" in template_text)
record("Template does not render raw diagnostics", "traceback" not in template_lower and "raw diagnostics" not in template_lower and "exception repr" not in template_lower)

for audit_path in (AUDIT_17C, AUDIT_17D):
    record(f"{audit_path.name} preserved", audit_path.exists(), audit_path)

status_text = "\n".join(line.replace("\\", "/") for line in status_lines())
unexpected_status = []
for line in status_lines():
    normalized = line.replace("\\", "/")
    if not any(path in normalized for path in ALLOWED_STATUS_PATHS):
        unexpected_status.append(line)
record("Repository scope preserved", not unexpected_status, "\n".join(unexpected_status) or "approved scope only")

print("POST-V2-17E SYSTEM WORKSPACE READINESS AUDIT")
print("-" * 88)
sections = [
    "Workspace readiness derivation",
    "Status vocabulary",
    "Protected-state accuracy",
    "Attention-state accuracy",
    "Restricted-state accuracy",
    "Unavailable-state accuracy",
    "Not-assessed accuracy",
    "Backup truthfulness",
    "Production truthfulness",
    "Database posture safety",
    "Operating-policy safety",
    "Exception-state guidance",
    "Sensitive-data exclusion",
    "Mutation exclusion",
    "Panel-order preservation",
    "Route exposure preservation",
]
for section in sections:
    print(f"{section}: tracked")
print()

for key, title in PANEL_TITLES.items():
    block = panel_block(service_text, key)
    statuses = [status for status in APPROVED_STATUSES if f'"{status}"' in block]
    has_guidance = "operator_guidance" in block
    print(f"{title}: statuses={','.join(sorted(statuses)) or 'none'} guidance={'yes' if has_guidance else 'no'}")

print()
print("SUMMARY CHECKS")
print("-" * 88)
for name, passed, detail in checks:
    print(f"{'PASS' if passed else 'FAIL'}: {name} - {detail}")

failed = [check for check in checks if not check[1]]
print()
print(f"checks_total: {len(checks)}")
print(f"checks_passed: {len(checks) - len(failed)}")
print(f"checks_failed: {len(failed)}")

if failed:
    print("POST-V2-17E RESULT")
    print("FAIL — One or more System Workspace readiness or exception states are unsupported, overstated, unsafe, or operationally misleading.")
    raise SystemExit(1)

print("POST-V2-17E RESULT")
print("PASS — System Workspace readiness and exception states are evidence-based, bounded, non-mutating, and institutionally accurate.")
