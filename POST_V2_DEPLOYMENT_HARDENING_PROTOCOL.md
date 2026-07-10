# POST-V2 Deployment Hardening Protocol

## Purpose

This protocol verifies deployment readiness after the Version 2 certified baseline.

It does not deploy the application.
It does not mutate the database.
It does not move or recreate the certified V2 tag.
It does not alter governance evidence.

## Certified Baseline

Certified Tag: v2-certified-baseline-2026-07-10

Certified Commit: 607eb174354510b64804f8dd8e4b87756f25f366

## Deployment Hardening Scope

The deployment hardening audit verifies:

- required deployment files exist
- app.py exists
- requirements.txt exists
- Procfile or render.yaml exists
- startup command is detectable
- environment configuration is detectable
- SECRET_KEY handling is detectable
- DB_PATH or database path handling is detectable
- UPLOAD_FOLDER or upload handling is detectable
- EXPORT_ROOT or export handling is detectable
- runtime database files are not staged or modified
- local-only Windows/Desktop paths are not embedded in deployment files
- certified V2 tag remains locally and remotely recoverable
- rollback instructions remain preserved

## Deployment Rule

Do not deploy from an unclean working tree.

Do not deploy from a detached HEAD unless intentionally testing rollback.

Do not deploy if the certified baseline tag cannot be resolved.

Do not deploy if runtime database files are staged or modified.

## Runtime Data Rule

Runtime data must remain outside committed source code.

Protected runtime files include:

- data/trustee_app.db
- trustee_app.db
- database.db
- data/database.db

## Environment Rule

Deployment-sensitive values should come from environment configuration.

Examples include:

- SECRET_KEY
- DB_PATH
- UPLOAD_FOLDER
- EXPORT_ROOT

## Rollback Rule

The certified rollback point remains:

v2-certified-baseline-2026-07-10

Rollback command:

git checkout v2-certified-baseline-2026-07-10

Restore branch command:

git checkout -b restore-v2-baseline v2-certified-baseline-2026-07-10

## Approved Next Phase

After POST-V2-2 passes, the next recommended phase is:

POST-V2-3 — Admin Dashboard Cleanup
