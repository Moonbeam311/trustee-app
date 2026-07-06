# RC2-0D1C — Core Transfer Chain Backfill Plan

Status: Draft Plan — No data changes applied  
Scope: Core transfer-chain tables normalized under RC2-0D1B.

## Purpose

Backfill existing records after the additive schema patch while preserving historical records.

## Target Tables

- transfers
- transfer_actions
- transfer_records
- transfer_support_docs
- ledger_entries
- trust_minutes
- transfer_archive_handoff
- transfer_archive_handoff_corrections
- archive_export_history

## Backfill Principles

1. Do not overwrite populated identity values.
2. Populate blank canonical identity fields from parent records.
3. Preserve legacy compatibility fields such as transfer_id_fk.
4. Do not rewrite historical notes or audit text.
5. Use transfer_id as the central bridge where available.
6. Use transfer_id_fk only as a compatibility bridge where needed.
7. Use trust_id and firm_id from the parent transfer as source of truth.
8. Use record_version = 1.0 for existing records unless already populated.

## Recommended Next Step

Proceed to RC2-0D1D — Dry-Run Backfill Preview before writing any data.
