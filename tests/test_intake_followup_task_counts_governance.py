import sqlite3

import services.services_intake as intake_service


TASK_SCHEMA = """
CREATE TABLE intake_followup_tasks (
    id INTEGER PRIMARY KEY,
    intake_id TEXT NOT NULL,
    firm_id TEXT NOT NULL,
    status TEXT
)
"""


def _db(tmp_path, governance=True):
    path = tmp_path / "followup-counts.db"

    with sqlite3.connect(path) as connection:
        connection.execute(TASK_SCHEMA)

        connection.executemany(
            """
            INSERT INTO intake_followup_tasks
                (id, intake_id, firm_id, status)
            VALUES (?, ?, ?, ?)
            """,
            [
                (1, "I1", "F1", "open"),
                (2, "I1", "F1", "completed"),
                (3, "I1", "F1", "pending_staff"),
                (4, "I1", "F1", "pending_client"),
                (5, "I1", "F1", "open"),
                (6, "I2", "F1", "pending_staff"),
                (7, "I1", "F2", "open"),
            ],
        )

        if governance:
            connection.execute("""
                CREATE TABLE intake_followup_reconciliations (
                    reconciliation_id TEXT PRIMARY KEY,
                    firm_id TEXT NOT NULL,
                    intake_id TEXT NOT NULL,
                    superseded_followup_task_id INTEGER NOT NULL,
                    replacement_followup_task_id INTEGER NOT NULL
                )
            """)

            connection.execute(
                """
                INSERT INTO intake_followup_reconciliations
                    (
                        reconciliation_id,
                        firm_id,
                        intake_id,
                        superseded_followup_task_id,
                        replacement_followup_task_id
                    )
                VALUES ('REC-1', 'F1', 'I1', 3, 1)
                """
            )

            connection.execute("""
                CREATE TABLE intake_followup_task_lifecycle_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    intake_id TEXT NOT NULL,
                    firm_id TEXT NOT NULL,
                    event_type TEXT NOT NULL
                )
            """)

            connection.executemany(
                """
                INSERT INTO intake_followup_task_lifecycle_events
                    (task_id, intake_id, firm_id, event_type)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (4, "I1", "F1", "no_successor_retired"),
                    (5, "I1", "F1", "no_successor_retired"),
                    (5, "I1", "F1", "reactivated"),
                ],
            )

    return path


def _configure(monkeypatch, path):
    monkeypatch.setattr(
        intake_service,
        "ensure_intake_followup_task_tables",
        lambda: None,
    )
    monkeypatch.setattr(
        intake_service,
        "get_current_firm_id",
        lambda: "F1",
    )
    monkeypatch.setattr(
        intake_service,
        "get_connection",
        lambda: sqlite3.connect(path),
    )


def test_counts_exclude_reconciled_and_effectively_retired_tasks(
    tmp_path, monkeypatch
):
    path = _db(tmp_path, governance=True)
    _configure(monkeypatch, path)

    counts = intake_service.get_intake_followup_task_counts()

    assert counts == {
        "I1": {
            "task_count": 3,
            "completed_task_count": 1,
            "open_task_count": 2,
        },
        "I2": {
            "task_count": 1,
            "completed_task_count": 0,
            "open_task_count": 1,
        },
    }


def test_latest_reactivated_event_restores_task_to_counts(
    tmp_path, monkeypatch
):
    path = _db(tmp_path, governance=True)
    _configure(monkeypatch, path)

    counts = intake_service.get_intake_followup_task_counts()

    # Task 5 was retired and then reactivated; latest lifecycle wins.
    assert counts["I1"]["task_count"] == 3
    assert counts["I1"]["open_task_count"] == 2


def test_counts_preserve_legacy_behavior_when_governance_tables_absent(
    tmp_path, monkeypatch
):
    path = _db(tmp_path, governance=False)
    _configure(monkeypatch, path)

    counts = intake_service.get_intake_followup_task_counts()

    assert counts == {
        "I1": {
            "task_count": 5,
            "completed_task_count": 1,
            "open_task_count": 4,
        },
        "I2": {
            "task_count": 1,
            "completed_task_count": 0,
            "open_task_count": 1,
        },
    }


def test_dashboard_uses_governed_firm_scoped_counts(
    tmp_path, monkeypatch
):
    path = _db(tmp_path, governance=True)
    _configure(monkeypatch, path)

    monkeypatch.setattr(
        intake_service,
        "list_intake_dashboard_with_review_notes",
        lambda limit=100, status_filter="all": [
            {"intake_id": "I1"},
            {"intake_id": "I2"},
        ],
    )

    items = intake_service.list_intake_dashboard_with_tasks()

    assert items == [
        {
            "intake_id": "I1",
            "task_count": 3,
            "open_task_count": 2,
            "completed_task_count": 1,
            "has_tasks": True,
        },
        {
            "intake_id": "I2",
            "task_count": 1,
            "open_task_count": 1,
            "completed_task_count": 0,
            "has_tasks": True,
        },
    ]
