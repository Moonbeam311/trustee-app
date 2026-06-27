# UPA-1B-6B-4E — Dual-Runtime Ownership and Continuity Map

Generated: 2026-06-14T14:05:10.440909
Status: **OWNERSHIP_MAP_COMPLETE_EXTRACTION_NOT_YET_AUTHORIZED**

## Safety

- Integrity: `ok`
- Database unchanged: **True**

## Classification Summary

- ALL_NULL_FIRM: **1**
- DEPENDENT_PARENT_SCOPE: **1**
- EMPTY_SCHEMA_REVIEW: **15**
- FIRM1_EXPLICIT: **12**
- FIRM2_EXPLICIT: **34**
- MIXED_EXPLICIT: **11**
- PROBABLE_FIRM2_PRIVATE: **2**
- PROBABLE_GLOBAL: **2**
- UNCLASSIFIED_UNSCOPED: **6**
- UNSCOPED_SENSITIVE_TENANT_DATA: **4**

## Extraction Eligibility

- COPY_SCHEMA_ONLY_PENDING_POLICY: **15**
- COPY_TO_BOTH_AFTER_GLOBAL_POLICY_REVIEW: **2**
- FILTER_BY_FIRM_AND_REVIEW_NULL_ROWS: **11**
- FIRM1_ONLY: **12**
- FIRM2_ONLY: **34**
- FIRM2_PENDING_PARENT_VALIDATION: **2**
- INHERIT_FROM_PARENT_AFTER_GRAPH_VALIDATION: **1**
- MANUAL_CLASSIFICATION_REQUIRED: **6**
- MANUAL_OR_PARENT_OWNERSHIP_REVIEW: **4**
- OWNERSHIP_REVIEW_REQUIRED: **1**

## Key Groups

- Explicit Firm 1: `['generated_documents', 'intake_draft_readiness_ledger', 'intake_final_draft_admin_approvals', 'intake_final_draft_completion_gate', 'intake_final_draft_prep_gate', 'intake_final_draft_sections', 'intake_final_draft_version_register', 'intake_review_gate_ledger', 'ledger_entries', 'media_records', 'trust_minutes', 'workspace_notes']`
- Explicit Firm 2: `['archive_packet_finalization', 'asset_intake', 'continuity_custody_log', 'controlled_docx_exports', 'controlled_export_prep', 'controlled_pdf_exports', 'document_intake', 'docx_verification_gate', 'draft_sessions', 'draft_variable_bindings', 'dynamic_draft_previews', 'execution_event_log', 'execution_packet_prep', 'final_record_archive', 'guided_draft_workspace', 'identity_intake', 'intake_answers', 'intake_deep_review', 'intake_document_draft_answers', 'intake_drafting_prep_gate', 'intake_followup_tasks', 'intake_lane_events', 'intake_orchestration', 'intake_review_notes', 'intake_scores', 'intake_sessions', 'intake_snapshots', 'intake_translations', 'intake_workflow_bridge_answers', 'matter_events', 'matter_relationships', 'matters', 'pdf_execution_approval_gate', 'section_review_gate']`
- Mixed: `['app_users', 'audit_log', 'execution_tasks', 'intake_document_recommendations', 'intake_export_logs', 'intake_final_draft_gate_actions', 'intake_review_gate_actions', 'properties', 'transfers', 'trusts', 'workspaces']`
- Probable global: `['permissions', 'role_permissions']`
- Dependent parent scope: `['transfer_actions']`
- Probable Firm 2 private: `['transfer_records', 'trust_article_assignments']`
- Ambiguous: `['decision_rules', 'discussion_messages', 'discussion_threads', 'document_templates', 'documents', 'intake_module_ledger', 'learning_articles', 'tax_form_guides', 'trust_articles', 'tutorial_videos', 'user_permission_overrides']`
- Null-firm: `{'audit_log': 3, 'documents': 3}`

## admin123

- Distribution: `{'FIRM-001': 11, 'FIRM-002': 231, '[NO_FIRM_COLUMN]': 23}`
- Policy: independent user record in each runtime.

## Warnings

- Probable global tables require policy review before copying to both runtimes.
- admin123 must become independent account records in Firm 1 and Firm 2.
- Private marker matches are strong Firm 2 evidence but still require parent validation.

## Blockers

- 11 table(s) contain explicit Firm 1 and Firm 2 records.
- 11 table(s) remain ambiguous or require parent/manual review.
- 6 null-firm row(s) exist across 2 table(s).
