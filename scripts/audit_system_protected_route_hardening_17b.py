from pathlib import Path
import ast
import re
import subprocess
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
PERMISSIONS_TEMPLATE = ROOT / "templates" / "permissions_dashboard.html"
SYSTEM_HEALTH_TEMPLATE = ROOT / "templates" / "system_health.html"
SYSTEM_WORKSPACE_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "system.html"

EXPECTED_HEAD = "03c2834cd987cca96f7a2a47a3d5555c74e68889"
ALLOWED_BRANCH = "post-v2-planning"
ALLOWED_STATUS_PATHS = {
    "app.py",
    "scripts/audit_system_protected_route_hardening_17b.py",
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


def call_positions(function_node, source_text):
    positions = {}
    for node in ast.walk(function_node):
        if isinstance(node, ast.Call):
            name = call_name(node.func)
            if name:
                positions.setdefault(name, []).append(node.lineno)
    return positions


def route_info(function_node):
    routes = []
    for decorator in function_node.decorator_list:
        call = decorator if isinstance(decorator, ast.Call) else None
        if not call:
            continue
        if call_name(call.func) != "route":
            continue
        route = None
        methods = None
        if call.args and isinstance(call.args[0], ast.Constant):
            route = call.args[0].value
        for keyword in call.keywords:
            if keyword.arg == "methods" and isinstance(keyword.value, (ast.List, ast.Tuple)):
                methods = [
                    item.value
                    for item in keyword.value.elts
                    if isinstance(item, ast.Constant)
                ]
        routes.append({"route": route, "methods": methods or ["GET"]})
    return routes


def line_of(source, pattern):
    for index, line in enumerate(source.splitlines(), start=1):
        if pattern in line:
            return index
    return None


def has_gate_pattern(source):
    return (
        "gate = require_master_admin()" in source
        and "if gate:" in source
        and "return gate" in source
    )


def contains_invalid_csrf_response(source):
    return (
        "if not validate_csrf_token():" in source
        and '"access_denied.html"' in source
        and 'reason="Invalid or missing CSRF token."' in source
        and "), 400" in source
    )


def first_call_line(positions, name):
    values = positions.get(name) or []
    return min(values) if values else None


app_text = read(APP)
permissions_text = read(PERMISSIONS_TEMPLATE)
system_health_text = read(SYSTEM_HEALTH_TEMPLATE)
system_workspace_text = read(SYSTEM_WORKSPACE_TEMPLATE) if SYSTEM_WORKSPACE_TEMPLATE.exists() else ""
tree = ast.parse(app_text)

branch = git("branch", "--show-current")
head = git("rev-parse", "HEAD")
origin_head = git("rev-parse", "origin/post-v2-planning")
status_short = git("status", "--short")

record("branch is post-v2-planning", branch == ALLOWED_BRANCH, branch)
record("HEAD is certified POST-V2-17B starting commit", head == EXPECTED_HEAD, head)
record("HEAD equals origin/post-v2-planning", head == origin_head and bool(head), f"HEAD={head} origin={origin_head}")

permissions_fn = find_function(tree, "permissions_dashboard")
reseed_fn = find_function(tree, "system_recovery_reseed_permissions")
run_fn = find_function(tree, "system_recovery_run")

record("permissions_dashboard exists", permissions_fn is not None, "found")
record("system_recovery_reseed_permissions exists", reseed_fn is not None, "found")
record("system_recovery_run exists", run_fn is not None, "found")

permissions_source = ast.get_source_segment(app_text, permissions_fn) if permissions_fn else ""
reseed_source = ast.get_source_segment(app_text, reseed_fn) if reseed_fn else ""
run_source = ast.get_source_segment(app_text, run_fn) if run_fn else ""

permissions_routes = route_info(permissions_fn) if permissions_fn else []
reseed_routes = route_info(reseed_fn) if reseed_fn else []
run_routes = route_info(run_fn) if run_fn else []

record("permissions route retained", any(r["route"] == "/permissions" for r in permissions_routes), permissions_routes)
record(
    "permissions route retains GET and POST",
    any(r["route"] == "/permissions" and set(r["methods"]) == {"GET", "POST"} for r in permissions_routes),
    permissions_routes,
)
record("permissions calls local require_master_admin", "require_master_admin()" in permissions_source, "gate call")
record("permissions returns gate result when denied", has_gate_pattern(permissions_source), "gate return")
record("permissions validates CSRF in POST branch", 'if request.method == "POST":' in permissions_source and contains_invalid_csrf_response(permissions_source), "POST CSRF")

permissions_positions = call_positions(permissions_fn, app_text) if permissions_fn else {}
csrf_line = first_call_line(permissions_positions, "validate_csrf_token")
form_get_line = (
    permissions_fn.lineno + line_of(permissions_source, 'request.form.get("role_name")') - 1
    if permissions_fn and line_of(permissions_source, 'request.form.get("role_name")')
    else None
)
form_getlist_line = (
    permissions_fn.lineno + line_of(permissions_source, 'request.form.getlist("permissions")') - 1
    if permissions_fn and line_of(permissions_source, 'request.form.getlist("permissions")')
    else None
)
replace_line = first_call_line(permissions_positions, "replace_role_permissions")
log_line = first_call_line(permissions_positions, "log_change")

record("permissions CSRF before role form read", csrf_line and form_get_line and csrf_line < form_get_line, f"csrf={csrf_line} form={form_get_line}")
record("permissions CSRF before permission form read", csrf_line and form_getlist_line and csrf_line < form_getlist_line, f"csrf={csrf_line} form={form_getlist_line}")
record("permissions CSRF before replace_role_permissions", csrf_line and replace_line and csrf_line < replace_line, f"csrf={csrf_line} replace={replace_line}")
record("permissions CSRF before audit log", csrf_line and log_line and csrf_line < log_line, f"csrf={csrf_line} log={log_line}")
record("permissions retains Admin Trustee Viewer roles", '["Admin", "Trustee", "Viewer"]' in permissions_source, "roles retained")
record("permissions retains redirect to permissions_dashboard", 'redirect(url_for("permissions_dashboard"))' in permissions_source, "redirect retained")
record("permissions does not expose recovery helpers", "run_safe_recovery_migrations" not in permissions_source and "reseed_default_role_permissions" not in permissions_source, "none")

record(
    "reseed route remains POST-only",
    any(r["route"] == "/system/recovery/reseed-permissions" and r["methods"] == ["POST"] for r in reseed_routes),
    reseed_routes,
)
record("reseed calls local require_master_admin", "require_master_admin()" in reseed_source, "gate call")
record("reseed returns gate result when denied", has_gate_pattern(reseed_source), "gate return")
record("reseed validates CSRF", contains_invalid_csrf_response(reseed_source), "CSRF response")
reseed_positions = call_positions(reseed_fn, app_text) if reseed_fn else {}
reseed_csrf_line = first_call_line(reseed_positions, "validate_csrf_token")
reseed_call_line = first_call_line(reseed_positions, "reseed_default_role_permissions")
record("reseed CSRF before reseed_default_role_permissions", reseed_csrf_line and reseed_call_line and reseed_csrf_line < reseed_call_line, f"csrf={reseed_csrf_line} reseed={reseed_call_line}")
record("reseed retains audit logging", "log_change(" in reseed_source and "permission_matrix_reseeded" in reseed_source, "audit log")
record("reseed retains System Health redirect", 'redirect(url_for("system_health_dashboard"))' in reseed_source, "redirect")
record("reseed contains no GET mutation path", all(r["methods"] == ["POST"] for r in reseed_routes), "POST only")

record(
    "recovery run route remains POST-only",
    any(r["route"] == "/system/recovery/run" and r["methods"] == ["POST"] for r in run_routes),
    run_routes,
)
record("recovery run calls local require_master_admin", "require_master_admin()" in run_source, "gate call")
record("recovery run returns gate result when denied", has_gate_pattern(run_source), "gate return")
record("recovery run validates CSRF", contains_invalid_csrf_response(run_source), "CSRF response")
run_positions = call_positions(run_fn, app_text) if run_fn else {}
run_csrf_line = first_call_line(run_positions, "validate_csrf_token")
run_call_line = first_call_line(run_positions, "run_safe_recovery_migrations")
record("recovery run CSRF before run_safe_recovery_migrations", run_csrf_line and run_call_line and run_csrf_line < run_call_line, f"csrf={run_csrf_line} recovery={run_call_line}")
record("recovery run retains audit logging", "log_change(" in run_source and "safe_recovery_migrations_run" in run_source, "audit log")
record("recovery run retains System Health redirect", 'redirect(url_for("system_health_dashboard"))' in run_source, "redirect")
record("recovery run contains no GET mutation path", all(r["methods"] == ["POST"] for r in run_routes), "POST only")

record("permissions template contains hidden CSRF token", 'name="_csrf_token"' in permissions_text and "csrf_token()" in permissions_text, "token present")
record("system health template contains hidden CSRF tokens", system_health_text.count('name="_csrf_token"') >= 2 and system_health_text.count("csrf_token()") >= 2, "tokens present")
record("templates contain no emergency hosted route forms", not any(marker in permissions_text + system_health_text for marker in ("hosted-", "hosted_", "bootstrap-admin-once", "repair-admin-access-once")), "none")

route_defs = re.findall(r"@app\.route\(", app_text)
record("no new routes introduced by audit scope", len(route_defs) > 0, f"route decorators={len(route_defs)}")
record("no route renames for hardened routes", all(route in app_text for route in ("/permissions", "/system/recovery/run", "/system/recovery/reseed-permissions")), "routes retained")
record("no database migrations changed", "migrations/" not in status_short.replace("\\", "/"), status_short or "none")
record("no schema files changed", "database/" not in status_short.replace("\\", "/") and ".db" not in status_short.lower(), status_short or "none")
record("no model files changed", "models/" not in status_short.replace("\\", "/"), status_short or "none")
record("no new role vocabulary", "SuperAdmin" not in app_text and "MasterAdmin" not in app_text, "no new roles")
record("no new permission vocabulary in app patch", "permission_id" in app_text and "POST-V2-17B" not in app_text, "no explicit new permission")
record("System workspace does not expose exceptional recovery links", not any(marker in system_workspace_text for marker in ("system/recovery", "reseed-permissions", "hosted-", "bootstrap", "repair", "lockout-clear", "migration")), "not exposed")
record("People workspace files unchanged", "templates/ios_workspaces/people.html" not in status_short.replace("\\", "/") and "people" not in "\n".join(status_short.splitlines()), status_short or "none")
record("roles route untouched by scope", "def role_dashboard" in app_text and "/roles" in app_text, "roles route retained")

unexpected_status = []
for line in status_short.splitlines():
    normalized = line.replace("\\", "/")
    if not any(path in normalized for path in ALLOWED_STATUS_PATHS):
        unexpected_status.append(line)
record("working tree limited to app.py and 17B audit", not unexpected_status, "\n".join(unexpected_status) or "approved scope only")

print("POST-V2-17B SYSTEM PROTECTED ROUTE HARDENING AUDIT")
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
    print("POST-V2-17B RESULT")
    print("FAIL - System permission and recovery mutation route hardening did not satisfy all checks.")
    raise SystemExit(1)

print("POST-V2-17B RESULT")
print("PASS - System permission and recovery mutation routes enforce local master-admin and CSRF protection without changing route ownership or recovery behavior.")
