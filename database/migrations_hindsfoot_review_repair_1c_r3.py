"""Additive canonical-binding substrate for Hindsfoot review repair 1C R3."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class HindsfootReviewRepairR3MigrationError(RuntimeError):
    pass


def _tables(connection):
    return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _columns(connection, table):
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}


def apply_hindsfoot_review_repair_r3_schema(db_path):
    """Install only missing owners/columns; never infer or adopt content."""
    connection = sqlite3.connect(str(Path(db_path)))
    try:
        tables = _tables(connection)
        required = {"documents", "document_template_clause_revisions"}
        if not required.issubset(tables):
            raise HindsfootReviewRepairR3MigrationError(
                "canonical document and clause revision owners are required"
            )
        if "document_id" not in _columns(connection, "documents"):
            raise HindsfootReviewRepairR3MigrationError("documents lacks document_id")
        document_rows = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        revision_rows = connection.execute(
            "SELECT COUNT(*) FROM document_template_clause_revisions"
        ).fetchone()[0]
        added = []
        document_columns = _columns(connection, "documents")
        for name in ("verified_content_sha256", "source_revision_id"):
            if name not in document_columns:
                connection.execute(f"ALTER TABLE documents ADD COLUMN {name} TEXT")
                added.append(name)
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS document_clause_revision_content (
            clause_revision_id TEXT PRIMARY KEY,
            renderable_content TEXT NOT NULL,
            content_format TEXT NOT NULL DEFAULT 'text/plain'
              CHECK(content_format IN ('text/plain')),
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(clause_revision_id)
              REFERENCES document_template_clause_revisions(clause_revision_id)
        );
        CREATE TRIGGER IF NOT EXISTS r3_clause_content_no_update
          BEFORE UPDATE ON document_clause_revision_content
          BEGIN SELECT RAISE(ABORT,'CLAUSE_REVISION_CONTENT_IMMUTABLE'); END;
        CREATE TRIGGER IF NOT EXISTS r3_clause_content_no_delete
          BEFORE DELETE ON document_clause_revision_content
          BEGIN SELECT RAISE(ABORT,'CLAUSE_REVISION_CONTENT_IMMUTABLE'); END;

        CREATE TABLE IF NOT EXISTS document_evidence_relationships (
            relationship_id TEXT PRIMARY KEY,
            firm_id TEXT NOT NULL,
            context_type TEXT NOT NULL CHECK(context_type IN ('TRUST','MATTER')),
            context_id TEXT NOT NULL,
            document_id TEXT NOT NULL,
            evidence_role TEXT NOT NULL CHECK(evidence_role IN (
              'GOVERNING_PRE_SIGNING_MASTER','BENEFICIARY_SCHEDULE',
              'INITIAL_TRUSTEE_ACCEPTANCE','SCHEDULE_A','CLOSING_CONTROL_SHEET',
              'HISTORICAL_PROFESSIONAL_REVIEW_REFERENCE')),
            relationship_state TEXT NOT NULL CHECK(relationship_state IN ('ACTIVE','RETIRED')),
            classification TEXT NOT NULL CHECK(classification IN ('SOURCE_EVIDENCE','HISTORICAL_REFERENCE')),
            basis TEXT NOT NULL,
            provenance TEXT NOT NULL,
            decision_origin TEXT NOT NULL CHECK(decision_origin IN ('OPERATOR_OR_FIDUCIARY','PROFESSIONAL')),
            human_confirmed INTEGER NOT NULL CHECK(human_confirmed = 1),
            prior_relationship_id TEXT,
            source_reference_id TEXT,
            created_by TEXT NOT NULL,
            actor_capacity TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(document_id) REFERENCES documents(document_id),
            FOREIGN KEY(prior_relationship_id) REFERENCES document_evidence_relationships(relationship_id)
        );
        CREATE INDEX IF NOT EXISTS idx_r3_evidence_scope
          ON document_evidence_relationships(firm_id,context_type,context_id,evidence_role);
        CREATE TRIGGER IF NOT EXISTS r3_evidence_no_update
          BEFORE UPDATE ON document_evidence_relationships
          BEGIN SELECT RAISE(ABORT,'DOCUMENT_EVIDENCE_RELATIONSHIP_IMMUTABLE'); END;
        CREATE TRIGGER IF NOT EXISTS r3_evidence_no_delete
          BEFORE DELETE ON document_evidence_relationships
          BEGIN SELECT RAISE(ABORT,'DOCUMENT_EVIDENCE_RELATIONSHIP_IMMUTABLE'); END;
        """)
        if connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0] != document_rows:
            raise HindsfootReviewRepairR3MigrationError("document rows changed")
        if connection.execute("SELECT COUNT(*) FROM document_template_clause_revisions").fetchone()[0] != revision_rows:
            raise HindsfootReviewRepairR3MigrationError("clause revision rows changed")
        connection.commit()
        return {"schema_complete": True, "columns_added": added,
                "document_rows_preserved": document_rows,
                "clause_revision_rows_preserved": revision_rows,
                "records_created": 0}
    except HindsfootReviewRepairR3MigrationError:
        connection.rollback(); raise
    except sqlite3.DatabaseError as exc:
        connection.rollback()
        raise HindsfootReviewRepairR3MigrationError(str(exc)) from exc
    finally:
        connection.close()
