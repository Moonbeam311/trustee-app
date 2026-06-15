from __future__ import annotations

import ast
import json
import sqlite3
from pathlib import Path

import services.services_intake as intake_service


def build_intake_database(path: Path) -> None:
    connection = sqlite3.connect(path)

    try:
        connection.executescript(
            """
            CREATE TABLE intake_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intake_id TEXT UNIQUE NOT NULL,
                firm_id TEXT NOT NULL,
                intake_lane TEXT NOT NULL,
                user_posture TEXT,
                default_depth TEXT,
                risk_posture TEXT,
                professional_review_recommended INTEGER,
                automation_limits TEXT,
                next_screen TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT,
                created_by TEXT
            );

            CREATE TABLE intake_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intake_id TEXT UNIQUE NOT NULL,
                snapshot_json TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            """
        )

        connection.execute(
            """
            INSERT INTO intake_sessions (
                intake_id,
                firm_id,
                intake_lane,
                user_posture,
                default_depth,
                risk_posture,
                professional_review_recommended,
                automation_limits,
                next_screen,
                status,
                created_at,
                updated_at,
                created_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "INTAKE-FIRM-1",
                "FIRM-001",
                "new_planning",
                "planning",
                "standard",
                "moderate",
                1,
                "review required",
                "/intake/next",
                "completed",
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
                user_posture,
                default_depth,
                risk_posture,
                professional_review_recommended,
                automation_limits,
                next_screen,
                status,
                created_at,
                updated_at,
                created_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "INTAKE-FIRM-2",
                "FIRM-002",
                "new_planning",
                "planning",
                "standard",
                "moderate",
                1,
                "review required",
                "/intake/next",
                "completed",
                "2026-06-14T00:00:00",
                "2026-06-14T00:00:00",
                "tester",
            ),
        )

        connection.execute(
            """
            INSERT INTO intake_snapshots (
                intake_id,
                snapshot_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "INTAKE-FIRM-1",
                json.dumps(
                    {
                        "intake_id": "INTAKE-FIRM-1",
                        "review_priority": "High",
                    }
                ),
                "2026-06-14T00:00:00",
                "2026-06-14T00:00:00",
            ),
        )

        connection.execute(
            """
            INSERT INTO intake_snapshots (
                intake_id,
                snapshot_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "INTAKE-FIRM-2",
                json.dumps(
                    {
                        "intake_id": "INTAKE-FIRM-2",
                        "review_priority": "Normal",
                    }
                ),
                "2026-06-14T00:00:00",
                "2026-06-14T00:00:00",
            ),
        )

        connection.commit()

    finally:
        connection.close()


def test_scoped_intake_session_blocks_other_firm(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database = tmp_path / "intake_scope.db"
    build_intake_database(database)

    def scoped_connection():
        return sqlite3.connect(database)

    monkeypatch.setattr(
        intake_service,
        "get_connection",
        scoped_connection,
    )

    allowed = intake_service.get_intake_session_for_firm(
        "INTAKE-FIRM-1",
        "FIRM-001",
    )

    blocked = intake_service.get_intake_session_for_firm(
        "INTAKE-FIRM-1",
        "FIRM-002",
    )

    assert allowed is not None
    assert allowed["intake_id"] == "INTAKE-FIRM-1"
    assert blocked is None


def test_scoped_snapshot_checks_ownership_first(
    monkeypatch,
) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        intake_service,
        "get_intake_session_for_firm",
        lambda intake_id, firm_id: None,
    )

    def forbidden_legacy_lookup(intake_id):
        calls.append(intake_id)
        raise AssertionError(
            "Legacy lookup must not run after failed ownership."
        )

    monkeypatch.setattr(
        intake_service,
        "get_saved_client_snapshot",
        forbidden_legacy_lookup,
    )

    snapshot, result = (
        intake_service.get_saved_client_snapshot_for_firm(
            "INTAKE-CROSS-FIRM",
            "FIRM-002",
        )
    )

    assert snapshot is None
    assert result is None
    assert calls == []


def test_scoped_snapshot_delegates_after_ownership(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        intake_service,
        "get_intake_session_for_firm",
        lambda intake_id, firm_id: {
            "intake_id": intake_id,
        },
    )

    monkeypatch.setattr(
        intake_service,
        "get_saved_client_snapshot",
        lambda intake_id: (
            {"intake_id": intake_id},
            {"translations": ["ok"]},
        ),
    )

    snapshot, result = (
        intake_service.get_saved_client_snapshot_for_firm(
            "INTAKE-FIRM-1",
            "FIRM-001",
        )
    )

    assert snapshot["intake_id"] == "INTAKE-FIRM-1"
    assert result["translations"] == ["ok"]


def test_app_route_foundation_contract() -> None:
    root = Path(__file__).resolve().parents[1]
    app_path = root / "app.py"
    source = app_path.read_text(
        encoding="utf-8",
    )

    tree = ast.parse(source)

    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    snapshot_route = functions["intake_saved_snapshot"]
    matter_route = functions["matter_detail"]

    snapshot_source = ast.get_source_segment(
        source,
        snapshot_route,
    )

    matter_source = ast.get_source_segment(
        source,
        matter_route,
    )

    assert snapshot_source is not None
    assert matter_source is not None

    assert (
        "get_saved_client_snapshot_for_firm("
        in snapshot_source
    )

    assert (
        "list_links_for_intake("
        in snapshot_source
    )

    assert (
        "firm_id=firm_id"
        in snapshot_source
    )

    assert (
        "matter_intake_links=matter_intake_links"
        in snapshot_source
    )

    assert (
        "get_saved_client_snapshot(intake_id)"
        not in snapshot_source
    )

    assert (
        "list_links_for_matter("
        in matter_source
    )

    assert (
        "matter_intake_links=matter_intake_links"
        in matter_source
    )

    assert (
        "create_matter_intake_link("
        not in snapshot_source
    )

    assert (
        "create_matter_intake_link("
        not in matter_source
    )
