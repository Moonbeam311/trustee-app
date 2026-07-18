# Audit-Expected Active-State Reconciliation

## 1. Purpose

Step 25AL-R1 reconciles the Step 25AL active database delta, proves the change was expected security-denial audit logging, establishes the current active database as the new continuity baseline, and records the safe clone method used to finish core product operator acceptance without further active database writes.

## 2. Baselines

| Item | Historical pre-Step-25AL | Current post-denial-test |
| --- | --- | --- |
| Active DB SHA-256 | `6E9E3EF0AE596FB296972B99EA4ED293DB8C5DBD4A64A03AA4FBB0C0CB7A6C36` | `7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525` |
| Active DB size | `3096576` | `3096576` |
| Audit count | `559` | `569` |
| Transfer count | `14` | `14` |
| Trust count | `22` | `22` |
| Matter count | `1` | `1` |
| User count | `7` | `7` |
| Policy SHA-256 | `660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361` | `660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361` |

Current active inventory: page count `756`, page size `4096`, schema version `404`, table count `132`, role count `0`, permission count `15`, role-permission count `25`, certificate count `3`, Compliance object count `[]`, System Observation object count `[]`.

## 3. Comparison Method

BASELINE_COMPARISON_MODE=CONSTRAINED

No preserved old database copy matching `6E9E3EF0AE596FB296972B99EA4ED293DB8C5DBD4A64A03AA4FBB0C0CB7A6C36` was found in the local database-file search. Same-size local candidates existed, but their hashes did not match the historical baseline. The reconciliation therefore uses preserved Step 25AK counts, current table inventory, exact new audit-row inspection, hash-chain continuity from audit row `559`, and active policy verification. It does not claim byte-for-byte row-level proof for the historical pre-test database.

Ignored local snapshots were created under `audit/runtime_sandbox/STEP-25AL-R1/`:

| Snapshot | SHA-256 | Purpose |
| --- | --- | --- |
| `active_reconciled_snapshot.db` | `7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525` | Frozen copy of the reconciled active DB |
| `step25al_acceptance_clone.db` | Started at `7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525` | Clone used for remaining acceptance checks |

## 4. Schema Comparison

SCHEMA_COMPARISON_RESULT=CONSTRAINED_PASS

Current active schema remained internally consistent: SQLite integrity check was `ok`, foreign-key check returned zero rows, schema version was `404`, and table count was `132`. No active migration was run in Step 25AL or Step 25AL-R1.

## 5. Non-Audit Table Comparison

NON_AUDIT_TABLE_COMPARISON_RESULT=CONSTRAINED_PASS

The active DB count evidence matched the preserved Step 25AK baseline for the protected business-state counts: transfer count `14`, user count `7`, trust count `22`, matter count `1`, role-permission count `25`, Compliance objects `[]`, and System Observation objects `[]`. No active export, upload, archive execution, recovery action, Compliance activation, or System Observation persistence activation was performed.

Clone testing provided a full current-to-clone row-digest comparison. After the clone acceptance pass, only `audit_log` changed and `sqlite_sequence` advanced because the audit table appended rows. No non-audit business table digest changed in the clone.

## 6. Audit-Log Delta

Exactly ten rows were appended to the active audit log during the Step 25AL stop-window. All ten are security-denial records tied to the routes and roles tested.

| Audit ID | Timestamp UTC | Actor | Role/Firm | Event | Entity | Context | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 560 | `2026-07-18 12:46:45` | `admin` | Admin / FIRM-001 | `transfer_firm_access_denied` | `T-0014` | Transfer FIRM-002 viewed from FIRM-001 session | EXPECTED_TRANSFER_FIRM_SCOPE_DENIAL |
| 561 | `2026-07-18 12:46:46` | `admin` | Admin / FIRM-001 | `transfer_firm_access_denied` | `T-0014` | Transfer review outside active firm scope | EXPECTED_TRANSFER_FIRM_SCOPE_DENIAL |
| 562 | `2026-07-18 12:46:46` | `admin` | Admin / FIRM-001 | `transfer_firm_access_denied` | `T-0014` | Transfer archive handoff outside active firm scope | EXPECTED_TRANSFER_FIRM_SCOPE_DENIAL |
| 563 | `2026-07-18 12:46:46` | `admin` | Admin / FIRM-001 | `transfer_firm_access_denied` | `T-0014` | Transfer archive audit trail outside active firm scope | EXPECTED_TRANSFER_FIRM_SCOPE_DENIAL |
| 564 | `2026-07-18 12:47:49` | `viewer` | Viewer / FIRM-001 | `role_denied` | `viewer` | `users_dashboard` requires Admin | EXPECTED_RESTRICTED_USER_DENIAL |
| 565 | `2026-07-18 12:47:49` | `viewer` | Viewer / FIRM-001 | `role_denied` | `viewer` | `role_dashboard` requires Admin | EXPECTED_RESTRICTED_USER_DENIAL |
| 566 | `2026-07-18 12:47:49` | `viewer` | Viewer / FIRM-001 | `role_denied` | `viewer` | `permissions_dashboard` requires Admin | EXPECTED_RESTRICTED_USER_DENIAL |
| 567 | `2026-07-18 12:47:49` | `viewer` | Viewer / FIRM-001 | `role_denied` | `viewer` | `security_dashboard` requires Admin | EXPECTED_RESTRICTED_USER_DENIAL |
| 568 | `2026-07-18 12:47:50` | `viewer` | Viewer / FIRM-001 | `permission_denied` | `viewer` | `admin_audit_log` requires `view_audit` | EXPECTED_RESTRICTED_USER_DENIAL |
| 569 | `2026-07-18 12:47:50` | `viewer` | Viewer / FIRM-001 | `trust_access_denied` | `viewer` | `trust_detail`, Trust `TR-022` | EXPECTED_RESTRICTED_USER_DENIAL |

TEN_NEW_AUDIT_ROWS_CLASSIFIED=10
TRANSFER_DENIAL_ROWS=4
RESTRICTED_VIEWER_DENIAL_ROWS=6
UNEXPLAINED_AUDIT_EVENTS=0

## 7. Existing Audit-Row Integrity

ORIGINAL_AUDIT_ROWS_UNCHANGED=CONSTRAINED_BY_ID_RANGE_AND_HASH_CHAIN

Rows `560` through `569` are subsequent to the preserved old maximum audit ID `559`. Row `560` has `previous_hash` equal to the known row `559` `entry_hash`, and each appended row chains to the prior appended row. No evidence indicates deletion or rewrite of the original audit rows, but because no old matching database copy was found, this is constrained proof rather than full row-by-row proof.

## 8. Policy Integrity

The export policy remained unchanged throughout Step 25AL and Step 25AL-R1.

| Item | Value |
| --- | --- |
| Policy SHA-256 | `660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361` |
| Policy size | `123` |
| `strict_packet_export` | `true` |
| `allow_user_creation` | `true` |
| `read_only_mode` | `false` |
| `allow_exports` | `false` |

## 9. Reconciliation Decision

RECONCILED_CONSTRAINED_PROOF

The active DB SHA changed because governed denial-audit records were appended. The ten appended rows are explained, expected, and security-related. No business-state mutation is accepted or authorized by this decision.

## 10. New Active Continuity Baseline

NEW ACTIVE DB CONTINUITY BASELINE

| Item | Value |
| --- | --- |
| DB SHA-256 | `7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525` |
| DB size | `3096576` |
| Audit-log count | `569` |
| Transfer count | `14` |
| Compliance objects | `[]` |
| System Observation objects | `[]` |
| Policy SHA-256 | `660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361` |

The prior SHA remains the historical pre-Step-25AL baseline.

## 11. Safe Clone Test Method

The app database override contract was confirmed as `DB_PATH`.

Flask command:

```text
cd ~/Desktop/trustee-app-clean
export FLASK_APP=app.py
export FLASK_ENV=development
export DB_PATH="audit/runtime_sandbox/STEP-25AL-R1/step25al_acceptance_clone.db"
flask run
```

Browser address: `http://127.0.0.1:5000`

A storage diagnostic confirmed the running app used `step25al_acceptance_clone.db` before acceptance checks continued.

## 12. Clone Test Delta

| Item | Value |
| --- | --- |
| Clone starting SHA | `7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525` |
| Clone final SHA | `2165DB6B2C4E74BB61942BB68C7DAAB52F50B184F5A9E99FE3578A3D936F4E1B` |
| Changed tables | `audit_log`, `sqlite_sequence` |
| Audit-log delta | `569 -> 576` |
| Non-audit business table changes | `0` |

Clone rows `570` through `576` were expected denial/security audit rows from one wrong-firm transfer denial and six restricted-viewer denials. `sqlite_sequence` changed only because `audit_log` advanced.

## 13. Active DB Preservation During Clone Testing

ACTIVE_UNCHANGED_DURING_CLONE_TESTING=True

After clone testing, active DB SHA remained `7958CAFE5AFBED418A093A32DADA9E07FCA8A87D90A0F3D23BF81C9B1C565525`, audit count remained `569`, transfer count remained `14`, and policy SHA remained `660ED85445BB8672E2082C410772F53C76D1AA0732FF62A6BFB68B04FE544361`.

## 14. Limitations

No old matching database copy was found, so this report does not claim RECONCILED_FULL_PROOF. The active delta is accepted only as RECONCILED_CONSTRAINED_PROOF, supported by exact audit-row inspection, unchanged preserved counts, unchanged policy, unchanged active state during clone testing, and clone row-digest evidence showing denial tests affect only audit bookkeeping.

## 15. Decision

Expected security-denial audit logging is permitted evidence. The ten audit rows were not deleted, rolled back, or rewritten. All non-audit business-state changes remain prohibited.
