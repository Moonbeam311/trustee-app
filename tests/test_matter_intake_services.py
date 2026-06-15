from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from database.migrations_matter_intake import (
    apply_matter_intake_bridge_schema,
)
from services.services_matter_intake import (
    MatterIntakeConflictError,
    MatterIntakeNotFoundError,
    create_matter_intake_link,
    end_matter_intake_link,
    get_matter_intake_link,
    list_link_events,
    list_links_for_intake,
    list_links_for_matter,
    update_handoff,
)


class MatterIntakeServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "service_test.db"

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
                ('MAT-003', 'FIRM-001', 'Firm 1 Second Matter');

            INSERT INTO intake_sessions (
                intake_id,
                firm_id,
                status
            )
            VALUES
                ('INTAKE-001', 'FIRM-001', 'READY'),
                ('INTAKE-002', 'FIRM-002', 'READY'),
                ('INTAKE-003', 'FIRM-001', 'READY');
            """
        )

        connection.commit()
        connection.close()

        apply_matter_intake_bridge_schema(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_proposed_link_records_event(self) -> None:
        result = create_matter_intake_link(
            self.db_path,
            firm_id="FIRM-001",
            matter_id="MAT-001",
            intake_id="INTAKE-001",
            created_by="admin1",
            is_primary=True,
            event_basis="Initial handoff proposal",
        )

        self.assertEqual(result["link"]["bridge_id"], "MIB-000001")
        self.assertEqual(result["link"]["link_status"], "PROPOSED")
        self.assertEqual(result["event"]["event_id"], "MIBE-000001")
        self.assertEqual(
            result["event"]["event_type"],
            "LINK_PROPOSED",
        )

    def test_accept_handoff_activates_link(self) -> None:
        created = create_matter_intake_link(
            self.db_path,
            firm_id="FIRM-001",
            matter_id="MAT-001",
            intake_id="INTAKE-001",
            created_by="admin1",
            is_primary=True,
        )

        result = update_handoff(
            self.db_path,
            firm_id="FIRM-001",
            bridge_id=created["link"]["bridge_id"],
            handoff_status="ACCEPTED",
            actor_id="reviewer1",
            recommendation_disposition="MODIFIED",
            event_basis="Matter review completed",
        )

        self.assertEqual(result["link"]["link_status"], "ACTIVE")
        self.assertEqual(
            result["link"]["handoff_status"],
            "ACCEPTED",
        )
        self.assertEqual(
            result["event"]["event_type"],
            "HANDOFF_ACCEPTED",
        )

    def test_cross_firm_read_returns_none(self) -> None:
        created = create_matter_intake_link(
            self.db_path,
            firm_id="FIRM-001",
            matter_id="MAT-001",
            intake_id="INTAKE-001",
            created_by="admin1",
        )

        result = get_matter_intake_link(
            self.db_path,
            firm_id="FIRM-002",
            bridge_id=created["link"]["bridge_id"],
        )

        self.assertIsNone(result)

    def test_cross_firm_create_is_rejected(self) -> None:
        with self.assertRaises(MatterIntakeNotFoundError):
            create_matter_intake_link(
                self.db_path,
                firm_id="FIRM-001",
                matter_id="MAT-001",
                intake_id="INTAKE-002",
                created_by="admin1",
            )

    def test_duplicate_active_primary_is_rejected(self) -> None:
        create_matter_intake_link(
            self.db_path,
            firm_id="FIRM-001",
            matter_id="MAT-001",
            intake_id="INTAKE-001",
            created_by="admin1",
            link_status="ACTIVE",
            handoff_status="ACCEPTED",
            is_primary=True,
        )

        with self.assertRaises(MatterIntakeConflictError):
            create_matter_intake_link(
                self.db_path,
                firm_id="FIRM-001",
                matter_id="MAT-003",
                intake_id="INTAKE-001",
                created_by="admin1",
                link_status="ACTIVE",
                handoff_status="ACCEPTED",
                is_primary=True,
            )

    def test_list_services_are_firm_scoped(self) -> None:
        create_matter_intake_link(
            self.db_path,
            firm_id="FIRM-001",
            matter_id="MAT-001",
            intake_id="INTAKE-001",
            created_by="admin1",
        )

        create_matter_intake_link(
            self.db_path,
            firm_id="FIRM-002",
            matter_id="MAT-002",
            intake_id="INTAKE-002",
            created_by="admin2",
        )

        firm1_matter_links = list_links_for_matter(
            self.db_path,
            firm_id="FIRM-001",
            matter_id="MAT-001",
        )

        firm1_intake_links = list_links_for_intake(
            self.db_path,
            firm_id="FIRM-001",
            intake_id="INTAKE-001",
        )

        self.assertEqual(len(firm1_matter_links), 1)
        self.assertEqual(len(firm1_intake_links), 1)
        self.assertEqual(
            firm1_matter_links[0]["firm_id"],
            "FIRM-001",
        )

    def test_end_link_records_immutable_history(self) -> None:
        created = create_matter_intake_link(
            self.db_path,
            firm_id="FIRM-001",
            matter_id="MAT-001",
            intake_id="INTAKE-003",
            created_by="admin1",
            link_status="ACTIVE",
            handoff_status="ACCEPTED",
            is_primary=True,
        )

        result = end_matter_intake_link(
            self.db_path,
            firm_id="FIRM-001",
            bridge_id=created["link"]["bridge_id"],
            actor_id="admin1",
            event_basis="Intake superseded",
        )

        events = list_link_events(
            self.db_path,
            firm_id="FIRM-001",
            bridge_id=created["link"]["bridge_id"],
        )

        self.assertEqual(result["link"]["link_status"], "ENDED")
        self.assertEqual(result["link"]["is_primary"], 0)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[-1]["event_type"], "LINK_ENDED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
