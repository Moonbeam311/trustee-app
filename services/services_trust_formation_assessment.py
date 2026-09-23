"""Matter-specific, non-owning Wave-5 trust formation assessments."""

import sqlite3
import uuid
from datetime import datetime, timezone


class TrustFormationAssessmentError(ValueError):
    pass


FORMATION_STATES = {"UNRESOLVED","PLANNING","DRAFTING","EXECUTION_PENDING","EXECUTION_RECORDED","FORMATION_RECORDED","SUPERSEDED"}
READINESS_STATES = {"UNRESOLVED","REVIEW_REQUIRED","NOT_READY","READY_FOR_DRAFT","READY_FOR_EXECUTION","READY_FOR_ACTIVATION"}
READY_STATES = {"READY_FOR_DRAFT","READY_FOR_EXECUTION","READY_FOR_ACTIVATION"}
DECISION_ORIGINS = {"SYSTEM_SUGGESTED","OPERATOR_OR_FIDUCIARY","PROFESSIONAL"}
HUMAN_ORIGINS = {"OPERATOR_OR_FIDUCIARY","PROFESSIONAL"}


def _now(): return datetime.now(timezone.utc).isoformat()
def _id(): return "FORM-" + uuid.uuid4().hex[:12].upper()


def _required(value, code):
    value = (value or "").strip()
    if not value: raise TrustFormationAssessmentError(code)
    return value


def _table(connection, name):
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def _columns(connection, name):
    return {row[1] for row in connection.execute(f"PRAGMA table_info({name})")}


def _row(connection, table, id_column, value):
    if not _table(connection, table) or id_column not in _columns(connection, table): return None
    connection.row_factory = sqlite3.Row
    row = connection.execute(f"SELECT * FROM {table} WHERE {id_column}=?", (value,)).fetchone()
    return dict(row) if row else None


def _owner_if_present(connection, table, id_columns, value, label):
    if not _table(connection, table): return None
    columns = _columns(connection, table)
    column = next((item for item in id_columns if item in columns), None)
    if not column: raise TrustFormationAssessmentError(f"canonical_{label}_identifier_unavailable")
    row = _row(connection, table, column, value)
    if not row: raise TrustFormationAssessmentError(f"{label}_not_found")
    return row


def _match(row, expected, code):
    if row is None: return
    for key, value in expected.items():
        if value is not None and key in row and row[key] is not None and row[key] != value:
            raise TrustFormationAssessmentError(code)


def record_trust_formation_assessment(db_path, *, firm_id, formation_state,
 readiness_state, basis, provenance, decision_origin, human_confirmed, actor,
 actor_capacity, intake_id=None, matter_id=None, trust_id=None,
 governing_document_type=None, governing_document_id=None,
 legal_state_event_id=None, jurisdiction_certification_id=None,
 trustee_acceptance_id=None, asset_control_id=None,
 prior_formation_assessment_id=None, formation_assessment_id=None, created_at=None):
    firm_id = _required(firm_id,"firm_required")
    basis = _required(basis,"basis_required"); provenance = _required(provenance,"provenance_required")
    actor = _required(actor,"actor_required"); actor_capacity = _required(actor_capacity,"actor_capacity_required")
    if not any((intake_id,matter_id,trust_id)): raise TrustFormationAssessmentError("formation_context_required")
    if formation_state not in FORMATION_STATES: raise TrustFormationAssessmentError("invalid_formation_state")
    if readiness_state not in READINESS_STATES: raise TrustFormationAssessmentError("invalid_readiness_state")
    if decision_origin not in DECISION_ORIGINS: raise TrustFormationAssessmentError("invalid_decision_origin")
    if governing_document_type == "INSTRUMENT": raise TrustFormationAssessmentError("instrument_object_type_prohibited")
    if governing_document_type is not None and governing_document_type not in {"DOCUMENT","GENERATED_DOCUMENT"}:
        raise TrustFormationAssessmentError("invalid_governing_document_type")
    if bool(governing_document_type) != bool(governing_document_id):
        raise TrustFormationAssessmentError("governing_document_reference_incomplete")
    if decision_origin == "SYSTEM_SUGGESTED":
        if formation_state != "UNRESOLVED" or readiness_state not in {"UNRESOLVED","REVIEW_REQUIRED"}:
            raise TrustFormationAssessmentError("machine_formation_or_readiness_finalization_prohibited")
    if formation_state in {"EXECUTION_RECORDED","FORMATION_RECORDED"} or readiness_state in READY_STATES:
        if decision_origin not in HUMAN_ORIGINS or not human_confirmed:
            raise TrustFormationAssessmentError("recorded_or_ready_state_requires_human_confirmation")
    if formation_state == "FORMATION_RECORDED" and not all((trust_id,governing_document_type,governing_document_id,legal_state_event_id,jurisdiction_certification_id)):
        raise TrustFormationAssessmentError("formation_recorded_links_required")
    with sqlite3.connect(str(db_path)) as connection:
        intake_table = "intake_sessions" if _table(connection,"intake_sessions") else "intakes"
        intake = _owner_if_present(connection,intake_table,("intake_id","id"),intake_id,"intake") if intake_id else None
        matter = _owner_if_present(connection,"matters",("matter_id","id"),matter_id,"matter") if matter_id else None
        trust = _owner_if_present(connection,"trusts",("trust_id",),trust_id,"trust") if trust_id else None
        for owner, label in ((intake,"intake"),(matter,"matter"),(trust,"trust")):
            _match(owner,{"firm_id":firm_id},f"{label}_firm_mismatch")
        if governing_document_id:
            table = "documents" if governing_document_type == "DOCUMENT" else "generated_documents"
            document = _owner_if_present(connection,table,("document_id",),governing_document_id,"governing_document")
            if document is None: raise TrustFormationAssessmentError("canonical_governing_document_owner_unavailable")
            _match(document,{"firm_id":firm_id,"trust_id":trust_id},"governing_document_context_mismatch")
        if legal_state_event_id:
            event = _owner_if_present(connection,"document_legal_state_events",("legal_state_event_id",),legal_state_event_id,"legal_state_event")
            if event is None: raise TrustFormationAssessmentError("canonical_legal_state_event_owner_unavailable")
            _match(event,{"firm_id":firm_id,"trust_id":trust_id,"document_object_type":governing_document_type,"document_object_id":governing_document_id},"legal_state_event_context_mismatch")
            if formation_state == "FORMATION_RECORDED" and event.get("legal_state") not in {"EXECUTION_RECORDED","EFFECTIVE_RECORDED"}:
                raise TrustFormationAssessmentError("formation_requires_recorded_execution_or_effectiveness")
        if jurisdiction_certification_id:
            certification = _owner_if_present(connection,"hub_jurisdiction_module_certifications",("certification_id",),jurisdiction_certification_id,"jurisdiction_certification")
            if certification is None or certification.get("certification_state") != "CERTIFIED":
                raise TrustFormationAssessmentError("certified_jurisdiction_required")
            _match(certification,{"firm_id":firm_id},"jurisdiction_certification_firm_mismatch")
            if certification.get("context_type") == "TRUST" and trust_id:
                _match(certification,{"context_id":trust_id},"jurisdiction_certification_context_mismatch")
            if certification.get("context_type") == "MATTER" and matter_id:
                _match(certification,{"context_id":matter_id},"jurisdiction_certification_context_mismatch")
        if trustee_acceptance_id:
            acceptance = _owner_if_present(connection,"successor_acceptances",("acceptance_id",),trustee_acceptance_id,"trustee_acceptance")
            if acceptance is None: raise TrustFormationAssessmentError("canonical_acceptance_owner_unavailable")
            _match(acceptance,{"firm_id":firm_id,"trust_id":trust_id},"trustee_acceptance_context_mismatch")
        if asset_control_id:
            asset = _owner_if_present(connection,"trust_asset_control_determinations",("asset_control_id",),asset_control_id,"asset_control")
            if asset is None: raise TrustFormationAssessmentError("canonical_asset_control_owner_unavailable")
            _match(asset,{"firm_id":firm_id,"trust_id":trust_id},"asset_control_context_mismatch")
        scope = (firm_id,intake_id,matter_id,trust_id)
        connection.row_factory = sqlite3.Row
        latest = connection.execute("""SELECT * FROM trust_formation_assessments
          WHERE firm_id=? AND intake_id IS ? AND matter_id IS ? AND trust_id IS ? ORDER BY rowid DESC LIMIT 1""", scope).fetchone()
        latest = dict(latest) if latest else None
        if formation_state == "SUPERSEDED" and not prior_formation_assessment_id:
            raise TrustFormationAssessmentError("superseded_requires_predecessor")
        if latest and prior_formation_assessment_id != latest["formation_assessment_id"]:
            raise TrustFormationAssessmentError("latest_predecessor_required")
        if not latest and prior_formation_assessment_id is not None:
            raise TrustFormationAssessmentError("predecessor_not_available_in_scope")
        if prior_formation_assessment_id:
            prior = _row(connection,"trust_formation_assessments","formation_assessment_id",prior_formation_assessment_id)
            if not prior or tuple(prior[k] for k in ("firm_id","intake_id","matter_id","trust_id")) != scope:
                raise TrustFormationAssessmentError("predecessor_not_available_in_scope")
        assessment_id = formation_assessment_id or _id()
        connection.execute("""INSERT INTO trust_formation_assessments
          (formation_assessment_id,firm_id,intake_id,matter_id,trust_id,formation_state,readiness_state,governing_document_type,governing_document_id,legal_state_event_id,jurisdiction_certification_id,trustee_acceptance_id,asset_control_id,basis,provenance,decision_origin,human_confirmed,actor,actor_capacity,prior_formation_assessment_id,created_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (assessment_id,firm_id,intake_id,matter_id,trust_id,formation_state,readiness_state,governing_document_type,governing_document_id,legal_state_event_id,jurisdiction_certification_id,trustee_acceptance_id,asset_control_id,basis,provenance,decision_origin,int(bool(human_confirmed)),actor,actor_capacity,prior_formation_assessment_id,created_at or _now()))
        return assessment_id


def get_trust_formation_assessment(db_path, formation_assessment_id):
    with sqlite3.connect(str(db_path)) as connection:
        return _row(connection,"trust_formation_assessments","formation_assessment_id",formation_assessment_id)


def get_trust_formation_history(db_path, *, firm_id, intake_id=None, matter_id=None, trust_id=None):
    with sqlite3.connect(str(db_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute("""SELECT * FROM trust_formation_assessments
          WHERE firm_id=? AND intake_id IS ? AND matter_id IS ? AND trust_id IS ? ORDER BY rowid""",(firm_id,intake_id,matter_id,trust_id))]


def evaluate_trust_formation_readiness(db_path, *, firm_id, intake_id=None, matter_id=None, trust_id=None):
    """Report only recorded assessment state and missing links; make no legal conclusion."""
    history = get_trust_formation_history(db_path,firm_id=firm_id,intake_id=intake_id,matter_id=matter_id,trust_id=trust_id)
    if not history:
        return {"assessment":None,"formation_state":"UNRESOLVED","readiness_state":"UNRESOLVED","review_required":True,"blockers":["no_recorded_assessment"],"legal_existence_determined":False,"validity_determined":False}
    current = history[-1]
    blockers = []
    if current["formation_state"] == "FORMATION_RECORDED":
        for field in ("trust_id","governing_document_type","governing_document_id","legal_state_event_id","jurisdiction_certification_id"):
            if not current.get(field): blockers.append(f"missing_{field}")
    if current["readiness_state"] in {"UNRESOLVED","REVIEW_REQUIRED","NOT_READY"}: blockers.append("recorded_readiness_not_ready")
    return {"assessment":current,"formation_state":current["formation_state"],"readiness_state":current["readiness_state"],"review_required":bool(blockers),"blockers":blockers,"legal_existence_determined":False,"validity_determined":False}
