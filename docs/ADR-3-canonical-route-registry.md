# ADR-3 — Canonical Route Registry

Generated: 2026-06-27T20:02:51

## Purpose

Create a canonical registry of Flask routes and classify each route by Institutional Operating System department.

## Classification Rule

Routes are classified by route path and endpoint naming patterns. This is an audit registry, not a behavior change.

## Summary

Total routes detected: **275**

## ADMINISTER

| Route | Endpoint | Methods |
|---|---|---|
| `/admin/diag/execution-record/<record_id>` | `admin_diag_execution_record` | `GET` |
| `/asset` | `asset_dashboard` | `GET` |
| `/asset_health` | `asset_health` | `GET` |
| `/certificates` | `certificate_registry` | `GET` |
| `/certificates/backfill` | `backfill_certificate_ids_route` | `POST` |
| `/certificates/verify/<certificate_id>` | `verify_certificate` | `GET` |
| `/execution` | `execution_dashboard` | `GET` |
| `/execution/tasks/<task_id>` | `execution_task_detail` | `GET` |
| `/execution/tasks/<task_id>/status` | `execution_task_status` | `POST` |
| `/execution/tasks/new` | `execution_task_new` | `GET,POST` |
| `/execution/transfers/<transfer_id>/archive-handoff/<handoff_id>` | `transfer_archive_handoff_detail` | `GET` |
| `/execution/transfers/<transfer_id>/archive-handoff/<handoff_id>/correction/<correction_id>` | `transfer_archive_handoff_correction_detail` | `GET` |
| `/execution/transfers/<transfer_id>/archive-handoff/audit-trail` | `transfer_archive_handoff_audit_trail` | `GET` |
| `/execution/transfers/<transfer_id>/archive-handoff/audit-trail/export.pdf` | `transfer_archive_handoff_audit_export_pdf` | `GET` |
| `/execution/transfers/<transfer_id>/archive-handoff/audit-trail/export.txt` | `transfer_archive_handoff_audit_export_txt` | `GET` |
| `/execution/transfers/<transfer_id>/archive-handoff/export-package.zip` | `transfer_archive_handoff_export_package` | `GET` |
| `/execution/transfers/<transfer_id>/asset` | `transfer_asset` | `GET,POST` |
| `/execution/transfers/<transfer_id>/assignment` | `transfer_assignment` | `GET,POST` |
| `/execution/transfers/<transfer_id>/bank-support-docs` | `transfer_bank_support_docs` | `GET` |
| `/execution/transfers/<transfer_id>/classification` | `transfer_classification` | `GET,POST` |
| `/execution/transfers/<transfer_id>/control_evidence` | `transfer_control_evidence` | `GET,POST` |
| `/execution/transfers/<transfer_id>/detail` | `transfer_detail` | `GET` |
| `/execution/transfers/<transfer_id>/external-tracking` | `transfer_external_tracking` | `GET,POST` |
| `/execution/transfers/<transfer_id>/instructions` | `transfer_instruction_template` | `GET` |
| `/execution/transfers/<transfer_id>/optional-support-docs` | `transfer_optional_support_docs` | `GET` |
| `/execution/transfers/<transfer_id>/personal-property-support-docs` | `transfer_personal_property_support_docs` | `GET` |
| `/execution/transfers/<transfer_id>/print` | `transfer_print_view` | `GET` |
| `/execution/transfers/<transfer_id>/recommended-support-docs` | `transfer_recommended_support_docs` | `GET` |
| `/execution/transfers/<transfer_id>/records` | `transfer_records` | `GET,POST` |
| `/execution/transfers/<transfer_id>/review` | `transfer_review` | `GET,POST` |
| `/execution/transfers/<transfer_id>/support-docs/<int:support_doc_id>/edit` | `transfer_support_doc_edit` | `GET,POST` |
| `/execution/transfers/<transfer_id>/template-center` | `transfer_template_center` | `GET` |
| `/execution/transfers/<transfer_id>/trustee_acceptance` | `transfer_trustee_acceptance` | `GET,POST` |
| `/matters` | `matters_dashboard` | `GET` |
| `/matters/<matter_id>` | `matter_detail` | `GET` |
| `/matters/<matter_id>/events/new` | `new_matter_event` | `GET,POST` |
| `/matters/<matter_id>/governance` | `matter_governance_state` | `POST` |
| `/matters/<matter_id>/relationships/new` | `new_matter_relationship` | `GET,POST` |
| `/matters/<matter_id>/risk` | `matter_risk_update` | `POST` |
| `/matters/new` | `new_matter` | `GET,POST` |
| `/minutes/<minute_id>/certificate.pdf` | `trust_minute_certificate_pdf` | `GET` |
| `/transfers/<transfer_id>/certificate.pdf` | `transfer_certificate_pdf` | `GET` |
| `/trust/<trust_id>/certificate-of-trust-output-surface` | `trust_certificate_of_trust_output_surface` | `GET` |
| `/trust/<trust_id>/certificate-of-trust-output-surface/pdf` | `trust_certificate_of_trust_output_surface_pdf` | `GET` |
| `/trust/<trust_id>/execution` | `trust_execution_dashboard` | `GET` |
| `/trust/<trust_id>/execution/transfers/new` | `transfer_start` | `GET,POST` |

## ARCHIVE

| Route | Endpoint | Methods |
|---|---|---|
| `/admin/audit-log` | `admin_audit_log` | `GET` |
| `/admin/export-policy/toggle` | `admin_toggle_export_policy` | `POST` |
| `/audit` | `audit_dashboard` | `GET` |
| `/docx-export/download/<export_id>` | `download_controlled_docx_export` | `GET` |
| `/exports` | `export_center` | `GET` |
| `/exports/1041/<trust_id>.txt` | `export_1041_text` | `GET` |
| `/exports/1041_summary/<trust_id>.txt` | `export_1041_summary_report` | `GET` |
| `/exports/handoff/<filename>` | `export_handoff_file` | `GET` |
| `/exports/k1/<trust_id>.csv` | `export_k1_live_csv` | `GET` |
| `/exports/k1_summary/<trust_id>.txt` | `export_k1_summary_report` | `GET` |
| `/exports/package/<filename>` | `export_package_file` | `GET` |
| `/exports/roadmap/<filename>` | `export_roadmap_file` | `GET` |
| `/exports/zip` | `export_zip_snapshot` | `GET` |
| `/k1/trust/<trust_id>/export.csv` | `k1_export_csv` | `GET` |
| `/pdf-export/download/<pdf_export_id>` | `download_controlled_pdf_export` | `GET` |
| `/reports/audit.pdf` | `audit_log_report_pdf` | `GET` |
| `/system/health/export.json` | `system_health_export_json` | `GET` |
| `/system/health/export.txt` | `system_health_export_txt` | `GET` |
| `/system/health/export.zip` | `system_health_export_zip` | `GET` |
| `/trust/<trust_id>/archive-handoff/export-index` | `archive_handoff_export_index` | `GET` |
| `/trust/<trust_id>/archive-handoff/export-index/export.csv` | `archive_handoff_export_index_csv` | `GET` |
| `/trust/<trust_id>/controlled-packet-export` | `trust_controlled_packet_export` | `GET` |

## CREATE

| Route | Endpoint | Methods |
|---|---|---|
| `/create-trust-launch` | `create_trust_launch` | `GET` |
| `/create_trust_step7/<trust_id>` | `create_trust_step7` | `GET` |
| `/documents` | `document_dashboard` | `GET` |
| `/documents/<document_id>` | `document_detail` | `GET` |
| `/documents/generate` | `document_generate` | `GET,POST` |
| `/execution/transfers/<transfer_id>/document-support-docs` | `transfer_document_support_docs` | `GET` |
| `/instruments` | `instruments_dashboard` | `GET` |
| `/instruments/<instrument_id>` | `instrument_detail` | `GET,POST` |
| `/instruments/new` | `instrument_create` | `GET,POST` |
| `/instruments/print/<instrument_id>` | `instrument_print` | `GET` |
| `/intake/<intake_id>/draft-readiness` | `intake_draft_readiness_ledger_detail` | `GET` |
| `/intake/<intake_id>/export-prep` | `intake_export_prep` | `GET` |
| `/intake/<intake_id>/exports` | `intake_export_history_detail` | `GET` |
| `/intake/<intake_id>/final-draft-approvals` | `intake_final_draft_admin_approval_ledger_detail` | `GET` |
| `/intake/<intake_id>/final-draft-gate` | `intake_final_draft_gate_ledger_detail` | `GET` |
| `/intake/<intake_id>/final-draft-version-register` | `intake_final_draft_version_register_intake` | `GET` |
| `/intake/<intake_id>/notes/add` | `intake_add_review_note` | `POST` |
| `/intake/<intake_id>/packet` | `intake_followup_packet` | `GET` |
| `/intake/<intake_id>/packet/docx` | `intake_followup_packet_docx` | `GET` |
| `/intake/<intake_id>/packet/pdf` | `intake_followup_packet_pdf` | `GET` |
| `/intake/<intake_id>/recommendations` | `intake_document_recommendations` | `GET` |
| `/intake/<intake_id>/recommendations/<workflow_key>/bridge` | `intake_workflow_bridge` | `GET,POST` |
| `/intake/<intake_id>/recommendations/<workflow_key>/bridge-summary` | `intake_workflow_bridge_summary` | `GET` |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft` | `intake_document_draft_choose` | `GET` |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>` | `intake_document_draft_questionnaire` | `GET,POST` |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/admin-approval` | `intake_final_draft_admin_approval` | `GET,POST` |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-completion-gate` | `intake_final_draft_completion_gate` | `GET,POST` |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate` | `intake_final_draft_gate_detail` | `GET` |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate/approve` | `intake_final_draft_gate_approve` | `POST` |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate/resolve` | `intake_final_draft_gate_resolution` | `GET,POST` |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-preview` | `intake_final_draft_preview` | `GET` |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-preview/docx` | `intake_final_draft_preview_docx` | `GET` |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-version-register` | `intake_final_draft_version_register_detail` | `GET` |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-workspace` | `intake_final_draft_workspace` | `GET` |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-section-editor` | `intake_final_draft_section_editor` | `GET` |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-section-editor/<int:section_id>` | `intake_final_draft_section_edit` | `GET,POST` |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/nonfinal` | `intake_nonfinal_draft_document` | `GET` |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/nonfinal/docx` | `intake_nonfinal_draft_docx` | `GET` |
| `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/preview` | `intake_document_draft_preview` | `GET` |
| `/intake/<intake_id>/recommendations/<workflow_key>/draft-packet` | `intake_workflow_draft_packet` | `GET` |
| `/intake/<intake_id>/recommendations/<workflow_key>/draft-packet/docx` | `intake_workflow_draft_packet_docx` | `GET` |
| `/intake/<intake_id>/recommendations/<workflow_key>/instrument-draft-packet` | `intake_instrument_draft_packet` | `GET` |
| `/intake/<intake_id>/recommendations/<workflow_key>/launch-prep` | `intake_workflow_launch_prep` | `GET` |
| `/intake/<intake_id>/recommendations/<workflow_key>/status` | `intake_update_recommendation_status` | `POST` |
| `/intake/<intake_id>/resume` | `intake_resume` | `GET` |
| `/intake/<intake_id>/review-gates` | `intake_review_gate_ledger_detail` | `GET` |
| `/intake/<intake_id>/review-gates/<workflow_key>/<document_key>` | `intake_review_gate_detail` | `GET` |
| `/intake/<intake_id>/review-gates/<workflow_key>/<document_key>/resolve` | `intake_review_gate_resolve` | `POST` |
| `/intake/<intake_id>/snapshot` | `intake_saved_snapshot` | `GET` |
| `/intake/<intake_id>/tasks/<int:task_id>/status` | `intake_update_followup_task_status` | `POST` |
| `/intake/<intake_id>/tasks/add` | `intake_add_followup_task` | `POST` |
| `/intake/<intake_id>/trust-instruments` | `intake_trust_instrument_menu` | `GET` |
| `/intake/<intake_id>/universal-profile` | `intake_universal_profile` | `GET,POST` |
| `/intake/dashboard` | `intake_dashboard` | `GET` |
| `/intake/draft-readiness` | `intake_draft_readiness_ledger` | `GET` |
| `/intake/exports` | `intake_export_history` | `GET` |
| `/intake/final-draft-approvals` | `intake_final_draft_admin_approval_ledger` | `GET` |
| `/intake/final-draft-gate` | `intake_final_draft_gate_ledger` | `GET` |
| `/intake/final-draft-version-register` | `intake_final_draft_version_register_all` | `GET` |
| `/intake/identity/<intake_id>` | `identity_intake_summary` | `GET` |
| `/intake/modules` | `intake_module_ledger` | `GET` |
| `/intake/readiness/<intake_id>` | `intake_readiness_review` | `GET` |
| `/intake/review-gates` | `intake_review_gate_ledger` | `GET` |
| `/intake/start` | `intake_start` | `GET,POST` |
| `/lifecycle-ledger/<intake_id>` | `lifecycle_master_ledger` | `GET` |
| `/reports/instrument/<instrument_id>.pdf` | `instrument_detail_pdf` | `GET` |
| `/trust/<trust_id>/post-create-review` | `trust_post_create_review` | `GET` |
| `/upload_document` | `upload_document` | `GET,POST` |
| `/workspaces/<workspace_id>/documents` | `workspace_documents` | `GET` |
| `/workspaces/<workspace_id>/documents/generate` | `workspace_document_generate` | `GET,POST` |

## DEVELOPER

| Route | Endpoint | Methods |
|---|---|---|
| `/admin/hosted-bootstrap-admin` | `hosted_bootstrap_admin` | `GET` |
| `/admin/seed-hosted-baseline` | `seed_hosted_baseline_route` | `POST` |
| `/bootstrap_admin_once` | `bootstrap_admin_once` | `GET,POST` |
| `/hosted-bootstrap-admin-once` | `hosted_bootstrap_admin_once` | `GET` |

## EXECUTIVE HOME

| Route | Endpoint | Methods |
|---|---|---|
| `/` | `home` | `GET` |
| `/admin` | `admin_index` | `GET` |
| `/resume` | `resume_process` | `GET` |
| `/workflow` | `workflow_hub` | `GET` |

## GOVERNANCE

| Route | Endpoint | Methods |
|---|---|---|
| `/decision` | `decision_dashboard` | `GET` |
| `/decision/run` | `decision_run` | `POST` |

## IOS Workspace

| Route | Endpoint | Methods |
|---|---|---|
| `/admin/workspace/<workspace_key>` | `admin_ios_workspace` | `GET` |

## LEGACY

| Route | Endpoint | Methods |
|---|---|---|
| `/genealogy` | `genealogy_dashboard` | `GET` |
| `/genealogy/new` | `genealogy_new` | `GET,POST` |
| `/media` | `media_dashboard` | `GET` |
| `/media/file/<media_id>` | `media_file` | `GET` |
| `/media/upload` | `media_upload` | `GET,POST` |

## LIBRARY

| Route | Endpoint | Methods |
|---|---|---|
| `/admin/forms/<form_name>/edit` | `form_guide_edit` | `GET,POST` |
| `/admin/forms/new` | `form_guide_new` | `GET,POST` |
| `/admin/learning/article/<article_id>/edit` | `learning_article_edit` | `GET,POST` |
| `/admin/learning/article/new` | `learning_article_new` | `GET,POST` |
| `/form1041` | `form1041_dashboard` | `GET` |
| `/form1041/preview/<trust_id>` | `form1041_preview` | `GET` |
| `/form1041/print/<trust_id>` | `form1041_print` | `GET` |
| `/forms` | `forms_dashboard` | `GET` |
| `/forms/name/<form_name>` | `form_guide_detail` | `GET` |
| `/guide` | `guide_page` | `GET` |
| `/learning` | `learning_dashboard` | `GET` |
| `/learning/article/<article_id>` | `learning_article` | `GET` |
| `/learning/category/<category>` | `learning_category` | `GET` |
| `/learning/trust-type/<slug>` | `trust_type_detail` | `GET` |
| `/learning/trust-types` | `trust_type_index` | `GET` |
| `/trust/<trust_id>/formation-preview-hub` | `trust_formation_preview_hub` | `GET` |
| `/videos` | `video_dashboard` | `GET` |
| `/videos/<video_id>` | `video_detail` | `GET` |
| `/videos/<video_id>/edit` | `video_edit` | `GET,POST` |
| `/videos/category/<category>` | `video_category` | `GET` |
| `/videos/trust-type/<trust_type>` | `video_trust_type` | `GET` |
| `/videos/upload` | `video_upload` | `GET,POST` |

## PEOPLE

| Route | Endpoint | Methods |
|---|---|---|
| `/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/edit` | `k1_edit_beneficiary` | `GET,POST` |
| `/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/toggle` | `k1_toggle_beneficiary` | `POST` |
| `/k1/trust/<trust_id>/beneficiary/new` | `k1_new_beneficiary` | `GET,POST` |
| `/roles` | `role_dashboard` | `GET` |
| `/roles/new` | `role_new` | `GET,POST` |
| `/trust/<trust_id>/successor-trustee-output-surface` | `trust_successor_trustee_output_surface` | `GET` |
| `/trust/<trust_id>/successor-trustee-output-surface/pdf` | `trust_successor_trustee_output_surface_pdf` | `GET` |
| `/trust/<trust_id>/successor-trustee-preview` | `trust_successor_trustee_preview` | `GET` |
| `/trust/<trust_id>/trustee-acceptance-output-surface` | `trust_trustee_acceptance_output_surface` | `GET` |
| `/trust/<trust_id>/trustee-acceptance-output-surface/pdf` | `trust_trustee_acceptance_output_surface_pdf` | `GET` |
| `/trust/<trust_id>/trustee-acceptance-preview` | `trust_trustee_acceptance_preview` | `GET` |

## REPORTS

| Route | Endpoint | Methods |
|---|---|---|
| `/reports` | `report_center` | `GET,POST` |
| `/reports/1041/<trust_id>` | `form1041_report_view` | `GET` |
| `/reports/1041/<trust_id>/print` | `form1041_report_print` | `GET` |
| `/reports/1041/trust/<trust_id>/<tax_year>.pdf` | `form1041_report_pdf` | `GET` |
| `/reports/fiduciaries.pdf` | `fiduciary_report_pdf` | `GET` |
| `/reports/k1/<trust_id>` | `k1_report_view` | `GET` |
| `/reports/k1/<trust_id>/print` | `k1_report_print` | `GET` |
| `/reports/k1/trust/<trust_id>/<tax_year>.pdf` | `k1_readiness_pdf` | `GET` |
| `/reports/ledger/trust/<trust_id>.pdf` | `ledger_report_pdf` | `GET` |
| `/reports/portfolio.pdf` | `portfolio_report_pdf` | `GET` |
| `/reports/trust/<trust_id>/summary.pdf` | `trust_summary_pdf` | `GET` |
| `/visualization` | `visualization_dashboard` | `GET` |
| `/visualization/analytics` | `analytics_dashboard` | `GET` |
| `/visualization/trust-map` | `trust_map_dashboard` | `GET` |

## SYSTEM

| Route | Endpoint | Methods |
|---|---|---|
| `/hosted-clear-login-lockout-once` | `hosted_clear_login_lockout_once` | `GET` |
| `/hosted-reseed-permissions-once` | `hosted_reseed_permissions_once` | `GET` |
| `/login` | `login` | `GET,POST` |
| `/logout` | `logout` | `GET` |
| `/permissions` | `permissions_dashboard` | `GET,POST` |
| `/security` | `security_dashboard` | `GET` |
| `/system/health` | `system_health_dashboard` | `GET` |
| `/system/recovery/reseed-permissions` | `system_recovery_reseed_permissions` | `POST` |
| `/system/recovery/run` | `system_recovery_run` | `POST` |
| `/users` | `users_dashboard` | `GET` |
| `/users/<username>/edit` | `users_edit` | `GET,POST` |
| `/users/<username>/reset_password` | `users_reset_password` | `GET,POST` |
| `/users/new` | `users_new` | `GET,POST` |

## UNCLASSIFIED

| Route | Endpoint | Methods |
|---|---|---|
| `/add_property` | `add_property` | `GET,POST` |
| `/admin/backup/database` | `admin_database_backup` | `GET` |
| `/admin/backup/database.zip` | `admin_database_backup_zip` | `GET` |
| `/admin/repair/int-lifecycle-tables` | `admin_repair_int_lifecycle_tables` | `GET` |
| `/admin/reset_admin_once` | `reset_admin_once` | `GET` |
| `/admin/run-hosted-firm-scope-migration` | `run_hosted_firm_scope_migration` | `GET` |
| `/admin/storage-diagnostics` | `admin_storage_diagnostics` | `GET` |
| `/change_password` | `change_password` | `GET,POST` |
| `/command` | `command_dashboard` | `GET` |
| `/discussions` | `discussion_dashboard` | `GET` |
| `/discussions/<thread_id>` | `discussion_thread` | `GET` |
| `/discussions/<thread_id>/reply` | `discussion_reply` | `GET,POST` |
| `/discussions/new` | `discussion_new` | `GET,POST` |
| `/evidence/<entity_type>/<entity_id>` | `evidence_by_entity` | `GET` |
| `/fiduciaries` | `fiduciary_dashboard` | `GET` |
| `/fiduciaries/new` | `fiduciary_new` | `GET,POST` |
| `/financial_summary` | `financial_summary` | `GET` |
| `/hosted-auth-diagnostic-once` | `hosted_auth_diagnostic_once` | `GET` |
| `/hosted-firm-scope-migration-once` | `hosted_firm_scope_migration_once` | `GET` |
| `/hosted-repair-admin-access-once` | `hosted_repair_admin_access_once` | `GET` |
| `/hosted-trust-diagnostic-once` | `hosted_trust_diagnostic_once` | `GET` |
| `/k1` | `k1_dashboard` | `GET` |
| `/k1/trust/<trust_id>` | `k1_trust_view` | `GET` |
| `/k1/trust/<trust_id>/distribution/<distribution_id>/edit` | `k1_edit_distribution` | `GET,POST` |
| `/k1/trust/<trust_id>/distribution/new` | `k1_new_distribution` | `GET,POST` |
| `/k1/trust/<trust_id>/year_end_summary` | `k1_year_end_summary` | `GET` |
| `/ledger_entry` | `ledger_entry` | `GET,POST` |
| `/link_account` | `link_account` | `GET,POST` |
| `/minutes` | `trust_minutes_dashboard` | `GET` |
| `/minutes/<minute_id>` | `trust_minute_detail` | `GET` |
| `/minutes/<minute_id>/execute` | `trust_minute_execute` | `POST` |
| `/minutes/<minute_id>/packet.pdf` | `trust_minute_execution_packet_pdf` | `GET` |
| `/minutes/new` | `trust_minutes_new` | `GET,POST` |
| `/portfolio` | `portfolio_dashboard` | `GET` |
| `/property/<property_id>` | `property_detail` | `GET` |
| `/tax_assistant` | `tax_assistant` | `GET` |
| `/trust/<trust_id>` | `trust_detail` | `GET` |
| `/trust/<trust_id>/accounting-method` | `trust_accounting_method_settings` | `GET,POST` |
| `/trust/<trust_id>/articles-output-surface` | `trust_articles_output_surface` | `GET` |
| `/trust/<trust_id>/articles-output-surface/pdf` | `trust_articles_output_surface_pdf` | `GET` |
| `/trust/<trust_id>/articles-preview` | `trust_articles_preview` | `GET` |
| `/trust/<trust_id>/branding` | `trust_branding_settings` | `GET,POST` |
| `/trust/<trust_id>/declaration-output-surface` | `trust_declaration_output_surface` | `GET` |
| `/trust/<trust_id>/declaration-output-surface/pdf` | `trust_declaration_output_surface_pdf` | `GET` |
| `/trust/<trust_id>/general-assignment-output-surface` | `trust_general_assignment_output_surface` | `GET` |
| `/trust/<trust_id>/general-assignment-output-surface/pdf` | `trust_general_assignment_output_surface_pdf` | `GET` |
| `/trust/<trust_id>/general-assignment-preview` | `trust_general_assignment_preview` | `GET` |
| `/trust/<trust_id>/organizational-minutes-output-surface` | `trust_organizational_minutes_output_surface` | `GET` |
| `/trust/<trust_id>/organizational-minutes-output-surface/pdf` | `trust_organizational_minutes_output_surface_pdf` | `GET` |
| `/trust/<trust_id>/organizational-minutes-preview` | `trust_organizational_minutes_preview` | `GET` |
| `/trust/<trust_id>/packet-preview` | `trust_packet_preview` | `GET` |
| `/trust/<trust_id>/seal` | `uploaded_seal` | `GET` |
| `/workspaces` | `workspace_dashboard` | `GET` |
| `/workspaces/<workspace_id>` | `workspace_detail` | `GET` |
| `/workspaces/<workspace_id>/discussions` | `workspace_discussions` | `GET` |
| `/workspaces/<workspace_id>/discussions/new` | `workspace_discussion_new` | `GET,POST` |
| `/workspaces/<workspace_id>/edit` | `workspace_edit` | `GET,POST` |
| `/workspaces/<workspace_id>/notes/new` | `workspace_note_new` | `GET,POST` |
| `/workspaces/<workspace_id>/tasks` | `workspace_tasks` | `GET` |
| `/workspaces/<workspace_id>/tasks/new` | `workspace_task_new` | `GET,POST` |
| `/workspaces/new` | `workspace_new` | `GET,POST` |

## ADR-3 Findings

- Unclassified routes: **61**
- This document should guide future workspace navigation cleanup.
- Broken or placeholder IOS links should be resolved against this registry before new routes are invented.
