# UPA-1B-6B — Controlled Firm 1/Firm 2 Runtime Verification

Generated: 2026-06-13T18:20:47.893694
Status: **FAIL_CROSS_FIRM_EXPOSURE_DETECTED**
Source: `audit\UPA-1B-6A_runtime_target_map_20260613_181830.json`

## Database Safety Control

- Live database unchanged: **True**
- Live SHA256 before: `eb2b318824be70aa2e37a5a9d7c8c5c1767a7bb7cbf9922f459128751cbf26f8`
- Live SHA256 after: `eb2b318824be70aa2e37a5a9d7c8c5c1767a7bb7cbf9922f459128751cbf26f8`
- Sandbox: `audit\runtime_sandbox\UPA-1B-6B_sandbox_20260613_182046.db`
- Runtime binding verified: **True**

## Summary

- Collision Targets: **7**
- Requests Attempted: **8**
- Requests Completed: **8**
- Opposite Firm Exposure Responses: **2**
- Write Functions Inventoried: **5**
- Write Mutations Executed: **0**
- Opposite Firm Exposure Detected: **1**
- Tested Without Opposite Marker: **1**
- No Resolvable Get Route: **5**
- Routes Unresolved: **0**

## Collision Runtime Tests

### `ISO-009` — `audit_log.entity_id` = `TR-001`

- Outcome: **NO_RESOLVABLE_GET_ROUTE**
- Database rows: **16**
- Route tests: **0**

### `ISO-010` — `audit_log.entity_id` = `admin123`

- Outcome: **NO_RESOLVABLE_GET_ROUTE**
- Database rows: **75**
- Route tests: **0**

### `ISO-011` — `intake_document_recommendations.intake_id` = `INTAKE-0005`

- Outcome: **NO_OPPOSITE_MARKER_DETECTED_IN_TESTED_GET_ROUTES**
- Database rows: **15**
- Route tests: **4**
  - `/intake/INTAKE-0005/recommendations` — TESTED
    - `FIRM-001` — status `302` — opposite markers `0`
    - `FIRM-002` — status `302` — opposite markers `0`
  - `/intake/<intake_id>/recommendations/<workflow_key>/launch-prep` — UNRESOLVED_ROUTE
  - `/intake/<intake_id>/recommendations/<workflow_key>/bridge` — UNRESOLVED_ROUTE
  - `/intake/<intake_id>/recommendations/<workflow_key>/bridge-summary` — UNRESOLVED_ROUTE

### `ISO-012` — `intake_export_logs.intake_id` = `INTAKE-0005`

- Outcome: **NO_RESOLVABLE_GET_ROUTE**
- Database rows: **10**
- Route tests: **0**

### `ISO-013` — `intake_final_draft_gate_actions.intake_id` = `INTAKE-0005`

- Outcome: **NO_RESOLVABLE_GET_ROUTE**
- Database rows: **6**
- Route tests: **0**

### `ISO-014` — `intake_review_gate_actions.intake_id` = `INTAKE-0005`

- Outcome: **NO_RESOLVABLE_GET_ROUTE**
- Database rows: **2**
- Route tests: **0**

### `ISO-015` — `workspaces.owner_id` = `ADMIN_OWNER_001`

- Outcome: **OPPOSITE_FIRM_DATA_EXPOSURE_DETECTED**
- Database rows: **7**
- Route tests: **3**
  - `/discussions/new` — TESTED
    - `FIRM-001` — status `200` — opposite markers `0`
    - `FIRM-002` — status `200` — opposite markers `1`
  - `/documents/generate` — TESTED
    - `FIRM-001` — status `200` — opposite markers `0`
    - `FIRM-002` — status `200` — opposite markers `1`
  - `/hosted-repair-admin-access-once` — TESTED
    - `FIRM-001` — status `302` — opposite markers `0`
    - `FIRM-002` — status `302` — opposite markers `0`

## Write Function Sandbox Readiness

- `update_app_user(username, data)` — SANDBOX_READY_REQUIRES_CONTROLLED_PAYLOAD — mutation executed: **False**
- `update_app_user_password(username, password_hash)` — SANDBOX_READY_REQUIRES_CONTROLLED_PAYLOAD — mutation executed: **False**
- `update_distribution_record(distribution_id, updates)` — SANDBOX_READY_REQUIRES_CONTROLLED_PAYLOAD — mutation executed: **False**
- `update_trust_fields(trust_id, updates)` — SANDBOX_READY_REQUIRES_CONTROLLED_PAYLOAD — mutation executed: **False**
- `update_trust_minute_execution(minute_id, data)` — SANDBOX_READY_REQUIRES_CONTROLLED_PAYLOAD — mutation executed: **False**

## Control Conclusion

**FAIL:** At least one Firm 1/Firm 2 response contained a marker unique to the opposite firm's database row.
