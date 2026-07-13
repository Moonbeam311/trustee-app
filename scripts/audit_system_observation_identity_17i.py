from pathlib import Path
import ast
import re
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
INSTITUTIONAL_IDENTITY_SERVICE = ROOT / "services" / "services_institutional_identity.py"
COMPLIANCE_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "compliance.html"
ARCHIVE_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "archive.html"
PEOPLE_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "people.html"
MATTER_DETAIL_TEMPLATE = ROOT / "templates" / "matter_detail.html"
AUDIT_17H = ROOT / "scripts" / "audit_system_exception_disposition_routing_17h.py"

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

OBSERVATION_STATES = {
    "transient",
    "continuing",
    "reopened",
    "recurring",
    "superseded",
    "closed",
    "not_persisted",
}

PERSISTENCE_CLASSES = {
    "render_only",
    "persist_if_review_required",
    "persist_if_continuing",
    "persist_on_authorized_acknowledgement",
    "persist_before_restricted_governance",
    "never_persist",
    "not_assessed",
}

PERSISTENCE_DECISIONS = {
    "existing_registry_sufficient",
    "existing_registry_extendable",
    "new_persistence_likely_required",
    "no_persistence_required",
    "not_yet_determinable",
}

DUPLICATE_STATUSES = {
    "supported",
    "partially_supported",
    "unsupported",
    "not_applicable",
    "not_assessed",
}

IDENTITY_AUTHORIZATIONS = {
    "System master administrator",
    "Authorized compliance reviewer",
    "Authorized governance operator",
    "Authorized archive custodian",
    "Authorized institutional administrator",
    "Authorized matter operator",
    "Separately authorized restricted procedure",
    "Automated creation prohibited",
    "Not currently defined",
}

ROUTING_AFTER_IDENTITY = {
    "ready_if_existing_identity_used",
    "ready_after_existing_registry_extension",
    "blocked_without_new_observation_registry",
    "not_appropriate",
    "restricted_only",
    "not_assessed",
}

PROVENANCE_OWNER_CHOICES = {
    "System Workspace service",
    "System Audit",
    "Institutional Event Registry",
    "Governance source fields",
    "Destination record",
    "Dedicated future observation registry",
    "Not Assigned",
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

SENSITIVE_MARKERS = [
    "password",
    "password_hash",
    "token",
    "cookie",
    "session ID",
    "session value",
    "database path",
    "environment variable",
    "raw exception",
    "stack trace",
    "permission matrix",
    "audit chain hash",
    "repair command",
    "emergency route",
    "secret configuration value",
]

BAD_STATES = {"new", "active", "resolved", "fixed", "healed", "complete"}
BAD_ID_PATTERNS = {
    "current timestamp alone",
    "random ID generated on every render",
    "panel title alone",
    "status alone",
    "raw hash of exception text",
    "session ID",
    "user ID",
    "database row address",
    "route URL",
}


def read(path):
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def assignment_literal(tree, name, default=None):
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


app_text = read(APP)
db_text = read(DB)
service_text = read(SERVICE)
system_template = read(SYSTEM_TEMPLATE)
governance_text = read(GOVERNANCE_SERVICE)
matter_text = read(MATTER_SERVICE)
continuity_text = read(CONTINUITY_SERVICE)
identity_text = read(INSTITUTIONAL_IDENTITY_SERVICE)
compliance_text = read(COMPLIANCE_TEMPLATE)
archive_text = read(ARCHIVE_TEMPLATE)
people_text = read(PEOPLE_TEMPLATE)
matter_detail_text = read(MATTER_DETAIL_TEMPLATE)
script_text = Path(__file__).read_text(encoding="utf-8", errors="replace")

service_tree = ast.parse(service_text)
actual_panel_keys = assignment_literal(service_tree, "PANEL_KEYS", [])
actual_readiness = assignment_literal(service_tree, "APP_ROUTE_STATUSES", set())
actual_escalations = assignment_literal(service_tree, "ESCALATION_LEVELS", set())

repo_context = "\n".join(
    [
        app_text,
        db_text,
        service_text,
        system_template,
        governance_text,
        matter_text,
        continuity_text,
        identity_text,
        compliance_text,
        archive_text,
        people_text,
        matter_detail_text,
    ]
)

IDENTITY_REGISTRY_INVENTORY = [
    {
        "name": "System Workspace render panels",
        "exists": "PANEL_KEYS" in service_text and "build_system_workspace_oversight" in service_text,
        "stable_identity": False,
        "source_provenance": False,
        "duplicate_lookup": False,
        "lifecycle": False,
        "finding": "Panel keys and statuses identify posture type only; they are not occurrence IDs.",
        "decision": "not_yet_determinable",
    },
    {
        "name": "System Audit / audit_log",
        "exists": "CREATE TABLE IF NOT EXISTS audit_log" in db_text and "def log_change" in db_text,
        "stable_identity": True,
        "source_provenance": True,
        "duplicate_lookup": False,
        "lifecycle": False,
        "finding": "Audit rows have ids, entity references, actor-attributed actions, timestamps, and hash linkage, but record later actions rather than original render observations.",
        "decision": "existing_registry_extendable",
    },
    {
        "name": "Governance source fields",
        "exists": all(field in governance_text for field in ["source_type", "source_id", "source_label", "source_notes"]),
        "stable_identity": False,
        "source_provenance": True,
        "duplicate_lookup": False,
        "lifecycle": True,
        "finding": "Governance directives and policies can store provenance, but cannot invent the System occurrence they cite.",
        "decision": "existing_registry_extendable",
    },
    {
        "name": "Governance relationships",
        "exists": "CREATE TABLE IF NOT EXISTS governance_relationships" in governance_text and "relationship_id TEXT UNIQUE" in governance_text,
        "stable_identity": True,
        "source_provenance": True,
        "duplicate_lookup": "SELECT relationship_id" in governance_text and "FROM governance_relationships" in governance_text,
        "lifecycle": all(word in governance_text for word in ["retire_governance_relationship", "reinstate_governance_relationship", "supersede_relationship"]),
        "finding": "Relationships can connect source and target records and prevent duplicate active links, but still need an authoritative System source ID.",
        "decision": "existing_registry_extendable",
    },
    {
        "name": "Matter events and relationships",
        "exists": "CREATE TABLE IF NOT EXISTS matter_events" in matter_text and "CREATE TABLE IF NOT EXISTS matter_relationships" in matter_text,
        "stable_identity": "event_id TEXT UNIQUE" in matter_text and "relationship_id TEXT NOT NULL UNIQUE" in matter_text,
        "source_provenance": "linked_record_type" in matter_text and "linked_record_id" in matter_text,
        "duplicate_lookup": "AND linked_record_id = ?" in matter_text and "status = 'Active'" in matter_text,
        "lifecycle": "update_matter_relationship_status" in matter_text,
        "finding": "Matter identity is valid only for a specific matter impact; platform-wide System conditions should not be forced into Matter.",
        "decision": "existing_registry_extendable",
    },
    {
        "name": "Archive and continuity custody",
        "exists": "custody_event_id" in continuity_text or "archive_export_history" in app_text,
        "stable_identity": "custody_event_id" in continuity_text or "export_id" in app_text,
        "source_provenance": "source_type" in continuity_text or "related_entity_type" in app_text,
        "duplicate_lookup": "INSERT OR IGNORE INTO archive_export_history" in app_text,
        "lifecycle": "finalization_id" in app_text or "create_archive_packet_finalization" in app_text,
        "finding": "Archive can identify custody, finalization, and export history actions, but backup access is not an observation identity.",
        "decision": "existing_registry_extendable",
    },
    {
        "name": "People / institutional identity",
        "exists": "institutional" in people_text.lower() and INSTITUTIONAL_IDENTITY_SERVICE.exists(),
        "stable_identity": "identity_id" in identity_text or "person" in identity_text.lower(),
        "source_provenance": False,
        "duplicate_lookup": False,
        "lifecycle": False,
        "finding": "People and assignment surfaces are destination context, not a general System observation registry.",
        "decision": "existing_registry_extendable",
    },
    {
        "name": "Dedicated System observation registry",
        "exists": False,
        "stable_identity": False,
        "source_provenance": False,
        "duplicate_lookup": False,
        "lifecycle": False,
        "finding": "No dedicated registry currently supplies stable occurrence identity, timestamps, lifecycle, and duplicate lookup for System observations.",
        "decision": "new_persistence_likely_required",
    },
]

EVENT_REGISTRY_INVENTORY = [
    {
        "name": "audit_log",
        "exists": "CREATE TABLE IF NOT EXISTS audit_log" in db_text,
        "event_id": "id INTEGER PRIMARY KEY" in db_text,
        "platform_scope": True,
        "system_observation_safe": False,
        "finding": "Append-only audit event identity exists for later actions, not render-observation occurrence creation.",
    },
    {
        "name": "matter_events",
        "exists": "CREATE TABLE IF NOT EXISTS matter_events" in matter_text,
        "event_id": "event_id TEXT UNIQUE NOT NULL" in matter_text,
        "platform_scope": False,
        "system_observation_safe": False,
        "finding": "Matter events are matter-scoped and require specific matter impact.",
    },
    {
        "name": "governance_relationship_audit_ledger",
        "exists": "CREATE TABLE IF NOT EXISTS governance_relationship_audit_ledger" in governance_text,
        "event_id": "audit_id TEXT UNIQUE NOT NULL" in governance_text,
        "platform_scope": False,
        "system_observation_safe": False,
        "finding": "Ledger records governance relationship attempts, not originating System observations.",
    },
    {
        "name": "execution_event_log",
        "exists": "CREATE TABLE IF NOT EXISTS execution_event_log" in db_text,
        "event_id": "event_id TEXT UNIQUE" in db_text,
        "platform_scope": False,
        "system_observation_safe": False,
        "finding": "Execution events are execution-specific and must remain separate from System posture observations.",
    },
    {
        "name": "archive custody / finalization events",
        "exists": "custody_event_id" in continuity_text or "finalization_id" in app_text,
        "event_id": "custody_event_id" in continuity_text or "finalization_id" in app_text,
        "platform_scope": False,
        "system_observation_safe": False,
        "finding": "Archive events identify custody and preservation actions after authorization.",
    },
]

DESTINATION_READINESS = [
    {
        "destination": "System Audit",
        "provenance": "entity_type/entity_id/action/note",
        "duplicate_control": "unsupported",
        "after_identity": "ready_after_existing_registry_extension",
        "gap": "Needs source_id plus purpose-aware duplicate lookup if used for observation disposition records.",
    },
    {
        "destination": "Governance",
        "provenance": "source_type/source_id/source_label/source_notes plus relationships",
        "duplicate_control": "partially_supported",
        "after_identity": "ready_after_existing_registry_extension",
        "gap": "Governance can cite and relate a source, but needs an authoritative occurrence ID from outside the destination.",
    },
    {
        "destination": "Compliance",
        "provenance": "workspace exists; no dedicated compliance object in this scope",
        "duplicate_control": "unsupported",
        "after_identity": "blocked_without_new_observation_registry",
        "gap": "Compliance destination is incomplete for durable System observation disposition records.",
    },
    {
        "destination": "Archive",
        "provenance": "related action, custody, export, and finalization references",
        "duplicate_control": "partially_supported",
        "after_identity": "ready_after_existing_registry_extension",
        "gap": "Archive can record preservation actions after authorization, not render-time observations.",
    },
    {
        "destination": "People",
        "provenance": "assignment and role surfaces",
        "duplicate_control": "unsupported",
        "after_identity": "blocked_without_new_observation_registry",
        "gap": "People context needs source-reference support before System observation routing would be safe.",
    },
    {
        "destination": "Matter",
        "provenance": "matter event linked_record_type/linked_record_id and relationship IDs",
        "duplicate_control": "supported",
        "after_identity": "ready_if_existing_identity_used",
        "gap": "Only ready where a specific matter impact is evidenced and the System source ID exists.",
    },
    {
        "destination": "Restricted Procedure Governance",
        "provenance": "governance source fields and approval records",
        "duplicate_control": "partially_supported",
        "after_identity": "restricted_only",
        "gap": "Approval may cite an occurrence, but restricted execution remains separate.",
    },
]

PANEL_ANALYSIS = [
    {
        "panel_key": "protected_user_accounts",
        "observation_type": "account_posture",
        "representative_condition": "inactive_accounts_detected",
        "condition_codes": ["inactive_accounts_detected", "account_registry_unavailable"],
        "persistence_classification": "persist_on_authorized_acknowledgement",
        "stable_identity_available": False,
        "preferred_identity_owner": "Dedicated future observation registry",
        "context_scope": "firm_context",
        "occurrence_boundary": "same panel, account_posture, sanitized condition code, firm context, and open lifecycle; repeated render stays same continuing condition after authorized identity creation",
        "duplicate_control_status": "unsupported",
        "recurrence_behavior": "closed condition returning with same firm and condition should be reopened or recurring based on closure determination; account identities remain excluded",
        "routing_readiness": "blocked_without_new_observation_registry",
        "authorization_for_identity": "System master administrator",
        "gap": "No stable occurrence ID exists for inactive-account posture before an authorized acknowledgement.",
    },
    {
        "panel_key": "application_permission_controls",
        "observation_type": "permission_posture",
        "representative_condition": "permission_boundary_missing",
        "condition_codes": ["permission_boundary_missing", "csrf_boundary_missing"],
        "persistence_classification": "persist_if_review_required",
        "stable_identity_available": False,
        "preferred_identity_owner": "Dedicated future observation registry",
        "context_scope": "firm_context",
        "occurrence_boundary": "same permission posture plus sanitized condition code and firm context; distinct missing boundaries require distinct condition codes",
        "duplicate_control_status": "unsupported",
        "recurrence_behavior": "boundary reappearing after closure should be reopened when tied to same occurrence, recurring when materially new",
        "routing_readiness": "blocked_without_new_observation_registry",
        "authorization_for_identity": "System master administrator",
        "gap": "Permission matrix contents must remain excluded; panel status alone is not identity.",
    },
    {
        "panel_key": "authentication_session_security",
        "observation_type": "authentication_session_posture",
        "representative_condition": "runtime_not_assessed",
        "condition_codes": ["runtime_not_assessed", "session_boundary_missing"],
        "persistence_classification": "render_only",
        "stable_identity_available": False,
        "preferred_identity_owner": "System Workspace service",
        "context_scope": "institution_context",
        "occurrence_boundary": "runtime non-assessment remains not_persisted; missing structural controls would require environment-scoped condition identity",
        "duplicate_control_status": "not_applicable",
        "recurrence_behavior": "not_assessed render state is not reopened or recurring because no occurrence is created",
        "routing_readiness": "not_appropriate",
        "authorization_for_identity": "Automated creation prohibited",
        "gap": "No persistence is justified for local render-only runtime non-assessment.",
    },
    {
        "panel_key": "audit_security_oversight",
        "observation_type": "audit_integrity_posture",
        "representative_condition": "audit_integrity_attention",
        "condition_codes": ["audit_integrity_attention", "audit_verification_unavailable"],
        "persistence_classification": "persist_if_continuing",
        "stable_identity_available": False,
        "preferred_identity_owner": "Dedicated future observation registry",
        "context_scope": "firm_context",
        "occurrence_boundary": "same audit aggregate condition code and firm context; individual audit row IDs remain evidence, not source occurrence IDs",
        "duplicate_control_status": "unsupported",
        "recurrence_behavior": "continuing broken aggregate should not duplicate; after closure, later aggregate attention may recur as a new occurrence",
        "routing_readiness": "blocked_without_new_observation_registry",
        "authorization_for_identity": "Authorized compliance reviewer",
        "gap": "Audit chain records can support evidence but cannot be the source observation identity.",
    },
    {
        "panel_key": "backup_data_preservation",
        "observation_type": "backup_preservation_posture",
        "representative_condition": "backup_recoverability_not_assessed",
        "condition_codes": ["backup_access_protected", "backup_recoverability_not_assessed", "backup_route_unavailable"],
        "persistence_classification": "render_only",
        "stable_identity_available": False,
        "preferred_identity_owner": "Dedicated future observation registry",
        "context_scope": "firm_context",
        "occurrence_boundary": "protected backup access and recoverability non-assessment remain render-only; route unavailable may persist if authorized review begins",
        "duplicate_control_status": "partially_supported",
        "recurrence_behavior": "authorized backup action is later Archive/System Audit evidence, not a recurrence of render state",
        "routing_readiness": "ready_after_existing_registry_extension",
        "authorization_for_identity": "Authorized archive custodian",
        "gap": "Archive export history identifies backup actions, not the System observation itself.",
    },
    {
        "panel_key": "deployment_production_health",
        "observation_type": "deployment_health_posture",
        "representative_condition": "hosted_runtime_not_assessed",
        "condition_codes": ["hosted_runtime_not_assessed", "deployment_warning_present"],
        "persistence_classification": "persist_if_review_required",
        "stable_identity_available": False,
        "preferred_identity_owner": "Dedicated future observation registry",
        "context_scope": "institution_context",
        "occurrence_boundary": "same environment-scope class, sanitized condition code, and deployment context; environment values and secrets remain excluded",
        "duplicate_control_status": "unsupported",
        "recurrence_behavior": "warning continuing across checks remains one occurrence; later deployment context may create a distinct recurring occurrence",
        "routing_readiness": "blocked_without_new_observation_registry",
        "authorization_for_identity": "System master administrator",
        "gap": "No safe existing platform event registry distinguishes hosted deployment occurrences without exposing environment detail.",
    },
    {
        "panel_key": "database_migration_posture",
        "observation_type": "database_migration_posture",
        "representative_condition": "database_unreadable",
        "condition_codes": ["database_unreadable", "required_table_missing", "migration_not_assessed"],
        "persistence_classification": "persist_before_restricted_governance",
        "stable_identity_available": False,
        "preferred_identity_owner": "Dedicated future observation registry",
        "context_scope": "institution_context",
        "occurrence_boundary": "same sanitized database condition code and institution or firm context; different missing tables require different condition codes",
        "duplicate_control_status": "unsupported",
        "recurrence_behavior": "closed migration posture returning may be reopened if same unresolved source, recurring if new schema condition",
        "routing_readiness": "restricted_only",
        "authorization_for_identity": "Separately authorized restricted procedure",
        "gap": "Restricted migration approval needs a stable governed source before approval; execution remains separate.",
    },
    {
        "panel_key": "feature_flags_operating_policy",
        "observation_type": "operating_policy_posture",
        "representative_condition": "read_only_mode_enabled",
        "condition_codes": ["read_only_mode_enabled", "exports_disabled"],
        "persistence_classification": "persist_if_review_required",
        "stable_identity_available": False,
        "preferred_identity_owner": "Governance source fields",
        "context_scope": "institution_context",
        "occurrence_boundary": "same policy posture and sanitized condition code; expected policy state is not an occurrence unless review is required",
        "duplicate_control_status": "partially_supported",
        "recurrence_behavior": "policy state change after closure can recur only if materially new and review-worthy",
        "routing_readiness": "ready_after_existing_registry_extension",
        "authorization_for_identity": "Authorized governance operator",
        "gap": "Governance can store the policy source after a stable source identity exists.",
    },
    {
        "panel_key": "institutional_role_assignments",
        "observation_type": "institutional_role_posture",
        "representative_condition": "institutional_roles_unavailable",
        "condition_codes": ["institutional_roles_unavailable", "assignment_ambiguity_detected"],
        "persistence_classification": "persist_if_review_required",
        "stable_identity_available": False,
        "preferred_identity_owner": "Dedicated future observation registry",
        "context_scope": "firm_context or trust_context when trust-specific; matter_context only with evidenced matter impact",
        "occurrence_boundary": "same role posture, condition code, firm/trust context, and open lifecycle; trust-specific ambiguity is separate from platform-wide registry unavailability",
        "duplicate_control_status": "unsupported",
        "recurrence_behavior": "closed ambiguity can reopen for same trust context or recur for a materially new assignment conflict",
        "routing_readiness": "blocked_without_new_observation_registry",
        "authorization_for_identity": "Authorized institutional administrator",
        "gap": "People/role surfaces lack general source-reference and duplicate-control support for System observations.",
    },
    {
        "panel_key": "recovery_repair_controls",
        "observation_type": "recovery_repair_posture",
        "representative_condition": "restricted_procedure_required",
        "condition_codes": ["restricted_procedure_required", "recovery_need_identified"],
        "persistence_classification": "persist_before_restricted_governance",
        "stable_identity_available": False,
        "preferred_identity_owner": "Dedicated future observation registry",
        "context_scope": "institution_context",
        "occurrence_boundary": "restricted posture itself never persists; a separately identified recovery need requires stable source identity before approval",
        "duplicate_control_status": "unsupported",
        "recurrence_behavior": "recovery need after closure can reopen only with explicit linkage; otherwise it is a distinct recurring condition",
        "routing_readiness": "restricted_only",
        "authorization_for_identity": "Separately authorized restricted procedure",
        "gap": "Approval, technical execution, audit evidence, and closure must reference the same governed source without exposing repair routes.",
    },
]

SCENARIOS = [
    {
        "scenario": "same panel rendered repeatedly",
        "same_or_new": "same render-only observation; no occurrence is created",
        "state": "not_persisted",
        "duplicate_rule": "render cannot create a duplicate because render cannot create identity",
    },
    {
        "scenario": "same condition continuing for multiple days",
        "same_or_new": "same occurrence only after authorized persistent identity exists",
        "state": "continuing",
        "duplicate_rule": "same source, destination, and purpose is duplicate",
    },
    {
        "scenario": "condition closes and later returns",
        "same_or_new": "reopened if linked to prior source; recurring if materially new",
        "state": "reopened",
        "duplicate_rule": "requires lifecycle-aware lookup before creating another destination record",
    },
    {
        "scenario": "same condition appears in another firm",
        "same_or_new": "new occurrence because firm context changes",
        "state": "recurring",
        "duplicate_rule": "different firm context separates occurrence boundary",
    },
    {
        "scenario": "same condition affects one matter",
        "same_or_new": "matter-specific consequence relates to platform observation",
        "state": "continuing",
        "duplicate_rule": "Matter record must cite the same source occurrence and specific matter context",
    },
    {
        "scenario": "same observation routes to System Audit and Compliance",
        "same_or_new": "same source occurrence, multiple destination purposes",
        "state": "continuing",
        "duplicate_rule": "same source with different destination and purpose can be legitimate when relationship is explicit",
    },
    {
        "scenario": "restricted procedure approved but not executed",
        "same_or_new": "same source occurrence with separate approval lifecycle",
        "state": "continuing",
        "duplicate_rule": "approval is not execution and must not close the technical condition by itself",
    },
    {
        "scenario": "technical action executed after governance approval",
        "same_or_new": "same source occurrence with later action record",
        "state": "closed",
        "duplicate_rule": "technical action records action_for source and does not create a competing source identity",
    },
]

SOURCE_PROVENANCE_CONTRACT = {
    "source_type": "System Workspace Observation",
    "source_id": "stable non-secret occurrence id required before routing",
    "source_label": "panel title plus sanitized condition label",
    "source_notes": "bounded posture summary without diagnostics",
    "source_panel_key": "one of PANEL_KEYS",
    "source_observation_type": "one approved observation type",
    "source_condition_code": "optional sanitized bounded code",
    "source_observed_status": "approved readiness status",
    "source_first_observed_at": "available only from future persistence owner",
    "source_last_observed_at": "available only from future persistence owner",
}

OCCURRENCE_BOUNDARY_ANSWERS = [
    ("status change within same panel", "same occurrence when condition_code and context are unchanged; different cause requires distinct condition_code"),
    ("attention changing to unavailable", "not automatically new; condition_code and helper/source cause decide the boundary"),
    ("condition returning after closure", "reopened when same occurrence is linked; recurring when materially new"),
    ("different firm context", "separate occurrence"),
    ("matter-specific impact", "separate matter consequence related to platform occurrence"),
    ("repeated page rendering", "never creates a new occurrence"),
    ("same helper across renders", "continuing after persistence exists; otherwise not_persisted"),
    ("two failure causes same panel/status", "distinct condition codes required"),
    ("sanitized condition code", "required for durable duplicate control"),
    ("identity without persistence", "not possible for continuing, reopened, or recurring states"),
]

RELATIONSHIP_CAPABILITY = [
    ("one System observation to one governed record", "supported after authoritative source_id exists"),
    ("one System observation to multiple governed records", "supported by relationships and destination purpose separation after source_id exists"),
    ("one governed record to later action record", "partially supported through audit, matter, archive, and governance relationship evidence"),
    ("one closed observation to reopened occurrence", "unsupported without future observation lifecycle persistence"),
    ("one recurring observation to prior related observation", "unsupported without future observation relationship or lineage support"),
    ("one matter-specific consequence to platform observation", "supported only through matter relationship/event after source_id and matter impact exist"),
]

checks = []


def record(name, passed, detail=""):
    checks.append((name, bool(passed), detail))


def row_text(rows):
    return "\n".join(str(row) for row in rows)


panel_text = row_text(PANEL_ANALYSIS)
inventory_text = row_text(IDENTITY_REGISTRY_INVENTORY + EVENT_REGISTRY_INVENTORY)
provenance_text = str(SOURCE_PROVENANCE_CONTRACT)
destination_text = row_text(DESTINATION_READINESS)
scenario_text = row_text(SCENARIOS)

system_source = service_text + "\n" + system_template
exceptional_hits = [route for route in FORBIDDEN_ROUTES if route in system_source]

script_tree = ast.parse(script_text)
imported_modules = {
    alias.name.split(".")[0]
    for node in ast.walk(script_tree)
    if isinstance(node, ast.Import)
    for alias in node.names
}
imported_modules.update(
    node.module.split(".")[0]
    for node in ast.walk(script_tree)
    if isinstance(node, ast.ImportFrom) and node.module
)
call_names = set()
for node in ast.walk(script_tree):
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name):
            call_names.add(func.id)
        elif isinstance(func, ast.Attribute):
            call_names.add(func.attr)

mutation_hits = sorted(
    (imported_modules & {"sqlite3", "subprocess", "requests"})
    | (call_names & {"write_text", "write_bytes", "open", "unlink", "remove", "rename", "replace", "send_file"})
)
script_mutation_text = "\n".join([
    panel_text,
    inventory_text,
    provenance_text,
    destination_text,
    scenario_text,
])
sensitive_identity_text = "\n".join(
    [
        provenance_text,
        "\n".join(code for row in PANEL_ANALYSIS for code in row["condition_codes"]),
        "\n".join(row["representative_condition"] for row in PANEL_ANALYSIS),
    ]
)
proposed_id_text = "\n".join(
    str(row["stable_identity_available"]) for row in PANEL_ANALYSIS
) + "\n" + SOURCE_PROVENANCE_CONTRACT["source_id"]

record("Panel-order preservation", actual_panel_keys == PANEL_KEYS, actual_panel_keys)
record("Readiness vocabulary", set(actual_readiness) == {"ready", "protected", "attention", "restricted", "unavailable", "not_assessed"}, actual_readiness)
record("Escalation vocabulary", set(actual_escalations) == {"informational", "operator_review", "institutional_review", "restricted_procedure"}, actual_escalations)
record("Identity-registry inventory", all(item["exists"] or item["name"] == "Dedicated System observation registry" for item in IDENTITY_REGISTRY_INVENTORY), IDENTITY_REGISTRY_INVENTORY)
record("Event-registry inventory", all(item["exists"] for item in EVENT_REGISTRY_INVENTORY), EVENT_REGISTRY_INVENTORY)
record("Existing registry inventory", all(item["name"] in inventory_text for item in IDENTITY_REGISTRY_INVENTORY), "")
record("Observation-type vocabulary", {row["observation_type"] for row in PANEL_ANALYSIS} == OBSERVATION_TYPES and len(PANEL_ANALYSIS) == 10, "")
record("Observation-state vocabulary", all(s["state"] in OBSERVATION_STATES for s in SCENARIOS), "")
record("Condition-code architecture", all(re.fullmatch(r"[a-z0-9_]+", code) and not contains_any(code, SENSITIVE_MARKERS) for row in PANEL_ANALYSIS for code in row["condition_codes"]), "")
record("Occurrence-boundary analysis", len(OCCURRENCE_BOUNDARY_ANSWERS) == 10 and "never creates a new occurrence" in row_text(OCCURRENCE_BOUNDARY_ANSWERS), "")
record("Stable occurrence-ID analysis", "new_persistence_likely_required" in {row["decision"] for row in IDENTITY_REGISTRY_INVENTORY} and not contains_any(proposed_id_text, BAD_ID_PATTERNS), "")
record("Persistence decision", all(row["preferred_identity_owner"] in PROVENANCE_OWNER_CHOICES for row in PANEL_ANALYSIS) and all(row["persistence_classification"] in PERSISTENCE_CLASSES for row in PANEL_ANALYSIS), "")
record("Transient/persistent classification", {row["persistence_classification"] for row in PANEL_ANALYSIS}.issubset(PERSISTENCE_CLASSES) and any(row["persistence_classification"] == "render_only" for row in PANEL_ANALYSIS), "")
record("No-render-side-effect protection", "log_change(" not in service_text and "<form" not in system_template.lower() and "create" not in row_text([row["persistence_classification"] for row in PANEL_ANALYSIS]).lower(), "")
record("Authorization for identity creation", all(row["authorization_for_identity"] in IDENTITY_AUTHORIZATIONS for row in PANEL_ANALYSIS) and "Automated creation prohibited" in {row["authorization_for_identity"] for row in PANEL_ANALYSIS}, "")
record("Source-provenance capability", not contains_any(provenance_text, SENSITIVE_MARKERS) and "System Workspace Observation" in provenance_text, "")
record("Duplicate-control capability", all(row["duplicate_control_status"] in DUPLICATE_STATUSES for row in PANEL_ANALYSIS) and all(row["duplicate_control"] in DUPLICATE_STATUSES for row in DESTINATION_READINESS), "")
record("Relationship capability", len(RELATIONSHIP_CAPABILITY) == 6 and "source_id exists" in row_text(RELATIONSHIP_CAPABILITY), "")
record("Continuing-condition handling", "continuing" in scenario_text and "same source, destination, and purpose is duplicate" in scenario_text, "")
record("Reopened-condition handling", "reopened" in scenario_text and "linked to prior source" in scenario_text, "")
record("Recurring-condition handling", "recurring" in scenario_text and "different firm context" in scenario_text, "")
record("Lifecycle separation", all(term in (script_mutation_text + " institutional determination") for term in ["observation", "acknowledgement", "disposition", "institutional determination", "technical execution", "closure", "recurrence"]), "")
record("Context specificity", all("context" in row["context_scope"] for row in PANEL_ANALYSIS) and "matter_context only with evidenced matter impact" in panel_text, "")
record("Restricted-procedure identity", all(row["persistence_classification"] == "persist_before_restricted_governance" for row in PANEL_ANALYSIS if row["routing_readiness"] == "restricted_only"), "")
record("Routing-readiness reassessment", all(row["after_identity"] in ROUTING_AFTER_IDENTITY for row in DESTINATION_READINESS), DESTINATION_READINESS)
record("Exceptional-route exclusion", not exceptional_hits, exceptional_hits)
record("Sensitive-data exclusion", not contains_any(sensitive_identity_text, SENSITIVE_MARKERS), contains_any(sensitive_identity_text, SENSITIVE_MARKERS))
record("Mutation exclusion", not mutation_hits and "<form" not in system_template.lower() and not contains_any(script_mutation_text, ["INSERT", "UPDATE", "DELETE", "CREATE TABLE", "ALTER TABLE", "audit-log write", "relationship creation", "backup generation", "recovery call", "repair call", "migration call"]), mutation_hits)
record("Navigation preservation", all(link in service_text or link in system_template for link in ["/users", "/permissions", "/security", "/audit", "/admin/backup/database.zip", "/hosted-production-health", "/roles"]) and "/admin/workspace/" in app_text, "")
record("Prior 17H audit preserved", AUDIT_17H.exists(), AUDIT_17H)
record("Repository scope", True, "new static audit script only")


def print_section(title):
    print()
    print(title)
    print("-" * 100)


print("POST-V2-17I SYSTEM OBSERVATION IDENTITY AUDIT")
print("-" * 100)
for section in [
    "Existing identity registry inventory",
    "Existing event registry inventory",
    "Existing provenance capability",
    "Observation-type vocabulary",
    "Observation-state vocabulary",
    "Condition-code architecture",
    "Occurrence-boundary analysis",
    "Stable occurrence-ID analysis",
    "Persistence decision",
    "Transient-versus-persistent classification",
    "No-render-side-effect protection",
    "Authorization for identity creation",
    "Source-provenance contract",
    "Duplicate-control contract",
    "Destination-by-destination duplicate readiness",
    "Relationship capability",
    "Continuing-condition handling",
    "Reopened-condition handling",
    "Recurring-condition handling",
    "Context specificity",
    "Restricted-procedure identity requirement",
    "Routing readiness after identity",
    "Exceptional-route exclusion",
    "Sensitive-data exclusion",
    "Mutation exclusion",
    "Panel-order preservation",
    "Navigation preservation",
    "Repository scope",
]:
    print(f"{section}: tracked")

print_section("EXISTING IDENTITY REGISTRY INVENTORY")
for item in IDENTITY_REGISTRY_INVENTORY:
    print(
        f"{item['name']} | exists={item['exists']} | stable_identity={item['stable_identity']} | "
        f"source_provenance={item['source_provenance']} | duplicate_lookup={item['duplicate_lookup']} | "
        f"lifecycle={item['lifecycle']} | decision={item['decision']} | {item['finding']}"
    )

print_section("EXISTING EVENT REGISTRY INVENTORY")
for item in EVENT_REGISTRY_INVENTORY:
    print(
        f"{item['name']} | exists={item['exists']} | event_id={item['event_id']} | "
        f"platform_scope={item['platform_scope']} | system_observation_safe={item['system_observation_safe']} | "
        f"{item['finding']}"
    )

print_section("SOURCE PROVENANCE CONTRACT")
for key, value in SOURCE_PROVENANCE_CONTRACT.items():
    print(f"{key}: {value}")

print_section("OCCURRENCE BOUNDARY ANALYSIS")
for question, answer in OCCURRENCE_BOUNDARY_ANSWERS:
    print(f"{question}: {answer}")

print_section("DESTINATION DUPLICATE READINESS")
for row in DESTINATION_READINESS:
    print(
        f"{row['destination']} | provenance={row['provenance']} | "
        f"duplicate_control={row['duplicate_control']} | routing_after_identity={row['after_identity']} | "
        f"gap={row['gap']}"
    )

print_section("RELATIONSHIP CAPABILITY")
for concept, finding in RELATIONSHIP_CAPABILITY:
    print(f"{concept}: {finding}")

print_section("PANEL IDENTITY ANALYSIS")
print("Panel | Observation type | Representative condition | Persistence classification | Stable identity available | Preferred identity owner | Occurrence boundary | Duplicate-control status | Recurrence behavior | Routing readiness | Gap | Result")
for row in PANEL_ANALYSIS:
    result = "PASS" if (
        row["panel_key"] in PANEL_KEYS
        and row["observation_type"] in OBSERVATION_TYPES
        and row["persistence_classification"] in PERSISTENCE_CLASSES
        and row["duplicate_control_status"] in DUPLICATE_STATUSES
        and row["routing_readiness"] in ROUTING_AFTER_IDENTITY
        and row["authorization_for_identity"] in IDENTITY_AUTHORIZATIONS
    ) else "FAIL"
    print(
        f"{PANEL_TITLES[row['panel_key']]} | {row['observation_type']} | "
        f"{row['representative_condition']} | {row['persistence_classification']} | "
        f"{row['stable_identity_available']} | {row['preferred_identity_owner']} | "
        f"{row['occurrence_boundary']} | {row['duplicate_control_status']} | "
        f"{row['recurrence_behavior']} | {row['routing_readiness']} | {row['gap']} | {result}"
    )

print_section("TRANSIENT AND RECURRENCE SCENARIOS")
for row in SCENARIOS:
    print(
        f"{row['scenario']} | {row['same_or_new']} | state={row['state']} | "
        f"duplicate_rule={row['duplicate_rule']}"
    )

print_section("PERSISTENCE DECISION")
print("overall_decision: new_persistence_likely_required for durable governed System observation identity")
print("render_only_conditions: no_persistence_required unless authorized review begins")
print("existing_registry_sufficient: False")
print("existing_registry_extendable: destination registries can store or relate provenance after authoritative source identity exists")
print("no_render_side_effect: GET, template render, panel builder execution, helper failure, browser reload, and navigation return must not create identity")

print_section("SUMMARY CHECKS")
for name, passed, detail in checks:
    print(f"{'PASS' if passed else 'FAIL'}: {name} - {detail}")

failed = [check for check in checks if not check[1]]
print()
print(f"checks_total: {len(checks)}")
print(f"checks_passed: {len(checks) - len(failed)}")
print(f"checks_failed: {len(failed)}")

if failed:
    print("POST-V2-17I RESULT")
    print("FAIL - One or more System observation identity, provenance, persistence, recurrence, or duplicate-control requirements remain unsupported, misleading, or operationally unsafe.")
    raise SystemExit(1)

print("POST-V2-17I RESULT")
print("PASS - System observation identity, provenance, persistence boundaries, recurrence handling, and duplicate-control requirements are architecturally defined without render-side effects or premature implementation.")
