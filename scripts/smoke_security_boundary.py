"""
Local security boundary smoke test.

Purpose:
- Prove assigned trust routes enforce role and assignment boundaries.
- Prove Viewer can read assigned trust surfaces but cannot export PDFs/ZIPs.
- Prove an unassigned Trustee cannot reach trust-scoped direct URLs.
- Prove audit/media helpers quarantine records by firm.

Run:
    python scripts/smoke_security_boundary.py
"""

import os
import sqlite3
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from flask import session
from werkzeug.security import generate_password_hash


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


fd, DB_PATH = tempfile.mkstemp(prefix="trustee_security_boundary_", suffix=".db")
os.close(fd)
os.environ["DB_PATH"] = DB_PATH

conn = sqlite3.connect(DB_PATH)
conn.execute("CREATE TABLE transfers (id INTEGER PRIMARY KEY)")
conn.commit()
conn.close()

from app import app  # noqa: E402
from app import UPLOAD_FOLDER  # noqa: E402
from database.db import (  # noqa: E402
    create_app_user,
    create_media_record,
    create_role_record,
    create_trust_record,
    ensure_role_tables,
    get_all_media,
    get_audit_log,
    get_media_by_id,
    get_next_role_id,
    get_next_user_id,
    log_change,
)


TRUST_ID = "TR-SEC"
FIRM_ID = "FIRM-SECURITY"


ROUTES = [
    (f"/trust/{TRUST_ID}", {
        "admin": "ALLOWED",
        "trustee": "ALLOWED",
        "viewer": "ALLOWED",
        "outsider": "DENIED",
    }),
    (f"/trust/{TRUST_ID}/branding", {
        "admin": "ALLOWED",
        "trustee": "ALLOWED",
        "viewer": "DENIED",
        "outsider": "DENIED",
    }),
    (f"/trust/{TRUST_ID}/packet-preview", {
        "admin": "ALLOWED",
        "trustee": "ALLOWED",
        "viewer": "ALLOWED",
        "outsider": "DENIED",
    }),
    (f"/trust/{TRUST_ID}/controlled-packet-export", {
        "admin": "ALLOWED",
        "trustee": "ALLOWED",
        "viewer": "DENIED",
        "outsider": "DENIED",
    }),
    (f"/trust/{TRUST_ID}/articles-output-surface", {
        "admin": "ALLOWED",
        "trustee": "ALLOWED",
        "viewer": "ALLOWED",
        "outsider": "DENIED",
    }),
    (f"/trust/{TRUST_ID}/articles-output-surface/pdf", {
        "admin": "ALLOWED",
        "trustee": "ALLOWED",
        "viewer": "DENIED",
        "outsider": "DENIED",
    }),
]


USERS = {
    "admin": "Admin",
    "trustee": "Trustee",
    "viewer": "Viewer",
    "outsider": "Trustee",
}


def seed_fixture():
    ensure_role_tables()

    for username, role in USERS.items():
        create_app_user({
            "user_id": get_next_user_id(),
            "username": username,
            "password_hash": generate_password_hash("local-security-smoke-only"),
            "role_name": role,
            "status": "active",
            "firm_id": FIRM_ID,
        })

    create_trust_record({
        "trust_id": TRUST_ID,
        "trust_name": "Security Boundary Trust",
        "short_name": "Security",
        "jurisdiction": "Test",
        "effective_date": "2026-01-01",
        "trust_type": "Revocable Trust",
        "trust_purpose": "Security boundary fixture",
        "accounting_method": "Cash",
        "workflow_mode": "simulation",
        "settlor_name": "Security Settlor",
        "trustee_name": "Security Trustee",
        "successor_trustee_name": "Security Successor",
        "beneficiary_name": "Security Beneficiary",
        "record_visibility": "private",
        "workflow_mode_confirmed": "private_office",
        "ai_explanations": "off",
        "recommended_guidance": "Security smoke only",
        "initial_corpus_description": "Security smoke corpus",
        "property_mapping_timing": "post_creation",
        "asset_categories": "general",
        "generate_schedule_recommendations": "yes",
        "status": "Security Fixture",
        "firm_id": FIRM_ID,
        "owner_id": "admin",
    })

    for username, role in [("trustee", "Trustee"), ("viewer", "Viewer")]:
        create_role_record({
            "role_id": get_next_role_id(),
            "full_name": username,
            "role_name": role,
            "trust_id": TRUST_ID,
            "status": "active",
            "notes": "security boundary fixture",
            "firm_id": FIRM_ID,
        })


def inject_session(client, username, role):
    with client.session_transaction() as active_session:
        active_session.clear()
        active_session["username"] = username
        active_session["role"] = role
        active_session["firm_id"] = FIRM_ID
        active_session["last_activity"] = datetime.now(UTC).timestamp()


def classify_response(response):
    content_type = response.headers.get("Content-Type", "")
    text = ""
    if content_type.startswith("text/"):
        text = (response.get_data() or b"").decode("utf-8", errors="ignore").lower()

    if response.status_code >= 500:
        return "ERROR"
    if response.status_code == 404 or "not found" in text:
        return "NOT_FOUND"
    if "access denied" in text or "not assigned" in text or "not allowed" in text:
        return "DENIED"
    return "ALLOWED"


def run_firm_quarantine_checks(failures):
    media_path = UPLOAD_FOLDER / "media" / FIRM_ID / "MED-SEC.txt"
    media_path.parent.mkdir(parents=True, exist_ok=True)
    media_path.write_text("security boundary media fixture", encoding="utf-8")

    with app.test_request_context("/"):
        session["username"] = "admin"
        session["role"] = "Admin"
        session["firm_id"] = FIRM_ID
        log_change("security_fixture", FIRM_ID, "visible_event", "Visible only to security firm")
        create_media_record({
            "media_id": "MED-SEC",
            "trust_id": TRUST_ID,
            "related_entity_type": "trust",
            "related_entity_id": TRUST_ID,
            "media_type": "document",
            "file_path": media_path.as_posix(),
            "category": "Boundary Fixture",
            "description": "Security firm media",
            "created_at": datetime.now(UTC).isoformat(),
            "firm_id": FIRM_ID,
        })

        security_logs = get_audit_log(20)
        security_media = get_all_media()
        security_file = get_media_by_id("MED-SEC")

    with app.test_request_context("/"):
        session["username"] = "other_admin"
        session["role"] = "Admin"
        session["firm_id"] = "FIRM-OTHER"
        other_logs = get_audit_log(20)
        other_media = get_all_media()
        other_file = get_media_by_id("MED-SEC")

    checks = [
        ("firm audit visible inside firm", bool(security_logs), True),
        ("firm media visible inside firm", bool(security_media), True),
        ("firm media file visible inside firm", bool(security_file), True),
        ("firm audit hidden outside firm", bool(other_logs), False),
        ("firm media hidden outside firm", bool(other_media), False),
        ("firm media file hidden outside firm", bool(other_file), False),
    ]

    print("Firm quarantine")
    for label, actual, expected in checks:
        marker = "PASS" if actual == expected else "FAIL"
        print(f"{marker} | expected={expected!s:5} actual={actual!s:5} | {label}")
        if actual != expected:
            failures.append(("firm-quarantine", label, expected, actual, "helper"))
    print()


def main():
    failures = []

    try:
        seed_fixture()

        with app.test_client() as client:
            print("===== SECURITY BOUNDARY SMOKE TEST =====")
            print(f"Trust ID: {TRUST_ID}")
            print()

            for username, role in USERS.items():
                inject_session(client, username, role)
                print(f"User: {username} ({role})")

                for route, expectations in ROUTES:
                    response = client.get(route, follow_redirects=False)
                    actual = classify_response(response)
                    expected = expectations[username]
                    marker = "PASS" if actual == expected else "FAIL"
                    print(f"{marker} | expected={expected:7} actual={actual:7} | {route}")

                    if actual != expected:
                        failures.append((username, route, expected, actual, response.status_code))

                print()

            run_firm_quarantine_checks(failures)

        if failures:
            print("===== FAILURES =====")
            for username, route, expected, actual, status in failures:
                print(f"{username} | {route} | expected={expected} actual={actual} status={status}")
            raise SystemExit(1)

        print("ALL SECURITY BOUNDARY CHECKS PASSED")
    finally:
        try:
            Path(DB_PATH).unlink()
        except Exception:
            pass


if __name__ == "__main__":
    main()
