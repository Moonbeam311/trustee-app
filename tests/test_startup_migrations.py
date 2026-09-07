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


    def test_hos_doc_generated_document_attribution_startup_is_additive_and_idempotent(
        self,
    ) -> None:
        connection = sqlite3.connect(self.db_path)

        connection.executescript(
            """
            CREATE TABLE generated_documents (
                document_id TEXT PRIMARY KEY,
                workspace_id TEXT,
                trust_id TEXT,
                template_id TEXT,
                title TEXT,
                content TEXT,
                status TEXT,
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                owner_id TEXT
            );

            INSERT INTO generated_documents (
                document_id,
                workspace_id,
                trust_id,
                template_id,
                title,
                content,
                status,
                created_by,
                owner_id
            )
            VALUES (
                'DOC-LEGACY-1',
                'WS-1',
                NULL,
                'TPL-1',
                'Legacy',
                'Body',
                'final',
                'legacy-user',
                'legacy-owner'
            );
            """
        )

        before = connection.execute(
            """
            SELECT document_id,
                   workspace_id,
                   trust_id,
                   template_id,
                   title,
                   content,
                   status,
                   created_by,
                   owner_id
            FROM generated_documents
            WHERE document_id = 'DOC-LEGACY-1'
            """
        ).fetchone()

        connection.commit()
        connection.close()

        first = run_additive_startup_migrations(
            self.db_path
        )
        second = run_additive_startup_migrations(
            self.db_path
        )

        attribution = first[
            "generated_document_attribution"
        ]
        repeated = second[
            "generated_document_attribution"
        ]

        self.assertTrue(
            attribution["schema_complete"]
        )
        self.assertFalse(
            attribution["deferred"]
        )
        self.assertEqual(
            attribution["columns_added"],
            4,
        )
        self.assertEqual(
            attribution["legacy_rows_preserved"],
            1,
        )
        self.assertEqual(
            attribution["legacy_rows_updated"],
            0,
        )
        self.assertEqual(
            attribution["records_created"],
            0,
        )

        self.assertTrue(
            repeated["schema_complete"]
        )
        self.assertEqual(
            repeated["columns_added"],
            0,
        )

        self.assertEqual(
            first[
                "generated_document_attribution_records_created"
            ],
            0,
        )
        self.assertEqual(
            second[
                "generated_document_attribution_records_created"
            ],
            0,
        )

        connection = sqlite3.connect(
            self.db_path
        )

        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(generated_documents)"
            ).fetchall()
        }

        self.assertTrue(
            {
                "firm_id",
                "source_record_type",
                "source_record_id",
                "generation_basis",
            }.issubset(columns)
        )

        after = connection.execute(
            """
            SELECT document_id,
                   workspace_id,
                   trust_id,
                   template_id,
                   title,
                   content,
                   status,
                   created_by,
                   owner_id
            FROM generated_documents
            WHERE document_id = 'DOC-LEGACY-1'
            """
        ).fetchone()

        attribution_fields = connection.execute(
            """
            SELECT firm_id,
                   source_record_type,
                   source_record_id,
                   generation_basis
            FROM generated_documents
            WHERE document_id = 'DOC-LEGACY-1'
            """
        ).fetchone()

        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM generated_documents
            """
        ).fetchone()[0]

        connection.close()

        self.assertEqual(after, before)
        self.assertEqual(
            attribution_fields,
            (None, None, None, None),
        )
        self.assertEqual(count, 1)


    def test_workspace_schema_is_fresh_safe_empty_and_idempotent(
        self,
    ) -> None:
        first = run_additive_startup_migrations(
            self.db_path
        )
        second = run_additive_startup_migrations(
            self.db_path
        )

        self.assertTrue(
            first["workspace_schema"]["schema_complete"]
        )
        self.assertTrue(
            second["workspace_schema"]["schema_complete"]
        )

        self.assertTrue(
            first["workspace_schema"]["table_created"]
        )
        self.assertFalse(
            second["workspace_schema"]["table_created"]
        )

        self.assertEqual(
            first["workspace_records_created"],
            0,
        )
        self.assertEqual(
            second["workspace_records_created"],
            0,
        )

        connection = sqlite3.connect(
            self.db_path
        )

        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(workspaces)"
            ).fetchall()
        }

        count = connection.execute(
            "SELECT COUNT(*) FROM workspaces"
        ).fetchone()[0]

        connection.close()

        self.assertTrue(
            {
                "workspace_id",
                "title",
                "workspace_type",
                "trust_type_focus",
                "purpose",
                "owner",
                "status",
                "owner_id",
                "firm_id",
                "created_at",
                "updated_at",
            }.issubset(columns)
        )

        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
