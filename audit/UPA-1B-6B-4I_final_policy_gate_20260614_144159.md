# UPA-1B-6B-4I — Final Policy Adjudication and Sandbox Authorization Gate

Generated: 2026-06-14T14:42:00.192963
Status: **FINAL_POLICY_PARTIAL_TENANT_PARENT_RESOLUTION_REQUIRED**

## Safety

- Integrity: `ok`
- Live database unchanged: **True**

## Final Policy Results

- Rows adjudicated: **59**
- Reference rows approved for both: **32**
- Tenant rows resolved: **0**
- Tenant rows unresolved: **27**
- Remaining quarantine: **27**

## Actions

- `COPY_TO_BOTH`: **32**
- `QUARANTINE_CONFLICT_REVIEW`: **10**
- `QUARANTINE_INTAKE_PARENT_REQUIRED`: **16**
- `QUARANTINE_PERMISSION_OWNER_REQUIRED`: **1**

## Remaining Quarantine Tables

- `discussion_messages`: **5**
- `discussion_threads`: **5**
- `intake_module_ledger`: **16**
- `user_permission_overrides`: **1**

## Sandbox Gate

- Authorized: **False**
- Live database modification: **PROHIBITED**
- Production cutover: **NOT AUTHORIZED**
