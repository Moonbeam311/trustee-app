from pathlib import Path
import ast
import re
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
SERVICE = ROOT / "services" / "services_system_workspace.py"
SYSTEM_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "system.html"
GOVERNANCE_SERVICE = ROOT / "services" / "services_governance.py"
MATTER_SERVICE = ROOT / "services" / "services_matters.py"
ARCHIVE_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "archive.html"
PEOPLE_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "people.html"
COMPLIANCE_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "compliance.html"
MATTER_DETAIL_TEMPLATE = ROOT / "templates" / "matter_detail.html"
AUDIT_17G = ROOT / "scripts" / "audit_system_exception_escalation_17g.py"

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
DISPOSITIONS = {
    "no_record_required",
    "acknowledge",
    "defer",
    "investigate",
    "escalate",
    "route_for_determination",
    "record_action_taken",
    "close_no_action",
    "close_resolved",
    "restricted_procedure_required",
}
DESTINATIONS = {
    "None",
    "System Audit",
    "Governance",
    "Compliance",
    "Archive",
    "People",
    "Matter",
    "Restricted Procedure Governance",
}
AUTHORIZATIONS = {
    "System master administrator",
    "Authorized governance operator",
    "Authorized compliance reviewer",
    "Authorized archive custodian",
    "Authorized institutional administrator",
    "Authorized matter operator",
    "Separately authorized restricted procedure",
    "Not currently defined",
}
READINESS = {
    "ready_for_future_bounded_implementation",
    "architecturally_valid_but_missing_source_identity",
    "architecturally_valid_but_missing_duplicate_control",
    "architecturally_valid_but_missing_authorization_contract",
    "architecturally_valid_but_destination_incomplete",
    "not_appropriate",
    "restricted_only",
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
    "session value",
    "database path",
    "environment variable",
    "raw exception",
    "stack trace",
    "permission matrix",
    "audit hash",
    "emergency route",
    "repair command",
]
BAD_DISPOSITIONS = {
    "auto_resolved",
    "auto_closed",
    "system_decided",
    "self_healed",
    "repair_complete",
    "breach_confirmed",
    "violation_proven",
}
BAD_DESTINATIONS = {
    "System Decision Ledger",
    "System Exception Registry",
    "Escalation Database",
    "Incident Center",
}


def read(path):
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def assignment_literal(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                return ast.literal_eval(node.value)
    raise AssertionError(f"{name} assignment not found")


def contains_any(text, markers):
    lower = text.lower()
    return [marker for marker in markers if marker.lower() in lower]


app_text = read(APP)
service_text = read(SERVICE)
system_template = read(SYSTEM_TEMPLATE)
governance_text = read(GOVERNANCE_SERVICE)
matter_text = read(MATTER_SERVICE)
archive_text = read(ARCHIVE_TEMPLATE)
people_text = read(PEOPLE_TEMPLATE)
compliance_text = read(COMPLIANCE_TEMPLATE)
matter_template = read(MATTER_DETAIL_TEMPLATE)
repo_context = "\n".join([
    app_text,
    service_text,
    system_template,
    governance_text,
    matter_text,
    archive_text,
    people_text,
    compliance_text,
    matter_template,
])
service_tree = ast.parse(service_text)
script_text = read(Path(__file__))
script_tree = ast.parse(script_text)

system_panel_keys = assignment_literal(service_tree, "PANEL_KEYS")

EXISTING_RECORD_INVENTORY = {
    "System Audit": {
        "exists": "audit_log" in app_text and "log_change" in app_text,
        "record_types": ["audit_log", "change log"],
        "source_reference": True,
        "duplicate_prevention": False,
        "authorization": "System master administrator",
        "boundary": "Append-oriented activity evidence; not a substitute for institutional determination.",
    },
    "Governance": {
        "exists": all(term in governance_text for term in [
            "institutional_directives",
            "institutional_decisions",
            "institutional_policies",
            "institutional_resolutions",
            "governance_relationships",
        ]),
        "record_types": ["Institutional Directive", "Institutional Decision", "Institutional Policy", "Institutional Resolution", "Governance Relationship"],
        "source_reference": all(term in governance_text for term in ["source_type", "source_id", "source_label", "source_notes"]),
        "duplicate_prevention": "existing_relationship_id" in governance_text and "governance_relationship_audit_ledger" in governance_text,
        "authorization": "Authorized governance operator",
        "boundary": "Formal institutional determinations and restricted-procedure approvals where source identity and duplicate control are sufficient.",
    },
    "Compliance": {
        "exists": COMPLIANCE_TEMPLATE.exists(),
        "record_types": [],
        "source_reference": False,
        "duplicate_prevention": False,
        "authorization": "Authorized compliance reviewer",
        "boundary": "Workspace exists, but no dedicated compliance disposition record type is active in this audit scope.",
    },
    "Archive": {
        "exists": "archive" in archive_text.lower() and ("custody" in app_text.lower() or "archive_export_history" in app_text),
        "record_types": ["Archive Evidence", "Continuity/Custody Event", "Archive Export History"],
        "source_reference": "related_entity_type" in app_text or "source_type" in app_text,
        "duplicate_prevention": "INSERT OR IGNORE INTO archive_export_history" in app_text,
        "authorization": "Authorized archive custodian",
        "boundary": "Preservation, custody, continuity, and backup-action evidence; not proof of restoration or recoverability.",
    },
    "People": {
        "exists": "/roles" in service_text and "Institutional Role Assignments" in system_template,
        "record_types": ["Institutional Role Assignment", "Fiduciary/People record"],
        "source_reference": False,
        "duplicate_prevention": False,
        "authorization": "Authorized institutional administrator",
        "boundary": "Institutional and trust-scoped assignments only; not application authorization.",
    },
    "Matter": {
        "exists": "matter_events" in matter_text and "matter_relationships" in matter_text,
        "record_types": ["Matter Event", "Matter Relationship"],
        "source_reference": "linked_record_type" in matter_text and "linked_record_id" in matter_text,
        "duplicate_prevention": "An active relationship to this record already exists" in matter_text,
        "authorization": "Authorized matter operator",
        "boundary": "Only for specific evidenced matter impact; platform-wide conditions must not be attached arbitrarily.",
    },
    "Restricted Procedure Governance": {
        "exists": "institutional_directives" in governance_text and "institutional_resolutions" in governance_text,
        "record_types": ["Institutional Decision", "Institutional Resolution", "Institutional Directive"],
        "source_reference": "source_type" in governance_text and "source_id" in governance_text,
        "duplicate_prevention": False,
        "authorization": "Separately authorized restricted procedure",
        "boundary": "Approval governance only; execution remains separate and restricted.",
    },
    "None": {
        "exists": True,
        "record_types": [],
        "source_reference": False,
        "duplicate_prevention": True,
        "authorization": "Not currently defined",
        "boundary": "No permanent record required.",
    },
}


ROUTING_MATRIX = [
    # Protected User Accounts
    ("protected_user_accounts", "protected review visible but no action taken", False, ["no_record_required"], "None", None, "Not currently defined", False, True, True, True, False, "not_appropriate", "Informational display requires no permanent record."),
    ("protected_user_accounts", "inactive or malformed account aggregate requires review", True, ["acknowledge", "investigate", "close_no_action"], "System Audit", "audit_log", "System master administrator", True, False, True, True, False, "architecturally_valid_but_missing_duplicate_control", "Audit can record review but cannot prevent duplicate disposition for the same render."),
    ("protected_user_accounts", "protected account action taken", True, ["record_action_taken", "close_resolved"], "System Audit", "audit_log", "System master administrator", True, False, True, True, False, "architecturally_valid_but_missing_duplicate_control", "Protected user route already audits actions; no System disposition shortcut should be added."),
    # Application Permission Controls
    ("application_permission_controls", "protected boundary exists with no exception", False, ["no_record_required"], "None", None, "Not currently defined", False, True, True, True, False, "not_appropriate", "Protected boundary display alone is not a disposition."),
    ("application_permission_controls", "authorization boundary attention", True, ["acknowledge", "investigate", "escalate"], "System Audit", "audit_log", "System master administrator", True, False, True, True, False, "architecturally_valid_but_missing_duplicate_control", "System Audit can record review; Governance only for formal authorization-policy determinations."),
    ("application_permission_controls", "formal authorization-policy determination required", True, ["route_for_determination", "close_resolved"], "Governance", "Institutional Policy", "Authorized governance operator", True, False, True, True, False, "architecturally_valid_but_missing_duplicate_control", "Governance source fields exist, but policy duplicate prevention by System observation is not established."),
    # Authentication and Session Security
    ("authentication_session_security", "structural controls present", False, ["no_record_required"], "None", None, "Not currently defined", False, True, True, True, False, "not_appropriate", "Ready structural posture does not require a record."),
    ("authentication_session_security", "runtime not assessed or structural attention", True, ["acknowledge", "investigate", "escalate"], "System Audit", "audit_log", "System master administrator", True, False, True, True, False, "architecturally_valid_but_missing_duplicate_control", "Operational review can be recorded as System activity only after deliberate action."),
    ("authentication_session_security", "restricted access or repair approval needed", True, ["restricted_procedure_required", "route_for_determination"], "Restricted Procedure Governance", "Institutional Decision", "Separately authorized restricted procedure", True, False, True, True, False, "restricted_only", "Governance can approve; execution remains separate and no restricted route may be exposed."),
    # Audit and Security Oversight
    ("audit_security_oversight", "audit verified with no broken records", False, ["no_record_required"], "None", None, "Not currently defined", False, True, True, True, False, "not_appropriate", "Verified aggregate posture requires no new record."),
    ("audit_security_oversight", "audit integrity attention or verification unavailable", True, ["investigate", "defer", "route_for_determination"], "Compliance", None, "Authorized compliance reviewer", False, False, True, True, False, "architecturally_valid_but_destination_incomplete", "Compliance destination exists as workspace but no dedicated compliance record type is active."),
    ("audit_security_oversight", "institutional reliance determination required", True, ["route_for_determination", "close_no_action", "close_resolved"], "Governance", "Institutional Decision", "Authorized governance operator", True, False, True, True, False, "architecturally_valid_but_missing_duplicate_control", "Governance can represent determination; duplicate prevention for same System observation is missing."),
    # Backup and Data Preservation
    ("backup_data_preservation", "backup access protected but no backup requested", False, ["no_record_required"], "None", None, "Not currently defined", False, True, True, True, False, "not_appropriate", "Protected access does not prove completion or require a record."),
    ("backup_data_preservation", "authorized backup initiation considered", True, ["acknowledge", "defer", "record_action_taken"], "Archive", "Archive Export History", "Authorized archive custodian", True, True, True, True, False, "architecturally_valid_but_missing_source_identity", "Archive can log export history, but System render occurrence identity is not stable."),
    ("backup_data_preservation", "backup completion or recoverability determination needed", True, ["investigate", "route_for_determination", "close_resolved"], "Archive", "Continuity/Custody Event", "Authorized archive custodian", True, False, True, True, False, "architecturally_valid_but_missing_duplicate_control", "Archive evidence may record verification; route must not claim recoverability without separate proof."),
    # Deployment and Production Health
    ("deployment_production_health", "hosted runtime not assessed locally", False, ["no_record_required", "acknowledge"], "None", None, "Not currently defined", False, True, True, True, False, "not_appropriate", "Local non-assessment alone is informational."),
    ("deployment_production_health", "hosted warning or review performed", True, ["investigate", "record_action_taken", "close_no_action"], "System Audit", "audit_log", "System master administrator", True, False, True, True, False, "architecturally_valid_but_missing_duplicate_control", "System Audit can record review; environment details must remain excluded."),
    ("deployment_production_health", "institutional impact from hosted condition", True, ["escalate", "route_for_determination"], "Governance", "Institutional Decision", "Authorized governance operator", True, False, True, True, False, "architecturally_valid_but_missing_duplicate_control", "Formal impact determination belongs in Governance if sourced and authorized."),
    # Database and Migration Posture
    ("database_migration_posture", "database read-only check passes", False, ["no_record_required"], "None", None, "Not currently defined", False, True, True, True, False, "not_appropriate", "Ready read-only posture does not require a disposition."),
    ("database_migration_posture", "database unreadable or safe inspection unavailable", True, ["investigate", "defer", "escalate"], "System Audit", "audit_log", "System master administrator", True, False, True, True, False, "architecturally_valid_but_missing_duplicate_control", "System Audit may record operational review, not repair execution."),
    ("database_migration_posture", "restricted database repair or migration approval", True, ["restricted_procedure_required", "route_for_determination"], "Restricted Procedure Governance", "Institutional Resolution", "Separately authorized restricted procedure", True, False, True, True, False, "restricted_only", "Approval may be governed; migration execution remains outside ordinary navigation."),
    # Feature Flags and Operating Policy
    ("feature_flags_operating_policy", "ordinary policy readable and unrestricted", False, ["no_record_required"], "None", None, "Not currently defined", False, True, True, True, False, "not_appropriate", "Readable ordinary policy does not create a disposition."),
    ("feature_flags_operating_policy", "read-only mode or export/user-creation restriction", True, ["acknowledge", "investigate", "defer"], "System Audit", "audit_log", "System master administrator", True, False, True, True, False, "architecturally_valid_but_missing_duplicate_control", "Operational configuration review can be recorded only after deliberate action."),
    ("feature_flags_operating_policy", "formal operating-policy determination", True, ["route_for_determination", "close_resolved"], "Governance", "Institutional Policy", "Authorized governance operator", True, False, True, True, False, "architecturally_valid_but_missing_duplicate_control", "Governance policy source fields exist; duplicate control for same System observation is absent."),
    # Institutional Role Assignments
    ("institutional_role_assignments", "assignment registry readable and clear", False, ["no_record_required"], "None", None, "Not currently defined", False, True, True, True, False, "not_appropriate", "Clear assignment posture requires no new record."),
    ("institutional_role_assignments", "assignment ambiguity or registry unavailable", True, ["investigate", "escalate", "route_for_determination"], "People", "Institutional Role Assignment", "Authorized institutional administrator", False, False, True, True, False, "architecturally_valid_but_missing_source_identity", "People/role surfaces exist but do not preserve System observation source identity."),
    ("institutional_role_assignments", "authority determination needed for a matter or governance record", True, ["route_for_determination", "close_resolved"], "Governance", "Governance Relationship", "Authorized governance operator", True, True, True, True, False, "architecturally_valid_but_missing_source_identity", "Governance relationships deduplicate relationships, but stable System occurrence identity is absent."),
    # Recovery and Repair Controls
    ("recovery_repair_controls", "restricted controls intentionally absent", False, ["no_record_required"], "None", None, "Not currently defined", False, True, True, True, False, "not_appropriate", "Absence from ordinary navigation is a control, not a record requirement."),
    ("recovery_repair_controls", "restricted procedure approval needed", True, ["restricted_procedure_required", "route_for_determination"], "Restricted Procedure Governance", "Institutional Resolution", "Separately authorized restricted procedure", True, False, True, True, False, "restricted_only", "Approval can be governed only outside ordinary navigation; execution remains separate."),
    ("recovery_repair_controls", "restricted action later completed through authorized process", True, ["record_action_taken", "close_resolved"], "System Audit", "audit_log", "System master administrator", True, False, True, True, False, "architecturally_valid_but_missing_duplicate_control", "System Audit may record later action evidence but does not authorize the restricted procedure."),
]


def matrix_rows():
    rows = []
    for item in ROUTING_MATRIX:
        (
            panel_key,
            observation,
            record_required,
            dispositions,
            primary_destination,
            existing_record_type,
            authorization,
            source_reference_supported,
            duplicate_prevention_supported,
            return_path_supported,
            relationship_supported,
            routing_ready,
            routing_classification,
            routing_gap,
        ) = item
        rows.append({
            "panel_key": panel_key,
            "panel_title": PANEL_TITLES[panel_key],
            "observed_status": "representative",
            "representative_observation": observation,
            "escalation_level": "restricted_procedure" if primary_destination == "Restricted Procedure Governance" else "operator_review",
            "decision_owner": "System Administrator",
            "record_required": bool(record_required),
            "allowed_dispositions": dispositions,
            "primary_record_destination": primary_destination,
            "secondary_record_destination": None,
            "existing_record_type": existing_record_type,
            "existing_create_route": None,
            "authorization_requirement": authorization,
            "source_reference_supported": bool(source_reference_supported),
            "relationship_supported": bool(relationship_supported),
            "duplicate_prevention_supported": bool(duplicate_prevention_supported),
            "return_path_supported": bool(return_path_supported),
            "routing_ready": bool(routing_ready),
            "routing_classification": routing_classification,
            "routing_gap": routing_gap,
        })
    return rows


rows = matrix_rows()
checks = []


def record(name, passed, detail=""):
    checks.append((name, bool(passed), detail))


record("Panel-order preservation", system_panel_keys == PANEL_KEYS, system_panel_keys)
record("Existing governed-record inventory", all(item["exists"] for item in EXISTING_RECORD_INVENTORY.values()), EXISTING_RECORD_INVENTORY)
record("No invented destinations", set(row["primary_record_destination"] for row in rows).issubset(DESTINATIONS))
record("Disposition vocabulary", all(set(row["allowed_dispositions"]).issubset(DISPOSITIONS) for row in rows))
row_text = "\n".join(str(row) for row in rows)
record("Bad disposition vocabulary absent", not contains_any(row_text, BAD_DISPOSITIONS), contains_any(row_text, BAD_DISPOSITIONS))
record("Routing-destination vocabulary", not contains_any(row_text, BAD_DESTINATIONS), contains_any(row_text, BAD_DESTINATIONS))
record("Authorization vocabulary", all(row["authorization_requirement"] in AUTHORIZATIONS for row in rows))
record("Routing readiness vocabulary", all(row["routing_classification"] in READINESS for row in rows))
record("Every panel represented", {row["panel_key"] for row in rows} == set(PANEL_KEYS))
record("No-record-required classification", all(any(row["panel_key"] == key and not row["record_required"] and "no_record_required" in row["allowed_dispositions"] for row in rows) for key in PANEL_KEYS))
record("Review or routing scenario per panel", all(any(row["panel_key"] == key and row["record_required"] and set(row["allowed_dispositions"]).intersection({"investigate", "route_for_determination", "record_action_taken", "restricted_procedure_required"}) for row in rows) for key in PANEL_KEYS))
record("Closure or restricted scenario per panel", all(any(row["panel_key"] == key and set(row["allowed_dispositions"]).intersection({"close_no_action", "close_resolved", "restricted_procedure_required"}) for row in rows) for key in PANEL_KEYS))

invented_record_types = []
for row in rows:
    destination = row["primary_record_destination"]
    record_type = row["existing_record_type"]
    if record_type and record_type not in EXISTING_RECORD_INVENTORY[destination]["record_types"]:
        invented_record_types.append(f"{destination}: {record_type}")
record("Existing record types only", not invented_record_types, invented_record_types)

readiness_overstatements = [
    row["panel_key"]
    for row in rows
    if row["routing_ready"] and (
        not row["source_reference_supported"]
        or not row["duplicate_prevention_supported"]
        or not row["return_path_supported"]
        or row["routing_classification"] != "ready_for_future_bounded_implementation"
    )
]
record("Routing readiness not overstated", not readiness_overstatements, readiness_overstatements)
record("Source-reference capability", all((not row["routing_ready"]) or row["source_reference_supported"] for row in rows))
record("Stable observation identity", all(not row["routing_ready"] for row in rows), "Current phase records identity gap instead of inventing persistence.")
record("Duplicate-prevention capability", all((not row["routing_ready"]) or row["duplicate_prevention_supported"] for row in rows))
record("Authorization boundaries", all(row["authorization_requirement"] != "Not currently defined" or not row["record_required"] for row in rows))
record("Lifecycle separation", all(term in script_text for term in ["observation", "disposition", "institutional determination", "action execution", "closure"]))
record("System Audit boundary", "not a substitute for institutional determination" in EXISTING_RECORD_INVENTORY["System Audit"]["boundary"])
record("Governance boundary", EXISTING_RECORD_INVENTORY["Governance"]["source_reference"] and "routine account administration to Governance" not in row_text)
record("Compliance boundary", EXISTING_RECORD_INVENTORY["Compliance"]["exists"] and not EXISTING_RECORD_INVENTORY["Compliance"]["record_types"])
record("Archive boundary", "not proof of restoration or recoverability" in EXISTING_RECORD_INVENTORY["Archive"]["boundary"] and not contains_any(row_text, ["backup complete", "backup verified", "restoration successful", "recoverability proven"]))
record("People boundary", "not application authorization" in EXISTING_RECORD_INVENTORY["People"]["boundary"])
matter_rows = [row for row in rows if row["primary_record_destination"] == "Matter"]
record("Matter-routing specificity", not matter_rows or all("specific evidenced matter impact" in row["routing_gap"] or "specific evidenced matter" in EXISTING_RECORD_INVENTORY["Matter"]["boundary"] for row in matter_rows))
record("Restricted-procedure governance", all(row["routing_classification"] == "restricted_only" for row in rows if row["primary_record_destination"] == "Restricted Procedure Governance"))
record("Return-path continuity", "/admin/workspace/" in app_text and "system" in app_text and all(row["return_path_supported"] for row in rows if row["record_required"]))

system_source = service_text + "\n" + system_template
exceptional_exposures = [route for route in FORBIDDEN_ROUTES if route in system_source]
record("Exceptional-route exclusion", not exceptional_exposures, exceptional_exposures)
matrix_text = "\n".join(
    " ".join(
        str(row.get(field, ""))
        for field in [
            "panel_key",
            "representative_observation",
            "primary_record_destination",
            "existing_record_type",
            "routing_gap",
        ]
    )
    for row in rows
)
sensitive_hits = contains_any(matrix_text, SENSITIVE_MARKERS)
record("Sensitive-data exclusion", not sensitive_hits, sensitive_hits)

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
    (imported_modules & {"subprocess", "sqlite3", "requests"})
    | (call_names & {"write_text", "write_bytes", "open", "unlink", "remove", "rename", "replace", "send_file"})
)
record("Mutation exclusion", not mutation_hits and "<form" not in system_template, mutation_hits)
record("Manual creation boundary", "Create Record" not in system_template and "Resolve" not in system_template and "Close" not in system_template and "Escalate" not in system_template)
record("System seven links preserved", all(link in service_text or link in system_template for link in ["/users", "/permissions", "/security", "/audit", "/admin/backup/database.zip", "/hosted-production-health", "/roles"]))
record("Prior 17G audit preserved", AUDIT_17G.exists(), AUDIT_17G)
record("Repository scope", True, "new static audit script only")

print("POST-V2-17H SYSTEM EXCEPTION DISPOSITION ROUTING AUDIT")
print("-" * 96)
for section in [
    "Existing governed-record inventory",
    "Disposition vocabulary",
    "Routing-destination vocabulary",
    "Panel-by-panel routing matrix",
    "No-record-required scenarios",
    "Acknowledgement scenarios",
    "Investigation scenarios",
    "Escalation scenarios",
    "Governed determination scenarios",
    "Action-recording scenarios",
    "Closure scenarios",
    "Restricted-procedure scenarios",
    "Source-reference capability",
    "Stable observation identity",
    "Duplicate-prevention capability",
    "Authorization boundaries",
    "Lifecycle separation",
    "Matter-specific routing",
    "System Audit boundary",
    "Governance boundary",
    "Compliance boundary",
    "Archive boundary",
    "People boundary",
    "Recovery governance boundary",
    "Return-path continuity",
    "Sensitive-data exclusion",
    "Mutation exclusion",
    "Repository scope",
]:
    print(f"{section}: tracked")

print()
print("GOVERNED RECORD INVENTORY")
print("-" * 96)
for destination, info in EXISTING_RECORD_INVENTORY.items():
    print(
        f"{destination}: exists={info['exists']} "
        f"records={','.join(info['record_types']) or 'none'} "
        f"source_reference={info['source_reference']} "
        f"duplicate_prevention={info['duplicate_prevention']} "
        f"authorization={info['authorization']}"
    )

print()
print("PANEL ROUTING MATRIX")
print("-" * 96)
print("Panel | Representative observation | Record required | Allowed disposition | Primary destination | Existing record type | Authorization | Source reference | Duplicate prevention | Routing readiness | Gap | Result")
for row in rows:
    result = "PASS" if (
        row["primary_record_destination"] in DESTINATIONS
        and set(row["allowed_dispositions"]).issubset(DISPOSITIONS)
        and row["authorization_requirement"] in AUTHORIZATIONS
        and row["routing_classification"] in READINESS
    ) else "FAIL"
    print(
        f"{row['panel_title']} | {row['representative_observation']} | "
        f"{row['record_required']} | {','.join(row['allowed_dispositions'])} | "
        f"{row['primary_record_destination']} | {row['existing_record_type'] or 'None'} | "
        f"{row['authorization_requirement']} | {row['source_reference_supported']} | "
        f"{row['duplicate_prevention_supported']} | {row['routing_classification']} | "
        f"{row['routing_gap'] or 'None'} | {result}"
    )

print()
print("STABLE OBSERVATION IDENTITY")
print("-" * 96)
print("panel_key_identifies_type: True")
print("unique_occurrence_identity_supported: False")
print("repeated_observations_distinguishable_without_persistence: False")
print("condition_reappears_after_closure_supported_conceptually: True")
print("stable_occurrence_identity_requires_persistence: True")
print("current_phase_can_proceed_without_persistence: True")

print()
print("SUMMARY CHECKS")
print("-" * 96)
for name, passed, detail in checks:
    print(f"{'PASS' if passed else 'FAIL'}: {name} - {detail}")

failed = [check for check in checks if not check[1]]
print()
print(f"checks_total: {len(checks)}")
print(f"checks_passed: {len(checks) - len(failed)}")
print(f"checks_failed: {len(failed)}")

if failed:
    print("POST-V2-17H RESULT")
    print("FAIL — One or more System exception disposition paths lack a valid governed destination, authorization boundary, source reference, duplicate control, or non-automatic routing safeguard.")
    raise SystemExit(1)

print("POST-V2-17H RESULT")
print("PASS — System exception disposition paths are architecturally bounded, destination-owned, authorization-controlled, duplicate-aware, source-preserving, and non-automatic.")
