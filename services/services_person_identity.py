"""Canonical Person identity service boundary.

This service operates only on explicit Person identity records.

It does not:
- infer identity from matching names;
- merge beneficiary, fiduciary, genealogy, signature, or other role records;
- establish genealogical relationships;
- establish legal authority, entitlement, ownership, inheritance, or status;
- perform automatic role/capacity linkage.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class PersonIdentityServiceError(RuntimeError):
    pass


def _scope(owner_id: str, firm_id: str) -> tuple[str, str]:
    owner = str(owner_id or "").strip()
    firm = str(firm_id or "").strip()

    if not owner:
        raise PersonIdentityServiceError(
            "Person owner scope is required."
        )

    if not firm:
        raise PersonIdentityServiceError(
            "Person firm scope is required."
        )

    return owner, firm


def _connection(db_path: str | Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(Path(db_path)))
    con.row_factory = sqlite3.Row
    return con


def create_person_identity(
    db_path: str | Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Create one explicit canonical Person identity record."""

    data = dict(payload or {})

    person_id = str(data.get("person_id") or "").strip()
    display_name = str(data.get("display_name") or "").strip()
    owner_id, firm_id = _scope(
        data.get("owner_id"),
        data.get("firm_id"),
    )

    if not person_id:
        raise PersonIdentityServiceError(
            "Person ID is required."
        )

    if not display_name:
        raise PersonIdentityServiceError(
            "Person display name is required."
        )

    con = _connection(db_path)

    try:
        con.execute(
            """
            INSERT INTO persons (
                person_id,
                owner_id,
                firm_id,
                display_name,
                sort_name,
                notes,
                created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                person_id,
                owner_id,
                firm_id,
                display_name,
                str(data.get("sort_name") or "").strip() or None,
                str(data.get("notes") or "").strip() or None,
                str(data.get("created_by") or "").strip() or None,
            ),
        )
        con.commit()

        row = con.execute(
            """
            SELECT *
            FROM persons
            WHERE person_id = ?
              AND owner_id = ?
              AND firm_id = ?
            """,
            (person_id, owner_id, firm_id),
        ).fetchone()

        if row is None:
            raise PersonIdentityServiceError(
                "Created Person identity could not be reloaded."
            )

        return dict(row)

    except sqlite3.IntegrityError as exc:
        con.rollback()
        raise PersonIdentityServiceError(
            f"Person identity could not be created: {exc}"
        ) from exc
    except sqlite3.Error as exc:
        con.rollback()
        raise PersonIdentityServiceError(str(exc)) from exc
    finally:
        con.close()


def get_person_identity(
    db_path: str | Path,
    person_id: str,
    owner_id: str,
    firm_id: str,
) -> dict[str, Any] | None:
    """Return one Person only inside the explicit owner/firm scope."""

    owner, firm = _scope(owner_id, firm_id)
    candidate = str(person_id or "").strip()

    if not candidate:
        raise PersonIdentityServiceError(
            "Person ID is required."
        )

    con = _connection(db_path)

    try:
        row = con.execute(
            """
            SELECT *
            FROM persons
            WHERE person_id = ?
              AND owner_id = ?
              AND firm_id = ?
            """,
            (candidate, owner, firm),
        ).fetchone()

        return dict(row) if row else None
    except sqlite3.Error as exc:
        raise PersonIdentityServiceError(str(exc)) from exc
    finally:
        con.close()


def list_person_identities(
    db_path: str | Path,
    owner_id: str,
    firm_id: str,
) -> list[dict[str, Any]]:
    """List canonical Person records for one owner/firm scope."""

    owner, firm = _scope(owner_id, firm_id)

    con = _connection(db_path)

    try:
        rows = con.execute(
            """
            SELECT *
            FROM persons
            WHERE owner_id = ?
              AND firm_id = ?
            ORDER BY
                COALESCE(NULLIF(sort_name, ''), display_name),
                display_name,
                person_id
            """,
            (owner, firm),
        ).fetchall()

        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        raise PersonIdentityServiceError(str(exc)) from exc
    finally:
        con.close()
