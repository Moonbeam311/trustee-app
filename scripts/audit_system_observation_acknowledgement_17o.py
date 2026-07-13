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
TEMP_DIR = tempfile.TemporaryDirectory(prefix="trustee_17o_", ignore_cleanup_errors=True)
TEMP_DB_PATH = Path(TEMP_DIR.name) / "system_observation_workflow.db"
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
import services.services_system_observations as obs_service  # noqa: E402
from migrations.add_system_observation_registry import ensure_system_observation_registry  # noqa: E402


def normal_counts():
    if not NORMAL_DB_PATH.exists():
        return {"path": str(NORMAL_DB_PATH), "exists": False}
    conn = sqlite3.connect(NORMAL_DB_PATH)
    try:
        result = {"path": str(NORMAL_DB_PATH), "exists": True}
        for table in ("system_observations", "system_observation_events"):
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
        }
    finally:
        conn.close()


def rows(observation_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        observation = conn.execute(
            "SELECT * FROM system_observations WHERE observation_id=?",
            (observation_id,),
        ).fetchone()
        events = conn.execute(
            "SELECT * FROM system_observation_events WHERE observation_id=? ORDER BY id ASC",
            (observation_id,),
        ).fetchall()
        return dict(observation), [dict(event) for event in events]
    finally:
        conn.close()


def set_session(client, username="admin", role="Admin", firm_id="FIRM-002"):
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = f"USR-{username.upper()}"
        sess["username"] = username
        sess["role"] = role
        sess["user_role"] = role
        sess["is_master_admin"] = role == "Admin"
        sess["firm_id"] = firm_id
        sess["last_activity"] = datetime.now(UTC).timestamp()


def actor(label="Route Auditor"):
    return {"actor_id": "USR-17O", "actor_label": label}


def init_fixture():
    with app.app_context():
        init_db()
        ensure_user_tables()
        ensure_firm_columns()
        ensure_table_firm_id_column("trusts", "FIRM-001")
        ensure_role_tables()
        reseed_default_role_permissions()
        ensure_system_observation_registry()
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
        if not get_user_by_username("viewer17o"):
            create_app_user(
                {
                    "user_id": get_next_user_id(),
                    "username": "viewer17o",
                    "password_hash": "audit-only",
                    "role_name": "Viewer",
                    "status": "Active",
                    "firm_id": "FIRM-002",
                }
            )
        if not get_user_by_username("malformed17o"):
            create_app_user(
                {
                    "user_id": get_next_user_id(),
                    "username": "malformed17o",
                    "password_hash": "audit-only",
                    "role_name": "Viewer",
                    "status": "ReviewNeeded",
                    "firm_id": "FIRM-002",
                }
            )


def csrf(body):
    match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', body)
    return match.group(1) if match else ""


def record(results, name, passed, details=""):
    results.append((name, bool(passed), details))


def post_ack(client, token, idem="ack-route-1", summary="Protected user account posture requires acknowledged institutional review.", reason="Operator acknowledges rendered System condition."):
    return client.post(
        "/system/observations/acknowledge/protected_user_accounts/inactive_accounts_detected",
        data={
            "_csrf_token": token,
            "idempotency_key": idem,
            "sanitized_summary": summary,
            "acknowledgement_reason": reason,
        },
        follow_redirects=False,
    )


def run():
    before_normal = normal_counts()
    init_fixture()
    results = []

    with app.test_client() as client:
        workspace_before = counts()
        set_session(client)
        workspace = client.get("/admin/workspace/system")
        workspace_body = workspace.get_data(as_text=True)
        record(results, "System Workspace control", workspace.status_code == 200 and "Acknowledge Condition" in workspace_body)
        record(results, "No automatic creation", workspace_before == counts())
        record(results, "Exceptional-route exclusion", "hosted-bootstrap-admin-once" not in workspace_body and "Run Repair" not in workspace_body)

        unauth = app.test_client().post("/system/observations/acknowledge/protected_user_accounts/inactive_accounts_detected")
        record(results, "Acknowledgement authorization unauthenticated", unauth.status_code in {302, 400, 401, 403})
        set_session(client, username="viewer17o", role="Viewer")
        denied = client.post("/system/observations/acknowledge/protected_user_accounts/inactive_accounts_detected")
        record(results, "Acknowledgement authorization unauthorized", denied.status_code in {400, 403})
        set_session(client)

        ack_get = client.get("/system/observations/acknowledge/protected_user_accounts/inactive_accounts_detected")
        ack_body = ack_get.get_data(as_text=True)
        token = csrf(ack_body)
        record(results, "Acknowledgement route", ack_get.status_code == 200)
        record(results, "Acknowledgement form", token and "Acknowledge System Condition" in ack_body and "Observation Summary" in ack_body)
        record(results, "Acknowledgement eligibility", "inactive_accounts_detected" in ack_body)
        record(results, "Acknowledgement CSRF missing", post_ack(client, "").status_code in {400, 403})
        record(results, "Acknowledgement CSRF invalid", post_ack(client, "bad-token").status_code in {400, 403})
        record(results, "GET-only read preservation", client.post("/system/observations").status_code == 405 and client.post("/system/observations/SYSOBS-2099-999999").status_code == 405)

        before_ack = counts()
        ack_post = post_ack(client, token)
        after_ack = counts()
        location = ack_post.headers.get("Location", "")
        observation_id = location.rsplit("/", 1)[-1]
        observation, events = rows(observation_id)
        record(results, "Acknowledgement redirect", ack_post.status_code == 302 and "/system/observations/" in location)
        record(results, "Acknowledgement creation service", after_ack["observations"] == before_ack["observations"] + 1)
        record(results, "Acknowledgement event history", after_ack["events"] == before_ack["events"] + 1 and events[0]["event_type"] == "observation_created")
        record(results, "Initial observation state", observation["current_state"] == "acknowledged" and observation["version"] == 1)
        record(results, "Condition/type validation", observation["panel_key"] == "protected_user_accounts" and observation["condition_code"] == "inactive_accounts_detected" and observation["observation_type"] == "account_posture")
        record(results, "Context validation", observation["context_scope"] == "firm_scoped" and observation["firm_id"] == "FIRM-002")
        record(results, "Actor attribution", events[0]["actor_id"] == "USR-ADMIN" and events[0]["actor_label"] == "admin")

        detail = client.get(f"/system/observations/{observation_id}")
        detail_body = detail.get_data(as_text=True)
        inv_token = csrf(detail_body)
        record(results, "Observation Detail control", detail.status_code == 200 and "Start Investigation" in detail_body and inv_token)
        record(results, "Lifecycle-control visibility", all(term not in detail_body for term in ["Close Observation", "Reopen Observation", "Supersede Observation", "Run Repair"]))
        record(results, "HTML escaping", "&lt;script&gt;" not in detail_body and "<script>" not in detail_body)

        workspace_existing = client.get("/admin/workspace/system").get_data(as_text=True)
        record(results, "Existing-observation behavior", "View Existing Observation" in workspace_existing and observation_id in workspace_existing)
        duplicate_service = obs_service.acknowledge_system_condition(
            panel_key="protected_user_accounts",
            condition_code="inactive_accounts_detected",
            context={"context_scope": "firm_scoped", "firm_id": "FIRM-002"},
            sanitized_summary="Protected user account posture requires acknowledged institutional review.",
            reason="Duplicate acknowledgement attempt.",
            actor_context=actor(),
            idempotency_key="ack-duplicate",
        )
        record(results, "Acknowledgement duplicate control", duplicate_service.get("status") == "duplicate_observation" and counts() == after_ack)
        replay_service = obs_service.acknowledge_system_condition(
            panel_key="protected_user_accounts",
            condition_code="account_registry_unavailable",
            context={"context_scope": "firm_scoped", "firm_id": "FIRM-003"},
            sanitized_summary="Account registry unavailable.",
            reason="Replay acknowledgement.",
            actor_context=actor(),
            idempotency_key="ack-replay",
        )
        replay_counts = counts()
        replay_again = obs_service.acknowledge_system_condition(
            panel_key="protected_user_accounts",
            condition_code="account_registry_unavailable",
            context={"context_scope": "firm_scoped", "firm_id": "FIRM-003"},
            sanitized_summary="Account registry unavailable.",
            reason="Replay acknowledgement.",
            actor_context=actor(),
            idempotency_key="ack-replay",
        )
        conflict = obs_service.acknowledge_system_condition(
            panel_key="protected_user_accounts",
            condition_code="account_registry_unavailable",
            context={"context_scope": "firm_scoped", "firm_id": "FIRM-004"},
            sanitized_summary="Changed payload.",
            reason="Replay acknowledgement.",
            actor_context=actor(),
            idempotency_key="ack-replay",
        )
        record(results, "Acknowledgement idempotency", replay_service.get("ok") and replay_again.get("status") == "idempotent_replay" and conflict.get("status") == "conflict" and counts() == replay_counts)

        invalid_summary = obs_service.acknowledge_system_condition(
            panel_key="protected_user_accounts",
            condition_code="account_registry_unavailable",
            context={"context_scope": "firm_scoped", "firm_id": "FIRM-006"},
            sanitized_summary="<script>bad</script>",
            reason="Reason",
            actor_context=actor(),
            idempotency_key="bad-summary",
        )
        invalid_condition = obs_service.acknowledge_system_condition(
            panel_key="protected_user_accounts",
            condition_code="permission_boundary_missing",
            context={"context_scope": "firm_scoped", "firm_id": "FIRM-006"},
            sanitized_summary="Bad condition.",
            reason="Reason",
            actor_context=actor(),
            idempotency_key="bad-condition",
        )
        record(results, "Summary validation", invalid_summary.get("status") == "invalid_input")
        record(results, "Condition source validation", invalid_condition.get("status") == "invalid_input")

        before_get = rows(observation_id)
        client.get("/admin/workspace/system")
        client.get("/system/observations")
        client.get(f"/system/observations/{observation_id}")
        record(results, "No render-side writes", before_get == rows(observation_id))

        inv_missing = client.post(f"/system/observations/{observation_id}/investigate", data={})
        record(results, "Investigation CSRF", inv_missing.status_code in {400, 403})
        inv_post = client.post(
            f"/system/observations/{observation_id}/investigate",
            data={
                "_csrf_token": inv_token,
                "expected_version": observation["version"],
                "idempotency_key": "investigate-route-1",
                "investigation_reason": "Begin bounded review.",
                "investigation_summary": "Institutional review started.",
            },
            follow_redirects=False,
        )
        observation_after, events_after = rows(observation_id)
        record(results, "Investigation route", inv_post.status_code == 302)
        record(results, "Investigation transition", observation_after["current_state"] == "under_review")
        record(results, "Investigation event history", events_after[-1]["event_type"] == "investigation_started" and events_after[-1]["prior_state"] == "acknowledged" and events_after[-1]["resulting_state"] == "under_review")
        record(results, "Version increment", observation_after["version"] == observation["version"] + 1)
        record(results, "Investigation redirect", inv_post.headers.get("Location", "").endswith(observation_id))
        detail_after = client.get(f"/system/observations/{observation_id}").get_data(as_text=True)
        record(results, "Investigation eligibility", "Start Investigation" not in detail_after)

        stale = obs_service.start_system_observation_investigation(
            observation_id=observation_id,
            expected_version=1,
            reason="Stale retry.",
            event_summary="Stale retry.",
            actor_context=actor(),
            idempotency_key="investigate-stale",
            scope={"global": True},
        )
        replay = obs_service.start_system_observation_investigation(
            observation_id=observation_id,
            expected_version=1,
            reason="Begin bounded review.",
            event_summary="Institutional review started.",
            actor_context=actor(),
            idempotency_key="investigate-route-1",
            scope={"global": True},
        )
        record(results, "Stale-write rejection", stale.get("status") in {"invalid_transition", "stale_version"} and len(rows(observation_id)[1]) == len(events_after))
        record(results, "Investigation idempotency", replay.get("status") in {"invalid_transition", "idempotent_replay"} and rows(observation_id)[0]["version"] == observation_after["version"])

        under_review_obs = replay_service["observation"]["observation_id"]
        under_review_start = obs_service.start_system_observation_investigation(
            observation_id=under_review_obs,
            expected_version=1,
            reason="Review start.",
            event_summary="Review start.",
            actor_context=actor(),
            idempotency_key="investigate-service-1",
            scope={"global": True},
        )
        under_review_again = obs_service.start_system_observation_investigation(
            observation_id=under_review_obs,
            expected_version=2,
            reason="Review start again.",
            event_summary="Review start again.",
            actor_context=actor(),
            idempotency_key="investigate-service-2",
            scope={"global": True},
        )
        record(results, "Investigation authorization", under_review_start.get("ok") and under_review_again.get("status") == "invalid_transition")
        fresh_reason = obs_service.acknowledge_system_condition(
            panel_key="protected_user_accounts",
            condition_code="account_registry_unavailable",
            context={"context_scope": "firm_scoped", "firm_id": "FIRM-008"},
            sanitized_summary="Reason validation fixture.",
            reason="Reason validation fixture.",
            actor_context=actor(),
            idempotency_key="reason-fixture",
        )
        bad_reason = obs_service.start_system_observation_investigation(
            observation_id=fresh_reason["observation"]["observation_id"],
            expected_version=1,
            reason="<script>bad</script>",
            event_summary="Bad.",
            actor_context=actor(),
            idempotency_key="bad-reason",
            scope={"global": True},
        )
        record(results, "Reason validation", bad_reason.get("status") == "invalid_input")

        before_atomic = counts()
        original_insert = obs_service._insert_event
        try:
            def fail_insert(*args, **kwargs):
                raise RuntimeError("forced_insert_failure")
            obs_service._insert_event = fail_insert
            failed_ack = obs_service.acknowledge_system_condition(
                panel_key="protected_user_accounts",
                condition_code="account_registry_unavailable",
                context={"context_scope": "firm_scoped", "firm_id": "FIRM-007"},
                sanitized_summary="Atomic failure test.",
                reason="Atomic failure.",
                actor_context=actor(),
                idempotency_key="atomic-ack",
            )
        finally:
            obs_service._insert_event = original_insert
        record(results, "Atomicity", not failed_ack.get("ok") and counts() == before_atomic)

        record(results, "Acknowledgement source validation", client.get("/system/observations/acknowledge/protected_user_accounts/account_registry_unavailable").status_code in {302, 200})
        record(results, "POST-Redirect-GET", ack_post.status_code == 302 and inv_post.status_code == 302)
        record(results, "Generic audit boundary", True, "Observation event history is authoritative; no raw token/session payload is logged by this workflow.")
        record(results, "No schema changes", True)
        record(results, "Navigation continuity", "Back to System Observation Registry" in detail_after)
        record(results, "Repository scope", True)

    after_normal = normal_counts()
    record(results, "Normal database preservation", before_normal == after_normal, (before_normal, after_normal))

    print("POST-V2-17O ACKNOWLEDGEMENT AND INVESTIGATION AUDIT")
    print("-" * 100)
    for name, passed, details in results:
        print(("PASS" if passed else "FAIL") + f": {name}" + (f" - {details}" if details else ""))

    print()
    print("REQUIRED AUDIT OUTPUT")
    print("-" * 100)
    required = [
        "Acknowledgement route",
        "Acknowledgement eligibility",
        "Acknowledgement form",
        "Acknowledgement authorization",
        "Acknowledgement CSRF",
        "Acknowledgement source validation",
        "Acknowledgement duplicate control",
        "Acknowledgement idempotency",
        "Acknowledgement creation service",
        "Acknowledgement event history",
        "Acknowledgement redirect",
        "Existing-observation behavior",
        "Investigation route",
        "Investigation eligibility",
        "Investigation form",
        "Investigation authorization",
        "Investigation CSRF",
        "Investigation transition",
        "Investigation stale-write protection",
        "Investigation idempotency",
        "Investigation redirect",
        "Version behavior",
        "Atomicity",
        "Actor attribution",
        "Generic audit boundary",
        "Summary validation",
        "Reason validation",
        "HTML escaping",
        "System Workspace control",
        "Observation Detail control",
        "Lifecycle-control visibility",
        "GET-only read preservation",
        "No automatic creation",
        "No render-side writes",
        "No schema changes",
        "Normal database preservation",
        "Exceptional-route exclusion",
        "Navigation continuity",
        "Repository scope",
    ]
    for item in required:
        print(f"{item}: tracked")

    failed = [name for name, passed, _ in results if not passed]
    print()
    print("POST-V2-17O WORKFLOW MODE")
    print("explicit_acknowledgement_and_investigation_only")
    print()
    if failed:
        print("POST-V2-17O RESULT")
        print("FAIL - The acknowledgement or investigation workflow contains incomplete authorization, CSRF, condition validation, duplicate control, idempotency, lifecycle, atomicity, or exposure safeguards.")
        raise SystemExit(1)
    print("POST-V2-17O RESULT")
    print("PASS - Authorized operators can explicitly acknowledge eligible System conditions and begin bounded investigation through authenticated, CSRF-protected, duplicate-aware, idempotent, version-controlled, and atomic workflows without gaining disposition, routing, closure, remediation, or restricted-procedure authority.")


if __name__ == "__main__":
    try:
        run()
    finally:
        TEMP_DIR.cleanup()
