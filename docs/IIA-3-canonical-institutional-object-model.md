# IIA-3 — Canonical Institutional Object Model (CIOM)

## Purpose

Define the permanent institutional object model for the Trustee App.

IIA-1 defines where information belongs.

IIA-2 defines how work moves.

IIA-3 defines what institutional objects exist.

## Core Principle

Every feature must be built from canonical institutional objects.

The app should not invent a new object model for every module.

## Primary Object Families

1. Identity Objects
2. Fiduciary Objects
3. Legal / Governance Objects
4. Property / Asset Objects
5. Instrument Objects
6. Workflow Objects
7. Evidence / Archive Objects
8. Knowledge / Research Objects
9. System Objects

---

# 1. Identity Objects

## Person

Represents a natural person.

Examples:
- Settlor
- Grantor
- Trustee
- Beneficiary
- Protector
- Advisor
- Witness
- Notary
- Family Member
- Operator

Required Fields:
- person_id
- full_name
- preferred_name
- role_context
- contact_information
- identity_status
- verification_status
- created_at
- updated_at

## Family

Represents a family grouping.

Required Fields:
- family_id
- family_name
- description
- primary_contacts
- related_people
- created_at
- updated_at

## Organization

Represents a non-person entity.

Examples:
- Firm
- Business
- Foundation
- Church
- Insurance Company
- Bank
- Government Agency
- Law Office
- Trustee Office

Required Fields:
- organization_id
- organization_name
- organization_type
- jurisdiction
- contact_information
- verification_status
- created_at
- updated_at

---

# 2. Fiduciary Objects

## Trust

Represents a trust record.

Examples:
- Revocable Trust
- Irrevocable Trust
- ILIT
- Dynasty Trust
- Pet Trust
- Firearms Trust
- Charitable Trust
- Business Trust
- Ecclesiastical Trust
- Special Needs Trust

Required Fields:
- trust_id
- trust_name
- trust_type
- jurisdiction
- governing_instrument
- status
- lifecycle_stage
- primary_matter_id
- created_at
- updated_at

## Matter

Represents an institutional case file or work container.

Required Fields:
- matter_id
- matter_name
- matter_type
- client_or_institution
- status
- priority
- risk_level
- governance_state
- archive_state
- created_at
- updated_at

## Fiduciary Role

Represents a person or organization acting in a fiduciary capacity.

Examples:
- Trustee
- Successor Trustee
- Trust Protector
- Executor
- Administrator
- Agent
- Advisor
- Custodian

Required Fields:
- role_id
- person_or_organization_id
- role_type
- linked_record_type
- linked_record_id
- appointment_basis
- acceptance_status
- authority_scope
- start_date
- end_date
- status

---

# 3. Legal / Governance Objects

## Relationship

Represents a formal relationship between records.

Examples:
- Person to Trust
- Trust to Matter
- Asset to Trust
- Document to Instrument
- Organization to Matter
- Trustee to Trust

Required Fields:
- relationship_id
- source_record_type
- source_record_id
- target_record_type
- target_record_id
- relationship_type
- purpose
- verification_status
- status
- created_at
- updated_at

## Governance Decision

Represents an institutional decision.

Required Fields:
- decision_id
- decision_type
- linked_record_type
- linked_record_id
- decision_summary
- decision_basis
- decision_status
- decided_by
- decided_at
- review_required
- archive_required

## Review

Represents a readiness, compliance, governance, or risk review.

Required Fields:
- review_id
- review_type
- linked_record_type
- linked_record_id
- review_status
- findings
- deficiencies
- recommendations
- reviewed_by
- reviewed_at
- next_action

## Risk Item

Represents a risk, warning, blocker, or concern.

Required Fields:
- risk_id
- linked_record_type
- linked_record_id
- risk_category
- risk_level
- risk_description
- mitigation_plan
- status
- created_at
- resolved_at

---

# 4. Property / Asset Objects

## Asset

Represents any asset or property interest.

Examples:
- Real Property
- Vehicle
- Bank Account
- Business Interest
- Insurance Policy
- Intellectual Property
- Personal Property
- Digital Asset
- Evidence Property

Required Fields:
- asset_id
- asset_name
- asset_type
- ownership_status
- linked_owner_record
- estimated_value
- title_status
- funding_status
- verification_status
- created_at
- updated_at

## Liability

Represents an obligation, debt, claim, lien, or encumbrance.

Required Fields:
- liability_id
- liability_type
- creditor_or_claimant
- linked_record_type
- linked_record_id
- amount
- status
- documentation_status
- created_at
- updated_at

## Transfer

Represents movement of an asset, document, or interest.

Required Fields:
- transfer_id
- transfer_type
- source_record
- destination_record
- subject_record
- transfer_status
- execution_status
- evidence_status
- archive_status
- created_at
- completed_at

---

# 5. Instrument Objects

## Instrument

Represents a formal fiduciary, legal, governance, or institutional instrument.

Examples:
- Trust Agreement
- Declaration of Trust
- Trustee Acceptance
- Assignment
- Certificate
- Minute
- Resolution
- Funding Schedule
- Appointment
- Resignation
- Removal
- Affidavit
- Notice
- Research Memo

Required Fields:
- instrument_id
- instrument_type
- instrument_title
- linked_record_type
- linked_record_id
- version
- status
- drafting_status
- review_status
- execution_status
- archive_status
- created_at
- updated_at

## Document

Represents a file or written output.

Required Fields:
- document_id
- document_title
- document_type
- file_path
- linked_record_type
- linked_record_id
- version
- file_hash
- review_status
- export_status
- archive_status
- created_at
- updated_at

## Certificate

Represents a certification, registry entry, or attestation.

Required Fields:
- certificate_id
- certificate_type
- linked_record_type
- linked_record_id
- issued_by
- issued_at
- verification_code
- status
- archive_status

---

# 6. Workflow Objects

## Task

Represents an assigned or pending action.

Required Fields:
- task_id
- task_title
- task_type
- linked_record_type
- linked_record_id
- assigned_to
- priority
- status
- due_date
- created_at
- completed_at

## Event

Represents something that happened.

Required Fields:
- event_id
- event_type
- linked_record_type
- linked_record_id
- event_summary
- actor
- event_time
- evidence_reference
- audit_reference

## Timeline Entry

Represents institutional chronology.

Required Fields:
- timeline_id
- linked_record_type
- linked_record_id
- event_type
- event_summary
- occurred_at
- recorded_by
- source_reference

## Notification

Represents a user-facing institutional alert.

Required Fields:
- notification_id
- notification_type
- linked_record_type
- linked_record_id
- message
- severity
- status
- created_at
- resolved_at

---

# 7. Evidence / Archive Objects

## Evidence Item

Represents proof, support, custody material, or substantiation.

Required Fields:
- evidence_id
- evidence_type
- linked_record_type
- linked_record_id
- source
- custody_status
- authenticity_status
- file_hash
- notes
- created_at
- archived_at

## Archive Record

Represents preserved institutional memory.

Required Fields:
- archive_id
- archive_type
- linked_record_type
- linked_record_id
- retention_category
- archive_status
- provenance_reference
- custody_reference
- created_at
- archived_at

## Provenance Record

Represents origin, chain, and authenticity metadata.

Required Fields:
- provenance_id
- linked_record_type
- linked_record_id
- origin_source
- creation_context
- custody_chain
- verification_status
- created_at
- updated_at

---

# 8. Knowledge / Research Objects

## Knowledge Article

Represents instructional or reference content.

Required Fields:
- article_id
- title
- category
- summary
- body
- status
- created_by
- created_at
- updated_at

## Research Project

Represents an exploratory or future module investigation.

Examples:
- ILIT Research
- Dynasty Trust Research
- Pet Trust Research
- Firearms Trust Research
- Ecclesiastical Trust Research

Required Fields:
- research_id
- title
- research_type
- status
- question
- findings
- risks
- recommendations
- linked_outputs
- created_at
- updated_at

## Template

Represents reusable content or forms.

Required Fields:
- template_id
- template_type
- title
- category
- version
- status
- required_inputs
- output_type
- created_at
- updated_at

---

# 9. System Objects

## User

Represents a system operator.

Required Fields:
- user_id
- username
- role
- firm_id
- status
- created_at
- updated_at

## Permission

Represents authorized access.

Required Fields:
- permission_id
- workspace
- module
- action
- role_or_user
- status

## Policy

Represents a system or institutional rule.

Required Fields:
- policy_id
- policy_type
- policy_name
- policy_value
- scope
- status
- updated_by
- updated_at

## Audit Entry

Represents immutable action history.

Required Fields:
- audit_id
- actor
- action
- linked_record_type
- linked_record_id
- summary
- timestamp
- hash_reference

---

# Universal Record Tabs

Every major institutional object should eventually expose:

- Overview
- People / Parties
- Relationships
- Timeline
- Documents
- Evidence
- Review
- Governance
- Compliance
- Reports
- Archive
- Notes

---

# Object Rules

Rule 1:
Every object has a stable ID.

Rule 2:
Every object has a lifecycle stage.

Rule 3:
Every object can have relationships.

Rule 4:
Every object can produce events.

Rule 5:
Every object can attach documents.

Rule 6:
Every object can produce evidence.

Rule 7:
Every object can be reviewed.

Rule 8:
Every object can be archived.

Rule 9:
Every object must be audit-aware.

Rule 10:
Every object must belong to an institutional context.

---

# Success Criteria

CIOM is successful when every future module can be described using existing canonical objects before new tables, pages, or routes are created.
