from pathlib import Path

from services.services_intake_correction_versioning_adapter import (
    build_governed_proposed_tasks,
)


ROOT = Path(__file__).resolve().parents[1]


def _text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def _route(source, function_name, next_function_name):
    start = source.index(f"def {function_name}")
    end = source.index(f"def {next_function_name}", start)
    return source[start:end]


def test_gate_and_governed_route_source_contracts():
    app = _text("app.py")
    assert 'os.getenv("HINDSFOOT_INTAKE_VERSIONING_1E_ENABLED") == "1"' in app

    post = _route(app, "intake_universal_profile", "asset_intake")
    assert "if HINDSFOOT_INTAKE_VERSIONING_1E_ENABLED:" in post
    assert "else:\n            auto_generate_followup_tasks_from_snapshot(" in post
    assert post.index("create_answer_revision(") < post.index("create_snapshot_version(")
    assert "confirm_snapshot(" not in post

    saved = _route(app, "intake_saved_snapshot", "intake_confirm_snapshot")
    enabled = saved.split("else:", 1)[0]
    assert "auto_generate_followup_tasks_from_snapshot(" not in enabled
    assert "create_answer_revision(" not in saved
    assert "create_snapshot_version(" not in saved
    assert "confirm_snapshot(" not in saved

    confirm = _route(app, "intake_confirm_snapshot", "intake_resume")
    assert "current_snapshot.get(\"snapshot_version_id\") != submitted_snapshot_id" in confirm
    assert "confirmation_allowed" in confirm
    assert "confirm_snapshot(" in confirm
    assert 'request.form.get("firm_id")' not in confirm
    assert 'request.form.get("confirmed_by")' not in confirm


def test_correction_and_template_source_contracts():
    snapshot = _text("templates/intake/client_snapshot.html")
    profile = _text("templates/intake/universal_profile.html")
    for label in (
        "Awaiting Confirmation",
        "Confirm These Answers",
        "Review or Correct My Answers",
        "Proposed Follow-Up",
    ):
        assert label in snapshot
    assert "correction=1" in snapshot
    assert "same Intake ID" in profile
    assert "new revision" in profile
    assert "Previous confirmed history remains preserved" in profile
    assert "again require confirmation" in profile


def test_adapter_mirrors_legacy_semantics_without_database_access(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("adapter must not open a database")

    monkeypatch.setattr("sqlite3.connect", forbidden)
    tasks = build_governed_proposed_tasks({
        "documents_to_gather": ["Current deed"],
        "review_flags": ["Ownership issue", "Tax review", "Legal review"],
        "recommended_next_session": "Asset review",
        "review_priority": "Elevated",
    })
    by_title = {task["title"]: task for task in tasks}
    assert by_title["Gather document: Current deed"] == {
        "task_type": "document",
        "priority": "normal",
        "title": "Gather document: Current deed",
        "description": "Client or staff should gather this item before the deeper review session.",
        "source": "auto_snapshot",
        "operational_status": "pending_client",
    }
    assert by_title["Review flag: Ownership issue"]["operational_status"] == "pending_staff"
    assert by_title["Review flag: Ownership issue"]["task_type"] == "staff_action"
    assert by_title["Review flag: Tax review"]["operational_status"] == "pending_professional"
    assert by_title["Review flag: Legal review"]["operational_status"] == "pending_professional"
    assert by_title["Prepare next session: Asset review"]["operational_status"] == "pending_staff"
    assert by_title["Prepare next session: Asset review"]["priority"] == "high"
