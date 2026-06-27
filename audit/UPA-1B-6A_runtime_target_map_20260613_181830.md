# UPA-1B-6A — Runtime Verification Target Map

Generated: 2026-06-13T18:18:34.004563
Source: `audit\UPA-1B-5_runtime_defect_triage_20260613_181635.json`

## Summary

- Active Write Functions: **5**
- Write Routes Found: **14**
- Collision Targets: **7**
- Collision References: **40**
- Unscoped Collision References: **19**
- Null Firm Ownership Maps: **6**
- Schema Review Tables: **4**

## Active Write Functions

### `update_app_user`

- Definitions: **1**
- Direct callers: **1**
- Second-level callers: **0**
- Flask routes found: **1**
  - `GET,POST /users/<username>/edit` — `app.py:6749` — `users_edit`

### `update_app_user_password`

- Definitions: **1**
- Direct callers: **3**
- Second-level callers: **0**
- Flask routes found: **3**
  - `GET,POST /users/<username>/reset_password` — `app.py:6813` — `users_reset_password`
  - `GET /admin/reset_admin_once` — `app.py:14337` — `reset_admin_once`
  - `GET,POST /change_password` — `app.py:14390` — `change_password`

### `update_distribution_record`

- Definitions: **1**
- Direct callers: **1**
- Second-level callers: **0**
- Flask routes found: **1**
  - `GET,POST /k1/trust/<trust_id>/distribution/<distribution_id>/edit` — `app.py:8074` — `k1_edit_distribution`

### `update_trust_fields`

- Definitions: **1**
- Direct callers: **8**
- Second-level callers: **0**
- Flask routes found: **8**
  - `GET,POST /create_trust_step2_grantor/<trust_id>` — `app.py:2981` — `create_trust_step2_grantor`
  - `GET,POST /create_trust_step2/<trust_id>` — `app.py:3003` — `create_trust_step2`
  - `GET,POST /create_trust_step3/<trust_id>` — `app.py:3023` — `create_trust_step3`
  - `GET,POST /create_trust_step4/<trust_id>` — `app.py:3043` — `create_trust_step4`
  - `GET,POST /create_trust_step5/<trust_id>` — `app.py:3063` — `create_trust_step5`
  - `GET,POST /create_trust_step6/<trust_id>` — `app.py:3083` — `create_trust_step6`
  - `GET,POST /trust/<trust_id>/branding` — `app.py:3272` — `trust_branding_settings`
  - `GET,POST /trust/<trust_id>/accounting-method` — `app.py:11402` — `trust_accounting_method_settings`

### `update_trust_minute_execution`

- Definitions: **1**
- Direct callers: **1**
- Second-level callers: **0**
- Flask routes found: **1**
  - `POST /minutes/<minute_id>/execute` — `app.py:7697` — `trust_minute_execute`

## Identifier Collision Targets

### `ISO-009` — `audit_log.entity_id` = `TR-001`

- Runtime references: **5**
- Unscoped references: **2**
  - `database/db.py:1939` — `init_audit_table` — scope: `none detected`
  - `database/db.py:1973` — `log_change` — scope: `firm_id`
  - `database/db.py:2044` — `get_audit_log_by_entity` — scope: `current_firm, firm_id, get_current_firm_id`
  - `database/db.py:2076` — `verify_audit_log_chain` — scope: `firm_id`
  - `database/db.py:3047` — `build_system_health_report` — scope: `none detected`

### `ISO-010` — `audit_log.entity_id` = `admin123`

- Runtime references: **5**
- Unscoped references: **2**
  - `database/db.py:1939` — `init_audit_table` — scope: `none detected`
  - `database/db.py:1973` — `log_change` — scope: `firm_id`
  - `database/db.py:2044` — `get_audit_log_by_entity` — scope: `current_firm, firm_id, get_current_firm_id`
  - `database/db.py:2076` — `verify_audit_log_chain` — scope: `firm_id`
  - `database/db.py:3047` — `build_system_health_report` — scope: `none detected`

### `ISO-011` — `intake_document_recommendations.intake_id` = `INTAKE-0005`

- Runtime references: **11**
- Unscoped references: **8**
  - `app.py:18060` — `intake_document_recommendations` — scope: `none detected`
  - `app.py:18085` — `intake_update_recommendation_status` — scope: `none detected`
  - `app.py:18101` — `intake_workflow_launch_prep` — scope: `none detected`
  - `app.py:18122` — `intake_workflow_bridge` — scope: `none detected`
  - `app.py:18204` — `intake_workflow_bridge_summary` — scope: `none detected`
  - `services/services_intake.py:3905` — `ensure_intake_document_recommendation_tables` — scope: `firm_id`
  - `services/services_intake.py:3966` — `save_document_recommendations` — scope: `current_firm, firm_id, get_current_firm_id`
  - `services/services_intake.py:4050` — `list_saved_document_recommendations` — scope: `none detected`
  - `services/services_intake.py:4435` — `update_document_recommendation_status` — scope: `none detected`
  - `services/services_intake.py:4467` — `get_document_recommendation` — scope: `none detected`
  - `services/services_intake.py:5084` — `save_workflow_bridge_answers` — scope: `current_firm, firm_id, get_current_firm_id`

### `ISO-012` — `intake_export_logs.intake_id` = `INTAKE-0005`

- Runtime references: **8**
- Unscoped references: **3**
  - `services/services_intake.py:2913` — `ensure_intake_export_log_tables` — scope: `firm_id`
  - `services/services_intake.py:2936` — `log_intake_export` — scope: `current_firm, firm_id, get_current_firm_id`
  - `services/services_intake.py:2976` — `list_intake_export_logs` — scope: `none detected`
  - `services/services_intake.py:3101` — `get_next_export_version` — scope: `none detected`
  - `services/services_intake.py:3123` — `log_intake_export_versioned` — scope: `current_firm, firm_id, get_current_firm_id`
  - `services/services_intake.py:3180` — `list_all_intake_export_logs` — scope: `current_firm, firm_id, get_current_firm_id`
  - `services/services_intake.py:3215` — `list_intake_export_logs_versioned` — scope: `none detected`
  - `services/services_intake.py:3371` — `list_all_intake_export_logs_any_scope` — scope: `firm_id`

### `ISO-013` — `intake_final_draft_gate_actions.intake_id` = `INTAKE-0005`

- Runtime references: **3**
- Unscoped references: **1**
  - `services/services_intake.py:7301` — `ensure_final_draft_resolution_tables` — scope: `firm_id`
  - `services/services_intake.py:7326` — `list_final_draft_resolution_actions` — scope: `none detected`
  - `services/services_intake.py:7361` — `record_final_draft_resolution_actions` — scope: `current_firm, firm_id, get_current_firm_id`

### `ISO-014` — `intake_review_gate_actions.intake_id` = `INTAKE-0005`

- Runtime references: **3**
- Unscoped references: **1**
  - `services/services_intake.py:6718` — `ensure_review_gate_resolution_tables` — scope: `firm_id`
  - `services/services_intake.py:6789` — `list_review_gate_actions` — scope: `none detected`
  - `services/services_intake.py:6822` — `resolve_review_gate_action` — scope: `current_firm, firm_id, get_current_firm_id`

### `ISO-015` — `workspaces.owner_id` = `ADMIN_OWNER_001`

- Runtime references: **5**
- Unscoped references: **2**
  - `app.py:318` — `run_hosted_startup_self_heal` — scope: `firm_id`
  - `app.py:8904` — `create_workspace` — scope: `firm_id, session.get("firm_id")`
  - `app.py:10528` — `discussion_new` — scope: `none detected`
  - `app.py:10888` — `document_generate` — scope: `none detected`
  - `app.py:14760` — `hosted_repair_admin_access_once` — scope: `firm_id`

## Null-Firm Ownership Review

- `ISO-016` — `audit_log` — proposed `FIRM-001`
- `ISO-017` — `audit_log` — proposed `FIRM-001`
- `ISO-018` — `audit_log` — proposed `FIRM-001`
- `ISO-019` — `documents` — proposed `FIRM-002`
- `ISO-020` — `documents` — proposed `FIRM-002`
- `ISO-021` — `documents` — proposed `FIRM-002`

## Schema Review Targets

- `ISO-022` — `chart_of_accounts` — rows: **0** — LIKELY_GLOBAL_ACCOUNT_CATALOG_OR_NEEDS_TRUST_PARENT
- `ISO-023` — `discussion_threads` — rows: **5** — LIKELY_TENANT_DATA
- `ISO-024` — `genealogy_records` — rows: **0** — LIKELY_TENANT_DATA
- `ISO-025` — `user_permission_overrides` — rows: **1** — LIKELY_FIRM_OR_USER_SCOPED

## Control

No application or database mutation occurred. This target map is the required input for controlled Firm 1 versus Firm 2 runtime testing.
