"""Read-only TR-001 property-finalization orchestration.

This module composes canonical records.  It creates no facts and deliberately
keeps identification, possession, transfer, acceptance, execution and funding
as separate propositions.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

from services.services_property_attestations import (
    get_latest_property_identification_revision,
    list_current_property_attestations,
    list_property_attestations,
    list_property_identification_revisions,
)


UNAVAILABLE = "UNAVAILABLE"
UNRESOLVED = "UNRESOLVED"


class PropertyFinalizationReadError(RuntimeError):
    pass


def _connect(db_path):
    # mode=ro is the principal non-mutation guarantee (and fails if absent).
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _tables(connection):
    return {r[0] for r in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}


def _columns(connection, table):
    return {r[1] for r in connection.execute(f'PRAGMA table_info("{table}")')}


def _rows(connection, table, filters, *, order="", required_scope=()):
    if table not in _tables(connection):
        return []
    columns = _columns(connection, table)
    if not set(required_scope).issubset(columns):
        return []
    usable = [(key, value) for key, value in filters.items() if key in columns]
    if not usable:
        return []
    where = " AND ".join(f'"{key}"=?' for key, _ in usable)
    sql = f'SELECT * FROM "{table}" WHERE {where}'
    if order:
        sql += " ORDER BY " + order
    return [dict(r) for r in connection.execute(sql, [v for _, v in usable])]


def _one_by_id(connection, tables, identifier, scope):
    if not identifier:
        return None
    for table, candidate_keys in tables:
        if table not in _tables(connection):
            continue
        columns = _columns(connection, table)
        key = next((k for k in candidate_keys if k in columns), None)
        if key:
            scope_filters = {k: v for k, v in scope.items() if k in columns}
            where = [f'"{key}"=?'] + [f'"{k}"=?' for k in scope_filters]
            row = connection.execute(
                f'SELECT * FROM "{table}" WHERE {" AND ".join(where)}',
                (identifier, *scope_filters.values()),
            ).fetchone()
            if row:
                value = dict(row)
                value["source_table"] = table
                return value
    return None


def _truth(value):
    return value is True or value == 1 or str(value or "").strip().upper() in {
        "YES", "TRUE", "COMPLETE", "COMPLETED", "FINAL", "FINALIZED",
        "EXECUTED", "RECORDED", "ACCEPTED", "ACCEPTED_RECORDED",
        "FUNDED", "FUNDED_RECORDED",
    }


def _is_open(record):
    if not record:
        return False
    value = str(record.get("status") or record.get("state") or record.get("disposition") or "").upper()
    return value not in {"CLOSED", "COMPLETE", "COMPLETED", "RESOLVED", "APPROVED", "DISMISSED"}


def _transfer_complete(record):
    if not record:
        return False
    # Property acceptance requires the canonical transfer's explicit completion fact.
    return _truth(record.get("transfer_complete"))


def _acceptance_complete(record):
    return bool(record) and str(record.get("trustee_decision") or "").strip().upper() in {
        "ACCEPT", "ACCEPTED", "ACCEPTED_RECORDED", "APPROVED",
    }


def _funding_complete(record):
    return bool(record) and str(record.get("funding_state") or "").strip().upper() == "FUNDED_RECORDED"


def build_schedule_a_context(snapshot):
    """Return prospective canonical input; this never adopts or executes it."""
    prop = snapshot.get("property") or {}
    revision = snapshot.get("latest_identification_revision") or {}
    description = revision.get("resulting_identification_json") or prop.get("address_or_identifier") or prop.get("title_notes")
    eligible = bool(prop) and bool(revision or prop.get("property_name"))
    return {
        "output_status": "DRAFT_PROSPECTIVE" if eligible else "UNAVAILABLE",
        "schedule_a_draft_eligible": "YES" if eligible else "NO",
        "property_id": prop.get("property_id", UNAVAILABLE),
        "asset_name": prop.get("property_name") or prop.get("name") or UNAVAILABLE,
        "asset_description": description or UNAVAILABLE,
        "estimated_value": prop.get("estimated_value", UNAVAILABLE),
        "transfer_id": (snapshot.get("transfer_summary") or {}).get("transfer_id", UNAVAILABLE),
        "transfer_complete": "YES" if snapshot.get("transfer_complete") else "NO",
        "trustee_acceptance_complete": "YES" if snapshot.get("trustee_acceptance_complete") else "NO",
        "execution_complete": "YES" if snapshot.get("execution_complete") else "NO",
        "funding_complete": "YES" if snapshot.get("funding_complete") else "NO",
        "legal_effect": "NONE_INFERRED",
    }


def build_schedule_a_draft_text(snapshot):
    """Call the established formatter without persistence or status promotion."""
    from services.services_transfer import build_schedule_a_text

    context = build_schedule_a_context(snapshot)
    if context["schedule_a_draft_eligible"] != "YES":
        return {"context": context, "text": None}
    transfer = SimpleNamespace(
        asset_name=context["asset_name"], asset_description=context["asset_description"],
        estimated_value=context["estimated_value"], transfer_id=context["transfer_id"],
    )
    return {"context": context, "text": build_schedule_a_text(transfer)}


def get_property_finalization_snapshot(
    db_path, firm_id, trust_id, property_id, *, task_id=None,
    professional_review_issue_id=None,
):
    """Compose canonical property workflow facts using a read-only connection."""
    with _connect(db_path) as connection:
        tables = _tables(connection)
        if "properties" not in tables:
            raise PropertyFinalizationReadError("Canonical properties table is unavailable.")
        if not {"property_id", "trust_id", "firm_id"}.issubset(_columns(connection, "properties")):
            raise PropertyFinalizationReadError("Properties schema does not support firm/trust scoping.")
        properties = _rows(connection, "properties", {
            "property_id": property_id, "trust_id": trust_id, "firm_id": firm_id,
        }, required_scope=("property_id", "trust_id", "firm_id"))
        if not properties:
            raise PropertyFinalizationReadError("Property is not in the supplied firm/trust scope.")
        prop = properties[0]

        attestations = list_property_attestations(db_path, property_id, trust_id, firm_id)
        current_possession = list_current_property_attestations(
            db_path, property_id, trust_id, firm_id, "possession"
        )
        current_ownership = list_current_property_attestations(
            db_path, property_id, trust_id, firm_id, "ownership"
        )
        revisions = list_property_identification_revisions(db_path, property_id, trust_id, firm_id)
        latest = get_latest_property_identification_revision(db_path, property_id, trust_id, firm_id)
        media = _rows(connection, "media_records", {
            "related_entity_type": "property", "related_entity_id": property_id,
            "trust_id": trust_id, "firm_id": firm_id,
        }, order="created_at", required_scope=("trust_id", "firm_id"))
        custody = _rows(connection, "continuity_custody_log", {
            "property_id": property_id, "trust_id": trust_id, "firm_id": firm_id,
        })
        transfers = _rows(connection, "transfers", {
            "property_id": property_id, "trust_id": trust_id, "firm_id": firm_id,
        }, order="created_at DESC" if "transfers" in tables and "created_at" in _columns(connection, "transfers") else "",
            required_scope=("property_id", "trust_id", "firm_id"))
        transfer = transfers[0] if transfers else None

        acceptances = _rows(connection, "successor_acceptances", {
            "trust_id": trust_id, "firm_id": firm_id,
        }, order="recorded_at DESC" if "successor_acceptances" in tables and "recorded_at" in _columns(connection, "successor_acceptances") else "")
        acceptance = next((r for r in acceptances if _acceptance_complete(r)), acceptances[0] if acceptances else None)
        controls = _rows(connection, "trust_asset_control_determinations", {
            "firm_id": firm_id, "trust_id": trust_id, "asset_object_type": "PROPERTY",
            "asset_object_id": property_id,
        }, order="created_at DESC", required_scope=("firm_id", "trust_id", "asset_object_id"))
        control = controls[0] if controls else None

        trust_rows = _rows(connection, "trusts", {"trust_id": trust_id, "firm_id": firm_id})
        trust = trust_rows[0] if trust_rows else None
        execution_value = next((trust.get(k) for k in ("execution_status", "document_status", "status") if trust and trust.get(k) is not None), None)
        execution_complete = str(execution_value or "").upper() in {"EXECUTED", "EXECUTION_COMPLETE"}

        scope = {"firm_id": firm_id, "trust_id": trust_id}
        task = _one_by_id(connection, [
            ("execution_tasks", ("task_id", "id")),
            ("intake_followup_tasks", ("task_id", "id")),
        ], task_id, scope)
        pri = _one_by_id(connection, [("professional_review_issues", ("issue_id", "id"))], professional_review_issue_id, scope)

        transfer_done = _transfer_complete(transfer)
        acceptance_done = transfer_done and _acceptance_complete(transfer)
        funded = acceptance_done and _funding_complete(control)
        blockers = []
        if task_id and task is None: blockers.append({"type": "TASK", "id": task_id, "reason": "UNAVAILABLE"})
        elif _is_open(task): blockers.append({"type": "TASK", "id": task_id, "reason": "OPEN"})
        if professional_review_issue_id and pri is None: blockers.append({"type": "PROFESSIONAL_REVIEW", "id": professional_review_issue_id, "reason": "UNAVAILABLE"})
        elif _is_open(pri): blockers.append({"type": "PROFESSIONAL_REVIEW", "id": professional_review_issue_id, "reason": "OPEN"})
        if not execution_complete:
            blockers.append({"type": "DOCUMENT_EXECUTION", "reason": "AWAITING_EXECUTION" if trust else "UNAVAILABLE"})

        if funded: state = "FUNDED_ACTIVE_TRUST_PROPERTY"
        elif acceptance_done: state = "ACCEPTED"
        elif transfer_done: state = "PENDING_TRUSTEE_ACCEPTANCE"
        elif latest: state = "IDENTIFIED"
        elif custody: state = "CUSTODY_ONLY"
        else: state = "PROPOSED"
        if pri and _is_open(pri): state = "PROFESSIONAL_REVIEW_REQUIRED"

        snapshot = {
            "property": prop,
            "latest_identification_revision": latest,
            "identification_revision_count": len(revisions),
            "current_possession_attestations": current_possession,
            "current_ownership_attestations": current_ownership,
            "attestation_history_count": len(attestations),
            "property_evidence_media": media,
            "custody_summary": {"count": len(custody), "records": custody},
            "transfer_summary": transfer or {"state": UNAVAILABLE, "count": 0},
            "trustee_acceptance_summary": transfer or {"state": UNAVAILABLE},
            "fiduciary_authority_context": acceptance or {"state": UNAVAILABLE},
            "funding_ownership_control_summary": control or {"state": UNAVAILABLE},
            "execution_state": execution_value if execution_value is not None else UNAVAILABLE,
            "task_state": task or ({"state": UNAVAILABLE} if task_id else {"state": "NOT_SUPPLIED"}),
            "professional_review_issue_state": pri or ({"state": UNAVAILABLE} if professional_review_issue_id else {"state": "NOT_SUPPLIED"}),
            "transfer_complete": transfer_done,
            "trustee_acceptance_complete": acceptance_done,
            "funding_complete": funded,
            "execution_complete": execution_complete,
            "blocker_reasons": blockers,
            "derived_workflow_state": state,
            "source_provenance": {
                "property": [prop.get("property_id")],
                "identification_revisions": [r.get("revision_id") for r in revisions],
                "attestations": [r.get("attestation_id") for r in attestations],
                "media": [r.get("media_id") for r in media],
                "custody": [r.get("custody_event_id", r.get("id")) for r in custody],
                "transfer": [transfer.get("transfer_id")] if transfer else [],
                "acceptance": [acceptance.get("acceptance_id")] if acceptance else [],
                "asset_control": [control.get("asset_control_id")] if control else [],
            },
        }
        snapshot["schedule_a_draft_context"] = build_schedule_a_context(snapshot)
        return snapshot
