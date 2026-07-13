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

EXPECTED_BRANCH = "post-v2-planning"
EXPECTED_HEAD = "58f7d054c47f2c3c258a03d6166e0aafcec2b719"
EXPECTED_KEYS = [
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
ALLOWED_ROUTES = {
    "/users",
    "/permissions",
    "/security",
    "/audit",
    "/admin/backup/database.zip",
    "/hosted-production-health",
    "/roles",
}
FORBIDDEN_ROUTES = {
    "/admin/backup/database",
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
}
SENSITIVE_TOKENS = [
    "password_hash",
    "HOSTED_RECOVERY_TOKEN",
    "RESET_ADMIN_PASSWORD",
    "HOSTED_BOOTSTRAP_PASSWORD",
    "DB_PATH",
    "UPLOAD_FOLDER",
    "EXPORT_ROOT",
    "RAILWAY_SERVICE_NAME",
    "RAILWAY_PROJECT_NAME",
    "session[",
    "cookie",
    "secret",
    "connection string",
    "permission_name",
    "selected_permissions",
    "allow_permissions",
    "deny_permissions",
]
FORBIDDEN_CALLS = {
    "run_safe_recovery_migrations",
    "reseed_default_role_permissions",
    "replace_role_permissions",
    "replace_user_permission_overrides",
    "log_change",
    "subprocess",
    "send_file",
}
ALLOWED_STATUS_PATHS = {
    "app.py",
    "services/services_system_workspace.py",
    "templates/ios_workspaces/system.html",
    "scripts/audit_system_workspace_oversight_17c.py",
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


def read(path):
    return path.read_text(encoding="utf-8")


def record(name, passed, detail=""):
    checks.append((name, bool(passed), str(detail)))


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


def route_decorators(function_node):
    routes = []
    for decorator in function_node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        if call_name(decorator.func) != "route":
            continue
        if decorator.args and isinstance(decorator.args[0], ast.Constant):
            routes.append(decorator.args[0].value)
    return routes


def constant_strings(tree):
    values = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            values.append(node.value)
    return values


def assignment_list(tree, target_name):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == target_name for target in node.targets):
            continue
        if isinstance(node.value, ast.List):
            return [
                item.value
                for item in node.value.elts
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            ]
    return []


def function_calls(tree):
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            calls.append(call_name(node.func))
    return calls


def hrefs_from_template(source):
    return {
        href
        for href in re.findall(r'href=["\']([^"\']+)["\']', source)
        if "{{" not in href and "}}" not in href
    }


def normalized_status_lines():
    lines = []
    for line in git("status", "--short").splitlines():
        if not line.strip() or line.lower().startswith("warning:"):
            continue
        lines.append(line)
    return lines


app_text = read(APP)
service_text = read(SERVICE) if SERVICE.exists() else ""
template_text = read(TEMPLATE) if TEMPLATE.exists() else ""
app_tree = ast.parse(app_text)
service_tree = ast.parse(service_text) if service_text else ast.Module(body=[], type_ignores=[])
service_strings = constant_strings(service_tree)
template_hrefs = hrefs_from_template(template_text)

branch = git("branch", "--show-current")
head = git("rev-parse", "HEAD")
origin_head = git("rev-parse", "origin/post-v2-planning")
status_lines = normalized_status_lines()

record("branch is post-v2-planning", branch == EXPECTED_BRANCH, branch)
record("HEAD is certified POST-V2-17C starting commit", head == EXPECTED_HEAD, head)
record("HEAD equals origin/post-v2-planning", head == origin_head and bool(head), f"HEAD={head} origin={origin_head}")
record("system workspace service exists", SERVICE.exists(), SERVICE)
record("system workspace template exists", TEMPLATE.exists(), TEMPLATE)

builder_fn = find_function(service_tree, "build_system_workspace_oversight")
record("build_system_workspace_oversight exists", builder_fn is not None, "found")
record(
    "app imports build_system_workspace_oversight",
    "from services.services_system_workspace import build_system_workspace_oversight" in app_text,
    "import present",
)

workspace_fn = find_function(app_tree, "admin_ios_workspace")
workspace_source = ast.get_source_segment(app_text, workspace_fn) if workspace_fn else ""
workspace_routes = route_decorators(workspace_fn) if workspace_fn else []
all_workspace_routes = [
    route
    for node in ast.walk(app_tree)
    if isinstance(node, ast.FunctionDef)
    for route in route_decorators(node)
    if route == "/admin/workspace/system" or route == "/admin/workspace/<workspace_key>"
]
record("existing workspace route retained", "/admin/workspace/<workspace_key>" in workspace_routes, workspace_routes)
record("no second System Workspace route added", all_workspace_routes == ["/admin/workspace/<workspace_key>"], all_workspace_routes)
record("workspace route calls oversight builder", "build_system_workspace_oversight()" in workspace_source, "builder call")
record("workspace route passes system_oversight", "system_oversight=system_oversight" in workspace_source, "context")

panel_keys = assignment_list(service_tree, "PANEL_KEYS")
record("service panel keys match locked order", panel_keys == EXPECTED_KEYS, panel_keys)
record("service defines exactly ten panel keys", len(panel_keys) == 10, len(panel_keys))
record("template iterates service-provided panels", "{% for panel in panels %}" in template_text, "service order")
record("template does not sort panels", "|sort" not in template_text and "sort(" not in template_text.lower(), "no sort")

service_routes = {value for value in service_strings if value.startswith("/")}
template_routes = template_hrefs
returned_routes = service_routes.union(template_routes)
record("only authorized route destinations appear", returned_routes.issubset(ALLOWED_ROUTES.union({"/admin"})), sorted(returned_routes))
record("service route destinations authorized", service_routes.issubset(ALLOWED_ROUTES), sorted(service_routes))
bad_service_routes = [route for route in service_routes if route in FORBIDDEN_ROUTES]
bad_template_routes = [route for route in template_routes if route in FORBIDDEN_ROUTES]
record("forbidden routes not returned by service", not bad_service_routes, bad_service_routes)
record("forbidden routes not rendered by template", not bad_template_routes, bad_template_routes)

combined_output_source = service_text + "\n" + template_text
present_sensitive = [token for token in SENSITIVE_TOKENS if token in combined_output_source]
record("sensitive tokens absent from service and template", not present_sensitive, present_sensitive)

calls = function_calls(service_tree)
bad_calls = [
    call
    for call in calls
    if call in FORBIDDEN_CALLS
    or call.startswith("ensure_")
    or call.startswith("create_")
    or call.startswith("update_")
    or call.startswith("delete_")
]
sql_mutation_phrases = [
    phrase
    for phrase in ("insert", "alter table", "create table", "update ", "delete ")
    if phrase in service_text.lower()
]
record("service contains no forbidden mutation helper calls", not bad_calls, bad_calls)
record("service contains no SQL mutation phrases", not sql_mutation_phrases, sql_mutation_phrases)
record("service does not write files", ".write_text(" not in service_text and ".write_bytes(" not in service_text, "no write calls")
record("service does not invoke subprocesses", "subprocess" not in service_text, "no subprocess")

record("template includes Application Permission Controls", "Application Permission Controls" in template_text, "present")
record("template includes Institutional Role Assignments", "Institutional Role Assignments" in template_text, "present")
record(
    "template includes role assignment clarification",
    "These are institutional and trust-scoped assignments, not application security roles." in template_text,
    "clarification present",
)
role_panel_bad_language = (
    re.search(r"Institutional Role Assignments[\s\S]{0,800}(application-role|permission administration|security-role)", template_text, re.I)
)
record("roles panel not described as application permission administration", role_panel_bad_language is None, "clean")

status_text = "\n".join(line.replace("\\", "/") for line in status_lines)
unexpected = []
for line in status_lines:
    normalized = line.replace("\\", "/")
    if not any(path in normalized for path in ALLOWED_STATUS_PATHS):
        unexpected.append(line)
record("models unchanged", "models/" not in status_text, status_text or "none")
record("migrations unchanged", "migrations/" not in status_text, status_text or "none")
record("People workspace unchanged", "templates/ios_workspaces/people.html" not in status_text, status_text or "none")
record("POST-V2-17B audit script unchanged", "scripts/audit_system_protected_route_hardening_17b.py" not in status_text, status_text or "none")
record("working tree limited to 17C files", not unexpected, "\n".join(unexpected) or "approved scope only")

print("POST-V2-17C SYSTEM WORKSPACE OVERSIGHT AUDIT")
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

if failed:
    print("POST-V2-17C RESULT")
    print("FAIL - System Workspace oversight panels did not satisfy all locked checks.")
    raise SystemExit(1)

print("POST-V2-17C RESULT")
print("PASS - System Workspace renders bounded read-only oversight panels with locked ownership, safe aggregate posture, and no exceptional recovery exposure.")
