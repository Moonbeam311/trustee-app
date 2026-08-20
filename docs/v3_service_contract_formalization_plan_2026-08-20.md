# V3-SVC-PLAN-1 — Service Contract Formalization Plan

## 1. Control Verdict

PASS. `V3-SVC-PLAN-1` was activated through the V3 control procedure and remotely anchored at commit `b7d247464a90470d26c79b762271f156c654aa05`. The guard reported `ACTIVE_PHASE=V3-SVC-PLAN-1` and `AUTHORIZED_NEXT_ACTION=V3-SVC-PLAN-1`. Repository, branch, local/remote authority, source DB, protected hashes, staging, and authorized worktree scope passed. No implementation phase was activated.

## 2. Preserved Audit Baseline

Primary evidence: `docs/v3_service_contract_inventory_boundary_audit_2026-08-20.md`.

The preserved classifications are unchanged:

- Fiduciary — FRAGMENTED CONTRACT
- Trust — FRAGMENTED CONTRACT
- Accounts / Assets — FRAGMENTED CONTRACT
- Governance — EXPLICIT CONTRACT
- Execution — FRAGMENTED CONTRACT
- Documents — FRAGMENTED CONTRACT
- Continuity — EXPLICIT CONTRACT
- Archive / Recovery — FRAGMENTED CONTRACT

The trust-handoff baseline is `V3-AUD-TRUST-HANDOFF — COMPLETE / REPAIR REQUIRED AT INTEGRATION LAYER`. The ledger record and current repository evidence are the available preserved evidence; further details are NOT DOCUMENTED.

## 3. Formalization Priority Matrix

| Domain | Current classification | Current boundary | Problem / risk | Formalization need | Reuse value | Successor-handoff relevance | Dependency risk | Recommended priority | Recommended action type |
|---|---|---|---|---|---|---|---|---|---|
| Governance | EXPLICIT CONTRACT | `services_governance.py` owns scoped records, transitions, relationships, audits, and exports | Refactoring risks strong existing flows; route authorization is external | Record and preserve callable/security expectations | High | Directives, provenance, evidence | Low if untouched; high if refactored | P0 preserve | PRESERVE AS-IS |
| Continuity | EXPLICIT CONTRACT | TPD-1C profiles, records, activation, and events in the intake-trust bridge and blueprint | Asset continuity is separate; broadening could blur ownership | Freeze scope and document consumer expectations | High | Vault references, obligations, activation, provenance | Low if untouched; moderate if merged | P0 preserve | DOCUMENT CONTRACT |
| Trust | FRAGMENTED CONTRACT | DB CRUD, application routes/generators, and partial TPD bridge | No canonical identity/read interface | Add a firm-scoped read facade without persistence migration | Very high | Foundational identity/context | High; prerequisite for other scoped domains | P1 | WRAP EXISTING FUNCTIONS |
| Fiduciary | FRAGMENTED CONTRACT | Fiduciary/role CRUD, route policy, destination verifier | Authority, assignment, acceptance, revocation, and app roles are conflated | Define authority vocabulary and a read/decision boundary after Trust | Very high | Successor, authority, responsibilities, acceptance | High | P2 | DEFINE AUTHORIZATION CONTRACT |
| Accounts / Assets | FRAGMENTED CONTRACT | DB account/property CRUD, continuity assets, institutional assets, transfers | Multiple asset meanings and bypass paths | Define source-attributed aggregation; do not merge persistence | High | Accounts, assets, custody, obligations | High | P3 | SEPARATE RESPONSIBILITIES |
| Documents | FRAGMENTED CONTRACT | Registry/object/adapters plus DB/application/intake generators | Registry does not own writes, lifecycle, or authorization | Formalize producer/adapter/output responsibilities | Medium-high | Instruments, evidence, packets | Moderate | P4 | DOCUMENT CONTRACT |
| Execution | FRAGMENTED CONTRACT | Sessions, tasks, transfers, intake execution, verification, recovery, exports | Parallel states and mixed authorization | Define orchestration facade while retaining state owners | High | Acceptance/assumption and controlled steps | Very high | P5 | SEPARATE RESPONSIBILITIES |
| Archive / Recovery | FRAGMENTED CONTRACT | Continuity packets, execution recovery, handoff exports, governance archive intake | No universal archive authority/package/restoration contract | Define package descriptor and custody boundary; keep recovery separate | High | Archive/export and recovery evidence | Very high | P6 | CONSOLIDATE BOUNDARY |

## 4. Target Contract Plan by Domain

### Governance

- Owner: preserve `services/services_governance.py`.
- Public interface: preserve existing create/list/get/transition/approve, relationship lifecycle, and evidence/export builders.
- Inputs/outputs: existing record dictionaries, firm-derived context, success/result conventions, and read-only exports.
- Persistence: governance tables, numbering, relationships, and audit ledger remain service-owned.
- Scope/authorization: retain service firm scope and existing endpoint authorization; no policy relocation.
- Validation/lifecycle/provenance: preserve configured types, allowed transitions, approvals, validation audits, relationships, and evidence digests.
- Idempotency/failure: preserve duplicate blocking and present failure conventions; a unified failure type is NOT DOCUMENTED and deferred.
- Consumers/compatibility: handoff reads active directives/evidence through service APIs, never tables; zero behavior/schema break.
- Migration risk: high if refactored, low if documented.
- Tests: existing governance mutation, access, lifecycle, export, and workspace audits using isolated DBs where required.

### Continuity

- Owner: preserve TPD-1C profile/record/activation behavior in `services/services_intake_trust_bridge.py`; preserve HTTP permission/CSRF boundary in `routes_tpd1c.py`.
- Public interface: create/get/link profile, add allowed record, transition activation plan, and readiness.
- Inputs/outputs: explicit firm/profile/plan IDs, actor, controlled payload, and dictionary/readiness results. Secrets remain prohibited; vault references only.
- Persistence: continuity tables/events remain service/migration-owned; asset custody remains separate.
- Scope/authorization: same-firm service operations and existing `create_trust`/`edit_trust` route permissions.
- Validation/lifecycle/provenance: preserve allowlist, secret rejection, transition graph, and actor/basis/previous/new events.
- Idempotency/failure: preserve existing bridge idempotency; replay behavior beyond evidence is NOT DOCUMENTED and must fail closed.
- Consumers/compatibility: handoff uses an adapter and must not merge custody tables.
- Migration risk: moderate if broadened, none for documentation-only preservation.
- Tests: existing TPD disposable-DB suites plus cross-firm/no-secret regression.

### Trust

- Proposed owner: `services/services_trust_contract.py`; `database/db.py` remains persistence adapter initially.
- Proposed public interface: `get_trust_identity`, `list_visible_trusts`, and `get_trust_contract_snapshot`.
- Inputs: nonblank trust/firm IDs and authenticated actor context, with no authority override.
- Outputs: side-effect-free snapshot containing identity, type, status, firm, trustee/successor references, and provenance availability; absent facts are NOT DOCUMENTED.
- Persistence: existing `trusts` table ownership remains unchanged.
- Scope/authorization: fail closed across firms and reproduce current role/assignment visibility without existence leakage.
- Validation/lifecycle: validate IDs/visibility; never advance lifecycle; retain bridge-draft restrictions.
- Provenance/idempotency/failure: expose bridge provenance when available; deterministic reads; explicit not-found/access-denied results.
- Consumers/compatibility: future domain facades and handoff use the facade; current routes remain unchanged until separately authorized.
- Migration risk: medium for facade, high for caller migration.
- Tests: disposable firm isolation, assignment visibility, legacy/string IDs, bridge drafts, no mutation.

### Fiduciary

- Proposed owner: `services/services_fiduciary_authority.py`.
- Proposed interface: list/get assignment, evaluate authority by capability, and describe successor status; writes deferred.
- Inputs/outputs: canonical Trust snapshot, assignment IDs, capability, actor/time; decision with basis/status/responsibility references and explicit unknowns.
- Persistence: existing fiduciary/role tables remain DB-owned initially.
- Scope/authorization: inherit Trust scope; application security roles remain distinct from institutional roles.
- Validation/lifecycle: reconcile controlled status vocabulary before any writes; never infer acceptance from a name or document.
- Provenance/idempotency/failure: deterministic reads with source/audit references; deny ambiguous or cross-firm authority.
- Consumers/compatibility: handoff and Execution consume decisions, not raw role tables; legacy CRUD/routes remain.
- Migration risk: high semantic risk.
- Tests: scope, role separation, inactive/revoked/superseded states, missing acceptance, capability matrix, no mutation.

### Accounts / Assets

- Proposed owner: `services/services_account_asset_contract.py` as read facade; existing DB, continuity, institutional-asset, and transfer owners remain distinct.
- Proposed interface: list trust accounts/assets, build asset handoff snapshot, and summarize obligations.
- Inputs/outputs: canonical Trust snapshot and actor; source-attributed DTOs containing scope, custody, continuity, and provenance availability.
- Persistence: no merged tables.
- Scope/authorization: require canonical Trust access; unprovable scope fails closed or is unavailable.
- Validation/lifecycle: do not equate trust property, identity assets, custody assets, or transfers; map without transitioning.
- Provenance/idempotency/failure: deterministic source-attributed reads; partial failures cannot imply completeness.
- Consumers/compatibility: handoff uses aggregate snapshot; legacy routes remain.
- Migration risk: medium for explicit read facade, high for hidden semantic merging.
- Tests: cross-firm, attribution, type separation, custody mapping, obligation non-duplication, no writes.

### Documents

- Owners: preserve registry/object/adapters as read surfaces; existing DB and generators remain persistence/producers.
- Proposed interface: list/get document object, resolve output capability, and build handoff references. Write API is NOT DOCUMENTED and deferred.
- Inputs/outputs: typed source/object IDs plus actor/Trust context; normalized object with provenance, lifecycle, storage/export reference, and governance links.
- Scope/authorization: inherit Trust scope and endpoint permissions; adapters cannot bypass authorization.
- Validation/lifecycle: distinguish generated output, executed instrument, evidence, and archive record; do not synthesize status.
- Provenance/idempotency/failure: require source adapter; deterministic reads; explicit missing-source behavior.
- Consumers/compatibility: Execution/Archive/handoff consume references, not generator internals; current routes remain.
- Migration risk: moderate-high.
- Tests: provenance/status mapping, firm visibility, missing sources, and no generation side effects.

### Execution

- Proposed owner: `services/services_execution_contract.py` facade over current execution, object, transfer, and verification services; recovery remains separate.
- Proposed interface: get context, evaluate readiness, list evidence, and evaluate successor acceptance; writes deferred pending state reconciliation.
- Inputs/outputs: canonical Trust, authority, account/asset, and document references; source-specific readiness/decision results and blocking reasons.
- Persistence: existing session/task/transfer/intake tables retain owners.
- Scope/authorization: canonical Trust scope plus fiduciary capability; preserve trustee-admin and endpoint gates.
- Validation/lifecycle: never collapse distinct state machines without a separately approved translation.
- Provenance/idempotency/failure: aggregate native events without inferring completion; deterministic reads; contradictory states fail closed.
- Consumers/compatibility: future handoff consumes facade; legacy routes remain.
- Migration risk: very high.
- Tests: source-state matrix, denial, incomplete evidence, cross-firm, no mutation, legacy compatibility.

### Archive / Recovery

- Proposed owner: `services/services_archive_contract.py` for package/custody reads; disaster recovery remains independently owned.
- Proposed interface: describe package, list components, evaluate readiness, get custody provenance, and get recovery reference; restoration writes deferred.
- Inputs/outputs: canonical Trust/Execution context and package IDs; descriptor with components, hashes, custody, finalization, producer, recovery references, and gaps.
- Persistence: existing custody, finalization, export, handoff, recovery registries, and files remain separately owned.
- Scope/authorization: canonical Trust scope; export/write permission mapping must precede writes.
- Validation/lifecycle: distinguish package completeness/integrity from topology/restoration success.
- Provenance/idempotency/failure: preserve native hashes/audit IDs; deterministic reads; contradictions fail closed.
- Consumers/compatibility: handoff receives one descriptor, not a replacement archive system.
- Migration risk: very high.
- Tests: integrity mismatch, incomplete package, cross-firm, custody lineage, producer separation, no restoration.

## 5. Dependency / Order Analysis

Evidence-supported order:

1. Preserve Governance and document/freeze TPD-1C Continuity.
2. Add the Trust read facade because all trust-scoped contracts depend on identity and visibility.
3. Add the Fiduciary authority facade because successor authority depends on Trust identity.
4. Add Accounts / Assets aggregation using Trust scope and authority.
5. Formalize Documents producer/adapter responsibilities to provide references for Execution and Archive.
6. Add Execution orchestration only after its inputs are formalized.
7. Add the Archive package descriptor after Documents and Execution.
8. Plan/implement trust-handoff integration repair only after those prerequisites close.

Governance preservation, Continuity documentation, and the read-only Trust facade are independently safe. Fiduciary write lifecycle, persistence consolidation, execution state merging, archive restoration, successor acceptance writes, route migrations, and unified handoff orchestration are destabilizing if attempted early and remain deferred. Governance and TPD-1C behavior are strong enough to preserve as-is.

## 6. Trust-Handoff Alignment Map

| Capability | Source domain | Reusable current contract | Required formalization | Risk | Prerequisite to repair |
|---|---|---|---|---|---|
| Trust identity | Trust | Firm-scoped reads and partial bridge provenance | Canonical read/visibility facade | High | Yes |
| Successor trustee | Trust + Fiduciary | Name fields/output surfaces | Authority assignment/acceptance decision | Critical | Yes |
| Fiduciary authority | Fiduciary | CRUD, route policy, active verifier | Capability-based authorization | Critical | Yes |
| Responsibilities | Fiduciary + Continuity | Role/continuity fields | Authority-backed normalized references | High | Yes |
| Accounts | Accounts / Assets | DB CRUD | Scoped account snapshot | High | Yes |
| Assets | Accounts / Assets | Property CRUD, custody scoring, transfers | Source-attributed asset snapshot | High | Yes |
| Digital vault references | Continuity | TPD-1C no-secret/vault-reference contract | Adapter only | Low | No, after Trust-link validation |
| Receivables/payables | Continuity + Accounts | TPD records/accounting summaries | Non-duplicating obligation sources | High | Yes |
| Governance directives | Governance | Explicit service/evidence | Preserve/read adapter | Low | No |
| Activation plan | Continuity | Explicit transitions/events | Preserve/read adapter | Low | No |
| Archive/export | Archive + Documents + Execution | Multiple exporters/integrity records | Package descriptor/ownership split | Critical | Yes |
| Successor acceptance | Fiduciary + Execution + Documents | PDFs/transfer decision fields | Authority-backed acceptance/evidence state | Critical | Yes |
| Provenance/audit | Governance + Continuity + others | Strong native ledgers in two domains; partial elsewhere | Envelope retaining native IDs | High | Yes for unified audit claims |

## 7. Proposed Implementation Phases

All phases below are proposals and are NOT AUTHORIZED.

### V3-SVC-GOVCONT-1 — Explicit Contract Preservation Baseline

- Scope: machine-checkable documentation/static inventory for Governance and TPD-1C Continuity; no service changes.
- Allowed: `docs/v3_governance_continuity_contract_baseline.md`, `scripts/audit_v3_svc_govcont_1.py`.
- Excluded: application, services, database, routes, migrations, templates, source DB, P03.
- Prerequisites: preserved audit and current Governance/TPD tests.
- Verification: static API/scope/event assertions; isolated existing suites only after inspection.
- DB rule: source hash before/after; disposable DB only. Browser not required.
- Commit boundary: exactly the two allowed files.
- Stop: contradiction, guard failure, source hash change, or unexpected path.

### V3-SVC-TRUST-1 — Canonical Trust Read Contract

- Scope: side-effect-free scoped facade; no route or persistence changes.
- Allowed: `services/services_trust_contract.py`, `tests/test_v3_svc_trust_contract.py`, `docs/v3_trust_read_contract.md`.
- Excluded: `app.py`, `database/db.py`, routes/templates/migrations/source DB/P03/handoff.
- Prerequisite: V3-SVC-GOVCONT-1.
- Tests: disposable scope/role/ID/draft/no-write/legacy cases. Browser not required.
- Commit: exactly three files.
- Stop: current visibility cannot be reproduced without forbidden changes, ambiguity, mutation, or incompatibility.

### V3-SVC-FID-1 — Fiduciary Authority Read/Decision Contract

- Scope: read-only assignment normalization and capability decisions; no transitions.
- Allowed: `services/services_fiduciary_authority.py`, `tests/test_v3_svc_fiduciary_authority.py`, `docs/v3_fiduciary_authority_contract.md`.
- Excluded: application/DB/routes/schema/templates/source DB/handoff.
- Prerequisite: Trust contract and approved role separation mapping.
- Tests: scope, status rejection, absent acceptance, capability, no mutation. Browser not required.
- Commit: exactly three files.
- Stop: unsupported vocabulary, role conflict, or scope leak.

### V3-SVC-AA-1 — Account/Asset Read Aggregation

- Scope: source-attributed read facade; no consolidation/writes.
- Allowed: `services/services_account_asset_contract.py`, `tests/test_v3_svc_account_asset_contract.py`, `docs/v3_account_asset_contract.md`.
- Excluded: current application, DB, asset/transfer services, schema/templates/source DB.
- Prerequisites: Trust and Fiduciary contracts.
- Tests: scope, attribution, source separation, obligations, no writes. Browser not required.
- Commit: exactly three files.
- Stop: unscoped data or conflicting source meanings cannot fail closed.

### V3-SVC-DOC-1 — Document Producer/Adapter Contract

- Scope: read adapters and output capability; no generator migration.
- Allowed: `services/services_document_contract.py`, `tests/test_v3_svc_document_contract.py`, `docs/v3_document_contract.md`.
- Excluded: application/current generators/DB/templates/routes/schema/source DB.
- Prerequisite: Trust contract and Fiduciary metadata decision.
- Tests: provenance, mapping, scope, missing source, no generation. Browser not required.
- Commit: exactly three files.
- Stop: authorization bypass or invented lifecycle required.

### V3-SVC-EXEC-1 — Execution Read/Orchestration Contract

- Scope: read-only context/readiness; no state merge/write transition.
- Allowed: `services/services_execution_contract.py`, `tests/test_v3_svc_execution_contract.py`, `docs/v3_execution_contract.md`.
- Excluded: application/current execution/transfer/recovery services/routes/templates/schema/source DB/handoff.
- Prerequisites: Trust, Fiduciary, Accounts/Assets, Documents.
- Tests: state sources, authority, evidence, scope, no mutation, compatibility. Browser not required.
- Commit: exactly three files.
- Stop: state contradiction, hidden mutation, or authority bypass.

### V3-SVC-ARCH-1 — Archive Package Descriptor Contract

- Scope: read-only package/custody/integrity descriptor; no restoration.
- Allowed: `services/services_archive_contract.py`, `tests/test_v3_svc_archive_contract.py`, `docs/v3_archive_contract.md`.
- Excluded: application/current exporters/recovery/continuity services/routes/templates/schema/source DB/handoff.
- Prerequisites: Documents, Execution, and the Governance/Continuity baseline.
- Tests: integrity, incompleteness, scope, custody, producer separation, no restoration. Browser not required.
- Commit: exactly three files.
- Stop: archive/recovery cannot remain separated or scope/integrity is ambiguous.

A future trust-handoff repair phase is not proposed for authorization until all prerequisite contracts close. Any later UI phase requires browser validation of authentication, firm isolation, role denial, lifecycle gates, downloads, and audit evidence.

## 8. Deferred / Do-Not-Touch Areas

- Suspended `V3-MOD-WLH-P03C.4C` footprint.
- P04 and later work.
- Source DB and production data.
- Existing Governance and TPD-1C behavior except separately authorized documentation/audits.
- Trust/fiduciary/account/asset schema or persistence migration.
- Existing route/template migration.
- Execution state consolidation.
- Archive restoration/disaster-recovery mutation.
- Successor-handoff repair and successor-acceptance writes.
- Application security-role redesign or merging with institutional roles.

## 9. Source DB Preservation

The required and final source DB SHA-256 is:

`3fcbbe1092072c47fe7e43fb1ab075f6ff626079511c948a1275936776b71d3c`

No planning inspection mutated the source DB, and no DB-touching tests were run.

## 10. P03 Preservation

The suspended P03 footprint remains present, untouched, and unstaged:

- `app.py`
- `templates/workspace_detail.html`
- `services/services_work_learning_programs.py`
- `templates/workspace_program_detail.html`
- `templates/workspace_program_form.html`
- `templates/workspace_programs.html`

## 11. Final Planning Disposition

`V3-SVC-PLAN-1 — COMPLETE / IMPLEMENTATION PLAN READY`

## 12. Exact Recommended Next Controlled Action

`V3-SVC-GOVCONT-1 — Explicit Contract Preservation Baseline`

Status: **PROPOSED / NOT AUTHORIZED**.

It is a documentation/static-audit compatibility baseline only. It must not begin until separately authorized by the operator.
