# GLOBAL 411 FIREWALL · G-7H — Hosted Production Lock Memo

Date: 2026-05-15
Branch: `strapback/stable-661bb66`
Hosted app: `trustee-app-production.up.railway.app`

## Locked Scope

This checkpoint documents the hosted production stability, firewall isolation, and recovery-hardening status after G-7D through G-7G.

## Locked Milestones

### G-7D — Permanent hosted startup self-heal
Status: LOCKED

Confirmed behavior:
- Hosted admin user is recreated/maintained on startup.
- Admin role is active.
- Admin permissions include `view_dashboard`.
- Firm scope is set to `FIRM-002`.
- Startup log confirms hosted self-heal completion.

Required Railway variable:
- `ENSURE_HOSTED_ADMIN=1`

### G-7E — Permanent hosted FIRM-002 test trust seed
Status: LOCKED

Confirmed behavior:
- Hosted test trust seed runs at startup.
- Seeded trust exists as `TR-001 — Redirect Test Trust 2`.
- Trust is assigned to `FIRM-002`.
- Owner is `admin123`.
- Status is `Finalized`.
- Report Center sees the trust.
- Trust Summary PDF generates successfully.

Required Railway variable:
- `ENSURE_HOSTED_TEST_TRUST=1`

### G-7F — Hosted cleanup and emergency route hardening
Status: LOCKED

Confirmed behavior:
- Emergency recovery routes no longer expose repair/diagnostic data.
- `/hosted-trust-diagnostic-once` no longer exposes DB/session/trust data.
- Normal app routes remain operational.

### G-7G — Final hosted firewall audit
Status: LOCKED

Confirmed behavior:
- `/login` works.
- `/admin` opens.
- `/reports` opens.
- `/reports/trust/TR-001/summary.pdf` opens.
- Invalid/cross-firm direct trust routes such as `TR-002` and `TR-999` do not expose trust data.
- FIRM-002 isolation is confirmed across Admin, Reports, PDF, and direct trust routes.

## Keep ON

These variables should remain enabled:

```text
ENSURE_HOSTED_ADMIN=1
ENSURE_HOSTED_TEST_TRUST=1
HOSTED_BOOTSTRAP_USERNAME=admin123
HOSTED_BOOTSTRAP_FIRM_ID=FIRM-002
DB_PATH=/data/trustee_app.db
APP_ENV=production
```

`HOSTED_BOOTSTRAP_PASSWORD` must remain set to the current hosted admin password value.

## Keep OFF Unless Emergency Recovery Is Intentionally Needed

```text
ALLOW_HOSTED_ADMIN_BOOTSTRAP=0
ALLOW_HOSTED_FIRM_MIGRATION=0
ALLOW_HOSTED_PERMISSION_RESEED=0
ALLOW_HOSTED_LOGIN_UNLOCK=0
```

## Confirmed Hosted Trust

```text
Trust ID: TR-001
Trust Name: Redirect Test Trust 2
Firm ID: FIRM-002
Owner ID: admin123
Status: Finalized
Effective Date: 2026-05-14
```

## Confirmed Browser Routes

```text
https://trustee-app-production.up.railway.app/login
https://trustee-app-production.up.railway.app/admin
https://trustee-app-production.up.railway.app/reports
https://trustee-app-production.up.railway.app/reports/trust/TR-001/summary.pdf
```

## Security Notes

- Public diagnostic exposure was identified and hardened.
- Emergency routes must remain disabled unless intentionally re-enabled for controlled recovery.
- The startup self-heal and hosted test trust seed are non-browser operational safeguards.
- Do not remove `ENSURE_HOSTED_ADMIN` or `ENSURE_HOSTED_TEST_TRUST` until persistent storage and full seed/migration policy are re-evaluated.

## Next Recommended Phase

G-8 — Hosted production data expansion and firewall regression suite.

Candidate checks:
- Create real FIRM-002 trust data beyond seeded test trust.
- Add properties/accounts/documents/ledger records scoped to FIRM-002.
- Confirm reports and direct routes remain firm-scoped.
- Add repeatable regression script or checklist for hosted firewall validation.
