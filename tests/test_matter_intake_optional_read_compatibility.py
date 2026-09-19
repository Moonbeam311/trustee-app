from __future__ import annotations

import sqlite3
from pathlib import Path

from services.services_matter_intake import (
    list_links_for_intake,
    list_links_for_matter,
)


def _table_exists(
    database: Path,
    table_name: str,
) -> bool:
    connection = sqlite3.connect(database)

    try:
        row = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
              AND name = ?
            """,
            (table_name,),
        ).fetchone()

        return row is not None

    finally:
        connection.close()


def test_optional_bridge_reads_return_empty_when_schema_absent(
    tmp_path: Path,
) -> None:
    database = tmp_path / "optional_bridge_absent.sqlite3"

    # Create a valid SQLite file with the Intake source table only.
    # Personal Firm currently has Intake capability but not the Matter
    # source schema required by the Matter–Intake bridge migration.
    connection = sqlite3.connect(database)

    try:
        connection.execute(
            """
            CREATE TABLE intake_sessions (
                intake_id TEXT NOT NULL,
                firm_id TEXT NOT NULL,
                PRIMARY KEY (firm_id, intake_id)
            )
            """
        )

        connection.execute(
            """
            INSERT INTO intake_sessions (
                intake_id,
                firm_id
            )
            VALUES (?, ?)
            """,
            (
                "INTAKE-0001",
                "FIRM-001",
            ),
        )

        connection.commit()

    finally:
        connection.close()

    assert not _table_exists(
        database,
        "matter_intake_links",
    )

    assert not _table_exists(
        database,
        "matter_intake_link_events",
    )

    assert list_links_for_intake(
        database,
        firm_id="FIRM-001",
        intake_id="INTAKE-0001",
    ) == []

    assert list_links_for_matter(
        database,
        firm_id="FIRM-001",
        matter_id="MAT-DOES-NOT-EXIST",
    ) == []

    # A read-only compatibility call must not install bridge schema.
    assert not _table_exists(
        database,
        "matter_intake_links",
    )

    assert not _table_exists(
        database,
        "matter_intake_link_events",
    )


def test_existing_bridge_behavior_remains_available(
    tmp_path: Path,
) -> None:
    database = tmp_path / "existing_bridge.sqlite3"

    connection = sqlite3.connect(database)

    try:
        connection.executescript(
            """
            CREATE TABLE matter_intake_links (
                bridge_id TEXT PRIMARY KEY,
                firm_id TEXT NOT NULL,
                matter_id TEXT NOT NULL,
                intake_id TEXT NOT NULL,
                link_status TEXT NOT NULL,
                is_primary INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            INSERT INTO matter_intake_links (
                bridge_id,
                firm_id,
                matter_id,
                intake_id,
                link_status,
                is_primary,
                created_at
            )
            VALUES (
                'MIB-000001',
                'FIRM-001',
                'MAT-001',
                'INTAKE-0001',
                'ACTIVE',
                1,
                '2026-09-19T00:00:00'
            );
            """
        )

        connection.commit()

    finally:
        connection.close()

    intake_links = list_links_for_intake(
        database,
        firm_id="FIRM-001",
        intake_id="INTAKE-0001",
    )

    matter_links = list_links_for_matter(
        database,
        firm_id="FIRM-001",
        matter_id="MAT-001",
    )

    assert len(intake_links) == 1
    assert len(matter_links) == 1

    assert intake_links[0]["bridge_id"] == "MIB-000001"
    assert matter_links[0]["bridge_id"] == "MIB-000001"
