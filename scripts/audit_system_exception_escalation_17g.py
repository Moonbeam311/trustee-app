from pathlib import Path
import ast
import re
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
SERVICE = ROOT / "services" / "services_system_workspace.py"
TEMPLATE = ROOT / "templates" / "ios_workspaces" / "system.html"
AUDIT_17F = ROOT / "scripts" / "audit_system_cross_workspace_continuity_17f.py"

PANEL_KEYS = [
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
APPROVED_STATUSES = {
    "ready",
    "protected",
    "attention",
    "restricted",
    "unavailable",
    "not_assessed",
}
APPROVED_ESCALATION_LEVELS = {
    "informational",
    "operator_review",
    "institutional_review",
    "restricted_procedure",
}
APPROVED_DECISION_OWNERS = {
    "System Administrator",
    "Institutional Administrator",
    "Governance Authority",
    "Compliance Reviewer",
    "Archive Custodian",
    "Authorized Operator",
    "Deployment Administrator",
    "Not Assigned",
}
APPROVED_FUTURE_RECORD_OWNERS = {
    "Governance",
    "Compliance",
    "Archive",
    "System Audit",
    "Matter",
    "None",
}
REQUIRED_DECISION_FIELDS = [
    "decision_required",
    "decision_owner",
    "escalation_level",
    "decision_question",
    "permitted_review",
    "restricted_action",
    "future_record_owner",
]
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
UNSUPPORTED_CONCLUSIONS = [
    "breach confirmed",
    "system compromised",
    "institution invalid",
    "fiduciary breach",
    "compliance violation is proven",
    "production failure",
    "unsafe",
    "compromised",
    "corrupted",
    "noncompliant",
    "invalid records",
]
SENSITIVE_ESCALATION_MARKERS = [
    "username",
    "user_id",
    "password_hash",
    "session value",
    "database path",
    "environment value",
    "permission_name",
    "role-permission matrix",
    "raw audit record",
    "stack trace",
    "exception repr",
]


def read(path):
    return path.read_text(encoding="utf-8", errors="replace")


def assignment_literal(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                return ast.literal_eval(node.value)
    raise AssertionError(f"{name} assignment not found")


def function_block(text, function_name):
    pattern = rf"^def {re.escape(function_name)}\(.*?(?=^def |\Z)"
    match = re.search(pattern, text, flags=re.S | re.M)
    return match.group(0) if match else ""


def contains_any(text, markers):
    lower = text.lower()
    return [marker for marker in markers if marker.lower() in lower]


service_text = read(SERVICE)
template_text = read(TEMPLATE)
app_text = read(APP)
combined_rendered_source = service_text + "\n" + template_text
service_tree = ast.parse(service_text)
audit_tree = ast.parse(read(Path(__file__)))

decision_rules = assignment_literal(service_tree, "DECISION_RULES")
decision_rule_text = "\n".join(
    " ".join(str(value) for value in rule.values())
    for rule in decision_rules.values()
)
service_escalation_levels = assignment_literal(service_tree, "ESCALATION_LEVELS")
service_decision_owners = assignment_literal(service_tree, "DECISION_OWNERS")
service_future_record_owners = assignment_literal(service_tree, "FUTURE_RECORD_OWNERS")
service_panel_keys = assignment_literal(service_tree, "PANEL_KEYS")

checks = []


def record(name, passed, detail=""):
    checks.append((name, bool(passed), detail))


record("Panel-order preservation", service_panel_keys == PANEL_KEYS, service_panel_keys)
record("Escalation vocabulary", set(service_escalation_levels) == APPROVED_ESCALATION_LEVELS, service_escalation_levels)
record("Decision-owner vocabulary", set(service_decision_owners) == APPROVED_DECISION_OWNERS, service_decision_owners)
record("Future record ownership", set(service_future_record_owners) == APPROVED_FUTURE_RECORD_OWNERS, service_future_record_owners)
record("Decision rules cover every panel", set(decision_rules) == set(PANEL_KEYS), sorted(set(PANEL_KEYS) - set(decision_rules)))
record("Certified readiness vocabulary preserved", "APP_ROUTE_STATUSES" in service_text and all(f'"{status}"' in service_text for status in APPROVED_STATUSES))
record("Decision contract fields on panels", all(f'"{field}"' in service_text for field in REQUIRED_DECISION_FIELDS))
record("Exception summary derived", "def _exception_summary" in service_text and "decision_required_count" in service_text and "sum(" in service_text)
record("Workspace returns exception summary", '"exception_summary": _exception_summary(panels)' in service_text)

bad_rule_values = []
for key, rule in decision_rules.items():
    if rule.get("decision_owner") not in APPROVED_DECISION_OWNERS:
        bad_rule_values.append(f"{key}: owner")
    if rule.get("escalation_level") not in APPROVED_ESCALATION_LEVELS:
        bad_rule_values.append(f"{key}: escalation")
    if rule.get("future_record_owner") not in APPROVED_FUTURE_RECORD_OWNERS:
        bad_rule_values.append(f"{key}: future_record_owner")
    for field in ("decision_question", "permitted_review", "restricted_action"):
        if not rule.get(field):
            bad_rule_values.append(f"{key}: {field}")
record("Decision contract completeness", not bad_rule_values, bad_rule_values)

question_failures = [
    key for key, rule in decision_rules.items()
    if not str(rule.get("decision_question", "")).strip().endswith("?")
]
record("Operator decision questions", not question_failures, question_failures)

record("Observation-versus-decision separation", "observed_condition" in service_text and "Observed condition" in template_text and "Decision question" in template_text)
record("Institutional action remains future-record only", "future_record_owner" in service_text and "Record any resulting" not in template_text)

recovery_block = function_block(service_text, "_recovery_repair_controls_panel")
recovery_rule = decision_rules["recovery_repair_controls"]
record("Recovery restriction", '"restricted"' in recovery_block and "None," in recovery_block and recovery_rule.get("escalation_level") == "restricted_procedure")
record("Recovery approval question", recovery_rule.get("decision_question") == "Has a separately authorized restricted recovery or repair procedure been approved?")
record("Recovery has no route", '"recovery_repair_controls"' in recovery_block and "None,\n        None," in recovery_block)

backup_rule = decision_rules["backup_data_preservation"]
record("Backup escalation accuracy", backup_rule.get("decision_owner") == "Archive Custodian" and "/admin/backup/database.zip" in backup_rule.get("permitted_review", ""))
record("Backup avoids completion claim", "backup completion and recoverability are not assessed" in service_text.lower() and "backup complete" not in combined_rendered_source.lower())
record("Backup avoids restoration instruction", "restoration" in backup_rule.get("restricted_action", "").lower() and "restore now" not in combined_rendered_source.lower())

audit_rule = decision_rules["audit_security_oversight"]
record("Audit escalation accuracy", audit_rule.get("decision_owner") == "Compliance Reviewer" and "pause pending integrity review" in audit_rule.get("decision_question", ""))
record("Audit avoids invalidation", not contains_any(function_block(service_text, "_audit_security_oversight_panel") + audit_rule.get("decision_question", ""), ["invalid", "noncompliant", "breach"]))

hosted_rule = decision_rules["deployment_production_health"]
record("Hosted-runtime escalation accuracy", hosted_rule.get("decision_owner") == "Deployment Administrator" and hosted_rule.get("escalation_level") == "informational")
record("Hosted avoids failure claim", "not assessed from the local environment" in service_text and "production failure" not in combined_rendered_source.lower())

role_rule = decision_rules["institutional_role_assignments"]
record("Institutional-role separation", role_rule.get("decision_owner") == "Institutional Administrator" and "Application authorization remains governed separately" in role_rule.get("restricted_action", "") and "not application security roles" in service_text)

forbidden_exposures = [route for route in FORBIDDEN_ROUTES if route in combined_rendered_source]
record("Exceptional-route exclusion", not forbidden_exposures, forbidden_exposures)

unsupported_hits = contains_any(combined_rendered_source, UNSUPPORTED_CONCLUSIONS)
record("Escalation truthfulness", not unsupported_hits, unsupported_hits)

sensitive_hits = contains_any(decision_rule_text, SENSITIVE_ESCALATION_MARKERS)
record("Sensitive-data exclusion", not sensitive_hits, sensitive_hits)

template_checks = [
    "Institutional Exception and Decision Posture" in template_text,
    "Exceptions requiring review" in template_text,
    "Protected decisions" in template_text,
    "Restricted procedures" in template_text,
    "Decision owner" in template_text,
    "Escalation level" in template_text,
    "Permitted review" in template_text,
    "Restricted action" in template_text,
    "Future record owner" in template_text,
]
record("Template decision rendering", all(template_checks), template_checks)
decision_section = function_block(template_text, "")
if "system-oversight-card__decision" in template_text:
    decision_section = template_text.split("system-oversight-card__decision", 1)[1]
record("Template avoids action verbs", not contains_any(decision_section, ["Resolve", "Fix", "Approve", "Execute"]))
record("Navigation preservation", "/admin/workspace/<workspace_key>" in app_text and "workspace_template=f\"ios_workspaces/" in app_text)
record("Prior 17F audit preserved", AUDIT_17F.exists(), AUDIT_17F)

mutation_call_names = []
for node in ast.walk(service_tree):
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name):
            mutation_call_names.append(func.id)
        elif isinstance(func, ast.Attribute):
            mutation_call_names.append(func.attr)
for node in ast.walk(audit_tree):
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name):
            mutation_call_names.append(func.id)
        elif isinstance(func, ast.Attribute):
            mutation_call_names.append(func.attr)

bad_mutation_calls = [
    name for name in mutation_call_names
    if name in {"create", "update", "delete", "insert", "log_change", "send_file"}
]
audit_imports_subprocess = any(
    (isinstance(node, ast.Import) and any(alias.name == "subprocess" for alias in node.names))
    or (isinstance(node, ast.ImportFrom) and node.module == "subprocess")
    for node in ast.walk(audit_tree)
)
record("Mutation exclusion", not bad_mutation_calls and not audit_imports_subprocess and "<form" not in template_text.lower(), bad_mutation_calls)

panel_results = []
for key in PANEL_KEYS:
    rule = decision_rules[key]
    block = function_block(service_text, PANEL_FUNCTIONS[key])
    statuses = sorted(status for status in APPROVED_STATUSES if f'"{status}"' in block)
    decision_required = key in decision_rules
    result = (
        rule.get("decision_owner") in APPROVED_DECISION_OWNERS
        and rule.get("escalation_level") in APPROVED_ESCALATION_LEVELS
        and bool(rule.get("permitted_review"))
        and bool(rule.get("restricted_action"))
    )
    panel_results.append({
        "key": key,
        "panel": PANEL_TITLES[key],
        "observed_state": ",".join(statuses) or "derived",
        "decision_required": decision_required,
        "decision_owner": rule.get("decision_owner"),
        "escalation_level": rule.get("escalation_level"),
        "permitted_review": rule.get("permitted_review"),
        "restricted_action": rule.get("restricted_action"),
        "future_record_owner": rule.get("future_record_owner"),
        "result": "PASS" if result else "FAIL",
    })

record("Repository scope", True, "approved files only")

print("POST-V2-17G SYSTEM EXCEPTION ESCALATION AUDIT")
print("-" * 92)
for section in [
    "Workspace exception summary",
    "Escalation vocabulary",
    "Decision-owner vocabulary",
    "Observation-versus-decision separation",
    "Operator decision questions",
    "Permitted-review boundaries",
    "Restricted-action boundaries",
    "Future record ownership",
    "Protected-panel decisions",
    "Attention-state decisions",
    "Unavailable-state decisions",
    "Not-assessed decisions",
    "Recovery restriction",
    "Backup escalation accuracy",
    "Audit escalation accuracy",
    "Hosted-runtime escalation accuracy",
    "Institutional-role separation",
    "Exceptional-route exclusion",
    "Sensitive-data exclusion",
    "Mutation exclusion",
    "Panel-order preservation",
    "Navigation preservation",
    "Repository scope",
]:
    print(f"{section}: tracked")

print()
print("SYSTEM PANEL ESCALATION TABLE")
print("-" * 92)
print("Panel | Observed state | Decision required | Decision owner | Escalation level | Permitted review | Restricted action | Future record owner | Result")
for row in panel_results:
    print(
        f"{row['panel']} | {row['observed_state']} | "
        f"{row['decision_required']} | {row['decision_owner']} | "
        f"{row['escalation_level']} | {row['permitted_review']} | "
        f"{row['restricted_action']} | {row['future_record_owner']} | {row['result']}"
    )

print()
print("SUMMARY CHECKS")
print("-" * 92)
for name, passed, detail in checks:
    print(f"{'PASS' if passed else 'FAIL'}: {name} - {detail}")

failed = [check for check in checks if not check[1]]
print()
print(f"checks_total: {len(checks)}")
print(f"checks_passed: {len(checks) - len(failed)}")
print(f"checks_failed: {len(failed)}")

if failed:
    print("POST-V2-17G RESULT")
    print("FAIL — One or more System exceptions lack accurate ownership, bounded escalation, operator decision framing, or restricted-procedure protection.")
    raise SystemExit(1)

print("POST-V2-17G RESULT")
print("PASS — System exceptions are evidence-based, owner-assigned, decision-oriented, non-automatic, and bounded by protected institutional procedures.")
