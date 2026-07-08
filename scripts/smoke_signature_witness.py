"""
Local signature/witness smoke test for trust minute execution.

Purpose:
- Verify a trust minute cannot execute with missing signer records.
- Verify execution requires at least one Trustee signer and one Witness signer.
- Verify a valid drawn-signature payload executes and locks the minute.

Run:
    python scripts/smoke_signature_witness.py
"""

import base64
import os
import sqlite3
import sys
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path

from werkzeug.security import generate_password_hash


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


fd, DB_PATH = tempfile.mkstemp(prefix="trustee_signature_witness_", suffix=".db")
os.close(fd)
os.environ["DB_PATH"] = DB_PATH

conn = sqlite3.connect(DB_PATH)
conn.execute("CREATE TABLE transfers (id INTEGER PRIMARY KEY)")
conn.commit()
conn.close()

from app import app  # noqa: E402
from database.db import (  # noqa: E402
    create_app_user,
    create_trust_minute,
    create_trust_record,
    get_next_minute_id,
    get_next_user_id,
    get_trust_minute_by_id,
)


TRUST_ID = "TR-SIGN"
USERNAME = "admin"
FIRM_ID = "FIRM-SIGN"


def signature_payload():
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + b"signature-smoke-test-payload" * 30
    )
    return "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")


def seed_fixture():
    create_app_user({
        "user_id": get_next_user_id(),
        "username": USERNAME,
        "password_hash": generate_password_hash("local-signature-smoke-only"),
        "role_name": "Admin",
        "status": "active",
        "firm_id": FIRM_ID,
    })

    create_trust_record({
        "trust_id": TRUST_ID,
        "trust_name": "Signature Witness Trust",
        "short_name": "Sign",
        "jurisdiction": "Test",
        "effective_date": "2026-01-01",
        "trust_type": "Revocable Trust",
        "trust_purpose": "Signature witness fixture",
        "accounting_method": "Cash",
        "workflow_mode": "simulation",
        "settlor_name": "Signature Settlor",
        "trustee_name": "Signature Trustee",
        "successor_trustee_name": "Signature Successor",
        "beneficiary_name": "Signature Beneficiary",
        "record_visibility": "private",
        "workflow_mode_confirmed": "private_office",
        "ai_explanations": "off",
        "recommended_guidance": "Signature smoke only",
        "initial_corpus_description": "Signature corpus",
        "property_mapping_timing": "post_creation",
        "asset_categories": "general",
        "generate_schedule_recommendations": "yes",
        "status": "Signature Fixture",
        "firm_id": FIRM_ID,
        "owner_id": USERNAME,
    })

    minute_id = get_next_minute_id()
    create_trust_minute({
        "minute_id": minute_id,
        "trust_id": TRUST_ID,
        "meeting_date": date.today().isoformat(),
        "meeting_type": "Resolution Without Meeting",
        "title": "Signature Witness Smoke Minute",
        "purpose": "Verify signature and witness execution boundary.",
        "resolutions": "Approve smoke execution validation.",
        "action_items": "Retain certificate.",
        "status": "Approved",
        "created_by": USERNAME,
        "firm_id": FIRM_ID,
    })
    return minute_id


def inject_session(client):
    with client.session_transaction() as active_session:
        active_session.clear()
        active_session["username"] = USERNAME
        active_session["role"] = "Admin"
        active_session["firm_id"] = FIRM_ID
        active_session["last_activity"] = datetime.now(UTC).timestamp()
        active_session["_csrf_token"] = "signature-smoke-token"


def post_execute(client, minute_id, payload):
    form = {
        "_csrf_token": "signature-smoke-token",
        "action": "execute",
        "trustee_1_name": "",
        "trustee_1_capacity": "Trustee",
        "trustee_1_signed_date": "",
        "trustee_1_signature_image": "",
        "trustee_2_name": "",
        "trustee_2_capacity": "Witness",
        "trustee_2_signed_date": "",
        "trustee_2_signature_image": "",
        "trustee_3_name": "",
        "trustee_3_capacity": "",
        "trustee_3_signed_date": "",
        "trustee_3_signature_image": "",
    }
    form.update(payload)
    return client.post(f"/minutes/{minute_id}/execute", data=form, follow_redirects=False)


def main():
    try:
        minute_id = seed_fixture()
        sig = signature_payload()

        with app.test_client() as client:
            inject_session(client)

            print("===== SIGNATURE/WITNESS SMOKE TEST =====")
            print(f"Minute ID: {minute_id}")
            print()

            response = post_execute(client, minute_id, {})
            print(f"Missing signer block status: {response.status_code}")
            if response.status_code != 400:
                raise SystemExit("Expected missing signer execution to fail with 400.")

            response = post_execute(client, minute_id, {
                "trustee_1_name": "Trustee One",
                "trustee_1_signed_date": date.today().isoformat(),
                "trustee_1_signature_image": sig,
            })
            print(f"Missing witness block status: {response.status_code}")
            if response.status_code != 400:
                raise SystemExit("Expected missing witness execution to fail with 400.")

            response = post_execute(client, minute_id, {
                "trustee_1_name": "Trustee One",
                "trustee_1_signed_date": date.today().isoformat(),
                "trustee_1_signature_image": sig,
                "trustee_2_name": "Witness One",
                "trustee_2_signed_date": date.today().isoformat(),
                "trustee_2_signature_image": sig,
            })
            print(f"Complete execution status: {response.status_code}")
            if response.status_code not in {302, 303}:
                raise SystemExit("Expected complete execution to redirect after success.")

            minute = get_trust_minute_by_id(minute_id)
            if minute["status"] != "Executed" or int(minute["locked"] or 0) != 1:
                raise SystemExit("Expected minute to be Executed and locked.")

            cert = client.get(f"/minutes/{minute_id}/certificate.pdf", follow_redirects=False)
            packet = client.get(f"/minutes/{minute_id}/packet.pdf", follow_redirects=False)
            print(f"Certificate PDF status: {cert.status_code} {cert.headers.get('Content-Type')}")
            print(f"Packet PDF status: {packet.status_code} {packet.headers.get('Content-Type')}")

            if cert.status_code != 200 or packet.status_code != 200:
                raise SystemExit("Expected certificate and packet PDFs to render.")

        print("ALL SIGNATURE/WITNESS CHECKS PASSED")
    finally:
        try:
            Path(DB_PATH).unlink()
        except Exception:
            pass


if __name__ == "__main__":
    main()
