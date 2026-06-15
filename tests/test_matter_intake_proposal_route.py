from __future__ import annotations

import ast
from pathlib import Path

from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]

APP = ROOT / "app.py"
TEMPLATE = ROOT / "templates" / "matter_detail.html"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def function_source(name: str) -> str:
    source = read(APP)
    tree = ast.parse(source)

    node = next(
        item
        for item in tree.body
        if (
            isinstance(item, ast.FunctionDef)
            and item.name == name
        )
    )

    segment = ast.get_source_segment(source, node)
    assert segment is not None
    return segment


def test_proposal_route_is_post_only() -> None:
    source = read(APP)

    assert (
        '"/matters/<matter_id>/intake-handoff/propose"'
        in source
    )
    assert 'methods=["POST"]' in source


def test_proposal_route_uses_explicit_application_csrf_gate() -> None:
    source = read(APP)
    route = function_source(
        "propose_matter_intake_bridge"
    )

    route_position = source.index(
        "def propose_matter_intake_bridge"
    )

    decorator_window = source[
        max(0, route_position - 180):
        route_position
    ]

    assert "@csrf.exempt" in decorator_window
    assert "validate_csrf_token()" in route
    assert "Invalid or missing CSRF token." in route

    creation_position = route.index(
        "create_matter_intake_link("
    )

    csrf_position = route.index(
        "validate_csrf_token()"
    )

    assert csrf_position < creation_position


def test_proposal_route_uses_session_scope_and_actor() -> None:
    route = function_source(
        "propose_matter_intake_bridge"
    )

    assert 'session.get("firm_id")' in route
    assert 'session.get("username")' in route
    assert 'session.get("user_id")' in route
    assert "firm_id=firm_id" in route
    assert "created_by=str(actor_id)" in route
    assert 'request.form.get("created_by")' not in route


def test_proposal_route_creates_pending_bridge_only() -> None:
    route = function_source(
        "propose_matter_intake_bridge"
    )

    assert "create_matter_intake_link(" in route
    assert 'link_status="PROPOSED"' in route
    assert 'handoff_status="PENDING"' in route
    assert (
        'recommendation_disposition="PENDING"'
        in route
    )

    assert "review_matter_intake_handoff(" not in route
    assert "add_matter_relationship(" not in route
    assert "update_matter_relationship" not in route


def test_proposal_requires_event_basis() -> None:
    route = function_source(
        "propose_matter_intake_bridge"
    )

    assert "event_basis" in route
    assert "Proposal basis is required." in route


def test_matter_detail_loads_only_same_firm_unlinked_intakes() -> None:
    route = function_source("matter_detail")

    assert "FROM intake_sessions AS i" in route
    assert "i.firm_id = ?" in route
    assert "mil.matter_id = ?" in route
    assert "mil.link_status != 'ENDED'" in route
    assert "mil.bridge_id IS NULL" in route
    assert "eligible_intakes=eligible_intakes" in route


def test_proposal_form_is_csrf_protected() -> None:
    source = read(TEMPLATE)

    assert (
        "MIA-1D-F-G-B3: explicit handoff proposal"
        in source
    )
    assert "propose_matter_intake_bridge" in source
    assert 'name="_csrf_token"' in source
    assert "{{ csrf_token() }}" in source
    assert 'name="intake_id"' in source
    assert 'name="is_primary"' in source
    assert 'name="event_basis"' in source


def test_matter_template_parses() -> None:
    Environment().parse(read(TEMPLATE))
