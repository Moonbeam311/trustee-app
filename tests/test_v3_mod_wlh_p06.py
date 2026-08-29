"""V3-MOD-WLH-P06 bounded adapter, route, and presentation contracts."""

import json
from pathlib import Path

import pytest

import services.services_work_learning_program_handoff as p06


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
DETAIL = (ROOT / "templates/workspace_program_detail.html").read_text(encoding="utf-8")
HANDOFF = (ROOT / "templates/workspace_program_handoff.html").read_text(encoding="utf-8")
ADAPTER = (ROOT / "services/services_work_learning_program_handoff.py").read_text(encoding="utf-8")


def _snapshot(program_id="PRG-1", workspace_id="WS-1", firm_id="FIRM-1", owner_id="OWNER-1"):
    return {
        "program": {"program_id": program_id, "workspace_id": workspace_id,
                    "firm_id": firm_id, "owner_id": owner_id, "title": "Plan",
                    "purpose": "Working purpose", "status": "draft"},
        "goals": [], "alternatives": [], "scenarios": [],
        "issues": [{"issue_id": "ISS-1", "issue_type": "gap",
                    "statement": "Working gap", "evidence_state": "unresolved",
                    "status": "open"}],
        "source_references": [{"source_reference_id": "SRC-1",
                               "source_type": "document_reference",
                               "source_reference": "DOC-1"}],
    }


def _install(monkeypatch, *, snapshot=None, revisions=None, package=None):
    snapshot = snapshot or _snapshot()
    program = snapshot["program"]
    monkeypatch.setattr(
        p06,
        "get_hub_program",
        lambda **kw: dict(program) if (
            kw["program_id"] == program["program_id"]
            and kw["firm_id"] == program["firm_id"]
            and kw["owner_id"] == program["owner_id"]
        ) else None,
    )
    monkeypatch.setattr(p06, "build_program_snapshot", lambda **kw: snapshot)
    monkeypatch.setattr(p06, "get_program_revisions", lambda **kw: revisions or [])
    monkeypatch.setattr(
        p06, "build_successor_handoff_package_descriptor",
        lambda trust_id, **kw: package or {
            "root_trust_id": trust_id, "readiness": {"status": "OPEN"},
            "content_index": [], "mutation_performed": False,
        },
    )


def _build(**overrides):
    values = dict(
        program_id="PRG-1", workspace_id="WS-1", firm_id="FIRM-1",
        owner_id="OWNER-1", state_mode=p06.CURRENT, trust_id="TRUST-1",
        db_path=Path("unused.sqlite"), trust_authorization_check=lambda _id: True,
        continuity_authorization_check=lambda _id: True,
        fiduciary_authorization_check=lambda _id, _trust: True,
        governance_authorization_check=lambda _id: True,
        acceptance_authorization_check=lambda _id, _trust: True,
    )
    values.update(overrides)
    return p06.build_work_learning_program_handoff_descriptor(**values)


def test_exact_two_modes_and_current_descriptor(monkeypatch):
    _install(monkeypatch)
    assert p06.PROGRAM_STATE_MODES == ("CURRENT", "SAVED_REVISION")
    descriptor = _build()
    assert descriptor["state_mode"] == "CURRENT"
    assert descriptor["program_id"] == "PRG-1"
    assert descriptor["workspace_id"] == "WS-1"
    assert descriptor["firm_id"] == "FIRM-1"
    assert descriptor["owner_id"] == "OWNER-1"
    assert descriptor["revision_id"] is None
    assert descriptor["program_snapshot"] == _snapshot()


def test_saved_revision_descriptor_preserves_p04_and_p05(monkeypatch):
    saved = _snapshot()
    revision = {"revision_id": "REV-1", "program_id": "PRG-1",
                "revision_number": 4, "snapshot_json": json.dumps(saved)}
    _install(monkeypatch, revisions=[revision])
    descriptor = _build(state_mode="SAVED_REVISION", revision_id="REV-1")
    assert descriptor["revision_id"] == "REV-1"
    assert descriptor["revision_number"] == 4
    assert descriptor["p04_issues"] == saved["issues"]
    assert descriptor["p05_source_references"] == saved["source_references"]
    assert descriptor["provenance_boundaries"]["p05_source_references"].endswith("not verification")


@pytest.mark.parametrize("change", [
    {"program_id": "PRG-X"}, {"workspace_id": "WS-X"},
    {"firm_id": "FIRM-X"}, {"owner_id": "OWNER-X"},
])
def test_saved_revision_scope_mismatch_fails_closed(monkeypatch, change):
    saved = _snapshot(**change)
    revision = {"revision_id": "REV-X", "program_id": "PRG-1",
                "revision_number": 1, "snapshot_json": json.dumps(saved)}
    _install(monkeypatch, revisions=[revision])
    with pytest.raises(p06.WorkLearningProgramHandoffError):
        _build(state_mode="SAVED_REVISION", revision_id="REV-X")


def test_wrong_revision_or_mode_fails_closed(monkeypatch):
    _install(monkeypatch)
    with pytest.raises(p06.WorkLearningProgramHandoffError):
        _build(state_mode="SAVED_REVISION", revision_id="REV-OTHER")
    with pytest.raises(p06.WorkLearningProgramHandoffError):
        _build(state_mode="OTHER")


def test_program_scope_checks_wrong_firm_owner_workspace(monkeypatch):
    _install(monkeypatch)
    for key, value in (("firm_id", "FIRM-X"), ("owner_id", "OWNER-X"),
                       ("workspace_id", "WS-X"), ("program_id", "PRG-X")):
        with pytest.raises(p06.WorkLearningProgramHandoffError):
            _build(**{key: value})


def test_canonical_handoff_authorization_is_independent(monkeypatch):
    _install(monkeypatch)
    seen = {}
    def canonical(trust_id, **kwargs):
        seen.update(kwargs)
        return None if not kwargs["trust_authorization_check"](trust_id) else {"ok": True}
    monkeypatch.setattr(p06, "build_successor_handoff_package_descriptor", canonical)
    with pytest.raises(p06.WorkLearningProgramHandoffError):
        _build(trust_authorization_check=lambda _id: False)
    assert "continuity_authorization_check" in seen
    assert "fiduciary_authorization_check" in seen
    assert "governance_authorization_check" in seen
    assert "acceptance_authorization_check" in seen


def test_canonical_package_is_ephemeral_reference_and_all_effects_false(monkeypatch):
    package = {"root_trust_id": "TRUST-1", "mutation_performed": False,
               "generation": {"package_record_created": False}}
    _install(monkeypatch, package=package)
    descriptor = _build()
    assert descriptor["canonical_handoff_package_descriptor"] is package
    assert descriptor["ephemeral"] is True
    assert descriptor["mutation_performed"] is False
    assert descriptor["classification"]["handoff_material"] == "CANONICAL_REFERENCE"
    assert descriptor["classification"]["institutional_record"] is False
    assert descriptor["institutional_effects"]
    assert all(value is False for value in descriptor["institutional_effects"].values())


def test_no_revision_or_lifecycle_mutation_calls_exist():
    assert "create_program_revision" not in ADAPTER
    assert "successor_acceptance_lifecycle" not in ADAPTER
    assert "transition_activation_plan" not in ADAPTER
    assert "acknowledge_handoff" not in ADAPTER
    assert "INSERT " not in ADAPTER and "UPDATE " not in ADAPTER


def test_secret_material_is_rejected(monkeypatch):
    secret = _snapshot()
    secret["program"]["password"] = "do-not-store-this"
    _install(monkeypatch, snapshot=secret)
    with pytest.raises(Exception, match="Secret fields are prohibited"):
        _build()


def test_routes_roles_csrf_and_browser_scope_are_bounded():
    assert '"workspace_program_handoff_prepare": {"Admin", "Trustee"}' in APP
    assert '"workspace_program_handoff": {"Admin", "Trustee", "Viewer"}' in APP
    prepare = APP[APP.index("def workspace_program_handoff_prepare"):APP.index("def workspace_program_handoff(")]
    assert "validate_csrf_token()" in prepare
    assert 'request.form.get("firm_id")' not in prepare
    assert 'request.form.get("owner_id")' not in prepare
    assert "_workspace_program_context" in prepare
    assert 'methods=["POST"]' in APP[APP.rfind("@app.route(", 0, APP.index("def workspace_program_handoff_prepare")):APP.index("def workspace_program_handoff_prepare")]


def test_route_uses_separate_trust_authorization_and_no_mutation():
    route = APP[APP.index("def workspace_program_handoff(workspace_id"):APP.index("@app.route(\"/workspaces/<workspace_id>/edit")]
    assert "operator_can_access_trust" in route
    assert "get_trust_by_id" in route
    assert "trust_authorization_check=trust_check" in route
    assert "continuity_authorization_check=" in route
    assert "create_program_revision" not in route
    assert "successor_acceptance" not in route.lower()


def test_program_detail_boundary_navigation_and_p05_csrf_contract():
    for phrase in ("remain working material", "does not govern or promote",
                   "attribution, not verification", "does not activate Continuity",
                   "Successor Acceptance", "acknowledge a handoff",
                   "governed package or archive record"):
        assert phrase in DETAIL
    navigation = DETAIL.index("'workspace_program_handoff'")
    guard = DETAIL.rfind("{% if session.get('role') in ['Admin', 'Trustee'] %}", 0, navigation)
    assert guard >= 0
    assert "'workspace_program_handoff_prepare'" not in DETAIL
    assert DETAIL.count('value="{{ wtf_csrf_token() }}"') == 7
    assert "Viewer access is read-only" in DETAIL


def test_handoff_preparation_form_is_role_bounded_and_csrf_signed():
    form_start = HANDOFF.index('<form method="post" action="{{ url_for(\n        \'workspace_program_handoff_prepare\'')
    guard = HANDOFF.rfind("{% if session.get('role') in ['Admin', 'Trustee'] %}", 0, form_start)
    assert guard >= 0
    form = HANDOFF[form_start:HANDOFF.index("</form>", form_start)]
    assert 'value="{{ wtf_csrf_token() }}"' in form
    assert 'name="trust_id"' in form
    assert 'name="state_mode"' in form
    assert 'name="revision_id"' in form
    viewer_branch = HANDOFF[HANDOFF.index("{% else %}", form_start):HANDOFF.index("{% endif %}", form_start)]
    assert "Viewer access is read-only" in viewer_branch
    assert "<form" not in viewer_branch


def test_handoff_route_supports_safe_unselected_state():
    route = APP[APP.index("def workspace_program_handoff(workspace_id"):APP.index("@app.route(\"/workspaces/<workspace_id>/edit")]
    assert "selection_supplied = bool(trust_id or state_mode or revision_id)" in route
    assert "descriptor = None" in route
    assert "if selection_supplied:" in route
    assert "handoff_trusts=" in route
    assert "revisions=get_program_revisions(" in route
    assert "{% if handoff %}" in HANDOFF
    assert "No Handoff Context Selected" in HANDOFF


def test_handoff_template_contains_identity_context_and_boundaries():
    for phrase in ("Program Handoff Context", "Workspace:", "State mode:",
                   "Working Program Content Summary", "P04 Working Issue Context",
                   "P05 Source / Reference Attribution", "Canonical Successor Handoff",
                   "ephemeral", "not a governed institutional record",
                   "Source attribution is not verification",
                   "Successor Acceptance is not created or changed",
                   "Continuity is not activated", "Responsibility is not assigned",
                   "Execution is not advanced", "Application access is not changed",
                   "Handoff is not acknowledged", "No archive or package record is created",
                   "No P07 promotion occurs"):
        assert phrase in HANDOFF
    assert "Open canonical Trust Handoff workspace" in HANDOFF
    assert "mutation" not in HANDOFF.lower() or "no canonical mutation buttons" in HANDOFF.lower()


def test_p07_p08_document_demo_and_canonical_ownership_remain_absent():
    product = ADAPTER + APP[APP.index("def workspace_program_handoff_prepare"):APP.index("@app.route(\"/workspaces/<workspace_id>/edit")]
    for forbidden in ("P08", "HOS-DOC-1", "HOS-DEMO-1"):
        assert forbidden not in product
    assert "services_handoff_package_adapter" in ADAPTER
    assert "routes_tpd1c.py" not in ADAPTER
    assert "templates/tpd1c/successor_handoff.html" not in ADAPTER
