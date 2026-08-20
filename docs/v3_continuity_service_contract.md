# V3 Continuity Service Contract

Status: explicit existing contract preserved by `V3-SVC-GOVCONT-1`.

## Domain owner

The canonical governed Continuity profile contract is implemented in `services/services_intake_trust_bridge.py` and exposed to HTTP callers through `routes_tpd1c.py`. Schema creation is provided by `database/migrations_intake_trust_bridge.py`.

`services/services_continuity_assets.py` is a separate asset-custody/archive subsystem and is not merged into this contract.

## Public interface

The preserved Continuity callable surface is:

- `validate_no_secret_material(values)`
- `create_continuity_profile(db_path, firm_id, subject_name, subject_type, capacities, purpose, actor, ...)`
- `get_continuity_profile(db_path, profile_id, firm_id)`
- `link_continuity_profile(db_path, profile_id, bridge_id, firm_id, actor)`
- `add_continuity_record(db_path, table, profile_id, firm_id, actor, values)`
- `transition_activation_plan(db_path, plan_id, profile_id, firm_id, actor, new_status, basis)`
- `continuity_readiness(bundle)`

The allowed child record types are responsibilities, digital accounts, receivables, payables, and activation plans.

## Input expectations

- Every persistence operation receives an explicit database path and firm ID.
- Profile creation requires a nonblank subject name and explicit capacity.
- Optional bridge linkage requires a bridge in the same firm.
- Child creation requires a supported child table, an existing same-firm profile, an actor, and fields supported by that table.
- Responsibility records represent responsibility, responsible/successor parties, authority sources, supporting references, and review metadata.
- Digital-account records contain service/account metadata, login identifiers where appropriate, vault references, recovery procedure metadata, MFA/custodian descriptions, authority references, and review dates—but never secret values.
- Receivable/payable records contain operational metadata and references, not payment-card secrets or authentication material.
- Activation transitions require a nonblank documented basis.

## Output expectations

- Profile creation and child creation return their generated IDs.
- Profile retrieval returns `None` when the profile is not visible in the supplied firm, otherwise a bundle containing `profile`, `responsibilities`, `digital_accounts`, `receivables`, `payables`, `activation_plans`, and computed `readiness`.
- Link and transition operations preserve their existing no-value success return.
- Readiness returns a dictionary with classification, gap count, gap categories, review dates, and disclaimer.

## Persistence ownership

The service/migration owns:

- `continuity_profiles`
- `continuity_responsibilities`
- `continuity_digital_accounts`
- `continuity_receivables`
- `continuity_payables`
- `continuity_activation_plans`
- `continuity_events`

New V3 consumers must use the callable contract and must not write directly to these tables.

## Firm-scope rules

- Profile retrieval filters by profile ID and firm ID.
- Profile/bridge linkage requires both records in the same supplied firm.
- Child creation requires the parent profile in the supplied firm and stores the same firm ID.
- Activation transition filters by plan, profile, and firm.
- Cross-firm records are unavailable and must not be disclosed or mutated.

## Authorization assumptions

The service enforces explicit firm scope and validation. The TPD-1C blueprint supplies HTTP authentication, `create_trust` or `edit_trust` permissions, and CSRF protection for writes. Non-route callers must provide equivalent authenticated actor and permission checks before calling mutations.

The service does not itself prove legal authority, incapacity, appointment, or financial certification.

## Secret and vault-reference policy

Only metadata and secure-vault references may be stored. `validate_no_secret_material` rejects prohibited secret field names and values matching the existing secret patterns.

The contract prohibits storage of:

- passwords
- PINs
- recovery or backup codes
- security answers
- access/authentication tokens
- private keys
- CVV/CVC values or complete payment-card secrets

Callers must store such material in an external approved vault and persist only a non-secret `vault_reference` and controlled recovery-procedure metadata.

This baseline does not weaken or bypass `validate_no_secret_material`.

## Validation and lifecycle rules

Supported activation transitions are preserved exactly:

- `plan_drafted` → `plan_reviewed`, `superseded`, or `closed`
- `plan_reviewed` → `trigger_reported`, `superseded`, or `closed`
- `trigger_reported` → `evidence_pending`, `activation_authorized`, or `closed`
- `evidence_pending` → `activation_authorized` or `closed`
- `activation_authorized` → `active` or `suspended`
- `active` → `suspended`, `restored`, `superseded`, or `closed`
- `suspended` → `active`, `restored`, or `closed`
- `restored` → `closed` or `superseded`
- `superseded` and `closed` are terminal

Unsupported child types, secret material, missing same-firm parents/bridges, missing transition basis, and invalid transitions raise `BridgeError` using existing messages.

## Provenance and audit behavior

- Profile creation emits `PROFILE_CREATED`.
- Same-firm bridge linkage emits `PROFILE_LINKED_TO_BRIDGE` with previous and new linkage state.
- Child creation emits `RECORD_ADDED` with the child identifier.
- Activation transition emits `ACTIVATION_STATUS_CHANGED` with previous/new status and transition basis.
- Events retain actor, firm, basis, previous/new JSON, and timestamp.
- Database triggers reject update and deletion of `continuity_events`, preserving immutable history.

## Readiness behavior

`continuity_readiness` reports `ready_for_review` only when documented gaps are zero; otherwise it reports `needs_attention`. It evaluates current/successor responsibility, authority source, supporting documents, vault reference or recovery instructions, account verification, and activation review.

Readiness is expressly not legal validity, appointment, financial certification, or proof of incapacity.

## Idempotency expectations

- Retrieval and readiness evaluation are deterministic for unchanged stored state.
- Bridge preparation/creation has separately tested idempotency in the wider TPD-1C bridge contract.
- Profile creation, child creation, linkage replay, and activation transition do not expose universal caller-provided idempotency keys. Additional replay guarantees are NOT DOCUMENTED.

## Failure behavior

- Expected validation, secret, scope, and lifecycle failures raise `BridgeError`.
- Cross-firm retrieval returns `None`.
- Linkage is transactional and rolls back on failure.
- Invalid activation transitions fail before the update/event commit.
- Unexpected persistence/runtime failures propagate according to existing behavior.

## Compatibility guarantees

- Existing public names, signatures, return shapes, table ownership, firm filters, transition graph, event types, immutable-event triggers, secret policy, TPD route permissions, and callers remain unchanged by this baseline.
- No dependency on Governance, suspended P03, or future trust-handoff implementation is introduced.
- Asset custody remains a separate responsibility.

## Prohibited behaviors

- Secret storage or secret-validation bypass.
- Direct child/event writes by new V3 consumers.
- Cross-firm lookup, linkage, or mutation.
- Event update/deletion.
- Unsupported activation transitions or transition without documented basis.
- Treating readiness as legal/financial/incapacity proof.
- Merging asset-custody/archive responsibilities into this profile contract.
- Adding Governance, P03, or trust-handoff dependencies in this baseline.

## Known limitations

- Authorization beyond firm scope is enforced by routes/callers, not the service functions themselves.
- Universal mutation idempotency keys are NOT DOCUMENTED.
- Legal authority and successor acceptance are not established by Continuity records.
- Asset custody/archive continuity is a separate subsystem.

## Safe consumers

Future V3 consumers may safely reuse same-firm profile retrieval, responsibility metadata, non-secret digital-account/vault references, receivable/payable metadata, activation plans, readiness, and native immutable event provenance when equivalent authorization is enforced. A future successor-handoff workflow must treat these as continuity metadata and evidence references, not as proof of fiduciary authority or successor acceptance.
