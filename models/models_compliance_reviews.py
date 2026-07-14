from dataclasses import dataclass
from datetime import datetime

from extensions import db


COMPLIANCE_REVIEW_STATES = {
    "draft",
    "opened",
    "under_review",
    "awaiting_information",
    "ready_for_disposition",
    "disposed",
    "closed",
    "superseded",
}

OPEN_COMPLIANCE_REVIEW_STATES = {
    "draft",
    "opened",
    "under_review",
    "awaiting_information",
    "ready_for_disposition",
}

CLOSED_COMPLIANCE_REVIEW_STATES = {
    "disposed",
    "closed",
    "superseded",
}

COMPLIANCE_REVIEW_TYPES = {
    "policy_compliance",
    "certificate_compliance",
    "execution_compliance",
    "recordkeeping_compliance",
    "governance_compliance",
    "fiduciary_compliance",
    "archive_and_continuity_compliance",
    "access_control_compliance",
    "institutional_standard_review",
}

COMPLIANCE_REQUIREMENT_TYPES = {
    "institutional_policy",
    "institutional_directive",
    "institutional_resolution",
    "governance_decision",
    "certificate_requirement",
    "execution_requirement",
    "contractual_provision",
    "statutory_or_regulatory_reference",
    "external_standard",
    "internal_control",
}

INTERNAL_COMPLIANCE_REQUIREMENT_TYPES = {
    "institutional_policy",
    "institutional_directive",
    "institutional_resolution",
    "governance_decision",
    "certificate_requirement",
    "execution_requirement",
    "internal_control",
}

COMPLIANCE_SOURCE_TYPES = {
    "system_observation",
    "matter",
    "trust",
    "certificate",
    "execution_session",
    "governance_record",
    "archive_record",
    "fiduciary_record",
    "document",
    "external_reference",
    "manual_institutional_review",
}

COMPLIANCE_REVIEW_PRIORITIES = {"low", "normal", "high", "urgent"}
COMPLIANCE_REVIEW_RISK_LEVELS = {"low", "moderate", "high", "critical"}

COMPLIANCE_REVIEW_DISPOSITIONS = {
    "compliant",
    "compliant_with_conditions",
    "not_compliant",
    "insufficient_information",
    "not_applicable",
    "referred_for_governance_action",
    "referred_for_remediation",
    "superseded",
    "withdrawn",
}

COMPLIANCE_REVIEW_EVENT_TYPES = {
    "compliance_review_created",
    "compliance_review_opened",
    "compliance_review_started",
    "compliance_information_requested",
    "compliance_information_received",
    "compliance_review_ready_for_disposition",
}

COMPLIANCE_REVIEW_TRANSITIONS = {
    ("draft", "open"): {
        "resulting_status": "opened",
        "event_type": "compliance_review_opened",
        "requires_reason": True,
        "requires_summary": True,
    },
    ("opened", "start_review"): {
        "resulting_status": "under_review",
        "event_type": "compliance_review_started",
        "requires_reason": True,
        "requires_summary": True,
    },
    ("under_review", "request_information"): {
        "resulting_status": "awaiting_information",
        "event_type": "compliance_information_requested",
        "requires_reason": True,
        "requires_summary": True,
    },
    ("awaiting_information", "resume_review"): {
        "resulting_status": "under_review",
        "event_type": "compliance_information_received",
        "requires_reason": True,
        "requires_summary": True,
    },
    ("under_review", "mark_ready_for_disposition"): {
        "resulting_status": "ready_for_disposition",
        "event_type": "compliance_review_ready_for_disposition",
        "requires_reason": True,
        "requires_summary": True,
    },
}

RESERVED_COMPLIANCE_REVIEW_ACTIONS = {
    "assign",
    "record_finding",
    "record_disposition",
    "approve_disposition",
    "close",
    "reopen",
    "supersede",
}


class ComplianceReview(db.Model):
    __tablename__ = "compliance_reviews"

    id = db.Column(db.Integer, primary_key=True)
    compliance_review_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    firm_id = db.Column(db.String(64), nullable=False, index=True)
    institution_id = db.Column(db.String(64), nullable=True, index=True)
    trust_id = db.Column(db.String(64), nullable=True, index=True)
    matter_id = db.Column(db.String(64), nullable=True, index=True)
    deployment_key = db.Column(db.String(120), nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    review_type = db.Column(db.String(80), nullable=False, index=True)
    question_presented = db.Column(db.Text, nullable=False)
    governing_requirement_type = db.Column(db.String(80), nullable=False, index=True)
    governing_requirement_id = db.Column(db.String(120), nullable=True, index=True)
    governing_requirement_label = db.Column(db.String(255), nullable=True)
    source_type = db.Column(db.String(80), nullable=False, index=True)
    source_id = db.Column(db.String(120), nullable=True, index=True)
    source_label = db.Column(db.String(255), nullable=True)
    scope_summary = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(80), nullable=False, default="draft", index=True)
    priority = db.Column(db.String(40), nullable=False, default="normal", index=True)
    risk_level = db.Column(db.String(40), nullable=False, default="moderate", index=True)
    review_owner = db.Column(db.String(255), nullable=True)
    assigned_to = db.Column(db.String(255), nullable=True)
    authority_basis = db.Column(db.Text, nullable=True)
    approval_required = db.Column(db.Boolean, nullable=False, default=False)
    approved_by = db.Column(db.String(255), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    finding = db.Column(db.Text, nullable=True)
    disposition = db.Column(db.String(80), nullable=True)
    disposition_basis = db.Column(db.Text, nullable=True)
    required_follow_up = db.Column(db.Text, nullable=True)
    opened_at = db.Column(db.DateTime, nullable=True)
    due_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_by = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = db.Column(db.Integer, nullable=False, default=1)
    idempotency_key = db.Column(db.String(160), nullable=True, unique=True)
    payload_hash = db.Column(db.String(64), nullable=True)


class ComplianceReviewEvent(db.Model):
    __tablename__ = "compliance_review_events"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(80), nullable=False, unique=True, index=True)
    compliance_review_id = db.Column(db.String(64), nullable=False, index=True)
    event_sequence = db.Column(db.Integer, nullable=False)
    event_type = db.Column(db.String(80), nullable=False, index=True)
    actor_id = db.Column(db.String(255), nullable=False)
    actor_label = db.Column(db.String(255), nullable=False)
    prior_status = db.Column(db.String(80), nullable=True)
    resulting_status = db.Column(db.String(80), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    reason = db.Column(db.Text, nullable=True)
    related_record_type = db.Column(db.String(80), nullable=True)
    related_record_id = db.Column(db.String(120), nullable=True)
    idempotency_key = db.Column(db.String(160), nullable=True)
    payload_hash = db.Column(db.String(64), nullable=True)
    expected_version = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class ComplianceReviewRelationship(db.Model):
    __tablename__ = "compliance_review_relationships"

    id = db.Column(db.Integer, primary_key=True)
    relationship_id = db.Column(db.String(80), nullable=False, unique=True, index=True)
    compliance_review_id = db.Column(db.String(64), nullable=False, index=True)
    relationship_type = db.Column(db.String(80), nullable=False, index=True)
    related_record_type = db.Column(db.String(80), nullable=False, index=True)
    related_record_id = db.Column(db.String(120), nullable=False, index=True)
    direction = db.Column(db.String(40), nullable=False, default="outbound")
    status = db.Column(db.String(40), nullable=False, default="active")
    created_by = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


@dataclass(frozen=True)
class ComplianceReviewResult:
    ok: bool
    status: str
    message: str = ""
    review: dict | None = None
    event: dict | None = None
    events: list | None = None
