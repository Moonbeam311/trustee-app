import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import get_connection


def ensure_system_observation_registry():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS system_observation_number_sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                namespace TEXT NOT NULL,
                sequence_year INTEGER NOT NULL,
                last_number INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(namespace, sequence_year)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS system_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                observation_id TEXT NOT NULL UNIQUE,
                observation_type TEXT NOT NULL,
                panel_key TEXT NOT NULL,
                condition_code TEXT NOT NULL,
                current_state TEXT NOT NULL,
                persistence_trigger TEXT NOT NULL,
                context_scope TEXT NOT NULL,
                context_id TEXT,
                firm_id TEXT,
                institution_id TEXT,
                trust_id TEXT,
                matter_id TEXT,
                deployment_key TEXT,
                sanitized_summary TEXT NOT NULL,
                first_observed_at TEXT NOT NULL,
                last_observed_at TEXT NOT NULL,
                prior_occurrence_id TEXT,
                superseded_by_observation_id TEXT,
                active_duplicate_key TEXT,
                version INTEGER NOT NULL DEFAULT 1,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_by TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CHECK(version >= 1),
                CHECK(length(sanitized_summary) BETWEEN 1 AND 1000)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS system_observation_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                observation_event_id TEXT NOT NULL UNIQUE,
                observation_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                prior_state TEXT,
                resulting_state TEXT,
                actor_id TEXT NOT NULL,
                actor_label TEXT NOT NULL,
                authority_record_type TEXT,
                authority_record_id TEXT,
                event_summary TEXT,
                reason_code TEXT,
                related_record_type TEXT,
                related_record_id TEXT,
                idempotency_key TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(observation_id)
                    REFERENCES system_observations(observation_id)
                    ON DELETE RESTRICT
            )
            """
        )
        cur.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_system_observations_open_duplicate
            ON system_observations(active_duplicate_key)
            WHERE active_duplicate_key IS NOT NULL
            """
        )
        cur.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_system_observation_events_idempotency
            ON system_observation_events(idempotency_key)
            WHERE idempotency_key IS NOT NULL
            """
        )
        for statement in [
            "CREATE INDEX IF NOT EXISTS idx_system_observations_type ON system_observations(observation_type)",
            "CREATE INDEX IF NOT EXISTS idx_system_observations_condition ON system_observations(condition_code)",
            "CREATE INDEX IF NOT EXISTS idx_system_observations_state ON system_observations(current_state)",
            "CREATE INDEX IF NOT EXISTS idx_system_observations_context ON system_observations(context_scope, context_id)",
            "CREATE INDEX IF NOT EXISTS idx_system_observations_firm ON system_observations(firm_id)",
            "CREATE INDEX IF NOT EXISTS idx_system_observation_events_observation ON system_observation_events(observation_id)",
            "CREATE INDEX IF NOT EXISTS idx_system_observation_events_type ON system_observation_events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_system_observation_events_created ON system_observation_events(created_at)",
        ]:
            cur.execute(statement)
        conn.commit()
        return {"ok": True, "status": "verified"}
    except Exception as exc:
        conn.rollback()
        return {"ok": False, "status": "failed", "message": exc.__class__.__name__}
    finally:
        conn.close()


if __name__ == "__main__":
    result = ensure_system_observation_registry()
    print(f"system_observation_registry: {result['status']}")
    if not result.get("ok"):
        raise SystemExit(1)
