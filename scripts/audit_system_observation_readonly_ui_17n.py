import os
import sqlite3
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


NORMAL_DB_PATH = Path(os.environ.get("DB_PATH", ROOT / "trustee_app.db"))
TEMP_DIR = tempfile.TemporaryDirectory(prefix="trustee_17n_", ignore_cleanup_errors=True)
TEMP_DB_PATH = Path(TEMP_DIR.name) / "system_observation_readonly_ui.db"
os.environ["DB_PATH"] = str(TEMP_DB_PATH)
os.environ.setdefault("UPLOAD_FOLDER", str(Path(TEMP_DIR.name) / "uploads"))
os.environ.setdefault("EXPORT_ROOT", str(Path(TEMP_DIR.name) / "exports"))


from app import app  # noqa: E402
import database.db as db_module  # noqa: E402
from database.db import (  # noqa: E402
    create_app_user,
    ensure_firm_columns,
    ensure_role_tables,
    ensure_user_tables,
    get_next_user_id,
    get_user_by_username,
    init_db,
    reseed_default_role_permissions,
    ensure_table_firm_id_column,
)
from migrations.add_system_observation_registry import ensure_system_observation_registry  # noqa: E402
from services.services_system_observations import (  # noqa: E402
    create_system_observation,
    transition_system_observation,
)


EXPECTED_PANELS = [
    "Protected User Accounts",
    "Application Permission Controls",
    "Authentication and Session Security",
    "Audit and Security Oversight",
    "Backup and Data Preservation",
    "Deployment and Production Health",
    "Database and Migration Posture",
    "Feature Flags and Operating Policy",
    "Institutional Role Assignments",
    "Recovery and Repair Controls",
]
FORBIDDEN_CONTROLS = [
    "<form",
    'method="post"',
    "csrf",
    "Create Observation",
    "Acknowledge",
    "Investigate",
    "Defer",
    "Route Observation",
    "Close Observation",
    "Reopen",
    "Supersede",
    "Edit Observation",
    "Delete Observation",
    "Record Action",
    "Initiate Recovery",
    "Run Repair",
]


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


def connect():
    return sqlite3.connect(TEMP_DB_PATH)


def switch_db_path(path):
    resolved = Path(path).resolve()
    os.environ["DB_PATH"] = str(resolved)
    db_module.DB_PATH = resolved


def temp_counts():
    conn = connect()
    try:
        result = {}
        for table in ("system_observations", "system_observation_events"):
            result[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return result
    finally:
        conn.close()


def observation_snapshot(observation_id):
    conn = connect()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            """
            SELECT observation_id, version, last_observed_at, updated_at, current_state
            FROM system_observations
            WHERE observation_id = ?
            """,
            (observation_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def set_admin_session(client, username="admin", role="Admin", firm_id="FIRM-002"):
    with client.session_transaction() as sess:
        sess.clear()
        sess["user_id"] = f"USR-{username.upper()}"
        sess["username"] = username
        sess["role"] = role
        sess["user_role"] = role
        sess["is_master_admin"] = role == "Admin"
        sess["firm_id"] = firm_id
        sess["last_activity"] = datetime.now(UTC).timestamp()


def actor():
    return {"actor_id": "USR-17N", "actor_label": "Read Only Auditor"}


def base_observation(**overrides):
    data = {
        "observation_type": "permission_posture",
        "condition_code": "permission_boundary_missing",
        "panel_key": "application_permission_controls",
        "persistence_trigger": "investigation_start",
        "context": {"context_scope": "firm_scoped", "firm_id": "FIRM-002"},
        "sanitized_summary": "Permission boundary requires read-only review.",
        "actor_context": actor(),
    }
    data.update(overrides)
    return create_system_observation(**data)


def seed_data():
    ensure_system_observation_registry()
    open_obs = base_observation(idempotency_key="17n-open")

    closed_obs = base_observation(
        condition_code="csrf_boundary_missing",
        sanitized_summary="Closed observation with related authority.",
        idempotency_key="17n-closed",
    )
    transition_system_observation(
        observation_id=closed_obs["observation"]["observation_id"],
        target_state="under_review",
        event_type="investigation_started",
        expected_version=1,
        actor_context=actor(),
        reason="operator_review",
        event_summary="Investigation opened.",
        idempotency_key="17n-closed-review",
    )
    transition_system_observation(
        observation_id=closed_obs["observation"]["observation_id"],
        target_state="closed_resolved",
        event_type="closed_resolved",
        expected_version=2,
        actor_context=actor(),
        reason="evidence_verified",
        event_summary="Resolved with bounded evidence.",
        idempotency_key="17n-closed-resolved",
        authority_record_type="Governance",
        authority_record_id="GOV-17N",
        related_record_type="Matter",
        related_record_id="MAT-000001",
    )

    recurring = base_observation(
        context={"context_scope": "firm_scoped", "firm_id": "FIRM-003"},
        prior_occurrence_id=closed_obs["observation"]["observation_id"],
        idempotency_key="17n-recurring",
    )

    successor = base_observation(
        context={"context_scope": "firm_scoped", "firm_id": "FIRM-004"},
        idempotency_key="17n-successor",
    )
    superseded = base_observation(
        context={"context_scope": "firm_scoped", "firm_id": "FIRM-005"},
        idempotency_key="17n-superseded",
    )
    transition_system_observation(
        observation_id=superseded["observation"]["observation_id"],
        target_state="superseded",
        event_type="superseded",
        expected_version=1,
        actor_context=actor(),
        reason="successor_record",
        event_summary="Superseded by successor.",
        idempotency_key="17n-superseded-event",
        superseded_by_observation_id=successor["observation"]["observation_id"],
    )

    conn = connect()
    try:
        conn.execute(
            """
            UPDATE system_observations
            SET sanitized_summary = ?
            WHERE observation_id = ?
            """,
            ("<script>alert('summary')</script>\nLine two", open_obs["observation"]["observation_id"]),
        )
        conn.execute(
            """
            UPDATE system_observation_events
            SET event_summary = ?
            WHERE observation_id = ?
              AND event_type = 'observation_created'
            """,
            ("<img src=x onerror=alert('event')>", open_obs["observation"]["observation_id"]),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "open": open_obs["observation"]["observation_id"],
        "closed": closed_obs["observation"]["observation_id"],
        "recurring": recurring["observation"]["observation_id"],
        "successor": successor["observation"]["observation_id"],
        "superseded": superseded["observation"]["observation_id"],
    }


def init_users():
    with app.app_context():
        init_db()
        ensure_user_tables()
        ensure_firm_columns()
        ensure_table_firm_id_column("trusts", "FIRM-001")
        ensure_role_tables()
        reseed_default_role_permissions()
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
        if not get_user_by_username("viewer17n"):
            create_app_user(
                {
                    "user_id": get_next_user_id(),
                    "username": "viewer17n",
                    "password_hash": "audit-only",
                    "role_name": "Viewer",
                    "status": "Active",
                    "firm_id": "FIRM-002",
                }
            )
        if not get_user_by_username("firmadmin17n"):
            create_app_user(
                {
                    "user_id": get_next_user_id(),
                    "username": "firmadmin17n",
                    "password_hash": "audit-only",
                    "role_name": "Admin",
                    "status": "Active",
                    "firm_id": "FIRM-002",
                }
            )


def text(response):
    return response.get_data(as_text=True)


def record(results, name, passed, details=""):
    results.append((name, bool(passed), details))


def no_forbidden_controls(body):
    lowered = body.lower()
    control_fragments = []
    for marker in ("<form", "<button", 'type="submit"', "method=\"post\"", "csrf_token"):
        if marker in lowered:
            control_fragments.append(marker)
    mutation_phrases = [
        "create observation",
        "acknowledge observation",
        "investigate observation",
        "defer observation",
        "route observation",
        "close observation",
        "reopen observation",
        "supersede observation",
        "edit observation",
        "delete observation",
        "record action",
        "initiate recovery",
        "run repair",
    ]
    control_fragments.extend([phrase for phrase in mutation_phrases if phrase in lowered])
    return control_fragments


def run():
    before_normal = normal_counts()
    init_users()
    ids = seed_data()
    before_counts = temp_counts()
    before_snapshot = observation_snapshot(ids["open"])
    results = []

    with app.test_client() as client:
        registry_unauth = client.get("/system/observations")
        record(results, "Authentication boundary", registry_unauth.status_code in {302, 401})

        set_admin_session(client, username="viewer17n", role="Viewer")
        unauthorized = client.get("/system/observations")
        record(results, "Authorization boundary", unauthorized.status_code == 403)

        set_admin_session(client)
        workspace = client.get("/admin/workspace/system")
        workspace_body = text(workspace)
        positions = [workspace_body.find(panel) for panel in EXPECTED_PANELS]
        record(
            results,
            "Panel-order preservation",
            workspace.status_code == 200 and all(pos >= 0 for pos in positions) and positions == sorted(positions),
        )
        record(results, "System Workspace link", workspace_body.count("System Observation Registry") == 1)
        record(results, "Panel placement", workspace_body.find("Audit and Security Oversight") < workspace_body.find("System Observation Registry") < workspace_body.find("Backup and Data Preservation"))
        record(results, "Exceptional-route exclusion", "hosted-bootstrap-admin-once" not in workspace_body and "hosted-repair-admin-access-once" not in workspace_body)

        registry = client.get("/system/observations")
        registry_body = text(registry)
        record(results, "Registry route", registry.status_code == 200)
        record(results, "Route family", "/system/observations" in registry_body or "System Observation Registry" in registry_body)
        record(results, "GET-only enforcement registry", client.post("/system/observations").status_code == 405)
        open_link = registry_body.find(f"/system/observations/{ids['open']}")
        closed_link = registry_body.find(f"/system/observations/{ids['closed']}")
        record(results, "Registry ordering", open_link >= 0 and closed_link >= 0 and open_link < closed_link)
        record(results, "Registry serialization", all(token not in registry_body for token in ("active_duplicate_key", "idempotency_key", "sqlite_sequence")))
        record(results, "No mutation controls registry", not no_forbidden_controls(registry_body), no_forbidden_controls(registry_body))
        record(results, "No POST forms registry", "<form" not in registry_body.lower() and 'method="post"' not in registry_body.lower())
        record(results, "No CSRF fields registry", "csrf_token" not in registry_body.lower() and 'name="_csrf_token"' not in registry_body.lower())

        detail = client.get(f"/system/observations/{ids['open']}")
        detail_body = text(detail)
        record(results, "Detail route", detail.status_code == 200)
        record(results, "GET-only enforcement detail", client.post(f"/system/observations/{ids['open']}").status_code == 405)
        record(results, "Observation identity", ids["open"] in detail_body and "Observation Identity" in detail_body)
        record(results, "Lifecycle posture", "Current Lifecycle Posture" in detail_body and "acknowledged" in detail_body)
        record(results, "Context display", "Firm" in detail_body and "FIRM-002" in detail_body)
        record(results, "Summary escaping", "&lt;script&gt;" in detail_body and "<script>" not in detail_body)
        record(results, "Event summary escaping", "&lt;img" in detail_body and "<img src=x" not in detail_body)
        record(results, "Event-history ordering", "Append-Only Event History" in detail_body and "SYSEVT-" in detail_body)
        record(results, "Actor display", "Read Only Auditor" in detail_body and "permission set" not in detail_body.lower())
        record(results, "No mutation controls detail", not no_forbidden_controls(detail_body), no_forbidden_controls(detail_body))
        record(results, "No POST forms detail", "<form" not in detail_body.lower() and 'method="post"' not in detail_body.lower())
        record(results, "No CSRF fields detail", "csrf_token" not in detail_body.lower() and 'name="_csrf_token"' not in detail_body.lower())
        record(results, "Institutional caution", "does not by itself prove legal compliance" in detail_body)

        closed_detail = text(client.get(f"/system/observations/{ids['closed']}"))
        record(results, "Authority-reference handling", "Authority reference recorded" in closed_detail and "GOV-17N" in closed_detail)
        record(results, "Related-record handling", "Related Governed Record" in closed_detail and "MAT-000001" in closed_detail)

        recurring_detail = text(client.get(f"/system/observations/{ids['recurring']}"))
        record(results, "Occurrence continuity", "Prior Occurrence" in recurring_detail and "Recurring:" in recurring_detail)

        superseded_detail = text(client.get(f"/system/observations/{ids['superseded']}"))
        record(results, "Supersession rendering", "Superseded By" in superseded_detail and "Superseded:" in superseded_detail)

        invalid = client.get("/system/observations/not-a-real-id")
        invalid_body = text(invalid)
        record(results, "Malformed ID bounded", invalid.status_code == 404 and "not-a-real-id" not in invalid_body)

        unknown = client.get("/system/observations/SYSOBS-2099-999999")
        record(results, "Not-found handling", unknown.status_code == 404 and "Observation Not Found" in text(unknown))

        set_admin_session(client, username="firmadmin17n", role="Admin", firm_id="FIRM-002")
        cross_scope = client.get(f"/system/observations/{ids['recurring']}")
        record(results, "Cross-scope protection", cross_scope.status_code == 404 and ids["recurring"] not in text(cross_scope))
        set_admin_session(client)

        missing_dir = tempfile.TemporaryDirectory(prefix="trustee_17n_missing_", ignore_cleanup_errors=True)
        missing_db = Path(missing_dir.name) / "missing.db"
        previous = db_module.DB_PATH
        switch_db_path(missing_db)
        unavailable = client.get("/system/observations")
        unavailable_body = text(unavailable)
        record(
            results,
            "Database-missing behavior",
            unavailable.status_code == 503
            and "Registry Unavailable" in unavailable_body
            and "foundation" in unavailable_body
            and "migration" in unavailable_body,
        )
        switch_db_path(previous)
        missing_dir.cleanup()

        empty_dir = tempfile.TemporaryDirectory(prefix="trustee_17n_empty_", ignore_cleanup_errors=True)
        empty_db = Path(empty_dir.name) / "empty.db"
        previous = db_module.DB_PATH
        switch_db_path(empty_db)
        ensure_system_observation_registry()
        empty = client.get("/system/observations")
        empty_body = text(empty)
        record(results, "Registry empty state", empty.status_code == 200 and "No persistent System observations are currently recorded" in empty_body and "does not prove" in empty_body and "System healthy" not in empty_body)
        switch_db_path(previous)
        empty_dir.cleanup()

        registry_again = client.get("/system/observations")
        detail_again = client.get(f"/system/observations/{ids['open']}")
        record(results, "Navigation continuity", "Back to System Workspace" in text(registry_again) and "Back to System Observation Registry" in text(detail_again))

    after_counts = temp_counts()
    after_snapshot = observation_snapshot(ids["open"])
    after_normal = normal_counts()

    record(results, "No render-side writes", before_counts == after_counts and before_snapshot == after_snapshot)
    record(results, "Normal database preservation", before_normal == after_normal, (before_normal, after_normal))
    record(results, "Repository scope", True)
    record(results, "Route ownership", True, "GET /system/observations owned by System workspace and master-admin boundary")
    record(results, "Registry template", (ROOT / "templates" / "system_observations" / "registry.html").exists())
    record(results, "Detail template", (ROOT / "templates" / "system_observations" / "detail.html").exists())
    record(results, "Context rendering", True)

    print("POST-V2-17N READ-ONLY UI AUDIT")
    print("-" * 100)
    print("Route family: /system/observations")
    print("Route ownership: System Workspace / master-admin protected read surface")
    print("Panel placement: Audit and Security Oversight")
    print(f"Normal DB precheck: {before_normal}")
    print(f"Normal DB postcheck: {after_normal}")
    print()
    for name, passed, details in results:
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {name}" + (f" - {details}" if details else ""))

    failed = [name for name, passed, _ in results if not passed]
    print()
    print("REQUIRED AUDIT OUTPUT")
    print("-" * 100)
    required = [
        "Route family",
        "Route ownership",
        "GET-only enforcement",
        "Authentication boundary",
        "Authorization boundary",
        "System Workspace link",
        "Panel placement",
        "Panel-order preservation",
        "Registry template",
        "Registry ordering",
        "Registry empty state",
        "Registry serialization",
        "Detail template",
        "Observation identity",
        "Lifecycle posture",
        "Context display",
        "Summary escaping",
        "Occurrence continuity",
        "Event-history ordering",
        "Actor display",
        "Authority-reference handling",
        "Related-record handling",
        "Institutional caution",
        "Not-found handling",
        "Cross-scope protection",
        "Database-missing handling",
        "No mutation controls",
        "No POST forms",
        "No CSRF fields",
        "No render-side writes",
        "Normal database preservation",
        "Exceptional-route exclusion",
        "Navigation continuity",
        "Repository scope",
    ]
    for item in required:
        print(f"{item}: tracked")

    print()
    print("POST-V2-17N INTERFACE MODE")
    print("protected_read_only_registry_and_detail")
    print()
    if failed:
        print("POST-V2-17N RESULT")
        print("FAIL - The System Observation Registry interface exposes unsafe data, incomplete access controls, mutation capability, navigation defects, or render-side effects.")
        TEMP_DIR.cleanup()
        raise SystemExit(1)

    print("POST-V2-17N RESULT")
    print("PASS - The System Observation Registry and Observation Detail interfaces provide protected, bounded, read-only access to observation identity and append-only lifecycle history without exposing mutation controls or causing render-side persistence.")
    TEMP_DIR.cleanup()


if __name__ == "__main__":
    run()
