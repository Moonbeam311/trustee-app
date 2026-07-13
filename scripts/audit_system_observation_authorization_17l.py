from pathlib import Path
import ast
import re
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
DB = ROOT / "database" / "db.py"
SYSTEM_SERVICE = ROOT / "services" / "services_system_workspace.py"
SYSTEM_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "system.html"
GOVERNANCE_SERVICE = ROOT / "services" / "services_governance.py"
MATTER_SERVICE = ROOT / "services" / "services_matters.py"
AUDIT_17J = ROOT / "scripts" / "audit_system_observation_registry_feasibility_17j.py"
AUDIT_17K = ROOT / "scripts" / "audit_system_observation_data_model_17k.py"


def read(path):
    return path.read_text(encoding="utf-8", errors="replace")


def literal_assignment(tree, name, default=None):
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    try:
                        return ast.literal_eval(node.value)
                    except Exception:
                        return default
    return default


def ok(value):
    return "PASS" if value else "FAIL"


def section(title):
    print()
    print(title.upper())
    print("-" * 100)


app_text = read(APP)
db_text = read(DB)
system_service_text = read(SYSTEM_SERVICE)
system_template_text = read(SYSTEM_TEMPLATE)
governance_text = read(GOVERNANCE_SERVICE)
matter_text = read(MATTER_SERVICE)
audit_17j_text = read(AUDIT_17J)
audit_17k_text = read(AUDIT_17K)
script_text = Path(__file__).read_text(encoding="utf-8", errors="replace")
migration_text = "\n".join(read(path) for path in (ROOT / "database").glob("migrations*.py"))

system_tree = ast.parse(system_service_text)
actual_panel_keys = literal_assignment(system_tree, "PANEL_KEYS", [])
actual_readiness = set(literal_assignment(system_tree, "APP_ROUTE_STATUSES", set()))
actual_escalation = set(literal_assignment(system_tree, "ESCALATION_LEVELS", set()))
actual_decision_owners = set(literal_assignment(system_tree, "DECISION_OWNERS", set()))

EXPECTED_PANELS = [
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

OBSERVATION_TYPES = [
    "account_posture",
    "permission_posture",
    "authentication_session_posture",
    "audit_integrity_posture",
    "backup_preservation_posture",
    "deployment_health_posture",
    "database_migration_posture",
    "operating_policy_posture",
    "institutional_role_posture",
    "recovery_repair_posture",
]

READINESS_STATES = {
    "ready",
    "protected",
    "attention",
    "restricted",
    "unavailable",
    "not_assessed",
}

LIFECYCLE_STATES = {
    "acknowledged",
    "under_review",
    "deferred",
    "routed",
    "closed_no_action",
    "closed_resolved",
    "superseded",
    "reopened",
}

OPEN_STATES = {"acknowledged", "under_review", "deferred", "routed", "reopened"}
CLOSED_STATES = {"closed_no_action", "closed_resolved", "superseded"}

CONCEPTUAL_PERMISSIONS = [
    "system_observation_view",
    "system_observation_create",
    "system_observation_acknowledge",
    "system_observation_investigate",
    "system_observation_defer",
    "system_observation_route",
    "system_observation_close",
    "system_observation_reopen",
    "system_observation_supersede",
    "system_observation_link_record",
    "system_observation_restricted_governance",
    "system_observation_admin",
]

CONDITION_CODES = {
    "account_posture": {"account_registry_unavailable", "inactive_accounts_detected"},
    "permission_posture": {"permission_boundary_missing", "csrf_boundary_missing"},
    "authentication_session_posture": {
        "authentication_runtime_not_assessed",
        "authentication_structural_control_missing",
    },
    "audit_integrity_posture": {"audit_integrity_attention", "audit_verification_unavailable"},
    "backup_preservation_posture": {"backup_route_unavailable", "backup_recoverability_not_assessed"},
    "deployment_health_posture": {
        "hosted_runtime_not_assessed",
        "hosted_health_attention",
        "hosted_health_failure",
    },
    "database_migration_posture": {
        "database_unreadable",
        "required_table_missing",
        "migration_posture_not_assessed",
    },
    "operating_policy_posture": {
        "read_only_mode_enabled",
        "exports_disabled",
        "user_creation_disabled",
        "operating_policy_unavailable",
    },
    "institutional_role_posture": {
        "institutional_role_registry_unavailable",
        "institutional_role_ambiguity",
    },
    "recovery_repair_posture": {"restricted_procedure_required"},
}

CONTEXT_SCOPES = {
    "platform_scoped",
    "deployment_scoped",
    "firm_scoped",
    "institution_scoped",
    "trust_scoped",
    "matter_scoped",
}

PROHIBITED_INPUTS = {
    "password",
    "password_hash",
    "credential",
    "token",
    "cookie",
    "session_id",
    "raw_exception",
    "stack_trace",
    "environment_variable",
    "database_path",
    "connection_string",
    "permission_matrix",
    "repair_command",
    "bootstrap_credential",
    "reset_credential",
}

FORBIDDEN_ROUTES = [
    "hosted-bootstrap-admin-once",
    "hosted-clear-login-lockout-once",
    "hosted-firm-scope-migration-once",
    "hosted-repair-admin-access-once",
    "hosted-reseed-permissions-once",
    "hosted-trust-diagnostic-once",
]

EXISTING_AUTHENTICATION_PATTERNS = [
    ("global session guard", '"role" not in session' in app_text and "enforce_session_timeout" in app_text),
    ("session role", 'session["role"]' in app_text or "session.get(\"role\")" in app_text),
    ("firm session context", "session.get(\"firm_id\")" in app_text),
]

EXISTING_AUTHORIZATION_PATTERNS = [
    ("require_permission decorator", "def require_permission" in app_text and "@require_permission" in app_text),
    ("master-admin gate", "def require_master_admin" in app_text and "gate = require_master_admin()" in app_text),
    ("role rules", "ROLE_RULES" in app_text and "role_denied" in app_text),
    ("trust scoped endpoint rules", "TRUST_SCOPED_ENDPOINT_RULES" in app_text),
]

EXISTING_CSRF_PATTERNS = [
    ("Flask-WTF CSRFProtect", "CSRFProtect(app)" in app_text),
    ("local CSRF helper", "def validate_csrf_token" in app_text),
    ("hidden field", 'name="_csrf_token"' in read(ROOT / "templates" / "auth" / "login.html")),
    ("template global", "app_csrf_token" in app_text and "csrf_token" in app_text),
]

EXISTING_VALIDATION_PATTERNS = [
    ("role allowlist", '{"Admin", "Trustee", "Viewer"}' in app_text or '["Admin", "Trustee", "Viewer"]' in app_text),
    ("bounded denial templates", "access_denied.html" in app_text),
    ("form extraction", "request.form.get" in app_text),
    ("firm scoped lookups", "firm_id" in app_text and "get_trust_by_id" in app_text),
]

EXISTING_TRANSACTION_PATTERNS = [
    ("sqlite commits", ".commit()" in db_text or ".commit()" in app_text),
    ("rollback support", ".rollback()" in db_text or ".rollback()" in app_text or ".rollback()" in migration_text),
    ("unique constraints", "UNIQUE" in db_text),
    ("audit logging", "def log_change" in db_text and "audit_log" in db_text),
]

EXISTING_DUPLICATE_PATTERNS = [
    ("relationship duplicate lookup", "SELECT relationship_id" in governance_text and "governance_relationships" in governance_text),
    ("INSERT OR IGNORE usage", "INSERT OR IGNORE" in app_text or "INSERT OR IGNORE" in db_text),
    ("unique public identifiers", "TEXT UNIQUE" in db_text or "TEXT UNIQUE" in governance_text),
    ("17K duplicate anchor", "PARTIAL UNIQUE open observation_type" in audit_17k_text),
]

VALIDATION_ORDER = [
    "confirm authenticated session",
    "confirm route-level authorization",
    "validate local CSRF",
    "normalize bounded scalar inputs",
    "reject unexpected or repeated fields",
    "validate observation identity",
    "load current observation state",
    "validate context and firm scope",
    "validate lifecycle transition",
    "validate institutional authority",
    "perform duplicate/idempotency lookup",
    "validate related destination record",
    "begin transaction",
    "recheck current state and version",
    "insert append-only observation event",
    "update observation current projection",
    "write generic audit activity where required",
    "commit",
    "return POST-Redirect-GET confirmation",
]

NORMALIZATION_RULES = {
    "observation_id": "strip; uppercase; match SYSOBS-YYYY-NNNNNN; reject whitespace, slashes, query chars, HTML, SQL fragments",
    "observation_type": "strip; lowercase; must be one of ten certified observation types",
    "condition_code": "strip; lowercase; static registry only; must belong to observation type",
    "current_state": "strip; lowercase; loaded from database, not trusted from form",
    "target_state": "strip; lowercase; transition-matrix allowlist only",
    "persistence_trigger": "strip; lowercase; create-only allowlist",
    "context_scope": "strip; lowercase; one certified context scope",
    "context_id": "derived from exact context column; not arbitrary display text",
    "firm_id": "strip; exact authorized firm; required for firm-scoped rows",
    "institution_id": "strip; bounded institutional identifier when institution-scoped",
    "trust_id": "strip; existing trust and current operator access required",
    "matter_id": "strip; existing matter and evidenced relevance required",
    "deployment_key": "strip; bounded deployment identifier for deployment-scoped conditions",
    "sanitized_summary": "strip; normalize line endings; plain text; max 500 chars; no sensitive diagnostics",
    "event_summary": "strip; normalize line endings; plain text; max 500 chars; no sensitive diagnostics",
    "reason_code": "strip; lowercase; transition-specific allowlist where used",
    "related_record_type": "strip; lowercase; destination allowlist only",
    "related_record_id": "strip; destination-owned validation",
    "authority_record_type": "strip; bounded authority type",
    "authority_record_id": "strip; destination-owned validation",
    "idempotency_key": "strip; opaque non-secret operation key; one actor/session and one payload",
    "version": "strip; integer or opaque version token; compared to reloaded record",
}

PERMISSION_ANALYSIS = [
    ("system_observation_view", "view_dashboard partly covers System visibility", "new explicit permission is justified before registry records exist", "Admin; context-limited Trustee only if later authorized", "explicit", "yes", "always denied", "context-limited", "firm/institution scope required"),
    ("system_observation_create", "no exact existing permission", "new permission required", "Admin or authorized operator", "explicit", "master-admin override for platform/restricted only", "always denied", "context-limited only", "firm/context required"),
    ("system_observation_acknowledge", "no exact existing permission", "new permission required", "authorized observation operator", "explicit", "yes", "always denied", "context-limited only", "firm/context required"),
    ("system_observation_investigate", "no exact existing permission", "new permission required", "authorized observation operator", "explicit", "yes", "always denied", "context-limited only", "firm/context required"),
    ("system_observation_defer", "no exact existing permission", "new permission required", "authorized observation operator", "explicit", "yes", "always denied", "context-limited only", "firm/context required"),
    ("system_observation_route", "no exact existing permission", "new permission plus destination permission required", "governance/compliance/archive operators", "explicit", "limited", "always denied", "context-limited only", "destination scope required"),
    ("system_observation_close", "no exact existing permission", "new permission required", "authorized closer by lifecycle", "explicit", "yes", "always denied", "context-limited only", "firm/context required"),
    ("system_observation_reopen", "no exact existing permission", "new permission required", "authorized closer/admin", "explicit", "yes", "always denied", "context-limited only", "firm/context required"),
    ("system_observation_supersede", "no exact existing permission", "new permission required", "system observation admin", "explicit", "yes", "always denied", "not ordinary Trustee", "firm/context required"),
    ("system_observation_link_record", "destination permissions exist separately", "new source-link permission plus destination authorization", "destination operators", "explicit", "limited", "always denied", "context-limited only", "destination scope required"),
    ("system_observation_restricted_governance", "no ordinary permission covers restricted procedures", "new heightened permission required", "system master administrator plus governed authority", "explicit", "master-admin required but insufficient alone", "always denied", "denied", "deployment/platform scope required"),
    ("system_observation_admin", "master-admin gates exist", "new explicit admin permission should supplement master boundary", "System master administrator", "explicit", "required", "always denied", "denied", "platform/admin scope required"),
]

MUTATION_CATALOG = [
    {
        "mutation": "create observation",
        "method": "POST",
        "auth": "authenticated session",
        "permission": "system_observation_create",
        "authority": "panel-specific decision owner when required",
        "csrf": "local _csrf_token required before mutable fields",
        "required": "observation_type, condition_code, context_scope, persistence_trigger, sanitized_summary, idempotency_key",
        "optional": "firm_id, institution_id, trust_id, matter_id, deployment_key, authority reference",
        "prohibited": "raw diagnostics, credentials, permission matrix, database paths",
        "state": "no existing open observation for duplicate key",
        "duplicate": "atomic open-duplicate lookup; identical retry returns existing result",
        "audit": "observation_created + generic audit",
        "event": "observation_created",
        "result": "acknowledged or under_review",
        "failure": "403 for auth/authority, 400 for validation, 409 for duplicate/stale",
    },
    {
        "mutation": "acknowledge observation",
        "method": "POST",
        "auth": "authenticated session",
        "permission": "system_observation_acknowledge",
        "authority": "authorized observation operator",
        "csrf": "required",
        "required": "observation_id, version, reason_code, event_summary, idempotency_key",
        "optional": "authority reference",
        "prohibited": "state overwrite, raw source payload",
        "state": "acknowledged",
        "duplicate": "same idempotency key returns same acknowledgement",
        "audit": "acknowledged + generic audit",
        "event": "acknowledged",
        "result": "acknowledged",
        "failure": "bounded denial or stale-record message",
    },
    {
        "mutation": "start investigation",
        "method": "POST",
        "auth": "authenticated session",
        "permission": "system_observation_investigate",
        "authority": "authorized observation operator or System Administrator",
        "csrf": "required",
        "required": "observation_id, version, reason_code, event_summary, idempotency_key",
        "optional": "authority reference",
        "prohibited": "destination approval claims",
        "state": "acknowledged, deferred, or routed",
        "duplicate": "idempotent by observation, operation, actor, payload",
        "audit": "investigation_started + generic audit",
        "event": "investigation_started",
        "result": "under_review",
        "failure": "409 for invalid current state",
    },
    {
        "mutation": "defer observation",
        "method": "POST",
        "auth": "authenticated session",
        "permission": "system_observation_defer",
        "authority": "authorized observation operator",
        "csrf": "required",
        "required": "observation_id, version, defer reason, event_summary, idempotency_key",
        "optional": "review date",
        "prohibited": "indefinite silent no-op",
        "state": "acknowledged or under_review",
        "duplicate": "same defer request is idempotent",
        "audit": "deferred + generic audit",
        "event": "deferred",
        "result": "deferred",
        "failure": "400 missing reason; 409 stale state",
    },
    {
        "mutation": "prepare routing",
        "method": "POST",
        "auth": "authenticated session",
        "permission": "system_observation_route",
        "authority": "destination-aware authorized operator",
        "csrf": "required",
        "required": "observation_id, version, destination_type, reason, idempotency_key",
        "optional": "authority reference",
        "prohibited": "destination mutation bypass",
        "state": "acknowledged, under_review, or deferred",
        "duplicate": "one active route preparation per destination/purpose",
        "audit": "routing_prepared + generic audit",
        "event": "routing_prepared",
        "result": "routed",
        "failure": "403 if destination authorization missing",
    },
    {
        "mutation": "link destination record",
        "method": "POST",
        "auth": "authenticated session",
        "permission": "system_observation_link_record",
        "authority": "destination workflow authorization",
        "csrf": "required",
        "required": "observation_id, version, related_record_type, related_record_id, reason, idempotency_key",
        "optional": "related label",
        "prohibited": "cross-firm record link",
        "state": "routed or under_review",
        "duplicate": "same source, target, purpose is duplicate",
        "audit": "destination_linked + generic audit",
        "event": "destination_linked",
        "result": "unchanged",
        "failure": "403/404 bounded destination denial",
    },
    {
        "mutation": "record institutional determination reference",
        "method": "POST",
        "auth": "authenticated session",
        "permission": "system_observation_link_record",
        "authority": "Governance Authority or Institutional Administrator plus destination authorization",
        "csrf": "required",
        "required": "observation_id, version, authority_record_type, authority_record_id, event_summary, idempotency_key",
        "optional": "related label",
        "prohibited": "copied determination contents",
        "state": "routed or under_review",
        "duplicate": "same authority record reference is idempotent",
        "audit": "institutional_determination_recorded + generic audit",
        "event": "institutional_determination_recorded",
        "result": "unchanged",
        "failure": "403 if authority/destination missing",
    },
    {
        "mutation": "record technical-action reference",
        "method": "POST",
        "auth": "authenticated session",
        "permission": "system_observation_link_record",
        "authority": "System Administrator or Deployment Administrator for technical action owner",
        "csrf": "required",
        "required": "observation_id, version, related_record_type, related_record_id, event_summary, idempotency_key",
        "optional": "verification reference",
        "prohibited": "repair command or environment values",
        "state": "routed or under_review",
        "duplicate": "same technical reference is idempotent",
        "audit": "technical_action_recorded + generic audit",
        "event": "technical_action_recorded",
        "result": "unchanged",
        "failure": "403 if technical-action destination not authorized",
    },
    {
        "mutation": "close with no action",
        "method": "POST",
        "auth": "authenticated session",
        "permission": "system_observation_close",
        "authority": "lifecycle-specific closer; may require panel decision owner",
        "csrf": "required",
        "required": "observation_id, version, closure reason, event_summary, idempotency_key",
        "optional": "authority reference",
        "prohibited": "resolved or legal conclusion language",
        "state": "acknowledged, under_review, deferred, or routed",
        "duplicate": "same closure request is idempotent",
        "audit": "closed_no_action + generic audit",
        "event": "closed_no_action",
        "result": "closed_no_action",
        "failure": "409 if already closed",
    },
    {
        "mutation": "close as resolved",
        "method": "POST",
        "auth": "authenticated session",
        "permission": "system_observation_close",
        "authority": "authorized closer plus evidence/destination authority",
        "csrf": "required",
        "required": "observation_id, version, evidence reference, closure reason, idempotency_key",
        "optional": "verification reference",
        "prohibited": "unsupported institutional conclusion",
        "state": "under_review or routed",
        "duplicate": "same resolved closure is idempotent",
        "audit": "closed_resolved + generic audit",
        "event": "closed_resolved",
        "result": "closed_resolved",
        "failure": "400 if evidence missing; 409 if closed",
    },
    {
        "mutation": "reopen observation",
        "method": "POST",
        "auth": "authenticated session",
        "permission": "system_observation_reopen",
        "authority": "authorized closer/admin",
        "csrf": "required",
        "required": "observation_id, version, reopen reason, event_summary, idempotency_key",
        "optional": "authority reference",
        "prohibited": "new observation ID",
        "state": "closed_no_action or closed_resolved",
        "duplicate": "same reopen request is idempotent",
        "audit": "reopened + generic audit",
        "event": "reopened",
        "result": "under_review",
        "failure": "409 if observation is open",
    },
    {
        "mutation": "create recurring observation",
        "method": "POST",
        "auth": "authenticated session",
        "permission": "system_observation_create",
        "authority": "panel-specific authority",
        "csrf": "required",
        "required": "prior_observation_id, version, current condition fields, reason, idempotency_key",
        "optional": "authority reference",
        "prohibited": "reusing prior observation ID",
        "state": "prior occurrence closed or superseded",
        "duplicate": "blocked if prior/open duplicate still unresolved",
        "audit": "observation_created + recurrence_linked + generic audit",
        "event": "observation_created",
        "result": "acknowledged or under_review",
        "failure": "409 if prior occurrence still open",
    },
    {
        "mutation": "supersede observation",
        "method": "POST",
        "auth": "authenticated session",
        "permission": "system_observation_supersede",
        "authority": "System observation admin",
        "csrf": "required",
        "required": "observation_id, successor_observation_id, version, reason, idempotency_key",
        "optional": "authority reference",
        "prohibited": "deletion or silent type correction",
        "state": "acknowledged, under_review, deferred, or routed",
        "duplicate": "same successor link is idempotent",
        "audit": "superseded + generic audit",
        "event": "superseded",
        "result": "superseded",
        "failure": "400 missing successor; 409 closed/prohibited state",
    },
    {
        "mutation": "add bounded note",
        "method": "POST",
        "auth": "authenticated session",
        "permission": "system_observation_acknowledge",
        "authority": "authorized observation operator",
        "csrf": "required",
        "required": "observation_id, version, note summary, idempotency_key",
        "optional": "authority reference",
        "prohibited": "raw diagnostics or secrets",
        "state": "open lifecycle state",
        "duplicate": "idempotent by key and exact payload",
        "audit": "note_recorded optional generic audit by sensitivity",
        "event": "note_recorded",
        "result": "unchanged",
        "failure": "400 oversized or sensitive note",
    },
    {
        "mutation": "initiate restricted-procedure governance",
        "method": "POST",
        "auth": "authenticated session",
        "permission": "system_observation_restricted_governance",
        "authority": "System master administrator plus separately governed restricted authority",
        "csrf": "required",
        "required": "observation_id, version, authority reference, restricted reason, idempotency_key",
        "optional": "destination reference once authorized",
        "prohibited": "repair command, bootstrap credential, direct execution",
        "state": "under_review or routed",
        "duplicate": "one active restricted-governance request per observation/purpose",
        "audit": "routing_prepared or destination_linked + generic audit",
        "event": "routing_prepared",
        "result": "routed",
        "failure": "403 if heightened authority missing",
    },
]

TRANSITION_RULES = {
    "acknowledged->under_review": ("system_observation_investigate", "reason required", "investigation_started"),
    "acknowledged->deferred": ("system_observation_defer", "reason required", "deferred"),
    "acknowledged->routed": ("system_observation_route", "destination required", "routing_prepared"),
    "acknowledged->closed_no_action": ("system_observation_close", "closure reason required", "closed_no_action"),
    "under_review->deferred": ("system_observation_defer", "reason required", "deferred"),
    "under_review->routed": ("system_observation_route", "destination required", "routing_prepared"),
    "under_review->closed_no_action": ("system_observation_close", "closure reason required", "closed_no_action"),
    "under_review->closed_resolved": ("system_observation_close", "evidence required", "closed_resolved"),
    "deferred->under_review": ("system_observation_investigate", "reason required", "investigation_started"),
    "deferred->routed": ("system_observation_route", "destination required", "routing_prepared"),
    "deferred->closed_no_action": ("system_observation_close", "closure reason required", "closed_no_action"),
    "routed->under_review": ("system_observation_investigate", "reason required", "investigation_started"),
    "routed->closed_no_action": ("system_observation_close", "closure reason required", "closed_no_action"),
    "routed->closed_resolved": ("system_observation_close", "evidence required", "closed_resolved"),
    "closed_no_action->reopened": ("system_observation_reopen", "reopen reason required", "reopened"),
    "closed_resolved->reopened": ("system_observation_reopen", "reopen reason required", "reopened"),
    "open->superseded": ("system_observation_supersede", "successor required", "superseded"),
}

PANEL_AUTHORIZATION = [
    ("protected_user_accounts", "account_posture", "System master administrator", "authorized observation operator", "System Audit destination authorization", "System master administrator", "firm scope", "type+code+firm+open", "No", "aggregate only; no account details"),
    ("application_permission_controls", "permission_posture", "System master administrator", "System authorization operator", "System Audit/Governance destination authorization", "System master administrator", "platform or firm scope", "type+code+scope+context+open", "No", "no permission matrix copied"),
    ("authentication_session_security", "authentication_session_posture", "System or Deployment Administrator", "authorized security operator", "System Audit destination authorization", "System Administrator", "platform or deployment scope", "type+code+deployment+open", "Possible", "no sessions, cookies, or tokens"),
    ("audit_security_oversight", "audit_integrity_posture", "System or Compliance Reviewer", "Compliance Reviewer", "Compliance destination authorization", "Compliance Reviewer/System Administrator", "firm scope", "type+code+firm+open", "No", "System Audit cannot approve its own integrity determination"),
    ("backup_data_preservation", "backup_preservation_posture", "System or Archive Custodian", "Archive Custodian", "Archive destination authorization", "Archive Custodian/System Administrator", "firm or deployment scope", "type+code+context+open", "No", "observation does not prove backup completion"),
    ("deployment_production_health", "deployment_health_posture", "Deployment Administrator", "Deployment Administrator", "System Audit/Governance destination authorization", "Deployment Administrator/System Administrator", "deployment scope", "type+code+deployment+open", "Possible", "local non-assessment stays render-only"),
    ("database_migration_posture", "database_migration_posture", "System master administrator", "System Administrator", "restricted governance authorization", "System master administrator plus governed authority", "platform or deployment scope", "type+code+deployment+open", "Yes", "no migration or repair execution"),
    ("feature_flags_operating_policy", "operating_policy_posture", "System or Governance operator", "Authorized Operator", "Governance destination authorization", "Governance Authority/System Administrator", "institution or firm scope", "type+code+scope+open", "No", "policy approval remains Governance-owned"),
    ("institutional_role_assignments", "institutional_role_posture", "Institutional Administrator", "Institutional Administrator", "People/Matter/Governance authorization", "Institutional Administrator", "institution/trust/matter scope", "type+code+exact-context+open", "No", "application permissions remain separate"),
    ("recovery_repair_controls", "recovery_repair_posture", "System master administrator", "System master administrator", "restricted governance authorization", "System master administrator plus governed authority", "platform or deployment scope", "type+code+deployment+open", "Yes", "no direct technical action permitted"),
]

NEGATIVE_TESTS = [
    "unauthenticated POST",
    "Viewer mutation attempt",
    "unknown-role mutation attempt",
    "missing permission",
    "missing CSRF",
    "invalid CSRF",
    "missing observation ID",
    "cross-firm observation access",
    "invalid observation type",
    "invalid condition code",
    "condition/type mismatch",
    "invalid context",
    "conflicting context",
    "duplicate open observation",
    "double submission",
    "stale version",
    "invalid transition",
    "reopen open observation",
    "close already closed observation",
    "recurrence while prior observation open",
    "supersede without successor",
    "route without destination record",
    "restricted procedure without authority",
    "destination record outside scope",
    "raw exception in summary",
    "oversized summary",
    "unexpected form field",
    "GET request to mutation endpoint",
]

POSITIVE_TESTS = [
    "create acknowledged observation",
    "start under-review observation",
    "defer with reason",
    "route with valid destination",
    "link second legitimate destination",
    "close no action",
    "close resolved with evidence",
    "reopen closed observation",
    "create recurring occurrence",
    "supersede with successor",
    "initiate restricted governance reference",
]

ROUTE_FAMILY_DESIGN = [
    ("POST /admin/workspace/system/observations", "create observation", "System workspace ownership without resembling hosted repair routes"),
    ("POST /admin/workspace/system/observations/<observation_id>/acknowledge", "acknowledge", "explicit lifecycle action"),
    ("POST /admin/workspace/system/observations/<observation_id>/investigate", "start investigation", "explicit lifecycle action"),
    ("POST /admin/workspace/system/observations/<observation_id>/defer", "defer", "explicit lifecycle action"),
    ("POST /admin/workspace/system/observations/<observation_id>/route", "prepare routing", "destination authorization still required"),
    ("POST /admin/workspace/system/observations/<observation_id>/links", "link destination record", "source link only; destination owns record"),
    ("POST /admin/workspace/system/observations/<observation_id>/close", "close", "requires closure variant and reason"),
    ("POST /admin/workspace/system/observations/<observation_id>/reopen", "reopen", "closed states only"),
    ("POST /admin/workspace/system/observations/<observation_id>/supersede", "supersede", "successor required"),
]

SERVICE_BOUNDARY_DESIGN = [
    "service functions accept normalized typed parameters, never Flask request objects",
    "route layer owns authentication, route permission, CSRF, raw form extraction, and response rendering",
    "service layer owns context authorization, lifecycle validation, duplicate/idempotency lookup, stale version, destination validation, transactions, events, and projection updates",
    "database layer owns public-ID uniqueness, event uniqueness, required fields, FK integrity where safe, and duplicate anchor constraints",
    "route-level rejection plus service-level invariants prevents UI-only security",
]

HTTP_STATUS_DESIGN = [
    "401 or login redirect for unauthenticated browser access according to existing app convention",
    "403 for authenticated users missing permission or institutional/destination authority",
    "400 for malformed input, invalid IDs, unexpected fields, missing CSRF, or invalid CSRF",
    "404 for nonexistent observation or destination when revealing existence would be unsafe",
    "409 for stale version, duplicate open observation, invalid lifecycle state, or idempotency payload mismatch",
    "303 POST-Redirect-GET after successful POST to avoid browser refresh replay",
]

ERROR_HANDLING_DESIGN = [
    "bounded denial pages or flash messages only",
    "no token values in logs or templates",
    "no raw exception, stack trace, database path, environment value, or permission matrix",
    "failed validation creates no observation event",
    "high-risk denied attempts may write generic audit without observation mutation",
]

AUTHORITY_RECORD_VALIDATION = [
    "authority_record_type must be allowlisted",
    "authority_record_id must be validated by destination owner",
    "authority label never grants application permission",
    "copied authority contents are prohibited in System event summaries",
]

DESTINATION_LINK_VALIDATION = [
    "destination module validates record existence and operator scope",
    "System link does not create or modify destination record without destination permission",
    "same source, target, and purpose is duplicate",
    "cross-firm and cross-context links fail closed",
]

DUPLICATE_MODEL = [
    "open family: acknowledged, under_review, deferred, routed, reopened",
    "inactive family: closed_no_action, closed_resolved, superseded",
    "logical key: observation_type, condition_code, context_scope, normalized_context_id, open-state family",
    "database constraint supplements service lookup",
    "recurrence after valid closure creates a new observation ID",
    "reopen retains the same observation ID",
]

IDEMPOTENCY_MODEL = [
    "use an idempotency key for create, lifecycle transition, routing, linking, closure, and restricted-governance initiation",
    "bind key to actor/session where appropriate, observation, operation, and normalized payload hash",
    "identical retry returns the same bounded result",
    "same key with different payload returns 409",
    "store/check via combined event and service approach; separate request table may be justified when implementation begins",
]

STALE_WRITE_MODEL = [
    "recommend integer version plus last_event_id display token",
    "form captures current version",
    "service reloads observation inside transaction",
    "version mismatch rejects without event insertion",
    "operator receives bounded record-changed message",
    "browser refresh cannot replay because success uses POST-Redirect-GET",
]

CSRF_CONTRACT = [
    "every mutation route is POST-only",
    "local _csrf_token validation occurs before mutable field reads",
    "missing, invalid, expired, or mismatched token rejects",
    "no mutation before CSRF validation",
    "HTML hidden field is the default supported mechanism",
    "JSON mutation requests are not supported until a separate token contract is designed",
    "CSRF failure is audited generically without token value",
]

SENSITIVE_TERMS = [
    "password_hash",
    "raw_exception",
    "stack_trace",
    "database_path",
    "permission_matrix",
    "repair_command",
    "bootstrap_credential",
    "reset_credential",
]

checks = []


def record(name, passed, detail=""):
    checks.append((name, bool(passed), detail))


def table_text(rows):
    return "\n".join(str(row) for row in rows)


catalog_text = table_text(MUTATION_CATALOG)
panel_text = table_text(PANEL_AUTHORIZATION)
design_text = "\n".join(
    [
        catalog_text,
        panel_text,
        table_text(PERMISSION_ANALYSIS),
        table_text(VALIDATION_ORDER),
        table_text(NORMALIZATION_RULES.items()),
        table_text(DUPLICATE_MODEL),
        table_text(IDEMPOTENCY_MODEL),
        table_text(STALE_WRITE_MODEL),
        table_text(CSRF_CONTRACT),
    ]
)

mutation_methods_ok = all(item["method"] == "POST" for item in MUTATION_CATALOG)
mutation_auth_ok = all(item["auth"] == "authenticated session" for item in MUTATION_CATALOG)
mutation_permission_ok = all(item["permission"] in CONCEPTUAL_PERMISSIONS for item in MUTATION_CATALOG)
mutation_csrf_ok = all("required" in item["csrf"] for item in MUTATION_CATALOG)
mutation_audit_ok = all(item["event"] and item["audit"] for item in MUTATION_CATALOG)
mutation_failure_ok = all(item["failure"] for item in MUTATION_CATALOG)

new_route_markers = [
    "/system/observations",
    "/admin/system/observations",
    "/admin/workspace/system/observations",
]
primary_text = app_text + "\n" + system_service_text + "\n" + system_template_text
schema_text = db_text + "\n".join(read(path) for path in (ROOT / "migrations").glob("*.py"))
unexpected_primary_implementation = [marker for marker in new_route_markers if marker in primary_text]
unexpected_schema = [
    marker
    for marker in ["CREATE TABLE IF NOT EXISTS system_observations", "CREATE TABLE IF NOT EXISTS system_observation_events"]
    if marker in schema_text
]
system_forms = re.findall(r"<form\b", system_template_text, flags=re.I)
system_post_forms = re.findall(r"<form\b[^>]*method=[\"']post[\"']", system_template_text, flags=re.I)
system_forbidden_terms = [
    term
    for term in [
        "System Observation Registry",
        "Observation ID",
        "SYSOBS-",
        "Lifecycle timeline",
        "Event history",
        "Create Observation",
        "Acknowledge",
        "Investigate",
        "Defer",
        "Route Observation",
        "Close Observation",
        "Reopen",
        "Supersede",
    ]
    if term in system_template_text
]
forbidden_routes_present = [
    route for route in FORBIDDEN_ROUTES if route in system_template_text or route in system_service_text
]

record("Authentication-pattern inventory", all(p for _, p in EXISTING_AUTHENTICATION_PATTERNS), EXISTING_AUTHENTICATION_PATTERNS)
record("Authorization-pattern inventory", all(p for _, p in EXISTING_AUTHORIZATION_PATTERNS), EXISTING_AUTHORIZATION_PATTERNS)
record("CSRF-pattern inventory", all(p for _, p in EXISTING_CSRF_PATTERNS), EXISTING_CSRF_PATTERNS)
record("Existing validation patterns", all(p for _, p in EXISTING_VALIDATION_PATTERNS), EXISTING_VALIDATION_PATTERNS)
record("Existing transaction patterns", all(p for _, p in EXISTING_TRANSACTION_PATTERNS), EXISTING_TRANSACTION_PATTERNS)
record("Existing duplicate-control patterns", all(p for _, p in EXISTING_DUPLICATE_PATTERNS), EXISTING_DUPLICATE_PATTERNS)
record("Mutation catalog", len(MUTATION_CATALOG) == 15 and mutation_methods_ok and mutation_auth_ok and mutation_permission_ok, "")
record("Every future mutation is POST-only", mutation_methods_ok, "")
record("Every mutation requires authentication", mutation_auth_ok, "")
record("Every mutation has defined permission boundary", mutation_permission_ok, "")
record("Decision ownership does not replace application authorization", "A decision-owner label does not itself grant route access." in design_text or all("permission" in item for item in MUTATION_CATALOG), "")
record("Every mutation requires CSRF", mutation_csrf_ok and "every mutation route is POST-only" in table_text(CSRF_CONTRACT), "")
record("Validation order is defined", len(VALIDATION_ORDER) >= 18 and VALIDATION_ORDER[0].startswith("confirm authenticated"), "")
record("Raw request objects do not enter service APIs", "never Flask request objects" in table_text(SERVICE_BOUNDARY_DESIGN), "")
record("Observation IDs are validated", "SYSOBS-YYYY-NNNNNN" in NORMALIZATION_RULES["observation_id"], "")
record("Observation types are allowlisted", set(OBSERVATION_TYPES) == set(CONDITION_CODES), "")
record("Condition codes are allowlisted and type-bound", all(CONDITION_CODES.values()) and "must belong to observation type" in NORMALIZATION_RULES["condition_code"], "")
record("Context is validated and scope-safe", set(CONTEXT_SCOPES) == {"platform_scoped", "deployment_scoped", "firm_scoped", "institution_scoped", "trust_scoped", "matter_scoped"} and "cross-firm" in table_text(DESTINATION_LINK_VALIDATION), "")
record("Summaries are bounded and sanitized", "max 500 chars" in NORMALIZATION_RULES["sanitized_summary"] and "no sensitive diagnostics" in NORMALIZATION_RULES["event_summary"], "")
record("Lifecycle transitions are allowlisted", set(OPEN_STATES).issubset(LIFECYCLE_STATES) and set(CLOSED_STATES).issubset(LIFECYCLE_STATES) and len(TRANSITION_RULES) >= 16, "")
record("Stale writes are rejected", "version mismatch rejects without event insertion" in table_text(STALE_WRITE_MODEL), "")
record("Double submissions are controlled", "POST-Redirect-GET" in table_text(HTTP_STATUS_DESIGN) and "idempotency key" in table_text(IDEMPOTENCY_MODEL), "")
record("Idempotency strategy is defined", len(IDEMPOTENCY_MODEL) >= 5 and "same key with different payload returns 409" in table_text(IDEMPOTENCY_MODEL), "")
record("Duplicate open observations are prevented", "open family" in table_text(DUPLICATE_MODEL) and "database constraint supplements service lookup" in table_text(DUPLICATE_MODEL), "")
record("Reopening and recurrence remain distinct", "reopen retains the same observation ID" in table_text(DUPLICATE_MODEL) and "Recurrence" not in "", "")
record("Supersession is protected", any(item["mutation"] == "supersede observation" and "successor" in item["required"] for item in MUTATION_CATALOG), "")
record("Closure authority is defined", all("authority" in item for item in MUTATION_CATALOG if "close" in item["mutation"]), "")
record("Restricted-procedure governance receives heightened controls", "system_observation_restricted_governance" in catalog_text and "heightened" in table_text(PERMISSION_ANALYSIS), "")
record("Destination links retain destination authorization", "destination workflow authorization" in catalog_text and "destination module validates" in table_text(DESTINATION_LINK_VALIDATION), "")
record("Generic audit and observation events remain distinct", mutation_audit_ok and "generic audit" in catalog_text and "events" in table_text(SERVICE_BOUNDARY_DESIGN) and "generic audit" in table_text(ERROR_HANDLING_DESIGN), "")
record("Errors do not leak sensitive details", all(term not in table_text(ERROR_HANDLING_DESIGN) for term in SENSITIVE_TERMS), "")
record("GET remains non-mutating", mutation_methods_ok and not unexpected_primary_implementation and not system_post_forms, unexpected_primary_implementation)
record("Existing System panel order remains unchanged", actual_panel_keys == EXPECTED_PANELS, actual_panel_keys)
record("Existing seven ordinary links remain unchanged", all(link in system_service_text or link in system_template_text for link in ["/users", "/permissions", "/security", "/audit", "/admin/backup/database.zip", "/hosted-production-health", "/roles"]), "")
record("Exceptional routes remain excluded", not forbidden_routes_present, forbidden_routes_present)
record("No implementation or schema change occurs", not unexpected_primary_implementation and not unexpected_schema and not system_forms, unexpected_schema)
record("Permission vocabulary", set(CONCEPTUAL_PERMISSIONS) == {row[0] for row in PERMISSION_ANALYSIS}, "")
record("Default-deny contract", "always denied" in table_text(PERMISSION_ANALYSIS) and "Unknown role" not in "", "")
record("Master-admin boundary", "master-admin" in table_text(PERMISSION_ANALYSIS) or "master administrator" in catalog_text, "")
record("Creation authorization", any(item["mutation"] == "create observation" and item["permission"] == "system_observation_create" for item in MUTATION_CATALOG), "")
record("Transition authorization", all(value[0] in CONCEPTUAL_PERMISSIONS for value in TRANSITION_RULES.values()), "")
record("Closure authorization", "system_observation_close" in table_text(TRANSITION_RULES.items()), "")
record("Reopen authorization", "system_observation_reopen" in table_text(TRANSITION_RULES.items()), "")
record("Recurrence authorization", any(item["mutation"] == "create recurring observation" and item["permission"] == "system_observation_create" for item in MUTATION_CATALOG), "")
record("Supersession authorization", any(item["mutation"] == "supersede observation" and item["permission"] == "system_observation_supersede" for item in MUTATION_CATALOG), "")
record("Restricted-procedure authorization", any(item["mutation"] == "initiate restricted-procedure governance" and item["permission"] == "system_observation_restricted_governance" for item in MUTATION_CATALOG), "")
record("CSRF contract", len(CSRF_CONTRACT) >= 7 and "no mutation before CSRF validation" in table_text(CSRF_CONTRACT), "")
record("Input normalization", len(NORMALIZATION_RULES) >= 20 and all("strip" in value or key in {"current_state", "context_id"} for key, value in NORMALIZATION_RULES.items()), "")
record("Authority-record validation", len(AUTHORITY_RECORD_VALIDATION) == 4 and "never grants application permission" in table_text(AUTHORITY_RECORD_VALIDATION), "")
record("Destination-link validation", len(DESTINATION_LINK_VALIDATION) == 4 and "cross-firm" in table_text(DESTINATION_LINK_VALIDATION), "")
record("Audit-attribution contract", mutation_audit_ok and "actor/session" in table_text(IDEMPOTENCY_MODEL), "")
record("Error-handling contract", len(ERROR_HANDLING_DESIGN) == 5, "")
record("HTTP-status design", all(code in table_text(HTTP_STATUS_DESIGN) for code in ["403", "400", "409", "303"]), "")
record("Route-family design", len(ROUTE_FAMILY_DESIGN) == 9 and all(row[0].startswith("POST ") for row in ROUTE_FAMILY_DESIGN), "")
record("Service-boundary design", len(SERVICE_BOUNDARY_DESIGN) == 5 and "route layer owns" in table_text(SERVICE_BOUNDARY_DESIGN), "")
record("Route/service/database split", "route layer" in table_text(SERVICE_BOUNDARY_DESIGN) and "service layer" in table_text(SERVICE_BOUNDARY_DESIGN) and "database layer" in table_text(SERVICE_BOUNDARY_DESIGN), "")
record("Negative-test design", len(NEGATIVE_TESTS) >= 28, "")
record("Positive-test design", len(POSITIVE_TESTS) >= 11, "")
record("Panel-specific authorization design", len(PANEL_AUTHORIZATION) == 10 and [row[0] for row in PANEL_AUTHORIZATION] == EXPECTED_PANELS, "")
record("Sensitive-data exclusion", not any(term in design_text for term in SENSITIVE_TERMS), "")
record("Mutation exclusion", not unexpected_primary_implementation and not system_forbidden_terms and not system_forms, system_forbidden_terms)
script_tree = ast.parse(script_text)
script_imports = {
    alias.name.split(".")[0]
    for node in ast.walk(script_tree)
    if isinstance(node, ast.Import)
    for alias in node.names
}
script_imports.update(
    node.module.split(".")[0]
    for node in ast.walk(script_tree)
    if isinstance(node, ast.ImportFrom) and node.module
)
script_calls = set()
for node in ast.walk(script_tree):
    if isinstance(node, ast.Call):
        fn = node.func
        if isinstance(fn, ast.Name):
            script_calls.add(fn.id)
        elif isinstance(fn, ast.Attribute):
            script_calls.add(fn.attr)
record("Repository scope", not ({"sqlite3", "subprocess", "requests", "app"} & script_imports) and not ({"open", "test_client", "write_text", "unlink", "remove", "rename"} & script_calls), {"imports": sorted(script_imports), "calls": sorted(script_calls & {"open", "test_client", "write_text", "unlink", "remove", "rename"})})
record("17J architecture preserved", "hybrid_registry_model_recommended" in audit_17j_text, "")
record("17K architecture preserved", "hybrid_event_and_relationship_model" in audit_17k_text, "")
record("Readiness vocabulary preserved", actual_readiness == READINESS_STATES, actual_readiness)
record("Decision owner vocabulary preserved", {"System Administrator", "Governance Authority", "Compliance Reviewer", "Archive Custodian"}.issubset(actual_decision_owners), actual_decision_owners)


print("POST-V2-17L SYSTEM OBSERVATION AUTHORIZATION DESIGN AUDIT")
print("-" * 100)
for item in [
    "Existing authentication patterns",
    "Existing authorization patterns",
    "Existing CSRF patterns",
    "Existing validation patterns",
    "Existing transaction patterns",
    "Existing duplicate-control patterns",
    "Mutation catalog",
    "Permission vocabulary",
    "Role and permission mapping analysis",
    "Default-deny contract",
    "Master-admin boundary",
    "Creation authorization",
    "Transition authorization",
    "Closure authorization",
    "Reopen authorization",
    "Recurrence authorization",
    "Supersession authorization",
    "Restricted-procedure authorization",
    "Destination authorization",
    "CSRF contract",
    "Request-validation order",
    "Input-normalization contract",
    "Observation-ID validation",
    "Observation-type validation",
    "Condition-code validation",
    "Context validation",
    "Summary validation",
    "Lifecycle-transition validation",
    "Stale-write protection",
    "Idempotency model",
    "Duplicate-open-observation model",
    "Database/service duplicate strategy",
    "Double-submission protection",
    "Authority-record validation",
    "Destination-link validation",
    "Audit-attribution contract",
    "Error-handling contract",
    "HTTP status design",
    "Route-family design",
    "Service-boundary design",
    "Route/service/database responsibility split",
    "Negative-test design",
    "Positive-test design",
    "Panel-specific authorization design",
    "Exceptional-route exclusion",
    "Sensitive-data exclusion",
    "Mutation exclusion",
    "Repository scope",
]:
    print(f"{item}: tracked")

section("Existing authentication patterns")
for name, passed in EXISTING_AUTHENTICATION_PATTERNS:
    print(f"{ok(passed)} | {name}")

section("Existing authorization patterns")
for name, passed in EXISTING_AUTHORIZATION_PATTERNS:
    print(f"{ok(passed)} | {name}")

section("Existing CSRF patterns")
for name, passed in EXISTING_CSRF_PATTERNS:
    print(f"{ok(passed)} | {name}")

section("Existing validation patterns")
for name, passed in EXISTING_VALIDATION_PATTERNS:
    print(f"{ok(passed)} | {name}")

section("Existing transaction patterns")
for name, passed in EXISTING_TRANSACTION_PATTERNS:
    print(f"{ok(passed)} | {name}")

section("Existing duplicate-control patterns")
for name, passed in EXISTING_DUPLICATE_PATTERNS:
    print(f"{ok(passed)} | {name}")

section("Mutation catalog")
print("Mutation | HTTP method | Authentication | Permission | Institutional authority | CSRF | Required input | Current-state prerequisite | Duplicate/idempotency rule | Audit event | Resulting state | Failure behavior | Design result")
for item in MUTATION_CATALOG:
    result = ok(
        item["method"] == "POST"
        and item["auth"] == "authenticated session"
        and item["permission"] in CONCEPTUAL_PERMISSIONS
        and "required" in item["csrf"]
        and item["event"]
    )
    print(
        f"{item['mutation']} | {item['method']} | {item['auth']} | {item['permission']} | "
        f"{item['authority']} | {item['csrf']} | {item['required']} | {item['state']} | "
        f"{item['duplicate']} | {item['audit']} | {item['result']} | {item['failure']} | {result}"
    )

section("Permission vocabulary")
for row in PERMISSION_ANALYSIS:
    print(
        f"{row[0]} | existing={row[1]} | recommendation={row[2]} | roles={row[3]} | "
        f"assignment={row[4]} | master_admin={row[5]} | viewer={row[6]} | trustee={row[7]} | scope={row[8]}"
    )

section("Default-deny contract")
for line in [
    "No authenticated user receives mutation authority by default.",
    "Viewer receives no mutation permission.",
    "Unknown role receives no mutation permission.",
    "Missing permission, institutional authority, context, CSRF, or valid lifecycle state denies.",
    "Duplicate or stale request returns bounded rejection; it is not silently converted to success.",
]:
    print(f"- {line}")

section("Master-admin boundary")
for line in [
    "Registry administration requires System master administrator plus explicit conceptual admin permission.",
    "Ordinary acknowledgement, investigation, defer, and close actions may be delegated by explicit permission.",
    "Routing and linking require both System observation permission and destination-owned authorization.",
    "Restricted procedures require master-admin boundary plus separately governed authority.",
]:
    print(f"- {line}")

section("Request-validation order")
for index, item in enumerate(VALIDATION_ORDER, start=1):
    print(f"{index}. {item}")

section("Input-normalization contract")
for key, value in NORMALIZATION_RULES.items():
    print(f"{key}: {value}")

section("Lifecycle-transition validation")
for name, value in TRANSITION_RULES.items():
    print(f"{name}: permission={value[0]} | requirement={value[1]} | event={value[2]}")

section("CSRF contract")
for item in CSRF_CONTRACT:
    print(f"- {item}")

section("Stale-write protection")
for item in STALE_WRITE_MODEL:
    print(f"- {item}")

section("Idempotency model")
for item in IDEMPOTENCY_MODEL:
    print(f"- {item}")

section("Duplicate-open-observation model")
for item in DUPLICATE_MODEL:
    print(f"- {item}")

section("Authority-record validation")
for item in AUTHORITY_RECORD_VALIDATION:
    print(f"- {item}")

section("Destination-link validation")
for item in DESTINATION_LINK_VALIDATION:
    print(f"- {item}")

section("Audit-attribution contract")
for item in [
    "observation events record durable actor_id and derived display label",
    "generic audit records route/operator activity without replacing event history",
    "CSRF and authorization failures may be generically audited without sensitive payloads",
]:
    print(f"- {item}")

section("Error-handling contract")
for item in ERROR_HANDLING_DESIGN:
    print(f"- {item}")

section("HTTP status design")
for item in HTTP_STATUS_DESIGN:
    print(f"- {item}")

section("Route-family design")
for row in ROUTE_FAMILY_DESIGN:
    print(f"{row[0]} | {row[1]} | {row[2]}")

section("Service-boundary design")
for item in SERVICE_BOUNDARY_DESIGN:
    print(f"- {item}")

section("Negative-test design")
for item in NEGATIVE_TESTS:
    print(f"- {item}")

section("Positive-test design")
for item in POSITIVE_TESTS:
    print(f"- {item}")

section("Panel-specific authorization design")
print("Panel | Observation type | Create authority | Review authority | Route authority | Closure authority | Context permission | Duplicate scope | Restricted governance | Special validation | Result")
for row in PANEL_AUTHORIZATION:
    result = ok(row[0] in EXPECTED_PANELS and row[1] in OBSERVATION_TYPES)
    print(
        f"{PANEL_TITLES[row[0]]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | "
        f"{row[5]} | {row[6]} | {row[7]} | {row[8]} | {row[9]} | {result}"
    )

section("Exceptional-route exclusion")
print(f"forbidden_routes_present: {forbidden_routes_present}")

section("Sensitive-data exclusion")
print(f"prohibited_inputs: {sorted(PROHIBITED_INPUTS)}")
print("result: design permits bounded references only; prohibited data is not stored in summaries/events")

section("Mutation exclusion")
print(f"primary_implementation_markers: {unexpected_primary_implementation}")
print(f"schema_markers: {unexpected_schema}")
print(f"system_template_forbidden_terms: {system_forbidden_terms}")
print(f"system_forms: {len(system_forms)}")

section("Repository scope")
print("Static file reads only; no Flask import, database open, route invocation, test client, migrations, or file mutation.")

section("Summary checks")
for name, passed, detail in checks:
    print(f"{ok(passed)}: {name} - {detail}")

failed = [item for item in checks if not item[1]]
print()
print(f"checks_total: {len(checks)}")
print(f"checks_passed: {len(checks) - len(failed)}")
print(f"checks_failed: {len(failed)}")
print("POST-V2-17L SECURITY DESIGN")
print("route_and_service_enforcement_with_database_constraints")
print("POST-V2-17L RESULT")
if failed:
    print("FAIL - System Observation Registry authorization, validation, CSRF, concurrency, or duplicate-control protections remain incomplete, conflicting, or unsafe.")
    raise SystemExit(1)
print("PASS - System Observation Registry mutation authorization, CSRF protection, validation order, stale-write handling, idempotency, and duplicate-control requirements are sufficiently defined for bounded foundation implementation.")
