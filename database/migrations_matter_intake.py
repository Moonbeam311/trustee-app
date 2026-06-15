from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


LINK_TABLE = "matter_intake_links"
EVENT_TABLE = "matter_intake_link_events"


class MatterIntakeMigrationError(RuntimeError):
    """Raised when the Matter–Intake bridge cannot be installed safely."""


def _table_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> set[str]:
    quoted = table_name.replace('"', '""')

    rows = connection.execute(
        f'PRAGMA table_info("{quoted}")'
    ).fetchall()

    return {str(row[1]) for row in rows}


def _require_source_schema(
    connection: sqlite3.Connection,
) -> None:
    requirements = {
        "matters": {"matter_id", "firm_id"},
        "intake_sessions": {"intake_id", "firm_id"},
    }

    failures: list[str] = []

    for table_name, required_columns in requirements.items():
        columns = _table_columns(connection, table_name)

        if not columns:
            failures.append(
                f"Required source table {table_name!r} does not exist."
            )
            continue

        missing = sorted(required_columns - columns)

        if missing:
            failures.append(
                f"Required source table {table_name!r} is missing "
                f"column(s): {', '.join(missing)}."
            )

    if failures:
        raise MatterIntakeMigrationError(" ".join(failures))


def apply_matter_intake_bridge_schema(
    db_path: str | Path,
) -> dict[str, Any]:
    """
    Install the Matter–Intake bridge schema without creating any linkage rows.

    The migration is additive and idempotent. It does not alter the matters or
    intake_sessions tables and does not infer links from matching identifiers.
    """

    resolved = Path(db_path).expanduser().resolve()

    if not resolved.exists():
        raise MatterIntakeMigrationError(
            f"Database does not exist: {resolved}"
        )

    connection = sqlite3.connect(str(resolved))

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        _require_source_schema(connection)

        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS matter_intake_links (
                bridge_id TEXT PRIMARY KEY,
                firm_id TEXT NOT NULL,
                matter_id TEXT NOT NULL,
                intake_id TEXT NOT NULL,

                link_type TEXT NOT NULL DEFAULT 'PRIMARY'
                    CHECK (
                        link_type IN (
                            'PRIMARY',
                            'SUPPLEMENTAL',
                            'RENEWAL',
                            'CORRECTIVE',
                            'HISTORICAL'
                        )
                    ),

                link_status TEXT NOT NULL DEFAULT 'ACTIVE'
                    CHECK (
                        link_status IN (
                            'PROPOSED',
                            'ACTIVE',
                            'SUSPENDED',
                            'ENDED',
                            'REJECTED'
                        )
                    ),

                is_primary INTEGER NOT NULL DEFAULT 0
                    CHECK (is_primary IN (0, 1)),

                handoff_status TEXT NOT NULL DEFAULT 'PENDING'
                    CHECK (
                        handoff_status IN (
                            'PENDING',
                            'ACCEPTED',
                            'MODIFIED',
                            'REJECTED',
                            'SUPERSEDED'
                        )
                    ),

                handoff_by TEXT,
                handoff_at TEXT,

                recommendation_disposition TEXT
                    CHECK (
                        recommendation_disposition IS NULL
                        OR recommendation_disposition IN (
                            'PENDING',
                            'ACCEPTED',
                            'MODIFIED',
                            'REJECTED',
                            'PARTIALLY_ACCEPTED'
                        )
                    ),

                intake_snapshot_id TEXT,

                effective_at TEXT,
                ended_at TEXT,

                correction_basis TEXT,

                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                updated_by TEXT,
                updated_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                CHECK (
                    NOT (
                        link_status = 'ENDED'
                        AND ended_at IS NULL
                    )
                ),

                CHECK (
                    NOT (
                        is_primary = 1
                        AND link_type NOT IN (
                            'PRIMARY',
                            'RENEWAL',
                            'CORRECTIVE'
                        )
                    )
                )
            );

            CREATE TABLE IF NOT EXISTS matter_intake_link_events (
                event_id TEXT PRIMARY KEY,
                bridge_id TEXT NOT NULL,
                firm_id TEXT NOT NULL,

                event_type TEXT NOT NULL
                    CHECK (
                        event_type IN (
                            'LINK_PROPOSED',
                            'LINK_ACTIVATED',
                            'HANDOFF_ACCEPTED',
                            'HANDOFF_MODIFIED',
                            'HANDOFF_REJECTED',
                            'LINK_SUSPENDED',
                            'LINK_ENDED',
                            'PRIMARY_CHANGED',
                            'CORRECTION_RECORDED'
                        )
                    ),

                actor_id TEXT NOT NULL,
                event_basis TEXT,

                previous_state_json TEXT,
                new_state_json TEXT,

                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (bridge_id)
                    REFERENCES matter_intake_links(bridge_id)
                    ON DELETE RESTRICT
            );

            CREATE UNIQUE INDEX IF NOT EXISTS
                uq_matter_intake_active_pair
            ON matter_intake_links (
                firm_id,
                matter_id,
                intake_id
            )
            WHERE
                link_status = 'ACTIVE'
                AND ended_at IS NULL;

            CREATE UNIQUE INDEX IF NOT EXISTS
                uq_matter_intake_primary_intake
            ON matter_intake_links (
                firm_id,
                intake_id
            )
            WHERE
                is_primary = 1
                AND link_status = 'ACTIVE'
                AND ended_at IS NULL;

            CREATE INDEX IF NOT EXISTS
                ix_matter_intake_links_matter
            ON matter_intake_links (
                firm_id,
                matter_id,
                link_status
            );

            CREATE INDEX IF NOT EXISTS
                ix_matter_intake_links_intake
            ON matter_intake_links (
                firm_id,
                intake_id,
                link_status
            );

            CREATE INDEX IF NOT EXISTS
                ix_matter_intake_events_bridge
            ON matter_intake_link_events (
                firm_id,
                bridge_id,
                created_at
            );

            CREATE TRIGGER IF NOT EXISTS
                trg_matter_intake_insert_same_firm
            BEFORE INSERT ON matter_intake_links
            BEGIN
                SELECT CASE
                    WHEN NOT EXISTS (
                        SELECT 1
                        FROM matters
                        WHERE matter_id = NEW.matter_id
                          AND firm_id = NEW.firm_id
                    )
                    THEN RAISE(
                        ABORT,
                        'Matter does not exist in the bridge firm.'
                    )
                END;

                SELECT CASE
                    WHEN NOT EXISTS (
                        SELECT 1
                        FROM intake_sessions
                        WHERE intake_id = NEW.intake_id
                          AND firm_id = NEW.firm_id
                    )
                    THEN RAISE(
                        ABORT,
                        'Intake does not exist in the bridge firm.'
                    )
                END;
            END;

            CREATE TRIGGER IF NOT EXISTS
                trg_matter_intake_update_same_firm
            BEFORE UPDATE OF firm_id, matter_id, intake_id
            ON matter_intake_links
            BEGIN
                SELECT CASE
                    WHEN NOT EXISTS (
                        SELECT 1
                        FROM matters
                        WHERE matter_id = NEW.matter_id
                          AND firm_id = NEW.firm_id
                    )
                    THEN RAISE(
                        ABORT,
                        'Matter does not exist in the bridge firm.'
                    )
                END;

                SELECT CASE
                    WHEN NOT EXISTS (
                        SELECT 1
                        FROM intake_sessions
                        WHERE intake_id = NEW.intake_id
                          AND firm_id = NEW.firm_id
                    )
                    THEN RAISE(
                        ABORT,
                        'Intake does not exist in the bridge firm.'
                    )
                END;
            END;

            CREATE TRIGGER IF NOT EXISTS
                trg_matter_intake_event_same_firm
            BEFORE INSERT ON matter_intake_link_events
            BEGIN
                SELECT CASE
                    WHEN NOT EXISTS (
                        SELECT 1
                        FROM matter_intake_links
                        WHERE bridge_id = NEW.bridge_id
                          AND firm_id = NEW.firm_id
                    )
                    THEN RAISE(
                        ABORT,
                        'Bridge event firm does not match bridge firm.'
                    )
                END;
            END;

            CREATE TRIGGER IF NOT EXISTS
                trg_matter_intake_event_immutable_update
            BEFORE UPDATE ON matter_intake_link_events
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Matter–Intake bridge events are immutable.'
                );
            END;

            CREATE TRIGGER IF NOT EXISTS
                trg_matter_intake_event_immutable_delete
            BEFORE DELETE ON matter_intake_link_events
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Matter–Intake bridge events are immutable.'
                );
            END;
            """
        )

        connection.commit()

        return validate_matter_intake_bridge_schema(connection)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def validate_matter_intake_bridge_schema(
    connection_or_path: sqlite3.Connection | str | Path,
) -> dict[str, Any]:
    owns_connection = not isinstance(
        connection_or_path,
        sqlite3.Connection,
    )

    if owns_connection:
        connection = sqlite3.connect(
            str(Path(connection_or_path).expanduser().resolve())
        )
    else:
        connection = connection_or_path

    try:
        table_rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name IN (?, ?)
            ORDER BY name
            """,
            (LINK_TABLE, EVENT_TABLE),
        ).fetchall()

        index_rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'index'
              AND tbl_name IN (?, ?)
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """,
            (LINK_TABLE, EVENT_TABLE),
        ).fetchall()

        trigger_rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'trigger'
              AND tbl_name IN (?, ?)
            ORDER BY name
            """,
            (LINK_TABLE, EVENT_TABLE),
        ).fetchall()

        link_count = connection.execute(
            f"SELECT COUNT(*) FROM {LINK_TABLE}"
        ).fetchone()[0]

        event_count = connection.execute(
            f"SELECT COUNT(*) FROM {EVENT_TABLE}"
        ).fetchone()[0]

        tables = [row[0] for row in table_rows]
        indexes = [row[0] for row in index_rows]
        triggers = [row[0] for row in trigger_rows]

        required_indexes = {
            "uq_matter_intake_active_pair",
            "uq_matter_intake_primary_intake",
            "ix_matter_intake_links_matter",
            "ix_matter_intake_links_intake",
            "ix_matter_intake_events_bridge",
        }

        required_triggers = {
            "trg_matter_intake_insert_same_firm",
            "trg_matter_intake_update_same_firm",
            "trg_matter_intake_event_same_firm",
            "trg_matter_intake_event_immutable_update",
            "trg_matter_intake_event_immutable_delete",
        }

        return {
            "tables": tables,
            "indexes": indexes,
            "triggers": triggers,
            "link_rows": link_count,
            "event_rows": event_count,
            "schema_complete": (
                set(tables) == {LINK_TABLE, EVENT_TABLE}
                and required_indexes.issubset(indexes)
                and required_triggers.issubset(triggers)
            ),
        }

    finally:
        if owns_connection:
            connection.close()
