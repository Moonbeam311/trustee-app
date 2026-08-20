# V3 Governance Service Contract

Status: explicit existing contract preserved by `V3-SVC-GOVCONT-1`.

## Domain owner

The canonical Governance service is `services/services_governance.py`. It owns governance record configuration, record persistence operations, lifecycle transitions, approvals, implementation/activity ledgers, governance relationships, relationship audit provenance, and governance evidence/export builders.

Flask routes are callers and authorization gates. They are not the Governance persistence owner.

## Public interface

The preserved callable surface includes:

- Configuration and vocabulary: `get_governance_config`, `get_governance_record_types`, `get_governance_relationship_types`, `get_governance_relationship_target_types`, `get_governance_directive_source_types`, `allowed_governance_transitions`.
- Records: `create_governance_record`, `list_governance_records`, `get_governance_record`, `transition_governance_record`.
- Approval: `approve_governance_directive`, `approve_governance_policy`.
- Implementation/activity: `create_directive_implementation_entry`, `list_directive_implementation_entries`, `create_policy_activity_entry`, `list_policy_activity_entries`.
- Relationships and provenance: `create_governance_relationship`, `get_governance_relationship`, `list_governance_relationships`, `record_governance_relationship_audit`, and relationship lifecycle/evidence builders.
- Evidence/export: existing governance packet, evidence index, CSV, manifest, digest, archive-intake preview, certification, exception, and completion-gate builders.

Existing function names and return conventions remain compatible.

## Input expectations

- `record_type` must resolve through `GOVERNANCE_OBJECTS`.
- Record creation requires a nonblank title.
- Directive and policy source metadata must use supported source types; a selected source type requires a source ID.
- Approval requires an existing same-firm record and a nonblank authority basis, either supplied or already stored.
- Lifecycle transition requires an existing same-firm record and a transition allowed by `GOVERNANCE_LIFECYCLE_TRANSITIONS`.
- Relationship creation requires source type/ID, supported relationship type, target type/ID, and uses the current firm unless a firm is explicitly supplied to the service operation.
- Callers are responsible for supplying actor, authority, reason, and evidence data honestly; the service does not infer institutional authority from display labels.

## Output expectations

- Creation, approval, transition, and relationship writes use the existing `(success, result_or_message)` convention.
- List operations return lists of dictionaries.
- Single-record retrieval returns a dictionary or `None`.
- Evidence builders return their currently documented text, bytes/buffer, dictionary, list, or other existing artifact type. This baseline does not normalize those output types.

## Persistence ownership

The Governance service owns access to its governance tables, numbering sequences, implementation/activity entries, relationships, and `governance_relationship_audit_ledger`. Other V3 consumers must use the service surface rather than issue direct governance-table SQL.

`ensure_governance_tables` remains a compatibility prerequisite used by the existing service. This baseline does not authorize schema redesign or migration.

## Firm-scope rules

- Record list/get/transition/approval operations derive the current firm through `get_current_firm_id` and include `firm_id` in queries and writes.
- Relationship retrieval and audit retrieval use an explicit firm when supplied or the current firm otherwise.
- A record in another firm is returned as unavailable (`None` or the existing not-found failure), without granting cross-firm access.
- Consumers must not bypass these rules through direct SQL.

## Authorization assumptions

The service enforces firm scope and domain validation, but HTTP authentication, role checks, CSRF, and endpoint permissions remain the responsibility of existing application routes and request policy. Direct non-route callers must establish an equivalent authenticated actor/firm context before invoking write operations.

The service does not independently prove that an actor possesses legal authority merely because an actor string is supplied.

## Validation and lifecycle rules

The canonical lifecycle is:

- Draft → Issued or Retired
- Issued → Active, Superseded, or Retired
- Active → Completed, Superseded, or Retired
- Completed → Superseded or Retired
- Superseded → Retired
- Retired → no further transition

Unsupported record types, missing titles, invalid source metadata, missing approval basis, invalid transitions, missing relationship fields, unsupported relationship types, and duplicate active relationships fail using existing behavior.

This baseline does not alter lifecycle semantics.

## Provenance and audit behavior

- Governance relationships record creation, validation failure, and duplicate blocking in `governance_relationship_audit_ledger`.
- Relationship retirement, reinstatement, and supersession retain their existing audit lineage.
- Record metadata includes existing creator/update, authority, source, approval, effective, retirement, and supersession fields where supported.
- Evidence/export builders expose existing governance state and audit provenance without changing institutional records.

Record lifecycle changes do not have a separate universal governance event ledger in the current service. Any stronger claim is NOT DOCUMENTED.

## Idempotency expectations

- Read and evidence-rendering operations are expected to be side-effect free apart from the existing table-ensure compatibility behavior.
- Duplicate active governance relationships are blocked and audited.
- General record creation, approval replay, lifecycle replay, and implementation-entry replay do not expose a universal idempotency-key contract. Additional guarantees are NOT DOCUMENTED.

## Failure behavior

- Expected validation/not-found failures use the existing false/message, empty-list, or `None` conventions.
- Invalid lifecycle transitions fail without updating the record.
- Cross-firm retrieval behaves as unavailable.
- Unexpected persistence/runtime failures are not normalized by this contract and propagate according to existing behavior.

## Compatibility guarantees

- Existing public function names, parameters, lifecycle vocabulary, firm scoping, return shapes, audit tables, and route callers remain unchanged by this baseline.
- No Governance dependency on Continuity, suspended P03, or future trust-handoff code is introduced.
- No existing caller is required to migrate in this phase.

## Prohibited behaviors

- Direct governance-table access by new V3 consumers.
- Weakening firm scope or route authorization.
- Treating actor labels as verified authority.
- Bypassing allowed lifecycle transitions.
- Recreating or mutating governance evidence during read-only export.
- Adding dependencies on Continuity, P03, or trust-handoff implementation in this baseline.

## Known limitations

- Route authorization remains external to the service.
- Failure result types are not uniform across all public functions.
- A universal event ledger for all governance record lifecycle changes is NOT DOCUMENTED.
- Universal idempotency keys for governance record writes are NOT DOCUMENTED.

## Safe consumers

Future V3 consumers may safely reuse firm-scoped governance retrieval, supported lifecycle metadata, relationship/audit APIs, and evidence/export builders when they preserve the existing authentication/authorization boundary. A future successor-handoff workflow may consume active directives and native provenance, but it must not infer fiduciary authority or handoff completion from Governance records alone.
