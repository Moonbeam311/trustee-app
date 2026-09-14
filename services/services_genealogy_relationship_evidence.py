"""Genealogy relationship ↔ existing Media Evidence adapter.

This module does not create a genealogy-specific evidence store.

It establishes the canonical Media Evidence linkage contract for a
genealogy relationship assertion:

    related_entity_type = "genealogy_relationship_assertion"
    related_entity_id   = <assertion_id>

The target assertion must already exist inside the explicit owner/firm
scope before a media link payload may be produced.

The existing Media Evidence subsystem remains responsible for actual file
storage and media record creation.

This adapter:
- does not create genealogy assertions;
- does not infer people or relationships;
- does not create reciprocal relationships;
- does not authenticate or confirm genealogy;
- does not change assertion review status;
- does not use or modify P09 verification;
- does not create another evidence table.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from services.services_genealogy_relationships import (
    GenealogyRelationshipServiceError,
    get_genealogy_relationship_assertion,
)


GENEALOGY_RELATIONSHIP_MEDIA_ENTITY_TYPE = (
    "genealogy_relationship_assertion"
)


class GenealogyRelationshipEvidenceServiceError(RuntimeError):
    pass


def _required(value: Any, label: str) -> str:
    text = str(value or "").strip()

    if not text:
        raise GenealogyRelationshipEvidenceServiceError(
            f"{label} is required."
        )

    return text


def _scoped_assertion(
    db_path: str | Path,
    assertion_id: Any,
    owner_id: Any,
    firm_id: Any,
) -> dict[str, Any]:
    assertion = _required(assertion_id, "Assertion ID")
    owner = _required(owner_id, "Owner scope")
    firm = _required(firm_id, "Firm scope")

    try:
        row = get_genealogy_relationship_assertion(
            db_path,
            assertion,
            owner,
            firm,
        )
    except GenealogyRelationshipServiceError as exc:
        raise GenealogyRelationshipEvidenceServiceError(
            str(exc)
        ) from exc

    if row is None:
        raise GenealogyRelationshipEvidenceServiceError(
            "Scoped genealogy relationship assertion not found."
        )

    return row


def build_genealogy_relationship_media_link(
    db_path: str | Path,
    assertion_id: str,
    owner_id: str,
    firm_id: str,
) -> dict[str, Any]:
    """Return the canonical payload fields for existing Media Evidence.

    This does not insert a media record. The existing Media Evidence
    creation path remains the write owner.
    """

    row = _scoped_assertion(
        db_path,
        assertion_id,
        owner_id,
        firm_id,
    )

    return {
        "related_entity_type": (
            GENEALOGY_RELATIONSHIP_MEDIA_ENTITY_TYPE
        ),
        "related_entity_id": row["assertion_id"],
        "firm_id": row["firm_id"],
        "trust_id": row.get("trust_id"),
    }


def list_genealogy_relationship_media_evidence(
    db_path: str | Path,
    assertion_id: str,
    owner_id: str,
    firm_id: str,
) -> list[dict[str, Any]]:
    """Read existing Media Evidence linked to one scoped assertion."""

    row = _scoped_assertion(
        db_path,
        assertion_id,
        owner_id,
        firm_id,
    )

    con = sqlite3.connect(str(Path(db_path)))
    con.row_factory = sqlite3.Row

    try:
        records = con.execute(
            """
            SELECT *
            FROM media_records
            WHERE related_entity_type = ?
              AND related_entity_id = ?
              AND firm_id = ?
            ORDER BY
                created_at DESC,
                media_id DESC
            """,
            (
                GENEALOGY_RELATIONSHIP_MEDIA_ENTITY_TYPE,
                row["assertion_id"],
                row["firm_id"],
            ),
        ).fetchall()

        return [dict(record) for record in records]

    except sqlite3.Error as exc:
        raise GenealogyRelationshipEvidenceServiceError(
            str(exc)
        ) from exc
    finally:
        con.close()
