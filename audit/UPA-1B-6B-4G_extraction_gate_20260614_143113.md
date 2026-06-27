# UPA-1B-6B-4G — Global Data Validation, Quarantine Resolution, and Extraction Gate

Generated: 2026-06-14T14:33:04.297754
Status: **EXTRACTION_GATE_BLOCKED_REVIEW_REQUIRED**

## Safety

- Integrity: `ok`
- Live database unchanged: **True**
- Source 4F report: `audit\UPA-1B-6B-4F_extraction_manifest_20260614_142435.json`

## Final Extraction Counts

- Copy to Firm 1: **496**
- Copy to Firm 2: **365**
- Copy to both: **23889**
- Quarantined: **59**
- Resolved from prior quarantine: **3**
- Rejected from prior shared classification: **0**

## Null-Firm Resolution

- Total null-firm rows: **6**
- Resolved: **6**
- Unresolved: **0**

## Shared-Data Validation

- `permissions`: COPY_TO_BOTH=13
- `role_permissions`: COPY_TO_BOTH=23873

## Remaining Quarantine Tables

- `decision_rules`: **5 row(s)**
- `discussion_messages`: **5 row(s)**
- `discussion_threads`: **5 row(s)**
- `document_templates`: **3 row(s)**
- `intake_module_ledger`: **16 row(s)**
- `learning_articles`: **9 row(s)**
- `tax_form_guides`: **10 row(s)**
- `tutorial_videos`: **5 row(s)**
- `user_permission_overrides`: **1 row(s)**

## Blockers

- 59 row(s) remain quarantined.
- 32 proposed shared row(s) require global or role-assignment review.

## Warnings

- 3 previously quarantined row(s) were resolved.

## Extraction Gate

- Approved for sandbox build: **False**
- Live database modification: **PROHIBITED**
- Production cutover: **NOT AUTHORIZED**
