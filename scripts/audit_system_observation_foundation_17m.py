import os
import sqlite3
import sys
import tempfile
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
TEMP_DIR = tempfile.TemporaryDirectory(prefix="trustee_17m_")
DB_PATH = Path(TEMP_DIR.name) / "system_observation_foundation.db"
os.environ["DB_PATH"] = str(DB_PATH)
sys.path.insert(0, str(ROOT))

from migrations.add_system_observation_registry import ensure_system_observation_registry
from services import services_system_observations as svc


APP = ROOT / "app.py"
SYSTEM_SERVICE = ROOT / "services" / "services_system_workspace.py"
SYSTEM_TEMPLATE = ROOT / "templates" / "ios_workspaces" / "system.html"
MODEL = ROOT / "models" / "models_system_observations.py"
SERVICE = ROOT / "services" / "services_system_observations.py"
MIGRATION = ROOT / "migrations" / "add_system_observation_registry.py"


def read(path):
    return path.read_text(encoding="utf-8", errors="replace")


def ok(value):
    return "PASS" if value else "FAIL"


def section(title):
    print()
    print(title.upper())
    print("-" * 100)


checks = []


def record(name, passed, detail=""):
    checks.append((name, bool(passed), detail))


def table_names():
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        return [row[0] for row in rows]
    finally:
        conn.close()


def columns(table):
    conn = sqlite3.connect(DB_PATH)
    try:
        return [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    finally:
        conn.close()


def indexes(table):
    conn = sqlite3.connect(DB_PATH)
    try:
        return [row[1] for row in conn.execute(f"PRAGMA index_list({table})").fetchall()]
    finally:
        conn.close()


def count_rows(table):
    conn = sqlite3.connect(DB_PATH)
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


def actor(label="Foundation Operator"):
    return {
        "actor_id": "USR-17M",
        "actor_label": label,
        "permissions": ["system_observation_create"],
        "is_master_admin": True,
        "firm_id": "FIRM-001",
    }


def create_base(**overrides):
    payload = {
        "observation_type": "permission_posture",
        "condition_code": "permission_boundary_missing",
        "panel_key": "application_permission_controls",
        "persistence_trigger": "investigation_start",
        "context": {"context_scope": "firm_scoped", "firm_id": "FIRM-001"},
        "sanitized_summary": "Permission boundary requires review.",
        "actor_context": actor(),
        "initial_state": "acknowledged",
    }
    payload.update(overrides)
    return svc.create_system_observation(**payload)


migration_one = ensure_system_observation_registry()
migration_two = ensure_system_observation_registry()

app_text = read(APP)
system_service_text = read(SYSTEM_SERVICE)
system_template_text = read(SYSTEM_TEMPLATE)
model_text = read(MODEL)
service_text = read(SERVICE)
migration_text = read(MIGRATION)

obs_columns = set(columns("system_observations"))
event_columns = set(columns("system_observation_events"))
obs_indexes = set(indexes("system_observations"))
event_indexes = set(indexes("system_observation_events"))

required_obs_columns = {
    "id",
    "observation_id",
    "observation_type",
    "panel_key",
    "condition_code",
    "current_state",
    "persistence_trigger",
    "context_scope",
    "context_id",
    "firm_id",
    "institution_id",
    "trust_id",
    "matter_id",
    "deployment_key",
    "sanitized_summary",
    "first_observed_at",
    "last_observed_at",
    "prior_occurrence_id",
    "superseded_by_observation_id",
    "active_duplicate_key",
    "version",
    "created_by",
    "created_at",
    "updated_by",
    "updated_at",
}

required_event_columns = {
    "id",
    "observation_event_id",
    "observation_id",
    "event_type",
    "prior_state",
    "resulting_state",
    "actor_id",
    "actor_label",
    "authority_record_type",
    "authority_record_id",
    "event_summary",
    "reason_code",
    "related_record_type",
    "related_record_id",
    "idempotency_key",
    "created_at",
}

record("Migration idempotency", migration_one.get("ok") and migration_two.get("ok"), (migration_one, migration_two))
record("Observation table", "system_observations" in table_names() and required_obs_columns.issubset(obs_columns), sorted(required_obs_columns - obs_columns))
record("Observation event table", "system_observation_events" in table_names() and required_event_columns.issubset(event_columns), sorted(required_event_columns - event_columns))
record("Numbering table", "system_observation_number_sequences" in table_names(), table_names())
record("Database duplicate control", "uq_system_observations_open_duplicate" in obs_indexes, obs_indexes)
record("Event idempotency index", "uq_system_observation_events_idempotency" in event_indexes, event_indexes)
record("No seed records", count_rows("system_observations") == 0 and count_rows("system_observation_events") == 0, "")
record("Observation-type registry", len(svc.OBSERVATION_TYPES) == 10 and "account_posture" in svc.OBSERVATION_TYPES, "")
record("Panel/type mapping", len(svc.PANEL_TYPE_MAP) == 10 and svc.PANEL_TYPE_MAP["application_permission_controls"] == "permission_posture", "")
record("Condition-code registry", "permission_boundary_missing" in svc.CONDITION_CODE_REGISTRY and svc.CONDITION_CODE_REGISTRY["permission_boundary_missing"]["observation_type"] == "permission_posture", "")
record("Context-scope registry", {"platform_scoped", "deployment_scoped", "firm_scoped", "institution_scoped", "trust_scoped", "matter_scoped"}.issubset(svc.CONTEXT_SCOPES), "")
record("Persistence-trigger registry", "investigation_start" in svc.PERSISTENCE_TRIGGERS and "render" not in svc.PERSISTENCE_TRIGGERS and "refresh" not in svc.PERSISTENCE_TRIGGERS, "")

created = create_base(idempotency_key="create-1")
observation = created.get("observation") or {}
event = created.get("event") or {}
record("Creation service", created.get("ok") and created.get("status") == "created", created)
record("Public numbering", str(observation.get("observation_id", "")).startswith("SYSOBS-") and str(event.get("observation_event_id", "")).startswith("SYSEVT-"), (observation, event))
record("Creation event generated", event.get("event_type") == "observation_created" and event.get("resulting_state") == "acknowledged", event)
record("Initial version", observation.get("version") == 1, observation)
record("Duplicate key", bool(observation.get("active_duplicate_key")), observation.get("active_duplicate_key"))

invalid_type = create_base(observation_type="bad_type")
invalid_panel = create_base(panel_key="protected_user_accounts")
invalid_condition = create_base(condition_code="audit_integrity_attention")
invalid_context = create_base(context={"context_scope": "platform_scoped", "firm_id": "FIRM-001"})
invalid_trigger = create_base(persistence_trigger="render")
oversized = create_base(sanitized_summary="x" * 1001)
sensitive = create_base(sanitized_summary="This contains a password.")
record("Validation", all(item.get("status") == "invalid_input" for item in [invalid_type, invalid_panel, invalid_condition, invalid_context, invalid_trigger, oversized, sensitive]), "")

duplicate = create_base(idempotency_key="create-duplicate")
different_context = create_base(context={"context_scope": "firm_scoped", "firm_id": "FIRM-002"}, idempotency_key="create-2")
different_condition = create_base(
    condition_code="csrf_boundary_missing",
    sanitized_summary="CSRF boundary requires review.",
    idempotency_key="create-3",
)
record("Service duplicate control", duplicate.get("status") == "duplicate_observation" and not duplicate.get("ok"), duplicate)
record("Different context allowed", different_context.get("ok"), different_context)
record("Different condition allowed", different_condition.get("ok"), different_condition)
record("Duplicate creates no event", count_rows("system_observation_events") == 3, count_rows("system_observation_events"))

replay_create = create_base(idempotency_key="create-1")
record("Creation idempotency replay", replay_create.get("ok") and replay_create.get("status") == "idempotent_replay", replay_create)

obs_id = observation["observation_id"]
transition = svc.transition_system_observation(
    observation_id=obs_id,
    target_state="under_review",
    event_type="investigation_started",
    expected_version=1,
    actor_context=actor(),
    reason="operator_review",
    event_summary="Investigation started.",
    idempotency_key="transition-1",
)
after_transition = transition.get("observation") or {}
record("Transition service", transition.get("ok") and transition.get("status") == "transitioned", transition)
record("Current-state projection", after_transition.get("current_state") == "under_review" and after_transition.get("version") == 2, after_transition)
record("Versioning", after_transition.get("version") == 2, after_transition)

stale = svc.transition_system_observation(
    observation_id=obs_id,
    target_state="deferred",
    event_type="deferred",
    expected_version=1,
    actor_context=actor(),
    reason="defer_review",
    event_summary="Stale test.",
    idempotency_key="stale-1",
)
record("Stale-write rejection", stale.get("status") == "stale_version" and count_rows("system_observation_events") == 4, stale)

invalid_transition = svc.transition_system_observation(
    observation_id=obs_id,
    target_state="acknowledged",
    event_type="acknowledged",
    expected_version=2,
    actor_context=actor(),
    reason="bad_jump",
    event_summary="Invalid transition.",
    idempotency_key="bad-transition-1",
)
record("Invalid transition", invalid_transition.get("status") == "invalid_transition", invalid_transition)

resolved = svc.transition_system_observation(
    observation_id=obs_id,
    target_state="closed_resolved",
    event_type="closed_resolved",
    expected_version=2,
    actor_context=actor(),
    reason="evidence_verified",
    event_summary="Resolved with bounded evidence.",
    related_record_type="Governance",
    related_record_id="GOV-17M",
    idempotency_key="close-1",
)
record("Closure handling", resolved.get("ok") and resolved["observation"]["active_duplicate_key"] is None, resolved)

recurrence = create_base(idempotency_key="create-recurrence", prior_occurrence_id=obs_id)
record("Recurrence handling", recurrence.get("ok") and recurrence["observation"]["observation_id"] != obs_id and recurrence["observation"]["prior_occurrence_id"] == obs_id, recurrence)

closed_no_action_source = create_base(
    condition_code="audit_integrity_attention",
    observation_type="audit_integrity_posture",
    panel_key="audit_security_oversight",
    context={"context_scope": "firm_scoped", "firm_id": "FIRM-003"},
    sanitized_summary="Audit integrity attention requires review.",
    idempotency_key="reopen-source",
)
closed_no_action = svc.transition_system_observation(
    observation_id=closed_no_action_source["observation"]["observation_id"],
    target_state="closed_no_action",
    event_type="closed_no_action",
    expected_version=1,
    actor_context=actor(),
    reason="no_record_required",
    event_summary="Closed with no action.",
    idempotency_key="close-no-action",
)
reopened = svc.transition_system_observation(
    observation_id=closed_no_action_source["observation"]["observation_id"],
    target_state="under_review",
    event_type="reopened",
    expected_version=2,
    actor_context=actor(),
    reason="condition_returned",
    event_summary="Reopened for review.",
    idempotency_key="reopen-1",
)
record("Reopen handling", reopened.get("ok") and reopened["observation"]["observation_id"] == closed_no_action_source["observation"]["observation_id"] and reopened["observation"]["active_duplicate_key"], reopened)

successor = create_base(
    context={"context_scope": "firm_scoped", "firm_id": "FIRM-004"},
    idempotency_key="successor-create",
)
source_for_supersede = create_base(
    context={"context_scope": "firm_scoped", "firm_id": "FIRM-005"},
    idempotency_key="supersede-source",
)
superseded = svc.transition_system_observation(
    observation_id=source_for_supersede["observation"]["observation_id"],
    target_state="superseded",
    event_type="superseded",
    expected_version=1,
    actor_context=actor(),
    reason="classification_corrected",
    event_summary="Superseded by successor.",
    superseded_by_observation_id=successor["observation"]["observation_id"],
    idempotency_key="supersede-1",
)
record("Supersession readiness", superseded.get("ok") and superseded["observation"]["current_state"] == "superseded" and superseded["observation"]["active_duplicate_key"] is None, superseded)

transition_replay = svc.transition_system_observation(
    observation_id=obs_id,
    target_state="closed_resolved",
    event_type="closed_resolved",
    expected_version=2,
    actor_context=actor(),
    reason="evidence_verified",
    event_summary="Resolved with bounded evidence.",
    related_record_type="Governance",
    related_record_id="GOV-17M",
    idempotency_key="close-1",
)
conflict_replay = svc.transition_system_observation(
    observation_id=obs_id,
    target_state="closed_resolved",
    event_type="closed_resolved",
    expected_version=3,
    actor_context=actor(),
    reason="different_reason",
    event_summary="Different payload.",
    related_record_type="Governance",
    related_record_id="GOV-17M",
    idempotency_key="close-1",
)
record("Idempotency", transition_replay.get("status") == "idempotent_replay" and conflict_replay.get("status") == "conflict", (transition_replay, conflict_replay))

events = svc.list_system_observation_events(obs_id)
record("Read services", svc.get_system_observation(obs_id) and events and svc.list_system_observations(limit=5), "")
record("Events ordered", [event["created_at"] for event in events] == sorted(event["created_at"] for event in events), events)
record("Append-only events", "update_event" not in service_text and "delete_event" not in service_text and "replace_event" not in service_text, "")

before_atomic = svc.get_system_observation(obs_id)
original_insert = svc._insert_event


def failing_insert(*args, **kwargs):
    raise RuntimeError("simulated_event_failure")


svc._insert_event = failing_insert
event_failure = svc.transition_system_observation(
    observation_id=obs_id,
    target_state="under_review",
    event_type="reopened",
    expected_version=before_atomic["version"],
    actor_context=actor(),
    reason="simulated",
    event_summary="Should fail.",
    idempotency_key="event-fail",
)
svc._insert_event = original_insert
after_event_failure = svc.get_system_observation(obs_id)
record("Atomic event failure", event_failure.get("status") == "unexpected_failure" and before_atomic["version"] == after_event_failure["version"], event_failure)

projection_source = create_base(
    condition_code="hosted_health_attention",
    observation_type="deployment_health_posture",
    panel_key="deployment_production_health",
    context={"context_scope": "deployment_scoped", "deployment_key": "railway-prod"},
    sanitized_summary="Hosted health needs review.",
    idempotency_key="projection-source",
)
projection_id = projection_source["observation"]["observation_id"]
events_before_projection = count_rows("system_observation_events")
original_projection = svc._update_observation_projection


def failing_projection(*args, **kwargs):
    raise RuntimeError("simulated_projection_failure")


svc._update_observation_projection = failing_projection
projection_failure = svc.transition_system_observation(
    observation_id=projection_id,
    target_state="under_review",
    event_type="investigation_started",
    expected_version=1,
    actor_context=actor(),
    reason="simulated",
    event_summary="Should roll back.",
    idempotency_key="projection-fail",
)
svc._update_observation_projection = original_projection
record("Atomic projection failure", projection_failure.get("status") == "unexpected_failure" and count_rows("system_observation_events") == events_before_projection and svc.get_system_observation(projection_id)["version"] == 1, projection_failure)

sensitive_result_text = str(created) + str(transition) + str(stale) + str(event_failure)
record("Sensitive-data exclusion", not any(marker in sensitive_result_text.lower() for marker in ["traceback", "database path", "password_hash", "connection string"]), "")
record("Error containment", event_failure.get("message") == "System observation could not be transitioned." and projection_failure.get("message") == "System observation could not be transitioned.", (event_failure, projection_failure))
record("Actor attribution", all(item.get("actor_id") == "USR-17M" for item in svc.list_system_observation_events(obs_id)), "")
record("Authority-reference readiness", {"authority_record_type", "authority_record_id"}.issubset(event_columns), "")
record("Related-record readiness", {"related_record_type", "related_record_id"}.issubset(event_columns), "")
record("No deletion services", all(name not in service_text for name in ["delete_system_observation", "delete_system_observation_event", "update_system_observation_event"]), "")
record("No route exposure", all(marker not in app_text for marker in ["/system/observations", "/admin/system/observations", "/admin/workspace/system/observations"]), "")
record("No render-side effects", "services_system_observations" not in system_service_text and "services_system_observations" not in system_template_text, "")
record("System Workspace preservation", "System Observation Registry" not in system_template_text and "<form" not in system_template_text and all(link in system_template_text or link in system_service_text for link in ["/users", "/permissions", "/security", "/audit", "/admin/backup/database.zip", "/hosted-production-health", "/roles"]), "")
record("Repository scope", all(path.exists() for path in [MODEL, SERVICE, MIGRATION]) and "app.route" not in service_text, "")

section("Schema foundation")
print(f"database: {DB_PATH}")
print(f"tables: {table_names()}")
print(f"observation_columns: {sorted(obs_columns)}")
print(f"event_columns: {sorted(event_columns)}")
print(f"observation_indexes: {sorted(obs_indexes)}")
print(f"event_indexes: {sorted(event_indexes)}")

section("Service exercise")
for label, result in [
    ("created", created),
    ("duplicate", duplicate),
    ("transition", transition),
    ("stale", stale),
    ("closure", resolved),
    ("reopened", reopened),
    ("recurrence", recurrence),
    ("superseded", superseded),
]:
    print(f"{label}: {result.get('status')} ok={result.get('ok')}")

section("Required audit output")
for item in [
    "Schema foundation",
    "Observation table",
    "Observation event table",
    "Public numbering",
    "Observation-type registry",
    "Condition-code registry",
    "Context validation",
    "Persistence-trigger validation",
    "Creation service",
    "Transition service",
    "Read services",
    "Duplicate-control anchor",
    "Database duplicate enforcement",
    "Versioning",
    "Stale-write rejection",
    "Idempotency",
    "Append-only event enforcement",
    "Atomicity",
    "Reopen handling",
    "Recurrence handling",
    "Supersession readiness",
    "Closure handling",
    "Actor attribution",
    "Authority-reference readiness",
    "Related-record readiness",
    "Sensitive-data exclusion",
    "Error containment",
    "Migration idempotency",
    "No seed records",
    "No route exposure",
    "No render-side effects",
    "System Workspace preservation",
    "Repository scope",
]:
    print(f"{item}: tracked")

section("Summary checks")
for name, passed, detail in checks:
    print(f"{ok(passed)}: {name} - {detail}")

failed = [item for item in checks if not item[1]]
print()
print(f"checks_total: {len(checks)}")
print(f"checks_passed: {len(checks) - len(failed)}")
print(f"checks_failed: {len(failed)}")
print("POST-V2-17M RESULT")
if failed:
    print("FAIL - The System Observation Registry foundation contains incomplete identity, lifecycle, validation, duplicate-control, atomicity, or exposure safeguards.")
    raise SystemExit(1)
print("PASS - The minimal System Observation Registry foundation provides stable identity, append-only lifecycle evidence, bounded validation, duplicate control, version protection, and atomic service behavior without exposing an operator mutation workflow.")
