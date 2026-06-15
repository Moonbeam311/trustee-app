from __future__ import annotations

from pathlib import Path

from jinja2 import Environment


ROOT = Path(__file__).resolve().parents[1]

MATTER_TEMPLATE = (
    ROOT
    / "templates"
    / "matter_detail.html"
)

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


def test_matter_detail_has_governed_handoff_panel() -> None:
    source = read(MATTER_TEMPLATE)

    assert (
        "MIA-1D-F-E: governed Intake handoff panel"
        in source
    )

    assert "Intake Handoff" in source
    assert "matter_intake_links" in source
    assert "link.bridge_id" in source
    assert "link.intake_id" in source
    assert "link.link_status" in source
    assert "link.handoff_status" in source
    assert "link.recommendation_disposition" in source
    assert "'intake_saved_snapshot'" in source

    assert (
        "separate from the"
        in source
    )

    assert (
        "general Matter Relationship"
        in source
    )


def test_intake_snapshot_has_institutional_matter_panel() -> None:
    source = read(INTAKE_TEMPLATE)

    assert (
        "MIA-1D-F-E: institutional Matter panel"
        in source
    )

    assert "Institutional Matter" in source
    assert "matter_intake_links" in source
    assert "link.bridge_id" in source
    assert "link.matter_id" in source
    assert "link.link_status" in source
    assert "link.handoff_status" in source
    assert "link.recommendation_disposition" in source
    assert "'matter_detail'" in source

    assert (
        "does not replace a Matter Relationship"
        in source
    )


def test_templates_parse_as_jinja() -> None:
    environment = Environment()

    environment.parse(
        read(MATTER_TEMPLATE)
    )

    environment.parse(
        read(INTAKE_TEMPLATE)
    )


def test_visibility_listing_remains_read_only() -> None:
    matter_source = read(MATTER_TEMPLATE)
    intake_source = read(INTAKE_TEMPLATE)

    matter_section = matter_source[
        matter_source.index(
            "MIA-1D-F-E: governed Intake handoff panel"
        ):
        matter_source.index(
            "<h2>Matter Timeline</h2>"
        )
    ]

    intake_section = intake_source[
        intake_source.index(
            "MIA-1D-F-E: institutional Matter panel"
        ):
        intake_source.index(
            'include "intake/translation_snapshot.html"'
        )
    ]

    proposal_marker = (
        "MIA-1D-F-G-B3: explicit handoff proposal"
    )

    assert proposal_marker in matter_section

    proposal_start = matter_section.index(
        proposal_marker
    )

    listing_start = matter_section.index(
        "{% if matter_intake_links %}",
        proposal_start,
    )

    matter_listing = matter_section[listing_start:]

    governed_listing_sections = (
        matter_listing
        + intake_section
    )

    prohibited = (
        "create_matter_intake_link",
        "review_matter_intake_handoff",
        "update_handoff",
        "<form",
        'method="POST"',
        "Add Matter Relationship",
    )

    for marker in prohibited:
        assert marker not in governed_listing_sections


def test_explicit_proposal_form_is_separate_from_listing() -> None:
    matter_source = read(MATTER_TEMPLATE)

    matter_section = matter_source[
        matter_source.index(
            "MIA-1D-F-E: governed Intake handoff panel"
        ):
        matter_source.index(
            "<h2>Matter Timeline</h2>"
        )
    ]

    proposal_marker = (
        "MIA-1D-F-G-B3: explicit handoff proposal"
    )

    proposal_start = matter_section.index(
        proposal_marker
    )

    listing_start = matter_section.index(
        "{% if matter_intake_links %}",
        proposal_start,
    )

    proposal_section = matter_section[
        proposal_start:
        listing_start
    ]

    assert "<form" in proposal_section
    assert 'method="POST"' in proposal_section
    assert "propose_matter_intake_bridge" in proposal_section
    assert 'name="_csrf_token"' in proposal_section
    assert "{{ csrf_token() }}" in proposal_section

    assert "review_matter_intake_handoff" not in proposal_section
    assert "Add Matter Relationship" not in proposal_section
