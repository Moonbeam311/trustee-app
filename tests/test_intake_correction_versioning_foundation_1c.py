import sqlite3

import pytest

from database.intake_correction_versioning_migration import (
    NEW_TABLES,
    apply_intake_correction_versioning_schema,
)


LEGACY_SCHEMA = """
CREATE TABLE intake_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intake_id TEXT NOT NULL,
    firm_id TEXT,
    question_key TEXT NOT NULL,
    answer_key TEXT NOT NULL,
    answer_label TEXT,
    created_at TEXT,
    created_by TEXT
);
CREATE TABLE intake_translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intake_id TEXT NOT NULL,
    firm_id TEXT,
    source_key TEXT NOT NULL,
    system_category TEXT,
    system_meaning TEXT,
    module_trigger TEXT,
    document_request TEXT,
    next_session TEXT,
    risk_flag TEXT,
    created_at TEXT,
    created_by TEXT
);
CREATE TABLE intake_followup_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intake_id TEXT NOT NULL,
    firm_id TEXT,
    task_type TEXT,
    priority TEXT,
    status TEXT,
    title TEXT NOT NULL,
    description TEXT,
    source TEXT,
    created_at TEXT,
    updated_at TEXT,
    created_by TEXT,
    completed_at TEXT,
    completed_by TEXT
);
INSERT INTO intake_answers VALUES
    (1, 'INT-LEGACY', 'FIRM-1', 'assets', 'home', 'Home', 't0', 'user-1');
INSERT INTO intake_translations VALUES
    (1, 'INT-LEGACY', 'FIRM-1', 'assets.home', 'ASSET', 'real_property',
     'property', 'deed', 'asset_review', NULL, 't0', 'system');
INSERT INTO intake_followup_tasks VALUES
    (1, 'INT-LEGACY', 'FIRM-1', 'document', 'normal', 'open', 'Get deed',
     'Legacy description', 'manual', 't0', 't0', 'user-1', NULL, NULL);
"""


REQUIRED_COLUMNS = {
    "intake_answer_revisions": {
        "answer_revision_id", "intake_id", "firm_id", "answer_revision_no",
        "revision_status", "supersedes_revision_id", "created_at", "created_by",
        "confirmed_at", "confirmed_by",
    },
    "intake_answer_revision_items": {
        "id", "answer_revision_id", "question_key", "answer_key", "answer_label",
        "created_at", "created_by",
    },
    "intake_snapshot_versions": {
        "snapshot_version_id", "intake_id", "firm_id", "answer_revision_id",
        "snapshot_version_no", "generation_batch_id", "confirmation_status",
        "supersedes_snapshot_id", "generated_at", "generated_by", "confirmed_at",
        "confirmed_by",
    },
    "intake_snapshot_translation_items": {
        "id", "snapshot_version_id", "source_key", "system_category",
        "system_meaning", "module_trigger", "document_request", "next_session",
        "risk_flag", "created_at", "created_by",
    },
    "intake_snapshot_proposed_tasks": {
        "proposed_task_id", "snapshot_version_id", "generation_batch_id",
        "task_type", "priority", "title", "description", "source",
        "proposal_status", "materialized_followup_task_id", "created_at",
        "created_by", "materialized_at",
    },
}


def _make_legacy_db(tmp_path):
    db_path = tmp_path / "intake-correction-foundation.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(LEGACY_SCHEMA)
    return db_path


def _insert_revision(connection, revision_id="REV-1", number=1, status="draft"):
    connection.execute(
        """
        INSERT INTO intake_answer_revisions (
            answer_revision_id, intake_id, firm_id, answer_revision_no,
            revision_status, created_at
        ) VALUES (?, 'INT-1', 'FIRM-1', ?, ?, '2026-09-18T00:00:00Z')
        """,
        (revision_id, number, status),
    )


def _insert_snapshot(connection, snapshot_id="SNAP-1", number=1, status="awaiting_confirmation"):
    connection.execute(
        """
        INSERT INTO intake_snapshot_versions (
            snapshot_version_id, intake_id, firm_id, answer_revision_id,
            snapshot_version_no, generation_batch_id, confirmation_status,
            generated_at
        ) VALUES (?, 'INT-1', 'FIRM-1', 'REV-1', ?, 'BATCH-1', ?,
                  '2026-09-18T00:01:00Z')
        """,
        (snapshot_id, number, status),
    )


def test_migration_is_idempotent_complete_and_preserves_legacy_data(tmp_path):
    db_path = _make_legacy_db(tmp_path)
    with sqlite3.connect(db_path) as connection:
        before = {
            table: connection.execute(f"SELECT * FROM {table}").fetchall()
            for table in ("intake_answers", "intake_translations")
        }
        followup_before = connection.execute(
            "SELECT id, intake_id, firm_id, task_type, priority, status, title, "
            "description, source, created_at, updated_at, created_by, completed_at, "
            "completed_by FROM intake_followup_tasks"
        ).fetchall()

    first = apply_intake_correction_versioning_schema(db_path)
    second = apply_intake_correction_versioning_schema(db_path)

    assert first["schema_complete"] is True
    assert first["followup_columns_added"] == (
        "snapshot_version_id", "generation_batch_id"
    )
    assert second["schema_complete"] is True
    assert second["followup_columns_added"] == ()

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert set(NEW_TABLES).issubset(tables)
        assert {"intake_answers", "intake_translations", "intake_followup_tasks"}.issubset(tables)

        for table, required in REQUIRED_COLUMNS.items():
            columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
            assert required.issubset(columns)

        followup_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(intake_followup_tasks)")
        }
        assert {"snapshot_version_id", "generation_batch_id"}.issubset(followup_columns)
        for table, rows in before.items():
            assert connection.execute(f"SELECT * FROM {table}").fetchall() == rows
        assert connection.execute(
            "SELECT id, intake_id, firm_id, task_type, priority, status, title, "
            "description, source, created_at, updated_at, created_by, completed_at, "
            "completed_by FROM intake_followup_tasks"
        ).fetchall() == followup_before
        assert connection.execute(
            "SELECT snapshot_version_id, generation_batch_id FROM intake_followup_tasks"
        ).fetchall() == [(None, None)]


def test_governed_uniqueness_statuses_and_multiselect(tmp_path):
    db_path = _make_legacy_db(tmp_path)
    apply_intake_correction_versioning_schema(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        _insert_revision(connection)

        with pytest.raises(sqlite3.IntegrityError):
            _insert_revision(connection, "REV-DUPLICATE-NUMBER", 1)
        with pytest.raises(sqlite3.IntegrityError):
            _insert_revision(connection, "REV-BAD-STATUS", 2, "edited")

        connection.executemany(
            """
            INSERT INTO intake_answer_revision_items (
                answer_revision_id, question_key, answer_key, answer_label,
                created_at
            ) VALUES ('REV-1', 'assets', ?, ?, '2026-09-18T00:00:00Z')
            """,
            [("home", "Home"), ("business", "Business")],
        )
        assert connection.execute(
            "SELECT answer_key FROM intake_answer_revision_items "
            "WHERE answer_revision_id = 'REV-1' AND question_key = 'assets' "
            "ORDER BY id"
        ).fetchall() == [("home",), ("business",)]
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO intake_answer_revision_items (
                    answer_revision_id, question_key, answer_key, answer_label,
                    created_at
                ) VALUES ('REV-1', 'assets', 'home', 'Home', 'later')
                """
            )

        _insert_snapshot(connection)
        with pytest.raises(sqlite3.IntegrityError):
            _insert_snapshot(connection, "SNAP-DUPLICATE-NUMBER", 1)
        with pytest.raises(sqlite3.IntegrityError):
            _insert_snapshot(connection, "SNAP-BAD-STATUS", 2, "draft")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO intake_snapshot_proposed_tasks (
                    proposed_task_id, snapshot_version_id, generation_batch_id,
                    proposal_status, created_at
                ) VALUES ('PROP-1', 'SNAP-1', 'BATCH-1', 'confirmed', 't1')
                """
            )


def test_absent_followup_table_is_not_created(tmp_path):
    db_path = tmp_path / "without-followups.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE intake_answers (id INTEGER PRIMARY KEY, marker TEXT)")
        connection.execute("INSERT INTO intake_answers VALUES (1, 'unchanged')")

    apply_intake_correction_versioning_schema(db_path)
    apply_intake_correction_versioning_schema(db_path)

    with sqlite3.connect(db_path) as connection:
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='intake_followup_tasks'"
        ).fetchone() is None
        assert connection.execute("SELECT * FROM intake_answers").fetchall() == [(1, "unchanged")]


def test_migration_requires_an_explicit_database_path():
    with pytest.raises(ValueError, match="db_path is required"):
        apply_intake_correction_versioning_schema("")
    with pytest.raises(ValueError, match="db_path is required"):
        apply_intake_correction_versioning_schema(None)
