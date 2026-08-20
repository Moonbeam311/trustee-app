# V3-AUD-SERVICE-CONTRACTS — Institutional Service Contract Inventory & Boundary Audit

## 1. Control Verdict

PASS. The V3 control guard authorized `V3-AUD-SERVICE-CONTRACTS`; the control root was remotely Git-anchored, the branch and authority ref matched, staging was empty, the worktree scope was authorized, and the source database and protected-record hashes passed.

## 2. Repository / Branch / HEAD

- Repository: `trustee-app-system1-user`
- Branch: `system-1-annual-evaluation`
- Audit HEAD: `32c4292dfd74645d6f97161466df2a9793f96822`
- Remote authority: `origin/system-1-annual-evaluation`
- Remote HEAD at audit: `32c4292dfd74645d6f97161466df2a9793f96822`
- Control history: `32c4292` is the bounded normalized-ledger-hash repair atop transition commit `3c7d20f`.

## 3. Source Database Preservation

PASS. The SHA-256 of `data/trustee_app.db` remained:

`3fcbbe1092072c47fe7e43fb1ab075f6ff626079511c948a1275936776b71d3c`

No database-touching tests were run. Evidence was obtained through read-only repository inspection and inspection of existing tests and audits.

## 4. Service Contract Matrix

| Domain | Classification | Primary contract surface | DB ownership | Authorization boundary | Lifecycle / validation | Audit / provenance | Test evidence | Fragmentation risk | Successor-handoff reuse assessment |
|---|---|---|---|---|---|---|---|---|---|
| Fiduciary | FRAGMENTED CONTRACT | `database/db.py` fiduciary and role CRUD; `app.py` fiduciary/role routes; `services_system_observation_destinations.py` verifier | `fiduciaries` and `roles` tables through `database/db.py`; routes invoke DB functions | Application endpoint role map and route-level trust access; no fiduciary authority service enforcement | CRUD status/fields; documented architecture lifecycle but no canonical transition or authority validator | Central `log_change` calls; destination verifier checks active statuses | Bridge/route guards cover fiduciary endpoints; no focused fiduciary contract suite found | High: fiduciary records, institutional roles, application roles, and trust assignments compete | Partial/unsafe; read-only registry data requires external validation |
| Trust | FRAGMENTED CONTRACT | `database/db.py` trust CRUD; extensive `app.py` routes/generators; `services_intake_trust_bridge.py` for a governed creation subset | `trusts` primarily through `database/db.py`; `app.py` also uses direct SQL; bridge writes through its supplied DB path | Firm-scoped DB operations and application trust-role gates; TPD routes add narrow permissions | Bridge-created drafts have explicit gates; general lifecycle is documented but not enforced by one service | Central audit plus bridge events and revisions; provenance is concentrated in the bridge subset | `test_tpd_ir_1c_firm_identity.py` and TPD-1C suites | High: application, DB module, intake bridge, and generators split responsibility | Partial/unsafe; bridge provenance and firm-scoped reads are reusable only within their scope |
| Accounts / Assets | FRAGMENTED CONTRACT | `database/db.py` account/property CRUD; `app.py` add/link routes; `services_continuity_assets.py`; `services_institutional_assets.py` | Account/property/document links in `database/db.py`; specialist services own continuity records and institutional asset files | Primarily global route permissions and trust access; service APIs do not consistently own authorization | Asset lifecycle is documented; continuity scoring/finalization exists; core CRUD validation is limited | Central route logging plus custody/finalization records; uneven across core CRUD | TPD route-guard coverage and archive/continuity audit scripts; no canonical account/asset suite found | High: direct DB CRUD, two specialist asset services, and transfer logic | Partial/unsafe |
| Governance | EXPLICIT CONTRACT | `services/services_governance.py` | Service owns governance tables, numbering, relationships, lifecycle audit ledger, and exports | Firm scope enforced throughout the service; route authorization remains in application endpoint policy | Explicit object configuration, allowed transitions, approvals, and relationship validation/retire/reinstate/supersede operations | Dedicated governance relationship audit ledger and evidence packets/manifests/digests | Governance mutation-boundary, create-review-approve, access, export, workspace-certification, and continuity audits | Low-to-moderate: routes orchestrate, but domain behavior is concentrated | Reusable contract |
| Execution | FRAGMENTED CONTRACT | Institutional execution, execution objects, verification, recovery, exports, transfer services, and `app.py` routes/direct access | Multiple execution/evidence/recovery/transfer tables and filesystem exports across modules | Transfer routes use trustee-admin and firm gates; other execution routes rely on application endpoint policy; service authorization is not uniform | Session ledger/signature/freeze semantics and transfer finalization exist, but task, transfer, packet, final-archive lifecycles are split | Execution ledger/evidence metadata, transfer audit, central logging, and recovery integrity records | Execution audit scripts and TPD downstream-gate tests; no single end-to-end contract suite found | High: sessions, tasks, transfers, intake execution, and recovery overlap | Partial/unsafe |
| Documents | FRAGMENTED CONTRACT | Document registry, object-model, adapter, and template services; `database/db.py`; `app.py` generation/PDF/DOCX/intake routes | Documents table through `database/db.py`; adapters read other registries; application/intake workflows directly access DB/files | Application endpoint permissions/roles; registry/adapters are presentation APIs, not an authorization boundary | Object model normalizes metadata; generation/review/execution/archive validation is distributed | Central audit, adapter provenance fields, governance evidence links, and intake ledgers | Document-governance and export audits plus TPD route-guard tests | High: the registry is aggregative while writes and generation remain elsewhere | Partial/unsafe |
| Continuity | EXPLICIT CONTRACT | TPD-1C profile, record, and activation-plan functions in `services/services_intake_trust_bridge.py`; `routes_tpd1c.py` | `continuity_*` tables and `continuity_events` through the service/migration | Same-firm parameters in service operations; narrow `create_trust`/`edit_trust` route permissions and CSRF | Secret rejection, record allowlist, activation transitions, idempotency, and same-firm linking | Ordered continuity/bridge events and bridge revisions with actor, basis, previous state, and new state | `test_tpd1c_bridge_continuity.py`, `test_tpd1c_routes.py`, and `test_tpd_ir_1c_firm_identity.py` use disposable databases | Moderate: asset-custody continuity is a separate subsystem | Reusable for profile, activation-plan, provenance, and vault-reference data; asset custody remains partial |
| Archive / Recovery | FRAGMENTED CONTRACT | Continuity-asset archive packets; execution recovery/exports; trust and transfer handoff routes; governance archive-intake exports | Custody/finalization, recovery registries, export history, transfer handoff tables, and files are separately owned | Varying route firm/role gates; service-level scope is inconsistent outside TPD/Governance | Integrity, finalization, and revalidation rules exist per subsystem, not as one archive lifecycle | Custody logs, finalizations, handoff audit trail, governance digests, and execution recovery records | Institutional archive/recovery/continuity and archive-workspace audits | Very high: archive, handoff, continuity asset, export, and disaster recovery are distinct contracts | Partial/unsafe |

## 5. Cross-Domain Findings

1. No canonical full Trust service exists. Trust behavior remains split across `app.py` and `database/db.py`, with an explicit but partial TPD-1C intake bridge.
2. Fiduciary provides CRUD plus route-level permissions and assignment checks, not a reusable authority/role service contract.
3. Accounts and Assets substantially use direct database functions and routes. Specialist continuity and institutional-asset services do not unify the domain.
4. Governance is materially stronger than Trust and Fiduciary and qualifies as an EXPLICIT CONTRACT because of its concentrated, firm-scoped lifecycle, validation, audit, relationship, and export APIs and its audit coverage.
5. Execution responsibility is split among `app.py`, institutional execution, execution objects, transfer, export, verification, and recovery services.
6. Documents is not a canonical domain service. Registry/object/adapters provide coherent read models, but writes, generation, and storage remain distributed.
7. TPD-1C Continuity supplies an explicit reusable profile/record/activation contract with same-firm scope, narrow permissions, validation, events, and tests.
8. Archive / Recovery is multiple distinct contracts, not one coherent contract.
9. Safe reuse without refactoring first is limited to Governance and the TPD-1C Continuity profile, activation-plan, provenance, and vault-reference functions within their existing scope. Firm-scoped trust retrieval may be consumed cautiously but is not an explicit contract.
10. Direct reuse of Fiduciary, full Trust, Accounts / Assets, Execution, Documents, or Archive / Recovery would couple a successor workflow to competing DB, route, or service implementations or duplicate lifecycle/audit logic.

## 6. Duplication / Bypass Risks

- `app.py` contains direct `get_connection`/SQLite paths and owns trust, document, export, and handoff orchestration outside domain services.
- Trust and fiduciary mutations use database CRUD while authorization and lifecycle rules reside in request hooks and routes.
- Account/property CRUD bypasses the continuity and institutional-asset services.
- Execution has parallel session, task, transfer, intake packet/event, and recovery models.
- The document registry/adapters may appear canonical but do not own writes, authorization, or lifecycle.
- Archive output, integrity, and audit concepts recur independently in Governance, Execution, transfer handoff, continuity assets, and application export history.

## 7. Trust-Handoff Reuse Map

| Capability | Assessment | Evidence / risk |
|---|---|---|
| Trust identity | Partial/unsafe contract | Firm-scoped retrieval exists; no full service boundary |
| Successor trustee | Missing boundary | Fields and output surfaces exist; no successor-authority lifecycle service |
| Fiduciary authority and responsibilities | Missing boundary | Fiduciary/role CRUD exists; acceptance and authority transitions are not centralized |
| Trust accounts and assets | Partial/unsafe contract | DB CRUD plus separate continuity and transfer services |
| Digital-account vault references | Reusable contract | TPD-1C rejects secret material and stores vault references |
| Receivables/payables | Partial/unsafe contract | Continuity records can represent obligations, but no canonical financial handoff boundary is established |
| Governance directives | Reusable contract | Explicit governance service and evidence lifecycle |
| Activation plan | Reusable contract | TPD-1C transition rules, events, and tests |
| Archive/export | Partial/unsafe contract | Multiple capable exporters; no unified archive contract |
| Successor acceptance/assumption | Missing boundary | Trustee-acceptance documents and transfer decisions exist, but no unified authority-assumption boundary |
| Provenance/audit | Reusable in Governance and TPD-1C; partial elsewhere | Dedicated ledgers/events contrast with central route logging elsewhere |

## 8. Required Future Formalization

Planning candidates supported by the audit are:

1. A canonical trust identity/read boundary.
2. A fiduciary authority and successor-acceptance lifecycle.
3. An account/asset read model with explicit firm and role rules.
4. Handoff orchestration ownership across Execution, Continuity, and Archive.
5. A canonical archive-package and restoration boundary.
6. Adapter contracts for document outputs.

Any future planning should preserve and integrate the existing Governance and TPD-1C Continuity contracts rather than duplicate them. This audit does not authorize implementation.

## 9. No-Change Confirmation

- Source database unchanged.
- Suspended P03 footprint untouched.
- Protected V3 documents untouched.
- No active feature mutation.
- No schema mutation.
- No production-data mutation.
- No implementation tests or repository behavior were added or changed during the audit.

## 10. Final Audit Disposition

`V3-AUD-SERVICE-CONTRACTS — COMPLETE / FORMALIZATION RECOMMENDED`
