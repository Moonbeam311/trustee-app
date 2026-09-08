from __future__ import annotations

from pathlib import Path
from typing import Any

from database.migrations_matter_intake import (
    apply_matter_intake_bridge_schema,
    MatterIntakeMigrationError,
)
from database.migrations_successor_acceptance import (
    apply_successor_acceptance_schema,
    SuccessorAcceptanceMigrationError,
)
from database.migrations_governed_program_promotion import (
    apply_governed_program_promotion_schema,
    GovernedProgramPromotionMigrationError,
)
from database.migrations_work_learning_authority import (
    apply_work_learning_authority_schema,
    WorkLearningAuthorityMigrationError,
)
from database.migrations_document_base_schema import (
    apply_document_base_schema,
    DocumentBaseSchemaMigrationError,
)
from database.migrations_generated_document_attribution import (
    apply_generated_document_attribution_schema,
    GeneratedDocumentAttributionMigrationError,
)
from database.migrations_workspace_schema import (
    apply_workspace_schema,
    WorkspaceSchemaMigrationError,
)


def run_additive_startup_migrations(
    db_path: str | Path,
) -> dict[str, Any]:
    """
    Run additive and idempotent application schema migrations.

    This function may create missing schema objects. It must not infer,
    create, accept, reject, or end operational Matter–Intake links.
    """

    try:
        result = apply_matter_intake_bridge_schema(db_path)
    except MatterIntakeMigrationError as exc:
        # Hosted startup safety:
        # On Railway/Render a fresh mounted SQLite database may exist before
        # the full application schema has been created. The Matter–Intake
        # bridge is additive and must not block app boot if its source tables
        # are not present yet.
        result = {
            "schema_complete": False,
            "deferred": True,
            "reason": str(exc),
            "link_rows": 0,
            "event_rows": 0,
        }

    try:
        acceptance_result = apply_successor_acceptance_schema(db_path)
    except SuccessorAcceptanceMigrationError as exc:
        acceptance_result = {
            "schema_complete": False,
            "deferred": True,
            "reason": str(exc),
            "acceptance_rows": 0,
        }

    try:
        promotion_result = apply_governed_program_promotion_schema(db_path)
    except GovernedProgramPromotionMigrationError as exc:
        promotion_result = {
            "schema_complete": False,
            "deferred": True,
            "reason": str(exc),
            "records_created": 0,
        }

    try:
        authority_result = apply_work_learning_authority_schema(db_path)
    except WorkLearningAuthorityMigrationError as exc:
        authority_result = {"schema_complete": False, "deferred": True,
                            "reason": str(exc), "records_created": 0}

    try:
        document_base_result = apply_document_base_schema(db_path)
    except DocumentBaseSchemaMigrationError as exc:
        document_base_result = {
            "schema_complete": False,
            "deferred": True,
            "reason": str(exc),
            "document_templates_table_created": False,
            "generated_documents_table_created": False,
            "document_templates_rows_preserved": 0,
            "generated_documents_rows_preserved": 0,
            "template_rows_seeded": 0,
            "records_created": 0,
        }

    try:
        document_attribution_result = (
            apply_generated_document_attribution_schema(db_path)
        )
    except GeneratedDocumentAttributionMigrationError as exc:
        document_attribution_result = {
            "schema_complete": False,
            "deferred": True,
            "reason": str(exc),
            "columns_added": 0,
            "legacy_rows_preserved": 0,
            "legacy_rows_updated": 0,
            "records_created": 0,
        }


    try:
        workspace_result = apply_workspace_schema(db_path)
    except WorkspaceSchemaMigrationError as exc:
        workspace_result = {
            "schema_complete": False,
            "deferred": True,
            "reason": str(exc),
            "table_created": False,
            "columns_added": [],
            "legacy_rows_preserved": 0,
            "legacy_rows_updated": 0,
            "records_created": 0,
        }

    return {
        "matter_intake_bridge": result,
        "successor_acceptance": acceptance_result,
        "governed_program_promotion": promotion_result,
        "work_learning_authority": authority_result,
        "document_base_schema": document_base_result,
        "generated_document_attribution": document_attribution_result,
        "workspace_schema": workspace_result,
        "operational_links_created": result.get("link_rows", 0),
        "operational_events_created": result.get("event_rows", 0),
        "acceptance_records_created": 0,
        "promotion_records_created": 0,
        "authority_records_created": 0,
        "generated_document_attribution_records_created": 0,
        "workspace_records_created": 0,
    }
