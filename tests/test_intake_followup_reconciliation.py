import sqlite3

import pytest

from database.intake_followup_reconciliation_migration import (
    apply_intake_followup_reconciliation_schema,
)
from services.services_intake_followup_reconciliation import (
    IntakeFollowupReconciliationError,
    get_intake_followup_reconciliation_history,
    reconcile_exact_followup_duplicates,
    reconcile_followup_duplicate,
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
    path = tmp_path / "reconciliation.db"
    con = sqlite3.connect(path)
    con.execute(TASK_SCHEMA)
    con.executemany(
        """INSERT INTO intake_followup_tasks VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, 'generated', 'c', 'u', 'maker', ?, ?, ?, ?)""",
        [
            (1, "I1", "F1", "staff_action", "high", "pending_staff",
             " Exact task ", "same  text", None, None, None, None),
            (2, "I1", "F1", "STAFF_ACTION", "HIGH", "PENDING_STAFF",
             "exact TASK", " same text ", None, None, "S1", "B1"),
            (3, "I1", "F1", "staff_action", "normal", "pending_client",
             "Legacy distinct", "legacy", None, None, None, None),
            (4, "I1", "F1", "staff_action", "normal", "pending_client",
             "Governed distinct", "governed", None, None, "S1", "B1"),
            (5, "I1", "F1", "staff_action", "normal", "pending_client",
             "Same title", "legacy description", None, None, None, None),
            (6, "I1", "F1", "staff_action", "normal", "pending_client",
             "Same title", "different description", None, None, "S1", "B1"),
            (7, "I2", "F1", "staff_action", "high", "pending_staff",
             "Exact task", "same text", None, None, "S2", "B2"),
            (8, "I1", "F2", "staff_action", "high", "pending_staff",
             "Exact task", "same text", None, None, "S3", "B3"),
        ],
    )
    con.commit()
    con.close()
    return path


def _rows(path):
    con = sqlite3.connect(path)
    rows = con.execute("SELECT * FROM intake_followup_tasks ORDER BY id").fetchall()
    con.close()
    return rows


def test_migration_is_additive_and_idempotent(tmp_path):
    path = _db(tmp_path)
    before = _rows(path)
    first = apply_intake_followup_reconciliation_schema(path)
    second = apply_intake_followup_reconciliation_schema(path)
    assert first["table_created"] is True
    assert second["table_created"] is False
    assert before == _rows(path)


def test_exact_reconciliation_preserves_tasks_and_history(tmp_path):
    path = _db(tmp_path)
    apply_intake_followup_reconciliation_schema(path)
    before = _rows(path)
    first = reconcile_exact_followup_duplicates(path, "F1", "I1", "operator")
    second = reconcile_exact_followup_duplicates(path, "F1", "I1", "operator")
    assert first["records_created"] == 1
    assert second["records_created"] == 0
    assert _rows(path) == before
    history = get_intake_followup_reconciliation_history(path, "F1", "I1")
    assert len(history) == 1
    assert history[0]["superseded_followup_task_id"] == 1
    assert history[0]["replacement_followup_task_id"] == 2
    assert history[0]["reconciliation_type"] == "superseded_duplicate"
    # Distinct and title-only rows remain outside the ledger.
    assert {3, 4, 5, 6}.isdisjoint(
        {history[0]["superseded_followup_task_id"]}
    )


def test_ambiguous_exact_matches_are_left_untouched(tmp_path):
    path = _db(tmp_path)
    con = sqlite3.connect(path)
    con.execute(
        """INSERT INTO intake_followup_tasks VALUES
        (9, 'I1', 'F1', 'staff_action', 'high', 'pending_staff',
         'Exact task', 'same text', 'generated', 'c', 'u', 'maker',
         NULL, NULL, NULL, NULL)"""
    )
    con.commit()
    con.close()
    apply_intake_followup_reconciliation_schema(path)
    result = reconcile_exact_followup_duplicates(path, "F1", "I1", "operator")
    assert result["records_created"] == 0
    assert get_intake_followup_reconciliation_history(path, "F1", "I1") == []


@pytest.mark.parametrize(
    "firm,intake,old,new",
    [
        ("F2", "I1", 1, 8),       # cross-firm
        ("F1", "I2", 1, 7),       # cross-intake
        ("F1", "I1", 2, 4),       # governed-to-governed
        ("F1", "I1", 1, 3),       # legacy-to-legacy
        ("F1", "I1", 5, 6),       # title-only
    ],
)
def test_invalid_explicit_pairs_are_prohibited(tmp_path, firm, intake, old, new):
    path = _db(tmp_path)
    apply_intake_followup_reconciliation_schema(path)
    with pytest.raises(IntakeFollowupReconciliationError):
        reconcile_followup_duplicate(path, firm, intake, old, new, "operator")
    assert get_intake_followup_reconciliation_history(path, firm, intake) == []


def test_active_listing_and_history_compatibility(tmp_path, monkeypatch):
    path = _db(tmp_path)
    monkeypatch.setattr(intake_service, "ensure_intake_followup_task_tables", lambda: None)
    monkeypatch.setattr(intake_service, "get_current_firm_id", lambda: "F1")
    monkeypatch.setattr(intake_service, "get_connection", lambda: sqlite3.connect(path))

    # Before ledger installation, old listing behavior remains intact.
    assert {row["id"] for row in intake_service.list_intake_followup_tasks("I1")} == {
        1, 2, 3, 4, 5, 6, 8
    }
    apply_intake_followup_reconciliation_schema(path)
    reconcile_exact_followup_duplicates(path, "F1", "I1", "operator")
    active_ids = {row["id"] for row in intake_service.list_intake_followup_tasks("I1")}
    history_ids = {
        row["id"]
        for row in intake_service.list_intake_followup_tasks(
            "I1", include_reconciled=True
        )
    }
    assert active_ids == {2, 3, 4, 5, 6, 8}
    assert history_ids == {1, 2, 3, 4, 5, 6, 8}
