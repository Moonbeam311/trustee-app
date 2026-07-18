# Core Product Manual Operator Acceptance

## 1. Purpose

This phase validates the deferred browser/operator behavior selected by Step 25AK and records final local core acceptance evidence without repairing product defects or activating deferred modules.

## 2. Baseline

| Item | Value |
| --- | --- |
| Branch | `post-v2-planning` |
| Starting HEAD | `8e6318ce7822cd0f66cca48817b31f4c1320845e` |
| Local browser address | `http://127.0.0.1:5000` |
| Flask command | `FLASK_APP=app.py FLASK_ENV=development DB_PATH=audit/runtime_sandbox/STEP-25AL-R1/step25al_acceptance_clone.db flask run` |
| Test date | `2026-07-18` |
| Active DB historical baseline | `6E9E3EF0AE596FB296972B99EA4ED293DB8C5DBD4A64A03AA4FBB0C0CB7A6C36`, audit count `559` |
| Active DB reconciled baseline | `7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525`, audit count `569` |
| Policy SHA | `660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361` |

Roles used without passwords: `admin` as master/admin-capable FIRM-001, `admin123` as admin-capable FIRM-002, and `viewer` as restricted FIRM-001. Tests that could write audit/security rows were run against the DB clone.

## 3. Test Method

Testing used local Flask navigation and HTTP/browser-compatible GET requests against `http://127.0.0.1:5000`, terminal request-log review, route-map inspection, and clone database comparison. No production repair was made. Compliance and System Observation were tested inactive without activation. Restricted roles were tested without changing roles or permissions.

## 4. Result Classification

Labels used: PASS, PASS_EXPECTED_302, PASS_EXPECTED_403, PASS_EXPECTED_503_INACTIVE, INVALID_ASSUMED_ROUTE, OPERATOR_FRICTION, BROKEN_NAVIGATION, CONFIRMED_PRODUCT_DEFECT, AUTHORIZATION_DEFECT, DATA_INTEGRITY_DEFECT, EVIDENCE_GAP, NOT_TESTED_SAFETY, and NOT_APPLICABLE.

## 5. Authentication and Session Results

| Test | Role | Route | Expected | Actual | Result | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Login page | Anonymous | `/login` | Page loads | HTTP 200, heading Login | PASS | Clone route result |
| Protected route before login | Anonymous | `/admin` | Redirect to login | HTTP 302 followed to `/login` | PASS_EXPECTED_302 | Terminal log and final URL |
| Admin landing | Admin FIRM-002 | `/admin` | Page loads | HTTP 200, Admin Trust Operations | PASS | Clone route result |
| Logout | Admin FIRM-002 | `/logout` | Redirect/login page | HTTP 302 followed to `/login` | PASS_EXPECTED_302 | Terminal log and final URL |
| Post-logout protected access | Anonymous | `/admin` | Redirect to login | HTTP 302 followed to `/login` | PASS_EXPECTED_302 | Clone route result |
| Credential form submission | Existing account | `/login` POST | Successful route covered safely | Not repeated after CSRF-blocked clone attempt | NOT_TESTED_SAFETY | GET/session continuity covered; no password recorded |

## 6. Institutional Navigation Results

| Workspace | Start | Destination | Return path | Result | Notes |
| --- | --- | --- | --- | --- | --- |
| Admin | `/admin` | Admin dashboard | Admin shell | PASS | HTTP 200 |
| Workspaces | `/workspaces` | Workspace dashboard | Admin link visible | PASS | HTTP 200 |
| Administer | `/admin/workspace/administer` | ADMINISTER Workspace | Admin link visible | PASS | HTTP 200 |
| Governance | `/admin/workspace/governance` | GOVERNANCE Workspace | Admin link visible | PASS | HTTP 200 |
| Reports | `/admin/workspace/reports` | REPORTS Workspace | Admin link visible | PASS | HTTP 200 |
| Archive | `/admin/workspace/archive` | ARCHIVE Workspace | Admin/governance links visible | PASS | HTTP 200 |
| System | `/admin/workspace/system` | SYSTEM Workspace | Admin link visible | PASS | HTTP 200 |
| Compliance | `/admin/workspace/compliance` | COMPLIANCE Workspace | Admin link visible | PASS | HTTP 200, inactive boundary separated |

## 7. Intake Results

| Route | Role | Expected | Actual | Result | Evidence |
| --- | --- | --- | --- | --- | --- |
| `/intake/identity` | Admin FIRM-002 | Page loads | HTTP 200, Identity & Family Structure Intake | PASS | Clone |
| `/intake/dashboard` | Admin FIRM-002 | Dashboard loads | HTTP 200, Intake Dashboard | PASS | Clone |
| `/intake/INTAKE-0005/snapshot` | Admin FIRM-002 | Existing snapshot opens | HTTP 200, Your Initial Fiduciary Snapshot | PASS | Clone |

## 8. Matter and Trust Results

| Route | Role | Expected | Actual | Result | Evidence |
| --- | --- | --- | --- | --- | --- |
| `/matters` | Admin FIRM-002 | List loads | HTTP 200 | PASS | Clone |
| `/matters/MAT-000001` | Admin FIRM-002 | Detail loads | HTTP 200, MOORE-MISHOE FAMILY TRUST | PASS | Clone |
| `/trust/TR-021` | Admin FIRM-002 | Detail loads | HTTP 200 | PASS | Clone |
| `/trust/TR-022` | Admin FIRM-002 | Detail loads | HTTP 200 | PASS | Clone |
| `/trust/TR-021/execution` | Admin FIRM-002 | Execution continuity | HTTP 200 | PASS | Clone |
| `/trust/TR-022/execution` | Admin FIRM-002 | Execution continuity | HTTP 200 | PASS | Clone |
| `/trust/TR-022/packet-preview` | Admin FIRM-002 | Preview loads | HTTP 200 | OPERATOR_FRICTION | Page lacks direct admin return marker |
| `/trust/TR-022/articles-preview` | Admin FIRM-002 | Preview loads | HTTP 200 | OPERATOR_FRICTION | Page lacks direct admin return marker |

## 9. Execution and Transfer Results

| Route | Role | Expected | Actual | Result | Evidence |
| --- | --- | --- | --- | --- | --- |
| `/execution` | Admin FIRM-002 | Dashboard loads | HTTP 200 | PASS | Clone |
| `/execution/transfers` | Admin FIRM-002 | Not a defined list route | HTTP 404 | INVALID_ASSUMED_ROUTE | Route map |
| `/execution/transfers/T-0014` | Admin FIRM-002 | Transfer detail loads | HTTP 200 | PASS | Clone |
| `/execution/transfers/T-0014/review` | Admin FIRM-002 | Transfer review loads | HTTP 200 | PASS | Clone |
| `/execution/transfers/T-0014/archive-handoff` | Admin FIRM-002 | Handoff view loads | HTTP 200 | PASS | Clone |
| `/execution/transfers/T-0014/archive-handoff/audit-trail` | Admin FIRM-002 | Audit trail loads | HTTP 200 | PASS | Clone |
| `/execution/transfers/T-0014/review` | Admin FIRM-001 | Wrong-firm denial | HTTP 403 | PASS_EXPECTED_403 | Clone audit row appended |
| `/execution/transfers/T-0001/` | Admin FIRM-002 | Invalid typed URL/trailing form | HTTP 404 | INVALID_ASSUMED_ROUTE | Route map |

## 10. Reports and PDF Results

| Route | Role | Expected | Actual | Result | Evidence |
| --- | --- | --- | --- | --- | --- |
| `/reports` | Admin FIRM-002 | Report Center loads | HTTP 200 | PASS | Clone |
| `/admin/workspace/reports` | Admin FIRM-002 | Reports workspace loads | HTTP 200 | PASS | Clone |
| `/reports/audit.pdf` | Admin FIRM-002 | PDF response | HTTP 200, `application/pdf` | PASS | Clone |
| `/reports/trust/TR-022/summary.pdf` | Admin FIRM-002 | PDF response | HTTP 200, `application/pdf` | PASS | Clone |
| `/reports/portfolio.pdf` | Admin FIRM-002 | Runtime failure reproduced | HTTP 500, `NameError: get_portfolio_snapshot is not defined` in `app.py:11781` | CONFIRMED_PRODUCT_DEFECT | Terminal traceback |
| `/reports/fiduciaries.pdf` | Admin FIRM-002 | Runtime failure reproduced | HTTP 500, `sqlite3.Row` `.get` error in `pdf_utils.py:294` | CONFIRMED_PRODUCT_DEFECT | Terminal traceback |
| `/portfolio.pdf` | Admin FIRM-002 | Invalid assumed route | HTTP 404 | INVALID_ASSUMED_ROUTE | Route map has `/portfolio`, not `/portfolio.pdf` |

## 11. Fiduciary, Property, Asset, and Certificate Results

| Route | Result | Notes |
| --- | --- | --- |
| `/fiduciaries` | PASS | HTTP 200 |
| `/assets` | PASS | HTTP 200 |
| `/assets?class=other` | PASS | HTTP 200 |
| `/property/PR-001` | PASS | HTTP 200 |
| `/certificates` | PASS | HTTP 200 |
| `/continuity/certificates/CERT-000002` | PASS | HTTP 200; terminal printed existing-column skip messages only |
| `/continuity/certificates/CERT-000003` | PASS | HTTP 200; terminal printed existing-column skip messages only |
| `/continuity/certificates/verify` | PASS | HTTP 200 |
| `/continuity/certificates/verify?certification_id=CERT-000002` | PASS | HTTP 200 |
| `/continuity/certificates/verify?certification_id=CERT-000003` | PASS | HTTP 200 |
| `/continuity/certificates/verify?certification_id=CERT-DOES-NOT-EXIST` | PASS | HTTP 200 safe unknown-ID handling |

## 12. Governance Results

| Route | Result | Notes |
| --- | --- | --- |
| `/governance` | PASS | HTTP 200 |
| `/governance/dashboard` | PASS | HTTP 200 |
| `/governance/directives/DIR-2026-0001` | PASS | HTTP 200 |
| `/governance/relationship-lifecycle` | PASS | HTTP 200 |
| `/governance/relationship-audits` | PASS | HTTP 200 |
| `/governance/relationships/GR-91EC10D977` | PASS | HTTP 200 |
| `/governance/evidence-exports` | PASS | HTTP 200 |
| `/governance/evidence-exports/manifest` | PASS | HTTP 200 |
| `/governance/evidence-exports/integrity` | PASS | HTTP 200 |
| `/governance/evidence-exports/archive-intake` | PASS | HTTP 200 |
| `/governance/evidence-exports/certification` | PASS | HTTP 200 |
| `/governance/v2-certification` | PASS | HTTP 200 |

## 13. Archive Results

`/admin/workspace/archive` loaded with HTTP 200 as ARCHIVE Workspace. Repeated access did not mutate active state because this was run on the clone. No backup, recovery, archive ingestion, or export generation action was triggered.

## 14. Compliance Inactive-State Results

| Route | Expected | Actual | Result |
| --- | --- | --- | --- |
| `/admin/workspace/compliance` | Workspace page loads | HTTP 200 | PASS |
| `/compliance/reviews` | Inactive module response | HTTP 503 | PASS_EXPECTED_503_INACTIVE |
| `/compliance/reviews/CMP-2026-0001` | Inactive module response | HTTP 503 | PASS_EXPECTED_503_INACTIVE |

## 15. System Observation Inactive-State Results

| Route | Expected | Actual | Result |
| --- | --- | --- | --- |
| `/admin/workspace/system` | Workspace page loads | HTTP 200 | PASS |
| `/system/observations` | Inactive persistence response | HTTP 503 | PASS_EXPECTED_503_INACTIVE |

## 16. Users, Roles, Permissions, Security, and Audit Results

| Route | Role | Expected | Actual | Result |
| --- | --- | --- | --- | --- |
| `/users` | Admin FIRM-002 | Load | HTTP 200 | PASS |
| `/users/trustee2/edit` | Admin FIRM-002 | GET form only | HTTP 200 | PASS |
| `/users/new` | Admin FIRM-002 | GET form only | HTTP 200 | PASS |
| `/roles` | Admin FIRM-002 | Load | HTTP 200 | PASS |
| `/permissions` | Admin FIRM-002 | Load | HTTP 200 | PASS |
| `/security` | Admin FIRM-002 | Load | HTTP 200 | PASS |
| `/audit` | Admin FIRM-002 | Load | HTTP 200 | PASS |
| `/admin/audit-log` | Admin FIRM-002 | Load | HTTP 200 | PASS |
| `/audit?entity_type=export_policy` | Admin FIRM-002 | Filter load | HTTP 200 | PASS |
| `/admin/audit-log?entity_type=export_policy` | Admin FIRM-002 | Filter load | HTTP 200 | PASS |
| `/users`, `/roles`, `/permissions`, `/security`, `/admin/audit-log`, `/trust/TR-022` | Viewer FIRM-001 | Denial | HTTP 403 | PASS_EXPECTED_403 |

## 17. Route Assumption Reconciliation

`/portfolio.pdf` is an invalid assumed route; the actual report route is `/reports/portfolio.pdf`. `/change-password` is an invalid assumed route; the actual route is `/change_password`, which loaded with HTTP 200. `/execution/transfers` is an invalid assumed route; transfer routes are record-specific, including `/execution/transfers/T-0014` and `/execution/transfers/T-0014/review`.

## 18. Confirmed Product Defects

| Finding | Route | Reproduction | Impact | Evidence | Recommended next phase |
| --- | --- | --- | --- | --- | --- |
| Portfolio PDF runtime failure | `/reports/portfolio.pdf` | GET as Admin FIRM-002 | Portfolio report cannot be generated | HTTP 500; `NameError: get_portfolio_snapshot is not defined`; `app.py:11781` | Step 25AM - Reports PDF Runtime Repair |
| Fiduciary PDF runtime failure | `/reports/fiduciaries.pdf` | GET as Admin FIRM-002 | Fiduciary report cannot be generated | HTTP 500; `AttributeError: 'sqlite3.Row' object has no attribute 'get'`; `pdf_utils.py:294` | Step 25AM - Reports PDF Runtime Repair |

## 19. Authorization Findings

Expected denials worked for restricted viewer access and wrong-firm transfer access. No authorization defect was confirmed. Master/admin-capable access to FIRM-002 matter/trust records was not treated as cross-firm leakage because those records belong to FIRM-002 or the role has master/admin context.

## 20. Operator Friction and Navigation Gaps

Two preview pages loaded but lacked a direct `/admin` marker in the response: `/trust/TR-022/packet-preview` and `/trust/TR-022/articles-preview`. These are OPERATOR_FRICTION findings, not release-blocking defects.

## 21. Not Tested for Safety

Successful credential form submission, password changes, user creation, role edits, export-policy toggles, backup downloads, archive execution, recovery execution, and any POST mutation were not completed against the active database. Login/session behavior was verified through safe route access, protected-route redirect, and logout redirect. One clone login POST attempt was CSRF-blocked and not repeated.

## 22. DB and Policy Integrity

| Item | Before clone testing | After clone testing |
| --- | --- | --- |
| Active DB SHA | `7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525` | `7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525` |
| Active audit count | `569` | `569` |
| Active transfer count | `14` | `14` |
| Active policy SHA | `660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361` | `660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361` |

ACTIVE_UNCHANGED_DURING_CLONE_TESTING=True

Clone starting SHA: `7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525`

Clone final SHA: `2165DB6B2C4E74BB61942BB68C7DAAB52F50B184F5A9E99FE3578A3D936F4E1B`

The clone changed only in `audit_log` and `sqlite_sequence`.

## 23. Acceptance Decision

ACCEPTANCE_PASS_WITH_REPAIR_ITEMS

The manual matrix is materially complete for local core acceptance. Expected 302, 403, and 503 results are distinguished from defects. Invalid assumed routes are not treated as broken UI. Exactly two confirmed product defects remain, both in Reports PDF runtime generation.

## 24. Recommended Next Phase

Step 25AM - Reports PDF Runtime Repair
