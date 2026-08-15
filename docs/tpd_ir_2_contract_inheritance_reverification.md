# TPD-IR-2 Contract Inheritance Re-verification

Date: 2026-08-14
Repository: current repository root on branch `system-1-annual-evaluation`
Branch: `system-1-annual-evaluation`
Committed HEAD: `ede2700712f8a6a1d4768698cbe2ee2f33efbcc8`
Source state: candidate integrated working tree; all changes unstaged

## Authoritative evidence

| Report | Authoritative external path | SHA-256 | Result |
|---|---|---|---|
| TPD-1A Topology Audit | External hash-verified predecessor report retained outside published source | `9F056BBB15D2D92BC05664A90BEA69EC51B12EFFF405F084BEA15EB30DD93151` | Exact match verified during the controlled recovery phase |
| TPD-1B Bridge Contract Audit | External hash-verified predecessor report retained outside published source | `BE4295EF706FE5FDEA4C374EF1E5EE1F2F9EB5CB96783C5872ECB29B904FD703` | Exact match verified during the controlled recovery phase |

The original reports, rather than reconstructed summaries, were used for this review.

## TPD-1A topology inheritance

| ID | Authoritative topology obligation | Current evidence | Result |
|---|---|---|---|
| A-01 | Preserve the identified System 1 source direction and do not silently substitute another repository. | Current branch descends from the System 1 lineage; the candidate remains in `trustee-app-system1-user`; no source transfer occurred in this phase. | PASS |
| A-02 | Keep intake, recommendation, bridge/proposal, formation, and downstream output boundaries explicit. | Intake and recommendation tables feed the isolated bridge service; proposal/revision/event tables are separate; trust creation is a separate transition; downstream actions are centrally guarded. | PASS |
| A-03 | Preserve existing systems and avoid destructive or indiscriminate consolidation. | V3-1 and branding coexist with TPD registration and lifecycle enforcement in `app.py`; the V3-1 audit confirms TPD guard preservation. | PASS |
| A-04 | Establish the bridge contract before pilot implementation. | The exact-hash TPD-1B contract is the predecessor to the present TPD-1C/1D implementation and this repair/re-verification sequence. | PASS |
| A-05 | Preserve the topology audit as historical read-only evidence. | The external original was read and hashed only; it was not edited or copied into the repository. | PASS |

Traceability through the implemented topology is intact: intake session and accepted recommendation -> firm-scoped bridge -> 23-field proposal -> immutable proposal revisions -> required confirmations -> derived readiness -> immutable governed events -> firm-scoped trust creation -> `/admin` firm-scoped list/count -> `/trust/<public-or-legacy-reference>` detail. Authentication, utility navigation, logout, and post-logout route protection provide the outer session boundary.

## TPD-1B contract matrix

| ID | Authoritative requirement | Implementation | Automated/browser evidence | Result |
|---|---|---|---|---|
| B-01 | Accept the TPD-1A topology and its source-authority boundary as predecessor. | TPD remains registered and integrated in the active System 1 candidate; no alternate repository is used at runtime. | V3-1 consolidation audit: PASS; ancestry/baseline verified. | PASS |
| B-02 | Limit the pilot bridge to the declaration-of-trust workflow and do not absorb downstream continuity or execution domains. | `services_intake_trust_bridge.WORKFLOW`; `routes_tpd1c.register_tpd1c_routes`; continuity tables/routes remain separately permissioned. | Core bridge tests and route tests: 33 PASS. | PASS |
| B-03 | Require an accepted recommendation, completed intake/preparation gate, eligible operator review, and no blocking review issues before preparation. | `evaluate_eligibility()` and `prepare_bridge()` use firm-scoped recommendation, intake, final-draft completion gate, and blocking-review queries. | Eligibility and blocking-review tests in `test_tpd1c_bridge_continuity.py`; adjacent intake/recommendation suites: 43 PASS. | PASS |
| B-04 | Preserve the contract's source classifications and display source/control status rather than collapsing provenance. | `_proposal_specs()` retains the governed classifications and confirmation requirements per field; bridge detail renders source classification and source references. | Required-control and rendered-proposal tests. | PASS |
| B-05 | Every `NO_RELIABLE_SOURCE` or `REQUIRE_NEW_ENTRY` field, including `grantor_contact`, requires nonblank operator entry and explicit confirmation. | `_required_fields_from_specs()`, `REQUIRED_FIELDS`, and `confirm_bridge()` derive requirements from classifications, trim whitespace, and reject unconfirmed fields before mutation. | Blank, whitespace, unconfirmed, invariant, and complete-confirmation tests. Disposable browser evidence confirmed required fields. | PASS |
| B-06 | Preserve proposal provenance and immutable ordered versions, including classifications, source identity/version/hash, before/after values, operator, confirmation, reason, and timestamp. | `_proposal_revision()`; `intake_trust_formation_proposal_revisions`; immutable update/delete triggers; source fingerprint/version fields. | Revision ordering/content and trigger rejection tests. Disposable bridge `ITFB-D8DECFC5F3B9` displayed immutable revision history. | PASS |
| B-07 | Do not infer parties, fabricate facts, or promote narrative/default content to verified values. | `_proposal_specs()` leaves unsupported party/contact fields empty with `REQUIRE_NEW_ENTRY`; confirmation rejects blank/placeholder absence rather than inventing values. | Source-value mapping, required-field, and no-parsing tests. | PASS |
| B-08 | Require explicit confirmation by an authorized operator; browser presentation alone is insufficient. | `confirm_bridge()` accepts the server-validated confirmed-field set; `routes_tpd1c.bridge_confirm` applies login, `create_trust` permission, firm scope, method, and CSRF protections. | Route auth/permission/CSRF and direct-call tests; disposable authorized-operator browser evidence. | PASS |
| B-09 | Enforce ordered lifecycle transitions and recompute `ready_for_confirmation`; posted, stale, malformed, route, or service state cannot bypass readiness. | `confirm_bridge()` re-reads firm-scoped bridge/proposals, verifies predecessor/source fingerprint/required values/revisions, derives readiness transactionally, then confirms. | Posted-readiness, stale-state, incomplete-direct-call, invalid-predecessor, rollback/no-mutation tests. | PASS |
| B-10 | Keep bridge/trust identity stable, make retries idempotent, and prevent duplicate trust creation. | Unique active bridge selection; `create_or_resume_trust()` resumes an existing linked trust, generates a new public identifier when required, and rolls back failure. | Prepare idempotency, create/resume, identifier-collision, retry, and rollback tests. | PASS |
| B-11 | Preserve immutable, ordered, firm-scoped proposal/lifecycle history with actor, timestamp, stable identifiers, and relevant revision/state references. | `_event()` plus immutable bridge-event triggers; preparation, source rebase, field entry/confirmation/deviation, readiness, confirmation, trust-start/create/resume events; `_proposal_revision()` links revisions. | Exact event ordering/count/no-duplicate/rollback tests. Disposable bridge showed governed events and revision history. | PASS |
| B-12 | Preserve authentication, semantically appropriate `create_trust` authority, CSRF, firm isolation, and server-controlled firm identity through trust creation/retrieval/mutation. | Route decorators use established `create_trust`; session firm is passed server-side; additive `trusts.firm_id`; bridge confirmation/trust creation and `database.db` trust lookup/update are firm-scoped; `/admin` and trust detail preserve role guards. | Fresh/additive/idempotent migration, same-firm, wrong-role, cross-firm, direct-service, Admin count/list, string/legacy lookup tests. Disposable admin/firm evidence passed. | PASS |
| B-13 | Keep database location externally configurable, use isolated validation, and preserve governed historical records and storage. | Application uses `DB_PATH`, `UPLOAD_FOLDER`, and `EXPORT_ROOT`; every automated command used unique temporary paths. | Protected DB strict read-only hash/record check; no pytest command used a browser DB. | PASS |
| B-14 | A bridge-created draft remains reviewable, but export/finalization/execution/funding/mapping/transfer/signing/upload/generation/certification/profile operations must be rejected before mutation. | `app.enforce_bridge_draft_lifecycle()` and endpoint inventory protect direct routes; preview route remains read-only. | Route/method 403 tests assert unchanged state, events, rows, uploads, and exports; preview-positive tests pass. | PASS |
| B-15 | Keep preparation, confirmation, trust creation, review, downstream lifecycle, and Continuity Profile creation as distinct governed domains. | Separate bridge/proposal/revision/event/trust/continuity schemas and endpoints; trust status remains `Draft - Bridge Created`; no automatic Continuity Profile link. | Bridge-continuity separation and prohibited-operation tests; historical profile count remains zero. | PASS |
| B-16 | Complete isolated automated, disposable-browser, route-continuity, authentication, authorization, regression, and preservation gates. | Current source plus recorded TPD-IR-1C.2 and TPD-IR-1C.3 evidence. | 80 pytest tests PASS; V3-1 audit PASS; disposable manual route/history/logout gates PASS; protected-state check PASS. | PASS |

## Automated evidence

All pytest commands set unique temporary `DB_PATH`, `UPLOAD_FOLDER`, `EXPORT_ROOT`, and `--basetemp` paths.

1. `python -m pytest -q -p no:cacheprovider --basetemp <unique-temp> tests/test_tpd1c_bridge_continuity.py tests/test_tpd1c_routes.py tests/test_tpd_ir_1c_firm_identity.py`
   Result: **33 passed, 0 failed, 0 errors, 0 skipped** in 84.88s.
2. `python -m pytest -q -p no:cacheprovider --basetemp <unique-temp> tests/test_matter_intake_visibility_panels.py tests/test_matter_intake_services.py tests/test_matter_intake_route_foundation.py tests/test_matter_intake_review.py tests/test_matter_intake_proposal_route.py tests/test_matter_intake_bridge_schema.py tests/test_matter_intake_bridge_route_contract.py tests/test_startup_migrations.py`
   Result: **43 passed, 0 failed, 0 errors, 0 skipped** in 21.89s.
3. `python -m pytest -q -p no:cacheprovider --basetemp <unique-temp> tests/test_hos_brand_1.py`
   Result: **4 passed, 0 failed, 0 errors, 0 skipped** in 14.47s.
4. `python scripts/audit_v3_1_admin_command_center_reconstruction.py` with unique temporary runtime paths.
   Result: **PASS** for source inventory, authorization (unauthenticated 302, Trustee 403, Admin 200), rendered routes, TPD guard, Hindsfoot introduction, runtime isolation, and `git diff --check`. Line-ending conversion warnings were informational; the diff check returned 0.

No independently runnable authoritative TPD-1A or TPD-1B audit script survives in the active repository; the original exact-hash reports and the focused executable regression suites are the controlling evidence.

## Manual and preservation evidence

Recognized completed disposable evidence (not recreated): firm `FIRM-IR1C-ALPHA`, operator `ir1c_disposable_admin`, bridge `ITFB-D8DECFC5F3B9`, trust `TR-F3C6642BADC8`. The operator confirmed Admin count/list consistency, public trust-route continuity, correct bridge/intake relationship, required confirmations, immutable events and revisions, logout, and post-logout denial with no protected data exposure.

Protected historical state was inspected through the established strict read-only preservation process. Its controlling hash history was reconciled to an authentication audit event, while governed bridge, trust, proposal, lifecycle-event, Continuity Profile, and schema state remained preserved. The database location and record identifiers remain in restricted local evidence and are intentionally excluded from published source.

Strict read-only inspection confirmed the expected historical bridge-to-trust relationship, proposal-field inventory, governed-event ordering, absence of a Continuity Profile, and preservation of the unmigrated legacy schema. Identifying record values and firm metadata remain in restricted evidence and are not reproduced here. No historical records were retrofitted.

## Deviations, residual risks, and recommendation

No TPD-1A topology obligation or TPD-1B B-01 through B-16 contract is failed or incomplete in the current candidate source. The source is still an uncommitted integrated candidate, so this verdict verifies contract inheritance but does not itself create a certified, committed, tagged, or published baseline. The next progression-preserving activity is a separate certification-candidate freeze/preservation phase; no further contract repair is indicated by this audit.

## Verdict

**CONTRACT INHERITANCE VERIFIED.**
