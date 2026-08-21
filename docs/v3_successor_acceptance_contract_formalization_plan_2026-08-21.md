# V3 Successor Acceptance Contract Formalization Plan

Date: 2026-08-21

Phase: `V3-THO-ACC-PLAN-1`

Status: `COMPLETE / IMPLEMENTATION PLAN READY`

## 1. Control Status

This plan was completed under the active `V3-THO-ACC-PLAN-1` planning boundary. It authorizes no acceptance implementation. Source data, protected records, and suspended P03 work remained preserved.

## 2. Current Acceptance Baseline

- `trusts.successor_trustee_name` is a free-text designation, not acceptance.
- Fiduciary records describe role, capacity, authority scope, appointment dates, and status but contain no canonical acceptance state.
- Existing successor-acceptance documents are derived outputs; generation neither persists nor proves acceptance.
- Continuity responsibility metadata is not a governed successor-appointment acceptance lifecycle.
- Transfer trustee acceptance is transfer-specific, not successor appointment acceptance.
- No canonical handoff receipt/review acknowledgement exists.
- Acceptance currently grants no application permission and triggers no Continuity activation.

## 3. Canonical Acceptance Definition

Successor acceptance is a governed institutional fact recording that a specifically identified successor fiduciary accepted a specifically identified appointment or capacity for a specifically identified Trust under a specifically recorded appointment/source context.

It is not proof of legal validity, active service, Continuity activation, operational responsibility, application access, execution authority, or handoff receipt.

## 4. Structured Record Design

A separate successor-acceptance source domain should reference existing Trust, Fiduciary, appointment, and evidence records rather than copy them.

| Field | Classification |
|---|---|
| `acceptance_id`, `firm_id`, `trust_id`, `fiduciary_id` | REQUIRED |
| appointment/designation reference, role/capacity, appointment/source reference | REQUIRED |
| `acceptance_status`, `recorded_by`, `recorded_at`, provenance/source | REQUIRED |
| server acceptance-context fingerprint | REQUIRED |
| `accepted_at` | REQUIRED for `ACCEPTED_RECORDED` |
| `acceptance_method` | CONDITIONAL |
| evidence document ID or external evidence reference | OPTIONAL individually; governed evidence is required for accepted state |
| caller idempotency key | OPTIONAL transport metadata |
| `supersedes_acceptance_id`, governed explanation/notes | OPTIONAL |
| successor/Trust names and current designation state | DERIVED from canonical sources |
| witness/notary fields, signature-hash requirements, legal-effectiveness date, jurisdiction attestations | NOT DOCUMENTED |

## 5. Lifecycle Model

Planned evidence-oriented states:

- `PENDING_EVIDENCE`
- `ACCEPTED_RECORDED`
- `DECLINED_RECORDED`
- `WITHDRAWN_RECORDED`
- `SUPERSEDED`

“Successor designated / acceptance not recorded” is a derived condition, not proof of an acceptance transaction. Pending may transition to accepted, declined, or superseded; accepted may transition to withdrawn or superseded; declined and withdrawn may transition to superseded; superseded is terminal. History is not deleted or silently overwritten.

`ACCEPTED_RECORDED` never means active, serving, Continuity-activated, or authorized application user.

## 6. Idempotency Contract

The server-derived acceptance-context fingerprint is the canonical institutional idempotency key. It derives from immutable/context-defining firm, Trust, successor fiduciary, appointment/capacity, and appointment/source identity.

- Exact replay returns the existing institutional result without a duplicate record or event.
- Different caller keys for the same canonical context still resolve to one institutional acceptance.
- Materially different appointment context produces a different fingerprint.
- New evidence may append provenance where institutional meaning is unchanged.
- Status changes require explicit governed transitions.
- Superseded contexts cannot be silently reused.
- Withdrawal or administrative invalidation requires actor, time, reason, and immutable provenance.

A caller key may be supported only as optional request replay protection. It cannot replace the fingerprint, bypass duplicate detection, alter scope/lifecycle, or become institutional truth. Reusing one caller key for materially different canonical contexts fails safely.

## 7. Evidence Contract

The contract distinguishes document generated, document executed, and acceptance recorded. `ACCEPTED_RECORDED` requires governed evidence linked by the Acceptance service. Evidence may reference a registered executed document, governed external document reference, or an explicitly recorded institutional evidence event where existing architecture supports it.

Evidence provenance includes type, source reference, recorder, observation/receipt time, and available integrity metadata. Recording evidence makes no unsupported legal-sufficiency claim.

## 8. Document Contract

An acceptance document may be generated from authorized canonical context. Generation is derived output and neither creates nor transitions acceptance. An executed document becomes evidence only after registration and explicit linking during an evidence-backed Acceptance service transition. Document finalization, evidence registration, and acceptance recording remain separately traceable.

## 9. Fiduciary Authority Boundary

Acceptance remains separately owned. Fiduciary reads may later expose a linked acceptance summary, but acceptance does not create authority, broaden `authority_scope`, prove appointment validity, change Fiduciary status automatically, or grant application permissions.

## 10. Continuity Activation Boundary

Successor acceptance is not a universal or automatic prerequisite for Continuity activation. A specific activation may require it only when an authoritative governed source expressly requires it, including a governing Trust record, appointment terms, an authorized activation plan, or another controlling institutional record.

`ACCEPTANCE_RECORDED != CONTINUITY_ACTIVATED`.

Continuity remains canonical owner of activation requirements and transitions. Acceptance may expose evidence to readiness decisions but never owns, performs, or silently triggers activation. Software must not manufacture a prerequisite absent an authoritative requirement.

## 11. Responsibility Boundary

Acceptance does not assign active responsibility. Existing Continuity responsibility records remain canonical. A separate governed responsibility assignment/transition is required; no second responsibility system is created.

## 12. Application Access Boundary

Acceptance never creates a user, assigns a role, or grants a permission. Application access remains governed by the existing authorization system. Successor or Fiduciary status cannot supply application authorization.

## 13. Handoff Acknowledgement Boundary

Appointment acceptance and acknowledgement of handoff receipt/review are separate facts. No current canonical acknowledgement record was identified. It remains a later separately audited, planned, and authorized concern.

## 14. Provenance Contract

Creation and every lifecycle transition preserve actor/user, event time, firm/Trust/Fiduciary/appointment context, evidence/source reference, prior and resulting status, transition basis, superseded-record reference, and immutable audit/event reference. Existing audit/event infrastructure must be reused where suitable; no second generic audit subsystem is authorized.

## 15. Authorization Contract

Read access requires authenticated Trust access and firm scope. Existing document-generation permissions remain unchanged. Roles allowed to record, verify, supersede, withdraw, or attach acceptance evidence remain `NOT DOCUMENTED` and must be decided before the governed write-service phase. This does not block the first read-only implementation phase.

## 16. Failure / Conflict Model

- Missing Trust/Fiduciary: safe not found.
- Cross-firm mismatch: deny without existence disclosure.
- Fiduciary not linked to the Trust/appointment: reject.
- Missing appointment/source reference: reject recording.
- Missing evidence: do not enter `ACCEPTED_RECORDED`.
- Exact duplicate: return existing record idempotently.
- Conflicting records: fail closed; require explicit reconciliation/supersession.
- Superseded context: reject ordinary submission; require governed review.
- Withdrawal: require authorized actor, reason, and event.
- Malformed evidence reference: reject.

No silent correction or automatic legal conclusion is permitted.

## 17. Source-of-Truth Map

| Meaning | Canonical owner | Operation | Evidence/provenance | Acceptance side effect |
|---|---|---|---|---|
| Designation | Trust/Fiduciary | Read | Governing source reference | None |
| Appointment/capacity | Fiduciary/appointment owner | Read | Appointment source | None |
| Acceptance state | Acceptance domain | Read/write | Evidence plus immutable transition provenance | Acceptance record/event only |
| Acceptance evidence | Document/evidence owner | Read/link | Registered evidence origin | Explicit link only |
| Fiduciary role/authority | Fiduciary | Read | Native authority provenance | None |
| Continuity activation | Continuity | Separate write | Activation requirement/event | Never automatic |
| Responsibility | Continuity responsibility owner | Separate write | Assignment provenance | Never automatic |
| Application access | User/role/permission owner | Separate write | Security audit | Never automatic |
| Handoff acknowledgement | Future separate owner | Separate contract | NOT DOCUMENTED | None |

## 18. Schema Decision

Recommendation: a new dedicated successor-acceptance table with reuse of established immutable event/audit infrastructure.

Acceptance has independent institutional meaning, identity, lifecycle, evidence, idempotency, provenance, and supersession. A dedicated table does not duplicate Trust, Fiduciary, Continuity, or Document truth because it stores only the acceptance fact and references those canonical records. No table is created in this planning phase.

## 19. Legacy / Backward-Compatibility Plan

Existing generated acceptance documents are classified:

`LEGACY DOCUMENT / ACCEPTANCE STATE NOT STRUCTURALLY VERIFIED`

They remain preserved without destructive migration. Existence/generation cannot be interpreted as acceptance, and no automatic backfill is allowed. A future authorized reconciliation may explicitly record acceptance after operator review of evidence and provenance.

## 20. Implementation Phase Sequence

All phases are proposed and require separate activation.

### V3-THO-ACC-1A — Structured Successor Acceptance Record and Read Contract

- Objective: bounded table/migration, canonical read service, contract documentation, and disposable-DB tests.
- Allowed: Acceptance persistence/read owner, narrow tests/docs, control files.
- Prohibited: routes/templates, write transitions, Continuity/permission/acknowledgement/P03/P04 changes.
- Boundary: public read service only; no mutation API.
- Tests: identity, firm/Trust scope, safe not-found, lifecycle reads, legacy neutrality, source DB preservation.
- Browser: not required.
- Stop: duplicated source truth, unsafe migration, leakage, or required alteration of certified contracts.

### V3-THO-ACC-1B — Governed Acceptance Recording and Lifecycle Service

- Objective: explicit recording/transitions, idempotency, evidence validation, immutable provenance.
- Prohibited: UI, Continuity activation, responsibility transfer, permission grants, acknowledgement.
- Tests: lifecycle, conflict/replay, fingerprint/caller-key semantics, provenance, authorization, isolation.
- Stop: write-role policy remains undocumented or existing audit infrastructure cannot be reused.

### V3-THO-ACC-1C — Acceptance Evidence and Document Adapter

- Objective: register/link executed evidence while preserving producer/adapter separation.
- Prohibited: transition from generation, broad template redesign, Continuity mutation.
- Tests: generated/executed/recorded separation, integrity references, no implicit transition.
- Browser: only if visible UI changes.

### V3-THO-ACC-1D — Handoff Workspace Acceptance Visibility

- Objective: scoped read-only aggregate/workspace visibility.
- Prohibited: recording controls, activation, responsibility, permission mutation.
- Tests: scope, no mutation, legal-language separation, secret exclusion.
- Browser: required.

### V3-THO-ACC-1E — Continuity Acceptance Evidence Boundary

- Objective: allow Continuity readiness to consume acceptance evidence only when an authoritative activation requirement requires it.
- Prohibited: universal prerequisite, silent activation, responsibility transfer, lifecycle redesign.
- Tests: required/not-required contexts and no activation side effect.
- Stop: no authoritative requirement source or state-machine redesign required.

### V3-THO-ACC-1F — End-to-End Regression and Browser Certification

- Objective: certify scope, lifecycle, evidence, authorization, provenance, compatibility, and UI.
- Prohibited: new semantics or unrelated repair.
- Tests: full disposable-DB regression and required browser certification.

Handoff acknowledgement remains outside this sequence pending separate authorization.

## 21. Exact First Implementation Phase

`V3-THO-ACC-1A — Structured Successor Acceptance Record and Read Contract`

It is authorized next but not active only after this plan and control closure are preserved. This plan does not begin it.

## 22. Source DB Preservation

Preserved SHA-256: `3fcbbe1092072c47fe7e43fb1ab075f6ff626079511c948a1275936776b71d3c`.

## 23. P03 Preservation

`V3-MOD-WLH-P03C.4C` remains preserved, suspended, and unstaged. This plan has no P03 dependency.

## 24. Protected Record Result

Protected records remain governed by the V3 guard and passed at planning closure.

## 25. Final Planning Disposition

`V3-THO-ACC-PLAN-1 — COMPLETE / IMPLEMENTATION PLAN READY`

The two policy blockers were resolved. Exact write-role policy remains visibly `NOT DOCUMENTED` and is a stop condition for the later write-service phase, not the read-only first phase.

## 26. Operator Policy Decision Locks

### Acceptance versus Continuity activation

- Acceptance is not a universal or automatic activation prerequisite.
- Acceptance and activation are separate governed facts.
- Acceptance is required for a specific activation only where an authoritative governed source expressly requires it.
- Acceptance never silently triggers activation.
- Continuity owns activation requirements and transitions; Acceptance only exposes evidence.

### Institutional and transport idempotency

- The server-derived context fingerprint is canonical institutional duplicate prevention.
- An optional caller key is request replay protection only.
- It cannot replace the fingerprint, create duplicates, change scope/lifecycle, or bypass detection.
- One caller key reused across materially different contexts fails safely.
- Different caller keys for one canonical context still produce one institutional acceptance.

### Locked semantic separations

- `DESIGNATION != ACCEPTANCE`
- `ACCEPTANCE != FIDUCIARY AUTHORITY`
- `ACCEPTANCE != CONTINUITY ACTIVATION`
- `ACCEPTANCE != ACTIVE OPERATIONAL RESPONSIBILITY`
- `ACCEPTANCE != APPLICATION ACCESS`
- `ACCEPTANCE != EXECUTION AUTHORITY`
- `ACCEPTANCE != HANDOFF ACKNOWLEDGEMENT`
- `DOCUMENT GENERATED != DOCUMENT EXECUTED`
- `DOCUMENT EXECUTED != ACCEPTANCE RECORDED` unless the governed Acceptance service expressly records the evidence-backed transition.
