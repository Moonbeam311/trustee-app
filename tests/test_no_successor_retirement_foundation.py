import sqlite3

import pytest

import services.services_intake as intake_service


TASK_SCHEMA = """
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
    completed_by TEXT,
    snapshot_version_id TEXT,
    generation_batch_id TEXT
)
"""


@pytest.fixture
def retirement_db(tmp_path, monkeypatch):
    path = tmp_path / "no-successor-retirement.db"
    with sqlite3.connect(path) as connection:
        connection.execute(TASK_SCHEMA)
        connection.execute("""
            CREATE TABLE intake_followup_reconciliations (
                reconciliation_id TEXT PRIMARY KEY,
                firm_id TEXT NOT NULL,
                intake_id TEXT NOT NULL,
                superseded_followup_task_id INTEGER NOT NULL UNIQUE,
                replacement_followup_task_id INTEGER NOT NULL,
                reconciliation_type TEXT NOT NULL,
                reason TEXT NOT NULL,
                reconciled_at TEXT NOT NULL,
                reconciled_by TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE intake_snapshot_versions (
                snapshot_version_id TEXT PRIMARY KEY,
                intake_id TEXT NOT NULL,
                firm_id TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE intake_snapshot_proposed_tasks (
                proposed_task_id TEXT PRIMARY KEY,
                snapshot_version_id TEXT NOT NULL,
                generation_batch_id TEXT NOT NULL,
                title TEXT,
                materialized_followup_task_id TEXT
            )
        """)
        connection.execute("""
            CREATE TABLE professional_review_issues (
                id INTEGER PRIMARY KEY,
                linked_record_type TEXT,
                linked_record_id TEXT
            )
        """)
        connection.executemany("""
            INSERT INTO intake_followup_tasks (
                id, intake_id, firm_id, task_type, priority, status, title,
                description, source, created_at, updated_at, created_by,
                completed_at, completed_by, snapshot_version_id,
                generation_batch_id
            ) VALUES (?, 'I1', 'F1', 'staff_action', 'normal', ?, ?, '',
                      'legacy', 'created', 'updated', 'maker', ?, ?, ?, ?)
        """, [
            (1, "open", "Eligible legacy", None, None, None, None),
            (2, "completed", "Completed", "done", "closer", None, None),
            (3, "open", "Versioned", None, None, "S-OLD", None),
            (4, "open", "Batched", None, None, None, "B-OLD"),
            (5, "open", "Superseded", None, None, None, None),
            (6, "open", "Replacement", None, None, None, None),
            (7, "open", "Materialized", None, None, None, None),
            (8, "open", "Governed title", None, None, None, None),
            (9, "open", "Professional Review", None, None, None, None),
            (10, "pending_staff", "Reconciliation bridge", None, None, None, None),
            (11, "pending_staff", "Ordinary active", None, None, None, None),
        ])
        connection.executemany("""
            INSERT INTO intake_followup_reconciliations VALUES
            (?, 'F1', 'I1', ?, ?, 'superseded_duplicate', 'reason', 'now', 'actor')
        """, [
            ("R1", 5, 10),
            ("R2", 10, 6),
        ])
        connection.execute(
            "INSERT INTO intake_snapshot_versions VALUES ('S1', 'I1', 'F1')"
        )
        connection.executemany("""
            INSERT INTO intake_snapshot_proposed_tasks VALUES (?, 'S1', ?, ?, ?)
        """, [
            ("P1", "B1", "Different title", "7"),
            ("P2", "B2", " governed TITLE ", None),
        ])
        connection.execute("""
            INSERT INTO professional_review_issues
            VALUES (1, 'intake_followup_task', '9')
        """)

    monkeypatch.setattr(
        intake_service, "ensure_intake_review_note_tables", lambda: None
    )
    monkeypatch.setattr(
        intake_service, "get_connection", lambda: sqlite3.connect(path)
    )
    monkeypatch.setattr(intake_service, "get_current_firm_id", lambda: "F1")
    intake_service.ensure_intake_followup_task_tables()
    return path


def _evaluate(path, task_id):
    with sqlite3.connect(path) as connection:
        return intake_service.evaluate_no_successor_retirement_eligibility(
            task_id, connection=connection
        )


def _retire(path, task_id=1):
    with sqlite3.connect(path) as connection:
        return intake_service.record_no_successor_task_retirement(
            task_id, "operator", "trustee", "manual legacy review",
            connection=connection,
        )


def _reactivate(path, task_id=1):
    with sqlite3.connect(path) as connection:
        return intake_service.record_no_successor_task_reactivation(
            task_id, "operator", "trustee", "new operational evidence",
            connection=connection,
        )


def test_lifecycle_schema_indexes_and_append_only_triggers(retirement_db):
    with sqlite3.connect(retirement_db) as connection:
        columns = {
            row[1] for row in connection.execute(
                "PRAGMA table_info(intake_followup_task_lifecycle_events)"
            )
        }
        assert columns == {
            "id", "event_id", "task_id", "intake_id", "firm_id",
            "event_type", "reason_code", "evidence_basis",
            "replacement_task_id", "actor", "actor_capacity", "created_at",
        }
        triggers = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger'"
            )
        }
        assert "prevent_intake_followup_task_lifecycle_events_update" in triggers
        assert "prevent_intake_followup_task_lifecycle_events_delete" in triggers


def test_lifecycle_update_and_delete_are_rejected(retirement_db):
    _retire(retirement_db)
    with sqlite3.connect(retirement_db) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("""
                UPDATE intake_followup_task_lifecycle_events
                SET evidence_basis = 'rewritten'
            """)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "DELETE FROM intake_followup_task_lifecycle_events"
            )


def test_eligible_legacy_active_task(retirement_db):
    decision = _evaluate(retirement_db, 1)
    assert decision["eligible"] is True
    assert decision["reason_codes"] == []


@pytest.mark.parametrize(
    "task_id,reason",
    [
        (2, "task_completed"),
        (3, "task_has_snapshot_version"),
        (4, "task_has_generation_batch"),
        (5, "task_is_reconciled_superseded"),
        (6, "task_is_reconciliation_replacement"),
        (7, "task_materialized_from_governed_proposal"),
        (8, "governed_same_intake_title_lineage_exists"),
        (9, "professional_review_issue_linked"),
    ],
)
def test_ineligible_governance_conditions(retirement_db, task_id, reason):
    decision = _evaluate(retirement_db, task_id)
    assert decision["eligible"] is False
    assert reason in decision["reason_codes"]


def test_missing_required_governance_source_fails_closed(retirement_db):
    with sqlite3.connect(retirement_db) as connection:
        connection.execute("DROP TABLE intake_snapshot_proposed_tasks")
    decision = _evaluate(retirement_db, 1)
    assert decision["eligible"] is False
    assert decision["reason_codes"] == ["missing_required_governance_source"]
    assert "intake_snapshot_proposed_tasks" in decision["evidence"][
        "missing_governance_sources"
    ]


def test_retirement_is_single_append_and_preserves_original_task(retirement_db):
    with sqlite3.connect(retirement_db) as connection:
        before = connection.execute(
            "SELECT * FROM intake_followup_tasks WHERE id = 1"
        ).fetchone()
        task_count_before = connection.execute(
            "SELECT COUNT(*) FROM intake_followup_tasks"
        ).fetchone()[0]
        issue_count_before = connection.execute(
            "SELECT COUNT(*) FROM professional_review_issues"
        ).fetchone()[0]

    first = _retire(retirement_db)
    second = _retire(retirement_db)
    assert first["retired"] is True
    assert first["already_retired"] is False
    assert second == {
        "event_id": first["event_id"],
        "task_id": 1,
        "retired": True,
        "already_retired": True,
    }
    with sqlite3.connect(retirement_db) as connection:
        event = connection.execute("""
            SELECT event_type, reason_code, replacement_task_id
            FROM intake_followup_task_lifecycle_events
        """).fetchone()
        after = connection.execute(
            "SELECT * FROM intake_followup_tasks WHERE id = 1"
        ).fetchone()
        task_count_after = connection.execute(
            "SELECT COUNT(*) FROM intake_followup_tasks"
        ).fetchone()[0]
        issue_count_after = connection.execute(
            "SELECT COUNT(*) FROM professional_review_issues"
        ).fetchone()[0]
    assert event == (
        "no_successor_retired",
        "legacy_unversioned_no_governed_successor",
        None,
    )
    assert after == before
    assert after[5] == "open"
    assert after[12:14] == (None, None)
    assert task_count_after == task_count_before
    assert issue_count_after == issue_count_before


def test_active_projection_and_reconciled_exclusion(retirement_db):
    _retire(retirement_db)
    default_ids = {
        row["id"] for row in intake_service.list_intake_followup_tasks("I1")
    }
    historical_ids = {
        row["id"] for row in intake_service.list_intake_followup_tasks(
            "I1", include_retired=True
        )
    }
    reconciled_history_ids = {
        row["id"] for row in intake_service.list_intake_followup_tasks(
            "I1", include_reconciled=True, include_retired=True
        )
    }
    assert 1 not in default_ids
    assert 1 in historical_ids
    assert 5 not in default_ids
    assert 5 not in historical_ids
    assert 5 in reconciled_history_ids
    assert 11 in default_ids


def test_reactivation_appends_history_and_restores_projection(retirement_db):
    retirement = _retire(retirement_db)
    first = _reactivate(retirement_db)
    second = _reactivate(retirement_db)
    assert first["reactivated"] is True
    assert first["already_active"] is False
    assert second["reactivated"] is False
    assert second["already_active"] is True
    assert second["event_id"] == first["event_id"]
    assert 1 in {
        row["id"] for row in intake_service.list_intake_followup_tasks("I1")
    }
    history = intake_service.list_intake_followup_task_lifecycle_events(
        "I1", task_id=1, firm_id="F1"
    )
    assert [row["event_type"] for row in history] == [
        "no_successor_retired", "reactivated"
    ]
    assert [row["id"] for row in history] == sorted(row["id"] for row in history)
    assert history[0]["event_id"] == retirement["event_id"]
    assert history[0]["replacement_task_id"] is None
    assert history[1]["replacement_task_id"] is None


def test_retirement_requires_nonblank_actor_capacity_and_evidence(retirement_db):
    with sqlite3.connect(retirement_db) as connection:
        for values in (
            ("", "trustee", "evidence"),
            ("operator", " ", "evidence"),
            ("operator", "trustee", None),
        ):
            with pytest.raises(ValueError):
                intake_service.record_no_successor_task_retirement(
                    1, *values, connection=connection
                )
        assert connection.execute(
            "SELECT COUNT(*) FROM intake_followup_task_lifecycle_events"
        ).fetchone()[0] == 0
