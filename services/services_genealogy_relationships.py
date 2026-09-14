"""Scoped first-class genealogy relationship assertion service.

This service records only explicit directional assertions between two
existing canonical Person identities in the same owner/firm scope.

Creation:
- requires explicit Person IDs;
- never searches or matches by name;
- never reads legacy parent_1, parent_2, or spouse text to infer a link;
- never creates a reciprocal or inverse assertion automatically;
- always begins at USER_ASSERTED;
- does not perform evidence review or confirmation;
- does not create Media Evidence records;
- does not use or modify P09 authority/claim verification;
- does not establish genealogical truth, inheritance, ownership,
  citizenship, legal status, authority, or entitlement.

Later review/status services may govern deliberate status transitions.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class GenealogyRelationshipServiceError(RuntimeError):
    pass


def _required(value: Any, label: str) -> str:
    text = str(value or "").strip()

    if not text:
        raise GenealogyRelationshipServiceError(
            f"{label} is required."
        )

    return text


def _scope(
    owner_id: Any,
    firm_id: Any,
) -> tuple[str, str]:
    return (
        _required(owner_id, "Owner scope"),
        _required(firm_id, "Firm scope"),
    )


def _connection(
    db_path: str | Path,
) -> sqlite3.Connection:
    con = sqlite3.connect(str(Path(db_path)))
    con.row_factory = sqlite3.Row
    return con


def _person_exists(
    con: sqlite3.Connection,
    person_id: str,
    owner_id: str,
    firm_id: str,
) -> bool:
    row = con.execute(
        """
        SELECT person_id
        FROM persons
        WHERE person_id = ?
          AND owner_id = ?
          AND firm_id = ?
        """,
        (
            person_id,
            owner_id,
            firm_id,
        ),
    ).fetchone()

    return row is not None


def create_genealogy_relationship_assertion(
    db_path: str | Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Create one explicit directional relationship assertion."""

    data = dict(payload or {})

    assertion_id = _required(
        data.get("assertion_id"),
        "Assertion ID",
    )

    owner_id, firm_id = _scope(
        data.get("owner_id"),
        data.get("firm_id"),
    )

    subject_person_id = _required(
        data.get("subject_person_id"),
        "Subject Person ID",
    )

    relationship_type = _required(
        data.get("relationship_type"),
        "Relationship type",
    )

    related_person_id = _required(
        data.get("related_person_id"),
        "Related Person ID",
    )

    if subject_person_id == related_person_id:
        raise GenealogyRelationshipServiceError(
            "Subject Person and Related Person must be different."
        )

    requested_status = str(
        data.get("assertion_status") or ""
    ).strip()

    if (
        requested_status
        and requested_status != "USER_ASSERTED"
    ):
        raise GenealogyRelationshipServiceError(
            "New genealogy relationship assertions must begin "
            "as USER_ASSERTED."
        )

    con = _connection(db_path)

    try:
        if not _person_exists(
            con,
            subject_person_id,
            owner_id,
            firm_id,
        ):
            raise GenealogyRelationshipServiceError(
                "Scoped Subject Person identity not found."
            )

        if not _person_exists(
            con,
            related_person_id,
            owner_id,
            firm_id,
        ):
            raise GenealogyRelationshipServiceError(
                "Scoped Related Person identity not found."
            )

        duplicate = con.execute(
            """
            SELECT assertion_id
            FROM genealogy_relationship_assertions
            WHERE owner_id = ?
              AND firm_id = ?
              AND subject_person_id = ?
              AND relationship_type = ?
              AND related_person_id = ?
            """,
            (
                owner_id,
                firm_id,
                subject_person_id,
                relationship_type,
                related_person_id,
            ),
        ).fetchone()

        if duplicate is not None:
            raise GenealogyRelationshipServiceError(
                "Explicit genealogy relationship assertion "
                "already exists."
            )

        con.execute(
            """
            INSERT INTO genealogy_relationship_assertions (
                assertion_id,
                owner_id,
                firm_id,
                subject_person_id,
                relationship_type,
                related_person_id,
                trust_id,
                legacy_genealogy_id,
                assertion_status,
                assertion_basis,
                notes,
                created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assertion_id,
                owner_id,
                firm_id,
                subject_person_id,
                relationship_type,
                related_person_id,
                str(data.get("trust_id") or "").strip() or None,
                str(
                    data.get("legacy_genealogy_id") or ""
                ).strip() or None,
                "USER_ASSERTED",
                str(
                    data.get("assertion_basis") or ""
                ).strip() or None,
                str(data.get("notes") or "").strip() or None,
                str(
                    data.get("created_by") or ""
                ).strip() or None,
            ),
        )

        con.commit()

        row = con.execute(
            """
            SELECT *
            FROM genealogy_relationship_assertions
            WHERE assertion_id = ?
              AND owner_id = ?
              AND firm_id = ?
            """,
            (
                assertion_id,
                owner_id,
                firm_id,
            ),
        ).fetchone()

        if row is None:
            raise GenealogyRelationshipServiceError(
                "Created genealogy relationship assertion "
                "could not be reloaded."
            )

        return dict(row)

    except GenealogyRelationshipServiceError:
        con.rollback()
        raise
    except sqlite3.IntegrityError as exc:
        con.rollback()
        raise GenealogyRelationshipServiceError(
            f"Genealogy relationship assertion "
            f"could not be created: {exc}"
        ) from exc
    except sqlite3.Error as exc:
        con.rollback()
        raise GenealogyRelationshipServiceError(
            str(exc)
        ) from exc
    finally:
        con.close()


def get_genealogy_relationship_assertion(
    db_path: str | Path,
    assertion_id: str,
    owner_id: str,
    firm_id: str,
) -> dict[str, Any] | None:
    """Return one assertion only inside its owner/firm scope."""

    owner, firm = _scope(owner_id, firm_id)
    candidate = _required(assertion_id, "Assertion ID")

    con = _connection(db_path)

    try:
        row = con.execute(
            """
            SELECT *
            FROM genealogy_relationship_assertions
            WHERE assertion_id = ?
              AND owner_id = ?
              AND firm_id = ?
            """,
            (
                candidate,
                owner,
                firm,
            ),
        ).fetchone()

        return dict(row) if row else None

    except sqlite3.Error as exc:
        raise GenealogyRelationshipServiceError(
            str(exc)
        ) from exc
    finally:
        con.close()


def list_genealogy_relationship_assertions_for_person(
    db_path: str | Path,
    person_id: str,
    owner_id: str,
    firm_id: str,
) -> list[dict[str, Any]]:
    """List stored assertions involving one scoped canonical Person.

    This returns the stored directional rows as written. It does not
    generate reciprocal or inverse relationships.
    """

    owner, firm = _scope(owner_id, firm_id)
    person = _required(person_id, "Person ID")

    con = _connection(db_path)

    try:
        rows = con.execute(
            """
            SELECT *
            FROM genealogy_relationship_assertions
            WHERE owner_id = ?
              AND firm_id = ?
              AND (
                    subject_person_id = ?
                 OR related_person_id = ?
              )
            ORDER BY
                created_at,
                assertion_id
            """,
            (
                owner,
                firm,
                person,
                person,
            ),
        ).fetchall()

        return [dict(row) for row in rows]

    except sqlite3.Error as exc:
        raise GenealogyRelationshipServiceError(
            str(exc)
        ) from exc
    finally:
        con.close()
