# UPA-1B-6B-4D — Authoritative Repository Baseline and Runtime Separation Design

Generated: 2026-06-14T13:42:24.091755
Status: **BASELINE_CONFIRMED_SEPARATION_DESIGN_BLOCKED**

## Authoritative Repository

- Path: `C:\Users\LunaMishoe\Desktop\trustee-app-clean`
- Branch: `strapback/stable-661bb66`
- HEAD: `1cf6497598d9d294bc0453847b896316f863c241`
- Expected branch matched: **True**
- Expected HEAD matched: **True**

## Database Classification

- Mixed databases: `['trustee_app.db']`
- Firm 1 only databases: `['data\\trustee_app.db']`
- Firm 2 only databases: `[]`
- Unclassified databases: `['data\\database.db', 'database\\app.db', 'database.db']`

## admin123 Verification

- Total matches: **265**
- Database distribution: `{'trustee_app.db': 265}`
- Firm distribution: `{'FIRM-001': 11, 'FIRM-002': 231, '[NO_FIRM_COLUMN_OR_NULL]': 23}`
- Table distribution: `{'app_users': 1, 'execution_tasks': 1, 'intake_answers': 50, 'intake_document_draft_answers': 3, 'intake_document_recommendations': 15, 'intake_draft_readiness_ledger': 1, 'intake_export_logs': 3, 'intake_final_draft_gate_actions': 5, 'intake_final_draft_sections': 1, 'intake_followup_tasks': 28, 'intake_lane_events': 5, 'intake_module_ledger': 16, 'intake_review_gate_actions': 1, 'intake_review_gate_ledger': 1, 'intake_review_notes': 1, 'intake_scores': 4, 'intake_sessions': 5, 'intake_snapshots': 1, 'intake_translations': 97, 'intake_workflow_bridge_answers': 3, 'matter_events': 13, 'matter_relationships': 2, 'transfer_actions': 7, 'transfers': 1}`

## Configuration Inventory

- database: **57 reference(s)**
- session_cookie: **0 reference(s)**
- secret_key: **15 reference(s)**
- firm_scope: **873 reference(s)**
- uploads: **22 reference(s)**
- exports: **35 reference(s)**
- archives: **0 reference(s)**
- storage: **25 reference(s)**

## Findings

- Authoritative branch matches the expected baseline.
- Authoritative HEAD matches the previously verified baseline.
- No working-tree changes outside audit/ were detected.
- admin123 appears in 265 identity or audit-field record(s).

## Warnings

- admin123 appears in records associated with more than one firm. The username cannot itself determine tenant ownership.
- No explicit archive-path configuration reference was found.

## Blockers

- 1 mixed Firm 1/Firm 2 database(s) remain.
- No database containing only FIRM-002 records exists.
- No explicit SESSION_COOKIE_NAME configuration was found.

## Approved Target Architecture

- One authoritative shared codebase.
- Separate Firm 1 and Firm 2 databases.
- Separate session-cookie names.
- Separate environment-provided secret keys.
- Separate uploads, exports, archives, generated files, and temporary storage.
- Deployment-bound firm identity.
- No reliance on interactive firm switching for tenant isolation.

## Prohibited Actions

- No database rows may be deleted.
- No FIRM-001 or FIRM-002 values may be rewritten.
- No database extraction may occur.
- No database may be designated production.
- No legacy repository may be merged or restored.
- No live application startup profile may be changed.
- No admin123 ownership assumption may be made solely from username.
