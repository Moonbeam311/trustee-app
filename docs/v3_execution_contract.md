# V3 Execution Read / Orchestration Contract

## Owner and scope

`services/services_execution_contract.py` is the canonical V3 read facade. Persistence and governed transitions remain owned by the existing execution-session, transfer, signature, certificate, archive, and recovery implementations. The facade does not replace their write APIs or state machines.

## Public interface

- `get_execution_session(execution_id, authorization_check=...)`
- `summarize_execution_readiness(execution_id, authorization_check=...)`
- `get_transfer(transfer_id, trust_id, authorization_check=...)`
- `summarize_transfer_readiness(transfer_id, trust_id, authorization_check=...)`
- `build_orchestration_context(trust_id, execution_id=..., transfer_id=..., authorization_check=...)`

Normal missing, denied, cross-firm, and mismatched-Trust reads share a `None` result. Missing required read schema raises `ExecutionContractError`; the service never creates schema.

## Scope and authorization

Every call requires the caller's existing authorization decision. Execution sessions inherit firm scope through their recorded `trust_id`, which must resolve through the canonical Trust read contract. Transfers require canonical Trust access plus exact `firm_id` and `trust_id` equality. A record ID cannot broaden the active-firm scope. The service does not grant a role or permission.

## Readiness and orchestration

Readiness results are interpretations of recorded fields only. Execution summaries expose the recorded ceremony state and step, pending signature evidence, and archive-freeze status. They deliberately do not claim `READY`, `COMPLETE`, or `CERTIFIED`. Transfer summaries preserve the existing asset, classification, assignment, trustee-acceptance, control-evidence, records, and external-verification requirements. A recommendation is navigation/decision context only and is never executed.

## Mutation boundary

The contract does not create sessions, tasks, transfers, actions, signatures, minutes, certificates, evidence packages, archive freezes/handoffs, or recovery actions. It does not advance, finalize, sign, certify, or archive anything. Ordinary reads create no audit event. Existing mutation routes and services remain outside this boundary.

## Domain separation and reuse

Execution sessions, tasks/steps, transfers, signature/minute/certificate evidence, archive handoff, and continuity/recovery retain distinct ownership. The facade reuses the V3 Trust contract and remains compatible with the separate Fiduciary, Account/Asset, and Document contracts; it does not duplicate or import their unrelated scope. Governance and Continuity are not coupled to this facade. Safe future consumers include governed dashboards and successor-handoff planning that need current recorded execution context without mutation.

## Provenance, documents, and limitations

Returned evidence retains source table identifiers and recorded ledger/provenance values. Document/certificate references are not synthesized; document rendering and persistence remain owned by the Document contract and legacy producers. The execution-session table has no `firm_id`, so a blank or inaccessible `trust_id` fails closed. Recovery helpers that seed or repair topology are intentionally excluded. Broader task normalization, archive topology, legal sufficiency, and an authoritative cross-component lifecycle are `NOT DOCUMENTED` by this contract.
