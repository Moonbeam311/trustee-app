"""Pure route adapter for governed Guided Intake proposed tasks."""

from __future__ import annotations

from typing import Any, Mapping


def build_governed_proposed_tasks(
    snapshot: Mapping[str, Any],
) -> list[dict[str, str]]:
    """Mirror legacy snapshot task semantics without creating operational work."""

    tasks = []
    for document in snapshot.get("documents_to_gather", []) or []:
        tasks.append({
            "task_type": "document",
            "priority": "normal",
            "title": f"Gather document: {document}",
            "description": (
                "Client or staff should gather this item before the deeper review "
                "session."
            ),
            "source": "auto_snapshot",
            "operational_status": "pending_client",
        })
    for flag in snapshot.get("review_flags", []) or []:
        professional = "tax" in flag.lower() or "legal" in flag.lower()
        tasks.append({
            "task_type": "professional_review" if professional else "staff_action",
            "priority": (
                "high" if professional or "liability" in flag.lower() else "normal"
            ),
            "title": f"Review flag: {flag}",
            "description": (
                "This item was flagged by the intake translation/scoring engine "
                "and should be reviewed before final action."
            ),
            "source": "auto_snapshot",
            "operational_status": (
                "pending_professional" if professional else "pending_staff"
            ),
        })
    next_session = snapshot.get("recommended_next_session")
    if next_session:
        tasks.append({
            "task_type": "next_session",
            "priority": (
                "high"
                if snapshot.get("review_priority") in ["High", "Elevated"]
                else "normal"
            ),
            "title": f"Prepare next session: {next_session}",
            "description": (
                "Prepare agenda, documents, and follow-up questions for the "
                "recommended next review session."
            ),
            "source": "auto_snapshot",
            "operational_status": "pending_staff",
        })
    return tasks
