# MIA-0B — Matter–Intake Linkage and Authority Trace

**Status:** `TRACE_COMPLETE_REVIEW_REQUIRED`
**Architecture Assessment:** `PARTIAL_MATTER_INTAKE_INTEGRATION_REPAIR_REQUIRED`
**Created:** `2026-06-14T19:51:17.950401`

## Repository

- Branch: `strapback/stable-661bb66`
- HEAD: `1cf6497598d9d294bc0453847b896316f863c241`
- Source MIA-0A: `audit\MIA-0A_matter_intake_baseline_20260614_194425.json`

## Database Safety

- Integrity: `ok`
- SHA-256 before: `eb2b318824be70aa2e37a5a9d7c8c5c1767a7bb7cbf9922f459128751cbf26f8`
- SHA-256 after: `eb2b318824be70aa2e37a5a9d7c8c5c1767a7bb7cbf9922f459128751cbf26f8`
- Database unchanged: `True`

## Linkage Summary

- Matter tables: **3**
- Intake tables: **42**
- Tables containing both matter_id and intake_id: **0**
- Integration routes: **1**
- Integration functions: **1**
- Integration templates: **6**

## Direct Bridge Tables

- None detected.

## Matter–Intake Integration Routes

- `GET /admin/repair/int-lifecycle-tables` → `admin_repair_int_lifecycle_tables` at `app.py:18964`

## Matter–Intake Integration Functions

- `app.py:19130` `matter_relationship_detail`

## Authority Map

### Status

- Assessment: `DUPLICATED_OR_SHARED_AUTHORITY_REVIEW_REQUIRED`
- Matter tables:
  - `matter_relationships` → `status, verification_status, link_validation_status, governance_clearance_status`
  - `matters` → `status, archive_status`
- Intake tables:
  - `controlled_docx_exports` → `export_status`
  - `controlled_export_prep` → `export_status`
  - `controlled_pdf_exports` → `pdf_status`
  - `document_intake` → `upload_status, review_status`
  - `docx_verification_gate` → `file_exists_status, review_status`
  - `draft_sessions` → `workflow_status`
  - `dynamic_draft_previews` → `preview_status`
  - `execution_event_log` → `custody_status, finalization_status`
  - `execution_packet_prep` → `packet_status`
  - `final_record_archive` → `final_status, archive_status, custody_status`
  - `guided_draft_workspace` → `workspace_status, generated_output_status`
  - `identity_intake` → `marital_status, completion_status`
  - `intake_deep_review` → `review_status`
  - `intake_document_recommendations` → `status`
  - `intake_draft_readiness_ledger` → `status`
  - `intake_drafting_prep_gate` → `drafting_status`
  - `intake_export_logs` → `export_status`
  - `intake_final_draft_admin_approvals` → `approval_status, gate_status_before, gate_status_after`
  - `intake_final_draft_completion_actions` → `action_status`
  - `intake_final_draft_completion_gate` → `gate_status`
  - `intake_final_draft_prep_gate` → `gate_status`
  - `intake_final_draft_sections` → `section_status`
  - `intake_final_draft_version_register` → `preview_status, finality_status`
  - `intake_followup_tasks` → `status`
  - `intake_module_ledger` → `status, status_label`
  - `intake_orchestration` → `identity_status, asset_status, document_status, review_status, drafting_status, execution_status, archive_status`
  - `intake_review_gate_actions` → `resulting_status`
  - `intake_review_gate_ledger` → `gate_status, document_status`
  - `intake_review_notes` → `followup_status`
  - `intake_sessions` → `status`
  - `pdf_execution_approval_gate` → `file_exists_status, review_status`
  - `section_review_gate` → `clause_status`
- Support tables:
  - `app_users` → `status`
  - `archive_packet_finalization` → `packet_status, integrity_status, resolution_status, finalized_status`
  - `discussion_threads` → `status`
  - `distributions` → `status`
  - `document_templates` → `status`
  - `execution_tasks` → `status`
  - `fiduciaries` → `status`
  - `genealogy_records` → `verification_status`
  - `generated_documents` → `status`
  - `instruments` → `status`
  - `learning_articles` → `status`
  - `properties` → `status, memorial_status, sacred_status`
  - `tax_form_guides` → `status`
  - `transfer_archive_handoff` → `archive_status`
  - `transfer_archive_handoff_corrections` → `corrected_archive_status`
  - `transfer_support_docs` → `status`
  - `transfers` → `status, control_change_status`
  - `trust_minutes` → `status`
  - `trusts` → `status`
  - `user_roles` → `status`
  - `workspaces` → `status`

### Risk

- Assessment: `DUPLICATED_OR_SHARED_AUTHORITY_REVIEW_REQUIRED`
- Matter tables:
  - `matters` → `risk_level`
- Intake tables:
  - `asset_intake` → `risk_level`
  - `intake_sessions` → `risk_posture`
  - `intake_translations` → `risk_flag`

### Priority

- Assessment: `DUPLICATED_OR_SHARED_AUTHORITY_REVIEW_REQUIRED`
- Matter tables:
  - `matters` → `priority`
- Intake tables:
  - `intake_document_recommendations` → `priority`
  - `intake_followup_tasks` → `priority`
  - `intake_review_notes` → `priority`
- Support tables:
  - `execution_tasks` → `priority`
  - `properties` → `continuity_priority`

### Complexity

- Assessment: `INTAKE_APPEARS_PRIMARY`
- Intake tables:
  - `intake_orchestration` → `complexity_level`
  - `intake_scores` → `complexity_score, complexity_level`

### Readiness

- Assessment: `INTAKE_APPEARS_PRIMARY`
- Intake tables:
  - `document_intake` → `readiness_impact`
  - `execution_packet_prep` → `execution_readiness`
  - `intake_draft_readiness_ledger` → `readiness`
  - `intake_orchestration` → `readiness_label`
  - `intake_scores` → `readiness_score, readiness_level`

### Governance

- Assessment: `MATTER_APPEARS_PRIMARY`
- Matter tables:
  - `matter_relationships` → `governance_clearance_status, governance_clearance_note, governance_cleared_by, governance_cleared_at`
  - `matters` → `governance_state`

### Review

- Assessment: `INTAKE_APPEARS_PRIMARY`
- Intake tables:
  - `document_intake` → `review_status`
  - `docx_verification_gate` → `review_status`
  - `dynamic_draft_previews` → `preview_status`
  - `intake_deep_review` → `review_status`
  - `intake_drafting_prep_gate` → `reviewer_approval`
  - `intake_final_draft_version_register` → `preview_status`
  - `intake_orchestration` → `review_status`
  - `pdf_execution_approval_gate` → `review_status`

### Drafting

- Assessment: `INTAKE_APPEARS_PRIMARY`
- Intake tables:
  - `intake_drafting_prep_gate` → `drafting_status`
  - `intake_orchestration` → `drafting_status`

### Execution

- Assessment: `INTAKE_APPEARS_PRIMARY`
- Intake tables:
  - `execution_packet_prep` → `execution_readiness`
  - `intake_orchestration` → `execution_status`

### Archive

- Assessment: `DUPLICATED_OR_SHARED_AUTHORITY_REVIEW_REQUIRED`
- Matter tables:
  - `matters` → `archive_status`
- Intake tables:
  - `final_record_archive` → `archive_status`
  - `intake_orchestration` → `archive_status`
- Support tables:
  - `transfer_archive_handoff` → `archive_status`
  - `transfer_archive_handoff_corrections` → `corrected_archive_status`

### Completion

- Assessment: `INTAKE_APPEARS_PRIMARY`
- Intake tables:
  - `identity_intake` → `completion_status`
  - `intake_final_draft_completion_gate` → `completion_note`

### Verification

- Assessment: `DUPLICATED_OR_SHARED_AUTHORITY_REVIEW_REQUIRED`
- Matter tables:
  - `matter_relationships` → `verification_status, verification_basis`
- Intake tables:
  - `controlled_pdf_exports` → `verification_id`
  - `docx_verification_gate` → `verification_id`
- Support tables:
  - `genealogy_records` → `verification_status`

### Finalization

- Assessment: `INTAKE_APPEARS_PRIMARY`
- Intake tables:
  - `execution_event_log` → `finalization_status, finalization_gate`
- Support tables:
  - `archive_packet_finalization` → `finalization_id`
  - `transfer_archive_handoff` → `finalization_verified`

### Approval

- Assessment: `INTAKE_APPEARS_PRIMARY`
- Intake tables:
  - `execution_packet_prep` → `approval_id`
  - `intake_drafting_prep_gate` → `reviewer_approval`
  - `intake_final_draft_admin_approvals` → `approval_status, approval_note`
  - `intake_final_draft_prep_gate` → `approval_note`
  - `pdf_execution_approval_gate` → `approval_id`

## Mixed-Firm Relevant Tables

- `app_users` → `{'FIRM-001': 5, 'FIRM-002': 2}`
- `execution_tasks` → `{'FIRM-001': 6, 'FIRM-002': 1}`
- `intake_document_recommendations` → `{'FIRM-001': 8, 'FIRM-002': 7}`
- `intake_export_logs` → `{'FIRM-001': 7, 'FIRM-002': 3}`
- `intake_final_draft_gate_actions` → `{'FIRM-001': 1, 'FIRM-002': 5}`
- `intake_review_gate_actions` → `{'FIRM-001': 1, 'FIRM-002': 1}`
- `properties` → `{'FIRM-001': 1, 'FIRM-002': 1}`
- `transfers` → `{'FIRM-001': 12, 'FIRM-002': 1}`
- `trusts` → `{'FIRM-001': 20, 'FIRM-002': 2}`
- `workspaces` → `{'FIRM-001': 6, 'FIRM-002': 1}`

## Findings

- SQLite integrity check returned ok.
- 1 route(s) contain both Matter and Intake references.
- 1 function(s) contain both Matter and Intake references.
- 6 template(s) contain both Matter and Intake references.
- Live database hash remained unchanged.

## Warnings

- No relevant table contains both matter_id and intake_id.

## Blockers

- Potential duplicated/shared authority detected for: archive, priority, risk, status, verification
- 10 relevant table(s) contain mixed firm scopes.

## Next Gate

**MIA-0C — Matter–Intake Architectural Adoption and Repair Decision**
