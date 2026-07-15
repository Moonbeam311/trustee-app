# Compliance Review Controlled Execution Authorization H.6F

This package is a pre-activation authorization template. It is not completed authorization and does not permit production activation by itself.

## Module Identity

- Module key: `compliance_reviews`
- Schema version: `compliance_reviews_h6b_v1`
- Permission migration: `add_compliance_review_permissions_h6e`
- Compliance activation migration: `activate_compliance_review_foundation_h6b`
- Required application HEAD: `REPLACE_WITH_VERIFIED_COMMIT`
- Target environment: `REPLACE_WITH_TARGET_ENVIRONMENT`
- Target database path: `REPLACE_WITH_VERIFIED_PERSISTENT_DB_PATH`

## Required Database Baseline

- Expected pre-activation SHA-256: `REPLACE_WITH_PRE_ACTIVATION_DATABASE_SHA256`
- Expected role-permission baseline: `25 role_permissions rows, 25 distinct pairs, duplicate groups 0, ux_role_permissions_role_permission present`
- Expected governance counts: `25 governance_relationships, 51 governance_relationship_audit_ledger`
- Expected Compliance objects before activation: `none`
- Expected System Observation objects before activation: `none`

## Backup Requirements

- Compliance activation backup path: `REPLACE_WITH_BACKUP_PATH_OUTSIDE_REPOSITORY`
- Backup SHA-256: `REPLACE_WITH_BACKUP_SHA256`
- Backup size: `REPLACE_WITH_BACKUP_SIZE`
- Backup integrity_check: `REPLACE_WITH_RESULT`
- Backup foreign_key_check: `REPLACE_WITH_RESULT`
- Backup row-count manifest: `REPLACE_WITH_MANIFEST_REFERENCE`
- Backup retention owner: `REPLACE_WITH_ROLLBACK_OWNER`

The H.6A authorization rollback backup is retained for authorization-baseline recovery only. It is not the Compliance activation rollback backup.

## Institutional Authority

- Activation requester: `REPLACE_WITH_NAMED_INSTITUTIONAL_REQUESTER`
- Activation approver: `REPLACE_WITH_DIFFERENT_NAMED_INSTITUTIONAL_APPROVER`
- Authority basis: `REPLACE_WITH_APPROVED_AUTHORITY_BASIS`
- Migration executor: `REPLACE_WITH_NAMED_MIGRATION_EXECUTOR`
- Post-migration verifier: `REPLACE_WITH_NAMED_VERIFIER`
- Certification owner: `REPLACE_WITH_NAMED_CERTIFICATION_OWNER`
- Rollback owner: `REPLACE_WITH_NAMED_ROLLBACK_OWNER`
- Planned activation window: `REPLACE_WITH_APPROVED_WINDOW`

Requester and approver must be different people where separation is required. Role membership alone is not institutional authority.

## Operational Confirmations

| Gate | Required evidence | Result | Sign-off |
| --- | --- | --- | --- |
| Write-freeze confirmation | Active operator writes paused |  |  |
| Active-connection confirmation | Connection count within safe policy |  |  |
| Repository confirmation | Deployed commit equals required application HEAD |  |  |
| Database confirmation | Database hash equals expected pre-activation SHA-256 |  |  |
| Backup confirmation | New Compliance activation backup verified |  |  |
| Permission-migration authorization | Permission migration separately approved |  |  |
| Schema-migration authorization | Schema migration separately approved |  |  |
| Controlled create-test authorization | Post-activation create test expressly approved or denied |  |  |
| Rollback authorization | Rollback owner and procedure verified |  |  |
| Go/no-go checklist | Every mandatory gate marked PASS |  |  |

## Migration Execution Authorization

Permission migration command must use an explicit database path, exactly one mode, and the approved token reference. It must not run against `trustee_app.db` until the completed controlled execution phase authorizes the target database identity.

Compliance activation migration command must use an explicit database path, exactly one mode, and the approved activation token reference. It must remain outside browser routes and must not be invoked by import, startup, login, render, or request handling.

## Sign-Off Fields

- Activation requester signature: `PENDING`
- Activation approver signature: `PENDING`
- Migration executor signature: `PENDING`
- Post-migration verifier signature: `PENDING`
- Certification owner signature: `PENDING`
- Rollback owner signature: `PENDING`

## Explicit Non-Authorization Statement

An uncompleted package is not authorization. Source publication, passing audits, and this template do not activate Compliance Review persistence and do not permit production activation without completed signatures, verified database identity, verified backup, approved manifest, and all go/no-go gates marked PASS.
