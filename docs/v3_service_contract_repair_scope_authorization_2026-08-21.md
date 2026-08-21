# V3 Service Contract Repair Scope Authorization

## Phase

`V3-AUD-SERVICE-CONTRACTS-AUTH-1`

## Baseline

- Branch: `system-1-annual-evaluation`
- Starting local HEAD: `9c8fbfad39d72eb34416c738874a86992abd1f05`
- Starting remote HEAD: `9c8fbfad39d72eb34416c738874a86992abd1f05`
- Source DB SHA-256:
  `3fcbbe1092072c47fe7e43fb1ab075f6ff626079511c948a1275936776b71d3c`

## Governing Audit Artifact

`docs/v3_service_contract_integrity_audit_2026-08-21.md`

Preserved SHA-256:
`196fe098c9ab5e02fe65ffb3c594ac95451a524c6c74fd4b96f9ac4e56535cd2`

## Audit Verdict

`C — REPAIR REQUIRED / BOUNDED INTEGRATION DEFECTS IDENTIFIED`

## Trust-Binding Disposition

Finding: `create_continuity_profile` accepts caller-supplied `trust_id` without
proving canonical same-firm Trust existence or agreement with a supplied
bridge. This permits nonexistent, cross-firm, or provenance-conflicting
institutional links even though later reads fail closed.

- Classification: `REQUIRED_V3_REPAIR`
- Repair required: `YES`

This is a current write-contract defect, not an architectural preference or
future capability.

## Event-History Read Disposition

Finding: Continuity events are append-only and immutable, but the public
profile bundle does not include events and no public event-list service exists.
The preserved Continuity output contract expressly lists its bundle without an
events collection, and no current route, template, aggregate, or certification
caller requires a public event-history API.

- Classification: `UNSUPPORTED_FUTURE_CAPABILITY`
- Included in R1: `NO`
- Separate follow-up required: `NO`

Event existence and institutional immutability do not independently create a
public read requirement. A later explicit contract may authorize such a
capability; this control phase does not.

## Authorized Repair Phase

`V3-AUD-SERVICE-CONTRACTS-R1 — Continuity Profile Trust-Binding Contract Repair`

Status: `AUTHORIZED NEXT / NOT STARTED`

## Authorized R1 Scope

1. When `trust_id` is supplied to Continuity profile creation, require a
   canonical Trust that exists in the supplied firm.
2. When both `bridge_id` and `trust_id` are supplied, require the Trust binding
   to agree with the bridge's governed Trust provenance; fail closed on a
   mismatch.
3. Preserve creation of pre-Trust Continuity profiles when no Trust reference
   is supplied.
4. Add focused disposable service regressions for valid, nonexistent,
   cross-firm, and bridge/Trust-mismatched contexts.
5. Add focused route regressions proving invalid caller context fails safely
   without profile or event creation.
6. Preserve existing same-firm reads, child contracts, activation lifecycle,
   secret policy, event append/immutability, and canonical context behavior.

## Explicitly Excluded Scope

- public/service event-history reads;
- changes to `continuity_events` schema, append behavior, or triggers;
- Continuity schema redesign or migration of existing governed data;
- automatic Trust, bridge, profile, successor, Acceptance, authority,
  responsibility, or access creation;
- unrelated routes, templates, UI, or application authorization;
- child update/delete lifecycles and universal idempotency keys;
- P03, P04, and unrelated future capabilities;
- governed source-database mutation.

## Control State

`V3-AUD-SERVICE-CONTRACTS-R1 — AUTHORIZED NEXT / NOT STARTED`

## P03

`PRESERVED / SUSPENDED / UNSTAGED`

## Browser

`NOT APPLICABLE  CONTROL-ONLY AUTHORIZATION PHASE`

R1 must define its own isolated executable/regression/browser requirements.

## Stop Boundary

`DO NOT BEGIN R1 IN THIS RUN.`
