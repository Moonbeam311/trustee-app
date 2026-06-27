# UPA-1B — Firm 1 / Firm 2 Implementation and Isolation Matrix

Generated: 2026-06-13T15:19:06.682643

## Repository State

- Branch: `strapback/stable-661bb66`
- HEAD: `1cf6497598d9d294bc0453847b896316f863c241`

## Database

- Selected database: `C:\Users\LunaMishoe\Desktop\trustee-app-clean\trustee_app.db`
- Tables inspected: **88**
- Tenant-scoped tables: **68**
- Possible global tables: **5**
- Tables requiring tenant-scope review: **15**

## Firm Values Found

- `FIRM-001`: 395 rows
- `FIRM-002`: 351 rows
- `[NULL]`: 6 rows

## Table Matrix

| Table | Classification | Rows | firm_id | Firm Counts |
|---|---|---:|---|---|
| `accounts` | tenant_scoped | 0 | Yes | — |
| `app_users` | tenant_scoped | 7 | Yes | FIRM-001: 5, FIRM-002: 2 |
| `archive_export_history` | tenant_scoped | 0 | Yes | — |
| `archive_packet_finalization` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `asset_intake` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `audit_log` | tenant_scoped | 368 | Yes | FIRM-001: 288, FIRM-002: 77, [NULL]: 3 |
| `beneficiaries` | tenant_scoped | 0 | Yes | — |
| `chart_of_accounts` | tenant_scope_review_required | 0 | No | — |
| `continuity_custody_log` | tenant_scoped | 3 | Yes | FIRM-002: 3 |
| `controlled_docx_exports` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `controlled_export_prep` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `controlled_pdf_exports` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `decision_rules` | tenant_scope_review_required | 5 | No | — |
| `discussion_messages` | tenant_scope_review_required | 5 | No | — |
| `discussion_threads` | tenant_scope_review_required | 5 | No | — |
| `distributions` | tenant_scoped | 0 | Yes | — |
| `document_intake` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `document_templates` | tenant_scope_review_required | 3 | No | — |
| `documents` | tenant_scoped | 3 | Yes | [NULL]: 3 |
| `docx_verification_gate` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `draft_sessions` | tenant_scoped | 2 | Yes | FIRM-002: 2 |
| `draft_variable_bindings` | tenant_scoped | 8 | Yes | FIRM-002: 8 |
| `dynamic_draft_previews` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `execution_event_log` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `execution_packet_prep` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `execution_tasks` | tenant_scoped | 7 | Yes | FIRM-001: 6, FIRM-002: 1 |
| `fiduciaries` | tenant_scoped | 0 | Yes | — |
| `final_record_archive` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `genealogy_records` | tenant_scope_review_required | 0 | No | — |
| `generated_documents` | tenant_scoped | 3 | Yes | FIRM-001: 3 |
| `guided_draft_workspace` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `identity_intake` | tenant_scoped | 2 | Yes | FIRM-002: 2 |
| `instruments` | tenant_scoped | 0 | Yes | — |
| `intake_answers` | tenant_scoped | 50 | Yes | FIRM-002: 50 |
| `intake_deep_review` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `intake_document_draft_answers` | tenant_scoped | 3 | Yes | FIRM-002: 3 |
| `intake_document_recommendations` | tenant_scoped | 15 | Yes | FIRM-001: 8, FIRM-002: 7 |
| `intake_draft_readiness_ledger` | tenant_scoped | 1 | Yes | FIRM-001: 1 |
| `intake_drafting_prep_gate` | tenant_scoped | 3 | Yes | FIRM-002: 3 |
| `intake_export_logs` | tenant_scoped | 10 | Yes | FIRM-001: 7, FIRM-002: 3 |
| `intake_final_draft_admin_approvals` | tenant_scoped | 1 | Yes | FIRM-001: 1 |
| `intake_final_draft_completion_actions` | tenant_scoped | 0 | Yes | — |
| `intake_final_draft_completion_gate` | tenant_scoped | 1 | Yes | FIRM-001: 1 |
| `intake_final_draft_gate_actions` | tenant_scoped | 6 | Yes | FIRM-002: 5, FIRM-001: 1 |
| `intake_final_draft_prep_gate` | tenant_scoped | 1 | Yes | FIRM-001: 1 |
| `intake_final_draft_sections` | tenant_scoped | 7 | Yes | FIRM-001: 7 |
| `intake_final_draft_version_register` | tenant_scoped | 1 | Yes | FIRM-001: 1 |
| `intake_followup_tasks` | tenant_scoped | 28 | Yes | FIRM-002: 28 |
| `intake_lane_events` | tenant_scoped | 5 | Yes | FIRM-002: 5 |
| `intake_module_ledger` | tenant_scope_review_required | 16 | No | — |
| `intake_orchestration` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `intake_review_gate_actions` | tenant_scoped | 2 | Yes | FIRM-002: 1, FIRM-001: 1 |
| `intake_review_gate_ledger` | tenant_scoped | 1 | Yes | FIRM-001: 1 |
| `intake_review_notes` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `intake_scores` | tenant_scoped | 4 | Yes | FIRM-002: 4 |
| `intake_sessions` | tenant_scoped | 5 | Yes | FIRM-002: 5 |
| `intake_snapshots` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `intake_translations` | tenant_scoped | 97 | Yes | FIRM-002: 97 |
| `intake_workflow_bridge_answers` | tenant_scoped | 3 | Yes | FIRM-002: 3 |
| `learning_articles` | possible_global | 9 | No | — |
| `ledger_entries` | tenant_scoped | 1 | Yes | FIRM-001: 1 |
| `matter_events` | tenant_scoped | 15 | Yes | FIRM-002: 15 |
| `matter_relationships` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `matters` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `media_records` | tenant_scoped | 1 | Yes | FIRM-001: 1 |
| `pdf_execution_approval_gate` | tenant_scoped | 3 | Yes | FIRM-002: 3 |
| `permissions` | possible_global | 15 | No | — |
| `properties` | tenant_scoped | 2 | Yes | FIRM-002: 1, FIRM-001: 1 |
| `role_permissions` | possible_global | 23873 | No | — |
| `section_review_gate` | tenant_scoped | 1 | Yes | FIRM-002: 1 |
| `tax_form_guides` | possible_global | 10 | No | — |
| `transfer_actions` | tenant_scope_review_required | 95 | No | — |
| `transfer_archive_handoff` | tenant_scoped | 0 | Yes | — |
| `transfer_archive_handoff_corrections` | tenant_scoped | 0 | Yes | — |
| `transfer_records` | tenant_scope_review_required | 11 | No | — |
| `transfer_support_docs` | tenant_scope_review_required | 0 | No | — |
| `transfers` | tenant_scoped | 13 | Yes | FIRM-001: 12, FIRM-002: 1 |
| `trust_article_assignments` | tenant_scope_review_required | 3 | No | — |
| `trust_article_conditions` | tenant_scope_review_required | 0 | No | — |
| `trust_articles` | tenant_scope_review_required | 3 | No | — |
| `trust_minutes` | tenant_scoped | 15 | Yes | FIRM-001: 15 |
| `trust_template_types` | tenant_scope_review_required | 0 | No | — |
| `trusts` | tenant_scoped | 22 | Yes | FIRM-001: 20, FIRM-002: 2 |
| `tutorial_videos` | sensitive_scope_review_required | 5 | No | — |
| `user_permission_overrides` | possible_global | 1 | No | — |
| `user_roles` | tenant_scoped | 0 | Yes | — |
| `workspace_notes` | tenant_scoped | 7 | Yes | FIRM-001: 7 |
| `workspaces` | tenant_scoped | 7 | Yes | FIRM-001: 6, FIRM-002: 1 |

## Tables Requiring Tenant-Scope Review

- `chart_of_accounts` — tenant_scope_review_required — 0 rows
- `decision_rules` — tenant_scope_review_required — 5 rows
- `discussion_messages` — tenant_scope_review_required — 5 rows
- `discussion_threads` — tenant_scope_review_required — 5 rows
- `document_templates` — tenant_scope_review_required — 3 rows
- `genealogy_records` — tenant_scope_review_required — 0 rows
- `intake_module_ledger` — tenant_scope_review_required — 16 rows
- `transfer_actions` — tenant_scope_review_required — 95 rows
- `transfer_records` — tenant_scope_review_required — 11 rows
- `transfer_support_docs` — tenant_scope_review_required — 0 rows
- `trust_article_assignments` — tenant_scope_review_required — 3 rows
- `trust_article_conditions` — tenant_scope_review_required — 0 rows
- `trust_articles` — tenant_scope_review_required — 3 rows
- `trust_template_types` — tenant_scope_review_required — 0 rows
- `tutorial_videos` — sensitive_scope_review_required — 5 rows

## Null or Blank Firm IDs

- `audit_log` — NULL: 3; blank/NULL-equivalent: 3
- `documents` — NULL: 3; blank/NULL-equivalent: 3

## Unexpected Firm Values

- None detected.

## Cross-Firm Duplicate Identifiers

- `audit_log.entity_id` = `TR-001` appears in firms `FIRM-001,FIRM-002`
- `audit_log.entity_id` = `admin123` appears in firms `FIRM-001,FIRM-002`
- `intake_document_recommendations.intake_id` = `INTAKE-0005` appears in firms `FIRM-001,FIRM-002`
- `intake_export_logs.intake_id` = `INTAKE-0005` appears in firms `FIRM-001,FIRM-002`
- `intake_final_draft_gate_actions.intake_id` = `INTAKE-0005` appears in firms `FIRM-001,FIRM-002`
- `intake_review_gate_actions.intake_id` = `INTAKE-0005` appears in firms `FIRM-001,FIRM-002`
- `workspaces.owner_id` = `ADMIN_OWNER_001` appears in firms `FIRM-001,FIRM-002`

## Hard-Coded Firm References

- `app.py:1006` — hardcoded_firm_001 — `FIRM-001`
- `app.py:1010` — hardcoded_firm_001 — `FIRM-001`
- `app.py:1013` — hardcoded_firm_001 — `FIRM-001`
- `app.py:1015` — hardcoded_firm_001 — `FIRM-001`
- `app.py:1051` — hardcoded_firm_001 — `FIRM-001`
- `app.py:1055` — hardcoded_firm_001 — `FIRM-001`
- `app.py:1057` — hardcoded_firm_001 — `FIRM-001`
- `app.py:1168` — hardcoded_firm_001 — `FIRM-001`
- `app.py:6636` — hardcoded_firm_001 — `FIRM-001`
- `app.py:8607` — hardcoded_firm_001 — `FIRM-001`
- `app.py:8619` — hardcoded_firm_001 — `FIRM-001`
- `app.py:8632` — hardcoded_firm_001 — `FIRM-001`
- `app.py:8644` — hardcoded_firm_001 — `FIRM-001`
- `app.py:8672` — hardcoded_firm_001 — `FIRM-001`
- `app.py:8684` — hardcoded_firm_001 — `FIRM-001`
- `app.py:8697` — hardcoded_firm_001 — `FIRM-001`
- `app.py:8709` — hardcoded_firm_001 — `FIRM-001`
- `app.py:8738` — hardcoded_firm_001 — `FIRM-001`
- `app.py:8883` — hardcoded_firm_001 — `FIRM-001`
- `app.py:8894` — hardcoded_firm_001 — `FIRM-001`
- `app.py:8906` — hardcoded_firm_001 — `FIRM-001`
- `app.py:8929` — hardcoded_firm_001 — `FIRM-001`
- `app.py:8956` — hardcoded_firm_001 — `FIRM-001`
- `app.py:8969` — hardcoded_firm_001 — `FIRM-001`
- `app.py:11448` — hardcoded_firm_001 — `FIRM-001`
- `app.py:11680` — hardcoded_firm_001 — `FIRM-001`
- `app.py:11891` — hardcoded_firm_001 — `FIRM-001`
- `app.py:11966` — hardcoded_firm_001 — `FIRM-001`
- `app.py:12197` — hardcoded_firm_001 — `FIRM-001`
- `app.py:12660` — hardcoded_firm_001 — `FIRM-001`
- `app.py:12884` — hardcoded_firm_001 — `FIRM-001`
- `app.py:12945` — hardcoded_firm_001 — `FIRM-001`
- `app.py:13046` — hardcoded_firm_001 — `FIRM-001`
- `app.py:13119` — hardcoded_firm_001 — `FIRM-001`
- `app.py:13467` — hardcoded_firm_001 — `FIRM-001`
- `app.py:13648` — hardcoded_firm_001 — `FIRM-001`
- `app.py:13827` — hardcoded_firm_001 — `FIRM-001`
- `app.py:13930` — hardcoded_firm_001 — `FIRM-001`
- `app.py:14095` — hardcoded_firm_001 — `FIRM-001`
- `app.py:14241` — hardcoded_firm_001 — `FIRM-001`
- `app.py:14373` — hardcoded_firm_001 — `FIRM-001`
- `app.py:15392` — hardcoded_firm_001 — `FIRM-001`
- `app.py:15408` — hardcoded_firm_001 — `FIRM-001`
- `app.py:15502` — hardcoded_firm_001 — `FIRM-001`
- `app.py:15513` — hardcoded_firm_001 — `FIRM-001`
- `app.py:15554` — hardcoded_firm_001 — `FIRM-001`
- `app.py:15593` — hardcoded_firm_001 — `FIRM-001`
- `app.py:15685` — hardcoded_firm_001 — `FIRM-001`
- `app.py:15820` — hardcoded_firm_001 — `FIRM-001`
- `app.py:15832` — hardcoded_firm_001 — `FIRM-001`
- `app.py:15959` — hardcoded_firm_001 — `FIRM-001`
- `app.py:15975` — hardcoded_firm_001 — `FIRM-001`
- `app.py:16046` — hardcoded_firm_001 — `FIRM-001`
- `app.py:16143` — hardcoded_firm_001 — `FIRM-001`
- `app.py:16309` — hardcoded_firm_001 — `FIRM-001`
- `app.py:16438` — hardcoded_firm_001 — `FIRM-001`
- `app.py:16587` — hardcoded_firm_001 — `FIRM-001`
- `app.py:16772` — hardcoded_firm_001 — `FIRM-001`
- `app.py:16824` — hardcoded_firm_001 — `FIRM-001`
- `app.py:16965` — hardcoded_firm_001 — `FIRM-001`
- `app.py:17156` — hardcoded_firm_001 — `FIRM-001`
- `app.py:17208` — hardcoded_firm_001 — `FIRM-001`
- `app.py:17350` — hardcoded_firm_001 — `FIRM-001`
- `app.py:17517` — hardcoded_firm_001 — `FIRM-001`
- `app.py:17707` — hardcoded_firm_001 — `FIRM-001`
- `app.py:17835` — hardcoded_firm_001 — `FIRM-001`
- `app.py:18825` — hardcoded_firm_001 — `FIRM-001`
- `app.py:18845` — hardcoded_firm_001 — `FIRM-001`
- `app.py:18876` — hardcoded_firm_001 — `FIRM-001`
- `app.py:18887` — hardcoded_firm_001 — `FIRM-001`
- `app.py:338` — hardcoded_firm_002 — `FIRM-002`
- `app.py:551` — hardcoded_firm_002 — `FIRM-002`
- `app.py:562` — hardcoded_firm_002 — `FIRM-002`
- `app.py:562` — hardcoded_firm_002 — `FIRM-002`
- `app.py:744` — hardcoded_firm_002 — `FIRM-002`
- `app.py:747` — hardcoded_firm_002 — `FIRM-002`
- `app.py:756` — hardcoded_firm_002 — `FIRM-002`
- `app.py:10053` — hardcoded_firm_002 — `FIRM-002`
- `app.py:14483` — hardcoded_firm_002 — `FIRM-002`
- `app.py:14565` — hardcoded_firm_002 — `FIRM-002`
- `app.py:14784` — hardcoded_firm_002 — `FIRM-002`
- `database/db.py:13` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:18` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:21` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:37` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:74` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:116` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:154` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:1978` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:1978` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:1980` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:3513` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:3581` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:3598` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:3707` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:3738` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:3769` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:3803` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:3839` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:3883` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:3915` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:3947` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:3978` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:4015` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:4054` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:4092` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:4130` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:4171` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:4211` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:4253` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:4306` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:4360` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:4421` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:4493` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:4529` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:4551` — hardcoded_firm_001 — `FIRM-001`
- `database/db.py:4731` — hardcoded_firm_001 — `FIRM-001`
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md:20` — hardcoded_firm_002 — `FIRM-002`
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md:26` — hardcoded_firm_002 — `FIRM-002`
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md:32` — hardcoded_firm_002 — `FIRM-002`
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md:58` — hardcoded_firm_002 — `FIRM-002`
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md:68` — hardcoded_firm_002 — `FIRM-002`
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md:89` — hardcoded_firm_002 — `FIRM-002`
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md:116` — hardcoded_firm_002 — `FIRM-002`
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md:117` — hardcoded_firm_002 — `FIRM-002`
- `docs/GLOBAL_411_FIREWALL_G8D_HOSTED_REGRESSION_CHECKLIST.md:140` — hardcoded_firm_001 — `FIRM-001`
- `docs/GLOBAL_411_FIREWALL_G8D_HOSTED_REGRESSION_CHECKLIST.md:14` — hardcoded_firm_002 — `FIRM-002`
- `docs/GLOBAL_411_FIREWALL_G8D_HOSTED_REGRESSION_CHECKLIST.md:28` — hardcoded_firm_002 — `FIRM-002`
- `docs/GLOBAL_411_FIREWALL_G8D_HOSTED_REGRESSION_CHECKLIST.md:64` — hardcoded_firm_002 — `FIRM-002`
- `docs/GLOBAL_411_FIREWALL_G8D_HOSTED_REGRESSION_CHECKLIST.md:116` — hardcoded_firm_002 — `FIRM-002`
- `scripts/migrate_hosted_firm_scope.py:62` — hardcoded_firm_001 — `FIRM-001`
- `scripts/migrate_hosted_firm_scope.py:68` — hardcoded_firm_001 — `FIRM-001`
- `scripts/migrate_hosted_firm_scope.py:71` — hardcoded_firm_001 — `FIRM-001`
- `scripts/migrate_hosted_firm_scope.py:75` — hardcoded_firm_002 — `FIRM-002`
- `scripts/migrate_hosted_firm_scope.py:82` — hardcoded_firm_002 — `FIRM-002`
- `scripts/migrate_hosted_firm_scope.py:85` — hardcoded_firm_002 — `FIRM-002`
- `services/services_intake.py:80` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:101` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:863` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:876` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:1169` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:1567` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:2033` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:2229` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:2922` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:3915` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:5070` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:5445` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:6070` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:6417` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:6731` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:6941` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:7313` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:7615` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:7996` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:8420` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:8628` — hardcoded_firm_001 — `FIRM-001`
- `services/services_intake.py:8651` — hardcoded_firm_001 — `FIRM-001`
- `services/services_matters.py:12` — hardcoded_firm_001 — `FIRM-001`
- `services/services_matters.py:34` — hardcoded_firm_001 — `FIRM-001`
- `docs/security/GLOBAL_411_FIREWALL_PRODUCTION_HARDENING_CHECKLIST.md:9` — hardcoded_firm_001 — `FIRM-001`
- `docs/security/GLOBAL_411_FIREWALL_PRODUCTION_HARDENING_CHECKLIST.md:10` — hardcoded_firm_001 — `FIRM-001`
- `docs/security/GLOBAL_411_FIREWALL_PRODUCTION_HARDENING_CHECKLIST.md:5` — hardcoded_firm_002 — `FIRM-002`
- `docs/security/GLOBAL_411_FIREWALL_PRODUCTION_HARDENING_CHECKLIST.md:8` — hardcoded_firm_002 — `FIRM-002`
- `docs/security/GLOBAL_411_FIREWALL_PRODUCTION_HARDENING_CHECKLIST.md:9` — hardcoded_firm_002 — `FIRM-002`
- `docs/security/GLOBAL_411_FIREWALL_PRODUCTION_HARDENING_CHECKLIST.md:10` — hardcoded_firm_002 — `FIRM-002`

## Code Scope References

- `app.py` — firm_id=495, hardcoded_firm_001=70, hardcoded_firm_002=11, session_firm_id=69, sql_firm_filter=85
- `database/db.py` — firm_id=248, get_current_firm_id=49, hardcoded_firm_001=36, session_firm_id=2, sql_firm_filter=52
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md` — hardcoded_firm_002=8
- `docs/GLOBAL_411_FIREWALL_G8D_HOSTED_REGRESSION_CHECKLIST.md` — hardcoded_firm_001=1, hardcoded_firm_002=4
- `migrations/add_archive_packet_finalization.py` — firm_id=1
- `migrations/add_continuity_custody_log.py` — firm_id=1
- `models/models_transfer.py` — firm_id=1
- `scripts/migrate_hosted_firm_scope.py` — firm_id=12, hardcoded_firm_001=3, hardcoded_firm_002=3, sql_firm_filter=1
- `services/services_continuity_assets.py` — firm_id=4
- `services/services_intake.py` — firm_id=106, get_current_firm_id=27, hardcoded_firm_001=22, sql_firm_filter=4
- `services/services_matters.py` — firm_id=74, get_current_firm_id=16, hardcoded_firm_001=2, sql_firm_filter=24
- `templates/transfer_archive_handoff_audit_pdf.html` — firm_id=1
- `templates/transfer_archive_handoff_correction_detail.html` — firm_id=1
- `templates/transfer_archive_handoff_detail.html` — firm_id=1
- `templates/intake/export_history.html` — firm_id=1
- `docs/security/GLOBAL_411_FIREWALL_PRODUCTION_HARDENING_CHECKLIST.md` — hardcoded_firm_001=2, hardcoded_firm_002=4

## SQL Firm-Filter References

- `app.py:503` — `WHERE firm_id IS NULL OR TRIM(firm_id`
- `app.py:792` — `WHERE property_id = 'PROP-001' AND firm_id`
- `app.py:841` — `WHERE account_id = 'ACCT-001' AND firm_id`
- `app.py:889` — `WHERE document_id = 'DOC-001' AND firm_id`
- `app.py:937` — `WHERE entry_id = 'LEDGER-001' AND firm_id`
- `app.py:8612` — `AND firm_id`
- `app.py:8625` — `AND firm_id`
- `app.py:8637` — `AND firm_id`
- `app.py:8677` — `AND firm_id`
- `app.py:8690` — `AND firm_id`
- `app.py:8702` — `AND firm_id`
- `app.py:8744` — `AND firm_id`
- `app.py:8887` — `WHERE firm_id`
- `app.py:8899` — `AND firm_id`
- `app.py:8941` — `AND firm_id`
- `app.py:8961` — `AND firm_id`
- `app.py:10053` — `AND firm_id`
- `app.py:11462` — `WHERE trust_id = ? AND firm_id`
- `app.py:11483` — `WHERE transfer_id = ? AND firm_id`
- `app.py:11491` — `WHERE transfer_id = ? AND firm_id`
- `app.py:11505` — `WHERE transfer_id = ? AND handoff_id = ? AND firm_id`
- `app.py:11513` — `WHERE transfer_id = ? AND handoff_id = ? AND firm_id`
- `app.py:11693` — `WHERE trust_id = ? AND firm_id`
- `app.py:11714` — `WHERE transfer_id = ? AND firm_id`
- `app.py:11722` — `WHERE transfer_id = ? AND firm_id`
- `app.py:11736` — `WHERE transfer_id = ? AND handoff_id = ? AND firm_id`
- `app.py:11744` — `WHERE transfer_id = ? AND handoff_id = ? AND firm_id`
- `app.py:11978` — `WHERE transfer_id = ? AND firm_id`
- `app.py:11988` — `WHERE transfer_id = ? AND firm_id`
- `app.py:12002` — `WHERE transfer_id = ? AND handoff_id = ? AND firm_id`
- `app.py:12012` — `WHERE transfer_id = ? AND handoff_id = ? AND firm_id`
- `app.py:12895` — `WHERE handoff_id = ? AND transfer_id = ? AND firm_id`
- `app.py:12908` — `WHERE correction_id = ? AND handoff_id = ? AND transfer_id = ? AND firm_id`
- `app.py:12956` — `WHERE handoff_id = ? AND transfer_id = ? AND firm_id`
- `app.py:13022` — `WHERE handoff_id = ? AND transfer_id = ? AND firm_id`
- `app.py:13056` — `WHERE handoff_id = ? AND transfer_id = ? AND firm_id`
- `app.py:13073` — `WHERE handoff_id = ? AND transfer_id = ? AND firm_id`
- `app.py:13082` — `WHERE handoff_id = ? AND transfer_id = ? AND firm_id`
- `app.py:13134` — `WHERE transfer_id = ? AND firm_id`
- `app.py:13142` — `WHERE transfer_id = ? AND firm_id`
- `app.py:13243` — `WHERE trust_id = ? AND firm_id`
- `app.py:13264` — `WHERE transfer_id = ? AND firm_id`
- `app.py:13272` — `WHERE transfer_id = ? AND firm_id`
- `app.py:13286` — `WHERE transfer_id = ? AND handoff_id = ? AND firm_id`
- `app.py:13294` — `WHERE transfer_id = ? AND handoff_id = ? AND firm_id`
- `app.py:13482` — `WHERE transfer_id = ? AND firm_id`
- `app.py:13490` — `WHERE transfer_id = ? AND firm_id`
- `app.py:13659` — `WHERE transfer_id = ? AND firm_id`
- `app.py:13667` — `WHERE transfer_id = ? AND firm_id`
- `app.py:13838` — `WHERE transfer_id = ? AND firm_id`
- `app.py:13846` — `WHERE transfer_id = ? AND firm_id`
- `app.py:14049` — `WHERE transfer_id = ? AND firm_id`
- `app.py:14241` — `and user["firm_id`
- `app.py:14764` — `and firm_id`
- `app.py:14794` — `and firm_id`
- `app.py:14957` — `WHERE firm_id IS NULL OR TRIM(firm_id`
- `app.py:15651` — `WHERE intake_id = ? AND firm_id`
- `app.py:15746` — `WHERE intake_id = ? AND firm_id`
- `app.py:16107` — `WHERE workspace_id = ? AND firm_id`
- `app.py:16168` — `WHERE workspace_id = ? AND firm_id`
- `app.py:16273` — `WHERE workspace_id = ? AND firm_id`
- `app.py:16334` — `WHERE workspace_id = ? AND firm_id`
- `app.py:16402` — `WHERE workspace_id = ? AND firm_id`
- `app.py:16463` — `WHERE workspace_id = ? AND firm_id`
- `app.py:16544` — `WHERE workspace_id = ? AND firm_id`
- `app.py:16613` — `AND firm_id`
- `app.py:16627` — `AND firm_id`
- `app.py:16740` — `WHERE workspace_id = ? AND firm_id`
- `app.py:16781` — `WHERE export_id = ? AND firm_id`
- `app.py:16834` — `WHERE export_id = ? AND firm_id`
- `app.py:16924` — `WHERE export_id = ? AND firm_id`
- `app.py:16977` — `WHERE export_id = ? AND firm_id`
- `app.py:16991` — `AND firm_id`
- `app.py:17124` — `WHERE export_id = ? AND firm_id`
- `app.py:17165` — `WHERE pdf_export_id = ? AND firm_id`
- `app.py:17218` — `WHERE pdf_export_id = ? AND firm_id`
- `app.py:17313` — `WHERE pdf_export_id = ? AND firm_id`
- `app.py:17362` — `WHERE pdf_export_id = ? AND firm_id`
- `app.py:17379` — `AND firm_id`
- `app.py:17479` — `WHERE pdf_export_id = ? AND firm_id`
- `app.py:17529` — `WHERE packet_id = ? AND firm_id`
- `app.py:17671` — `WHERE packet_id = ? AND firm_id`
- `app.py:17719` — `WHERE event_id = ? AND firm_id`
- `app.py:17808` — `WHERE event_id = ? AND firm_id`
- `app.py:18875` — `WHERE intake_id = ? AND firm_id`
- `database/db.py:411` — `WHERE firm_id IS NULL OR TRIM(firm_id`
- `database/db.py:416` — `WHERE firm_id`
- `database/db.py:507` — `WHERE firm_id IS NULL OR TRIM(firm_id`
- `database/db.py:528` — `WHERE firm_id IS NULL OR TRIM(firm_id`
- `database/db.py:533` — `WHERE firm_id`
- `database/db.py:546` — `WHERE trust_id = ? AND firm_id`
- `database/db.py:600` — `WHERE property_id = ? AND firm_id`
- `database/db.py:614` — `WHERE trust_id = ? AND firm_id`
- `database/db.py:629` — `WHERE p.firm_id`
- `database/db.py:643` — `WHERE firm_id`
- `database/db.py:685` — `WHERE trust_id = ? AND firm_id`
- `database/db.py:697` — `WHERE property_id = ? AND firm_id`
- `database/db.py:736` — `WHERE trust_id = ? AND firm_id`
- `database/db.py:1205` — `WHERE beneficiary_id = ? AND firm_id`
- `database/db.py:1218` — `WHERE trust_id = ? AND firm_id`
- `database/db.py:1263` — `WHERE distribution_id = ? AND firm_id`
- `database/db.py:1280` — `WHERE d.trust_id = ? AND d.tax_year = ? AND d.firm_id`
- `database/db.py:1288` — `WHERE d.trust_id = ? AND d.firm_id`
- `database/db.py:1451` — `WHERE trust_id = ? AND firm_id`
- `database/db.py:1721` — `WHERE firm_id`
- `database/db.py:1804` — `WHERE instrument_id = ? AND firm_id`
- `database/db.py:1814` — `WHERE instrument_id = ? AND firm_id`
- `database/db.py:1828` — `WHERE trust_id = ? AND firm_id`
- `database/db.py:1844` — `WHERE firm_id`
- `database/db.py:1872` — `WHERE trust_id = ? AND firm_id`
- `database/db.py:1879` — `WHERE firm_id`
- `database/db.py:1898` — `WHERE firm_id`
- `database/db.py:1912` — `WHERE firm_id = ?", (firm_id`
- `database/db.py:1923` — `WHERE firm_id = ?", (firm_id`
- `database/db.py:1934` — `WHERE firm_id = ?", (firm_id`
- `database/db.py:2035` — `WHERE firm_id`
- `database/db.py:2052` — `WHERE entity_type = ? AND entity_id = ? AND firm_id`
- `database/db.py:2059` — `WHERE entity_type = ? AND firm_id`
- `database/db.py:2066` — `WHERE firm_id`
- `database/db.py:2398` — `WHERE firm_id`
- `database/db.py:2412` — `WHERE trust_id = ? AND firm_id`
- `database/db.py:2595` — `WHERE firm_id`
- `database/db.py:2608` — `WHERE related_entity_type = ? AND related_entity_id = ? AND firm_id`
- `database/db.py:2621` — `WHERE trust_id = ? AND firm_id`
- `database/db.py:2745` — `WHERE firm_id`
- `database/db.py:2758` — `WHERE trust_id = ? AND firm_id`
- `database/db.py:3373` — `WHERE firm_id`
- `database/db.py:3388` — `WHERE trust_id = ? AND firm_id`
- `database/db.py:3401` — `WHERE minute_id = ? AND firm_id`
- `database/db.py:3574` — `WHERE intake_id = ? AND firm_id`
- `database/db.py:3591` — `WHERE intake_id = ? AND firm_id`
- `database/db.py:3612` — `WHERE intake_id = ? AND firm_id = ?", (intake_id, firm_id`
- `database/db.py:3615` — `WHERE intake_id = ? AND firm_id = ?", (intake_id, firm_id`
- `database/db.py:3618` — `WHERE intake_id = ? AND firm_id = ?", (intake_id, firm_id`
- `database/db.py:4592` — `WHERE intake_id = ? AND firm_id`
- `database/db.py:4599` — `WHERE intake_id = ? AND firm_id`
- `database/db.py:4626` — `WHERE intake_id = ? AND firm_id`
- `scripts/migrate_hosted_firm_scope.py:69` — `WHERE firm_id IS NULL OR TRIM(firm_id`
- `services/services_intake.py:1670` — `WHERE firm_id`
- `services/services_intake.py:2161` — `WHERE firm_id`
- `services/services_intake.py:2394` — `WHERE firm_id`
- `services/services_intake.py:3191` — `WHERE firm_id`
- `services/services_matters.py:295` — `WHERE matter_id = ? AND firm_id = ?", (now, matter_id, firm_id`
- `services/services_matters.py:309` — `WHERE firm_id`
- `services/services_matters.py:327` — `WHERE matter_id = ? AND firm_id`
- `services/services_matters.py:345` — `AND firm_id`
- `services/services_matters.py:406` — `AND firm_id`
- `services/services_matters.py:429` — `AND firm_id`
- `services/services_matters.py:541` — `AND firm_id`
- `services/services_matters.py:555` — `AND firm_id`
- `services/services_matters.py:662` — `AND firm_id`
- `services/services_matters.py:693` — `AND firm_id`
- `services/services_matters.py:778` — `AND firm_id`
- `services/services_matters.py:839` — `AND firm_id`
- `services/services_matters.py:882` — `AND firm_id`
- `services/services_matters.py:946` — `AND firm_id`
- `services/services_matters.py:989` — `AND firm_id`
- `services/services_matters.py:1023` — `AND firm_id`
- `services/services_matters.py:1101` — `AND firm_id`
- `services/services_matters.py:1134` — `AND firm_id`
- `services/services_matters.py:1175` — `AND firm_id`
- `services/services_matters.py:1268` — `AND firm_id`
- `services/services_matters.py:1414` — `AND firm_id`
- `services/services_matters.py:1481` — `AND firm_id`
- `services/services_matters.py:1497` — `WHERE matter_id = ? AND firm_id = ?", (matter_id, firm_id`
- `services/services_matters.py:1502` — `WHERE matter_id = ? AND firm_id`

## Errors

- None.
