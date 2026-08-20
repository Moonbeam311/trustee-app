"""Canonical, read-only Trust boundary for reusable V3 consumers.

Persistence remains owned by :mod:`database.db`.  Callers must supply their
existing authorization decision as a callback; this module never interprets a
username or role label as authority.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import database.db as trust_db


AuthorizationCheck = Callable[[str], bool]


class TrustReadContractError(RuntimeError):
    """Raised when the read boundary cannot operate safely."""


def _normalized_trust_id(trust_id: Any) -> str:
    return str(trust_id or "").strip()


def _authorization_allows(
    trust_id: str, authorization_check: AuthorizationCheck | None
) -> bool:
    if authorization_check is None:
        raise TrustReadContractError("An explicit Trust authorization check is required.")
    return bool(authorization_check(trust_id))


def _require_firm_scoped_schema() -> None:
    """Fail closed instead of invoking the DB layer's legacy schema mutation."""
    connection = trust_db.get_connection()
    try:
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='trusts'"
        ).fetchone()
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(trusts)").fetchall()
        }
    finally:
        connection.close()

    if table is None or "firm_id" not in columns:
        raise TrustReadContractError(
            "The Trust read boundary requires an existing firm-scoped trusts schema."
        )


def get_trust_by_id(
    trust_id: Any, *, authorization_check: AuthorizationCheck | None
):
    """Return the active-firm Trust row, or ``None`` for denied/missing input.

    The shared denied/not-found result prevents this boundary from disclosing
    whether an inaccessible Trust exists in another firm.
    """
    normalized_id = _normalized_trust_id(trust_id)
    if not normalized_id or not _authorization_allows(
        normalized_id, authorization_check
    ):
        return None
    _require_firm_scoped_schema()
    return trust_db.get_trust_by_id(normalized_id)


def list_trusts(*, authorization_check: AuthorizationCheck | None):
    """Return authorized Trust rows from the active firm's scoped DB listing."""
    if authorization_check is None:
        raise TrustReadContractError("An explicit Trust authorization check is required.")
    _require_firm_scoped_schema()
    return [
        trust
        for trust in trust_db.get_all_trusts()
        if authorization_check(str(trust["trust_id"]))
    ]


def trust_is_accessible(
    trust_id: Any, *, authorization_check: AuthorizationCheck | None
) -> bool:
    """Return whether the Trust is both authorized and visible in the active firm."""
    return (
        get_trust_by_id(trust_id, authorization_check=authorization_check) is not None
    )
