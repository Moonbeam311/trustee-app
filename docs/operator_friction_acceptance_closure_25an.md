# Remaining Operator Friction and Acceptance Evidence Closure

## 1. Purpose

Step 25AN closes the remaining operator-friction acceptance evidence from Step 25AL using clone-backed runtime checks and evidence-only repository changes. No production application code was changed for this step.

## 2. Baseline

- Repository branch: `post-v2-planning`
- Starting HEAD: `7524a3b4d724cabc6f473bc3e92f14b281794174`
- Starting index: clean
- Starting worktree: clean
- Active database SHA-256: `7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525`
- Active database size: `3096576`
- Active audit rows: `569`
- Active transfer rows: `14`
- Active trust rows: `22`
- Active matter rows: `1`
- Active app user rows: `7`
- Active permissions rows: `15`
- Active institutional certification rows: `3`
- Active compliance/system-observation objects: `[]`
- Export policy SHA-256: `660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361`
- Export policy size: `123`
- Clone database: `audit/runtime_sandbox/STEP-25AN/step25an_acceptance_clone.db`
- Clone source SHA-256: `7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525`
- Runtime command: `flask run` with `FLASK_APP=app.py`, `FLASK_ENV=development`, and `DB_PATH` pointed at the Step 25AN clone
- Browser address: `http://127.0.0.1:5000`

## 3. Remaining Items from Step 25AL

Step 25AL left two preview pages classified as operator-friction items because the preview surfaces did not show a direct Admin return marker:

- `/trust/TR-022/packet-preview`
- `/trust/TR-022/articles-preview`

Step 25AN tested whether those pages have a clear, working indirect return path that preserves trust context and avoids relying on browser Back.

## 4. Preview Page 1 Result

- Page: `/trust/TR-022/packet-preview`
- Title observed: `Packet Preview TR-022`
- Source navigation: `/admin -> /trust/TR-022/execution -> /trust/TR-022/packet-preview`
- Visible return controls: `Back to Trust Execution`, `Return to Execution`
- Tested return target: `/trust/TR-022/execution`
- Return target HTTP status: `200`
- Trust context preserved: `TR-022`
- Admin return from execution dashboard: visible `Return to Admin`
- Clicks from preview page to Admin: `2`
- Classification: `PASS_INDIRECT_CLEAR_RETURN`
- Operator impact: nonblocking. The page lacks a direct Admin shortcut, but it has clear visible navigation back to the trust execution dashboard, and that dashboard has a visible Admin return control.

## 5. Preview Page 2 Result

- Page: `/trust/TR-022/articles-preview`
- Title observed: `Articles Preview TR-022`
- Source navigation: `/admin -> /trust/TR-022/execution -> /trust/TR-022/articles-preview`
- Visible return control: `Back to Trust Execution`
- Tested return target: `/trust/TR-022/execution`
- Return target HTTP status: `200`
- Trust context preserved: `TR-022`
- Admin return from execution dashboard: visible `Return to Admin`
- Clicks from preview page to Admin: `2`
- Classification: `PASS_INDIRECT_CLEAR_RETURN`
- Operator impact: nonblocking. The page lacks a direct Admin shortcut, but it has clear visible navigation back to the trust execution dashboard, and that dashboard has a visible Admin return control.

## 6. Reports Re-Acceptance

The repaired PDF report routes were re-accepted against the Step 25AN clone:

| Route | HTTP | Content type | Length | PDF magic |
| --- | ---: | --- | ---: | --- |
| `/reports/portfolio.pdf` | `200` | `application/pdf` | `2386` | `%PDF-` |
| `/reports/fiduciaries.pdf` | `200` | `application/pdf` | `2234` | `%PDF-` |
| `/reports/audit.pdf` | `200` | `application/pdf` | `13894` | `%PDF-` |
| `/reports/trust/TR-022/summary.pdf` | `200` | `application/pdf` | `2873` | `%PDF-` |

Result: all four report routes remained accepted after the Step 25AM PDF runtime repair.

## 7. Credential POST Assessment

- Exact operation: `/login` POST login submission
- CSRF source: legitimate `/login` GET
- Runtime target: Step 25AN clone database only
- Result: login POST succeeded with HTTP `302` using an existing authorized local test account
- Stored credential evidence: none. No password is recorded in this report.
- Clone audit evidence: row `570`, category `auth`, action `login_success`, note `User logged in successfully`
- Classification: `ALREADY_VERIFIED_BY_LOGIN`

The prior credential-POST limitation is closed and does not block acceptance.

## 8. Authorization Spot Check

- Admin reports workspace: `/admin/workspace/reports` returned `200`
- Reports index: `/reports` returned `200`
- Restricted viewer denial: Viewer session for `FIRM-001` received `403` for `/admin/audit-log`
- Viewer denial audit evidence: row `571`, category `security`, action `permission_denied`
- Wrong-firm denial: Admin session for `FIRM-001` received `403` for `/execution/transfers/T-0014`
- Wrong-firm denial audit evidence: row `572`, category `security`, action `transfer_firm_access_denied`

Result: authorization spot checks behaved as expected.

## 9. Inactive Module Spot Check

- Compliance workspace shell: `/admin/workspace/compliance` returned `200`
- Compliance active endpoint: `/compliance/reviews` returned `503`
- System workspace shell: `/admin/workspace/system` returned `200`
- System active endpoint: `/system/observations` returned `503`
- Compliance/System Observation objects created: none

Classification: `PASS_EXPECTED_503_INACTIVE`.

## 10. Clone-State Integrity

- Clone SHA before official test: `7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525`
- Clone SHA after official test: `46547D201353834DC26C14CCCCE37C7FCB88C7BD8D92F99EC4F8BF5A756DB16C`
- Clone audit rows: `569 -> 572`
- Clone trust rows: `22 -> 22`
- Clone matter rows: `1 -> 1`
- Clone transfer rows: `14 -> 14`
- Clone app user rows: `7 -> 7`
- Clone permissions rows: `15 -> 15`
- Clone role permission rows: `25 -> 25`
- Clone institutional certification rows: `3 -> 3`

The clone changed only by the three expected audit rows:

- `570`: `auth`, `admin123`, `login_success`, `FIRM-002`, `User logged in successfully`
- `571`: `security`, `viewer`, `permission_denied`, `FIRM-001`, `Endpoint=admin_audit_log; Role=Viewer; Required=view_audit; EffectiveOverride=True`
- `572`: `security`, `T-0014`, `transfer_firm_access_denied`, `FIRM-001`, `Transfer outside active firm scope. User=admin; Firm=FIRM-001; TransferFirm=FIRM-002`

No checked business table counts changed.

## 11. Active-State Integrity

- Active database SHA-256 after test: `7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525`
- Active audit rows after test: `569`
- Active transfer rows after test: `14`
- Export policy SHA-256 after test: `660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361`
- `ACTIVE_UNCHANGED=True`
- `POLICY_UNCHANGED=True`

## 12. Remaining Operator Friction

Blocking operator friction: none found.

Nonblocking operator friction: the two preview pages do not include a direct Admin shortcut. This is not a broken navigation path because each page has visible return navigation to the trust execution dashboard, and the execution dashboard has visible Admin return navigation while preserving `TR-022` context.

Future UX enhancement: add a direct Admin return shortcut to preview pages if operators want fewer clicks.

## 13. Acceptance Closure Decision

Decision: `ACCEPTANCE_CLOSED_WITH_NONBLOCKING_FRICTION`.

Rationale: PDFs pass, preview pages have clear indirect return paths, credential POST evidence is closed on the clone, authorization denials behave as expected, inactive modules return expected 503 responses without creating active objects, and the active database and policy file remained unchanged.

## 14. Recommended Next Phase

Recommended next phase: `Step 25AO - V2 Certification Candidate Readiness Audit`.
