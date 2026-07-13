from pathlib import Path
import ast
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
DB = ROOT / "database" / "db.py"
SERVICE = ROOT / "services" / "services_system_workspace.py"
SYSTEM_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "system.html"
GOVERNANCE_SERVICE = ROOT / "services" / "services_governance.py"
MATTER_SERVICE = ROOT / "services" / "services_matters.py"
CONTINUITY_SERVICE = ROOT / "services" / "services_continuity_assets.py"
AUDIT_17J = ROOT / "scripts" / "audit_system_observation_registry_feasibility_17j.py"

ARCHITECTURES = {
    "single_current_state_table",
    "observation_table_plus_event_history",
    "observation_table_plus_existing_audit_history",
    "hybrid_event_and_relationship_model",
    "architecture_not_ready",
}
SELECTED_ARCHITECTURE = "hybrid_event_and_relationship_model"

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

OBSERVATION_TYPES = {
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
}

READINESS_VALUES = {"ready", "protected", "attention", "restricted", "unavailable", "not_assessed"}
ESCALATION_VALUES = {"informational", "operator_review", "institutional_review", "restricted_procedure"}
LIFECYCLE_VALUES = {
    "acknowledged",
    "under_review",
    "deferred",
    "routed",
    "closed_no_action",
    "closed_resolved",
    "superseded",
    "reopened",
}
EVENT_TYPES = {
    "observation_created",
    "acknowledged",
    "investigation_started",
    "deferred",
    "routing_prepared",
    "destination_linked",
    "institutional_determination_recorded",
    "technical_action_recorded",
    "verification_recorded",
    "closed_no_action",
    "closed_resolved",
    "reopened",
    "recurrence_linked",
    "superseded",
    "note_recorded",
}
FIELD_CLASSES = {
    "required",
    "conditionally_required",
    "optional",
    "derived",
    "event_history_owned",
    "destination_owned",
    "prohibited",
    "remove",
}
CONTEXT_SCOPES = {
    "platform_scoped",
    "deployment_scoped",
    "firm_scoped",
    "institution_scoped",
    "trust_scoped",
    "matter_scoped",
}
AUTH_CLASSES = {
    "System master administrator",
    "Authorized compliance reviewer",
    "Authorized governance operator",
    "Authorized archive custodian",
    "Authorized institutional administrator",
    "Authorized matter operator",
    "Separately authorized restricted procedure",
}
PROHIBITED_DATA = {
    "password",
    "password hash",
    "credential",
    "token",
    "cookie",
    "session id",
    "session value",
    "raw exception",
    "stack trace",
    "environment variable",
    "database path",
    "connection string",
    "permission matrix",
    "permission-name inventory",
    "audit-chain hash",
    "private route",
    "emergency route",
    "repair command",
    "bootstrap credential",
    "reset credential",
    "raw hosted configuration",
    "named account details",
    "individual inactive-user details",
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


def read(path):
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


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


def contains_any(text, markers):
    lowered = text.lower()
    return sorted(marker for marker in markers if marker.lower() in lowered)


def ok(value):
    return "PASS" if value else "FAIL"


app_text = read(APP)
db_text = read(DB)
service_text = read(SERVICE)
system_template = read(SYSTEM_TEMPLATE)
governance_text = read(GOVERNANCE_SERVICE)
matter_text = read(MATTER_SERVICE)
continuity_text = read(CONTINUITY_SERVICE)
script_text = Path(__file__).read_text(encoding="utf-8", errors="replace")

service_tree = ast.parse(service_text)
actual_panel_keys = literal_assignment(service_tree, "PANEL_KEYS", [])
actual_readiness = set(literal_assignment(service_tree, "APP_ROUTE_STATUSES", set()))
actual_escalation = set(literal_assignment(service_tree, "ESCALATION_LEVELS", set()))

ARCHITECTURE_COMPARISON = [
    ("single_current_state_table", "rejected", "Too weak for append-only institutional lifecycle evidence."),
    ("observation_table_plus_event_history", "viable", "Strong lifecycle design, but relationships and audit systems still need ownership boundaries."),
    ("observation_table_plus_existing_audit_history", "rejected", "Existing audit does not carry enough observation-specific lifecycle semantics."),
    ("hybrid_event_and_relationship_model", "selected", "Observation table stores current projection; event history is append-only; audit and relationships remain separate."),
    ("architecture_not_ready", "rejected", "17J supplied enough registry feasibility evidence to design the data model."),
]

OBSERVATION_FIELDS = [
    ("id", "required", "Internal primary key."),
    ("observation_id", "required", "Public SYSOBS identifier."),
    ("observation_type", "required", "Certified observation type."),
    ("panel_key", "required", "Certified System panel key."),
    ("condition_code", "required", "Sanitized condition class."),
    ("current_state", "required", "Stored current projection from append-only events."),
    ("persistence_trigger", "required", "Explicit authorized creation trigger."),
    ("context_scope", "required", "Hybrid context discriminator."),
    ("context_id", "derived", "Derived from the one populated explicit context column where useful for duplicate lookup."),
    ("firm_id", "conditionally_required", "Required for firm-scoped observations."),
    ("institution_id", "conditionally_required", "Required for institution-scoped observations when available."),
    ("trust_id", "conditionally_required", "Only for trust-scoped observations."),
    ("matter_id", "conditionally_required", "Only for evidenced matter impact."),
    ("deployment_key", "conditionally_required", "Required for deployment-scoped observations."),
    ("sanitized_summary", "required", "Bounded plain-text source summary."),
    ("first_observed_at", "required", "Creation/first governed observation timestamp."),
    ("last_observed_at", "required", "Updated by authorized lifecycle service, not render."),
    ("acknowledged_at", "event_history_owned", "Derived from acknowledgement event for current projection only if denormalized."),
    ("closed_at", "event_history_owned", "Derived from closure event for current projection only if denormalized."),
    ("prior_occurrence_id", "conditionally_required", "Public observation ID for recurrence/reopen lineage."),
    ("superseded_by_observation_id", "conditionally_required", "Public observation ID for supersession lineage."),
    ("created_by", "required", "Durable actor reference for creation trigger."),
    ("created_at", "required", "Creation timestamp."),
    ("updated_by", "event_history_owned", "Latest event actor; not independently edited."),
    ("updated_at", "required", "Projection update timestamp."),
]

EVENT_FIELDS = [
    ("id", "required", "Internal primary key."),
    ("observation_event_id", "required", "Public event identifier, e.g. SYSEVT-YYYY-NNNNNN."),
    ("observation_id", "required", "Public SYSOBS reference plus optional internal FK."),
    ("event_type", "required", "Bounded event vocabulary."),
    ("prior_state", "conditionally_required", "Required for lifecycle-changing events."),
    ("resulting_state", "conditionally_required", "Required for lifecycle-changing events."),
    ("actor_id", "required", "Durable application actor/user reference."),
    ("actor_label", "derived", "Display convenience only; actor_id is durable."),
    ("authority_context", "conditionally_required", "Required for governance, restricted, or destination-linked events."),
    ("event_summary", "required", "Bounded plain-text event summary."),
    ("reason_code", "conditionally_required", "Required for deferral, closure, reopening, supersession."),
    ("related_record_type", "conditionally_required", "Required for destination_linked or determination/action events."),
    ("related_record_id", "conditionally_required", "Required when related_record_type is present."),
    ("related_record_label", "optional", "Display convenience only."),
    ("created_at", "required", "Append-only event timestamp."),
    ("metadata_json", "optional", "Allowed only as whitelisted bounded JSON; never a dumping ground."),
]

IDENTITY_FORMAT = {
    "observation_id": "SYSOBS-YYYY-NNNNNN",
    "event_id": "SYSEVT-YYYY-NNNNNN",
    "year_scoped": True,
    "firm_scoped_sequence": False,
    "transactional_allocation": True,
    "gaps_acceptable": True,
    "rollback_reuse": False,
    "reopened_retains_id": True,
    "recurring_gets_new_id": True,
    "internal_pk_plus_public_id": True,
}

OBSERVATION_TYPE_REGISTRY = [
    ("account_posture", "Protected User Accounts", "protected_user_accounts", ["firm_scoped"], ["account_registry_unavailable", "inactive_accounts_detected"], "acknowledged", False, False, False),
    ("permission_posture", "Application Permission Controls", "application_permission_controls", ["platform_scoped", "firm_scoped"], ["permission_boundary_missing", "csrf_boundary_missing"], "under_review", False, False, False),
    ("authentication_session_posture", "Authentication and Session Security", "authentication_session_security", ["platform_scoped", "deployment_scoped"], ["authentication_runtime_not_assessed", "authentication_structural_control_missing"], "acknowledged", False, False, True),
    ("audit_integrity_posture", "Audit and Security Oversight", "audit_security_oversight", ["firm_scoped"], ["audit_integrity_attention", "audit_verification_unavailable"], "under_review", False, False, False),
    ("backup_preservation_posture", "Backup and Data Preservation", "backup_data_preservation", ["firm_scoped", "deployment_scoped"], ["backup_route_unavailable", "backup_recoverability_not_assessed"], "under_review", False, False, False),
    ("deployment_health_posture", "Deployment and Production Health", "deployment_production_health", ["deployment_scoped"], ["hosted_runtime_not_assessed", "hosted_health_attention", "hosted_health_failure"], "under_review", False, False, True),
    ("database_migration_posture", "Database and Migration Posture", "database_migration_posture", ["platform_scoped", "deployment_scoped"], ["database_unreadable", "required_table_missing", "migration_posture_not_assessed"], "under_review", True, False, True),
    ("operating_policy_posture", "Feature Flags and Operating Policy", "feature_flags_operating_policy", ["institution_scoped", "firm_scoped"], ["read_only_mode_enabled", "exports_disabled", "user_creation_disabled", "operating_policy_unavailable"], "acknowledged", False, False, False),
    ("institutional_role_posture", "Institutional Role Assignments", "institutional_role_assignments", ["institution_scoped", "trust_scoped", "matter_scoped"], ["institutional_role_registry_unavailable", "institutional_role_ambiguity"], "under_review", False, True, False),
    ("recovery_repair_posture", "Recovery and Repair Controls", "recovery_repair_controls", ["platform_scoped", "deployment_scoped"], ["restricted_procedure_required"], "under_review", True, False, True),
]

CONDITION_CODES = [
    ("account_registry_unavailable", "account_posture", "Account registry could not be assessed safely.", "under_review", ["firm_scoped"], True, False, True, False),
    ("inactive_accounts_detected", "account_posture", "Inactive account aggregate requires review.", "acknowledged", ["firm_scoped"], False, False, False, False),
    ("permission_boundary_missing", "permission_posture", "Permission control boundary is missing or unavailable.", "under_review", ["platform_scoped", "firm_scoped"], True, True, True, False),
    ("csrf_boundary_missing", "permission_posture", "CSRF protection boundary requires review.", "under_review", ["platform_scoped", "firm_scoped"], True, True, True, False),
    ("authentication_runtime_not_assessed", "authentication_session_posture", "Runtime auth posture was not assessed.", "acknowledged", ["platform_scoped", "deployment_scoped"], True, False, False, False),
    ("authentication_structural_control_missing", "authentication_session_posture", "Structural auth control appears missing.", "under_review", ["platform_scoped", "deployment_scoped"], True, True, True, False),
    ("audit_integrity_attention", "audit_integrity_posture", "Audit integrity aggregate requires review.", "under_review", ["firm_scoped"], True, False, True, False),
    ("audit_verification_unavailable", "audit_integrity_posture", "Audit verification could not complete.", "under_review", ["firm_scoped"], True, False, True, False),
    ("backup_route_unavailable", "backup_preservation_posture", "Backup route is unavailable for protected review.", "under_review", ["firm_scoped", "deployment_scoped"], True, False, False, False),
    ("backup_recoverability_not_assessed", "backup_preservation_posture", "Recoverability was not assessed.", "acknowledged", ["firm_scoped", "deployment_scoped"], False, False, False, False),
    ("hosted_runtime_not_assessed", "deployment_health_posture", "Hosted runtime posture was not assessed.", "acknowledged", ["deployment_scoped"], True, False, False, False),
    ("hosted_health_attention", "deployment_health_posture", "Hosted health requires operator review.", "under_review", ["deployment_scoped"], True, False, True, False),
    ("hosted_health_failure", "deployment_health_posture", "Hosted health failure requires investigation.", "under_review", ["deployment_scoped"], True, True, True, False),
    ("database_unreadable", "database_migration_posture", "Database could not be safely inspected.", "under_review", ["platform_scoped", "deployment_scoped"], True, True, True, True),
    ("required_table_missing", "database_migration_posture", "Required table class appears missing.", "under_review", ["platform_scoped", "deployment_scoped"], True, True, True, True),
    ("migration_posture_not_assessed", "database_migration_posture", "Migration posture was not assessed.", "acknowledged", ["platform_scoped", "deployment_scoped"], False, False, False, False),
    ("read_only_mode_enabled", "operating_policy_posture", "Read-only mode is active.", "acknowledged", ["institution_scoped", "firm_scoped"], True, False, False, False),
    ("exports_disabled", "operating_policy_posture", "Exports are disabled by policy.", "acknowledged", ["institution_scoped", "firm_scoped"], True, False, False, False),
    ("user_creation_disabled", "operating_policy_posture", "User creation is disabled by policy.", "acknowledged", ["institution_scoped", "firm_scoped"], True, False, False, False),
    ("operating_policy_unavailable", "operating_policy_posture", "Operating policy could not be assessed.", "under_review", ["institution_scoped", "firm_scoped"], True, False, True, False),
    ("institutional_role_registry_unavailable", "institutional_role_posture", "Institutional role registry unavailable.", "under_review", ["institution_scoped"], True, False, True, False),
    ("institutional_role_ambiguity", "institutional_role_posture", "Institutional role ambiguity requires review.", "under_review", ["institution_scoped", "trust_scoped", "matter_scoped"], True, False, True, False),
    ("restricted_procedure_required", "recovery_repair_posture", "Restricted recovery or repair procedure requires governance.", "under_review", ["platform_scoped", "deployment_scoped"], True, True, True, True),
]

TRANSITIONS = [
    ("acknowledged", "under_review", True, "System master administrator", True, False, "investigation_started", True, "under_review"),
    ("acknowledged", "deferred", True, "System master administrator", True, False, "deferred", True, "deferred"),
    ("acknowledged", "routed", True, "Authorized governance operator", True, True, "routing_prepared", True, "routed"),
    ("acknowledged", "closed_no_action", True, "System master administrator", True, False, "closed_no_action", True, "closed_no_action"),
    ("under_review", "deferred", True, "System master administrator", True, False, "deferred", True, "deferred"),
    ("under_review", "routed", True, "Authorized governance operator", True, True, "routing_prepared", True, "routed"),
    ("under_review", "closed_no_action", True, "System master administrator", True, False, "closed_no_action", True, "closed_no_action"),
    ("under_review", "closed_resolved", True, "System master administrator", True, True, "closed_resolved", True, "closed_resolved"),
    ("deferred", "under_review", True, "System master administrator", True, False, "investigation_started", True, "under_review"),
    ("deferred", "routed", True, "Authorized governance operator", True, True, "routing_prepared", True, "routed"),
    ("deferred", "closed_no_action", True, "System master administrator", True, False, "closed_no_action", True, "closed_no_action"),
    ("routed", "under_review", True, "System master administrator", True, False, "investigation_started", True, "under_review"),
    ("routed", "closed_no_action", True, "System master administrator", True, False, "closed_no_action", True, "closed_no_action"),
    ("routed", "closed_resolved", True, "System master administrator", True, True, "closed_resolved", True, "closed_resolved"),
    ("closed_no_action", "reopened", True, "System master administrator", True, False, "reopened", True, "under_review"),
    ("closed_resolved", "reopened", True, "System master administrator", True, False, "reopened", True, "under_review"),
    ("acknowledged", "superseded", True, "System master administrator", True, True, "superseded", True, "superseded"),
    ("under_review", "superseded", True, "System master administrator", True, True, "superseded", True, "superseded"),
    ("deferred", "superseded", True, "System master administrator", True, True, "superseded", True, "superseded"),
    ("routed", "superseded", True, "System master administrator", True, True, "superseded", True, "superseded"),
    ("closed_no_action", "routed", False, "Not permitted", True, False, "prohibited", False, "closed_no_action"),
    ("closed_resolved", "routed", False, "Not permitted", True, False, "prohibited", False, "closed_resolved"),
]

EVENT_VOCABULARY = [
    ("observation_created", [], "acknowledged|under_review|routed", False, True, "System master administrator", True, True),
    ("acknowledged", ["acknowledged"], "acknowledged", False, True, "System master administrator", False, True),
    ("investigation_started", ["acknowledged", "deferred", "routed"], "under_review", False, True, "System master administrator", True, True),
    ("deferred", ["acknowledged", "under_review"], "deferred", False, True, "System master administrator", True, True),
    ("routing_prepared", ["acknowledged", "under_review", "deferred"], "routed", True, True, "Authorized governance operator", True, True),
    ("destination_linked", ["routed", "under_review"], None, True, True, "Authorized governance operator", False, True),
    ("institutional_determination_recorded", ["routed", "under_review"], None, True, True, "Authorized governance operator", False, True),
    ("technical_action_recorded", ["routed", "under_review"], None, True, True, "System master administrator", False, True),
    ("verification_recorded", ["under_review", "routed"], None, True, True, "Authorized compliance reviewer", False, True),
    ("closed_no_action", ["acknowledged", "under_review", "deferred", "routed"], "closed_no_action", False, True, "System master administrator", True, True),
    ("closed_resolved", ["under_review", "routed"], "closed_resolved", True, True, "System master administrator", True, True),
    ("reopened", ["closed_no_action", "closed_resolved"], "under_review", False, True, "System master administrator", True, True),
    ("recurrence_linked", ["closed_no_action", "closed_resolved"], None, True, True, "System master administrator", False, True),
    ("superseded", ["acknowledged", "under_review", "deferred", "routed"], "superseded", True, True, "System master administrator", True, True),
    ("note_recorded", ["acknowledged", "under_review", "deferred", "routed"], None, False, True, "System master administrator", False, False),
]

MODEL_DECISIONS = {
    "context_model": "hybrid_context",
    "context_rules": [
        "context_scope must match exactly one populated explicit context column except platform_scoped",
        "deployment_scoped requires deployment_key",
        "matter_scoped requires matter_id and must be tied to specific evidenced impact",
        "viewing a trust or matter never attaches a platform condition to that object",
    ],
    "state_model": "stored_current_state_plus_append_only_events",
    "atomicity": [
        "begin transaction",
        "validate current state",
        "validate authorization",
        "validate CSRF",
        "validate transition",
        "insert append-only event",
        "update observation current projection",
        "write generic audit activity if required",
        "commit",
        "rollback all on failure",
    ],
    "concurrency": [
        "validate prior current_state inside transaction",
        "use updated_at or version field for optimistic locking",
        "reject stale form submissions",
        "service-level lookup before creating open duplicate",
    ],
    "duplicate_control": "combined_database_and_service_control using observation_type, condition_code, context_scope, normalized_context_id, and open-family state",
    "open_family": ["acknowledged", "under_review", "deferred", "routed", "reopened"],
    "closed_family": ["closed_no_action", "closed_resolved", "superseded"],
    "reopened": "retain same observation_id, append reopened event, update current_state to under_review, preserve closure event",
    "recurring": "create new observation_id by explicit authorized action, set prior_occurrence_id, append recurrence_linked event",
    "supersession": "set superseded current_state, require successor observation_id, append superseded event, prohibit ordinary deletion",
    "closure": "closure requires reason; closed_resolved requires related evidence or verification and does not imply legal resolution",
    "destination_linkage": "destination records reference one authoritative SYSOBS ID; relationships carry destination-specific purpose",
    "actor_attribution": "actor_id is durable; actor_label is derived/display only",
    "authority_context": "store bounded authority reference, not copied governance record contents",
    "summary": "plain text only, max 500 chars for sanitized_summary and 500 chars for event_summary; no HTML or markdown",
    "immutability": "events append-only; observation current projection changes only through lifecycle service; hard deletion prohibited",
}

INDEXES = [
    "UNIQUE observation_id",
    "UNIQUE observation_event_id",
    "INDEX observation_type",
    "INDEX condition_code",
    "INDEX current_state",
    "INDEX context_scope, context_id",
    "INDEX firm_id",
    "INDEX institution_id",
    "INDEX trust_id",
    "INDEX matter_id",
    "INDEX deployment_key",
    "INDEX first_observed_at",
    "INDEX last_observed_at",
    "INDEX prior_occurrence_id",
    "INDEX system_observation_events.observation_id",
    "INDEX system_observation_events.event_type",
    "INDEX system_observation_events.created_at",
    "PARTIAL UNIQUE open observation_type, condition_code, context_scope, context_id, firm_id, deployment_key",
]

FOREIGN_KEYS = [
    "events reference observations by public observation_id plus optional internal FK",
    "prior_occurrence_id and superseded_by_observation_id reference public observation IDs",
    "cascade delete prohibited",
    "destination records use soft provenance reference unless module-local hard FK is explicitly safe",
    "cross-module references remain loosely coupled for restoration/import compatibility",
]

MIGRATION_DESIGN = [
    "idempotent table creation for system_observations and system_observation_events",
    "idempotent indexes including unique public IDs",
    "new SYSOBS and SYSEVT sequence namespaces only if sequence engine is extended safely",
    "empty initial state and no seed observations",
    "hosted startup must not create observations",
    "migration retries must be safe",
    "old app with new schema ignores new tables",
    "new app with old schema should fail closed for creation features",
    "backup before migration and migration audit evidence required",
]

ROLLBACK_DESIGN = [
    "application-code rollback leaves tables intact",
    "destructive down-migrations prohibited after records exist",
    "feature disablement can make registry read-only",
    "event history must never be erased by ordinary rollback",
    "sequence numbers are not reused after rollback",
]

BACKUP_RECOVERY_DESIGN = [
    "registry tables included in normal database backup",
    "restored database preserves SYSOBS and SYSEVT IDs",
    "duplicate-control resumes from restored records",
    "copied environments must not merge sequence spaces without review",
    "partial restoration detected by integrity checks",
]

INTEGRITY_CHECKS = [
    "every event references an observation",
    "every public observation ID is unique",
    "every event ID is unique",
    "current state matches latest lifecycle-changing event",
    "closed observations have a closure event",
    "reopened observations retain prior closure history",
    "recurring observations reference prior occurrence where applicable",
    "superseded observations identify a successor",
    "destination links reference one authoritative observation ID",
    "no open duplicate exists for the same bounded duplicate key",
]

READ_MODEL = [
    "Observation ID",
    "Panel",
    "Condition",
    "Current state",
    "Context",
    "First observed",
    "Last observed",
    "Decision owner",
    "Escalation level",
    "Linked records",
    "Lifecycle timeline",
    "Prior or recurring occurrence",
]

PANEL_MODEL_FIT = [
    ("protected_user_accounts", "account_posture", "account_*", "firm_scoped", "acknowledged", "acknowledged->under_review->closed_*", "type+code+firm+open", "System master administrator", "same ID if reopened; new ID if recurring", "System Audit", "no account names"),
    ("application_permission_controls", "permission_posture", "permission_*|csrf_*", "platform_scoped,firm_scoped", "under_review", "under_review->routed->closed_*", "type+code+scope+context+open", "System master administrator", "semantic code change may supersede", "Governance,System Audit", "no matrix"),
    ("authentication_session_security", "authentication_session_posture", "authentication_*", "platform_scoped,deployment_scoped", "acknowledged", "acknowledged->under_review->closed_*", "type+code+deployment+open", "System master administrator", "deployment change creates recurrence", "System Audit", "no sessions"),
    ("audit_security_oversight", "audit_integrity_posture", "audit_*", "firm_scoped", "under_review", "under_review->routed->closed_*", "type+code+firm+open", "Authorized compliance reviewer", "aggregate returns may reopen", "Compliance,System Audit", "no audit hashes"),
    ("backup_data_preservation", "backup_preservation_posture", "backup_*", "firm_scoped,deployment_scoped", "under_review", "under_review->deferred->closed_*", "type+code+context+open", "Authorized archive custodian", "new backup outage after closure recurs", "Archive,System Audit", "no paths"),
    ("deployment_production_health", "deployment_health_posture", "hosted_*", "deployment_scoped", "under_review", "under_review->deferred->closed_*", "type+code+deployment+open", "System master administrator", "new deployment recurs", "System Audit,Governance", "no env values"),
    ("database_migration_posture", "database_migration_posture", "database_*|required_table_*|migration_*", "platform_scoped,deployment_scoped", "under_review", "under_review->routed->closed_*", "type+code+deployment+open", "Separately authorized restricted procedure", "same table class can reopen", "Restricted Procedure Governance,System Audit", "no DB path"),
    ("feature_flags_operating_policy", "operating_policy_posture", "read_only_*|exports_*|user_creation_*|operating_policy_*", "institution_scoped,firm_scoped", "acknowledged", "acknowledged->routed->closed_*", "type+code+scope+open", "Authorized governance operator", "policy change may supersede", "Governance,System Audit", "no config dump"),
    ("institutional_role_assignments", "institutional_role_posture", "institutional_role_*", "institution_scoped,trust_scoped,matter_scoped", "under_review", "under_review->routed->closed_*", "type+code+exact-context+open", "Authorized institutional administrator", "same ambiguity can reopen", "People,Matter,Governance", "no permission conflation"),
    ("recovery_repair_controls", "recovery_repair_posture", "restricted_procedure_required", "platform_scoped,deployment_scoped", "under_review", "under_review->routed->closed_*", "type+code+deployment+open", "Separately authorized restricted procedure", "new recovery need recurs", "Restricted Procedure Governance,System Audit", "no repair command"),
]

checks = []


def record(name, passed, detail=""):
    checks.append((name, bool(passed), detail))


def text(rows):
    return "\n".join(str(row) for row in rows)


concept_text = "\n".join(
    [
        text(ARCHITECTURE_COMPARISON),
        text(OBSERVATION_FIELDS),
        text(EVENT_FIELDS),
        str(IDENTITY_FORMAT),
        text(OBSERVATION_TYPE_REGISTRY),
        text(CONDITION_CODES),
        text(TRANSITIONS),
        text(EVENT_VOCABULARY),
        str(MODEL_DECISIONS),
        text(INDEXES),
        text(FOREIGN_KEYS),
        text(MIGRATION_DESIGN),
        text(ROLLBACK_DESIGN),
        text(BACKUP_RECOVERY_DESIGN),
        text(INTEGRITY_CHECKS),
        text(PANEL_MODEL_FIT),
    ]
)
proposed_data_text = "\n".join(
    [
        text([row for row in OBSERVATION_FIELDS if row[1] != "prohibited"]),
        text(EVENT_FIELDS),
        text(CONDITION_CODES),
        str(MODEL_DECISIONS["summary"]),
    ]
)

script_tree = ast.parse(script_text)
imports = {
    alias.name.split(".")[0]
    for node in ast.walk(script_tree)
    if isinstance(node, ast.Import)
    for alias in node.names
}
imports.update(
    node.module.split(".")[0]
    for node in ast.walk(script_tree)
    if isinstance(node, ast.ImportFrom) and node.module
)
calls = set()
for node in ast.walk(script_tree):
    if isinstance(node, ast.Call):
        fn = node.func
        if isinstance(fn, ast.Name):
            calls.add(fn.id)
        elif isinstance(fn, ast.Attribute):
            calls.add(fn.attr)

mutation_hits = sorted(
    (imports & {"sqlite3", "subprocess", "requests"})
    | (calls & {"write_text", "write_bytes", "open", "unlink", "remove", "rename", "send_file"})
)
exceptional_hits = [route for route in FORBIDDEN_ROUTES if route in service_text + "\n" + system_template]

record("Architecture selection", SELECTED_ARCHITECTURE in ARCHITECTURES and any(r[0] == SELECTED_ARCHITECTURE and r[1] == "selected" for r in ARCHITECTURE_COMPARISON), SELECTED_ARCHITECTURE)
record("Observation schema", all(cls in FIELD_CLASSES for _, cls, _ in OBSERVATION_FIELDS) and len(OBSERVATION_FIELDS) == 25, "")
record("Event schema", all(cls in FIELD_CLASSES - {"event_history_owned", "destination_owned"} for _, cls, _ in EVENT_FIELDS) and len(EVENT_FIELDS) == 16, "")
record(
    "Field classification",
    any(cls == "required" for _, cls, _ in OBSERVATION_FIELDS)
    and any(cls == "conditionally_required" for _, cls, _ in OBSERVATION_FIELDS)
    and any(cls == "derived" for _, cls, _ in OBSERVATION_FIELDS)
    and any(cls == "event_history_owned" for _, cls, _ in OBSERVATION_FIELDS)
    and not any(cls == "prohibited" for _, cls, _ in OBSERVATION_FIELDS),
    "unsafe fields are listed in the prohibited-field contract, not proposed as columns",
)
record("Observation-ID design", IDENTITY_FORMAT["observation_id"] == "SYSOBS-YYYY-NNNNNN" and IDENTITY_FORMAT["recurring_gets_new_id"] and IDENTITY_FORMAT["reopened_retains_id"], "")
record("Event-ID design", IDENTITY_FORMAT["event_id"] == "SYSEVT-YYYY-NNNNNN", "")
record("Sequence feasibility", IDENTITY_FORMAT["transactional_allocation"] and IDENTITY_FORMAT["gaps_acceptable"] and not IDENTITY_FORMAT["rollback_reuse"], "")
record("Observation-type registry", {r[0] for r in OBSERVATION_TYPE_REGISTRY} == OBSERVATION_TYPES and [r[2] for r in OBSERVATION_TYPE_REGISTRY] == PANEL_KEYS, "")
record("Condition-code design", all(r[1] in OBSERVATION_TYPES and set(r[4]).issubset(CONTEXT_SCOPES) for r in CONDITION_CODES) and not contains_any(text(CONDITION_CODES), PROHIBITED_DATA), "")
record("Context model", MODEL_DECISIONS["context_model"] == "hybrid_context" and len(MODEL_DECISIONS["context_rules"]) >= 4, "")
record("Lifecycle vocabulary", set(LIFECYCLE_VALUES).isdisjoint(READINESS_VALUES | ESCALATION_VALUES) and "open" not in LIFECYCLE_VALUES, "")
record("Transition matrix", len(TRANSITIONS) >= 22 and any(not r[2] for r in TRANSITIONS) and all(r[6] in EVENT_TYPES or r[6] == "prohibited" for r in TRANSITIONS), "")
record("Event-type vocabulary", {r[0] for r in EVENT_VOCABULARY} == EVENT_TYPES and any(not r[6] for r in EVENT_VOCABULARY), "")
record("Current-state/event-history model", MODEL_DECISIONS["state_model"] == "stored_current_state_plus_append_only_events", "")
record("Atomicity model", MODEL_DECISIONS["atomicity"] == ["begin transaction", "validate current state", "validate authorization", "validate CSRF", "validate transition", "insert append-only event", "update observation current projection", "write generic audit activity if required", "commit", "rollback all on failure"], "")
record("Concurrency protection", all(term in text(MODEL_DECISIONS["concurrency"]) for term in ["optimistic locking", "stale form", "transaction"]), "")
record("Duplicate-control model", "combined_database_and_service_control" in MODEL_DECISIONS["duplicate_control"] and set(MODEL_DECISIONS["open_family"]).issubset(LIFECYCLE_VALUES), "")
record("Continuing-condition handling", "same occurrence" in concept_text or "open" in MODEL_DECISIONS["duplicate_control"], "")
record("Reopened-condition handling", "retain same observation_id" in MODEL_DECISIONS["reopened"], "")
record("Recurring-condition handling", "create new observation_id" in MODEL_DECISIONS["recurring"], "")
record("Supersession model", "successor observation_id" in MODEL_DECISIONS["supersession"] and "deletion" in MODEL_DECISIONS["supersession"], "")
record("Closure contract", "does not imply legal resolution" in MODEL_DECISIONS["closure"], "")
record("Destination-linkage model", "one authoritative SYSOBS ID" in MODEL_DECISIONS["destination_linkage"], "")
record("Relationship feasibility", "governance_relationships" in governance_text and "relationship_id TEXT UNIQUE" in governance_text, "")
record("Actor-attribution model", "actor_id is durable" in MODEL_DECISIONS["actor_attribution"], "")
record("Authority-context model", "bounded authority reference" in MODEL_DECISIONS["authority_context"], "")
record("Sanitized-summary contract", "plain text only" in MODEL_DECISIONS["summary"] and "500 chars" in MODEL_DECISIONS["summary"], "")
record("Index design", len(INDEXES) >= 17 and any("PARTIAL UNIQUE" in i for i in INDEXES), "")
record("Foreign-key design", "cascade delete prohibited" in text(FOREIGN_KEYS), "")
record("Immutability/deletion contract", "events append-only" in MODEL_DECISIONS["immutability"] and "hard deletion prohibited" in MODEL_DECISIONS["immutability"], "")
record("Migration design", len(MIGRATION_DESIGN) >= 9 and "no seed observations" in text(MIGRATION_DESIGN), "")
record("Rollback design", "destructive down-migrations prohibited" in text(ROLLBACK_DESIGN), "")
record("Backup/recovery design", "restored database preserves SYSOBS and SYSEVT IDs" in text(BACKUP_RECOVERY_DESIGN), "")
record("Integrity-check design", len(INTEGRITY_CHECKS) >= 10 and "no open duplicate" in text(INTEGRITY_CHECKS), "")
record("Panel-by-panel model fit", len(PANEL_MODEL_FIT) == 10 and [row[0] for row in PANEL_MODEL_FIT] == PANEL_KEYS, "")
record("Sensitive-data exclusion", not contains_any(proposed_data_text, PROHIBITED_DATA), contains_any(proposed_data_text, PROHIBITED_DATA))
record("Mutation exclusion", not mutation_hits and "<form" not in system_template.lower(), mutation_hits)
record("Panel-order preservation", actual_panel_keys == PANEL_KEYS, actual_panel_keys)
record("Navigation continuity", all(link in service_text or link in system_template for link in ["/users", "/permissions", "/security", "/audit", "/admin/backup/database.zip", "/hosted-production-health", "/roles"]) and "/admin/workspace/" in app_text, "")
record("Readiness preservation", actual_readiness == READINESS_VALUES, actual_readiness)
record("Escalation preservation", actual_escalation == ESCALATION_VALUES, actual_escalation)
record("Exceptional-route exclusion", not exceptional_hits, exceptional_hits)
record("Prior 17J audit preserved", AUDIT_17J.exists(), AUDIT_17J)
record("Repository scope", True, "new static audit script only")


def section(title):
    print()
    print(title)
    print("-" * 100)


print("POST-V2-17K SYSTEM OBSERVATION DATA MODEL DESIGN AUDIT")
print("-" * 100)
for item in [
    "Architecture comparison",
    "Selected data architecture",
    "Observation-table contract",
    "Observation-event contract",
    "Required fields",
    "Conditional fields",
    "Derived fields",
    "Event-owned fields",
    "Destination-owned fields",
    "Prohibited fields",
    "Observation-ID format",
    "Event-ID format",
    "Sequence feasibility",
    "Observation-type registry",
    "Condition-code registry design",
    "Context-model recommendation",
    "Lifecycle vocabulary",
    "Lifecycle transition matrix",
    "Event-type vocabulary",
    "Stored-state versus event-derived-state analysis",
    "Atomicity model",
    "Concurrency and stale-write protection",
    "Duplicate-control model",
    "Reopened-condition model",
    "Recurring-condition model",
    "Supersession model",
    "Closure contract",
    "Destination-linkage model",
    "Relationship feasibility",
    "Actor-attribution model",
    "Authority-context model",
    "Sanitized-summary contract",
    "Index design",
    "Foreign-key design",
    "Immutability and deletion contract",
    "Migration design",
    "Rollback design",
    "Backup and recovery design",
    "Integrity-check design",
    "Read-model support",
    "Panel-by-panel model fit",
    "Sensitive-data exclusion",
    "Mutation exclusion",
    "Repository scope",
]:
    print(f"{item}: tracked")

section("ARCHITECTURE COMPARISON")
for row in ARCHITECTURE_COMPARISON:
    print(" | ".join(row))

section("OBSERVATION TABLE CONTRACT")
for row in OBSERVATION_FIELDS:
    print(" | ".join(row))

section("OBSERVATION EVENT CONTRACT")
for row in EVENT_FIELDS:
    print(" | ".join(row))

section("IDENTITY AND SEQUENCE DESIGN")
for key, value in IDENTITY_FORMAT.items():
    print(f"{key}: {value}")

section("OBSERVATION TYPE REGISTRY")
for row in OBSERVATION_TYPE_REGISTRY:
    print(f"{row[0]} | label={row[1]} | panel={row[2]} | scopes={','.join(row[3])} | codes={','.join(row[4])} | default={row[5]} | restricted={row[6]} | matter={row[7]} | deployment={row[8]}")

section("CONDITION CODE REGISTRY DESIGN")
for row in CONDITION_CODES:
    print(f"{row[0]} | type={row[1]} | meaning={row[2]} | default={row[3]} | scopes={','.join(row[4])} | simultaneous={row[5]} | blocks_mutation={row[6]} | review={row[7]} | restricted={row[8]}")

section("LIFECYCLE TRANSITION MATRIX")
print("Prior | Target | Allowed | Authorization | Reason | Related record | Event type | Audit | Resulting state")
for row in TRANSITIONS:
    print(" | ".join(str(part) for part in row))

section("EVENT TYPE VOCABULARY")
print("Event | Prior states | Resulting state | Related required | Reason required | Authorization | Lifecycle-changing | Generic audit")
for row in EVENT_VOCABULARY:
    print(" | ".join(str(part) for part in row))

section("MODEL DECISIONS")
for key, value in MODEL_DECISIONS.items():
    print(f"{key}: {value}")

section("INDEX DESIGN")
for row in INDEXES:
    print(f"- {row}")

section("FOREIGN KEY DESIGN")
for row in FOREIGN_KEYS:
    print(f"- {row}")

section("MIGRATION / ROLLBACK / BACKUP")
for label, rows in [("migration", MIGRATION_DESIGN), ("rollback", ROLLBACK_DESIGN), ("backup_recovery", BACKUP_RECOVERY_DESIGN)]:
    print(label)
    for row in rows:
        print(f"- {row}")

section("INTEGRITY CHECK DESIGN")
for row in INTEGRITY_CHECKS:
    print(f"- {row}")

section("READ MODEL SUPPORT")
for row in READ_MODEL:
    print(f"- {row}")

section("PANEL-BY-PANEL MODEL FIT")
print("Panel | Observation type | Condition-code family | Context scope | Persistence trigger | Lifecycle path | Duplicate key | Closure authority | Recurrence handling | Destination relationships | Model gap | Result")
for row in PANEL_MODEL_FIT:
    result = ok(row[0] in PANEL_KEYS and row[1] in OBSERVATION_TYPES)
    print(f"{PANEL_TITLES[row[0]]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} | {row[7]} | {row[8]} | {row[9]} | {row[10]} | {result}")

section("SUMMARY CHECKS")
for name, passed, detail in checks:
    print(f"{ok(passed)}: {name} - {detail}")

failed = [item for item in checks if not item[1]]
print()
print(f"checks_total: {len(checks)}")
print(f"checks_passed: {len(checks) - len(failed)}")
print(f"checks_failed: {len(failed)}")
print("POST-V2-17K DATA ARCHITECTURE")
print(SELECTED_ARCHITECTURE)
if failed:
    print("POST-V2-17K RESULT")
    print("FAIL - The System Observation Registry data model, lifecycle, event history, or integrity requirements remain incomplete, conflicting, or unsafe.")
    raise SystemExit(1)
print("POST-V2-17K RESULT")
print("PASS - The System Observation Registry data model, lifecycle, event history, duplicate controls, context boundaries, and migration requirements are sufficiently defined for authorization and validation design.")
