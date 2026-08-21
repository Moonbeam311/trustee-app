"""Read-only, bidirectional Trust–Continuity context adapter."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any
import sqlite3

import database.db as context_db
from services.services_intake_trust_bridge import get_continuity_profile
import services.services_trust_contract as trust_contract


TrustAuthorizationCheck = Callable[[str], bool]
ContinuityAuthorizationCheck = Callable[[str], bool]

LINKED = "LINKED"
UNLINKED = "UNLINKED"
NOT_FOUND_OR_NOT_ACCESSIBLE = "NOT_FOUND_OR_NOT_ACCESSIBLE"


class TrustContinuityContextError(RuntimeError):
    """Raised when the adapter cannot prove a safe read boundary."""


def _text(value: Any) -> str:
    return str(value or "").strip()


def _require_authorization(
    trust_check: TrustAuthorizationCheck | None,
    continuity_check: ContinuityAuthorizationCheck | None,
) -> tuple[TrustAuthorizationCheck, ContinuityAuthorizationCheck]:
    if trust_check is None or continuity_check is None:
        raise TrustContinuityContextError(
            "Explicit Trust and Continuity authorization checks are required."
        )
    return trust_check, continuity_check


def _require_context_schema(db_path: str | Path) -> None:
    connection = sqlite3.connect(str(Path(db_path).resolve()))
    connection.row_factory = sqlite3.Row
    try:
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='continuity_profiles'"
        ).fetchone()
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(continuity_profiles)"
            ).fetchall()
        }
    finally:
        connection.close()
    required = {"continuity_profile_id", "firm_id", "trust_id", "created_at"}
    if table is None or not required.issubset(columns):
        raise TrustContinuityContextError(
            "The context adapter requires an existing firm-scoped Continuity schema."
        )


def _trust_summary(row) -> dict[str, Any]:
    values = dict(row)
    return {
        key: values.get(key)
        for key in (
            "trust_id",
            "trust_name",
            "short_name",
            "trust_type",
            "status",
            "firm_id",
        )
    }


def _profile_summary(bundle: dict[str, Any]) -> dict[str, Any]:
    profile = bundle["profile"]
    readiness = bundle.get("readiness") or {}
    return {
        "continuity_profile_id": profile.get("continuity_profile_id"),
        "subject_name": profile.get("subject_name"),
        "subject_type": profile.get("subject_type"),
        "subject_capacities": profile.get("subject_capacities"),
        "status": profile.get("status"),
        "readiness": {
            "classification": readiness.get("classification"),
            "gap_count": readiness.get("gap_count"),
            "disclaimer": readiness.get("disclaimer"),
        },
        "provenance": {
            "intake_id": profile.get("intake_id"),
            "matter_id": profile.get("matter_id"),
            "bridge_id": profile.get("bridge_id"),
            "created_at": profile.get("created_at"),
            "updated_at": profile.get("updated_at"),
        },
    }


def resolve_continuity_contexts_for_trust(
    trust_id: Any,
    *,
    db_path: str | Path,
    trust_authorization_check: TrustAuthorizationCheck | None,
    continuity_authorization_check: ContinuityAuthorizationCheck | None,
) -> dict[str, Any] | None:
    """Return all authorized profiles linked to one canonical Trust.

    The schema permits zero or many profiles per Trust. Results are ordered by
    recorded creation time and profile identifier; no profile is promoted as
    canonical, latest, or primary.
    """
    trust_check, continuity_check = _require_authorization(
        trust_authorization_check, continuity_authorization_check
    )
    trust_key = _text(trust_id)
    trust = trust_contract.get_trust_by_id(
        trust_key, authorization_check=trust_check
    )
    if trust is None:
        return None
    _require_context_schema(db_path)
    firm_id = context_db.get_current_firm_id()
    connection = sqlite3.connect(str(Path(db_path).resolve()))
    connection.row_factory = sqlite3.Row
    try:
        profile_ids = [
            row["continuity_profile_id"]
            for row in connection.execute(
                """SELECT continuity_profile_id FROM continuity_profiles
                   WHERE firm_id=? AND trust_id=?
                   ORDER BY created_at, continuity_profile_id""",
                (firm_id, trust_key),
            ).fetchall()
        ]
    finally:
        connection.close()
    contexts = []
    for profile_id in profile_ids:
        if not continuity_check(profile_id):
            continue
        bundle = get_continuity_profile(db_path, profile_id, firm_id)
        if bundle is not None:
            contexts.append(_profile_summary(bundle))
    return {
        "contract_version": "V3-THO-CTX-1",
        "relationship_cardinality": "ZERO_OR_MANY",
        "relationship_state": LINKED if contexts else UNLINKED,
        "trust": _trust_summary(trust),
        "continuity_profiles": contexts,
        "continuity_profile_count": len(contexts),
        "mutation_performed": False,
    }


def resolve_trust_context_for_continuity(
    continuity_profile_id: Any,
    *,
    db_path: str | Path,
    trust_authorization_check: TrustAuthorizationCheck | None,
    continuity_authorization_check: ContinuityAuthorizationCheck | None,
) -> dict[str, Any] | None:
    """Return canonical Trust context for one accessible Continuity Profile."""
    trust_check, continuity_check = _require_authorization(
        trust_authorization_check, continuity_authorization_check
    )
    profile_id = _text(continuity_profile_id)
    if not profile_id or not continuity_check(profile_id):
        return None
    _require_context_schema(db_path)
    firm_id = context_db.get_current_firm_id()
    bundle = get_continuity_profile(db_path, profile_id, firm_id)
    if bundle is None:
        return None
    profile = bundle["profile"]
    trust_key = _text(profile.get("trust_id"))
    if not trust_key:
        return {
            "contract_version": "V3-THO-CTX-1",
            "relationship_state": UNLINKED,
            "continuity_profile": _profile_summary(bundle),
            "trust": None,
            "mutation_performed": False,
        }
    trust = trust_contract.get_trust_by_id(
        trust_key, authorization_check=trust_check
    )
    if trust is None:
        return {
            "contract_version": "V3-THO-CTX-1",
            "relationship_state": NOT_FOUND_OR_NOT_ACCESSIBLE,
            "continuity_profile": _profile_summary(bundle),
            "trust": None,
            "mutation_performed": False,
        }
    return {
        "contract_version": "V3-THO-CTX-1",
        "relationship_state": LINKED,
        "continuity_profile": _profile_summary(bundle),
        "trust": _trust_summary(trust),
        "mutation_performed": False,
    }
