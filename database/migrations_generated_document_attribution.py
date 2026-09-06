"""HOS-DOC-1 additive generated-document attribution migration."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


ADDITIVE_COLUMNS = {
    "firm_id": "TEXT",
    "source_record_type": "TEXT",
    "source_record_id": "TEXT",
    "generation_basis": "TEXT",
}

REQUIRED_LEGACY_COLUMNS = {
    "document_id",
    "workspace_id",
    "trust_id",
    "template_id",
    "title",
    "content",
    "status",
    "created_by",
    "created_at",
    "updated_at",
    "owner_id",
}


class GeneratedDocumentAttributionMigrationError(RuntimeError):
    pass


def apply_generated_document_attribution_schema(
    db_path: str | Path,
) -> dict[str, Any]:
    connection = sqlite3.connect(str(Path(db_path)))

    try:
        table = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type='table' AND name='generated_documents'
            """
        ).fetchone()

        if table is None:
            return {
                "schema_complete": False,
                "deferred": True,
                "reason": "generated_documents table is not present",
                "columns_added": 0,
                "legacy_rows_preserved": 0,
                "legacy_rows_updated": 0,
                "records_created": 0,
            }

        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(generated_documents)"
            ).fetchall()
        }

        missing = REQUIRED_LEGACY_COLUMNS - columns
        if missing:
            raise GeneratedDocumentAttributionMigrationError(
                "required legacy columns missing: "
                + ", ".join(sorted(missing))
            )

        before = connection.execute(
            "SELECT COUNT(*) FROM generated_documents"
        ).fetchone()[0]

        connection.execute("BEGIN")
        added = []

        for name, definition in ADDITIVE_COLUMNS.items():
            if name not in columns:
                connection.execute(
                    f"ALTER TABLE generated_documents "
                    f"ADD COLUMN {name} {definition}"
                )
                added.append(name)

        after = connection.execute(
            "SELECT COUNT(*) FROM generated_documents"
        ).fetchone()[0]

        if after != before:
            raise GeneratedDocumentAttributionMigrationError(
                "row count changed during additive migration"
            )

        connection.commit()

        return {
            "schema_complete": True,
            "deferred": False,
            "reason": None,
            "columns_added": len(added),
            "added_columns": tuple(added),
            "legacy_rows_preserved": before,
            "legacy_rows_updated": 0,
            "records_created": 0,
        }

    except GeneratedDocumentAttributionMigrationError:
        connection.rollback()
        raise
    except sqlite3.Error as exc:
        connection.rollback()
        raise GeneratedDocumentAttributionMigrationError(str(exc)) from exc
    finally:
        connection.close()
