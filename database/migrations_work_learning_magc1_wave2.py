"""Explicit, non-startup MAGC-1 Wave-2 schema for disposable SQLite databases."""
import sqlite3
from pathlib import Path


class Magc1Wave2MigrationError(RuntimeError):
    pass


TABLES = (
    "hub_authority_hierarchy_determinations",
    "hub_program_source_change_checks",
    "hub_authority_change_impacts",
)


def apply_magc1_wave2_schema(db_path: str | Path) -> dict[str, object]:
    connection = sqlite3.connect(Path(db_path))
    try:
        existing = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        required = {"hub_programs", "hub_program_source_references"}
        if not required.issubset(existing):
            raise Magc1Wave2MigrationError("wave2_requires_p05_substrate")
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS hub_authority_hierarchy_determinations (
          hierarchy_id TEXT PRIMARY KEY, firm_id TEXT NOT NULL,
          context_type TEXT NOT NULL CHECK(context_type IN ('PROGRAM','MATTER','TRUST','OTHER')),
          context_id TEXT NOT NULL, subject TEXT NOT NULL,
          hierarchy_kind TEXT NOT NULL CHECK(hierarchy_kind IN ('CONTROLLING_LAW','GOVERNING_INSTRUMENT','AUTHORITY_ORDER')),
          source_reference_id TEXT NOT NULL,
          hierarchy_state TEXT NOT NULL CHECK(hierarchy_state IN ('CONTROLLING','PERSUASIVE','SUPERSEDED','NOT_APPLICABLE','UNRESOLVED')),
          applicability_jurisdiction TEXT, document_object_type TEXT,
          document_object_id TEXT, basis TEXT NOT NULL, provenance TEXT NOT NULL,
          decision_origin TEXT NOT NULL CHECK(decision_origin IN ('SYSTEM_SUGGESTED','OPERATOR_OR_FIDUCIARY','PROFESSIONAL')),
          human_confirmed INTEGER NOT NULL CHECK(human_confirmed IN (0,1)),
          actor TEXT NOT NULL, actor_capacity TEXT NOT NULL,
          prior_hierarchy_id TEXT, created_at TEXT NOT NULL,
          FOREIGN KEY(source_reference_id) REFERENCES hub_program_source_references(source_reference_id),
          FOREIGN KEY(prior_hierarchy_id) REFERENCES hub_authority_hierarchy_determinations(hierarchy_id)
        );
        CREATE INDEX IF NOT EXISTS idx_magc2_hierarchy_scope ON hub_authority_hierarchy_determinations
          (firm_id,context_type,context_id,subject,hierarchy_kind,created_at);

        CREATE TABLE IF NOT EXISTS hub_program_source_change_checks (
          change_check_id TEXT PRIMARY KEY, program_id TEXT NOT NULL,
          source_reference_id TEXT NOT NULL, metadata_id TEXT,
          observation_state TEXT NOT NULL CHECK(observation_state IN ('NO_CHANGE','CHANGE_DETECTED','REVIEW_DUE','UNRESOLVED')),
          basis TEXT NOT NULL, provenance TEXT NOT NULL, actor TEXT NOT NULL,
          actor_capacity TEXT NOT NULL, prior_change_check_id TEXT, created_at TEXT NOT NULL,
          FOREIGN KEY(source_reference_id) REFERENCES hub_program_source_references(source_reference_id),
          FOREIGN KEY(prior_change_check_id) REFERENCES hub_program_source_change_checks(change_check_id)
        );
        CREATE INDEX IF NOT EXISTS idx_magc2_change_source ON hub_program_source_change_checks
          (program_id,source_reference_id,created_at);

        CREATE TABLE IF NOT EXISTS hub_authority_change_impacts (
          impact_id TEXT PRIMARY KEY, firm_id TEXT NOT NULL,
          context_type TEXT NOT NULL CHECK(context_type IN ('PROGRAM','MATTER','TRUST','OTHER')),
          context_id TEXT NOT NULL, subject TEXT NOT NULL,
          source_reference_id TEXT NOT NULL, change_check_id TEXT NOT NULL,
          applicability_id TEXT, hierarchy_id TEXT,
          impact_state TEXT NOT NULL CHECK(impact_state IN ('REVIEW_REQUIRED','UNDER_REVIEW','NO_IMPACT','RESOLVED','UNRESOLVED')),
          basis TEXT NOT NULL, provenance TEXT NOT NULL,
          decision_origin TEXT NOT NULL CHECK(decision_origin IN ('SYSTEM_SUGGESTED','OPERATOR_OR_FIDUCIARY','PROFESSIONAL')),
          actor TEXT NOT NULL, actor_capacity TEXT NOT NULL,
          prior_impact_id TEXT, created_at TEXT NOT NULL,
          FOREIGN KEY(source_reference_id) REFERENCES hub_program_source_references(source_reference_id),
          FOREIGN KEY(change_check_id) REFERENCES hub_program_source_change_checks(change_check_id),
          FOREIGN KEY(prior_impact_id) REFERENCES hub_authority_change_impacts(impact_id)
        );
        CREATE INDEX IF NOT EXISTS idx_magc2_impact_scope ON hub_authority_change_impacts
          (firm_id,context_type,context_id,subject,source_reference_id,created_at);
        """)
        for table in TABLES:
            connection.executescript(f"""
            CREATE TRIGGER IF NOT EXISTS magc2_{table}_no_update BEFORE UPDATE ON {table}
            BEGIN SELECT RAISE(ABORT,'magc2_append_only'); END;
            CREATE TRIGGER IF NOT EXISTS magc2_{table}_no_delete BEFORE DELETE ON {table}
            BEGIN SELECT RAISE(ABORT,'magc2_append_only'); END;
            """)
        connection.commit()
        return {"schema_complete": True, "records_created": 0}
    except sqlite3.DatabaseError as exc:
        connection.rollback()
        raise Magc1Wave2MigrationError(str(exc)) from exc
    finally:
        connection.close()
