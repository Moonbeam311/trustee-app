# Reports PDF Runtime Repair

## 1. Purpose

Step 25AM repaired the two confirmed Reports PDF runtime failures from Step 25AL-R1:

- `/reports/portfolio.pdf`
- `/reports/fiduciaries.pdf`

The repair was limited to runtime PDF generation. Preview-page return navigation, credential POST testing, Compliance activation, System Observation activation, and broader Reports enhancements remain deferred.

## 2. Baseline

Branch: `post-v2-planning`

Starting HEAD: `7b20ef7 Record reconciled core operator acceptance`

Required publication state at start: local `HEAD` and `origin/post-v2-planning` both pointed to `7b20ef7`.

Normal repository status at start: clean, with an empty index.

Active DB continuity baseline:

- DB SHA: `7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525`
- DB size: `3096576`
- Audit-log count: `569`
- Transfer count: `14`
- Trust count: `22`
- Matter count: `1`
- User count: `7`
- Certificate count: `3`
- Compliance/System Observation object inventory: no active persistence objects

Policy baseline:

- Policy SHA: `660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361`
- Policy size: `123`

Clone testing method:

- Application DB override confirmed as `DB_PATH`.
- Active DB was copied to ignored runtime category `audit/runtime_sandbox/STEP-25AM/`.
- Clone file: `step25am_reports_clone.db`.
- Clone starting SHA matched the active DB SHA.
- Flask was started with `FLASK_APP=app.py`, `FLASK_ENV=development`, and `DB_PATH` pointed at the clone.
- Browser address: `http://127.0.0.1:5000`.

## 3. Confirmed Pre-Repair Failures

| Route | Before | Content Type | PDF Valid | Failure |
| --- | --- | --- | --- | --- |
| `/reports/portfolio.pdf` | HTTP 500 | `text/html; charset=utf-8` | No | `NameError: get_portfolio_snapshot is not defined` in `portfolio_report_pdf()` |
| `/reports/fiduciaries.pdf` | HTTP 500 | `text/html; charset=utf-8` | No | `AttributeError: 'sqlite3.Row' object has no attribute 'get'` in `fiduciary_report_story()` |

Control routes before repair:

| Route | Before | Content Type | PDF Valid | Result |
| --- | --- | --- | --- | --- |
| `/reports/audit.pdf` | HTTP 200 | `application/pdf` | Yes | Passing control |
| `/reports/trust/TR-022/summary.pdf` | HTTP 200 | `application/pdf` | Yes | Passing control |

## 4. Root Cause - Portfolio PDF

`portfolio_report_pdf()` referenced `get_portfolio_snapshot()` and `get_portfolio_totals()`, but no canonical helper with those names exists in the application, services, models, database layer, templates, or scripts.

The canonical portfolio data source is `get_portfolio_summary()` from `database/db.py`, which is already imported by `app.py` and used by the `/portfolio` UI route. That helper returns:

- `portfolio`: list of trust-level portfolio dictionaries
- `totals`: aggregate totals dictionary

The helper preserves firm scope through the existing `get_all_trusts()` path, which selects records for the current firm context.

Root-cause classification: `DELETED_OR_MISSING_HELPER`.

## 5. Root Cause - Fiduciary PDF

`fiduciary_report_pdf()` passes `get_all_trusts()` and `get_all_fiduciaries()` results to `fiduciary_report_story()`. Those database helpers return `sqlite3.Row` objects. The PDF utility assumed ordinary dictionaries and called `.get()` on each row.

The repair boundary was selected inside `pdf_utils.py` because `fiduciary_report_story()` is the contract point that consumes both route query rows and pure dictionary callers. Normalizing there preserves dictionary support while accepting row-like mappings.

## 6. Repair

Production files changed:

- `app.py`
- `pdf_utils.py`

Behavior change:

- `app.py`: `portfolio_report_pdf()` now uses the existing canonical `get_portfolio_summary()` provider used by the `/portfolio` UI.
- `pdf_utils.py`: `fiduciary_report_story()` normalizes dictionary and row-like mapping inputs into ordinary dictionaries before using `.get()`.

No templates, migrations, schemas, authorization policy, Compliance code, System Observation code, archive/recovery code, or unrelated report routes were changed.

## 7. Automated Regression Results

`python scripts/audit_reports_pdf_runtime_repair_25am.py`: PASS

Validated:

- `/reports/portfolio.pdf` returns HTTP 200 PDF.
- `/reports/fiduciaries.pdf` returns HTTP 200 PDF.
- `/reports/fiduciaries.pdf?trust_id=TR-022` returns HTTP 200 PDF.
- `/reports/audit.pdf` remains HTTP 200 PDF.
- `/reports/trust/TR-022/summary.pdf` remains HTTP 200 PDF.
- `/reports` remains HTTP 200 for an authorized operator session.
- `/portfolio.pdf` remains HTTP 404 and was not added as an alias.
- Unauthenticated portfolio and fiduciary report access still redirects to `/login`.
- Empty portfolio and empty fiduciary story inputs produce valid nontrivial PDFs.
- Dictionary fiduciary inputs and `sqlite3.Row` fiduciary inputs are both supported.
- Malformed unsupported fiduciary input raises a clear `TypeError`.
- Active DB and policy remain unchanged.

## 8. Manual Browser Results

| Route | Before | After | Content Type | PDF Valid | Result |
| --- | --- | --- | --- | --- | --- |
| `/reports/portfolio.pdf` | HTTP 500 | HTTP 200 | `application/pdf` | Yes | Repaired by clone-backed runtime audit |
| `/reports/fiduciaries.pdf` | HTTP 500 | HTTP 200 | `application/pdf` | Yes | Repaired by clone-backed runtime audit |
| `/reports/audit.pdf` | HTTP 200 | HTTP 200 | `application/pdf` | Yes | Regression preserved |
| `/reports/trust/TR-022/summary.pdf` | HTTP 200 | HTTP 200 | `application/pdf` | Yes | Regression preserved |

Browser session result:

- Flask ran against the Step 25AM clone at `http://127.0.0.1:5000`.
- In-app browser navigation to `/admin` redirected to `/login`.
- Login page loaded successfully.
- No existing authenticated browser session was present.
- Credential POST testing remains deferred, so the browser was not used to submit login credentials.
- Authenticated PDF route behavior was verified with clone-backed application request testing rather than credential form submission.
- Terminal traceback absence was confirmed during repaired route sweeps.

## 9. Authorization and Firm Scope

Authorization remained enforced by the existing global session guard:

- Anonymous `/reports/portfolio.pdf` request: HTTP 302 to `/login`
- Anonymous `/reports/fiduciaries.pdf` request: HTTP 302 to `/login`

Firm scope remained in the existing database access layer:

- Portfolio PDF uses `get_portfolio_summary()`, which uses scoped `get_all_trusts()`.
- Fiduciary PDF uses `get_all_trusts()` and `get_all_fiduciaries()`, both scoped to current firm context.
- No bypass or broad query was introduced.

## 10. Clone-State Integrity

Permissible clone category: ignored runtime sandbox.

Observed clone business-table counts remained unchanged during automated testing:

- trusts: `22`
- matters: `1`
- transfers: `14`
- app_users: `7`
- institutional_certifications: `3`
- fiduciaries: `0`
- role_permissions: `25`

No trust, matter, transfer, user, role/permission, certificate, Compliance, System Observation, schema, policy, export, archive, or recovery mutation was introduced by the repair tests.

## 11. Active-State Integrity

ACTIVE_UNCHANGED=True

Active DB after repair testing:

- DB SHA: `7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525`
- Audit-log count: `569`
- Transfer count: `14`

POLICY_UNCHANGED=True

Policy after repair testing:

- Policy SHA: `660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361`
- Policy size: `123`

## 12. Deferred Items

Deferred explicitly:

- Preview-page direct `/admin` return marker.
- Successful credential POST testing.
- Compliance activation.
- System Observation activation.
- Unrelated Reports enhancements.

## 13. Repair Decision

REPAIR_PASS_WITH_LIMITATIONS

The two confirmed PDF runtime failures are repaired and regression-protected. The limitation is manual authenticated browser navigation: the in-app browser had no existing authenticated session, and credential POST testing remains deferred by directive.

## 14. Recommended Next Phase

Step 25AN - Remaining Operator Friction and Acceptance Evidence Closure
