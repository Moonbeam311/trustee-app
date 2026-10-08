"""Canonical document integrity and contextual evidence relationships."""

from __future__ import annotations

import hashlib
import sqlite3
import uuid
from datetime import datetime, timezone


class DocumentEvidenceError(ValueError):
    pass


ROLES = {
    "GOVERNING_PRE_SIGNING_MASTER", "BENEFICIARY_SCHEDULE",
    "INITIAL_TRUSTEE_ACCEPTANCE", "SCHEDULE_A", "CLOSING_CONTROL_SHEET",
    "HISTORICAL_PROFESSIONAL_REVIEW_REFERENCE",
}


def _now(): return datetime.now(timezone.utc).isoformat()
def _required(value, code):
    value = str(value or "").strip()
    if not value: raise DocumentEvidenceError(code)
    return value


def register_document_integrity(db_path, *, document_id, content_bytes,
                                source_revision_id, firm_id=None):
    """Verify actual bytes and bind intrinsic metadata to the existing document."""
    if not isinstance(content_bytes, bytes):
        raise DocumentEvidenceError("DOCUMENT_CONTENT_BYTES_REQUIRED")
    revision = _required(source_revision_id, "SOURCE_REVISION_REQUIRED")
    digest = hashlib.sha256(content_bytes).hexdigest()
    with sqlite3.connect(str(db_path)) as connection:
        connection.row_factory = sqlite3.Row
        clauses, params = ["document_id=?"], [document_id]
        columns = {r[1] for r in connection.execute("PRAGMA table_info(documents)")}
        if firm_id is not None and "firm_id" in columns:
            clauses.append("firm_id=?"); params.append(firm_id)
        row = connection.execute(
            f"SELECT * FROM documents WHERE {' AND '.join(clauses)}", params
        ).fetchone()
        if not row: raise DocumentEvidenceError("CANONICAL_DOCUMENT_NOT_FOUND")
        row = dict(row)
        if row.get("verified_content_sha256") not in (None, "", digest):
            raise DocumentEvidenceError("DOCUMENT_INTEGRITY_IMMUTABLE")
        if row.get("source_revision_id") not in (None, "", revision):
            raise DocumentEvidenceError("DOCUMENT_REVISION_IMMUTABLE")
        connection.execute(
            "UPDATE documents SET verified_content_sha256=?,source_revision_id=? WHERE document_id=?",
            (digest, revision, document_id),
        )
        return {"document_id": document_id, "verified_content_sha256": digest,
                "source_revision_id": revision}


def create_document_evidence_relationship(db_path, *, firm_id, context_type,
 document_id, evidence_role, relationship_state, classification, basis,
 provenance, decision_origin, human_confirmed, created_by, actor_capacity,
 context_id, prior_relationship_id=None, source_reference_id=None,
 relationship_id=None, created_at=None):
    values = [firm_id, context_id, document_id, basis, provenance, created_by, actor_capacity]
    if not all(str(v or "").strip() for v in values):
        raise DocumentEvidenceError("EVIDENCE_RELATIONSHIP_FIELDS_REQUIRED")
    if context_type not in {"TRUST", "MATTER"}: raise DocumentEvidenceError("INVALID_CONTEXT_TYPE")
    if evidence_role not in ROLES: raise DocumentEvidenceError("INVALID_EVIDENCE_ROLE")
    if relationship_state not in {"ACTIVE", "RETIRED"}: raise DocumentEvidenceError("INVALID_RELATIONSHIP_STATE")
    expected = "HISTORICAL_REFERENCE" if evidence_role == "HISTORICAL_PROFESSIONAL_REVIEW_REFERENCE" else "SOURCE_EVIDENCE"
    if classification != expected: raise DocumentEvidenceError("INVALID_EVIDENCE_CLASSIFICATION")
    if decision_origin not in {"OPERATOR_OR_FIDUCIARY", "PROFESSIONAL"} or not human_confirmed:
        raise DocumentEvidenceError("HUMAN_CONFIRMATION_REQUIRED")
    with sqlite3.connect(str(db_path)) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.row_factory = sqlite3.Row
        doc = connection.execute("SELECT * FROM documents WHERE document_id=?", (document_id,)).fetchone()
        if not doc: raise DocumentEvidenceError("CANONICAL_DOCUMENT_NOT_FOUND")
        if "firm_id" in doc.keys() and doc["firm_id"] not in (None, "", firm_id):
            raise DocumentEvidenceError("DOCUMENT_FIRM_MISMATCH")
        owner_table = "trusts" if context_type == "TRUST" else "matters"
        owner_key = "trust_id" if context_type == "TRUST" else "matter_id"
        tables = {r[0] for r in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        if owner_table not in tables:
            code = ("CANONICAL_TRUST_CONTEXT_NOT_FOUND" if context_type == "TRUST"
                    else "MATTER_CONTEXT_OWNER_REQUIRES_REVIEW")
            raise DocumentEvidenceError(code)
        owner_columns = {r[1] for r in connection.execute(f"PRAGMA table_info({owner_table})")}
        if owner_key not in owner_columns or "firm_id" not in owner_columns:
            code = ("CANONICAL_TRUST_CONTEXT_NOT_FOUND" if context_type == "TRUST"
                    else "MATTER_CONTEXT_OWNER_REQUIRES_REVIEW")
            raise DocumentEvidenceError(code)
        owner = connection.execute(
            f"SELECT * FROM {owner_table} WHERE {owner_key}=?", (context_id,)
        ).fetchone()
        if not owner:
            code = ("CANONICAL_TRUST_CONTEXT_NOT_FOUND" if context_type == "TRUST"
                    else "CANONICAL_MATTER_CONTEXT_NOT_FOUND")
            raise DocumentEvidenceError(code)
        if owner["firm_id"] != firm_id:
            code = "TRUST_FIRM_MISMATCH" if context_type == "TRUST" else "MATTER_FIRM_MISMATCH"
            raise DocumentEvidenceError(code)
        if context_type == "TRUST" and "trust_id" in doc.keys() and doc["trust_id"] not in (None, "", context_id):
            raise DocumentEvidenceError("DOCUMENT_TRUST_CONTEXT_MISMATCH")
        if context_type == "MATTER" and "matter_id" in doc.keys() and doc["matter_id"] not in (None, "", context_id):
            raise DocumentEvidenceError("DOCUMENT_MATTER_CONTEXT_MISMATCH")
        if source_reference_id:
            required = {"hub_program_source_references", "hub_programs"}
            if not required.issubset(tables):
                raise DocumentEvidenceError("P05_SOURCE_REFERENCE_OWNER_REQUIRES_REVIEW")
            source = connection.execute("""SELECT r.source_reference_id,p.firm_id
              FROM hub_program_source_references r
              JOIN hub_programs p ON p.program_id=r.program_id
              WHERE r.source_reference_id=?""", (source_reference_id,)).fetchone()
            if not source or source["firm_id"] != firm_id:
                raise DocumentEvidenceError("INVALID_CANONICAL_SOURCE_REFERENCE")
        prior = None
        if prior_relationship_id:
            prior = connection.execute("SELECT * FROM document_evidence_relationships WHERE relationship_id=?", (prior_relationship_id,)).fetchone()
            if not prior: raise DocumentEvidenceError("PRIOR_RELATIONSHIP_NOT_FOUND")
            scope = (firm_id, context_type, context_id, evidence_role)
            if tuple(prior[k] for k in ("firm_id","context_type","context_id","evidence_role")) != scope:
                raise DocumentEvidenceError("PRIOR_RELATIONSHIP_SCOPE_MISMATCH")
        rid = relationship_id or "DER-" + uuid.uuid4().hex[:12].upper()
        connection.execute("""INSERT INTO document_evidence_relationships
          (relationship_id,firm_id,context_type,context_id,document_id,evidence_role,
           relationship_state,classification,basis,provenance,decision_origin,human_confirmed,
           prior_relationship_id,source_reference_id,created_by,actor_capacity,created_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (rid,firm_id,context_type,context_id,document_id,evidence_role,relationship_state,
           classification,basis,provenance,decision_origin,1,prior_relationship_id,
           source_reference_id,created_by,actor_capacity,created_at or _now()))
        return rid


def resolve_document_evidence(db_path, *, firm_id, context_type, context_id):
    with sqlite3.connect(str(db_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = [dict(r) for r in connection.execute("""SELECT r.*,d.verified_content_sha256,d.source_revision_id
          FROM document_evidence_relationships r JOIN documents d ON d.document_id=r.document_id
          WHERE r.firm_id=? AND r.context_type=? AND r.context_id=?""",
          (firm_id,context_type,context_id))]
    predecessor_ids = {r["prior_relationship_id"] for r in rows if r["prior_relationship_id"]}
    terminals = [r for r in rows if r["relationship_id"] not in predecessor_ids and r["relationship_state"] == "ACTIVE"]
    grouped = {}
    for row in terminals: grouped.setdefault(row["evidence_role"], []).append(row)
    conflicts = [role for role, values in grouped.items() if len(values) > 1]
    return {"relationships": [values[0] for role, values in grouped.items() if len(values) == 1],
            "lineage": rows, "conflicts": conflicts}
