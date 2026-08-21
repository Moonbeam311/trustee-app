# V3 Unified Handoff Read Aggregate Contract

## Owner and purpose

`services/services_handoff_read_aggregate.py` owns the ephemeral
`TrustSuccessorHandoffContext` composition boundary. The root governed subject
is one Trust. The aggregate is a read-only view and is not a persistence owner,
workspace, acceptance record, activation mechanism, or package.

## Public interface

`build_trust_successor_handoff_context(trust_id, *, db_path,
trust_authorization_check, continuity_authorization_check,
fiduciary_authorization_check, governance_authorization_check,
execution_id=None, transfer_id=None)` returns a structured dictionary or
`None`. Missing, denied, and cross-firm Trust roots share the `None` result.
All four authorization callbacks are required. Optional Execution identifiers
request existing read/orchestration evidence; they do not execute an action.

## Source-of-truth map

| Aggregate section | Canonical source |
|---|---|
| Trust identity, current trustee, recorded successor name | Trust Read contract |
| Trust–Continuity relationship | TrustContinuity Context Adapter |
| Recorded fiduciary role, capacity, and authority evidence | Fiduciary Authority Read/Decision contract |
| Responsibilities, digital-access metadata, obligations, activation, readiness | Continuity contract |
| Accounts and properties/assets | Account/Asset Read Aggregation contract |
| Linked directives/policies and relationships | Governance contract |
| Existing document references | Document Producer/Adapter contract |
| Existing Execution/transfer state and recommendations | Execution Read/Orchestration contract |
| Existing archive/handoff descriptors | Archive Package Descriptor contract |
| Application permissions | Existing authorization architecture; never this aggregate |

The aggregate retains native identifiers in its `provenance` list. It does not
copy any source record into aggregate persistence; its stable-looking
`aggregate_id` is derived from the Trust identifier and is not stored.

## Sections and status vocabulary

The result contains `identity`, `fiduciary_authority`, `continuity`,
`accounts_assets`, `governance`, `execution`, `documents`, `archive`,
`readiness`, `provenance`, and `boundaries` sections. Evidence state uses
`AVAILABLE`, `UNLINKED`, `MISSING`, `UNRESOLVED`, `NOT DOCUMENTED`, and
`NOT APPLICABLE` where applicable. It does not report legal validity,
appointment, incapacity, certification, completion, or application access.

Continuity has `ZERO_OR_MANY` cardinality. All authorized profiles linked to the
Trust are represented; none is silently selected as primary. An unlinked Trust
is a valid aggregate with explicit `UNLINKED` state. Execution is `NOT
APPLICABLE` unless an existing execution or transfer identifier is supplied.
Successor-acceptance persistence remains `NOT DOCUMENTED`.

## Firm, Trust, and profile scope

Canonical Trust authorization establishes the root firm/Trust scope. The
context adapter independently enforces Trust and Continuity authorization and
same-firm profile linkage. Fiduciary, Account/Asset, Document, Execution, and
Archive sections use their existing firm-scoped contracts. Governance data is
read only after an explicit Trust-level Governance authorization decision.
Denied source sections are not bypassed. Callers must retain their existing
route or application authorization gates.

## Readiness and gaps

The aggregate preserves Continuity readiness rather than replacing it. Its
integration view may report evidence-derived gaps for missing successor
identity, missing/unresolved Fiduciary evidence, missing Continuity linkage,
Continuity readiness gaps, unresolved account/property references, and supplied
Execution/transfer blockers. Absence of a Document or Archive descriptor is
shown in that section but is not treated as universally required because no
universal requirement policy is documented.

`ready_for_review` and `needs_attention` are administrative review states only.
They are not legal, financial, execution, acceptance, or certification claims.

## Security contract

Digital-access output is an allowlisted metadata view. It may contain a login
identifier, vault reference, recovery procedure, MFA method/custodian, access
authorization metadata, and responsible parties where recorded. It must never
contain passwords, PINs, recovery codes, security answers, tokens, private
keys, or complete payment-card secrets. The aggregate reuses Continuity's
secret-material validation before returning output. A vault reference is
metadata, not a credential.

Recorded successor status, responsibility, or Fiduciary authority never grants
an application permission.

## No-mutation guarantee

Building the aggregate does not create or update Trusts, Continuity profiles or
children, events, audit records, permissions, Execution tasks/transfers,
documents, archives, exports, handoffs, or packages. It does not transition an
activation plan or execute an orchestration recommendation. The `boundaries`
and `mutation_performed` fields make these exclusions explicit.

## Compatibility and limitations

The service composes the existing canonical boundaries without changing them.
It does not add routes or templates. Governance reads require the established
Governance schema to exist; schema creation is outside this contract. Existing
Execution/transfer evidence is included only when its identifier is supplied;
automatic discovery of a canonical Execution context by Trust is not
documented. The aggregate lists recorded Archive descriptors and Document
references but creates neither output nor history.

Future safe consumers include the separately controlled read-only successor
handoff workspace, derived Document/package adapters, and a read-only Guide
interpretation adapter. Workspace UI, acceptance, activation bridging, package
generation, and every mutation remain excluded from `V3-THO-AGG-1`.
