"""Explicit canonical Person-to-role/capacity link service.

This service records deliberate pointers from an existing canonical Person
identity to a caller-supplied institutional or operational role record.

It does not:
- search for or match people by name;
- infer role links;
- create Person identities;
- modify beneficiary, fiduciary, genealogy, or other role records;
- create family or genealogical relationships;
- verify that a role confers legal authority, entitlement, ownership,
  inheritance, authenticity, or other legal effect.

The role_type and role_record_id identify the intended external role record.
Their substantive validity remains governed by the owning role subsystem.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class PersonRoleLinkServiceError(RuntimeError):
    pass


def _required(value: Any, label: str) -> str:
    text = str(value or "").strip()

    if not text:
        raise PersonRoleLinkServiceError(
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


def create_person_role_link(
    db_path: str | Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Create one explicit scoped Person-to-role link."""

    data = dict(payload or {})

    link_id = _required(
        data.get("link_id"),
        "Role link ID",
    )
    person_id = _required(
        data.get("person_id"),
        "Person ID",
    )
    role_type = _required(
        data.get("role_type"),
        "Role type",
    )
    role_record_id = _required(
        data.get("role_record_id"),
        "Role record ID",
    )

    owner_id, firm_id = _scope(
        data.get("owner_id"),
        data.get("firm_id"),
    )

    con = _connection(db_path)

    try:
        person = con.execute(
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

        if person is None:
            raise PersonRoleLinkServiceError(
                "Scoped Person identity not found."
            )

        duplicate = con.execute(
            """
            SELECT link_id
            FROM person_role_links
            WHERE owner_id = ?
              AND firm_id = ?
              AND person_id = ?
              AND role_type = ?
              AND role_record_id = ?
            """,
            (
                owner_id,
                firm_id,
                person_id,
                role_type,
                role_record_id,
            ),
        ).fetchone()

        if duplicate is not None:
            raise PersonRoleLinkServiceError(
                "Explicit Person role link already exists."
            )

        con.execute(
            """
            INSERT INTO person_role_links (
                link_id,
                owner_id,
                firm_id,
                person_id,
                role_type,
                role_record_id,
                trust_id,
                capacity_label,
                notes,
                created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                link_id,
                owner_id,
                firm_id,
                person_id,
                role_type,
                role_record_id,
                str(data.get("trust_id") or "").strip() or None,
                str(data.get("capacity_label") or "").strip() or None,
                str(data.get("notes") or "").strip() or None,
                str(data.get("created_by") or "").strip() or None,
            ),
        )

        con.commit()

        row = con.execute(
            """
            SELECT *
            FROM person_role_links
            WHERE link_id = ?
              AND owner_id = ?
              AND firm_id = ?
            """,
            (
                link_id,
                owner_id,
                firm_id,
            ),
        ).fetchone()

        if row is None:
            raise PersonRoleLinkServiceError(
                "Created Person role link could not be reloaded."
            )

        return dict(row)

    except PersonRoleLinkServiceError:
        con.rollback()
        raise
    except sqlite3.IntegrityError as exc:
        con.rollback()
        raise PersonRoleLinkServiceError(
            f"Person role link could not be created: {exc}"
        ) from exc
    except sqlite3.Error as exc:
        con.rollback()
        raise PersonRoleLinkServiceError(str(exc)) from exc
    finally:
        con.close()


def get_person_role_link(
    db_path: str | Path,
    link_id: str,
    owner_id: str,
    firm_id: str,
) -> dict[str, Any] | None:
    """Return one link only inside its explicit owner/firm scope."""

    owner, firm = _scope(owner_id, firm_id)
    candidate = _required(link_id, "Role link ID")

    con = _connection(db_path)

    try:
        row = con.execute(
            """
            SELECT *
            FROM person_role_links
            WHERE link_id = ?
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
        raise PersonRoleLinkServiceError(str(exc)) from exc
    finally:
        con.close()


def list_person_role_links(
    db_path: str | Path,
    person_id: str,
    owner_id: str,
    firm_id: str,
) -> list[dict[str, Any]]:
    """List explicit role links for one scoped canonical Person."""

    owner, firm = _scope(owner_id, firm_id)
    person = _required(person_id, "Person ID")

    con = _connection(db_path)

    try:
        rows = con.execute(
            """
            SELECT *
            FROM person_role_links
            WHERE person_id = ?
              AND owner_id = ?
              AND firm_id = ?
            ORDER BY
                role_type,
                role_record_id,
                link_id
            """,
            (
                person,
                owner,
                firm,
            ),
        ).fetchall()

        return [dict(row) for row in rows]

    except sqlite3.Error as exc:
        raise PersonRoleLinkServiceError(str(exc)) from exc
    finally:
        con.close()


def list_role_person_links(
    db_path: str | Path,
    role_type: str,
    role_record_id: str,
    owner_id: str,
    firm_id: str,
) -> list[dict[str, Any]]:
    """List scoped Person links for one explicit role pointer."""

    owner, firm = _scope(owner_id, firm_id)
    role = _required(role_type, "Role type")
    record = _required(role_record_id, "Role record ID")

    con = _connection(db_path)

    try:
        rows = con.execute(
            """
            SELECT *
            FROM person_role_links
            WHERE role_type = ?
              AND role_record_id = ?
              AND owner_id = ?
              AND firm_id = ?
            ORDER BY person_id, link_id
            """,
            (
                role,
                record,
                owner,
                firm,
            ),
        ).fetchall()

        return [dict(row) for row in rows]

    except sqlite3.Error as exc:
        raise PersonRoleLinkServiceError(str(exc)) from exc
    finally:
        con.close()
