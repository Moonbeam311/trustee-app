"""Explicit Focused-to-Guided intake bridge schema.

This module is intentionally non-automatic.  The caller must supply a database
path and explicitly invoke ``ensure_intake_bridge_table``.  Importing this
module never opens or mutates a database.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Union


PathLike = Union[str, Path]

BRIDGE_TABLE = "focused_guided_intake_bridges"

_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS {BRIDGE_TABLE} (
    bridge_id TEXT PRIMARY KEY,
    firm_id TEXT NOT NULL,
    focused_intake_id TEXT NOT NULL,
    person_id TEXT NOT NULL,
    guided_intake_id TEXT,
    guided_lane_key TEXT,
    bridge_status TEXT NOT NULL DEFAULT 'person_linked'
        CHECK (
            bridge_status IN (
                'person_linked',
                'guided_linked'
            )
        ),
    provenance_json TEXT NOT NULL DEFAULT '{{}}',
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (
        (
            guided_intake_id IS NULL
            AND guided_lane_key IS NULL
            AND bridge_status = 'person_linked'
        )
        OR
        (
            guided_intake_id IS NOT NULL
            AND guided_lane_key IS NOT NULL
            AND bridge_status = 'guided_linked'
        )
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS
    uq_focused_guided_bridge_focused
ON {BRIDGE_TABLE} (
    firm_id,
    focused_intake_id
);

CREATE UNIQUE INDEX IF NOT EXISTS
    uq_focused_guided_bridge_guided
ON {BRIDGE_TABLE} (
    firm_id,
    guided_intake_id
)
WHERE guided_intake_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS
    ix_focused_guided_bridge_person
ON {BRIDGE_TABLE} (
    firm_id,
    person_id
);
"""


def ensure_intake_bridge_table(db_path: PathLike) -> None:
    """Create the bridge table and indexes in the explicitly supplied DB.

    The operation is idempotent.  There is deliberately no default database
    path so this helper cannot silently target the Personal Firm database.
    """

    if db_path is None or str(db_path).strip() == "":
        raise ValueError("db_path is required")

    path = Path(db_path).expanduser()

    conn = sqlite3.connect(str(path))

    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()
