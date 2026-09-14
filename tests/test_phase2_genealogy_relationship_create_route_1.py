from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_relationship_create_route_is_registered_for_admin_trustee():
    app = _text("app.py")

    assert (
        '"genealogy_relationship_new": '
        '{"Admin", "Trustee"},'
        in app
    )

    assert (
        '"/genealogy/legacy-workspace/relationship/new",'
        in app
    )

    assert 'def genealogy_relationship_new():' in app


def test_relationship_create_route_uses_current_scope_and_canonical_services():
    app = _text("app.py")

    start = app.index(
        'def genealogy_relationship_new():'
    )
    end = app.index(
        "\n\nTRUST_TYPE_LABELS = {",
        start,
    )
    route = app[start:end]

    required = [
        "get_current_owner()",
        "get_current_firm_id()",
        "list_person_identities",
        "create_genealogy_relationship_assertion",
        "generate_genealogy_relationship_assertion_id",
        '"assertion_id"',
        '"subject_person_id"',
        '"relationship_type"',
        '"related_person_id"',
        '"assertion_basis"',
        '"notes"',
        '"created_by"',
        'url_for("genealogy_legacy_workspace")',
    ]

    for token in required:
        assert token in route

    assert '"owner_id": owner_id' in route
    assert '"firm_id": firm_id' in route


def test_relationship_create_route_keeps_initial_status_governed_by_service():
    app = _text("app.py")

    start = app.index(
        'def genealogy_relationship_new():'
    )
    end = app.index(
        "\n\nTRUST_TYPE_LABELS = {",
        start,
    )
    route = app[start:end]

    assert '"assertion_status"' not in route
    assert "transition_genealogy_relationship_status" not in route
    assert "create_media_record" not in route
    assert "legacy_genealogy_id" not in route
    assert '"trust_id"' not in route


def test_initial_operator_relationship_vocabulary_is_bounded_without_service_enum():
    app = _text("app.py")
    service = _text(
        "services/services_genealogy_relationships.py"
    )

    start = app.index(
        'def genealogy_relationship_new():'
    )
    end = app.index(
        "\n\nTRUST_TYPE_LABELS = {",
        start,
    )
    route = app[start:end]

    assert '"value": "PARENT_OF"' in route
    assert '"value": "CHILD_OF"' in route
    assert (
        "allowed_relationship_types"
        in route
    )

    assert "RELATIONSHIP_TYPES =" not in service
    assert "ALLOWED_RELATIONSHIP_TYPES" not in service


def test_relationship_form_exposes_only_operator_fields():
    template = _text(
        "templates/genealogy_relationship_form.html"
    )

    required = [
        'name="_csrf_token"',
        "wtf_csrf_token()",
        'name="subject_person_id"',
        'name="relationship_type"',
        'name="related_person_id"',
        'name="assertion_basis"',
        'name="notes"',
        "Create Relationship Assertion",
        "Relationship boundary",
        "User Asserted",
    ]

    for token in required:
        assert token in template

    prohibited = [
        'name="assertion_id"',
        'name="owner_id"',
        'name="firm_id"',
        'name="assertion_status"',
        'name="trust_id"',
        'name="legacy_genealogy_id"',
        'name="parent_1"',
        'name="parent_2"',
        'name="spouse"',
    ]

    for token in prohibited:
        assert token not in template


def test_relationship_form_requires_two_existing_people_before_submit():
    template = _text(
        "templates/genealogy_relationship_form.html"
    )

    assert "people|length < 2" in template
    assert "Add another Person" in template
    assert "disabled" in template


def test_workspace_exposes_relationship_create_entry_point():
    template = _text(
        "templates/genealogy_legacy_workspace.html"
    )

    assert (
        "url_for('genealogy_relationship_new')"
        in template
    )
    assert "Add Relationship" in template


def test_relationship_form_states_no_auto_reciprocal_or_auto_confirmation():
    template = _text(
        "templates/genealogy_relationship_form.html"
    ).lower()

    assert "does not automatically" in template
    assert "inverse or reciprocal" in template
    assert "connected evidence does not automatically confirm" in template
