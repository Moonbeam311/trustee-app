import ast
from pathlib import Path


APP = Path("app.py").read_text(encoding="utf-8")
FORM = Path(
    "templates/genealogy_relationship_review_form.html"
).read_text(encoding="utf-8")
WORKSPACE = Path(
    "templates/genealogy_legacy_workspace.html"
).read_text(encoding="utf-8")


def _route_source():
    tree = ast.parse(APP)
    lines = APP.splitlines()

    for node in tree.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "genealogy_relationship_review"
        ):
            start = min(
                [d.lineno for d in node.decorator_list]
                + [node.lineno]
            )
            return "\n".join(
                lines[start - 1:node.end_lineno]
            )

    raise AssertionError("Review route not found")


def test_review_route_role_and_path():
    source = _route_source()

    assert (
        '"genealogy_relationship_review": '
        '{"Admin", "Trustee"}'
    ) in APP
    assert "<assertion_id>/review" in source
    assert 'methods=["GET", "POST"]' in source


def test_review_route_uses_governed_services():
    source = _route_source()

    for token in (
        "get_genealogy_relationship_assertion",
        "ALLOWED_TRANSITIONS",
        "generate_genealogy_relationship_review_id",
        "transition_genealogy_relationship_status",
    ):
        assert token in source


def test_scope_and_review_id_are_system_supplied():
    source = _route_source()

    assert '"owner_id": owner_id' in source
    assert '"firm_id": firm_id' in source
    assert "generate_genealogy_relationship_review_id()" in source

    for field in (
        'name="review_id"',
        'name="owner_id"',
        'name="firm_id"',
        'name="assertion_id"',
    ):
        assert field not in FORM


def test_form_requires_explicit_human_confirmation():
    assert 'name="human_confirmed"' in FORM
    assert 'value="yes"' in FORM
    assert "I explicitly confirm" in FORM


def test_form_exposes_only_human_decision_origins():
    assert "OPERATOR_OR_FIDUCIARY" in FORM
    assert "PROFESSIONAL" in FORM
    assert "SYSTEM_SUGGESTED" not in FORM


def test_governance_boundaries_are_visible():
    for phrase in (
        "cannot move directly",
        "Review Required",
        "evidence alone never confirms",
        "append-only",
        "genealogical truth",
    ):
        assert phrase in FORM


def test_route_does_not_create_evidence_or_use_p09():
    source = _route_source()

    for token in (
        "create_media_record",
        "INSERT INTO media_records",
        "P09",
        "p09",
    ):
        assert token not in source


def test_workspace_exposes_review_action():
    assert "Review Relationship" in WORKSPACE
    assert "genealogy_relationship_review" in WORKSPACE
