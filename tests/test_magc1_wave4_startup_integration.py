from __future__ import annotations

import ast
import importlib
import sqlite3
import sys
from pathlib import Path

from database.migrations_magc1_wave4 import TABLES
from database.startup_migrations import run_additive_startup_migrations


STARTUP_MODULE = Path(__file__).parents[1] / "database" / "startup_migrations.py"


def _create_wave4_substrate(db_path: Path) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE hub_authority_applicability (
                applicability_id TEXT PRIMARY KEY
            );
            CREATE TABLE hub_authority_hierarchy_determinations (
                hierarchy_id TEXT PRIMARY KEY
            );
            CREATE TABLE hub_program_evidence_sufficiency_assessments (
                sufficiency_id TEXT PRIMARY KEY
            );
            CREATE TABLE pre_wave4_records (
                record_id TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            INSERT INTO pre_wave4_records VALUES ('existing-1', 'unchanged');
            """
        )


def test_canonical_startup_creates_empty_idempotent_wave4_schema(tmp_path):
    db_path = tmp_path / "wave4-startup.sqlite3"
    _create_wave4_substrate(db_path)

    first = run_additive_startup_migrations(db_path)
    second = run_additive_startup_migrations(db_path)

    assert first["magc1_wave4"]["schema_complete"] is True
    assert second["magc1_wave4"]["schema_complete"] is True
    assert first["magc1_wave4"]["records_created"] == 0
    assert second["magc1_wave4"]["records_created"] == 0
    assert first["magc1_wave4_records_created"] == 0
    assert second["magc1_wave4_records_created"] == 0

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert set(TABLES).issubset(tables)
        assert connection.execute(
            "SELECT record_id, value FROM pre_wave4_records"
        ).fetchall() == [("existing-1", "unchanged")]

        for table in TABLES:
            assert connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0] == 0
            triggers = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='trigger' AND tbl_name=?",
                    (table,),
                )
            }
            assert triggers == {
                f"w4_{table}_no_update",
                f"w4_{table}_no_delete",
            }


def test_import_is_inert_and_has_no_app_or_shadow_registry(tmp_path):
    db_path = tmp_path / "import-sentinel.sqlite3"
    _create_wave4_substrate(db_path)
    before = db_path.read_bytes()

    sys.modules.pop("database.startup_migrations", None)
    module = importlib.import_module("database.startup_migrations")

    assert db_path.read_bytes() == before
    assert callable(module.run_additive_startup_migrations)
    assert "app" not in sys.modules

    source = STARTUP_MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert "app" not in imports
    assert "database.migrations_magc1_wave4" in source
    assert source.count("def run_additive_startup_migrations(") == 1
    assert not any(
        isinstance(node, (ast.List, ast.Tuple))
        and any(
            isinstance(item, ast.Name)
            and item.id == "apply_magc1_wave4_schema"
            for item in node.elts
        )
        for node in ast.walk(tree)
    )
