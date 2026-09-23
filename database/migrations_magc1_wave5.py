"""Additive schema for the bounded MAGC-1 Wave-5 extension records."""

import sqlite3
from pathlib import Path


TABLES = (
    "document_template_clause_revisions",
    "document_clause_generation_events",
    "trust_formation_assessments",
)


class Magc1Wave5MigrationError(RuntimeError):
    pass


def apply_magc1_wave5_schema(db_path):
    """Create only the three empty, append-only Wave-5 tables."""
    connection = sqlite3.connect(str(Path(db_path)))
    try:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS document_template_clause_revisions (
            clause_revision_id TEXT PRIMARY KEY,
            template_id TEXT NOT NULL,
            clause_id TEXT NOT NULL,
            clause_key TEXT NOT NULL,
            revision_label TEXT NOT NULL,
            revision_state TEXT NOT NULL CHECK(revision_state IN ('DRAFT','REVIEW_REQUIRED','APPROVED','SUPERSEDED')),
            content_sha256 TEXT NOT NULL,
            source_reference_id TEXT,
            basis TEXT NOT NULL,
            provenance TEXT NOT NULL,
            decision_origin TEXT NOT NULL CHECK(decision_origin IN ('SYSTEM_SUGGESTED','OPERATOR_OR_FIDUCIARY','PROFESSIONAL')),
            human_confirmed INTEGER NOT NULL CHECK(human_confirmed IN (0,1)),
            actor TEXT NOT NULL,
            actor_capacity TEXT NOT NULL,
            prior_clause_revision_id TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(prior_clause_revision_id) REFERENCES document_template_clause_revisions(clause_revision_id)
        );
        CREATE INDEX IF NOT EXISTS idx_w5_clause_revision_scope
          ON document_template_clause_revisions(template_id,clause_id,created_at);

        CREATE TABLE IF NOT EXISTS document_clause_generation_events (
            clause_generation_event_id TEXT PRIMARY KEY,
            firm_id TEXT NOT NULL,
            context_type TEXT NOT NULL CHECK(context_type IN ('PROGRAM','MATTER','TRUST','OTHER')),
            context_id TEXT NOT NULL,
            trust_id TEXT,
            matter_id TEXT,
            intake_id TEXT,
            template_id TEXT NOT NULL,
            clause_revision_id TEXT NOT NULL,
            generated_document_id TEXT,
            generation_state TEXT NOT NULL CHECK(generation_state IN ('UNRESOLVED','PROPOSED','AUTHORIZED','APPLIED','REJECTED','SUPERSEDED')),
            applicability_id TEXT,
            hierarchy_id TEXT,
            evidence_sufficiency_id TEXT,
            jurisdiction_certification_id TEXT,
            portability_id TEXT,
            basis TEXT NOT NULL,
            provenance TEXT NOT NULL,
            decision_origin TEXT NOT NULL CHECK(decision_origin IN ('SYSTEM_SUGGESTED','OPERATOR_OR_FIDUCIARY','PROFESSIONAL')),
            human_confirmed INTEGER NOT NULL CHECK(human_confirmed IN (0,1)),
            actor TEXT NOT NULL,
            actor_capacity TEXT NOT NULL,
            prior_clause_generation_event_id TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(clause_revision_id) REFERENCES document_template_clause_revisions(clause_revision_id),
            FOREIGN KEY(prior_clause_generation_event_id) REFERENCES document_clause_generation_events(clause_generation_event_id)
        );
        CREATE INDEX IF NOT EXISTS idx_w5_clause_generation_scope
          ON document_clause_generation_events(firm_id,context_type,context_id,template_id,clause_revision_id,created_at);

        CREATE TABLE IF NOT EXISTS trust_formation_assessments (
            formation_assessment_id TEXT PRIMARY KEY,
            firm_id TEXT NOT NULL,
            intake_id TEXT,
            matter_id TEXT,
            trust_id TEXT,
            formation_state TEXT NOT NULL CHECK(formation_state IN ('UNRESOLVED','PLANNING','DRAFTING','EXECUTION_PENDING','EXECUTION_RECORDED','FORMATION_RECORDED','SUPERSEDED')),
            readiness_state TEXT NOT NULL CHECK(readiness_state IN ('UNRESOLVED','REVIEW_REQUIRED','NOT_READY','READY_FOR_DRAFT','READY_FOR_EXECUTION','READY_FOR_ACTIVATION')),
            governing_document_type TEXT CHECK(governing_document_type IS NULL OR governing_document_type IN ('DOCUMENT','GENERATED_DOCUMENT')),
            governing_document_id TEXT,
            legal_state_event_id TEXT,
            jurisdiction_certification_id TEXT,
            trustee_acceptance_id TEXT,
            asset_control_id TEXT,
            basis TEXT NOT NULL,
            provenance TEXT NOT NULL,
            decision_origin TEXT NOT NULL CHECK(decision_origin IN ('SYSTEM_SUGGESTED','OPERATOR_OR_FIDUCIARY','PROFESSIONAL')),
            human_confirmed INTEGER NOT NULL CHECK(human_confirmed IN (0,1)),
            actor TEXT NOT NULL,
            actor_capacity TEXT NOT NULL,
            prior_formation_assessment_id TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(prior_formation_assessment_id) REFERENCES trust_formation_assessments(formation_assessment_id)
        );
        CREATE INDEX IF NOT EXISTS idx_w5_formation_scope
          ON trust_formation_assessments(firm_id,intake_id,matter_id,trust_id,created_at);
        """)
        for table in TABLES:
            connection.executescript(f"""
            CREATE TRIGGER IF NOT EXISTS w5_{table}_no_update
            BEFORE UPDATE ON {table} BEGIN SELECT RAISE(ABORT,'wave5_append_only'); END;
            CREATE TRIGGER IF NOT EXISTS w5_{table}_no_delete
            BEFORE DELETE ON {table} BEGIN SELECT RAISE(ABORT,'wave5_append_only'); END;
            """)
        connection.commit()
        rows = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in TABLES}
        return {"schema_complete": True, "rows": rows, "records_created": 0}
    except sqlite3.DatabaseError as exc:
        connection.rollback()
        raise Magc1Wave5MigrationError(str(exc)) from exc
    finally:
        connection.close()
