from __future__ import annotations

import sqlite3

from database.migrations_workspace_schema import (
    REQUIRED_COLUMNS,
    apply_workspace_schema,
)
from database.startup_migrations import (
    run_additive_startup_migrations,
)


def _columns(path):
    connection = sqlite3.connect(path)
    try:
        return {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(workspaces)"
            ).fetchall()
        }
    finally:
        connection.close()


def test_fresh_database_creates_complete_empty_workspace_schema(tmp_path):
    path = tmp_path / "fresh.db"

    first = apply_workspace_schema(path)
    second = apply_workspace_schema(path)

    assert first["schema_complete"] is True
    assert first["table_created"] is True
    assert first["records_created"] == 0

    assert second["schema_complete"] is True
    assert second["table_created"] is False
    assert second["columns_added"] == []
    assert second["records_created"] == 0

    assert set(REQUIRED_COLUMNS).issubset(_columns(path))

    connection = sqlite3.connect(path)
    try:
        assert connection.execute(
            "SELECT COUNT(*) FROM workspaces"
        ).fetchone()[0] == 0
    finally:
        connection.close()


def test_existing_legacy_workspace_row_is_preserved_without_backfill(tmp_path):
    path = tmp_path / "legacy.db"

    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE workspaces (
            workspace_id TEXT PRIMARY KEY,
            title TEXT,
            owner_id TEXT
        );

        INSERT INTO workspaces (
            workspace_id,
            title,
            owner_id
        )
        VALUES (
            'WS-LEGACY-1',
            'Legacy Workspace',
            'OWNER-LEGACY'
        );
        """
    )
    connection.commit()

    before = connection.execute(
        """
        SELECT workspace_id,
               title,
               owner_id
        FROM workspaces
        WHERE workspace_id = 'WS-LEGACY-1'
        """
    ).fetchone()

    connection.close()

    result = apply_workspace_schema(path)

    assert result["schema_complete"] is True
    assert result["table_created"] is False
    assert result["legacy_rows_preserved"] == 1
    assert result["legacy_rows_updated"] == 0

    assert set(REQUIRED_COLUMNS).issubset(_columns(path))

    connection = sqlite3.connect(path)
    try:
        after = connection.execute(
            """
            SELECT workspace_id,
                   title,
                   owner_id
            FROM workspaces
            WHERE workspace_id = 'WS-LEGACY-1'
            """
        ).fetchone()

        added_values = connection.execute(
            """
            SELECT workspace_type,
                   trust_type_focus,
                   purpose,
                   owner,
                   status,
                   firm_id,
                   created_at,
                   updated_at
            FROM workspaces
            WHERE workspace_id = 'WS-LEGACY-1'
            """
        ).fetchone()

        count = connection.execute(
            "SELECT COUNT(*) FROM workspaces"
        ).fetchone()[0]

    finally:
        connection.close()

    assert after == before
    assert added_values == (
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )
    assert count == 1


def test_workspace_schema_supports_firm_scoped_queries(tmp_path):
    path = tmp_path / "firm_scope.db"

    apply_workspace_schema(path)

    connection = sqlite3.connect(path)

    connection.execute(
        """
        INSERT INTO workspaces (
            workspace_id,
            title,
            owner_id,
            firm_id,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "WS-A",
            "Workspace A",
            "OWNER-A",
            "FIRM-A",
            "draft",
        ),
    )

    connection.execute(
        """
        INSERT INTO workspaces (
            workspace_id,
            title,
            owner_id,
            firm_id,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "WS-B",
            "Workspace B",
            "OWNER-B",
            "FIRM-B",
            "draft",
        ),
    )

    connection.commit()

    visible = connection.execute(
        """
        SELECT workspace_id
        FROM workspaces
        WHERE firm_id = ?
        ORDER BY workspace_id
        """,
        ("FIRM-A",),
    ).fetchall()

    connection.close()

    assert visible == [("WS-A",)]


def test_canonical_startup_path_creates_workspaces_on_empty_database(tmp_path):
    path = tmp_path / "empty_startup.db"

    first = run_additive_startup_migrations(path)
    second = run_additive_startup_migrations(path)

    assert first["workspace_schema"]["schema_complete"] is True
    assert first["workspace_schema"]["table_created"] is True

    assert second["workspace_schema"]["schema_complete"] is True
    assert second["workspace_schema"]["table_created"] is False

    assert first["workspace_records_created"] == 0
    assert second["workspace_records_created"] == 0

    assert set(REQUIRED_COLUMNS).issubset(_columns(path))
