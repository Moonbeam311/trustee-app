# UPA-1B-2 — Isolation Classification and Risk Reduction

Generated: 2026-06-13T15:56:54.910763
Source: `audit\UPA-1B-1_isolation_exceptions_20260613_152142.json`

## Summary

- Null Firm Records: **6**
- Scope Review Tables: **20**
- Probable Global Tables: **11**
- Dependent Scope Tables: **5**
- High Review Tables: **4**
- Cross Firm Duplicate Groups: **7**
- Hardcoded Firm References: **166**
- Hardcoded Code Review Required: **81**
- High Query Candidates: **137**
- High Route Candidates: **128**

## Critical Findings

- **HIGH — NULL_FIRM_RECORDS**: 6 — Determine correct firm ownership before any automatic update.
- **HIGH — UNSCOPED_TENANT_TABLES**: 4 — Determine whether firm_id must be added or whether scope is inherited through a parent table.
- **HIGH_REVIEW — POSSIBLE_UNSCOPED_SQL**: 137 — Inspect service/helper context before changing SQL.
- **HIGH_REVIEW — POSSIBLE_UNGATED_RECORD_ROUTES**: 128 — Inspect decorators and called service functions before patching.

## Null-Firm Records

### `audit_log`

- Identifiers: `{"id": 114, "entity_id": "trustee", "firm_id": null}`
- Risk: **HIGH**
- Reason: Tenant-scoped table contains a record without firm ownership.

```json
{
  "id": 114,
  "entity_type": "auth",
  "entity_id": "trustee",
  "action": "login_success",
  "note": "User logged in successfully",
  "created_at": "2026-04-29 16:42:03",
  "previous_hash": "f5d247f6a6faaa52f50c060bdbb8bda2760dca7b62663080257f80f7872dc89c",
  "entry_hash": "58772444f918fa176739034f73f4452fd1bb7c7740d274873ec09c760223c12e",
  "hash_algorithm": "sha256",
  "firm_id": null
}
```
### `audit_log`

- Identifiers: `{"id": 115, "entity_id": "trustee", "firm_id": null}`
- Risk: **HIGH**
- Reason: Tenant-scoped table contains a record without firm ownership.

```json
{
  "id": 115,
  "entity_type": "auth",
  "entity_id": "trustee",
  "action": "login_success",
  "note": "User logged in successfully",
  "created_at": "2026-04-29 16:43:36",
  "previous_hash": "58772444f918fa176739034f73f4452fd1bb7c7740d274873ec09c760223c12e",
  "entry_hash": "c3754a2db8fb998685c0bfdfcdb922c26ce38e2475ee592434150fddc9edbe6b",
  "hash_algorithm": "sha256",
  "firm_id": null
}
```
### `audit_log`

- Identifiers: `{"id": 116, "entity_id": "admin", "firm_id": null}`
- Risk: **HIGH**
- Reason: Tenant-scoped table contains a record without firm ownership.

```json
{
  "id": 116,
  "entity_type": "auth",
  "entity_id": "admin",
  "action": "login_success",
  "note": "User logged in successfully",
  "created_at": "2026-04-29 16:43:58",
  "previous_hash": "c3754a2db8fb998685c0bfdfcdb922c26ce38e2475ee592434150fddc9edbe6b",
  "entry_hash": "22ee34aafe54ee2be4d0e5819b2cca5d7a30345c66b07a07835a2add97568382",
  "hash_algorithm": "sha256",
  "firm_id": null
}
```
### `documents`

- Identifiers: `{"document_id": "DOC-001", "trust_id": "TR-022", "property_id": "PR-001", "account_id": "", "owner_id": null, "firm_id": null}`
- Risk: **HIGH**
- Reason: Tenant-scoped table contains a record without firm ownership.

```json
{
  "document_id": "DOC-001",
  "trust_id": "TR-022",
  "property_id": "PR-001",
  "account_id": "",
  "document_category": "property_record",
  "document_title": "PR-001 Supporting Evidence for PR-001",
  "notes": "Test evidence upload for AC-1 readiness recovery.",
  "original_filename": "PR-001_Continuity_Custody_Log (2).pdf",
  "stored_filename": "DOC-001_PR-001_Continuity_Custody_Log_2.pdf",
  "file_path": "C:\\Users\\LunaMishoe\\Desktop\\trustee-app-clean\\uploads\\DOC-001_PR-001_Continuity_Custody_Log_2.pdf",
  "owner_id": null,
  "firm_id": null
}
```
### `documents`

- Identifiers: `{"document_id": "DOC-002", "trust_id": "TR-022", "property_id": "PR-001", "account_id": "", "owner_id": null, "firm_id": null}`
- Risk: **HIGH**
- Reason: Tenant-scoped table contains a record without firm ownership.

```json
{
  "document_id": "DOC-002",
  "trust_id": "TR-022",
  "property_id": "PR-001",
  "account_id": "",
  "document_category": "property_record",
  "document_title": "Supporting Evidence for PR-001",
  "notes": "",
  "original_filename": "Continuity_Asset_Dashboard_Report (3).pdf",
  "stored_filename": "DOC-002_Continuity_Asset_Dashboard_Report_3.pdf",
  "file_path": "C:\\Users\\LunaMishoe\\Desktop\\trustee-app-clean\\uploads\\DOC-002_Continuity_Asset_Dashboard_Report_3.pdf",
  "owner_id": null,
  "firm_id": null
}
```
### `documents`

- Identifiers: `{"document_id": "DOC-003", "trust_id": "TR-022", "property_id": "PR-001", "account_id": "", "owner_id": null, "firm_id": null}`
- Risk: **HIGH**
- Reason: Tenant-scoped table contains a record without firm ownership.

```json
{
  "document_id": "DOC-003",
  "trust_id": "TR-022",
  "property_id": "PR-001",
  "account_id": "",
  "document_category": "property_record",
  "document_title": "Supporting Evidence for PR-001",
  "notes": "Test evidence upload for AC-1 readiness recovery.",
  "original_filename": "PR-001_Continuity_Custody_Log (2).pdf",
  "stored_filename": "DOC-003_PR-001_Continuity_Custody_Log_2.pdf",
  "file_path": "C:\\Users\\LunaMishoe\\Desktop\\trustee-app-clean\\uploads\\DOC-003_PR-001_Continuity_Custody_Log_2.pdf",
  "owner_id": null,
  "firm_id": null
}
```

## Table Scope Classification

| Table | Rows | Classification | Reason |
|---|---:|---|---|
| `chart_of_accounts` | 0 | HIGH_REVIEW | Tenant-sensitive domain table lacks direct firm_id. |
| `decision_rules` | 5 | PROBABLE_GLOBAL | Shared catalog, policy, learning, permission, or reference data. |
| `discussion_messages` | 5 | DEPENDENT_SCOPE_REVIEW | May inherit tenant scope through parent relation: discussion_threads |
| `discussion_threads` | 5 | HIGH_REVIEW | Tenant-sensitive domain table lacks direct firm_id. |
| `document_templates` | 3 | PROBABLE_GLOBAL | Shared catalog, policy, learning, permission, or reference data. |
| `genealogy_records` | 0 | HIGH_REVIEW | Tenant-sensitive domain table lacks direct firm_id. |
| `intake_module_ledger` | 16 | PROBABLE_GLOBAL | Shared catalog, policy, learning, permission, or reference data. |
| `learning_articles` | 9 | PROBABLE_GLOBAL | Shared catalog, policy, learning, permission, or reference data. |
| `permissions` | 15 | PROBABLE_GLOBAL | Shared catalog, policy, learning, permission, or reference data. |
| `role_permissions` | 23873 | PROBABLE_GLOBAL | Shared catalog, policy, learning, permission, or reference data. |
| `tax_form_guides` | 10 | PROBABLE_GLOBAL | Shared catalog, policy, learning, permission, or reference data. |
| `transfer_actions` | 95 | DEPENDENT_SCOPE_REVIEW | May inherit tenant scope through parent relation: transfers |
| `transfer_records` | 11 | DEPENDENT_SCOPE_REVIEW | May inherit tenant scope through parent relation: transfers |
| `transfer_support_docs` | 0 | DEPENDENT_SCOPE_REVIEW | May inherit tenant scope through parent relation: transfers |
| `trust_article_assignments` | 3 | DEPENDENT_SCOPE_REVIEW | May inherit tenant scope through parent relation: trusts |
| `trust_article_conditions` | 0 | PROBABLE_GLOBAL | Shared catalog, policy, learning, permission, or reference data. |
| `trust_articles` | 3 | PROBABLE_GLOBAL | Shared catalog, policy, learning, permission, or reference data. |
| `trust_template_types` | 0 | PROBABLE_GLOBAL | Shared catalog, policy, learning, permission, or reference data. |
| `tutorial_videos` | 5 | PROBABLE_GLOBAL | Shared catalog, policy, learning, permission, or reference data. |
| `user_permission_overrides` | 1 | HIGH_REVIEW | Tenant-sensitive domain table lacks direct firm_id. |

## Cross-Firm Duplicate Identifiers

- `audit_log.entity_id` = `TR-001` — LIKELY_VALID_TENANT_LOCAL_REUSE — firms `FIRM-001,FIRM-002`
- `audit_log.entity_id` = `admin123` — LIKELY_VALID_TENANT_LOCAL_REUSE — firms `FIRM-001,FIRM-002`
- `intake_document_recommendations.intake_id` = `INTAKE-0005` — LIKELY_VALID_TENANT_LOCAL_REUSE — firms `FIRM-001,FIRM-002`
- `intake_export_logs.intake_id` = `INTAKE-0005` — LIKELY_VALID_TENANT_LOCAL_REUSE — firms `FIRM-001,FIRM-002`
- `intake_final_draft_gate_actions.intake_id` = `INTAKE-0005` — LIKELY_VALID_TENANT_LOCAL_REUSE — firms `FIRM-001,FIRM-002`
- `intake_review_gate_actions.intake_id` = `INTAKE-0005` — LIKELY_VALID_TENANT_LOCAL_REUSE — firms `FIRM-001,FIRM-002`
- `workspaces.owner_id` = `ADMIN_OWNER_001` — LIKELY_VALID_TENANT_LOCAL_REUSE — firms `FIRM-001,FIRM-002`

## Hard-Coded Firm Reference Classification

- Code Review Required: **81**
- Likely Default Test Or Legacy: **83**
- Manual Review: **2**

## High-Review SQL Candidates

- `app.py:380` — SELECT — tables `app_users`
  - `SELECT user_id FROM app_users WHERE TRIM(LOWER(username)) = TRIM(LOWER(?))`
- `app.py:398` — SELECT — tables `app_users`
  - `SELECT COUNT(*) AS count FROM app_users`
- `app.py:624` — SELECT — tables `trusts`
  - `SELECT trust_id FROM trusts WHERE trust_id = ?`
- `app.py:11467` — SELECT — tables `transfers`
  - `SELECT * FROM transfers WHERE trust_id = ? ORDER BY created_at DESC`
- `app.py:11698` — SELECT — tables `transfers`
  - `SELECT * FROM transfers WHERE trust_id = ? ORDER BY created_at DESC`
- `app.py:11918` — SELECT — tables `trust_minutes`
  - `SELECT COUNT(*) AS count FROM trust_minutes WHERE {" AND ".join(where_parts)}`
- `app.py:13248` — SELECT — tables `transfers`
  - `SELECT * FROM transfers WHERE trust_id = ? ORDER BY created_at DESC`
- `app.py:13967` — SELECT — tables `trust_minutes`
  - `SELECT * FROM trust_minutes WHERE {" AND ".join(where_parts)} ORDER BY {order_col} DESC`
- `app.py:14124` — SELECT — tables `trust_minutes`
  - `SELECT * FROM trust_minutes WHERE {" AND ".join(where_parts)} ORDER BY {order_col} DESC`
- `app.py:14521` — SELECT — tables `app_users`
  - `SELECT user_id FROM app_users WHERE username = ?`
- `app.py:14538` — SELECT — tables `app_users`
  - `SELECT COUNT(*) AS count FROM app_users`
- `app.py:14603` — SELECT — tables `app_users`
  - `SELECT user_id FROM app_users WHERE username = ?`
- `app.py:14620` — SELECT — tables `app_users`
  - `SELECT COUNT(*) AS count FROM app_users`
- `app.py:14725` — SELECT — tables `app_users`
  - `SELECT name FROM sqlite_master WHERE type='table' AND name='app_users'`
- `app.py:14829` — SELECT — tables `app_users`
  - `SELECT user_id FROM app_users WHERE TRIM(LOWER(username)) = TRIM(LOWER(?))`
- `app.py:14845` — SELECT — tables `app_users`
  - `SELECT COUNT(*) AS count FROM app_users`
- `app.py:15356` — SELECT — tables `identity_intake`
  - `SELECT * FROM identity_intake WHERE intake_id = ?`
- `app.py:15420` — SELECT — tables `asset_intake`
  - `SELECT * FROM asset_intake WHERE intake_id = ? ORDER BY created_at DESC`
- `app.py:15465` — SELECT — tables `identity_intake`
  - `SELECT * FROM identity_intake WHERE intake_id = ?`
- `app.py:15523` — SELECT — tables `document_intake`
  - `SELECT * FROM document_intake WHERE intake_id = ? ORDER BY created_at DESC`
- `app.py:15786` — SELECT — tables `identity_intake`
  - `SELECT * FROM identity_intake WHERE intake_id = ?`
- `app.py:15900` — SELECT — tables `identity_intake`
  - `SELECT * FROM identity_intake WHERE intake_id = ?`
- `app.py:15908` — SELECT — tables `asset_intake`
  - `SELECT * FROM asset_intake WHERE intake_id = ?`
- `app.py:15916` — SELECT — tables `document_intake`
  - `SELECT * FROM document_intake WHERE intake_id = ?`
- `app.py:15985` — SELECT — tables `guided_draft_workspace`
  - `SELECT * FROM guided_draft_workspace WHERE draft_session_id = ? ORDER BY created_at DESC`
- `app.py:16031` — SELECT — tables `guided_draft_workspace`
  - `SELECT * FROM guided_draft_workspace WHERE workspace_id = ?`
- `app.py:16152` — SELECT — tables `guided_draft_workspace`
  - `SELECT * FROM guided_draft_workspace WHERE workspace_id = ?`
- `app.py:16318` — SELECT — tables `guided_draft_workspace`
  - `SELECT * FROM guided_draft_workspace WHERE workspace_id = ?`
- `app.py:16447` — SELECT — tables `guided_draft_workspace`
  - `SELECT * FROM guided_draft_workspace WHERE workspace_id = ?`
- `app.py:16596` — SELECT — tables `guided_draft_workspace`
  - `SELECT * FROM guided_draft_workspace WHERE workspace_id = ?`
- `database/db.py:431` — SELECT — tables `trusts`
  - `SELECT COUNT(*) AS count FROM trusts`
- `database/db.py:558` — UPDATE — tables `trusts`
  - `UPDATE trusts SET {fields} WHERE trust_id = ?`
- `database/db.py:654` — SELECT — tables `accounts`
  - `SELECT COUNT(*) AS count FROM accounts`
- `database/db.py:707` — SELECT — tables `documents`
  - `SELECT COUNT(*) AS count FROM documents`
- `database/db.py:755` — SELECT — tables `documents`
  - `SELECT * FROM documents WHERE property_id = ? ORDER BY document_id`
- `database/db.py:765` — SELECT — tables `ledger_entries`
  - `SELECT COUNT(*) AS count FROM ledger_entries`
- `database/db.py:793` — SELECT — tables `ledger_entries`
  - `SELECT * FROM ledger_entries WHERE trust_id = ? AND owner_id = ? ORDER BY entry_id`
- `database/db.py:804` — SELECT — tables `ledger_entries`
  - `SELECT * FROM ledger_entries WHERE property_id = ? AND owner_id = ? ORDER BY entry_id`
- `database/db.py:1163` — SELECT — tables `distributions`
  - `SELECT COUNT(*) AS count FROM distributions`
- `database/db.py:1253` — UPDATE — tables `distributions`
  - `UPDATE distributions SET {fields} WHERE distribution_id = ?`
- `database/db.py:1384` — SELECT — tables `beneficiaries, distributions`
  - `SELECT d.*, b.full_name AS beneficiary_name, b.tax_id AS beneficiary_tax_id FROM distributions d LEFT JOIN beneficiaries b ON d.beneficiary_id = b.beneficiary_id WHERE d.distribution_id = ? AND d.trust_id = ?`
- `database/db.py:1538` — SELECT — tables `ledger_entries`
  - `SELECT * FROM ledger_entries WHERE trust_id = ? ORDER BY entry_date DESC, entry_id DESC`
- `database/db.py:2556` — SELECT — tables `media_records`
  - `SELECT COUNT(*) AS count FROM media_records`
- `database/db.py:2711` — SELECT — tables `user_roles`
  - `SELECT COUNT(*) AS count FROM user_roles`
- `database/db.py:2811` — SELECT — tables `app_users`
  - `SELECT * FROM app_users WHERE username = ? LIMIT 1`
- `database/db.py:2845` — SELECT — tables `app_users`
  - `SELECT COUNT(*) AS count FROM app_users`
- `database/db.py:2854` — SELECT — tables `app_users`
  - `SELECT * FROM app_users ORDER BY username`
- `database/db.py:2866` — UPDATE — tables `app_users`
  - `UPDATE app_users SET role_name = ?, status = ? WHERE username = ?`
- `database/db.py:2882` — UPDATE — tables `app_users`
  - `UPDATE app_users SET password_hash = ? WHERE username = ?`
- `database/db.py:2987` — SELECT — tables `app_users`
  - `SELECT * FROM app_users WHERE username = ? LIMIT 1`
- `database/db.py:3255` — SELECT — tables `trust_minutes`
  - `SELECT COUNT(*) AS count FROM trust_minutes`
- `database/db.py:3291` — SELECT — tables `trust_minutes`
  - `SELECT minute_id FROM trust_minutes WHERE status IN ('Executed', 'Archived') AND (certificate_id IS NULL OR TRIM(certificate_id) = '') ORDER BY minute_id ASC`
- `database/db.py:3306` — UPDATE — tables `trust_minutes`
  - `UPDATE trust_minutes SET certificate_id = ? WHERE minute_id = ? AND (certificate_id IS NULL OR TRIM(certificate_id) = '')`
- `database/db.py:3327` — SELECT — tables `trust_minutes`
  - `SELECT * FROM trust_minutes WHERE certificate_id = ? LIMIT 1`
- `database/db.py:3343` — SELECT — tables `trust_minutes`
  - `SELECT minute_id, trust_id, title, status, executed_at, archived_at, locked, certificate_id, trustee_1_capacity, trustee_2_capacity, trustee_3_capacity FROM trust_minutes WHERE status IN ('Executed', 'Archived') ORDER BY executed_at DESC, minute_id DESC`
- `database/db.py:3439` — UPDATE — tables `trust_minutes`
  - `UPDATE trust_minutes SET trustee_1_name = ?, trustee_1_capacity = ?, trustee_1_signed_date = ?, trustee_1_signature_image = ?, trustee_2_name = ?, trustee_2_capacity = ?, trustee_2_signed_date = ?, trustee_2_signature_image = ?, trustee_3_name = ?, trustee_3_capacity = ?, trustee_3_signed_date = ?, trustee_3_signature_image = ?, certificate_id = ?, approved_at = ?, executed_at = ?, archived_at = ?, status = ?, locked = ? WHERE minute_id = ?`
- `services/services_continuity_assets.py:351` — SELECT — tables `documents`
  - `SELECT * FROM documents WHERE property_id = ? ORDER BY document_id ASC`
- `services/services_continuity_assets.py:368` — SELECT — tables `media_records`
  - `SELECT * FROM media_records WHERE related_entity_type = 'property' AND related_entity_id = ? ORDER BY created_at DESC`
- `services/services_continuity_assets.py:858` — SELECT — tables `archive_packet_finalization`
  - `SELECT COUNT(*) AS count FROM archive_packet_finalization`
- `services/services_continuity_assets.py:912` — SELECT — tables `archive_packet_finalization`
  - `SELECT * FROM archive_packet_finalization WHERE property_id = ? ORDER BY finalized_at DESC, id DESC`
- `services/services_intake.py:123` — SELECT — tables `intake_sessions`
  - `SELECT intake_id FROM intake_sessions ORDER BY id DESC LIMIT 1`
- `services/services_intake.py:1008` — UPDATE — tables `intake_sessions`
  - `UPDATE intake_sessions SET status = ?, updated_at = ? WHERE intake_id = ?`
- `services/services_intake.py:1054` — SELECT — tables `intake_sessions`
  - `SELECT intake_id, intake_lane, user_posture, default_depth, risk_posture, professional_review_recommended, automation_limits, next_screen, status, created_at, updated_at FROM intake_sessions WHERE intake_id = ?`
- `services/services_intake.py:1295` — UPDATE — tables `intake_sessions`
  - `UPDATE intake_sessions SET status = ?, updated_at = ? WHERE intake_id = ?`
- `services/services_intake.py:1611` — UPDATE — tables `intake_sessions`
  - `UPDATE intake_sessions SET status = ?, updated_at = ? WHERE intake_id = ?`
- `services/services_intake.py:1628` — SELECT — tables `intake_scores`
  - `SELECT s1.intake_id, s1.complexity_score, s1.complexity_level, s1.urgency_score, s1.urgency_level, s1.readiness_score, s1.readiness_level FROM intake_scores s1 INNER JOIN ( SELECT intake_id, MAX(id) AS max_id FROM intake_scores GROUP BY intake_id ) latest ON s1.id = latest.max_id`
- `services/services_intake.py:1710` — SELECT — tables `intake_answers`
  - `SELECT question_key, answer_key, answer_label FROM intake_answers WHERE intake_id = ? ORDER BY id ASC`
- `services/services_intake.py:1735` — SELECT — tables `intake_translations`
  - `SELECT source_key, system_category, system_meaning, module_trigger, document_request, next_session, risk_flag FROM intake_translations WHERE intake_id = ? ORDER BY id ASC`
- `services/services_intake.py:1765` — SELECT — tables `intake_scores`
  - `SELECT complexity_score, complexity_level, urgency_score, urgency_level, readiness_score, readiness_level, scoring_notes FROM intake_scores WHERE intake_id = ? ORDER BY id DESC LIMIT 1`
- `services/services_intake.py:1814` — SELECT — tables `intake_snapshots`
  - `SELECT snapshot_json FROM intake_snapshots WHERE intake_id = ? LIMIT 1`
- `services/services_intake.py:2095` — UPDATE — tables `intake_sessions`
  - `UPDATE intake_sessions SET updated_at = ? WHERE intake_id = ?`
- `services/services_intake.py:2121` — SELECT — tables `intake_review_notes`
  - `SELECT id, intake_id, note_type, priority, followup_status, note_body, created_at, updated_at, created_by FROM intake_review_notes WHERE intake_id = ? ORDER BY id DESC`
- `services/services_intake.py:2301` — UPDATE — tables `intake_sessions`
  - `UPDATE intake_sessions SET updated_at = ? WHERE intake_id = ?`
- `services/services_intake.py:2329` — SELECT — tables `intake_followup_tasks`
  - `SELECT id, intake_id, task_type, priority, status, title, description, source, created_at, updated_at, created_by, completed_at, completed_by FROM intake_followup_tasks WHERE intake_id = ? ORDER BY CASE status WHEN 'open' THEN 1 WHEN 'pending_client' THEN 2 WHEN 'pending_staff' THEN 3 WHEN 'pending_professional' THEN 4 WHEN 'deferred' THEN 5 WHEN 'completed' THEN 6 ELSE 7 END, CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'normal' THEN 3 WHEN 'low' THEN 4 ELSE 5 END, id ASC`
- `services/services_intake.py:2417` — SELECT — tables `intake_followup_tasks`
  - `SELECT COUNT(*) FROM intake_followup_tasks WHERE intake_id = ? AND title = ?`
- `services/services_intake.py:2513` — UPDATE — tables `intake_followup_tasks`
  - `UPDATE intake_followup_tasks SET status = ?, updated_at = ?, completed_at = ?, completed_by = ? WHERE id = ?`
- `services/services_intake.py:2982` — SELECT — tables `intake_export_logs`
  - `SELECT export_type, export_status, file_path, message, created_at, created_by FROM intake_export_logs WHERE intake_id = ? ORDER BY id DESC LIMIT 25`
- `services/services_intake.py:3107` — SELECT — tables `intake_export_logs`
  - `SELECT COALESCE(MAX(version_number), 0) FROM intake_export_logs WHERE intake_id = ? AND export_type = ? AND packet_type = ? AND export_status IN ('success', 'failed', 'error')`
- `services/services_intake.py:3221` — SELECT — tables `intake_export_logs`
  - `SELECT export_type, export_status, file_path, message, created_at, created_by, version_number, packet_type FROM intake_export_logs WHERE intake_id = ? ORDER BY id DESC LIMIT 100`
- `services/services_intake.py:3980` — SELECT — tables `intake_document_recommendations`
  - `SELECT id, status FROM intake_document_recommendations WHERE intake_id = ? AND workflow_key = ? LIMIT 1`
- `services/services_intake.py:3999` — UPDATE — tables `intake_document_recommendations`
  - `UPDATE intake_document_recommendations SET title = ?, workflow_type = ?, priority = ?, confidence = ?, reason = ?, source = ?, status = ?, updated_at = ?, created_by = ? WHERE id = ?`
- `services/services_intake.py:4056` — SELECT — tables `intake_document_recommendations`
  - `SELECT workflow_key, title, workflow_type, priority, confidence, reason, source, status, created_at, updated_at, created_by FROM intake_document_recommendations WHERE intake_id = ? ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'normal' THEN 3 WHEN 'low' THEN 4 ELSE 5 END, confidence DESC, id ASC`
- `services/services_intake.py:4451` — UPDATE — tables `intake_document_recommendations`
  - `UPDATE intake_document_recommendations SET status = ?, updated_at = ?, created_by = ? WHERE intake_id = ? AND workflow_key = ?`
- `services/services_intake.py:4473` — SELECT — tables `intake_document_recommendations`
  - `SELECT workflow_key, title, workflow_type, priority, confidence, reason, source, status, created_at, updated_at, created_by FROM intake_document_recommendations WHERE intake_id = ? AND workflow_key = ? LIMIT 1`
- `services/services_intake.py:5099` — DELETE — tables `intake_workflow_bridge_answers`
  - `DELETE FROM intake_workflow_bridge_answers WHERE intake_id = ? AND workflow_key = ?`
- `services/services_intake.py:5143` — UPDATE — tables `intake_document_recommendations`
  - `UPDATE intake_document_recommendations SET status = ?, updated_at = ?, created_by = ? WHERE intake_id = ? AND workflow_key = ?`
- `services/services_intake.py:5168` — SELECT — tables `intake_workflow_bridge_answers`
  - `SELECT question_key, answer_key, answer_label, created_at, updated_at, created_by FROM intake_workflow_bridge_answers WHERE intake_id = ? AND workflow_key = ? ORDER BY id ASC`
- `services/services_intake.py:5535` — SELECT — tables `intake_draft_readiness_ledger`
  - `SELECT intake_id, workflow_key, draft_packet_type, readiness, open_issue_count, open_task_count, completed_task_count, document_count, drafting_question_count, status, created_at, updated_at, updated_by, notes FROM intake_draft_readiness_ledger WHERE intake_id = ? ORDER BY updated_at DESC`
- `services/services_intake.py:5545` — SELECT — tables `intake_draft_readiness_ledger`
  - `SELECT intake_id, workflow_key, draft_packet_type, readiness, open_issue_count, open_task_count, completed_task_count, document_count, drafting_question_count, status, created_at, updated_at, updated_by, notes FROM intake_draft_readiness_ledger ORDER BY updated_at DESC LIMIT 200`
- `services/services_intake.py:6098` — DELETE — tables `intake_document_draft_answers`
  - `DELETE FROM intake_document_draft_answers WHERE intake_id = ? AND workflow_key = ? AND document_key = ?`
- `services/services_intake.py:6152` — SELECT — tables `intake_document_draft_answers`
  - `SELECT question_key, answer_key, answer_label, created_at, updated_at, created_by FROM intake_document_draft_answers WHERE intake_id = ? AND workflow_key = ? AND document_key = ? ORDER BY id ASC`
- `services/services_intake.py:6530` — SELECT — tables `intake_review_gate_ledger`
  - `SELECT intake_id, workflow_key, document_key, gate_name, gate_status, gate_reason, missing_answer_count, open_issue_count, open_task_count, document_status, created_at, updated_at, updated_by, notes FROM intake_review_gate_ledger WHERE intake_id = ? ORDER BY updated_at DESC`
- `services/services_intake.py:6540` — SELECT — tables `intake_review_gate_ledger`
  - `SELECT intake_id, workflow_key, document_key, gate_name, gate_status, gate_reason, missing_answer_count, open_issue_count, open_task_count, document_status, created_at, updated_at, updated_by, notes FROM intake_review_gate_ledger ORDER BY updated_at DESC LIMIT 200`
- `services/services_intake.py:6751` — SELECT — tables `intake_review_gate_ledger`
  - `SELECT intake_id, workflow_key, document_key, gate_name, gate_status, gate_reason, missing_answer_count, open_issue_count, open_task_count, document_status, created_at, updated_at, updated_by, notes FROM intake_review_gate_ledger WHERE intake_id = ? AND workflow_key = ? AND document_key = ? AND gate_name = ? LIMIT 1`
- `services/services_intake.py:6795` — SELECT — tables `intake_review_gate_actions`
  - `SELECT action_key, action_label, resulting_status, note, created_at, created_by FROM intake_review_gate_actions WHERE intake_id = ? AND workflow_key = ? AND document_key = ? AND gate_name = ? ORDER BY id DESC`
- `services/services_intake.py:6885` — UPDATE — tables `intake_review_gate_ledger`
  - `UPDATE intake_review_gate_ledger SET gate_status = ?, gate_reason = ?, updated_at = ?, updated_by = ?, notes = ? WHERE intake_id = ? AND workflow_key = ? AND document_key = ? AND gate_name = ?`
- `services/services_intake.py:7073` — SELECT — tables `intake_final_draft_prep_gate`
  - `SELECT admin_approved, approval_note FROM intake_final_draft_prep_gate WHERE intake_id = ? AND workflow_key = ? AND document_key = ? LIMIT 1`
- `services/services_intake.py:7151` — SELECT — tables `intake_final_draft_prep_gate`
  - `SELECT intake_id, workflow_key, document_key, gate_status, gate_reason, questionnaire_complete, open_issues_reviewed, open_tasks_reviewed, professional_review_recorded, required_documents_acknowledged, admin_approved, approval_note, created_at, updated_at, updated_by FROM intake_final_draft_prep_gate WHERE intake_id = ? AND workflow_key = ? AND document_key = ? LIMIT 1`
- `services/services_intake.py:7209` — UPDATE — tables `intake_final_draft_prep_gate`
  - `UPDATE intake_final_draft_prep_gate SET gate_status = ?, gate_reason = ?, admin_approved = 1, approval_note = ?, updated_at = ?, updated_by = ? WHERE intake_id = ? AND workflow_key = ? AND document_key = ?`
- `services/services_intake.py:7242` — SELECT — tables `intake_final_draft_prep_gate`
  - `SELECT intake_id, workflow_key, document_key, gate_status, gate_reason, questionnaire_complete, open_issues_reviewed, open_tasks_reviewed, professional_review_recorded, required_documents_acknowledged, admin_approved, approval_note, updated_at, updated_by FROM intake_final_draft_prep_gate WHERE intake_id = ? ORDER BY updated_at DESC`
- `services/services_intake.py:7253` — SELECT — tables `intake_final_draft_prep_gate`
  - `SELECT intake_id, workflow_key, document_key, gate_status, gate_reason, questionnaire_complete, open_issues_reviewed, open_tasks_reviewed, professional_review_recorded, required_documents_acknowledged, admin_approved, approval_note, updated_at, updated_by FROM intake_final_draft_prep_gate ORDER BY updated_at DESC LIMIT 200`
- `services/services_intake.py:7332` — SELECT — tables `intake_final_draft_gate_actions`
  - `SELECT action_key, action_label, note, created_at, created_by FROM intake_final_draft_gate_actions WHERE intake_id = ? AND workflow_key = ? AND document_key = ? ORDER BY id DESC`
- `services/services_intake.py:7499` — SELECT — tables `intake_final_draft_prep_gate`
  - `SELECT admin_approved, approval_note FROM intake_final_draft_prep_gate WHERE intake_id = ? AND workflow_key = ? AND document_key = ? LIMIT 1`
- `services/services_intake.py:7666` — UPDATE — tables `intake_final_draft_prep_gate`
  - `UPDATE intake_final_draft_prep_gate SET gate_status = ?, gate_reason = ?, admin_approved = 1, approval_note = ?, updated_at = ?, updated_by = ? WHERE intake_id = ? AND workflow_key = ? AND document_key = ?`
- `services/services_intake.py:7732` — SELECT — tables `intake_final_draft_admin_approvals`
  - `SELECT intake_id, workflow_key, document_key, approval_status, approval_note, gate_status_before, gate_status_after, created_at, created_by FROM intake_final_draft_admin_approvals`
- `services/services_intake.py:8067` — SELECT — tables `intake_final_draft_sections`
  - `SELECT id, section_order, section_heading, section_source, section_body, section_status, created_at, updated_at, updated_by FROM intake_final_draft_sections WHERE intake_id = ? AND workflow_key = ? AND document_key = ? ORDER BY section_order ASC`
- `services/services_intake.py:8101` — SELECT — tables `intake_final_draft_sections`
  - `SELECT id, section_order, section_heading, section_source, section_body, section_status, created_at, updated_at, updated_by FROM intake_final_draft_sections WHERE intake_id = ? AND workflow_key = ? AND document_key = ? AND id = ? LIMIT 1`
- `services/services_intake.py:8152` — UPDATE — tables `intake_final_draft_sections`
  - `UPDATE intake_final_draft_sections SET section_heading = ?, section_body = ?, section_status = ?, updated_at = ?, updated_by = ? WHERE intake_id = ? AND workflow_key = ? AND document_key = ? AND id = ?`
- `services/services_intake.py:8445` — SELECT — tables `intake_final_draft_version_register`
  - `SELECT COUNT(*) FROM intake_final_draft_version_register WHERE intake_id = ? AND workflow_key = ? AND document_key = ?`
- `services/services_intake.py:8534` — SELECT — tables `intake_final_draft_version_register`
  - `SELECT intake_id, workflow_key, document_key, version_label, export_type, file_path, preview_status, ready_count, total_sections, preparation_classification, finality_status, created_at, created_by, notes FROM intake_final_draft_version_register`
- `services/services_intake.py:8720` — SELECT — tables `intake_final_draft_completion_gate`
  - `SELECT intake_id, workflow_key, document_key, gate_status, gate_reason, total_sections, ready_sections, not_ready_sections, latest_version_label, completion_note, completed_at, completed_by, created_at, updated_at, updated_by FROM intake_final_draft_completion_gate WHERE intake_id = ? AND workflow_key = ? AND document_key = ? LIMIT 1`
- `services/services_intake.py:8769` — SELECT — tables `intake_final_draft_completion_gate`
  - `SELECT gate_status, completion_note, completed_at, completed_by FROM intake_final_draft_completion_gate WHERE intake_id = ? AND workflow_key = ? AND document_key = ? LIMIT 1`
- `services/services_intake.py:8845` — SELECT — tables `intake_final_draft_completion_actions`
  - `SELECT action_status, note, created_at, created_by FROM intake_final_draft_completion_actions WHERE intake_id = ? AND workflow_key = ? AND document_key = ? ORDER BY id DESC`
- `services/services_intake.py:8893` — UPDATE — tables `intake_final_draft_completion_gate`
  - `UPDATE intake_final_draft_completion_gate SET gate_status = ?, gate_reason = ?, completion_note = ?, completed_at = ?, completed_by = ?, updated_at = ?, updated_by = ? WHERE intake_id = ? AND workflow_key = ? AND document_key = ?`
- `services/services_matters.py:467` — SELECT — tables `matter_relationships`
  - `SELECT relationship_id FROM matter_relationships ORDER BY id DESC LIMIT 1`
- `package_export/database/db.py:165` — SELECT — tables `trusts`
  - `SELECT COUNT(*) AS count FROM trusts`
- `package_export/database/db.py:198` — SELECT — tables `trusts`
  - `SELECT * FROM trusts ORDER BY trust_id`
- `package_export/database/db.py:206` — SELECT — tables `trusts`
  - `SELECT * FROM trusts WHERE trust_id = ?`
- `package_export/database/db.py:216` — UPDATE — tables `trusts`
  - `UPDATE trusts SET {fields} WHERE trust_id = ?`
- `package_export/database/db.py:269` — SELECT — tables `properties, trusts`
  - `SELECT p.*, t.trust_name FROM properties p LEFT JOIN trusts t ON p.trust_id = t.trust_id ORDER BY p.property_id`
- `package_export/database/db.py:295` — SELECT — tables `accounts`
  - `SELECT COUNT(*) AS count FROM accounts`
- `package_export/database/db.py:319` — SELECT — tables `accounts`
  - `SELECT * FROM accounts WHERE trust_id = ? ORDER BY account_id`
- `package_export/database/db.py:327` — SELECT — tables `accounts`
  - `SELECT * FROM accounts WHERE property_id = ? ORDER BY account_id`
- `package_export/database/db.py:335` — SELECT — tables `documents`
  - `SELECT COUNT(*) AS count FROM documents`
- `package_export/database/db.py:360` — SELECT — tables `documents`
  - `SELECT * FROM documents WHERE trust_id = ? ORDER BY document_id`
- `package_export/database/db.py:368` — SELECT — tables `documents`
  - `SELECT * FROM documents WHERE property_id = ? ORDER BY document_id`
- `package_export/database/db.py:376` — SELECT — tables `ledger_entries`
  - `SELECT COUNT(*) AS count FROM ledger_entries`
- `package_export/database/db.py:403` — SELECT — tables `ledger_entries`
  - `SELECT * FROM ledger_entries WHERE trust_id = ? ORDER BY entry_id`
- `package_export/database/db.py:411` — SELECT — tables `ledger_entries`
  - `SELECT * FROM ledger_entries WHERE property_id = ? ORDER BY entry_id`
- `package_export/database/db.py:768` — SELECT — tables `distributions`
  - `SELECT COUNT(*) AS count FROM distributions`
- `package_export/database/db.py:844` — UPDATE — tables `distributions`
  - `UPDATE distributions SET {fields} WHERE distribution_id = ?`
- `package_export/database/db.py:852` — SELECT — tables `distributions`
  - `SELECT * FROM distributions WHERE distribution_id = ?`
- `package_export/database/db.py:862` — SELECT — tables `beneficiaries, distributions`
  - `SELECT d.*, b.full_name AS beneficiary_name, b.tax_id AS beneficiary_tax_id FROM distributions d LEFT JOIN beneficiaries b ON d.beneficiary_id = b.beneficiary_id WHERE d.trust_id = ? AND d.tax_year = ? ORDER BY d.distribution_date DESC, d.distribution_id DESC`
- `package_export/database/db.py:870` — SELECT — tables `beneficiaries, distributions`
  - `SELECT d.*, b.full_name AS beneficiary_name, b.tax_id AS beneficiary_tax_id FROM distributions d LEFT JOIN beneficiaries b ON d.beneficiary_id = b.beneficiary_id WHERE d.trust_id = ? ORDER BY d.distribution_date DESC, d.distribution_id DESC`
- `package_export/database/db.py:970` — SELECT — tables `beneficiaries, distributions`
  - `SELECT d.*, b.full_name AS beneficiary_name, b.tax_id AS beneficiary_tax_id FROM distributions d LEFT JOIN beneficiaries b ON d.beneficiary_id = b.beneficiary_id WHERE d.distribution_id = ? AND d.trust_id = ?`
- `package_export/database/db.py:1033` — SELECT — tables `ledger_entries`
  - `SELECT * FROM ledger_entries WHERE trust_id = ? ORDER BY entry_date DESC, entry_id DESC`
- `package_export/database/db.py:1123` — SELECT — tables `ledger_entries`
  - `SELECT * FROM ledger_entries WHERE trust_id = ? ORDER BY entry_date DESC, entry_id DESC`

## High-Review Route Candidates

- `app.py:2979` — `create_trust_step2_grantor` — `"/create_trust_step2_grantor/<trust_id>", methods=["GET", "POST"]`
- `app.py:3001` — `create_trust_step2` — `"/create_trust_step2/<trust_id>", methods=["GET", "POST"]`
- `app.py:3021` — `create_trust_step3` — `"/create_trust_step3/<trust_id>", methods=["GET", "POST"]`
- `app.py:3041` — `create_trust_step4` — `"/create_trust_step4/<trust_id>", methods=["GET", "POST"]`
- `app.py:3061` — `create_trust_step5` — `"/create_trust_step5/<trust_id>", methods=["GET", "POST"]`
- `app.py:3081` — `create_trust_step6` — `"/create_trust_step6/<trust_id>", methods=["GET", "POST"]`
- `app.py:3095` — `create_trust_step7` — `"/create_trust_step7/<trust_id>"`
- `app.py:6244` — `k1_trust_view` — `"/k1/trust/<trust_id>"`
- `app.py:6278` — `k1_new_beneficiary` — `"/k1/trust/<trust_id>/beneficiary/new", methods=["GET", "POST"]`
- `app.py:6327` — `k1_new_distribution` — `"/k1/trust/<trust_id>/distribution/new", methods=["GET", "POST"]`
- `app.py:6387` — `k1_year_end_summary` — `"/k1/trust/<trust_id>/year_end_summary"`
- `app.py:6450` — `form1041_preview` — `"/form1041/preview/<trust_id>"`
- `app.py:6457` — `form1041_print` — `"/form1041/print/<trust_id>"`
- `app.py:7471` — `trust_minute_certificate_pdf` — `"/minutes/<minute_id>/certificate.pdf"`
- `app.py:7549` — `trust_minute_execution_packet_pdf` — `"/minutes/<minute_id>/packet.pdf"`
- `app.py:7696` — `trust_minute_execute` — `"/minutes/<minute_id>/execute", methods=["POST"]`
- `app.py:7818` — `trust_minute_detail` — `"/minutes/<minute_id>"`
- `app.py:8025` — `k1_edit_beneficiary` — `"/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/edit", methods=["GET", "POST"]`
- `app.py:8064` — `k1_toggle_beneficiary` — `"/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/toggle", methods=["POST"]`
- `app.py:8073` — `k1_edit_distribution` — `"/k1/trust/<trust_id>/distribution/<distribution_id>/edit", methods=["GET", "POST"]`
- `app.py:9456` — `k1_report_view` — `"/reports/k1/<trust_id>"`
- `app.py:9486` — `form1041_report_view` — `"/reports/1041/<trust_id>"`
- `app.py:9561` — `k1_report_print` — `"/reports/k1/<trust_id>/print"`
- `app.py:9593` — `form1041_report_print` — `"/reports/1041/<trust_id>/print"`
- `app.py:9896` — `trust_summary_pdf` — `"/reports/trust/<trust_id>/summary.pdf"`
- `app.py:9913` — `k1_readiness_pdf` — `"/reports/k1/trust/<trust_id>/<tax_year>.pdf"`
- `app.py:9946` — `ledger_report_pdf` — `"/reports/ledger/trust/<trust_id>.pdf"`
- `app.py:9956` — `form1041_report_pdf` — `"/reports/1041/trust/<trust_id>/<tax_year>.pdf"`
- `app.py:10344` — `video_trust_type` — `"/videos/trust-type/<trust_type>"`
- `app.py:10952` — `document_detail` — `"/documents/<document_id>"`
- `app.py:10969` — `workspace_documents` — `"/workspaces/<workspace_id>/documents"`
- `app.py:10978` — `workspace_document_generate` — `"/workspaces/<workspace_id>/documents/generate", methods=["GET", "POST"]`
- `app.py:11050` — `trust_post_create_review` — `"/trust/<trust_id>/post-create-review"`
- `app.py:11058` — `trust_formation_preview_hub` — `"/trust/<trust_id>/formation-preview-hub"`
- `app.py:11075` — `trust_successor_trustee_preview` — `"/trust/<trust_id>/successor-trustee-preview"`
- `app.py:11088` — `trust_successor_trustee_output_surface` — `"/trust/<trust_id>/successor-trustee-output-surface"`
- `app.py:11102` — `trust_successor_trustee_output_surface_pdf` — `"/trust/<trust_id>/successor-trustee-output-surface/pdf"`
- `app.py:11174` — `trust_general_assignment_preview` — `"/trust/<trust_id>/general-assignment-preview"`
- `app.py:11187` — `trust_general_assignment_output_surface` — `"/trust/<trust_id>/general-assignment-output-surface"`
- `app.py:11201` — `trust_general_assignment_output_surface_pdf` — `"/trust/<trust_id>/general-assignment-output-surface/pdf"`
- `app.py:11216` — `trust_organizational_minutes_preview` — `"/trust/<trust_id>/organizational-minutes-preview"`
- `app.py:11229` — `trust_organizational_minutes_output_surface` — `"/trust/<trust_id>/organizational-minutes-output-surface"`
- `app.py:11243` — `trust_organizational_minutes_output_surface_pdf` — `"/trust/<trust_id>/organizational-minutes-output-surface/pdf"`
- `app.py:11258` — `trust_trustee_acceptance_preview` — `"/trust/<trust_id>/trustee-acceptance-preview"`
- `app.py:11271` — `trust_trustee_acceptance_output_surface` — `"/trust/<trust_id>/trustee-acceptance-output-surface"`
- `app.py:11285` — `trust_trustee_acceptance_output_surface_pdf` — `"/trust/<trust_id>/trustee-acceptance-output-surface/pdf"`
- `app.py:11300` — `trust_articles_preview` — `"/trust/<trust_id>/articles-preview"`
- `app.py:11313` — `trust_declaration_output_surface` — `"/trust/<trust_id>/declaration-output-surface"`
- `app.py:11326` — `trust_declaration_output_surface_pdf` — `"/trust/<trust_id>/declaration-output-surface/pdf"`
- `app.py:11341` — `trust_certificate_of_trust_output_surface` — `"/trust/<trust_id>/certificate-of-trust-output-surface"`
- `app.py:11354` — `trust_certificate_of_trust_output_surface_pdf` — `"/trust/<trust_id>/certificate-of-trust-output-surface/pdf"`
- `app.py:11369` — `trust_articles_output_surface` — `"/trust/<trust_id>/articles-output-surface"`
- `app.py:11384` — `trust_articles_output_surface_pdf` — `"/trust/<trust_id>/articles-output-surface/pdf"`
- `app.py:15054` — `trust_dynamic_declaration` — `"/trust/<trust_id>/dynamic-declaration"`
- `app.py:15151` — `trust_dynamic_declaration_pdf` — `"/trust/<trust_id>/dynamic-declaration/pdf"`
- `app.py:15178` — `trust_article_assignments` — `"/trust/<trust_id>/article-assignments"`
- `app.py:15209` — `trust_article_assignment_add` — `"/trust/<trust_id>/article-assignments/add", methods=["POST"]`
- `app.py:15272` — `intake_universal_profile` — `"/intake/<intake_id>/universal-profile", methods=["GET", "POST"]`
- `app.py:17857` — `intake_saved_snapshot` — `"/intake/<intake_id>/snapshot"`
- `app.py:17890` — `intake_resume` — `"/intake/<intake_id>/resume"`
- `app.py:17904` — `intake_export_prep` — `"/intake/<intake_id>/export-prep"`
- `app.py:17920` — `intake_add_review_note` — `"/intake/<intake_id>/notes/add", methods=["POST"]`
- `app.py:17938` — `intake_add_followup_task` — `"/intake/<intake_id>/tasks/add", methods=["POST"]`
- `app.py:17958` — `intake_update_followup_task_status` — `"/intake/<intake_id>/tasks/<int:task_id>/status", methods=["POST"]`
- `app.py:17973` — `intake_followup_packet` — `"/intake/<intake_id>/packet"`
- `app.py:17990` — `intake_followup_packet_docx` — `"/intake/<intake_id>/packet/docx"`
- `app.py:18004` — `intake_followup_packet_pdf` — `"/intake/<intake_id>/packet/pdf"`
- `app.py:18033` — `intake_export_history_detail` — `"/intake/<intake_id>/exports"`
- `app.py:18059` — `intake_document_recommendations` — `"/intake/<intake_id>/recommendations"`
- `app.py:18084` — `intake_update_recommendation_status` — `"/intake/<intake_id>/recommendations/<workflow_key>/status", methods=["POST"]`
- `app.py:18100` — `intake_workflow_launch_prep` — `"/intake/<intake_id>/recommendations/<workflow_key>/launch-prep"`
- `app.py:18121` — `intake_workflow_bridge` — `"/intake/<intake_id>/recommendations/<workflow_key>/bridge", methods=["GET", "POST"]`
- `app.py:18203` — `intake_workflow_bridge_summary` — `"/intake/<intake_id>/recommendations/<workflow_key>/bridge-summary"`
- `app.py:18217` — `intake_workflow_draft_packet` — `"/intake/<intake_id>/recommendations/<workflow_key>/draft-packet"`
- `app.py:18238` — `intake_workflow_draft_packet_docx` — `"/intake/<intake_id>/recommendations/<workflow_key>/draft-packet/docx"`
- `app.py:18263` — `intake_draft_readiness_ledger_detail` — `"/intake/<intake_id>/draft-readiness"`
- `app.py:18273` — `intake_document_draft_choose` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft"`
- `app.py:18291` — `intake_document_draft_questionnaire` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>", methods=["GET", "POST"]`
- `app.py:18330` — `intake_document_draft_preview` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/preview"`
- `app.py:18344` — `intake_nonfinal_draft_document` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/nonfinal"`
- `app.py:18371` — `intake_nonfinal_draft_docx` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/nonfinal/docx"`
- `app.py:18402` — `intake_review_gate_ledger_detail` — `"/intake/<intake_id>/review-gates"`
- `app.py:18412` — `intake_review_gate_detail` — `"/intake/<intake_id>/review-gates/<workflow_key>/<document_key>"`
- `app.py:18430` — `intake_review_gate_resolve` — `"/intake/<intake_id>/review-gates/<workflow_key>/<document_key>/resolve", methods=["POST"]`
- `app.py:18452` — `intake_final_draft_gate_ledger_detail` — `"/intake/<intake_id>/final-draft-gate"`
- `app.py:18474` — `intake_final_draft_gate_detail` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate"`
- `app.py:18495` — `intake_final_draft_gate_approve` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate/approve", methods=["POST"]`
- `app.py:18516` — `intake_final_draft_gate_resolution` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate/resolve", methods=["GET", "POST"]`
- `app.py:18561` — `intake_final_draft_admin_approval` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/admin-approval", methods=["GET", "POST"]`
- `app.py:18604` — `intake_final_draft_admin_approval_ledger_detail` — `"/intake/<intake_id>/final-draft-approvals"`
- `app.py:18615` — `intake_final_draft_workspace` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-workspace"`
- `app.py:18629` — `intake_final_draft_section_editor` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-section-editor"`
- `app.py:18640` — `intake_final_draft_section_edit` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-section-editor/<int:section_id>", methods=["GET", "POST"]`
- `app.py:18682` — `intake_final_draft_preview` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-preview"`
- `app.py:18692` — `intake_final_draft_preview_docx` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-preview/docx"`
- `app.py:18722` — `intake_final_draft_version_register_intake` — `"/intake/<intake_id>/final-draft-version-register"`
- `app.py:18731` — `intake_final_draft_version_register_detail` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-version-register"`
- `app.py:18744` — `intake_final_draft_completion_gate` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-completion-gate", methods=["GET", "POST"]`
- `app.py:18777` — `intake_trust_instrument_menu` — `"/intake/<intake_id>/trust-instruments"`
- `app.py:18787` — `intake_instrument_draft_packet` — `"/intake/<intake_id>/recommendations/<workflow_key>/instrument-draft-packet"`
- `app.py:19062` — `matter_governance_state` — `"/matters/<matter_id>/governance", methods=["POST"]`
- `app.py:19090` — `matter_risk_update` — `"/matters/<matter_id>/risk", methods=["POST"]`
- `app.py:19114` — `matter_detail` — `"/matters/<matter_id>"`
- `app.py:19127` — `matter_relationship_detail` — `"/matters/<matter_id>/relationships/<relationship_id>"`
- `app.py:19207` — `matter_relationship_clearance` — `"/matters/<matter_id>/relationships/" "<relationship_id>/clearance", methods=["POST"]`
- `app.py:19249` — `matter_relationship_relink` — `"/matters/<matter_id>/relationships/" "<relationship_id>/relink", methods=["POST"]`
- `app.py:19296` — `matter_relationship_validate_link` — `"/matters/<matter_id>/relationships/" "<relationship_id>/validate-link", methods=["POST"]`
- `app.py:19335` — `matter_relationship_verification_update` — `"/matters/<matter_id>/relationships/" "<relationship_id>/verification", methods=["POST"]`
- `app.py:19384` — `matter_relationship_status_update` — `"/matters/<matter_id>/relationships/<relationship_id>/status", methods=["POST"]`
- `app.py:19418` — `new_matter_relationship` — `"/matters/<matter_id>/relationships/new", methods=["GET", "POST"]`
- `app.py:19458` — `new_matter_event` — `"/matters/<matter_id>/events/new", methods=["GET", "POST"]`
- `package_export/app.py:215` — `create_trust_step2` — `"/create_trust_step2/<trust_id>", methods=["GET", "POST"]`
- `package_export/app.py:231` — `create_trust_step3` — `"/create_trust_step3/<trust_id>", methods=["GET", "POST"]`
- `package_export/app.py:247` — `create_trust_step4` — `"/create_trust_step4/<trust_id>", methods=["GET", "POST"]`
- `package_export/app.py:263` — `create_trust_step5` — `"/create_trust_step5/<trust_id>", methods=["GET", "POST"]`
- `package_export/app.py:279` — `create_trust_step6` — `"/create_trust_step6/<trust_id>", methods=["GET", "POST"]`
- `package_export/app.py:289` — `create_trust_step7` — `"/create_trust_step7/<trust_id>"`
- `package_export/app.py:407` — `trust_detail` — `"/trust/<trust_id>"`
- `package_export/app.py:452` — `k1_trust_view` — `"/k1/trust/<trust_id>"`
- `package_export/app.py:469` — `k1_new_beneficiary` — `"/k1/trust/<trust_id>/beneficiary/new", methods=["GET", "POST"]`
- `package_export/app.py:489` — `k1_new_distribution` — `"/k1/trust/<trust_id>/distribution/new", methods=["GET", "POST"]`
- `package_export/app.py:511` — `k1_year_end_summary` — `"/k1/trust/<trust_id>/year_end_summary"`
- `package_export/app.py:542` — `form1041_preview` — `"/form1041/preview/<trust_id>"`
- `package_export/app.py:549` — `form1041_print` — `"/form1041/print/<trust_id>"`
- `package_export/app.py:665` — `k1_edit_beneficiary` — `"/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/edit", methods=["GET", "POST"]`
- `package_export/app.py:687` — `k1_toggle_beneficiary` — `"/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/toggle", methods=["POST"]`
- `package_export/app.py:693` — `k1_edit_distribution` — `"/k1/trust/<trust_id>/distribution/<distribution_id>/edit", methods=["GET", "POST"]`
- `package_export/app.py:722` — `k1_export_csv` — `"/k1/trust/<trust_id>/export.csv"`

## Governing Rule

No database or code correction should be made until each high-review finding is traced through its route, helper, service, parent relation, and active-firm access control.
