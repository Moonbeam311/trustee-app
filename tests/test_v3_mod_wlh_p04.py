import json
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

APP = (ROOT / "app.py").read_text(encoding="utf-8")
SERVICE_PATH = (
    ROOT / "services" / "services_work_learning_programs.py"
)
SERVICE = SERVICE_PATH.read_text(encoding="utf-8")
TEMPLATE = (
    ROOT / "templates" / "workspace_program_detail.html"
).read_text(encoding="utf-8")


def _function_source(text, name):
    marker = f"def {name}("
    start = text.index(marker)
    next_def = text.find("\ndef ", start + len(marker))
    if next_def == -1:
        return text[start:]
    return text[start:next_def]


@pytest.fixture()
def isolated_program_service(tmp_path, monkeypatch):
    import services.services_work_learning_programs as service

    db_path = tmp_path / "p04-working-issues.db"

    def get_connection():
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        return connection

    monkeypatch.setattr(service, "get_connection", get_connection)

    service.ensure_work_learning_program_tables()

    yield service, db_path


def _create_program(service):
    return service.create_hub_program(
        workspace_id="WS-P04",
        firm_id="FIRM-A",
        owner_id="OWNER-A",
        title="P04 Program",
        purpose="P04 regression",
        created_by="tester",
    )


def test_p04_reuses_locked_guide_evidence_vocabulary(
    isolated_program_service,
):
    service, _db = isolated_program_service

    from services.guide_foundation import GENEALOGY_EVIDENCE_STATES

    assert service.ISSUE_EVIDENCE_STATES == tuple(
        GENEALOGY_EVIDENCE_STATES
    )

    assert service.ISSUE_EVIDENCE_STATES == (
        "documented",
        "corroborated",
        "inferred",
        "disputed",
        "unresolved",
    )


def test_p04_issue_types_and_statuses_are_bounded(
    isolated_program_service,
):
    service, _db = isolated_program_service

    assert service.ISSUE_TYPES == (
        "assumption",
        "gap",
        "conflict",
        "unresolved_issue",
    )

    assert service.ISSUE_STATUSES == (
        "open",
        "resolved",
        "dismissed",
    )


def test_p04_schema_is_wlh_owned_and_does_not_preimplement_p05_or_p07(
    isolated_program_service,
):
    _service, db_path = isolated_program_service

    connection = sqlite3.connect(db_path)

    columns = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(hub_program_issues)"
        ).fetchall()
    }

    connection.close()

    assert {
        "issue_id",
        "program_id",
        "issue_type",
        "statement",
        "evidence_state",
        "status",
        "resolution_note",
        "created_by",
        "created_at",
        "updated_at",
    } <= columns

    # P05 owns source/reference attribution.
    assert "source_reference" not in columns
    assert "source_id" not in columns

    # P07 owns governed promotion.
    assert "governed_record_id" not in columns
    assert "promotion_status" not in columns


def test_p04_create_and_list_working_issue(
    isolated_program_service,
):
    service, _db = isolated_program_service
    program_id = _create_program(service)

    issue_id = service.create_program_issue(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
        issue_type="assumption",
        statement="Assume the timeline remains available.",
        evidence_state="inferred",
        created_by="tester",
    )

    rows = service.get_program_issues(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
    )

    assert len(rows) == 1
    assert rows[0]["issue_id"] == issue_id
    assert rows[0]["issue_type"] == "assumption"
    assert rows[0]["evidence_state"] == "inferred"
    assert rows[0]["status"] == "open"


def test_p04_update_is_working_disposition_only(
    isolated_program_service,
):
    service, _db = isolated_program_service
    program_id = _create_program(service)

    issue_id = service.create_program_issue(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
        issue_type="gap",
        statement="The supporting record has not been located.",
        evidence_state="unresolved",
        created_by="tester",
    )

    changed = service.update_program_issue(
        issue_id=issue_id,
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
        evidence_state="documented",
        status="resolved",
        resolution_note="Record located for later source review.",
    )

    assert changed is True

    issue = service.get_program_issues(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
    )[0]

    assert issue["evidence_state"] == "documented"
    assert issue["status"] == "resolved"
    assert (
        issue["resolution_note"]
        == "Record located for later source review."
    )


def test_p04_invalid_classification_fails_closed(
    isolated_program_service,
):
    service, _db = isolated_program_service
    program_id = _create_program(service)

    with pytest.raises(
        ValueError,
        match="invalid_program_issue_type",
    ):
        service.create_program_issue(
            program_id=program_id,
            firm_id="FIRM-A",
            owner_id="OWNER-A",
            issue_type="verified_fact",
            statement="Not permitted as a P04 issue type.",
            evidence_state="documented",
            created_by="tester",
        )

    with pytest.raises(
        ValueError,
        match="invalid_program_issue_evidence_state",
    ):
        service.create_program_issue(
            program_id=program_id,
            firm_id="FIRM-A",
            owner_id="OWNER-A",
            issue_type="gap",
            statement="Unsupported evidence state.",
            evidence_state="verified",
            created_by="tester",
        )


def test_p04_cross_firm_and_owner_scope_fail_closed(
    isolated_program_service,
):
    service, _db = isolated_program_service
    program_id = _create_program(service)

    issue_id = service.create_program_issue(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
        issue_type="conflict",
        statement="Two working interpretations differ.",
        evidence_state="disputed",
        created_by="tester",
    )

    assert service.get_program_issues(
        program_id=program_id,
        firm_id="FIRM-X",
        owner_id="OWNER-A",
    ) == []

    assert service.get_program_issues(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-X",
    ) == []

    assert service.update_program_issue(
        issue_id=issue_id,
        program_id=program_id,
        firm_id="FIRM-X",
        owner_id="OWNER-A",
        evidence_state="unresolved",
        status="open",
        resolution_note="Cross-firm attempt",
    ) is False

    assert service.update_program_issue(
        issue_id=issue_id,
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-X",
        evidence_state="unresolved",
        status="open",
        resolution_note="Cross-owner attempt",
    ) is False


def test_p04_snapshot_and_revision_preserve_working_issue_state(
    isolated_program_service,
):
    service, _db = isolated_program_service
    program_id = _create_program(service)

    service.create_program_issue(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
        issue_type="unresolved_issue",
        statement="An operator decision remains outstanding.",
        evidence_state="unresolved",
        created_by="tester",
    )

    snapshot = service.build_program_snapshot(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
    )

    assert len(snapshot["issues"]) == 1

    service.create_program_revision(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
        revision_note="Capture P04 working state.",
        created_by="tester",
    )

    revision = service.get_program_revisions(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
    )[0]

    saved = json.loads(revision["snapshot_json"])

    assert len(saved["issues"]) == 1
    assert saved["issues"][0]["issue_type"] == "unresolved_issue"


def test_p04_route_authorization_and_csrf_contract():
    assert (
        '"workspace_program_detail": '
        '{"Admin", "Trustee", "Viewer"}'
    ) in APP

    for rule in (
        '"workspace_program_issue_add": {"Admin", "Trustee"}',
        '"workspace_program_issue_update": {"Admin", "Trustee"}',
    ):
        assert rule in APP
        assert "Viewer" not in rule

    for name in (
        "workspace_program_issue_add",
        "workspace_program_issue_update",
    ):
        source = _function_source(APP, name)
        assert "validate_csrf_token()" in source
        assert "_workspace_program_context(" in source


def test_p04_browser_cannot_supply_firm_or_owner_scope():
    start = APP.index("def workspace_program_issue_add(")
    end = APP.index(
        "def workspace_program_revision_create(",
        start,
    )

    section = APP[start:end]

    for prohibited in (
        'request.form.get("firm_id")',
        "request.form.get('firm_id')",
        'request.args.get("firm_id")',
        "request.args.get('firm_id')",
        'request.form.get("owner_id")',
        "request.form.get('owner_id')",
        'request.args.get("owner_id")',
        "request.args.get('owner_id')",
    ):
        assert prohibited not in section

    assert "_workspace_program_context(" in section


def test_p04_template_preserves_non_authoritative_boundary():
    required = (
        "Assumptions, Gaps, Conflicts &amp; Unresolved Issues",
        "does not make them verified",
        "source attribution is a later controlled capability",
        "workspace_program_issue_add",
        "workspace_program_issue_update",
        "Update Working Issue",
        "Add Working Issue",
    )

    normalized_template = " ".join(TEMPLATE.split())

    for marker in required:
        assert marker in normalized_template

    assert (
        "{% if session.get('role') in ['Admin', 'Trustee'] %}"
        in TEMPLATE
    )

    # P04 must not expose governed promotion controls.
    lowered = TEMPLATE.lower()
    assert "promote to governed" not in lowered
    assert "automatic promotion" not in lowered
