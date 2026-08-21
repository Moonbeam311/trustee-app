# V3 Governed Successor Acceptance Lifecycle Service Contract

Status: `V3-THO-ACC-1B — GOVERNED WRITE SERVICE`

## Permissions and actors

The dedicated permissions are:

- `record_successor_acceptance` for maker/recorder actions.
- `verify_successor_acceptance` for independent review, finalization, rejection, and supersession review.

The existing default-role convention maps both permissions to Admin. Trustee and Viewer receive no default Acceptance write mapping. Effective permission, active-firm user identity, and explicit Trust/Fiduciary access are all required. Successor status, Fiduciary status or `authority_scope`, Continuity state, and authentication alone grant no Acceptance write authority.

A maker cannot review the same proposed transition. Matching maker and reviewer actors fail closed even if that actor holds both permissions.

## Public lifecycle interface

- `propose_successor_acceptance(...)` creates one idempotent `PENDING_EVIDENCE` record and immutable transition proposal.
- `attach_acceptance_evidence(...)` associates non-conflicting evidence with a pending record without finalizing it.
- `propose_acceptance_transition(...)` proposes an evidence-backed withdrawal or supersession without changing current status.
- `review_acceptance_transition(...)` independently approves/finalizes or rejects an exact proposal.
- `list_acceptance_events(...)` returns immutable Acceptance lifecycle provenance through the existing read authorization gate.

The 1A read-only service remains unchanged.

## Lifecycle

Implemented transitions are:

- `PENDING_EVIDENCE` to `ACCEPTED_RECORDED`, `DECLINED_RECORDED`, or `SUPERSEDED`.
- `ACCEPTED_RECORDED` to `WITHDRAWN_RECORDED` or `SUPERSEDED`.
- `DECLINED_RECORDED` to `SUPERSEDED`.
- `WITHDRAWN_RECORDED` to `SUPERSEDED`.
- `SUPERSEDED` is terminal.

Every finalized state requires a separately authorized reviewer and evidence. Decline, withdrawal, and supersession remain institutional records rather than legal conclusions. Supersession preserves prior events and never deletes the prior record.

## Evidence, idempotency, and provenance

Generated documents do not record acceptance. A document evidence reference must resolve through the canonical Document contract in the Acceptance Trust. Governed external references may also supply evidence. Attachment alone never finalizes a state.

The server-derived context fingerprint remains canonical duplicate prevention. Exact replay returns the existing record without a new record or proposal event. No caller idempotency-key behavior is implemented.

Immutable `successor_acceptance_events` preserve maker, reviewer, timestamps, prior/resulting states, evidence references, firm, Trust, Fiduciary, reason, related proposal, and canonical fingerprint. This is the established domain-event provenance pattern, not a second generic audit subsystem.

## Explicitly excluded effects

Acceptance writes do not alter Trust facts, Fiduciary role or authority, Continuity profiles/readiness/activation/responsibility, users, roles, permissions, authentication, Execution authority, Document generation, or handoff acknowledgement. Acceptance is evidence of a recorded decision only and does not establish appointment or legal validity.
