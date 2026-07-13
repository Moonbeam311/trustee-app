import inspect
import json
import sqlite3
from pathlib import Path

from flask import current_app

from database.db import get_connection, verify_audit_log_chain


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

CRITICAL_PANEL_KEYS = {
    "protected_user_accounts",
    "application_permission_controls",
    "authentication_session_security",
    "audit_security_oversight",
    "backup_data_preservation",
    "deployment_production_health",
    "database_migration_posture",
    "feature_flags_operating_policy",
}

EXPECTED_CORE_TABLES = {
    "trusts",
    "app_users",
    "user_roles",
    "audit_log",
    "documents",
    "media",
}

POLICY_PATH = Path("data") / "export_policy.json"
APP_ROLES = ("Admin", "Trustee", "Viewer")
APP_ROUTE_STATUSES = {
    "ready",
    "protected",
    "attention",
    "restricted",
    "unavailable",
    "not_assessed",
}


def _metric(label, value):
    return {"label": label, "value": value}


def _label(status):
    return status.replace("_", " ").title()


def _panel(
    key,
    title,
    summary,
    status,
    route,
    action_label,
    exposure,
    owner,
    warning=None,
    metrics=None,
    exception_state=False,
    exception_label=None,
    operator_guidance=None,
):
    if status not in APP_ROUTE_STATUSES:
        status = "not_assessed"

    return {
        "key": key,
        "title": title,
        "summary": summary,
        "status": status,
        "status_label": _label(status),
        "route": route,
        "action_label": action_label,
        "exposure": exposure,
        "owner": owner,
        "warning": warning,
        "metrics": metrics or [],
        "exception_state": bool(exception_state),
        "exception_label": exception_label,
        "operator_guidance": operator_guidance,
    }


def _route_available(route):
    try:
        return route in {rule.rule for rule in current_app.url_map.iter_rules()}
    except Exception:
        return False


def _endpoint_source(endpoint_name):
    try:
        view = current_app.view_functions.get(endpoint_name)
        return inspect.getsource(view) if view else ""
    except Exception:
        return ""


def _route_endpoint(route):
    try:
        for rule in current_app.url_map.iter_rules():
            if rule.rule == route:
                return rule.endpoint
    except Exception:
        return None
    return None


def _endpoint_has(route, markers):
    endpoint = _route_endpoint(route)
    source = _endpoint_source(endpoint) if endpoint else ""
    return bool(source) and all(marker in source for marker in markers)


def _count_rows(table_name):
    conn = get_connection()
    try:
        row = conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
        return int(row["count"] if row else 0)
    finally:
        conn.close()


def _protected_user_accounts_panel():
    route = "/users"
    route_exists = _route_available(route)
    has_gate = _endpoint_has(route, ("require_master_admin",))

    try:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT LOWER(COALESCE(status, '')) AS status_value, COUNT(*) AS count
                FROM app_users
                GROUP BY LOWER(COALESCE(status, ''))
                """
            ).fetchall()
        finally:
            conn.close()

        active = 0
        inactive = 0
        malformed = 0
        total = 0
        for row in rows:
            status_value = row["status_value"]
            count = int(row["count"])
            total += count
            if status_value == "active":
                active += count
            elif status_value in {"inactive", "disabled", "suspended"}:
                inactive += count
            else:
                malformed += count

        if not route_exists:
            status = "unavailable"
            guidance = "Review System route registration before relying on account oversight."
        elif malformed:
            status = "attention"
            guidance = "Review the protected user registry."
        elif has_gate:
            status = "ready"
            guidance = "Use the protected registry for account-level review."
        else:
            status = "attention"
            guidance = "Review the account route boundary before operator use."

        return _panel(
            "protected_user_accounts",
            "Protected User Accounts",
            "Application account registry aggregates were read without exposing individual account details.",
            status,
            route if route_exists else None,
            "Open Protected User Accounts" if route_exists else None,
            "Protected administrative destination",
            "System",
            metrics=[
                _metric("Registry readable", "Yes"),
                _metric("Total application accounts", total),
                _metric("Active accounts", active),
                _metric("Inactive accounts", inactive),
                _metric("Aggregate status review", "Attention" if malformed else "Bounded"),
                _metric("Master-admin boundary", "Present" if has_gate else "Attention"),
            ],
            exception_state=status != "ready",
            exception_label="Review required" if status == "attention" else ("Unavailable" if status == "unavailable" else None),
            operator_guidance=guidance,
        )
    except Exception:
        return _panel(
            "protected_user_accounts",
            "Protected User Accounts",
            "Application account registry aggregates could not be safely read.",
            "unavailable",
            route if route_exists else None,
            "Open Protected User Accounts" if route_exists else None,
            "Protected administrative destination",
            "System",
            metrics=[
                _metric("Registry readable", "No"),
                _metric("Master-admin boundary", "Present" if has_gate else "Not assessed"),
            ],
            exception_state=True,
            exception_label="Unavailable",
            operator_guidance="Review the protected user registry.",
        )


def _application_permission_controls_panel():
    route = "/permissions"
    route_exists = _route_available(route)
    has_master_gate = _endpoint_has(route, ("require_master_admin",))
    has_form_check = _endpoint_has(route, ("validate_csrf",))
    status = "protected"
    guidance = "Use the protected permission surface for application authorization changes."
    if not route_exists:
        status = "unavailable"
        guidance = "Review System route registration before relying on permission controls."
    elif not (has_master_gate and has_form_check):
        status = "attention"
        guidance = "Review the protected permission route boundary."

    return _panel(
        "application_permission_controls",
        "Application Permission Controls",
        "The permission matrix is intentionally not summarized here; this panel confirms the protected authorization boundary.",
        status,
        route if route_exists else None,
        "Open Permission Controls" if route_exists else None,
        "High-risk protected administrative destination",
        "System",
        warning="High-risk protected administration. The permission matrix is not summarized in this workspace.",
        metrics=[
            _metric("Route registered", "Yes" if route_exists else "No"),
            _metric("Master-admin boundary", "Present" if has_master_gate else "Attention"),
            _metric("Form safety check", "Present" if has_form_check else "Attention"),
            _metric("Application role vocabulary", ", ".join(APP_ROLES)),
            _metric("Matrix summary", "Excluded"),
        ],
        exception_state=status != "protected",
        exception_label="Review required" if status == "attention" else ("Unavailable" if status == "unavailable" else "Protected boundary"),
        operator_guidance=guidance,
    )


def _authentication_session_security_panel():
    route = "/security"
    route_exists = _route_available(route)
    global_guard = _endpoint_source("enforce_session_timeout")
    headers = _endpoint_source("apply_security_headers")
    controls = {
        "Global authentication guard": '"role" not in session' in global_guard,
        "Session timeout logic": "SESSION_TIMEOUT_SECONDS" in global_guard and "last_activity" in global_guard,
        "Form safety helper": "def validate_csrf" in _source_app_text(),
        "Security headers": "X-Frame-Options" in headers and "Content-Security-Policy" in headers,
    }

    if not route_exists:
        status = "unavailable"
        guidance = "Review System route registration before relying on security oversight."
    elif all(controls.values()):
        status = "ready"
        guidance = "Use Security Oversight for structural control review."
    else:
        status = "attention"
        guidance = "Review missing structural control evidence before relying on this posture."

    return _panel(
        "authentication_session_security",
        "Authentication and Session Security",
        "Required structural controls are present when all bounded checks pass; this is not a complete security certification.",
        status,
        route if route_exists else None,
        "Open Security Oversight" if route_exists else None,
        "Read-only oversight",
        "System",
        metrics=[_metric(name, "Present" if present else "Attention") for name, present in controls.items()],
        exception_state=status != "ready",
        exception_label="Review required" if status == "attention" else ("Unavailable" if status == "unavailable" else None),
        operator_guidance=guidance,
    )


def _audit_security_oversight_panel():
    route = "/audit"
    route_exists = _route_available(route)
    if not route_exists:
        return _panel(
            "audit_security_oversight",
            "Audit and Security Oversight",
            "Audit oversight route is unavailable.",
            "unavailable",
            None,
            None,
            "Read-only oversight",
            "System / Evidence",
            metrics=[_metric("Audit route", "No")],
            exception_state=True,
            exception_label="Unavailable",
            operator_guidance="Review audit route registration.",
        )

    try:
        result = verify_audit_log_chain()
        broken = int(result.get("broken") or 0)
        status = "ready" if str(result.get("status")) == "VERIFIED" and broken == 0 else "attention"
        return _panel(
            "audit_security_oversight",
            "Audit and Security Oversight",
            "Audit integrity posture is summarized using aggregate counts only.",
            status,
            route,
            "Open Audit Oversight",
            "Read-only oversight",
            "System / Evidence",
            metrics=[
                _metric("Audit route", "Yes"),
                _metric("Integrity status", "Bounded pass" if status == "ready" else "Attention"),
                _metric("Checked count", int(result.get("checked") or 0)),
                _metric("Broken count", broken),
                _metric("Legacy count", int(result.get("legacy") or 0)),
            ],
            exception_state=status != "ready",
            exception_label="Review required" if status == "attention" else None,
            operator_guidance="Open Audit Oversight to review integrity posture.",
        )
    except Exception:
        return _panel(
            "audit_security_oversight",
            "Audit and Security Oversight",
            "Audit integrity could not be assessed without exposing raw diagnostics.",
            "not_assessed",
            route,
            "Open Audit Oversight",
            "Read-only oversight",
            "System / Evidence",
            metrics=[_metric("Integrity status", "Not assessed")],
            exception_state=True,
            exception_label="Not assessed",
            operator_guidance="Open Audit Oversight to review available audit posture.",
        )


def _backup_data_preservation_panel():
    route = "/admin/backup/database.zip"
    route_exists = _route_available(route)
    has_gate = _endpoint_has(route, ("require_master_admin",))
    has_confirmation = _endpoint_has(route, ("confirmed", "admin_backup_database_confirm"))
    if not route_exists:
        status = "unavailable"
        guidance = "Review backup route registration before relying on backup access."
    elif has_gate and has_confirmation:
        status = "protected"
        guidance = "Use the existing protected backup confirmation flow when an authorized backup is required."
    else:
        status = "attention"
        guidance = "Review the backup confirmation boundary before operator use."

    return _panel(
        "backup_data_preservation",
        "Backup and Data Preservation",
        "Protected backup access is available; backup completion and recoverability are not assessed here.",
        status,
        route if route_exists else None,
        "Open Backup Confirmation" if route_exists else None,
        "Protected download with existing confirmation boundary",
        "System / Archive",
        warning="Protected database-copy download. Existing master-admin and confirmation boundaries remain required.",
        metrics=[
            _metric("ZIP route registered", "Yes" if route_exists else "No"),
            _metric("Master-admin boundary", "Present" if has_gate else "Attention"),
            _metric("Confirmation boundary", "Present" if has_confirmation else "Attention"),
            _metric("Completion evidence", "Not assessed"),
            _metric("Recoverability evidence", "Not assessed"),
        ],
        exception_state=status != "protected",
        exception_label="Review required" if status == "attention" else ("Unavailable" if status == "unavailable" else "Protected boundary"),
        operator_guidance=guidance,
    )


def _deployment_production_health_panel():
    route = "/hosted-production-health"
    route_exists = _route_available(route)
    has_permission_gate = _endpoint_has(route, ("require_permission",))
    if not route_exists:
        status = "unavailable"
        guidance = "Review hosted health route registration."
    elif not has_permission_gate:
        status = "attention"
        guidance = "Review the hosted health permission boundary."
    else:
        status = "not_assessed"
        guidance = "Hosted runtime posture is not assessed from the local environment."

    return _panel(
        "deployment_production_health",
        "Deployment and Production Health",
        "Local structural routing is visible, but hosted runtime readiness is not concluded from this workspace.",
        status,
        route if route_exists else None,
        "Open Production Health" if route_exists else None,
        "Sanitized oversight",
        "System / Deployment",
        metrics=[
            _metric("Route registered", "Yes" if route_exists else "No"),
            _metric("Permission boundary", "Present" if has_permission_gate else "Attention"),
            _metric("Local structural posture", "Reviewable" if route_exists else "Unavailable"),
            _metric("Hosted runtime posture", "Not assessed locally"),
        ],
        exception_state=True,
        exception_label="Not assessed" if status == "not_assessed" else ("Review required" if status == "attention" else "Unavailable"),
        operator_guidance=guidance,
    )


def _database_migration_posture_panel():
    try:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        finally:
            conn.close()
        table_names = {row["name"] for row in rows}
        missing = sorted(EXPECTED_CORE_TABLES - table_names)
        status = "ready" if not missing else "attention"
        return _panel(
            "database_migration_posture",
            "Database and Migration Posture",
            "Database posture is inspected read-only without invoking repair or migration helpers.",
            status,
            None,
            None,
            "Read-only status only",
            "System / Database",
            metrics=[
                _metric("Database reachable", "Yes"),
                _metric("Expected core tables", "Present" if not missing else "Attention required"),
                _metric("Schema review", "Read-only bounded table check"),
                _metric("Migration action", "Not invoked"),
            ],
            exception_state=status != "ready",
            exception_label="Review required" if status == "attention" else None,
            operator_guidance="Review database posture through an approved maintenance process." if status == "attention" else "No database action is invoked from this workspace.",
        )
    except sqlite3.Error:
        return _panel(
            "database_migration_posture",
            "Database and Migration Posture",
            "Database posture could not be inspected through a safe read-only connection.",
            "unavailable",
            None,
            None,
            "Read-only status only",
            "System / Database",
            metrics=[
                _metric("Database reachable", "No"),
                _metric("Schema review", "Unavailable"),
            ],
            exception_state=True,
            exception_label="Unavailable",
            operator_guidance="Review database access through an approved maintenance process.",
        )
    except Exception:
        return _panel(
            "database_migration_posture",
            "Database and Migration Posture",
            "Database posture is not assessed because safe inspection could not be guaranteed.",
            "not_assessed",
            None,
            None,
            "Read-only status only",
            "System / Database",
            metrics=[_metric("Schema review", "Not assessed")],
            exception_state=True,
            exception_label="Not assessed",
            operator_guidance="Use approved database review procedures if posture evidence is required.",
        )


def _feature_flags_operating_policy_panel():
    if not POLICY_PATH.exists():
        return _panel(
            "feature_flags_operating_policy",
            "Feature Flags and Operating Policy",
            "Ordinary operating policy is not assessed because no read-only policy file is present.",
            "not_assessed",
            None,
            None,
            "Read-only status only",
            "System",
            metrics=[_metric("Policy availability", "Not assessed")],
            exception_state=True,
            exception_label="Not assessed",
            operator_guidance="Review operating policy through the protected Admin policy surface.",
        )

    try:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        read_only = bool(policy.get("read_only_mode"))
        exports = bool(policy.get("allow_exports"))
        user_creation = bool(policy.get("allow_user_creation"))
        restricted = read_only or not exports or not user_creation
        return _panel(
            "feature_flags_operating_policy",
            "Feature Flags and Operating Policy",
            "Ordinary operating policy is summarized without emergency controls or raw policy data.",
            "attention" if restricted else "ready",
            None,
            None,
            "Read-only status only",
            "System",
            metrics=[
                _metric("Read-only mode", "Enabled" if read_only else "Disabled"),
                _metric("Exports", "Enabled" if exports else "Disabled"),
                _metric("User creation", "Enabled" if user_creation else "Disabled"),
                _metric("Policy summary", "Sanitized"),
            ],
            exception_state=restricted,
            exception_label="Review required" if restricted else None,
            operator_guidance="Review operating policy before write or export work." if restricted else "Ordinary operating policy is readable and not restricting standard operations.",
        )
    except Exception:
        return _panel(
            "feature_flags_operating_policy",
            "Feature Flags and Operating Policy",
            "Ordinary operating policy could not be read without exposing raw diagnostics.",
            "unavailable",
            None,
            None,
            "Read-only status only",
            "System",
            metrics=[_metric("Policy availability", "Unavailable")],
            exception_state=True,
            exception_label="Unavailable",
            operator_guidance="Review operating policy through the protected Admin policy surface.",
        )


def _institutional_role_assignments_panel():
    route = "/roles"
    route_exists = _route_available(route)
    has_gate = _endpoint_has(route, ("require_master_admin",))
    try:
        assignment_count = _count_rows("user_roles")
        if not route_exists:
            status = "unavailable"
            guidance = "Review role-assignment route registration."
        elif has_gate:
            status = "ready"
            guidance = "Use Institutional Role Assignments for trust-scoped assignment review."
        else:
            status = "attention"
            guidance = "Review the institutional assignment route boundary."
        return _panel(
            "institutional_role_assignments",
            "Institutional Role Assignments",
            "These are institutional and trust-scoped assignments, not application security roles.",
            status,
            route if route_exists else None,
            "Open Institutional Role Assignments" if route_exists else None,
            "Contextual protected destination",
            "Institutional / Trust",
            metrics=[
                _metric("Route registered", "Yes" if route_exists else "No"),
                _metric("Assignment record count", assignment_count),
                _metric("Ownership classification", "Institutional / Trust"),
                _metric("Master-admin boundary", "Present" if has_gate else "Attention"),
            ],
            exception_state=status != "ready",
            exception_label="Review required" if status == "attention" else ("Unavailable" if status == "unavailable" else None),
            operator_guidance=guidance,
        )
    except Exception:
        return _panel(
            "institutional_role_assignments",
            "Institutional Role Assignments",
            "Institutional assignment registry could not be safely read.",
            "unavailable",
            route if route_exists else None,
            "Open Institutional Role Assignments" if route_exists else None,
            "Contextual protected destination",
            "Institutional / Trust",
            metrics=[_metric("Ownership classification", "Institutional / Trust")],
            exception_state=True,
            exception_label="Unavailable",
            operator_guidance="Review Institutional Role Assignments through the protected route.",
        )


def _recovery_repair_controls_panel():
    return _panel(
        "recovery_repair_controls",
        "Recovery and Repair Controls",
        "Exceptional recovery and repair controls are intentionally excluded from ordinary System navigation.",
        "restricted",
        None,
        None,
        "Exceptional and restricted",
        "System Recovery",
        warning="Exceptional recovery and repair controls are intentionally excluded from ordinary System navigation.",
        metrics=[
            _metric("Ordinary navigation", "Excluded"),
            _metric("Central action link", "None"),
            _metric("Route exposure", "Disabled"),
        ],
        exception_state=True,
        exception_label="Restricted",
        operator_guidance="Recovery controls remain outside ordinary navigation.",
    )


def _source_app_text():
    try:
        view = current_app.view_functions.get("login")
        source_file = inspect.getsourcefile(view)
        return Path(source_file).read_text(encoding="utf-8") if source_file else ""
    except Exception:
        return ""


def _derive_workspace_status(panels):
    critical = [panel for panel in panels if panel.get("key") in CRITICAL_PANEL_KEYS]
    precedence = ("unavailable", "attention", "not_assessed", "protected", "ready")
    for status in precedence:
        if any(panel.get("status") == status for panel in critical):
            return status
    return "not_assessed"


def _workspace_summary(status):
    summaries = {
        "ready": "Ordinary System oversight panels have bounded supporting evidence; restricted recovery remains outside ordinary navigation.",
        "protected": "System oversight primarily confirms protected boundaries; operational completion is not implied.",
        "attention": "One or more System oversight conditions require operator review.",
        "restricted": "Restricted controls remain outside ordinary navigation.",
        "unavailable": "One or more critical System oversight checks are unavailable.",
        "not_assessed": "One or more critical System readiness conditions are not assessed by this workspace.",
    }
    return summaries.get(status, summaries["not_assessed"])


def build_system_workspace_oversight():
    builders = [
        _protected_user_accounts_panel,
        _application_permission_controls_panel,
        _authentication_session_security_panel,
        _audit_security_oversight_panel,
        _backup_data_preservation_panel,
        _deployment_production_health_panel,
        _database_migration_posture_panel,
        _feature_flags_operating_policy_panel,
        _institutional_role_assignments_panel,
        _recovery_repair_controls_panel,
    ]

    panels = []
    for key, builder in zip(PANEL_KEYS, builders):
        try:
            panel = builder()
        except Exception:
            panel = _panel(
                key,
                key.replace("_", " ").title(),
                "This System posture panel could not be safely assessed.",
                "not_assessed",
                None,
                None,
                "Read-only status only",
                "System",
                metrics=[_metric("Status", "Not assessed")],
                exception_state=True,
                exception_label="Not assessed",
                operator_guidance="Review this posture through its protected source surface.",
            )
        panels.append(panel)

    workspace_status = _derive_workspace_status(panels)
    return {
        "workspace_status": workspace_status,
        "workspace_status_label": _label(workspace_status),
        "workspace_summary": _workspace_summary(workspace_status),
        "panels": panels,
    }
