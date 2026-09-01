from pathlib import Path


SERVICE = Path("services/services_work_learning_provenance.py")
APP = Path("app.py")
TEMPLATE = Path("templates/workspace_program_provenance.html")
DETAIL = Path("templates/workspace_program_detail.html")


def text(path):
    return path.read_text(encoding="utf-8")


def test_p08_exact_product_surface_exists():
    assert SERVICE.is_file()
    assert TEMPLATE.is_file()
    assert APP.is_file()
    assert DETAIL.is_file()


def test_p08_is_explicitly_derived_read_only_model():
    source = text(SERVICE)
    assert "DERIVED_UNIFIED_READ_MODEL" in source
    assert '"read_only": True' in source
    assert "new_persistence" in source
    assert "new_migration" in source
    assert "new_permission" in source
    assert "new_fiduciary_authority" in source


def test_p08_reuses_p06_and_p07_canonical_read_surfaces():
    source = text(SERVICE)
    assert "build_work_learning_program_handoff_descriptor" in source
    assert "list_program_promotion_state" in source
    assert "governed_program_promotion_events" not in source
    # P08 may explicitly name generic audit_log only to deny it domain-truth
    # status. What is prohibited is querying or joining that table as a
    # canonical provenance source.
    assert "FROM audit_log" not in source
    assert "JOIN audit_log" not in source
    assert "from audit_log" not in source
    assert "join audit_log" not in source
    assert '"generic_audit_log_as_domain_truth": False' in source


def test_p08_does_not_own_writes_or_schema():
    source = text(SERVICE).lower()
    prohibited = (
        "insert into",
        "update governed_",
        "delete from",
        "create table",
        "alter table",
        "drop table",
        "commit()",
    )
    for token in prohibited:
        assert token not in source


def test_p08_uses_caller_supplied_db_path():
    source = text(SERVICE)
    app = text(APP)
    assert "db_path" in source
    assert "db_path=DB_PATH" in app
    assert "data/trustee_app.db" not in source
    assert "trustee_app.db" not in source


def test_p08_route_is_get_only():
    app = text(APP)
    marker = (
        '@app.route("/workspaces/<workspace_id>/programs/'
        '<program_id>/provenance")'
    )
    assert marker in app
    assert (
        '@app.route("/workspaces/<workspace_id>/programs/'
        '<program_id>/provenance", methods='
    ) not in app


def test_p08_role_contract_is_existing_read_roles_only():
    app = text(APP)
    assert (
        '"workspace_program_provenance": '
        '{"Admin", "Trustee", "Viewer"}'
    ) in app


def test_p08_has_no_mutation_controls():
    template = text(TEMPLATE)
    lowered = template.lower()

    # Structural mutation controls are prohibited. Explanatory language may
    # say that P08 does not approve/reject/execute anything.
    assert "<form" not in lowered
    assert 'method="post"' not in lowered
    assert "method='post'" not in lowered

    prohibited_endpoints = (
        "workspace_program_promotion_request",
        "workspace_program_promotion_approve",
        "workspace_program_promotion_reject",
        "workspace_program_promotion_execute",
        "workspace_program_issue_add",
        "workspace_program_issue_update",
        "workspace_program_source_reference_add",
        "workspace_program_revision_create",
        "workspace_program_handoff_prepare",
    )
    for endpoint in prohibited_endpoints:
        assert endpoint not in template

    # Required negative semantics remain visible rather than being removed
    # merely to satisfy a lexical test.
    assert "attribution is not verification" in lowered
    assert (
        "does not" in lowered
        or "no " in lowered
    )


def test_p08_preserves_attribution_not_verification():
    source = text(SERVICE)
    template = text(TEMPLATE)
    assert "ATTRIBUTION_NOT_VERIFICATION" in source
    assert "Source attribution is not" in template


def test_p08_does_not_fabricate_missing_timestamps():
    source = text(SERVICE)
    assert '"occurred_at": _text(occurred_at) or None' in source
    assert "datetime.now" not in source
    assert "datetime.utcnow" not in source


def test_p08_preserves_cross_firm_fail_closed_scope():
    source = text(SERVICE)
    assert '"firm_id": firm' in source
    assert '"owner_id": owner' in source
    assert 'event.get("firm_id")' in source
    assert 'event.get("owner_id")' in source
    assert "provenance_context_not_available" in source


def test_p08_does_not_claim_legal_or_institutional_effect():
    source = text(SERVICE)
    template = text(TEMPLATE)
    assert '"legal_validity_inferred": False' in source
    assert '"handoff_acknowledgement_created": False' in source
    assert '"continuity_activated": False' in source
    assert '"acceptance_created": False' in source
    assert "No Institutional Effect" in template


def test_p08_program_detail_change_is_non_mutating_context_only():
    detail = text(DETAIL)
    app = text(APP)
    heading = "P08 Unified Program Provenance / Audit History"
    start = detail.index(heading)
    end = detail.index('{% include "_institutional_property_notice.html" %}', start)
    navigation = detail[start:end]

    assert heading in detail
    assert "workspace_program_provenance" in navigation
    assert "trust_id=trust['trust_id']" in navigation
    assert "revision_id=revision['revision_id']" in navigation
    assert "revisions" in navigation
    assert "visible_trusts" in navigation
    assert "<form" not in navigation.lower()
    assert 'method="post"' not in navigation.lower()
    assert "Source attribution is not verification." in navigation
    assert "Viewer" not in navigation or "read-only" in navigation

    prohibited_endpoints = (
        "workspace_program_handoff_prepare",
        "workspace_program_promotion_request",
        "workspace_program_promotion_approve",
        "workspace_program_promotion_reject",
        "workspace_program_promotion_execute",
    )
    for endpoint in prohibited_endpoints:
        assert endpoint not in navigation

    route_start = app.index("def workspace_program_detail(")
    route_end = app.index(
        '@app.route(\n    "/workspaces/<workspace_id>/programs/<program_id>/edit"',
        route_start,
    )
    route = app[route_start:route_end]
    assert "visible_trusts=get_visible_trusts_for_current_operator()" in route


def test_p08_program_detail_navigation_preserves_p06_p07_ownership():
    detail = text(DETAIL)
    start = detail.index("P08 Unified Program Provenance / Audit History")
    end = detail.index('{% include "_institutional_property_notice.html" %}', start)
    navigation = detail[start:end].lower()
    normalized = " ".join(navigation.split())

    assert "derived, read-only, source-native" in navigation
    assert "does not create or modify p06 preparation" in normalized
    assert "p07 promotion" in normalized
    assert "institutional record" in normalized
    assert "navigation context only" in normalized


def test_p08_route_uses_existing_p07_actor_scope():
    app = text(APP)
    start = app.index("def workspace_program_provenance(")
    end = app.index(
        '@app.route("/workspaces/<workspace_id>/programs/'
        '<program_id>/promotion")',
        start,
    )
    block = app[start:end]
    assert "_p07_actor_context(workspace_id, program_id)" in block
    assert "session.clear" not in block
    assert "session[" not in block
