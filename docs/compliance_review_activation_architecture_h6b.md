# Compliance Review Activation Architecture H.6B

H.6B defines and validates the activation architecture but does not activate Compliance Review persistence in the normal database. Normal `trustee_app.db` must remain free of Compliance Review tables until a later controlled activation phase expressly authorizes the migration.

## Purpose

A Compliance Review is a permanent governed institutional record. It documents the subject reviewed, the authority to review it, the scope and standard applied, evidence examined, findings reached, remediation required, approval/certification, and append-only provenance.

A Compliance Review is not a generic note, checklist, or task. Its existence does not itself prove legal sufficiency, regulatory compliance, evidentiary authenticity, or institutional approval.

## Object Model

Minimum Compliance Review identity:

- `compliance_review_id`
- `firm_id`
- `institution_id`
- `matter_id`
- `trust_id`
- `related_object_type`
- `related_object_id`
- `related_object_label`
- `review_type`
- `title`
- `purpose`
- `scope`
- `review_standard`
- `jurisdiction`
- `status`
- `risk_level`
- `priority`
- `confidentiality_level`
- `initiated_by`
- `initiated_at`
- `assigned_reviewer`
- `issuing_authority`
- `authority_basis`
- `approval_required`
- `approved_by`
- `approved_at`
- `due_date`
- `completed_at`
- `closed_at`
- `reopened_at`
- `superseded_by`
- `created_by`
- `created_at`
- `updated_by`
- `updated_at`
- `version_number`
- `is_active`

Supported review types are governed labels: Governance Compliance Review, Trust Administration Review, Fiduciary Duty Review, Document Completeness Review, Execution Review, Funding Review, Asset Titling Review, Tax and Filing Review, Regulatory Review, Internal Control Review, Evidence Integrity Review, Archive and Retention Review, Continuity Readiness Review, Corrective Action Verification, and Custom Institutional Review.

## Lifecycle

Canonical lifecycle states:

- Draft
- Open
- In Review
- Findings Issued
- Remediation Required
- Remediation In Progress
- Pending Verification
- Pending Approval
- Approved
- Certified
- Closed
- Reopened
- Superseded
- Archived
- Cancelled

Valid transitions must be performed through a transition validator. Free-form status mutation is prohibited.

Authority rules:

- Draft may be opened by an authorized compliance initiator.
- Open may enter review when a reviewer is assigned.
- Findings may be issued only by an authorized reviewer.
- Findings are not editable after issuance except by amendment/supersession.
- Remediation Required requires an issued finding or approved exception.
- Pending Approval requires reviewer completion and any required remediation verification or exception approval.
- Approved requires maker-checker separation when the initiator is also the reviewer.
- Certified requires certification authority and an approved review.
- Closed requires certification, approved exception, or no-action authority.
- Reopened requires reopening authority and a reason.
- Superseded links to a successor review and preserves the old record.
- Archived records are immutable except for governed archive metadata.
- Cancelled is only available before material findings are issued.

Versioning is represented by `version_number` on the review and append-only audit entries for material amendments.

## Subject And Relationship Model

A review has one primary subject and may have secondary subjects, source records, related governance records, parent/child reviews, superseded reviews, and dependent reviews.

Supported subject contexts: Institution, Firm, Matter, Trust, Person or Fiduciary, Property or Asset, Document, Certificate, Instrument, Execution Session, Transfer, Funding Event, Intake, Governance Record, Archive Record, Continuity Record, Recovery Record, and External Reference.

Relationships are normalized in `compliance_review_subjects` and `compliance_review_relationships`. A single text field must not represent all relationships.

## Evidence Architecture

Evidence is recorded in `compliance_review_evidence` with:

- `compliance_evidence_id`
- `compliance_review_id`
- `evidence_type`
- `source_type`
- `source_id`
- `source_label`
- `document_id`
- `upload_id`
- `external_reference`
- `description`
- `relevance`
- `evidence_status`
- `verification_status`
- `verified_by`
- `verified_at`
- `integrity_reference`
- `added_by`
- `added_at`
- `removed_at`
- `removal_reason`

Evidence statuses: Identified, Requested, Received, Reviewed, Verified, Rejected, Superseded, Withdrawn.

Evidence existence, authenticity, integrity, relevance, and sufficiency are separate concepts. Linked records are not automatically authentic, integral, relevant, or sufficient.

## Findings Architecture

Findings are recorded in `compliance_review_findings` with:

- `compliance_finding_id`
- `compliance_review_id`
- `finding_number`
- `finding_type`
- `title`
- `description`
- `requirement_or_standard`
- `evidence_basis`
- `severity`
- `risk_level`
- `status`
- `disputed`
- `dispute_basis`
- `issued_by`
- `issued_at`
- `acknowledged_by`
- `acknowledged_at`
- `resolved_at`
- `superseded_by`
- `created_at`
- `updated_at`

Finding types: Compliant, Observation, Advisory, Deficiency, Material Deficiency, Control Failure, Documentation Gap, Evidence Gap, Procedural Failure, Authority Failure, Timing Failure, Integrity Concern, Exception, Not Applicable.

Severity and risk are separate. An Observation is not automatically a formal deficiency. H.6B does not create System Observation records.

## Remediation Architecture

Remediation is recorded in `compliance_review_remediations` with:

- `compliance_remediation_id`
- `compliance_review_id`
- `compliance_finding_id`
- `action_number`
- `required_action`
- `responsible_party_type`
- `responsible_party_id`
- `responsible_party_label`
- `due_date`
- `status`
- `completion_evidence`
- `completed_by`
- `completed_at`
- `verified_by`
- `verified_at`
- `verification_result`
- `exception_requested`
- `exception_basis`
- `exception_approved_by`
- `exception_approved_at`
- `closure_notes`
- `created_at`
- `updated_at`

Statuses: Proposed, Required, Assigned, In Progress, Submitted for Verification, Verified, Rejected, Overdue, Waived, Exception Approved, Closed, Superseded.

One finding may have multiple remediation actions. Overdue status is derived at read time and must not mutate the database during rendering.

## Approval And Certification

Approval authority includes initiation, assignment, findings issuance, remediation approval, exception approval, review approval, certification, closure, reopening, and archival authority.

Certification is represented in `compliance_review_certifications` with:

- `certification_id`
- `compliance_review_id`
- `certification_type`
- `certification_statement`
- `certified_by`
- `authority_basis`
- `certified_at`
- `effective_date`
- `expiration_date`
- `certification_status`
- `revoked_by`
- `revoked_at`
- `revocation_basis`

Self-approval is not silent. Maker-checker separation is required where the same actor would otherwise initiate, review, and approve a material action.

## Audit Ledger

`compliance_review_audit_ledger` is append-only and stores:

- `compliance_audit_id`
- `compliance_review_id`
- `entity_type`
- `entity_id`
- `action`
- `previous_state`
- `new_state`
- `note`
- `actor_id`
- `actor_role`
- `authority_basis`
- `created_at`
- `previous_hash`
- `entry_hash`
- `hash_algorithm`
- `firm_id`

Audit events include creation, assignment, transition, evidence addition, evidence verification, finding issuance, finding amendment, remediation assignment, remediation submission, remediation verification, approval, certification, closure, reopening, supersession, archival, attempted invalid transition, attempted unauthorized action, and migration activation.

Audit notes must not store sensitive full document contents, secrets, passwords, or raw private data.

## Database Schema

H.6B migration tables:

- `compliance_review_number_sequences`: public identifier sequencing; unique namespace/year.
- `compliance_reviews`: review identity, scope, lifecycle, authority, version, and compatibility fields.
- `compliance_review_subjects`: primary/secondary/source/parent/dependent subject links.
- `compliance_review_evidence`: evidence inventory and verification status.
- `compliance_review_findings`: governed findings and dispute state.
- `compliance_review_remediations`: corrective actions and verification state.
- `compliance_review_approvals`: maker-checker approval records.
- `compliance_review_certifications`: certification and revocation records.
- `compliance_review_relationships`: governed related-record links compatible with the existing read-only UI.
- `compliance_review_events`: lifecycle event stream compatible with H.6A read services.
- `compliance_review_audit_ledger`: append-only audit ledger.
- `compliance_review_activation_registry`: controlled activation metadata.

Permanent records use `ON DELETE RESTRICT`. Deletion is not the normal lifecycle; archival, inactive status, supersession, or revocation records are preferred.

## Identifiers

Identifier families:

- `CMP-YYYY-000001`: Compliance Review
- `CEV-YYYY-000001`: Compliance Evidence
- `CFN-YYYY-000001`: Compliance Finding
- `CRM-YYYY-000001`: Remediation
- `CAP-YYYY-000001`: Approval
- `CCT-YYYY-000001`: Certification
- `CRL-YYYY-000001`: Relationship
- `CAL-YYYY-000001`: Audit Ledger
- `CAR-YYYY-000001`: Activation Registry

Identifiers are allocated by explicit services or migrations, never by route rendering. Sequencing uses governed sequence tables and unique constraints, not bare `COUNT(*) + 1`.

## Authorization Boundary

Future action matrix:

| Action | Permission Basis | Additional Boundary | Response If Denied |
| --- | --- | --- | --- |
| View Compliance Workspace | Existing authenticated admin/workspace access | Firm scope | 403 |
| View Registry | Existing authenticated Compliance read surface | Firm/global scope | 403 |
| View Detail | Existing authenticated Compliance read surface | Firm/global scope and record visibility | 403 or 404 |
| Create Review | Proposed compliance review create authority | Activated foundation, firm scope, initiation authority | 403 |
| Edit Draft | Proposed compliance review edit authority | Draft only, creator/reviewer authority | 403/409 |
| Assign Reviewer | Proposed assignment authority | Maker-checker as needed | 403/409 |
| Add Evidence | Proposed evidence authority | Open review, evidence provenance | 403/409 |
| Verify Evidence | Proposed verification authority | Cannot verify own untrusted evidence silently | 403/409 |
| Issue Findings | Proposed findings authority | Review in progress, evidence basis | 403/409 |
| Assign Remediation | Proposed remediation authority | Issued finding or exception basis | 403/409 |
| Submit Remediation | Proposed responsible-party authority | Assigned action | 403/409 |
| Verify Remediation | Proposed verification authority | Separation from submitter where needed | 403/409 |
| Approve Exception | Proposed exception approval authority | Authority basis required | 403/409 |
| Approve Review | Proposed approval authority | Maker-checker separation | 403/409 |
| Certify Review | Proposed certification authority | Approved review | 403/409 |
| Close Review | Proposed closure authority | Approved/certified or exception | 403/409 |
| Reopen Review | Proposed reopening authority | Closed/certified/archive restrictions | 403/409 |
| Supersede Review | Proposed supersession authority | Successor link required | 403/409 |
| Archive Review | Proposed archive authority | Closed/certified record | 403/409 |
| Activate Persistence | Controlled operator authorization outside browser | Explicit migration token and approval record | 403 |
| Execute Migration | Command-line migration authority | Explicit database path and token | 403/refusal |

H.6B does not insert new permissions into the normal database. New permissions remain proposed until a later authorization migration analyzes and authorizes them.

## Response Semantics

- Foundation unavailable: HTTP 503; no record creation; no migration; no authorization implication; explicit activation boundary.
- Authorization denied: HTTP 403; no mutation; bounded audit event where appropriate after activation.
- Record not found: HTTP 404 after activation when a visible record does not exist.
- Invalid lifecycle transition: HTTP 409 or repository-standard conflict response; no mutation; attempted transition audit after activation.
- Validation failure: HTTP 400 or 422 according to repository convention.
- Activation not authorized: HTTP 403/refusal; no migration; no schema mutation.
- Migration failure: transaction rolled back, activation inactive, operator-safe message, details restricted to controlled logs.

These states must remain structurally distinct.

## Activation Registry

`compliance_review_activation_registry` records architecture defined, migration prepared, temporary validation, approval pending, authorized activation, executing, completed, verified, failed, rolled back, and revoked/disabled status where supported.

Minimum fields include activation id, module key, schema version, migration name, status, requester/approver, authority basis, target database identifier, pre/post hashes, backup reference, started/completed timestamps, rollback status/reference, verification status, verifier, and notes.

H.6B writes this registry only in temporary database copies.

## Migration Boundary

`migrations/activate_compliance_review_foundation.py` is command-line only. It requires:

- explicit `--database PATH`;
- exactly one of `--dry-run` or `--apply`;
- explicit `--activation-token H6B-TEMPORARY-ACTIVATION`;
- target outside the repository;
- refusal of `trustee_app.db`;
- transactional creation of tables, indexes, constraints, and activation metadata;
- no sample records;
- idempotent repeat apply;
- rollback on failure;
- refusal of partial/conflicting schema.

It must not run during app import, login, route rendering, or request processing.

## Service Boundary

Before activation:

- registry/detail read routes keep bounded unavailable behavior when tables are absent;
- write services fail closed with foundation unavailable;
- no table creation occurs;
- no migration occurs.

After temporary activation:

- read services may list temporary records;
- create/transition services may be exercised only against temporary databases with explicit `DB_PATH`;
- lifecycle validation still governs transitions;
- future write routes remain unexposed in H.6B.

## Route Architecture

Current H.6A routes:

- `GET /compliance/reviews`: read-only registry; 503 when foundation unavailable.
- `GET /compliance/reviews/<compliance_review_id>`: read-only detail; 503 before activation; 404 for missing records after activation.

Future read routes: evidence, findings, remediation, and audit tabs under a review.

Future write routes: create, assign, evidence, findings, remediation, approve, certify, close, reopen, archive. They must be POST-only, CSRF protected, activation gated, permission checked, lifecycle checked, and audited.

Activation must remain a controlled command-line migration plus institutional approval record, not a simple browser button.

## UI Information Architecture

Registry columns: Review ID, Title, Review Type, Primary Subject, Status, Risk Level, Assigned Reviewer, Due Date, Findings Count, Open Remediation Count, Certification Status, Last Updated, Action.

Detail sections: Review Summary, Authority and Scope, Subject Context, Evidence, Findings, Remediation, Approval, Certification, Relationships, Audit History, Archive Status.

Before normal activation, the normal environment retains the bounded unavailable state and must not render empty activated tables.

## Rollback

Rollback strategy:

- migration refuses normal DB in H.6B;
- temporary validation proves transaction rollback on forced failure;
- activation metadata is inserted only after schema verification inside the transaction;
- partial schemas are refused instead of silently repaired;
- normal H.6A rollback backup remains retained and untouched.

## Temporary Validation

H.6B validates dry-run, apply, repeat apply, forced rollback, partial-schema conflict, import-read-only before activation, import-read-only after temporary activation, request behavior before activation, request behavior after temporary activation, lifecycle validator, and authorization response separation on temporary database copies only.

## Remaining Risks

- Final permission names are proposed, not inserted.
- Browser write workflows are intentionally not exposed in H.6B.
- System Observation integration remains intentionally unactivated.
- Normal database activation requires a later controlled phase with operator approval and backup procedure.

## Next Controlled Phase

POST-V2-17Q-H.6C — Compliance Review Temporary Activation, Service Validation, and Operator Workflow
