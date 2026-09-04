from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from database.startup_migrations import (
    run_additive_startup_migrations,
)


class StartupMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "startup_test.db"

        connection = sqlite3.connect(self.db_path)

        connection.executescript(
            """
            CREATE TABLE matters (
                matter_id TEXT NOT NULL,
                firm_id TEXT NOT NULL,
                title TEXT,
                PRIMARY KEY (firm_id, matter_id)
            );

            CREATE TABLE intake_sessions (
                intake_id TEXT NOT NULL,
                firm_id TEXT NOT NULL,
                status TEXT,
                PRIMARY KEY (firm_id, intake_id)
            );

            CREATE TABLE role_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT NOT NULL,
                permission_name TEXT NOT NULL
            );

            CREATE TABLE permissions (
                permission_name TEXT PRIMARY KEY
            );

            INSERT INTO permissions VALUES ('matter_detail');

            INSERT INTO role_permissions (
                role_name,
                permission_name
            )
            VALUES
                ('Admin', 'matter_detail'),
                ('Admin', 'new_matter');
            """
        )

        connection.commit()
        connection.close()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_startup_migration_is_idempotent(self) -> None:
        first = run_additive_startup_migrations(self.db_path)
        second = run_additive_startup_migrations(self.db_path)

        self.assertTrue(
            first["matter_intake_bridge"]["schema_complete"]
        )
        self.assertTrue(
            second["matter_intake_bridge"]["schema_complete"]
        )

        self.assertEqual(first["operational_links_created"], 0)
        self.assertEqual(first["operational_events_created"], 0)
        self.assertEqual(second["operational_links_created"], 0)
        self.assertEqual(second["operational_events_created"], 0)

    def test_startup_migration_does_not_change_role_permissions(self) -> None:
        connection = sqlite3.connect(self.db_path)

        before = connection.execute(
            "SELECT COUNT(*) FROM role_permissions"
        ).fetchone()[0]

        connection.close()

        run_additive_startup_migrations(self.db_path)
        run_additive_startup_migrations(self.db_path)

        connection = sqlite3.connect(self.db_path)

        after = connection.execute(
            "SELECT COUNT(*) FROM role_permissions"
        ).fetchone()[0]

        connection.close()

        self.assertEqual(before, after)

    def test_p07_schema_is_idempotent_and_creates_no_lifecycle_rows(self) -> None:
        first = run_additive_startup_migrations(self.db_path)
        second = run_additive_startup_migrations(self.db_path)
        self.assertTrue(first["governed_program_promotion"]["schema_complete"])
        self.assertTrue(second["governed_program_promotion"]["schema_complete"])
        self.assertEqual(first["promotion_records_created"], 0)
        connection = sqlite3.connect(self.db_path)
        try:
            for table in (
                "fiduciary_authority_capabilities",
                "fiduciary_authority_capability_events",
                "governed_program_promotion_requests",
                "governed_program_promotions",
                "governed_program_promotion_events",
            ):
                self.assertEqual(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 0)
        finally:
            connection.close()

    def test_p09_schema_is_fresh_safe_empty_and_preserves_result_keys(self) -> None:
        before_connection = sqlite3.connect(self.db_path)
        before_permissions = tuple(before_connection.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0] for table in ("permissions", "role_permissions"))
        before_connection.close()
        result = run_additive_startup_migrations(self.db_path)
        repeated = run_additive_startup_migrations(self.db_path)
        self.assertTrue(result["work_learning_authority"]["schema_complete"])
        self.assertTrue(repeated["work_learning_authority"]["schema_complete"])
        self.assertIsInstance(result["work_learning_authority"], dict)
        self.assertEqual(result["authority_records_created"], 0)
        for legacy_key in ("matter_intake_bridge", "successor_acceptance", "governed_program_promotion", "operational_links_created", "operational_events_created", "acceptance_records_created", "promotion_records_created"):
            self.assertIn(legacy_key, result)
        connection = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(tuple(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ("permissions", "role_permissions")), before_permissions)
            for table in ("hub_program_authority_classifications", "hub_program_authority_relationships", "hub_program_authority_claims", "hub_program_authority_evidence", "hub_program_authority_verifications", "hub_program_authority_reviews", "hub_program_authority_determinations"):
                self.assertEqual(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 0)
                trigger_names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name=?", (table,))}
                self.assertEqual(trigger_names, {f"p09_{table}_no_update", f"p09_{table}_no_delete"})
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
