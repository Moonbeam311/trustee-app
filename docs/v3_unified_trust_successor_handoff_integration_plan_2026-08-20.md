# V3-THO-PLAN-1 — Unified Trust Successor Handoff Integration Plan

## 1. Control Verdict

PASS. Operator authorization was recorded and remotely anchored at `d19fb9e42918667581ffa0c0955f3c8e1fa3dee2`. The guard returned PASS with `AUTHORIZED_NEXT_ACTION=V3-THO-PLAN-1`. This plan authorizes no implementation.

## 2. Current Baseline

The eight service boundaries required for planning are established: Governance, Continuity, Trust Read, Fiduciary Authority Read/Decision, Account/Asset Read Aggregation, Document Producer/Adapter, Execution Read/Orchestration, and Archive Package Descriptor. The preserved handoff audit disposition is `COMPLETE / REPAIR REQUIRED AT INTEGRATION LAYER`. P03 remains suspended and P04 remains unauthorized.

## 3. Authoritative Handoff Gap Summary

`trust_detail` independently reads Trust, Accounts/Assets, Documents, ledger, and Governance. Continuity navigation is supplied by `routes_tpd1c.formation_provenance`, which first requires a formation bridge before it queries profiles linked by `trust_id` or `bridge_id`. A valid same-firm Continuity profile linked by Trust but lacking that bridge path is therefore not surfaced from Trust detail. Successor names, authority evidence, responsibilities, activation state, Execution evidence, documents, and Archive descriptors remain separate facts without a governed handoff aggregate. Existing successor-trustee PDFs are derived output, not authoritative acceptance records.

## 4. Existing Capability / Contract Reuse Matrix

| Capability | Canonical source | Planned reuse |
|---|---|---|
| Trust identity | Trust Read | Direct firm-scoped reuse |
| Successor identity and authority evidence | Trust + Fiduciary | Preserve recorded and unresolved states |
| Responsibilities | Continuity | Direct reuse; no duplicated responsibility records |
| Accounts and assets | Account/Asset aggregation | Source-attributed read reuse |
| Vault references | Continuity | Metadata only; secrets remain prohibited |
| Receivables and payables | Continuity | Direct reuse without accounting duplication |
| Directives | Governance | Read linked governed records |
| Activation | Continuity | Existing state machine remains authoritative |
| Acceptance and execution evidence | Execution + Documents | Evidence only; acceptance persistence remains incomplete |
| Archive/handoff evidence | Archive descriptor | Recorded descriptors only |
| Provenance | Native domain ledgers/events | Retain native identifiers and meanings |

## 5. Proposed Handoff Aggregate

The initial `TrustSuccessorHandoffContext` is a read-only, source-attributed aggregate containing Trust identity and firm scope; recorded successor identity; Fiduciary authority evidence; responsibilities and authority-source references; accounts and assets; Continuity digital-account metadata and vault references; receivables/payables; Governance directives; activation plans; Execution/transfer/acceptance evidence; document references; Archive descriptors; readiness gaps; and native provenance references. It must not become a second persistence owner.

## 6. Source-of-Truth Map

- Trust identity and recorded successor name: Trust Read.
- Recorded authority evidence: Fiduciary Authority Read/Decision.
- Responsibilities, digital metadata, obligations, activation plans, and Continuity events: Continuity.
- Financial accounts and property inventory: Account/Asset aggregation.
- Governance directives and evidence: Governance.
- Derived output and document references: Document Producer/Adapter.
- Execution, transfer, signature, and current orchestration evidence: Execution.
- Recorded handoff, correction, export, custody, and hash references: Archive descriptor.
- Application roles and permissions: existing authorization architecture, never the institutional aggregate.

## 7. Trust–Continuity Repair Plan

First create a read-only adapter that resolves same-firm Continuity profiles through canonical Trust scope without requiring a formation bridge. It must preserve optional bridge provenance when present, return safe absent results, and invoke no Continuity mutation. Route/template adoption is deferred to a separate authorized UI phase.

## 8. Successor Handoff Workspace Plan

After the adapter and aggregate are independently verified, add a read-only Trust-scoped workspace displaying identity, successor evidence, responsibilities, inventory, activation, execution, document, archive, and gap panels. It must retain current route permissions and require isolated browser validation for authentication, role denial, firm isolation, navigation, and no mutation.

## 9. Acceptance / Activation / Responsibility Model

- Successor designation is a recorded name or institutional reference.
- Fiduciary authority is recorded evidence, not a legal verdict.
- Responsibility is Continuity assignment metadata.
- Successor acceptance is separately governed evidence and is currently `NOT DOCUMENTED` as a canonical persistence contract.
- Activation remains the existing Continuity activation-plan state machine.
- System authorization remains separate and is never granted by designation, authority, responsibility, acceptance, or activation.

## 10. Readiness Plan

The aggregate may report `needs_attention`, `ready_for_review`, or `unresolved`. Evidence-based gaps include missing successor identity, authority source, responsibility coverage, supporting documents, vault/recovery reference, account verification, activation review, acceptance evidence, Execution blockers, and Archive references. Readiness must not claim legal validity, incapacity, appointment, completion, certification, or system access.

## 11. Document / Archive Package Plan

Handoff output is derived from the governed aggregate through the Document contract. Archive metadata comes from the Archive descriptor. Generation, persistence, export history, finalization, certification, custody transfer, and recovery remain separate governed actions. No package may substitute for its source records or imply acceptance/finality merely because a file exists.

## 12. Provenance / Event Plan

The read-only phases emit no event. Aggregate output retains native Governance audits, Continuity events, Execution ledger references, Document provenance, and Archive handoff/export IDs. Any future handoff-specific write/event ledger requires a separately authorized acceptance contract and must reference rather than rewrite native history.

## 13. Security Model

Canonical Trust authorization and firm scope are mandatory; cross-firm existence is not disclosed. Passwords, PINs, recovery codes, security answers, tokens, private keys, and complete payment-card secrets remain prohibited. Only approved metadata and vault references may flow through the aggregate. Guide may interpret gaps and recommend navigation but may not silently mutate permanent records.

## 14. Implementation Phase Sequence

All phases are proposals and are not authorized by this artifact.

1. `V3-THO-CTX-1 — Canonical Trust–Continuity Context Adapter`: read-only adapter, tests, and contract documentation; no routes/templates/schema.
2. `V3-THO-AGG-1 — Unified Handoff Read Aggregate`: compose the eight contracts without persistence.
3. `V3-THO-UI-1 — Read-Only Successor Handoff Workspace`: minimal route/template adoption with isolated browser validation.
4. `V3-THO-ACC-AUD-1 — Successor Acceptance Contract Audit`: determine vocabulary, evidence, lifecycle, authorization, and persistence ownership.
5. `V3-THO-ACC-1 — Governed Successor Acceptance`: proposed only if the audit supplies sufficient evidence.
6. `V3-THO-PKG-1 — Handoff Document/Archive Package Adapter`: derived output without automatic finalization.
7. `V3-THO-GUIDE-1 — Guide Interpretation Adapter`: read-only explanations and navigation recommendations.

## 15. P03 Dependency Result

No P03 dependency was found. V3-MOD-WLH-P03C.4C remains suspended and untouched.

## 16. Guide Integration Result

Guide integration is not a prerequisite for the context adapter or aggregate. It is a later optional read-only consumer and may interpret/recommend only.

## 17. Source DB Preservation

The source database remained unchanged at SHA-256 `3fcbbe1092072c47fe7e43fb1ab075f6ff626079511c948a1275936776b71d3c`. No DB-mutating planning action or test was performed.

## 18. Final Planning Disposition

`V3-THO-PLAN-1 — COMPLETE / IMPLEMENTATION PLAN READY`

The bounded read-only sequence is ready. Successor-acceptance mutation remains evidence-gated behind its proposed audit.

## 19. Exact Recommended First Implementation Phase

`V3-THO-CTX-1 — Canonical Trust–Continuity Context Adapter`

Status: **PROPOSED / NOT ACTIVE** pending controlled closure and separate operator authorization.
