# UPA-1B-6B-3 — Firm 2 Testing-Ground Configuration Audit

Generated: 2026-06-13T18:37:50.031805
Status: **FIRM2_TESTING_GROUND_NOT_READY**

## Governing Rule

- Firm 2 is the testing and development instance.
- Firm 1 remains the protected baseline.
- Shared code is promoted to Firm 1 only after Firm 2 passes.
- Firm 1 and Firm 2 must not share a live database.

## Active Configuration

- Environment DB_PATH: `not set`
- Resolved database: `C:\Users\LunaMishoe\Desktop\trustee-app-clean\trustee_app.db`
- Database firms: `['FIRM-001', 'FIRM-002']`
- Database firm row counts: `{'FIRM-001': 395, 'FIRM-002': 351}`

## Summary

- Database Candidates: **5**
- Active Database Tables: **88**
- Active Database Firms: **2**
- Active Database Null Firm Rows: **6**
- Firm 001 Default References: **35**
- Firm 002 References: **29**
- Firm Switching References: **74**
- Storage References: **24**
- Session References: **15**
- Configuration References: **59**
- Blockers: **4**
- Warnings: **1**
- Passed Controls: **3**

## Passed Controls

- DB_PATH is environment-controllable.
- The secret key appears environment-controlled.
- A Firm 2 launch/configuration reference was detected.

## Blockers

- The currently resolved database contains both FIRM-001 and FIRM-002 records.
- database/db.py still contains one or more FIRM-001 defaults.
- Firm 2 does not have an explicitly separate SESSION_COOKIE_NAME.
- No clearly Firm-2-specific storage/export/archive path was detected.

## Warnings

- Internal firm-session switching remains in the shared code. It may remain temporarily, but Firm 2 must not rely on it as its isolation boundary.

## Database Inventory

### `C:\Users\LunaMishoe\Desktop\trustee-app-clean\data\database.db`

- Tables: **0**
- Firm values: `[]`
- Firm row counts: `{}`
- Null-firm rows: **0**
- SHA256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

### `C:\Users\LunaMishoe\Desktop\trustee-app-clean\data\trustee_app.db`

- Tables: **33**
- Firm values: `['FIRM-001']`
- Firm row counts: `{'FIRM-001': 123}`
- Null-firm rows: **3**
- SHA256: `3fcbbe1092072c47fe7e43fb1ab075f6ff626079511c948a1275936776b71d3c`

### `C:\Users\LunaMishoe\Desktop\trustee-app-clean\database\app.db`

- Tables: **0**
- Firm values: `[]`
- Firm row counts: `{}`
- Null-firm rows: **0**
- SHA256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

### `C:\Users\LunaMishoe\Desktop\trustee-app-clean\database.db`

- Tables: **0**
- Firm values: `[]`
- Firm row counts: `{}`
- Null-firm rows: **0**
- SHA256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

### `C:\Users\LunaMishoe\Desktop\trustee-app-clean\trustee_app.db`

- Tables: **88**
- Firm values: `['FIRM-001', 'FIRM-002']`
- Firm row counts: `{'FIRM-001': 395, 'FIRM-002': 351}`
- Null-firm rows: **6**
- SHA256: `eb2b318824be70aa2e37a5a9d7c8c5c1767a7bb7cbf9922f459128751cbf26f8`

## Decision Rule

Firm 2 must not receive mutation or migration testing until the listed blockers are corrected.
