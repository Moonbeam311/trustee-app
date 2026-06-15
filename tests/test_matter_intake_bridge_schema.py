from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from database.migrations_matter_intake import (
    apply_matter_intake_bridge_schema,
)


class MatterIntakeBridgeSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "bridge_test.db"

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

            INSERT INTO matters (
                matter_id,
                firm_id,
                title
            )
            VALUES
                ('MAT-001', 'FIRM-001', 'Firm 1 Matter'),
                ('MAT-002', 'FIRM-002', 'Firm 2 Matter'),
                ('MAT-003', 'FIRM-001', 'Firm 1 Secondary Matter');

            INSERT INTO intake_sessions (
                intake_id,
                firm_id,
                status
            )
            VALUES
                ('INTAKE-001', 'FIRM-001', 'READY'),
                ('INTAKE-002', 'FIRM-002', 'READY');
            """
        )

        connection.commit()
        connection.close()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_migration_is_idempotent(self) -> None:
        first = apply_matter_intake_bridge_schema(self.db_path)
        second = apply_matter_intake_bridge_schema(self.db_path)

        self.assertTrue(first["schema_complete"])
        self.assertTrue(second["schema_complete"])
        self.assertEqual(first["link_rows"], 0)
        self.assertEqual(second["link_rows"], 0)

    def test_valid_same_firm_link_is_allowed(self) -> None:
        apply_matter_intake_bridge_schema(self.db_path)

        connection = sqlite3.connect(self.db_path)

        connection.execute(
            """
            INSERT INTO matter_intake_links (
                bridge_id,
                firm_id,
                matter_id,
                intake_id,
                link_type,
                link_status,
                is_primary,
                handoff_status,
                created_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "MIB-001",
                "FIRM-001",
                "MAT-001",
                "INTAKE-001",
                "PRIMARY",
                "ACTIVE",
                1,
                "ACCEPTED",
                "tester",
            ),
        )

        connection.commit()

        count = connection.execute(
            "SELECT COUNT(*) FROM matter_intake_links"
        ).fetchone()[0]

        connection.close()

        self.assertEqual(count, 1)

    def test_cross_firm_link_is_rejected(self) -> None:
        apply_matter_intake_bridge_schema(self.db_path)

        connection = sqlite3.connect(self.db_path)

        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO matter_intake_links (
                    bridge_id,
                    firm_id,
                    matter_id,
                    intake_id,
                    link_type,
                    link_status,
                    is_primary,
                    handoff_status,
                    created_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "MIB-002",
                    "FIRM-001",
                    "MAT-001",
                    "INTAKE-002",
                    "PRIMARY",
                    "ACTIVE",
                    1,
                    "ACCEPTED",
                    "tester",
                ),
            )

        connection.close()

    def test_second_active_primary_matter_is_rejected(self) -> None:
        apply_matter_intake_bridge_schema(self.db_path)

        connection = sqlite3.connect(self.db_path)

        connection.execute(
            """
            INSERT INTO matter_intake_links (
                bridge_id,
                firm_id,
                matter_id,
                intake_id,
                link_type,
                link_status,
                is_primary,
                handoff_status,
                created_by
            )
            VALUES (
                'MIB-003',
                'FIRM-001',
                'MAT-001',
                'INTAKE-001',
                'PRIMARY',
                'ACTIVE',
                1,
                'ACCEPTED',
                'tester'
            )
            """
        )

        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO matter_intake_links (
                    bridge_id,
                    firm_id,
                    matter_id,
                    intake_id,
                    link_type,
                    link_status,
                    is_primary,
                    handoff_status,
                    created_by
                )
                VALUES (
                    'MIB-004',
                    'FIRM-001',
                    'MAT-003',
                    'INTAKE-001',
                    'PRIMARY',
                    'ACTIVE',
                    1,
                    'ACCEPTED',
                    'tester'
                )
                """
            )

        connection.close()

    def test_bridge_events_are_immutable(self) -> None:
        apply_matter_intake_bridge_schema(self.db_path)

        connection = sqlite3.connect(self.db_path)
        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute(
            """
            INSERT INTO matter_intake_links (
                bridge_id,
                firm_id,
                matter_id,
                intake_id,
                link_type,
                link_status,
                is_primary,
                handoff_status,
                created_by
            )
            VALUES (
                'MIB-005',
                'FIRM-001',
                'MAT-001',
                'INTAKE-001',
                'PRIMARY',
                'ACTIVE',
                1,
                'ACCEPTED',
                'tester'
            )
            """
        )

        connection.execute(
            """
            INSERT INTO matter_intake_link_events (
                event_id,
                bridge_id,
                firm_id,
                event_type,
                actor_id,
                event_basis
            )
            VALUES (
                'MIBE-001',
                'MIB-005',
                'FIRM-001',
                'LINK_ACTIVATED',
                'tester',
                'Unit test'
            )
            """
        )

        connection.commit()

        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                """
                UPDATE matter_intake_link_events
                SET event_basis = 'Changed'
                WHERE event_id = 'MIBE-001'
                """
            )

        connection.rollback()

        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                """
                DELETE FROM matter_intake_link_events
                WHERE event_id = 'MIBE-001'
                """
            )

        connection.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
