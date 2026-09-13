import inspect
import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def test_discussion_schema_owner_and_manual_reply_contract(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    db_path = tmp_path / "discussion_contract.db"

    env = os.environ.copy()
    env["DB_PATH"] = str(db_path)

    script = r"""
import inspect
import os
import sqlite3

from database.db import init_db

init_db()

import app as app_module
from flask import session

db_path = os.environ["DB_PATH"]

conn = sqlite3.connect(db_path)

thread_cols = [
    row[1]
    for row in conn.execute("PRAGMA table_info(discussion_threads)").fetchall()
]
message_cols = [
    row[1]
    for row in conn.execute("PRAGMA table_info(discussion_messages)").fetchall()
]

assert thread_cols == [
    "thread_id",
    "workspace_id",
    "title",
    "category",
    "related_trust_type",
    "related_form",
    "created_by",
    "status",
    "owner_id",
    "created_at",
    "updated_at",
]

assert message_cols == [
    "message_id",
    "thread_id",
    "parent_message_id",
    "author",
    "body",
    "owner_id",
    "created_at",
]

assert conn.execute(
    "SELECT COUNT(*) FROM discussion_threads"
).fetchone()[0] == 0

assert conn.execute(
    "SELECT COUNT(*) FROM discussion_messages"
).fetchone()[0] == 0

conn.close()

with app_module.app.test_request_context("/discussions"):
    session["username"] = "admin"
    session["firm_id"] = "FIRM-001"

    app_module.create_discussion_thread({
        "thread_id": "THREAD-TEST-001",
        "workspace_id": None,
        "title": "Finding 43 Test Thread",
        "category": "general_design_discussion",
        "related_trust_type": None,
        "related_form": None,
        "created_by": "admin",
        "status": "open",
        "owner_id": app_module.get_current_owner(),
    })

    rows = app_module.get_all_discussion_threads()
    assert len(rows) == 1
    assert rows[0]["thread_id"] == "THREAD-TEST-001"
    assert rows[0]["owner_id"] == "admin"

with app_module.app.test_request_context("/discussions"):
    session["username"] = "other-owner"
    session["firm_id"] = "FIRM-001"
    assert app_module.get_all_discussion_threads() == []

original_csrf = app_module.validate_csrf_token
app_module.validate_csrf_token = lambda: True

try:
    with app_module.app.test_request_context(
        "/discussions/THREAD-TEST-001/reply",
        method="POST",
        data={
            "message_id": "MSG-TEST-001",
            "parent_message_id": "",
            "body": "Finding 43 reply contract test.",
        },
    ):
        session["username"] = "admin"
        session["firm_id"] = "FIRM-001"

        response = app_module.discussion_reply("THREAD-TEST-001")
        assert response.status_code in (301, 302)
finally:
    app_module.validate_csrf_token = original_csrf

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

thread = conn.execute(
    "SELECT * FROM discussion_threads WHERE thread_id = ?",
    ("THREAD-TEST-001",),
).fetchone()

message = conn.execute(
    "SELECT * FROM discussion_messages WHERE message_id = ?",
    ("MSG-TEST-001",),
).fetchone()

assert thread is not None
assert thread["owner_id"] == "admin"

assert message is not None
assert message["thread_id"] == "THREAD-TEST-001"
assert message["owner_id"] == "admin"
assert message["body"] == "Finding 43 reply contract test."

conn.close()

reply_source = inspect.getsource(app_module.discussion_reply)
assert "get_next_discussion_message_id" not in reply_source
assert 'request.form.get("message_id")' in reply_source
assert 'Message ID and body are required.' in reply_source

print("FINDING_43_SUBPROCESS_CONTRACT=PASS")
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise AssertionError(
            f"discussion contract subprocess failed with {result.returncode}"
        )

    assert "FINDING_43_SUBPROCESS_CONTRACT=PASS" in result.stdout
