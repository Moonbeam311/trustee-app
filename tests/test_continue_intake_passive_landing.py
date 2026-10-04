import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
TEMPLATE = ROOT / "templates" / "intake" / "continuation.html"


def _route_source():
    text = APP.read_text(encoding="utf-8")
    tree = ast.parse(text)

    node = next(
        item
        for item in tree.body
        if isinstance(item, ast.FunctionDef)
        and item.name == "intake_resume"
    )

    return text, node, ast.get_source_segment(text, node) or ""


def test_existing_resume_endpoint_is_preserved_as_passive_landing():
    text, node, source = _route_source()

    route_text = "\n".join(
        ast.get_source_segment(text, decorator) or ""
        for decorator in node.decorator_list
    )

    assert "/intake/<intake_id>/resume" in route_text
    assert "resolve_intake_continuation" in source
    assert 'render_template(' in source
    assert '"intake/continuation.html"' in source

    # No automatic redirect into a governed workflow.
    assert "intake_universal_profile" not in source
    assert "intake_saved_snapshot" not in source
    assert "professional_review_issue_registry" not in source
    assert "get_intake_resume_target" not in source


def test_passive_route_has_no_write_or_bootstrap_calls():
    _, _, source = _route_source()

    forbidden = [
        "ensure_",
        "upsert_",
        "save_",
        "sync_",
        "seed_",
        ".commit(",
        "INSERT ",
        "UPDATE ",
        "DELETE ",
        "CREATE TABLE",
        "ALTER TABLE",
    ]

    assert [
        token for token in forbidden
        if token in source
    ] == []


def test_passive_template_displays_governed_state_and_explicit_actions():
    template = TEMPLATE.read_text(encoding="utf-8")

    required = [
        "Current Stage:",
        "Current State:",
        "Open Professional Review Issues:",
        "Blocking Issues:",
        "Open Follow-Up Tasks:",
        "Completed Follow-Up Tasks:",
        "Document Checklist Items:",
        "Drafting Questions:",
        "Earlier Intake Checkpoint:",
        "Open Professional Review Issues",
        "Continue Intake Questions",
        "Review Saved Intake Snapshot",
        "Return to Intake Dashboard",
    ]

    for item in required:
        assert item in template


def test_passive_template_has_no_automatic_navigation_or_mutation_surface():
    template = TEMPLATE.read_text(encoding="utf-8").lower()

    forbidden = [
        "recommended_route",
        "window.location",
        "location.href",
        "http-equiv=\"refresh\"",
        "http-equiv='refresh'",
        "<form",
        "method=\"post\"",
        "method='post'",
    ]

    assert [
        token for token in forbidden
        if token in template
    ] == []
