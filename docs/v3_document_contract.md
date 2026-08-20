# V3 Document Producer/Adapter Contract

Status: bounded producer/adapter boundary established by `V3-SVC-DOC-1`.

## Source-of-truth rule

Generated documents are derived outputs. Governed Trust, Governance, Execution,
Certificate, Continuity, document-registry, and archive records remain their
respective authoritative sources unless an existing lifecycle explicitly
establishes a separately governed finalized record. Rendering never fills a
missing institutional fact with an invented value and never grants authority,
approval, execution, certification, or finality.

## Canonical owner and public interface

`services/services_document_contract.py` owns this bounded contract:

- `produce_trust_document_context(...)`
- `describe_output_capabilities()`
- `render_document(context, output_format)`
- `build_delivery_metadata(context, output_format)`
- `list_document_references(trust_id, *, authorization_check)`
- `get_document_reference(document_id, trust_id, *, authorization_check)`

The producer reuses `services/services_trust_contract.py` for canonical firm and
authorization scope. Existing Fiduciary and Account/Asset contracts remain
available to future producer-specific phases but are not automatically embedded
in ordinary Trust output.

## Producer contract

The implemented producer accepts an authorized Trust ID, documented output type,
and optional caller-supplied generation actor/time. It emits canonical source
identity, a safe allowlist of Trust fields, missing optional fields, provenance,
and explicit derived/transient/not-final output state. Actor/time remain `NOT
DOCUMENTED` when the caller has no supported value.

Missing, denied, and cross-firm sources return no context. The producer neither
mutates the source nor emits audit, export, document, execution, or archive rows.
Other governed source producers are NOT IMPLEMENTED in this phase.

## Rendering and delivery adapters

`render_document` supports transient UTF-8 TXT and JSON only. TXT preserves
blank optional values; JSON preserves the canonical context. Unsupported formats
fail explicitly. Existing HTML templates, PDF builders, CSV exporters, and ZIP
packet generators retain their current owners and are not claimed as migrated.

Delivery metadata provides a sanitized filename, media type, content disposition,
and `persistence: none`. It does not send a response, write a file, or record an
export.

## Persistence and provenance distinction

The existing `documents` table remains a metadata registry read through scoped
reference functions. A transient render never creates a document row. Controlled
DOCX/PDF exports, export history, generated execution documents, certificate
records, archive packets, and finalized artifacts remain distinct persistence
and lifecycle contracts. This facade exposes no persistence adapter because no
single canonical write contract is documented for all generated outputs.

Producer provenance records source type/ID/firm, producer name, and supported
caller-supplied generation actor/time. A universal generated-output checksum,
storage reference, or finality rule is NOT DOCUMENTED here.

## Security, authorization, and no mutation

Trust authorization remains mandatory and caller-owned through the canonical
Trust callback. Document references require exact active-firm and Trust scope.
Passwords, PINs, recovery/backup codes, security answers, tokens, private keys,
and payment-card secrets are rejected before rendering. Vault or digital-account
metadata is not automatically inserted.

No public function mutates Trust, Fiduciary, Account/Asset, Governance,
Continuity, Execution, document, export, certificate, or archive state.

## Existing production inventory and compatibility

Current Trust output functions in `app.py` are mixed producer/PDF/delivery
implementations. Governance supplies stable context and text producers.
Certificate, execution, controlled-export, report, archive, and packet modules
retain specialized producers, renderers, persistence, and delivery behavior.
Universal registry/object/adapters remain read surfaces; their broad legacy
scope and inferred verification claims are not adopted by this contract.

No route, template, generator, or caller is rewired. Canonical context remains
compatible with the existing universal document object builder through explicit
source type/ID and payload mapping.

## Known limitations and future consumers

Only Trust-source context and transient TXT/JSON rendering are implemented.
HTML/PDF/CSV/ZIP production, generalized source adapters, persistence, checksums,
execution/finality, and archive delivery remain producer-specific or NOT
DOCUMENTED. Execution, Archive, Governance, and a future successor-handoff
consumer may reuse references/context in later authorized phases; no such
integration is implemented here.
