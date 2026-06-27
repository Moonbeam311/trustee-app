# UPA-1B-6B-4F — Record-Level Ownership Resolution and Extraction Manifest

Generated: 2026-06-14T14:24:35.784313
Status: **EXTRACTION_MANIFEST_COMPLETE_REVIEW_REQUIRED**

## Safety

- Database integrity: `ok`
- Database unchanged: **True**
- Source 4E report: `audit\UPA-1B-6B-4E_dual_runtime_ownership_20260614_141357.json`

## Manifest Summary

- Total rows classified: **24809**
- Copy to Firm 1: **496**
- Copy to Firm 2: **365**
- Copy to both: **23886**
- Quarantine: **62**
- Null-firm rows mapped: **6**

## Ownership Counts

- BOTH_GLOBAL: **23886**
- FIRM-001: **496**
- FIRM-002: **365**
- GLOBAL_CANDIDATE: **35**
- UNRESOLVED_TENANT: **27**

## Action Counts

- COPY_TO_BOTH: **23886**
- COPY_TO_FIRM1: **496**
- COPY_TO_FIRM2: **365**
- QUARANTINE_GLOBAL_POLICY_REVIEW: **35**
- QUARANTINE_OWNERSHIP_REVIEW: **27**

## Null-Firm Records

- `audit_log` `{'id': 114}` → `COPY_TO_FIRM1` (HIGH)
- `audit_log` `{'id': 115}` → `COPY_TO_FIRM1` (HIGH)
- `audit_log` `{'id': 116}` → `COPY_TO_FIRM1` (HIGH)
- `documents` `{'document_id': 'DOC-001'}` → `COPY_TO_FIRM2` (HIGH)
- `documents` `{'document_id': 'DOC-002'}` → `COPY_TO_FIRM2` (HIGH)
- `documents` `{'document_id': 'DOC-003'}` → `COPY_TO_FIRM2` (HIGH)

## Quarantine Tables

- `decision_rules`: **5 row(s)**
- `discussion_messages`: **5 row(s)**
- `discussion_threads`: **5 row(s)**
- `document_templates`: **3 row(s)**
- `intake_module_ledger`: **16 row(s)**
- `learning_articles`: **9 row(s)**
- `tax_form_guides`: **10 row(s)**
- `trust_articles`: **3 row(s)**
- `tutorial_videos`: **5 row(s)**
- `user_permission_overrides`: **1 row(s)**

## Extraction Gate

- No Firm 1 or Firm 2 database was created.
- COPY_TO_FIRM1 rows are eligible only for a future Firm 1 sandbox.
- COPY_TO_FIRM2 rows are eligible only for a future Firm 2 sandbox.
- COPY_TO_BOTH rows are approved shared platform data.
- QUARANTINE rows remain excluded until resolved.
