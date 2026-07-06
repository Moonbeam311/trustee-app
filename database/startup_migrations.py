from __future__ import annotations

from pathlib import Path
from typing import Any

from database.migrations_matter_intake import (
    apply_matter_intake_bridge_schema,
    MatterIntakeMigrationError,
)


def run_additive_startup_migrations(
    db_path: str | Path,
) -> dict[str, Any]:
    """
    Run additive and idempotent application schema migrations.

    This function may create missing schema objects. It must not infer,
    create, accept, reject, or end operational Matter–Intake links.
    """

    try:
        result = apply_matter_intake_bridge_schema(db_path)
    except MatterIntakeMigrationError as exc:
        # Hosted startup safety:
        # On Railway/Render a fresh mounted SQLite database may exist before
        # the full application schema has been created. The Matter–Intake
        # bridge is additive and must not block app boot if its source tables
        # are not present yet.
        result = {
            "schema_complete": False,
            "deferred": True,
            "reason": str(exc),
            "link_rows": 0,
            "event_rows": 0,
        }

    return {
        "matter_intake_bridge": result,
        "operational_links_created": result.get("link_rows", 0),
        "operational_events_created": result.get("event_rows", 0),
    }
