# V3 Continuity Acceptance Evidence Boundary Contract

Status: `V3-THO-ACC-1E` bounded read-only integration.

## Ownership and public interface

`services/services_continuity_acceptance_evidence.py` owns no persistence. Its
public `get_continuity_acceptance_evidence(...)` function composes the canonical
Trust–Continuity context adapter, Successor Acceptance read contract, and
Acceptance evidence adapter. Acceptance owns the acceptance fact and evidence
references. Continuity retains exclusive ownership of readiness, activation
requirements, activation transitions, responsibilities, and Continuity events.

The caller must supply explicit Trust, Continuity, Fiduciary, Acceptance, and
Document authorization decisions. The result is scoped to one active firm, one
linked Continuity Profile, its exact Trust, and (when supplied) one Fiduciary.
Missing, inaccessible, unlinked, cross-firm, wrong-Trust, and mismatched-context
requests fail closed without disclosure.

## Evidence result

The boundary exposes the Acceptance identifier and canonical lifecycle state,
Fiduciary and appointment/capacity context, accepted timestamp, Acceptance
provenance, and safely authorized evidence descriptions. It preserves
`ACCEPTED_RECORDED`, `PENDING_EVIDENCE`, and the canonical declined, withdrawn,
or superseded states instead of flattening them into a boolean. Absence is
reported as `DESIGNATED / ACCEPTANCE NOT RECORDED`; legacy document presence is
never promoted into structured Acceptance.

## Requirement and readiness semantics

The current Continuity schema has no structured, canonical mechanism that says
Successor Acceptance is required for a particular activation. The free-text
`required_evidence` field on an activation plan is not safely interpreted as an
Acceptance policy. Accordingly the boundary reports the requirement as
`NOT DOCUMENTED`, makes no software default, and returns an `INFORMATIONAL ONLY`
readiness contribution that does not block activation or alter existing
Continuity readiness.

An authoritative governed source may establish a context-specific requirement
in a later separately controlled integration. This contract does not create
that source or redesign the activation state machine.

## Institutional separation and no mutation

`ACCEPTANCE_RECORDED != CONTINUITY_ACTIVATED`. Reading this result never creates
a Continuity Profile or event, changes readiness or activation, assigns a
responsible party, changes Fiduciary authority, or changes application access.
Acceptance is institutional evidence, not proof of legal or appointment
validity. No UI, route, or template is part of this contract.

## Known limitation

Whether Acceptance is required for a specific Continuity activation remains
`NOT DOCUMENTED` until a canonical authoritative-requirement source is
established. The boundary deliberately cannot infer that requirement from
narrative text.
