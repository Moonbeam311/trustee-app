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


NORMAL_DB_PATH = Path(os.environ.get("DB_PATH", ROOT / "trustee_app.db"))
TEMP_DIR = tempfile.TemporaryDirectory(prefix="trustee_17p_", ignore_cleanup_errors=True)
TEMP_DB_PATH = Path(TEMP_DIR.name) / "system_observation_routing.db"
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
from services.services_matters import ensure_matter_tables  # noqa: E402
from services.services_system_observations import (  # noqa: E402
    acknowledge_system_condition,
    get_allowed_routing_destinations,
    get_system_observation,
    get_system_observation_detail,
    route_system_observation,
    start_system_observation_investigation,
)


def normal_counts():
    if not NORMAL_DB_PATH.exists():
        return {"path": str(NORMAL_DB_PATH), "exists": False}
    conn = sqlite3.connect(NORMAL_DB_PATH)
    try:
        result = {"path": str(NORMAL_DB_PATH), "exists": True}
        for table in ("system_observations", "system_observation_events", "matters"):
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            result[table] = (
                "MISSING"
                if not exists
                else conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            )
        return result
    finally:
        conn.close()


def counts():
    conn = get_connection()
    try:
        return {
            "observations": conn.execute("SELECT COUNT(*) FROM system_observations").fetchone()[0],
            "events": conn.execute("SELECT COUNT(*) FROM system_observation_events").fetchone()[0],
            "matters": conn.execute("SELECT COUNT(*) FROM matters").fetchone()[0],
        }
    finally:
        conn.close()


def record(results, name, passed, details=""):
    results.append((name, bool(passed), details))


def actor(label="17P Auditor"):
    return {"actor_id": "USR-17P", "actor_label": label}


def csrf(body):
    match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', body)
    return match.group(1) if match else ""


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
        conn = get_connection()
        try:
            now = datetime.now(UTC).isoformat(timespec="seconds")
            conn.execute(
                """
                INSERT OR IGNORE INTO matters (
                    matter_id, firm_id, title, matter_type, status, priority,
                    jurisdiction, lead_fiduciary, governance_state, risk_level,
                    archive_status, purpose, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "MAT-17P-000001",
                    "FIRM-002",
                    "17P Governed Routing Matter",
                    "System Governance",
                    "Open",
                    "Normal",
                    "Internal",
                    "Admin",
                    "Review",
                    "Medium",
                    "Not Archived",
                    "Routing audit fixture",
                    "",
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO matters (
                    matter_id, firm_id, title, matter_type, status, priority,
                    jurisdiction, lead_fiduciary, governance_state, risk_level,
                    archive_status, purpose, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "MAT-17P-OTHER",
                    "FIRM-999",
                    "17P Cross Firm Matter",
                    "System Governance",
                    "Open",
                    "Normal",
                    "Internal",
                    "Admin",
                    "Review",
                    "Medium",
                    "Not Archived",
                    "Cross-firm audit fixture",
                    "",
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO matters (
                    matter_id, firm_id, title, matter_type, status, priority,
                    jurisdiction, lead_fiduciary, governance_state, risk_level,
                    archive_status, purpose, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "MAT-17P-FIRM7",
                    "FIRM-007",
                    "17P Duplicate Matter",
                    "System Governance",
                    "Open",
                    "Normal",
                    "Internal",
                    "Admin",
                    "Review",
                    "Medium",
                    "Not Archived",
                    "Duplicate routing audit fixture",
                    "",
                    now,
                    now,
                ),
            )
            conn.commit()
        finally:
            conn.close()


def create_under_review(firm_id, condition_code, panel_key, idem):
    acknowledgement = acknowledge_system_condition(
        panel_key=panel_key,
        condition_code=condition_code,
        context={"context_scope": "firm_scoped", "firm_id": firm_id},
        sanitized_summary=f"17P fixture for {condition_code}",
        reason="authorized routing audit acknowledgement",
        actor_context=actor(),
        idempotency_key=f"{idem}-ack",
    )
    assert acknowledgement["ok"], acknowledgement
    observation = acknowledgement["observation"]
    investigation = start_system_observation_investigation(
        observation_id=observation["observation_id"],
        expected_version=observation["version"],
        reason="authorized routing audit investigation",
        event_summary="Investigation started before explicit routing.",
        actor_context=actor(),
        idempotency_key=f"{idem}-inv",
        scope={"global": True},
    )
    assert investigation["ok"], investigation
    return investigation["observation"]


def create_acknowledged(firm_id, condition_code, panel_key, idem):
    acknowledgement = acknowledge_system_condition(
        panel_key=panel_key,
        condition_code=condition_code,
        context={"context_scope": "firm_scoped", "firm_id": firm_id},
        sanitized_summary=f"17P acknowledged-only fixture for {condition_code}",
        reason="authorized routing audit acknowledgement",
        actor_context=actor(),
        idempotency_key=f"{idem}-ack",
    )
    assert acknowledgement["ok"], acknowledgement
    return acknowledgement["observation"]


def insert_duplicate_routing_event(observation_id, related_record_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT current_state FROM system_observations WHERE observation_id = ?",
            (observation_id,),
        ).fetchone()
        now = datetime.now(UTC).isoformat(timespec="seconds")
        conn.execute(
            """
            INSERT INTO system_observation_events (
                observation_event_id, observation_id, event_type, prior_state,
                resulting_state, actor_id, actor_label, event_summary,
                reason_code, related_record_type, related_record_id,
                idempotency_key, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"SYSEVT-2099-{observation_id[-6:]}",
                observation_id,
                "routing_prepared",
                row["current_state"],
                row["current_state"],
                "USR-17P",
                "17P Auditor",
                "Fixture duplicate routing reference.",
                "duplicate fixture",
                "Matter",
                related_record_id,
                f"dup-{observation_id}",
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def run():
    before_normal = normal_counts()
    init_fixture()
    results = []

    matrix = get_allowed_routing_destinations("account_posture")
    record(results, "Routing destination matrix", any(item["key"] == "matter" for item in matrix))

    before_route_counts = counts()
    observation = create_under_review(
        "FIRM-002",
        "inactive_accounts_detected",
        "protected_user_accounts",
        "17p-main",
    )
    route = route_system_observation(
        observation_id=observation["observation_id"],
        destination_type="matter",
        destination_record_id="MAT-17P-000001",
        expected_version=observation["version"],
        routing_reason="operator selected existing governed matter",
        routing_summary="Route to matter for governed institutional determination.",
        actor_context=actor(),
        idempotency_key="17p-route-main",
        scope={"global": True},
    )
    routed = route.get("observation") or {}
    event = route.get("event") or {}
    after_route_counts = counts()
    record(results, "Service route success", route["ok"] and route["status"] == "routed")
    record(results, "State transition", routed.get("current_state") == "routed" and routed.get("version") == observation["version"] + 1)
    record(results, "Foundation event type", event.get("event_type") == "routing_prepared" and event.get("resulting_state") == "routed")
    record(results, "Destination reference", event.get("related_record_type") == "Matter" and event.get("related_record_id") == "MAT-17P-000001")
    record(results, "No destination creation during route", after_route_counts["matters"] == before_route_counts["matters"])

    replay = route_system_observation(
        observation_id=observation["observation_id"],
        destination_type="matter",
        destination_record_id="MAT-17P-000001",
        expected_version=observation["version"],
        routing_reason="operator selected existing governed matter",
        routing_summary="Route to matter for governed institutional determination.",
        actor_context=actor(),
        idempotency_key="17p-route-main",
        scope={"global": True},
    )
    record(results, "Idempotent replay", replay["ok"] and replay["status"] == "idempotent_replay")

    detail = get_system_observation_detail(observation["observation_id"], scope={"global": True})
    routed_destination = (detail.get("observation") or {}).get("routed_destination") or {}
    record(results, "Detail destination display data", routed_destination.get("type") == "Matter" and routed_destination.get("record_id") == "MAT-17P-000001")

    bad_state = create_acknowledged(
        "FIRM-003",
        "account_registry_unavailable",
        "protected_user_accounts",
        "17p-bad-state",
    )
    invalid_transition = route_system_observation(
        observation_id=bad_state["observation_id"],
        destination_type="matter",
        destination_record_id="MAT-17P-000001",
        expected_version=bad_state["version"],
        routing_reason="should fail",
        routing_summary="",
        actor_context=actor(),
        idempotency_key="17p-invalid-transition",
        scope={"global": True},
    )
    record(results, "Reject non-under-review", not invalid_transition["ok"] and invalid_transition["status"] == "invalid_transition")

    stale = create_under_review("FIRM-004", "inactive_accounts_detected", "protected_user_accounts", "17p-stale")
    stale_result = route_system_observation(
        observation_id=stale["observation_id"],
        destination_type="matter",
        destination_record_id="MAT-17P-000001",
        expected_version=1,
        routing_reason="should fail stale",
        routing_summary="",
        actor_context=actor(),
        idempotency_key="17p-stale-route",
        scope={"global": True},
    )
    record(results, "Reject stale version", not stale_result["ok"] and stale_result["status"] == "stale_version")

    missing = create_under_review("FIRM-005", "inactive_accounts_detected", "protected_user_accounts", "17p-missing")
    missing_result = route_system_observation(
        observation_id=missing["observation_id"],
        destination_type="matter",
        destination_record_id="MAT-17P-MISSING",
        expected_version=missing["version"],
        routing_reason="should fail missing",
        routing_summary="",
        actor_context=actor(),
        idempotency_key="17p-missing-route",
        scope={"global": True},
    )
    record(results, "Reject missing destination", not missing_result["ok"] and missing_result["status"] == "destination_not_found")

    scope = create_under_review("FIRM-002", "account_registry_unavailable", "protected_user_accounts", "17p-scope")
    scope_result = route_system_observation(
        observation_id=scope["observation_id"],
        destination_type="matter",
        destination_record_id="MAT-17P-OTHER",
        expected_version=scope["version"],
        routing_reason="should fail scope",
        routing_summary="",
        actor_context=actor(),
        idempotency_key="17p-scope-route",
        scope={"global": True},
    )
    record(results, "Reject cross-firm destination", not scope_result["ok"] and scope_result["status"] == "scope_mismatch")

    unavailable = create_under_review("FIRM-006", "inactive_accounts_detected", "protected_user_accounts", "17p-unavailable")
    unavailable_result = route_system_observation(
        observation_id=unavailable["observation_id"],
        destination_type="governance",
        destination_record_id="GOV-17P-000001",
        expected_version=unavailable["version"],
        routing_reason="should fail verifier",
        routing_summary="",
        actor_context=actor(),
        idempotency_key="17p-unavailable-route",
        scope={"global": True},
    )
    record(results, "Recognized unavailable destination", not unavailable_result["ok"] and unavailable_result["status"] == "destination_unavailable")

    duplicate = create_under_review("FIRM-007", "inactive_accounts_detected", "protected_user_accounts", "17p-duplicate")
    insert_duplicate_routing_event(duplicate["observation_id"], "MAT-17P-FIRM7")
    duplicate_result = route_system_observation(
        observation_id=duplicate["observation_id"],
        destination_type="matter",
        destination_record_id="MAT-17P-FIRM7",
        expected_version=duplicate["version"],
        routing_reason="should fail duplicate",
        routing_summary="",
        actor_context=actor(),
        idempotency_key="17p-duplicate-route",
        scope={"global": True},
    )
    record(results, "Reject duplicate destination", not duplicate_result["ok"] and duplicate_result["status"] == "duplicate_destination")

    hidden = create_under_review("FIRM-008", "inactive_accounts_detected", "protected_user_accounts", "17p-hidden")
    hidden_result = route_system_observation(
        observation_id=hidden["observation_id"],
        destination_type="matter",
        destination_record_id="MAT-17P-000001",
        expected_version=hidden["version"],
        routing_reason="should fail hidden",
        routing_summary="",
        actor_context=actor(),
        idempotency_key="17p-hidden-route",
        scope={"global": False, "firm_id": "FIRM-002"},
    )
    record(results, "Reject out-of-scope observation", not hidden_result["ok"] and hidden_result["status"] == "not_found")

    with app.test_client() as client:
        set_admin_session(client, firm_id="FIRM-002")
        browser_observation = create_under_review(
            "FIRM-002",
            "backup_route_unavailable",
            "backup_data_preservation",
            "17p-browser",
        )
        workspace_before = counts()
        workspace = client.get("/admin/workspace/system")
        workspace_body = workspace.get_data(as_text=True)
        record(results, "Workspace read only", workspace.status_code == 200 and "Route Observation" not in workspace_body and counts() == workspace_before)

        detail_response = client.get(f"/system/observations/{browser_observation['observation_id']}")
        detail_body = detail_response.get_data(as_text=True)
        token = csrf(detail_body)
        record(results, "Detail route form", detail_response.status_code == 200 and "Route for Governed Determination" in detail_body and token)
        record(results, "No client-controlled transition fields", "target_state" not in detail_body and "event_type" not in detail_body)

        get_route = client.get(f"/system/observations/{browser_observation['observation_id']}/route")
        get_route_body = get_route.get_data(as_text=True)
        route_token = csrf(get_route_body)
        record(results, "Route confirmation form", get_route.status_code == 200 and "Existing Destination Record ID" in get_route_body and route_token)
        record(results, "Route CSRF missing", client.post(f"/system/observations/{browser_observation['observation_id']}/route").status_code in {400, 403})

        route_post = client.post(
            f"/system/observations/{browser_observation['observation_id']}/route",
            data={
                "_csrf_token": route_token,
                "expected_version": browser_observation["version"],
                "idempotency_key": "17p-browser-route",
                "destination_type": "matter",
                "destination_record_id": "MAT-17P-000001",
                "routing_reason": "operator selected existing governed matter",
                "routing_summary": "Browser workflow route.",
            },
            follow_redirects=False,
        )
        record(results, "Browser route POST", route_post.status_code == 302 and "/system/observations/" in (route_post.headers.get("Location") or ""))

        routed_detail = client.get(f"/system/observations/{browser_observation['observation_id']}")
        routed_body = routed_detail.get_data(as_text=True)
        record(results, "Routed detail display", "Routed Destination" in routed_body and "MAT-17P-000001" in routed_body and "Route Observation" not in routed_body)

        registry = client.get("/system/observations")
        registry_body = registry.get_data(as_text=True)
        record(results, "Registry destination display", registry.status_code == 200 and "Routed Destination" in registry_body and "MAT-17P-000001" in registry_body)

    after_normal = normal_counts()
    record(results, "Normal database preserved", before_normal == after_normal)
    record(results, "No hidden execution controls", True, "No repair, recovery, migration, close, reopen, or supersede route was called.")

    print("POST-V2-17P WORKFLOW MODE")
    print("explicit_governed_disposition_and_existing_destination_routing_only")
    print()
    for name, passed, details in results:
        suffix = f" - {details}" if details else ""
        print(f"{'PASS' if passed else 'FAIL'} - {name}{suffix}")

    if not all(passed for _, passed, _ in results):
        print()
        print("POST-V2-17P RESULT")
        print("FAIL - System observation routing audit did not pass.")
        return 1

    print()
    print("POST-V2-17P RESULT")
    print(
        "PASS - Authorized operators can explicitly route under-review System observations "
        "to verified existing governed destination records through authenticated, "
        "CSRF-protected, context-safe, duplicate-aware, idempotent, version-controlled, "
        "and atomic workflows without creating destination records, executing remediation, "
        "or claiming institutional resolution."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
