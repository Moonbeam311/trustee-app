# V3 Fiduciary Authority Read/Decision Contract

Status: canonical read/decision boundary established by `V3-SVC-FID-1`.

## Canonical owner and persistence

`services/services_fiduciary_authority.py` owns the reusable boundary.
`database/db.py` and the existing `fiduciaries` table remain persistence owners.
No CRUD SQL, route, schema, template, or permission model is migrated here.

## Public interface

- `get_fiduciary_by_id(fiduciary_id, *, authorization_check)`
- `list_fiduciaries(*, authorization_check)`
- `list_fiduciaries_for_trust(trust_id, *, authorization_check)`
- `evaluate_authority_evidence(fiduciary_id, *, trust_id=None, capability=None, authorization_check)`

The mandatory authorization callback accepts fiduciary and Trust identifiers
and represents the authenticated caller's existing route/service policy.

## Semantic separation

A Fiduciary record is an institutional registry row. `role_title` is the title
recorded on that row. `authority_scope` is free-text recorded evidence. Neither
field proves legal authority, appointment acceptance, or a specific capability.

Application roles and effective permissions remain separate. An Admin,
Trustee, or Viewer role does not establish substantive authority for a Trust;
likewise, a Fiduciary row never grants an application permission. Every
decision result therefore reports `system_permission_granted: false`.

## Scope and authorization

All queries require the active firm from `database.db.get_current_firm_id` and
include `firm_id`. Trust-specific lists additionally require exact `trust_id`.
Cross-firm, wrong-Trust, denied, and missing records are not disclosed.

The service performs a read-only schema preflight and fails closed with
`FiduciaryAuthorityContractError` when a firm-scoped fiduciary schema is not
available. Authorization omission also fails closed.

## Evidence decision output

The decision describes evidence, not a legal verdict:

- `record_state`: recorded or missing/not visible.
- `authority_evidence_state`: recorded, missing, or unresolved.
- `scope_state`: recorded or unresolved.
- `capability_state`: unresolved when a capability is requested because the
  repository has no controlled capability mapping for free-text scope.
- `acceptance_state`: `not_documented` because the current persisted schema has
  no `acceptance_status` field.
- recorded status, role title, authority scope, and the normalized Fiduciary
  record when visible.

The IIA target model names `appointment_basis` and `acceptance_status`, but the
current table does not persist them. The facade returns these as unavailable;
it does not manufacture values from names, titles, dates, notes, or documents.

## Status, provenance, and failure behavior

The existing observation verifier recognizes Active, Current, Appointed,
Authorized, Accepted, and Verified as active recorded statuses. Other or blank
statuses remain unresolved; revoked or superseded records do not support a
positive evidence state.

Provenance identifies the `fiduciaries` table. A record-specific audit reference
is NOT DOCUMENTED. Creation routes currently emit central `log_change` entries,
but the table does not store a universal provenance link.

Missing, denied, cross-firm, and wrong-Trust reads use safe non-disclosing
results. Unexpected database/runtime failures retain existing propagation.

## No-mutation and compatibility guarantee

The boundary exposes no create, update, delete, transition, permission grant,
acceptance, or lifecycle operation. Reads do not emit audit events or modify
records. Existing dashboard, creation, report, Governance, Trust, Continuity,
and permission callers remain unchanged.

## Known limitations and future consumers

Authority scope is uncontrolled text; capability mapping, appointment basis,
acceptance status, responsibility references, and authoritative legal validity
are NOT DOCUMENTED in the current Fiduciary schema. Trust, Governance,
Continuity, Execution, and a future successor-handoff consumer may reuse this
boundary for recorded evidence only. No integration is implemented or
authorized by this contract.
