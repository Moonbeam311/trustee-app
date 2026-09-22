"""Explicit, non-startup MAGC-1 Wave-1 schema for disposable databases."""
import sqlite3
from pathlib import Path

TABLES = ("hub_program_source_metadata", "hub_authority_applicability")


def apply_magc1_wave1_schema(db_path: str | Path) -> dict[str, object]:
    connection = sqlite3.connect(Path(db_path))
    try:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS hub_program_source_metadata (
            metadata_id TEXT PRIMARY KEY,
            program_id TEXT NOT NULL,
            source_reference_id TEXT NOT NULL,
            source_origin_jurisdiction TEXT,
            effective_date TEXT,
            current_as_of_date TEXT,
            lifecycle_state TEXT NOT NULL CHECK (lifecycle_state IN
              ('CURRENT','REVIEW_DUE','SUPERSEDED','WITHDRAWN','DEPRECATED','UNRESOLVED')),
            prior_metadata_id TEXT,
            actor TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(source_reference_id) REFERENCES hub_program_source_references(source_reference_id),
            FOREIGN KEY(prior_metadata_id) REFERENCES hub_program_source_metadata(metadata_id)
        );
        CREATE INDEX IF NOT EXISTS idx_magc_source_metadata
          ON hub_program_source_metadata(program_id, source_reference_id, created_at);
        CREATE TABLE IF NOT EXISTS hub_authority_applicability (
            applicability_id TEXT PRIMARY KEY,
            firm_id TEXT NOT NULL,
            context_type TEXT NOT NULL CHECK(context_type IN ('PROGRAM','MATTER','TRUST','OTHER')),
            context_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            source_reference_id TEXT NOT NULL,
            applicability_jurisdiction TEXT,
            trust_type_applicability TEXT,
            legal_scope TEXT NOT NULL CHECK(legal_scope IN
              ('CREATION','ADMINISTRATION','TAX','PROPERTY','TRANSACTION','LITIGATION','DIGITAL_ASSETS','OTHER')),
            research_only INTEGER NOT NULL DEFAULT 1 CHECK(research_only IN (0,1)),
            generation_authorized INTEGER NOT NULL DEFAULT 0 CHECK(generation_authorized IN (0,1)),
            independent_support_state TEXT NOT NULL DEFAULT 'UNRESOLVED'
              CHECK(independent_support_state IN ('YES','NO','UNRESOLVED')),
            applicability_basis TEXT NOT NULL,
            applicability_provenance TEXT NOT NULL,
            decision_origin TEXT NOT NULL CHECK(decision_origin IN
              ('SYSTEM_SUGGESTED','OPERATOR_OR_FIDUCIARY','PROFESSIONAL')),
            actor TEXT NOT NULL,
            actor_capacity TEXT NOT NULL,
            prior_applicability_id TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(source_reference_id) REFERENCES hub_program_source_references(source_reference_id),
            FOREIGN KEY(prior_applicability_id) REFERENCES hub_authority_applicability(applicability_id)
        );
        CREATE INDEX IF NOT EXISTS idx_magc_applicability
          ON hub_authority_applicability(firm_id, context_type, context_id, source_reference_id, subject, created_at);
        """)
        for table in TABLES:
            connection.executescript(f"""
            CREATE TRIGGER IF NOT EXISTS magc_{table}_no_update BEFORE UPDATE ON {table}
            BEGIN SELECT RAISE(ABORT, 'magc_append_only'); END;
            CREATE TRIGGER IF NOT EXISTS magc_{table}_no_delete BEFORE DELETE ON {table}
            BEGIN SELECT RAISE(ABORT, 'magc_append_only'); END;
            """)
        connection.commit()
        return {"schema_complete": True, "records_created": 0}
    finally:
        connection.close()
