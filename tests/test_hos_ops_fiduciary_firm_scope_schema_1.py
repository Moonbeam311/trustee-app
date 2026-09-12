import os
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_isolated(db_path, code):
    env = os.environ.copy()
    env["DB_PATH"] = str(db_path)

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, (
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    return result


def test_fresh_fiduciary_table_includes_firm_id(tmp_path):
    db_path = tmp_path / "fresh.db"

    run_isolated(
        db_path,
        """
from database import db

db.ensure_fiduciary_tables()

conn = db.get_connection()
cols = [
    row["name"]
    for row in conn.execute("PRAGMA table_info(fiduciaries)").fetchall()
]
conn.close()

assert "firm_id" in cols
""",
    )


def test_legacy_fiduciary_table_is_additively_migrated(tmp_path):
    db_path = tmp_path / "legacy.db"

    conn = sqlite3.connect(db_path)
    conn.execute(
        '''
        CREATE TABLE fiduciaries (
            fiduciary_id TEXT PRIMARY KEY,
            full_name TEXT,
            role_title TEXT,
            authority_scope TEXT,
            trust_id TEXT,
            appointment_date TEXT,
            effective_date TEXT,
            status TEXT,
            notes TEXT
        )
        '''
    )
    conn.execute(
        """
        INSERT INTO fiduciaries (
            fiduciary_id, full_name, role_title, authority_scope,
            trust_id, appointment_date, effective_date, status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "FID-001",
            "Legacy Fiduciary",
            "Trustee",
            "Legacy scope",
            "TR-LEGACY",
            None,
            None,
            "active",
            "preserve",
        ),
    )
    conn.commit()
    conn.close()

    run_isolated(
        db_path,
        """
from database import db

db.ensure_fiduciary_tables()

conn = db.get_connection()
cols = [
    row["name"]
    for row in conn.execute("PRAGMA table_info(fiduciaries)").fetchall()
]
row = conn.execute(
    "SELECT fiduciary_id, full_name, firm_id FROM fiduciaries "
    "WHERE fiduciary_id = ?",
    ("FID-001",),
).fetchone()
conn.close()

assert "firm_id" in cols
assert row["fiduciary_id"] == "FID-001"
assert row["full_name"] == "Legacy Fiduciary"
assert row["firm_id"] is None
""",
    )


def test_firm_scoped_fiduciary_provider_operates_after_schema_ensure(tmp_path):
    db_path = tmp_path / "provider.db"

    run_isolated(
        db_path,
        """
from flask import Flask, session
from database import db

app = Flask(__name__)
app.secret_key = "finding-30-test"

db.ensure_fiduciary_tables()

with app.test_request_context("/"):
    session["firm_id"] = "FIRM-DEMO-001"

    db.create_fiduciary_record({
        "fiduciary_id": "FID-001",
        "full_name": "Demo Fiduciary",
        "role_title": "Trustee",
        "authority_scope": "Training",
        "trust_id": "TR-DEMO-001",
        "status": "active",
        "notes": "Finding 30 regression fixture",
    })

    rows = db.get_all_fiduciaries()

    assert len(rows) == 1
    assert rows[0]["fiduciary_id"] == "FID-001"
    assert rows[0]["firm_id"] == "FIRM-DEMO-001"
""",
    )
