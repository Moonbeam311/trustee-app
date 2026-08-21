"""Additive schema for the canonical successor-acceptance institutional fact."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


ACCEPTANCE_TABLE = "successor_acceptances"
ACCEPTANCE_STATES = (
    "PENDING_EVIDENCE",
    "ACCEPTED_RECORDED",
    "DECLINED_RECORDED",
    "WITHDRAWN_RECORDED",
    "SUPERSEDED",
)


class SuccessorAcceptanceMigrationError(RuntimeError):
    """Raised when the acceptance schema cannot be installed safely."""


def _columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    quoted = table_name.replace('"', '""')
    return {
        str(row[1])
        for row in connection.execute(f'PRAGMA table_info("{quoted}")').fetchall()
    }


def _require_source_schema(connection: sqlite3.Connection) -> None:
    requirements = {
        "trusts": {"trust_id", "firm_id"},
        "fiduciaries": {"fiduciary_id", "trust_id", "firm_id"},
    }
    failures: list[str] = []
    for table_name, required in requirements.items():
        actual = _columns(connection, table_name)
        if not actual:
            failures.append(f"Required source table {table_name!r} does not exist.")
        elif missing := sorted(required - actual):
            failures.append(
                f"Required source table {table_name!r} is missing column(s): "
                f"{', '.join(missing)}."
            )
    if failures:
        raise SuccessorAcceptanceMigrationError(" ".join(failures))


def apply_successor_acceptance_schema(db_path: str | Path) -> dict[str, Any]:
    """Install the additive schema without inferring or creating acceptance rows."""
    resolved = Path(db_path).expanduser().resolve()
    if not resolved.exists():
        raise SuccessorAcceptanceMigrationError(f"Database does not exist: {resolved}")

    connection = sqlite3.connect(str(resolved))
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        _require_source_schema(connection)
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS successor_acceptances (
                acceptance_id TEXT PRIMARY KEY,
                firm_id TEXT NOT NULL,
                trust_id TEXT NOT NULL,
                fiduciary_id TEXT NOT NULL,
                appointment_reference TEXT NOT NULL,
                role_capacity TEXT NOT NULL,
                appointment_source_reference TEXT NOT NULL,
                acceptance_status TEXT NOT NULL
                    CHECK (acceptance_status IN (
                        'PENDING_EVIDENCE',
                        'ACCEPTED_RECORDED',
                        'DECLINED_RECORDED',
                        'WITHDRAWN_RECORDED',
                        'SUPERSEDED'
                    )),
                recorded_by TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                provenance_source TEXT NOT NULL,
                context_fingerprint TEXT NOT NULL UNIQUE,
                accepted_at TEXT,
                acceptance_method TEXT,
                evidence_document_id TEXT,
                external_evidence_reference TEXT,
                supersedes_acceptance_id TEXT,
                governed_explanation TEXT,
                CHECK (
                    acceptance_status != 'ACCEPTED_RECORDED'
                    OR (
                        accepted_at IS NOT NULL
                        AND trim(accepted_at) != ''
                        AND (
                            (evidence_document_id IS NOT NULL AND trim(evidence_document_id) != '')
                            OR (external_evidence_reference IS NOT NULL AND trim(external_evidence_reference) != '')
                        )
                    )
                ),
                FOREIGN KEY (trust_id) REFERENCES trusts(trust_id) ON DELETE RESTRICT,
                FOREIGN KEY (fiduciary_id) REFERENCES fiduciaries(fiduciary_id) ON DELETE RESTRICT,
                FOREIGN KEY (supersedes_acceptance_id)
                    REFERENCES successor_acceptances(acceptance_id) ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS ix_successor_acceptances_trust
            ON successor_acceptances(firm_id, trust_id, recorded_at, acceptance_id);

            CREATE INDEX IF NOT EXISTS ix_successor_acceptances_fiduciary
            ON successor_acceptances(firm_id, trust_id, fiduciary_id, acceptance_status);

            CREATE TRIGGER IF NOT EXISTS trg_successor_acceptance_source_scope_insert
            BEFORE INSERT ON successor_acceptances
            BEGIN
                SELECT CASE WHEN NOT EXISTS (
                    SELECT 1 FROM trusts
                    WHERE trust_id = NEW.trust_id AND firm_id = NEW.firm_id
                ) THEN RAISE(ABORT, 'Trust does not exist in the acceptance firm.') END;

                SELECT CASE WHEN NOT EXISTS (
                    SELECT 1 FROM fiduciaries
                    WHERE fiduciary_id = NEW.fiduciary_id
                      AND trust_id = NEW.trust_id
                      AND firm_id = NEW.firm_id
                ) THEN RAISE(ABORT, 'Fiduciary is not scoped to the acceptance Trust and firm.') END;
            END;

            CREATE TRIGGER IF NOT EXISTS trg_successor_acceptance_context_immutable
            BEFORE UPDATE OF
                firm_id, trust_id, fiduciary_id, appointment_reference,
                role_capacity, appointment_source_reference, context_fingerprint
            ON successor_acceptances
            BEGIN
                SELECT RAISE(ABORT, 'Successor acceptance context is immutable.');
            END;
            """
        )
        connection.commit()
        return validate_successor_acceptance_schema(connection)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def validate_successor_acceptance_schema(
    connection_or_path: sqlite3.Connection | str | Path,
) -> dict[str, Any]:
    owns_connection = not isinstance(connection_or_path, sqlite3.Connection)
    connection = (
        sqlite3.connect(str(Path(connection_or_path).expanduser().resolve()))
        if owns_connection
        else connection_or_path
    )
    try:
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (ACCEPTANCE_TABLE,),
        ).fetchone()
        indexes = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?",
                (ACCEPTANCE_TABLE,),
            ).fetchall()
        }
        triggers = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name=?",
                (ACCEPTANCE_TABLE,),
            ).fetchall()
        }
        required_columns = {
            "acceptance_id", "firm_id", "trust_id", "fiduciary_id",
            "appointment_reference", "role_capacity",
            "appointment_source_reference", "acceptance_status", "recorded_by",
            "recorded_at", "provenance_source", "context_fingerprint",
            "accepted_at", "acceptance_method", "evidence_document_id",
            "external_evidence_reference", "supersedes_acceptance_id",
            "governed_explanation",
        }
        row_count = (
            connection.execute("SELECT COUNT(*) FROM successor_acceptances").fetchone()[0]
            if table
            else 0
        )
        complete = (
            table is not None
            and required_columns.issubset(_columns(connection, ACCEPTANCE_TABLE))
            and {
                "ix_successor_acceptances_trust",
                "ix_successor_acceptances_fiduciary",
                "sqlite_autoindex_successor_acceptances_2",
            }.issubset(indexes)
            and {
                "trg_successor_acceptance_source_scope_insert",
                "trg_successor_acceptance_context_immutable",
            }.issubset(triggers)
        )
        return {
            "schema_complete": complete,
            "tables": [ACCEPTANCE_TABLE] if table else [],
            "indexes": sorted(indexes),
            "triggers": sorted(triggers),
            "acceptance_rows": row_count,
        }
    finally:
        if owns_connection:
            connection.close()


if __name__ == "__main__":
    raise SystemExit(
        "Import apply_successor_acceptance_schema(db_path) with an explicit isolated database path."
    )
