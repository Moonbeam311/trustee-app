# GLOBAL 411 FIREWALL · G-8D — Hosted Firewall Regression Checklist

Date: 2026-05-15
Branch: `strapback/stable-661bb66`
Hosted app: `https://trustee-app-production.up.railway.app`

## Purpose

This checklist is the repeatable hosted firewall regression test for the Trustee App after future deployments, schema changes, seed changes, report changes, and route additions.

The goal is to confirm that hosted production remains scoped to:

```text
Firm ID: FIRM-002
Admin User: admin123
Seed Trust: TR-001 — Redirect Test Trust 2
```

## Required Railway Variables

Keep ON:

```text
ENSURE_HOSTED_ADMIN=1
ENSURE_HOSTED_TEST_TRUST=1
ENSURE_HOSTED_PORTFOLIO_SEED=1
HOSTED_BOOTSTRAP_USERNAME=admin123
HOSTED_BOOTSTRAP_FIRM_ID=FIRM-002
DB_PATH=/data/trustee_app.db
APP_ENV=production
```

Keep OFF unless emergency recovery is intentionally needed:

```text
ALLOW_HOSTED_ADMIN_BOOTSTRAP=0
ALLOW_HOSTED_FIRM_MIGRATION=0
ALLOW_HOSTED_PERMISSION_RESEED=0
ALLOW_HOSTED_LOGIN_UNLOCK=0
```

## Expected Startup Logs

After Railway deploy/restart, logs should include:

```text
✅ Hosted startup self-heal complete
✅ Hosted test trust seed complete
✅ Hosted portfolio seed complete: property/account/document/ledger created
```

Known warning currently acceptable unless transfer module is being tested:

```text
⚠️ Transfer runtime schema migration failed: no such table: transfers
```

## Seeded Production Test Data

Trust:

```text
TR-001 — Redirect Test Trust 2
Firm ID: FIRM-002
Owner ID: admin123
Status: Finalized
```

Portfolio records:

```text
PROP-001 — Hosted Test Property
ACCT-001 — Checking
DOC-001 — Hosted Portfolio Seed Document
LEDGER-001 — Asset — $15,000 — Hosted portfolio seed ledger entry
```

Expected Trust Summary counts:

```text
Properties: 1
Accounts: 1
Documents: 1
Ledger Entries: 1
```

---

# Regression Test A — Normal Authenticated Routes

Open:

```text
https://trustee-app-production.up.railway.app/login
```

Expected:

```text
Login page opens.
Login with admin123 works.
```

Open:

```text
https://trustee-app-production.up.railway.app/admin
```

Expected:

```text
Admin dashboard opens.
No Access Denied.
No Internal Server Error.
Only FIRM-002 scoped data appears.
```

---

# Regression Test B — Report Center Dropdown

Open:

```text
https://trustee-app-production.up.railway.app/reports
```

Expected dropdown:

```text
TR-001 — Redirect Test Trust 2
```

Failure signatures:

```text
Dropdown empty
Dropdown shows only TR-002
Dropdown shows FIRM-001 records
Internal Server Error
Access Denied for Admin
```

---

# Regression Test C — Trust Summary PDF

Open:

```text
https://trustee-app-production.up.railway.app/reports/trust/TR-001/summary.pdf
```

Expected:

```text
Trustee App Report
Redirect Test Trust 2
Trust ID: TR-001
Properties 1
Accounts 1
Documents 1
Ledger Entries 1
PROP-001
ACCT-001
DOC-001
LEDGER-001
```

Failure signatures:

```text
Trust TR-001 not found
Counts return to 0/0/0/0
PDF opens for wrong trust
Internal Server Error
```

---

# Regression Test D — Invalid Direct Report Routes

Open:

```text
https://trustee-app-production.up.railway.app/reports/trust/TR-002/summary.pdf
https://trustee-app-production.up.railway.app/reports/trust/TR-999/summary.pdf
```

Expected acceptable results:

```text
Trust not found
Access Denied
404
```

Failure signatures:

```text
Any other trust data appears
Seeded TR-001 data appears under invalid ID
Cross-firm data appears
Raw DB output appears
```

---

# Regression Test E — Direct Trust Routes

Open:

```text
https://trustee-app-production.up.railway.app/trust/TR-001
```

Expected:

```text
Redirect Test Trust 2 opens, if route exists.
```

Open:

```text
https://trustee-app-production.up.railway.app/trust/TR-002
https://trustee-app-production.up.railway.app/trust/TR-999
```

Expected acceptable results:

```text
Not found
Access Denied
404
```

Failure signatures:

```text
Any other trust data appears
Cross-firm data appears
Seeded data appears under invalid ID
```

---

# Regression Test F — Guessed Portfolio Object Routes

Open:

```text
https://trustee-app-production.up.railway.app/property/PROP-001
https://trustee-app-production.up.railway.app/account/ACCT-001
https://trustee-app-production.up.railway.app/document/DOC-001
https://trustee-app-production.up.railway.app/ledger/LEDGER-001
```

Expected acceptable results:

```text
404
Not Found
Access Denied
Login Required
Firm-scoped authenticated detail page
```

Failure signatures:

```text
Unauthenticated sensitive portfolio exposure
Raw DB rows
Cross-firm data
Other tenant data
```

---

# Regression Test G — Emergency Route Hardening

Open in Incognito/private window while logged out:

```text
https://trustee-app-production.up.railway.app/hosted-bootstrap-admin-once
https://trustee-app-production.up.railway.app/hosted-firm-scope-migration-once
https://trustee-app-production.up.railway.app/hosted-reseed-permissions-once
https://trustee-app-production.up.railway.app/hosted-clear-login-lockout-once
https://trustee-app-production.up.railway.app/hosted-auth-diagnostic-once
https://trustee-app-production.up.railway.app/hosted-trust-diagnostic-once
https://trustee-app-production.up.railway.app/hosted-repair-admin-access-once
```

Expected acceptable results:

```text
Redirect to login
Access Denied
Hosted trust diagnostic has been permanently disabled
```

Failure signatures:

```text
Hosted admin bootstrap created
MIGRATION COMPLETE
PERMISSION RESEED COMPLETE
Login lockout cleared
HOSTED ADMIN ACCESS REPAIR COMPLETE
DB_PATH output
SESSION_USERNAME output
TRUST_ROWS output
Raw diagnostic output
```

---

# Lock Criteria

The hosted firewall regression suite is considered passed when:

```text
Login works.
Admin works.
Report Center dropdown shows TR-001 — Redirect Test Trust 2.
Trust Summary PDF shows 1/1/1/1 seeded portfolio counts.
Invalid direct routes do not expose data.
Guessed portfolio routes do not leak raw records.
Emergency routes remain blocked or disabled.
```

## Current G-8 Lock Status

```text
G-8A — Hosted portfolio seed: LOCKED
G-8B — Report Center regression + firm-scope validation: LOCKED
G-8C — Direct-route firewall regression: LOCKED
G-8D — Hosted firewall regression checklist: CREATED
```
