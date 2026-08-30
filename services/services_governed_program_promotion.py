"""Canonical owner for governed Program promotion (V3-MOD-WLH-P07)."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

import database.db as promotion_db
from services.services_fiduciary_authority import (
    resolve_promotion_approval_capability,
)


PROMOTION_ACTION = "PROMOTE_SAVED_REVISION"
DESTINATION_FAMILY = "GOVERNED_PROGRAM_PROMOTION"
MUTATING_ROLES = {"Admin", "Trustee"}
READ_ROLES = MUTATING_ROLES | {"Viewer"}


class PromotionError(RuntimeError):
    status_code = 409


class PromotionBadRequest(PromotionError):
    status_code = 400


class PromotionForbidden(PromotionError):
    status_code = 403


class PromotionNotFound(PromotionError):
    status_code = 404


class PromotionConflict(PromotionError):
    status_code = 409


TrustCheck = Callable[[str], bool]


def _text(value: Any) -> str:
    return str(value or "").strip()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:20].upper()}"


def _hash(*parts: Any) -> str:
    material = " | ".join(_text(part) for part in parts)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _row(connection, query: str, parameters: tuple[Any, ...]):
    value = connection.execute(query, parameters).fetchone()
    return dict(value) if value else None


def _require_actor(connection, actor: str, role: str, firm_id: str) -> None:
    if role not in READ_ROLES or not actor or not firm_id:
        raise PromotionForbidden("promotion_scope_denied")
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "app_users" not in tables:
        raise PromotionForbidden("promotion_scope_denied")
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(app_users)").fetchall()
    }
    required = {"username", "role_name", "firm_id"}
    if not required.issubset(columns):
        raise PromotionForbidden("promotion_scope_denied")
    user = _row(
        connection,
        """SELECT username, role_name, firm_id, status FROM app_users
           WHERE lower(username)=lower(?) AND firm_id=? LIMIT 1""",
        (actor, firm_id),
    )
    if not user or user.get("role_name") != role or _text(user.get("status")).lower() not in {
        "", "active", "current"
    }:
        raise PromotionForbidden("promotion_scope_denied")


def _require_trust_assignment(
    connection, actor: str, role: str, trust_id: str, trust_check: TrustCheck
) -> None:
    if not trust_check(trust_id):
        raise PromotionForbidden("promotion_scope_denied")
    if role != "Trustee":
        return
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "user_roles" not in tables:
        raise PromotionForbidden("promotion_scope_denied")
    columns = {row[1] for row in connection.execute("PRAGMA table_info(user_roles)").fetchall()}
    if not {"trust_id", "full_name"}.issubset(columns):
        raise PromotionForbidden("promotion_scope_denied")
    assigned = connection.execute(
        "SELECT 1 FROM user_roles WHERE trust_id=? AND lower(full_name)=lower(?) LIMIT 1",
        (trust_id, actor),
    ).fetchone()
    if not assigned:
        raise PromotionForbidden("promotion_scope_denied")


def _resolve_scope(
    connection,
    *,
    workspace_id: str,
    program_id: str,
    revision_id: str | None,
    trust_id: str,
    firm_id: str,
    owner_id: str,
    actor: str,
    role: str,
    trust_check: TrustCheck,
) -> dict[str, Any]:
    _require_actor(connection, actor, role, firm_id)
    workspace = _row(
        connection,
        "SELECT * FROM workspaces WHERE workspace_id=? AND firm_id=? AND owner_id=?",
        (workspace_id, firm_id, owner_id),
    )
    program = _row(
        connection,
        """SELECT * FROM hub_programs
           WHERE program_id=? AND workspace_id=? AND firm_id=? AND owner_id=?""",
        (program_id, workspace_id, firm_id, owner_id),
    )
    trust = _row(
        connection,
        "SELECT * FROM trusts WHERE trust_id=? AND firm_id=?",
        (trust_id, firm_id),
    )
    if not workspace or not program or not trust:
        raise PromotionForbidden("promotion_scope_denied")
    _require_trust_assignment(connection, actor, role, trust_id, trust_check)
    revision = None
    if revision_id:
        revision = _row(
            connection,
            """SELECT * FROM hub_program_revisions
               WHERE revision_id=? AND program_id=?""",
            (revision_id, program_id),
        )
        if not revision:
            raise PromotionForbidden("promotion_scope_denied")
    return {"workspace": workspace, "program": program, "revision": revision, "trust": trust}


def _append_event(
    connection,
    *,
    request_row: dict[str, Any],
    event_type: str,
    prior_state: str | None,
    resulting_state: str,
    actor: str,
    authority_grant_id: str | None,
    destination_record_id: str | None,
    reason: str | None,
    identity: str,
) -> str:
    existing = _row(
        connection,
        "SELECT * FROM governed_program_promotion_events WHERE event_idempotency_key=?",
        (identity,),
    )
    if existing:
        return existing["event_id"]
    event_id = _id("P07EVT")
    connection.execute(
        """INSERT INTO governed_program_promotion_events (
             event_id, request_id, event_type, prior_state, resulting_state,
             firm_id, owner_id, workspace_id, program_id, program_revision_id,
             trust_id, actor_username, authority_grant_id, destination_record_id,
             reason, event_at, event_idempotency_key
           ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            event_id, request_row["request_id"], event_type, prior_state,
            resulting_state, request_row["firm_id"], request_row["owner_id"],
            request_row["workspace_id"], request_row["program_id"],
            request_row["program_revision_id"], request_row["trust_id"], actor,
            authority_grant_id, destination_record_id, reason, _now(), identity,
        ),
    )
    return event_id


def list_program_promotion_state(
    *, workspace_id: Any, program_id: Any, trust_id: Any, firm_id: Any,
    owner_id: Any, actor: Any, role: Any, trust_authorization_check: TrustCheck,
) -> dict[str, Any]:
    values = tuple(map(_text, (workspace_id, program_id, trust_id, firm_id, owner_id, actor, role)))
    workspace, program, trust, firm, owner, principal, actor_role = values
    connection = promotion_db.get_connection()
    try:
        scope = _resolve_scope(
            connection, workspace_id=workspace, program_id=program, revision_id=None,
            trust_id=trust, firm_id=firm, owner_id=owner, actor=principal,
            role=actor_role, trust_check=trust_authorization_check,
        )
        revisions = [dict(row) for row in connection.execute(
            "SELECT * FROM hub_program_revisions WHERE program_id=? ORDER BY revision_number",
            (program,),
        ).fetchall()]
        requests = [dict(row) for row in connection.execute(
            """SELECT * FROM governed_program_promotion_requests
               WHERE firm_id=? AND owner_id=? AND workspace_id=? AND program_id=? AND trust_id=?
               ORDER BY requested_at, request_id""", (firm, owner, workspace, program, trust)
        ).fetchall()]
        promotions = [dict(row) for row in connection.execute(
            """SELECT * FROM governed_program_promotions
               WHERE firm_id=? AND owner_id=? AND workspace_id=? AND program_id=? AND trust_id=?
               ORDER BY recorded_at, promotion_id""", (firm, owner, workspace, program, trust)
        ).fetchall()]
        events = [dict(row) for row in connection.execute(
            """SELECT event.* FROM governed_program_promotion_events event
               JOIN governed_program_promotion_requests request ON request.request_id=event.request_id
               WHERE request.firm_id=? AND request.owner_id=? AND request.workspace_id=?
                 AND request.program_id=? AND request.trust_id=?
               ORDER BY event.event_at, event.event_id""", (firm, owner, workspace, program, trust)
        ).fetchall()]
    finally:
        connection.close()
    return {**scope, "revisions": revisions, "requests": requests, "promotions": promotions, "events": events}


def create_promotion_request(
    *, workspace_id: Any, program_id: Any, revision_id: Any, trust_id: Any,
    firm_id: Any, owner_id: Any, actor: Any, role: Any, request_reason: Any,
    trust_authorization_check: TrustCheck,
) -> dict[str, Any]:
    values = tuple(map(_text, (workspace_id, program_id, revision_id, trust_id, firm_id, owner_id, actor, role)))
    workspace, program, revision, trust, firm, owner, principal, actor_role = values
    if actor_role not in MUTATING_ROLES or not revision or not trust:
        raise PromotionForbidden("promotion_scope_denied")
    identity = _hash(firm, owner, workspace, program, revision, trust, PROMOTION_ACTION, DESTINATION_FAMILY)
    source_lock = _hash(firm, owner, workspace, program, revision, PROMOTION_ACTION)
    connection = promotion_db.get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        scope = _resolve_scope(
            connection, workspace_id=workspace, program_id=program, revision_id=revision,
            trust_id=trust, firm_id=firm, owner_id=owner, actor=principal,
            role=actor_role, trust_check=trust_authorization_check,
        )
        existing = _row(connection, "SELECT * FROM governed_program_promotion_requests WHERE idempotency_key=?", (identity,))
        if existing:
            connection.commit()
            return existing
        conflict = _row(connection, "SELECT * FROM governed_program_promotion_requests WHERE source_lock_key=?", (source_lock,))
        if conflict:
            raise PromotionConflict("conflicting_promotion_target")
        now = _now()
        request_id = _id("P07REQ")
        request_row = {
            "request_id": request_id, "firm_id": firm, "owner_id": owner,
            "workspace_id": workspace, "program_id": program,
            "program_revision_id": revision, "trust_id": trust,
        }
        source_sha = hashlib.sha256(scope["revision"]["snapshot_json"].encode("utf-8")).hexdigest()
        connection.execute(
            """INSERT INTO governed_program_promotion_requests (
              request_id, firm_id, owner_id, workspace_id, program_id,
              program_revision_id, trust_id, source_revision_sha256,
              promotion_action, destination_family, request_status, requested_by,
              requested_at, request_reason, idempotency_key, source_lock_key,
              created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,'PENDING',?,?,?,?,?,?,?)""",
            (request_id, firm, owner, workspace, program, revision, trust, source_sha,
             PROMOTION_ACTION, DESTINATION_FAMILY, principal, now,
             _text(request_reason) or None, identity, source_lock, now, now),
        )
        _append_event(
            connection, request_row=request_row, event_type="REQUESTED",
            prior_state=None, resulting_state="PENDING", actor=principal,
            authority_grant_id=None, destination_record_id=None,
            reason=_text(request_reason) or None,
            identity=_hash(request_id, "REQUESTED", identity),
        )
        connection.commit()
        return _row(connection, "SELECT * FROM governed_program_promotion_requests WHERE request_id=?", (request_id,))
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _transition_decision(
    *, request_id: Any, outcome: str, actor: Any, role: Any, reason: Any,
    firm_id: Any, owner_id: Any, workspace_id: Any, program_id: Any,
    trust_authorization_check: TrustCheck,
) -> dict[str, Any]:
    request_key, principal, actor_role, firm, owner, workspace, program = tuple(
        map(_text, (request_id, actor, role, firm_id, owner_id, workspace_id, program_id))
    )
    if actor_role not in MUTATING_ROLES:
        raise PromotionForbidden("promotion_scope_denied")
    connection = promotion_db.get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        row = _row(connection, "SELECT * FROM governed_program_promotion_requests WHERE request_id=?", (request_key,))
        if not row or any(row[key] != expected for key, expected in (
            ("firm_id", firm), ("owner_id", owner), ("workspace_id", workspace), ("program_id", program)
        )):
            raise PromotionNotFound("promotion_request_not_found")
        _resolve_scope(
            connection, workspace_id=workspace, program_id=program,
            revision_id=row["program_revision_id"], trust_id=row["trust_id"],
            firm_id=firm, owner_id=owner, actor=principal, role=actor_role,
            trust_check=trust_authorization_check,
        )
        if row["requested_by"].lower() == principal.lower():
            raise PromotionForbidden("requester_cannot_approve")
        grant = resolve_promotion_approval_capability(principal, firm_id=firm, trust_id=row["trust_id"])
        if not grant:
            raise PromotionForbidden("approval_authority_required")
        target = "APPROVED" if outcome == "APPROVE" else "REJECTED"
        actor_field = "approved_by" if target == "APPROVED" else "rejected_by"
        if row["request_status"] == target and _text(row.get(actor_field)).lower() == principal.lower():
            connection.commit()
            return row
        if row["request_status"] != "PENDING":
            raise PromotionConflict("invalid_promotion_transition")
        identity = _hash(request_key, "APPROVE_OR_REJECT", grant["authority_grant_id"], target)
        opposite = "REJECTED" if target == "APPROVED" else "APPROVED"
        if _row(connection, "SELECT * FROM governed_program_promotion_events WHERE request_id=? AND event_type=?", (request_key, opposite)):
            raise PromotionConflict("conflicting_approval_outcome")
        now = _now()
        if target == "APPROVED":
            connection.execute(
                """UPDATE governed_program_promotion_requests SET request_status='APPROVED',
                   approved_by=?, approval_authority_id=?, approval_reason=?, approved_at=?, updated_at=?
                   WHERE request_id=? AND request_status='PENDING'""",
                (principal, grant["authority_grant_id"], _text(reason) or None, now, now, request_key),
            )
        else:
            connection.execute(
                """UPDATE governed_program_promotion_requests SET request_status='REJECTED',
                   rejected_by=?, rejection_reason=?, rejected_at=?, updated_at=?
                   WHERE request_id=? AND request_status='PENDING'""",
                (principal, _text(reason) or None, now, now, request_key),
            )
        _append_event(
            connection, request_row=row, event_type=target, prior_state="PENDING",
            resulting_state=target, actor=principal,
            authority_grant_id=grant["authority_grant_id"], destination_record_id=None,
            reason=_text(reason) or None, identity=identity,
        )
        connection.commit()
        return _row(connection, "SELECT * FROM governed_program_promotion_requests WHERE request_id=?", (request_key,))
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def approve_promotion_request(**kwargs) -> dict[str, Any]:
    return _transition_decision(outcome="APPROVE", **kwargs)


def reject_promotion_request(**kwargs) -> dict[str, Any]:
    return _transition_decision(outcome="REJECT", **kwargs)


def execute_promotion_request(
    *, request_id: Any, actor: Any, role: Any, firm_id: Any, owner_id: Any,
    workspace_id: Any, program_id: Any, trust_authorization_check: TrustCheck,
) -> dict[str, Any]:
    request_key, principal, actor_role, firm, owner, workspace, program = tuple(
        map(_text, (request_id, actor, role, firm_id, owner_id, workspace_id, program_id))
    )
    if actor_role not in MUTATING_ROLES:
        raise PromotionForbidden("promotion_scope_denied")
    connection = promotion_db.get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        row = _row(connection, "SELECT * FROM governed_program_promotion_requests WHERE request_id=?", (request_key,))
        if not row or any(row[key] != expected for key, expected in (
            ("firm_id", firm), ("owner_id", owner), ("workspace_id", workspace), ("program_id", program)
        )):
            raise PromotionNotFound("promotion_request_not_found")
        _resolve_scope(
            connection, workspace_id=workspace, program_id=program,
            revision_id=row["program_revision_id"], trust_id=row["trust_id"],
            firm_id=firm, owner_id=owner, actor=principal, role=actor_role,
            trust_check=trust_authorization_check,
        )
        existing = _row(connection, "SELECT * FROM governed_program_promotions WHERE request_id=?", (request_key,))
        if row["request_status"] == "EXECUTED" and existing:
            connection.commit()
            return existing
        if row["request_status"] != "APPROVED" or not row.get("approval_authority_id"):
            raise PromotionConflict("promotion_request_not_approved")
        identity = _hash(request_key, "PROMOTION_RECORDED", row["idempotency_key"])
        promotion_id = _id("P07GOV")
        now = _now()
        connection.execute(
            """INSERT INTO governed_program_promotions (
              promotion_id, governance_state, firm_id, owner_id, workspace_id,
              program_id, program_revision_id, trust_id, source_revision_sha256,
              request_id, approved_by, approval_authority_id, executed_by,
              recorded_at, idempotency_key
            ) VALUES (?,'GOVERNED_RECORDED',?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (promotion_id, firm, owner, workspace, program, row["program_revision_id"],
             row["trust_id"], row["source_revision_sha256"], request_key,
             row["approved_by"], row["approval_authority_id"], principal, now, identity),
        )
        event_id = _append_event(
            connection, request_row=row, event_type="PROMOTION_RECORDED",
            prior_state="APPROVED", resulting_state="EXECUTED", actor=principal,
            authority_grant_id=row["approval_authority_id"],
            destination_record_id=promotion_id, reason=None, identity=identity,
        )
        changed = connection.execute(
            """UPDATE governed_program_promotion_requests SET request_status='EXECUTED',
               executed_by=?, executed_at=?, destination_record_id=?, promotion_event_id=?, updated_at=?
               WHERE request_id=? AND request_status='APPROVED'""",
            (principal, now, promotion_id, event_id, now, request_key),
        ).rowcount
        if changed != 1:
            raise PromotionConflict("concurrent_promotion_conflict")
        connection.commit()
        return _row(connection, "SELECT * FROM governed_program_promotions WHERE promotion_id=?", (promotion_id,))
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_governed_promotion(
    *, promotion_id: Any, workspace_id: Any, program_id: Any, firm_id: Any,
    owner_id: Any, actor: Any, role: Any, trust_authorization_check: TrustCheck,
) -> dict[str, Any]:
    key = _text(promotion_id)
    connection = promotion_db.get_connection()
    try:
        promotion = _row(
            connection,
            """SELECT * FROM governed_program_promotions WHERE promotion_id=?
               AND firm_id=? AND owner_id=? AND workspace_id=? AND program_id=?""",
            (key, _text(firm_id), _text(owner_id), _text(workspace_id), _text(program_id)),
        )
        if not promotion:
            raise PromotionNotFound("promotion_result_not_found")
        _resolve_scope(
            connection, workspace_id=_text(workspace_id), program_id=_text(program_id),
            revision_id=promotion["program_revision_id"], trust_id=promotion["trust_id"],
            firm_id=_text(firm_id), owner_id=_text(owner_id), actor=_text(actor),
            role=_text(role), trust_check=trust_authorization_check,
        )
        request_row = _row(connection, "SELECT * FROM governed_program_promotion_requests WHERE request_id=?", (promotion["request_id"],))
        events = [dict(row) for row in connection.execute(
            "SELECT * FROM governed_program_promotion_events WHERE request_id=? ORDER BY event_at,event_id",
            (promotion["request_id"],),
        ).fetchall()]
        return {"promotion": promotion, "request": request_row, "events": events}
    finally:
        connection.close()
