# UPA-1B-6B-3 — Standalone Dual-Firm Architecture Alignment Audit

Generated: 2026-06-13T18:32:04.425008
Status: **TRANSITIONAL_MULTI_FIRM_IMPLEMENTATION_DETECTED**

## Governing Architecture

- One shared application codebase.
- Firm 1 runs as a standalone application instance.
- Firm 2 runs as a separate standalone application instance.
- No shared live database.
- No shared uploads, generated files, sessions, secrets, or backups.
- Business identifiers may repeat because databases are independent.

## Summary

- Database Files: **5**
- Combined Databases: **1**
- Firm 1 Database Candidates: **1**
- Firm 2 Database Candidates: **0**
- Configuration References: **1005**
- Firm References: **162**
- Storage References: **1146**
- Launch References: **0**
- Architecture Blockers: **4**

## Architecture Blockers

- At least one active database contains both FIRM-001 and FIRM-002.
- Separate session cookie names are not explicitly configured.
- Internal firm switching remains present even though each deployment should represent one standalone firm.
- No distinct Firm 1 and Firm 2 startup profiles were found.

## Database Inventory

### `data/database.db`

- Tables: **0**
- Tables with firm_id: **0**
- Firm values: `{}`
- SHA256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

### `data/trustee_app.db`

- Tables: **33**
- Tables with firm_id: **2**
- Firm values: `{'FIRM-001': 123, '[NULL]': 3}`
- SHA256: `3fcbbe1092072c47fe7e43fb1ab075f6ff626079511c948a1275936776b71d3c`

### `database/app.db`

- Tables: **0**
- Tables with firm_id: **0**
- Firm values: `{}`
- SHA256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

### `database.db`

- Tables: **0**
- Tables with firm_id: **0**
- Firm values: `{}`
- SHA256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

### `trustee_app.db`

- Tables: **88**
- Tables with firm_id: **68**
- Firm values: `{'FIRM-001': 395, 'FIRM-002': 351, '[NULL]': 6}`
- SHA256: `eb2b318824be70aa2e37a5a9d7c8c5c1767a7bb7cbf9922f459128751cbf26f8`

## Separation Controls

- Database: **NOT_SEPARATED**
- Environment Configuration: **PARTIAL**
- Session Cookie Namespace: **NOT_EXPLICITLY_SEPARATED**
- Secret Keys: **ENVIRONMENT_DRIVEN**
- File Storage: **REFERENCES_FOUND_REVIEW_REQUIRED**
- Launch Profiles: **NOT_FOUND**
- Firm Switching: **TRANSITIONAL_SWITCHING_PRESENT**

## Next Architecture Rule

All future shared-code improvements must be tested twice: once with the Firm 1 configuration and database, and once with the Firm 2 configuration and database.
