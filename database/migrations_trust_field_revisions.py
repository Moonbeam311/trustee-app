"""Additive schema for canonical Trust field revision history."""

from __future__ import annotations

import sqlite3
from pathlib import Path


REQUIRED_TRUST_COLUMNS = {"trust_id", "firm_id", "owner_id"}
REQUIRED_REVISION_COLUMNS = {
    "revision_id",
    "firm_id",
    "owner_id",
    "trust_id",
    "field_name",
    "revision_number",
    "prior_value",
    "resulting_value",
    "revision_basis",
    "provenance",
    "decision_origin",
    "human_confirmed",
    "actor_id",
    "actor_capacity",
    "prior_revision_id",
    "created_at",
}


class TrustFieldRevisionMigrationError(RuntimeError):
    """Raised when the revision schema cannot be installed safely."""


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {
        row[1]
        for row in connection.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    }


def apply_trust_field_revision_schema(db_path: str | Path) -> None:
    """Install the append-only Trust revision schema without changing Trust rows."""

    connection = sqlite3.connect(str(Path(db_path)))
    try:
        trust_columns = _table_columns(connection, "trusts")
        missing = REQUIRED_TRUST_COLUMNS - trust_columns
        if missing:
            raise TrustFieldRevisionMigrationError(
                "trusts table missing required columns: " + ", ".join(sorted(missing))
            )

        revision_columns = _table_columns(connection, "trust_field_revisions")
        if revision_columns:
            missing = REQUIRED_REVISION_COLUMNS - revision_columns
            if missing:
                raise TrustFieldRevisionMigrationError(
                    "existing trust_field_revisions table missing required columns: "
                    + ", ".join(sorted(missing))
                )

        connection.executescript(
            """
            BEGIN IMMEDIATE;

            CREATE TABLE IF NOT EXISTS trust_field_revisions (
                revision_id TEXT PRIMARY KEY,
                firm_id TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                trust_id TEXT NOT NULL,
                field_name TEXT NOT NULL,
                revision_number INTEGER NOT NULL,
                prior_value TEXT,
                resulting_value TEXT,
                revision_basis TEXT NOT NULL,
                provenance TEXT NOT NULL,
                decision_origin TEXT NOT NULL CHECK (
                    decision_origin IN (
                        'SYSTEM_SUGGESTED',
                        'OPERATOR_OR_FIDUCIARY',
                        'PROFESSIONAL'
                    )
                ),
                human_confirmed INTEGER NOT NULL CHECK (human_confirmed IN (0, 1)),
                actor_id TEXT NOT NULL,
                actor_capacity TEXT NOT NULL,
                prior_revision_id TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(firm_id, owner_id, trust_id, field_name, revision_number),
                FOREIGN KEY(prior_revision_id)
                    REFERENCES trust_field_revisions(revision_id)
            );

            CREATE INDEX IF NOT EXISTS idx_trust_field_revisions_scope
                ON trust_field_revisions(
                    firm_id, owner_id, trust_id, field_name, revision_number
                );

            CREATE TRIGGER IF NOT EXISTS trust_field_revisions_scope_insert
            BEFORE INSERT ON trust_field_revisions
            WHEN NOT EXISTS (
                SELECT 1 FROM trusts
                WHERE trust_id = NEW.trust_id
                  AND firm_id = NEW.firm_id
                  AND owner_id = NEW.owner_id
            )
            BEGIN
                SELECT RAISE(ABORT, 'trust_field_revisions_scope_mismatch');
            END;

            CREATE TRIGGER IF NOT EXISTS trust_field_revisions_prior_insert
            BEFORE INSERT ON trust_field_revisions
            WHEN NEW.prior_revision_id IS NOT NULL
             AND NOT EXISTS (
                SELECT 1 FROM trust_field_revisions
                WHERE revision_id = NEW.prior_revision_id
            )
            BEGIN
                SELECT RAISE(ABORT, 'trust_field_revisions_prior_missing');
            END;

            CREATE TRIGGER IF NOT EXISTS trust_field_revisions_chain_insert
            BEFORE INSERT ON trust_field_revisions
            WHEN NEW.revision_number < 1
              OR (NEW.revision_number = 1 AND NEW.prior_revision_id IS NOT NULL)
              OR (NEW.revision_number > 1 AND NEW.prior_revision_id IS NULL)
              OR (NEW.prior_revision_id IS NOT NULL AND NOT EXISTS (
                    SELECT 1
                    FROM trust_field_revisions AS prior
                    WHERE prior.revision_id = NEW.prior_revision_id
                      AND prior.firm_id = NEW.firm_id
                      AND prior.owner_id = NEW.owner_id
                      AND prior.trust_id = NEW.trust_id
                      AND prior.field_name = NEW.field_name
                      AND prior.revision_number = NEW.revision_number - 1
                 ))
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'trust_field_revisions_invalid_prior_revision'
                );
            END;

            CREATE TRIGGER IF NOT EXISTS trust_field_revisions_no_update
            BEFORE UPDATE ON trust_field_revisions
            BEGIN
                SELECT RAISE(ABORT, 'trust_field_revisions_append_only');
            END;

            CREATE TRIGGER IF NOT EXISTS trust_field_revisions_no_delete
            BEFORE DELETE ON trust_field_revisions
            BEGIN
                SELECT RAISE(ABORT, 'trust_field_revisions_append_only');
            END;

            COMMIT;
            """
        )
    except TrustFieldRevisionMigrationError:
        connection.rollback()
        raise
    except sqlite3.Error as exc:
        connection.rollback()
        raise TrustFieldRevisionMigrationError(str(exc)) from exc
    finally:
        connection.close()
