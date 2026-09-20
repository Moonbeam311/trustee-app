from pathlib import Path

import pytest

import database.db as db
import services.services_intake as intake


INTAKE_ID = "INT-XCONTRACT"
WORKFLOW_KEY = "estate_plan"
DOCUMENT_KEY = "draft"


def _document(*, issues=0, tasks=0, documents=0):
    return {
        "missing_answers": [],
        "preview": {
            "draft_packet": {
                "open_issues": [{} for _ in range(issues)],
                "open_tasks": [{} for _ in range(tasks)],
                "documents": [{} for _ in range(documents)],
            }
        },
    }


def _configure(monkeypatch, *, total, blocking, issues=0, tasks=0, documents=0,
               review_actions=(), resolution_actions=()):
    monkeypatch.setattr(
        intake,
        "build_nonfinal_draft_document",
        lambda *_: _document(issues=issues, tasks=tasks, documents=documents),
    )
    monkeypatch.setattr(
        intake,
        "get_review_gate_record",
        lambda *_: {"gate_status": "professional_review_required"},
    )
    monkeypatch.setattr(
        intake,
        "list_review_gate_actions",
        lambda *_: [{"action_key": key} for key in review_actions],
    )
    monkeypatch.setattr(intake, "get_current_firm_id", lambda: "FIRM-TEST")
    monkeypatch.setattr(
        db,
        "get_professional_review_issue_summary",
        lambda intake_id, firm_id=None: {
            "total": total,
            "blocking": blocking,
        },
    )
    monkeypatch.setattr(
        intake,
        "_final_draft_resolution_action_keys",
        lambda *_: set(resolution_actions),
    )


def _evaluate(monkeypatch, **conditions):
    _configure(monkeypatch, **conditions)
    return intake.evaluate_final_draft_prep_gate_with_resolutions(
        INTAKE_ID, WORKFLOW_KEY, DOCUMENT_KEY
    )


def test_authoritative_blocking_count_keeps_issue_condition_false(monkeypatch):
    gate = _evaluate(monkeypatch, total=1, blocking=1)
    assert gate["open_issues_reviewed"] == 0
    assert gate["gate_status"] == "blocked"


@pytest.mark.parametrize(
    "review_action",
    ["open_issues_reviewed", "approved_for_final_draft_prep"],
)
def test_review_gate_actions_cannot_override_professional_review_blockers(
    monkeypatch, review_action
):
    gate = _evaluate(
        monkeypatch,
        total=1,
        blocking=1,
        review_actions=(review_action,),
    )
    assert gate["open_issues_reviewed"] == 0


def test_final_draft_issue_acknowledgment_cannot_override_blockers(monkeypatch):
    gate = _evaluate(
        monkeypatch,
        total=1,
        blocking=1,
        resolution_actions=("open_issues_reviewed",),
    )
    assert gate["open_issues_reviewed"] == 0


def test_issue_review_action_cannot_satisfy_tasks_or_documents(monkeypatch):
    gate = _evaluate(
        monkeypatch,
        total=1,
        blocking=0,
        tasks=1,
        documents=1,
        review_actions=("open_issues_reviewed",),
        resolution_actions=("open_issues_reviewed",),
    )
    assert gate["open_tasks_reviewed"] == 0
    assert gate["required_documents_acknowledged"] == 0


def test_task_resolution_affects_only_task_condition(monkeypatch):
    gate = _evaluate(
        monkeypatch,
        total=1,
        blocking=1,
        tasks=1,
        documents=1,
        resolution_actions=("open_tasks_reviewed",),
    )
    assert gate["open_tasks_reviewed"] == 1
    assert gate["open_issues_reviewed"] == 0
    assert gate["required_documents_acknowledged"] == 0


def test_document_resolution_affects_only_document_condition(monkeypatch):
    gate = _evaluate(
        monkeypatch,
        total=1,
        blocking=1,
        tasks=1,
        documents=1,
        resolution_actions=("required_documents_acknowledged",),
    )
    assert gate["required_documents_acknowledged"] == 1
    assert gate["open_issues_reviewed"] == 0
    assert gate["open_tasks_reviewed"] == 0


def test_populated_registry_without_blockers_clears_issue_condition(monkeypatch):
    gate = _evaluate(monkeypatch, total=3, blocking=0, issues=2)
    assert gate["open_issues_reviewed"] == 1


def test_empty_registry_with_underlying_open_issues_stays_blocked(monkeypatch):
    gate = _evaluate(monkeypatch, total=0, blocking=0, issues=1)
    assert gate["open_issues_reviewed"] == 0


def test_empty_registry_without_underlying_open_issues_may_clear(monkeypatch):
    gate = _evaluate(monkeypatch, total=0, blocking=0, issues=0)
    assert gate["open_issues_reviewed"] == 1


def test_escalated_major_or_critical_summary_remains_blocking(monkeypatch):
    gate = _evaluate(monkeypatch, total=2, blocking=1)
    assert gate["open_issues_reviewed"] == 0
    assert gate["gate_status"] == "blocked"


def test_admin_approval_freshly_rechecks_and_refuses_blocked_gate(monkeypatch):
    calls = []
    monkeypatch.setattr(intake, "ensure_final_draft_admin_approval_tables", lambda: None)
    monkeypatch.setattr(
        intake,
        "upsert_final_draft_prep_gate_with_resolutions",
        lambda **kwargs: calls.append(kwargs) or {
            "gate_status": "blocked",
            "open_issues_reviewed": 0,
        },
    )
    monkeypatch.setattr(
        intake,
        "get_connection",
        lambda: pytest.fail("blocked approval must not open a write connection"),
    )

    with pytest.raises(ValueError, match="Gate is blocked"):
        intake.record_final_draft_admin_approval(
            INTAKE_ID,
            WORKFLOW_KEY,
            DOCUMENT_KEY,
            "approval must be rejected",
            approved_by="admin",
        )

    assert len(calls) == 1


def test_repair_uses_existing_summary_without_new_persistence_authority():
    source = Path(intake.__file__).read_text(encoding="utf-8")
    evaluator = source.split("def evaluate_final_draft_prep_gate(", 1)[1].split(
        "def upsert_final_draft_prep_gate(", 1
    )[0]
    assert "get_professional_review_issue_summary" in evaluator
    assert "CREATE TABLE" not in evaluator
    assert "INSERT INTO" not in evaluator
    assert "UPDATE " not in evaluator
