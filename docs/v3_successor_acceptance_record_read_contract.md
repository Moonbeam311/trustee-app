# V3 Structured Successor Acceptance Record and Read Contract

Status: `V3-THO-ACC-1A — STRUCTURED RECORD / READ CONTRACT`

## Canonical ownership

`successor_acceptances` owns only the institutional fact that a named canonical Fiduciary accepted a specific appointment/capacity for a specific Trust under a specific appointment/source context. Trust, Fiduciary, Document, Continuity, Execution, responsibility, and application authorization facts remain owned by their existing domains.

The additive schema is installed by `database.migrations_successor_acceptance`. The read-only boundary is `services.services_successor_acceptance`.

## Structured record

Required fields are acceptance, firm, Trust, and Fiduciary identifiers; appointment reference; role/capacity; appointment source reference; lifecycle state; recorder and recording time; provenance source; and the server-derived context fingerprint. Accepted records additionally require `accepted_at` and a document or external evidence reference.

Optional record fields are acceptance method, evidence references, a superseded-acceptance reference, and governed explanation. Trust/Fiduciary display facts are not copied into the record.

Lifecycle states are `PENDING_EVIDENCE`, `ACCEPTED_RECORDED`, `DECLINED_RECORDED`, `WITHDRAWN_RECORDED`, and `SUPERSEDED`. Designated without recorded acceptance is a derived absence, not an acceptance row. Accepted does not mean active, serving, activated, legally valid, or authorized application user.

## Canonical context and uniqueness

The fingerprint is a deterministic SHA-256 digest over normalized firm, Trust, Fiduciary, appointment, capacity, and appointment-source identity. The database uniquely constrains it. It is server-derived and cannot be replaced by caller input. Caller replay keys are outside this phase.

## Public read interface

- `derive_acceptance_context_fingerprint(...)`
- `get_successor_acceptance(acceptance_id, authorization_check=...)`
- `get_successor_acceptance_for_context(..., authorization_check=...)`
- `list_successor_acceptances_for_trust(trust_id, authorization_check=...)`

Every record read is active-firm scoped and requires an explicit caller authorization decision using acceptance and Trust identity. Missing, denied, and cross-firm records share a safe absent result. Reads perform no schema bootstrap or institutional mutation.

## Institutional boundaries

Acceptance does not create or alter Fiduciary authority, Continuity activation, operational responsibility, application access, Execution authority, or handoff acknowledgement. It does not prove appointment or legal validity. Continuity remains canonical owner of activation requirements and transitions, including any context-specific requirement to consider acceptance evidence.

Generated or historical acceptance documents do not become structured acceptance records automatically. Their classification remains `LEGACY DOCUMENT / ACCEPTANCE STATE NOT STRUCTURALLY VERIFIED` until a future separately governed evidence-backed recording operation is authorized.

## Exclusions and limitations

This phase supplies no acceptance creation, recording, lifecycle-transition, evidence-registration, route, form, template, permission, acknowledgement, or activation API. Exact write-role policy remains `NOT DOCUMENTED` and must be resolved before the later governed write-service phase.
