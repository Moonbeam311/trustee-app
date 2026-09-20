import ast
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"
TEMPLATE_ROOT = ROOT / "templates"
PARTIAL_PATH = TEMPLATE_ROOT / "intake" / "_final_draft_gate_progress.html"
LABELS = [
    "Controlled questionnaire complete",
    "Open issues reviewed / accepted",
    "Open tasks reviewed / accepted",
    "Professional review status recorded",
    "Required documents acknowledged",
    "Admin intentionally approved final-draft preparation",
]
TRUTH_KEYS = [
    "questionnaire_complete",
    "open_issues_reviewed",
    "open_tasks_reviewed",
    "professional_review_recorded",
    "required_documents_acknowledged",
    "admin_approved",
]


def _load_adapter():
    tree = ast.parse(APP_PATH.read_text(encoding="utf-8"))
    selected = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name)
            and target.id == "FINAL_DRAFT_GATE_PROGRESS_CONDITIONS"
            for target in node.targets
        ):
            selected.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name == "build_final_draft_gate_progress":
            selected.append(node)
    namespace = {}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(APP_PATH), "exec"), namespace)
    return namespace["build_final_draft_gate_progress"]


def _gate(completed=(), gate_status="blocked"):
    gate = {key: key in completed for key in TRUTH_KEYS}
    gate["gate_status"] = gate_status
    return gate


def _render(progress):
    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_ROOT),
        autoescape=select_autoescape(("html",)),
    )
    return environment.get_template("intake/_final_draft_gate_progress.html").render(
        final_draft_gate_progress=progress
    )


def test_zero_of_six_derives_and_renders_pending_states():
    progress = _load_adapter()(_gate())
    rendered = _render(progress)
    assert progress["complete_count"] == 0
    assert "0 of 6 gate conditions complete" in rendered
    assert rendered.count("Pending</span>") == 6


def test_mixed_completion_derives_and_shows_complete_and_pending():
    progress = _load_adapter()(_gate(TRUTH_KEYS[:3]))
    rendered = _render(progress)
    assert progress["complete_count"] == 3
    assert "3 of 6 gate conditions complete" in rendered
    assert "Complete</span>" in rendered
    assert "Pending</span>" in rendered


def test_six_of_six_derives_without_automatic_approval():
    adapter = _load_adapter()
    ready = adapter(_gate(TRUTH_KEYS, "ready_for_admin_approval"))
    approved = adapter(_gate(TRUTH_KEYS, "approved_for_final_draft_preparation"))
    assert ready["complete_count"] == approved["complete_count"] == 6
    assert ready["approved"] is False
    assert "6 of 6 gate conditions complete" in _render(ready)
    assert approved["approved"] is True
    assert "6 of 6 — Approved for Final-Draft Preparation" in _render(approved)


def test_locked_labels_appear_in_locked_order():
    rendered = _render(_load_adapter()(_gate()))
    positions = [rendered.index(label) for label in LABELS]
    assert positions == sorted(positions)


def test_all_three_existing_surfaces_include_the_shared_component():
    surfaces = [
        "final_draft_prep_gate.html",
        "final_draft_gate_resolution.html",
        "final_draft_admin_approval.html",
    ]
    include = '{% include "intake/_final_draft_gate_progress.html" %}'
    for surface in surfaces:
        assert include in (TEMPLATE_ROOT / "intake" / surface).read_text(encoding="utf-8")


def test_component_preserves_status_boundary_and_authoritative_truth_contract():
    partial = PARTIAL_PATH.read_text(encoding="utf-8")
    app_source = APP_PATH.read_text(encoding="utf-8")
    assert "Preparation only — does not authorize signing, filing, execution, transfer, or final legal use." in partial
    assert "gate_status" in partial or "gate_status" in app_source
    assert "CREATE TABLE" not in partial
    assert "INSERT INTO" not in partial
    assert "UPDATE " not in partial
    for key in TRUTH_KEYS:
        assert key in app_source
    assert "build_final_draft_gate_progress(context[\"gate\"])" in app_source
    assert "build_final_draft_gate_progress(gate)" in app_source
