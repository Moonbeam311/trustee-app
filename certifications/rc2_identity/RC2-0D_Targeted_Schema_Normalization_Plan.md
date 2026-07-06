# RC2-0D — Targeted Schema Normalization Plan

Status: Draft Plan — No schema changes applied
Source Matrix: RC2-0C_Identity_Mapping_Matrix.csv

## Purpose

This plan converts the RC2-0C Identity Mapping Matrix into a targeted schema-normalization roadmap. The goal is to normalize institutional identity fields surgically, avoiding broad or unnecessary schema changes.

## Summary

Tables Mapped: 118
High Priority Tables: 52
Medium Priority Tables: 59
Low Priority Tables: 7

## Class Counts

- Class I — Institutional Core: 24
- Class III — Administrative / Workflow: 40
- Class IV — Reference / Registry: 26
- Class II — Governance / Execution: 28

## Normalization Principles

1. Do not add every identity field to every table.
2. Normalize only the fields required by each table class.
3. Preserve existing columns for backward compatibility.
4. Add canonical fields for future use where missing.
5. Backfill identity from parent records before enforcing new write behavior.
6. Do not rewrite historical audit text unless a correction/migration record is created.

## Phase 1 — High Priority Institutional Core and Governance Tables

These tables should be addressed first because they carry fiduciary, governance, archive, execution, or certification significance.

- `accounts` — Class I — Institutional Core — Missing: matter_id, created_by, created_at, updated_at, capacity, status, record_version
- `archive_export_history` — Class I — Institutional Core — Missing: matter_id, created_by, updated_at, capacity, status, record_version
- `beneficiaries` — Class I — Institutional Core — Missing: matter_id, created_by, created_at, updated_at, capacity, status, record_version
- `certificate_event_bus` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, updated_at, capacity, status, record_version
- `certificate_lifecycle_events` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, updated_at, capacity, status, record_version
- `certificate_relationships` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, capacity, status, record_version
- `continuity_custody_log` — Class II — Governance / Execution — Missing: institution_id, matter_id, created_by, updated_at, capacity, status, record_version
- `documents` — Class I — Institutional Core — Missing: matter_id, created_by, created_at, updated_at, capacity, status, record_version
- `execution_event_log` — Class II — Governance / Execution — Missing: institution_id, trust_id, matter_id, created_by, capacity, status, record_version
- `execution_packet_prep` — Class II — Governance / Execution — Missing: institution_id, trust_id, matter_id, created_by, capacity, status, record_version
- `execution_tasks` — Class II — Governance / Execution — Missing: institution_id, matter_id, created_by, capacity, record_version
- `fiduciaries` — Class I — Institutional Core — Missing: matter_id, created_by, created_at, updated_at, capacity, record_version
- `institutional_archive_freezes` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, created_at, updated_at, capacity, status, record_version
- `institutional_archive_replication_ledger` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, created_at, updated_at, capacity, status, record_version
- `institutional_archive_repositories` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, capacity, status, record_version
- `institutional_archive_topology` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, capacity, status, record_version
- `institutional_brand_packages` — Class II — Governance / Execution — Missing: institution_id, trust_id, matter_id, updated_at, capacity, record_version
- `institutional_certifications` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, created_at, updated_at, capacity, status, record_version
- `institutional_custody_transfers` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, created_at, updated_at, capacity, status, record_version
- `institutional_disaster_recovery_registry` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, capacity, status, record_version
- `institutional_evidence_packages` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, capacity, status, record_version
- `institutional_execution_ledger` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, created_at, updated_at, capacity, status, record_version
- `institutional_execution_object_events` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, created_at, updated_at, capacity, status, record_version
- `institutional_execution_object_relationships` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, updated_at, capacity, status, record_version
- `institutional_execution_objects` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, updated_at, capacity, record_version
- `institutional_execution_sessions` — Class II — Governance / Execution — Missing: institution_id, firm_id, capacity, status, record_version
- `institutional_identity_assets` — Class II — Governance / Execution — Missing: institution_id, trust_id, matter_id, created_by, created_at, updated_at, capacity, status, record_version
- `institutional_integrity_revalidations` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, created_at, updated_at, capacity, status, record_version
- `institutional_recovery_events` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, created_at, updated_at, capacity, status, record_version
- `institutional_seal_ledger` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, created_at, updated_at, capacity, status, record_version
- `institutional_signature_profiles` — Class II — Governance / Execution — Missing: institution_id, trust_id, matter_id, updated_at, capacity, record_version
- `institutional_signature_records` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, updated_at, capacity, status, record_version
- `institutional_witness_notary_records` — Class II — Governance / Execution — Missing: institution_id, firm_id, trust_id, matter_id, created_by, updated_at, capacity, status, record_version
- `instruments` — Class I — Institutional Core — Missing: matter_id, created_by, created_at, updated_at, capacity, record_version
- `ledger_entries` — Class I — Institutional Core — Missing: matter_id, created_by, created_at, updated_at, capacity, status, record_version
- `matter_events` — Class I — Institutional Core — Missing: trust_id, created_by, updated_at, capacity, status, record_version
- `matter_intake_link_events` — Class I — Institutional Core — Missing: trust_id, matter_id, created_by, updated_at, capacity, status, record_version
- `matter_intake_links` — Class I — Institutional Core — Missing: trust_id, capacity, status, record_version
- `matter_relationships` — Class I — Institutional Core — Missing: trust_id, capacity, record_version
- `matters` — Class I — Institutional Core — Missing: trust_id, created_by, capacity, record_version
- `properties` — Class I — Institutional Core — Missing: matter_id, created_by, created_at, updated_at, capacity, record_version
- `transfer_actions` — Class I — Institutional Core — Missing: firm_id, trust_id, matter_id, created_by, updated_at, capacity, status, record_version
- `transfer_archive_handoff` — Class I — Institutional Core — Missing: matter_id, created_by, capacity, status, record_version
- `transfer_archive_handoff_corrections` — Class I — Institutional Core — Missing: matter_id, created_by, capacity, status, record_version
- `transfer_records` — Class I — Institutional Core — Missing: firm_id, trust_id, matter_id, created_by, capacity, status, record_version
- `transfer_support_docs` — Class I — Institutional Core — Missing: firm_id, trust_id, matter_id, created_by, capacity, record_version
- `transfers` — Class I — Institutional Core — Missing: matter_id, capacity, record_version
- `trust_article_assignments` — Class I — Institutional Core — Missing: firm_id, matter_id, created_by, updated_at, capacity, status, record_version
- `trust_article_conditions` — Class I — Institutional Core — Missing: firm_id, trust_id, matter_id, created_by, created_at, updated_at, capacity, status, record_version
- `trust_articles` — Class I — Institutional Core — Missing: firm_id, trust_id, matter_id, created_by, updated_at, capacity, status, record_version
- `trust_minutes` — Class I — Institutional Core — Missing: matter_id, updated_at, capacity, record_version
- `trusts` — Class I — Institutional Core — Missing: matter_id, created_by, created_at, updated_at, capacity, record_version

## Phase 2 — Medium Priority Administrative and Registry Tables

These tables should be normalized after core execution records are stable.

- `app_users` — Class III — Administrative / Workflow — Missing: created_by, created_at, updated_at
- `archive_packet_finalization` — Class IV — Reference / Registry — Missing: created_at, updated_at, status
- `asset_intake` — Class IV — Reference / Registry — Missing: updated_at, status
- `audit_log` — Class III — Administrative / Workflow — Missing: created_by, updated_at, status
- `certificate_governance_policies` — Class IV — Reference / Registry — Missing: status
- `certificate_templates` — Class IV — Reference / Registry — Missing: status
- `certificate_type_registry` — Class IV — Reference / Registry — Missing: status
- `chart_of_accounts` — Class IV — Reference / Registry — Missing: created_at, updated_at, status
- `controlled_docx_exports` — Class III — Administrative / Workflow — Missing: created_by, status
- `controlled_export_prep` — Class III — Administrative / Workflow — Missing: created_by, status
- `controlled_pdf_exports` — Class III — Administrative / Workflow — Missing: created_by, status
- `decision_rules` — Class IV — Reference / Registry — Missing: updated_at, status
- `discussion_messages` — Class IV — Reference / Registry — Missing: updated_at, status
- `distributions` — Class IV — Reference / Registry — Missing: created_at, updated_at
- `document_intake` — Class IV — Reference / Registry — Missing: updated_at, status
- `document_templates` — Class III — Administrative / Workflow — Missing: firm_id, created_by
- `docx_verification_gate` — Class IV — Reference / Registry — Missing: status
- `draft_sessions` — Class III — Administrative / Workflow — Missing: created_by, status
- `draft_variable_bindings` — Class III — Administrative / Workflow — Missing: created_by, status
- `dynamic_draft_previews` — Class IV — Reference / Registry — Missing: status
- `final_record_archive` — Class IV — Reference / Registry — Missing: status
- `genealogy_records` — Class IV — Reference / Registry — Missing: created_at, updated_at, status
- `guided_draft_workspace` — Class III — Administrative / Workflow — Missing: created_by, status
- `identity_intake` — Class IV — Reference / Registry — Missing: status
- `intake_answers` — Class III — Administrative / Workflow — Missing: updated_at, status
- `intake_deep_review` — Class III — Administrative / Workflow — Missing: created_by, status
- `intake_document_draft_answers` — Class III — Administrative / Workflow — Missing: status
- `intake_draft_readiness_ledger` — Class III — Administrative / Workflow — Missing: created_by
- `intake_drafting_prep_gate` — Class III — Administrative / Workflow — Missing: created_by, status
- `intake_export_logs` — Class III — Administrative / Workflow — Missing: updated_at, status
- `intake_final_draft_admin_approvals` — Class III — Administrative / Workflow — Missing: updated_at, status
- `intake_final_draft_completion_actions` — Class III — Administrative / Workflow — Missing: updated_at, status
- `intake_final_draft_completion_gate` — Class III — Administrative / Workflow — Missing: created_by, status
- `intake_final_draft_gate_actions` — Class III — Administrative / Workflow — Missing: updated_at, status
- `intake_final_draft_prep_gate` — Class III — Administrative / Workflow — Missing: created_by, status
- `intake_final_draft_sections` — Class III — Administrative / Workflow — Missing: created_by, status
- `intake_final_draft_version_register` — Class III — Administrative / Workflow — Missing: updated_at, status
- `intake_lane_events` — Class III — Administrative / Workflow — Missing: updated_at, status
- `intake_module_ledger` — Class III — Administrative / Workflow — Missing: firm_id, created_by, created_at
- `intake_orchestration` — Class III — Administrative / Workflow — Missing: created_by, status
- `intake_review_gate_actions` — Class III — Administrative / Workflow — Missing: updated_at, status
- `intake_review_gate_ledger` — Class III — Administrative / Workflow — Missing: created_by, status
- `intake_review_notes` — Class III — Administrative / Workflow — Missing: status
- `intake_scores` — Class III — Administrative / Workflow — Missing: status
- `intake_snapshots` — Class III — Administrative / Workflow — Missing: status
- `intake_translations` — Class III — Administrative / Workflow — Missing: updated_at, status
- `intake_workflow_bridge_answers` — Class III — Administrative / Workflow — Missing: status
- `media_records` — Class III — Administrative / Workflow — Missing: created_by, updated_at, status
- `pdf_execution_approval_gate` — Class IV — Reference / Registry — Missing: status
- `permissions` — Class IV — Reference / Registry — Missing: created_at, updated_at, status
- `role_permissions` — Class IV — Reference / Registry — Missing: created_at, updated_at, status
- `section_review_gate` — Class IV — Reference / Registry — Missing: status
- `sqlite_sequence` — Class IV — Reference / Registry — Missing: created_at, updated_at, status
- `trust_template_types` — Class IV — Reference / Registry — Missing: created_at, updated_at, status
- `tutorial_videos` — Class IV — Reference / Registry — Missing: status
- `user_permission_overrides` — Class IV — Reference / Registry — Missing: updated_at, status
- `user_roles` — Class III — Administrative / Workflow — Missing: created_by, created_at, updated_at
- `workspace_notes` — Class III — Administrative / Workflow — Missing: created_by, status
- `workspaces` — Class III — Administrative / Workflow — Missing: created_by

## Phase 3 — Low Priority / Already Sufficient Tables

These tables require little or no immediate action.

- `discussion_threads` — Class IV — Reference / Registry — Missing: None
- `generated_documents` — Class III — Administrative / Workflow — Missing: None
- `intake_document_recommendations` — Class III — Administrative / Workflow — Missing: None
- `intake_followup_tasks` — Class III — Administrative / Workflow — Missing: None
- `intake_sessions` — Class III — Administrative / Workflow — Missing: None
- `learning_articles` — Class IV — Reference / Registry — Missing: None
- `tax_form_guides` — Class IV — Reference / Registry — Missing: None

## Recommended Implementation Order

### RC2-0D1 — Core Transfer Chain

Normalize and backfill:

- transfers
- transfer_actions
- transfer_records
- transfer_support_docs
- ledger_entries
- trust_minutes
- transfer_archive_handoff
- transfer_archive_handoff_corrections
- archive_export_history

### RC2-0D2 — Matter / Trust / Asset Records

Normalize and backfill:

- trusts
- matters
- matter_events
- matter_relationships
- documents
- properties
- accounts
- beneficiaries
- fiduciaries
- instruments

### RC2-0D3 — Governance / Certificate / Execution Records

Normalize and backfill:

- certificate_event_bus
- certificate_lifecycle_events
- certificate_relationships
- institutional_evidence_packages
- execution_event_log
- execution_packet_prep
- execution_tasks
- institutional_execution_sessions
- institutional_execution_objects
- institutional_signature_records
- institutional_witness_notary_records

### RC2-0D4 — Administrative Records

Normalize only where operationally useful:

- intake_*
- draft_*
- controlled_*
- workspaces
- workspace_notes
- media_records

## RC2-0D Conclusion

The schema should be normalized in phases, beginning with the RR-1P transfer execution chain. The first active schema patch should therefore be RC2-0D1, focused on transfer, ledger, minute, archive, and export records.
