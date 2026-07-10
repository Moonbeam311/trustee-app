"""
V2-BACKFILL-TEST-1 Matter Governance Timeline smoke test.

Uses the active V2 governance schema and service functions. This verifies that
MAT-000001 can surface linked Directive and Policy records through the existing
Matter governance link, summary, timeline, and Matter detail paths.
"""

import os
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = Path(tempfile.gettempdir()) / "v2_matter_governance_timeline_smoke.sqlite"
if DB_PATH.exists():
    DB_PATH.unlink()

os.environ["DB_PATH"] = str(DB_PATH)

from app import app
from database.migrations_matter_intake import apply_matter_intake_bridge_schema
from services.services_governance import (
    build_matter_governance_links,
    build_matter_governance_summary,
    build_matter_governance_timeline,
    create_governance_record,
    create_governance_relationship,
    ensure_governance_tables,
)
from services.services_intake import ensure_intake_tables
from services.services_matters import create_matter, ensure_matter_tables


FIRM_ID = "FIRM-V2-GOV-SMOKE"


def seed_fixture():
    with app.test_request_context("/"):
        from flask import session

        session["username"] = "admin"
        session["role"] = "Admin"
        session["firm_id"] = FIRM_ID

        ensure_matter_tables()
        ensure_intake_tables()
        apply_matter_intake_bridge_schema(DB_PATH)
        ensure_governance_tables()

        matter_id = create_matter({
            "title": "V2 Matter Governance Timeline Smoke",
            "matter_type": "Governance",
            "status": "Open",
            "priority": "Normal",
            "governance_state": "Pending Review",
        })
        assert matter_id == "MAT-000001", matter_id

        directive_ok, directive_id = create_governance_record("directive", {
            "firm_id": FIRM_ID,
            "title": "Smoke Directive Governing Matter",
            "status": "Active",
            "authority": "V2 smoke authority",
            "summary": "Directive linked to MAT-000001 for timeline smoke.",
            "body": "Directive body for timeline smoke.",
            "rationale": "V2-BACKFILL-TEST-1",
            "created_by": "admin",
            "directive_code": "DIR-SMOKE-MATTER",
            "directive_type": "Operational Directive",
            "approval_required": "1",
            "approved_by": "admin",
            "approved_at": "2026-07-10T08:00:00",
            "effective_at": "2026-07-10T08:30:00",
        })
        assert directive_ok, directive_id

        policy_ok, policy_id = create_governance_record("policy", {
            "firm_id": FIRM_ID,
            "title": "Smoke Policy Applying To Matter",
            "status": "Active",
            "authority": "V2 smoke authority",
            "summary": "Policy linked to MAT-000001 for timeline smoke.",
            "body": "Policy body for timeline smoke.",
            "rationale": "V2-BACKFILL-TEST-1",
            "created_by": "admin",
            "policy_area": "Governance",
            "approval_required": "1",
            "approved_by": "admin",
            "approved_at": "2026-07-10T09:00:00",
            "effective_at": "2026-07-10T09:30:00",
        })
        assert policy_ok, policy_id

        directive_link_ok, directive_link_id = create_governance_relationship({
            "firm_id": FIRM_ID,
            "source_object_type": "Directive",
            "source_object_id": directive_id,
            "relationship_type": "governs",
            "target_object_type": "Matter",
            "target_object_id": matter_id,
            "authority": "V2 smoke authority",
            "reason": "Directive governs MAT-000001 smoke matter.",
            "status": "Active",
            "created_by": "admin",
        })
        assert directive_link_ok, directive_link_id

        policy_link_ok, policy_link_id = create_governance_relationship({
            "firm_id": FIRM_ID,
            "source_object_type": "Matter",
            "source_object_id": matter_id,
            "relationship_type": "implements",
            "target_object_type": "Policy",
            "target_object_id": policy_id,
            "authority": "V2 smoke authority",
            "reason": "MAT-000001 implements linked policy.",
            "status": "Active",
            "created_by": "admin",
        })
        assert policy_link_ok, policy_link_id

        return matter_id, directive_id, policy_id


def inject_admin_session(client):
    with client.session_transaction() as session:
        session.clear()
        session["username"] = "admin"
        session["role"] = "Admin"
        session["user_role"] = "Admin"
        session["firm_id"] = FIRM_ID
        session["last_activity"] = datetime.now(UTC).timestamp()


def main():
    matter_id, directive_id, policy_id = seed_fixture()

    with app.test_request_context("/"):
        from flask import session

        session["username"] = "admin"
        session["role"] = "Admin"
        session["firm_id"] = FIRM_ID

        links = build_matter_governance_links(matter_id)
        summary = build_matter_governance_summary(matter_id)
        timeline = build_matter_governance_timeline(matter_id)

    with app.test_client() as client:
        inject_admin_session(client)
        response = client.get(f"/matters/{matter_id}")
        body = response.get_data(as_text=True)

    link_ids = {link.get("governance_id") for link in links}
    timeline_ids = {item.get("governance_id") for item in timeline}
    timeline_titles = {item.get("title") for item in timeline}

    checks = [
        ("matter_id_is_mat_000001", matter_id == "MAT-000001"),
        ("links_include_directive", directive_id in link_ids),
        ("links_include_policy", policy_id in link_ids),
        ("summary_total", summary.get("total") == 2),
        ("summary_directives", summary.get("directives") == 1),
        ("summary_policies", summary.get("policies") == 1),
        ("summary_active_governance", summary.get("active_governance") >= 1),
        ("timeline_include_directive", directive_id in timeline_ids),
        ("timeline_include_policy", policy_id in timeline_ids),
        ("timeline_newest_first", timeline[0].get("governance_id") == policy_id),
        ("timeline_directive_title", "Smoke Directive Governing Matter" in timeline_titles),
        ("timeline_policy_title", "Smoke Policy Applying To Matter" in timeline_titles),
        ("matter_detail_status_200", response.status_code == 200),
        ("matter_detail_timeline_heading", "Governance Timeline" in body),
        ("matter_detail_directive_visible", directive_id in body and "Smoke Directive Governing Matter" in body),
        ("matter_detail_policy_visible", policy_id in body and "Smoke Policy Applying To Matter" in body),
    ]

    print("===== V2 MATTER GOVERNANCE TIMELINE SMOKE =====")
    print(f"Matter ID: {matter_id}")
    print(f"Directive ID: {directive_id}")
    print(f"Policy ID: {policy_id}")
    for label, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'} | {label}")

    failures = [label for label, ok in checks if not ok]
    if failures:
        raise SystemExit("Smoke failed: " + ", ".join(failures))

    print("ALL V2 MATTER GOVERNANCE TIMELINE CHECKS PASSED")


if __name__ == "__main__":
    main()

