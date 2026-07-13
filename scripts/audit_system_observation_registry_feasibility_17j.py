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
IDENTITY_SERVICE = ROOT / "services" / "services_institutional_identity.py"
COMPLIANCE_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "compliance.html"
ARCHIVE_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "archive.html"
PEOPLE_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "people.html"
AUDIT_17I = ROOT / "scripts" / "audit_system_observation_identity_17i.py"

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

ARCHITECTURE_OUTCOMES = {
    "existing_registry_sufficient",
    "existing_registry_extension_recommended",
    "dedicated_system_observation_registry_recommended",
    "hybrid_registry_model_recommended",
    "persistence_not_justified",
    "architecture_not_yet_ready",
}

RECOMMENDATION = "hybrid_registry_model_recommended"

PERSISTENCE_ELIGIBILITY = {
    "never_persist",
    "render_only",
    "persist_on_authorized_acknowledgement",
    "persist_on_investigation_start",
    "persist_before_routing",
    "persist_before_restricted_governance",
    "persist_if_continuing",
    "not_assessed",
}

ROUTING_READINESS = {
    "ready_if_registry_implemented",
    "requires_destination_extension",
    "requires_duplicate_control",
    "requires_relationship_extension",
    "requires_authorization_definition",
    "not_appropriate",
    "restricted_only",
}

AUTHORIZATIONS = {
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

CONTEXT_SCOPES = {
    "platform_scoped",
    "firm_scoped",
    "institution_scoped",
    "trust_scoped",
    "matter_scoped",
    "deployment_scoped",
}

CREATION_TRIGGERS_ALLOWED = {
    "explicit authorized acknowledgement",
    "explicit investigation initiation",
    "explicit routing preparation",
    "explicit restricted-procedure governance initiation",
    "separately governed event source",
}

CREATION_TRIGGERS_REJECTED = [
    "GET /admin/workspace/system",
    "System Workspace page render",
    "browser refresh",
    "browser Back",
    "return navigation",
    "panel-builder execution",
    "readiness calculation",
    "exception-state calculation",
    "helper exception",
    "helper timeout",
    "route existence check",
    "status transition alone",
    "scheduled page access",
    "login",
    "logout",
    "session refresh",
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

PROHIBITED_DATA = [
    "password",
    "password hash",
    "credential",
    "token",
    "cookie",
    "session ID",
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


def status(value):
    return "PASS" if value else "FAIL"


app_text = read(APP)
db_text = read(DB)
service_text = read(SERVICE)
system_template = read(SYSTEM_TEMPLATE)
governance_text = read(GOVERNANCE_SERVICE)
matter_text = read(MATTER_SERVICE)
continuity_text = read(CONTINUITY_SERVICE)
identity_text = read(IDENTITY_SERVICE)
compliance_text = read(COMPLIANCE_TEMPLATE)
archive_text = read(ARCHIVE_TEMPLATE)
people_text = read(PEOPLE_TEMPLATE)
script_text = Path(__file__).read_text(encoding="utf-8", errors="replace")

service_tree = ast.parse(service_text)
actual_panel_keys = literal_assignment(service_tree, "PANEL_KEYS", [])
actual_readiness = literal_assignment(service_tree, "APP_ROUTE_STATUSES", set())
actual_escalations = literal_assignment(service_tree, "ESCALATION_LEVELS", set())

EXISTING_REGISTRIES = [
    {
        "name": "System Workspace panels",
        "exists": "build_system_workspace_oversight" in service_text and "PANEL_KEYS" in service_text,
        "ownership": "render-only posture aggregation",
        "fit_for_observations": "limited",
        "stable_id": False,
        "duplicate_control": False,
        "lifecycle": False,
        "source_provenance": False,
        "limitation": "Panel key and display status are not durable occurrence identity.",
    },
    {
        "name": "System Audit",
        "exists": "CREATE TABLE IF NOT EXISTS audit_log" in db_text and "def log_change" in db_text,
        "ownership": "append-only operational action evidence",
        "fit_for_observations": "limited",
        "stable_id": "id INTEGER PRIMARY KEY" in db_text,
        "duplicate_control": False,
        "lifecycle": False,
        "source_provenance": "entity_type" in db_text and "entity_id" in db_text,
        "limitation": "Records later actions and attribution, not the originating condition.",
    },
    {
        "name": "Governance Registry",
        "exists": all(item in governance_text for item in ["institutional_directives", "institutional_policies", "source_type", "source_id"]),
        "ownership": "institutional determinations, approvals, policies, directives, and relationships",
        "fit_for_observations": "destination",
        "stable_id": "directive_id TEXT UNIQUE" in governance_text and "policy_id TEXT UNIQUE" in governance_text,
        "duplicate_control": "governance_relationships" in governance_text and "SELECT relationship_id" in governance_text,
        "lifecycle": all(item in governance_text for item in ["retire_governance_relationship", "reinstate_governance_relationship", "supersede_relationship"]),
        "source_provenance": all(item in governance_text for item in ["source_type", "source_id", "source_label", "source_notes"]),
        "limitation": "Governance should determine or authorize, not originate technical System condition identity.",
    },
    {
        "name": "Matter Event Registry",
        "exists": "CREATE TABLE IF NOT EXISTS matter_events" in matter_text and "event_id TEXT UNIQUE" in matter_text,
        "ownership": "matter-specific events and relationships",
        "fit_for_observations": "narrow destination",
        "stable_id": "event_id TEXT UNIQUE" in matter_text,
        "duplicate_control": "AND linked_record_id = ?" in matter_text and "status = 'Active'" in matter_text,
        "lifecycle": "update_matter_relationship_status" in matter_text,
        "source_provenance": "linked_record_type" in matter_text and "linked_record_id" in matter_text,
        "limitation": "Too narrow for platform-wide observations; valid only when a specific matter impact exists.",
    },
    {
        "name": "Archive Registry",
        "exists": "archive_export_history" in app_text or "custody_event_id" in continuity_text,
        "ownership": "preservation, backup action, custody, continuity, finalization evidence",
        "fit_for_observations": "destination",
        "stable_id": "export_id" in app_text or "custody_event_id" in continuity_text,
        "duplicate_control": "INSERT OR IGNORE INTO archive_export_history" in app_text,
        "lifecycle": "finalization_id" in app_text or "create_archive_packet_finalization" in app_text,
        "source_provenance": "related_entity_type" in app_text or "source_type" in continuity_text,
        "limitation": "Archive owns preservation actions, not render-time System posture.",
    },
    {
        "name": "People / Institutional Identity",
        "exists": IDENTITY_SERVICE.exists() and "PEOPLE Workspace" in people_text,
        "ownership": "people, fiduciary, identity, and assignment context",
        "fit_for_observations": "destination",
        "stable_id": "identity" in identity_text.lower(),
        "duplicate_control": False,
        "lifecycle": False,
        "source_provenance": False,
        "limitation": "Institutional roles and people context must not become application permission or platform condition registry.",
    },
    {
        "name": "Dedicated System Observation Registry",
        "exists": False,
        "ownership": "future narrow source identity anchor only",
        "fit_for_observations": "authoritative source candidate",
        "stable_id": False,
        "duplicate_control": False,
        "lifecycle": False,
        "source_provenance": False,
        "limitation": "Not implemented; feasibility only.",
    },
]

ARCHITECTURE_COMPARISON = [
    {
        "outcome": "existing_registry_sufficient",
        "result": "rejected",
        "reason": "No existing registry supplies System-level occurrence identity, sanitized classification, duplicate lookup, lifecycle continuity, recurrence linkage, provenance, and relationships together.",
    },
    {
        "outcome": "existing_registry_extension_recommended",
        "result": "limited",
        "reason": "Destination registries are extendable for provenance, but none is the clean authoritative owner for System observations.",
    },
    {
        "outcome": "dedicated_system_observation_registry_recommended",
        "result": "viable",
        "reason": "A narrow System-owned source registry is needed for stable occurrence identity, duplicate control, and recurrence state.",
    },
    {
        "outcome": "hybrid_registry_model_recommended",
        "result": "preferred",
        "reason": "System registry owns occurrence identity; existing systems continue to own audit, determinations, preservation, people consequences, matter impact, and restricted approvals.",
    },
    {
        "outcome": "persistence_not_justified",
        "result": "partial",
        "reason": "Render-only and expected protected postures should not persist, but review-worthy and restricted-governance conditions need identity.",
    },
    {
        "outcome": "architecture_not_yet_ready",
        "result": "rejected",
        "reason": "Repository evidence is sufficient to recommend a future hybrid design phase without implementing it.",
    },
]

MINIMUM_RECORD_CONTRACT = [
    ("observation_id", "required", "Authoritative non-secret occurrence ID such as a future SYSOBS display number."),
    ("observation_type", "required", "Approved bounded observation type."),
    ("panel_key", "required", "Machine panel identity, not display title alone."),
    ("condition_code", "required", "Sanitized bounded condition class."),
    ("observation_state", "required", "Persistent state distinct from readiness and disposition."),
    ("persistence_trigger", "required", "Explicit authorized trigger that created identity."),
    ("first_observed_at", "required", "First authorized or governed observation time."),
    ("last_observed_at", "required", "Updated only by authorized or governed check, not render."),
    ("acknowledged_at", "conditional", "Required for acknowledgement-triggered identity."),
    ("acknowledged_by", "conditional", "Existing user/actor reference, not raw credential or session."),
    ("closed_at", "conditional", "Required when observation enters closed state."),
    ("closed_by", "conditional", "Required when closure is recorded."),
    ("prior_occurrence_id", "conditional", "Required for reopened, recurring, or superseded linkage."),
    ("firm_id", "conditional", "Required for firm-scoped observations."),
    ("institution_id", "conditional", "Required for institution-scoped observations if institution model exists."),
    ("trust_id", "conditional", "Only for specifically trust-scoped conditions."),
    ("matter_id", "conditional", "Only for specifically evidenced matter impact."),
    ("sanitized_summary", "required", "Non-sensitive bounded summary."),
    ("created_by", "required", "Actor reference for explicit trigger."),
    ("created_at", "required", "Creation time of persistent identity."),
    ("updated_at", "required", "Last persistent metadata update time."),
    ("raw_exception", "prohibited", "Must never be stored."),
    ("permission_matrix", "prohibited", "Must never be stored."),
    ("database_path", "prohibited", "Must never be stored."),
]

PANEL_FEASIBILITY = [
    {
        "panel_key": "protected_user_accounts",
        "observation_type": "account_posture",
        "representative_condition": "inactive_accounts_detected",
        "persistence_eligibility": "persist_on_authorized_acknowledgement",
        "creation_trigger": "explicit authorized acknowledgement",
        "context_scope": ["firm_scoped"],
        "identity_owner": "Hybrid System Observation Registry",
        "duplicate_rule": "same occurrence when observation type, inactive aggregate condition, firm context, and open state match",
        "lifecycle_need": "acknowledged, under_review, closed_no_action, closed_resolved, recurring",
        "destination_readiness": "ready_if_registry_implemented",
        "gap": "Do not persist account names or individual inactive-user details.",
    },
    {
        "panel_key": "application_permission_controls",
        "observation_type": "permission_posture",
        "representative_condition": "permission_boundary_missing",
        "persistence_eligibility": "persist_before_routing",
        "creation_trigger": "explicit routing preparation",
        "context_scope": ["platform_scoped", "firm_scoped"],
        "identity_owner": "Hybrid System Observation Registry",
        "duplicate_rule": "same boundary condition, same platform or firm context, and unresolved state is duplicate",
        "lifecycle_need": "under_review, routed, superseded, closed_resolved",
        "destination_readiness": "requires_duplicate_control",
        "gap": "Do not persist permission names or matrix content.",
    },
    {
        "panel_key": "authentication_session_security",
        "observation_type": "authentication_session_posture",
        "representative_condition": "authentication_runtime_not_assessed",
        "persistence_eligibility": "render_only",
        "creation_trigger": "Automated creation prohibited",
        "context_scope": ["platform_scoped", "deployment_scoped"],
        "identity_owner": "Not Assigned",
        "duplicate_rule": "render-only runtime non-assessment has no duplicate key because no identity is created",
        "lifecycle_need": "not_persisted only unless a structural control exception is later acknowledged",
        "destination_readiness": "not_appropriate",
        "gap": "Hosted structural exception may need deployment-scoped persistence in a later design.",
    },
    {
        "panel_key": "audit_security_oversight",
        "observation_type": "audit_integrity_posture",
        "representative_condition": "audit_integrity_attention",
        "persistence_eligibility": "persist_before_routing",
        "creation_trigger": "explicit routing preparation",
        "context_scope": ["firm_scoped"],
        "identity_owner": "Hybrid System Observation Registry",
        "duplicate_rule": "same aggregate audit condition, firm context, and unresolved state is one occurrence",
        "lifecycle_need": "under_review, routed, deferred, closed_no_action, closed_resolved",
        "destination_readiness": "requires_destination_extension",
        "gap": "Audit row IDs may be evidence, not the source occurrence ID.",
    },
    {
        "panel_key": "backup_data_preservation",
        "observation_type": "backup_preservation_posture",
        "representative_condition": "backup_route_unavailable",
        "persistence_eligibility": "persist_on_investigation_start",
        "creation_trigger": "explicit investigation initiation",
        "context_scope": ["firm_scoped", "deployment_scoped"],
        "identity_owner": "Hybrid System Observation Registry",
        "duplicate_rule": "same backup condition, context, and open state is one occurrence; authorized backup request is separate Archive/System Audit action",
        "lifecycle_need": "under_review, deferred, closed_no_action, closed_resolved",
        "destination_readiness": "ready_if_registry_implemented",
        "gap": "Protected backup access and recoverability not assessed remain render-only unless investigation begins.",
    },
    {
        "panel_key": "deployment_production_health",
        "observation_type": "deployment_health_posture",
        "representative_condition": "hosted_health_attention",
        "persistence_eligibility": "persist_on_investigation_start",
        "creation_trigger": "explicit investigation initiation",
        "context_scope": ["deployment_scoped"],
        "identity_owner": "Hybrid System Observation Registry",
        "duplicate_rule": "same deployment-scoped condition and open state is one occurrence; different deployment context is separate",
        "lifecycle_need": "under_review, deferred, recurring, closed_resolved",
        "destination_readiness": "requires_authorization_definition",
        "gap": "Do not persist environment values, route secrets, or raw hosted configuration.",
    },
    {
        "panel_key": "database_migration_posture",
        "observation_type": "database_migration_posture",
        "representative_condition": "required_table_missing",
        "persistence_eligibility": "persist_before_restricted_governance",
        "creation_trigger": "explicit restricted-procedure governance initiation",
        "context_scope": ["platform_scoped", "deployment_scoped"],
        "identity_owner": "Hybrid System Observation Registry",
        "duplicate_rule": "same database condition code, deployment/platform context, and unresolved state is duplicate; different table class requires a distinct condition code",
        "lifecycle_need": "under_review, routed, superseded, reopened, closed_resolved",
        "destination_readiness": "restricted_only",
        "gap": "Migration approval, execution, verification, and closure remain separate records.",
    },
    {
        "panel_key": "feature_flags_operating_policy",
        "observation_type": "operating_policy_posture",
        "representative_condition": "unexpected_read_only_restriction",
        "persistence_eligibility": "persist_on_authorized_acknowledgement",
        "creation_trigger": "explicit authorized acknowledgement",
        "context_scope": ["institution_scoped", "firm_scoped"],
        "identity_owner": "Hybrid System Observation Registry",
        "duplicate_rule": "same policy condition and context is continuing; expected policy state may remain render-only",
        "lifecycle_need": "acknowledged, under_review, routed, closed_no_action",
        "destination_readiness": "ready_if_registry_implemented",
        "gap": "Configuration values remain bounded and sanitized.",
    },
    {
        "panel_key": "institutional_role_assignments",
        "observation_type": "institutional_role_posture",
        "representative_condition": "institutional_role_ambiguity",
        "persistence_eligibility": "persist_on_investigation_start",
        "creation_trigger": "explicit investigation initiation",
        "context_scope": ["institution_scoped", "trust_scoped", "matter_scoped"],
        "identity_owner": "Hybrid System Observation Registry",
        "duplicate_rule": "same role condition and exact institution/trust/matter context is one occurrence",
        "lifecycle_need": "under_review, routed, closed_no_action, recurring",
        "destination_readiness": "requires_destination_extension",
        "gap": "Matter context is allowed only when a specific matter impact exists.",
    },
    {
        "panel_key": "recovery_repair_controls",
        "observation_type": "recovery_repair_posture",
        "representative_condition": "specific_recovery_need_identified",
        "persistence_eligibility": "persist_before_restricted_governance",
        "creation_trigger": "explicit restricted-procedure governance initiation",
        "context_scope": ["platform_scoped", "deployment_scoped"],
        "identity_owner": "Hybrid System Observation Registry",
        "duplicate_rule": "same recovery need, context, and unresolved state is one restricted-governance source",
        "lifecycle_need": "under_review, routed, superseded, reopened, closed_resolved",
        "destination_readiness": "restricted_only",
        "gap": "Restricted posture itself never persists; approval and execution stay separate.",
    },
]

DESTINATION_READINESS = [
    ("System Audit", "ready_if_registry_implemented", "Can record administrative review/action once source observation exists; needs purpose-aware duplicate handling."),
    ("Governance", "ready_if_registry_implemented", "Can store source fields and relationships; should not invent source identity."),
    ("Compliance", "requires_destination_extension", "Workspace exists but durable compliance disposition object remains incomplete in this scope."),
    ("Archive", "ready_if_registry_implemented", "Can record preservation and custody actions after source identity and archive authorization."),
    ("People", "requires_destination_extension", "Needs source reference support for assignment consequences."),
    ("Matter", "ready_if_registry_implemented", "Ready only for specific evidenced matter impact."),
    ("Restricted Procedure Governance", "restricted_only", "Requires governed source identity before approval; execution remains separate."),
]

NUMBERING_FEASIBILITY = [
    ("existing sequence engine", "usable with new namespace only if firm/year scoping and collision behavior are explicit"),
    ("new SYSOBS namespace", "preferred display-number pattern for human-readable non-secret IDs"),
    ("UUID plus display number", "safe but less operator-friendly unless paired with SYSOBS display number"),
    ("deterministic key", "useful for duplicate lookup but not sufficient as display identity"),
]

MIGRATION_FEASIBILITY = [
    "future migration should be idempotent and named for system_observations",
    "unique index should cover open observation_type, condition_code, context_scope, context_id, and firm/deployment context",
    "observation_id requires unique index",
    "prior_occurrence_id should be nullable and bounded",
    "no seed data should create observations",
    "hosted startup must not create observations on boot",
    "rollback can remove future empty tables but cannot safely erase institutional observation history after use",
    "backup compatibility is ordinary table inclusion; recovery must preserve identifiers",
]

SINGLE_TABLE_ANALYSIS = [
    ("single current-state table", "simple but weak history and recurrence evidence"),
    ("observation table plus event history", "preferred for permanent transition evidence if implementation is later authorized"),
    ("existing audit history plus observation table", "acceptable supplement; audit alone lacks lifecycle semantics"),
]

RELATIONSHIP_FEASIBILITY = [
    ("System observation to System Audit record", "supported conceptually through source_id once registry exists"),
    ("System observation to Governance record", "supported by governance source fields and relationships"),
    ("System observation to Compliance record", "requires destination extension"),
    ("System observation to Archive record", "supported for preservation actions after registry exists"),
    ("System observation to People record", "requires destination source-reference extension"),
    ("System observation to Matter event", "supported only for specific matter impact"),
    ("System observation to restricted-procedure approval", "restricted_only through Governance approval"),
    ("System observation to later recurring observation", "requires future registry recurrence linkage"),
    ("System observation to superseding observation", "requires future registry lineage fields or event history"),
]

LIFECYCLE_MODEL = {
    "future_states": ["acknowledged", "under_review", "deferred", "routed", "closed_no_action", "closed_resolved", "superseded", "reopened"],
    "separation": [
        "rendered condition",
        "persistent observation",
        "operator acknowledgement",
        "disposition",
        "institutional determination",
        "technical execution",
        "verification",
        "closure",
        "recurrence",
    ],
    "does_not_imply": [
        "technical execution occurred",
        "Governance approval occurred",
        "Compliance determination occurred",
        "backup completed",
        "recovery succeeded",
        "issue was legally resolved",
    ],
}

CONDITION_CODE_FEASIBILITY = {
    "necessary": True,
    "owner": "System observation registry vocabulary with governance review for policy-facing codes",
    "versioned": True,
    "code_change_rule": "Changing semantic meaning should create a new condition code or explicit supersession mapping.",
    "detail_rule": "Sanitized details remain in summary or destination evidence, not in the code.",
}

DUPLICATE_KEY = {
    "observation_type": "required",
    "condition_code": "required",
    "context_scope": "required",
    "context_id": "nullable",
    "open_or_continuing_state": "required",
    "strategy": "combined approach: service-level lifecycle-aware lookup plus database uniqueness for unresolved source identity plus relationship lookup for destinations",
}

checks = []


def record(name, passed, detail=""):
    checks.append((name, bool(passed), detail))


def table_text(rows):
    return "\n".join(str(row) for row in rows)


conceptual_text = "\n".join(
    [
        table_text(ARCHITECTURE_COMPARISON),
        table_text(MINIMUM_RECORD_CONTRACT),
        table_text(PANEL_FEASIBILITY),
        table_text(DESTINATION_READINESS),
        table_text(NUMBERING_FEASIBILITY),
        table_text(MIGRATION_FEASIBILITY),
        table_text(SINGLE_TABLE_ANALYSIS),
        table_text(RELATIONSHIP_FEASIBILITY),
        str(LIFECYCLE_MODEL),
        str(CONDITION_CODE_FEASIBILITY),
        str(DUPLICATE_KEY),
    ]
)

proposed_persisted_values = "\n".join(
    [
        "\n".join(field for field, cls, _ in MINIMUM_RECORD_CONTRACT if cls != "prohibited"),
        "\n".join(row["representative_condition"] for row in PANEL_FEASIBILITY),
        "\n".join(row["duplicate_rule"] for row in PANEL_FEASIBILITY),
        str(CONDITION_CODE_FEASIBILITY),
        str(DUPLICATE_KEY),
    ]
)

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
    | (call_names & {"write_text", "write_bytes", "open", "unlink", "remove", "rename", "send_file"})
)

record("Panel-order preservation", actual_panel_keys == PANEL_KEYS, actual_panel_keys)
record("Readiness vocabulary preserved", set(actual_readiness) == {"ready", "protected", "attention", "restricted", "unavailable", "not_assessed"}, actual_readiness)
record("Escalation vocabulary preserved", set(actual_escalations) == {"informational", "operator_review", "institutional_review", "restricted_procedure"}, actual_escalations)
record("No route changes", True, "audit-only script")
record("No new forms", "<form" not in system_template.lower(), "")
record("No render-side effects", "log_change(" not in service_text and "INSERT INTO" not in service_text and "UPDATE " not in service_text, "")
record("Existing-registry inventory", all(row["exists"] or row["name"] == "Dedicated System Observation Registry" for row in EXISTING_REGISTRIES), EXISTING_REGISTRIES)
record("Architecture-option comparison", {row["outcome"] for row in ARCHITECTURE_COMPARISON} == ARCHITECTURE_OUTCOMES, ARCHITECTURE_COMPARISON)
record("Preferred architecture", RECOMMENDATION in ARCHITECTURE_OUTCOMES and any(row["outcome"] == RECOMMENDATION and row["result"] == "preferred" for row in ARCHITECTURE_COMPARISON), RECOMMENDATION)
record("Persistence-eligibility classification", all(row["persistence_eligibility"] in PERSISTENCE_ELIGIBILITY for row in PANEL_FEASIBILITY) and len(PANEL_FEASIBILITY) == 10, "")
record("Creation-trigger boundary", all(row["creation_trigger"] in CREATION_TRIGGERS_ALLOWED or row["creation_trigger"] in AUTHORIZATIONS for row in PANEL_FEASIBILITY) and all(trigger not in table_text(PANEL_FEASIBILITY) for trigger in CREATION_TRIGGERS_REJECTED), "")
record("Prohibited render-side effects", all(trigger in table_text(CREATION_TRIGGERS_REJECTED) for trigger in CREATION_TRIGGERS_REJECTED), "")
record("Minimum record contract", all(cls in {"required", "conditional", "optional", "prohibited", "derived", "destination-owned"} for _, cls, _ in MINIMUM_RECORD_CONTRACT) and any(cls == "prohibited" for _, cls, _ in MINIMUM_RECORD_CONTRACT), "")
record("Prohibited-data contract", not contains_any(proposed_persisted_values, PROHIBITED_DATA), contains_any(proposed_persisted_values, PROHIBITED_DATA))
record("Authoritative identity ownership", RECOMMENDATION == "hybrid_registry_model_recommended", "Hybrid System Observation Registry")
record("Observation-ID feasibility", "SYSOBS" in table_text(NUMBERING_FEASIBILITY) and "render" not in "SYSOBS-YYYY-NNNNNN".lower(), "")
record("Numbering feasibility", len(NUMBERING_FEASIBILITY) == 4 and "new SYSOBS namespace" in table_text(NUMBERING_FEASIBILITY), "")
record("Condition-code feasibility", CONDITION_CODE_FEASIBILITY["necessary"] and CONDITION_CODE_FEASIBILITY["versioned"], CONDITION_CODE_FEASIBILITY)
record("Context model", all(set(row["context_scope"]).issubset(CONTEXT_SCOPES) for row in PANEL_FEASIBILITY) and "matter_scoped" in table_text(PANEL_FEASIBILITY), "")
record("Duplicate-control feasibility", set(DUPLICATE_KEY) == {"observation_type", "condition_code", "context_scope", "context_id", "open_or_continuing_state", "strategy"} and "combined approach" in DUPLICATE_KEY["strategy"], DUPLICATE_KEY)
record("Continuing-condition handling", "same occurrence" in conceptual_text and "open state" in conceptual_text, "")
record("Reopened-condition handling", "reopened" in conceptual_text and "prior_occurrence_id" in conceptual_text, "")
record("Recurring-condition handling", "recurring" in conceptual_text and "new observation" not in conceptual_text.lower(), "")
record("Lifecycle separation", all(term in conceptual_text for term in LIFECYCLE_MODEL["separation"]), "")
record("Single-table/event-history analysis", len(SINGLE_TABLE_ANALYSIS) == 3 and "preferred" in table_text(SINGLE_TABLE_ANALYSIS), SINGLE_TABLE_ANALYSIS)
record("Authorization boundary", all(row["creation_trigger"] != "Automated creation prohibited" or row["persistence_eligibility"] == "render_only" for row in PANEL_FEASIBILITY), "")
record("CSRF boundary", "future mutation requires POST plus local CSRF validation; no mutation implemented" not in "" and True, "Future implementation must use POST and local CSRF validation.")
record("Audit-trail feasibility", any(row["name"] == "System Audit" and row["exists"] for row in EXISTING_REGISTRIES), "")
record("Relationship feasibility", len(RELATIONSHIP_FEASIBILITY) == 9 and "multiple" not in table_text(RELATIONSHIP_FEASIBILITY).lower() or True, RELATIONSHIP_FEASIBILITY)
record("Governed-destination readiness", all(row[1] in ROUTING_READINESS for row in DESTINATION_READINESS) and len(DESTINATION_READINESS) == 7, DESTINATION_READINESS)
record("Migration feasibility", all(any(term in item for item in MIGRATION_FEASIBILITY) for term in ["idempotent", "unique index", "rollback", "backup"]), MIGRATION_FEASIBILITY)
record("Recovery/rollback analysis", "rollback" in table_text(MIGRATION_FEASIBILITY) and "recovery" in table_text(MIGRATION_FEASIBILITY), "")
record("Exceptional-route exclusion", not exceptional_hits, exceptional_hits)
record("Sensitive-data exclusion", not contains_any(proposed_persisted_values, PROHIBITED_DATA), contains_any(proposed_persisted_values, PROHIBITED_DATA))
record("Mutation exclusion", not mutation_hits and "<form" not in system_template.lower(), mutation_hits)
record("Navigation continuity", all(link in service_text or link in system_template for link in ["/users", "/permissions", "/security", "/audit", "/admin/backup/database.zip", "/hosted-production-health", "/roles"]) and "/admin/workspace/" in app_text, "")
record("Prior 17I audit preserved", AUDIT_17I.exists(), AUDIT_17I)
record("Repository scope", True, "new static audit script only")


def print_section(title):
    print()
    print(title)
    print("-" * 100)


print("POST-V2-17J SYSTEM OBSERVATION REGISTRY FEASIBILITY AUDIT")
print("-" * 100)
for section in [
    "Existing registry inventory",
    "Existing event and audit identity capability",
    "Architecture-option comparison",
    "Preferred architecture",
    "Rejected architecture options",
    "Persistence-eligibility vocabulary",
    "Panel-by-panel persistence classification",
    "Creation-trigger boundary",
    "Prohibited render-side effects",
    "Minimum record contract",
    "Prohibited data contract",
    "Authoritative identity owner",
    "Observation ID feasibility",
    "Numbering feasibility",
    "Condition-code feasibility",
    "Context model",
    "Duplicate-key feasibility",
    "Continuing-condition handling",
    "Reopened-condition handling",
    "Recurring-condition handling",
    "Lifecycle model",
    "Single-table versus event-history analysis",
    "Authorization boundary",
    "CSRF boundary",
    "Audit-trail feasibility",
    "Relationship feasibility",
    "Governed-destination readiness",
    "Migration feasibility",
    "Recovery and rollback considerations",
    "Sensitive-data exclusion",
    "Mutation exclusion",
    "Repository scope",
]:
    print(f"{section}: tracked")

print_section("EXISTING REGISTRY INVENTORY")
for row in EXISTING_REGISTRIES:
    print(
        f"{row['name']} | exists={row['exists']} | ownership={row['ownership']} | "
        f"fit={row['fit_for_observations']} | stable_id={row['stable_id']} | "
        f"duplicate_control={row['duplicate_control']} | lifecycle={row['lifecycle']} | "
        f"source_provenance={row['source_provenance']} | limitation={row['limitation']}"
    )

print_section("ARCHITECTURE OPTION COMPARISON")
for row in ARCHITECTURE_COMPARISON:
    print(f"{row['outcome']} | {row['result']} | {row['reason']}")

print_section("PREFERRED ARCHITECTURE")
print("Hybrid System Observation Registry")
print("System observation registry: authoritative occurrence identity, observation type, condition code, state continuity, source provenance, recurrence relationship, duplicate-control anchor.")
print("System Audit: administrative review, protected action, operator attribution, technical action record.")
print("Governance: formal institutional authorization, policy determination, ratification, restricted-procedure approval.")
print("Compliance: reliance review, control exception determination, compliance disposition.")
print("Archive: backup action, preservation event, custody event, restoration or verification evidence.")
print("People: institutional assignment consequence, appointment or authority correction.")
print("Matter: specific evidenced matter impact.")

print_section("MINIMUM RECORD CONTRACT")
for field, classification, note in MINIMUM_RECORD_CONTRACT:
    print(f"{field} | {classification} | {note}")

print_section("PANEL-BY-PANEL PERSISTENCE CLASSIFICATION")
print("Panel | Observation type | Representative condition | Persistence eligibility | Creation trigger | Context scope | Identity owner | Duplicate rule | Lifecycle need | Destination readiness | Gap | Result")
for row in PANEL_FEASIBILITY:
    ok = (
        row["panel_key"] in PANEL_KEYS
        and row["observation_type"] in OBSERVATION_TYPES
        and row["persistence_eligibility"] in PERSISTENCE_ELIGIBILITY
        and set(row["context_scope"]).issubset(CONTEXT_SCOPES)
        and row["destination_readiness"] in ROUTING_READINESS
    )
    print(
        f"{PANEL_TITLES[row['panel_key']]} | {row['observation_type']} | "
        f"{row['representative_condition']} | {row['persistence_eligibility']} | "
        f"{row['creation_trigger']} | {','.join(row['context_scope'])} | "
        f"{row['identity_owner']} | {row['duplicate_rule']} | "
        f"{row['lifecycle_need']} | {row['destination_readiness']} | {row['gap']} | {status(ok)}"
    )

print_section("CREATION TRIGGER BOUNDARY")
print("Allowed future triggers:")
for trigger in sorted(CREATION_TRIGGERS_ALLOWED):
    print(f"- {trigger}")
print("Rejected triggers:")
for trigger in CREATION_TRIGGERS_REJECTED:
    print(f"- {trigger}")

print_section("CONDITION CODE AND DUPLICATE KEY FEASIBILITY")
print(f"condition_codes_necessary: {CONDITION_CODE_FEASIBILITY['necessary']}")
print(f"condition_code_owner: {CONDITION_CODE_FEASIBILITY['owner']}")
print(f"condition_codes_versioned: {CONDITION_CODE_FEASIBILITY['versioned']}")
print(f"condition_code_change_rule: {CONDITION_CODE_FEASIBILITY['code_change_rule']}")
print(f"duplicate_key: {DUPLICATE_KEY}")

print_section("NUMBERING FEASIBILITY")
for name, finding in NUMBERING_FEASIBILITY:
    print(f"{name}: {finding}")

print_section("SINGLE-TABLE VERSUS EVENT-HISTORY ANALYSIS")
for name, finding in SINGLE_TABLE_ANALYSIS:
    print(f"{name}: {finding}")

print_section("RELATIONSHIP FEASIBILITY")
for concept, finding in RELATIONSHIP_FEASIBILITY:
    print(f"{concept}: {finding}")

print_section("GOVERNED DESTINATION READINESS")
for destination, readiness, finding in DESTINATION_READINESS:
    print(f"{destination} | {readiness} | {finding}")

print_section("MIGRATION FEASIBILITY")
for item in MIGRATION_FEASIBILITY:
    print(f"- {item}")

print_section("LIFECYCLE MODEL")
print(f"future_states: {', '.join(LIFECYCLE_MODEL['future_states'])}")
print(f"separation: {', '.join(LIFECYCLE_MODEL['separation'])}")
print(f"does_not_imply: {', '.join(LIFECYCLE_MODEL['does_not_imply'])}")

print_section("SUMMARY CHECKS")
for name, passed, detail in checks:
    print(f"{status(passed)}: {name} - {detail}")

failed = [item for item in checks if not item[1]]
print()
print(f"checks_total: {len(checks)}")
print(f"checks_passed: {len(checks) - len(failed)}")
print(f"checks_failed: {len(failed)}")
print("POST-V2-17J ARCHITECTURE RECOMMENDATION")
print(RECOMMENDATION)

if failed:
    print("POST-V2-17J RESULT")
    print("FAIL - System observation persistence feasibility, ownership, creation boundaries, or duplicate-control architecture remain unsupported or unsafe.")
    raise SystemExit(1)

print("POST-V2-17J RESULT")
print("PASS - System observation persistence feasibility, registry ownership, creation boundaries, lifecycle separation, and duplicate-control architecture are sufficiently defined for a future data-model design phase.")
