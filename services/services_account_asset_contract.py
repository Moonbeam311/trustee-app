"""Canonical read-only Account/Asset aggregation for V3 consumers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import database.db as account_asset_db
import services.services_trust_contract as trust_contract


AuthorizationCheck = Callable[[str], bool]

ACCOUNT_FIELDS = (
    "account_id",
    "trust_id",
    "property_id",
    "account_type",
    "institution",
    "account_label",
    "masked_number",
    "purpose",
    "firm_id",
)
ASSET_FIELDS = (
    "property_id",
    "trust_id",
    "property_name",
    "property_type",
    "address_or_identifier",
    "acquisition_date",
    "status",
    "asset_class",
    "asset_subtype",
    "established_date",
    "effective_date",
    "review_date",
    "expiration_date",
    "responsible_party",
    "custodian",
    "continuity_classification",
    "custody_classification",
    "continuity_priority",
    "firm_id",
)


class AccountAssetReadContractError(RuntimeError):
    """Raised when a scoped read cannot be performed without mutation."""


def _text(value: Any) -> str:
    return str(value or "").strip()


def _require_scoped_tables() -> None:
    connection = account_asset_db.get_connection()
    try:
        for table, required in {
            "accounts": {"account_id", "trust_id", "firm_id"},
            "properties": {"property_id", "trust_id", "firm_id"},
        }.items():
            exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            columns = {
                row["name"]
                for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
            }
            if exists is None or not required.issubset(columns):
                raise AccountAssetReadContractError(
                    f"The {table} read boundary requires an existing firm-scoped schema."
                )
    finally:
        connection.close()


def _trust_context(trust_id: Any, authorization_check: AuthorizationCheck | None):
    scoped_id = _text(trust_id)
    if not scoped_id:
        return None
    return trust_contract.get_trust_by_id(
        scoped_id, authorization_check=authorization_check
    )


def _safe_row(row, fields: tuple[str, ...], source: str) -> dict[str, Any]:
    data = dict(row)
    result = {field: data.get(field) for field in fields}
    result["source"] = source
    return result


def list_trust_accounts(
    trust_id: Any, *, authorization_check: AuthorizationCheck | None
) -> list[dict[str, Any]]:
    """List safe account metadata for one authorized active-firm Trust."""
    trust = _trust_context(trust_id, authorization_check)
    if trust is None:
        return []
    _require_scoped_tables()
    scoped_id = _text(trust_id)
    connection = account_asset_db.get_connection()
    try:
        rows = connection.execute(
            "SELECT * FROM accounts WHERE trust_id=? AND firm_id=? ORDER BY account_id",
            (scoped_id, account_asset_db.get_current_firm_id()),
        ).fetchall()
    finally:
        connection.close()
    return [_safe_row(row, ACCOUNT_FIELDS, "accounts") for row in rows]


def get_trust_account(
    account_id: Any,
    trust_id: Any,
    *,
    authorization_check: AuthorizationCheck | None,
) -> dict[str, Any] | None:
    """Return one account only when its firm and Trust both match."""
    record_id = _text(account_id)
    trust = _trust_context(trust_id, authorization_check)
    if not record_id or trust is None:
        return None
    _require_scoped_tables()
    connection = account_asset_db.get_connection()
    try:
        row = connection.execute(
            """SELECT * FROM accounts
               WHERE account_id=? AND trust_id=? AND firm_id=?""",
            (record_id, _text(trust_id), account_asset_db.get_current_firm_id()),
        ).fetchone()
    finally:
        connection.close()
    return _safe_row(row, ACCOUNT_FIELDS, "accounts") if row else None


def list_trust_assets(
    trust_id: Any, *, authorization_check: AuthorizationCheck | None
) -> list[dict[str, Any]]:
    """List safe property/asset metadata for one authorized active-firm Trust."""
    trust = _trust_context(trust_id, authorization_check)
    if trust is None:
        return []
    _require_scoped_tables()
    scoped_id = _text(trust_id)
    connection = account_asset_db.get_connection()
    try:
        rows = connection.execute(
            """SELECT * FROM properties
               WHERE trust_id=? AND firm_id=? ORDER BY property_id""",
            (scoped_id, account_asset_db.get_current_firm_id()),
        ).fetchall()
    finally:
        connection.close()
    return [_safe_row(row, ASSET_FIELDS, "properties") for row in rows]


def get_trust_asset(
    property_id: Any,
    trust_id: Any,
    *,
    authorization_check: AuthorizationCheck | None,
) -> dict[str, Any] | None:
    """Return one property only when its firm and Trust both match."""
    record_id = _text(property_id)
    trust = _trust_context(trust_id, authorization_check)
    if not record_id or trust is None:
        return None
    _require_scoped_tables()
    connection = account_asset_db.get_connection()
    try:
        row = connection.execute(
            """SELECT * FROM properties
               WHERE property_id=? AND trust_id=? AND firm_id=?""",
            (record_id, _text(trust_id), account_asset_db.get_current_firm_id()),
        ).fetchone()
    finally:
        connection.close()
    return _safe_row(row, ASSET_FIELDS, "properties") if row else None


def aggregate_trust_inventory(
    trust_id: Any, *, authorization_check: AuthorizationCheck | None
) -> dict[str, Any] | None:
    """Build a source-attributed account/property snapshot without side effects."""
    trust = _trust_context(trust_id, authorization_check)
    if trust is None:
        return None
    accounts = list_trust_accounts(
        trust_id, authorization_check=authorization_check
    )
    assets = list_trust_assets(trust_id, authorization_check=authorization_check)
    asset_ids = {_text(asset.get("property_id")) for asset in assets}
    unresolved_links = sum(
        1
        for account in accounts
        if _text(account.get("property_id"))
        and _text(account.get("property_id")) not in asset_ids
    )
    return {
        "trust_id": _text(trust_id),
        "trust": {
            "trust_id": trust["trust_id"],
            "trust_name": trust["trust_name"] if "trust_name" in trust.keys() else None,
            "source": "trusts",
        },
        "accounts": accounts,
        "assets": assets,
        "summary": {
            "account_count": len(accounts),
            "asset_count": len(assets),
            "unresolved_account_property_references": unresolved_links,
            "scope": "active_firm_and_trust",
            "completeness": "accounts_and_properties_only",
        },
        "excluded_sources": [
            "ledger_entries",
            "chart_of_accounts",
            "continuity_custody_log",
            "archive_packets",
            "transfers",
        ],
    }
