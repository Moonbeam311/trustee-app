"""Governed genealogy relationship review/status service.

Current assertion state remains separate from append-only review history.

Status mutation is permitted only through an explicit human-governed
review action.

This service does not:
- infer people or relationships;
- parse legacy parent/spouse text;
- create reciprocal relationships;
- create Media Evidence;
- treat attached evidence as automatic confirmation;
- allow SYSTEM_SUGGESTED review to finalize status;
- reuse or modify P09;
- establish inheritance, ownership, citizenship, legal status,
  authority, entitlement, or genealogical truth.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class GenealogyRelationshipReviewServiceError(RuntimeError):
    pass


HUMAN_DECISION_ORIGINS = (
    "OPERATOR_OR_FIDUCIARY",
    "PROFESSIONAL",
)


ALLOWED_TRANSITIONS = {
    "USER_ASSERTED": {
        "REVIEW_REQUIRED",
    },
    "REVIEW_REQUIRED": {
        "CONFIRMED",
        "CONFLICTING",
        "UNRESOLVED",
    },
    "CONFIRMED": {
        "REVIEW_REQUIRED",
    },
    "CONFLICTING": {
        "REVIEW_REQUIRED",
    },
    "UNRESOLVED": {
        "REVIEW_REQUIRED",
    },
}


GENEALOGY_RELATIONSHIP_MEDIA_ENTITY_TYPE = (
    "genealogy_relationship_assertion"
)


def _required(value: Any, label: str) -> str:
    text = str(value or "").strip()

    if not text:
        raise GenealogyRelationshipReviewServiceError(
            f"{label} is required."
        )

    return text


def _connection(
    db_path: str | Path,
) -> sqlite3.Connection:
    con = sqlite3.connect(str(Path(db_path)))
    con.row_factory = sqlite3.Row
    return con


def _scoped_assertion(
    con: sqlite3.Connection,
    assertion_id: str,
    owner_id: str,
    firm_id: str,
) -> sqlite3.Row:
    row = con.execute(
        """
        SELECT *
        FROM genealogy_relationship_assertions
        WHERE assertion_id = ?
          AND owner_id = ?
          AND firm_id = ?
        LIMIT 1
        """,
        (
            assertion_id,
            owner_id,
            firm_id,
        ),
    ).fetchone()

    if row is None:
        raise GenealogyRelationshipReviewServiceError(
            "Scoped genealogy relationship assertion not found."
        )

    return row


def _latest_review(
    con: sqlite3.Connection,
    assertion_id: str,
    owner_id: str,
    firm_id: str,
) -> sqlite3.Row | None:
    return con.execute(
        """
        SELECT *
        FROM genealogy_relationship_reviews
        WHERE assertion_id = ?
          AND owner_id = ?
          AND firm_id = ?
        ORDER BY
            created_at DESC,
            rowid DESC
        LIMIT 1
        """,
        (
            assertion_id,
            owner_id,
            firm_id,
        ),
    ).fetchone()


def _linked_evidence_count(
    con: sqlite3.Connection,
    assertion_id: str,
    firm_id: str,
) -> int:
    try:
        row = con.execute(
            """
            SELECT COUNT(*)
            FROM media_records
            WHERE related_entity_type = ?
              AND related_entity_id = ?
              AND firm_id = ?
            """,
            (
                GENEALOGY_RELATIONSHIP_MEDIA_ENTITY_TYPE,
                assertion_id,
                firm_id,
            ),
        ).fetchone()
    except sqlite3.Error as exc:
        raise GenealogyRelationshipReviewServiceError(
            "Media Evidence schema unavailable."
        ) from exc

    return int(row[0])


def transition_genealogy_relationship_status(
    db_path: str | Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Record one human-governed review and atomically update status."""

    data = dict(payload or {})

    review_id = _required(
        data.get("review_id"),
        "Review ID",
    )
    assertion_id = _required(
        data.get("assertion_id"),
        "Assertion ID",
    )
    owner_id = _required(
        data.get("owner_id"),
        "Owner scope",
    )
    firm_id = _required(
        data.get("firm_id"),
        "Firm scope",
    )
    new_status = _required(
        data.get("new_status"),
        "New status",
    )
    review_basis = _required(
        data.get("review_basis"),
        "Review basis",
    )
    provenance = _required(
        data.get("provenance"),
        "Provenance",
    )
    decision_origin = _required(
        data.get("decision_origin"),
        "Decision origin",
    )
    actor = _required(
        data.get("actor"),
        "Actor",
    )
    actor_capacity = _required(
        data.get("actor_capacity"),
        "Actor capacity",
    )

    human_confirmed = data.get("human_confirmed")

    if human_confirmed is not True:
        raise GenealogyRelationshipReviewServiceError(
            "Status transition requires explicit human confirmation."
        )

    if decision_origin not in HUMAN_DECISION_ORIGINS:
        raise GenealogyRelationshipReviewServiceError(
            "SYSTEM_SUGGESTED status finalization is prohibited."
        )

    professional_authority = (
        str(
            data.get("professional_authority") or ""
        ).strip()
        or None
    )

    if (
        decision_origin == "PROFESSIONAL"
        and professional_authority is None
    ):
        raise GenealogyRelationshipReviewServiceError(
            "Professional authority is required."
        )

    con = _connection(db_path)

    try:
        con.execute("BEGIN IMMEDIATE")

        assertion = _scoped_assertion(
            con,
            assertion_id,
            owner_id,
            firm_id,
        )

        current_status = str(
            assertion["assertion_status"]
        )

        allowed = ALLOWED_TRANSITIONS.get(
            current_status,
            set(),
        )

        if new_status not in allowed:
            raise GenealogyRelationshipReviewServiceError(
                "Invalid governed genealogy status transition: "
                f"{current_status} -> {new_status}."
            )

        duplicate = con.execute(
            """
            SELECT review_id
            FROM genealogy_relationship_reviews
            WHERE review_id = ?
            LIMIT 1
            """,
            (review_id,),
        ).fetchone()

        if duplicate is not None:
            raise GenealogyRelationshipReviewServiceError(
                "Review ID already exists."
            )

        if new_status == "CONFIRMED":
            if (
                _linked_evidence_count(
                    con,
                    assertion_id,
                    firm_id,
                )
                < 1
            ):
                raise GenealogyRelationshipReviewServiceError(
                    "CONFIRMED requires linked Media Evidence."
                )

        prior = _latest_review(
            con,
            assertion_id,
            owner_id,
            firm_id,
        )

        prior_review_id = (
            prior["review_id"]
            if prior is not None
            else None
        )

        con.execute(
            """
            INSERT INTO genealogy_relationship_reviews (
                review_id,
                owner_id,
                firm_id,
                assertion_id,
                prior_review_id,
                prior_status,
                new_status,
                review_basis,
                provenance,
                decision_origin,
                human_confirmed,
                actor,
                actor_capacity,
                professional_authority
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_id,
                owner_id,
                firm_id,
                assertion_id,
                prior_review_id,
                current_status,
                new_status,
                review_basis,
                provenance,
                decision_origin,
                1,
                actor,
                actor_capacity,
                professional_authority,
            ),
        )

        updated = con.execute(
            """
            UPDATE genealogy_relationship_assertions
            SET assertion_status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE assertion_id = ?
              AND owner_id = ?
              AND firm_id = ?
              AND assertion_status = ?
            """,
            (
                new_status,
                assertion_id,
                owner_id,
                firm_id,
                current_status,
            ),
        )

        if updated.rowcount != 1:
            raise GenealogyRelationshipReviewServiceError(
                "Assertion status changed during governed review."
            )

        review = con.execute(
            """
            SELECT *
            FROM genealogy_relationship_reviews
            WHERE review_id = ?
            """,
            (review_id,),
        ).fetchone()

        con.commit()

        result = dict(review)
        result["assertion_status"] = new_status

        return result

    except GenealogyRelationshipReviewServiceError:
        con.rollback()
        raise

    except sqlite3.Error as exc:
        con.rollback()
        raise GenealogyRelationshipReviewServiceError(
            str(exc)
        ) from exc

    finally:
        con.close()


def list_genealogy_relationship_reviews(
    db_path: str | Path,
    assertion_id: str,
    owner_id: str,
    firm_id: str,
) -> list[dict[str, Any]]:
    assertion = _required(
        assertion_id,
        "Assertion ID",
    )
    owner = _required(
        owner_id,
        "Owner scope",
    )
    firm = _required(
        firm_id,
        "Firm scope",
    )

    con = _connection(db_path)

    try:
        _scoped_assertion(
            con,
            assertion,
            owner,
            firm,
        )

        rows = con.execute(
            """
            SELECT *
            FROM genealogy_relationship_reviews
            WHERE assertion_id = ?
              AND owner_id = ?
              AND firm_id = ?
            ORDER BY
                created_at,
                rowid
            """,
            (
                assertion,
                owner,
                firm,
            ),
        ).fetchall()

        return [dict(row) for row in rows]

    except sqlite3.Error as exc:
        raise GenealogyRelationshipReviewServiceError(
            str(exc)
        ) from exc

    finally:
        con.close()
