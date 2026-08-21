"""TPD-1C HTTP boundary. All writes are explicit, CSRF-protected, and firm-scoped."""

import os
from functools import wraps
from pathlib import Path

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from flask_wtf.csrf import generate_csrf

from database.db import get_roles_by_trust_id, user_has_effective_permission
from services.services_handoff_read_aggregate import build_trust_successor_handoff_context
from services.services_intake_trust_bridge import (
    BridgeError, FORMATION_FIELD_CONTROLS, REQUIRED_FIELDS, acknowledge_source_rebase, add_continuity_record, confirm_bridge, create_continuity_profile,
    create_or_resume_trust, evaluate_eligibility, get_bridge, get_continuity_profile,
    link_continuity_profile, prepare_bridge, transition_activation_plan,
)

tpd1c = Blueprint("tpd1c", __name__)


@tpd1c.app_context_processor
def _provenance_helpers():
    def formation_provenance(trust_id):
        if not trust_id or not _firm():
            return None
        import sqlite3
        connection = sqlite3.connect(str(_db_path()))
        connection.row_factory = sqlite3.Row
        try:
            bridge = connection.execute("""SELECT b.*,r.title recommendation_title,r.reason recommendation_reason
                FROM intake_trust_formation_bridges b JOIN intake_document_recommendations r ON r.id=b.recommendation_id
                WHERE b.firm_id=? AND b.trust_id=? LIMIT 1""", (_firm(), trust_id)).fetchone()
            if not bridge:
                return None
            profiles = connection.execute("SELECT continuity_profile_id,subject_name FROM continuity_profiles WHERE firm_id=? AND (trust_id=? OR bridge_id=?)", (_firm(), trust_id, bridge["bridge_id"])).fetchall()
            deviations = connection.execute("SELECT COUNT(*) FROM intake_trust_formation_field_proposals WHERE bridge_id=? AND deviation_indicator=1", (bridge["bridge_id"],)).fetchone()[0]
            proposals = connection.execute("""
                SELECT target_field,confirmed_value,source_classification,
                       deviation_indicator,deviation_reason
                FROM intake_trust_formation_field_proposals
                WHERE bridge_id=? ORDER BY target_step,proposal_id
            """, (bridge["bridge_id"],)).fetchall()
            return {
                "bridge": dict(bridge),
                "profiles": [dict(row) for row in profiles],
                "proposals": [dict(row) for row in proposals],
                "deviation_count": deviations,
            }
        except sqlite3.OperationalError:
            return None
        finally:
            connection.close()
    return {
        "formation_provenance": formation_provenance,
        "tpd1c_csrf_token": generate_csrf,
    }


def _db_path():
    return Path(os.environ.get("DB_PATH", Path(__file__).resolve().parent / "trustee_app.db")).resolve()


def _actor():
    return session.get("username") or session.get("user_id") or ""


def _firm():
    return session.get("firm_id") or ""


def permission_required(name):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if not _actor():
                return redirect(url_for("login"))
            if not user_has_effective_permission(_actor(), name):
                abort(403)
            if not _firm():
                abort(403)
            return func(*args, **kwargs)
        return wrapped
    return decorator


def _operator_can_read_trust(trust_id):
    """Mirror the established Trust-detail assignment policy in this blueprint."""
    if not _actor() or not _firm():
        return False
    if session.get("is_master_admin") or session.get("role") == "Admin":
        return True
    username = _actor().strip().lower()
    return any(
        str(row["full_name"] or "").strip().lower() == username
        for row in get_roles_by_trust_id(trust_id)
    )


@tpd1c.route("/trust/<trust_id>/successor-handoff")
@permission_required("view_dashboard")
def successor_handoff_workspace(trust_id):
    """Render the canonical successor-handoff aggregate without mutation."""
    trust_check = lambda candidate: candidate == trust_id and _operator_can_read_trust(candidate)
    continuity_check = lambda profile_id: get_continuity_profile(
        _db_path(), profile_id, _firm()
    ) is not None
    aggregate = build_trust_successor_handoff_context(
        trust_id,
        db_path=_db_path(),
        trust_authorization_check=trust_check,
        continuity_authorization_check=continuity_check,
        fiduciary_authorization_check=lambda _fiduciary_id, candidate_trust: (
            candidate_trust == trust_id and trust_check(trust_id)
        ),
        acceptance_authorization_check=lambda _acceptance_id, candidate_trust: (
            candidate_trust == trust_id and trust_check(trust_id)
        ),
        governance_authorization_check=trust_check,
        execution_id=request.args.get("execution_id"),
        transfer_id=request.args.get("transfer_id"),
    )
    if aggregate is None:
        abort(404)
    return render_template("tpd1c/successor_handoff.html", handoff=aggregate)


@tpd1c.route("/intake/<intake_id>/recommendations/declaration_of_trust/trust-formation-bridge", methods=["GET", "POST"])
@permission_required("create_trust")
def bridge_prepare(intake_id):
    try:
        if request.method == "POST":
            bridge = prepare_bridge(_db_path(), _firm(), intake_id, _actor(), request.form.get("matter_id") or None)
            return redirect(url_for("tpd1c.bridge_detail", bridge_id=bridge["bridge_id"]))
        eligibility = evaluate_eligibility(_db_path(), _firm(), intake_id)
        return render_template("tpd1c/bridge_prepare.html", intake_id=intake_id, eligibility=eligibility)
    except BridgeError as exc:
        flash(str(exc), "warning")
        return redirect(url_for("intake_document_recommendations", intake_id=intake_id))


@tpd1c.route("/trust-formation-bridges/<bridge_id>")
@permission_required("create_trust")
def bridge_detail(bridge_id):
    bundle = get_bridge(_db_path(), bridge_id, _firm())
    if not bundle:
        abort(404)
    return render_template(
        "tpd1c/bridge_detail.html",
        field_controls=FORMATION_FIELD_CONTROLS,
        required_fields=set(REQUIRED_FIELDS),
        **bundle,
    )


@tpd1c.route("/trust-formation-bridges/<bridge_id>/acknowledge-source", methods=["POST"])
@permission_required("create_trust")
def bridge_acknowledge_source(bridge_id):
    try:
        acknowledge_source_rebase(_db_path(), bridge_id, _firm(), _actor())
        flash("Metadata-only source change acknowledged and recorded. Formation values still require explicit confirmation.", "success")
    except BridgeError as exc:
        flash(str(exc), "warning")
    return redirect(url_for("tpd1c.bridge_detail", bridge_id=bridge_id))


@tpd1c.route("/trust-formation-bridges/<bridge_id>/continuity/link", methods=["POST"])
@permission_required("edit_trust")
def bridge_link_continuity(bridge_id):
    try:
        link_continuity_profile(_db_path(), request.form.get("continuity_profile_id", ""), bridge_id, _firm(), _actor())
        flash("Existing Continuity Profile linked with an audit event.", "success")
    except BridgeError as exc:
        flash(str(exc), "warning")
    return redirect(url_for("tpd1c.bridge_detail", bridge_id=bridge_id))


@tpd1c.route("/trust-formation-bridges/<bridge_id>/confirm", methods=["POST"])
@permission_required("create_trust")
def bridge_confirm(bridge_id):
    bundle = get_bridge(_db_path(), bridge_id, _firm())
    if not bundle:
        abort(404)
    values = {row["target_field"]: request.form.get(row["target_field"], "") for row in bundle["proposals"]}
    reasons = {row["target_field"]: request.form.get(f"deviation_reason__{row['target_field']}", "") for row in bundle["proposals"]}
    confirmed_fields = request.form.getlist("confirmed_fields")
    try:
        confirm_bridge(_db_path(), bridge_id, _firm(), values, _actor(), reasons, confirmed_fields)
        flash("Formation values confirmed. This is not legal or execution approval.", "success")
    except BridgeError as exc:
        flash(str(exc), "warning")
    return redirect(url_for("tpd1c.bridge_detail", bridge_id=bridge_id))


@tpd1c.route("/trust-formation-bridges/<bridge_id>/create-or-resume", methods=["POST"])
@permission_required("create_trust")
def bridge_create_or_resume(bridge_id):
    try:
        result = create_or_resume_trust(_db_path(), bridge_id, _firm(), _actor())
        flash("Existing trust resumed." if result["resumed"] else "Draft trust created from confirmed values.", "success")
        return redirect(url_for("trust_detail", trust_id=result["trust_id"]))
    except BridgeError as exc:
        flash(str(exc), "warning")
        return redirect(url_for("tpd1c.bridge_detail", bridge_id=bridge_id))


@tpd1c.route("/continuity-profiles/new", methods=["GET", "POST"])
@permission_required("edit_trust")
def continuity_new():
    if request.method == "POST":
        try:
            profile_id = create_continuity_profile(
                _db_path(), _firm(), request.form.get("subject_name", ""), request.form.get("subject_type", "person"),
                request.form.get("subject_capacities", ""), request.form.get("primary_purpose", ""), _actor(),
                intake_id=request.form.get("intake_id") or None, matter_id=request.form.get("matter_id") or None,
                bridge_id=request.form.get("bridge_id") or None, trust_id=request.form.get("trust_id") or None,
                subject_object_id=request.form.get("subject_object_id") or None,
            )
            return redirect(url_for("tpd1c.continuity_detail", profile_id=profile_id))
        except BridgeError as exc:
            flash(str(exc), "warning")
    return render_template("tpd1c/continuity_new.html", defaults=request.args)


@tpd1c.route("/continuity-profiles/<profile_id>")
@permission_required("edit_trust")
def continuity_detail(profile_id):
    bundle = get_continuity_profile(_db_path(), profile_id, _firm())
    if not bundle:
        abort(404)
    return render_template("tpd1c/continuity_detail.html", **bundle)


RECORD_TABLES = {
    "responsibility": "continuity_responsibilities", "digital-account": "continuity_digital_accounts",
    "receivable": "continuity_receivables", "payable": "continuity_payables", "activation-plan": "continuity_activation_plans",
}


@tpd1c.route("/continuity-profiles/<profile_id>/records/<record_type>", methods=["POST"])
@permission_required("edit_trust")
def continuity_add_record(profile_id, record_type):
    table = RECORD_TABLES.get(record_type)
    if not table:
        abort(404)
    try:
        add_continuity_record(_db_path(), table, profile_id, _firm(), _actor(), request.form.to_dict())
        flash("Continuity record added. Designation does not grant legal or application authority.", "success")
    except (BridgeError, Exception) as exc:
        flash(str(exc), "warning")
    return redirect(url_for("tpd1c.continuity_detail", profile_id=profile_id))


@tpd1c.route("/continuity-profiles/<profile_id>/activation/<plan_id>/transition", methods=["POST"])
@permission_required("edit_trust")
def activation_transition(profile_id, plan_id):
    try:
        transition_activation_plan(_db_path(), plan_id, profile_id, _firm(), _actor(),
                                   request.form.get("new_status", ""), request.form.get("basis", ""))
        flash("Activation status recorded; the software did not determine incapacity or grant authority.", "success")
    except BridgeError as exc:
        flash(str(exc), "warning")
    return redirect(url_for("tpd1c.continuity_detail", profile_id=profile_id))
