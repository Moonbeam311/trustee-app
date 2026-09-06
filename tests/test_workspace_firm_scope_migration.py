import sqlite3

import database.db as dbmod


def _seed(db_path, with_workspaces=True):
    con = sqlite3.connect(db_path)

    con.execute("CREATE TABLE app_users (user_id TEXT PRIMARY KEY)")
    con.execute("CREATE TABLE audit_log (id INTEGER PRIMARY KEY)")
    con.execute("CREATE TABLE trusts (trust_id TEXT PRIMARY KEY)")

    if with_workspaces:
        con.execute(
            """
            CREATE TABLE workspaces (
                workspace_id TEXT PRIMARY KEY,
                title TEXT,
                owner_id TEXT
            )
            """
        )
        con.execute(
            """
            INSERT INTO workspaces
                (workspace_id, title, owner_id)
            VALUES
                ('WS-LEGACY-1', 'Legacy Workspace', 'ADMIN_OWNER_001')
            """
        )

    con.commit()
    con.close()


def test_workspace_firm_column_added_without_backfill(tmp_path, monkeypatch):
    db_path = tmp_path / "with_workspace.db"
    _seed(db_path)

    monkeypatch.setattr(dbmod, "DB_PATH", db_path)

    dbmod.ensure_firm_columns()
    dbmod.ensure_firm_columns()

    con = sqlite3.connect(db_path)

    columns = {
        row[1]
        for row in con.execute("PRAGMA table_info(workspaces)")
    }

    row = con.execute(
        """
        SELECT workspace_id, title, owner_id, firm_id
        FROM workspaces
        WHERE workspace_id = 'WS-LEGACY-1'
        """
    ).fetchone()

    con.close()

    assert "firm_id" in columns
    assert row == (
        "WS-LEGACY-1",
        "Legacy Workspace",
        "ADMIN_OWNER_001",
        None,
    )


def test_workspace_table_not_created_when_absent(tmp_path, monkeypatch):
    db_path = tmp_path / "without_workspace.db"
    _seed(db_path, with_workspaces=False)

    monkeypatch.setattr(dbmod, "DB_PATH", db_path)

    dbmod.ensure_firm_columns()
    dbmod.ensure_firm_columns()

    con = sqlite3.connect(db_path)

    count = con.execute(
        """
        SELECT COUNT(*)
        FROM sqlite_master
        WHERE type='table' AND name='workspaces'
        """
    ).fetchone()[0]

    con.close()

    assert count == 0
