from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

APP = (ROOT / "app.py").read_text(
    encoding="utf-8",
    errors="strict",
)

TEMPLATE = (
    ROOT / "templates" / "property_detail.html"
).read_text(
    encoding="utf-8",
    errors="strict",
)


def _property_detail_route_block():
    start = APP.index(
        '@app.route("/property/<property_id>")'
    )

    next_route = APP.find(
        "\n@app.route(",
        start + 1,
    )

    if next_route == -1:
        return APP[start:]

    return APP[start:next_route]


def _finalization_template_section():
    begin = (
        "<!-- HOS 1E-C2 PROPERTY "
        "FINALIZATION STATUS BEGIN -->"
    )

    end = (
        "<!-- HOS 1E-C2 PROPERTY "
        "FINALIZATION STATUS END -->"
    )

    start = TEMPLATE.index(begin)
    finish = TEMPLATE.index(
        end,
        start,
    ) + len(end)

    return TEMPLATE[start:finish]


def test_property_detail_reuses_certified_read_model():
    block = _property_detail_route_block()

    assert (
        "get_property_finalization_snapshot("
        in block
    )

    assert (
        "services.services_tr001_property_finalization"
        in block
    )

    assert (
        "from database.db import DB_PATH"
        in block
    )


def test_property_detail_uses_property_scope_not_hardcoded_tr001():
    block = _property_detail_route_block()

    assert (
        'firm_id = prop_data.get("firm_id")'
        in block
    )

    assert (
        'trust_id = prop_data.get("trust_id")'
        in block
    )

    assert '"TR-001"' not in block
    assert "'TR-001'" not in block

    assert "Task36" not in block
    assert "PRI-5C42BFAE8B" not in block


def test_property_detail_passes_read_model_to_existing_template():
    block = _property_detail_route_block()

    assert (
        "finalization_snapshot="
        "finalization_snapshot"
        in block
    )

    assert (
        "finalization_snapshot_error="
        "finalization_snapshot_error"
        in block
    )

    assert (
        '"property_detail.html"'
        in block
    )


def test_property_finalization_section_is_read_only():
    section = _finalization_template_section()

    lowered = section.lower()

    assert "<form" not in lowered
    assert "method=" not in lowered
    assert "action=" not in lowered
    assert "<button" not in lowered


def test_property_finalization_section_keeps_fact_boundaries_visible():
    section = _finalization_template_section()

    required = (
        "Possession attestations currently recorded",
        "Ownership attestations currently recorded",
        "Transfer completed",
        "Trustee property acceptance recorded",
        "Funding recorded",
        "Execution state",
        "Schedule A derived-draft eligibility",
    )

    for text in required:
        assert text in section


def test_schedule_a_is_described_as_derived_not_dispositive():
    section = _finalization_template_section()

    assert (
        "prospective and derived"
        in section
    )

    assert (
        "not a second property registry"
        in section
    )

    assert (
        "does not itself"
        in section
    )


def test_property_page_does_not_hardcode_task_or_pri_identity():
    section = _finalization_template_section()

    assert "Task36" not in section
    assert "PRI-5C42BFAE8B" not in section
