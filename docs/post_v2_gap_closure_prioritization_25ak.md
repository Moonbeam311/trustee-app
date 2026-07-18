# POST-V2 Gap Closure Prioritization and Build Sequence

## 1. Purpose

This document consolidates POST-V2-18 and POST-V2-19 into the current authoritative closure sequence at `b143198`. It is a planning record only. It does not implement any product change, activate Compliance Review, create records, run migrations, or certify manual browser behavior.

The source reports are:

- `docs/product_completion_gap_audit_post_v2_18.md`
- `docs/core_product_operator_acceptance_post_v2_19.md`

The current validation audits are:

- `scripts/audit_product_completion_gap_post_v2_18.py`
- `scripts/audit_core_product_operator_acceptance_post_v2_19.py`
- `scripts/audit_transfer_helper_contract_post_v2_19_r1.py`
- `scripts/run_compliance_current_successor_suite_25ae.py`

## 2. Verified Baseline

- Branch: `post-v2-planning`
- HEAD: `b1431982caa3a3a9515e2362392f31bc411880a6`
- Required evidence commits: `d8b39c9`, `0d43de6`, `fb4cb77`, `5619459`, `b143198`
- Compliance Review normal database state: inactive, with no Compliance/System Observation objects in the active database
- Active database continuity: SHA-256 `6E9E3EF0AE596FB296972B99EA4ED293DB8C5DBD4A64A03AA4FBB0C0CB7A6C36`, size `3096576`, audit log `559`, transfer count `14`
- Active policy continuity: SHA-256 `660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361`, size `123`
- Evidence gates at this baseline: POST-V2-18 PASS, POST-V2-19 PASS, POST-V2-19-R1 PASS, Compliance current successor suite PASS
- Compliance successor suite: `ACTIVE_UNCHANGED=True`, `POLICY_UNCHANGED=True`

## 3. Classification Rules

- Confirmed defect: current behavior is directly reproduced or statically proven to violate its intended contract.
- Workflow blockage: an operator cannot complete or continue an intended workflow.
- Operator acceptance gap: browser or human acceptance behavior remains unverified; this is not automatically a product defect.
- Automated coverage gap: behavior appears implemented but lacks enough reproducible audit coverage.
- Documentation or evidence gap: implementation status cannot be accepted without clearer written or audit evidence.
- Enhancement: useful expansion outside the current certification-critical scope.
- Resolved historical item: previously open or blocking, but closed by a later verified commit or current audit.

Priority uses the Step 25AK scoring model: raw risk is operator impact plus institutional record risk plus authorization risk plus data-integrity risk plus workflow criticality plus production-readiness impact. Evidence confidence is scored separately from 0 to 5.

## 4. Closed and Superseded Items

| Item | Original source | Resolution | Commit/evidence | Current status |
| --- | --- | --- | --- | --- |
| Compliance historical H6 audit contract mismatch | POST-V2-18 Compliance successor evidence limitation | Current successor suite separates historical H6 evidence from current least-privilege validation. | `d8b39c9`; `docs/compliance_audit_lineage_25ae.md`; `scripts/run_compliance_current_successor_suite_25ae.py` | HISTORICAL_RESOLVED_ITEM |
| Compliance authority and attribution successor controls | POST-V2-18 Compliance deferred architecture and audit-coverage concerns | Current audits cover authorization, firm scope, service enforcement, separation of duties, attribution, migration alignment, activation boundary, and audit lineage. | `d8b39c9`; `scripts/compliance_current_control_coverage.json` | HISTORICAL_RESOLVED_ITEM |
| Transfer detail automated server error | POST-V2-19 defect register and prepared acceptance route smoke | Transfer helper now returns the canonical `(transfer, gate)` pair and R1 validates 27 direct callers. | `0d43de6`; `scripts/audit_transfer_helper_contract_post_v2_19_r1.py` | HISTORICAL_RESOLVED_ITEM |
| Product gap report missing | POST-V2-18 documentation gap | Product completion gap report and audit were published. | `fb4cb77`; `docs/product_completion_gap_audit_post_v2_18.md` | HISTORICAL_RESOLVED_ITEM |
| Operator acceptance checklist missing | POST-V2-18 final build roadmap and acceptance checklist gap | Prepared operator acceptance document and audit were published. Manual execution remains open separately. | `5619459`; `docs/core_product_operator_acceptance_post_v2_19.md` | PARTIALLY_RESOLVED |
| Repository-shape guards rejected approved hygiene package | Step 25AJ and Step 25AJ-R1 blockers | Both POST-V2-18 and POST-V2-19 audits now classify exact approved later repository-policy paths and retain negative tests. | `b143198`; POST-V2-18 and POST-V2-19 audits | HISTORICAL_RESOLVED_ITEM |
| Raw generated audit reports creating status noise | Step 25AJ test artifact disposition | Generated JSON reports are ignored, retained locally, and documented as reproducible machine-specific output. | `b143198`; `.gitignore`; `test_artifacts/README.md` | HISTORICAL_RESOLVED_ITEM |

## 5. Open Gap Matrix

| Key | Gap | Source | Primary type | Current evidence | Operator impact | Institutional risk | Authorization risk | Data-integrity risk | Workflow criticality | Production impact | Evidence confidence | Raw risk | Priority | Dependencies | Recommended phase |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OPEN-01 | Final manual operator/browser acceptance is incomplete across the core route script and output checks. | POST-V2-18 blocker register; POST-V2-19 manual browser acceptance script | OPERATOR_ACCEPTANCE_GAP | `docs/core_product_operator_acceptance_post_v2_19.md` still contains blank PASS/FAIL and sign-off fields; prepared audit passes but states manual browser testing is pending. | 4 | 3 | 3 | 3 | 5 | 5 | 5 | 23 | P1 | Root blocker for local acceptance, hosted hardening, manuals, and certification candidate | Step 25AL |
| OPEN-02 | Representative output review is incomplete for trust documents, certificates, reports, export packages, archive evidence, and continuity/recovery output states. | POST-V2-19 Output Acceptance Plan; POST-V2-18 document/output validation notes | OPERATOR_ACCEPTANCE_GAP | Output acceptance rows remain blank; no manual visual evidence package is present. | 3 | 3 | 1 | 2 | 4 | 4 | 5 | 17 | P2 | Depends on OPEN-01 test session design; may be executed inside Step 25AL if read-only or explicitly approved output generation is used | Step 25AL |
| OPEN-03 | Hosted V2 hardening and recovery certification are incomplete. | POST-V2-18 hosted deployment status and blocker register | DEPLOYMENT_READINESS_GAP | Hosted health and recovery routes exist, but POST-V2-18 says current V2 hosted persistence, backup, restore, env flags, rollback, and SQLite write-risk controls still need final verification. | 3 | 4 | 3 | 4 | 4 | 5 | 4 | 23 | P1 | Requires OPEN-01 local acceptance first; may require hosted environment authority | Step 25AM |
| OPEN-04 | System Observation persistence decision is unresolved and normal database objects remain absent. | POST-V2-18 data completeness and deferred register; POST-V2-19 baseline | EVIDENCE_GAP | Routes/templates/services and historical 17J-17P audits exist, but active DB has no System Observation objects and current reports classify persistence as unactivated. | 2 | 3 | 2 | 2 | 3 | 3 | 4 | 15 | P3 | Depends on institutional decision after local acceptance; must not be mixed with browser acceptance | Step 25AN |
| OPEN-05 | Compliance Review activation authorization remains incomplete. | POST-V2-18 deferred stage register; POST-V2-19 Deferred Compliance Bookmark | AUTHORIZATION_CONTROL_GAP | Successor suite validates inactive boundary and local ignored H.6G files, but requester, approver, executor, verifier, authority basis, activation window, and sign-offs remain blank. | 2 | 4 | 5 | 3 | 4 | 3 | 5 | 21 | P2 | Requires institutional authorization and should follow core acceptance unless a separate authority directive arrives | Deferred activation track |
| OPEN-06 | Unified operator/admin manual is missing. | POST-V2-18 documentation gaps and blocker register | DOCUMENTATION_GAP | Documentation is distributed across phase reports; no unified operator/admin manual is tracked. | 3 | 2 | 1 | 1 | 3 | 3 | 4 | 13 | P3 | Depends on OPEN-01 findings so the manual reflects accepted flows | Step 25AO |
| OPEN-07 | Admin workspace density needs acceptance classification before deciding whether consolidation is necessary. | POST-V2-18 operator workspace findings; POST-V2-19 Admin and Security Plan | OPERATOR_ACCEPTANCE_GAP | POST-V2-19 leaves Admin density classification blank; POST-V2-18 says dense Admin is high-priority usability work but not yet a blocker. | 3 | 1 | 1 | 0 | 3 | 3 | 4 | 11 | P3 | Best evaluated during OPEN-01 manual browser acceptance; implementation only if classified as requiring targeted consolidation | Step 25AL evidence, possible later implementation |
| OPEN-08 | Final sampled non-Compliance route/security review remains open before release candidate. | POST-V2-18 authorization/security remaining risk and completion scorecard | AUTOMATED_TEST_COVERAGE_GAP | Existing route smokes and security audits exist, but POST-V2-18 calls for final sampled route authorization review. | 2 | 3 | 4 | 2 | 4 | 4 | 4 | 19 | P2 | Can follow OPEN-01 or run in parallel as a read-only static/test audit; must not activate Compliance | Step 25AM or Step 25AN |
| OPEN-09 | Funding/accounting lifecycle certification remains partial. | POST-V2-18 lifecycle audit and completion scorecard | AUTOMATED_TEST_COVERAGE_GAP | K1, Form 1041, ledger, and account routes/templates exist; no final accounting certification evidence is cited. | 2 | 3 | 1 | 3 | 3 | 3 | 3 | 15 | P3 | Requires sampled workflow and output acceptance, likely after OPEN-01 route acceptance | Step 25AO |
| OPEN-10 | Reports to Archive and hosted export persistence remain partially certified. | POST-V2-18 lifecycle audit, hosted status, and report/archive scorecard | DEPLOYMENT_READINESS_GAP | Report and archive surfaces exist, but hosted export persistence and archive/recovery drill remain incomplete. | 3 | 4 | 2 | 4 | 4 | 5 | 4 | 22 | P2 | Depends on OPEN-01 local output review and precedes hosted certification closure | Step 25AM |
| OPEN-11 | Older-module object-specific ledger coverage is not fully established. | POST-V2-18 audit/governance material gap | EVIDENCE_GAP | General audit log and several ledgers exist; report says older/legacy actions may rely on general `audit_log` rather than object-specific immutable ledgers. | 2 | 3 | 2 | 2 | 3 | 3 | 3 | 15 | P3 | Evidence-first inventory should precede any implementation | Step 25AN |
| OPEN-12 | Firm/institution identity scope is implemented but not fully certified. | POST-V2-18 module inventory and security notes | AUTOMATED_TEST_COVERAGE_GAP | Current audits cover selected firm-scope boundaries; POST-V2-18 still labels identity scope as implemented not fully certified. | 2 | 3 | 4 | 3 | 4 | 4 | 3 | 20 | P2 | Can be covered by final sampled authorization review and browser acceptance | Step 25AM |
| OPEN-13 | Compliance-to-reports lifecycle is blocked while Compliance persistence remains inactive. | POST-V2-18 lifecycle audit | AUTHORIZATION_CONTROL_GAP | Compliance reports cannot be certified until activation is authorized and executed; active database intentionally has no Compliance objects. | 1 | 3 | 4 | 3 | 3 | 2 | 5 | 16 | P2 | Blocked by OPEN-05; not a code defect while activation is deferred | Deferred activation track |

## 6. Deferred Acceptance Matrix

| Key | Workflow or route | What remains unverified | Why deferred | Required test method | Blocking status |
| --- | --- | --- | --- | --- | --- |
| ACCEPT-01 | `/login`, `/admin`, `/logout` | Manual login, shell context, logout, and protected-route behavior | Requires operator credentials and browser session | Flask browser test plus post-test DB manifest | Blocks local acceptance |
| ACCEPT-02 | `/intake/dashboard`, `/matters/MAT-000001`, `/trust/TR-001` | Read-only workflow comprehension and record context | Requires manual visual context review | Browser acceptance rows 3-5 | Blocks local acceptance |
| ACCEPT-03 | `/fiduciaries`, `/assets`, `/documents`, `/execution` | People, asset, document, and execution workspace usability | Requires manual visual route review | Browser acceptance rows 6-9 | Blocks local acceptance |
| ACCEPT-04 | `/execution/transfers/T-0001` | Manual transfer detail and reverse navigation after R1 repair | Automated route smoke passes, manual confirmation pending | Browser acceptance row 10 | Blocks local acceptance |
| ACCEPT-05 | `/certificates`, `/governance`, `/reports`, `/archive` | Certificate, governance, reports, and archive workspace acceptance | Requires manual visual route and output-context review | Browser acceptance rows 11-14 | Blocks local acceptance |
| ACCEPT-06 | `/continuity`, `/recovery` | Controlled available or unavailable state without unsafe mutation | Requires operator review of safeguards | Browser acceptance rows 15-16 | Blocks local acceptance |
| ACCEPT-07 | `/audit`, `/admin/roles` | Audit visibility and permission baseline display | Requires browser and permission-scope review | Browser acceptance rows 18-19 | Blocks local acceptance |
| ACCEPT-08 | `/compliance/reviews` | Controlled unavailable boundary with no activation | Deferred by institutional authorization | Optional read-only browser check | Does not block core local acceptance if unavailable boundary passes |
| ACCEPT-09 | Representative outputs | Visual correctness and provenance of documents, certificates, reports, exports, archive evidence, continuity/recovery output | Output generation is controlled and may require explicit operator approval | Manual output acceptance plan | Blocks output acceptance, not proof of current defect |

## 7. Documentation and Evidence Gaps

| Key | Missing evidence/documentation | Product effect | Required closure | Priority |
| --- | --- | --- | --- | --- |
| EVID-01 | Completed browser acceptance record | Cannot claim local core product acceptance | Execute Step 25AL and record pass/fail, DB manifest, and defects | P1 |
| EVID-02 | Unified operator/admin manual | Handoff requires too much phase-history knowledge | Build manual after accepted workflows are stable | P3 |
| EVID-03 | Hosted V2 recovery and persistence evidence | Hosted production certification remains incomplete | Run hosted hardening and recovery certification after local acceptance | P1 after Step 25AL |
| EVID-04 | System Observation persistence decision record | Normal DB remains intentionally unactivated with no final decision | Decide whether V2 requires persistent System Observation records | P3 |
| EVID-05 | Non-Compliance route authorization sample | Release candidate security confidence remains incomplete | Create sampled static and route audit across current non-Compliance surfaces | P2 |

## 8. Future Enhancements

| Item | Value | Why not current blocker | Earliest appropriate phase |
| --- | --- | --- | --- |
| Advanced trust-type pathways such as ILIT, dynasty, pet, firearms, ecclesiastical, land-preservation, and special-purpose trusts | Expands market and drafting coverage | POST-V2-18 classifies these as optional expansion, not core blockers | After local and hosted certification candidate |
| Expanded analytics and reporting | Better executive oversight | Current report center exists; advanced analytics are not required for core acceptance | After hosted hardening |
| External integrations and expanded electronic-signature provider support | Broader production ecosystem | Current product can be accepted without third-party integration expansion | After certification candidate |
| Mobile optimization | Better field usability | No current evidence that mobile limitations block institutional operation | Post-certification polish |

## 9. Dependency Graph

OPEN-01 -> OPEN-03
OPEN-01 -> OPEN-06
OPEN-01 -> OPEN-07
OPEN-01 -> OPEN-10
OPEN-02 -> OPEN-10
OPEN-05 -> OPEN-13
OPEN-08 -> release-candidate-evidence
OPEN-12 -> release-candidate-evidence
OPEN-03 -> hosted-production-candidate
OPEN-10 -> hosted-production-candidate
OPEN-04 -> system-observation-decision

Root blockers:

- OPEN-01 is the root local acceptance blocker.
- OPEN-05 is the root Compliance activation blocker.
- OPEN-03 and OPEN-10 are hosted-production blockers after local acceptance.

## 10. Ordered Closure Sequence

Step 25AL - Core Product Manual Operator Acceptance

- Scope: execute the existing POST-V2-19 browser acceptance checklist, including representative read-only route review, controlled unavailable Compliance check, output review only when explicitly approved, and post-browser DB reconciliation.
- Reason for order: it is the highest-risk, highest-confidence remaining local acceptance gap and gates hosted work, manuals, Admin density classification, and release-candidate confidence.
- Prerequisites: clean `post-v2-planning` baseline; Flask local server; approved operator credentials; no active migrations; no Compliance activation.
- Completion gate: signed acceptance record, failed-row defect notes, post-test DB/policy integrity comparison, and updated audit evidence.

Step 25AM - Hosted Production Hardening and Recovery Certification

- Scope: hosted/current environment persistence, backup, restore, env flags, rollback, SQLite write-risk checks, hosted export persistence, and recovery drill planning.
- Reason for order: hosted certification should not precede local operator acceptance.
- Prerequisites: Step 25AL complete with no critical local defects.
- Completion gate: hosted evidence report and audit showing persistence/recovery checks passed or controlled blockers are documented.

Step 25AN - Release Candidate Authorization and Evidence Coverage

- Scope: sampled non-Compliance route authorization, firm/institution identity scope, older-module ledger inventory, and System Observation persistence decision record.
- Reason for order: fills evidence/control gaps before certification candidate without mixing activation or UX polish.
- Prerequisites: Step 25AL, and any Step 25AM findings that affect route/security posture.
- Completion gate: static and route audits pass, decision records are explicit, and no active DB mutation occurs unless separately authorized.

Step 25AO - Operator Documentation and Acceptance Handoff

- Scope: unified operator/admin manual, accepted workflow instructions, known limitations, deferred activation notes, and handoff checklist.
- Reason for order: manual should reflect accepted flows and final control decisions.
- Prerequisites: Step 25AL and any material Step 25AN acceptance findings.
- Completion gate: manual audit validates coverage and no unsupported certification claims.

## 11. Selected Next Build

Selected next package: Step 25AL - Core Product Manual Operator Acceptance.

Problem statement: the app has passing automated prepared-mode and successor evidence, but the final browser/operator acceptance rows and output review remain blank. This prevents a credible local core product acceptance decision.

Evidence basis:

- `docs/product_completion_gap_audit_post_v2_18.md` lists final operator acceptance/browser smoke as the remaining Core Product Complete blocker.
- `docs/core_product_operator_acceptance_post_v2_19.md` is explicitly prepared state only and contains unfilled PASS/FAIL, defect notes, output review, and sign-off fields.
- `scripts/audit_core_product_operator_acceptance_post_v2_19.py` passes prepared-mode automated checks but does not replace manual browser review.
- `scripts/audit_transfer_helper_contract_post_v2_19_r1.py` resolves the known automated transfer blocker, leaving manual acceptance as the next safe gate.

Files likely involved:

- `docs/core_product_operator_acceptance_post_v2_19.md`
- a new post-browser reconciliation audit script
- optional evidence document for acceptance results

Files explicitly out of scope:

- `app.py`
- templates
- services
- models
- migrations
- active database and policy files, except read-only measurement
- Compliance activation files

Dependencies:

- clean baseline at the start of Step 25AL
- approved operator credentials
- explicit permission before any controlled output generation
- no active migration or Compliance activation

Risks:

- login/logout may create expected audit/session entries
- output generation may create artifacts if approved
- manual results may reveal product defects that require a separate implementation phase

Required tests:

- POST-V2-19 prepared audit before browser session
- local Flask browser acceptance for all required rows
- post-browser DB/policy manifest comparison
- R1 transfer helper regression
- Compliance successor suite
- a new static acceptance-result audit

Flask routes requiring browser testing:

- `/login`
- `/admin`
- `/intake/dashboard`
- `/matters/MAT-000001`
- `/trust/TR-001`
- `/fiduciaries`
- `/assets`
- `/documents`
- `/execution`
- `/execution/transfers/T-0001`
- `/certificates`
- `/governance`
- `/reports`
- `/archive`
- `/continuity`
- `/recovery`
- `/audit`
- `/admin/roles`
- `/compliance/reviews`
- `/logout`

Completion criteria:

- exactly one acceptance record is completed
- each failed row has a defect note and severity classification
- no uncontrolled database mutation occurs
- Compliance and System Observation remain inactive unless a later directive authorizes otherwise
- post-test DB/policy integrity is reconciled
- next implementation phase is selected only from actual failed rows or evidence gaps

Stop conditions:

- unexpected DB or policy change
- uncontrolled record creation
- unexpected export/upload/recovery artifact
- server error on a required route
- cross-firm exposure
- privilege escalation
- inability to distinguish expected audit/session writes from unsafe mutation

Rollback boundary:

- Step 25AL should commit only acceptance documentation/audit evidence unless a separate defect-fix directive is issued.
- Any production fix discovered during acceptance must be handled in a later isolated implementation package.

## 12. Explicitly Deferred Work

- Broad feature expansion.
- Admin redesign unless Step 25AL classifies the current Admin surface as blocking.
- Compliance Review activation.
- Hosted Compliance activation.
- Merge, tag, or final certification.
- Future trust-type expansion.
- Unrelated workspace enhancements.
- Cosmetic polish outside a verified blocker.

## 13. Decision Summary

Highest current risk: OPEN-01, final manual operator/browser acceptance, because it directly gates local core product acceptance and has complete evidence that the acceptance record is still blank.

Next build: Step 25AL - Core Product Manual Operator Acceptance.

Why it is next: the known automated transfer blocker is repaired, the current evidence gates pass, and no higher-confidence product defect or active authorization/data-integrity failure is currently open. Manual acceptance is the smallest safe high-value unit because it can confirm real operator behavior without modifying production code.

What must not be mixed into Step 25AL: hosted hardening, Compliance activation, System Observation persistence activation, Admin redesign, broad route refactors, future trust-type work, and opportunistic production fixes.
