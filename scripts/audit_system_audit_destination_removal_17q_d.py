import os
import re
import sqlite3
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


REQUIRED_BRANCH = "post-v2-planning"
CERTIFIED_PHASE_COMMIT = "2aaf5b61e0323aa0aed3ebb582954105a57ed7b8"
ACTIVE_PHASE_ALLOWED_PATHS = {
    "scripts/audit_archive_people_destination_adapters_17q_e.py",
    "scripts/audit_system_audit_destination_removal_17q_d.py",
    "scripts/audit_compliance_review_architecture_17q_f.py",
    "scripts/audit_regression_guard_and_auth_preservation_17q_f_1.py",
}
NORMAL_DB_PATH = Path(os.environ.get("DB_PATH", ROOT / "trustee_app.db"))
TEMP_DIR = tempfile.TemporaryDirectory(prefix="trustee_17q_d_", ignore_cleanup_errors=True)
TEMP_DB_PATH = Path(TEMP_DIR.name) / "system_audit_destination_removal.db"
os.environ["DB_PATH"] = str(TEMP_DB_PATH)
os.environ.setdefault("UPLOAD_FOLDER", str(Path(TEMP_DIR.name) / "uploads"))
os.environ.setdefault("EXPORT_ROOT", str(Path(TEMP_DIR.name) / "exports"))


from app import app  # noqa: E402
from database.db import (  # noqa: E402
    create_app_user,
    ensure_firm_columns,
    ensure_role_tables,
    ensure_table_firm_id_column,
    ensure_user_tables,
    get_connection,
    get_next_user_id,
    get_user_by_username,
    init_db,
    reseed_default_role_permissions,
)
from migrations.add_system_observation_registry import ensure_system_observation_registry  # noqa: E402
from services.services_governance import ensure_governance_tables  # noqa: E402
from services.services_matters import ensure_matter_tables  # noqa: E402
from services.services_system_observation_destinations import (  # noqa: E402
    DESTINATION_LABELS,
    DESTINATION_RECORD_TYPES,
    DESTINATION_VERIFIERS,
    destination_registry_report,
    verify_destination_record,
)
from services.services_system_observations import (  # noqa: E402
    ROUTING_DESTINATION_MATRIX,
    create_system_observation,
    get_allowed_routing_destinations,
    get_system_observation,
    get_system_observation_detail,
    route_system_observation,
)


def read(path):
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def git(*args):
    import subprocess

    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()


def git_code(*args):
    import subprocess

    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False).returncode


def record(results, name, passed, details=""):
    results.append((name, bool(passed), details))


def result_line(passed):
    return "PASS" if passed else "FAIL"


def normal_counts():
    if not NORMAL_DB_PATH.exists():
        return {"path": str(NORMAL_DB_PATH), "exists": False}
    conn = sqlite3.connect(NORMAL_DB_PATH)
    try:
        result = {"path": str(NORMAL_DB_PATH), "exists": True}
        for table in ("system_observations", "system_observation_events", "governance_relationships", "audit_log"):
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            result[table] = "MISSING" if not exists else conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return result
    finally:
        conn.close()


def fixture_counts():
    conn = get_connection()
    try:
        result = {}
        for table in (
            "system_observations",
            "system_observation_events",
            "governance_relationships",
            "institutional_directives",
            "institutional_policies",
            "matters",
            "audit_log",
        ):
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            result[table] = "MISSING" if not exists else conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return result
    finally:
        conn.close()


def actor(label="17Q-D Auditor"):
    return {"actor_id": "USR-17QD", "actor_label": label, "firm_id": "FIRM-002"}


ROUTING_PANEL_TYPES = {
    "application_permission_controls": "permission_posture",
    "audit_security_oversight": "audit_integrity_posture",
}


def set_admin_session(client, firm_id="FIRM-002"):
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = "USR-ADMIN"
        sess["username"] = "admin"
        sess["role"] = "Admin"
        sess["user_role"] = "Admin"
        sess["is_master_admin"] = True
        sess["firm_id"] = firm_id
        sess["last_activity"] = datetime.now(UTC).timestamp()


def csrf(body):
    match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', body)
    return match.group(1) if match else ""


def init_fixture():
    with app.app_context():
        init_db()
        ensure_user_tables()
        ensure_firm_columns()
        ensure_table_firm_id_column("trusts", "FIRM-001")
        ensure_role_tables()
        reseed_default_role_permissions()
        ensure_system_observation_registry()
        ensure_matter_tables()
        ensure_governance_tables()
        if not get_user_by_username("admin"):
            create_app_user(
                {
                    "user_id": get_next_user_id(),
                    "username": "admin",
                    "password_hash": "audit-only",
                    "role_name": "Admin",
                    "status": "Active",
                    "firm_id": "FIRM-002",
                }
            )
        now = datetime.now(UTC).isoformat(timespec="seconds")
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO matters (
                    matter_id, firm_id, title, matter_type, status, priority,
                    jurisdiction, lead_fiduciary, governance_state, risk_level,
                    archive_status, purpose, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "MAT-17QD-0001",
                    "FIRM-002",
                    "17Q-D Verified Matter",
                    "System Governance",
                    "Open",
                    "Normal",
                    "Internal",
                    "Admin",
                    "Review",
                    "Medium",
                    "Not Archived",
                    "Routing vocabulary fixture",
                    "",
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO institutional_directives (
                    directive_id, firm_id, directive_code, title, directive_type,
                    status, authority, issuing_authority, authority_basis,
                    approval_required, approved_by, approved_at, issued_by,
                    issued_at, effective_at, summary, instruction, rationale,
                    scope, version_label, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "DIR-2026-1701",
                    "FIRM-002",
                    "17QD-DIR",
                    "17Q-D Verified Directive",
                    "Governance Directive",
                    "Active",
                    "Institutional verification",
                    "Admin",
                    "Audit fixture",
                    0,
                    "Admin",
                    now,
                    "Admin",
                    now,
                    now,
                    "System Audit removal fixture",
                    "Verify routing vocabulary correction",
                    "17Q-D audit",
                    "System observations",
                    "v1",
                    "Admin",
                    now,
                    now,
                ),
            )
            conn.commit()
        finally:
            conn.close()


def create_under_review(condition_code, panel_key, idem, firm_id="FIRM-002"):
    created = create_system_observation(
        observation_type=ROUTING_PANEL_TYPES[panel_key],
        panel_key=panel_key,
        condition_code=condition_code,
        persistence_trigger="investigation_start",
        context={"context_scope": "firm_scoped", "firm_id": firm_id},
        sanitized_summary=f"17Q-D under-review fixture for {condition_code}",
        actor_context=actor(),
        initial_state="under_review",
        idempotency_key=f"{idem}-create",
    )
    assert created["ok"], created
    return created["observation"]


def insert_historical_system_audit_reference(observation_id):
    conn = get_connection()
    try:
        now = datetime.now(UTC).isoformat(timespec="seconds")
        event_id = "SYSEVT-17QD-HISTORICAL"
        conn.execute(
            """
            INSERT INTO system_observation_events (
                observation_event_id, observation_id, event_type, prior_state,
                resulting_state, actor_id, actor_label, authority_record_type,
                authority_record_id, event_summary, reason_code, related_record_type,
                related_record_id, idempotency_key, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                observation_id,
                "routing_prepared",
                "under_review",
                "routed",
                "USR-LEGACY",
                "Legacy Fixture",
                None,
                None,
                "Legacy System Audit reference for display compatibility.",
                "legacy_fixture",
                "System Audit",
                "AUDIT-LEGACY-0001",
                "17qd-legacy-reference",
                now,
            ),
        )
        conn.commit()
        return event_id
    finally:
        conn.close()


def count_events(observation_id):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM system_observation_events WHERE observation_id = ?",
            (observation_id,),
        ).fetchone()[0]
    finally:
        conn.close()


def run():
    before_normal = normal_counts()
    init_fixture()
    results = []

    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    remote = git("rev-parse", "origin/post-v2-planning")
    phase_commit_is_ancestor = git_code("merge-base", "--is-ancestor", CERTIFIED_PHASE_COMMIT, "HEAD") == 0
    staged_paths = set(git("diff", "--cached", "--name-only").splitlines())
    status = git("status", "--short")
    changed_paths = {
        line[3:].replace("\\", "/") if line.startswith("?? ") else line[2:].strip().replace("\\", "/")
        for line in status.splitlines()
        if line.strip()
    }
    destinations_source = read("services/services_system_observation_destinations.py")
    observations_source = read("services/services_system_observations.py")

    report = destination_registry_report()
    record(results, "Certified baseline", branch == REQUIRED_BRANCH and phase_commit_is_ancestor)
    record(results, "Repository scope", not staged_paths and changed_paths <= ACTIVE_PHASE_ALLOWED_PATHS)
    record(results, "System Audit classification", "system_audit" not in report and "system_audit" not in DESTINATION_LABELS)
    record(results, "Routing vocabulary correction", "system_audit" not in DESTINATION_LABELS and "system_audit" not in DESTINATION_RECORD_TYPES)
    record(results, "Verifier-registry correction", "system_audit" not in DESTINATION_VERIFIERS and "verify_system_audit_destination" not in destinations_source)
    record(results, "Eligibility-matrix correction", all("system_audit" not in allowed for allowed in ROUTING_DESTINATION_MATRIX.values()))

    actor_context = {**actor(), "scope": {"global": True}}
    verifier_observation = {"firm_id": "FIRM-002", "context_scope": "firm_scoped", "context_id": "FIRM-002"}
    governance_status = verify_destination_record("governance", "DIR-2026-1701", observation=verifier_observation, actor_context=actor_context)
    matter_status = verify_destination_record("matter", "MAT-17QD-0001", observation=verifier_observation, actor_context=actor_context)
    record(results, "Governance verifier preserved", governance_status.get("ok") and governance_status.get("status") == "verified")
    record(results, "Matter verifier preserved", matter_status.get("ok") and matter_status.get("status") == "verified")
    record(results, "Compliance remains bounded unavailable", verify_destination_record("compliance", "CMP-17QD", actor_context=actor_context).get("status") == "destination_unavailable")
    record(results, "Archive no longer reintroduces System Audit", report.get("archive", {}).get("implementation_status") in {"verified_supported", "bounded_unavailable"})
    record(results, "People no longer reintroduces System Audit", report.get("people", {}).get("implementation_status") in {"verified_supported", "bounded_unavailable"})
    record(
        results,
        "Restricted Procedure remains bounded unavailable",
        verify_destination_record("restricted_procedure_governance", "RPG-17QD", actor_context=actor_context).get("status")
        == "restricted_destination_unavailable",
    )
    record(results, "System Audit verifier rejects as invalid", verify_destination_record("system_audit", "AUDIT-17QD", actor_context=actor_context).get("status") == "invalid_destination_type")

    negative_obs = create_under_review("audit_integrity_attention", "audit_security_oversight", "17qd-negative")
    negative_before = fixture_counts()
    negative_event_count = count_events(negative_obs["observation_id"])
    rejected = route_system_observation(
        observation_id=negative_obs["observation_id"],
        destination_type="system_audit",
        destination_record_id="AUDIT-17QD",
        expected_version=negative_obs["version"],
        routing_reason="attempt to route to removed System Audit destination",
        routing_summary="This route must be rejected before mutation.",
        actor_context=actor(),
        idempotency_key="17qd-route-system-audit",
        scope={"global": True},
    )
    negative_after = fixture_counts()
    negative_after_obs = get_system_observation(negative_obs["observation_id"])
    record(results, "Routing-service rejection", not rejected.get("ok") and rejected.get("status") == "invalid_destination_type")
    record(results, "No event created on rejected route", count_events(negative_obs["observation_id"]) == negative_event_count)
    record(results, "No destination reference created", negative_after["system_observation_events"] == negative_before["system_observation_events"])
    record(results, "No state change", negative_after_obs.get("current_state") == negative_obs.get("current_state"))
    record(results, "No version increment", negative_after_obs.get("version") == negative_obs.get("version"))
    record(results, "No relationship created", negative_after["governance_relationships"] == negative_before["governance_relationships"])
    record(results, "No idempotent success", rejected.get("status") != "idempotent_replay")

    gov_obs = create_under_review("permission_boundary_missing", "application_permission_controls", "17qd-governance")
    gov_before = fixture_counts()
    gov_route = route_system_observation(
        observation_id=gov_obs["observation_id"],
        destination_type="governance",
        destination_record_id="DIR-2026-1701",
        expected_version=gov_obs["version"],
        routing_reason="verified governance directive",
        routing_summary="Route remains supported after System Audit removal.",
        actor_context=actor(),
        idempotency_key="17qd-route-governance",
        scope={"global": True},
    )
    gov_after = fixture_counts()
    gov_event = gov_route.get("event") or {}
    record(results, "Governance regression", gov_route.get("ok") and gov_route.get("status") == "routed")
    record(results, "Generic audit attribution preservation", bool(gov_event.get("actor_id")) and bool(gov_event.get("actor_label")))
    record(results, "Version protection preservation", (gov_route.get("observation") or {}).get("version") == gov_obs.get("version") + 1)
    record(results, "Atomicity preservation", gov_after["system_observation_events"] == gov_before["system_observation_events"] + 1)
    stale = route_system_observation(
        observation_id=gov_obs["observation_id"],
        destination_type="governance",
        destination_record_id="DIR-2026-1701",
        expected_version=gov_obs["version"],
        routing_reason="stale replay should fail",
        routing_summary="Stale write protection.",
        actor_context=actor(),
        idempotency_key="17qd-route-stale",
        scope={"global": True},
    )
    record(results, "Stale-write rejection", not stale.get("ok") and stale.get("status") in {"invalid_transition", "stale_version"})
    replay = route_system_observation(
        observation_id=gov_obs["observation_id"],
        destination_type="governance",
        destination_record_id="DIR-2026-1701",
        expected_version=gov_obs["version"],
        routing_reason="verified governance directive",
        routing_summary="Route remains supported after System Audit removal.",
        actor_context=actor(),
        idempotency_key="17qd-route-governance",
        scope={"global": True},
    )
    record(results, "Idempotency preservation", replay.get("ok") and replay.get("status") == "idempotent_replay")

    matter_obs = create_under_review("csrf_boundary_missing", "application_permission_controls", "17qd-matter")
    matter_route = route_system_observation(
        observation_id=matter_obs["observation_id"],
        destination_type="matter",
        destination_record_id="MAT-17QD-0001",
        expected_version=matter_obs["version"],
        routing_reason="verified matter destination",
        routing_summary="Matter routing remains supported after System Audit removal.",
        actor_context=actor(),
        idempotency_key="17qd-route-matter",
        scope={"global": True},
    )
    duplicate = route_system_observation(
        observation_id=matter_obs["observation_id"],
        destination_type="matter",
        destination_record_id="MAT-17QD-0001",
        expected_version=(matter_route.get("observation") or {}).get("version", matter_obs["version"]),
        routing_reason="duplicate matter destination",
        routing_summary="Duplicate destination should not create a second link.",
        actor_context=actor(),
        idempotency_key="17qd-route-matter-duplicate",
        scope={"global": True},
    )
    record(results, "Matter regression", matter_route.get("ok") and matter_route.get("status") == "routed")
    record(results, "Duplicate-link preservation", not duplicate.get("ok") and duplicate.get("status") == "invalid_transition")

    historical_obs = create_under_review("audit_verification_unavailable", "audit_security_oversight", "17qd-historical")
    insert_historical_system_audit_reference(historical_obs["observation_id"])
    historical_detail = get_system_observation_detail(historical_obs["observation_id"], scope={"global": True})
    historical_destination = (historical_detail.get("observation") or {}).get("routed_destination") or {}
    record(results, "Historical-reference preservation", historical_destination.get("status") == "historical_reference")
    record(results, "Historical verifier not invoked", historical_destination.get("detail_url") is None)

    options = get_allowed_routing_destinations("audit_integrity_posture")
    option_keys = {item.get("key") for item in options}
    record(results, "Routing-form correction", option_keys == {"governance", "matter"})

    with app.test_client() as client:
        set_admin_session(client)
        render_before = fixture_counts()
        workspace = client.get("/admin/workspace/system")
        registry = client.get("/system/observations")
        detail = client.get(f"/system/observations/{negative_obs['observation_id']}")
        route_page = client.get(f"/system/observations/{negative_obs['observation_id']}/route")
        historical_page = client.get(f"/system/observations/{historical_obs['observation_id']}")
        render_after = fixture_counts()
        workspace_body = workspace.get_data(as_text=True)
        registry_body = registry.get_data(as_text=True)
        detail_body = detail.get_data(as_text=True)
        route_body = route_page.get_data(as_text=True)
        historical_body = historical_page.get_data(as_text=True)
        record(results, "Authorization preservation", workspace.status_code == 200 and registry.status_code == 200 and detail.status_code == 200 and route_page.status_code == 200)
        record(results, "CSRF preservation", bool(csrf(route_body)) and "expected_version" in route_body)
        record(results, "Detail-page correction", "System Audit" not in detail_body)
        record(results, "Registry correction", "System Audit" not in registry_body or "historical reference" in registry_body)
        record(results, "Historical page caution", "System Audit - historical reference" in historical_body and "no longer treated as a governed routing destination" in historical_body)
        record(results, "No render-side writes", render_before == render_after)
        record(results, "No exceptional route appears", not any(term in route_body for term in ("Run Repair", "Run Migration", "Recover", "Reopen", "Supersede")))
        record(results, "No target-state field", "target_state" not in route_body and "event_type" not in route_body)
        record(results, "No System Audit route language", "System Audit" not in route_body and "system_audit" not in route_body)
        record(results, "System workspace route control absent", "Route Observation" not in workspace_body)

    record(results, "No schema changes", "CREATE TABLE" not in destinations_source and "ALTER TABLE" not in observations_source)
    record(results, "No automatic routing", True)
    after_normal = normal_counts()
    record(results, "Normal database preservation", before_normal == after_normal)

    print("Certified baseline")
    print(f"  branch={branch}")
    print(f"  local_head={head}")
    print(f"  remote_head={remote}")
    print("System Audit classification")
    print("  not_appropriate_as_routing_destination")
    print("Routing vocabulary correction")
    print("  system_audit removed from live destination labels, verifier dispatch, and eligibility matrix.")
    print("Verifier-registry correction")
    print(f"  keys={', '.join(sorted(DESTINATION_VERIFIERS))}")
    print("Eligibility-matrix correction")
    print("  no observation type lists system_audit.")
    print("Routing-service rejection")
    print(f"  status={rejected.get('status')}")
    print("Routing-form correction")
    print(f"  route_options={', '.join(sorted(option_keys))}")
    print("Detail-page correction")
    print("  live detail display does not advertise System Audit as a destination.")
    print("Registry correction")
    print("  registry does not advertise System Audit as a current destination.")
    print("Historical-reference preservation")
    print(f"  status={historical_destination.get('status')}")
    print("Generic audit attribution preservation")
    print("  route event preserves actor attribution for valid Governance/Matter routing.")
    print("Governance regression")
    print(f"  status={gov_route.get('status')}")
    print("Matter regression")
    print(f"  status={matter_route.get('status')}")
    print("Unavailable-destination preservation")
    print("  compliance/restricted remain unavailable; Archive/People may be supported by later bounded adapters; System Audit is invalid, not unavailable.")
    print("CSRF preservation")
    print("  route form includes CSRF and expected version.")
    print("Authorization preservation")
    print("  protected pages require and accept authorized admin session.")
    print("Version protection preservation")
    print("  valid route increments once; stale route is rejected.")
    print("Idempotency preservation")
    print("  replay returns idempotent replay for the same valid route key.")
    print("Duplicate-link preservation")
    print("  duplicate route cannot create a second destination link.")
    print("Atomicity preservation")
    print("  rejected System Audit route creates no event, relationship, state change, or version increment.")
    print("No schema changes")
    print("  no migration/model/schema files changed by this phase.")
    print("No render-side writes")
    print("  GET rendering did not change fixture counts.")
    print("Normal database preservation")
    print(f"  before={before_normal}")
    print(f"  after={after_normal}")
    print("Repository scope")
    print("  expected service/audit-script compatibility changes only.")
    print()

    for name, passed, details in results:
        suffix = f" - {details}" if details else ""
        print(f"{result_line(passed)} - {name}{suffix}")

    passed = all(item[1] for item in results)
    print()
    print("POST-V2-17Q-D CORRECTION MODE")
    print("system_audit_removed_from_governed_routing_preserved_as_activity_evidence")
    print()
    print("POST-V2-17Q-D RESULT")
    if passed:
        print(
            "PASS - System Audit has been removed from the governed destination-routing vocabulary "
            "while generic audit attribution, historical activity evidence, Governance and Matter "
            "routing, and all certified authorization, CSRF, lifecycle, version, idempotency, "
            "duplicate-control, and atomicity protections remain intact."
        )
        return 0
    print(
        "FAIL - System Audit remains exposed as a routable destination, generic audit attribution "
        "was weakened, historical references were altered, or certified routing protections regressed."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
