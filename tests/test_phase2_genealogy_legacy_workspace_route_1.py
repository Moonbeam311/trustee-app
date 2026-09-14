from pathlib import Path


APP = Path("app.py")
TEMPLATE = Path(
    "templates/genealogy_legacy_workspace.html"
)


def _app_text():
    return APP.read_text(encoding="utf-8")


def _template_text():
    return TEMPLATE.read_text(encoding="utf-8")


def test_canonical_genealogy_workspace_is_separate_read_only_route():
    text = _app_text()

    assert text.count(
        '@app.route("/genealogy/legacy-workspace")'
    ) == 1

    assert (
        'def genealogy_legacy_workspace():'
        in text
    )

    assert (
        '"genealogy_legacy_workspace": '
        '{"Admin", "Trustee"},'
        in text
    )

    start = text.index(
        '@app.route("/genealogy/legacy-workspace")'
    )

    end = text.index(
        '@app.route(\n'
        '    "/genealogy/legacy-workspace/person/new",',
        start,
    )

    route = text[start:end]

    assert "methods=[\"POST\"]" not in route
    assert "methods=['POST']" not in route

    assert (
        "build_genealogy_legacy_read_model"
        in route
    )

    assert "get_current_owner()" in route
    assert "get_current_firm_id()" in route
    assert "DB_PATH" in route

    assert "create_genealogy_record" not in route
    assert "create_person_identity" not in route
    assert (
        "create_genealogy_relationship_assertion"
        not in route
    )
    assert (
        "transition_genealogy_relationship_status"
        not in route
    )


def test_legacy_genealogy_routes_remain_intact():
    text = _app_text()

    assert text.count(
        '@app.route("/genealogy")'
    ) == 1

    assert text.count(
        '@app.route("/genealogy/new", '
        'methods=["GET", "POST"])'
    ) == 1

    assert (
        "records = get_all_genealogy_records()"
        in text
    )

    assert (
        'render_template("genealogy_dashboard.html"'
        in text
    )


def test_canonical_template_uses_platform_shell_and_read_model():
    text = _template_text()

    assert '{% extends "base.html" %}' in text
    assert (
        '{% include "_platform_nav.html" %}'
        in text
    )

    assert "Genealogy &amp; Legacy" in text
    assert 'model["persons"]' in text
    assert 'model["summary"]' in text
    assert "Source connected" in text
    assert "Governance boundary" in text

    assert "parent_1" not in text
    assert "parent_2" not in text
    assert 'model["spouse"]' not in text
    assert "model[\'spouse\']" not in text
    assert "verification_status" not in text


def test_canonical_workspace_does_not_claim_automatic_truth():
    text = _template_text()

    assert (
        "does not automatically confirm a relationship"
        in text
    )

    assert (
        "not automatically converted"
        in text
    )

    assert (
        "do not establish inheritance, ownership,"
        in text
    )
