# UPA-1A — Universal Platform Inventory

Generated: 2026-06-13T15:16:00.483564

## Repository State

- Branch: `strapback/stable-661bb66`
- HEAD: `1cf6497598d9d294bc0453847b896316f863c241`
- Last commit:
```text
1cf6497598d9d294bc0453847b896316f863c241
2026-06-13 14:41:22 -0400
Complete IC-1 relationship audit summary and closeout gate
```
- Git status:
```text
[clean]
```

## Counts

- All Files: **623**
- Text Files: **414**
- Python Files: **28**
- Template Files: **277**
- Routes: **380**
- Sql Table Definitions: **104**
- Personal Leakage Hits: **16**
- Firm Scope Files: **15**

## File Types

- `.backup_before_fix`: 1
- `.bak`: 33
- `.bak_admin_polish_pass2`: 1
- `.bak_admin_polish_pass3`: 1
- `.bak_admin_recovery_route`: 1
- `.bak_admin_ux1`: 1
- `.bak_admin_ux2`: 1
- `.bak_admin_ux3`: 1
- `.bak_admin_ux4`: 1
- `.bak_admin_ux4_labels`: 1
- `.bak_admin_ux5`: 1
- `.bak_before_admin_polish`: 1
- `.bak_cleanup_duplicates`: 1
- `.bak_db_int_repair_1`: 1
- `.bak_db_int_repair_2`: 1
- `.bak_diag_assets_docs`: 1
- `.bak_diag_table_names_2`: 1
- `.bak_doc_specific_correction_links`: 1
- `.bak_document_readiness_matrix`: 1
- `.bak_exec_approval_1`: 1
- `.bak_exec_flow_2`: 1
- `.bak_execution_handoff_banner`: 1
- `.bak_export_activity`: 4
- `.bak_export_guard_1`: 1
- `.bak_export_guard_1b`: 1
- `.bak_export_guard_1c`: 1
- `.bak_export_guard_direct`: 1
- `.bak_firm_scope_1`: 1
- `.bak_firm_scope_2`: 1
- `.bak_firm_scope_diag`: 1
- `.bak_packet_status_banner`: 1
- `.bak_phase34_step2`: 1
- `.bak_phase34_step2_cleanup`: 1
- `.bak_phase35_articles_output_surface`: 1
- `.bak_phase35_step2`: 1
- `.bak_phase36_print`: 1
- `.bak_phase36_step2`: 1
- `.bak_phase37_live`: 1
- `.bak_phase37_trustee_acceptance`: 2
- `.bak_phase38_general_assignment,`: 1
- `.bak_phase39_exec_fix`: 1
- `.bak_phase39_organizational_minutes`: 1
- `.bak_phase40_successor_trustee`: 1
- `.bak_phase41_preview_context_refine`: 1
- `.bak_phase41_upgrade`: 5
- `.bak_phase42`: 5
- `.bak_phase43_pdf`: 5
- `.bak_phase43_pdf_fanout`: 1
- `.bak_phase43_pdf_layer`: 1
- `.bak_phase44_packet_export`: 2
- `.bak_phase45_packet_manifest`: 1
- `.bak_phase46_dynamic_admin`: 2
- `.bak_phase47_status_matrix`: 1
- `.bak_phase48_readiness`: 2
- `.bak_phase49_missing_hints`: 2
- `.bak_phase50_friendly_labels`: 1
- `.bak_phase51_packet_preview`: 2
- `.bak_phase52_validation_detail`: 2
- `.bak_phase53_packet_gating`: 3
- `.bak_phase54_admin_dashboard`: 2
- `.bak_phase55_docs_ui`: 5
- `.bak_phase55_ui`: 3
- `.bak_phase55_ui_continue`: 4
- `.bak_phase56_visual_consistency`: 3
- `.bak_phase57_correction_links`: 3
- `.bak_phase58_exact_wizard_links`: 1
- `.bak_phase59_strict_export`: 3
- `.bak_phase60_export_mode_toggle`: 2
- `.bak_phase61_policy_visibility`: 4
- `.bak_phase62_return_routing`: 5
- `.bak_phase63_return_routing`: 1
- `.bak_phase64_post_save_return`: 1
- `.bak_phase65_return_banner`: 3
- `.bak_phase66_admin_completion_summary`: 2
- `.bak_phase67_timestamp_visibility`: 4
- `.bak_phase69_master_admin_routes`: 1
- `.bak_phase71_scoped_data_visibility`: 1
- `.bak_phase72_trust_assignment_scoping`: 1
- `.bak_phase73_master_admin_audit_logging`: 1
- `.bak_phase74_audit_log_viewer`: 2
- `.bak_phase75_db_path_env`: 2
- `.bak_phase_admin_launch`: 1
- `.bak_phase_nav_execution`: 1
- `.bak_phase_nav_fix`: 1
- `.bak_policy_access_1`: 1
- `.bak_policy_toggle_access`: 1
- `.bak_policy_ui_1`: 1
- `.bak_post_create_console`: 1
- `.bak_railway_sec_3a_exports`: 1
- `.bak_readiness_panel`: 1
- `.bak_sec4ab`: 4
- `.bak_stabilize_live_execution`: 1
- `.css`: 1
- `.csv`: 1
- `.db`: 5
- `.docx`: 5
- `.example`: 1
- `.html`: 280
- `.jpg`: 1
- `.json`: 2
- `.md`: 50
- `.pdf`: 5
- `.png`: 2
- `.py`: 28
- `.txt`: 52
- `.yaml`: 1
- `.zip`: 4
- `[no extension]`: 2

## Routes

| Methods | Route | Endpoint | Source |
|---|---|---|---|
| GET | `/` | `home` | `app.py:2835` |
| GET | `/` | `home` | `package_export/app.py:86` |
| GET, POST | `/add_property` | `add_property` | `app.py:3103` |
| GET, POST | `/add_property` | `add_property` | `package_export/app.py:297` |
| GET | `/admin` | `admin_index` | `app.py:6672` |
| GET | `/admin` | `admin_index` | `package_export/app.py:657` |
| GET | `/admin/articles` | `admin_articles` | `app.py:15017` |
| GET, POST | `/admin/articles/new` | `admin_articles_new` | `app.py:15024` |
| GET | `/admin/audit-log` | `admin_audit_log` | `app.py:14193` |
| GET | `/admin/backup/database` | `admin_database_backup` | `app.py:7200` |
| GET | `/admin/backup/database.zip` | `admin_database_backup_zip` | `app.py:7158` |
| GET | `/admin/diag/execution-record/<record_id>` | `admin_diag_execution_record` | `app.py:18900` |
| POST | `/admin/export-policy/toggle` | `admin_toggle_export_policy` | `app.py:6606` |
| GET, POST | `/admin/forms/<form_name>/edit` | `form_guide_edit` | `app.py:10302` |
| GET, POST | `/admin/forms/new` | `form_guide_new` | `app.py:10275` |
| GET | `/admin/hosted-bootstrap-admin` | `hosted_bootstrap_admin` | `app.py:14474` |
| GET, POST | `/admin/learning/article/<article_id>/edit` | `learning_article_edit` | `app.py:10247` |
| GET, POST | `/admin/learning/article/new` | `learning_article_new` | `app.py:10218` |
| GET | `/admin/repair/int-lifecycle-tables` | `admin_repair_int_lifecycle_tables` | `app.py:18964` |
| GET | `/admin/reset_admin_once` | `reset_admin_once` | `app.py:14337` |
| GET | `/admin/run-hosted-firm-scope-migration` | `run_hosted_firm_scope_migration` | `app.py:14435` |
| POST | `/admin/seed-hosted-baseline` | `seed_hosted_baseline_route` | `app.py:6642` |
| GET | `/admin/storage-diagnostics` | `admin_storage_diagnostics` | `app.py:7124` |
| GET | `/asset` | `asset_dashboard` | `app.py:2895` |
| GET | `/asset` | `asset_dashboard` | `package_export/app.py:146` |
| GET | `/asset_health` | `asset_health` | `app.py:2914` |
| GET | `/asset_health` | `asset_health` | `package_export/app.py:165` |
| GET | `/assets` | `asset_dashboard` | `app.py:2895` |
| GET | `/assets` | `asset_dashboard` | `package_export/app.py:146` |
| GET | `/audit` | `audit_dashboard` | `app.py:7995` |
| GET, POST | `/bootstrap_admin_once` | `bootstrap_admin_once` | `app.py:14289` |
| GET | `/certificates` | `certificate_registry` | `app.py:7964` |
| POST | `/certificates/backfill` | `backfill_certificate_ids_route` | `app.py:7887` |
| GET | `/certificates/verify/<certificate_id>` | `verify_certificate` | `app.py:7857` |
| GET, POST | `/change_password` | `change_password` | `app.py:14390` |
| GET | `/command` | `command_dashboard` | `app.py:2840` |
| GET | `/command` | `command_dashboard` | `package_export/app.py:91` |
| GET | `/continuity-assets` | `continuity_asset_dashboard` | `app.py:3650` |
| GET | `/continuity-assets/pdf` | `continuity_asset_dashboard_pdf` | `app.py:3631` |
| GET | `/create-trust-launch` | `create_trust_launch` | `app.py:2934` |
| GET, POST | `/create_trust_step1` | `create_trust_step1` | `app.py:2940` |
| GET, POST | `/create_trust_step1` | `create_trust_step1` | `package_export/app.py:184` |
| GET, POST | `/create_trust_step2/<trust_id>` | `create_trust_step2` | `app.py:3003` |
| GET, POST | `/create_trust_step2/<trust_id>` | `create_trust_step2` | `package_export/app.py:216` |
| GET, POST | `/create_trust_step2_grantor/<trust_id>` | `create_trust_step2_grantor` | `app.py:2981` |
| GET, POST | `/create_trust_step3/<trust_id>` | `create_trust_step3` | `app.py:3023` |
| GET, POST | `/create_trust_step3/<trust_id>` | `create_trust_step3` | `package_export/app.py:232` |
| GET, POST | `/create_trust_step4/<trust_id>` | `create_trust_step4` | `app.py:3043` |
| GET, POST | `/create_trust_step4/<trust_id>` | `create_trust_step4` | `package_export/app.py:248` |
| GET, POST | `/create_trust_step5/<trust_id>` | `create_trust_step5` | `app.py:3063` |
| GET, POST | `/create_trust_step5/<trust_id>` | `create_trust_step5` | `package_export/app.py:264` |
| GET, POST | `/create_trust_step6/<trust_id>` | `create_trust_step6` | `app.py:3083` |
| GET, POST | `/create_trust_step6/<trust_id>` | `create_trust_step6` | `package_export/app.py:280` |
| GET | `/create_trust_step7/<trust_id>` | `create_trust_step7` | `app.py:3096` |
| GET | `/create_trust_step7/<trust_id>` | `create_trust_step7` | `package_export/app.py:290` |
| GET | `/decision` | `decision_dashboard` | `app.py:10649` |
| POST | `/decision/run` | `decision_run` | `app.py:10681` |
| GET | `/discussions` | `discussion_dashboard` | `app.py:10522` |
| GET | `/discussions/<thread_id>` | `discussion_thread` | `app.py:10557` |
| GET, POST | `/discussions/<thread_id>/reply` | `discussion_reply` | `app.py:10574` |
| GET, POST | `/discussions/new` | `discussion_new` | `app.py:10528` |
| GET | `/documents` | `document_dashboard` | `app.py:10881` |
| GET | `/documents/<document_id>` | `document_detail` | `app.py:10953` |
| GET, POST | `/documents/generate` | `document_generate` | `app.py:10888` |
| GET, POST | `/docx-export/<workspace_id>` | `controlled_docx_export` | `app.py:16567` |
| GET | `/docx-export/download/<export_id>` | `download_controlled_docx_export` | `app.py:16762` |
| GET, POST | `/docx-verify/<export_id>` | `docx_verification_gate` | `app.py:16809` |
| GET, POST | `/draft-bind/<workspace_id>` | `draft_variable_binding` | `app.py:16011` |
| GET, POST | `/draft-launch/<intake_id>` | `launch_draft_session` | `app.py:15766` |
| GET, POST | `/draft-preview/<workspace_id>` | `dynamic_draft_preview` | `app.py:16128` |
| GET | `/evidence/<entity_type>/<entity_id>` | `evidence_by_entity` | `app.py:9444` |
| GET | `/execution` | `execution_dashboard` | `app.py:10728` |
| GET, POST | `/execution-event/<packet_id>` | `execution_event_log` | `app.py:17502` |
| GET, POST | `/execution-packet/<pdf_export_id>` | `execution_packet_prep` | `app.py:17334` |
| GET | `/execution/tasks/<task_id>` | `execution_task_detail` | `app.py:10783` |
| POST | `/execution/tasks/<task_id>/status` | `execution_task_status` | `app.py:10799` |
| GET, POST | `/execution/tasks/new` | `execution_task_new` | `app.py:10734` |
| GET, POST | `/execution/transfers/<transfer_id>/archive-handoff` | `transfer_archive_handoff` | `app.py:13921` |
| GET | `/execution/transfers/<transfer_id>/archive-handoff/<handoff_id>` | `transfer_archive_handoff_detail` | `app.py:13038` |
| GET, POST | `/execution/transfers/<transfer_id>/archive-handoff/<handoff_id>/correction` | `transfer_archive_handoff_correction` | `app.py:12932` |
| GET | `/execution/transfers/<transfer_id>/archive-handoff/<handoff_id>/correction/<correction_id>` | `transfer_archive_handoff_correction_detail` | `app.py:12872` |
| GET | `/execution/transfers/<transfer_id>/archive-handoff/audit-trail` | `transfer_archive_handoff_audit_trail` | `app.py:13815` |
| GET | `/execution/transfers/<transfer_id>/archive-handoff/audit-trail/export.pdf` | `transfer_archive_handoff_audit_export_pdf` | `app.py:13452` |
| GET | `/execution/transfers/<transfer_id>/archive-handoff/audit-trail/export.txt` | `transfer_archive_handoff_audit_export_txt` | `app.py:13634` |
| GET | `/execution/transfers/<transfer_id>/archive-handoff/export-package.zip` | `transfer_archive_handoff_export_package` | `app.py:13101` |
| GET, POST | `/execution/transfers/<transfer_id>/asset` | `transfer_asset` | `app.py:12228` |
| GET, POST | `/execution/transfers/<transfer_id>/assignment` | `transfer_assignment` | `app.py:12322` |
| GET | `/execution/transfers/<transfer_id>/bank-support-docs` | `transfer_bank_support_docs` | `app.py:12736` |
| GET, POST | `/execution/transfers/<transfer_id>/classification` | `transfer_classification` | `app.py:12277` |
| GET, POST | `/execution/transfers/<transfer_id>/control_evidence` | `transfer_control_evidence` | `app.py:12427` |
| GET | `/execution/transfers/<transfer_id>/detail` | `transfer_detail` | `app.py:14070` |
| GET | `/execution/transfers/<transfer_id>/document-support-docs` | `transfer_document_support_docs` | `app.py:12712` |
| GET, POST | `/execution/transfers/<transfer_id>/external-tracking` | `transfer_external_tracking` | `app.py:12836` |
| GET | `/execution/transfers/<transfer_id>/instructions` | `transfer_instruction_template` | `app.py:12795` |
| GET | `/execution/transfers/<transfer_id>/optional-support-docs` | `transfer_optional_support_docs` | `app.py:12760` |
| GET | `/execution/transfers/<transfer_id>/personal-property-support-docs` | `transfer_personal_property_support_docs` | `app.py:12724` |
| GET | `/execution/transfers/<transfer_id>/print` | `transfer_print_view` | `app.py:14152` |
| GET | `/execution/transfers/<transfer_id>/recommended-support-docs` | `transfer_recommended_support_docs` | `app.py:12748` |
| GET, POST | `/execution/transfers/<transfer_id>/records` | `transfer_records` | `app.py:12473` |
| GET, POST | `/execution/transfers/<transfer_id>/review` | `transfer_review` | `app.py:12530` |
| GET, POST | `/execution/transfers/<transfer_id>/support-docs/<int:support_doc_id>/edit` | `transfer_support_doc_edit` | `app.py:12807` |
| GET | `/execution/transfers/<transfer_id>/template-center` | `transfer_template_center` | `app.py:12772` |
| GET, POST | `/execution/transfers/<transfer_id>/trustee_acceptance` | `transfer_trustee_acceptance` | `app.py:12381` |
| GET, POST | `/export-prep/<workspace_id>` | `controlled_export_prep` | `app.py:16423` |
| GET | `/exports` | `export_center` | `app.py:6928` |
| GET | `/exports/1041/<trust_id>.txt` | `export_1041_text` | `app.py:7011` |
| GET | `/exports/1041_summary/<trust_id>.txt` | `export_1041_summary_report` | `app.py:8178` |
| GET | `/exports/handoff/<filename>` | `export_handoff_file` | `app.py:6950` |
| GET | `/exports/k1/<trust_id>.csv` | `export_k1_live_csv` | `app.py:6986` |
| GET | `/exports/k1_summary/<trust_id>.txt` | `export_k1_summary_report` | `app.py:8137` |
| GET | `/exports/package/<filename>` | `export_package_file` | `app.py:6968` |
| GET | `/exports/roadmap/<filename>` | `export_roadmap_file` | `app.py:6959` |
| GET | `/exports/zip` | `export_zip_snapshot` | `app.py:6977` |
| GET | `/fiduciaries` | `fiduciary_dashboard` | `app.py:8244` |
| GET, POST | `/fiduciaries/new` | `fiduciary_new` | `app.py:8252` |
| GET, POST | `/final-archive/<event_id>` | `final_record_archive_gate` | `app.py:17692` |
| GET | `/financial_summary` | `financial_summary` | `app.py:2845` |
| GET | `/financial_summary` | `financial_summary` | `package_export/app.py:96` |
| GET | `/form1041` | `form1041_dashboard` | `app.py:6396` |
| GET | `/form1041` | `form1041_dashboard` | `package_export/app.py:520` |
| GET | `/form1041/preview/<trust_id>` | `form1041_preview` | `app.py:6451` |
| GET | `/form1041/preview/<trust_id>` | `form1041_preview` | `package_export/app.py:543` |
| GET | `/form1041/print/<trust_id>` | `form1041_print` | `app.py:6458` |
| GET | `/form1041/print/<trust_id>` | `form1041_print` | `package_export/app.py:550` |
| GET | `/forms` | `forms_dashboard` | `app.py:10204` |
| GET | `/forms/name/<form_name>` | `form_guide_detail` | `app.py:10211` |
| GET | `/genealogy` | `genealogy_dashboard` | `app.py:8280` |
| GET, POST | `/genealogy/new` | `genealogy_new` | `app.py:8288` |
| GET | `/guide` | `guide_page` | `app.py:14216` |
| GET, POST | `/guided-draft/<draft_session_id>` | `guided_draft_workspace` | `app.py:15865` |
| GET | `/hosted-auth-diagnostic-once` | `hosted_auth_diagnostic_once` | `app.py:14702` |
| GET | `/hosted-bootstrap-admin-once` | `hosted_bootstrap_admin_once` | `app.py:14556` |
| GET | `/hosted-clear-login-lockout-once` | `hosted_clear_login_lockout_once` | `app.py:14687` |
| GET | `/hosted-firm-scope-migration-once` | `hosted_firm_scope_migration_once` | `app.py:14638` |
| GET | `/hosted-production-health` | `hosted_production_health` | `app.py:9996` |
| GET | `/hosted-repair-admin-access-once` | `hosted_repair_admin_access_once` | `app.py:14760` |
| GET | `/hosted-reseed-permissions-once` | `hosted_reseed_permissions_once` | `app.py:14673` |
| GET | `/hosted-trust-diagnostic-once` | `hosted_trust_diagnostic_once` | `app.py:15003` |
| GET | `/instruments` | `instruments_dashboard` | `app.py:6465` |
| GET | `/instruments` | `instruments_dashboard` | `package_export/app.py:557` |
| GET, POST | `/instruments/<instrument_id>` | `instrument_detail` | `app.py:6518` |
| GET, POST | `/instruments/<instrument_id>` | `instrument_detail` | `package_export/app.py:607` |
| GET, POST | `/instruments/new` | `instrument_create` | `app.py:6489` |
| GET, POST | `/instruments/new` | `instrument_create` | `package_export/app.py:581` |
| GET | `/instruments/print/<instrument_id>` | `instrument_print` | `app.py:6585` |
| GET | `/instruments/print/<instrument_id>` | `instrument_print` | `package_export/app.py:638` |
| GET, POST | `/intake` | `intake_start` | `app.py:15248` |
| GET | `/intake/<intake_id>/draft-readiness` | `intake_draft_readiness_ledger_detail` | `app.py:18264` |
| GET | `/intake/<intake_id>/export-prep` | `intake_export_prep` | `app.py:17905` |
| GET | `/intake/<intake_id>/exports` | `intake_export_history_detail` | `app.py:18034` |
| GET | `/intake/<intake_id>/final-draft-approvals` | `intake_final_draft_admin_approval_ledger_detail` | `app.py:18605` |
| GET | `/intake/<intake_id>/final-draft-gate` | `intake_final_draft_gate_ledger_detail` | `app.py:18453` |
| GET | `/intake/<intake_id>/final-draft-version-register` | `intake_final_draft_version_register_intake` | `app.py:18723` |
| POST | `/intake/<intake_id>/notes/add` | `intake_add_review_note` | `app.py:17921` |
| GET | `/intake/<intake_id>/packet` | `intake_followup_packet` | `app.py:17974` |
| GET | `/intake/<intake_id>/packet/docx` | `intake_followup_packet_docx` | `app.py:17991` |
| GET | `/intake/<intake_id>/packet/pdf` | `intake_followup_packet_pdf` | `app.py:18005` |
| GET | `/intake/<intake_id>/recommendations` | `intake_document_recommendations` | `app.py:18060` |
| GET, POST | `/intake/<intake_id>/recommendations/<workflow_key>/bridge` | `intake_workflow_bridge` | `app.py:18122` |
| GET | `/intake/<intake_id>/recommendations/<workflow_key>/bridge-summary` | `intake_workflow_bridge_summary` | `app.py:18204` |
| GET | `/intake/<intake_id>/recommendations/<workflow_key>/document-draft` | `intake_document_draft_choose` | `app.py:18274` |
| GET, POST | `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>` | `intake_document_draft_questionnaire` | `app.py:18292` |
| GET, POST | `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/admin-approval` | `intake_final_draft_admin_approval` | `app.py:18562` |
| GET, POST | `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-completion-gate` | `intake_final_draft_completion_gate` | `app.py:18745` |
| GET | `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate` | `intake_final_draft_gate_detail` | `app.py:18475` |
| POST | `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate/approve` | `intake_final_draft_gate_approve` | `app.py:18496` |
| GET, POST | `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate/resolve` | `intake_final_draft_gate_resolution` | `app.py:18517` |
| GET | `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-preview` | `intake_final_draft_preview` | `app.py:18683` |
| GET | `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-preview/docx` | `intake_final_draft_preview_docx` | `app.py:18693` |
| GET | `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-version-register` | `intake_final_draft_version_register_detail` | `app.py:18732` |
| GET | `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-workspace` | `intake_final_draft_workspace` | `app.py:18616` |
| GET | `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-section-editor` | `intake_final_draft_section_editor` | `app.py:18630` |
| GET, POST | `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-section-editor/<int:section_id>` | `intake_final_draft_section_edit` | `app.py:18641` |
| GET | `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/nonfinal` | `intake_nonfinal_draft_document` | `app.py:18345` |
| GET | `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/nonfinal/docx` | `intake_nonfinal_draft_docx` | `app.py:18372` |
| GET | `/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/preview` | `intake_document_draft_preview` | `app.py:18331` |
| GET | `/intake/<intake_id>/recommendations/<workflow_key>/draft-packet` | `intake_workflow_draft_packet` | `app.py:18218` |
| GET | `/intake/<intake_id>/recommendations/<workflow_key>/draft-packet/docx` | `intake_workflow_draft_packet_docx` | `app.py:18239` |
| GET | `/intake/<intake_id>/recommendations/<workflow_key>/instrument-draft-packet` | `intake_instrument_draft_packet` | `app.py:18788` |
| GET | `/intake/<intake_id>/recommendations/<workflow_key>/launch-prep` | `intake_workflow_launch_prep` | `app.py:18101` |
| POST | `/intake/<intake_id>/recommendations/<workflow_key>/status` | `intake_update_recommendation_status` | `app.py:18085` |
| GET | `/intake/<intake_id>/resume` | `intake_resume` | `app.py:17891` |
| GET | `/intake/<intake_id>/review-gates` | `intake_review_gate_ledger_detail` | `app.py:18403` |
| GET | `/intake/<intake_id>/review-gates/<workflow_key>/<document_key>` | `intake_review_gate_detail` | `app.py:18413` |
| POST | `/intake/<intake_id>/review-gates/<workflow_key>/<document_key>/resolve` | `intake_review_gate_resolve` | `app.py:18431` |
| GET | `/intake/<intake_id>/snapshot` | `intake_saved_snapshot` | `app.py:17858` |
| POST | `/intake/<intake_id>/tasks/<int:task_id>/status` | `intake_update_followup_task_status` | `app.py:17959` |
| POST | `/intake/<intake_id>/tasks/add` | `intake_add_followup_task` | `app.py:17939` |
| GET | `/intake/<intake_id>/trust-instruments` | `intake_trust_instrument_menu` | `app.py:18778` |
| GET, POST | `/intake/<intake_id>/universal-profile` | `intake_universal_profile` | `app.py:15273` |
| GET, POST | `/intake/assets/<intake_id>` | `asset_intake` | `app.py:15334` |
| GET | `/intake/dashboard` | `intake_dashboard` | `app.py:17850` |
| GET, POST | `/intake/deep-review/<intake_id>` | `intake_deep_review` | `app.py:15579` |
| GET, POST | `/intake/documents/<intake_id>` | `document_intake` | `app.py:15443` |
| GET | `/intake/draft-readiness` | `intake_draft_readiness_ledger` | `app.py:18254` |
| GET, POST | `/intake/drafting-prep/<intake_id>` | `intake_drafting_prep` | `app.py:15671` |
| GET | `/intake/exports` | `intake_export_history` | `app.py:18022` |
| GET | `/intake/final-draft-approvals` | `intake_final_draft_admin_approval_ledger` | `app.py:18595` |
| GET | `/intake/final-draft-gate` | `intake_final_draft_gate_ledger` | `app.py:18464` |
| GET | `/intake/final-draft-version-register` | `intake_final_draft_version_register_all` | `app.py:18714` |
| GET, POST | `/intake/identity` | `identity_intake` | `app.py:18804` |
| GET | `/intake/identity/<intake_id>` | `identity_intake_summary` | `app.py:18864` |
| GET | `/intake/modules` | `intake_module_ledger` | `app.py:18045` |
| GET | `/intake/readiness/<intake_id>` | `intake_readiness_review` | `app.py:15545` |
| GET | `/intake/review-gates` | `intake_review_gate_ledger` | `app.py:18393` |
| GET, POST | `/intake/start` | `intake_start` | `app.py:15248` |
| GET | `/k1` | `k1_dashboard` | `app.py:6240` |
| GET | `/k1` | `k1_dashboard` | `package_export/app.py:448` |
| GET | `/k1` | `k1_home` | `routes_k1.py:14` |
| GET | `/k1/trust/<int:trust_id>` | `k1_trust_view` | `routes_k1.py:20` |
| GET, POST | `/k1/trust/<int:trust_id>/beneficiary/new` | `new_beneficiary` | `routes_k1.py:50` |
| GET, POST | `/k1/trust/<int:trust_id>/distribution/new` | `new_distribution` | `routes_k1.py:97` |
| GET | `/k1/trust/<int:trust_id>/export.csv` | `export_k1_csv` | `routes_k1.py:155` |
| GET | `/k1/trust/<int:trust_id>/year_end_summary` | `year_end_summary` | `routes_k1.py:167` |
| GET | `/k1/trust/<trust_id>` | `k1_trust_view` | `app.py:6245` |
| GET | `/k1/trust/<trust_id>` | `k1_trust_view` | `package_export/app.py:453` |
| GET, POST | `/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/edit` | `k1_edit_beneficiary` | `app.py:8026` |
| GET, POST | `/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/edit` | `k1_edit_beneficiary` | `package_export/app.py:666` |
| POST | `/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/toggle` | `k1_toggle_beneficiary` | `app.py:8065` |
| POST | `/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/toggle` | `k1_toggle_beneficiary` | `package_export/app.py:688` |
| GET, POST | `/k1/trust/<trust_id>/beneficiary/new` | `k1_new_beneficiary` | `app.py:6279` |
| GET, POST | `/k1/trust/<trust_id>/beneficiary/new` | `k1_new_beneficiary` | `package_export/app.py:470` |
| GET, POST | `/k1/trust/<trust_id>/distribution/<distribution_id>/edit` | `k1_edit_distribution` | `app.py:8074` |
| GET, POST | `/k1/trust/<trust_id>/distribution/<distribution_id>/edit` | `k1_edit_distribution` | `package_export/app.py:694` |
| GET, POST | `/k1/trust/<trust_id>/distribution/new` | `k1_new_distribution` | `app.py:6328` |
| GET, POST | `/k1/trust/<trust_id>/distribution/new` | `k1_new_distribution` | `package_export/app.py:490` |
| GET | `/k1/trust/<trust_id>/export.csv` | `k1_export_csv` | `app.py:8122` |
| GET | `/k1/trust/<trust_id>/export.csv` | `k1_export_csv` | `package_export/app.py:723` |
| GET | `/k1/trust/<trust_id>/year_end_summary` | `k1_year_end_summary` | `app.py:6388` |
| GET | `/k1/trust/<trust_id>/year_end_summary` | `k1_year_end_summary` | `package_export/app.py:512` |
| GET | `/learning` | `learning_dashboard` | `app.py:10159` |
| GET | `/learning/article/<article_id>` | `learning_article` | `app.py:10182` |
| GET | `/learning/category/<category>` | `learning_category` | `app.py:10172` |
| GET | `/learning/trust-type/<slug>` | `trust_type_detail` | `app.py:10196` |
| GET | `/learning/trust-types` | `trust_type_index` | `app.py:10190` |
| GET, POST | `/ledger_entry` | `ledger_entry` | `app.py:3206` |
| GET, POST | `/ledger_entry` | `ledger_entry` | `package_export/app.py:380` |
| GET | `/lifecycle-ledger/<intake_id>` | `lifecycle_master_ledger` | `app.py:17828` |
| GET, POST | `/link_account` | `link_account` | `app.py:3134` |
| GET, POST | `/link_account` | `link_account` | `package_export/app.py:325` |
| GET, POST | `/login` | `login` | `app.py:14220` |
| GET | `/logout` | `logout` | `app.py:14283` |
| GET | `/matters` | `matters_dashboard` | `app.py:19045` |
| GET | `/matters/<matter_id>` | `matter_detail` | `app.py:19115` |
| GET, POST | `/matters/<matter_id>/events/new` | `new_matter_event` | `app.py:19459` |
| POST | `/matters/<matter_id>/governance` | `matter_governance_state` | `app.py:19063` |
| GET | `/matters/<matter_id>/relationships/<relationship_id>` | `matter_relationship_detail` | `app.py:19130` |
| POST | `/matters/<matter_id>/relationships/<relationship_id>/clearance` | `matter_relationship_clearance` | `app.py:19212` |
| POST | `/matters/<matter_id>/relationships/<relationship_id>/relink` | `matter_relationship_relink` | `app.py:19254` |
| POST | `/matters/<matter_id>/relationships/<relationship_id>/status` | `matter_relationship_status_update` | `app.py:19388` |
| POST | `/matters/<matter_id>/relationships/<relationship_id>/validate-link` | `matter_relationship_validate_link` | `app.py:19301` |
| POST | `/matters/<matter_id>/relationships/<relationship_id>/verification` | `matter_relationship_verification_update` | `app.py:19340` |
| GET, POST | `/matters/<matter_id>/relationships/new` | `new_matter_relationship` | `app.py:19419` |
| POST | `/matters/<matter_id>/risk` | `matter_risk_update` | `app.py:19091` |
| GET, POST | `/matters/new` | `new_matter` | `app.py:19052` |
| GET | `/media` | `media_dashboard` | `app.py:9363` |
| GET | `/media/file/<media_id>` | `media_file` | `app.py:9415` |
| GET, POST | `/media/upload` | `media_upload` | `app.py:9370` |
| GET | `/minutes` | `trust_minutes_dashboard` | `app.py:7842` |
| GET | `/minutes/<minute_id>` | `trust_minute_detail` | `app.py:7819` |
| GET | `/minutes/<minute_id>/certificate.pdf` | `trust_minute_certificate_pdf` | `app.py:7472` |
| POST | `/minutes/<minute_id>/execute` | `trust_minute_execute` | `app.py:7697` |
| GET | `/minutes/<minute_id>/packet.pdf` | `trust_minute_execution_packet_pdf` | `app.py:7550` |
| GET, POST | `/minutes/new` | `trust_minutes_new` | `app.py:7392` |
| GET, POST | `/pdf-convert/<export_id>` | `controlled_pdf_conversion` | `app.py:16945` |
| GET, POST | `/pdf-execution-approval/<pdf_export_id>` | `pdf_execution_approval_gate` | `app.py:17193` |
| GET | `/pdf-export/download/<pdf_export_id>` | `download_controlled_pdf_export` | `app.py:17146` |
| GET, POST | `/permissions` | `permissions_dashboard` | `app.py:9631` |
| GET | `/portfolio` | `portfolio_dashboard` | `app.py:8222` |
| GET | `/property/<property_id>` | `property_detail` | `app.py:3368` |
| GET | `/property/<property_id>` | `property_detail` | `package_export/app.py:428` |
| GET | `/property/<property_id>/ac1-completion-report/pdf` | `property_ac1_completion_report_pdf` | `app.py:5953` |
| GET | `/property/<property_id>/archive-packet` | `property_archive_packet` | `app.py:5930` |
| GET | `/property/<property_id>/archive-packet/finalization-certificate/pdf` | `property_archive_finalization_certificate_pdf` | `app.py:5718` |
| GET | `/property/<property_id>/archive-packet/finalization-history/pdf` | `property_archive_finalization_history_pdf` | `app.py:5680` |
| GET, POST | `/property/<property_id>/archive-packet/finalize` | `property_archive_packet_finalize` | `app.py:5753` |
| GET | `/property/<property_id>/archive-packet/integrity` | `property_archive_packet_integrity` | `app.py:5816` |
| GET | `/property/<property_id>/archive-packet/integrity/pdf` | `property_archive_packet_integrity_pdf` | `app.py:5843` |
| GET | `/property/<property_id>/archive-packet/manifest/pdf` | `property_archive_packet_manifest_pdf` | `app.py:5903` |
| GET | `/property/<property_id>/archive-packet/zip` | `property_archive_packet_zip` | `app.py:5876` |
| GET, POST | `/property/<property_id>/continuity` | `property_continuity_profile` | `app.py:6196` |
| GET | `/property/<property_id>/continuity/pdf` | `property_continuity_profile_pdf` | `app.py:3886` |
| GET, POST | `/property/<property_id>/custody-log` | `property_custody_log` | `app.py:6136` |
| GET, POST | `/property/<property_id>/custody-log/<custody_event_id>/resolve` | `resolve_custody_event_evidence` | `app.py:6073` |
| GET | `/property/<property_id>/custody-log/pdf` | `property_custody_log_pdf` | `app.py:4089` |
| GET | `/property/<property_id>/resolution-queue` | `property_resolution_queue` | `app.py:5978` |
| GET | `/property/<property_id>/resolution-queue/pdf` | `property_resolution_queue_pdf` | `app.py:4539` |
| GET | `/property/<property_id>/timeline` | `property_evidence_custody_timeline` | `app.py:5999` |
| GET | `/property/<property_id>/timeline/pdf` | `property_evidence_custody_timeline_pdf` | `app.py:4309` |
| GET, POST | `/reports` | `report_center` | `app.py:10076` |
| GET | `/reports/1041/<trust_id>` | `form1041_report_view` | `app.py:9487` |
| GET | `/reports/1041/<trust_id>/print` | `form1041_report_print` | `app.py:9594` |
| GET | `/reports/1041/trust/<trust_id>/<tax_year>.pdf` | `form1041_report_pdf` | `app.py:9957` |
| GET | `/reports/audit.pdf` | `audit_log_report_pdf` | `app.py:10146` |
| GET | `/reports/fiduciaries.pdf` | `fiduciary_report_pdf` | `app.py:9937` |
| GET | `/reports/instrument/<instrument_id>.pdf` | `instrument_detail_pdf` | `app.py:9977` |
| GET | `/reports/k1/<trust_id>` | `k1_report_view` | `app.py:9457` |
| GET | `/reports/k1/<trust_id>/print` | `k1_report_print` | `app.py:9562` |
| GET | `/reports/k1/trust/<trust_id>/<tax_year>.pdf` | `k1_readiness_pdf` | `app.py:9914` |
| GET | `/reports/ledger/trust/<trust_id>.pdf` | `ledger_report_pdf` | `app.py:9947` |
| GET | `/reports/portfolio.pdf` | `portfolio_report_pdf` | `app.py:10138` |
| GET | `/reports/trust/<trust_id>/summary.pdf` | `trust_summary_pdf` | `app.py:9897` |
| GET | `/resume` | `resume_process` | `app.py:14372` |
| GET | `/roles` | `role_dashboard` | `app.py:9522` |
| GET, POST | `/roles/new` | `role_new` | `app.py:9533` |
| GET, POST | `/section-review/<workspace_id>` | `section_review_gate` | `app.py:16294` |
| GET | `/security` | `security_dashboard` | `app.py:9680` |
| GET | `/system/health` | `system_health_dashboard` | `app.py:7978` |
| GET | `/system/health/export.json` | `system_health_export_json` | `app.py:7304` |
| GET | `/system/health/export.txt` | `system_health_export_txt` | `app.py:7334` |
| GET | `/system/health/export.zip` | `system_health_export_zip` | `app.py:7237` |
| POST | `/system/recovery/reseed-permissions` | `system_recovery_reseed_permissions` | `app.py:7073` |
| POST | `/system/recovery/run` | `system_recovery_run` | `app.py:7095` |
| GET | `/tax_assistant` | `tax_assistant` | `app.py:2868` |
| GET | `/tax_assistant` | `tax_assistant` | `package_export/app.py:119` |
| GET | `/transfers/<transfer_id>/certificate.pdf` | `transfer_certificate_pdf` | `app.py:7916` |
| GET | `/trust/<trust_id>` | `trust_detail` | `app.py:3345` |
| GET | `/trust/<trust_id>` | `trust_detail` | `package_export/app.py:408` |
| GET, POST | `/trust/<trust_id>/accounting-method` | `trust_accounting_method_settings` | `app.py:11402` |
| GET | `/trust/<trust_id>/archive-handoff/export-index` | `archive_handoff_export_index` | `app.py:11672` |
| GET | `/trust/<trust_id>/archive-handoff/export-index/export.csv` | `archive_handoff_export_index_csv` | `app.py:11436` |
| GET | `/trust/<trust_id>/article-assignments` | `trust_article_assignments` | `app.py:15180` |
| POST | `/trust/<trust_id>/article-assignments/add` | `trust_article_assignment_add` | `app.py:15211` |
| GET | `/trust/<trust_id>/articles-output-surface` | `trust_articles_output_surface` | `app.py:11370` |
| GET | `/trust/<trust_id>/articles-output-surface/pdf` | `trust_articles_output_surface_pdf` | `app.py:11385` |
| GET | `/trust/<trust_id>/articles-preview` | `trust_articles_preview` | `app.py:11301` |
| GET, POST | `/trust/<trust_id>/branding` | `trust_branding_settings` | `app.py:3272` |
| GET | `/trust/<trust_id>/certificate-of-trust-output-surface` | `trust_certificate_of_trust_output_surface` | `app.py:11342` |
| GET | `/trust/<trust_id>/certificate-of-trust-output-surface/pdf` | `trust_certificate_of_trust_output_surface_pdf` | `app.py:11355` |
| GET | `/trust/<trust_id>/controlled-packet-export` | `trust_controlled_packet_export` | `app.py:11118` |
| GET | `/trust/<trust_id>/declaration-output-surface` | `trust_declaration_output_surface` | `app.py:11314` |
| GET | `/trust/<trust_id>/declaration-output-surface/pdf` | `trust_declaration_output_surface_pdf` | `app.py:11327` |
| GET | `/trust/<trust_id>/dynamic-declaration` | `trust_dynamic_declaration` | `app.py:15056` |
| GET | `/trust/<trust_id>/dynamic-declaration/pdf` | `trust_dynamic_declaration_pdf` | `app.py:15153` |
| GET | `/trust/<trust_id>/execution` | `trust_execution_dashboard` | `app.py:11810` |
| GET, POST | `/trust/<trust_id>/execution/transfers/new` | `transfer_start` | `app.py:12177` |
| GET | `/trust/<trust_id>/formation-preview-hub` | `trust_formation_preview_hub` | `app.py:11059` |
| GET | `/trust/<trust_id>/general-assignment-output-surface` | `trust_general_assignment_output_surface` | `app.py:11188` |
| GET | `/trust/<trust_id>/general-assignment-output-surface/pdf` | `trust_general_assignment_output_surface_pdf` | `app.py:11202` |
| GET | `/trust/<trust_id>/general-assignment-preview` | `trust_general_assignment_preview` | `app.py:11175` |
| GET | `/trust/<trust_id>/organizational-minutes-output-surface` | `trust_organizational_minutes_output_surface` | `app.py:11230` |
| GET | `/trust/<trust_id>/organizational-minutes-output-surface/pdf` | `trust_organizational_minutes_output_surface_pdf` | `app.py:11244` |
| GET | `/trust/<trust_id>/organizational-minutes-preview` | `trust_organizational_minutes_preview` | `app.py:11217` |
| GET | `/trust/<trust_id>/packet-preview` | `trust_packet_preview` | `app.py:11149` |
| GET | `/trust/<trust_id>/post-create-review` | `trust_post_create_review` | `app.py:11051` |
| GET | `/trust/<trust_id>/seal` | `uploaded_seal` | `app.py:3237` |
| GET | `/trust/<trust_id>/successor-trustee-output-surface` | `trust_successor_trustee_output_surface` | `app.py:11089` |
| GET | `/trust/<trust_id>/successor-trustee-output-surface/pdf` | `trust_successor_trustee_output_surface_pdf` | `app.py:11103` |
| GET | `/trust/<trust_id>/successor-trustee-preview` | `trust_successor_trustee_preview` | `app.py:11076` |
| GET | `/trust/<trust_id>/trustee-acceptance-output-surface` | `trust_trustee_acceptance_output_surface` | `app.py:11272` |
| GET | `/trust/<trust_id>/trustee-acceptance-output-surface/pdf` | `trust_trustee_acceptance_output_surface_pdf` | `app.py:11286` |
| GET | `/trust/<trust_id>/trustee-acceptance-preview` | `trust_trustee_acceptance_preview` | `app.py:11259` |
| GET, POST | `/upload_document` | `upload_document` | `app.py:3156` |
| GET, POST | `/upload_document` | `upload_document` | `package_export/app.py:344` |
| GET | `/users` | `users_dashboard` | `app.py:6689` |
| GET, POST | `/users/<username>/edit` | `users_edit` | `app.py:6749` |
| GET, POST | `/users/<username>/reset_password` | `users_reset_password` | `app.py:6813` |
| GET, POST | `/users/new` | `users_new` | `app.py:6698` |
| GET | `/videos` | `video_dashboard` | `app.py:10326` |
| GET | `/videos/<video_id>` | `video_detail` | `app.py:10351` |
| GET, POST | `/videos/<video_id>/edit` | `video_edit` | `app.py:10388` |
| GET | `/videos/category/<category>` | `video_category` | `app.py:10339` |
| GET | `/videos/trust-type/<trust_type>` | `video_trust_type` | `app.py:10345` |
| GET, POST | `/videos/upload` | `video_upload` | `app.py:10359` |
| GET | `/visualization` | `visualization_dashboard` | `app.py:14166` |
| GET | `/visualization/analytics` | `analytics_dashboard` | `app.py:14179` |
| GET | `/visualization/trust-map` | `trust_map_dashboard` | `app.py:14173` |
| GET | `/workflow` | `workflow_hub` | `app.py:6598` |
| GET | `/workflow` | `workflow_hub` | `package_export/app.py:651` |
| GET | `/workspaces` | `workspace_dashboard` | `app.py:10413` |
| GET | `/workspaces/<workspace_id>` | `workspace_detail` | `app.py:10445` |
| GET | `/workspaces/<workspace_id>/discussions` | `workspace_discussions` | `app.py:10609` |
| GET, POST | `/workspaces/<workspace_id>/discussions/new` | `workspace_discussion_new` | `app.py:10618` |
| GET | `/workspaces/<workspace_id>/documents` | `workspace_documents` | `app.py:10970` |
| GET, POST | `/workspaces/<workspace_id>/documents/generate` | `workspace_document_generate` | `app.py:10979` |
| GET, POST | `/workspaces/<workspace_id>/edit` | `workspace_edit` | `app.py:10470` |
| GET, POST | `/workspaces/<workspace_id>/notes/new` | `workspace_note_new` | `app.py:10494` |
| GET | `/workspaces/<workspace_id>/tasks` | `workspace_tasks` | `app.py:10821` |
| GET, POST | `/workspaces/<workspace_id>/tasks/new` | `workspace_task_new` | `app.py:10830` |
| GET, POST | `/workspaces/new` | `workspace_new` | `app.py:10419` |

## Duplicate Route Signatures

- `GET /` appears 2 times
- `GET /command` appears 2 times
- `GET /financial_summary` appears 2 times
- `GET /tax_assistant` appears 2 times
- `GET /assets` appears 2 times
- `GET /asset` appears 2 times
- `GET /asset_health` appears 2 times
- `GET,POST /create_trust_step1` appears 2 times
- `GET,POST /create_trust_step2/<trust_id>` appears 2 times
- `GET,POST /create_trust_step3/<trust_id>` appears 2 times
- `GET,POST /create_trust_step4/<trust_id>` appears 2 times
- `GET,POST /create_trust_step5/<trust_id>` appears 2 times
- `GET,POST /create_trust_step6/<trust_id>` appears 2 times
- `GET /create_trust_step7/<trust_id>` appears 2 times
- `GET,POST /add_property` appears 2 times
- `GET,POST /link_account` appears 2 times
- `GET,POST /upload_document` appears 2 times
- `GET,POST /ledger_entry` appears 2 times
- `GET /trust/<trust_id>` appears 2 times
- `GET /property/<property_id>` appears 2 times
- `GET /k1` appears 3 times
- `GET /k1/trust/<trust_id>` appears 2 times
- `GET,POST /k1/trust/<trust_id>/beneficiary/new` appears 2 times
- `GET,POST /k1/trust/<trust_id>/distribution/new` appears 2 times
- `GET /k1/trust/<trust_id>/year_end_summary` appears 2 times
- `GET /form1041` appears 2 times
- `GET /form1041/preview/<trust_id>` appears 2 times
- `GET /form1041/print/<trust_id>` appears 2 times
- `GET /instruments` appears 2 times
- `GET,POST /instruments/new` appears 2 times
- `GET,POST /instruments/<instrument_id>` appears 2 times
- `GET /instruments/print/<instrument_id>` appears 2 times
- `GET /workflow` appears 2 times
- `GET /admin` appears 2 times
- `GET,POST /k1/trust/<trust_id>/beneficiary/<beneficiary_id>/edit` appears 2 times
- `POST /k1/trust/<trust_id>/beneficiary/<beneficiary_id>/toggle` appears 2 times
- `GET,POST /k1/trust/<trust_id>/distribution/<distribution_id>/edit` appears 2 times
- `GET /k1/trust/<trust_id>/export.csv` appears 2 times

## Database Tables Detected

- `accounts` — `app.py:819`
- `accounts` — `database/db.py:290`
- `accounts` — `package_export/database/db.py:67`
- `app_users` — `app.py:353`
- `app_users` — `app.py:14499`
- `app_users` — `app.py:14581`
- `app_users` — `app.py:14802`
- `app_users` — `database/db.py:2796`
- `archive_export_history` — `database/db.py:4456`
- `archive_packet_finalization` — `migrations/add_archive_packet_finalization.py:10`
- `asset_intake` — `database/db.py:112`
- `audit_log` — `database/db.py:1943`
- `beneficiaries` — `database/db.py:1115`
- `beneficiaries` — `package_export/database/db.py:720`
- `chart_of_accounts` — `database/db.py:337`
- `chart_of_accounts` — `package_export/database/db.py:114`
- `continuity_custody_log` — `migrations/add_continuity_custody_log.py:10`
- `controlled_docx_exports` — `database/db.py:4085`
- `controlled_export_prep` — `database/db.py:4008`
- `controlled_export_prep` — `database/db.py:4047`
- `controlled_pdf_exports` — `database/db.py:4162`
- `distributions` — `database/db.py:1131`
- `distributions` — `package_export/database/db.py:736`
- `document_intake` — `database/db.py:149`
- `documents` — `app.py:868`
- `documents` — `database/db.py:303`
- `documents` — `package_export/database/db.py:80`
- `docx_verification_gate` — `database/db.py:4122`
- `draft_sessions` — `database/db.py:3798`
- `draft_variable_binding` — `database/db.py:4724`
- `draft_variable_bindings` — `database/db.py:3876`
- `draft_variable_bindings` — `database/db.py:3908`
- `dynamic_draft_previews` — `database/db.py:3940`
- `execution_event_log` — `database/db.py:4350`
- `execution_packet_prep` — `database/db.py:4243`
- `execution_packet_prep` — `database/db.py:4296`
- `fiduciaries` — `database/db.py:2339`
- `final_record_archive` — `database/db.py:4410`
- `genealogy_records` — `database/db.py:2424`
- `guided_draft_workspace` — `database/db.py:3833`
- `identity_intake` — `database/db.py:34`
- `instruments` — `database/db.py:1630`
- `instruments` — `database/db.py:1744`
- `instruments` — `package_export/database/db.py:1215`
- `instruments` — `package_export/database/db.py:1326`
- `intake_answers` — `services/services_intake.py:860`
- `intake_deep_review` — `database/db.py:3703`
- `intake_deep_review` — `database/db.py:3734`
- `intake_document_draft_answers` — `services/services_intake.py:6065`
- `intake_document_recommendations` — `services/services_intake.py:3912`
- `intake_draft_readiness_ledger` — `services/services_intake.py:5441`
- `intake_drafting_prep_gate` — `database/db.py:3765`
- `intake_export_logs` — `services/services_intake.py:2919`
- `intake_final_draft_admin_approvals` — `services/services_intake.py:7610`
- `intake_final_draft_completion_actions` — `services/services_intake.py:8646`
- `intake_final_draft_completion_gate` — `services/services_intake.py:8623`
- `intake_final_draft_gate_actions` — `services/services_intake.py:7308`
- `intake_final_draft_prep_gate` — `services/services_intake.py:6936`
- `intake_final_draft_sections` — `services/services_intake.py:7991`
- `intake_final_draft_version_register` — `services/services_intake.py:8415`
- `intake_followup_tasks` — `services/services_intake.py:2226`
- `intake_lane_events` — `services/services_intake.py:98`
- `intake_module_ledger` — `services/services_intake.py:3490`
- `intake_orchestration` — `database/db.py:71`
- `intake_review_gate_actions` — `services/services_intake.py:6725`
- `intake_review_gate_ledger` — `services/services_intake.py:6412`
- `intake_review_notes` — `services/services_intake.py:2030`
- `intake_scores` — `services/services_intake.py:1166`
- `intake_sessions` — `services/services_intake.py:77`
- `intake_snapshots` — `services/services_intake.py:1564`
- `intake_translations` — `services/services_intake.py:873`
- `intake_workflow_bridge_answers` — `services/services_intake.py:5066`
- `ledger_entries` — `app.py:914`
- `ledger_entries` — `database/db.py:318`
- `ledger_entries` — `package_export/database/db.py:95`
- `matter_events` — `services/services_matters.py:30`
- `matter_relationships` — `services/services_matters.py:47`
- `matters` — `services/services_matters.py:9`
- `media_records` — `database/db.py:2536`
- `pdf_execution_approval_gate` — `database/db.py:4202`
- `permissions` — `app.py:410`
- `permissions` — `app.py:14859`
- `permissions` — `database/db.py:2644`
- `permissions` — `database/db.py:3130`
- `properties` — `app.py:770`
- `properties` — `database/db.py:268`
- `properties` — `package_export/database/db.py:45`
- `role_permissions` — `app.py:418`
- `role_permissions` — `app.py:14867`
- `role_permissions` — `database/db.py:2652`
- `role_permissions` — `database/db.py:3138`
- `section_review_gate` — `database/db.py:3971`
- `transfer_archive_handoff` — `database/db.py:4523`
- `transfer_archive_handoff_corrections` — `database/db.py:4486`
- `trust_article_assignments` — `migrations/add_article_registry_tables.py:24`
- `trust_article_conditions` — `migrations/add_article_registry_tables.py:44`
- `trust_articles` — `migrations/add_article_registry_tables.py:10`
- `trust_minutes` — `database/db.py:3233`
- `trust_template_types` — `migrations/add_article_registry_tables.py:35`
- `trusts` — `app.py:573`
- `trusts` — `database/db.py:224`
- `trusts` — `package_export/database/db.py:18`
- `user_permission_overrides` — `database/db.py:2936`
- `user_roles` — `database/db.py:2633`

## Module Presence

### Learning Hub

- Files with matching implementation terms: **60**
  - `app.py` — article, form guide, learning
  - `FULL_SYSTEM_HANDOFF.txt` — article, learning
  - `HOSTED_SMOKE_TEST_CHECKLIST.md` — article
  - `OPERATOR_RUNBOOK_V1.txt` — learning
  - `PHASE9_TRACK_C_STATUS.txt` — article, form guide, learning
  - `QA_CHECKLIST_V1.txt` — article, form guide, learning
  - `RELEASE_CHECKLIST.md` — article
  - `RELEASE_READINESS_V1.txt` — learning
  - `ROLE_ACCESS_MATRIX_V1.txt` — learning
  - `ROUTE_TEST_MATRIX_V1.txt` — article, learning
  - `SMOKE_TEST_ORDER_V1.txt` — learning
  - `VERSION_SUMMARY_V1.txt` — learning
  - `docs/POST_CREATE_CONSOLE_CHECKPOINT.md` — article
  - `handoff/FINAL_STABILIZATION_SUMMARY.txt` — lesson
  - `handoff/MODULE_STATUS.txt` — lesson
  - `handoff/NAV_EXPOSURE_MATRIX.md` — learning
  - `handoff/PHASE_7A_VIEWER_NAV_CLOSEOUT_NOTE.md` — learning
  - `handoff/PROJECT_CONTINUITY_SUPERSEDING_NOTE.md` — learning
  - `handoff/ROLE_PERMISSION_MATRIX.md` — learning
  - `handoff/ROUTE_INTENT_MATRIX.md` — learning
  - …and 40 more files

### Genealogy

- Files with matching implementation terms: **21**
  - `app.py` — ancestor, genealogy, lineage, memorial
  - `database/db.py` — genealogy, lineage
  - `handoff/MEDIA_EVIDENCE_PHASE_NOTE.txt` — genealogy
  - `handoff/NAV_EXPOSURE_MATRIX.md` — genealogy
  - `handoff/PHASE_11_GENEALOGY_CLOSEOUT_NOTE.md` — genealogy, lineage
  - `handoff/PHASE_12_DEPLOYMENT_BLOCKER_NOTE.md` — genealogy
  - `handoff/PHASE_7A_VIEWER_NAV_CLOSEOUT_NOTE.md` — genealogy
  - `handoff/PROJECT_CONTINUITY_SUPERSEDING_NOTE.md` — genealogy
  - `handoff/ROLE_PERMISSION_MATRIX.md` — genealogy
  - `handoff/ROUTE_INTENT_MATRIX.md` — genealogy
  - `migrations/add_continuity_asset_fields.py` — lineage, memorial
  - `services/services_continuity_assets.py` — lineage, memorial
  - `services/services_intake.py` — heirloom
  - `templates/continuity_asset_dashboard.html` — lineage, memorial
  - `templates/genealogy_dashboard.html` — genealogy, lineage
  - `templates/genealogy_form.html` — genealogy, lineage
  - `templates/guide_page.html` — genealogy, lineage
  - `templates/property_continuity_profile.html` — lineage, memorial
  - `templates/property_custody_log.html` — lineage, memorial
  - `templates/property_detail.html` — lineage, memorial
  - …and 1 more files

### Intake

- Files with matching implementation terms: **116**
  - `app.py` — assessment, intake, questionnaire, readiness
  - `FULL_SYSTEM_HANDOFF.txt` — readiness
  - `HOSTED_SMOKE_TEST_CHECKLIST.md` — readiness
  - `pdf_utils.py` — readiness
  - `QA_CHECKLIST_V1.txt` — readiness
  - `RELEASE_READINESS_V1.txt` — readiness
  - `REPORT_SUBSYSTEM_HANDOFF.txt` — readiness
  - `routes_k1.py` — readiness
  - `backups_sqlite_change_history/k1_readiness.html` — readiness
  - `database/db.py` — intake, readiness
  - `docs/BUILD_DOCTRINE.md` — readiness
  - `docs/EXECUTION_HANDOFF_CHECKPOINT.md` — readiness
  - `docs/FORM_1041_ENGINE_PHASE_START.md` — readiness
  - `docs/K1_ENGINE_SAFE_BUILD_INTENT.md` — readiness
  - `docs/POST_CREATE_CONSOLE_CHECKPOINT.md` — readiness
  - `docs/TAX_ASSISTANT_PHASE1_COMPLETE.md` — readiness
  - `docs/WIZARD_PROGRESS_STEP7.md` — intake
  - `handoff/FILE_MANIFEST.txt` — readiness
  - `handoff/MODULE_STATUS.txt` — readiness
  - `handoff/PHASE_10_CLOSEOUT_NOTE.md` — readiness
  - …and 96 more files

### Matters

- Files with matching implementation terms: **29**
  - `app.py` — matter, matter_event, matter_relationship
  - `REPORT_SUBSYSTEM_HANDOFF.txt` — matter
  - `docs/TAX_ASSISTANT_DIRECTION_CONFIRMED.md` — matter
  - `docs/WEALTH_SYSTEM_OPTION_A_ROADMAP.md` — matter
  - `services/services_intake.py` — matter
  - `services/services_matters.py` — matter, matter_event, matter_relationship
  - `templates/admin_index.html` — matter
  - `templates/controlled_export_prep.html` — matter
  - `templates/create_trust_step1.html` — matter
  - `templates/create_trust_step2.html` — matter
  - `templates/create_trust_step2_grantor.html` — matter
  - `templates/create_trust_step3.html` — matter
  - `templates/create_trust_step4.html` — matter
  - `templates/create_trust_step5.html` — matter
  - `templates/matters_dashboard.html` — matter
  - `templates/matter_detail.html` — matter, matter_relationship
  - `templates/matter_event_form.html` — matter
  - `templates/matter_form.html` — matter
  - `templates/matter_relationship_detail.html` — matter, matter_relationship
  - `templates/matter_relationship_form.html` — matter
  - …and 9 more files

### Trusts

- Files with matching implementation terms: **326**
  - `app.py` — beneficiary, grantor, settlor, trust, trustee
  - `FULL_SYSTEM_HANDOFF.txt` — trust, trustee
  - `HANDOFF_PHASE8E_ALIGNED.md` — trust, trustee
  - `HOSTED_SMOKE_TEST_CHECKLIST.md` — trust, trustee
  - `KNOWN_ISSUES_WATCHLIST_V1.txt` — trust, trustee
  - `OPERATOR_RUNBOOK_V1.txt` — trust, trustee
  - `pdf_utils.py` — beneficiary, settlor, trust, trustee
  - `QA_CHECKLIST_V1.txt` — trust
  - `RELEASE_CHECKLIST.md` — trust, trustee
  - `RELEASE_READINESS_V1.txt` — trust, trustee
  - `render.yaml` — trust, trustee
  - `REPORT_SUBSYSTEM_HANDOFF.txt` — trust
  - `ROLE_ACCESS_MATRIX_V1.txt` — trust, trustee
  - `routes_k1.py` — beneficiary, trust
  - `ROUTE_TEST_MATRIX_V1.txt` — trust
  - `SMOKE_TEST_ORDER_V1.txt` — trust, trustee
  - `TR-001.txt` — trust, trustee
  - `VERSION_SUMMARY_V1.txt` — trust, trustee
  - `backups_sqlite_change_history/form1041_dashboard.html` — trust
  - `backups_sqlite_change_history/instrument_detail.html` — trust
  - …and 306 more files

### Articles Rules

- Files with matching implementation terms: **34**
  - `app.py` — article, dynamic declaration
  - `FULL_SYSTEM_HANDOFF.txt` — article
  - `HOSTED_SMOKE_TEST_CHECKLIST.md` — article
  - `PHASE9_TRACK_C_STATUS.txt` — article
  - `QA_CHECKLIST_V1.txt` — article
  - `RELEASE_CHECKLIST.md` — article
  - `ROUTE_TEST_MATRIX_V1.txt` — article
  - `docs/POST_CREATE_CONSOLE_CHECKPOINT.md` — article
  - `migrations/add_article_registry_tables.py` — article
  - `scripts/smoke_routes.py` — article
  - `services/services_articles.py` — article, dynamic declaration
  - `services/services_intake.py` — article
  - `templates/admin_articles.html` — article
  - `templates/admin_article_new.html` — article
  - `templates/admin_index.html` — article
  - `templates/create_trust_launch.html` — article
  - `templates/create_trust_step1.html` — article
  - `templates/create_trust_step2.html` — article
  - `templates/create_trust_step2_grantor.html` — article
  - `templates/create_trust_step6.html` — article
  - …and 14 more files

### Documents

- Files with matching implementation terms: **248**
  - `app.py` — document, generate, pdf, template
  - `FULL_SYSTEM_HANDOFF.txt` — document, generate, pdf, template
  - `HANDOFF_PHASE8E_ALIGNED.md` — document
  - `HOSTED_SMOKE_TEST_CHECKLIST.md` — document, pdf
  - `KNOWN_ISSUES_WATCHLIST_V1.txt` — document, pdf, template
  - `OPERATOR_RUNBOOK_V1.txt` — document, pdf
  - `pdf_utils.py` — document, pdf, template
  - `PHASE9_TRACK_C_STATUS.txt` — document, generate
  - `QA_CHECKLIST_V1.txt` — document, generate, pdf
  - `RELEASE_CHECKLIST.md` — pdf
  - `RELEASE_READINESS_V1.txt` — document, pdf
  - `REPORT_SUBSYSTEM_HANDOFF.txt` — document, pdf, template
  - `ROLE_ACCESS_MATRIX_V1.txt` — document, generate
  - `routes_k1.py` — template
  - `ROUTE_TEST_MATRIX_V1.txt` — document, generate, pdf
  - `SMOKE_TEST_ORDER_V1.txt` — document, generate, pdf
  - `test.txt` — document
  - `VERSION_SUMMARY_V1.txt` — document, pdf, template
  - `data/export_activity_log.json` — document
  - `database/db.py` — document, generate, pdf
  - …and 228 more files

### Execution

- Files with matching implementation terms: **103**
  - `app.py` — execution, finalization, jurat, notary, signature, witness
  - `FULL_SYSTEM_HANDOFF.txt` — execution
  - `OPERATOR_RUNBOOK_V1.txt` — execution
  - `PHASE9_TRACK_C_STATUS.txt` — execution
  - `QA_CHECKLIST_V1.txt` — execution
  - `RELEASE_READINESS_V1.txt` — execution
  - `ROLE_ACCESS_MATRIX_V1.txt` — execution
  - `ROUTE_TEST_MATRIX_V1.txt` — execution
  - `SMOKE_TEST_ORDER_V1.txt` — execution
  - `VERSION_SUMMARY_V1.txt` — execution
  - `database/db.py` — execution, finalization, jurat, notary, signature, witness
  - `docs/BUILD_DOCTRINE.md` — finalization
  - `docs/EXECUTION_HANDOFF_CHECKPOINT.md` — execution
  - `docs/GLOBAL_411_FIREWALL_G8D_HOSTED_REGRESSION_CHECKLIST.md` — signature
  - `docs/POST_CREATE_CONSOLE_CHECKPOINT.md` — execution
  - `handoff/NAV_EXPOSURE_MATRIX.md` — execution
  - `handoff/PHASE_7A_VIEWER_NAV_CLOSEOUT_NOTE.md` — execution
  - `handoff/PROJECT_CONTINUITY_SUPERSEDING_NOTE.md` — execution
  - `handoff/ROLE_PERMISSION_MATRIX.md` — execution
  - `handoff/ROUTE_INTENT_MATRIX.md` — execution
  - …and 83 more files

### Assets

- Files with matching implementation terms: **164**
  - `app.py` — account, asset, custodian, property
  - `pdf_utils.py` — account, asset, property
  - `database/db.py` — account, asset, custodian, property
  - `docs/ACCOUNTING_LAYER_DIRECTION_CONFIRMED.md` — account, asset
  - `docs/ACCRUAL_ACCOUNTING_LAYER_COMPLETE.md` — account
  - `docs/ACCRUAL_AND_TAX_ASSISTANT_REQUIREMENT.md` — account
  - `docs/ASSET_CONSTANTS_AND_SUBTYPES.md` — account, asset, property
  - `docs/ASSET_DASHBOARD_COMPLETE.md` — asset, custodian, property
  - `docs/ASSET_DETAIL_DISPLAY_COMPLETE.md` — asset, custodian, property
  - `docs/BUILD_DOCTRINE.md` — account, property
  - `docs/DATE_INTELLIGENCE_COMPLETE.md` — asset, custodian
  - `docs/EXPANDED_ASSET_CLASSES_LOCKED.md` — asset, property
  - `docs/FILE_UPLOAD_MILESTONE.md` — account, property
  - `docs/FORM_1041_ENGINE_PHASE_START.md` — account, asset
  - `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md` — account
  - `docs/GLOBAL_411_FIREWALL_G8D_HOSTED_REGRESSION_CHECKLIST.md` — account, asset, property
  - `docs/K1_ENGINE_SAFE_BUILD_INTENT.md` — account, asset
  - `docs/LEDGER_PERSISTENCE_COMPLETE.md` — account, asset, custodian, property
  - `docs/PERSISTENCE_PROGRESS_ACCOUNTS.md` — account, property
  - `docs/POST_CREATE_CONSOLE_CHECKPOINT.md` — property
  - …and 144 more files

### Transfers Funding

- Files with matching implementation terms: **104**
  - `app.py` — assignment, funding, transfer
  - `HOSTED_SMOKE_TEST_CHECKLIST.md` — assignment
  - `RELEASE_CHECKLIST.md` — assignment
  - `database/db.py` — transfer
  - `docs/BUILD_DOCTRINE.md` — funding
  - `docs/EXECUTION_HANDOFF_CHECKPOINT.md` — transfer
  - `docs/GLOBAL_411_FIREWALL_G8D_HOSTED_REGRESSION_CHECKLIST.md` — transfer
  - `docs/POST_CREATE_CONSOLE_CHECKPOINT.md` — assignment
  - `docs/WIZARD_PROGRESS_STEP5.md` — funding
  - `docs/WIZARD_PROGRESS_STEP7.md` — funding
  - `handoff/PHASE_10_OPERATOR_READINESS_NOTE.md` — assignment
  - `handoff/PHASE_STATUS_LEDGER.md` — assignment
  - `handoff/TRANSFER_ENGINE_TEMPLATE_INVENTORY_AUDIT.md` — assignment, transfer
  - `migrations/add_article_registry_tables.py` — assignment
  - `models/models_transfer.py` — assignment, transfer
  - `models/models_transfer_support.py` — transfer
  - `models/__init__.py` — transfer
  - `scripts/migrate_hosted_firm_scope.py` — transfer
  - `scripts/smoke_routes.py` — assignment
  - `services/services_articles.py` — assignment
  - …and 84 more files

### Fiduciaries Governance

- Files with matching implementation terms: **137**
  - `app.py` — acceptance, appointment, decision, fiduciary, minutes, resolution
  - `FULL_SYSTEM_HANDOFF.txt` — decision, fiduciary
  - `HOSTED_SMOKE_TEST_CHECKLIST.md` — acceptance, minutes
  - `OPERATOR_RUNBOOK_V1.txt` — decision, fiduciary
  - `pdf_utils.py` — appointment, fiduciary
  - `QA_CHECKLIST_V1.txt` — decision, fiduciary
  - `RELEASE_CHECKLIST.md` — acceptance, minutes
  - `RELEASE_READINESS_V1.txt` — decision
  - `REPORT_SUBSYSTEM_HANDOFF.txt` — fiduciary
  - `ROLE_ACCESS_MATRIX_V1.txt` — decision
  - `ROUTE_TEST_MATRIX_V1.txt` — decision
  - `SMOKE_TEST_ORDER_V1.txt` — decision, fiduciary
  - `VERSION_SUMMARY_V1.txt` — decision
  - `database/db.py` — appointment, fiduciary, minutes, resolution
  - `docs/ACCOUNTING_LAYER_DIRECTION_CONFIRMED.md` — fiduciary
  - `docs/ACCRUAL_ACCOUNTING_LAYER_COMPLETE.md` — fiduciary
  - `docs/ACCRUAL_AND_TAX_ASSISTANT_REQUIREMENT.md` — fiduciary
  - `docs/ASSET_DASHBOARD_COMPLETE.md` — fiduciary
  - `docs/ASSET_DETAIL_DISPLAY_COMPLETE.md` — fiduciary
  - `docs/DATE_INTELLIGENCE_COMPLETE.md` — fiduciary
  - …and 117 more files

### Accounting Tax

- Files with matching implementation terms: **160**
  - `app.py` — 1041, accounting, distribution, income, k-1, k1, ledger, principal, tax
  - `FULL_SYSTEM_HANDOFF.txt` — 1041, k1, ledger
  - `HANDOFF_PHASE8E_ALIGNED.md` — 1041, k-1
  - `OPERATOR_RUNBOOK_V1.txt` — 1041, k-1, ledger
  - `pdf_utils.py` — 1041, accounting, distribution, k-1, k1, ledger, principal, tax
  - `QA_CHECKLIST_V1.txt` — 1041, k-1, ledger
  - `REPORT_SUBSYSTEM_HANDOFF.txt` — 1041, k1, ledger, tax
  - `routes_k1.py` — distribution, k1, ledger, principal, tax
  - `ROUTE_TEST_MATRIX_V1.txt` — 1041, k1, ledger, tax
  - `SMOKE_TEST_ORDER_V1.txt` — 1041, k-1, ledger
  - `TR-001.txt` — 1041, distribution, income, k-1, ledger, tax
  - `backups_sqlite_change_history/form1041_dashboard.html` — 1041, distribution, income, k-1, k1, principal, tax
  - `backups_sqlite_change_history/k1_readiness.html` — 1041, distribution, k-1, k1, principal, tax
  - `data/export_activity_log.json` — 1041, k1, tax
  - `database/db.py` — 1041, accounting, distribution, income, k-1, k1, ledger, principal, tax
  - `docs/ACCOUNTING_LAYER_DIRECTION_CONFIRMED.md` — accounting, income, ledger
  - `docs/ACCRUAL_ACCOUNTING_LAYER_COMPLETE.md` — 1041, accounting, income, k-1, ledger, tax
  - `docs/ACCRUAL_AND_TAX_ASSISTANT_REQUIREMENT.md` — accounting, ledger, tax
  - `docs/ASSET_CONSTANTS_AND_SUBTYPES.md` — ledger, tax
  - `docs/BUILD_DOCTRINE.md` — accounting, ledger, tax
  - …and 140 more files

### Evidence Provenance

- Files with matching implementation terms: **110**
  - `app.py` — audit, certified, chain of custody, evidence, verification
  - `FULL_SYSTEM_HANDOFF.txt` — audit
  - `HANDOFF_PHASE8E_ALIGNED.md` — audit
  - `OPERATOR_RUNBOOK_V1.txt` — audit
  - `pdf_utils.py` — audit, evidence
  - `QA_CHECKLIST_V1.txt` — audit
  - `REPORT_SUBSYSTEM_HANDOFF.txt` — audit, verification
  - `ROUTE_TEST_MATRIX_V1.txt` — audit
  - `SMOKE_TEST_ORDER_V1.txt` — audit
  - `database/db.py` — audit, evidence, verification
  - `docs/ACCOUNTING_LAYER_DIRECTION_CONFIRMED.md` — audit
  - `docs/EXECUTION_HANDOFF_CHECKPOINT.md` — audit
  - `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md` — audit
  - `docs/POST_CREATE_CONSOLE_CHECKPOINT.md` — verification
  - `handoff/AUDIT_TRAIL_PHASE_NOTE.txt` — audit
  - `handoff/CHANGE_HISTORY_PANELS_PHASE_NOTE.txt` — audit
  - `handoff/DASHBOARD_POLISH_COMPLETE.txt` — audit
  - `handoff/INSTRUMENT_INTEGRITY_COMPLETE.txt` — audit
  - `handoff/MASTER_CONTINUITY_AUDIT.md` — audit
  - `handoff/MEDIA_EVIDENCE_PHASE_NOTE.txt` — evidence
  - …and 90 more files

### Archive Continuity

- Files with matching implementation terms: **64**
  - `app.py` — archive, continuity, emergency, retention
  - `database/db.py` — archive, continuity
  - `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md` — emergency
  - `docs/GLOBAL_411_FIREWALL_G8D_HOSTED_REGRESSION_CHECKLIST.md` — emergency
  - `handoff/ADMIN_MANIFEST.txt` — continuity
  - `handoff/MASTER_CONTINUITY_AUDIT.md` — continuity
  - `handoff/OPEN_DECISIONS.md` — continuity
  - `handoff/PHASE_11_GENEALOGY_CLOSEOUT_NOTE.md` — archive
  - `handoff/PHASE_12_DEPLOYMENT_BLOCKER_NOTE.md` — archive
  - `handoff/PHASE_6_CLOSEOUT_NOTE.md` — continuity
  - `handoff/PHASE_7A_VIEWER_NAV_CLOSEOUT_NOTE.md` — continuity
  - `handoff/PHASE_STATUS_LEDGER.md` — continuity
  - `handoff/PROJECT_CONTINUITY_SUPERSEDING_NOTE.md` — continuity
  - `handoff/ROUTE_INTENT_MATRIX.md` — continuity
  - `migrations/add_archive_packet_finalization.py` — archive
  - `migrations/add_continuity_asset_fields.py` — continuity
  - `migrations/add_continuity_custody_log.py` — continuity
  - `roadmap/FEATURE_ROADMAP.md` — continuity
  - `services/services_continuity_assets.py` — archive, continuity
  - `services/services_intake.py` — continuity, succession
  - …and 44 more files

### Communications

- Files with matching implementation terms: **46**
  - `app.py` — delivery, notice, tracking
  - `database/db.py` — delivery, tracking
  - `docs/ACCOUNTING_LAYER_DIRECTION_CONFIRMED.md` — tracking
  - `docs/ACCRUAL_AND_TAX_ASSISTANT_REQUIREMENT.md` — tracking
  - `docs/ASSET_DETAIL_DISPLAY_COMPLETE.md` — tracking
  - `docs/BUILD_DOCTRINE.md` — tracking
  - `docs/K1_ENGINE_SAFE_BUILD_INTENT.md` — tracking
  - `docs/TAX_ASSISTANT_DIRECTION_CONFIRMED.md` — tracking
  - `handoff/PHASE_11_GENEALOGY_CLOSEOUT_NOTE.md` — tracking
  - `handoff/SESSION_TIMEOUT_PHASE_NOTE.txt` — tracking
  - `models/models_transfer.py` — tracking
  - `services/services_intake.py` — notice
  - `templates/admin_index.html` — notice
  - `templates/continuity_asset_dashboard.html` — tracking
  - `templates/controlled_export_prep.html` — tracking
  - `templates/create_trust_step1.html` — notice
  - `templates/create_trust_step2.html` — notice
  - `templates/create_trust_step2_grantor.html` — notice
  - `templates/create_trust_step3.html` — notice
  - `templates/create_trust_step4.html` — notice
  - …and 26 more files

### Administration Security

- Files with matching implementation terms: **222**
  - `app.py` — admin, csrf, login, permission, role, security, session
  - `FULL_SYSTEM_HANDOFF.txt` — admin, csrf, role, security
  - `HANDOFF_PHASE8E_ALIGNED.md` — admin, login, permission, role, security, session
  - `HOSTED_SMOKE_TEST_CHECKLIST.md` — admin, login
  - `KNOWN_ISSUES_WATCHLIST_V1.txt` — admin, permission, role
  - `OPERATOR_RUNBOOK_V1.txt` — admin, role
  - `pdf_utils.py` — role
  - `QA_CHECKLIST_V1.txt` — admin
  - `RELEASE_CHECKLIST.md` — admin
  - `RELEASE_READINESS_V1.txt` — admin, role
  - `REPORT_SUBSYSTEM_HANDOFF.txt` — admin
  - `ROLE_ACCESS_MATRIX_V1.txt` — admin, role
  - `routes_k1.py` — session
  - `ROUTE_TEST_MATRIX_V1.txt` — admin
  - `SMOKE_TEST_ORDER_V1.txt` — admin, role
  - `VERSION_SUMMARY_V1.txt` — admin, csrf, role, security
  - `data/export_activity_log.json` — admin, permission, role
  - `database/db.py` — admin, permission, role, security, session
  - `deployment/DEPLOYMENT_CHECKLIST.txt` — role
  - `docs/ACCOUNTING_LAYER_DIRECTION_CONFIRMED.md` — admin
  - …and 202 more files

### Firm Tenant Scope

- Files with matching implementation terms: **15**
  - `app.py` — active_firm, firm_id, tenant
  - `database/db.py` — current_firm, firm_id, tenant
  - `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md` — firm_id
  - `docs/GLOBAL_411_FIREWALL_G8D_HOSTED_REGRESSION_CHECKLIST.md` — firm_id, tenant
  - `migrations/add_archive_packet_finalization.py` — firm_id
  - `migrations/add_continuity_custody_log.py` — firm_id
  - `models/models_transfer.py` — firm_id
  - `scripts/migrate_hosted_firm_scope.py` — firm_id
  - `services/services_continuity_assets.py` — firm_id
  - `services/services_intake.py` — current_firm, firm_id
  - `services/services_matters.py` — current_firm, firm_id
  - `templates/transfer_archive_handoff_audit_pdf.html` — firm_id
  - `templates/transfer_archive_handoff_correction_detail.html` — firm_id
  - `templates/transfer_archive_handoff_detail.html` — firm_id
  - `templates/intake/export_history.html` — firm_id

### Workspaces Discussions

- Files with matching implementation terms: **69**
  - `app.py` — discussion, reply, thread, workspace
  - `FULL_SYSTEM_HANDOFF.txt` — discussion, reply, thread, workspace
  - `KNOWN_ISSUES_WATCHLIST_V1.txt` — thread, workspace
  - `OPERATOR_RUNBOOK_V1.txt` — discussion, workspace
  - `PHASE9_TRACK_C_STATUS.txt` — discussion, thread, workspace
  - `QA_CHECKLIST_V1.txt` — discussion, reply, thread, workspace
  - `RELEASE_READINESS_V1.txt` — discussion, workspace
  - `REPORT_SUBSYSTEM_HANDOFF.txt` — thread
  - `ROLE_ACCESS_MATRIX_V1.txt` — discussion, reply, workspace
  - `ROUTE_TEST_MATRIX_V1.txt` — discussion, reply, thread, workspace
  - `SMOKE_TEST_ORDER_V1.txt` — discussion, thread, workspace
  - `VERSION_SUMMARY_V1.txt` — discussion, workspace
  - `database/db.py` — workspace
  - `handoff/NATION1_PYTHON_HANDOFF.py` — thread
  - `handoff/NAV_EXPOSURE_MATRIX.md` — discussion, workspace
  - `handoff/OPEN_DECISIONS.md` — thread
  - `handoff/PHASE_7A_VIEWER_NAV_CLOSEOUT_NOTE.md` — discussion, workspace
  - `handoff/PHASE_STATUS_LEDGER.md` — thread
  - `handoff/PROJECT_CONTINUITY_SUPERSEDING_NOTE.md` — discussion, thread, workspace
  - `handoff/ROLE_PERMISSION_MATRIX.md` — discussion, workspace
  - …and 49 more files

### Analytics Visualization

- Files with matching implementation terms: **169**
  - `app.py` — analytics, dashboard, visualization
  - `FULL_SYSTEM_HANDOFF.txt` — analytics, dashboard, visualization
  - `HANDOFF_PHASE8E_ALIGNED.md` — dashboard
  - `HOSTED_SMOKE_TEST_CHECKLIST.md` — dashboard
  - `KNOWN_ISSUES_WATCHLIST_V1.txt` — dashboard
  - `OPERATOR_RUNBOOK_V1.txt` — visualization
  - `QA_CHECKLIST_V1.txt` — analytics, dashboard, trust map, visualization
  - `RELEASE_CHECKLIST.md` — dashboard
  - `RELEASE_READINESS_V1.txt` — analytics, visualization
  - `REPORT_SUBSYSTEM_HANDOFF.txt` — dashboard
  - `ROLE_ACCESS_MATRIX_V1.txt` — analytics, dashboard, visualization
  - `routes_k1.py` — dashboard
  - `ROUTE_TEST_MATRIX_V1.txt` — analytics, visualization
  - `SMOKE_TEST_ORDER_V1.txt` — analytics, visualization
  - `VERSION_SUMMARY_V1.txt` — analytics, visualization
  - `backups_sqlite_change_history/form1041_dashboard.html` — dashboard
  - `backups_sqlite_change_history/k1_readiness.html` — dashboard
  - `database/db.py` — dashboard
  - `docs/ASSET_CONSTANTS_AND_SUBTYPES.md` — dashboard
  - `docs/ASSET_DASHBOARD_COMPLETE.md` — dashboard
  - …and 149 more files

### Media

- Files with matching implementation terms: **121**
  - `app.py` — media, upload, video
  - `FULL_SYSTEM_HANDOFF.txt` — upload, video
  - `HOSTED_SMOKE_TEST_CHECKLIST.md` — upload
  - `OPERATOR_RUNBOOK_V1.txt` — video
  - `PHASE9_TRACK_C_STATUS.txt` — video
  - `QA_CHECKLIST_V1.txt` — upload, video
  - `RELEASE_READINESS_V1.txt` — video
  - `ROLE_ACCESS_MATRIX_V1.txt` — upload, video
  - `ROUTE_TEST_MATRIX_V1.txt` — upload, video
  - `SMOKE_TEST_ORDER_V1.txt` — video
  - `VERSION_SUMMARY_V1.txt` — media, video
  - `database/db.py` — media, upload
  - `deployment/DEPLOYMENT_CHECKLIST.txt` — media, upload
  - `docs/EXPANDED_ASSET_CLASSES_LOCKED.md` — media
  - `docs/FILE_UPLOAD_MILESTONE.md` — upload
  - `docs/FORM_1041_SAFE_MODE_INTENT.md` — media
  - `docs/K1_ENGINE_SAFE_BUILD_INTENT.md` — media
  - `docs/WEALTH_SYSTEM_OPTION_A_ROADMAP.md` — media
  - `handoff/DEPLOYMENT_PREP_SUMMARY.txt` — upload
  - `handoff/FILE_MANIFEST.txt` — upload
  - …and 101 more files

## Firm/Tenant Scope References

- `app.py` — firm_id, session.get("firm_id"), session.get('firm_id'), tenant
- `database/db.py` — firm_id, get_current_firm_id, session.get("firm_id"), tenant
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md` — firm_id
- `docs/GLOBAL_411_FIREWALL_G8D_HOSTED_REGRESSION_CHECKLIST.md` — firm_id, tenant
- `migrations/add_archive_packet_finalization.py` — firm_id
- `migrations/add_continuity_custody_log.py` — firm_id
- `models/models_transfer.py` — firm_id
- `scripts/migrate_hosted_firm_scope.py` — firm_id
- `services/services_continuity_assets.py` — firm_id
- `services/services_intake.py` — firm_id, get_current_firm_id
- `services/services_matters.py` — firm_id, get_current_firm_id
- `templates/transfer_archive_handoff_audit_pdf.html` — firm_id
- `templates/transfer_archive_handoff_correction_detail.html` — firm_id
- `templates/transfer_archive_handoff_detail.html` — firm_id
- `templates/intake/export_history.html` — firm_id

## Potential Personal-Reference Leakage

- `data/export_activity_log.json:1253` — `Luna Isaac`
- `data/export_activity_log.json:1264` — `Luna Isaac`
- `data/export_activity_log.json:1253` — `Mishoe`
- `data/export_activity_log.json:1264` — `Mishoe`
- `templates/matter_form.html:18` — `Mishoe`
- `templates/matter_form.html:18` — `Moore-Mishoe`
- `docs/bookmarks/LIM3_living_revocable_trust_progress_bookmark.md:21` — `Luna Isaac`
- `docs/bookmarks/LIM3_living_revocable_trust_progress_bookmark.md:21` — `Mishoe`
- `docs/bookmarks/LIM3_living_revocable_trust_progress_bookmark.md:1` — `LIM3`
- `docs/bookmarks/LIM3_living_revocable_trust_progress_bookmark.md:30` — `LIM3`
- `docs/bookmarks/LIM3_living_revocable_trust_progress_bookmark.md:35` — `LIM3`
- `docs/bookmarks/LIM3_living_revocable_trust_progress_bookmark.md:40` — `LIM3`
- `docs/bookmarks/LIM3_living_revocable_trust_progress_bookmark.md:45` — `LIM3`
- `docs/bookmarks/LIM3_living_revocable_trust_progress_bookmark.md:50` — `LIM3`
- `docs/bookmarks/LIM3_living_revocable_trust_progress_bookmark.md:57` — `LIM3`
- `docs/bookmarks/LIM3_living_revocable_trust_progress_bookmark.md:70` — `LIM3`

## Template Integrity

- Templates present: **238**
- Templates referenced by Python: **223**
- Referenced but missing: **0**
- Present but not directly referenced: **15**

### Present but Not Directly Referenced

- `_create_trust_progress.html`
- `_nav.html`
- `_platform_nav.html`
- `_platform_shell.html`
- `_transfer_completion_score.html`
- `_transfer_execution_gate.html`
- `_transfer_guidance.html`
- `_transfer_mode_badge.html`
- `_transfer_review_warnings.html`
- `base.html`
- `create_trust.html`
- `form_1041.html`
- `intake/orientation.html`
- `intake/translation_snapshot.html`
- `intake_dashboard.html`

## Parse Errors

- No Python syntax parse errors detected.
