import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_COLUMNS = {
    "article_id",
    "title",
    "category",
    "subcategory",
    "trust_type",
    "summary",
    "body",
    "difficulty_level",
    "related_forms",
    "related_reports",
    "status",
    "created_at",
    "updated_at",
}


def test_learning_article_schema_and_empty_dashboard(tmp_path):
    db_path = tmp_path / "learning_schema.db"

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
        "PRAGMA table_info(learning_articles)"
    ).fetchall()
}

expected = {
    "article_id",
    "title",
    "category",
    "subcategory",
    "trust_type",
    "summary",
    "body",
    "difficulty_level",
    "related_forms",
    "related_reports",
    "status",
    "created_at",
    "updated_at",
}

assert columns == expected, (columns, expected)

count = conn.execute(
    "SELECT COUNT(*) FROM learning_articles"
).fetchone()[0]

assert count == 0

conn.close()

import app as app_module

client = app_module.app.test_client()

with client.session_transaction() as session:
    session["username"] = "learning-schema-test-operator"
    session["firm_id"] = "FIRM-LEARNING-TEST"
    session["role"] = "Admin"
    session["last_activity"] = time.time()

response = client.get("/learning")

assert response.status_code == 200, response.get_data(as_text=True)
'''

    subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )
