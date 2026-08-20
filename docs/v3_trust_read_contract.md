# V3 Canonical Trust Read Contract

Status: canonical read boundary established by `V3-SVC-TRUST-1`.

## Owner and persistence source

`services/services_trust_contract.py` owns the reusable Trust read boundary.
`database/db.py` remains the persistence owner and supplies the existing
firm-scoped `get_trust_by_id` and `get_all_trusts` operations. The service does
not relocate SQL or own Trust writes.

## Public interface

- `get_trust_by_id(trust_id, *, authorization_check)`
- `list_trusts(*, authorization_check)`
- `trust_is_accessible(trust_id, *, authorization_check)`

The authorization callback accepts a Trust identifier and returns whether the
current caller may access it. It is mandatory and must represent the caller's
existing authenticated role/assignment policy.

## Input and output contract

Trust identifiers are normalized to stripped strings. Blank, denied, missing,
and cross-firm identifiers produce `None` from `get_trust_by_id` and `False`
from `trust_is_accessible`. This shared result avoids cross-firm existence
disclosure.

Successful single-record reads return the existing SQLite row shape from
`database/db.py`. `list_trusts` returns a list of those existing row objects,
limited first by active firm and then by the supplied authorization callback.
This baseline does not normalize records into a new DTO.

## Firm scope

The active firm continues to come from `database.db.get_current_firm_id` under
the established application/session context. The contract does not accept a
browser-supplied or caller-selected firm ID. Existing database reads constrain
Trust queries by `firm_id`.

The boundary performs a read-only schema preflight. If the `trusts` table or
its `firm_id` column is absent, it raises `TrustReadContractError` instead of
invoking the database layer's legacy schema-ensure mutation.

## Authorization

Authentication, roles, permissions, and Trust assignments remain owned by the
calling route or service. The boundary requires an explicit
`authorization_check`; omission raises `TrustReadContractError`. It does not
infer authority from a username, role label, Trustee name, successor field, or
Trust status, and it does not weaken any existing route gate.

For an existing application caller, the current `operator_can_access_trust`
pattern can serve as the callback. Other consumers must supply an equivalent
authenticated, firm-aware decision.

## Read-only guarantee

The public interface exposes no create, update, delete, lifecycle-transition,
schema-migration, audit-write, or implicit record-creation operation. Reads do
not filter out Draft or inactive records unless the caller's authorization
policy does so; no universal active-status visibility rule is documented.

## Failure behavior

- Blank, denied, missing, and cross-firm Trust identifiers use the same safe
  not-visible result.
- Missing authorization or an unscoped legacy schema raises
  `TrustReadContractError` and fails closed.
- Unexpected database/runtime errors retain existing propagation behavior.
- The contract does not distinguish denied from missing records for callers.

## Compatibility

No existing route or caller is rewired in this phase. Existing DB functions,
return shapes, Trust detail behavior, creation workflows, packet generation,
and role gates remain unchanged. Later callers can adopt the facade without
requiring Trust persistence migration.

## Excluded behavior and known limitations

This contract does not implement Trust creation, editing, deletion, lifecycle
transitions, successor acceptance, fiduciary authority, account/asset reads,
continuity linkage, handoff assembly, or audit events. Authorization decisions
remain outside the service. Master-admin and assignment semantics remain those
of the current caller; a universal service-owned role vocabulary is NOT
DOCUMENTED.

## Approved future consumers

Trust detail, Governance, Execution, Documents, Continuity, and a future
successor-handoff assembler may consume this boundary when they supply their
existing authorization decision. This statement records reuse suitability; it
does not implement or authorize those integrations.
