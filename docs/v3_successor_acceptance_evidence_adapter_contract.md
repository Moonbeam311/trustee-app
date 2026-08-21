# V3 Successor Acceptance Evidence and Document Adapter Contract

Status: `V3-THO-ACC-1C — EVIDENCE/DOCUMENT ADAPTER`

## Ownership

Acceptance owns its institutional fact, lifecycle, provenance, and evidence references. Document owns document identity, metadata, storage/reference semantics, and any documented generation or finalization state. `services.services_successor_acceptance_evidence` links these canonical domains without copying document truth or changing Acceptance semantics.

## Public interface

- `link_acceptance_document_evidence(...)`
- `link_acceptance_external_evidence(...)`
- `describe_acceptance_evidence(...)`
- `build_acceptance_document_source_context(...)`
- `describe_legacy_acceptance_document(...)`

Document attachment delegates to the 1B maker-authorized lifecycle service. It requires exact firm, Trust, Acceptance, Fiduciary, and canonical Document scope. External governed references remain opaque references whose external owner and finalization semantics are `NOT DOCUMENTED`; the adapter creates no shadow evidence store.

## Document and Acceptance separation

Document generation does not create, finalize, verify, or transition Acceptance. Executed or uploaded document presence also does not record Acceptance. The governed sequence is evidence existence, explicit maker-authorized evidence linking, independent 1B review, then an Acceptance transition.

Producer-ready source context reads canonical Acceptance, Trust, and Fiduciary contracts. Building it generates and persists nothing. Existing document producers, renderers, universal object ownership, and delivery behavior remain unchanged.

## Provenance and verification

Evidence descriptions derive maker attachment and reviewer reliance from immutable 1B Acceptance events. `RELIED_ON_IN_FINALIZED_TRANSITION` means only that a separately authorized reviewer relied on the reference in a finalized Acceptance transition. It is not a conclusion about signature authenticity, notarization, appointment legality, legal validity, or Document finality.

Document execution/finalization remains `NOT DOCUMENTED` where the canonical Document metadata contract does not expose it.

## Authorization and scope

Evidence linking requires `record_successor_acceptance` through 1B. Finalization remains governed by `verify_successor_acceptance` and maker/reviewer separation. Read descriptions require explicit Acceptance and Document authorization decisions. Successor, Fiduciary, document ownership, Continuity status, or login alone grant no evidence authority.

## Legacy compatibility and excluded effects

An unlinked historical generated document remains `LEGACY DOCUMENT / ACCEPTANCE STATE NOT STRUCTURALLY VERIFIED`. No migration or inspection backfills Acceptance.

Adapter operations do not mutate Trust, Fiduciary authority, Continuity activation/readiness/responsibility, application users/roles/permissions, Execution authority, Document generation, or handoff acknowledgement. No UI or public route is included.
