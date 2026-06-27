# MIA-0A — Matter and Intake Implementation Baseline

**Status:** BASELINE_COMPLETE_BLOCKERS_IDENTIFIED
**Created:** 2026-06-14T19:44:25.934399

## Repository

- Branch: `strapback/stable-661bb66`
- HEAD: `1cf6497598d9d294bc0453847b896316f863c241`
- Last commit:

```text
1cf6497598d9d294bc0453847b896316f863c241
2026-06-13T14:41:22-04:00
Complete IC-1 relationship audit summary and closeout gate
```

## Database Safety

- Database: `C:\Users\LunaMishoe\Desktop\trustee-app-clean\trustee_app.db`
- Integrity: `ok`
- SHA-256 before: `eb2b318824be70aa2e37a5a9d7c8c5c1767a7bb7cbf9922f459128751cbf26f8`
- SHA-256 after: `eb2b318824be70aa2e37a5a9d7c8c5c1767a7bb7cbf9922f459128751cbf26f8`
- Live database unchanged: `True`

## Route Summary

- Total relevant routes: **69**
- INTAKE: **62**
- MATTER: **7**

## Relevant Routes

- `GET,POST /intake` → `intake_start` at `app.py:15248` [INTAKE]
- `GET,POST /intake/start` → `intake_start` at `app.py:15248` [INTAKE]
- `GET,POST /intake/<intake_id>/universal-profile` → `intake_universal_profile` at `app.py:15273` [INTAKE]
- `GET,POST /intake/assets/<intake_id>` → `asset_intake` at `app.py:15334` [INTAKE]
- `GET,POST /intake/documents/<intake_id>` → `document_intake` at `app.py:15443` [INTAKE]
- `GET /intake/readiness/<intake_id>` → `intake_readiness_review` at `app.py:15545` [INTAKE]
- `GET,POST /intake/deep-review/<intake_id>` → `intake_deep_review` at `app.py:15579` [INTAKE]
- `GET,POST /intake/drafting-prep/<intake_id>` → `intake_drafting_prep` at `app.py:15671` [INTAKE]
- `GET,POST /draft-launch/<intake_id>` → `launch_draft_session` at `app.py:15766` [INTAKE]
- `GET /lifecycle-ledger/<intake_id>` → `lifecycle_master_ledger` at `app.py:17828` [INTAKE]
- `GET /intake/dashboard` → `intake_dashboard` at `app.py:17850` [INTAKE]
- `GET /intake/<intake_id>/snapshot` → `intake_saved_snapshot` at `app.py:17858` [INTAKE]
- `GET /intake/<intake_id>/resume` → `intake_resume` at `app.py:17891` [INTAKE]
- `GET /intake/<intake_id>/export-prep` → `intake_export_prep` at `app.py:17905` [INTAKE]
- `POST /intake/<intake_id>/notes/add` → `intake_add_review_note` at `app.py:17921` [INTAKE]
- `POST /intake/<intake_id>/tasks/add` → `intake_add_followup_task` at `app.py:17939` [INTAKE]
- `POST /intake/<intake_id>/tasks/<int:task_id>/status` → `intake_update_followup_task_status` at `app.py:17959` [INTAKE]
- `GET /intake/<intake_id>/packet` → `intake_followup_packet` at `app.py:17974` [INTAKE]
- `GET /intake/<intake_id>/packet/docx` → `intake_followup_packet_docx` at `app.py:17991` [INTAKE]
- `GET /intake/<intake_id>/packet/pdf` → `intake_followup_packet_pdf` at `app.py:18005` [INTAKE]
- `GET /intake/exports` → `intake_export_history` at `app.py:18022` [INTAKE]
- `GET /intake/<intake_id>/exports` → `intake_export_history_detail` at `app.py:18034` [INTAKE]
- `GET /intake/modules` → `intake_module_ledger` at `app.py:18045` [INTAKE]
- `GET /intake/<intake_id>/recommendations` → `intake_document_recommendations` at `app.py:18060` [INTAKE]
- `POST /intake/<intake_id>/recommendations/<workflow_key>/status` → `intake_update_recommendation_status` at `app.py:18085` [INTAKE]
- `GET /intake/<intake_id>/recommendations/<workflow_key>/launch-prep` → `intake_workflow_launch_prep` at `app.py:18101` [INTAKE]
- `GET,POST /intake/<intake_id>/recommendations/<workflow_key>/bridge` → `intake_workflow_bridge` at `app.py:18122` [INTAKE]
- `GET /intake/<intake_id>/recommendations/<workflow_key>/bridge-summary` → `intake_workflow_bridge_summary` at `app.py:18204` [INTAKE]
- `GET /intake/<intake_id>/recommendations/<workflow_key>/draft-packet` → `intake_workflow_draft_packet` at `app.py:18218` [INTAKE]
- `GET /intake/<intake_id>/recommendations/<workflow_key>/draft-packet/docx` → `intake_workflow_draft_packet_docx` at `app.py:18239` [INTAKE]
- `GET /intake/draft-readiness` → `intake_draft_readiness_ledger` at `app.py:18254` [INTAKE]
- `GET /intake/<intake_id>/draft-readiness` → `intake_draft_readiness_ledger_detail` at `app.py:18264` [INTAKE]
- `GET /intake/<intake_id>/recommendations/<workflow_key>/document-draft` → `intake_document_draft_choose` at `app.py:18274` [INTAKE]
- `GET,POST /intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>` → `intake_document_draft_questionnaire` at `app.py:18292` [INTAKE]
- `GET /intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/preview` → `intake_document_draft_preview` at `app.py:18331` [INTAKE]
- `GET /intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/nonfinal` → `intake_nonfinal_draft_document` at `app.py:18345` [INTAKE]
- `GET /intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/nonfinal/docx` → `intake_nonfinal_draft_docx` at `app.py:18372` [INTAKE]
- `GET /intake/review-gates` → `intake_review_gate_ledger` at `app.py:18393` [INTAKE]
- `GET /intake/<intake_id>/review-gates` → `intake_review_gate_ledger_detail` at `app.py:18403` [INTAKE]
- `GET /intake/<intake_id>/review-gates/<workflow_key>/<document_key>` → `intake_review_gate_detail` at `app.py:18413` [INTAKE]
- `POST /intake/<intake_id>/review-gates/<workflow_key>/<document_key>/resolve` → `intake_review_gate_resolve` at `app.py:18431` [INTAKE]
- `GET /intake/<intake_id>/final-draft-gate` → `intake_final_draft_gate_ledger_detail` at `app.py:18453` [INTAKE]
- `GET /intake/final-draft-gate` → `intake_final_draft_gate_ledger` at `app.py:18464` [INTAKE]
- `GET /intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate` → `intake_final_draft_gate_detail` at `app.py:18475` [INTAKE]
- `POST /intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate/approve` → `intake_final_draft_gate_approve` at `app.py:18496` [INTAKE]
- `GET,POST /intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate/resolve` → `intake_final_draft_gate_resolution` at `app.py:18517` [INTAKE]
- `GET,POST /intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/admin-approval` → `intake_final_draft_admin_approval` at `app.py:18562` [INTAKE]
- `GET /intake/final-draft-approvals` → `intake_final_draft_admin_approval_ledger` at `app.py:18595` [INTAKE]
- `GET /intake/<intake_id>/final-draft-approvals` → `intake_final_draft_admin_approval_ledger_detail` at `app.py:18605` [INTAKE]
- `GET /intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-workspace` → `intake_final_draft_workspace` at `app.py:18616` [INTAKE]
- `GET /intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-section-editor` → `intake_final_draft_section_editor` at `app.py:18630` [INTAKE]
- `GET,POST /intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-section-editor/<int:section_id>` → `intake_final_draft_section_edit` at `app.py:18641` [INTAKE]
- `GET /intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-preview` → `intake_final_draft_preview` at `app.py:18683` [INTAKE]
- `GET /intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-preview/docx` → `intake_final_draft_preview_docx` at `app.py:18693` [INTAKE]
- `GET /intake/final-draft-version-register` → `intake_final_draft_version_register_all` at `app.py:18714` [INTAKE]
- `GET /intake/<intake_id>/final-draft-version-register` → `intake_final_draft_version_register_intake` at `app.py:18723` [INTAKE]
- `GET /intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-version-register` → `intake_final_draft_version_register_detail` at `app.py:18732` [INTAKE]
- `GET,POST /intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-completion-gate` → `intake_final_draft_completion_gate` at `app.py:18745` [INTAKE]
- `GET /intake/<intake_id>/trust-instruments` → `intake_trust_instrument_menu` at `app.py:18778` [INTAKE]
- `GET /intake/<intake_id>/recommendations/<workflow_key>/instrument-draft-packet` → `intake_instrument_draft_packet` at `app.py:18788` [INTAKE]
- `GET,POST /intake/identity` → `identity_intake` at `app.py:18804` [INTAKE]
- `GET /intake/identity/<intake_id>` → `identity_intake_summary` at `app.py:18864` [INTAKE]
- `GET /matters` → `matters_dashboard` at `app.py:19045` [MATTER]
- `GET,POST /matters/new` → `new_matter` at `app.py:19052` [MATTER]
- `POST /matters/<matter_id>/governance` → `matter_governance_state` at `app.py:19063` [MATTER]
- `POST /matters/<matter_id>/risk` → `matter_risk_update` at `app.py:19091` [MATTER]
- `GET /matters/<matter_id>` → `matter_detail` at `app.py:19115` [MATTER]
- `GET,POST /matters/<matter_id>/relationships/new` → `new_matter_relationship` at `app.py:19419` [MATTER]
- `GET,POST /matters/<matter_id>/events/new` → `new_matter_event` at `app.py:19459` [MATTER]

## Database Tables

- Total database tables: **88**
- Matter/Intake relevant tables: **45**

### `asset_intake`

- Rows: **1**
- Linkage columns: `intake_id, firm_id, risk_level, created_at`
- Firm distribution: `{'FIRM-002': 1}`

### `controlled_docx_exports`

- Rows: **1**
- Linkage columns: `workspace_id, intake_id, firm_id, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 1}`

### `controlled_export_prep`

- Rows: **1**
- Linkage columns: `workspace_id, intake_id, firm_id, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 1}`

### `controlled_pdf_exports`

- Rows: **1**
- Linkage columns: `workspace_id, intake_id, firm_id, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 1}`

### `document_intake`

- Rows: **1**
- Linkage columns: `document_id, intake_id, firm_id, created_at`
- Firm distribution: `{'FIRM-002': 1}`

### `docx_verification_gate`

- Rows: **1**
- Linkage columns: `workspace_id, intake_id, firm_id, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 1}`

### `draft_sessions`

- Rows: **2**
- Linkage columns: `intake_id, firm_id, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 2}`

### `draft_variable_bindings`

- Rows: **8**
- Linkage columns: `workspace_id, intake_id, firm_id, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 8}`

### `dynamic_draft_previews`

- Rows: **1**
- Linkage columns: `workspace_id, intake_id, firm_id, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 1}`

### `execution_event_log`

- Rows: **1**
- Linkage columns: `workspace_id, intake_id, firm_id, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 1}`

### `execution_packet_prep`

- Rows: **1**
- Linkage columns: `workspace_id, intake_id, firm_id, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 1}`

### `final_record_archive`

- Rows: **1**
- Linkage columns: `workspace_id, intake_id, firm_id, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 1}`

### `guided_draft_workspace`

- Rows: **1**
- Linkage columns: `workspace_id, intake_id, firm_id, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 1}`

### `identity_intake`

- Rows: **2**
- Linkage columns: `intake_id, firm_id, intake_type, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 2}`

### `intake_answers`

- Rows: **50**
- Linkage columns: `intake_id, firm_id, created_at, created_by`
- Firm distribution: `{'FIRM-002': 50}`

### `intake_deep_review`

- Rows: **1**
- Linkage columns: `intake_id, firm_id, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 1}`

### `intake_document_draft_answers`

- Rows: **3**
- Linkage columns: `intake_id, firm_id, created_at, updated_at, created_by`
- Firm distribution: `{'FIRM-002': 3}`

### `intake_document_recommendations`

- Rows: **15**
- Linkage columns: `intake_id, firm_id, priority, status, created_at, updated_at, created_by`
- Firm distribution: `{'FIRM-001': 8, 'FIRM-002': 7}`

### `intake_draft_readiness_ledger`

- Rows: **1**
- Linkage columns: `intake_id, firm_id, status, created_at, updated_at, updated_by`
- Firm distribution: `{'FIRM-001': 1}`

### `intake_drafting_prep_gate`

- Rows: **3**
- Linkage columns: `intake_id, firm_id, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 3}`

### `intake_export_logs`

- Rows: **10**
- Linkage columns: `intake_id, firm_id, created_at, created_by`
- Firm distribution: `{'FIRM-001': 7, 'FIRM-002': 3}`

### `intake_final_draft_admin_approvals`

- Rows: **1**
- Linkage columns: `intake_id, firm_id, created_at, created_by`
- Firm distribution: `{'FIRM-001': 1}`

### `intake_final_draft_completion_actions`

- Rows: **0**
- Linkage columns: `intake_id, firm_id, created_at, created_by`
- Firm distribution: `{}`

### `intake_final_draft_completion_gate`

- Rows: **1**
- Linkage columns: `intake_id, firm_id, created_at, updated_at, updated_by`
- Firm distribution: `{'FIRM-001': 1}`

### `intake_final_draft_gate_actions`

- Rows: **6**
- Linkage columns: `intake_id, firm_id, created_at, created_by`
- Firm distribution: `{'FIRM-001': 1, 'FIRM-002': 5}`

### `intake_final_draft_prep_gate`

- Rows: **1**
- Linkage columns: `intake_id, firm_id, created_at, updated_at, updated_by`
- Firm distribution: `{'FIRM-001': 1}`

### `intake_final_draft_sections`

- Rows: **7**
- Linkage columns: `intake_id, firm_id, created_at, updated_at, updated_by`
- Firm distribution: `{'FIRM-001': 7}`

### `intake_final_draft_version_register`

- Rows: **1**
- Linkage columns: `intake_id, firm_id, created_at, created_by`
- Firm distribution: `{'FIRM-001': 1}`

### `intake_followup_tasks`

- Rows: **28**
- Linkage columns: `intake_id, firm_id, priority, status, created_at, updated_at, created_by`
- Firm distribution: `{'FIRM-002': 28}`

### `intake_lane_events`

- Rows: **5**
- Linkage columns: `intake_id, firm_id, created_at, created_by`
- Firm distribution: `{'FIRM-002': 5}`

### `intake_module_ledger`

- Rows: **16**
- Linkage columns: `status, updated_at, updated_by`
- Firm distribution: `None`

### `intake_orchestration`

- Rows: **1**
- Linkage columns: `intake_id, firm_id, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 1}`

### `intake_review_gate_actions`

- Rows: **2**
- Linkage columns: `intake_id, firm_id, created_at, created_by`
- Firm distribution: `{'FIRM-001': 1, 'FIRM-002': 1}`

### `intake_review_gate_ledger`

- Rows: **1**
- Linkage columns: `intake_id, firm_id, created_at, updated_at, updated_by`
- Firm distribution: `{'FIRM-001': 1}`

### `intake_review_notes`

- Rows: **1**
- Linkage columns: `intake_id, firm_id, priority, created_at, updated_at, created_by`
- Firm distribution: `{'FIRM-002': 1}`

### `intake_scores`

- Rows: **4**
- Linkage columns: `intake_id, firm_id, created_at, updated_at, created_by`
- Firm distribution: `{'FIRM-002': 4}`

### `intake_sessions`

- Rows: **5**
- Linkage columns: `intake_id, firm_id, intake_lane, status, created_at, updated_at, created_by`
- Firm distribution: `{'FIRM-002': 5}`

### `intake_snapshots`

- Rows: **1**
- Linkage columns: `intake_id, firm_id, created_at, updated_at, created_by`
- Firm distribution: `{'FIRM-002': 1}`

### `intake_translations`

- Rows: **97**
- Linkage columns: `intake_id, firm_id, created_at, created_by`
- Firm distribution: `{'FIRM-002': 97}`

### `intake_workflow_bridge_answers`

- Rows: **3**
- Linkage columns: `intake_id, firm_id, created_at, updated_at, created_by`
- Firm distribution: `{'FIRM-002': 3}`

### `matter_events`

- Rows: **15**
- Linkage columns: `matter_id, firm_id, created_at`
- Firm distribution: `{'FIRM-002': 15}`

### `matter_relationships`

- Rows: **1**
- Linkage columns: `relationship_id, matter_id, firm_id, created_by, status, created_at, updated_at, verified_by`
- Firm distribution: `{'FIRM-002': 1}`

### `matters`

- Rows: **1**
- Linkage columns: `matter_id, firm_id, matter_type, status, priority, governance_state, risk_level, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 1}`

### `pdf_execution_approval_gate`

- Rows: **3**
- Linkage columns: `workspace_id, intake_id, firm_id, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 3}`

### `section_review_gate`

- Rows: **1**
- Linkage columns: `workspace_id, intake_id, firm_id, created_at, updated_at`
- Firm distribution: `{'FIRM-002': 1}`

## Relevant Python Functions

- `app.py:15248` `intake_start()`
- `app.py:15273` `intake_universal_profile(intake_id)`
- `app.py:15334` `asset_intake(intake_id)`
- `app.py:15443` `document_intake(intake_id)`
- `app.py:15545` `intake_readiness_review(intake_id)`
- `app.py:15579` `intake_deep_review(intake_id)`
- `app.py:15671` `intake_drafting_prep(intake_id)`
- `app.py:17850` `intake_dashboard()`
- `app.py:17858` `intake_saved_snapshot(intake_id)`
- `app.py:17891` `intake_resume(intake_id)`
- `app.py:17905` `intake_export_prep(intake_id)`
- `app.py:17921` `intake_add_review_note(intake_id)`
- `app.py:17939` `intake_add_followup_task(intake_id)`
- `app.py:17959` `intake_update_followup_task_status(intake_id, task_id)`
- `app.py:17974` `intake_followup_packet(intake_id)`
- `app.py:17991` `intake_followup_packet_docx(intake_id)`
- `app.py:18005` `intake_followup_packet_pdf(intake_id)`
- `app.py:18022` `intake_export_history()`
- `app.py:18034` `intake_export_history_detail(intake_id)`
- `app.py:18045` `intake_module_ledger()`
- `app.py:18060` `intake_document_recommendations(intake_id)`
- `app.py:18085` `intake_update_recommendation_status(intake_id, workflow_key)`
- `app.py:18101` `intake_workflow_launch_prep(intake_id, workflow_key)`
- `app.py:18122` `intake_workflow_bridge(intake_id, workflow_key)`
- `app.py:18204` `intake_workflow_bridge_summary(intake_id, workflow_key)`
- `app.py:18218` `intake_workflow_draft_packet(intake_id, workflow_key)`
- `app.py:18239` `intake_workflow_draft_packet_docx(intake_id, workflow_key)`
- `app.py:18254` `intake_draft_readiness_ledger()`
- `app.py:18264` `intake_draft_readiness_ledger_detail(intake_id)`
- `app.py:18274` `intake_document_draft_choose(intake_id, workflow_key)`
- `app.py:18292` `intake_document_draft_questionnaire(intake_id, workflow_key, document_key)`
- `app.py:18331` `intake_document_draft_preview(intake_id, workflow_key, document_key)`
- `app.py:18345` `intake_nonfinal_draft_document(intake_id, workflow_key, document_key)`
- `app.py:18372` `intake_nonfinal_draft_docx(intake_id, workflow_key, document_key)`
- `app.py:18393` `intake_review_gate_ledger()`
- `app.py:18403` `intake_review_gate_ledger_detail(intake_id)`
- `app.py:18413` `intake_review_gate_detail(intake_id, workflow_key, document_key)`
- `app.py:18431` `intake_review_gate_resolve(intake_id, workflow_key, document_key)`
- `app.py:18453` `intake_final_draft_gate_ledger_detail(intake_id)`
- `app.py:18464` `intake_final_draft_gate_ledger()`
- `app.py:18475` `intake_final_draft_gate_detail(intake_id, workflow_key, document_key)`
- `app.py:18496` `intake_final_draft_gate_approve(intake_id, workflow_key, document_key)`
- `app.py:18517` `intake_final_draft_gate_resolution(intake_id, workflow_key, document_key)`
- `app.py:18562` `intake_final_draft_admin_approval(intake_id, workflow_key, document_key)`
- `app.py:18595` `intake_final_draft_admin_approval_ledger()`
- `app.py:18605` `intake_final_draft_admin_approval_ledger_detail(intake_id)`
- `app.py:18616` `intake_final_draft_workspace(intake_id, workflow_key, document_key)`
- `app.py:18630` `intake_final_draft_section_editor(intake_id, workflow_key, document_key)`
- `app.py:18641` `intake_final_draft_section_edit(intake_id, workflow_key, document_key, section_id)`
- `app.py:18683` `intake_final_draft_preview(intake_id, workflow_key, document_key)`
- `app.py:18693` `intake_final_draft_preview_docx(intake_id, workflow_key, document_key)`
- `app.py:18714` `intake_final_draft_version_register_all()`
- `app.py:18723` `intake_final_draft_version_register_intake(intake_id)`
- `app.py:18732` `intake_final_draft_version_register_detail(intake_id, workflow_key, document_key)`
- `app.py:18745` `intake_final_draft_completion_gate(intake_id, workflow_key, document_key)`
- `app.py:18778` `intake_trust_instrument_menu(intake_id)`
- `app.py:18788` `intake_instrument_draft_packet(intake_id, workflow_key)`
- `app.py:18804` `identity_intake()`
- `app.py:18864` `identity_intake_summary(intake_id)`
- `app.py:19045` `matters_dashboard()`
- `app.py:19052` `new_matter()`
- `app.py:19063` `matter_governance_state(matter_id)`
- `app.py:19091` `matter_risk_update(matter_id)`
- `app.py:19115` `matter_detail(matter_id)`
- `app.py:19130` `matter_relationship_detail(matter_id, relationship_id)`
- `app.py:19212` `matter_relationship_clearance(matter_id, relationship_id)`
- `app.py:19254` `matter_relationship_relink(matter_id, relationship_id)`
- `app.py:19301` `matter_relationship_validate_link(matter_id, relationship_id)`
- `app.py:19340` `matter_relationship_verification_update(matter_id, relationship_id)`
- `app.py:19388` `matter_relationship_status_update(matter_id, relationship_id)`
- `app.py:19419` `new_matter_relationship(matter_id)`
- `app.py:19459` `new_matter_event(matter_id)`
- `database/db.py:26` `ensure_identity_intake_table()`
- `database/db.py:61` `ensure_intake_orchestration_table()`
- `database/db.py:103` `ensure_asset_intake_table()`
- `database/db.py:140` `ensure_document_intake_table()`
- `database/db.py:3511` `upsert_intake_orchestration_state(intake_id, firm_id="FIRM-001", identity_status=None, asset_status=None, document_status=None, review_status=None, drafting_status=None, execution_status=None, archive_status=None, overall_stage=None, readiness_label=None, next_recommended_action=None, next_route=None, complexity_level=None, urgency_level=None)`
- `database/db.py:3581` `get_intake_orchestration_state(intake_id, firm_id="FIRM-001")`
- `database/db.py:3598` `build_intake_readiness_summary(intake_id, firm_id="FIRM-001")`

## Relevant Templates

- `templates/_transfer_guidance.html` references={'matter': 1, 'intake': 0}
- `templates/admin_index.html` references={'matter': 3, 'intake': 26}
- `templates/asset_intake.html` references={'matter': 0, 'intake': 10}
- `templates/controlled_export_prep.html` references={'matter': 1, 'intake': 0}
- `templates/create_trust_step1.html` references={'matter': 1, 'intake': 0}
- `templates/create_trust_step2.html` references={'matter': 2, 'intake': 0}
- `templates/create_trust_step2_grantor.html` references={'matter': 1, 'intake': 0}
- `templates/create_trust_step3.html` references={'matter': 1, 'intake': 0}
- `templates/create_trust_step4.html` references={'matter': 1, 'intake': 0}
- `templates/create_trust_step5.html` references={'matter': 1, 'intake': 0}
- `templates/create_trust_step6.html` references={'matter': 0, 'intake': 2}
- `templates/create_trust_step7.html` references={'matter': 0, 'intake': 3}
- `templates/document_intake.html` references={'matter': 0, 'intake': 10}
- `templates/draft_launch.html` references={'matter': 0, 'intake': 8}
- `templates/guided_draft_workspace.html` references={'matter': 0, 'intake': 9}
- `templates/intake/client_snapshot.html` references={'matter': 0, 'intake': 29}
- `templates/intake/dashboard.html` references={'matter': 0, 'intake': 34}
- `templates/intake/document_draft_choose.html` references={'matter': 0, 'intake': 11}
- `templates/intake/document_draft_preview.html` references={'matter': 0, 'intake': 12}
- `templates/intake/document_draft_questionnaire.html` references={'matter': 0, 'intake': 11}
- `templates/intake/document_recommendations.html` references={'matter': 0, 'intake': 23}
- `templates/intake/draft_readiness_ledger.html` references={'matter': 0, 'intake': 8}
- `templates/intake/export_history.html` references={'matter': 0, 'intake': 10}
- `templates/intake/export_history_detail.html` references={'matter': 0, 'intake': 15}
- `templates/intake/export_prep.html` references={'matter': 0, 'intake': 12}
- `templates/intake/final_draft_admin_approval.html` references={'matter': 0, 'intake': 26}
- `templates/intake/final_draft_completion_gate.html` references={'matter': 0, 'intake': 17}
- `templates/intake/final_draft_gate_resolution.html` references={'matter': 0, 'intake': 14}
- `templates/intake/final_draft_prep_gate.html` references={'matter': 0, 'intake': 29}
- `templates/intake/final_draft_preview.html` references={'matter': 0, 'intake': 14}
- `templates/intake/final_draft_section_editor.html` references={'matter': 0, 'intake': 17}
- `templates/intake/final_draft_version_register.html` references={'matter': 0, 'intake': 16}
- `templates/intake/final_draft_workspace.html` references={'matter': 0, 'intake': 20}
- `templates/intake/followup_packet.html` references={'matter': 0, 'intake': 21}
- `templates/intake/instrument_draft_packet.html` references={'matter': 0, 'intake': 14}
- `templates/intake/module_ledger.html` references={'matter': 0, 'intake': 7}
- `templates/intake/nonfinal_draft_document.html` references={'matter': 0, 'intake': 17}
- `templates/intake/orientation.html` references={'matter': 0, 'intake': 8}
- `templates/intake/review_gate_detail.html` references={'matter': 0, 'intake': 17}
- `templates/intake/review_gate_ledger.html` references={'matter': 0, 'intake': 12}
- `templates/intake/start.html` references={'matter': 0, 'intake': 31}
- `templates/intake/translation_snapshot.html` references={'matter': 2, 'intake': 7}
- `templates/intake/trust_instrument_menu.html` references={'matter': 0, 'intake': 15}
- `templates/intake/universal_profile.html` references={'matter': 0, 'intake': 40}
- `templates/intake/workflow_bridge.html` references={'matter': 0, 'intake': 17}
- `templates/intake/workflow_bridge_summary.html` references={'matter': 0, 'intake': 14}
- `templates/intake/workflow_draft_packet.html` references={'matter': 0, 'intake': 20}
- `templates/intake/workflow_launch_prep.html` references={'matter': 0, 'intake': 18}
- `templates/intake_dashboard.html` references={'matter': 0, 'intake': 25}
- `templates/intake_deep_review.html` references={'matter': 0, 'intake': 9}
- `templates/intake_drafting_prep.html` references={'matter': 0, 'intake': 7}
- `templates/intake_identity.html` references={'matter': 0, 'intake': 6}
- `templates/intake_identity_summary.html` references={'matter': 0, 'intake': 33}
- `templates/intake_readiness.html` references={'matter': 0, 'intake': 10}
- `templates/lifecycle_master_ledger.html` references={'matter': 0, 'intake': 19}
- `templates/matter_detail.html` references={'matter': 43, 'intake': 1}
- `templates/matter_event_form.html` references={'matter': 8, 'intake': 1}
- `templates/matter_form.html` references={'matter': 5, 'intake': 1}
- `templates/matter_relationship_detail.html` references={'matter': 21, 'intake': 0}
- `templates/matter_relationship_form.html` references={'matter': 10, 'intake': 1}
- `templates/matters_dashboard.html` references={'matter': 7, 'intake': 0}
- `templates/transfer_document_support_docs.html` references={'matter': 1, 'intake': 0}
- `templates/trust_formation_preview_hub.html` references={'matter': 0, 'intake': 1}
- `templates/trust_organizational_minutes_output_surface.html` references={'matter': 1, 'intake': 0}

## Findings

- Active branch is strapback/stable-661bb66.
- Active HEAD is 1cf6497598d9d294bc0453847b896316f863c241.
- SQLite integrity check returned ok.
- Live database hash remained unchanged during the audit.

## Warnings

- No route name or endpoint was automatically classified as an explicit Matter–Intake integration route.

## Blockers

- 4 relevant table(s) contain multiple firm/null scopes.

## Next Gate

**MIA-0B — Matter–Intake linkage and authority trace**
