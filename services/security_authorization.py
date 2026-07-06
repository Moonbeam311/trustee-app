"""
RBT-2C — Institutional Authorization Framework

Central authority helpers for Version 1.0.x stabilization.

This module does not replace every route at once.
It provides the controlled authorization vocabulary for:
- System Owner / Platform Administrator
- Trustee-Administrator
- firm-scoped execution access
"""

from functools import wraps
from flask import session, redirect, url_for, flash, abort


ROLE_SYSTEM_OWNER = "system_owner"
ROLE_PLATFORM_ADMIN = "platform_admin"
ROLE_MASTER_ADMIN = "master_admin"

ROLE_TRUSTEE_ADMIN = "trustee_admin"
ROLE_TRUSTEE_ADMINISTRATOR = "trustee_administrator"

LEGACY_ADMIN = "admin"
LEGACY_TRUSTEE = "trustee"
LEGACY_RESTRICTED_ADMIN = "restricted_admin"


SYSTEM_OWNER_ROLES = {
    ROLE_SYSTEM_OWNER,
    ROLE_PLATFORM_ADMIN,
    ROLE_MASTER_ADMIN,
}

TRUSTEE_ADMIN_ROLES = {
    ROLE_TRUSTEE_ADMIN,
    ROLE_TRUSTEE_ADMINISTRATOR,
    LEGACY_ADMIN,
    LEGACY_TRUSTEE,
    LEGACY_RESTRICTED_ADMIN,
}


def current_role():
    role = session.get("role")
    if role is None:
        return None
    return str(role).strip().lower()


def current_firm_id():
    return session.get("firm_id")


def current_username():
    return session.get("username")


def is_authenticated():
    return bool(current_username())


def is_system_owner():
    return current_role() in SYSTEM_OWNER_ROLES


def is_trustee_admin():
    return current_role() in TRUSTEE_ADMIN_ROLES or is_system_owner()


def require_authenticated_redirect():
    if not is_authenticated():
        flash("Please log in to continue.", "warning")
        return redirect(url_for("login"))
    return None


def require_system_owner_gate():
    gate = require_authenticated_redirect()
    if gate:
        return gate

    if not is_system_owner():
        flash("System Owner access required.", "warning")
        return abort(403)

    return None


def require_trustee_admin_gate():
    gate = require_authenticated_redirect()
    if gate:
        return gate

    if not is_trustee_admin():
        flash("Trustee-Administrator access required.", "warning")
        return abort(403)

    return None


def require_system_owner(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        gate = require_system_owner_gate()
        if gate:
            return gate
        return fn(*args, **kwargs)
    return wrapper


def require_trustee_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        gate = require_trustee_admin_gate()
        if gate:
            return gate
        return fn(*args, **kwargs)
    return wrapper


def firm_scope_matches(record_firm_id):
    if is_system_owner():
        return True

    if not record_firm_id:
        return True

    return str(record_firm_id) == str(current_firm_id())


def require_firm_scope_gate(record_firm_id):
    gate = require_trustee_admin_gate()
    if gate:
        return gate

    if not firm_scope_matches(record_firm_id):
        flash("This record is outside your assigned firm scope.", "warning")
        return abort(403)

    return None


def authorization_snapshot():
    return {
        "username": current_username(),
        "role": current_role(),
        "firm_id": current_firm_id(),
        "is_system_owner": is_system_owner(),
        "is_trustee_admin": is_trustee_admin(),
    }
