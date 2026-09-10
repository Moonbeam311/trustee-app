import os
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CONTINUITY_COLUMNS = {
    "continuity_classification": ("TEXT", None),
    "custody_classification": ("TEXT", None),
    "continuity_priority": ("INTEGER", "0"),
    "heritage_significance": ("TEXT", None),
    "preservation_requirements": ("TEXT", None),
    "restricted_access_level": ("TEXT", None),
    "lineage_association": ("TEXT", None),
    "memorial_status": ("INTEGER", "0"),
    "sacred_status": ("INTEGER", "0"),
    "continuity_notes": ("TEXT", None),
}


def _run_init_db(db_path: Path) -> None:
    env = os.environ.copy()
    env["DB_PATH"] = str(db_path)

    code = """
from database import db as canonical_db
canonical_db.init_db()
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, (
        "canonical init_db failed\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def _property_schema(db_path: Path):
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("PRAGMA table_info(properties)").fetchall()
    finally:
        conn.close()

    return {
        row[1]: {
            "type": row[2],
            "default": row[4],
        }
        for row in rows
    }


def _assert_continuity_contract(schema):
    for column, (expected_type, expected_default) in CONTINUITY_COLUMNS.items():
        assert column in schema, f"missing continuity column: {column}"
        assert schema[column]["type"].upper() == expected_type
        assert schema[column]["default"] == expected_default


def test_fresh_init_creates_complete_continuity_property_schema(tmp_path):
    db_path = tmp_path / "fresh.db"

    _run_init_db(db_path)

    schema = _property_schema(db_path)
    _assert_continuity_contract(schema)


def test_existing_properties_table_is_migrated_to_continuity_contract(tmp_path):
    db_path = tmp_path / "legacy.db"

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE properties (
                property_id TEXT PRIMARY KEY,
                trust_id TEXT,
                property_name TEXT,
                property_type TEXT,
                address_or_identifier TEXT,
                acquisition_date TEXT,
                title_notes TEXT,
                beneficial_notes TEXT,
                status TEXT,
                asset_class TEXT,
                asset_subtype TEXT,
                established_date TEXT,
                effective_date TEXT,
                review_date TEXT,
                expiration_date TEXT,
                responsible_party TEXT,
                custodian TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO properties (
                property_id,
                trust_id,
                property_name,
                property_type
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "PROP-LEGACY-001",
                "TR-LEGACY-001",
                "Legacy Property",
                "artifact",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    _run_init_db(db_path)

    schema = _property_schema(db_path)
    _assert_continuity_contract(schema)

    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            """
            SELECT
                property_id,
                trust_id,
                continuity_priority,
                memorial_status,
                sacred_status
            FROM properties
            WHERE property_id = ?
            """,
            ("PROP-LEGACY-001",),
        ).fetchone()
    finally:
        conn.close()

    assert row == (
        "PROP-LEGACY-001",
        "TR-LEGACY-001",
        0,
        0,
        0,
    )
