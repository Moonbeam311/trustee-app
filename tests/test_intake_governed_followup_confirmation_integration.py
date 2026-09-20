import sqlite3

import pytest

from database.intake_correction_versioning_migration import (
    apply_intake_correction_versioning_schema,
)
from database.intake_followup_reconciliation_migration import (
    apply_intake_followup_reconciliation_schema,
)
import services.services_intake as intake_service
import services.services_intake_correction_versioning as versioning
from services.services_intake_followup_reconciliation import (
    IntakeFollowupReconciliationError,
)


BASE_SCHEMA = """
CREATE TABLE intake_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intake_id TEXT UNIQUE NOT NULL,
    firm_id TEXT NOT NULL
);
CREATE TABLE intake_followup_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intake_id TEXT NOT NULL, firm_id TEXT NOT NULL,
    task_type TEXT, priority TEXT, status TEXT, title TEXT NOT NULL,
    description TEXT, source TEXT, created_at TEXT, updated_at TEXT,
    created_by TEXT, completed_at TEXT, completed_by TEXT
);
INSERT INTO intake_sessions (intake_id, firm_id) VALUES ('INT-1', 'FIRM-1');
"""


def _db(tmp_path, *, ledger=True):
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / ("with-ledger.db" if ledger else "without-ledger.db")
    with sqlite3.connect(path) as connection:
        connection.executescript(BASE_SCHEMA)
    apply_intake_correction_versioning_schema(path)
    if ledger:
        apply_intake_followup_reconciliation_schema(path)
    return path


def _task(title, status="open"):
    return {
        "task_type": "document",
        "priority": "high",
        "operational_status": status,
        "title": title,
        "description": f"Description for {title}",
        "source": "guided_intake",
    }


def _revision(path, answer, actor="user"):
    return versioning.create_answer_revision(
        path,
        "FIRM-1",
        "INT-1",
        [{"question_key": "asset", "answer_key": answer}],
        actor,
    )


def _snapshot(path, revision, tasks):
    return versioning.create_snapshot_version(
        path,
        "FIRM-1",
        "INT-1",
        revision["answer_revision_id"],
        [],
        tasks,
        "engine",
    )


def _confirm(path, snapshot):
    return versioning.confirm_snapshot(
        path, "FIRM-1", "INT-1", snapshot["snapshot_version_id"], "reviewer"
    )


def _confirmed_predecessor(path, tasks):
    revision = _revision(path, "one")
    snapshot = _snapshot(path, revision, tasks)
    _confirm(path, snapshot)
    return snapshot


def test_confirmation_reconciles_exact_successor_without_mutating_tasks(
    tmp_path, monkeypatch
):
    path = _db(tmp_path)
    predecessor = _confirmed_predecessor(
        path, [_task("Exact"), _task("Completed"), _task("Old only")]
    )
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE intake_followup_tasks SET status='completed', "
            "completed_at='done', completed_by='worker' WHERE title='Completed'"
        )
        predecessor_rows = connection.execute(
            "SELECT * FROM intake_followup_tasks ORDER BY id"
        ).fetchall()

    successor = _snapshot(
        path,
        _revision(path, "two"),
        [_task("Exact"), _task("Completed"), _task("New only")],
    )
    first = _confirm(path, successor)
    second = _confirm(path, successor)
    assert first["materialized_task_count"] == 3
    assert first["already_confirmed"] is False
    assert second["materialized_task_count"] == 3
    assert second["already_confirmed"] is True

    with sqlite3.connect(path) as connection:
        all_rows = connection.execute(
            "SELECT * FROM intake_followup_tasks ORDER BY id"
        ).fetchall()
        pairs = connection.execute(
            "SELECT superseded_followup_task_id, replacement_followup_task_id "
            "FROM intake_followup_reconciliations"
        ).fetchall()
        exact_ids = connection.execute(
            "SELECT id FROM intake_followup_tasks WHERE title='Exact' ORDER BY id"
        ).fetchall()
        materialized = connection.execute(
            "SELECT COUNT(*) FROM intake_snapshot_proposed_tasks "
            "WHERE snapshot_version_id=? AND proposal_status='materialized'",
            (successor["snapshot_version_id"],),
        ).fetchone()[0]
    assert all_rows[:3] == predecessor_rows
    assert len(all_rows) == 6
    assert pairs == [(exact_ids[0][0], exact_ids[1][0])]
    assert materialized == 3

    monkeypatch.setattr(intake_service, "ensure_intake_followup_task_tables", lambda: None)
    monkeypatch.setattr(intake_service, "get_current_firm_id", lambda: "FIRM-1")
    monkeypatch.setattr(intake_service, "get_connection", lambda: sqlite3.connect(path))
    active = {row["id"] for row in intake_service.list_intake_followup_tasks("INT-1")}
    assert exact_ids[0][0] not in active
    assert exact_ids[1][0] in active


def test_first_snapshot_and_ledger_absent_preserve_confirmation_behavior(tmp_path):
    first_path = _db(tmp_path / "first")
    first = _snapshot(first_path, _revision(first_path, "one"), [_task("First")])
    assert first["supersedes_snapshot_id"] is None
    assert _confirm(first_path, first)["materialized_task_count"] == 1
    with sqlite3.connect(first_path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM intake_followup_reconciliations"
        ).fetchone()[0] == 0

    absent_path = _db(tmp_path / "absent", ledger=False)
    predecessor = _confirmed_predecessor(absent_path, [_task("Exact")])
    successor = _snapshot(
        absent_path, _revision(absent_path, "two"), [_task("Exact")]
    )
    assert successor["supersedes_snapshot_id"] == predecessor["snapshot_version_id"]
    assert _confirm(absent_path, successor)["materialized_task_count"] == 1
    with sqlite3.connect(absent_path) as connection:
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' "
            "AND name='intake_followup_reconciliations'"
        ).fetchone() is None


def test_reconciliation_failure_rolls_back_entire_confirmation(tmp_path, monkeypatch):
    path = _db(tmp_path)
    _confirmed_predecessor(path, [_task("Exact")])
    successor = _snapshot(path, _revision(path, "two"), [_task("Exact")])

    def fail(*args, **kwargs):
        raise IntakeFollowupReconciliationError("forced failure")

    monkeypatch.setattr(
        versioning,
        "reconcile_governed_snapshot_followup_successors_in_transaction",
        fail,
    )
    with pytest.raises(
        versioning.IntakeCorrectionVersioningError,
        match="governed follow-up succession failed: forced failure",
    ):
        _confirm(path, successor)

    with sqlite3.connect(path) as connection:
        snapshot_status = connection.execute(
            "SELECT confirmation_status FROM intake_snapshot_versions "
            "WHERE snapshot_version_id=?",
            (successor["snapshot_version_id"],),
        ).fetchone()[0]
        revision_status = connection.execute(
            "SELECT revision_status FROM intake_answer_revisions "
            "WHERE answer_revision_id=?",
            (successor["answer_revision_id"],),
        ).fetchone()[0]
        proposal = connection.execute(
            "SELECT proposal_status, materialized_followup_task_id "
            "FROM intake_snapshot_proposed_tasks WHERE snapshot_version_id=?",
            (successor["snapshot_version_id"],),
        ).fetchone()
        task_count = connection.execute(
            "SELECT COUNT(*) FROM intake_followup_tasks WHERE snapshot_version_id=?",
            (successor["snapshot_version_id"],),
        ).fetchone()[0]
        ledger_count = connection.execute(
            "SELECT COUNT(*) FROM intake_followup_reconciliations"
        ).fetchone()[0]
    assert snapshot_status == "awaiting_confirmation"
    assert revision_status == "awaiting_confirmation"
    assert proposal == ("proposed", None)
    assert task_count == 0
    assert ledger_count == 0
