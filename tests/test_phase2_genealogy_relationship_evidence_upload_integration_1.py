import ast
from pathlib import Path


APP = Path("app.py").read_text(encoding="utf-8")
MEDIA_TEMPLATE = Path(
    "templates/media_form.html"
).read_text(encoding="utf-8")
WORKSPACE = Path(
    "templates/genealogy_legacy_workspace.html"
).read_text(encoding="utf-8")


def _function_source(name):
    tree = ast.parse(APP)
    lines = APP.splitlines()

    for node in tree.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == name
        ):
            return "\n".join(
                lines[node.lineno - 1:node.end_lineno]
            )

    raise AssertionError(f"Function not found: {name}")


def test_scoped_genealogy_evidence_launcher_exists():
    assert (
        '"genealogy_relationship_evidence_new": '
        '{"Admin", "Trustee"}'
    ) in APP

    source = _function_source(
        "genealogy_relationship_evidence_new"
    )

    assert (
        "build_genealogy_relationship_media_link"
        in source
    )
    assert 'url_for(\n            "media_upload"' in source
    assert "create_media_record" not in source


def test_existing_media_upload_remains_write_owner():
    source = _function_source("media_upload")

    assert "create_media_record(payload)" in source
    assert (
        "GENEALOGY_RELATIONSHIP_MEDIA_ENTITY_TYPE"
        in source
    )
    assert (
        "build_genealogy_relationship_media_link"
        in source
    )
    assert 'payload["firm_id"]' in source
    assert (
        'url_for("genealogy_legacy_workspace")'
        in source
    )


def test_canonical_genealogy_upload_is_trust_optional_only():
    assert "{% if canonical_genealogy %}" in MEDIA_TEMPLATE

    assert (
        "No trust association required for this canonical"
        in MEDIA_TEMPLATE
    )

    # The legacy/general Media Evidence path stays trust-required.
    assert (
        '<select name="trust_id" required>'
        in MEDIA_TEMPLATE
    )

    # Canonical genealogy does not expose editable entity identity.
    assert 'type="hidden"' in MEDIA_TEMPLATE
    assert 'name="entity_type"' in MEDIA_TEMPLATE
    assert 'name="entity_id"' in MEDIA_TEMPLATE


def test_canonical_genealogy_media_uses_platform_navigation():
    assert "_platform_nav.html" in MEDIA_TEMPLATE
    assert "_nav.html" in MEDIA_TEMPLATE


def test_workspace_exposes_scoped_attach_evidence_action():
    assert "Attach Evidence" in WORKSPACE
    assert (
        "genealogy_relationship_evidence_new"
        in WORKSPACE
    )


def test_evidence_integration_does_not_create_second_store():
    source = _function_source(
        "genealogy_relationship_evidence_new"
    )

    prohibited = (
        "genealogy_media_records",
        "CREATE TABLE",
        "INSERT INTO media_records",
    )

    for token in prohibited:
        assert token not in source
