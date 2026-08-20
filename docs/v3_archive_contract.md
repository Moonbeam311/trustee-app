# V3 Archive Package Descriptor Contract

## Canonical owner and interface

`services/services_archive_contract.py` owns the canonical V3 read-only descriptor facade for the repository's strongest safely scoped archive representation: recorded transfer archive handoffs.

- `describe_transfer_archive_package(transfer_id, trust_id, authorization_check=..., handoff_id=...)`
- `list_transfer_archive_packages(trust_id, authorization_check=...)`

Missing, denied, cross-firm, wrong-Trust, and mismatched-source reads return the same safe `None` or empty-list result. Missing required read schema raises `ArchiveContractError`; the facade never creates schema.

## Package, manifest, handoff, and export separation

A descriptor is an in-memory read representation. Its `items` inventory contains only existing handoff, correction, and export-history records. A concrete export manifest is generated content; package generation creates ZIP/TXT/CSV/PDF output; handoff is a governed custody record; export history records delivery. None of those mutations occurs here. A package's required-item policy is `NOT DOCUMENTED` unless a producer-specific contract establishes it.

## Source and firm scope

Every descriptor requires the caller's explicit authorization decision, canonical Trust access, a transfer returned by the canonical Execution contract, and exact `firm_id`, `trust_id`, and `transfer_id` equality. An archive or handoff identifier cannot broaden source scope or disclose another firm's metadata.

## Integrity and finalization semantics

The descriptor exposes seal references and stored `archive_export_history.export_hash` values exactly as recorded. Those values are labelled recorded export hashes; they are not recomputed, verified, or conflated with manifest, content, package, file, or V3 control hashes. `archive_status` is reported as handoff state, not package certification. File existence never promotes a package to finalized, frozen, or certified.

## Mutation and ownership boundaries

Descriptor calls do not generate files or manifests, create/correct handoffs, write export history, finalize or freeze archives, mutate Continuity or Execution, or create recovery records. Continuity asset packet assembly/finalization, final-record archive records, institutional execution freezes, document rendering, transfer mutations, delivery routes, and disaster-recovery topology retain their existing independent owners. In particular, `services_execution_recovery.get_archive_topology()` is excluded because it seeds and updates recovery state.

## Provenance and limitations

The descriptor preserves recorded handoff actor/capacity/time, correction records, export references, custody classification, status, seals, and hashes. It does not claim legal custody sufficiency or integrity certification. `final_record_archive` does not carry a canonical Trust relationship, so it is not exposed through this reusable Trust-scoped facade. Continuity package required-item rules, stored manifests, generalized package identity, retention policy, restoration, and cross-domain archive lifecycle remain `NOT DOCUMENTED` here.

Safe future consumers include read-only Archive views and successor-handoff planning that need recorded handoff/export facts without producing or changing archive state.
