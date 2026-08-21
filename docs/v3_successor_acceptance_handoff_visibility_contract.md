# V3 Successor Acceptance Handoff Visibility Contract

Status: `V3-THO-ACC-1D - READ-ONLY WORKSPACE VISIBILITY`

## Canonical composition

The existing Trust Successor Handoff aggregate composes structured Acceptance facts through `services_successor_acceptance` and evidence/provenance through `services_successor_acceptance_evidence`. The route and template do not query or reconstruct Acceptance persistence.

The visible section exposes the canonical Acceptance identifier, lifecycle state, Fiduciary and appointment context, recorded time and actor, scoped evidence references, and immutable maker/reviewer provenance where available. It exposes no internal context fingerprint.

## Display semantics

The workspace distinguishes `DESIGNATED / ACCEPTANCE NOT RECORDED`, `ACCEPTANCE RECORDED`, `ACCEPTANCE PENDING REVIEW`, canonical declined/withdrawn/superseded states, and `NOT DOCUMENTED / NO ACCEPTANCE EVIDENCE`. A missing structured record is an evidence/readiness gap, not a legal conclusion. Legacy generated documents are never promoted to structured Acceptance.

## Institutional boundaries

Acceptance does not establish legal or appointment validity, Fiduciary authority, Continuity activation, operational responsibility, application access, Execution authority, or handoff acknowledgement. Document presence and generation do not record Acceptance.

## Authorization and mutation boundary

Visibility inherits the existing authenticated, firm-scoped, Trust-assignment Handoff access policy. Acceptance maker/reviewer permissions are not display permissions. Reads remain fail-closed against cross-firm and mismatched Trust identifiers.

The workspace contains no Acceptance record, review, evidence attachment, upload, generation, decline, withdrawal, or supersession controls. GET requests create no Acceptance, evidence, Document, Continuity, responsibility, Fiduciary, user, role, permission, or read-audit mutation.
