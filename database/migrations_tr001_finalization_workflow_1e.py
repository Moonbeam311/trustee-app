"""Additive schema for canonical property fact history (TR001 1E-A)."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class PropertyFactMigrationError(RuntimeError):
    pass


TABLES = ("property_attestations", "property_identification_revisions")


def apply_property_fact_schema(db_path: str | Path) -> dict:
    connection = sqlite3.connect(str(Path(db_path)))
    try:
        before = {
            table: connection.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()[0]
            for table in TABLES
        }
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS property_attestations (
                attestation_id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                trust_id TEXT NOT NULL,
                firm_id TEXT NOT NULL,
                attestation_type TEXT NOT NULL CHECK(attestation_type IN ('possession','ownership')),
                subject_field_or_fact TEXT NOT NULL,
                attested_value TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                actor_capacity TEXT NOT NULL,
                basis TEXT NOT NULL,
                attested_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'recorded',
                supersedes_attestation_id TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(supersedes_attestation_id) REFERENCES property_attestations(attestation_id)
            );
            CREATE INDEX IF NOT EXISTS idx_property_attestations_scope
                ON property_attestations(firm_id, trust_id, property_id, attestation_type, created_at);

            CREATE TABLE IF NOT EXISTS property_identification_revisions (
                revision_id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                trust_id TEXT NOT NULL,
                firm_id TEXT NOT NULL,
                revision_number INTEGER NOT NULL CHECK(revision_number > 0),
                prior_identification_json TEXT NOT NULL,
                resulting_identification_json TEXT NOT NULL,
                revision_basis TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                actor_capacity TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'recorded',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(firm_id, trust_id, property_id, revision_number)
            );
            CREATE INDEX IF NOT EXISTS idx_property_identification_revision_scope
                ON property_identification_revisions(firm_id, trust_id, property_id, revision_number);

            CREATE TRIGGER IF NOT EXISTS property_attestations_no_update
            BEFORE UPDATE ON property_attestations BEGIN
                SELECT RAISE(ABORT, 'property_attestations_append_only');
            END;
            CREATE TRIGGER IF NOT EXISTS property_attestations_no_delete
            BEFORE DELETE ON property_attestations BEGIN
                SELECT RAISE(ABORT, 'property_attestations_append_only');
            END;
            CREATE TRIGGER IF NOT EXISTS property_identification_revisions_no_update
            BEFORE UPDATE ON property_identification_revisions BEGIN
                SELECT RAISE(ABORT, 'property_identification_revisions_append_only');
            END;
            CREATE TRIGGER IF NOT EXISTS property_identification_revisions_no_delete
            BEFORE DELETE ON property_identification_revisions BEGIN
                SELECT RAISE(ABORT, 'property_identification_revisions_append_only');
            END;
            """
        )
        connection.commit()
        return {
            "schema_complete": True,
            "tables_created": [table for table, existed in before.items() if not existed],
            "records_created": 0,
        }
    except sqlite3.DatabaseError as exc:
        connection.rollback()
        raise PropertyFactMigrationError(str(exc)) from exc
    finally:
        connection.close()
