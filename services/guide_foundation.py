"""Governed Guide interpretation foundation for Hindsfoot OS Version 3.

This module defines interpretation classes and action boundaries shared by
future Guide integrations.  It does not mutate institutional records.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


GUIDE_PRINCIPLE: Final[str] = (
    "The Guide interprets the governed institutional record, explains context, "
    "identifies gaps, and recommends next actions while preserving operator "
    "authority over changes to the permanent record."
)

NO_SILENT_MUTATION_RULE: Final[str] = (
    "The Guide may interpret and recommend but must not silently mutate "
    "permanent institutional records."
)


INTERPRETATION_CLASSES: Final[tuple[str, ...]] = (
    "recorded_fact",
    "system_status",
    "source_supported_relationship",
    "inference",
    "conflict",
    "recommendation",
    "proposed_action",
    "operator_authorized_institutional_action",
)


INTERPRETATION_LABELS: Final[dict[str, str]] = {
    "recorded_fact": "Recorded fact",
    "system_status": "System status",
    "source_supported_relationship": "Source-supported relationship",
    "inference": "Inference",
    "conflict": "Conflict",
    "recommendation": "Recommendation",
    "proposed_action": "Proposed action",
    "operator_authorized_institutional_action": (
        "Operator-authorized institutional action"
    ),
}


GENEALOGY_EVIDENCE_STATES: Final[tuple[str, ...]] = (
    "documented",
    "corroborated",
    "inferred",
    "disputed",
    "unresolved",
)


CONFLICT_FLOW: Final[tuple[str, ...]] = (
    "Conflict detected",
    "Supporting evidence",
    "Proposed interpretation or correction",
    "Operator review",
    "Governed action",
    "Permanent audit record",
)


@dataclass(frozen=True)
class GuideInterpretation:
    """Read-only Guide interpretation envelope."""

    classification: str
    summary: str
    basis: str
    source_reference: str | None = None

    def __post_init__(self) -> None:
        if self.classification not in INTERPRETATION_CLASSES:
            raise ValueError(
                f"Unsupported Guide classification: {self.classification}"
            )

        if not self.summary.strip():
            raise ValueError("Guide interpretation summary is required.")

        if not self.basis.strip():
            raise ValueError("Guide interpretation basis is required.")

    @property
    def label(self) -> str:
        return INTERPRETATION_LABELS[self.classification]

    @property
    def requires_operator_authorization(self) -> bool:
        return self.classification in {
            "proposed_action",
            "operator_authorized_institutional_action",
        }


def classify_interpretation(
    classification: str,
    summary: str,
    basis: str,
    source_reference: str | None = None,
) -> GuideInterpretation:
    """Create a governed read-only interpretation envelope."""

    return GuideInterpretation(
        classification=classification,
        summary=summary,
        basis=basis,
        source_reference=source_reference,
    )


def can_silently_mutate_permanent_record() -> bool:
    """Permanent institutional mutation is never silently authorized."""

    return False
