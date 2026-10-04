import hashlib
import sqlite3

import database.db as db
import services.services_intake as intake_service


SESSION_SCHEMA = """
CREATE TABLE intake_sessions (
    id INTEGER PRIMARY KEY,
    intake_id TEXT,
    firm_id TEXT,
    next_screen TEXT,
    status TEXT,
    completed_at TEXT,
    created_at TEXT,
    updated_at TEXT
)
"""


def _database(tmp_path, *, status="in_progress", next_screen="universal_profile"):
    path = tmp_path / "resolver.db"

    with sqlite3.connect(path) as connection:
        connection.execute(SESSION_SCHEMA)
        connection.execute(
            """
            INSERT INTO intake_sessions (
                id, intake_id, firm_id, next_screen, status,
                completed_at, created_at, updated_at
            )
            VALUES (1, 'I1', 'F1', ?, ?, NULL, 'c', 'u')
            """,
            (next_screen, status),
        )

    return path


def _use(path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(path))


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _add_version_tables(path):
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE intake_answer_revisions (
                answer_revision_id TEXT PRIMARY KEY,
                intake_id TEXT,
                firm_id TEXT,
                answer_revision_no INTEGER,
                revision_status TEXT,
                supersedes_revision_id TEXT,
                created_at TEXT,
                confirmed_at TEXT
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE intake_snapshot_versions (
                snapshot_version_id TEXT PRIMARY KEY,
                intake_id TEXT,
                firm_id TEXT,
                answer_revision_id TEXT,
                snapshot_version_no INTEGER,
                generation_batch_id TEXT,
                confirmation_status TEXT,
                supersedes_snapshot_id TEXT,
                generated_at TEXT,
                confirmed_at TEXT
            )
            """
        )


def test_resolver_is_firm_scoped_and_read_only(tmp_path, monkeypatch):
    path = _database(tmp_path)
    _use(path, monkeypatch)

    before = _sha256(path)

    result = intake_service.resolve_intake_continuation("I1", "F2")

    after = _sha256(path)

    assert result["stage"] == "not_found"
    assert result["reason_code"] == "scoped_intake_not_found"
    assert before == after


def test_early_intake_fallback_does_not_invent_missing_counts(
    tmp_path,
    monkeypatch,
):
    path = _database(tmp_path)
    _use(path, monkeypatch)

    result = intake_service.resolve_intake_continuation("I1", "F1")

    assert result["stage"] == "intake"
    assert result["early_next_screen"] == "universal_profile"
    assert result["pending_confirmation"] is None
    assert result["open_issue_count"] is None
    assert result["open_task_count"] is None


def test_confirmed_baseline_uses_lifecycle_not_highest_version(
    tmp_path,
    monkeypatch,
):
    path = _database(tmp_path, status="snapshot_saved")
    _add_version_tables(path)

    with sqlite3.connect(path) as connection:
        connection.executemany(
            """
            INSERT INTO intake_answer_revisions VALUES
            (?, 'I1', 'F1', ?, ?, ?, ?, ?)
            """,
            [
                ("R1", 1, "superseded", None, "1", None),
                ("R2", 2, "confirmed", "R1", "2", "2"),
                ("R3", 3, "superseded", "R2", "3", None),
            ],
        )

        connection.executemany(
            """
            INSERT INTO intake_snapshot_versions VALUES
            (?, 'I1', 'F1', ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("S1", "R1", 1, "B1", "superseded", None, "1", None),
                ("S2", "R2", 2, "B2", "confirmed", "S1", "2", "2"),
                ("S3", "R3", 3, "B3", "superseded", "S2", "3", None),
            ],
        )

    _use(path, monkeypatch)

    result = intake_service.resolve_intake_continuation("I1", "F1")

    assert result["confirmed_answer_revision_id"] == "R2"
    assert result["confirmed_snapshot_version_id"] == "S2"
    assert result["pending_confirmation"] is False
    assert result["stage"] == "snapshot_review"
    assert result["is_terminal"] is False


def test_pending_confirmation_outranks_professional_review(
    tmp_path,
    monkeypatch,
):
    path = _database(tmp_path, status="snapshot_saved")
    _add_version_tables(path)

    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            INSERT INTO intake_answer_revisions VALUES
            ('R1', 'I1', 'F1', 1, 'confirmed', NULL, '1', '1')
            """
        )

        connection.execute(
            """
            INSERT INTO intake_snapshot_versions VALUES
            (
                'S1', 'I1', 'F1', 'R1', 1, 'B1',
                'awaiting_confirmation', NULL, '1', NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE professional_review_issues (
                id INTEGER PRIMARY KEY,
                issue_id TEXT,
                intake_id TEXT,
                firm_id TEXT,
                workflow_key TEXT,
                severity TEXT,
                status TEXT,
                disposition TEXT,
                recommended_action TEXT,
                linked_record_type TEXT,
                linked_record_id TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )

        connection.execute(
            """
            INSERT INTO professional_review_issues VALUES
            (
                1, 'P1', 'I1', 'F1', 'professional_review_checklist',
                'major', 'open', NULL, NULL, NULL, NULL, 'c', 'u'
            )
            """
        )

    _use(path, monkeypatch)

    result = intake_service.resolve_intake_continuation("I1", "F1")

    assert result["pending_confirmation"] is True
    assert result["open_issue_count"] == 1
    assert result["stage"] == "confirmation_review"
    assert result["reason_code"] == "pending_confirmation"


def test_professional_review_owns_stage_and_governed_task_count(
    tmp_path,
    monkeypatch,
):
    path = _database(tmp_path, status="snapshot_saved")
    _add_version_tables(path)

    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            INSERT INTO intake_answer_revisions VALUES
            ('R2', 'I1', 'F1', 2, 'confirmed', NULL, '2', '2')
            """
        )

        connection.execute(
            """
            INSERT INTO intake_snapshot_versions VALUES
            ('S2', 'I1', 'F1', 'R2', 2, 'B2',
             'confirmed', NULL, '2', '2')
            """
        )

        connection.execute(
            """
            CREATE TABLE professional_review_issues (
                id INTEGER PRIMARY KEY,
                issue_id TEXT,
                intake_id TEXT,
                firm_id TEXT,
                workflow_key TEXT,
                severity TEXT,
                status TEXT,
                disposition TEXT,
                recommended_action TEXT,
                linked_record_type TEXT,
                linked_record_id TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )

        connection.executemany(
            """
            INSERT INTO professional_review_issues VALUES
            (?, ?, 'I1', 'F1', 'professional_review_checklist',
             'major', ?, ?, NULL, NULL, NULL, 'c', 'u')
            """,
            [
                (1, "P1", "open", None),
                (2, "P2", "escalated", "escalated"),
                (3, "P3", "resolved", "source_cleared"),
            ],
        )

        connection.execute(
            """
            CREATE TABLE intake_followup_tasks (
                id INTEGER PRIMARY KEY,
                intake_id TEXT,
                firm_id TEXT,
                status TEXT
            )
            """
        )

        connection.executemany(
            """
            INSERT INTO intake_followup_tasks VALUES
            (?, 'I1', 'F1', ?)
            """,
            [
                (1, "open"),
                (2, "open"),
                (3, "completed"),
                (4, "pending_staff"),
            ],
        )

        connection.execute(
            """
            CREATE TABLE intake_followup_reconciliations (
                reconciliation_id TEXT PRIMARY KEY,
                firm_id TEXT,
                intake_id TEXT,
                superseded_followup_task_id INTEGER,
                replacement_followup_task_id INTEGER
            )
            """
        )

        connection.execute(
            """
            INSERT INTO intake_followup_reconciliations VALUES
            ('REC1', 'F1', 'I1', 1, 4)
            """
        )

        connection.execute(
            """
            CREATE TABLE intake_followup_task_lifecycle_events (
                id INTEGER PRIMARY KEY,
                event_id TEXT,
                task_id INTEGER,
                intake_id TEXT,
                firm_id TEXT,
                event_type TEXT
            )
            """
        )

        connection.execute(
            """
            INSERT INTO intake_followup_task_lifecycle_events VALUES
            (1, 'E1', 2, 'I1', 'F1', 'no_successor_retired')
            """
        )

    _use(path, monkeypatch)

    result = intake_service.resolve_intake_continuation("I1", "F1")

    assert result["stage"] == "professional_review"
    assert result["state"] == "blocked"
    assert result["open_issue_count"] == 2
    assert result["blocking_issue_count"] == 2

    # Raw physical task rows = 4.
    # Task 1 is reconciliation-superseded.
    # Task 2 is effectively retired.
    # Task 3 remains completed.
    # Task 4 remains open.
    assert result["task_count"] == 2
    assert result["completed_task_count"] == 1
    assert result["open_task_count"] == 1


def test_review_gate_can_require_review_when_issue_registry_absent(
    tmp_path,
    monkeypatch,
):
    path = _database(tmp_path, status="snapshot_saved")

    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE intake_review_gate_ledger (
                id INTEGER PRIMARY KEY,
                intake_id TEXT,
                workflow_key TEXT,
                document_key TEXT,
                firm_id TEXT,
                gate_name TEXT,
                gate_status TEXT,
                gate_reason TEXT,
                missing_answer_count INTEGER,
                open_issue_count INTEGER,
                open_task_count INTEGER,
                document_status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )

        connection.execute(
            """
            INSERT INTO intake_review_gate_ledger VALUES
            (
                1, 'I1', 'professional_review_checklist',
                'urgent_issue_checklist', 'F1',
                'non_final_draft_review_gate',
                'professional_review_required',
                'Professional review required.',
                0, 8, 24, 'Review Required', 'c', 'u'
            )
            """
        )

    _use(path, monkeypatch)

    result = intake_service.resolve_intake_continuation("I1", "F1")

    assert result["stage"] == "professional_review"
    assert result["reason_code"] == "professional_review_required"

    # Registry is absent, so the resolver must not convert
    # review-gate projection counts into canonical issue counts.
    assert result["open_issue_count"] is None


def test_completed_is_terminal_only_when_no_stronger_state_exists(
    tmp_path,
    monkeypatch,
):
    path = _database(
        tmp_path,
        status="completed",
        next_screen="universal_profile",
    )
    _use(path, monkeypatch)

    result = intake_service.resolve_intake_continuation("I1", "F1")

    assert result["stage"] == "completed"
    assert result["is_terminal"] is True
