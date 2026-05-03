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

TRUST_ID = "TR-001"

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
    with client.session_transaction() as session:
        session.clear()
        session["username"] = "admin"
        session["role"] = "Admin"
        session["user_role"] = "Admin"
        session["is_master_admin"] = True
        session["last_activity"] = datetime.now(UTC).timestamp()


def main():
    failures = []

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
