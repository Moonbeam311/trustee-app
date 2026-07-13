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
SYSTEM_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "system.html"

EXPECTED_BRANCH = "post-v2-planning"
EXPECTED_HEAD = "eed1a62eecffed05be0fe560d317be8203ef27f3"
SYSTEM_RETURN = "admin_ios_workspace"
EXPECTED_PANEL_TITLES = [
    "Protected User Accounts",
    "Application Permission Controls",
    "Authentication and Session Security",
    "Audit and Security Oversight",
    "Backup and Data Preservation",
    "Deployment and Production Health",
    "Database and Migration Posture",
    "Feature Flags and Operating Policy",
    "Institutional Role Assignments",
    "Recovery and Repair Controls",
]
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
ALLOWED_SYSTEM_ROUTES = {
    "/users",
    "/permissions",
    "/security",
    "/audit",
    "/admin/backup/database.zip",
    "/hosted-production-health",
    "/roles",
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
    "confirmed=1",
    "/admin/backup/database ",
]
DESTINATIONS = [
    {
        "name": "Protected User Accounts",
        "route": "/users",
        "function": "users_dashboard",
        "template": "templates/user_dashboard.html",
        "owner_terms": ["Protected User Accounts", "System-owned application account registry"],
        "protection_terms": ["require_master_admin"],
    },
    {
        "name": "Application Permission Controls",
        "route": "/permissions",
        "function": "permissions_dashboard",
        "template": "templates/permissions_dashboard.html",
        "owner_terms": ["Application authorization and permission controls", "Admin", "Trustee", "Viewer"],
        "protection_terms": ["require_master_admin", "validate_csrf_token"],
    },
    {
        "name": "Authentication and Session Security",
        "route": "/security",
        "function": "security_dashboard",
        "template": "templates/security_dashboard.html",
        "owner_terms": ["Authentication and Session Security", "read-only oversight"],
        "protection_terms": ["require_admin"],
    },
    {
        "name": "Audit and Security Oversight",
        "route": "/audit",
        "function": "audit_dashboard",
        "template": "templates/audit_dashboard.html",
        "owner_terms": ["Audit and Security Oversight", "read-only surface"],
        "protection_terms": ["require_admin"],
    },
    {
        "name": "Backup and Data Preservation",
        "route": "/admin/backup/database.zip",
        "function": "admin_database_backup_zip",
        "template": "templates/admin_backup_database_confirm.html",
        "owner_terms": ["Confirm Database Backup Download", "MEDIUM RISK"],
        "protection_terms": ["require_master_admin"],
    },
    {
        "name": "Deployment and Production Health",
        "route": "/hosted-production-health",
        "function": "hosted_production_health",
        "template": "templates/hosted_production_health.html",
        "owner_terms": ["Deployment and Production Health", "sanitized oversight"],
        "protection_terms": ["require_permission"],
    },
    {
        "name": "Institutional Role Assignments",
        "route": "/roles",
        "function": "role_dashboard",
        "template": "templates/role_dashboard.html",
        "owner_terms": ["Institutional Role Assignments", "not application security roles"],
        "protection_terms": ["require_master_admin"],
    },
]
ALLOWED_STATUS_PATHS = {
    "templates/user_dashboard.html",
    "templates/permissions_dashboard.html",
    "templates/security_dashboard.html",
    "templates/audit_dashboard.html",
    "templates/admin_backup_database_confirm.html",
    "templates/hosted_production_health.html",
    "templates/role_dashboard.html",
    "scripts/audit_system_workspace_navigation_17d.py",
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


def read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def record(name, passed, detail=""):
    checks.append((name, bool(passed), str(detail)))


def parse(path):
    return ast.parse(path.read_text(encoding="utf-8"))


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


def route_paths(function_node):
    routes = []
    for decorator in function_node.decorator_list:
        if isinstance(decorator, ast.Call) and call_name(decorator.func) == "route":
            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                routes.append(decorator.args[0].value)
    return routes


def source_segment(source, node):
    return ast.get_source_segment(source, node) if node else ""


def decorator_source(source, node):
    if not node:
        return ""
    return "\n".join(
        ast.get_source_segment(source, decorator) or ""
        for decorator in node.decorator_list
    )


def constant_strings(tree):
    values = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            values.append(node.value)
    return values


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


def hrefs(source):
    return {
        href
        for href in re.findall(r'href=["\']([^"\']+)["\']', source)
        if "{{" not in href and "}}" not in href
    }


def has_system_return_link(source):
    return (
        SYSTEM_RETURN in source
        and "workspace_key='system'" in source
        and "<a" in source
    )


def return_link_non_mutating(source):
    if not has_system_return_link(source):
        return False
    snippets = re.findall(r"<a[^>]+admin_ios_workspace[^>]*>", source, flags=re.I | re.S)
    return bool(snippets) and not any("method=" in snippet.lower() or "submit" in snippet.lower() for snippet in snippets)


def status_lines():
    lines = []
    for line in git("status", "--short").splitlines():
        if not line.strip() or line.lower().startswith("warning:"):
            continue
        lines.append(line)
    return lines


app_text = APP.read_text(encoding="utf-8")
service_text = SERVICE.read_text(encoding="utf-8")
system_text = SYSTEM_TEMPLATE.read_text(encoding="utf-8")
app_tree = ast.parse(app_text)
service_tree = parse(SERVICE)
service_strings = constant_strings(service_tree)
global_auth_source = source_segment(app_text, find_function(app_tree, "enforce_session_timeout"))

record("branch is post-v2-planning", git("branch", "--show-current") == EXPECTED_BRANCH)
record("HEAD is certified POST-V2-17D starting commit", git("rev-parse", "HEAD") == EXPECTED_HEAD)
record("HEAD equals origin/post-v2-planning", git("rev-parse", "HEAD") == git("rev-parse", "origin/post-v2-planning"))

panel_keys = assignment_list(service_tree, "PANEL_KEYS")
record("System panel order preserved", panel_keys == EXPECTED_PANEL_KEYS, panel_keys)
record("System panel titles preserved", all(title in service_text or title in system_text for title in EXPECTED_PANEL_TITLES))

system_routes = {value for value in service_strings if value.startswith("/")}
system_hrefs = hrefs(system_text)
unexpected_system_routes = (system_routes | system_hrefs) - ALLOWED_SYSTEM_ROUTES - {"/admin"}
record("System Workspace exposes only authorized routes", not unexpected_system_routes, sorted(unexpected_system_routes))
non_linked_keys = {"database_migration_posture", "feature_flags_operating_policy", "recovery_repair_controls"}
non_linked_ok = all(key in service_text for key in non_linked_keys)
non_linked_ok = non_linked_ok and all(
    re.search(rf'"{key}"[\s\S]{{0,500}}None,\s*None,', service_text) is not None
    for key in non_linked_keys
)
record("Non-linked panels remain non-linked", non_linked_ok)
record("System Workspace has no mutation forms", "<form" not in system_text.lower() and "method=\"post\"" not in system_text.lower())

all_destination_template_text = ""
destination_results = []

for destination in DESTINATIONS:
    template_text = read(destination["template"])
    all_destination_template_text += "\n" + template_text
    function_node = find_function(app_tree, destination["function"])
    function_source = source_segment(app_text, function_node)
    protection_source = function_source + "\n" + decorator_source(app_text, function_node)
    route_ok = function_node is not None and destination["route"] in route_paths(function_node)
    owner_ok = all(term in template_text for term in destination["owner_terms"])
    if destination["function"] in {"security_dashboard", "audit_dashboard"}:
        protection_ok = (
            "if request.endpoint not in public_endpoints" in global_auth_source
            and "if \"role\" not in session" in global_auth_source
            and destination["function"] not in global_auth_source
        )
    else:
        protection_ok = all(term in protection_source for term in destination["protection_terms"])
    return_present = has_system_return_link(template_text)
    return_non_mutating = return_link_non_mutating(template_text)
    forbidden_present = [route for route in FORBIDDEN_ROUTES if route in template_text]
    destination_results.append(
        {
            "name": destination["name"],
            "route": route_ok,
            "owner": owner_ok,
            "protection": protection_ok,
            "return": return_present,
            "non_mutating": return_non_mutating,
            "exceptional": not forbidden_present,
            "detail": forbidden_present,
        }
    )
    record(f"{destination['name']} correct route", route_ok, destination["route"])
    record(f"{destination['name']} correct owner", owner_ok, destination["owner_terms"])
    record(f"{destination['name']} protection preserved", protection_ok, destination["protection_terms"])
    record(f"{destination['name']} return path present", return_present, destination["template"])
    record(f"{destination['name']} return path non-mutating", return_non_mutating, destination["template"])
    record(f"{destination['name']} exceptional routes excluded", not forbidden_present, forbidden_present)

record("Application Permission Controls associated with /permissions", "/permissions" in service_text and "Application Permission Controls" in service_text)
record("Institutional Role Assignments associated with /roles", "/roles" in service_text and "Institutional Role Assignments" in service_text)
record("role page distinguishes institutional assignments", "not application security roles" in read("templates/role_dashboard.html"))
record("permissions page identifies application authorization", "Application authorization and permission controls" in read("templates/permissions_dashboard.html"))
record("backup System link uses ZIP route only", "/admin/backup/database.zip" in service_text and "/admin/backup/database\"" not in system_text)
record("backup confirmation keeps confirmed link on confirmation screen", "admin_database_backup_zip" in read("templates/admin_backup_database_confirm.html") and "confirmed=1" in read("templates/admin_backup_database_confirm.html"))
record("backup confirmation has System return path", has_system_return_link(read("templates/admin_backup_database_confirm.html")))

combined_templates = system_text + all_destination_template_text
forbidden_template_routes = [route for route in FORBIDDEN_ROUTES if route in combined_templates]
record("Exceptional routes excluded from System and destination templates", not forbidden_template_routes, forbidden_template_routes)
sensitive_present = [token for token in SENSITIVE_TOKENS if token in system_text]
record("Sensitive-data exclusions preserved in System Workspace", not sensitive_present, sensitive_present)

status_text = "\n".join(line.replace("\\", "/") for line in status_lines())
unexpected_status = []
for line in status_lines():
    normalized = line.replace("\\", "/")
    if not any(path in normalized for path in ALLOWED_STATUS_PATHS):
        unexpected_status.append(line)
record("Repository scope preserved", not unexpected_status, "\n".join(unexpected_status) or "approved scope only")

print("POST-V2-17D SYSTEM WORKSPACE NAVIGATION AUDIT")
print("-" * 88)
for result in destination_results:
    print(result["name"])
    print(f"  Correct route: {'PASS' if result['route'] else 'FAIL'}")
    print(f"  Correct owner: {'PASS' if result['owner'] else 'FAIL'}")
    print(f"  Protection preserved: {'PASS' if result['protection'] else 'FAIL'}")
    print(f"  Return path present: {'PASS' if result['return'] else 'FAIL'}")
    print(f"  Return path non-mutating: {'PASS' if result['non_mutating'] else 'FAIL'}")
    print(f"  Exceptional routes excluded: {'PASS' if result['exceptional'] else 'FAIL'}")
    print(f"  Result: {'PASS' if all(result[key] for key in ('route', 'owner', 'protection', 'return', 'non_mutating', 'exceptional')) else 'FAIL'}")
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
    print("POST-V2-17D RESULT")
    print("FAIL - One or more System Workspace drill-down destinations lack correct ownership, protection, orientation, or return-path continuity.")
    raise SystemExit(1)

print("POST-V2-17D RESULT")
print("PASS - System Workspace drill-down navigation preserves ownership, protection, contextual orientation, and return-path continuity.")
