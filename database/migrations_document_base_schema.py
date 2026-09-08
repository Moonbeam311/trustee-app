"""Additive fresh-database base schema for the legacy document generator lane."""

import sqlite3
from pathlib import Path

DOCUMENT_TEMPLATE_REQUIRED_COLUMNS = {
    "template_id", "name", "category", "description",
    "template_body", "status", "created_at", "updated_at",
}

GENERATED_DOCUMENT_BASE_COLUMNS = {
    "document_id", "workspace_id", "trust_id", "template_id", "title",
    "content", "status", "created_by", "created_at", "updated_at", "owner_id",
}


class DocumentBaseSchemaMigrationError(RuntimeError):
    pass


def _columns(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def apply_document_base_schema(db_path):
    """Create only absent base tables; preserve all existing tables and rows."""
    conn = sqlite3.connect(str(Path(db_path)))
    try:
        existing = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name IN ('document_templates','generated_documents')"
            )
        }
        template_before = (
            _count(conn, "document_templates")
            if "document_templates" in existing else 0
        )
        generated_before = (
            _count(conn, "generated_documents")
            if "generated_documents" in existing else 0
        )

        checks = (
            ("document_templates", DOCUMENT_TEMPLATE_REQUIRED_COLUMNS),
            ("generated_documents", GENERATED_DOCUMENT_BASE_COLUMNS),
        )
        for table, required in checks:
            if table in existing:
                missing = required - _columns(conn, table)
                if missing:
                    raise DocumentBaseSchemaMigrationError(
                        f"existing {table} missing required columns: "
                        + ", ".join(sorted(missing))
                    )

        conn.execute("BEGIN")
        template_created = "document_templates" not in existing
        generated_created = "generated_documents" not in existing

        if template_created:
            conn.execute("""
                CREATE TABLE document_templates (
                    template_id TEXT,
                    name TEXT,
                    category TEXT,
                    description TEXT,
                    template_body TEXT,
                    status TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

        if generated_created:
            conn.execute("""
                CREATE TABLE generated_documents (
                    document_id TEXT,
                    workspace_id TEXT,
                    trust_id TEXT,
                    template_id TEXT,
                    title TEXT,
                    content TEXT,
                    status TEXT,
                    created_by TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    owner_id TEXT
                )
            """)

        if _count(conn, "document_templates") != template_before:
            raise DocumentBaseSchemaMigrationError(
                "document_templates row count changed"
            )
        if _count(conn, "generated_documents") != generated_before:
            raise DocumentBaseSchemaMigrationError(
                "generated_documents row count changed"
            )

        conn.commit()
        return {
            "schema_complete": True,
            "deferred": False,
            "reason": None,
            "document_templates_table_created": template_created,
            "generated_documents_table_created": generated_created,
            "document_templates_rows_preserved": template_before,
            "generated_documents_rows_preserved": generated_before,
            "template_rows_seeded": 0,
            "records_created": 0,
        }
    except DocumentBaseSchemaMigrationError:
        conn.rollback()
        raise
    except sqlite3.Error as exc:
        conn.rollback()
        raise DocumentBaseSchemaMigrationError(str(exc)) from exc
    finally:
        conn.close()
