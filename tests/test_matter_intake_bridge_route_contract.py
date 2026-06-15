from __future__ import annotations

import ast
from pathlib import Path

from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]

APP = ROOT / "app.py"
DETAIL_TEMPLATE = (
    ROOT
    / "templates"
    / "matter_intake_bridge_detail.html"
)
MATTER_TEMPLATE = ROOT / "templates" / "matter_detail.html"
INTAKE_TEMPLATE = (
    ROOT
    / "templates"
    / "intake"
    / "client_snapshot.html"
)


def read(path: Path) -> str:
    return path.read_text(
        encoding="utf-8",
    )


def get_route_source() -> str:
    source = read(APP)
    tree = ast.parse(source)

    function = next(
        node
        for node in tree.body
        if (
            isinstance(node, ast.FunctionDef)
            and node.name
            == "matter_intake_bridge_detail"
        )
    )

    segment = ast.get_source_segment(
        source,
        function,
    )

    assert segment is not None
    return segment


def test_bridge_route_is_firm_scoped() -> None:
    route = get_route_source()

    assert 'session.get("firm_id")' in route
    assert "get_matter_intake_link(" in route
    assert "firm_id=firm_id" in route
    assert "list_link_events(" in route


def test_bridge_route_uses_atomic_review_only() -> None:
    route = get_route_source()

    assert "review_matter_intake_handoff(" in route
    assert "update_handoff(" not in route
    assert "create_matter_intake_link(" not in route
    assert "add_matter_relationship(" not in route
    assert "intake_workflow_bridge(" not in route


def test_bridge_route_requires_explicit_decision_basis() -> None:
    route = get_route_source()

    assert '"ACCEPTED"' in route
    assert '"MODIFIED"' in route
    assert '"REJECTED"' in route
    assert "event_basis" in route
    assert "Decision basis is required." in route


def test_bridge_route_actor_comes_from_session() -> None:
    route = get_route_source()

    assert 'session.get("username")' in route
    assert 'session.get("user_id")' in route
    assert 'request.form.get("actor' not in route


def test_bridge_template_contains_review_and_history() -> None:
    source = read(DETAIL_TEMPLATE)

    assert "Matter–Intake Handoff Review" in source
    assert "Record Handoff Decision" in source
    assert "Immutable Bridge History" in source
    assert 'name="handoff_status"' in source
    assert 'name="event_basis"' in source
    assert 'name="csrf_token"' in source
    assert "{{ csrf_token() }}" in source
    assert "event.event_id" in source
    assert "event.event_type" in source


def test_existing_panels_link_to_bridge_detail() -> None:
    matter_source = read(MATTER_TEMPLATE)
    intake_source = read(INTAKE_TEMPLATE)

    assert "matter_intake_bridge_detail" in matter_source
    assert "matter_intake_bridge_detail" in intake_source
    assert "Review Handoff" in matter_source
    assert "Review Handoff" in intake_source


def test_templates_parse_as_jinja() -> None:
    environment = Environment()

    environment.parse(
        read(DETAIL_TEMPLATE)
    )

    environment.parse(
        read(MATTER_TEMPLATE)
    )

    environment.parse(
        read(INTAKE_TEMPLATE)
    )
