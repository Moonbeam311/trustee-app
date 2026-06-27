
from __future__ import annotations

import json
import os
import sqlite3

db_path = os.environ["DB_PATH"]


def count(table_name: str):
    connection = sqlite3.connect(db_path)

    try:
        exists = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
              AND name = ?
            """,
            (table_name,),
        ).fetchone()

        if exists is None:
            return None

        quoted = table_name.replace('"', '""')

        return connection.execute(
            f'SELECT COUNT(*) FROM "{quoted}"'
        ).fetchone()[0]

    finally:
        connection.close()


before = {
    "role_permissions": count("role_permissions"),
    "matter_intake_links": count("matter_intake_links"),
    "matter_intake_link_events": count(
        "matter_intake_link_events"
    ),
}

import app  # noqa: F401

after = {
    "role_permissions": count("role_permissions"),
    "matter_intake_links": count("matter_intake_links"),
    "matter_intake_link_events": count(
        "matter_intake_link_events"
    ),
}

print(
    json.dumps(
        {
            "db_path": db_path,
            "before": before,
            "after": after,
        }
    )
)
