from pathlib import Path

from services.guide_foundation import (
    CONFLICT_FLOW,
    GENEALOGY_EVIDENCE_STATES,
    GUIDE_PRINCIPLE,
    INTERPRETATION_CLASSES,
    NO_SILENT_MUTATION_RULE,
    can_silently_mutate_permanent_record,
    classify_interpretation,
)


EXPECTED_CLASSES = (
    "recorded_fact",
    "system_status",
    "source_supported_relationship",
    "inference",
    "conflict",
    "recommendation",
    "proposed_action",
    "operator_authorized_institutional_action",
)


def test_interpretation_taxonomy_is_locked():
    assert INTERPRETATION_CLASSES == EXPECTED_CLASSES


def test_genealogy_evidence_vocabulary_is_locked():
    assert GENEALOGY_EVIDENCE_STATES == (
        "documented",
        "corroborated",
        "inferred",
        "disputed",
        "unresolved",
    )


def test_conflict_flow_is_locked():
    assert CONFLICT_FLOW == (
        "Conflict detected",
        "Supporting evidence",
        "Proposed interpretation or correction",
        "Operator review",
        "Governed action",
        "Permanent audit record",
    )


def test_guide_cannot_silently_mutate_records():
    assert can_silently_mutate_permanent_record() is False
    assert "must not silently mutate" in NO_SILENT_MUTATION_RULE


def test_interpretation_preserves_classification_and_basis():
    item = classify_interpretation(
        classification="recommendation",
        summary="Review the unresolved evidence.",
        basis="Two records conflict.",
        source_reference="EVIDENCE-001",
    )

    assert item.classification == "recommendation"
    assert item.label == "Recommendation"
    assert item.requires_operator_authorization is False
    assert item.source_reference == "EVIDENCE-001"


def test_proposed_action_requires_operator_authorization():
    item = classify_interpretation(
        classification="proposed_action",
        summary="Correct the relationship after review.",
        basis="The governed evidence conflicts.",
    )

    assert item.requires_operator_authorization is True


def test_invalid_classification_rejected():
    try:
        classify_interpretation(
            classification="fact",
            summary="Unsupported class.",
            basis="Test.",
        )
    except ValueError:
        return

    raise AssertionError("Invalid Guide classification was accepted")


def test_guide_template_integrates_foundation():
    page = Path("templates/guide_page.html").read_text(encoding="utf-8")

    assert '{% include "_guide_ai_foundation.html" %}' in page


def test_foundation_partial_contains_governance_boundary():
    partial = Path("templates/_guide_ai_foundation.html").read_text(
        encoding="utf-8"
    )

    assert GUIDE_PRINCIPLE in " ".join(partial.split())
    assert "must not silently mutate" in partial
    assert "Recorded fact" in partial
    assert "System status" in partial
    assert "Source-supported relationship" in partial
    assert "Inference" in partial
    assert "Conflict" in partial
    assert "Recommendation" in partial
    assert "Proposed action" in partial
    assert "Operator-authorized institutional action" in partial
