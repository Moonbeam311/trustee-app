"""Contract #11: append-only assessments of canonical template portability."""

import sqlite3
import uuid
from datetime import datetime, timezone

from services.services_work_learning_authority import LEGAL_SCOPES

PORTABILITY_STATES = ("UNRESOLVED", "REVIEW_REQUIRED", "PORTABLE", "NOT_PORTABLE", "SUPERSEDED")
DECISION_ORIGINS = ("SYSTEM_SUGGESTED", "OPERATOR_OR_FIDUCIARY", "PROFESSIONAL")


def _required(value, code):
    value = str(value or "").strip()
    if not value: raise ValueError(code)
    return value


def record_template_portability_assessment(
    db_path, *, firm_id, template_id, target_jurisdiction, target_trust_type,
    legal_scope, portability_state, basis, provenance, decision_origin,
    human_confirmed, actor, actor_capacity, jurisdiction_certification_id=None,
    prior_portability_id=None,
):
    firm_id = _required(firm_id, "firm_required")
    template_id = _required(template_id, "template_required")
    target_jurisdiction = _required(target_jurisdiction, "target_jurisdiction_required")
    target_trust_type = _required(target_trust_type, "target_trust_type_required")
    basis = _required(basis, "portability_basis_required")
    provenance = _required(provenance, "portability_provenance_required")
    actor = _required(actor, "actor_required"); actor_capacity = _required(actor_capacity, "actor_capacity_required")
    if legal_scope not in LEGAL_SCOPES: raise ValueError("invalid_legal_scope")
    if portability_state not in PORTABILITY_STATES: raise ValueError("invalid_portability_state")
    if decision_origin not in DECISION_ORIGINS: raise ValueError("invalid_decision_origin")
    if decision_origin == "SYSTEM_SUGGESTED" and portability_state not in ("UNRESOLVED", "REVIEW_REQUIRED"):
        raise ValueError("machine_portability_finalization_prohibited")
    if portability_state in ("PORTABLE", "NOT_PORTABLE") and (decision_origin not in ("OPERATOR_OR_FIDUCIARY", "PROFESSIONAL") or not human_confirmed):
        raise ValueError("portability_requires_human_confirmation")
    connection = sqlite3.connect(str(db_path)); connection.row_factory = sqlite3.Row
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "document_templates" not in tables:
            raise ValueError("canonical_template_owner_unavailable")
        columns = {row[1] for row in connection.execute("PRAGMA table_info(document_templates)")}
        if "template_id" not in columns or not connection.execute("SELECT 1 FROM document_templates WHERE template_id=? LIMIT 1", (template_id,)).fetchone():
            raise ValueError("template_not_available")
        certification = None
        if jurisdiction_certification_id:
            row = connection.execute("SELECT * FROM hub_jurisdiction_module_certifications WHERE certification_id=?", (jurisdiction_certification_id,)).fetchone()
            certification = dict(row) if row else None
            if not certification or certification["firm_id"] != firm_id:
                raise ValueError("jurisdiction_certification_not_available_in_context")
        if portability_state == "PORTABLE":
            if not certification or certification["certification_state"] != "CERTIFIED":
                raise ValueError("certified_jurisdiction_assessment_required")
            if certification["jurisdiction"] != target_jurisdiction or certification["legal_scope"] != legal_scope:
                raise ValueError("jurisdiction_certification_scope_mismatch")
        latest_row = connection.execute("""SELECT * FROM document_template_portability_assessments
          WHERE firm_id=? AND template_id=? AND target_jurisdiction=? AND target_trust_type=? AND legal_scope=?
          ORDER BY created_at DESC,portability_id DESC LIMIT 1""", (firm_id,template_id,target_jurisdiction,target_trust_type,legal_scope)).fetchone()
        latest = dict(latest_row) if latest_row else None
        if latest and prior_portability_id != latest["portability_id"]:
            raise ValueError("prior_portability_required")
        if not latest and prior_portability_id:
            raise ValueError("prior_portability_not_available_in_context")
        prior = None
        if prior_portability_id:
            row = connection.execute("SELECT * FROM document_template_portability_assessments WHERE portability_id=?", (prior_portability_id,)).fetchone()
            prior = dict(row) if row else None
            keys = ("firm_id","template_id","target_jurisdiction","target_trust_type","legal_scope")
            if not prior or tuple(prior[k] for k in keys) != (firm_id,template_id,target_jurisdiction,target_trust_type,legal_scope):
                raise ValueError("prior_portability_not_available_in_context")
        if portability_state == "SUPERSEDED" and not prior: raise ValueError("superseded_requires_predecessor")
        portability_id = "PORT-" + uuid.uuid4().hex[:10].upper()
        connection.execute("""INSERT INTO document_template_portability_assessments
          (portability_id,firm_id,template_id,target_jurisdiction,target_trust_type,legal_scope,jurisdiction_certification_id,portability_state,basis,provenance,decision_origin,human_confirmed,actor,actor_capacity,prior_portability_id,created_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (portability_id,firm_id,template_id,target_jurisdiction,target_trust_type,legal_scope,jurisdiction_certification_id,portability_state,basis,provenance,decision_origin,int(bool(human_confirmed)),actor,actor_capacity,prior_portability_id,datetime.now(timezone.utc).isoformat()))
        connection.commit(); return portability_id
    finally: connection.close()


def get_template_portability_assessment(db_path, portability_id):
    connection=sqlite3.connect(str(db_path)); connection.row_factory=sqlite3.Row
    try:
        row=connection.execute("SELECT * FROM document_template_portability_assessments WHERE portability_id=?",(portability_id,)).fetchone(); return dict(row) if row else None
    finally: connection.close()


def get_template_portability_history(db_path, *, firm_id, template_id, target_jurisdiction, target_trust_type, legal_scope):
    connection=sqlite3.connect(str(db_path)); connection.row_factory=sqlite3.Row
    try:
        return [dict(row) for row in connection.execute("""SELECT * FROM document_template_portability_assessments WHERE firm_id=? AND template_id=? AND target_jurisdiction=? AND target_trust_type=? AND legal_scope=? ORDER BY created_at,portability_id""",(firm_id,template_id,target_jurisdiction,target_trust_type,legal_scope))]
    finally: connection.close()
