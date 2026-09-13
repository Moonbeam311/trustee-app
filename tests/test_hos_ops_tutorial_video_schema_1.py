import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_tutorial_video_schema_and_empty_dashboard(tmp_path):
    db_path = tmp_path / "tutorial_video_schema.db"

    env = os.environ.copy()
    env["DB_PATH"] = str(db_path)

    code = r'''
import os
import sqlite3
import time

from database.db import init_db

init_db()

conn = sqlite3.connect(os.environ["DB_PATH"])

columns = {
    row[1]
    for row in conn.execute(
        "PRAGMA table_info(tutorial_videos)"
    ).fetchall()
}

expected = {
    "video_id",
    "title",
    "category",
    "trust_type",
    "description",
    "file_path",
    "thumbnail_path",
    "transcript_notes",
    "visibility",
    "created_at",
    "updated_at",
}

assert columns == expected, (columns, expected)

count = conn.execute(
    "SELECT COUNT(*) FROM tutorial_videos"
).fetchone()[0]

assert count == 0
conn.close()

import app as app_module

client = app_module.app.test_client()

with client.session_transaction() as session:
    session["username"] = "video-schema-test-operator"
    session["firm_id"] = "FIRM-VIDEO-TEST"
    session["role"] = "Admin"
    session["last_activity"] = time.time()

response = client.get("/videos")
assert response.status_code == 200, response.get_data(as_text=True)

upload = client.get("/videos/upload")
assert upload.status_code == 200, upload.get_data(as_text=True)
'''

    subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )
