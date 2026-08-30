"""Additive schema for governed Program promotion (V3-MOD-WLH-P07)."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class GovernedProgramPromotionMigrationError(RuntimeError):
    """Raised when the additive P07 schema cannot be installed safely."""


TABLES = (
    "fiduciary_authority_capabilities",
    "fiduciary_authority_capability_events",
    "governed_program_promotion_requests",
    "governed_program_promotions",
    "governed_program_promotion_events",
)


def apply_governed_program_promotion_schema(db_path: str | Path) -> dict[str, object]:
    """Install the idempotent P07 schema without creating lifecycle rows."""
    connection = sqlite3.connect(Path(db_path))
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS fiduciary_authority_capabilities (
                authority_grant_id TEXT PRIMARY KEY,
                firm_id TEXT NOT NULL,
                trust_id TEXT NOT NULL,
                fiduciary_id TEXT NOT NULL,
                principal_username TEXT NOT NULL,
                capability TEXT NOT NULL,
                authority_basis TEXT NOT NULL,
                source_reference TEXT NOT NULL,
                effective_at TEXT NOT NULL,
                expires_at TEXT,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(firm_id, trust_id, principal_username, capability, authority_grant_id)
            );

            CREATE INDEX IF NOT EXISTS idx_fiduciary_capability_scope
            ON fiduciary_authority_capabilities
                (firm_id, trust_id, principal_username, capability);

            CREATE TABLE IF NOT EXISTS fiduciary_authority_capability_events (
                authority_event_id TEXT PRIMARY KEY,
                authority_grant_id TEXT NOT NULL,
                event_type TEXT NOT NULL CHECK(event_type IN ('GRANTED', 'REVOKED')),
                actor_username TEXT NOT NULL,
                reason TEXT NOT NULL,
                event_at TEXT NOT NULL,
                event_idempotency_key TEXT NOT NULL UNIQUE,
                FOREIGN KEY(authority_grant_id)
                    REFERENCES fiduciary_authority_capabilities(authority_grant_id)
            );

            CREATE TABLE IF NOT EXISTS governed_program_promotion_requests (
                request_id TEXT PRIMARY KEY,
                firm_id TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                program_id TEXT NOT NULL,
                program_revision_id TEXT NOT NULL,
                trust_id TEXT NOT NULL,
                source_revision_sha256 TEXT NOT NULL,
                promotion_action TEXT NOT NULL CHECK(promotion_action = 'PROMOTE_SAVED_REVISION'),
                destination_family TEXT NOT NULL CHECK(destination_family = 'GOVERNED_PROGRAM_PROMOTION'),
                request_status TEXT NOT NULL CHECK(request_status IN ('PENDING','APPROVED','REJECTED','EXECUTED')),
                requested_by TEXT NOT NULL,
                requested_at TEXT NOT NULL,
                request_reason TEXT,
                approved_by TEXT,
                approval_authority_id TEXT,
                approval_reason TEXT,
                approved_at TEXT,
                rejected_by TEXT,
                rejection_reason TEXT,
                rejected_at TEXT,
                executed_by TEXT,
                executed_at TEXT,
                destination_record_id TEXT,
                promotion_event_id TEXT,
                idempotency_key TEXT NOT NULL UNIQUE,
                source_lock_key TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_promotion_request_scope
            ON governed_program_promotion_requests
                (firm_id, owner_id, workspace_id, program_id, trust_id, requested_at);

            CREATE TABLE IF NOT EXISTS governed_program_promotions (
                promotion_id TEXT PRIMARY KEY,
                governance_state TEXT NOT NULL CHECK(governance_state = 'GOVERNED_RECORDED'),
                firm_id TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                program_id TEXT NOT NULL,
                program_revision_id TEXT NOT NULL,
                trust_id TEXT NOT NULL,
                source_revision_sha256 TEXT NOT NULL,
                request_id TEXT NOT NULL UNIQUE,
                approved_by TEXT NOT NULL,
                approval_authority_id TEXT NOT NULL,
                executed_by TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                idempotency_key TEXT NOT NULL UNIQUE,
                FOREIGN KEY(request_id) REFERENCES governed_program_promotion_requests(request_id)
            );

            CREATE TABLE IF NOT EXISTS governed_program_promotion_events (
                event_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                event_type TEXT NOT NULL CHECK(event_type IN ('REQUESTED','APPROVED','REJECTED','PROMOTION_RECORDED')),
                prior_state TEXT,
                resulting_state TEXT NOT NULL CHECK(resulting_state IN ('PENDING','APPROVED','REJECTED','EXECUTED')),
                firm_id TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                program_id TEXT NOT NULL,
                program_revision_id TEXT NOT NULL,
                trust_id TEXT NOT NULL,
                actor_username TEXT NOT NULL,
                authority_grant_id TEXT,
                destination_record_id TEXT,
                reason TEXT,
                event_at TEXT NOT NULL,
                event_idempotency_key TEXT NOT NULL UNIQUE,
                FOREIGN KEY(request_id) REFERENCES governed_program_promotion_requests(request_id)
            );

            CREATE INDEX IF NOT EXISTS idx_promotion_event_request
            ON governed_program_promotion_events(request_id, event_at, event_id);

            CREATE TRIGGER IF NOT EXISTS p07_capability_events_no_update
            BEFORE UPDATE ON fiduciary_authority_capability_events
            BEGIN SELECT RAISE(ABORT, 'append_only'); END;
            CREATE TRIGGER IF NOT EXISTS p07_capability_events_no_delete
            BEFORE DELETE ON fiduciary_authority_capability_events
            BEGIN SELECT RAISE(ABORT, 'append_only'); END;
            CREATE TRIGGER IF NOT EXISTS p07_capabilities_no_update
            BEFORE UPDATE ON fiduciary_authority_capabilities
            BEGIN SELECT RAISE(ABORT, 'immutable_authority_grant'); END;
            CREATE TRIGGER IF NOT EXISTS p07_capabilities_no_delete
            BEFORE DELETE ON fiduciary_authority_capabilities
            BEGIN SELECT RAISE(ABORT, 'immutable_authority_grant'); END;
            CREATE TRIGGER IF NOT EXISTS p07_request_scope_no_update
            BEFORE UPDATE ON governed_program_promotion_requests
            WHEN NEW.firm_id != OLD.firm_id
              OR NEW.owner_id != OLD.owner_id
              OR NEW.workspace_id != OLD.workspace_id
              OR NEW.program_id != OLD.program_id
              OR NEW.program_revision_id != OLD.program_revision_id
              OR NEW.trust_id != OLD.trust_id
              OR NEW.source_revision_sha256 != OLD.source_revision_sha256
              OR NEW.promotion_action != OLD.promotion_action
              OR NEW.destination_family != OLD.destination_family
              OR NEW.requested_by != OLD.requested_by
              OR NEW.idempotency_key != OLD.idempotency_key
              OR NEW.source_lock_key != OLD.source_lock_key
            BEGIN SELECT RAISE(ABORT, 'immutable_request_scope'); END;
            CREATE TRIGGER IF NOT EXISTS p07_promotion_events_no_update
            BEFORE UPDATE ON governed_program_promotion_events
            BEGIN SELECT RAISE(ABORT, 'append_only'); END;
            CREATE TRIGGER IF NOT EXISTS p07_promotion_events_no_delete
            BEFORE DELETE ON governed_program_promotion_events
            BEGIN SELECT RAISE(ABORT, 'append_only'); END;
            CREATE TRIGGER IF NOT EXISTS p07_promotions_no_update
            BEFORE UPDATE ON governed_program_promotions
            BEGIN SELECT RAISE(ABORT, 'immutable_record'); END;
            CREATE TRIGGER IF NOT EXISTS p07_promotions_no_delete
            BEFORE DELETE ON governed_program_promotions
            BEGIN SELECT RAISE(ABORT, 'immutable_record'); END;
            """
        )
        connection.commit()
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in TABLES
        }
        return {"schema_complete": True, "rows": counts, "records_created": 0}
    except sqlite3.DatabaseError as exc:
        connection.rollback()
        raise GovernedProgramPromotionMigrationError(str(exc)) from exc
    finally:
        connection.close()
