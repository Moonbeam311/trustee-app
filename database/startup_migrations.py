from __future__ import annotations

from pathlib import Path
from typing import Any

from database.migrations_matter_intake import (
    apply_matter_intake_bridge_schema,
)


def run_additive_startup_migrations(
    db_path: str | Path,
) -> dict[str, Any]:
    """
    Run additive and idempotent application schema migrations.

    This function may create missing schema objects. It must not infer,
    create, accept, reject, or end operational Matter–Intake links.
    """

    result = apply_matter_intake_bridge_schema(db_path)

    if not result.get("schema_complete"):
        raise RuntimeError(
            "Matter–Intake additive startup migration did not "
            "produce a complete schema."
        )

    return {
        "matter_intake_bridge": result,
        "operational_links_created": result.get("link_rows", 0),
        "operational_events_created": result.get("event_rows", 0),
    }
