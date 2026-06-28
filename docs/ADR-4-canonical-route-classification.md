# ADR-4 — Canonical Route Classification

Generated: 2026-06-27T20:45:43

## Purpose

Classify routes from ADR-3 into proposed Institutional Operating System ownership groups.

This is a governance document only. It does not change Flask routes, templates, permissions, or navigation.

## Summary

Total routes classified: **275**
Manual review required: **96**

## ADMINISTER

| Route | Endpoint | Methods | Proposed Action |
|---|---|---|---|
| `/add_property` | `add_property` | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/asset` | `asset_dashboard` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/asset_health` | `asset_health` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/certificates` | `certificate_registry` | `GET` | Keep; evaluate for Certificates module. |
| `/certificates/backfill` | `backfill_certificate_ids_route` | `POST` | Keep; evaluate for Certificates module. |
| `/certificates/verify/<certificate_id>` | `verify_certificate` | `GET` | Keep; evaluate for Certificates module. |
| `/create-trust-launch` | `create_trust_launch` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/create_trust_step7/<trust_id>` | `create_trust_step7` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/execution/transfers/<transfer_id>/archive-handoff/<handoff_id>` | `transfer_archive_handoff_detail` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/archive-handoff/<handoff_id>/correction/<correction_id>` | `transfer_archive_handoff_correction_detail` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/archive-handoff/audit-trail` | `transfer_archive_handoff_audit_trail` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/archive-handoff/audit-trail/export.pdf` | `transfer_archive_handoff_audit_export_pdf` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/archive-handoff/audit-trail/export.txt` | `transfer_archive_handoff_audit_export_txt` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/archive-handoff/export-package.zip` | `transfer_archive_handoff_export_package` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/asset` | `transfer_asset` | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/assignment` | `transfer_assignment` | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/bank-support-docs` | `transfer_bank_support_docs` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/classification` | `transfer_classification` | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/control_evidence` | `transfer_control_evidence` | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/detail` | `transfer_detail` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/document-support-docs` | `transfer_document_support_docs` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/external-tracking` | `transfer_external_tracking` | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/instructions` | `transfer_instruction_template` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/optional-support-docs` | `transfer_optional_support_docs` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/personal-property-support-docs` | `transfer_personal_property_support_docs` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/print` | `transfer_print_view` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/recommended-support-docs` | `transfer_recommended_support_docs` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/records` | `transfer_records` | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/review` | `transfer_review` | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/support-docs/<int:support_doc_id>/edit` | `transfer_support_doc_edit` | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/template-center` | `transfer_template_center` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/trustee_acceptance` | `transfer_trustee_acceptance` | `GET,POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/exports/1041/<trust_id>.txt` | `export_1041_text` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/exports/1041_summary/<trust_id>.txt` | `export_1041_summary_report` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/exports/k1/<trust_id>.csv` | `export_k1_live_csv` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/exports/k1_summary/<trust_id>.txt` | `export_k1_summary_report` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/form1041/preview/<trust_id>` | `form1041_preview` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/form1041/print/<trust_id>` | `form1041_print` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/hosted-trust-diagnostic-once` | `hosted_trust_diagnostic_once` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/intake/<intake_id>/trust-instruments` | `intake_trust_instrument_menu` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/k1/trust/<trust_id>` | `k1_trust_view` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/edit` | `k1_edit_beneficiary` | `GET,POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/toggle` | `k1_toggle_beneficiary` | `POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/k1/trust/<trust_id>/beneficiary/new` | `k1_new_beneficiary` | `GET,POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/k1/trust/<trust_id>/distribution/<distribution_id>/edit` | `k1_edit_distribution` | `GET,POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/k1/trust/<trust_id>/distribution/new` | `k1_new_distribution` | `GET,POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/k1/trust/<trust_id>/export.csv` | `k1_export_csv` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/k1/trust/<trust_id>/year_end_summary` | `k1_year_end_summary` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/learning/trust-type/<slug>` | `trust_type_detail` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/learning/trust-types` | `trust_type_index` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/matters` | `matters_dashboard` | `GET` | Keep; evaluate for Matter Operations. |
| `/matters/<matter_id>` | `matter_detail` | `GET` | Keep; evaluate for Matter Operations. |
| `/matters/<matter_id>/events/new` | `new_matter_event` | `GET,POST` | Keep; evaluate for Matter Operations. |
| `/matters/<matter_id>/governance` | `matter_governance_state` | `POST` | Keep; evaluate for Matter Operations. |
| `/matters/<matter_id>/relationships/new` | `new_matter_relationship` | `GET,POST` | Keep; evaluate for Matter Operations. |
| `/matters/<matter_id>/risk` | `matter_risk_update` | `POST` | Keep; evaluate for Matter Operations. |
| `/matters/new` | `new_matter` | `GET,POST` | Keep; evaluate for Matter Operations. |
| `/minutes/<minute_id>/certificate.pdf` | `trust_minute_certificate_pdf` | `GET` | Keep; evaluate for Certificates module. |
| `/property/<property_id>` | `property_detail` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/reports/1041/<trust_id>` | `form1041_report_view` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/reports/1041/<trust_id>/print` | `form1041_report_print` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/reports/1041/trust/<trust_id>/<tax_year>.pdf` | `form1041_report_pdf` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/reports/k1/<trust_id>` | `k1_report_view` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/reports/k1/<trust_id>/print` | `k1_report_print` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/reports/k1/trust/<trust_id>/<tax_year>.pdf` | `k1_readiness_pdf` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/reports/ledger/trust/<trust_id>.pdf` | `ledger_report_pdf` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/reports/trust/<trust_id>/summary.pdf` | `trust_summary_pdf` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/transfers/<transfer_id>/certificate.pdf` | `transfer_certificate_pdf` | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/trust/<trust_id>` | `trust_detail` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/accounting-method` | `trust_accounting_method_settings` | `GET,POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/archive-handoff/export-index` | `archive_handoff_export_index` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/archive-handoff/export-index/export.csv` | `archive_handoff_export_index_csv` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/articles-output-surface` | `trust_articles_output_surface` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/articles-output-surface/pdf` | `trust_articles_output_surface_pdf` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/articles-preview` | `trust_articles_preview` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/branding` | `trust_branding_settings` | `GET,POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/certificate-of-trust-output-surface` | `trust_certificate_of_trust_output_surface` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/certificate-of-trust-output-surface/pdf` | `trust_certificate_of_trust_output_surface_pdf` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/controlled-packet-export` | `trust_controlled_packet_export` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/declaration-output-surface` | `trust_declaration_output_surface` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/declaration-output-surface/pdf` | `trust_declaration_output_surface_pdf` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/execution` | `trust_execution_dashboard` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/execution/transfers/new` | `transfer_start` | `GET,POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/formation-preview-hub` | `trust_formation_preview_hub` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/general-assignment-output-surface` | `trust_general_assignment_output_surface` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/general-assignment-output-surface/pdf` | `trust_general_assignment_output_surface_pdf` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/general-assignment-preview` | `trust_general_assignment_preview` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/organizational-minutes-output-surface` | `trust_organizational_minutes_output_surface` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/organizational-minutes-output-surface/pdf` | `trust_organizational_minutes_output_surface_pdf` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/organizational-minutes-preview` | `trust_organizational_minutes_preview` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/packet-preview` | `trust_packet_preview` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/post-create-review` | `trust_post_create_review` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/seal` | `uploaded_seal` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/successor-trustee-output-surface` | `trust_successor_trustee_output_surface` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/successor-trustee-output-surface/pdf` | `trust_successor_trustee_output_surface_pdf` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/successor-trustee-preview` | `trust_successor_trustee_preview` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/trustee-acceptance-output-surface` | `trust_trustee_acceptance_output_surface` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/trustee-acceptance-output-surface/pdf` | `trust_trustee_acceptance_output_surface_pdf` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/trustee-acceptance-preview` | `trust_trustee_acceptance_preview` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/videos/trust-type/<trust_type>` | `video_trust_type` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/visualization/trust-map` | `trust_map_dashboard` | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |

## ARCHIVE

| Route | Endpoint | Methods | Proposed Action |
|---|---|---|---|
| `/admin/audit-log` | `admin_audit_log` | `GET` | Keep; migrate under Archive workspace. |
| `/admin/export-policy/toggle` | `admin_toggle_export_policy` | `POST` | Keep; migrate under Archive workspace. |
| `/audit` | `audit_dashboard` | `GET` | Keep; migrate under Archive workspace. |
| `/docx-export/download/<export_id>` | `download_controlled_docx_export` | `GET` | Keep; migrate under Archive workspace. |
| `/exports` | `export_center` | `GET` | Keep; migrate under Archive workspace. |
| `/exports/handoff/<filename>` | `export_handoff_file` | `GET` | Keep; migrate under Archive workspace. |
| `/exports/package/<filename>` | `export_package_file` | `GET` | Keep; migrate under Archive workspace. |
| `/exports/roadmap/<filename>` | `export_roadmap_file` | `GET` | Keep; migrate under Archive workspace. |
| `/exports/zip` | `export_zip_snapshot` | `GET` | Keep; migrate under Archive workspace. |
| `/intake/<intake_id>/export-prep` | `intake_export_prep` | `GET` | Keep; migrate under Archive workspace. |
| `/intake/<intake_id>/exports` | `intake_export_history_detail` | `GET` | Keep; migrate under Archive workspace. |
| `/intake/exports` | `intake_export_history` | `GET` | Keep; migrate under Archive workspace. |
| `/pdf-export/download/<pdf_export_id>` | `download_controlled_pdf_export` | `GET` | Keep; migrate under Archive workspace. |
| `/system/health/export.json` | `system_health_export_json` | `GET` | Keep; migrate under Archive workspace. |
| `/system/health/export.txt` | `system_health_export_txt` | `GET` | Keep; migrate under Archive workspace. |
| `/system/health/export.zip` | `system_health_export_zip` | `GET` | Keep; migrate under Archive workspace. |

## DEVELOPER

| Route | Endpoint | Methods | Proposed Action |
|---|---|---|---|
| `/admin/hosted-bootstrap-admin` | `hosted_bootstrap_admin` | `GET` | Restrict; keep developer/internal only. |
| `/admin/seed-hosted-baseline` | `seed_hosted_baseline_route` | `POST` | Restrict; keep developer/internal only. |
| `/bootstrap_admin_once` | `bootstrap_admin_once` | `GET,POST` | Restrict; keep developer/internal only. |
| `/hosted-bootstrap-admin-once` | `hosted_bootstrap_admin_once` | `GET` | Restrict; keep developer/internal only. |

## EXECUTIVE HOME

| Route | Endpoint | Methods | Proposed Action |
|---|---|---|---|
| `/` | `home` | `GET` | Keep; expose through HOME or legacy dashboard. |
| `/admin` | `admin_index` | `GET` | Keep; expose through HOME or legacy dashboard. |
| `/resume` | `resume_process` | `GET` | Keep; expose through HOME or legacy dashboard. |
| `/workflow` | `workflow_hub` | `GET` | Keep; expose through HOME or legacy dashboard. |

## GOVERNANCE

| Route | Endpoint | Methods | Proposed Action |
|---|---|---|---|
| `/command` | `command_dashboard` | `GET` | Review; likely governance/decision workflow. |
| `/decision` | `decision_dashboard` | `GET` | Review; likely governance/decision workflow. |
| `/decision/run` | `decision_run` | `POST` | Review; likely governance/decision workflow. |
| `/discussions` | `discussion_dashboard` | `GET` | Review; likely governance/decision workflow. |
| `/discussions/<thread_id>` | `discussion_thread` | `GET` | Review; likely governance/decision workflow. |
| `/discussions/<thread_id>/reply` | `discussion_reply` | `GET,POST` | Review; likely governance/decision workflow. |
| `/discussions/new` | `discussion_new` | `GET,POST` | Review; likely governance/decision workflow. |
| `/workspaces/<workspace_id>/discussions` | `workspace_discussions` | `GET` | Review; likely governance/decision workflow. |
| `/workspaces/<workspace_id>/discussions/new` | `workspace_discussion_new` | `GET,POST` | Review; likely governance/decision workflow. |

## LEGACY

| Route | Endpoint | Methods | Proposed Action |
|---|---|---|---|
| `/genealogy` | `genealogy_dashboard` | `GET` | Keep; migrate under Legacy workspace. |
| `/genealogy/new` | `genealogy_new` | `GET,POST` | Keep; migrate under Legacy workspace. |
| `/media` | `media_dashboard` | `GET` | Keep; migrate under Legacy workspace. |
| `/media/file/<media_id>` | `media_file` | `GET` | Keep; migrate under Legacy workspace. |
| `/media/upload` | `media_upload` | `GET,POST` | Keep; migrate under Legacy workspace. |

## LIBRARY

| Route | Endpoint | Methods | Proposed Action |
|---|---|---|---|
| `/admin/forms/<form_name>/edit` | `form_guide_edit` | `GET,POST` | Keep; migrate under Library workspace. |
| `/admin/forms/new` | `form_guide_new` | `GET,POST` | Keep; migrate under Library workspace. |
| `/admin/learning/article/<article_id>/edit` | `learning_article_edit` | `GET,POST` | Keep; migrate under Library workspace. |
| `/admin/learning/article/new` | `learning_article_new` | `GET,POST` | Keep; migrate under Library workspace. |
| `/form1041` | `form1041_dashboard` | `GET` | Keep; migrate under Library workspace. |
| `/forms` | `forms_dashboard` | `GET` | Keep; migrate under Library workspace. |
| `/forms/name/<form_name>` | `form_guide_detail` | `GET` | Keep; migrate under Library workspace. |
| `/guide` | `guide_page` | `GET` | Keep; migrate under Library workspace. |
| `/learning` | `learning_dashboard` | `GET` | Keep; migrate under Library workspace. |
| `/learning/article/<article_id>` | `learning_article` | `GET` | Keep; migrate under Library workspace. |
| `/learning/category/<category>` | `learning_category` | `GET` | Keep; migrate under Library workspace. |
| `/videos` | `video_dashboard` | `GET` | Keep; migrate under Library workspace. |
| `/videos/<video_id>` | `video_detail` | `GET` | Keep; migrate under Library workspace. |
| `/videos/<video_id>/edit` | `video_edit` | `GET,POST` | Keep; migrate under Library workspace. |
| `/videos/category/<category>` | `video_category` | `GET` | Keep; migrate under Library workspace. |
| `/videos/upload` | `video_upload` | `GET,POST` | Keep; migrate under Library workspace. |

## PEOPLE

| Route | Endpoint | Methods | Proposed Action |
|---|---|---|---|
| `/roles` | `role_dashboard` | `GET` | Keep; evaluate for People workspace or System users. |
| `/roles/new` | `role_new` | `GET,POST` | Keep; evaluate for People workspace or System users. |
| `/users` | `users_dashboard` | `GET` | Keep; evaluate for People workspace or System users. |
| `/users/<username>/edit` | `users_edit` | `GET,POST` | Keep; evaluate for People workspace or System users. |
| `/users/<username>/reset_password` | `users_reset_password` | `GET,POST` | Keep; evaluate for People workspace or System users. |
| `/users/new` | `users_new` | `GET,POST` | Keep; evaluate for People workspace or System users. |

## REPORTS

| Route | Endpoint | Methods | Proposed Action |
|---|---|---|---|
| `/k1` | `k1_dashboard` | `GET` | Keep; migrate under Reports workspace. |
| `/reports` | `report_center` | `GET,POST` | Keep; migrate under Reports workspace. |
| `/reports/audit.pdf` | `audit_log_report_pdf` | `GET` | Keep; migrate under Reports workspace. |
| `/reports/fiduciaries.pdf` | `fiduciary_report_pdf` | `GET` | Keep; migrate under Reports workspace. |
| `/reports/instrument/<instrument_id>.pdf` | `instrument_detail_pdf` | `GET` | Keep; migrate under Reports workspace. |
| `/reports/portfolio.pdf` | `portfolio_report_pdf` | `GET` | Keep; migrate under Reports workspace. |
| `/tax_assistant` | `tax_assistant` | `GET` | Keep; migrate under Reports workspace. |
| `/visualization` | `visualization_dashboard` | `GET` | Keep; migrate under Reports workspace. |
| `/visualization/analytics` | `analytics_dashboard` | `GET` | Keep; migrate under Reports workspace. |

## REVIEW REQUIRED

| Route | Endpoint | Methods | Proposed Action |
|---|---|---|---|
| `/admin/backup/database` | `admin_database_backup` | `GET` | Manual classification required. |
| `/admin/backup/database.zip` | `admin_database_backup_zip` | `GET` | Manual classification required. |
| `/admin/diag/execution-record/<record_id>` | `admin_diag_execution_record` | `GET` | Manual classification required. |
| `/admin/repair/int-lifecycle-tables` | `admin_repair_int_lifecycle_tables` | `GET` | Manual classification required. |
| `/admin/reset_admin_once` | `reset_admin_once` | `GET` | Manual classification required. |
| `/admin/run-hosted-firm-scope-migration` | `run_hosted_firm_scope_migration` | `GET` | Manual classification required. |
| `/admin/storage-diagnostics` | `admin_storage_diagnostics` | `GET` | Manual classification required. |
| `/admin/workspace/<workspace_key>` | `admin_ios_workspace` | `GET` | Manual classification required. |
| `/change_password` | `change_password` | `GET,POST` | Manual classification required. |
| `/documents` | `document_dashboard` | `GET` | Manual classification required. |
| `/documents/<document_id>` | `document_detail` | `GET` | Manual classification required. |
| `/documents/generate` | `document_generate` | `GET,POST` | Manual classification required. |
| `/evidence/<entity_type>/<entity_id>` | `evidence_by_entity` | `GET` | Manual classification required. |
| `/execution` | `execution_dashboard` | `GET` | Manual classification required. |
| `/execution/tasks/<task_id>` | `execution_task_detail` | `GET` | Manual classification required. |
| `/execution/tasks/<task_id>/status` | `execution_task_status` | `POST` | Manual classification required. |
| `/execution/tasks/new` | `execution_task_new` | `GET,POST` | Manual classification required. |
| `/fiduciaries` | `fiduciary_dashboard` | `GET` | Manual classification required. |
| `/fiduciaries/new` | `fiduciary_new` | `GET,POST` | Manual classification required. |
| `/financial_summary` | `financial_summary` | `GET` | Manual classification required. |
| `/hosted-auth-diagnostic-once` | `hosted_auth_diagnostic_once` | `GET` | Manual classification required. |
| `/hosted-firm-scope-migration-once` | `hosted_firm_scope_migration_once` | `GET` | Manual classification required. |
| `/hosted-repair-admin-access-once` | `hosted_repair_admin_access_once` | `GET` | Manual classification required. |
| `/instruments` | `instruments_dashboard` | `GET` | Manual classification required. |
| `/instruments/<instrument_id>` | `instrument_detail` | `GET,POST` | Manual classification required. |
| `/instruments/new` | `instrument_create` | `GET,POST` | Manual classification required. |
| `/instruments/print/<instrument_id>` | `instrument_print` | `GET` | Manual classification required. |
| `/intake/<intake_id>/draft-readiness` | `intake_draft_readiness_ledger_detail` | `GET` | Manual classification required. |
| `/intake/<intake_id>/final-draft-approvals` | `intake_final_draft_admin_approval_ledger_detail` | `GET` | Manual classification required. |
| `/intake/<intake_id>/final-draft-gate` | `intake_final_draft_gate_ledger_detail` | `GET` | Manual classification required. |
| `/intake/<intake_id>/final-draft-version-register` | `intake_final_draft_version_register_intake` | `GET` | Manual classification required. |
| `/intake/<intake_id>/notes/add` | `intake_add_review_note` | `POST` | Manual classification required. |
| `/intake/<intake_id>/packet` | `intake_followup_packet` | `GET` | Manual classification required. |
| `/intake/<intake_id>/packet/docx` | `intake_followup_packet_docx` | `GET` | Manual classification required. |
| `/intake/<intake_id>/packet/pdf` | `intake_followup_packet_pdf` | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations` | `intake_document_recommendations` | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/bridge` | `intake_workflow_bridge` | `GET,POST` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/bridge-summary` | `intake_workflow_bridge_summary` | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft` | `intake_document_draft_choose` | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>` | `intake_document_draft_questionnaire` | `GET,POST` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/admin-approval` | `intake_final_draft_admin_approval` | `GET,POST` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-completion-gate` | `intake_final_draft_completion_gate` | `GET,POST` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate` | `intake_final_draft_gate_detail` | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate/approve` | `intake_final_draft_gate_approve` | `POST` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate/resolve` | `intake_final_draft_gate_resolution` | `GET,POST` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-preview` | `intake_final_draft_preview` | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-preview/docx` | `intake_final_draft_preview_docx` | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-version-register` | `intake_final_draft_version_register_detail` | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-workspace` | `intake_final_draft_workspace` | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-section-editor` | `intake_final_draft_section_editor` | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-section-editor/<int:section_id>` | `intake_final_draft_section_edit` | `GET,POST` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/nonfinal` | `intake_nonfinal_draft_document` | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/nonfinal/docx` | `intake_nonfinal_draft_docx` | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/preview` | `intake_document_draft_preview` | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/draft-packet` | `intake_workflow_draft_packet` | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/draft-packet/docx` | `intake_workflow_draft_packet_docx` | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/instrument-draft-packet` | `intake_instrument_draft_packet` | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/launch-prep` | `intake_workflow_launch_prep` | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/status` | `intake_update_recommendation_status` | `POST` | Manual classification required. |
| `/intake/<intake_id>/resume` | `intake_resume` | `GET` | Manual classification required. |
| `/intake/<intake_id>/review-gates` | `intake_review_gate_ledger_detail` | `GET` | Manual classification required. |
| `/intake/<intake_id>/review-gates/<workflow_key>/<document_key>` | `intake_review_gate_detail` | `GET` | Manual classification required. |
| `/intake/<intake_id>/review-gates/<workflow_key>/<document_key>/resolve` | `intake_review_gate_resolve` | `POST` | Manual classification required. |
| `/intake/<intake_id>/snapshot` | `intake_saved_snapshot` | `GET` | Manual classification required. |
| `/intake/<intake_id>/tasks/<int:task_id>/status` | `intake_update_followup_task_status` | `POST` | Manual classification required. |
| `/intake/<intake_id>/tasks/add` | `intake_add_followup_task` | `POST` | Manual classification required. |
| `/intake/<intake_id>/universal-profile` | `intake_universal_profile` | `GET,POST` | Manual classification required. |
| `/intake/dashboard` | `intake_dashboard` | `GET` | Manual classification required. |
| `/intake/draft-readiness` | `intake_draft_readiness_ledger` | `GET` | Manual classification required. |
| `/intake/final-draft-approvals` | `intake_final_draft_admin_approval_ledger` | `GET` | Manual classification required. |
| `/intake/final-draft-gate` | `intake_final_draft_gate_ledger` | `GET` | Manual classification required. |
| `/intake/final-draft-version-register` | `intake_final_draft_version_register_all` | `GET` | Manual classification required. |
| `/intake/identity/<intake_id>` | `identity_intake_summary` | `GET` | Manual classification required. |
| `/intake/modules` | `intake_module_ledger` | `GET` | Manual classification required. |
| `/intake/readiness/<intake_id>` | `intake_readiness_review` | `GET` | Manual classification required. |
| `/intake/review-gates` | `intake_review_gate_ledger` | `GET` | Manual classification required. |
| `/intake/start` | `intake_start` | `GET,POST` | Manual classification required. |
| `/ledger_entry` | `ledger_entry` | `GET,POST` | Manual classification required. |
| `/lifecycle-ledger/<intake_id>` | `lifecycle_master_ledger` | `GET` | Manual classification required. |
| `/link_account` | `link_account` | `GET,POST` | Manual classification required. |
| `/minutes` | `trust_minutes_dashboard` | `GET` | Manual classification required. |
| `/minutes/<minute_id>` | `trust_minute_detail` | `GET` | Manual classification required. |
| `/minutes/<minute_id>/execute` | `trust_minute_execute` | `POST` | Manual classification required. |
| `/minutes/<minute_id>/packet.pdf` | `trust_minute_execution_packet_pdf` | `GET` | Manual classification required. |
| `/minutes/new` | `trust_minutes_new` | `GET,POST` | Manual classification required. |
| `/portfolio` | `portfolio_dashboard` | `GET` | Manual classification required. |
| `/upload_document` | `upload_document` | `GET,POST` | Manual classification required. |
| `/workspaces` | `workspace_dashboard` | `GET` | Manual classification required. |
| `/workspaces/<workspace_id>` | `workspace_detail` | `GET` | Manual classification required. |
| `/workspaces/<workspace_id>/documents` | `workspace_documents` | `GET` | Manual classification required. |
| `/workspaces/<workspace_id>/documents/generate` | `workspace_document_generate` | `GET,POST` | Manual classification required. |
| `/workspaces/<workspace_id>/edit` | `workspace_edit` | `GET,POST` | Manual classification required. |
| `/workspaces/<workspace_id>/notes/new` | `workspace_note_new` | `GET,POST` | Manual classification required. |
| `/workspaces/<workspace_id>/tasks` | `workspace_tasks` | `GET` | Manual classification required. |
| `/workspaces/<workspace_id>/tasks/new` | `workspace_task_new` | `GET,POST` | Manual classification required. |
| `/workspaces/new` | `workspace_new` | `GET,POST` | Manual classification required. |

## SYSTEM

| Route | Endpoint | Methods | Proposed Action |
|---|---|---|---|
| `/hosted-clear-login-lockout-once` | `hosted_clear_login_lockout_once` | `GET` | Keep; migrate under System workspace. |
| `/hosted-reseed-permissions-once` | `hosted_reseed_permissions_once` | `GET` | Keep; migrate under System workspace. |
| `/login` | `login` | `GET,POST` | Keep; migrate under System workspace. |
| `/logout` | `logout` | `GET` | Keep; migrate under System workspace. |
| `/permissions` | `permissions_dashboard` | `GET,POST` | Keep; migrate under System workspace. |
| `/security` | `security_dashboard` | `GET` | Keep; migrate under System workspace. |
| `/system/health` | `system_health_dashboard` | `GET` | Keep; migrate under System workspace. |
| `/system/recovery/reseed-permissions` | `system_recovery_reseed_permissions` | `POST` | Keep; migrate under System workspace. |
| `/system/recovery/run` | `system_recovery_run` | `POST` | Keep; migrate under System workspace. |

## ADR-4 Findings

- ADR-4 converts route inventory into IOS ownership decisions.
- Routes marked REVIEW REQUIRED should not be migrated until individually evaluated.
- Workspace navigation should be built only after ownership is assigned.
- Unimplemented links from IOS-2G should be resolved only after consulting this classification.
