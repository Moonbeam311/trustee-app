"""Explicit, additive MAGC-1 Wave-4 boundary schema."""

import sqlite3
from pathlib import Path


TABLES = (
    "hub_jurisdiction_module_certifications",
    "document_template_portability_assessments",
)


class Magc1Wave4MigrationError(RuntimeError):
    pass


def apply_magc1_wave4_schema(db_path):
    """Create exactly the two Wave-4 append-only record types."""
    connection = sqlite3.connect(str(Path(db_path)))
    try:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS hub_jurisdiction_module_certifications (
            certification_id TEXT PRIMARY KEY,
            firm_id TEXT NOT NULL,
            context_type TEXT NOT NULL CHECK(context_type IN ('PROGRAM','MATTER','TRUST','OTHER')),
            context_id TEXT NOT NULL,
            jurisdiction TEXT NOT NULL,
            subject TEXT NOT NULL,
            legal_scope TEXT NOT NULL CHECK(legal_scope IN ('CREATION','ADMINISTRATION','TAX','PROPERTY','TRANSACTION','LITIGATION','DIGITAL_ASSETS','OTHER')),
            trust_type_applicability TEXT,
            applicability_id TEXT NOT NULL,
            hierarchy_id TEXT NOT NULL,
            evidence_sufficiency_id TEXT,
            certification_state TEXT NOT NULL CHECK(certification_state IN ('UNRESOLVED','REVIEW_REQUIRED','CERTIFIED','REJECTED','SUPERSEDED')),
            basis TEXT NOT NULL,
            provenance TEXT NOT NULL,
            decision_origin TEXT NOT NULL CHECK(decision_origin IN ('SYSTEM_SUGGESTED','OPERATOR_OR_FIDUCIARY','PROFESSIONAL')),
            human_confirmed INTEGER NOT NULL CHECK(human_confirmed IN (0,1)),
            actor TEXT NOT NULL,
            actor_capacity TEXT NOT NULL,
            prior_certification_id TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(applicability_id) REFERENCES hub_authority_applicability(applicability_id),
            FOREIGN KEY(hierarchy_id) REFERENCES hub_authority_hierarchy_determinations(hierarchy_id),
            FOREIGN KEY(evidence_sufficiency_id) REFERENCES hub_program_evidence_sufficiency_assessments(sufficiency_id),
            FOREIGN KEY(prior_certification_id) REFERENCES hub_jurisdiction_module_certifications(certification_id)
        );
        CREATE INDEX IF NOT EXISTS idx_w4_certification_scope
          ON hub_jurisdiction_module_certifications(firm_id,context_type,context_id,subject,jurisdiction,legal_scope,created_at);

        CREATE TABLE IF NOT EXISTS document_template_portability_assessments (
            portability_id TEXT PRIMARY KEY,
            firm_id TEXT NOT NULL,
            template_id TEXT NOT NULL,
            target_jurisdiction TEXT NOT NULL,
            target_trust_type TEXT NOT NULL,
            legal_scope TEXT NOT NULL CHECK(legal_scope IN ('CREATION','ADMINISTRATION','TAX','PROPERTY','TRANSACTION','LITIGATION','DIGITAL_ASSETS','OTHER')),
            jurisdiction_certification_id TEXT,
            portability_state TEXT NOT NULL CHECK(portability_state IN ('UNRESOLVED','REVIEW_REQUIRED','PORTABLE','NOT_PORTABLE','SUPERSEDED')),
            basis TEXT NOT NULL,
            provenance TEXT NOT NULL,
            decision_origin TEXT NOT NULL CHECK(decision_origin IN ('SYSTEM_SUGGESTED','OPERATOR_OR_FIDUCIARY','PROFESSIONAL')),
            human_confirmed INTEGER NOT NULL CHECK(human_confirmed IN (0,1)),
            actor TEXT NOT NULL,
            actor_capacity TEXT NOT NULL,
            prior_portability_id TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(jurisdiction_certification_id) REFERENCES hub_jurisdiction_module_certifications(certification_id),
            FOREIGN KEY(prior_portability_id) REFERENCES document_template_portability_assessments(portability_id)
        );
        CREATE INDEX IF NOT EXISTS idx_w4_portability_scope
          ON document_template_portability_assessments(firm_id,template_id,target_jurisdiction,target_trust_type,legal_scope,created_at);
        """)
        for table in TABLES:
            connection.executescript(f"""
            CREATE TRIGGER IF NOT EXISTS w4_{table}_no_update
            BEFORE UPDATE ON {table} BEGIN SELECT RAISE(ABORT,'wave4_append_only'); END;
            CREATE TRIGGER IF NOT EXISTS w4_{table}_no_delete
            BEFORE DELETE ON {table} BEGIN SELECT RAISE(ABORT,'wave4_append_only'); END;
            """)
        connection.commit()
        rows = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in TABLES}
        return {"schema_complete": True, "rows": rows, "records_created": 0}
    except sqlite3.DatabaseError as exc:
        connection.rollback()
        raise Magc1Wave4MigrationError(str(exc)) from exc
    finally:
        connection.close()
