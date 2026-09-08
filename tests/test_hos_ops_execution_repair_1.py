from __future__ import annotations

import sqlite3

from database.migrations_execution_task_schema import (
    REQUIRED_COLUMNS,
    apply_execution_task_schema,
)
from database.startup_migrations import run_additive_startup_migrations


def _columns(path):
    connection = sqlite3.connect(path)
    try:
        return {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(execution_tasks)"
            ).fetchall()
        }
    finally:
        connection.close()


def _count(path):
    connection = sqlite3.connect(path)
    try:
        return connection.execute(
            "SELECT COUNT(*) FROM execution_tasks"
        ).fetchone()[0]
    finally:
        connection.close()


def _table_sql(path):
    connection = sqlite3.connect(path)
    try:
        row = connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'execution_tasks'
            """
        ).fetchone()
        return row[0] if row else ""
    finally:
        connection.close()


def test_fresh_database_creates_complete_empty_execution_task_schema(tmp_path):
    path = tmp_path / "fresh.db"

    result = apply_execution_task_schema(path)

    assert result["schema_complete"] is True
    assert result["deferred"] is False
    assert result["table_created"] is True
    assert result["columns_added"] == []
    assert result["records_created"] == 0
    assert result["legacy_rows_updated"] == 0

    columns = _columns(path)
    assert set(REQUIRED_COLUMNS).issubset(columns)
    assert "id" in columns
    assert _count(path) == 0

    connection = sqlite3.connect(path)
    try:
        id_info = next(
            row
            for row in connection.execute(
                "PRAGMA table_info(execution_tasks)"
            ).fetchall()
            if row[1] == "id"
        )
    finally:
        connection.close()

    assert id_info[2].upper() == "INTEGER"
    assert id_info[5] == 1
    assert "ID INTEGER PRIMARY KEY AUTOINCREMENT" in _table_sql(path).upper()


def test_execution_task_schema_is_idempotent_and_seeds_no_rows(tmp_path):
    path = tmp_path / "idempotent.db"

    first = apply_execution_task_schema(path)
    second = apply_execution_task_schema(path)

    assert first["table_created"] is True
    assert second["schema_complete"] is True
    assert second["table_created"] is False
    assert second["columns_added"] == []
    assert second["legacy_rows_preserved"] == 0
    assert second["legacy_rows_updated"] == 0
    assert first["records_created"] == 0
    assert second["records_created"] == 0
    assert _count(path) == 0


def test_existing_execution_task_row_is_preserved_without_backfill(tmp_path):
    path = tmp_path / "legacy.db"

    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE execution_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT,
            title TEXT,
            owner_id TEXT,
            created_at TEXT
        );

        INSERT INTO execution_tasks (
            task_id,
            title,
            owner_id,
            created_at
        )
        VALUES (
            'TASK-LEGACY-1',
            'Legacy Task',
            'OWNER-LEGACY',
            '2026-04-24T00:00:00'
        );
        """
    )
    connection.commit()

    before = connection.execute(
        """
        SELECT id,
               task_id,
               title,
               owner_id,
               created_at
        FROM execution_tasks
        WHERE task_id = 'TASK-LEGACY-1'
        """
    ).fetchone()
    connection.close()

    result = apply_execution_task_schema(path)

    assert result["schema_complete"] is True
    assert result["table_created"] is False
    assert result["legacy_rows_preserved"] == 1
    assert result["legacy_rows_updated"] == 0
    assert result["records_created"] == 0
    assert set(REQUIRED_COLUMNS).issubset(_columns(path))

    connection = sqlite3.connect(path)
    try:
        after = connection.execute(
            """
            SELECT id,
                   task_id,
                   title,
                   owner_id,
                   created_at
            FROM execution_tasks
            WHERE task_id = 'TASK-LEGACY-1'
            """
        ).fetchone()

        added_values = connection.execute(
            """
            SELECT workspace_id,
                   trust_id,
                   task_type,
                   description,
                   related_form,
                   related_report,
                   priority,
                   status,
                   due_date,
                   assigned_to,
                   updated_at,
                   firm_id
            FROM execution_tasks
            WHERE task_id = 'TASK-LEGACY-1'
            """
        ).fetchone()

        count = connection.execute(
            "SELECT COUNT(*) FROM execution_tasks"
        ).fetchone()[0]
    finally:
        connection.close()

    assert after == before
    assert added_values == (None,) * 12
    assert count == 1


def test_execution_task_schema_supports_current_create_and_status_contract(tmp_path):
    path = tmp_path / "contract.db"

    apply_execution_task_schema(path)

    connection = sqlite3.connect(path)
    try:
        connection.execute(
            """
            INSERT INTO execution_tasks (
                task_id, workspace_id, trust_id, title, task_type, description,
                related_form, related_report, priority, status, due_date,
                assigned_to, owner_id, created_at, updated_at, firm_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                      CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
            """,
            (
                "TASK-CURRENT-1",
                "WS-CURRENT-1",
                "TR-CURRENT-1",
                "Current Task",
                "analysis",
                "Current contract test",
                "FORM-1",
                "REPORT-1",
                "medium",
                "pending",
                "2026-09-30",
                "demo-admin",
                "OWNER-CURRENT",
                "FIRM-DEMO-001",
            ),
        )
        connection.commit()

        row = connection.execute(
            """
            SELECT task_id,
                   workspace_id,
                   trust_id,
                   task_type,
                   related_form,
                   related_report,
                   status,
                   assigned_to,
                   owner_id,
                   firm_id,
                   created_at,
                   updated_at
            FROM execution_tasks
            WHERE task_id = ?
              AND firm_id = ?
            """,
            ("TASK-CURRENT-1", "FIRM-DEMO-001"),
        ).fetchone()

        connection.execute(
            """
            UPDATE execution_tasks
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ?
              AND firm_id = ?
            """,
            ("blocked", "TASK-CURRENT-1", "FIRM-OTHER"),
        )
        connection.commit()

        unchanged = connection.execute(
            """
            SELECT status
            FROM execution_tasks
            WHERE task_id = ?
            """,
            ("TASK-CURRENT-1",),
        ).fetchone()[0]

        connection.execute(
            """
            UPDATE execution_tasks
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ?
              AND firm_id = ?
            """,
            ("completed", "TASK-CURRENT-1", "FIRM-DEMO-001"),
        )
        connection.commit()

        updated = connection.execute(
            """
            SELECT status
            FROM execution_tasks
            WHERE task_id = ?
              AND firm_id = ?
            """,
            ("TASK-CURRENT-1", "FIRM-DEMO-001"),
        ).fetchone()[0]
    finally:
        connection.close()

    assert row[:10] == (
        "TASK-CURRENT-1",
        "WS-CURRENT-1",
        "TR-CURRENT-1",
        "analysis",
        "FORM-1",
        "REPORT-1",
        "pending",
        "demo-admin",
        "OWNER-CURRENT",
        "FIRM-DEMO-001",
    )
    assert row[10] is not None
    assert row[11] is not None
    assert unchanged == "pending"
    assert updated == "completed"
    assert _count(path) == 1


def test_canonical_startup_path_creates_execution_schema_idempotently(tmp_path):
    path = tmp_path / "startup.db"

    first = run_additive_startup_migrations(path)
    second = run_additive_startup_migrations(path)

    first_execution = first["execution_task_schema"]
    second_execution = second["execution_task_schema"]

    assert first_execution["schema_complete"] is True
    assert first_execution["table_created"] is True
    assert first_execution["records_created"] == 0

    assert second_execution["schema_complete"] is True
    assert second_execution["table_created"] is False
    assert second_execution["columns_added"] == []
    assert second_execution["records_created"] == 0

    assert first["execution_task_records_created"] == 0
    assert second["execution_task_records_created"] == 0
    assert set(REQUIRED_COLUMNS).issubset(_columns(path))
    assert _count(path) == 0
