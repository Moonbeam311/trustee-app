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

EXPECTED_CORE_TABLES = {
    "trusts",
    "app_users",
    "user_roles",
    "audit_log",
    "documents",
    "media",
}

POLICY_PATH = Path("data") / "export_policy.json"


def _metric(label, value):
    return {"label": label, "value": value}


def _panel(
    key,
    title,
    summary,
    status,
    status_label,
    route,
    action_label,
    exposure,
    owner,
    warning=None,
    metrics=None,
):
    return {
        "key": key,
        "title": title,
        "summary": summary,
        "status": status,
        "status_label": status_label,
        "route": route,
        "action_label": action_label,
        "exposure": exposure,
        "owner": owner,
        "warning": warning,
        "metrics": metrics or [],
    }


def _route_available(route):
    try:
        routes = {rule.rule for rule in current_app.url_map.iter_rules()}
        return route in routes
    except Exception:
        return False


def _count_rows(table_name):
    conn = get_connection()
    try:
        row = conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
        return int(row["count"] if row else 0)
    finally:
        conn.close()


def _protected_user_accounts_panel():
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
        total = 0
        for row in rows:
            count = int(row["count"])
            total += count
            if row["status_value"] == "active":
                active += count
            else:
                inactive += count

        status = "protected" if _route_available("/users") else "not_configured"
        status_label = "Protected" if status == "protected" else "Unavailable"
        return _panel(
            "protected_user_accounts",
            "Protected User Accounts",
            "Application account administration remains behind the protected System boundary.",
            status,
            status_label,
            "/users" if _route_available("/users") else None,
            "Open Protected User Accounts" if _route_available("/users") else None,
            "Protected administrative destination",
            "System",
            metrics=[
                _metric("Total application accounts", total),
                _metric("Active accounts", active),
                _metric("Inactive accounts", inactive),
                _metric("Protected status", status_label),
                _metric("Availability", "Available" if _route_available("/users") else "Unavailable"),
            ],
        )
    except Exception:
        return _panel(
            "protected_user_accounts",
            "Protected User Accounts",
            "Application account posture could not be safely assessed.",
            "not_assessed",
            "Not Assessed",
            "/users" if _route_available("/users") else None,
            "Open Protected User Accounts" if _route_available("/users") else None,
            "Protected administrative destination",
            "System",
            metrics=[_metric("Protected status", "Protected")],
        )


def _application_permission_controls_panel():
    route_available = _route_available("/permissions")
    return _panel(
        "application_permission_controls",
        "Application Permission Controls",
        "Protected authorization controls are available only through the existing permission surface.",
        "protected" if route_available else "not_configured",
        "Protected" if route_available else "Unavailable",
        "/permissions" if route_available else None,
        "Open Permission Controls" if route_available else None,
        "High-risk protected administrative destination",
        "System",
        warning="High-risk protected administration. The permission matrix is not summarized in this workspace.",
        metrics=[
            _metric("Route availability", "Available" if route_available else "Unavailable"),
            _metric("Master-admin requirement", "Required"),
            _metric("Application role count", 3),
            _metric("Matrix exposure", "Excluded"),
        ],
    )


def _authentication_session_security_panel():
    route_available = _route_available("/security")
    csrf_available = "csrf_token" in current_app.jinja_env.globals
    session_timeout = bool(current_app.config.get("PERMANENT_SESSION_LIFETIME"))
    security_headers = bool(current_app.after_request_funcs)
    return _panel(
        "authentication_session_security",
        "Authentication and Session Security",
        "Authentication and session posture is summarized without exposing session values or credentials.",
        "available" if route_available else "not_configured",
        "Available" if route_available else "Unavailable",
        "/security" if route_available else None,
        "Open Security Oversight" if route_available else None,
        "Read-only oversight",
        "System",
        metrics=[
            _metric("Authentication required", "Yes"),
            _metric("Session timeout", "Configured" if session_timeout else "Not assessed"),
            _metric("Security headers", "Configured" if security_headers else "Not assessed"),
            _metric("CSRF protection", "Available" if csrf_available else "Not assessed"),
            _metric("Master-admin gate", "Available"),
        ],
    )


def _audit_security_oversight_panel():
    route_available = _route_available("/audit")
    try:
        result = verify_audit_log_chain()
        broken = int(result.get("broken") or 0)
        status = "available" if broken == 0 else "attention"
        return _panel(
            "audit_security_oversight",
            "Audit and Security Oversight",
            "Audit integrity posture is summarized using aggregate counts only.",
            status,
            "Available" if status == "available" else "Attention",
            "/audit" if route_available else None,
            "Open Audit Oversight" if route_available else None,
            "Read-only oversight",
            "System / Evidence",
            metrics=[
                _metric("Audit route", "Available" if route_available else "Unavailable"),
                _metric("Audit chain", "Verified" if broken == 0 else "Attention"),
                _metric("Checked count", int(result.get("checked") or 0)),
                _metric("Broken count", broken),
                _metric("Legacy count", int(result.get("legacy") or 0)),
                _metric("Protected status", "Protected"),
            ],
        )
    except Exception:
        return _panel(
            "audit_security_oversight",
            "Audit and Security Oversight",
            "Audit posture requires attention. Raw diagnostics are withheld from this workspace.",
            "attention",
            "Attention",
            "/audit" if route_available else None,
            "Open Audit Oversight" if route_available else None,
            "Read-only oversight",
            "System / Evidence",
            metrics=[
                _metric("Audit route", "Available" if route_available else "Unavailable"),
                _metric("Audit chain", "Attention"),
            ],
        )


def _backup_data_preservation_panel():
    route_available = _route_available("/admin/backup/database.zip")
    return _panel(
        "backup_data_preservation",
        "Backup and Data Preservation",
        "Controlled backup access remains behind the existing confirmation boundary.",
        "protected" if route_available else "not_configured",
        "Protected" if route_available else "Unavailable",
        "/admin/backup/database.zip" if route_available else None,
        "Open Backup Confirmation" if route_available else None,
        "Protected download with existing confirmation boundary",
        "System / Archive",
        warning="Protected database-copy download. Existing master-admin and confirmation boundaries remain required.",
        metrics=[
            _metric("Protected download", "Available" if route_available else "Unavailable"),
            _metric("Confirmation required", "Yes"),
            _metric("Master-admin required", "Yes"),
            _metric("Preservation posture", "Controlled"),
            _metric("Risk level", "Medium"),
        ],
    )


def _deployment_production_health_panel():
    route_available = _route_available("/hosted-production-health")
    return _panel(
        "deployment_production_health",
        "Deployment and Production Health",
        "Hosted production posture is summarized without exposing environment details.",
        "available" if route_available else "not_configured",
        "Available" if route_available else "Unavailable",
        "/hosted-production-health" if route_available else None,
        "Open Production Health" if route_available else None,
        "Sanitized oversight",
        "System / Deployment",
        metrics=[
            _metric("Route availability", "Available" if route_available else "Unavailable"),
            _metric("Deployment review", "Available" if route_available else "Not configured"),
            _metric("Hosted review", "Sanitized"),
            _metric("Production posture", "Reviewable" if route_available else "Not assessed"),
        ],
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
        present = len(EXPECTED_CORE_TABLES.intersection(table_names))
        missing = len(EXPECTED_CORE_TABLES) - present
        status = "available" if missing == 0 else "attention"
        return _panel(
            "database_migration_posture",
            "Database and Migration Posture",
            "Database posture is inspected read-only without invoking repair or migration helpers.",
            status,
            "Available" if status == "available" else "Attention",
            None,
            None,
            "Read-only status only",
            "System / Database",
            metrics=[
                _metric("Database reachable", "Yes"),
                _metric("Expected core tables", "Present" if missing == 0 else "Attention required"),
                _metric("Schema review", "Read-only"),
                _metric("Migration posture", "Available" if missing == 0 else "Attention"),
            ],
        )
    except sqlite3.Error:
        return _panel(
            "database_migration_posture",
            "Database and Migration Posture",
            "Database posture is restricted because safe inspection could not be completed.",
            "restricted",
            "Restricted",
            None,
            None,
            "Read-only status only",
            "System / Database",
            metrics=[
                _metric("Database reachable", "Not assessed"),
                _metric("Schema review", "Restricted"),
            ],
        )
    except Exception:
        return _panel(
            "database_migration_posture",
            "Database and Migration Posture",
            "Database posture is not assessed in this workspace.",
            "not_assessed",
            "Not Assessed",
            None,
            None,
            "Read-only status only",
            "System / Database",
            metrics=[_metric("Schema review", "Not assessed")],
        )


def _feature_flags_operating_policy_panel():
    allowed_policy = {
        "read_only_mode": "Read-only mode",
        "allow_exports": "Exports",
        "allow_user_creation": "User creation",
    }
    metrics = [_metric("Policy availability", "Unavailable")]
    status = "not_assessed"
    status_label = "Not Assessed"
    try:
        if POLICY_PATH.exists():
            policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
            metrics = [
                _metric(label, "Enabled" if bool(policy.get(key)) else "Disabled")
                for key, label in allowed_policy.items()
            ]
            metrics.append(_metric("Policy summary", "Sanitized"))
            status = "available"
            status_label = "Available"
    except Exception:
        metrics = [_metric("Policy availability", "Attention")]
        status = "attention"
        status_label = "Attention"

    return _panel(
        "feature_flags_operating_policy",
        "Feature Flags and Operating Policy",
        "Ordinary operating policy is summarized without emergency controls or raw policy data.",
        status,
        status_label,
        None,
        None,
        "Read-only status only",
        "System",
        metrics=metrics,
    )


def _institutional_role_assignments_panel():
    route_available = _route_available("/roles")
    try:
        assignment_count = _count_rows("user_roles")
        status = "protected" if route_available else "not_configured"
        return _panel(
            "institutional_role_assignments",
            "Institutional Role Assignments",
            "These are institutional and trust-scoped assignments, not application security roles.",
            status,
            "Protected" if status == "protected" else "Unavailable",
            "/roles" if route_available else None,
            "Open Institutional Role Assignments" if route_available else None,
            "Contextual protected destination",
            "Institutional / Trust",
            metrics=[
                _metric("Route availability", "Available" if route_available else "Unavailable"),
                _metric("Assignment record count", assignment_count),
                _metric("Trust-scoped status", "Contextual"),
                _metric("Protected status", "Protected"),
            ],
        )
    except Exception:
        return _panel(
            "institutional_role_assignments",
            "Institutional Role Assignments",
            "These are institutional and trust-scoped assignments, not application security roles.",
            "not_assessed",
            "Not Assessed",
            "/roles" if route_available else None,
            "Open Institutional Role Assignments" if route_available else None,
            "Contextual protected destination",
            "Institutional / Trust",
            metrics=[_metric("Trust-scoped status", "Contextual")],
        )


def _recovery_repair_controls_panel():
    return _panel(
        "recovery_repair_controls",
        "Recovery and Repair Controls",
        "Exceptional recovery and repair controls are intentionally excluded from ordinary System navigation.",
        "restricted",
        "Restricted",
        None,
        None,
        "Exceptional and restricted",
        "System Recovery",
        warning="Exceptional recovery and repair controls are intentionally excluded from ordinary System navigation.",
        metrics=[
            _metric("Exceptional controls", "Exist"),
            _metric("Controlled procedures", "Required"),
            _metric("Ordinary navigation", "Excluded"),
            _metric("Protected status", "Protected"),
            _metric("Route exposure", "Disabled"),
        ],
    )


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
                "Not Assessed",
                None,
                None,
                "Read-only status only",
                "System",
                metrics=[_metric("Status", "Not assessed")],
            )
        panels.append(panel)

    return {
        "workspace_status": "read_only_oversight",
        "panels": panels,
    }
