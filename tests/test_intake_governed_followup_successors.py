import sqlite3

import pytest

from database.intake_correction_versioning_migration import (
    apply_intake_correction_versioning_schema,
)
from database.intake_followup_reconciliation_migration import (
    apply_intake_followup_reconciliation_schema,
)
from services.services_intake_followup_reconciliation import (
    IntakeFollowupReconciliationError,
    reconcile_governed_snapshot_followup_successors,
)
import services.services_intake as intake_service


TASK_SCHEMA = """
CREATE TABLE intake_followup_tasks (
 id INTEGER PRIMARY KEY, intake_id TEXT NOT NULL, firm_id TEXT NOT NULL,
 task_type TEXT, priority TEXT, status TEXT, title TEXT, description TEXT,
 source TEXT, created_at TEXT, updated_at TEXT, created_by TEXT,
 completed_at TEXT, completed_by TEXT, snapshot_version_id TEXT,
 generation_batch_id TEXT
)
"""


def _db(tmp_path):
    path = tmp_path / "governed-successors.db"
    with sqlite3.connect(path) as connection:
        connection.execute(TASK_SCHEMA)
    apply_intake_correction_versioning_schema(path)
    apply_intake_followup_reconciliation_schema(path)
    with sqlite3.connect(path) as connection:
        connection.executemany(
            """
            INSERT INTO intake_answer_revisions
            (answer_revision_id, intake_id, firm_id, answer_revision_no,
             revision_status, created_at)
            VALUES (?, ?, ?, ?, 'confirmed', 't')
            """,
            [
                ("R1", "I1", "F1", 1), ("R2", "I1", "F1", 2),
                ("R3", "I1", "F1", 3), ("RX", "IX", "F1", 1),
                ("RF", "I1", "F2", 1),
            ],
        )
        connection.executemany(
            """
            INSERT INTO intake_snapshot_versions
            (snapshot_version_id, intake_id, firm_id, answer_revision_id,
             snapshot_version_no, generation_batch_id, confirmation_status,
             supersedes_snapshot_id, generated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 't')
            """,
            [
                ("S1", "I1", "F1", "R1", 1, "B1", "superseded", None),
                ("S2", "I1", "F1", "R2", 2, "B2", "confirmed", "S1"),
                ("S3", "I1", "F1", "R3", 3, "B3", "confirmed", "S2"),
                ("SU", "I1", "F1", "R3", 4, "BU", "awaiting_confirmation", "S3"),
                ("SX", "IX", "F1", "RX", 2, "BX", "confirmed", "S1"),
                ("SF", "I1", "F2", "RF", 2, "BF", "confirmed", "S1"),
            ],
        )
        connection.executemany(
            """
            INSERT INTO intake_followup_tasks VALUES
            (?, ?, ?, 'staff_action', ?, ?, ?, ?, 'generated', 'c', 'u',
             'maker', ?, ?, ?, ?)
            """,
            [
                (1, "I1", "F1", "high", "pending_staff", "Exact", "same", None, None, "S1", "B1"),
                (2, "I1", "F1", "HIGH", "PENDING_STAFF", " exact ", " same ", None, None, "S2", "B2"),
                (3, "I1", "F1", "normal", "completed", "Done", "history", "done-at", "operator", "S1", "B1"),
                (4, "I1", "F1", "normal", "completed", "Done", "history", None, None, "S2", "B2"),
                (5, "I1", "F1", "normal", "open", "Old only", "unmatched", None, None, "S1", "B1"),
                (6, "I1", "F1", "normal", "open", "New only", "unmatched", None, None, "S2", "B2"),
            ],
        )
    return path


def _run(path, predecessor="S1", successor="S2", firm="F1", intake="I1"):
    return reconcile_governed_snapshot_followup_successors(
        path, firm, intake, predecessor, successor, "operator"
    )


def _tasks(path):
    with sqlite3.connect(path) as connection:
        return connection.execute(
            "SELECT * FROM intake_followup_tasks ORDER BY id"
        ).fetchall()


def test_direct_confirmed_successor_is_ledgered_without_task_mutation_and_lists_correctly(
    tmp_path, monkeypatch
):
    path = _db(tmp_path)
    before = _tasks(path)
    first = _run(path)
    second = _run(path)
    assert first["records_created"] == 1
    assert second["records_created"] == 0
    assert _tasks(path) == before
    with sqlite3.connect(path) as connection:
        ledger = connection.execute(
            "SELECT superseded_followup_task_id, replacement_followup_task_id, "
            "reconciliation_type, reason FROM intake_followup_reconciliations"
        ).fetchall()
    assert ledger == [(1, 2, "superseded_duplicate", "Exact governed snapshot operational follow-up succession")]

    monkeypatch.setattr(intake_service, "ensure_intake_followup_task_tables", lambda: None)
    monkeypatch.setattr(intake_service, "get_current_firm_id", lambda: "F1")
    monkeypatch.setattr(intake_service, "get_connection", lambda: sqlite3.connect(path))
    active = {row["id"] for row in intake_service.list_intake_followup_tasks("I1")}
    all_rows = {row["id"] for row in intake_service.list_intake_followup_tasks("I1", include_reconciled=True)}
    assert active == {2, 3, 4, 5, 6}
    assert all_rows == {1, 2, 3, 4, 5, 6}


def test_completed_and_unmatched_tasks_remain_untouched(tmp_path):
    path = _db(tmp_path)
    before = _tasks(path)
    _run(path)
    assert _tasks(path) == before
    with sqlite3.connect(path) as connection:
        pairs = connection.execute(
            "SELECT superseded_followup_task_id, replacement_followup_task_id "
            "FROM intake_followup_reconciliations"
        ).fetchall()
    assert pairs == [(1, 2)]
    assert {3, 4, 5, 6}.isdisjoint({value for pair in pairs for value in pair})


@pytest.mark.parametrize("ambiguous_side", ["predecessor", "successor"])
def test_ambiguous_exact_matches_create_no_ledger_row(tmp_path, ambiguous_side):
    path = _db(tmp_path)
    with sqlite3.connect(path) as connection:
        if ambiguous_side == "predecessor":
            connection.execute(
                "INSERT INTO intake_followup_tasks SELECT 7, intake_id, firm_id, task_type, priority, status, title, description, source, created_at, updated_at, created_by, completed_at, completed_by, snapshot_version_id, generation_batch_id FROM intake_followup_tasks WHERE id=1"
            )
        else:
            connection.execute(
                "INSERT INTO intake_followup_tasks SELECT 7, intake_id, firm_id, task_type, priority, status, title, description, source, created_at, updated_at, created_by, completed_at, completed_by, snapshot_version_id, generation_batch_id FROM intake_followup_tasks WHERE id=2"
            )
    before = _tasks(path)
    assert _run(path)["records_created"] == 0
    assert _tasks(path) == before


@pytest.mark.parametrize(
    "firm,intake,predecessor,successor",
    [
        ("F1", "I1", "S1", "SF"),
        ("F1", "I1", "S1", "SX"),
        ("F1", "I1", "S1", "S3"),
        ("F1", "I1", "S3", "SU"),
    ],
)
def test_invalid_snapshot_relationships_are_prohibited(
    tmp_path, firm, intake, predecessor, successor
):
    path = _db(tmp_path)
    before = _tasks(path)
    with pytest.raises(IntakeFollowupReconciliationError):
        _run(path, predecessor, successor, firm, intake)
    assert _tasks(path) == before
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM intake_followup_reconciliations"
        ).fetchone()[0] == 0
