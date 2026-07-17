# POST-V2-19 Core Product Operator Acceptance

Prepared state only. Manual browser testing is pending operator completion and sign-off.

## Baseline

- Repository: `~/Desktop/trustee-app-clean`
- Branch: `post-v2-planning`
- Historical prepared-acceptance source commit: `5407e1ba8b1247dbfb05c2947288270a4cfd532e`
- Current application commit after Compliance successor publication and R1 repair: `0d43de6d9e1b6f3c2a4493e4d4001650e0b92597`
- Compliance successor package commit: `d8b39c9c8e34e84388613494ce15c572b0b1e58e`
- R1 transfer-helper repair commit: `0d43de6d9e1b6f3c2a4493e4d4001650e0b92597`
- Normal database: `trustee_app.db`
- Expected database SHA-256: `6E9E3EF0AE596FB296972B99EA4ED293DB8C5DBD4A64A03AA4FBB0C0CB7A6C36`
- Expected audit log: `559` rows, maximum ID `559`
- Expected role permissions: `25`
- Expected governance relationships: `25`
- Expected governance audit ledger rows: `51`
- Compliance Review persistence: deferred
- System Observation persistence: unactivated

## Deferred Compliance Bookmark

- Deferred phase: `POST-V2-17Q-H.6G - Compliance Review Controlled Local Activation Execution and Post-Activation Certification`
- Resume point: `POST-V2-17Q-H.6G-R2 - Authorization Field and Sign-Off Completion`
- Classification: `DEFERRED_INSTITUTIONAL_AUTHORIZATION`
- Operator note: changing permissions will not activate Compliance Review persistence. Activation requires the deferred controlled phase above.

## Start Commands

```bash
cd ~/Desktop/trustee-app-clean
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

Browser start:

`http://127.0.0.1:5000/login`

Primary authenticated start:

`http://127.0.0.1:5000/admin`

## Proposed Acceptance Records

| Record | Classification | Notes |
| --- | --- | --- |
| User `admin123`, firm `FIRM-002` | SAFE_READ_ONLY_ACCEPTANCE_RECORD | Primary operator login candidate if credentials are available. |
| Matter `MAT-000001` | SAFE_READ_ONLY_ACCEPTANCE_RECORD | Existing Firm 2 matter for matter and governance continuity review. |
| Trust `TR-001` through `TR-010` | DO_NOT_MODIFY | Existing trust records are suitable for read-only navigation checks unless the operator selects a specific controlled update. |
| Transfers `T-0001` through `T-0010` | DO_NOT_MODIFY | Existing transfer records are suitable for read-only funding review. |
| Trust minutes beginning `MIN-001` | DO_NOT_MODIFY | Existing execution records are suitable for read-only execution review. |
| Archive repositories `REP-000001` through `REP-000005` | SAFE_READ_ONLY_ACCEPTANCE_RECORD | Existing archive destinations for archive workspace review. |
| Compliance Review records | MISSING | Deferred by institutional authorization; do not create during POST-V2-19. |
| System Observation records | MISSING | Not activated for this acceptance phase. |

## Controlled Database-Change Policy

Default action policy: keep each workflow `READ_ONLY` unless the operator explicitly approves a controlled workflow action before starting that step.

Allowed classifications:

- `READ_ONLY`: navigation, record viewing, and output review only.
- `EXPECTED_AUDIT_ONLY`: login, logout, or ordinary authenticated access that records only audit/session history.
- `CONTROLLED_RECORD_UPDATE`: only if the script identifies the exact existing record and intended field change.
- `CONTROLLED_RECORD_CREATION`: only if the operator approves the record type before browser testing.
- `CONTROLLED_OUTPUT_GENERATION`: only for generated documents, reports, exports, archive packages, or recovery artifacts that are retained as evidence.

No uncontrolled creation, migration, permission seeding, schema activation, Compliance write testing, or System Observation activation is part of this phase.

## Manual Browser Acceptance Script

Complete each row manually. Leave failed rows with notes and evidence.

| # | Workflow | Exact URL | Expected Page Title | Expected Visible Context | Action | Expected Result | DB Change Class | Reverse Path | PASS/FAIL | Defect Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Login | `http://127.0.0.1:5000/login` | Login | Sign-in form and institutional app context | Log in with the approved Admin operator account | Authenticated session opens the app without error | EXPECTED_AUDIT_ONLY | Logout returns to login | ____ | ____ |
| 2 | Institutional shell | `http://127.0.0.1:5000/admin` | Admin | Firm or institution context, navigation, admin workspace | Review visible navigation and workspace links | Shell loads with coherent context and no missing navigation | READ_ONLY | Admin to login via logout | ____ | ____ |
| 3 | Intake | `http://127.0.0.1:5000/intake/dashboard` | Intake | Intake workspace and intake lifecycle cues | Open intake workspace and review available actions | Intake workspace is reachable and understandable | READ_ONLY | Intake to Admin | ____ | ____ |
| 4 | Matter | `http://127.0.0.1:5000/matters/MAT-000001` | Matter Detail | Matter `MAT-000001`, firm context, linked governance context if present | Review matter summary and linked continuity panels | Matter detail loads and preserves institutional context | READ_ONLY | Matter to Matters to Admin | ____ | ____ |
| 5 | Trust | `http://127.0.0.1:5000/trust/TR-001` | Trust Detail | Trust record, trustee context, direct URL boundary behavior | Review trust detail without editing | Trust is visible only if authorized; otherwise denial is controlled | READ_ONLY | Trust to Trusts or Admin | ____ | ____ |
| 6 | Fiduciaries or people | `http://127.0.0.1:5000/fiduciaries` | Fiduciaries | Fiduciary or people listing | Review people/fiduciary records | People context is accessible without cross-firm leakage | READ_ONLY | Fiduciaries to Admin | ____ | ____ |
| 7 | Property or assets | `http://127.0.0.1:5000/assets` | Assets | Asset or property workspace | Review asset workspace and representative record link | Asset workspace loads and preserves context | READ_ONLY | Assets to Admin | ____ | ____ |
| 8 | Documents or instruments | `http://127.0.0.1:5000/documents` | Documents | Document or instrument workspace | Review document list and generation options without creating unapproved records | Document workspace is usable and bounded | READ_ONLY | Documents to Admin | ____ | ____ |
| 9 | Execution | `http://127.0.0.1:5000/execution` | Execution | Execution workspace and trust-minute context | Review execution workspace | Execution workspace loads and links to records | READ_ONLY | Execution to Admin | ____ | ____ |
| 10 | Funding or transfer | `http://127.0.0.1:5000/execution/transfers/T-0001` | Transfer Detail | Transfer record, funding status, trust context | Review representative transfer | Transfer detail is reachable if authorized and does not leak across firms | READ_ONLY | Transfer to Execution to Admin | ____ | ____ |
| 11 | Certificates | `http://127.0.0.1:5000/certificates` | Certificates | Certificate workspace | Review certificate registry and available outputs | Certificate workspace loads without schema or template errors | READ_ONLY | Certificates to Admin | ____ | ____ |
| 12 | Governance | `http://127.0.0.1:5000/governance` | Governance | Governance workspace, directives, policies, relationships | Review governance list and relationship controls | Governance workspace is usable and read/review flows are visible | READ_ONLY | Governance to Admin | ____ | ____ |
| 13 | Reports | `http://127.0.0.1:5000/reports` | Reports | Reports workspace and status panels | Review report options | Reports workspace explains available outputs and limitations | READ_ONLY | Reports to Admin | ____ | ____ |
| 14 | Archive | `http://127.0.0.1:5000/archive` | Archive | Archive workspace and repositories | Review archive status and repositories | Archive workspace is reachable and institutional context is visible | READ_ONLY | Archive to Admin | ____ | ____ |
| 15 | Continuity | `http://127.0.0.1:5000/continuity` | Continuity | Continuity workspace or controlled unavailable state | Review continuity route and status | Continuity is available or clearly bounded without data loss | READ_ONLY | Continuity to Admin | ____ | ____ |
| 16 | Recovery | `http://127.0.0.1:5000/recovery` | Recovery | Recovery workspace or controlled unavailable state | Review recovery route and safeguards | Recovery is available or clearly bounded without unsafe mutation | READ_ONLY | Recovery to Admin | ____ | ____ |
| 17 | Admin | `http://127.0.0.1:5000/admin` | Admin | Admin workspace, storage, backup, system controls | Review admin density and high-risk controls | Admin is acceptable for release or documented for targeted consolidation | READ_ONLY | Admin home | ____ | ____ |
| 18 | Audit | `http://127.0.0.1:5000/audit` | Audit | Audit visibility and event listing | Review audit page | Audit is visible to authorized operator and not visible to unauthorized users | READ_ONLY | Audit to Admin | ____ | ____ |
| 19 | Roles and Permissions | `http://127.0.0.1:5000/admin/roles` | Roles | Roles, permissions, and 25-row permission baseline context | Review roles and permissions without changing them | Permissions remain stable; no Compliance permissions appear | READ_ONLY | Roles to Admin | ____ | ____ |
| 20 | Reverse-navigation continuity | Use the current record route from steps 4, 5, 10, or 12 | Current record title | Institution, firm, matter, trust, or governance context | Navigate action to record to module to workspace to institution | Context is preserved without manual identifier re-entry | READ_ONLY | Record to Module to Admin | ____ | ____ |
| 21 | Logout | `http://127.0.0.1:5000/logout` | Login | Logged-out session boundary | Log out and try a protected route | Protected route redirects or denies unauthenticated access | EXPECTED_AUDIT_ONLY | Login page | ____ | ____ |

Optional bounded check:

| # | Workflow | Exact URL | Expected Page Title | Expected Visible Context | Action | Expected Result | DB Change Class | Reverse Path | PASS/FAIL | Defect Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 22 | Compliance unavailable boundary | `http://127.0.0.1:5000/compliance/reviews` | Compliance Review Unavailable | Foundation unavailable, no review record created | Open route only | HTTP 503 or equivalent controlled unavailable page; permissions do not activate it | READ_ONLY | Compliance to Admin | ____ | ____ |

## Output Acceptance Plan

Manual visual review is required for the following representative outputs. Do not generate new output unless the operator approves `CONTROLLED_OUTPUT_GENERATION` for that item.

| Output Type | Candidate Source | Acceptance Checks | PASS/FAIL | Defect Notes |
| --- | --- | --- | --- | --- |
| Trust document or trust-related output | Existing trust record such as `TR-001` if authorized | File exists, opens, shows trust identifier/title, no placeholder text, readable formatting, provenance visible | ____ | ____ |
| Certificate | Certificate workspace output | File exists, opens, shows certificate identifier/title, provenance visible | ____ | ____ |
| Report | Reports workspace output | File exists, opens, includes expected title, date or generated context, readable formatting | ____ | ____ |
| Export package | Export or evidence package from governed workflow | Package exists, opens, contains manifest or expected files, source record linked | ____ | ____ |
| Archive or evidence package | Archive repository or evidence export | Destination is correct, provenance visible, package is traceable | ____ | ____ |
| Continuity or recovery output | Continuity or recovery workspace | Output exists or unavailable state is controlled and documented | ____ | ____ |

## Navigation And Continuity Plan

Validate representative transitions:

- Institution to Workspace to Module to Record to Action.
- Action to Record to Module to Workspace to Institution.
- Matter detail to governance context and back.
- Trust detail to execution or document context and back.
- Transfer detail to execution workspace and back.
- Admin to audit, roles, permissions, and back.

Classify any failure as one of:

- `BLOCKING_NAVIGATION_DEFECT`
- `HIGH_PRIORITY_USABILITY_DEFECT`
- `MODERATE_USABILITY_DEFECT`
- `LOW_PRIORITY_POLISH`

## Admin And Security Plan

Validate:

- Admin landing.
- User listing.
- Roles and permissions.
- Audit visibility.
- Security and session boundary behavior.
- Export and backup controls.
- Firm context.
- No cross-firm leakage.
- No privilege escalation.
- Normal 25-row permission baseline.
- Compliance permissions absent.
- Unavailable modules clearly identified.

Admin density classification:

- `ACCEPTABLE_FOR_RELEASE`
- `ACCEPTABLE_WITH_DOCUMENTATION`
- `REQUIRES_TARGETED_CONSOLIDATION`
- `BLOCKING_USABILITY_FAILURE`

Selected classification: ____

## Defect Register

| Defect ID | Title | Module | Route | Steps | Expected Result | Actual Result | Severity | Database Impact | Security Impact | Lifecycle Impact | Workaround | Evidence Reference | Recommended Repair Phase | Blocker Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D-001 | Transfer detail route returns server error during automated pre-browser acceptance | Funding or transfer | `/execution/transfers/T-0001` | Authenticated representative GET route test using a temporary copy of `trustee_app.db` | Transfer detail should render or deny access without a 500 error | Repaired in `app.py`: `get_transfer_for_active_firm_or_404` now returns the canonical two-value contract `transfer, gate`; wrong-firm denial is carried inside `gate` as HTTP 403 | HIGH | None observed; tests used temporary database copies | Firm-scope denial preserved; no transfer ID leaked in wrong-firm response | Automated blocker repaired; manual browser acceptance remains pending | Continue to manual operator acceptance | POST-V2-19-R1 transfer helper audit and prepared acceptance audit | `POST-V2-19-M1 - Core Product Manual Operator Acceptance` | REPAIRED_AUTOMATED_PENDING_MANUAL |

Allowed severities:

- `CRITICAL`
- `HIGH`
- `MEDIUM`
- `LOW`
- `COSMETIC`

A defect is a release blocker only when it prevents safe authentication, core trust administration, institutional record preservation, correct authorization, database integrity, archive or recovery, a required operator workflow, or required output generation.

## Operator Acceptance Record

- Operator identity: ____
- Test date: ____
- Application commit: `0d43de6d9e1b6f3c2a4493e4d4001650e0b92597`
- Database pre-test hash: `6E9E3EF0AE596FB296972B99EA4ED293DB8C5DBD4A64A03AA4FBB0C0CB7A6C36`
- Database post-test hash: ____
- Tested firm: ____
- Tested records: ____
- Completed steps: ____
- Failed steps: ____
- Output review: ____
- Defect register: ____
- Acceptance determination: ____
- Operator sign-off: ____

## Post-Browser Reconciliation To Run Later

After manual testing, stop Flask, confirm port `5000` is closed, capture the post-test database manifest, compare table counts and hashes, reconcile expected and unexpected mutations, verify audit entries, verify outputs, confirm no Compliance activation, confirm no System Observation activation, and preserve the evidence package.
