# ADR-5 — Navigation Ownership Matrix

Generated: 2026-06-27T20:47:45

## Purpose

Map every canonical Flask route to its Institutional Operating System workspace.

This document governs navigation ownership only. It does not modify routes or permissions.

## REVIEW

| Route | Endpoint | Owner | Methods | Action |
|---|---|---|---|---|
| `/` | `home` | P | `GET` | Keep; expose through HOME or legacy dashboard. |
| `/add_property` | `add_property` | P | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/admin` | `admin_index` | P | `GET` | Keep; expose through HOME or legacy dashboard. |
| `/admin/audit-log` | `admin_audit_log` | P | `GET` | Keep; migrate under Archive workspace. |
| `/admin/backup/database` | `admin_database_backup` | P | `GET` | Manual classification required. |
| `/admin/backup/database.zip` | `admin_database_backup_zip` | P | `GET` | Manual classification required. |
| `/admin/diag/execution-record/<record_id>` | `admin_diag_execution_record` | P | `GET` | Manual classification required. |
| `/admin/export-policy/toggle` | `admin_toggle_export_policy` | P | `POST` | Keep; migrate under Archive workspace. |
| `/admin/forms/<form_name>/edit` | `form_guide_edit` | P | `GET,POST` | Keep; migrate under Library workspace. |
| `/admin/forms/new` | `form_guide_new` | P | `GET,POST` | Keep; migrate under Library workspace. |
| `/admin/hosted-bootstrap-admin` | `hosted_bootstrap_admin` | P | `GET` | Restrict; keep developer/internal only. |
| `/admin/learning/article/<article_id>/edit` | `learning_article_edit` | P | `GET,POST` | Keep; migrate under Library workspace. |
| `/admin/learning/article/new` | `learning_article_new` | P | `GET,POST` | Keep; migrate under Library workspace. |
| `/admin/repair/int-lifecycle-tables` | `admin_repair_int_lifecycle_tables` | P | `GET` | Manual classification required. |
| `/admin/reset_admin_once` | `reset_admin_once` | P | `GET` | Manual classification required. |
| `/admin/run-hosted-firm-scope-migration` | `run_hosted_firm_scope_migration` | P | `GET` | Manual classification required. |
| `/admin/seed-hosted-baseline` | `seed_hosted_baseline_route` | P | `POST` | Restrict; keep developer/internal only. |
| `/admin/storage-diagnostics` | `admin_storage_diagnostics` | P | `GET` | Manual classification required. |
| `/admin/workspace/<workspace_key>` | `admin_ios_workspace` | P | `GET` | Manual classification required. |
| `/asset` | `asset_dashboard` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/asset_health` | `asset_health` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/audit` | `audit_dashboard` | P | `GET` | Keep; migrate under Archive workspace. |
| `/bootstrap_admin_once` | `bootstrap_admin_once` | P | `GET,POST` | Restrict; keep developer/internal only. |
| `/certificates` | `certificate_registry` | P | `GET` | Keep; evaluate for Certificates module. |
| `/certificates/backfill` | `backfill_certificate_ids_route` | P | `POST` | Keep; evaluate for Certificates module. |
| `/certificates/verify/<certificate_id>` | `verify_certificate` | P | `GET` | Keep; evaluate for Certificates module. |
| `/change_password` | `change_password` | P | `GET,POST` | Manual classification required. |
| `/command` | `command_dashboard` | P | `GET` | Review; likely governance/decision workflow. |
| `/create-trust-launch` | `create_trust_launch` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/create_trust_step7/<trust_id>` | `create_trust_step7` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/decision` | `decision_dashboard` | P | `GET` | Review; likely governance/decision workflow. |
| `/decision/run` | `decision_run` | P | `POST` | Review; likely governance/decision workflow. |
| `/discussions` | `discussion_dashboard` | P | `GET` | Review; likely governance/decision workflow. |
| `/discussions/<thread_id>` | `discussion_thread` | P | `GET` | Review; likely governance/decision workflow. |
| `/discussions/<thread_id>/reply` | `discussion_reply` | P | `GET,POST` | Review; likely governance/decision workflow. |
| `/discussions/new` | `discussion_new` | P | `GET,POST` | Review; likely governance/decision workflow. |
| `/documents` | `document_dashboard` | P | `GET` | Manual classification required. |
| `/documents/<document_id>` | `document_detail` | P | `GET` | Manual classification required. |
| `/documents/generate` | `document_generate` | P | `GET,POST` | Manual classification required. |
| `/docx-export/download/<export_id>` | `download_controlled_docx_export` | P | `GET` | Keep; migrate under Archive workspace. |
| `/evidence/<entity_type>/<entity_id>` | `evidence_by_entity` | P | `GET` | Manual classification required. |
| `/execution` | `execution_dashboard` | P | `GET` | Manual classification required. |
| `/execution/tasks/<task_id>` | `execution_task_detail` | P | `GET` | Manual classification required. |
| `/execution/tasks/<task_id>/status` | `execution_task_status` | P | `POST` | Manual classification required. |
| `/execution/tasks/new` | `execution_task_new` | P | `GET,POST` | Manual classification required. |
| `/execution/transfers/<transfer_id>/archive-handoff/<handoff_id>` | `transfer_archive_handoff_detail` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/archive-handoff/<handoff_id>/correction/<correction_id>` | `transfer_archive_handoff_correction_detail` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/archive-handoff/audit-trail` | `transfer_archive_handoff_audit_trail` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/archive-handoff/audit-trail/export.pdf` | `transfer_archive_handoff_audit_export_pdf` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/archive-handoff/audit-trail/export.txt` | `transfer_archive_handoff_audit_export_txt` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/archive-handoff/export-package.zip` | `transfer_archive_handoff_export_package` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/asset` | `transfer_asset` | P | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/assignment` | `transfer_assignment` | P | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/bank-support-docs` | `transfer_bank_support_docs` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/classification` | `transfer_classification` | P | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/control_evidence` | `transfer_control_evidence` | P | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/detail` | `transfer_detail` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/document-support-docs` | `transfer_document_support_docs` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/external-tracking` | `transfer_external_tracking` | P | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/instructions` | `transfer_instruction_template` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/optional-support-docs` | `transfer_optional_support_docs` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/personal-property-support-docs` | `transfer_personal_property_support_docs` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/print` | `transfer_print_view` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/recommended-support-docs` | `transfer_recommended_support_docs` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/records` | `transfer_records` | P | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/review` | `transfer_review` | P | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/support-docs/<int:support_doc_id>/edit` | `transfer_support_doc_edit` | P | `GET,POST` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/template-center` | `transfer_template_center` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/execution/transfers/<transfer_id>/trustee_acceptance` | `transfer_trustee_acceptance` | P | `GET,POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/exports` | `export_center` | P | `GET` | Keep; migrate under Archive workspace. |
| `/exports/1041/<trust_id>.txt` | `export_1041_text` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/exports/1041_summary/<trust_id>.txt` | `export_1041_summary_report` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/exports/handoff/<filename>` | `export_handoff_file` | P | `GET` | Keep; migrate under Archive workspace. |
| `/exports/k1/<trust_id>.csv` | `export_k1_live_csv` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/exports/k1_summary/<trust_id>.txt` | `export_k1_summary_report` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/exports/package/<filename>` | `export_package_file` | P | `GET` | Keep; migrate under Archive workspace. |
| `/exports/roadmap/<filename>` | `export_roadmap_file` | P | `GET` | Keep; migrate under Archive workspace. |
| `/exports/zip` | `export_zip_snapshot` | P | `GET` | Keep; migrate under Archive workspace. |
| `/fiduciaries` | `fiduciary_dashboard` | P | `GET` | Manual classification required. |
| `/fiduciaries/new` | `fiduciary_new` | P | `GET,POST` | Manual classification required. |
| `/financial_summary` | `financial_summary` | P | `GET` | Manual classification required. |
| `/form1041` | `form1041_dashboard` | P | `GET` | Keep; migrate under Library workspace. |
| `/form1041/preview/<trust_id>` | `form1041_preview` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/form1041/print/<trust_id>` | `form1041_print` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/forms` | `forms_dashboard` | P | `GET` | Keep; migrate under Library workspace. |
| `/forms/name/<form_name>` | `form_guide_detail` | P | `GET` | Keep; migrate under Library workspace. |
| `/genealogy` | `genealogy_dashboard` | P | `GET` | Keep; migrate under Legacy workspace. |
| `/genealogy/new` | `genealogy_new` | P | `GET,POST` | Keep; migrate under Legacy workspace. |
| `/guide` | `guide_page` | P | `GET` | Keep; migrate under Library workspace. |
| `/hosted-auth-diagnostic-once` | `hosted_auth_diagnostic_once` | P | `GET` | Manual classification required. |
| `/hosted-bootstrap-admin-once` | `hosted_bootstrap_admin_once` | P | `GET` | Restrict; keep developer/internal only. |
| `/hosted-clear-login-lockout-once` | `hosted_clear_login_lockout_once` | P | `GET` | Keep; migrate under System workspace. |
| `/hosted-firm-scope-migration-once` | `hosted_firm_scope_migration_once` | P | `GET` | Manual classification required. |
| `/hosted-repair-admin-access-once` | `hosted_repair_admin_access_once` | P | `GET` | Manual classification required. |
| `/hosted-reseed-permissions-once` | `hosted_reseed_permissions_once` | P | `GET` | Keep; migrate under System workspace. |
| `/hosted-trust-diagnostic-once` | `hosted_trust_diagnostic_once` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/instruments` | `instruments_dashboard` | P | `GET` | Manual classification required. |
| `/instruments/<instrument_id>` | `instrument_detail` | P | `GET,POST` | Manual classification required. |
| `/instruments/new` | `instrument_create` | P | `GET,POST` | Manual classification required. |
| `/instruments/print/<instrument_id>` | `instrument_print` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/draft-readiness` | `intake_draft_readiness_ledger_detail` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/export-prep` | `intake_export_prep` | P | `GET` | Keep; migrate under Archive workspace. |
| `/intake/<intake_id>/exports` | `intake_export_history_detail` | P | `GET` | Keep; migrate under Archive workspace. |
| `/intake/<intake_id>/final-draft-approvals` | `intake_final_draft_admin_approval_ledger_detail` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/final-draft-gate` | `intake_final_draft_gate_ledger_detail` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/final-draft-version-register` | `intake_final_draft_version_register_intake` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/notes/add` | `intake_add_review_note` | P | `POST` | Manual classification required. |
| `/intake/<intake_id>/packet` | `intake_followup_packet` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/packet/docx` | `intake_followup_packet_docx` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/packet/pdf` | `intake_followup_packet_pdf` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations` | `intake_document_recommendations` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/bridge` | `intake_workflow_bridge` | P | `GET,POST` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/bridge-summary` | `intake_workflow_bridge_summary` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft` | `intake_document_draft_choose` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>` | `intake_document_draft_questionnaire` | P | `GET,POST` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/admin-approval` | `intake_final_draft_admin_approval` | P | `GET,POST` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-completion-gate` | `intake_final_draft_completion_gate` | P | `GET,POST` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate` | `intake_final_draft_gate_detail` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate/approve` | `intake_final_draft_gate_approve` | P | `POST` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate/resolve` | `intake_final_draft_gate_resolution` | P | `GET,POST` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-preview` | `intake_final_draft_preview` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-preview/docx` | `intake_final_draft_preview_docx` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-version-register` | `intake_final_draft_version_register_detail` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-workspace` | `intake_final_draft_workspace` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-section-editor` | `intake_final_draft_section_editor` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-section-editor/<int:section_id>` | `intake_final_draft_section_edit` | P | `GET,POST` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/nonfinal` | `intake_nonfinal_draft_document` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/nonfinal/docx` | `intake_nonfinal_draft_docx` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/preview` | `intake_document_draft_preview` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/draft-packet` | `intake_workflow_draft_packet` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/draft-packet/docx` | `intake_workflow_draft_packet_docx` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/instrument-draft-packet` | `intake_instrument_draft_packet` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/launch-prep` | `intake_workflow_launch_prep` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/recommendations/<workflow_key>/status` | `intake_update_recommendation_status` | P | `POST` | Manual classification required. |
| `/intake/<intake_id>/resume` | `intake_resume` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/review-gates` | `intake_review_gate_ledger_detail` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/review-gates/<workflow_key>/<document_key>` | `intake_review_gate_detail` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/review-gates/<workflow_key>/<document_key>/resolve` | `intake_review_gate_resolve` | P | `POST` | Manual classification required. |
| `/intake/<intake_id>/snapshot` | `intake_saved_snapshot` | P | `GET` | Manual classification required. |
| `/intake/<intake_id>/tasks/<int:task_id>/status` | `intake_update_followup_task_status` | P | `POST` | Manual classification required. |
| `/intake/<intake_id>/tasks/add` | `intake_add_followup_task` | P | `POST` | Manual classification required. |
| `/intake/<intake_id>/trust-instruments` | `intake_trust_instrument_menu` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/intake/<intake_id>/universal-profile` | `intake_universal_profile` | P | `GET,POST` | Manual classification required. |
| `/intake/dashboard` | `intake_dashboard` | P | `GET` | Manual classification required. |
| `/intake/draft-readiness` | `intake_draft_readiness_ledger` | P | `GET` | Manual classification required. |
| `/intake/exports` | `intake_export_history` | P | `GET` | Keep; migrate under Archive workspace. |
| `/intake/final-draft-approvals` | `intake_final_draft_admin_approval_ledger` | P | `GET` | Manual classification required. |
| `/intake/final-draft-gate` | `intake_final_draft_gate_ledger` | P | `GET` | Manual classification required. |
| `/intake/final-draft-version-register` | `intake_final_draft_version_register_all` | P | `GET` | Manual classification required. |
| `/intake/identity/<intake_id>` | `identity_intake_summary` | P | `GET` | Manual classification required. |
| `/intake/modules` | `intake_module_ledger` | P | `GET` | Manual classification required. |
| `/intake/readiness/<intake_id>` | `intake_readiness_review` | P | `GET` | Manual classification required. |
| `/intake/review-gates` | `intake_review_gate_ledger` | P | `GET` | Manual classification required. |
| `/intake/start` | `intake_start` | P | `GET,POST` | Manual classification required. |
| `/k1` | `k1_dashboard` | P | `GET` | Keep; migrate under Reports workspace. |
| `/k1/trust/<trust_id>` | `k1_trust_view` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/edit` | `k1_edit_beneficiary` | P | `GET,POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/toggle` | `k1_toggle_beneficiary` | P | `POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/k1/trust/<trust_id>/beneficiary/new` | `k1_new_beneficiary` | P | `GET,POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/k1/trust/<trust_id>/distribution/<distribution_id>/edit` | `k1_edit_distribution` | P | `GET,POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/k1/trust/<trust_id>/distribution/new` | `k1_new_distribution` | P | `GET,POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/k1/trust/<trust_id>/export.csv` | `k1_export_csv` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/k1/trust/<trust_id>/year_end_summary` | `k1_year_end_summary` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/learning` | `learning_dashboard` | P | `GET` | Keep; migrate under Library workspace. |
| `/learning/article/<article_id>` | `learning_article` | P | `GET` | Keep; migrate under Library workspace. |
| `/learning/category/<category>` | `learning_category` | P | `GET` | Keep; migrate under Library workspace. |
| `/learning/trust-type/<slug>` | `trust_type_detail` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/learning/trust-types` | `trust_type_index` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/ledger_entry` | `ledger_entry` | P | `GET,POST` | Manual classification required. |
| `/lifecycle-ledger/<intake_id>` | `lifecycle_master_ledger` | P | `GET` | Manual classification required. |
| `/link_account` | `link_account` | P | `GET,POST` | Manual classification required. |
| `/login` | `login` | P | `GET,POST` | Keep; migrate under System workspace. |
| `/logout` | `logout` | P | `GET` | Keep; migrate under System workspace. |
| `/matters` | `matters_dashboard` | P | `GET` | Keep; evaluate for Matter Operations. |
| `/matters/<matter_id>` | `matter_detail` | P | `GET` | Keep; evaluate for Matter Operations. |
| `/matters/<matter_id>/events/new` | `new_matter_event` | P | `GET,POST` | Keep; evaluate for Matter Operations. |
| `/matters/<matter_id>/governance` | `matter_governance_state` | P | `POST` | Keep; evaluate for Matter Operations. |
| `/matters/<matter_id>/relationships/new` | `new_matter_relationship` | P | `GET,POST` | Keep; evaluate for Matter Operations. |
| `/matters/<matter_id>/risk` | `matter_risk_update` | P | `POST` | Keep; evaluate for Matter Operations. |
| `/matters/new` | `new_matter` | P | `GET,POST` | Keep; evaluate for Matter Operations. |
| `/media` | `media_dashboard` | P | `GET` | Keep; migrate under Legacy workspace. |
| `/media/file/<media_id>` | `media_file` | P | `GET` | Keep; migrate under Legacy workspace. |
| `/media/upload` | `media_upload` | P | `GET,POST` | Keep; migrate under Legacy workspace. |
| `/minutes` | `trust_minutes_dashboard` | P | `GET` | Manual classification required. |
| `/minutes/<minute_id>` | `trust_minute_detail` | P | `GET` | Manual classification required. |
| `/minutes/<minute_id>/certificate.pdf` | `trust_minute_certificate_pdf` | P | `GET` | Keep; evaluate for Certificates module. |
| `/minutes/<minute_id>/execute` | `trust_minute_execute` | P | `POST` | Manual classification required. |
| `/minutes/<minute_id>/packet.pdf` | `trust_minute_execution_packet_pdf` | P | `GET` | Manual classification required. |
| `/minutes/new` | `trust_minutes_new` | P | `GET,POST` | Manual classification required. |
| `/pdf-export/download/<pdf_export_id>` | `download_controlled_pdf_export` | P | `GET` | Keep; migrate under Archive workspace. |
| `/permissions` | `permissions_dashboard` | P | `GET,POST` | Keep; migrate under System workspace. |
| `/portfolio` | `portfolio_dashboard` | P | `GET` | Manual classification required. |
| `/property/<property_id>` | `property_detail` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/reports` | `report_center` | P | `GET,POST` | Keep; migrate under Reports workspace. |
| `/reports/1041/<trust_id>` | `form1041_report_view` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/reports/1041/<trust_id>/print` | `form1041_report_print` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/reports/1041/trust/<trust_id>/<tax_year>.pdf` | `form1041_report_pdf` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/reports/audit.pdf` | `audit_log_report_pdf` | P | `GET` | Keep; migrate under Reports workspace. |
| `/reports/fiduciaries.pdf` | `fiduciary_report_pdf` | P | `GET` | Keep; migrate under Reports workspace. |
| `/reports/instrument/<instrument_id>.pdf` | `instrument_detail_pdf` | P | `GET` | Keep; migrate under Reports workspace. |
| `/reports/k1/<trust_id>` | `k1_report_view` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/reports/k1/<trust_id>/print` | `k1_report_print` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/reports/k1/trust/<trust_id>/<tax_year>.pdf` | `k1_readiness_pdf` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/reports/ledger/trust/<trust_id>.pdf` | `ledger_report_pdf` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/reports/portfolio.pdf` | `portfolio_report_pdf` | P | `GET` | Keep; migrate under Reports workspace. |
| `/reports/trust/<trust_id>/summary.pdf` | `trust_summary_pdf` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/resume` | `resume_process` | P | `GET` | Keep; expose through HOME or legacy dashboard. |
| `/roles` | `role_dashboard` | P | `GET` | Keep; evaluate for People workspace or System users. |
| `/roles/new` | `role_new` | P | `GET,POST` | Keep; evaluate for People workspace or System users. |
| `/security` | `security_dashboard` | P | `GET` | Keep; migrate under System workspace. |
| `/system/health` | `system_health_dashboard` | P | `GET` | Keep; migrate under System workspace. |
| `/system/health/export.json` | `system_health_export_json` | P | `GET` | Keep; migrate under Archive workspace. |
| `/system/health/export.txt` | `system_health_export_txt` | P | `GET` | Keep; migrate under Archive workspace. |
| `/system/health/export.zip` | `system_health_export_zip` | P | `GET` | Keep; migrate under Archive workspace. |
| `/system/recovery/reseed-permissions` | `system_recovery_reseed_permissions` | P | `POST` | Keep; migrate under System workspace. |
| `/system/recovery/run` | `system_recovery_run` | P | `POST` | Keep; migrate under System workspace. |
| `/tax_assistant` | `tax_assistant` | P | `GET` | Keep; migrate under Reports workspace. |
| `/transfers/<transfer_id>/certificate.pdf` | `transfer_certificate_pdf` | P | `GET` | Keep; evaluate for Assets/Funding/Transfer workflow. |
| `/trust/<trust_id>` | `trust_detail` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/accounting-method` | `trust_accounting_method_settings` | P | `GET,POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/archive-handoff/export-index` | `archive_handoff_export_index` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/archive-handoff/export-index/export.csv` | `archive_handoff_export_index_csv` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/articles-output-surface` | `trust_articles_output_surface` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/articles-output-surface/pdf` | `trust_articles_output_surface_pdf` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/articles-preview` | `trust_articles_preview` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/branding` | `trust_branding_settings` | P | `GET,POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/certificate-of-trust-output-surface` | `trust_certificate_of_trust_output_surface` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/certificate-of-trust-output-surface/pdf` | `trust_certificate_of_trust_output_surface_pdf` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/controlled-packet-export` | `trust_controlled_packet_export` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/declaration-output-surface` | `trust_declaration_output_surface` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/declaration-output-surface/pdf` | `trust_declaration_output_surface_pdf` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/execution` | `trust_execution_dashboard` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/execution/transfers/new` | `transfer_start` | P | `GET,POST` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/formation-preview-hub` | `trust_formation_preview_hub` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/general-assignment-output-surface` | `trust_general_assignment_output_surface` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/general-assignment-output-surface/pdf` | `trust_general_assignment_output_surface_pdf` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/general-assignment-preview` | `trust_general_assignment_preview` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/organizational-minutes-output-surface` | `trust_organizational_minutes_output_surface` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/organizational-minutes-output-surface/pdf` | `trust_organizational_minutes_output_surface_pdf` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/organizational-minutes-preview` | `trust_organizational_minutes_preview` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/packet-preview` | `trust_packet_preview` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/post-create-review` | `trust_post_create_review` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/seal` | `uploaded_seal` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/successor-trustee-output-surface` | `trust_successor_trustee_output_surface` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/successor-trustee-output-surface/pdf` | `trust_successor_trustee_output_surface_pdf` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/successor-trustee-preview` | `trust_successor_trustee_preview` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/trustee-acceptance-output-surface` | `trust_trustee_acceptance_output_surface` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/trustee-acceptance-output-surface/pdf` | `trust_trustee_acceptance_output_surface_pdf` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/trust/<trust_id>/trustee-acceptance-preview` | `trust_trustee_acceptance_preview` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/upload_document` | `upload_document` | P | `GET,POST` | Manual classification required. |
| `/users` | `users_dashboard` | P | `GET` | Keep; evaluate for People workspace or System users. |
| `/users/<username>/edit` | `users_edit` | P | `GET,POST` | Keep; evaluate for People workspace or System users. |
| `/users/<username>/reset_password` | `users_reset_password` | P | `GET,POST` | Keep; evaluate for People workspace or System users. |
| `/users/new` | `users_new` | P | `GET,POST` | Keep; evaluate for People workspace or System users. |
| `/videos` | `video_dashboard` | P | `GET` | Keep; migrate under Library workspace. |
| `/videos/<video_id>` | `video_detail` | P | `GET` | Keep; migrate under Library workspace. |
| `/videos/<video_id>/edit` | `video_edit` | P | `GET,POST` | Keep; migrate under Library workspace. |
| `/videos/category/<category>` | `video_category` | P | `GET` | Keep; migrate under Library workspace. |
| `/videos/trust-type/<trust_type>` | `video_trust_type` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/videos/upload` | `video_upload` | P | `GET,POST` | Keep; migrate under Library workspace. |
| `/visualization` | `visualization_dashboard` | P | `GET` | Keep; migrate under Reports workspace. |
| `/visualization/analytics` | `analytics_dashboard` | P | `GET` | Keep; migrate under Reports workspace. |
| `/visualization/trust-map` | `trust_map_dashboard` | P | `GET` | Keep; evaluate for Trust Registry or trust detail workflow. |
| `/workflow` | `workflow_hub` | P | `GET` | Keep; expose through HOME or legacy dashboard. |
| `/workspaces` | `workspace_dashboard` | P | `GET` | Manual classification required. |
| `/workspaces/<workspace_id>` | `workspace_detail` | P | `GET` | Manual classification required. |
| `/workspaces/<workspace_id>/discussions` | `workspace_discussions` | P | `GET` | Review; likely governance/decision workflow. |
| `/workspaces/<workspace_id>/discussions/new` | `workspace_discussion_new` | P | `GET,POST` | Review; likely governance/decision workflow. |
| `/workspaces/<workspace_id>/documents` | `workspace_documents` | P | `GET` | Manual classification required. |
| `/workspaces/<workspace_id>/documents/generate` | `workspace_document_generate` | P | `GET,POST` | Manual classification required. |
| `/workspaces/<workspace_id>/edit` | `workspace_edit` | P | `GET,POST` | Manual classification required. |
| `/workspaces/<workspace_id>/notes/new` | `workspace_note_new` | P | `GET,POST` | Manual classification required. |
| `/workspaces/<workspace_id>/tasks` | `workspace_tasks` | P | `GET` | Manual classification required. |
| `/workspaces/<workspace_id>/tasks/new` | `workspace_task_new` | P | `GET,POST` | Manual classification required. |
| `/workspaces/new` | `workspace_new` | P | `GET,POST` | Manual classification required. |

## ADR-5 Findings

- Every route now has an IOS navigation owner.
- REVIEW workspace indicates governance decisions still required.
- Navigation should be generated from this matrix rather than hard-coded.
- Future workspaces should inherit ownership from this registry.
