"""Canonical read-only descriptor for recorded transfer archive packages."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import database.db as archive_db
import services.services_execution_contract as execution_contract
import services.services_trust_contract as trust_contract


AuthorizationCheck = Callable[[str], bool]
REQUIRED_TABLES = {
    "transfer_archive_handoff",
    "transfer_archive_handoff_corrections",
    "archive_export_history",
}


class ArchiveContractError(RuntimeError):
    """Raised when an archive descriptor cannot be read safely."""


def _text(value: Any) -> str:
    return str(value or "").strip()


def _require_schema() -> None:
    """Fail closed without invoking legacy schema-creation helpers."""
    connection = archive_db.get_connection()
    try:
        present = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        connection.close()
    missing = sorted(REQUIRED_TABLES - present)
    if missing:
        raise ArchiveContractError(
            "Required archive descriptor schema is unavailable: " + ", ".join(missing)
        )


def _source_context(
    transfer_id: Any,
    trust_id: Any,
    authorization_check: AuthorizationCheck | None,
) -> dict[str, Any] | None:
    trust_key = _text(trust_id)
    if trust_contract.get_trust_by_id(
        trust_key, authorization_check=authorization_check
    ) is None:
        return None
    return execution_contract.get_transfer(
        transfer_id, trust_key, authorization_check=authorization_check
    )


def describe_transfer_archive_package(
    transfer_id: Any,
    trust_id: Any,
    *,
    authorization_check: AuthorizationCheck | None,
    handoff_id: Any = None,
) -> dict[str, Any] | None:
    """Describe recorded handoff/package metadata without producing an export.

    If ``handoff_id`` is omitted, the latest recorded handoff for the scoped
    transfer is described. Missing, denied, and mismatched sources share the
    same ``None`` result.
    """
    transfer = _source_context(transfer_id, trust_id, authorization_check)
    if transfer is None:
        return None
    _require_schema()
    firm_id = archive_db.get_current_firm_id()
    transfer_key = _text(transfer_id)
    handoff_key = _text(handoff_id)
    connection = archive_db.get_connection()
    try:
        if handoff_key:
            handoff = connection.execute(
                """SELECT * FROM transfer_archive_handoff
                   WHERE handoff_id=? AND transfer_id=? AND trust_id=? AND firm_id=?""",
                (handoff_key, transfer_key, _text(trust_id), firm_id),
            ).fetchone()
        else:
            handoff = connection.execute(
                """SELECT * FROM transfer_archive_handoff
                   WHERE transfer_id=? AND trust_id=? AND firm_id=?
                   ORDER BY created_at DESC, id DESC LIMIT 1""",
                (transfer_key, _text(trust_id), firm_id),
            ).fetchone()
        if handoff is None:
            return None
        corrections = [
            dict(row)
            for row in connection.execute(
                """SELECT * FROM transfer_archive_handoff_corrections
                   WHERE handoff_id=? AND transfer_id=? AND trust_id=? AND firm_id=?
                   ORDER BY created_at, id""",
                (handoff["handoff_id"], transfer_key, _text(trust_id), firm_id),
            ).fetchall()
        ]
        exports = [
            dict(row)
            for row in connection.execute(
                """SELECT * FROM archive_export_history
                   WHERE transfer_id=? AND trust_id=? AND firm_id=?
                   ORDER BY generated_at, id""",
                (transfer_key, _text(trust_id), firm_id),
            ).fetchall()
        ]
    finally:
        connection.close()

    handoff_record = dict(handoff)
    items = [
        {
            "item_type": "handoff_record",
            "item_id": handoff_record["handoff_id"],
            "status": handoff_record.get("archive_status"),
            "present": True,
        }
    ]
    items.extend(
        {
            "item_type": "handoff_correction",
            "item_id": record.get("correction_id"),
            "status": record.get("corrected_archive_status"),
            "present": True,
        }
        for record in corrections
    )
    items.extend(
        {
            "item_type": "recorded_export",
            "item_id": record.get("export_id"),
            "status": "recorded",
            "present": True,
            "filename": record.get("filename"),
        }
        for record in exports
    )
    integrity = [
        {
            "export_id": record.get("export_id"),
            "hash_value": record.get("export_hash"),
            "hash_semantics": "recorded_export_hash",
            "verified_by_descriptor": False,
        }
        for record in exports
        if _text(record.get("export_hash"))
    ]
    return {
        "contract_version": "V3-SVC-ARCH-1",
        "package_id": handoff_record["handoff_id"],
        "package_type": "transfer_archive_handoff_descriptor",
        "source": {
            "object_type": "transfer",
            "object_id": transfer_key,
            "trust_id": _text(trust_id),
            "firm_id": firm_id,
        },
        "handoff": handoff_record,
        "corrections": corrections,
        "export_references": exports,
        "items": items,
        "inventory": {
            "present_count": len(items),
            "missing_count": 0,
            "missing_items": [],
            "required_item_policy": "NOT DOCUMENTED",
        },
        "integrity": {
            "seal_reference": handoff_record.get("seal_reference"),
            "recorded_hashes": integrity,
            "content_verified": False,
            "manifest_hash": "NOT DOCUMENTED",
            "control_hash": "not_applicable",
        },
        "finalization": {
            "recorded_status": handoff_record.get("archive_status"),
            "semantics": "handoff_state_not_package_certification",
            "certified_by_descriptor": False,
        },
        "provenance": {
            "handoff_by": handoff_record.get("handoff_by"),
            "handoff_capacity": handoff_record.get("handoff_capacity"),
            "created_at": handoff_record.get("created_at"),
            "correction_count": len(corrections),
            "export_reference_count": len(exports),
        },
        "boundaries": {
            "manifest_generated": False,
            "output_generated": False,
            "handoff_created": False,
            "export_history_written": False,
            "archive_finalized": False,
            "recovery_topology_read": False,
        },
        "mutation_performed": False,
    }


def list_transfer_archive_packages(
    trust_id: Any, *, authorization_check: AuthorizationCheck | None
) -> list[dict[str, Any]]:
    """List minimal handoff descriptors in exact active-firm/Trust scope."""
    trust_key = _text(trust_id)
    if trust_contract.get_trust_by_id(
        trust_key, authorization_check=authorization_check
    ) is None:
        return []
    _require_schema()
    connection = archive_db.get_connection()
    try:
        rows = connection.execute(
            """SELECT h.handoff_id, h.transfer_id, h.trust_id, h.firm_id,
                      h.archive_status, h.custody_classification, h.seal_reference,
                      h.handoff_by, h.handoff_capacity, h.created_at
               FROM transfer_archive_handoff h
               JOIN transfers t ON t.transfer_id=h.transfer_id
                 AND t.trust_id=h.trust_id AND t.firm_id=h.firm_id
               WHERE h.trust_id=? AND h.firm_id=? ORDER BY h.created_at, h.id""",
            (trust_key, archive_db.get_current_firm_id()),
        ).fetchall()
    finally:
        connection.close()
    return [
        {
            "package_id": row["handoff_id"],
            "package_type": "transfer_archive_handoff_descriptor",
            "source_object_type": "transfer",
            "source_object_id": row["transfer_id"],
            "trust_id": row["trust_id"],
            "firm_id": row["firm_id"],
            "recorded_status": row["archive_status"],
            "custody_classification": row["custody_classification"],
            "seal_reference": row["seal_reference"],
            "created_at": row["created_at"],
            "mutation_performed": False,
        }
        for row in rows
    ]
