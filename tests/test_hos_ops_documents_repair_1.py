import sqlite3

from database.migrations_document_base_schema import (
    DOCUMENT_TEMPLATE_REQUIRED_COLUMNS,
    GENERATED_DOCUMENT_BASE_COLUMNS,
    apply_document_base_schema,
)
from database.startup_migrations import run_additive_startup_migrations


def _columns(db_path, table):
    conn = sqlite3.connect(str(db_path))
    try:
        return {
            row[1]
            for row in conn.execute(
                f"PRAGMA table_info({table})"
            ).fetchall()
        }
    finally:
        conn.close()


def _count(db_path, table):
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
    finally:
        conn.close()


def test_fresh_database_creates_document_base_schema_without_seed_rows(tmp_path):
    db_path = tmp_path / "fresh.db"

    result = apply_document_base_schema(db_path)

    assert result["schema_complete"] is True
    assert result["deferred"] is False
    assert result["document_templates_table_created"] is True
    assert result["generated_documents_table_created"] is True
    assert result["template_rows_seeded"] == 0
    assert result["records_created"] == 0

    assert DOCUMENT_TEMPLATE_REQUIRED_COLUMNS <= _columns(
        db_path, "document_templates"
    )
    assert GENERATED_DOCUMENT_BASE_COLUMNS <= _columns(
        db_path, "generated_documents"
    )
    assert _count(db_path, "document_templates") == 0
    assert _count(db_path, "generated_documents") == 0


def test_document_base_schema_is_idempotent(tmp_path):
    db_path = tmp_path / "idempotent.db"

    first = apply_document_base_schema(db_path)
    second = apply_document_base_schema(db_path)

    assert first["document_templates_table_created"] is True
    assert first["generated_documents_table_created"] is True
    assert second["document_templates_table_created"] is False
    assert second["generated_documents_table_created"] is False
    assert second["document_templates_rows_preserved"] == 0
    assert second["generated_documents_rows_preserved"] == 0
    assert second["template_rows_seeded"] == 0
    assert _count(db_path, "document_templates") == 0
    assert _count(db_path, "generated_documents") == 0


def test_existing_document_tables_and_rows_are_preserved(tmp_path):
    db_path = tmp_path / "existing.db"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            '''
            CREATE TABLE document_templates (
                template_id TEXT,
                name TEXT,
                category TEXT,
                description TEXT,
                template_body TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            '''
        )
        conn.execute(
            '''
            CREATE TABLE generated_documents (
                document_id TEXT,
                workspace_id TEXT,
                trust_id TEXT,
                template_id TEXT,
                title TEXT,
                content TEXT,
                status TEXT,
                created_by TEXT,
                created_at TEXT,
                updated_at TEXT,
                owner_id TEXT
            )
            '''
        )
        conn.execute(
            '''
            INSERT INTO document_templates (
                template_id, name, category, description,
                template_body, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                "TPL-KEEP",
                "Keep Template",
                "test",
                "sentinel",
                "{{title}}",
                "active",
                "2026-09-07T00:00:00",
                "2026-09-07T00:00:00",
            ),
        )
        conn.execute(
            '''
            INSERT INTO generated_documents (
                document_id, workspace_id, trust_id, template_id,
                title, content, status, created_by,
                created_at, updated_at, owner_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                "DOC-KEEP",
                "WS-KEEP",
                "TR-KEEP",
                "TPL-KEEP",
                "Keep Document",
                "sentinel content",
                "draft",
                "tester",
                "2026-09-07T00:00:00",
                "2026-09-07T00:00:00",
                "OWNER-KEEP",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    before = sqlite3.connect(str(db_path))
    try:
        template_row = before.execute(
            "SELECT * FROM document_templates"
        ).fetchone()
        generated_row = before.execute(
            "SELECT * FROM generated_documents"
        ).fetchone()
    finally:
        before.close()

    result = apply_document_base_schema(db_path)

    assert result["document_templates_table_created"] is False
    assert result["generated_documents_table_created"] is False
    assert result["document_templates_rows_preserved"] == 1
    assert result["generated_documents_rows_preserved"] == 1
    assert result["template_rows_seeded"] == 0

    after = sqlite3.connect(str(db_path))
    try:
        assert after.execute(
            "SELECT * FROM document_templates"
        ).fetchone() == template_row
        assert after.execute(
            "SELECT * FROM generated_documents"
        ).fetchone() == generated_row
    finally:
        after.close()


def test_startup_orders_document_base_before_hos_doc_attribution(tmp_path):
    db_path = tmp_path / "startup.db"

    result = run_additive_startup_migrations(db_path)

    base = result["document_base_schema"]
    attribution = result["generated_document_attribution"]

    assert base["schema_complete"] is True
    assert base["document_templates_table_created"] is True
    assert base["generated_documents_table_created"] is True
    assert base["template_rows_seeded"] == 0

    assert attribution["schema_complete"] is True
    assert attribution["deferred"] is False
    assert attribution["columns_added"] == 4

    generated_columns = _columns(db_path, "generated_documents")
    assert {
        "firm_id",
        "source_record_type",
        "source_record_id",
        "generation_basis",
    } <= generated_columns

    assert _count(db_path, "document_templates") == 0
    assert _count(db_path, "generated_documents") == 0


def test_repeated_startup_keeps_document_schema_empty_and_complete(tmp_path):
    db_path = tmp_path / "repeat-startup.db"

    first = run_additive_startup_migrations(db_path)
    second = run_additive_startup_migrations(db_path)

    assert first["document_base_schema"]["schema_complete"] is True
    assert second["document_base_schema"]["schema_complete"] is True
    assert second["document_base_schema"][
        "document_templates_table_created"
    ] is False
    assert second["document_base_schema"][
        "generated_documents_table_created"
    ] is False
    assert second["generated_document_attribution"][
        "schema_complete"
    ] is True
    assert second["generated_document_attribution"][
        "columns_added"
    ] == 0
    assert _count(db_path, "document_templates") == 0
    assert _count(db_path, "generated_documents") == 0
