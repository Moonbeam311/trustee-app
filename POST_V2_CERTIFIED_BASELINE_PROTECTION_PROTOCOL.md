# POST-V2 Certified Baseline Protection Protocol

## Certified Baseline

Tag: v2-certified-baseline-2026-07-10

Commit: 607eb174354510b64804f8dd8e4b87756f25f366

## Protection Principle

The Version 2 certified baseline is a locked institutional reference point.

Future work must not erase, move, overwrite, or blur the certified baseline.

## Branch Discipline

Future work must occur on a post-V2 branch, not directly on the certified tag.

Recommended branches:

- post-v2-planning
- post-v2-deployment-hardening
- post-v2-admin-cleanup
- v3-development

## Rollback Commands

Return to the certified baseline directly:

git checkout v2-certified-baseline-2026-07-10

Create a restoration branch from the certified baseline:

git checkout -b restore-v2-baseline v2-certified-baseline-2026-07-10

Compare active work against the certified baseline:

git diff v2-certified-baseline-2026-07-10..HEAD

## Tag Protection Rule

Do not move, delete, force-update, or reuse the certified V2 tag.

Certified tag:

v2-certified-baseline-2026-07-10

## Runtime Data Rule

Do not commit runtime database files during post-V2 planning or protection work.

Protected runtime paths:

- data/trustee_app.db
- trustee_app.db
- database.db
- data/database.db

## Certification Continuity

V2-CERT-1 confirmed:

Certification Ready: True
Checks Failed: 0
Branch: v2-development
Working Tree Clean: True
Tag Created: False

V2-CERT-2 created and verified the official certified baseline tag.

## Next Approved Phases

- POST-V2-2 — Deployment Hardening
- POST-V2-3 — Admin Dashboard Cleanup
- V3 — Institutional Lifecycle Expansion
