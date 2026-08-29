"""P06 read-only adapter between a working Program and canonical Handoff reads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from services.services_handoff_package_adapter import (
    build_successor_handoff_package_descriptor,
)
from services.services_intake_trust_bridge import validate_no_secret_material
from services.services_work_learning_programs import (
    build_program_snapshot,
    get_hub_program,
    get_program_revisions,
)


CURRENT = "CURRENT"
SAVED_REVISION = "SAVED_REVISION"
PROGRAM_STATE_MODES = (CURRENT, SAVED_REVISION)


class WorkLearningProgramHandoffError(ValueError):
    """Fail-closed P06 boundary error without inaccessible-record detail."""


def _validate_secret_tree(value: Any) -> None:
    if isinstance(value, dict):
        validate_no_secret_material(value)
        for item in value.values():
            _validate_secret_tree(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _validate_secret_tree(item)


def build_work_learning_program_handoff_descriptor(
    *,
    program_id: str,
    workspace_id: str,
    firm_id: str,
    owner_id: str,
    state_mode: str,
    trust_id: str,
    db_path: str | Path,
    trust_authorization_check: Callable[[str], bool],
    continuity_authorization_check: Callable[[str], bool],
    fiduciary_authorization_check: Callable[[str, str | None], bool],
    governance_authorization_check: Callable[[str], bool],
    acceptance_authorization_check: Callable[[str, str], bool] | None = None,
    revision_id: str | None = None,
    execution_id: Any = None,
    transfer_id: Any = None,
) -> dict[str, Any]:
    """Build one ephemeral integration view from already-authorized scope."""
    mode = str(state_mode or "").strip().upper()
    if mode not in PROGRAM_STATE_MODES:
        raise WorkLearningProgramHandoffError("handoff_context_not_available")
    if not all((program_id, workspace_id, firm_id, owner_id, trust_id)):
        raise WorkLearningProgramHandoffError("handoff_context_not_available")
    if any(check is None for check in (
        trust_authorization_check,
        continuity_authorization_check,
        fiduciary_authorization_check,
        governance_authorization_check,
    )):
        raise WorkLearningProgramHandoffError("handoff_context_not_available")

    program = get_hub_program(
        program_id=program_id,
        firm_id=firm_id,
        owner_id=owner_id,
    )
    if not program or program.get("workspace_id") != workspace_id:
        raise WorkLearningProgramHandoffError("handoff_context_not_available")

    selected_revision = None
    if mode == CURRENT:
        if revision_id:
            raise WorkLearningProgramHandoffError("handoff_context_not_available")
        snapshot = build_program_snapshot(
            program_id=program_id,
            firm_id=firm_id,
            owner_id=owner_id,
        )
    else:
        if not revision_id:
            raise WorkLearningProgramHandoffError("handoff_context_not_available")
        selected_revision = next((
            row for row in get_program_revisions(
                program_id=program_id,
                firm_id=firm_id,
                owner_id=owner_id,
            )
            if row.get("revision_id") == revision_id
            and row.get("program_id") == program_id
        ), None)
        if selected_revision is None:
            raise WorkLearningProgramHandoffError("handoff_context_not_available")
        try:
            snapshot = json.loads(selected_revision["snapshot_json"])
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise WorkLearningProgramHandoffError(
                "handoff_context_not_available"
            ) from exc
        snapshot_program = snapshot.get("program") if isinstance(snapshot, dict) else None
        if not isinstance(snapshot_program, dict) or (
            snapshot_program.get("program_id") != program_id
            or snapshot_program.get("workspace_id") != workspace_id
            or snapshot_program.get("firm_id") != firm_id
            or snapshot_program.get("owner_id") != owner_id
        ):
            raise WorkLearningProgramHandoffError("handoff_context_not_available")

    _validate_secret_tree(snapshot)
    handoff_package = build_successor_handoff_package_descriptor(
        trust_id,
        db_path=db_path,
        trust_authorization_check=trust_authorization_check,
        continuity_authorization_check=continuity_authorization_check,
        fiduciary_authorization_check=fiduciary_authorization_check,
        governance_authorization_check=governance_authorization_check,
        acceptance_authorization_check=acceptance_authorization_check,
        execution_id=execution_id,
        transfer_id=transfer_id,
    )
    if handoff_package is None:
        raise WorkLearningProgramHandoffError("handoff_context_not_available")

    effects = {
        "governed_record_created": False,
        "package_record_created": False,
        "archive_record_created": False,
        "successor_acceptance_changed": False,
        "continuity_activated": False,
        "responsibility_assigned": False,
        "execution_advanced": False,
        "application_access_changed": False,
        "handoff_acknowledged": False,
        "program_revision_created": False,
    }
    descriptor = {
        "contract_version": "V3-MOD-WLH-P06",
        "descriptor_type": "WorkLearningProgramHandoffDescriptor",
        "ephemeral": True,
        "program_id": program_id,
        "workspace_id": workspace_id,
        "firm_id": firm_id,
        "owner_id": owner_id,
        "trust_id": trust_id,
        "state_mode": mode,
        "revision_id": selected_revision.get("revision_id") if selected_revision else None,
        "revision_number": selected_revision.get("revision_number") if selected_revision else None,
        "program_snapshot": snapshot,
        "p04_issues": snapshot.get("issues", []),
        "p05_source_references": snapshot.get("source_references", []),
        "canonical_handoff_package_descriptor": handoff_package,
        "provenance_boundaries": {
            "program": "Work & Learning Hub Program working material",
            "p04_issues": "Program-owned working issue context",
            "p05_source_references": "Program-owned attribution; not verification",
            "handoff": "Canonical Handoff package adapter reference input",
        },
        "classification": {
            "program_material": "WORKING",
            "handoff_material": "CANONICAL_REFERENCE",
            "institutional_record": False,
        },
        "institutional_effects": effects,
        **effects,
        "mutation_performed": False,
    }
    _validate_secret_tree(descriptor)
    return descriptor
