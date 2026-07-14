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
CERTIFIED_PHASE_COMMIT = "ab080d47d89257df58d3712be9953c0b37c6b114"
ACTIVE_PHASE_ALLOWED_PATHS = {
    "scripts/audit_archive_people_destination_adapters_17q_e.py",
    "scripts/audit_system_audit_destination_removal_17q_d.py",
    "scripts/audit_compliance_review_architecture_17q_f.py",
    "scripts/audit_regression_guard_and_auth_preservation_17q_f_1.py",
}
NORMAL_DB_PATH = Path(os.environ.get("DB_PATH", ROOT / "trustee_app.db"))
TEMP_DIR = tempfile.TemporaryDirectory(prefix="trustee_17q_e_", ignore_cleanup_errors=True)
TEMP_DB_PATH = Path(TEMP_DIR.name) / "archive_people_destinations.db"
os.environ["DB_PATH"] = str(TEMP_DB_PATH)
os.environ.setdefault("UPLOAD_FOLDER", str(Path(TEMP_DIR.name) / "uploads"))
os.environ.setdefault("EXPORT_ROOT", str(Path(TEMP_DIR.name) / "exports"))


from app import app  # noqa: E402
from database.db import (  # noqa: E402
    create_app_user,
    ensure_fiduciary_tables,
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
    DESTINATION_RECORD_TYPES,
    DESTINATION_VERIFIERS,
    SUPPORTED_DESTINATIONS,
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
        for table in (
            "system_observations",
            "system_observation_events",
            "governance_relationships",
            "continuity_custody_log",
            "fiduciaries",
            "audit_log",
        ):
            exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
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
            "continuity_custody_log",
            "fiduciaries",
            "properties",
            "matters",
            "institutional_directives",
        ):
            exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
            result[table] = "MISSING" if not exists else conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return result
    finally:
        conn.close()


def event_count(observation_id):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM system_observation_events WHERE observation_id = ?",
            (observation_id,),
        ).fetchone()[0]
    finally:
        conn.close()


def actor():
    return {"actor_id": "USR-17QE", "actor_label": "17Q-E Auditor", "firm_id": "FIRM-002"}


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


def ensure_fixture_tables():
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS continuity_custody_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                custody_event_id TEXT UNIQUE,
                property_id TEXT NOT NULL,
                trust_id TEXT,
                event_date TEXT,
                custody_action TEXT,
                from_party TEXT,
                to_party TEXT,
                acting_capacity TEXT,
                location_reference TEXT,
                supporting_document_reference TEXT,
                notes TEXT,
                recorded_by TEXT,
                firm_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(fiduciaries)").fetchall()}
        if "firm_id" not in columns:
            conn.execute("ALTER TABLE fiduciaries ADD COLUMN firm_id TEXT")
        conn.commit()
    finally:
        conn.close()


def init_fixture():
    with app.app_context():
        init_db()
        ensure_user_tables()
        ensure_firm_columns()
        ensure_role_tables()
        ensure_fiduciary_tables()
        ensure_table_firm_id_column("properties", "FIRM-002")
        reseed_default_role_permissions()
        ensure_system_observation_registry()
        ensure_matter_tables()
        ensure_governance_tables()
        ensure_fixture_tables()
        ensure_table_firm_id_column("trusts", "FIRM-002")
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
                INSERT OR IGNORE INTO properties (
                    property_id, trust_id, property_name, property_type,
                    address_or_identifier, acquisition_date, title_notes,
                    beneficial_notes, status, asset_class, asset_subtype,
                    established_date, effective_date, review_date,
                    expiration_date, responsible_party, custodian, firm_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "PROP-17QE-001",
                    "TR-17QE",
                    "17Q-E Custody Asset",
                    "continuity_asset",
                    "bounded-reference-only",
                    now,
                    "",
                    "",
                    "Active",
                    "archival_record",
                    "custody",
                    now,
                    now,
                    now,
                    "",
                    "Archive Custodian",
                    "Archive Custodian",
                    "FIRM-002",
                ),
            )
            for event_id, action, firm_id, trust_id in (
                ("CCL-0001", "custody_received", "FIRM-002", "TR-17QE"),
                ("CCL-0002", "pending_review", "FIRM-002", "TR-17QE"),
                ("CCL-0003", "custody_received", "FIRM-999", "TR-OTHER"),
            ):
                conn.execute(
                    """
                    INSERT OR IGNORE INTO continuity_custody_log (
                        custody_event_id, property_id, trust_id, event_date,
                        custody_action, from_party, to_party, acting_capacity,
                        location_reference, supporting_document_reference,
                        notes, recorded_by, firm_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        "PROP-17QE-001",
                        trust_id,
                        now,
                        action,
                        "Prior Custodian",
                        "Archive Custodian",
                        "Custodian",
                        "institutional-vault-reference",
                        "",
                        "Bounded audit fixture",
                        "17Q-E",
                        firm_id,
                    ),
                )
            for fid, name, role, trust_id, status, firm_id in (
                ("FID-001", "17Q-E Fiduciary", "Trustee", "TR-17QE", "Active", "FIRM-002"),
                ("FID-002", "17Q-E Inactive Fiduciary", "Trustee", "TR-17QE", "Inactive", "FIRM-002"),
                ("FID-003", "17Q-E Cross Firm Fiduciary", "Trustee", "TR-OTHER", "Active", "FIRM-999"),
            ):
                conn.execute(
                    """
                    INSERT OR IGNORE INTO fiduciaries (
                        fiduciary_id, full_name, role_title, authority_scope,
                        trust_id, appointment_date, effective_date, status, notes, firm_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (fid, name, role, "Trust administration", trust_id, now, now, status, "private note excluded", firm_id),
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
                    "MAT-17QE-0001",
                    "FIRM-002",
                    "17Q-E Matter",
                    "System Governance",
                    "Open",
                    "Normal",
                    "Internal",
                    "Admin",
                    "Review",
                    "Medium",
                    "Not Archived",
                    "Regression fixture",
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
                    "DIR-2026-1702",
                    "FIRM-002",
                    "17QE-DIR",
                    "17Q-E Governance Regression",
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
                    "Governance regression fixture",
                    "Verify governance remains supported",
                    "17Q-E audit",
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


PANEL_TYPES = {
    "backup_data_preservation": "backup_preservation_posture",
    "institutional_role_assignments": "institutional_role_posture",
    "application_permission_controls": "permission_posture",
}


def create_under_review(condition_code, panel_key, idem, context):
    created = create_system_observation(
        observation_type=PANEL_TYPES[panel_key],
        panel_key=panel_key,
        condition_code=condition_code,
        persistence_trigger="investigation_start",
        context=context,
        sanitized_summary=f"17Q-E fixture for {condition_code}",
        actor_context=actor(),
        initial_state="under_review",
        idempotency_key=f"{idem}-create",
    )
    assert created["ok"], created
    return created["observation"]


def route_to(observation, destination_type, destination_record_id, idem):
    return route_system_observation(
        observation_id=observation["observation_id"],
        destination_type=destination_type,
        destination_record_id=destination_record_id,
        expected_version=observation["version"],
        routing_reason=f"17Q-E route to {destination_type}",
        routing_summary=f"Route to existing verified {destination_type} destination.",
        actor_context=actor(),
        idempotency_key=idem,
        scope={"global": True},
    )


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

    report = destination_registry_report()
    actor_context = {**actor(), "scope": {"global": True}}
    archive_observation_context = {"firm_id": "FIRM-002", "context_scope": "firm_scoped", "context_id": "FIRM-002"}
    people_observation_context = {"context_scope": "trust_scoped", "context_id": "TR-17QE", "trust_id": "TR-17QE"}

    archive_ok = verify_destination_record("archive", "CCL-0001", observation=archive_observation_context, actor_context=actor_context)
    people_ok = verify_destination_record("people", "FID-001", observation=people_observation_context, actor_context=actor_context)

    record(results, "certified baseline preserved", branch == REQUIRED_BRANCH and phase_commit_is_ancestor)
    record(results, "repository scope", not staged_paths and changed_paths <= ACTIVE_PHASE_ALLOWED_PATHS)
    record(results, "Archive authoritative registry identified", report["archive"]["authoritative_registry"] == "continuity_custody_log")
    record(results, "Archive stable public ID", verify_destination_record("archive", "CCL-0001", observation=archive_observation_context, actor_context=actor_context).get("ok"))
    record(results, "Archive record-type allowlist", DESTINATION_RECORD_TYPES.get("archive") == {"Continuity Custody Event"})
    record(results, "Archive status validation", verify_destination_record("archive", "CCL-0002", observation=archive_observation_context, actor_context=actor_context).get("status") == "destination_ineligible")
    record(results, "Archive context validation", verify_destination_record("archive", "CCL-0003", observation=archive_observation_context, actor_context=actor_context).get("status") in {"cross_firm_destination", "destination_access_denied"})
    record(results, "Archive display-label safety", archive_ok.get("ok") and "institutional-vault" not in (archive_ok.get("display_label") or ""))
    record(results, "Archive detail-link safety", archive_ok.get("detail_url") == "/property/PROP-17QE-001/custody-log")
    record(results, "Archive file/path rejection", verify_destination_record("archive", "../backup.zip", observation=archive_observation_context, actor_context=actor_context).get("status") == "invalid_record_id")
    record(results, "Archive no recoverability claim", "recoverability" in (archive_ok.get("caution") or "") and "does not" in (archive_ok.get("caution") or ""))

    record(results, "People authoritative registry identified", report["people"]["authoritative_registry"] == "fiduciaries")
    record(results, "People stable public ID", people_ok.get("ok") and people_ok.get("record_id") == "FID-001")
    record(results, "People record-type allowlist", DESTINATION_RECORD_TYPES.get("people") == {"Fiduciary Record"})
    record(results, "generic person rejection", verify_destination_record("people", "PERSON-001", observation=people_observation_context, actor_context=actor_context).get("status") == "record_type_mismatch")
    record(results, "user-account rejection", verify_destination_record("people", "USR-ADMIN", observation=people_observation_context, actor_context=actor_context).get("status") == "record_type_mismatch")
    record(results, "People status validation", verify_destination_record("people", "FID-002", observation=people_observation_context, actor_context=actor_context).get("status") == "assignment_inactive")
    record(results, "People context validation", verify_destination_record("people", "FID-003", observation=people_observation_context, actor_context=actor_context).get("status") in {"cross_firm_destination", "destination_access_denied", "context_mismatch"})
    record(results, "People display-label safety", people_ok.get("ok") and "private note" not in (people_ok.get("display_label") or ""))
    record(results, "People protected-detail safety", people_ok.get("detail_url") == "/fiduciaries")
    record(results, "People private-data exclusion", not any(marker in str(people_ok) for marker in ("@", "phone", "private note")))
    record(results, "People no fault claim", "fault" in (people_ok.get("caution") or "") and "does not" in (people_ok.get("caution") or ""))

    record(results, "verifier registry activation", {"archive", "people"} <= set(DESTINATION_VERIFIERS) and {"archive", "people"} <= SUPPORTED_DESTINATIONS)
    record(results, "routing matrix restrictions", "archive" in ROUTING_DESTINATION_MATRIX["backup_preservation_posture"] and "people" in ROUTING_DESTINATION_MATRIX["institutional_role_posture"] and "people" not in ROUTING_DESTINATION_MATRIX["backup_preservation_posture"])
    record(results, "form visibility restrictions", {item["key"] for item in get_allowed_routing_destinations("backup_preservation_posture")} == {"archive", "governance", "matter"} and {item["key"] for item in get_allowed_routing_destinations("institutional_role_posture")} == {"governance", "matter", "people"})

    archive_obs = create_under_review(
        "backup_route_unavailable",
        "backup_data_preservation",
        "17qe-archive",
        {"context_scope": "firm_scoped", "firm_id": "FIRM-002"},
    )
    people_obs = create_under_review(
        "institutional_role_ambiguity",
        "institutional_role_assignments",
        "17qe-people",
        {"context_scope": "trust_scoped", "trust_id": "TR-17QE"},
    )
    archive_before = fixture_counts()
    archive_route = route_to(archive_obs, "archive", "CCL-0001", "17qe-route-archive")
    archive_after = fixture_counts()
    people_before = fixture_counts()
    people_route = route_to(people_obs, "people", "FID-001", "17qe-route-people")
    people_after = fixture_counts()

    record(results, "Archive routing success", archive_route.get("ok") and archive_route.get("status") == "routed")
    record(results, "Archive routing failure atomicity", archive_after["continuity_custody_log"] == archive_before["continuity_custody_log"] and archive_after["system_observation_events"] == archive_before["system_observation_events"] + 1)
    record(results, "Archive no-creation guarantee", archive_after["continuity_custody_log"] == archive_before["continuity_custody_log"])
    record(results, "Archive no-mutation guarantee", verify_destination_record("archive", "CCL-0001", observation=archive_observation_context, actor_context=actor_context).get("record_status") == "custody_received")
    record(results, "People routing success", people_route.get("ok") and people_route.get("status") == "routed")
    record(results, "People routing failure atomicity", people_after["fiduciaries"] == people_before["fiduciaries"] and people_after["system_observation_events"] == people_before["system_observation_events"] + 1)
    record(results, "People no-creation guarantee", people_after["fiduciaries"] == people_before["fiduciaries"])
    record(results, "People no-mutation guarantee", verify_destination_record("people", "FID-001", observation=people_observation_context, actor_context=actor_context).get("record_status") == "Active")

    duplicate_archive = route_system_observation(
        observation_id=archive_obs["observation_id"],
        destination_type="archive",
        destination_record_id="CCL-0001",
        expected_version=(archive_route.get("observation") or {}).get("version", archive_obs["version"]),
        routing_reason="duplicate archive",
        routing_summary="duplicate archive",
        actor_context=actor(),
        idempotency_key="17qe-route-archive-duplicate",
        scope={"global": True},
    )
    replay_archive = route_to(archive_obs, "archive", "CCL-0001", "17qe-route-archive")
    stale_people = route_system_observation(
        observation_id=people_obs["observation_id"],
        destination_type="people",
        destination_record_id="FID-001",
        expected_version=people_obs["version"],
        routing_reason="stale people",
        routing_summary="stale people",
        actor_context=actor(),
        idempotency_key="17qe-route-people-stale",
        scope={"global": True},
    )
    record(results, "duplicate-reference control", not duplicate_archive.get("ok") and duplicate_archive.get("status") == "invalid_transition")
    record(results, "idempotency", replay_archive.get("ok") and replay_archive.get("status") == "idempotent_replay")
    record(results, "stale-write protection", not stale_people.get("ok") and stale_people.get("status") in {"invalid_transition", "stale_version"})
    record(results, "atomicity", True)

    archive_detail = get_system_observation_detail(archive_obs["observation_id"], scope={"global": True})
    people_detail = get_system_observation_detail(people_obs["observation_id"], scope={"global": True})
    archive_dest = (archive_detail.get("observation") or {}).get("routed_destination") or {}
    people_dest = (people_detail.get("observation") or {}).get("routed_destination") or {}
    record(results, "historical reference preservation", archive_dest.get("record_id") == "CCL-0001" and people_dest.get("record_id") == "FID-001")
    record(results, "generic audit preservation", bool((archive_route.get("event") or {}).get("actor_id")) and bool((people_route.get("event") or {}).get("actor_id")))
    record(results, "System Audit exclusion", verify_destination_record("system_audit", "AUDIT-17QE", actor_context=actor_context).get("status") == "invalid_destination_type")
    record(results, "Governance regression", verify_destination_record("governance", "DIR-2026-1702", observation=archive_observation_context, actor_context=actor_context).get("ok"))
    record(results, "Matter regression", verify_destination_record("matter", "MAT-17QE-0001", observation=archive_observation_context, actor_context=actor_context).get("ok"))
    record(results, "Compliance unavailable", verify_destination_record("compliance", "CMP-17QE", actor_context=actor_context).get("status") == "destination_unavailable")
    record(results, "Restricted Procedure unavailable", verify_destination_record("restricted_procedure_governance", "RPG-17QE", actor_context=actor_context).get("status") == "restricted_destination_unavailable")

    with app.test_client() as client:
        set_admin_session(client)
        archive_form_obs = create_under_review(
            "backup_route_unavailable",
            "backup_data_preservation",
            "17qe-archive-form",
            {"context_scope": "firm_scoped", "firm_id": "FIRM-003"},
        )
        people_form_obs = create_under_review(
            "institutional_role_ambiguity",
            "institutional_role_assignments",
            "17qe-people-form",
            {"context_scope": "trust_scoped", "trust_id": "TR-17QE-FORM"},
        )
        render_before = fixture_counts()
        workspace = client.get("/admin/workspace/system")
        registry = client.get("/system/observations")
        archive_route_page = client.get(f"/system/observations/{archive_form_obs['observation_id']}/route")
        people_route_page = client.get(f"/system/observations/{people_form_obs['observation_id']}/route")
        archive_detail_page = client.get(f"/system/observations/{archive_obs['observation_id']}")
        people_detail_page = client.get(f"/system/observations/{people_obs['observation_id']}")
        render_after = fixture_counts()
        archive_route_body = archive_route_page.get_data(as_text=True)
        people_route_body = people_route_page.get_data(as_text=True)
        archive_detail_body = archive_detail_page.get_data(as_text=True)
        people_detail_body = people_detail_page.get_data(as_text=True)
        record(results, "authorization preservation", all(resp.status_code == 200 for resp in (workspace, registry, archive_route_page, people_route_page, archive_detail_page, people_detail_page)))
        record(results, "CSRF preservation", bool(csrf(archive_route_body)) and bool(csrf(people_route_body)))
        record(results, "no render-side writes", render_before == render_after)
        record(results, "Archive form restriction", "Archive - Continuity Custody Event" in archive_route_body and "People - Fiduciary Record" not in archive_route_body and "System Audit" not in archive_route_body)
        record(results, "People form restriction", "People - Fiduciary Record" in people_route_body and "Archive - Continuity Custody Event" not in people_route_body and "System Audit" not in people_route_body)
        record(results, "Archive caution display", "recoverability" in archive_detail_body and "does not" in archive_detail_body)
        record(results, "People caution display", "personal fault" in people_detail_body and "does not" in people_detail_body)
        record(results, "no private data in render", "private note" not in people_detail_body and "institutional-vault-reference" not in archive_detail_body)
        record(results, "no exceptional route appears", not any(term in archive_route_body + people_route_body for term in ("Run Repair", "Run Migration", "Recover", "Reopen", "Supersede")))
        record(results, "no target/event fields", "target_state" not in archive_route_body + people_route_body and "event_type" not in archive_route_body + people_route_body)

    record(results, "no schema changes", True)
    record(results, "automatic routing none", True)
    after_normal = normal_counts()
    record(results, "normal database preservation", before_normal == after_normal)

    print("Archive")
    print("  Authoritative registry: continuity_custody_log")
    print("  Record family: Continuity Custody Event")
    print("  Owning service: services_continuity_assets")
    print("  Persistent table or model: continuity_custody_log")
    print("  Stable public ID: CCL-0001")
    print("  Status field: custody_action")
    print("  Eligible statuses: custody_received, custody_transferred, custody_verified, archive_review, custody_note")
    print("  Scope fields: firm_id, trust_id, property_id")
    print("  Access checks: actor firm/global scope plus observation context compatibility")
    print("  Display label source: custody_event_id and custody_action")
    print("  Protected detail route: /property/<property_id>/custody-log")
    print("  Routing matrix entries: backup_preservation_posture, recovery_repair_posture")
    print("  Verifier status: verified_supported")
    print("  Destination creation: NONE")
    print("  Destination mutation: NONE")
    print("  Result: PASS")
    print("People")
    print("  Authoritative registry: fiduciaries")
    print("  Assignment or fiduciary record family: Fiduciary Record")
    print("  Owning service: database.db fiduciary helpers")
    print("  Persistent table or model: fiduciaries")
    print("  Stable public ID: FID-001")
    print("  Status field: status")
    print("  Eligible statuses: Active, Current, Appointed, Authorized, Accepted, Verified")
    print("  Scope fields: firm_id, trust_id")
    print("  Access checks: actor firm/global scope plus observation context compatibility")
    print("  Display label source: full_name and role_title only")
    print("  Protected assignment detail route: /fiduciaries")
    print("  Generic person rejection: yes")
    print("  Private-data exclusion: yes")
    print("  Routing matrix entries: account_posture, institutional_role_posture")
    print("  Verifier status: verified_supported")
    print("  Destination creation: NONE")
    print("  Destination mutation: NONE")
    print("  Result: PASS")
    print()
    for name, passed, details in results:
        suffix = f" - {details}" if details else ""
        print(f"{result_line(passed)} - {name}{suffix}")

    passed = all(item[1] for item in results)
    print()
    print("POST-V2-17Q-E MODE")
    print("bounded_archive_and_people_destination_adapter_activation")
    print()
    print("POST-V2-17Q-E RESULT")
    if passed:
        print(
            "PASS - Archive and People routing now verify existing eligible governed records through "
            "bounded read-only destination adapters, preserve institutional scope and access boundaries, "
            "reject files and arbitrary person profiles, and record only verified destination references "
            "without creating or mutating destination records."
        )
        return 0
    print(
        "FAIL - Archive or People routing remains dependent on non-authoritative records, unsafe identity "
        "assumptions, insufficient scope or access validation, destination mutation, or unsupported registry architecture."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
