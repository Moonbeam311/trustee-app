from pathlib import Path
import ast
import re
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
SYSTEM_SERVICE = ROOT / "services" / "services_system_workspace.py"
WORKSPACE_DIR = ROOT / "templates" / "ios_workspaces"
WORKSPACE_MAP = ROOT / "templates" / "_institutional_workspace_map.html"
SYSTEM_TEMPLATE = WORKSPACE_DIR / "system.html"

WORKSPACES = [
    ("home", "HOME"),
    ("create", "CREATE"),
    ("administer", "ADMINISTER"),
    ("people", "PEOPLE"),
    ("governance", "GOVERNANCE"),
    ("compliance", "COMPLIANCE"),
    ("legacy", "LEGACY"),
    ("library", "LIBRARY"),
    ("research", "RESEARCH"),
    ("archive", "ARCHIVE"),
    ("reports", "REPORTS"),
    ("system", "SYSTEM"),
    ("developer", "DEVELOPER"),
]

APPROVED_DOMAINS = {
    "authentication",
    "authorization",
    "accounts",
    "institutional_roles",
    "audit",
    "evidence_integrity",
    "backup",
    "archive_preservation",
    "deployment_health",
    "database",
    "operating_policy",
    "exports",
    "uploads",
    "session_continuity",
    "recovery_repair",
}

APPROVED_CLASSIFICATIONS = {
    "direct",
    "indirect",
    "contextual",
    "protected",
    "restricted",
    "degraded",
    "not_assessed",
    "duplicate",
    "misowned",
}

APPROVED_IMPACTS = {
    "critical",
    "high",
    "moderate",
    "low",
    "informational",
}

APPROVED_FAILURE_BEHAVIOR = {
    "fail_closed",
    "degrade_read_only",
    "warn_and_continue",
    "redirect_to_owner",
    "not_assessed",
}

SYSTEM_OWNED_DOMAINS = {
    "authentication",
    "authorization",
    "accounts",
    "audit",
    "deployment_health",
    "database",
    "operating_policy",
    "session_continuity",
    "recovery_repair",
}

FORBIDDEN_EXCEPTIONAL_ROUTES = [
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

SENSITIVE_MARKERS = [
    "password_hash",
    "DB_PATH",
    "UPLOAD_FOLDER",
    "EXPORT_ROOT",
    "RAILWAY_SERVICE_NAME",
    "RAILWAY_PROJECT_NAME",
    "HOSTED_RECOVERY_TOKEN",
    "RESET_ADMIN_PASSWORD",
    "HOSTED_BOOTSTRAP_PASSWORD",
    "connection string",
    "stack trace",
    "exception repr",
]


def read(path):
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


APP_TEXT = read(APP)
SERVICE_TEXT = read(SYSTEM_SERVICE)
MAP_TEXT = read(WORKSPACE_MAP)
WORKSPACE_TEXTS = {
    key: read(WORKSPACE_DIR / f"{key}.html")
    for key, _title in WORKSPACES
}
ORDINARY_WORKSPACE_TEXT = "\n".join(WORKSPACE_TEXTS.values()) + "\n" + MAP_TEXT


def route_for(workspace_key):
    return f"/admin/workspace/{workspace_key}"


DEPENDENCY_MATRIX = [
    # HOME
    ("home", "authentication", "System", "direct", "critical", route_for("home"), "authentication_session_security", "Authenticated access is required for workspace entry.", "Unauthenticated operators are redirected before workspace access.", "fail_closed", "System authentication controls govern HOME access.", True, True),
    ("home", "session_continuity", "System", "direct", "critical", route_for("home"), "authentication_session_security", "Session state preserves identity and firm context across workspace navigation.", "Expired or invalid sessions must return to login.", "fail_closed", "System session controls preserve continuity across IOS navigation.", True, True),
    ("home", "authorization", "System", "protected", "high", route_for("home"), "application_permission_controls", "HOME links remain behind the existing authenticated shell.", "Authorization failure limits workspace entry rather than exposing controls.", "fail_closed", "System authorization controls govern protected workspace use.", True, True),
    ("home", "database", "System", "indirect", "critical", route_for("home"), "database_migration_posture", "HOME displays aggregate counts through existing read paths.", "Unreadable data degrades summaries and should not create records.", "warn_and_continue", "System database posture affects HOME summaries.", True, True),
    # CREATE
    ("create", "authentication", "System", "direct", "critical", route_for("create"), "authentication_session_security", "CREATE is opened through the authenticated workspace shell.", "Unauthenticated operators are redirected before create actions.", "fail_closed", "System authentication controls govern CREATE access.", True, True),
    ("create", "authorization", "System", "direct", "high", route_for("create"), "application_permission_controls", "Create links point to existing controlled workflows.", "Authorization failure should block mutation-capable workflows.", "fail_closed", "System authorization controls govern create workflows.", True, True),
    ("create", "database", "System", "direct", "critical", route_for("create"), "database_migration_posture", "Create workflows need persistent records.", "Database failure must prevent silent partial records.", "fail_closed", "System database posture affects CREATE continuity.", True, True),
    ("create", "uploads", "System", "indirect", "moderate", route_for("create"), None, "Document generation and intake may depend on upload/file policy in downstream routes.", "Upload failure degrades document intake but does not expose repair controls.", "degrade_read_only", "Upload restrictions remain governed by protected System and route policy.", False, True),
    ("create", "operating_policy", "System", "protected", "high", route_for("create"), "feature_flags_operating_policy", "Read-only or export policy may restrict create-side outputs.", "Restricted policy should stop mutation or export behavior where enforced.", "degrade_read_only", "System operating policy controls create and export availability.", True, True),
    ("create", "audit", "System", "indirect", "high", route_for("create"), "audit_security_oversight", "Create actions rely on audit attribution in downstream routes.", "Audit concern should warn operators and preserve governed review.", "warn_and_continue", "System Audit Oversight owns audit infrastructure.", False, True),
    # ADMINISTER
    ("administer", "authentication", "System", "direct", "critical", route_for("administer"), "authentication_session_security", "Administer is entered through authenticated workspace routing.", "Unauthenticated access fails closed.", "fail_closed", "System authentication controls govern ADMINISTER access.", True, True),
    ("administer", "authorization", "System", "direct", "high", route_for("administer"), "application_permission_controls", "Administer links point to controlled trust, matter, asset, and execution routes.", "Authorization failure blocks protected operations.", "fail_closed", "Application authorization remains System-owned.", True, True),
    ("administer", "database", "System", "direct", "critical", route_for("administer"), "database_migration_posture", "Trust, matter, asset, and execution records require database readability.", "Database failure prevents institutionally valid operations.", "fail_closed", "System database posture governs persistence continuity.", True, True),
    ("administer", "audit", "System", "indirect", "high", route_for("administer"), "audit_security_oversight", "Administrative actions depend on audit attribution.", "Audit degradation reduces confidence and requires System review.", "warn_and_continue", "Audit infrastructure remains System-owned.", False, True),
    ("administer", "institutional_roles", "Institutional / Trust", "contextual", "moderate", route_for("administer"), "institutional_role_assignments", "Institutional assignments are separate from application permissions.", "Ambiguous role context can confuse authority review.", "redirect_to_owner", "Institutional role assignments are separate from System authorization.", True, True),
    ("administer", "operating_policy", "System", "protected", "high", route_for("administer"), "feature_flags_operating_policy", "Policy may affect exports or mutation-capable workflows.", "Restricted policy should degrade mutation-capable operations.", "degrade_read_only", "System operating policy controls platform-level restrictions.", True, True),
    # PEOPLE
    ("people", "authentication", "System", "direct", "critical", route_for("people"), "authentication_session_security", "People workspace is protected by workspace authentication.", "Unauthenticated access fails closed.", "fail_closed", "System authentication controls govern PEOPLE access.", True, True),
    ("people", "authorization", "System", "protected", "high", route_for("people"), "application_permission_controls", "People routes remain protected without owning application permissions.", "Authorization failure blocks protected records.", "fail_closed", "System authorization remains separate from people records.", True, True),
    ("people", "database", "System", "direct", "critical", route_for("people"), "database_migration_posture", "People summaries and fiduciary records rely on database reads.", "Unreadable records degrade People summaries.", "warn_and_continue", "System database posture supports People records.", True, True),
    ("people", "institutional_roles", "Institutional / Trust", "contextual", "moderate", route_for("people"), "institutional_role_assignments", "People status references fiduciary and trust-scoped roles as institutional records.", "Ambiguous ownership can conflate people records with login authorization.", "redirect_to_owner", "Institutional role assignments are managed separately from application authorization.", True, True),
    ("people", "audit", "System", "indirect", "high", route_for("people"), "audit_security_oversight", "People record changes depend on audit attribution downstream.", "Audit concerns reduce confidence in chronology.", "warn_and_continue", "Audit integrity requires review in System Audit Oversight.", False, True),
    # GOVERNANCE
    ("governance", "authentication", "System", "direct", "critical", route_for("governance"), "authentication_session_security", "Governance workspace is authenticated.", "Unauthenticated access fails closed.", "fail_closed", "System authentication controls govern GOVERNANCE access.", True, True),
    ("governance", "authorization", "System", "protected", "high", route_for("governance"), "application_permission_controls", "Governance authority does not replace application authorization.", "Authorization failure blocks protected governance actions.", "fail_closed", "System authorization controls platform access.", True, True),
    ("governance", "database", "System", "direct", "critical", route_for("governance"), "database_migration_posture", "Governance records and relationships require database readability.", "Database failure blocks valid governance work.", "fail_closed", "System database posture supports governance continuity.", True, True),
    ("governance", "audit", "System", "direct", "high", route_for("governance"), "audit_security_oversight", "Governance evidence and lifecycle review depend on audit infrastructure.", "Audit degradation should surface as continuity concern.", "warn_and_continue", "System Audit Oversight owns audit infrastructure.", True, True),
    ("governance", "evidence_integrity", "Governance / Archive", "direct", "high", route_for("governance"), "audit_security_oversight", "Governance evidence export links preserve evidence continuity.", "Integrity concerns require governed review without automatic repair.", "warn_and_continue", "Evidence integrity is reviewed through Governance and Archive with System audit support.", True, True),
    ("governance", "institutional_roles", "Institutional / Trust", "contextual", "moderate", route_for("governance"), "institutional_role_assignments", "Governance authority is institutional and contextual.", "Ambiguous authority can impair governance review.", "redirect_to_owner", "Governance authority does not replace System authorization.", True, True),
    # COMPLIANCE
    ("compliance", "authentication", "System", "direct", "critical", route_for("compliance"), "authentication_session_security", "Compliance workspace is entered through authenticated routing.", "Unauthenticated access fails closed.", "fail_closed", "System authentication controls govern COMPLIANCE access.", True, True),
    ("compliance", "authorization", "System", "protected", "high", route_for("compliance"), "application_permission_controls", "Compliance depends on protected records and reports.", "Authorization failure blocks protected review.", "fail_closed", "System authorization controls compliance access.", True, True),
    ("compliance", "audit", "System", "direct", "high", route_for("compliance"), "audit_security_oversight", "Compliance conclusions depend on audit and evidence records.", "Audit degradation should warn, not expose raw diagnostics.", "warn_and_continue", "Audit integrity requires review in System Audit Oversight.", False, True),
    ("compliance", "evidence_integrity", "Governance / Archive", "direct", "high", route_for("compliance"), "audit_security_oversight", "Evidence integrity supports compliance posture.", "Integrity concerns degrade confidence in compliance readiness.", "warn_and_continue", "Evidence integrity is reviewed through governed evidence and Archive surfaces.", False, True),
    ("compliance", "database", "System", "direct", "critical", route_for("compliance"), "database_migration_posture", "Compliance depends on readable institutional records.", "Database failure blocks valid compliance posture.", "fail_closed", "System database posture supports compliance review.", True, True),
    ("compliance", "exports", "System", "indirect", "moderate", route_for("compliance"), "feature_flags_operating_policy", "Compliance reporting may depend on controlled exports.", "Disabled exports should not bypass System policy.", "degrade_read_only", "Export availability is controlled by System operating policy.", False, True),
    # LEGACY
    ("legacy", "database", "System", "direct", "critical", route_for("legacy"), "database_migration_posture", "Legacy records require readable database state.", "Unreadable records degrade institutional history access.", "warn_and_continue", "System database posture supports Legacy continuity.", True, True),
    ("legacy", "archive_preservation", "Archive", "contextual", "high", route_for("legacy"), None, "Long-term legacy continuity depends on archive preservation workflow.", "Preservation gaps warn but do not expose recovery controls.", "warn_and_continue", "Archive governs preservation workflow with System infrastructure support.", False, True),
    ("legacy", "backup", "System / Archive", "protected", "high", route_for("legacy"), "backup_data_preservation", "Legacy continuity may depend on protected backup access.", "Backup access does not prove recoverability.", "not_assessed", "Archive preservation depends on protected System backup access; recoverability is not assessed here.", False, True),
    ("legacy", "audit", "System", "indirect", "high", route_for("legacy"), "audit_security_oversight", "Legacy provenance depends on audit chronology where applicable.", "Audit degradation reduces provenance confidence.", "warn_and_continue", "System Audit Oversight owns audit infrastructure.", False, True),
    ("legacy", "evidence_integrity", "Governance / Archive", "indirect", "high", route_for("legacy"), None, "Legacy evidence relies on governed evidence and archive integrity.", "Integrity issues should be reviewed in Governance or Archive.", "redirect_to_owner", "Evidence integrity remains governed outside Legacy shortcuts.", False, True),
    # LIBRARY
    ("library", "authentication", "System", "direct", "critical", route_for("library"), "authentication_session_security", "Library workspace is authenticated.", "Unauthenticated access fails closed.", "fail_closed", "System authentication controls govern LIBRARY access.", True, True),
    ("library", "authorization", "System", "protected", "high", route_for("library"), "application_permission_controls", "Library content access remains permission-controlled downstream.", "Authorization failure blocks protected content actions.", "fail_closed", "System authorization controls protected content.", True, True),
    ("library", "database", "System", "direct", "critical", route_for("library"), "database_migration_posture", "Guides, forms, and videos depend on database records.", "Database failure degrades Library availability.", "warn_and_continue", "System database posture supports Library records.", True, True),
    ("library", "uploads", "System", "indirect", "moderate", route_for("library"), None, "Video and document upload posture is governed in source routes.", "Upload failure should not expose storage paths.", "degrade_read_only", "Upload and storage restrictions remain System-governed.", False, True),
    ("library", "archive_preservation", "Archive", "contextual", "moderate", route_for("library"), None, "Library preservation is contextual and separate from System recovery.", "Preservation gaps warn without exposing backup routes.", "warn_and_continue", "Archive governs preservation while Library manages content.", False, True),
    # RESEARCH
    ("research", "authentication", "System", "direct", "critical", route_for("research"), "authentication_session_security", "Research workspace is authenticated.", "Unauthenticated access fails closed.", "fail_closed", "System authentication controls govern RESEARCH access.", True, True),
    ("research", "authorization", "System", "protected", "high", route_for("research"), "application_permission_controls", "Research routes remain behind authorization.", "Authorization failure blocks protected research surfaces.", "fail_closed", "System authorization controls protected access.", True, True),
    ("research", "database", "System", "direct", "critical", route_for("research"), "database_migration_posture", "Research concepts and records depend on database reads.", "Database failure degrades research access.", "warn_and_continue", "System database posture supports Research continuity.", True, True),
    ("research", "audit", "System", "indirect", "high", route_for("research"), "audit_security_oversight", "Provenance and changes may depend on audit attribution.", "Audit issues warn without exposing raw records.", "warn_and_continue", "System Audit Oversight owns provenance infrastructure.", False, True),
    ("research", "exports", "System", "protected", "moderate", route_for("research"), "feature_flags_operating_policy", "Research outputs may depend on controlled export policy.", "Export-disabled posture should not be bypassed.", "degrade_read_only", "System operating policy controls exports.", False, True),
    # ARCHIVE
    ("archive", "backup", "System / Archive", "protected", "high", route_for("archive"), "backup_data_preservation", "Archive links to protected backup confirmation rather than raw download bypass.", "Backup availability does not prove restoration.", "not_assessed", "Archive preservation depends on protected System backup access; recoverability is not assessed here.", True, True),
    ("archive", "archive_preservation", "Archive", "direct", "high", route_for("archive"), None, "Archive governs preservation workflow and evidence continuity.", "Preservation gaps require Archive review without repair routes.", "warn_and_continue", "Archive owns preservation workflow; System owns infrastructure controls.", True, True),
    ("archive", "audit", "System", "direct", "high", route_for("archive"), "audit_security_oversight", "Archive integrity and certification depend on audit infrastructure.", "Audit degradation reduces archive confidence.", "warn_and_continue", "System Audit Oversight owns audit infrastructure.", True, True),
    ("archive", "evidence_integrity", "Governance / Archive", "direct", "high", route_for("archive"), None, "Archive evidence manifest and integrity surfaces are centrally linked.", "Integrity exceptions require governed review.", "warn_and_continue", "Evidence integrity remains governed and read-only from Archive.", True, True),
    ("archive", "database", "System", "direct", "critical", route_for("archive"), "database_migration_posture", "Archive status and records depend on database readability.", "Database failure blocks authoritative archive review.", "fail_closed", "System database posture supports Archive continuity.", True, True),
    ("archive", "authorization", "System", "protected", "high", route_for("archive"), "application_permission_controls", "Archive backup and evidence links remain protected downstream.", "Authorization failure blocks protected archive actions.", "fail_closed", "System authorization controls protected Archive actions.", True, True),
    ("archive", "recovery_repair", "System", "restricted", "high", route_for("archive"), "recovery_repair_controls", "Archive states recovery execution is intentionally excluded.", "Restricted recovery requires controlled procedures outside ordinary navigation.", "not_assessed", "Recovery controls remain System-owned and absent from Archive workflow.", True, True),
    # REPORTS
    ("reports", "authorization", "System", "protected", "high", route_for("reports"), "application_permission_controls", "Reports links remain governed by authorization and route controls.", "Authorization failure blocks protected reports.", "fail_closed", "System authorization controls Reports access.", True, True),
    ("reports", "database", "System", "direct", "critical", route_for("reports"), "database_migration_posture", "Reports summaries and registries depend on readable data.", "Database failure degrades report availability.", "warn_and_continue", "System database posture supports Reports continuity.", True, True),
    ("reports", "exports", "System", "protected", "moderate", route_for("reports"), "feature_flags_operating_policy", "Reports depend on controlled export policy without owning it.", "Export-disabled posture should prevent bypass while preserving read-only discovery.", "degrade_read_only", "Export availability is controlled by System operating policy.", True, True),
    ("reports", "audit", "System", "direct", "high", route_for("reports"), "audit_security_oversight", "Audit dashboards and attribution support reports.", "Audit degradation warns and requires System review.", "warn_and_continue", "Audit integrity requires review in System Audit Oversight.", True, True),
    ("reports", "operating_policy", "System", "protected", "high", route_for("reports"), "feature_flags_operating_policy", "Reports do not own System policy or policy mutation.", "Policy restrictions degrade exports without bypass.", "degrade_read_only", "System operating policy controls report export availability.", True, True),
    # SYSTEM
    ("system", "authentication", "System", "direct", "critical", route_for("system"), "authentication_session_security", "System itself is protected by authenticated workspace routing.", "Unauthenticated access fails closed.", "fail_closed", "System is the authoritative infrastructure oversight surface.", True, True),
    ("system", "authorization", "System", "direct", "high", route_for("system"), "application_permission_controls", "System summarizes protected authorization boundaries.", "Authorization failure blocks control surfaces.", "fail_closed", "System owns application authorization oversight.", True, True),
    ("system", "accounts", "System", "direct", "high", route_for("system"), "protected_user_accounts", "System owns protected application account administration.", "Account registry failures require protected System review.", "redirect_to_owner", "Protected account controls remain System-owned.", True, True),
    ("system", "audit", "System", "direct", "high", route_for("system"), "audit_security_oversight", "System owns audit infrastructure posture.", "Audit issues require System Audit Oversight.", "redirect_to_owner", "System is authoritative for audit infrastructure.", True, True),
    ("system", "backup", "System / Archive", "protected", "high", route_for("system"), "backup_data_preservation", "System confirms protected backup access without claiming recoverability.", "Backup recoverability remains not assessed here.", "not_assessed", "Protected backup access does not prove completion or recoverability.", True, True),
    ("system", "deployment_health", "System", "not_assessed", "moderate", route_for("system"), "deployment_production_health", "System distinguishes local structural posture from hosted runtime posture.", "Hosted runtime uncertainty should warn without claiming readiness.", "not_assessed", "Hosted runtime posture must be verified in its protected destination.", True, True),
    ("system", "database", "System", "direct", "critical", route_for("system"), "database_migration_posture", "System performs bounded read-only database posture checks.", "Database read failure affects institution-wide continuity.", "fail_closed", "System database posture is authoritative for infrastructure continuity.", True, True),
    ("system", "operating_policy", "System", "direct", "high", route_for("system"), "feature_flags_operating_policy", "System summarizes ordinary operating policy without emergency flags.", "Restricted policy degrades mutation and exports.", "degrade_read_only", "System operating policy owns platform restrictions.", True, True),
    ("system", "institutional_roles", "Institutional / Trust", "contextual", "moderate", route_for("system"), "institutional_role_assignments", "System distinguishes institutional assignments from application security roles.", "Ambiguous ownership can confuse authority review.", "redirect_to_owner", "Institutional assignments are not application authorization.", True, True),
    ("system", "recovery_repair", "System", "restricted", "high", route_for("system"), "recovery_repair_controls", "Recovery controls are intentionally excluded from ordinary navigation.", "Restricted recovery remains outside ordinary workflow.", "not_assessed", "Recovery controls remain outside ordinary navigation.", True, True),
    # DEVELOPER
    ("developer", "deployment_health", "System", "contextual", "moderate", route_for("developer"), "deployment_production_health", "Developer may inspect implementation posture but is not the production health owner.", "Developer access should not become ordinary repair workflow.", "redirect_to_owner", "Production health remains a protected System concern.", False, True),
    ("developer", "database", "System", "contextual", "critical", route_for("developer"), "database_migration_posture", "Developer diagnostics may depend on database posture but should not run migrations here.", "Database issues require controlled System review.", "redirect_to_owner", "System owns database posture and migration boundaries.", False, True),
    ("developer", "recovery_repair", "System", "restricted", "high", route_for("developer"), "recovery_repair_controls", "Developer must not expose recovery or repair as ordinary tooling.", "Restricted recovery stays outside normal developer navigation.", "not_assessed", "Exceptional recovery controls remain System-owned and excluded.", False, True),
    ("developer", "audit", "System", "contextual", "high", route_for("developer"), "audit_security_oversight", "Developer may inspect implementation posture; audit infrastructure remains System-owned.", "Audit concern requires System review.", "redirect_to_owner", "System Audit Oversight owns audit infrastructure.", False, True),
    ("developer", "authentication", "System", "direct", "critical", route_for("developer"), "authentication_session_security", "Developer workspace is authenticated.", "Unauthenticated access fails closed.", "fail_closed", "System authentication controls govern Developer access.", True, True),
    ("developer", "authorization", "System", "protected", "high", route_for("developer"), "application_permission_controls", "Developer is not the ordinary path for security administration.", "Authorization failure blocks protected diagnostics.", "fail_closed", "System authorization controls protected developer access.", True, True),
]


def matrix_rows():
    rows = []
    workspace_titles = dict(WORKSPACES)
    for entry in DEPENDENCY_MATRIX:
        (
            workspace_key,
            dependency_domain,
            dependency_owner,
            classification,
            continuity_impact,
            source_route,
            system_panel_key,
            evidence,
            failure_effect,
            failure_behavior,
            continuity_guidance,
            exposed_in_workspace,
            ownership_clear,
        ) = entry
        rows.append({
            "workspace_key": workspace_key,
            "workspace_title": workspace_titles[workspace_key],
            "dependency_domain": dependency_domain,
            "dependency_owner": dependency_owner,
            "classification": classification,
            "continuity_impact": continuity_impact,
            "source_route": source_route,
            "system_panel_key": system_panel_key,
            "evidence": evidence,
            "failure_effect": failure_effect,
            "failure_behavior": failure_behavior,
            "continuity_guidance": continuity_guidance,
            "exposed_in_workspace": bool(exposed_in_workspace),
            "ownership_clear": bool(ownership_clear),
        })
    return rows


def app_workspace_meta_keys():
    match = re.search(r"IOS_WORKSPACE_META\s*=\s*\{(?P<body>.*?)\n\}", APP_TEXT, re.S)
    if not match:
        return set()
    return set(re.findall(r'"([a-z_]+)"\s*:', match.group("body")))


def hrefs(text):
    return re.findall(r'href=["\']([^"\']+)["\']', text)


def forms_with_method_post(text):
    return re.findall(r"<form\b[^>]*method=[\"']?post[\"']?", text, flags=re.I)


def contains_any(text, markers):
    lower = text.lower()
    return [marker for marker in markers if marker.lower() in lower]


checks = []


def record(name, passed, detail=""):
    checks.append((name, bool(passed), detail))


rows = matrix_rows()
workspace_keys = {key for key, _title in WORKSPACES}
matrix_workspace_keys = {row["workspace_key"] for row in rows}
meta_keys = app_workspace_meta_keys()
template_keys = {
    path.stem
    for path in WORKSPACE_DIR.glob("*.html")
    if path.stem in workspace_keys
}

record("Workspace inventory", workspace_keys == meta_keys == template_keys, f"expected={sorted(workspace_keys)} meta={sorted(meta_keys)} templates={sorted(template_keys)}")
record("Dependency-domain inventory", {row["dependency_domain"] for row in rows}.issubset(APPROVED_DOMAINS), sorted({row["dependency_domain"] for row in rows} - APPROVED_DOMAINS))
record("Every workspace has dependency classification", matrix_workspace_keys == workspace_keys, f"matrix={sorted(matrix_workspace_keys)}")
record("Dependency matrix required keys", all({
    "workspace_key",
    "workspace_title",
    "dependency_domain",
    "dependency_owner",
    "classification",
    "continuity_impact",
    "source_route",
    "system_panel_key",
    "evidence",
    "failure_effect",
    "failure_behavior",
    "continuity_guidance",
    "exposed_in_workspace",
    "ownership_clear",
}.issubset(row) for row in rows))
record("Dependency classifications approved", all(row["classification"] in APPROVED_CLASSIFICATIONS for row in rows))
record("Continuity impacts approved", all(row["continuity_impact"] in APPROVED_IMPACTS for row in rows))
record("Failure behavior approved", all(row["failure_behavior"] in APPROVED_FAILURE_BEHAVIOR for row in rows))
record("All entries have evidence", all(row["evidence"] and row["failure_effect"] and row["continuity_guidance"] for row in rows))

system_owner_failures = [
    row
    for row in rows
    if row["dependency_domain"] in SYSTEM_OWNED_DOMAINS and "System" not in row["dependency_owner"]
]
record("System ownership preservation", not system_owner_failures, [row["dependency_domain"] for row in system_owner_failures])

roles_language = WORKSPACE_TEXTS["people"] + "\n" + WORKSPACE_TEXTS["system"] + "\n" + SERVICE_TEXT
record("Institutional-role separation", "/permissions" in SERVICE_TEXT and "not application security roles" in roles_language.lower() and "Institutional Role Assignments" in SYSTEM_TEMPLATE.read_text(encoding="utf-8", errors="replace"))

archive_text = WORKSPACE_TEXTS["archive"]
record("Archive/System dependency boundary", "Recovery execution remains protected and unavailable from this workspace" in archive_text and "/admin/backup/database.zip" in archive_text and "confirmation boundary" in archive_text)
record("Archive recoverability not overstated", not contains_any(archive_text, ["verified restoration", "backup verified", "backup complete", "recoverable backup"]))

reports_text = WORKSPACE_TEXTS["reports"]
record("Reports/System dependency boundary", "does not bypass those controls" in reports_text and "Export creation" in reports_text and "/exports" in reports_text)
record("Reports do not own policy", "System policy" not in reports_text and "/admin/export-policy/toggle" not in reports_text)

developer_text = WORKSPACE_TEXTS["developer"]
record("Developer/System dependency boundary", "placeholder" in developer_text.lower() and not contains_any(developer_text, ["repair", "recovery", "bootstrap", "migration", "production health"]))

exceptional_exposures = [
    route
    for route in FORBIDDEN_EXCEPTIONAL_ROUTES
    if route in ORDINARY_WORKSPACE_TEXT
]
record("Exceptional-route exclusion", not exceptional_exposures, exceptional_exposures)

duplicate_control_findings = []
for key, text in WORKSPACE_TEXTS.items():
    post_forms = forms_with_method_post(text)
    if post_forms:
        duplicate_control_findings.append(f"{key}: POST form")
    lowered = text.lower()
    if "permission matrix" in lowered and key != "system":
        duplicate_control_findings.append(f"{key}: permission matrix language")
    if "/users/new" in text or "reset_password" in text or "/permissions" in text:
        duplicate_control_findings.append(f"{key}: user or permission admin link")
    if "/admin/backup/database.zip?confirmed=1" in text:
        duplicate_control_findings.append(f"{key}: backup confirmation bypass")
record("Duplicate-control exclusion", not duplicate_control_findings, duplicate_control_findings)

misownership_findings = []
if "application authorization" in WORKSPACE_TEXTS["people"].lower() and "separate" not in WORKSPACE_TEXTS["people"].lower():
    misownership_findings.append("people: application authorization ambiguity")
if "/roles" in WORKSPACE_TEXTS["system"] and "application security roles" not in WORKSPACE_TEXTS["system"]:
    misownership_findings.append("system: role assignment ambiguity")
record("Misownership findings", not misownership_findings, misownership_findings)

critical_rows = [row for row in rows if row["continuity_impact"] == "critical"]
high_rows = [row for row in rows if row["continuity_impact"] == "high"]
record("Critical continuity dependencies", critical_rows and all(row["failure_behavior"] in {"fail_closed", "warn_and_continue", "redirect_to_owner"} for row in critical_rows))
record("High-impact dependencies", high_rows and all(row["failure_behavior"] in APPROVED_FAILURE_BEHAVIOR for row in high_rows))
record("Failure-state expectations", all(row["failure_behavior"] for row in rows))

unsafe_guidance_markers = [
    "click here to",
    "run the",
    "run recovery",
    "run repair",
    "run migration",
    "use the emergency",
    "automatic fix",
    "automatically repair",
    "reseed permissions",
]
guidance_issues = [
    row
    for row in rows
    if contains_any(row["continuity_guidance"], unsafe_guidance_markers)
]
record("Cross-workspace guidance", not guidance_issues, [row["workspace_key"] for row in guidance_issues])

map_and_shell_ok = all(f"/admin/workspace/{key}" in read(ROOT / "templates" / "_ios_shell.html") for key, _title in WORKSPACES)
record("Navigation continuity", map_and_shell_ok and "/admin/workspace/system" in ORDINARY_WORKSPACE_TEXT)

sensitive_hits = contains_any(ORDINARY_WORKSPACE_TEXT, SENSITIVE_MARKERS)
record("Sensitive-data exclusion", not sensitive_hits, sensitive_hits)

new_script_text = read(Path(__file__))
script_tree = ast.parse(new_script_text)
call_names = []
for node in ast.walk(script_tree):
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name):
            call_names.append(func.id)
        elif isinstance(func, ast.Attribute):
            call_names.append(func.attr)

mutation_call_markers = {
    "write_text",
    "open",
    "remove",
    "unlink",
    "rmdir",
    "mkdir",
    "rename",
    "system",
    "popen",
}
imports_subprocess = any(
    (isinstance(node, ast.Import) and any(alias.name == "subprocess" for alias in node.names))
    or (isinstance(node, ast.ImportFrom) and node.module == "subprocess")
    for node in ast.walk(script_tree)
)
record("Mutation exclusion", not any(name in mutation_call_markers for name in call_names) and not imports_subprocess)

expected_scope = {
    "scripts/audit_system_cross_workspace_continuity_17f.py",
}
record("Repository scope", Path(__file__).name == "audit_system_cross_workspace_continuity_17f.py" and expected_scope)

workspace_summary = {}
for key, title in WORKSPACES:
    key_rows = [row for row in rows if row["workspace_key"] == key]
    impacts = sorted({row["continuity_impact"] for row in key_rows})
    behaviors = sorted({row["failure_behavior"] for row in key_rows})
    exceptional = any(route in WORKSPACE_TEXTS[key] for route in FORBIDDEN_EXCEPTIONAL_ROUTES)
    ownership_clear = all(row["ownership_clear"] for row in key_rows)
    workspace_summary[key] = {
        "title": title,
        "dependencies": sorted({row["dependency_domain"] for row in key_rows}),
        "owner": "System" if any("System" in row["dependency_owner"] for row in key_rows) else key.title(),
        "impact": ",".join(impacts),
        "behavior": ",".join(behaviors),
        "ownership": "clear" if ownership_clear else "review",
        "exceptional": "none" if not exceptional else "exposed",
        "result": "PASS" if ownership_clear and not exceptional else "FAIL",
    }

questions = {
    "cannot_function_without_authentication": sorted({row["workspace_key"] for row in rows if row["dependency_domain"] == "authentication" and row["continuity_impact"] == "critical"}),
    "degrade_when_authorization_unavailable": sorted({row["workspace_key"] for row in rows if row["dependency_domain"] == "authorization"}),
    "depend_on_database_readability": sorted({row["workspace_key"] for row in rows if row["dependency_domain"] == "database"}),
    "depend_on_audit_integrity": sorted({row["workspace_key"] for row in rows if row["dependency_domain"] == "audit"}),
    "depend_on_export_policy": sorted({row["workspace_key"] for row in rows if row["dependency_domain"] in {"exports", "operating_policy"}}),
    "depend_on_backup_or_archive_preservation": sorted({row["workspace_key"] for row in rows if row["dependency_domain"] in {"backup", "archive_preservation"}}),
    "depend_on_institutional_role_assignments": sorted({row["workspace_key"] for row in rows if row["dependency_domain"] == "institutional_roles"}),
    "institution_wide_interruptions": ["authentication", "session_continuity", "database", "authorization"],
    "warning_not_blocking": ["audit", "evidence_integrity", "backup", "deployment_health", "exports", "archive_preservation"],
    "implicit_dependencies": sorted({row["workspace_key"] for row in rows if not row["exposed_in_workspace"]}),
    "duplicated_capabilities": duplicate_control_findings,
    "misowned_capabilities": misownership_findings,
    "owner_identifiable": all(row["ownership_clear"] for row in rows),
    "return_continuity": bool(map_and_shell_ok),
    "exceptional_recovery_absent": not exceptional_exposures,
}

print("POST-V2-17F SYSTEM CROSS-WORKSPACE CONTINUITY AUDIT")
print("-" * 92)
for section in [
    "Workspace inventory",
    "Dependency-domain inventory",
    "System-owned dependencies",
    "Archive/System dependency boundary",
    "Reports/System dependency boundary",
    "Developer/System dependency boundary",
    "Institutional-role separation",
    "Critical continuity dependencies",
    "High-impact dependencies",
    "Failure-state expectations",
    "Cross-workspace guidance",
    "Duplicate-control findings",
    "Misownership findings",
    "Exceptional-route exclusion",
    "Navigation continuity",
    "Sensitive-data exclusion",
    "Mutation exclusion",
    "Repository scope",
]:
    print(f"{section}: tracked")

print()
print("WORKSPACE-BY-WORKSPACE TABLE")
print("-" * 92)
print("Workspace | Dependencies | Primary System owner | Continuity impact | Failure behavior | Ownership clarity | Exceptional exposure | Result")
for key, title in WORKSPACES:
    summary = workspace_summary[key]
    print(
        f"{title} | "
        f"{','.join(summary['dependencies'])} | "
        f"{summary['owner']} | "
        f"{summary['impact']} | "
        f"{summary['behavior']} | "
        f"{summary['ownership']} | "
        f"{summary['exceptional']} | "
        f"{summary['result']}"
    )

print()
print("CONTINUITY QUESTIONS")
print("-" * 92)
for key, value in questions.items():
    if isinstance(value, list):
        printable = ",".join(value) if value else "none"
    else:
        printable = str(value)
    print(f"{key}: {printable}")

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
    print("POST-V2-17F RESULT")
    print("FAIL — One or more cross-workspace dependencies are duplicated, misowned, operationally unclear, continuity-breaking, or improperly exposed.")
    raise SystemExit(1)

print("POST-V2-17F RESULT")
print("PASS — Cross-workspace dependencies preserve System ownership, institutional continuity, bounded failure behavior, and exceptional-route exclusion.")
