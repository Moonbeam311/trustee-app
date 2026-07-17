"""Compliance Review authorization registry and actor-context helpers."""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping, Any


PERMISSION_TO_AUTHORITIES = MappingProxyType({
    "create_compliance_review": ("create_review",),
    "edit_compliance_review": ("edit_draft", "add_subject", "add_relationship"),
    "assign_compliance_reviewer": ("assign_reviewer",),
    "add_compliance_evidence": ("add_evidence",),
    "verify_compliance_evidence": ("verify_evidence",),
    "issue_compliance_findings": ("issue_findings",),
    "acknowledge_compliance_findings": ("acknowledge_findings",),
    "manage_compliance_remediation": ("assign_remediation",),
    "submit_compliance_remediation": ("submit_remediation",),
    "verify_compliance_remediation": ("verify_remediation",),
    "request_compliance_exception": ("request_exception",),
    "approve_compliance_exception": ("approve_exception",),
    "approve_compliance_review": ("approve_review",),
    "certify_compliance_review": ("certify_review",),
    "close_compliance_review": ("close_review",),
    "reopen_compliance_review": ("reopen_review",),
    "supersede_compliance_review": ("supersede_review",),
    "archive_compliance_review": ("archive_review",),
    "open_compliance_review": ("open_review",),
})

GLOBAL_READ_PERMISSIONS = frozenset({
    "view_all_compliance_reviews",
})

GLOBAL_MUTATION_PERMISSIONS = frozenset({
    "mutate_all_compliance_reviews",
})

INTENTIONALLY_SHARED_PERMISSION_MAPPINGS = MappingProxyType({
    "edit_compliance_review": ("edit_draft", "add_subject", "add_relationship"),
})

SENSITIVE_COMPLIANCE_PERMISSIONS = frozenset({
    "approve_compliance_exception",
    "approve_compliance_review",
    "certify_compliance_review",
    "reopen_compliance_review",
    "supersede_compliance_review",
    "archive_compliance_review",
    "mutate_all_compliance_reviews",
})

SEPARATION_RULES = MappingProxyType({
    "approve_review": (
        ("created_by", "creator_self_approval_denied"),
        ("approval_submitted_by", "submitter_self_approval_denied"),
    ),
    "verify_evidence": (
        ("evidence_submitted_by", "evidence_self_verification_denied"),
    ),
    "acknowledge_findings": (
        ("finding_issued_by", "finding_self_acknowledgement_denied"),
    ),
    "verify_remediation": (
        ("remediation_submitted_by", "remediation_self_verification_denied"),
    ),
    "approve_exception": (
        ("exception_requested_by", "exception_self_approval_denied"),
    ),
    "certify_review": (
        ("approved_by", "approver_self_certification_denied"),
    ),
    "reopen_review": (
        ("closed_by", "closer_self_reopen_denied"),
        ("certified_by", "certifier_self_reopen_denied"),
    ),
})

PERMISSIVE_WITH_AUDIT_RULES = MappingProxyType({
    "archive_review": (
        ("certified_by", "certifier_archival_overlap_requires_audit"),
    ),
})


def _normalize_values(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        values = (values,)
    try:
        iterator = iter(values)
    except TypeError:
        iterator = iter((values,))
    normalized = {
        str(value).strip()
        for value in iterator
        if str(value).strip()
    }
    return tuple(sorted(normalized))


def map_compliance_permissions(effective_permissions: Any) -> tuple[str, ...]:
    """Map database-backed permissions to canonical service authorities."""
    authorities: set[str] = set()
    for permission in _normalize_values(effective_permissions):
        authorities.update(PERMISSION_TO_AUTHORITIES.get(permission, ()))
    return tuple(sorted(authorities))


def source_permissions_for_authority(authority: str) -> tuple[str, ...]:
    canonical = str(authority or "").strip()
    return tuple(sorted(
        permission
        for permission, authorities in PERMISSION_TO_AUTHORITIES.items()
        if canonical in authorities
    ))


def canonical_authority_for_action(action: str, action_authorities: Mapping[str, str]) -> str:
    cleaned = str(action or "").strip()
    return str(action_authorities.get(cleaned, cleaned)).strip()


def validate_mapping_completeness(action_authorities: Mapping[str, str]) -> dict[str, Any]:
    canonical_service_authorities = {
        str(value).strip()
        for value in action_authorities.values()
        if str(value).strip()
    }
    mapped_authorities = {
        authority
        for authorities in PERMISSION_TO_AUTHORITIES.values()
        for authority in authorities
    }
    empty_permissions = [
        permission for permission in PERMISSION_TO_AUTHORITIES
        if not str(permission).strip()
    ]
    empty_authorities = [
        authority
        for authorities in PERMISSION_TO_AUTHORITIES.values()
        for authority in authorities
        if not str(authority).strip()
    ]
    unmapped_authorities = sorted(canonical_service_authorities - mapped_authorities)
    unknown_mapped_authorities = sorted(mapped_authorities - canonical_service_authorities)
    one_to_many = {
        permission: tuple(authorities)
        for permission, authorities in PERMISSION_TO_AUTHORITIES.items()
        if len(tuple(authorities)) > 1
    }
    unexpected_one_to_many = {
        permission: authorities
        for permission, authorities in one_to_many.items()
        if permission not in INTENTIONALLY_SHARED_PERMISSION_MAPPINGS
    }
    ambiguous_sources = {
        authority: source_permissions_for_authority(authority)
        for authority in mapped_authorities
        if len(source_permissions_for_authority(authority)) > 1
    }
    ok = not (
        empty_permissions
        or empty_authorities
        or unmapped_authorities
        or unknown_mapped_authorities
        or unexpected_one_to_many
        or ambiguous_sources
    )
    return {
        "ok": ok,
        "canonical_service_authorities": tuple(sorted(canonical_service_authorities)),
        "mapped_authorities": tuple(sorted(mapped_authorities)),
        "empty_permissions": tuple(empty_permissions),
        "empty_authorities": tuple(empty_authorities),
        "unmapped_authorities": tuple(unmapped_authorities),
        "unknown_mapped_authorities": tuple(unknown_mapped_authorities),
        "intentionally_shared_permission_mappings": dict(INTENTIONALLY_SHARED_PERMISSION_MAPPINGS),
        "unexpected_one_to_many": unexpected_one_to_many,
        "ambiguous_sources": ambiguous_sources,
    }


def build_test_actor_context(
    *,
    actor_id: str | None,
    username: str | None,
    actor_label: str | None = None,
    role: str | None = None,
    firm_id: str | None = None,
    effective_permissions: Any = (),
    authority_basis: str | None = "Step 25AB test authority basis",
    master_admin: bool = False,
    global_read: bool = False,
    global_mutation: bool = False,
) -> dict[str, Any]:
    permissions = _normalize_values(effective_permissions)
    authorities = map_compliance_permissions(permissions)
    return {
        "actor_id": actor_id,
        "username": username,
        "actor_label": actor_label or username or actor_id,
        "role": role,
        "firm_id": firm_id,
        "scope": {
            "firm_id": firm_id,
            "global_read": bool(global_read),
            "global_mutation": bool(global_mutation),
        },
        "effective_permissions": permissions,
        "authorities": authorities,
        "compliance_authorities": authorities,
        "authority_basis": authority_basis,
        "master_admin": bool(master_admin),
        "global_authority": False,
    }


def build_compliance_actor_context(
    *,
    username: str | None,
    session_role: str | None = None,
    session_firm_id: str | None = None,
    payload: Mapping[str, Any] | None = None,
    target_firm_id: str | None = None,
    master_admin: bool = False,
    effective_permissions: Any | None = None,
    user_lookup=None,
    permission_lookup=None,
) -> dict[str, Any]:
    """Build the live Compliance actor context from database permissions.

    Role, username, and Master Admin status are retained as attribution and
    audit metadata only. They do not grant Compliance mutation authority.
    """
    normalized_username = str(username or "").strip()
    if not normalized_username:
        raise PermissionError("authentication_required")

    if user_lookup is None or permission_lookup is None:
        from database.db import get_effective_permissions_for_user, get_user_by_username

        user_lookup = user_lookup or get_user_by_username
        permission_lookup = permission_lookup or get_effective_permissions_for_user

    user = user_lookup(normalized_username)
    if not user:
        raise PermissionError("authentication_required")

    def read_field(record, key, default=None):
        try:
            return record[key]
        except Exception:
            if isinstance(record, Mapping):
                return record.get(key, default)
            return default

    status = str(read_field(user, "status", "") or "").strip().lower()
    if status and status != "active":
        raise PermissionError("inactive_user")

    actor_id = read_field(user, "user_id") or normalized_username
    role = read_field(user, "role_name") or session_role
    firm_id = read_field(user, "firm_id") or session_firm_id
    if not firm_id:
        raise PermissionError("firm_scope_required")

    permissions = _normalize_values(
        effective_permissions
        if effective_permissions is not None
        else permission_lookup(normalized_username)
    )
    authorities = map_compliance_permissions(permissions)
    global_read = bool(set(permissions).intersection(GLOBAL_READ_PERMISSIONS))
    global_mutation = bool(set(permissions).intersection(GLOBAL_MUTATION_PERMISSIONS))
    authority_sources = {
        authority: source_permissions_for_authority(authority)
        for authority in authorities
    }

    return {
        "actor_id": actor_id,
        "username": normalized_username,
        "actor_label": normalized_username,
        "actor_role": role,
        "role": role,
        "firm_id": firm_id,
        "scope": {
            "firm_id": firm_id,
            "global": global_read,
            "global_read": global_read,
            "global_mutation": global_mutation,
            "target_firm_id": target_firm_id,
        },
        "effective_permissions": permissions,
        "authorities": authorities,
        "compliance_authorities": authorities,
        "authority_sources": authority_sources,
        "authority_basis": (payload or {}).get("authority_basis"),
        "master_admin": bool(master_admin),
        "global_authority": False,
    }


def evaluate_compliance_authority(
    actor_context: Mapping[str, Any] | None,
    action: str,
    *,
    target_firm_id: str | None = None,
    action_authorities: Mapping[str, str] | None = None,
    require_authority_basis: bool = True,
    require_global_mutation: bool = False,
) -> dict[str, Any]:
    actor_context = dict(actor_context or {})
    action_authorities = action_authorities or {}
    canonical = canonical_authority_for_action(action, action_authorities)
    actor_id = actor_context.get("actor_id")
    username = actor_context.get("username")
    actor_firm = actor_context.get("firm_id") or (actor_context.get("scope") or {}).get("firm_id")
    target_firm = target_firm_id or actor_firm
    effective_permissions = _normalize_values(actor_context.get("effective_permissions"))
    authorities = set(map_compliance_permissions(effective_permissions))
    scope = actor_context.get("scope") or {}
    source_permissions = source_permissions_for_authority(canonical)
    matched_sources = tuple(sorted(set(source_permissions).intersection(effective_permissions)))

    decision = {
        "allowed": False,
        "category": "permission_denied",
        "action": action,
        "canonical_authority": canonical,
        "source_permissions": matched_sources,
        "actor_id": actor_id,
        "username": username,
        "actor_role": actor_context.get("role"),
        "actor_firm_id": actor_firm,
        "target_firm_id": target_firm,
        "global_read": bool(scope.get("global_read")),
        "global_mutation": bool(scope.get("global_mutation")),
        "master_admin": bool(actor_context.get("master_admin")),
        "authority_basis_present": bool(str(actor_context.get("authority_basis") or "").strip()),
    }

    if not actor_id or not username:
        decision["category"] = "authentication_required"
        return decision
    if not actor_firm:
        decision["category"] = "firm_scope_required"
        return decision
    if target_firm and target_firm != actor_firm:
        if not scope.get("global_mutation") or not require_global_mutation:
            decision["category"] = "firm_scope_denied"
            return decision
    if canonical not in authorities:
        decision["category"] = "permission_denied"
        return decision
    if require_authority_basis and not decision["authority_basis_present"]:
        decision["category"] = "authority_basis_required"
        decision["authorized_but_invalid_documentation"] = True
        return decision

    decision["allowed"] = True
    decision["category"] = "allowed"
    return decision


def evaluate_compliance_separation(
    action: str,
    actor_id: str,
    record_context: Mapping[str, Any] | None,
    *,
    allow_certifier_archive_with_audit: bool = True,
) -> dict[str, Any]:
    record_context = dict(record_context or {})
    canonical = str(action or "").strip()
    for field, conflict_type in SEPARATION_RULES.get(canonical, ()):
        if actor_id and record_context.get(field) == actor_id:
            return {
                "allowed": False,
                "conflict_type": conflict_type,
                "actor_id": actor_id,
                "prior_actor_field": field,
                "prior_actor_id": record_context.get(field),
                "governed_override_required": True,
            }
    for field, conflict_type in PERMISSIVE_WITH_AUDIT_RULES.get(canonical, ()):
        if actor_id and record_context.get(field) == actor_id:
            return {
                "allowed": bool(allow_certifier_archive_with_audit),
                "conflict_type": conflict_type,
                "actor_id": actor_id,
                "prior_actor_field": field,
                "prior_actor_id": record_context.get(field),
                "governed_override_required": not allow_certifier_archive_with_audit,
                "audit_required": True,
            }
    return {
        "allowed": True,
        "conflict_type": None,
        "actor_id": actor_id,
        "prior_actor_field": None,
        "prior_actor_id": None,
        "governed_override_required": False,
    }
