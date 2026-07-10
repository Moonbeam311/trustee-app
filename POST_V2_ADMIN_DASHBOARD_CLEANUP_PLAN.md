# POST-V2 Admin Dashboard Cleanup Plan

## Purpose

The Admin dashboard is functional but visually and operationally crowded.

This cleanup phase will reorganize the operator experience without changing certified governance evidence logic, database behavior, access-control rules, export logic, or the V2 certified baseline.

## Certified Baseline Protection

Certified Tag: v2-certified-baseline-2026-07-10

Certified Commit: 607eb174354510b64804f8dd8e4b87756f25f366

The certified baseline remains the rollback point.

## Cleanup Principle

Make the app easier to operate.

Do not weaken governance.

Do not remove certified evidence routes.

Do not mutate institutional records.

Do not restructure the database.

## Proposed Admin Dashboard Groups

1. System Status
   - health
   - current branch or build status
   - deployment readiness
   - diagnostics

2. Governance
   - governance dashboard
   - directives
   - policies
   - resolutions
   - decisions
   - evidence chain
   - V2 certification dashboard

3. Matters / Trusts
   - matter dashboard
   - trust registry
   - portfolio
   - trust execution status

4. People / Fiduciaries
   - fiduciaries
   - users
   - genealogy
   - roles connected to people

5. Documents / Exports
   - documents
   - generated instruments
   - exports
   - media

6. Archive / Continuity
   - archive readiness
   - continuity assets
   - recovery
   - backup/export preservation

7. Security / Access
   - users
   - roles
   - permissions
   - security
   - change password

8. Developer / Diagnostics
   - audit
   - logs
   - migrations
   - developer tools
   - debug/status pages

## Cleanup Rules

- Keep certified governance evidence routes intact.
- Keep V2 certification dashboard intact.
- Avoid deleting routes during initial cleanup.
- Prefer grouping, labeling, and navigation simplification first.
- Avoid changing database schema.
- Avoid changing permission rules unless separately audited.
- Avoid changing export logic.
- Avoid changing trust/matter lifecycle logic.

## First Implementation Recommendation

After the audit passes, create a cleaner Admin landing page with grouped cards.

The top-level navigation can remain stable while the Admin page becomes the clearer operator control center.

## Next Step After Audit

POST-V2-3A — Admin Dashboard Grouped Landing Page
