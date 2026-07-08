from datetime import datetime

from extensions import db


class GovernanceNumberSequence(db.Model):
    __tablename__ = "governance_number_sequences"

    id = db.Column(db.Integer, primary_key=True)
    firm_id = db.Column(db.String(64), nullable=False, default="FIRM-001", index=True)
    prefix = db.Column(db.String(12), nullable=False, index=True)
    sequence_year = db.Column(db.Integer, nullable=False, index=True)
    last_number = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint(
            "firm_id",
            "prefix",
            "sequence_year",
            name="uq_governance_number_sequence_scope",
        ),
    )


class InstitutionalDirective(db.Model):
    __tablename__ = "institutional_directives"

    id = db.Column(db.Integer, primary_key=True)
    directive_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    firm_id = db.Column(db.String(64), nullable=False, default="FIRM-001", index=True)
    directive_code = db.Column(db.String(64), nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    directive_type = db.Column(db.String(80), nullable=False, default="Governance Directive")
    status = db.Column(db.String(50), nullable=False, default="Draft", index=True)
    authority = db.Column(db.String(255), nullable=True)
    issuing_authority = db.Column(db.String(255), nullable=True)
    authority_basis = db.Column(db.Text, nullable=True)
    approval_required = db.Column(db.Boolean, nullable=False, default=False)
    approved_by = db.Column(db.String(255), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    source_type = db.Column(db.String(80), nullable=True, index=True)
    source_id = db.Column(db.String(120), nullable=True, index=True)
    source_label = db.Column(db.String(255), nullable=True)
    source_notes = db.Column(db.Text, nullable=True)
    issued_by = db.Column(db.String(255), nullable=True)
    issued_at = db.Column(db.DateTime, nullable=True)
    effective_at = db.Column(db.DateTime, nullable=True)
    retired_at = db.Column(db.DateTime, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    instruction = db.Column(db.Text, nullable=True)
    rationale = db.Column(db.Text, nullable=True)
    scope = db.Column(db.Text, nullable=True)
    milestone_plan = db.Column(db.Text, nullable=True)
    completion_record = db.Column(db.Text, nullable=True)
    version_label = db.Column(db.String(40), nullable=False, default="v1")
    supersedes_id = db.Column(db.String(64), nullable=True, index=True)
    superseded_by_id = db.Column(db.String(64), nullable=True, index=True)
    created_by = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class DirectiveImplementationEntry(db.Model):
    __tablename__ = "directive_implementation_entries"

    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    firm_id = db.Column(db.String(64), nullable=False, default="FIRM-001", index=True)
    directive_id = db.Column(db.String(64), nullable=False, index=True)
    action_type = db.Column(db.String(80), nullable=True, index=True)
    action_summary = db.Column(db.Text, nullable=False)
    performed_by = db.Column(db.String(255), nullable=True)
    performed_at = db.Column(db.DateTime, nullable=True, index=True)
    result_status = db.Column(db.String(80), nullable=False, default="Recorded", index=True)
    evidence_reference = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class InstitutionalDecision(db.Model):
    __tablename__ = "institutional_decisions"

    id = db.Column(db.Integer, primary_key=True)
    decision_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    firm_id = db.Column(db.String(64), nullable=False, default="FIRM-001", index=True)
    title = db.Column(db.String(255), nullable=False)
    decision_type = db.Column(db.String(80), nullable=False, default="Governance Decision")
    status = db.Column(db.String(50), nullable=False, default="Draft", index=True)
    authority = db.Column(db.String(255), nullable=True)
    decided_by = db.Column(db.String(255), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)
    effective_at = db.Column(db.DateTime, nullable=True)
    retired_at = db.Column(db.DateTime, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    decision_text = db.Column(db.Text, nullable=True)
    rationale = db.Column(db.Text, nullable=True)
    approval_history = db.Column(db.Text, nullable=True)
    version_label = db.Column(db.String(40), nullable=False, default="v1")
    supersedes_id = db.Column(db.String(64), nullable=True, index=True)
    superseded_by_id = db.Column(db.String(64), nullable=True, index=True)
    created_by = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class InstitutionalPolicy(db.Model):
    __tablename__ = "institutional_policies"

    id = db.Column(db.Integer, primary_key=True)
    policy_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    firm_id = db.Column(db.String(64), nullable=False, default="FIRM-001", index=True)
    title = db.Column(db.String(255), nullable=False)
    policy_area = db.Column(db.String(120), nullable=True, index=True)
    status = db.Column(db.String(50), nullable=False, default="Draft", index=True)
    authority = db.Column(db.String(255), nullable=True)
    approved_by = db.Column(db.String(255), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    effective_at = db.Column(db.DateTime, nullable=True)
    retired_at = db.Column(db.DateTime, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    policy_text = db.Column(db.Text, nullable=True)
    rationale = db.Column(db.Text, nullable=True)
    version_label = db.Column(db.String(40), nullable=False, default="v1")
    supersedes_id = db.Column(db.String(64), nullable=True, index=True)
    superseded_by_id = db.Column(db.String(64), nullable=True, index=True)
    created_by = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class InstitutionalResolution(db.Model):
    __tablename__ = "institutional_resolutions"

    id = db.Column(db.Integer, primary_key=True)
    resolution_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    firm_id = db.Column(db.String(64), nullable=False, default="FIRM-001", index=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Draft", index=True)
    authority = db.Column(db.String(255), nullable=True)
    resolved_by = db.Column(db.String(255), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    effective_at = db.Column(db.DateTime, nullable=True)
    retired_at = db.Column(db.DateTime, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    resolution_text = db.Column(db.Text, nullable=True)
    recitals = db.Column(db.Text, nullable=True)
    approval_history = db.Column(db.Text, nullable=True)
    version_label = db.Column(db.String(40), nullable=False, default="v1")
    supersedes_id = db.Column(db.String(64), nullable=True, index=True)
    superseded_by_id = db.Column(db.String(64), nullable=True, index=True)
    created_by = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class InstitutionalMemorandum(db.Model):
    __tablename__ = "institutional_memoranda"

    id = db.Column(db.Integer, primary_key=True)
    memorandum_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    firm_id = db.Column(db.String(64), nullable=False, default="FIRM-001", index=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Draft", index=True)
    authority = db.Column(db.String(255), nullable=True)
    authored_by = db.Column(db.String(255), nullable=True)
    issued_at = db.Column(db.DateTime, nullable=True)
    effective_at = db.Column(db.DateTime, nullable=True)
    retired_at = db.Column(db.DateTime, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    memorandum_text = db.Column(db.Text, nullable=True)
    rationale = db.Column(db.Text, nullable=True)
    version_label = db.Column(db.String(40), nullable=False, default="v1")
    supersedes_id = db.Column(db.String(64), nullable=True, index=True)
    superseded_by_id = db.Column(db.String(64), nullable=True, index=True)
    created_by = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class InstitutionalOpinion(db.Model):
    __tablename__ = "institutional_opinions"

    id = db.Column(db.Integer, primary_key=True)
    opinion_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    firm_id = db.Column(db.String(64), nullable=False, default="FIRM-001", index=True)
    title = db.Column(db.String(255), nullable=False)
    opinion_type = db.Column(db.String(80), nullable=False, default="Governance Opinion")
    status = db.Column(db.String(50), nullable=False, default="Draft", index=True)
    authority = db.Column(db.String(255), nullable=True)
    authored_by = db.Column(db.String(255), nullable=True)
    issued_at = db.Column(db.DateTime, nullable=True)
    effective_at = db.Column(db.DateTime, nullable=True)
    retired_at = db.Column(db.DateTime, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    opinion_text = db.Column(db.Text, nullable=True)
    findings = db.Column(db.Text, nullable=True)
    rationale = db.Column(db.Text, nullable=True)
    version_label = db.Column(db.String(40), nullable=False, default="v1")
    supersedes_id = db.Column(db.String(64), nullable=True, index=True)
    superseded_by_id = db.Column(db.String(64), nullable=True, index=True)
    created_by = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class InstitutionalPrecedent(db.Model):
    __tablename__ = "institutional_precedents"

    id = db.Column(db.Integer, primary_key=True)
    precedent_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    firm_id = db.Column(db.String(64), nullable=False, default="FIRM-001", index=True)
    title = db.Column(db.String(255), nullable=False)
    precedent_type = db.Column(db.String(80), nullable=False, default="Governance Precedent")
    status = db.Column(db.String(50), nullable=False, default="Active", index=True)
    authority = db.Column(db.String(255), nullable=True)
    source_object_type = db.Column(db.String(80), nullable=True, index=True)
    source_object_id = db.Column(db.String(80), nullable=True, index=True)
    established_at = db.Column(db.DateTime, nullable=True)
    effective_at = db.Column(db.DateTime, nullable=True)
    retired_at = db.Column(db.DateTime, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    precedent_text = db.Column(db.Text, nullable=True)
    rationale = db.Column(db.Text, nullable=True)
    version_label = db.Column(db.String(40), nullable=False, default="v1")
    supersedes_id = db.Column(db.String(64), nullable=True, index=True)
    superseded_by_id = db.Column(db.String(64), nullable=True, index=True)
    created_by = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class GovernanceRelationship(db.Model):
    __tablename__ = "governance_relationships"

    id = db.Column(db.Integer, primary_key=True)
    relationship_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    firm_id = db.Column(db.String(64), nullable=False, default="FIRM-001", index=True)
    source_object_type = db.Column(db.String(80), nullable=False, index=True)
    source_object_id = db.Column(db.String(80), nullable=False, index=True)
    relationship_type = db.Column(db.String(80), nullable=False, index=True)
    target_object_type = db.Column(db.String(80), nullable=False, index=True)
    target_object_id = db.Column(db.String(80), nullable=False, index=True)
    authority = db.Column(db.String(255), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Active", index=True)
    effective_at = db.Column(db.DateTime, nullable=True)
    retired_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
