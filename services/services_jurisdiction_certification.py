"""Wave-4 jurisdiction certification records; P09 remains the fact owner."""

import sqlite3
import uuid
from datetime import datetime, timezone

from services.services_work_learning_authority import LEGAL_SCOPES


CONTEXT_TYPES = ("PROGRAM", "MATTER", "TRUST", "OTHER")
CERTIFICATION_STATES = ("UNRESOLVED", "REVIEW_REQUIRED", "CERTIFIED", "REJECTED", "SUPERSEDED")
DECISION_ORIGINS = ("SYSTEM_SUGGESTED", "OPERATOR_OR_FIDUCIARY", "PROFESSIONAL")


def _required(value, code):
    value = str(value or "").strip()
    if not value:
        raise ValueError(code)
    return value


def _row(connection, sql, values):
    row = connection.execute(sql, values).fetchone()
    return dict(row) if row else None


def record_jurisdiction_module_certification(
    db_path, *, firm_id, context_type, context_id, jurisdiction, subject,
    legal_scope, applicability_id, hierarchy_id, certification_state, basis,
    provenance, decision_origin, human_confirmed, actor, actor_capacity,
    trust_type_applicability=None, evidence_sufficiency_id=None,
    prior_certification_id=None,
):
    firm_id = _required(firm_id, "firm_required")
    context_id = _required(context_id, "context_required")
    jurisdiction = _required(jurisdiction, "jurisdiction_required")
    subject = _required(subject, "subject_required")
    basis = _required(basis, "certification_basis_required")
    provenance = _required(provenance, "certification_provenance_required")
    actor = _required(actor, "actor_required")
    actor_capacity = _required(actor_capacity, "actor_capacity_required")
    if context_type not in CONTEXT_TYPES: raise ValueError("invalid_context_type")
    if legal_scope not in LEGAL_SCOPES: raise ValueError("invalid_legal_scope")
    if certification_state not in CERTIFICATION_STATES: raise ValueError("invalid_certification_state")
    if decision_origin not in DECISION_ORIGINS: raise ValueError("invalid_decision_origin")
    if decision_origin == "SYSTEM_SUGGESTED" and certification_state not in ("UNRESOLVED", "REVIEW_REQUIRED"):
        raise ValueError("machine_certification_finalization_prohibited")
    if certification_state in ("CERTIFIED", "REJECTED") and (
        decision_origin not in ("OPERATOR_OR_FIDUCIARY", "PROFESSIONAL") or not human_confirmed
    ):
        raise ValueError("certification_requires_human_confirmation")

    connection = sqlite3.connect(str(db_path)); connection.row_factory = sqlite3.Row
    try:
        applicability = _row(connection, "SELECT * FROM hub_authority_applicability WHERE applicability_id=?", (applicability_id,))
        if not applicability:
            raise ValueError("applicability_not_available_in_context")
        keys = ("firm_id", "context_type", "context_id", "subject")
        expected = (firm_id, context_type, context_id, subject)
        if tuple(applicability[k] for k in keys) != expected:
            raise ValueError("applicability_not_available_in_context")
        hierarchy = _row(connection, "SELECT * FROM hub_authority_hierarchy_determinations WHERE hierarchy_id=?", (hierarchy_id,))
        if not hierarchy or tuple(hierarchy[k] for k in keys) != expected:
            raise ValueError("hierarchy_not_available_in_context")
        if applicability["legal_scope"] != legal_scope:
            raise ValueError("applicability_legal_scope_mismatch")
        if evidence_sufficiency_id:
            sufficiency = _row(connection, "SELECT * FROM hub_program_evidence_sufficiency_assessments WHERE sufficiency_id=?", (evidence_sufficiency_id,))
            if not sufficiency or sufficiency["firm_id"] != firm_id or context_type != "PROGRAM" or sufficiency["program_id"] != context_id:
                raise ValueError("evidence_sufficiency_not_available_in_context")
        if certification_state == "CERTIFIED":
            if applicability["applicability_jurisdiction"] != jurisdiction:
                raise ValueError("applicability_jurisdiction_mismatch")
            if applicability["independent_support_state"] != "YES" or applicability["research_only"] or not applicability["generation_authorized"]:
                raise ValueError("applicability_not_generation_authorized")
            if hierarchy["hierarchy_kind"] != "CONTROLLING_LAW" or hierarchy["hierarchy_state"] != "CONTROLLING":
                raise ValueError("controlling_law_hierarchy_required")
            if hierarchy["applicability_jurisdiction"] != jurisdiction:
                raise ValueError("hierarchy_jurisdiction_mismatch")
            if hierarchy["source_reference_id"] != applicability["source_reference_id"]:
                raise ValueError("p09_source_relationship_mismatch")
        latest = _row(connection, """SELECT * FROM hub_jurisdiction_module_certifications
          WHERE firm_id=? AND context_type=? AND context_id=? AND subject=? AND jurisdiction=? AND legal_scope=?
          ORDER BY created_at DESC,certification_id DESC LIMIT 1""",
          (firm_id,context_type,context_id,subject,jurisdiction,legal_scope))
        if latest and prior_certification_id != latest["certification_id"]:
            raise ValueError("prior_certification_required")
        if not latest and prior_certification_id:
            raise ValueError("prior_certification_not_available_in_context")
        prior = None
        if prior_certification_id:
            prior = _row(connection, "SELECT * FROM hub_jurisdiction_module_certifications WHERE certification_id=?", (prior_certification_id,))
            continuity = ("firm_id", "context_type", "context_id", "subject", "jurisdiction", "legal_scope")
            if not prior or tuple(prior[k] for k in continuity) != (firm_id, context_type, context_id, subject, jurisdiction, legal_scope):
                raise ValueError("prior_certification_not_available_in_context")
        if certification_state == "SUPERSEDED" and not prior:
            raise ValueError("superseded_requires_predecessor")
        certification_id = "JCRT-" + uuid.uuid4().hex[:10].upper()
        connection.execute("""INSERT INTO hub_jurisdiction_module_certifications
          (certification_id,firm_id,context_type,context_id,jurisdiction,subject,legal_scope,trust_type_applicability,applicability_id,hierarchy_id,evidence_sufficiency_id,certification_state,basis,provenance,decision_origin,human_confirmed,actor,actor_capacity,prior_certification_id,created_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            certification_id, firm_id, context_type, context_id, jurisdiction, subject,
            legal_scope, str(trust_type_applicability or "").strip() or None,
            applicability_id, hierarchy_id, evidence_sufficiency_id, certification_state,
            basis, provenance, decision_origin, int(bool(human_confirmed)), actor,
            actor_capacity, prior_certification_id, datetime.now(timezone.utc).isoformat(),
        ))
        connection.commit()
        return certification_id
    finally:
        connection.close()


def get_jurisdiction_module_certification(db_path, certification_id):
    connection = sqlite3.connect(str(db_path)); connection.row_factory = sqlite3.Row
    try:
        return _row(connection, "SELECT * FROM hub_jurisdiction_module_certifications WHERE certification_id=?", (certification_id,))
    finally: connection.close()


def get_jurisdiction_module_certification_history(db_path, *, firm_id, context_type, context_id, subject, jurisdiction, legal_scope):
    connection = sqlite3.connect(str(db_path)); connection.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in connection.execute("""SELECT * FROM hub_jurisdiction_module_certifications
          WHERE firm_id=? AND context_type=? AND context_id=? AND subject=? AND jurisdiction=? AND legal_scope=?
          ORDER BY created_at,certification_id""", (firm_id,context_type,context_id,subject,jurisdiction,legal_scope))]
    finally: connection.close()
