# Compliance Review Production Activation Plan H.6E

This H.6E record is a readiness artifact. It does not activate Compliance Review persistence, seed Compliance permissions into `trustee_app.db`, or authorize production execution. Production activation remains blocked until every go/no-go gate is signed off in a later controlled phase.

## Implementation Inventory

| File or area | Classification | Production note |
| --- | --- | --- |
| `docs/compliance_review_activation_architecture_h6b.md` | DOCUMENTATION_ONLY | Defines H.6B architecture and temporary activation boundary. |
| `migrations/activate_compliance_review_foundation.py` | PRODUCTION_READY_WITH_PERMISSION_DEPENDENCY | Schema activation is command-line only and currently refuses the normal database during H.6B-H.6E validation. |
| `services/services_compliance_reviews.py` | PRODUCTION_READY_WITH_PERMISSION_DEPENDENCY | Service functions validate lifecycle, firm scope, authority, idempotency, audit chain, and foundation availability. |
| `app.py` Compliance Review routes | PRODUCTION_READY_WITH_PERMISSION_DEPENDENCY | Browser registry/detail/write routes fail closed before activation and require session authority after temporary activation. |
| `templates/compliance_reviews/registry.html` | PRODUCTION_READY_WITH_PERMISSION_DEPENDENCY | Read-only registry shell plus gated create link. |
| `templates/compliance_reviews/detail.html` | PRODUCTION_READY_WITH_PERMISSION_DEPENDENCY | Lifecycle forms include expected version, CSRF/session integrity, authority basis, and confirmations. |
| `templates/compliance_reviews/create.html` | PRODUCTION_READY_WITH_PERMISSION_DEPENDENCY | Create form is operator-facing but remains unavailable until foundation activation. |
| H.6B-H.6D audit scripts | AUDIT_ONLY | Validate temporary-only activation, service workflow, route controls, UI controls, maker-checker, and preservation. |
| `migrations/add_compliance_review_permissions.py` | TEMPORARY_VALIDATION_ONLY | H.6E permission migration rehearsal. It must refuse normal `trustee_app.db` during H.6E. |
| `config/compliance_review_activation_manifest.example.json` | DOCUMENTATION_ONLY | Example manifest only; no live secrets or authorization token. |

Code that must not be published as production-ready without further authorization: temporary activation tokens, test-only session authority injection, H.6E migration refusal logic, and any route access based only on role labels without explicit permissions and institutional authority.

## Existing Authorization Inventory

Current roles found in the normal database are `Admin`, `Trustee`, and `Viewer`.

Current permission names are:

- `create_trust`
- `edit_trust`
- `export_documents`
- `generate_documents`
- `manage_permissions`
- `manage_roles`
- `manage_tax_reports`
- `manage_users`
- `matter_detail`
- `matters_dashboard`
- `new_matter`
- `view_audit`
- `view_dashboard`
- `view_documents`
- `view_security`

Existing broad permissions such as `manage_permissions`, `view_audit`, `edit_trust`, and `manage_roles` are not sufficient to govern Compliance Review actions. Compliance Review needs explicit permissions plus record-level institutional authority.

## Compliance Permission Model

Minimum production permission set:

| Permission | Category | Default role assignment |
| --- | --- | --- |
| `view_compliance_workspace` | Ordinary operator | Admin, Trustee, Viewer |
| `view_compliance_reviews` | Ordinary operator | Admin, Trustee, Viewer |
| `create_compliance_review` | Ordinary operator | Admin, Trustee |
| `edit_compliance_review` | Ordinary operator | Admin, Trustee |
| `assign_compliance_reviewer` | Reviewer administration | Admin |
| `add_compliance_evidence` | Evidence | Admin, Trustee |
| `verify_compliance_evidence` | Evidence checker | Admin |
| `issue_compliance_findings` | Reviewer | Admin |
| `manage_compliance_remediation` | Remediation owner | Admin, Trustee |
| `submit_compliance_remediation` | Remediation submitter | Admin, Trustee |
| `verify_compliance_remediation` | Remediation checker | Admin |
| `approve_compliance_exception` | Approver | MANUAL_INSTITUTIONAL_ASSIGNMENT_REQUIRED |
| `approve_compliance_review` | Approver | MANUAL_INSTITUTIONAL_ASSIGNMENT_REQUIRED |
| `certify_compliance_review` | Certifier | MANUAL_INSTITUTIONAL_ASSIGNMENT_REQUIRED |
| `close_compliance_review` | Closure | Admin |
| `reopen_compliance_review` | Reopening | MANUAL_INSTITUTIONAL_ASSIGNMENT_REQUIRED |
| `supersede_compliance_review` | Supersession | MANUAL_INSTITUTIONAL_ASSIGNMENT_REQUIRED |
| `archive_compliance_review` | Archive | MANUAL_INSTITUTIONAL_ASSIGNMENT_REQUIRED |
| `view_compliance_audit` | Audit read | Admin |
| `activate_compliance_foundation` | Institutional activation | MANUAL_INSTITUTIONAL_ASSIGNMENT_REQUIRED |
| `execute_compliance_migration` | Migration execution | MANUAL_INSTITUTIONAL_ASSIGNMENT_REQUIRED |

Activation and migration permissions must never be granted through ordinary Compliance administration.

## Role-To-Permission Governance

| Role | Default Compliance permissions | Manual institutional permissions |
| --- | --- | --- |
| Admin | View workspace/reviews, create/edit, assign reviewer, add/verify evidence, issue findings, manage/submit/verify remediation, close review, view audit | approve exception, approve review, certify review, reopen, supersede, archive, activate foundation, execute migration |
| Trustee | View workspace/reviews, create/edit, add evidence, manage/submit remediation | reviewer assignment, evidence verification, findings issuance, approvals, certification, reopen, supersede, archive, activation, migration |
| Viewer | View workspace/reviews only | none |

Role membership alone is never institutional authority. Every material create, lifecycle, approval, certification, exception, activation, migration, and rollback action also needs an authority basis and record-level maker-checker validation.

## Maker-Checker Production Matrix

Restrictions are transaction-level and actor-history-based:

- Creator cannot approve their own review where approval is required.
- Assigned reviewer cannot certify the same review where separation is required.
- Evidence submitter cannot verify their own evidence.
- Remediation submitter cannot verify their own remediation.
- Exception requester cannot approve their own exception.
- Activation requester cannot be sole activation approver.
- Migration executor cannot be sole post-migration certifier.
- Rollback executor cannot be sole rollback certifier.

Permissions allow a person to attempt an action; authority and maker-checker history decide whether the transaction may complete.

## Permission Migration Architecture

`migrations/add_compliance_review_permissions.py` is the proposed permission migration.

Required controls:

- explicit `--database PATH`;
- exactly one of `--dry-run` or `--apply`;
- explicit `--authorization-token`;
- refusal of normal `trustee_app.db` during H.6E;
- verification of reconciled `ux_role_permissions_role_permission`;
- transactional inserts only;
- idempotent repeat apply;
- no duplicate pairs;
- reversible JSON manifest;
- no unrelated table mutation.

## Activation Authority Model

Activation requires named requester, named approver, authority basis, target database identity, migration name, schema version, pre-migration hash, verified backup reference, approved permission baseline, planned activation window, rollback owner, post-activation verifier, and certification owner.

Two-person approval is mandatory. Activation fails closed when requester equals approver, backup is missing, database hash differs, permission baseline is incomplete, migration audit fails, staging is unsafe, schema conflict exists, connection policy is unsafe, prior activation is incomplete, or rollback artifact cannot be verified.

## Production Backup Plan

The Compliance activation backup must be new and separate from the H.6A authorization rollback backup.

Required backup evidence:

- byte-for-byte pre-activation database backup;
- safe SQLite online backup or equivalent if production is active;
- backup outside repository;
- timestamped filename;
- SHA-256 and size;
- `integrity_check` and `foreign_key_check`;
- row counts and schema manifest;
- logical table hashes;
- permission baseline manifest;
- governance and audit-log counts;
- sidecar inventory;
- storage-location record;
- rollback owner and retention period.

## Production Migration Execution Plan

Mandatory sequence:

1. Freeze write operations.
2. Verify repository and deployed code version.
3. Verify normal database hash.
4. Verify authorization baseline.
5. Create and verify Compliance activation backup.
6. Verify activation approval record.
7. Run permission migration only if separately authorized.
8. Verify permission additions.
9. Run Compliance activation migration.
10. Verify all tables and indexes.
11. Verify activation registry.
12. Import application twice.
13. Verify no import-time writes.
14. Run read-only route checks.
15. Run controlled authorized create test only if expressly permitted.
16. Verify audit chain.
17. Verify maker-checker controls.
18. Certify activation.
19. Reopen normal operations.
20. Retain rollback artifacts.

Stop points exist after every verification or mutation step. Permission migration and schema activation are separate actions.

## Rollback Plan

Rollback triggers include migration failure, schema mismatch, foreign-key failure, integrity failure, missing table/index, partial activation registry, permission baseline mismatch, import-time mutation, route regression, authorization bypass, maker-checker failure, audit-chain failure, unrelated-table mutation, or inability to certify.

Rollback procedure:

1. Stop application writes.
2. Preserve failed database for forensic analysis.
3. Restore verified activation backup.
4. Verify restored hash and logical manifests.
5. Verify permissions.
6. Verify application import.
7. Verify unavailable-state behavior.
8. Write bounded rollback record outside the restored DB if needed.
9. Certify rollback.
10. Prevent automatic retry.

Silent retry is prohibited.

## Production Route Exposure Plan

Before activation: Registry returns 503, Detail returns 503, Create is unavailable, write routes fail closed, and controls are not displayed.

After activation and permission migration: Registry requires view permission, Detail requires firm scope, Create requires create permission and authority, controls require lifecycle and authority, direct crafted POST remains protected, and activation/migration execution remains outside browser routes.

Response semantics:

- Foundation unavailable: 503, no record created.
- Permission denied: 403.
- Wrong firm: 404 or 403 fail-closed response.
- Record missing: 404.
- Stale version: 409 or validation failure without mutation.
- Invalid transition: 400 or validation failure without mutation.
- Archived mutation: fail closed without mutation.
- Migration pending: 503.
- Activation failed: 503 and operator-safe message.
- Activation rolled back: 503 until recertified.

## Production Configuration Boundary

Activation must not rely only on table existence. The activation check should verify complete schema, expected schema version, activation registry status, migration identity, verification status, and no rollback-active state. If configuration and schema disagree, the system fails closed.

## Deployment And Hosted Database Analysis

Hosted production must separately confirm deployed DB path, persistent storage path, backup location, upload path, export path, restart behavior, multiple-process risk, SQLite locking risk, migration execution access, rollback access, environment-variable controls, log retention, deployed file hash verification, ability to pause writes, and code/migration deployment order.

Railway-specific watchpoints: persistent volume paths must be verified immediately before activation, a restart during migration must be prevented, file-hash verification must be possible from the running environment, and SQLite write locking must be treated as a deployment risk.

## Production-Like Temporary Rehearsal

H.6E rehearsal uses temporary database copies only:

- baseline verification;
- permission migration dry-run/apply/repeat;
- activation backup creation;
- activation migration apply/repeat;
- import read-only verification;
- route exposure verification;
- authorized and unauthorized workflow checks;
- maker-checker workflow checks;
- post-activation certification;
- forced rollback and restored unavailable-state verification.

## Failure-Injection Rehearsal

Simulated failures must stop safely for wrong pre-migration hash, missing backup, invalid activation token, requester equals approver, missing permission baseline, partial permission migration, partial Compliance schema, migration exception, foreign-key failure, invalid activation-registry state, import mutation, unauthorized create, maker-checker failure, audit-chain corruption, and rollback hash mismatch.

## Post-Activation Certification Plan

Database checks: expected tables, indexes, constraints, activation-registry status, integrity, foreign keys, unrelated-table preservation, approved role-permission baseline, and no duplicate permissions.

Application checks: import read-only, route registration, registry/detail status, write-route protection, no render-side writes, and no automatic migration.

Authorization checks: view/create allow-deny, wrong-firm block, maker-checker enforcement, activation restriction, and migration restriction.

Workflow checks: one controlled review may be created only if authorized, audit chain is valid, lifecycle controls are valid, archive immutability is valid, and rollback artifact remains verified.

## Go/No-Go Checklist

No production activation may occur unless every mandatory gate is PASS.

| Gate | Required evidence | Responsible role | Pass/Fail | Blocking conditions | Sign-off |
| --- | --- | --- | --- | --- | --- |
| REPOSITORY READY | exact commit, clean staging, reviewed untracked set | release owner |  | wrong branch, unsafe staging |  |
| DATABASE READY | hash, integrity, FK, row counts, no conflicts | database owner |  | hash mismatch, integrity/FK failure |  |
| BACKUP READY | verified new activation backup outside repo | rollback owner |  | missing or unverifiable backup |  |
| PERMISSIONS READY | approved permission manifest and role matrix | security owner |  | missing baseline or broad admin grant |  |
| AUTHORITY READY | requester, approver, basis, window | institutional approver |  | same requester/approver |  |
| MIGRATION READY | dry-run/apply/repeat rehearsal | migration executor |  | non-idempotent migration |  |
| ROLLBACK READY | tested restore procedure | rollback owner |  | rollback hash mismatch |  |
| DEPLOYMENT READY | hosted path, persistence, pause-write plan | deployment owner |  | unknown live DB path |  |
| AUDITS READY | all H.6B-H.6E audits pass | QA owner |  | failing audit |  |
| OPERATOR READY | route exposure and training notes | operations owner |  | unclear status messaging |  |
| CERTIFICATION READY | post-activation certification owner | certification owner |  | no named certifier |  |

## Remaining Risks

- SQLite concurrent write locking during hosted activation.
- Deployment restart during migration.
- Stale code against migrated schema.
- Incomplete permission assignments.
- Excessive Admin privileges if manual institutional permissions are over-granted.
- Rollback under active sessions.
- Audit-chain performance as review volume grows.
- Identifier concurrency under multiple workers.
- Long-running review queries without pagination tuning.
- Cross-firm leakage if firm scope is bypassed.
- Operator misunderstanding of readiness versus activation.
- Activation-registry mismatch.
- Backup retention and access control.

## Current H.6E Status

Architecture complete, temporary validation complete, production readiness assessed, permission migration prepared, activation migration prepared, and production activation not yet executed.
