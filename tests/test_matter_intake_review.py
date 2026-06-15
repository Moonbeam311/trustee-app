from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from database.migrations_matter_intake import (
    apply_matter_intake_bridge_schema,
)
from services.services_matter_intake import (
    MatterIntakeConflictError,
    create_matter_intake_link,
    get_matter_intake_link,
    list_link_events,
    review_matter_intake_handoff,
)


def connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def build_database(path: Path) -> None:
    connection = connect(path)

    try:
        connection.executescript(
            """
            CREATE TABLE matters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matter_id TEXT UNIQUE NOT NULL,
                firm_id TEXT NOT NULL,
                title TEXT NOT NULL,
                matter_type TEXT NOT NULL,
                status TEXT DEFAULT 'Open',
                priority TEXT DEFAULT 'Normal',
                jurisdiction TEXT,
                lead_fiduciary TEXT,
                governance_state TEXT DEFAULT 'Intake',
                risk_level TEXT DEFAULT 'Unrated',
                archive_status TEXT DEFAULT 'Not Archived',
                purpose TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE matter_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                matter_id TEXT NOT NULL,
                firm_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor TEXT,
                authority_basis TEXT,
                description TEXT NOT NULL,
                linked_record_type TEXT,
                linked_record_id TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE intake_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intake_id TEXT UNIQUE NOT NULL,
                firm_id TEXT NOT NULL,
                intake_lane TEXT NOT NULL,
                status TEXT DEFAULT 'lane_selected',
                created_at TEXT,
                updated_at TEXT,
                created_by TEXT
            );
            """
        )

        connection.execute(
            """
            INSERT INTO matters (
                matter_id,
                firm_id,
                title,
                matter_type,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "MAT-TEST-001",
                "FIRM-001",
                "Atomic Review Matter",
                "Trust Formation",
                "2026-06-14T00:00:00",
                "2026-06-14T00:00:00",
            ),
        )

        connection.execute(
            """
            INSERT INTO matters (
                matter_id,
                firm_id,
                title,
                matter_type,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "MAT-TEST-002",
                "FIRM-002",
                "Other Firm Matter",
                "Trust Formation",
                "2026-06-14T00:00:00",
                "2026-06-14T00:00:00",
            ),
        )

        connection.execute(
            """
            INSERT INTO intake_sessions (
                intake_id,
                firm_id,
                intake_lane,
                created_at,
                updated_at,
                created_by
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "INTAKE-TEST-001",
                "FIRM-001",
                "new_planning",
                "2026-06-14T00:00:00",
                "2026-06-14T00:00:00",
                "tester",
            ),
        )

        connection.execute(
            """
            INSERT INTO intake_sessions (
                intake_id,
                firm_id,
                intake_lane,
                created_at,
                updated_at,
                created_by
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "INTAKE-TEST-002",
                "FIRM-002",
                "new_planning",
                "2026-06-14T00:00:00",
                "2026-06-14T00:00:00",
                "tester",
            ),
        )

        connection.commit()

    finally:
        connection.close()

    apply_matter_intake_bridge_schema(path)


def create_proposed_bridge(
    path: Path,
    *,
    firm_id: str = "FIRM-001",
    matter_id: str = "MAT-TEST-001",
    intake_id: str = "INTAKE-TEST-001",
) -> str:
    created = create_matter_intake_link(
        path,
        firm_id=firm_id,
        matter_id=matter_id,
        intake_id=intake_id,
        created_by="tester",
        link_type="PRIMARY",
        link_status="PROPOSED",
        is_primary=True,
        handoff_status="PENDING",
        recommendation_disposition="PENDING",
        event_basis="Proposed for review",
    )

    return created["link"]["bridge_id"]


def test_acceptance_is_atomic(tmp_path: Path) -> None:
    database = tmp_path / "acceptance.db"
    build_database(database)

    bridge_id = create_proposed_bridge(database)

    result = review_matter_intake_handoff(
        database,
        firm_id="FIRM-001",
        bridge_id=bridge_id,
        handoff_status="ACCEPTED",
        actor_id="reviewer",
        recommendation_disposition="ACCEPTED",
        event_basis="Reviewed and accepted",
    )

    assert result["link"]["link_status"] == "ACTIVE"
    assert result["link"]["handoff_status"] == "ACCEPTED"
    assert (
        result["bridge_event"]["event_type"]
        == "HANDOFF_ACCEPTED"
    )
    assert (
        result["matter_event"]["event_type"]
        == "Intake Handoff Accepted"
    )
    assert (
        result["matter_event"]["linked_record_id"]
        == bridge_id
    )

    connection = connect(database)

    try:
        matter_event = connection.execute(
            """
            SELECT *
            FROM matter_events
            WHERE firm_id = ?
              AND linked_record_id = ?
            """,
            (
                "FIRM-001",
                bridge_id,
            ),
        ).fetchone()

        assert matter_event is not None
        assert matter_event["event_id"] == "MEV-000001"

    finally:
        connection.close()

    events = list_link_events(
        database,
        firm_id="FIRM-001",
        bridge_id=bridge_id,
    )

    assert [
        event["event_type"]
        for event in events
    ] == [
        "LINK_PROPOSED",
        "HANDOFF_ACCEPTED",
    ]


def test_rejection_preserves_bridge(tmp_path: Path) -> None:
    database = tmp_path / "rejection.db"
    build_database(database)

    bridge_id = create_proposed_bridge(database)

    result = review_matter_intake_handoff(
        database,
        firm_id="FIRM-001",
        bridge_id=bridge_id,
        handoff_status="REJECTED",
        actor_id="reviewer",
        recommendation_disposition="REJECTED",
        event_basis="Insufficient review basis",
    )

    assert result["link"]["link_status"] == "REJECTED"
    assert result["link"]["handoff_status"] == "REJECTED"

    stored = get_matter_intake_link(
        database,
        firm_id="FIRM-001",
        bridge_id=bridge_id,
    )

    assert stored is not None
    assert stored["link_status"] == "REJECTED"


def test_cross_firm_review_is_blocked(
    tmp_path: Path,
) -> None:
    database = tmp_path / "scope.db"
    build_database(database)

    bridge_id = create_proposed_bridge(database)

    with pytest.raises(Exception):
        review_matter_intake_handoff(
            database,
            firm_id="FIRM-002",
            bridge_id=bridge_id,
            handoff_status="ACCEPTED",
            actor_id="wrong-firm-reviewer",
            recommendation_disposition="ACCEPTED",
            event_basis="Cross-firm attempt",
        )

    stored = get_matter_intake_link(
        database,
        firm_id="FIRM-001",
        bridge_id=bridge_id,
    )

    assert stored is not None
    assert stored["link_status"] == "PROPOSED"
    assert stored["handoff_status"] == "PENDING"


def test_matter_event_failure_rolls_back_everything(
    tmp_path: Path,
) -> None:
    database = tmp_path / "rollback.db"
    build_database(database)

    bridge_id = create_proposed_bridge(database)

    connection = connect(database)

    try:
        connection.execute(
            """
            CREATE TRIGGER force_matter_event_failure
            BEFORE INSERT ON matter_events
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'forced matter event failure'
                );
            END;
            """
        )
        connection.commit()

    finally:
        connection.close()

    with pytest.raises(MatterIntakeConflictError):
        review_matter_intake_handoff(
            database,
            firm_id="FIRM-001",
            bridge_id=bridge_id,
            handoff_status="ACCEPTED",
            actor_id="reviewer",
            recommendation_disposition="ACCEPTED",
            event_basis="Rollback test",
        )

    stored = get_matter_intake_link(
        database,
        firm_id="FIRM-001",
        bridge_id=bridge_id,
    )

    assert stored is not None
    assert stored["link_status"] == "PROPOSED"
    assert stored["handoff_status"] == "PENDING"

    events = list_link_events(
        database,
        firm_id="FIRM-001",
        bridge_id=bridge_id,
    )

    assert [
        event["event_type"]
        for event in events
    ] == [
        "LINK_PROPOSED",
    ]

    connection = connect(database)

    try:
        matter_event_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM matter_events
            WHERE firm_id = ?
              AND linked_record_id = ?
            """,
            (
                "FIRM-001",
                bridge_id,
            ),
        ).fetchone()[0]

        assert matter_event_count == 0

    finally:
        connection.close()


def test_matter_event_identifier_skips_gaps(
    tmp_path: Path,
) -> None:
    database = tmp_path / "identifier.db"
    build_database(database)

    connection = connect(database)

    try:
        connection.execute(
            """
            INSERT INTO matter_events (
                event_id,
                matter_id,
                firm_id,
                event_type,
                actor,
                authority_basis,
                description,
                linked_record_type,
                linked_record_id,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "MEV-000010",
                "MAT-TEST-001",
                "FIRM-001",
                "Historical Test",
                "tester",
                "Identifier test",
                "Historical fixture",
                "",
                "",
                "2026-06-14T00:00:00",
            ),
        )

        connection.commit()

    finally:
        connection.close()

    bridge_id = create_proposed_bridge(database)

    result = review_matter_intake_handoff(
        database,
        firm_id="FIRM-001",
        bridge_id=bridge_id,
        handoff_status="ACCEPTED",
        actor_id="reviewer",
        recommendation_disposition="ACCEPTED",
        event_basis="Identifier validation",
    )

    assert (
        result["matter_event"]["event_id"]
        == "MEV-000011"
    )
