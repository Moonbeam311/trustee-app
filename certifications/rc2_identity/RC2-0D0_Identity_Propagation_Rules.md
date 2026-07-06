# RC2-0D0 — Identity Propagation Rules

Status: Draft Standard — No schema changes applied  
Purpose: Define how institutional identity moves from parent records to child records before schema normalization begins.

## Core Principle

Child records must inherit institutional identity from parent records whenever the relationship is created by workflow logic.

A child record should not require manual re-entry of identity fields already known from the parent.

## Canonical Parent Chain

Trust / Matter
    ↓
Transfer
    ↓
Ledger Entry
    ↓
Trust Minute
    ↓
Certificate
    ↓
Archive Handoff
    ↓
Certified Export

## Propagation Rule 1 — Transfer Creation

Parent source: trust / matter / firm context

Transfer should carry:

- firm_id
- trust_id
- matter_id when available
- created_by
- created_at
- updated_at
- status
- capacity
- record_version

## Propagation Rule 2 — Transfer Action History

Parent source: transfer

Transfer action records should inherit:

- firm_id
- trust_id
- matter_id
- transfer_id
- created_by or performed_by
- created_at
- capacity
- status
- record_version

Existing `transfer_id_fk` may remain for compatibility, but new logic should expose canonical `transfer_id`.

## Propagation Rule 3 — Ledger Entry from Transfer

Parent source: transfer

Ledger entries created from a transfer should inherit:

- firm_id
- trust_id
- matter_id
- transfer_id
- created_by
- created_at
- capacity
- status
- record_version

Ledger entries should not rely only on description text to preserve transfer linkage.

## Propagation Rule 4 — Trust Minute from Transfer

Parent source: transfer

Trust minutes generated from transfer finalization should inherit:

- firm_id
- trust_id
- matter_id
- transfer_id
- created_by
- created_at
- updated_at
- capacity
- status
- record_version

Minute-specific fields remain unique:

- minute_id
- certificate_id
- approved_at
- executed_at
- archived_at
- locked

## Propagation Rule 5 — Certificate from Minute / Transfer

Parent source: minute or transfer

Certificates should inherit:

- institution_id when available
- firm_id
- trust_id
- matter_id
- transfer_id when applicable
- minute_id when applicable
- created_by / generated_by
- created_at / generated_at
- capacity
- status
- record_version

Certificate-specific fields remain unique:

- certificate_id
- certificate_type
- certificate_hash
- hash_algorithm
- verification_status

## Propagation Rule 6 — Archive Handoff from Transfer

Parent source: transfer + minute verification + ledger verification

Archive handoff records should inherit:

- firm_id
- trust_id
- matter_id
- transfer_id
- certificate_id when applicable
- created_by / handoff_by
- created_at
- updated_at
- capacity / handoff_capacity
- status / archive_status
- record_version

Archive-specific fields remain unique:

- handoff_id
- archive_id when implemented
- seal_reference
- custody_classification
- correction history

## Propagation Rule 7 — Certified Export from Archive Handoff

Parent source: archive handoff

Certified export records should inherit:

- firm_id
- trust_id
- matter_id
- transfer_id
- handoff_id
- certificate_id when applicable
- created_by / generated_by
- created_at / generated_at
- status
- record_version

Export-specific fields remain unique:

- export_id
- export_scope
- export_hash_sha256
- package_hash_sha256
- manifest_hash_sha256

## Immutability Rule

The following fields should generally not be overwritten after creation:

- institution_id
- firm_id
- trust_id
- matter_id
- transfer_id
- minute_id
- certificate_id
- archive_id
- handoff_id
- created_by
- created_at

Corrections should be handled through correction records, versioning, or superseding records.

## Compatibility Rule

Existing fields such as `transfer_id_fk` may remain for backward compatibility.

New development should prefer canonical identity names:

- transfer_id
- firm_id
- trust_id
- matter_id
- certificate_id
- handoff_id

## First Implementation Target

The first active schema wave should be:

RC2-0D1 — Core Transfer Chain Normalization

Target tables:

- transfers
- transfer_actions
- transfer_records
- transfer_support_docs
- ledger_entries
- trust_minutes
- transfer_archive_handoff
- transfer_archive_handoff_corrections
- archive_export_history

## RC2-0D0 Conclusion

No schema changes are applied by this document. This standard defines how identity should propagate before fields are added, backfilled, or enforced.
