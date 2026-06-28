# ADR-6B — Workspace Migration Manifest

Generated: 2026-06-27T20:52:50

## Purpose

Create the actionable migration manifest for moving existing Trustee App templates into IOS workspaces while preserving legacy routes.

## Core Rule

Do not delete legacy routes. Do not rename routes until a replacement route is verified. Migrate by surfacing existing capabilities through IOS workspaces first.

## ADMINISTER

| Template | Current Location | Target Workspace | Migration Status | Legacy Route Preserved |
|---|---|---|---|---|
| `_transfer_execution_gate.html` | `templates/_transfer_execution_gate.html` | ADMINISTER | Pending | Yes |
| `asset_dashboard.html` | `templates/asset_dashboard.html` | ADMINISTER | Pending | Yes |
| `asset_health.html` | `templates/asset_health.html` | ADMINISTER | Pending | Yes |
| `asset_intake.html` | `templates/asset_intake.html` | ADMINISTER | Pending | Yes |
| `certificate_registry.html` | `templates/certificate_registry.html` | ADMINISTER | Pending | Yes |
| `certificate_verify.html` | `templates/certificate_verify.html` | ADMINISTER | Pending | Yes |
| `continuity_asset_dashboard.html` | `templates/continuity_asset_dashboard.html` | ADMINISTER | Pending | Yes |
| `execution_dashboard.html` | `templates/execution_dashboard.html` | ADMINISTER | Pending | Yes |
| `execution_event_log.html` | `templates/execution_event_log.html` | ADMINISTER | Pending | Yes |
| `execution_packet_prep.html` | `templates/execution_packet_prep.html` | ADMINISTER | Pending | Yes |
| `execution_task_detail.html` | `templates/execution_task_detail.html` | ADMINISTER | Pending | Yes |
| `execution_task_form.html` | `templates/execution_task_form.html` | ADMINISTER | Pending | Yes |
| `matter_detail.html` | `templates/matter_detail.html` | ADMINISTER | Pending | Yes |
| `matter_event_form.html` | `templates/matter_event_form.html` | ADMINISTER | Pending | Yes |
| `matter_form.html` | `templates/matter_form.html` | ADMINISTER | Pending | Yes |
| `matter_intake_bridge_detail.html` | `templates/matter_intake_bridge_detail.html` | ADMINISTER | Pending | Yes |
| `matter_relationship_detail.html` | `templates/matter_relationship_detail.html` | ADMINISTER | Pending | Yes |
| `matter_relationship_form.html` | `templates/matter_relationship_form.html` | ADMINISTER | Pending | Yes |
| `pdf_execution_approval_gate.html` | `templates/pdf_execution_approval_gate.html` | ADMINISTER | Pending | Yes |
| `transfer_asset.html` | `templates/transfer_asset.html` | ADMINISTER | Pending | Yes |
| `transfer_execution_dashboard.html` | `templates/transfer_execution_dashboard.html` | ADMINISTER | Pending | Yes |
| `trust_accounting_method.html` | `templates/trust_accounting_method.html` | ADMINISTER | Pending | Yes |
| `trust_article_assignments.html` | `templates/trust_article_assignments.html` | ADMINISTER | Pending | Yes |
| `trust_articles_output_surface.html` | `templates/trust_articles_output_surface.html` | ADMINISTER | Pending | Yes |
| `trust_articles_preview.html` | `templates/trust_articles_preview.html` | ADMINISTER | Pending | Yes |
| `trust_branding_settings.html` | `templates/trust_branding_settings.html` | ADMINISTER | Pending | Yes |
| `trust_certificate_of_trust_output_surface.html` | `templates/trust_certificate_of_trust_output_surface.html` | ADMINISTER | Pending | Yes |
| `trust_declaration_output_surface.html` | `templates/trust_declaration_output_surface.html` | ADMINISTER | Pending | Yes |
| `trust_detail.html` | `templates/trust_detail.html` | ADMINISTER | Pending | Yes |
| `trust_dynamic_declaration.html` | `templates/trust_dynamic_declaration.html` | ADMINISTER | Pending | Yes |
| `trust_formation_preview_hub.html` | `templates/trust_formation_preview_hub.html` | ADMINISTER | Pending | Yes |
| `trust_general_assignment_output_surface.html` | `templates/trust_general_assignment_output_surface.html` | ADMINISTER | Pending | Yes |
| `trust_general_assignment_preview.html` | `templates/trust_general_assignment_preview.html` | ADMINISTER | Pending | Yes |
| `trust_map_dashboard.html` | `templates/trust_map_dashboard.html` | ADMINISTER | Pending | Yes |
| `trust_minute_detail.html` | `templates/trust_minute_detail.html` | ADMINISTER | Pending | Yes |
| `trust_minutes_dashboard.html` | `templates/trust_minutes_dashboard.html` | ADMINISTER | Pending | Yes |
| `trust_minutes_form.html` | `templates/trust_minutes_form.html` | ADMINISTER | Pending | Yes |
| `trust_organizational_minutes_output_surface.html` | `templates/trust_organizational_minutes_output_surface.html` | ADMINISTER | Pending | Yes |
| `trust_organizational_minutes_preview.html` | `templates/trust_organizational_minutes_preview.html` | ADMINISTER | Pending | Yes |
| `trust_packet_preview.html` | `templates/trust_packet_preview.html` | ADMINISTER | Pending | Yes |
| `trust_successor_trustee_output_surface.html` | `templates/trust_successor_trustee_output_surface.html` | ADMINISTER | Pending | Yes |
| `trust_successor_trustee_preview.html` | `templates/trust_successor_trustee_preview.html` | ADMINISTER | Pending | Yes |
| `trust_trustee_acceptance_output_surface.html` | `templates/trust_trustee_acceptance_output_surface.html` | ADMINISTER | Pending | Yes |
| `trust_trustee_acceptance_preview.html` | `templates/trust_trustee_acceptance_preview.html` | ADMINISTER | Pending | Yes |
| `trust_type_detail.html` | `templates/trust_type_detail.html` | ADMINISTER | Pending | Yes |
| `trust_type_index.html` | `templates/trust_type_index.html` | ADMINISTER | Pending | Yes |

## ARCHIVE

| Template | Current Location | Target Workspace | Migration Status | Legacy Route Preserved |
|---|---|---|---|---|
| `archive_handoff_export_index.html` | `templates/archive_handoff_export_index.html` | ARCHIVE | Pending | Yes |
| `audit_dashboard.html` | `templates/audit_dashboard.html` | ARCHIVE | Pending | Yes |
| `audit_log_viewer.html` | `templates/audit_log_viewer.html` | ARCHIVE | Pending | Yes |
| `controlled_docx_export.html` | `templates/controlled_docx_export.html` | ARCHIVE | Pending | Yes |
| `controlled_export_prep.html` | `templates/controlled_export_prep.html` | ARCHIVE | Pending | Yes |
| `evidence_entity_view.html` | `templates/evidence_entity_view.html` | ARCHIVE | Pending | Yes |
| `export_center.html` | `templates/export_center.html` | ARCHIVE | Pending | Yes |
| `property_archive_finalize.html` | `templates/property_archive_finalize.html` | ARCHIVE | Pending | Yes |
| `property_archive_integrity.html` | `templates/property_archive_integrity.html` | ARCHIVE | Pending | Yes |
| `property_archive_packet.html` | `templates/property_archive_packet.html` | ARCHIVE | Pending | Yes |
| `property_custody_log.html` | `templates/property_custody_log.html` | ARCHIVE | Pending | Yes |
| `property_evidence_custody_timeline.html` | `templates/property_evidence_custody_timeline.html` | ARCHIVE | Pending | Yes |
| `resolve_custody_event_evidence.html` | `templates/resolve_custody_event_evidence.html` | ARCHIVE | Pending | Yes |
| `transfer_archive_handoff.html` | `templates/transfer_archive_handoff.html` | ARCHIVE | Pending | Yes |
| `transfer_archive_handoff_audit_pdf.html` | `templates/transfer_archive_handoff_audit_pdf.html` | ARCHIVE | Pending | Yes |
| `transfer_archive_handoff_audit_trail.html` | `templates/transfer_archive_handoff_audit_trail.html` | ARCHIVE | Pending | Yes |
| `transfer_archive_handoff_correction.html` | `templates/transfer_archive_handoff_correction.html` | ARCHIVE | Pending | Yes |
| `transfer_archive_handoff_correction_detail.html` | `templates/transfer_archive_handoff_correction_detail.html` | ARCHIVE | Pending | Yes |
| `transfer_archive_handoff_detail.html` | `templates/transfer_archive_handoff_detail.html` | ARCHIVE | Pending | Yes |
| `transfer_control_evidence.html` | `templates/transfer_control_evidence.html` | ARCHIVE | Pending | Yes |

## COMPLIANCE

| Template | Current Location | Target Workspace | Migration Status | Legacy Route Preserved |
|---|---|---|---|---|
| `_transfer_review_warnings.html` | `templates/_transfer_review_warnings.html` | COMPLIANCE | Pending | Yes |
| `docx_verification_gate.html` | `templates/docx_verification_gate.html` | COMPLIANCE | Pending | Yes |
| `final_record_archive_gate.html` | `templates/final_record_archive_gate.html` | COMPLIANCE | Pending | Yes |
| `form1041_preview.html` | `templates/form1041_preview.html` | COMPLIANCE | Pending | Yes |
| `k1_readiness.html` | `templates/k1_readiness.html` | COMPLIANCE | Pending | Yes |
| `section_review_gate.html` | `templates/section_review_gate.html` | COMPLIANCE | Pending | Yes |
| `transfer_review.html` | `templates/transfer_review.html` | COMPLIANCE | Pending | Yes |

## CREATE

| Template | Current Location | Target Workspace | Migration Status | Legacy Route Preserved |
|---|---|---|---|---|
| `_create_trust_progress.html` | `templates/_create_trust_progress.html` | CREATE | Pending | Yes |
| `create_trust.html` | `templates/create_trust.html` | CREATE | Pending | Yes |
| `create_trust_launch.html` | `templates/create_trust_launch.html` | CREATE | Pending | Yes |
| `create_trust_step1.html` | `templates/create_trust_step1.html` | CREATE | Pending | Yes |
| `create_trust_step2.html` | `templates/create_trust_step2.html` | CREATE | Pending | Yes |
| `create_trust_step2_grantor.html` | `templates/create_trust_step2_grantor.html` | CREATE | Pending | Yes |
| `create_trust_step3.html` | `templates/create_trust_step3.html` | CREATE | Pending | Yes |
| `create_trust_step4.html` | `templates/create_trust_step4.html` | CREATE | Pending | Yes |
| `create_trust_step5.html` | `templates/create_trust_step5.html` | CREATE | Pending | Yes |
| `create_trust_step6.html` | `templates/create_trust_step6.html` | CREATE | Pending | Yes |
| `create_trust_step7.html` | `templates/create_trust_step7.html` | CREATE | Pending | Yes |
| `document_generate_form.html` | `templates/document_generate_form.html` | CREATE | Pending | Yes |
| `document_intake.html` | `templates/document_intake.html` | CREATE | Pending | Yes |
| `draft_launch.html` | `templates/draft_launch.html` | CREATE | Pending | Yes |
| `draft_variable_binding.html` | `templates/draft_variable_binding.html` | CREATE | Pending | Yes |
| `dynamic_draft_preview.html` | `templates/dynamic_draft_preview.html` | CREATE | Pending | Yes |
| `guided_draft_workspace.html` | `templates/guided_draft_workspace.html` | CREATE | Pending | Yes |
| `instrument_create.html` | `templates/instrument_create.html` | CREATE | Pending | Yes |
| `instrument_dashboard.html` | `templates/instrument_dashboard.html` | CREATE | Pending | Yes |
| `instrument_detail.html` | `templates/instrument_detail.html` | CREATE | Pending | Yes |
| `instrument_print.html` | `templates/instrument_print.html` | CREATE | Pending | Yes |
| `intake_dashboard.html` | `templates/intake_dashboard.html` | CREATE | Pending | Yes |
| `intake_deep_review.html` | `templates/intake_deep_review.html` | CREATE | Pending | Yes |
| `intake_drafting_prep.html` | `templates/intake_drafting_prep.html` | CREATE | Pending | Yes |
| `intake_identity.html` | `templates/intake_identity.html` | CREATE | Pending | Yes |
| `intake_identity_summary.html` | `templates/intake_identity_summary.html` | CREATE | Pending | Yes |
| `intake_readiness.html` | `templates/intake_readiness.html` | CREATE | Pending | Yes |

## DEVELOPER

| Template | Current Location | Target Workspace | Migration Status | Legacy Route Preserved |
|---|---|---|---|---|
| `bootstrap_admin_once.html` | `templates/bootstrap_admin_once.html` | DEVELOPER | Pending | Yes |
| `hosted_production_health.html` | `templates/hosted_production_health.html` | DEVELOPER | Pending | Yes |

## GOVERNANCE

| Template | Current Location | Target Workspace | Migration Status | Legacy Route Preserved |
|---|---|---|---|---|
| `command_dashboard.html` | `templates/command_dashboard.html` | GOVERNANCE | Pending | Yes |
| `decision_dashboard.html` | `templates/decision_dashboard.html` | GOVERNANCE | Pending | Yes |
| `decision_result.html` | `templates/decision_result.html` | GOVERNANCE | Pending | Yes |
| `discussion_dashboard.html` | `templates/discussion_dashboard.html` | GOVERNANCE | Pending | Yes |
| `discussion_form.html` | `templates/discussion_form.html` | GOVERNANCE | Pending | Yes |
| `discussion_reply_form.html` | `templates/discussion_reply_form.html` | GOVERNANCE | Pending | Yes |
| `discussion_thread.html` | `templates/discussion_thread.html` | GOVERNANCE | Pending | Yes |
| `workspace_discussions.html` | `templates/workspace_discussions.html` | GOVERNANCE | Pending | Yes |

## LEGACY

| Template | Current Location | Target Workspace | Migration Status | Legacy Route Preserved |
|---|---|---|---|---|
| `genealogy_dashboard.html` | `templates/genealogy_dashboard.html` | LEGACY | Pending | Yes |
| `genealogy_form.html` | `templates/genealogy_form.html` | LEGACY | Pending | Yes |
| `media_dashboard.html` | `templates/media_dashboard.html` | LEGACY | Pending | Yes |
| `media_form.html` | `templates/media_form.html` | LEGACY | Pending | Yes |

## LIBRARY

| Template | Current Location | Target Workspace | Migration Status | Legacy Route Preserved |
|---|---|---|---|---|
| `form_guide_detail.html` | `templates/form_guide_detail.html` | LIBRARY | Pending | Yes |
| `form_guide_form.html` | `templates/form_guide_form.html` | LIBRARY | Pending | Yes |
| `forms_dashboard.html` | `templates/forms_dashboard.html` | LIBRARY | Pending | Yes |
| `guide_page.html` | `templates/guide_page.html` | LIBRARY | Pending | Yes |
| `learning_article.html` | `templates/learning_article.html` | LIBRARY | Pending | Yes |
| `learning_article_form.html` | `templates/learning_article_form.html` | LIBRARY | Pending | Yes |
| `learning_category.html` | `templates/learning_category.html` | LIBRARY | Pending | Yes |
| `learning_dashboard.html` | `templates/learning_dashboard.html` | LIBRARY | Pending | Yes |
| `video_category.html` | `templates/video_category.html` | LIBRARY | Pending | Yes |
| `video_dashboard.html` | `templates/video_dashboard.html` | LIBRARY | Pending | Yes |
| `video_detail.html` | `templates/video_detail.html` | LIBRARY | Pending | Yes |
| `video_trust_type.html` | `templates/video_trust_type.html` | LIBRARY | Pending | Yes |
| `video_upload.html` | `templates/video_upload.html` | LIBRARY | Pending | Yes |

## PEOPLE

| Template | Current Location | Target Workspace | Migration Status | Legacy Route Preserved |
|---|---|---|---|---|
| `fiduciary_dashboard.html` | `templates/fiduciary_dashboard.html` | PEOPLE | Pending | Yes |
| `fiduciary_form.html` | `templates/fiduciary_form.html` | PEOPLE | Pending | Yes |
| `role_dashboard.html` | `templates/role_dashboard.html` | PEOPLE | Pending | Yes |
| `role_form.html` | `templates/role_form.html` | PEOPLE | Pending | Yes |
| `user_dashboard.html` | `templates/user_dashboard.html` | PEOPLE | Pending | Yes |
| `user_edit.html` | `templates/user_edit.html` | PEOPLE | Pending | Yes |
| `user_form.html` | `templates/user_form.html` | PEOPLE | Pending | Yes |
| `user_reset_password.html` | `templates/user_reset_password.html` | PEOPLE | Pending | Yes |

## REPORTS

| Template | Current Location | Target Workspace | Migration Status | Legacy Route Preserved |
|---|---|---|---|---|
| `analytics_dashboard.html` | `templates/analytics_dashboard.html` | REPORTS | Pending | Yes |
| `form1041_dashboard.html` | `templates/form1041_dashboard.html` | REPORTS | Pending | Yes |
| `form1041_print.html` | `templates/form1041_print.html` | REPORTS | Pending | Yes |
| `form1041_report_print.html` | `templates/form1041_report_print.html` | REPORTS | Pending | Yes |
| `form1041_report_view.html` | `templates/form1041_report_view.html` | REPORTS | Pending | Yes |
| `form_1041.html` | `templates/form_1041.html` | REPORTS | Pending | Yes |
| `k1_beneficiary_edit.html` | `templates/k1_beneficiary_edit.html` | REPORTS | Pending | Yes |
| `k1_beneficiary_form.html` | `templates/k1_beneficiary_form.html` | REPORTS | Pending | Yes |
| `k1_dashboard.html` | `templates/k1_dashboard.html` | REPORTS | Pending | Yes |
| `k1_distribution_edit.html` | `templates/k1_distribution_edit.html` | REPORTS | Pending | Yes |
| `k1_distribution_form.html` | `templates/k1_distribution_form.html` | REPORTS | Pending | Yes |
| `k1_report_print.html` | `templates/k1_report_print.html` | REPORTS | Pending | Yes |
| `k1_report_view.html` | `templates/k1_report_view.html` | REPORTS | Pending | Yes |
| `k1_year_end_summary.html` | `templates/k1_year_end_summary.html` | REPORTS | Pending | Yes |
| `report_center.html` | `templates/report_center.html` | REPORTS | Pending | Yes |
| `tax_assistant.html` | `templates/tax_assistant.html` | REPORTS | Pending | Yes |
| `visualization_dashboard.html` | `templates/visualization_dashboard.html` | REPORTS | Pending | Yes |

## REVIEW

| Template | Current Location | Target Workspace | Migration Status | Legacy Route Preserved |
|---|---|---|---|---|
| `access_denied.html` | `templates/access_denied.html` | REVIEW | Pending | Yes |
| `add_property.html` | `templates/add_property.html` | REVIEW | Pending | Yes |
| `admin_article_new.html` | `templates/admin_article_new.html` | REVIEW | Pending | Yes |
| `admin_articles.html` | `templates/admin_articles.html` | REVIEW | Pending | Yes |
| `admin_index.html` | `templates/admin_index.html` | REVIEW | Pending | Yes |
| `controlled_pdf_conversion.html` | `templates/controlled_pdf_conversion.html` | REVIEW | Pending | Yes |
| `dashboard.html` | `templates/dashboard.html` | REVIEW | Pending | Yes |
| `document_dashboard.html` | `templates/document_dashboard.html` | REVIEW | Pending | Yes |
| `document_detail.html` | `templates/document_detail.html` | REVIEW | Pending | Yes |
| `financial_summary.html` | `templates/financial_summary.html` | REVIEW | Pending | Yes |
| `ledger_entry.html` | `templates/ledger_entry.html` | REVIEW | Pending | Yes |
| `lifecycle_master_ledger.html` | `templates/lifecycle_master_ledger.html` | REVIEW | Pending | Yes |
| `link_account.html` | `templates/link_account.html` | REVIEW | Pending | Yes |
| `matters_dashboard.html` | `templates/matters_dashboard.html` | REVIEW | Pending | Yes |
| `portfolio_dashboard.html` | `templates/portfolio_dashboard.html` | REVIEW | Pending | Yes |
| `property_continuity_profile.html` | `templates/property_continuity_profile.html` | REVIEW | Pending | Yes |
| `property_detail.html` | `templates/property_detail.html` | REVIEW | Pending | Yes |
| `property_resolution_queue.html` | `templates/property_resolution_queue.html` | REVIEW | Pending | Yes |
| `transfer_assignment.html` | `templates/transfer_assignment.html` | REVIEW | Pending | Yes |
| `transfer_bank_support_docs.html` | `templates/transfer_bank_support_docs.html` | REVIEW | Pending | Yes |
| `transfer_classification.html` | `templates/transfer_classification.html` | REVIEW | Pending | Yes |
| `transfer_detail.html` | `templates/transfer_detail.html` | REVIEW | Pending | Yes |
| `transfer_document_support_docs.html` | `templates/transfer_document_support_docs.html` | REVIEW | Pending | Yes |
| `transfer_external_tracking.html` | `templates/transfer_external_tracking.html` | REVIEW | Pending | Yes |
| `transfer_instruction_template.html` | `templates/transfer_instruction_template.html` | REVIEW | Pending | Yes |
| `transfer_optional_support_docs.html` | `templates/transfer_optional_support_docs.html` | REVIEW | Pending | Yes |
| `transfer_personal_property_support_docs.html` | `templates/transfer_personal_property_support_docs.html` | REVIEW | Pending | Yes |
| `transfer_print_view.html` | `templates/transfer_print_view.html` | REVIEW | Pending | Yes |
| `transfer_recommended_support_docs.html` | `templates/transfer_recommended_support_docs.html` | REVIEW | Pending | Yes |
| `transfer_records.html` | `templates/transfer_records.html` | REVIEW | Pending | Yes |
| `transfer_start.html` | `templates/transfer_start.html` | REVIEW | Pending | Yes |
| `transfer_support_doc_edit.html` | `templates/transfer_support_doc_edit.html` | REVIEW | Pending | Yes |
| `transfer_template_center.html` | `templates/transfer_template_center.html` | REVIEW | Pending | Yes |
| `transfer_trustee_acceptance.html` | `templates/transfer_trustee_acceptance.html` | REVIEW | Pending | Yes |
| `upload_document.html` | `templates/upload_document.html` | REVIEW | Pending | Yes |
| `workflow_hub.html` | `templates/workflow_hub.html` | REVIEW | Pending | Yes |
| `workspace_dashboard.html` | `templates/workspace_dashboard.html` | REVIEW | Pending | Yes |
| `workspace_detail.html` | `templates/workspace_detail.html` | REVIEW | Pending | Yes |
| `workspace_documents.html` | `templates/workspace_documents.html` | REVIEW | Pending | Yes |
| `workspace_form.html` | `templates/workspace_form.html` | REVIEW | Pending | Yes |
| `workspace_note_form.html` | `templates/workspace_note_form.html` | REVIEW | Pending | Yes |
| `workspace_tasks.html` | `templates/workspace_tasks.html` | REVIEW | Pending | Yes |

## SHELL / SHARED

| Template | Current Location | Target Workspace | Migration Status | Legacy Route Preserved |
|---|---|---|---|---|
| `_institutional_workspace_map.html` | `templates/_institutional_workspace_map.html` | SHELL / SHARED | Shared Shell | Yes |
| `_ios_shell.html` | `templates/_ios_shell.html` | SHELL / SHARED | Shared Shell | Yes |
| `_nav.html` | `templates/_nav.html` | SHELL / SHARED | Shared Shell | Yes |
| `_platform_nav.html` | `templates/_platform_nav.html` | SHELL / SHARED | Shared Shell | Yes |
| `_platform_shell.html` | `templates/_platform_shell.html` | SHELL / SHARED | Shared Shell | Yes |
| `_transfer_completion_score.html` | `templates/_transfer_completion_score.html` | SHELL / SHARED | Shared Shell | Yes |
| `_transfer_guidance.html` | `templates/_transfer_guidance.html` | SHELL / SHARED | Shared Shell | Yes |
| `_transfer_mode_badge.html` | `templates/_transfer_mode_badge.html` | SHELL / SHARED | Shared Shell | Yes |
| `base.html` | `templates/base.html` | SHELL / SHARED | Shared Shell | Yes |
| `ios_shell.html` | `templates/ios_shell.html` | SHELL / SHARED | Shared Shell | Yes |
| `ios_workspace.html` | `templates/ios_workspace.html` | SHELL / SHARED | Shared Shell | Yes |

## SYSTEM

| Template | Current Location | Target Workspace | Migration Status | Legacy Route Preserved |
|---|---|---|---|---|
| `change_password.html` | `templates/change_password.html` | SYSTEM | Pending | Yes |
| `permissions_dashboard.html` | `templates/permissions_dashboard.html` | SYSTEM | Pending | Yes |
| `security_dashboard.html` | `templates/security_dashboard.html` | SYSTEM | Pending | Yes |
| `system_health.html` | `templates/system_health.html` | SYSTEM | Pending | Yes |

## ADR-6B Findings

- Total templates inventoried: **209**
- REVIEW templates remaining: **42**
- ADMINISTER, CREATE, PEOPLE, LEGACY, LIBRARY, REPORTS, ARCHIVE, SYSTEM, GOVERNANCE, and COMPLIANCE now have migration queues.
- REVIEW items require either manual ownership assignment or promotion into a new shared/system category.
