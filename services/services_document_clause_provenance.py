"""Wave-5 clause revision and generation provenance extension service."""

import re
import sqlite3
import uuid
from datetime import datetime, timezone


class DocumentClauseProvenanceError(ValueError):
    pass


REVISION_STATES = {"DRAFT", "REVIEW_REQUIRED", "APPROVED", "SUPERSEDED"}
GENERATION_STATES = {"UNRESOLVED", "PROPOSED", "AUTHORIZED", "APPLIED", "REJECTED", "SUPERSEDED"}
CONTEXT_TYPES = {"PROGRAM", "MATTER", "TRUST", "OTHER"}
DECISION_ORIGINS = {"SYSTEM_SUGGESTED", "OPERATOR_OR_FIDUCIARY", "PROFESSIONAL"}
HUMAN_ORIGINS = {"OPERATOR_OR_FIDUCIARY", "PROFESSIONAL"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _id(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


def _required(value, code):
    value = (value or "").strip()
    if not value:
        raise DocumentClauseProvenanceError(code)
    return value


def _table(connection, name):
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def _columns(connection, name):
    return {row[1] for row in connection.execute(f"PRAGMA table_info({name})")}


def _row(connection, table, id_column, value):
    if not _table(connection, table):
        return None
    connection.row_factory = sqlite3.Row
    row = connection.execute(f"SELECT * FROM {table} WHERE {id_column}=?", (value,)).fetchone()
    return dict(row) if row else None


def _owner(connection, table, id_column, value, label):
    if not _table(connection, table) or id_column not in _columns(connection, table):
        raise DocumentClauseProvenanceError(f"canonical_{label}_owner_unavailable")
    row = _row(connection, table, id_column, value)
    if not row:
        raise DocumentClauseProvenanceError(f"{label}_not_found")
    return row


def _matches(row, expected, code):
    for key, value in expected.items():
        if key in row and row[key] is not None and row[key] != value:
            raise DocumentClauseProvenanceError(code)


def record_template_clause_revision(db_path, *, template_id, clause_id, clause_key,
 revision_label, revision_state, content_sha256, basis, provenance, decision_origin,
 human_confirmed, actor, actor_capacity, source_reference_id=None,
 prior_clause_revision_id=None, clause_revision_id=None, created_at=None):
    template_id = _required(template_id, "template_required")
    clause_id = _required(clause_id, "clause_id_required")
    clause_key = _required(clause_key, "clause_key_required")
    revision_label = _required(revision_label, "revision_label_required")
    basis = _required(basis, "basis_required")
    provenance = _required(provenance, "provenance_required")
    actor = _required(actor, "actor_required")
    actor_capacity = _required(actor_capacity, "actor_capacity_required")
    if revision_state not in REVISION_STATES:
        raise DocumentClauseProvenanceError("invalid_revision_state")
    if decision_origin not in DECISION_ORIGINS:
        raise DocumentClauseProvenanceError("invalid_decision_origin")
    if not re.fullmatch(r"[0-9a-f]{64}", content_sha256 or ""):
        raise DocumentClauseProvenanceError("invalid_content_sha256")
    if decision_origin == "SYSTEM_SUGGESTED" and revision_state not in {"DRAFT", "REVIEW_REQUIRED"}:
        raise DocumentClauseProvenanceError("machine_revision_finalization_prohibited")
    if revision_state == "APPROVED" and (decision_origin not in HUMAN_ORIGINS or not human_confirmed):
        raise DocumentClauseProvenanceError("approved_revision_requires_human_confirmation")
    if revision_state == "SUPERSEDED" and (decision_origin not in HUMAN_ORIGINS or not human_confirmed or not prior_clause_revision_id):
        raise DocumentClauseProvenanceError("superseded_revision_requires_human_predecessor")
    with sqlite3.connect(str(db_path)) as connection:
        _owner(connection, "document_templates", "template_id", template_id, "template")
        if source_reference_id is not None:
            _owner(connection, "hub_program_source_references", "source_reference_id", source_reference_id, "source_reference")
        connection.row_factory = sqlite3.Row
        latest = connection.execute("SELECT * FROM document_template_clause_revisions WHERE template_id=? AND clause_id=? ORDER BY rowid DESC LIMIT 1", (template_id, clause_id)).fetchone()
        latest = dict(latest) if latest else None
        if latest and prior_clause_revision_id != latest["clause_revision_id"]:
            raise DocumentClauseProvenanceError("latest_predecessor_required")
        if not latest and prior_clause_revision_id is not None:
            raise DocumentClauseProvenanceError("predecessor_not_available_in_scope")
        if latest and latest["clause_key"] != clause_key:
            raise DocumentClauseProvenanceError("stable_clause_identity_violation")
        if prior_clause_revision_id:
            prior = _row(connection, "document_template_clause_revisions", "clause_revision_id", prior_clause_revision_id)
            if not prior or prior["template_id"] != template_id or prior["clause_id"] != clause_id:
                raise DocumentClauseProvenanceError("predecessor_not_available_in_scope")
        revision_id = clause_revision_id or _id("CLREV")
        connection.execute("""INSERT INTO document_template_clause_revisions
          (clause_revision_id,template_id,clause_id,clause_key,revision_label,revision_state,content_sha256,source_reference_id,basis,provenance,decision_origin,human_confirmed,actor,actor_capacity,prior_clause_revision_id,created_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (revision_id,template_id,clause_id,clause_key,revision_label,revision_state,content_sha256,source_reference_id,basis,provenance,decision_origin,int(bool(human_confirmed)),actor,actor_capacity,prior_clause_revision_id,created_at or _now()))
        return revision_id


def get_template_clause_revision(db_path, clause_revision_id):
    with sqlite3.connect(str(db_path)) as connection:
        return _row(connection, "document_template_clause_revisions", "clause_revision_id", clause_revision_id)


def get_template_clause_history(db_path, *, template_id, clause_id):
    with sqlite3.connect(str(db_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute("SELECT * FROM document_template_clause_revisions WHERE template_id=? AND clause_id=? ORDER BY rowid", (template_id, clause_id))]


def _validate_context(connection, firm_id, context_type, context_id):
    mapping = {"PROGRAM": ("hub_programs", "program_id"), "MATTER": ("matters", "matter_id"), "TRUST": ("trusts", "trust_id")}
    if context_type in mapping and _table(connection, mapping[context_type][0]):
        row = _owner(connection, mapping[context_type][0], mapping[context_type][1], context_id, "context")
        _matches(row, {"firm_id": firm_id}, "context_firm_mismatch")


def _validate_final_authority(connection, *, firm_id, context_type, context_id,
 revision, template_id, applicability_id, hierarchy_id, evidence_sufficiency_id,
 jurisdiction_certification_id, portability_id):
    app = _owner(connection, "hub_authority_applicability", "applicability_id", applicability_id, "applicability")
    hierarchy = _owner(connection, "hub_authority_hierarchy_determinations", "hierarchy_id", hierarchy_id, "hierarchy")
    evidence = _owner(connection, "hub_program_evidence_sufficiency_assessments", "sufficiency_id", evidence_sufficiency_id, "evidence_sufficiency")
    certification = _owner(connection, "hub_jurisdiction_module_certifications", "certification_id", jurisdiction_certification_id, "jurisdiction_certification")
    portability = _owner(connection, "document_template_portability_assessments", "portability_id", portability_id, "portability")
    for row, label in ((app,"applicability"),(hierarchy,"hierarchy"),(certification,"jurisdiction_certification")):
        _matches(row, {"firm_id":firm_id,"context_type":context_type,"context_id":context_id}, f"{label}_context_mismatch")
    _matches(evidence, {"firm_id": firm_id}, "evidence_sufficiency_firm_mismatch")
    _matches(portability, {"firm_id": firm_id, "template_id": template_id}, "portability_context_mismatch")
    _matches(certification, {"applicability_id":applicability_id,"hierarchy_id":hierarchy_id}, "jurisdiction_certification_authority_mismatch")
    _matches(portability, {"jurisdiction_certification_id":jurisdiction_certification_id}, "portability_certification_mismatch")
    if int(app.get("generation_authorized") or 0) != 1 or int(app.get("research_only") or 0) != 0 or app.get("independent_support_state") != "YES":
        raise DocumentClauseProvenanceError("applicability_not_generation_authorized")
    if hierarchy.get("hierarchy_state") != "CONTROLLING":
        raise DocumentClauseProvenanceError("hierarchy_not_controlling")
    if evidence.get("sufficiency_state") != "SUFFICIENT" or evidence.get("target_use") not in {"GENERATION", "FINALIZATION"}:
        raise DocumentClauseProvenanceError("evidence_not_sufficient_for_generation")
    if certification.get("certification_state") != "CERTIFIED":
        raise DocumentClauseProvenanceError("jurisdiction_not_certified")
    if portability.get("portability_state") != "PORTABLE":
        raise DocumentClauseProvenanceError("template_not_portable")
    source = revision.get("source_reference_id")
    if source and (app.get("source_reference_id") != source or hierarchy.get("source_reference_id") != source):
        raise DocumentClauseProvenanceError("authority_source_mismatch")
    return app, hierarchy, evidence, certification, portability


def record_clause_generation_event(db_path, *, firm_id, context_type, context_id,
 template_id, clause_revision_id, generation_state, basis, provenance,
 decision_origin, human_confirmed, actor, actor_capacity, trust_id=None,
 matter_id=None, intake_id=None, generated_document_id=None, applicability_id=None,
 hierarchy_id=None, evidence_sufficiency_id=None, jurisdiction_certification_id=None,
 portability_id=None, prior_clause_generation_event_id=None,
 clause_generation_event_id=None, created_at=None):
    firm_id = _required(firm_id, "firm_required"); context_id = _required(context_id, "context_required")
    template_id = _required(template_id, "template_required"); clause_revision_id = _required(clause_revision_id, "clause_revision_required")
    basis = _required(basis, "basis_required"); provenance = _required(provenance, "provenance_required")
    actor = _required(actor, "actor_required"); actor_capacity = _required(actor_capacity, "actor_capacity_required")
    if context_type not in CONTEXT_TYPES: raise DocumentClauseProvenanceError("invalid_context_type")
    if generation_state not in GENERATION_STATES: raise DocumentClauseProvenanceError("invalid_generation_state")
    if decision_origin not in DECISION_ORIGINS: raise DocumentClauseProvenanceError("invalid_decision_origin")
    if decision_origin == "SYSTEM_SUGGESTED" and generation_state not in {"UNRESOLVED", "PROPOSED"}:
        raise DocumentClauseProvenanceError("machine_generation_finalization_prohibited")
    if generation_state in {"AUTHORIZED","APPLIED","REJECTED","SUPERSEDED"} and (decision_origin not in HUMAN_ORIGINS or not human_confirmed):
        raise DocumentClauseProvenanceError("generation_state_requires_human_confirmation")
    with sqlite3.connect(str(db_path)) as connection:
        _owner(connection, "document_templates", "template_id", template_id, "template")
        revision = _owner(connection, "document_template_clause_revisions", "clause_revision_id", clause_revision_id, "clause_revision")
        if revision["template_id"] != template_id: raise DocumentClauseProvenanceError("clause_revision_template_mismatch")
        _validate_context(connection, firm_id, context_type, context_id)
        intake_table = "intake_sessions" if _table(connection, "intake_sessions") else "intakes"
        for table, column, value, label in (("trusts","trust_id",trust_id,"trust"),("matters","matter_id",matter_id,"matter"),(intake_table,"intake_id",intake_id,"intake")):
            if value is not None and _table(connection, table):
                owner = _owner(connection, table, column, value, label); _matches(owner, {"firm_id":firm_id}, f"{label}_firm_mismatch")
        if generation_state in {"AUTHORIZED", "APPLIED"}:
            if revision["revision_state"] != "APPROVED": raise DocumentClauseProvenanceError("approved_clause_revision_required")
            if not all((applicability_id,hierarchy_id,evidence_sufficiency_id,jurisdiction_certification_id,portability_id)):
                raise DocumentClauseProvenanceError("final_generation_authority_links_required")
            _validate_final_authority(connection, firm_id=firm_id, context_type=context_type, context_id=context_id, revision=revision, template_id=template_id, applicability_id=applicability_id, hierarchy_id=hierarchy_id, evidence_sufficiency_id=evidence_sufficiency_id, jurisdiction_certification_id=jurisdiction_certification_id, portability_id=portability_id)
        if generation_state == "APPLIED":
            if not generated_document_id: raise DocumentClauseProvenanceError("applied_requires_generated_document")
            document = _owner(connection, "generated_documents", "document_id", generated_document_id, "generated_document")
            _matches(document, {"firm_id":firm_id,"trust_id":trust_id,"template_id":template_id}, "generated_document_context_mismatch")
        scope = (firm_id,context_type,context_id,template_id,clause_revision_id)
        connection.row_factory = sqlite3.Row
        latest = connection.execute("SELECT * FROM document_clause_generation_events WHERE firm_id=? AND context_type=? AND context_id=? AND template_id=? AND clause_revision_id=? ORDER BY rowid DESC LIMIT 1", scope).fetchone()
        latest = dict(latest) if latest else None
        if generation_state == "SUPERSEDED" and not prior_clause_generation_event_id:
            raise DocumentClauseProvenanceError("superseded_requires_predecessor")
        if latest and prior_clause_generation_event_id != latest["clause_generation_event_id"]:
            raise DocumentClauseProvenanceError("latest_predecessor_required")
        if not latest and prior_clause_generation_event_id is not None:
            raise DocumentClauseProvenanceError("predecessor_not_available_in_scope")
        if prior_clause_generation_event_id:
            prior = _row(connection,"document_clause_generation_events","clause_generation_event_id",prior_clause_generation_event_id)
            if not prior or tuple(prior[k] for k in ("firm_id","context_type","context_id","template_id","clause_revision_id")) != scope:
                raise DocumentClauseProvenanceError("predecessor_not_available_in_scope")
        event_id = clause_generation_event_id or _id("CLGEN")
        connection.execute("""INSERT INTO document_clause_generation_events
          (clause_generation_event_id,firm_id,context_type,context_id,trust_id,matter_id,intake_id,template_id,clause_revision_id,generated_document_id,generation_state,applicability_id,hierarchy_id,evidence_sufficiency_id,jurisdiction_certification_id,portability_id,basis,provenance,decision_origin,human_confirmed,actor,actor_capacity,prior_clause_generation_event_id,created_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (event_id,firm_id,context_type,context_id,trust_id,matter_id,intake_id,template_id,clause_revision_id,generated_document_id,generation_state,applicability_id,hierarchy_id,evidence_sufficiency_id,jurisdiction_certification_id,portability_id,basis,provenance,decision_origin,int(bool(human_confirmed)),actor,actor_capacity,prior_clause_generation_event_id,created_at or _now()))
        return event_id


def get_clause_generation_event(db_path, clause_generation_event_id):
    with sqlite3.connect(str(db_path)) as connection:
        return _row(connection,"document_clause_generation_events","clause_generation_event_id",clause_generation_event_id)


def get_clause_generation_history(db_path, *, firm_id, context_type, context_id, template_id, clause_revision_id):
    with sqlite3.connect(str(db_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute("SELECT * FROM document_clause_generation_events WHERE firm_id=? AND context_type=? AND context_id=? AND template_id=? AND clause_revision_id=? ORDER BY rowid", (firm_id,context_type,context_id,template_id,clause_revision_id))]


def build_clause_generation_provenance(db_path, clause_generation_event_id):
    """Read linked records exactly as recorded; never compose a legal result."""
    with sqlite3.connect(str(db_path)) as connection:
        event = _row(connection,"document_clause_generation_events","clause_generation_event_id",clause_generation_event_id)
        if not event: return None
        links = {
            "clause_revision": ("document_template_clause_revisions","clause_revision_id",event["clause_revision_id"]),
            "applicability": ("hub_authority_applicability","applicability_id",event.get("applicability_id")),
            "hierarchy": ("hub_authority_hierarchy_determinations","hierarchy_id",event.get("hierarchy_id")),
            "evidence_sufficiency": ("hub_program_evidence_sufficiency_assessments","sufficiency_id",event.get("evidence_sufficiency_id")),
            "jurisdiction_certification": ("hub_jurisdiction_module_certifications","certification_id",event.get("jurisdiction_certification_id")),
            "portability": ("document_template_portability_assessments","portability_id",event.get("portability_id")),
        }
        result = {"generation_event": event}
        for name, (table, column, value) in links.items():
            result[name] = _row(connection,table,column,value) if value is not None and _table(connection,table) else None
        return result
