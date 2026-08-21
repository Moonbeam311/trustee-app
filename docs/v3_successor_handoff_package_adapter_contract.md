# V3 Successor Handoff Package Adapter Contract

Status: `V3-THO-PKG-1 — IMPLEMENTED / REGRESSION VERIFIED`

## Owner and interface

`services/services_handoff_package_adapter.py` owns the ephemeral
`TrustSuccessorHandoffPackageDescriptor`. Its public
`build_successor_handoff_package_descriptor(...)` function delegates all source
composition and authorization to the certified unified Handoff aggregate. It
owns no persistence, source record, package lifecycle, file, manifest, Archive
handoff, export history, legal decision, or application permission.

## Supported sections and sources

The descriptor contains Trust identity, Fiduciary authority evidence,
Successor Acceptance state/evidence, Continuity/readiness/responsibilities,
Account/Asset inventory, Governance context, optional Execution context,
Document references, Archive descriptors, unresolved gaps, and provenance.
Each section names its canonical owner and is classified as `INCLUDED`,
`REFERENCE ONLY`, `NOT AVAILABLE`, `NOT DOCUMENTED`, or `NOT APPLICABLE`.

Document and Archive entries are references only. Execution is reference-only
when an existing identifier is supplied. Missing Document or Archive records do
not become universal gaps because no universal required-item policy is
documented. Canonical provenance identifiers form a deterministic, ordered
content index; no second package identity or hash system is created.

## Acceptance and Continuity semantics

The certified Acceptance aggregate section preserves accepted, pending,
designated-without-Acceptance, legacy/unverified, declined, withdrawn, and
superseded meanings where present. Document presence never proves Acceptance.
Continuity data remains separately owned. Descriptor assembly does not create a
profile, alter readiness, activate Continuity, assign responsibility, or make
Acceptance a universal activation prerequisite.

## Document, Archive, and generation boundary

`PACKAGE DESCRIPTOR != ARCHIVED PACKAGE`. The adapter produces no ZIP, PDF,
manifest, Document, handoff, export-history, finalization, seal, or recovery
record. Existing Document and Archive contracts remain the only owners of their
facts. Actual output production or Archive registration requires a separately
authorized producer action and its existing permissions.

## Scope, security, and no mutation

The caller supplies the existing Handoff authorization callbacks. Missing,
denied, cross-firm, wrong-Trust, and mismatched source contexts fail closed
through canonical contracts. Successor, Acceptance, Fiduciary, or Continuity
status grants no access. Canonical secret-material validation prohibits
passwords, PINs, recovery codes, security answers, tokens, private keys, and
complete card secrets.

Building a descriptor changes no Trust, Fiduciary authority, Acceptance,
Continuity, responsibility, Governance, Execution, Document, Archive, user,
role, permission, or acknowledgement record. Package completeness, legal
certification, required-item policy, and generated-at time remain explicitly
unsupported or `NOT DOCUMENTED` rather than inferred.
