"""Additive schema for MAGC-1 Wave-3 semantic records."""

import sqlite3
from pathlib import Path


TABLES = (
    "document_legal_state_events",
    "hub_program_evidence_sufficiency_assessments",
    "fiduciary_authority_lifecycle_records",
    "trust_asset_control_determinations",
)

OWNER_TABLES = {
    "documents": {"document_id", "trust_id"},
    "generated_documents": {"document_id", "trust_id"},
    "hub_programs": {"program_id", "firm_id"},
    "hub_program_issues": {"issue_id", "program_id"},
    "hub_program_authority_claims": {"claim_id", "program_id", "issue_id"},
    "hub_program_authority_evidence": {"evidence_id", "program_id", "claim_id"},
    "hub_program_authority_verifications": {"verification_id", "program_id"},
    "fiduciaries": {"fiduciary_id", "firm_id", "trust_id"},
    "successor_acceptances": {"acceptance_id", "firm_id", "trust_id", "fiduciary_id"},
    "properties": {"property_id", "trust_id"},
    "accounts": {"account_id", "trust_id"},
    "transfers": {"transfer_id", "firm_id", "trust_id"},
    "trusts": {"trust_id", "firm_id"},
}


class Magc1Wave3MigrationError(RuntimeError):
    pass


def _columns(connection, table):
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}


def apply_magc1_wave3_schema(db_path):
    """Create only the four Wave-3 extensions; never create owner records."""
    connection = sqlite3.connect(str(Path(db_path)))
    try:
        present = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        for table, required in OWNER_TABLES.items():
            if table not in present or not required.issubset(_columns(connection, table)):
                raise Magc1Wave3MigrationError(
                    f"required canonical owner substrate unavailable: {table}"
                )

        connection.executescript("""
        CREATE TABLE IF NOT EXISTS document_legal_state_events (
            legal_state_event_id TEXT PRIMARY KEY,
            firm_id TEXT NOT NULL, trust_id TEXT NOT NULL,
            document_object_type TEXT NOT NULL CHECK(document_object_type IN ('DOCUMENT','GENERATED_DOCUMENT')),
            document_object_id TEXT NOT NULL,
            legal_state TEXT NOT NULL CHECK(legal_state IN ('UNRESOLVED','DRAFT_RECORDED','EXECUTION_RECORDED','EFFECTIVE_RECORDED','SUPERSEDED_RECORDED','REVOKED_RECORDED','EXPIRED_RECORDED')),
            effective_at TEXT, basis TEXT, provenance TEXT,
            decision_origin TEXT NOT NULL CHECK(decision_origin IN ('SYSTEM_SUGGESTED','OPERATOR_OR_FIDUCIARY','PROFESSIONAL')),
            human_confirmed INTEGER NOT NULL CHECK(human_confirmed IN (0,1)),
            actor TEXT NOT NULL, actor_capacity TEXT NOT NULL,
            prior_legal_state_event_id TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(prior_legal_state_event_id) REFERENCES document_legal_state_events(legal_state_event_id)
        );
        CREATE INDEX IF NOT EXISTS idx_w3_document_legal_scope ON document_legal_state_events(firm_id,trust_id,document_object_type,document_object_id,created_at);

        CREATE TABLE IF NOT EXISTS hub_program_evidence_sufficiency_assessments (
            sufficiency_id TEXT PRIMARY KEY,
            program_id TEXT NOT NULL, firm_id TEXT NOT NULL,
            issue_id TEXT NOT NULL, claim_id TEXT NOT NULL,
            target_use TEXT NOT NULL CHECK(target_use IN ('RESEARCH','DRAFT','GENERATION','FINALIZATION','OPERATIONAL_ACTION')),
            sufficiency_state TEXT NOT NULL CHECK(sufficiency_state IN ('SUFFICIENT','INSUFFICIENT','UNRESOLVED')),
            evidence_ids_json TEXT NOT NULL, verification_ids_json TEXT NOT NULL,
            basis TEXT, provenance TEXT,
            decision_origin TEXT NOT NULL CHECK(decision_origin IN ('SYSTEM_SUGGESTED','OPERATOR_OR_FIDUCIARY','PROFESSIONAL')),
            human_confirmed INTEGER NOT NULL CHECK(human_confirmed IN (0,1)),
            actor TEXT NOT NULL, actor_capacity TEXT NOT NULL,
            prior_sufficiency_id TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY(prior_sufficiency_id) REFERENCES hub_program_evidence_sufficiency_assessments(sufficiency_id)
        );
        CREATE INDEX IF NOT EXISTS idx_w3_sufficiency_scope ON hub_program_evidence_sufficiency_assessments(program_id,firm_id,issue_id,claim_id,target_use,created_at);

        CREATE TABLE IF NOT EXISTS fiduciary_authority_lifecycle_records (
            authority_lifecycle_id TEXT PRIMARY KEY,
            firm_id TEXT NOT NULL, trust_id TEXT NOT NULL, fiduciary_id TEXT NOT NULL,
            authority_state TEXT NOT NULL CHECK(authority_state IN ('UNRESOLVED','PENDING_AUTHORITY','ACTIVE_RECORDED','SUSPENDED_RECORDED','INCAPACITY_RECORDED','RESIGNED_RECORDED','REMOVED_RECORDED','ENDED_RECORDED')),
            effective_at TEXT, authority_basis TEXT, provenance TEXT, source_reference TEXT,
            decision_origin TEXT NOT NULL CHECK(decision_origin IN ('SYSTEM_SUGGESTED','OPERATOR_OR_FIDUCIARY','PROFESSIONAL')),
            human_confirmed INTEGER NOT NULL CHECK(human_confirmed IN (0,1)),
            actor TEXT NOT NULL, actor_capacity TEXT NOT NULL,
            successor_acceptance_id TEXT, prior_authority_lifecycle_id TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(prior_authority_lifecycle_id) REFERENCES fiduciary_authority_lifecycle_records(authority_lifecycle_id)
        );
        CREATE INDEX IF NOT EXISTS idx_w3_fiduciary_lifecycle_scope ON fiduciary_authority_lifecycle_records(firm_id,trust_id,fiduciary_id,created_at);

        CREATE TABLE IF NOT EXISTS trust_asset_control_determinations (
            asset_control_id TEXT PRIMARY KEY,
            firm_id TEXT NOT NULL, trust_id TEXT NOT NULL,
            asset_object_type TEXT NOT NULL CHECK(asset_object_type IN ('PROPERTY','ACCOUNT')),
            asset_object_id TEXT NOT NULL, related_transfer_id TEXT,
            funding_state TEXT NOT NULL CHECK(funding_state IN ('UNRESOLVED','PROPOSED','IN_PROCESS','FUNDED_RECORDED','NOT_FUNDED_RECORDED')),
            ownership_state TEXT NOT NULL CHECK(ownership_state IN ('UNRESOLVED','TRUST_TITLE_RECORDED','BENEFICIAL_INTEREST_RECORDED','THIRD_PARTY_TITLE_RECORDED')),
            control_state TEXT NOT NULL CHECK(control_state IN ('UNRESOLVED','TRUSTEE_CONTROL_RECORDED','SHARED_CONTROL_RECORDED','THIRD_PARTY_CONTROL_RECORDED')),
            evidence_reference TEXT, basis TEXT, provenance TEXT,
            decision_origin TEXT NOT NULL CHECK(decision_origin IN ('SYSTEM_SUGGESTED','OPERATOR_OR_FIDUCIARY','PROFESSIONAL')),
            human_confirmed INTEGER NOT NULL CHECK(human_confirmed IN (0,1)),
            actor TEXT NOT NULL, actor_capacity TEXT NOT NULL,
            prior_asset_control_id TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY(prior_asset_control_id) REFERENCES trust_asset_control_determinations(asset_control_id)
        );
        CREATE INDEX IF NOT EXISTS idx_w3_asset_control_scope ON trust_asset_control_determinations(firm_id,trust_id,asset_object_type,asset_object_id,created_at);
        """)
        for table in TABLES:
            connection.executescript(f"""
            CREATE TRIGGER IF NOT EXISTS w3_{table}_no_update
            BEFORE UPDATE ON {table} BEGIN SELECT RAISE(ABORT,'wave3_append_only'); END;
            CREATE TRIGGER IF NOT EXISTS w3_{table}_no_delete
            BEFORE DELETE ON {table} BEGIN SELECT RAISE(ABORT,'wave3_append_only'); END;
            """)
        connection.commit()
        rows = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in TABLES}
        return {"schema_complete": True, "rows": rows, "records_created": 0}
    except Magc1Wave3MigrationError:
        connection.rollback()
        raise
    except sqlite3.DatabaseError as exc:
        connection.rollback()
        raise Magc1Wave3MigrationError(str(exc)) from exc
    finally:
        connection.close()
