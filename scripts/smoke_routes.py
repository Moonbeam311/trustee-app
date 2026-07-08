"""
TOS-35 Local Route Smoke Test

Purpose:
- Verify critical Trustee App routes respond locally.
- Confirm no 404/500 errors on document surfaces, PDFs, packet preview,
  controlled packet export, branding, admin, and storage diagnostics.

Run:
    python scripts/smoke_routes.py

Assumption:
- Uses Flask test_client against the local app object.
- Auth session is injected for local testing only.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app
from datetime import datetime, UTC
from database.db import (
    create_app_user,
    create_trust_record,
    ensure_firm_columns,
    ensure_role_tables,
    ensure_user_tables,
    get_next_user_id,
    get_trust_by_id,
    get_user_by_username,
    reseed_default_role_permissions,
)

TRUST_ID = "TR-001"
SMOKE_FIRM_ID = "FIRM-SMOKE"

ROUTES = [
    ("GET", "/admin", "Admin dashboard"),
    ("GET", "/admin/storage-diagnostics", "Storage diagnostics"),
    ("GET", f"/trust/{TRUST_ID}/branding", "Trust branding settings"),
    ("GET", f"/trust/{TRUST_ID}/packet-preview", "Packet preview"),
    ("GET", f"/trust/{TRUST_ID}/controlled-packet-export", "Controlled packet ZIP export"),

    ("GET", f"/trust/{TRUST_ID}/articles-output-surface", "Articles final surface"),
    ("GET", f"/trust/{TRUST_ID}/articles-output-surface/pdf", "Articles PDF"),

    ("GET", f"/trust/{TRUST_ID}/trustee-acceptance-output-surface", "Trustee Acceptance final surface"),
    ("GET", f"/trust/{TRUST_ID}/trustee-acceptance-output-surface/pdf", "Trustee Acceptance PDF"),

    ("GET", f"/trust/{TRUST_ID}/general-assignment-output-surface", "General Assignment final surface"),
    ("GET", f"/trust/{TRUST_ID}/general-assignment-output-surface/pdf", "General Assignment PDF"),

    ("GET", f"/trust/{TRUST_ID}/organizational-minutes-output-surface", "Organizational Minutes final surface"),
    ("GET", f"/trust/{TRUST_ID}/organizational-minutes-output-surface/pdf", "Organizational Minutes PDF"),

    ("GET", f"/trust/{TRUST_ID}/successor-trustee-output-surface", "Successor Trustee final surface"),
    ("GET", f"/trust/{TRUST_ID}/successor-trustee-output-surface/pdf", "Successor Trustee PDF"),

    ("GET", f"/trust/{TRUST_ID}/declaration-output-surface", "Declaration final surface"),
    ("GET", f"/trust/{TRUST_ID}/declaration-output-surface/pdf", "Declaration PDF"),

    ("GET", f"/trust/{TRUST_ID}/certificate-of-trust-output-surface", "Certificate final surface"),
    ("GET", f"/trust/{TRUST_ID}/certificate-of-trust-output-surface/pdf", "Certificate PDF"),
]


def inject_admin_session(client):
    admin_user = get_user_by_username("admin")
    with client.session_transaction() as session:
        session.clear()
        if admin_user:
            session["user_id"] = admin_user["user_id"]
        session["username"] = "admin"
        session["role"] = "Admin"
        session["user_role"] = "Admin"
        session["is_master_admin"] = True
        session["firm_id"] = SMOKE_FIRM_ID
        session["last_activity"] = datetime.now(UTC).timestamp()


def ensure_smoke_trust():
    with app.test_request_context("/"):
        from flask import session

        ensure_user_tables()
        ensure_firm_columns()
        ensure_role_tables()
        reseed_default_role_permissions()

        session["username"] = "admin"
        session["role"] = "Admin"
        session["firm_id"] = SMOKE_FIRM_ID

        if not get_user_by_username("admin"):
            create_app_user({
                "user_id": get_next_user_id(),
                "username": "admin",
                "password_hash": "smoke-fixture-only",
                "role_name": "Admin",
                "status": "Active",
                "firm_id": SMOKE_FIRM_ID,
            })

        if get_trust_by_id(TRUST_ID):
            return

        create_trust_record({
            "trust_id": TRUST_ID,
            "trust_name": "Smoke Test Trust",
            "short_name": "Smoke",
            "jurisdiction": "Test Jurisdiction",
            "effective_date": "2026-01-01",
            "trust_type": "Revocable Trust",
            "trust_purpose": "Local smoke-test fixture",
            "accounting_method": "Cash",
            "workflow_mode": "simulation",
            "settlor_name": "Smoke Settlor",
            "trustee_name": "Smoke Trustee",
            "successor_trustee_name": "Smoke Successor Trustee",
            "beneficiary_name": "Smoke Beneficiary",
            "record_visibility": "private",
            "workflow_mode_confirmed": "private_office",
            "ai_explanations": "off",
            "recommended_guidance": "Smoke test only",
            "initial_corpus_description": "Smoke fixture corpus",
            "property_mapping_timing": "post_creation",
            "asset_categories": "general",
            "generate_schedule_recommendations": "yes",
            "status": "Smoke Fixture",
            "firm_id": SMOKE_FIRM_ID,
            "owner_id": "admin",
        })


def main():
    failures = []
    ensure_smoke_trust()

    with app.test_client() as client:
        inject_admin_session(client)

        print("===== TOS-35 LOCAL ROUTE SMOKE TEST =====")
        print(f"Trust ID: {TRUST_ID}")
        print()

        for method, route, label in ROUTES:
            response = client.open(route, method=method, follow_redirects=False)
            status = response.status_code

            ok = status in {200, 302}
            marker = "PASS" if ok else "FAIL"

            content_type = response.headers.get("Content-Type", "")
            content_length = len(response.get_data() or b"")

            print(f"{marker} | {status} | {label} | {route} | {content_type} | bytes={content_length}")

            if not ok:
                failures.append((status, label, route))

    print()
    if failures:
        print("===== FAILURES =====")
        for status, label, route in failures:
            print(f"{status} | {label} | {route}")
        raise SystemExit(1)

    print("ALL SMOKE TEST ROUTES PASSED")


if __name__ == "__main__":
    main()
