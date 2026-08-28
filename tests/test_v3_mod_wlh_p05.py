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

    db_path = tmp_path / "p05-source-attribution.db"

    def get_connection():
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        return connection

    monkeypatch.setattr(
        service,
        "get_connection",
        get_connection,
    )

    service.ensure_work_learning_program_tables()

    yield service, db_path


def _create_program(
    service,
    *,
    workspace_id="WS-P05",
    firm_id="FIRM-A",
    owner_id="OWNER-A",
):
    return service.create_hub_program(
        workspace_id=workspace_id,
        firm_id=firm_id,
        owner_id=owner_id,
        title="P05 Program",
        purpose="P05 regression",
        created_by="tester",
    )


def _create_gap(
    service,
    program_id,
    *,
    firm_id="FIRM-A",
    owner_id="OWNER-A",
):
    return service.create_program_issue(
        program_id=program_id,
        firm_id=firm_id,
        owner_id=owner_id,
        issue_type="gap",
        statement="Supporting attribution remains unresolved.",
        evidence_state="unresolved",
        created_by="tester",
    )


def test_p05_source_reference_types_are_bounded(
    isolated_program_service,
):
    service, _db = isolated_program_service

    assert service.SOURCE_REFERENCE_TYPES == (
        "document_reference",
        "governance_reference",
        "external_reference",
        "other_reference",
    )


def test_p05_schema_is_relationship_only_and_uses_optional_issue_child(
    isolated_program_service,
):
    _service, db_path = isolated_program_service

    connection = sqlite3.connect(db_path)

    columns = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(hub_program_source_references)"
        ).fetchall()
    }

    connection.close()

    assert {
        "source_reference_id",
        "program_id",
        "issue_id",
        "source_type",
        "source_reference",
        "source_label",
        "source_notes",
        "created_by",
        "created_at",
    } <= columns

    # Program is the canonical firm/owner root.
    assert "firm_id" not in columns
    assert "owner_id" not in columns

    # P02 Question learning-resource ownership remains separate.
    assert "question_id" not in columns

    # Attribution is not verification, issue classification,
    # governance, or promotion.
    for prohibited in (
        "evidence_state",
        "verification_status",
        "verified_by",
        "governed_record_id",
        "promotion_status",
        "approval_status",
    ):
        assert prohibited not in columns


def test_p05_program_level_reference_and_duplicate_identity_are_stable(
    isolated_program_service,
):
    service, _db = isolated_program_service

    program_id = _create_program(service)

    first = service.create_program_source_reference(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
        source_type="external_reference",
        source_reference="EXT-P05-001",
        source_label="External working source",
        source_notes="Attribution only.",
        issue_id=None,
        created_by="tester",
    )

    second = service.create_program_source_reference(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
        source_type="external_reference",
        source_reference="EXT-P05-001",
        source_label="Duplicate submission",
        source_notes="Should resolve to existing identity.",
        issue_id="",
        created_by="tester",
    )

    assert second == first

    rows = service.get_program_source_references(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
    )

    assert len(rows) == 1
    assert rows[0]["source_reference_id"] == first
    assert rows[0]["issue_id"] == ""
    assert rows[0]["source_reference"] == "EXT-P05-001"


def test_p05_optional_issue_child_must_belong_to_same_program(
    isolated_program_service,
):
    service, _db = isolated_program_service

    first_program = _create_program(service)
    first_issue = _create_gap(service, first_program)

    second_program = _create_program(
        service,
        workspace_id="WS-P05-B",
    )

    second_issue = _create_gap(service, second_program)

    source_id = service.create_program_source_reference(
        program_id=first_program,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
        source_type="document_reference",
        source_reference="DOC-P05-001",
        source_label="Same-program issue reference",
        source_notes=None,
        issue_id=first_issue,
        created_by="tester",
    )

    assert source_id.startswith("SRC-")

    rows = service.get_program_source_references(
        program_id=first_program,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
    )

    assert rows[0]["issue_id"] == first_issue
    assert rows[0]["issue_type"] == "gap"

    with pytest.raises(
        ValueError,
        match="program_source_reference_issue_not_available",
    ):
        service.create_program_source_reference(
            program_id=first_program,
            firm_id="FIRM-A",
            owner_id="OWNER-A",
            source_type="document_reference",
            source_reference="DOC-P05-WRONG-ISSUE",
            source_label=None,
            source_notes=None,
            issue_id=second_issue,
            created_by="tester",
        )


def test_p05_reference_does_not_mutate_p04_issue_classification(
    isolated_program_service,
):
    service, _db = isolated_program_service

    program_id = _create_program(service)
    issue_id = _create_gap(service, program_id)

    before = service.get_program_issues(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
    )[0]

    service.create_program_source_reference(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
        source_type="document_reference",
        source_reference="DOC-P05-NO-MUTATION",
        source_label="Attribution only",
        source_notes="No evidence-state mutation.",
        issue_id=issue_id,
        created_by="tester",
    )

    after = service.get_program_issues(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
    )[0]

    assert after["issue_id"] == before["issue_id"]
    assert after["evidence_state"] == "unresolved"
    assert after["status"] == "open"
    assert after["resolution_note"] == before["resolution_note"]
    assert after["updated_at"] == before["updated_at"]


def test_p05_cross_firm_and_owner_scope_fail_closed(
    isolated_program_service,
):
    service, _db = isolated_program_service

    program_id = _create_program(service)

    with pytest.raises(
        ValueError,
        match="program_not_available_in_context",
    ):
        service.create_program_source_reference(
            program_id=program_id,
            firm_id="FIRM-X",
            owner_id="OWNER-A",
            source_type="external_reference",
            source_reference="EXT-CROSS-FIRM",
            source_label=None,
            source_notes=None,
            issue_id=None,
            created_by="tester",
        )

    with pytest.raises(
        ValueError,
        match="program_not_available_in_context",
    ):
        service.create_program_source_reference(
            program_id=program_id,
            firm_id="FIRM-A",
            owner_id="OWNER-X",
            source_type="external_reference",
            source_reference="EXT-CROSS-OWNER",
            source_label=None,
            source_notes=None,
            issue_id=None,
            created_by="tester",
        )

    assert service.get_program_source_references(
        program_id=program_id,
        firm_id="FIRM-X",
        owner_id="OWNER-A",
    ) == []

    assert service.get_program_source_references(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-X",
    ) == []


def test_p05_invalid_type_and_blank_reference_fail_closed(
    isolated_program_service,
):
    service, _db = isolated_program_service

    program_id = _create_program(service)

    with pytest.raises(
        ValueError,
        match="invalid_program_source_reference_type",
    ):
        service.create_program_source_reference(
            program_id=program_id,
            firm_id="FIRM-A",
            owner_id="OWNER-A",
            source_type="verified_fact",
            source_reference="NOT-PERMITTED",
            source_label=None,
            source_notes=None,
            issue_id=None,
            created_by="tester",
        )

    with pytest.raises(
        ValueError,
        match="program_source_reference_required",
    ):
        service.create_program_source_reference(
            program_id=program_id,
            firm_id="FIRM-A",
            owner_id="OWNER-A",
            source_type="other_reference",
            source_reference="   ",
            source_label=None,
            source_notes=None,
            issue_id=None,
            created_by="tester",
        )


def test_p05_snapshot_and_revision_preserve_reference_relationships(
    isolated_program_service,
):
    service, _db = isolated_program_service

    program_id = _create_program(service)
    issue_id = _create_gap(service, program_id)

    service.create_program_source_reference(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
        source_type="governance_reference",
        source_reference="GOV-P05-001",
        source_label="Working governance reference",
        source_notes="Attribution relationship only.",
        issue_id=issue_id,
        created_by="tester",
    )

    snapshot = service.build_program_snapshot(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
    )

    assert len(snapshot["source_references"]) == 1
    assert (
        snapshot["source_references"][0]["issue_id"]
        == issue_id
    )

    service.create_program_revision(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
        revision_note="Capture P05 attribution state.",
        created_by="tester",
    )

    revision = service.get_program_revisions(
        program_id=program_id,
        firm_id="FIRM-A",
        owner_id="OWNER-A",
    )[0]

    saved = json.loads(revision["snapshot_json"])

    assert len(saved["source_references"]) == 1
    assert (
        saved["source_references"][0]["source_reference"]
        == "GOV-P05-001"
    )


def test_p05_route_authorization_csrf_and_parent_scope_contract():
    assert (
        '"workspace_program_detail": '
        '{"Admin", "Trustee", "Viewer"}'
    ) in APP

    rule = (
        '"workspace_program_source_reference_add": '
        '{"Admin", "Trustee"}'
    )

    assert rule in APP
    assert "Viewer" not in rule

    source = _function_source(
        APP,
        "workspace_program_source_reference_add",
    )

    assert "validate_csrf_token()" in source
    assert "_workspace_program_context(" in source
    assert "create_program_source_reference(" in source


def test_p05_browser_cannot_supply_scope_or_question_target():
    start = APP.index(
        "def workspace_program_source_reference_add("
    )

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
        'request.form.get("question_id")',
        "request.form.get('question_id')",
        'request.args.get("question_id")',
        "request.args.get('question_id')",
    ):
        assert prohibited not in section

    assert 'request.form.get("issue_id")' in section
    assert "_workspace_program_context(" in section

    lowered = section.lower()

    assert "successor_handoff" not in lowered
    assert "promotion_status" not in lowered
    assert "unified_provenance" not in lowered


def test_p05_template_preserves_attribution_and_phase_boundaries():
    normalized = " ".join(TEMPLATE.split())

    required = (
        "Source &amp; Reference Attribution",
        "Program-level reference",
        "does not verify the referenced content",
        "does not change a working issue's evidence state or status",
        "P02 question learning resources remain separate",
        "workspace_program_source_reference_add",
        "Add Source Reference",
    )

    for marker in required:
        assert marker in normalized

    assert (
        "{% if session.get('role') in ['Admin', 'Trustee'] %}"
        in TEMPLATE
    )

    # Program Detail is globally Flask-WTF protected.
    # All mutation forms on this shared P03/P04/P05 surface must
    # therefore render the signed helper rather than the raw
    # application session-token helper.
    assert 'value="{{ csrf_token() }}"' not in TEMPLATE
    assert TEMPLATE.count(
        'value="{{ wtf_csrf_token() }}"'
    ) == 7

    assert (
        'app.jinja_env.globals["wtf_csrf_token"] = '
        'generate_wtf_csrf_token'
    ) in APP

    # P05 is attribution only. Later-phase controls remain absent.
    lowered = TEMPLATE.lower()

    assert "successor-handoff control" not in lowered
    assert "governed-promotion control" not in lowered
    assert "unified provenance-history control" not in lowered
