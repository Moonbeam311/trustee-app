# V3 Service Contracts R1 Path Registration

## Phase

`V3-AUD-SERVICE-CONTRACTS-R1-PRES-1`

## Purpose

Register the exact implementation, test, and evidence paths required by the
already authorized R1 Continuity Profile Trust-Binding Contract Repair. This is
a control-only preservation phase and performs no R1 implementation.

## Baseline

- Branch: `system-1-annual-evaluation`
- Starting local HEAD: `f5005cc8d228078af10c265115ebfa721967a2f7`
- Starting remote HEAD: `f5005cc8d228078af10c265115ebfa721967a2f7`
- Source DB SHA-256:
  `3fcbbe1092072c47fe7e43fb1ab075f6ff626079511c948a1275936776b71d3c`

## Governing Authorization

- AUTH-1 artifact:
  `docs/v3_service_contract_repair_scope_authorization_2026-08-21.md`
- R1 status: `AUTHORIZED NEXT / NOT STARTED`
- Event-history disposition: `UNSUPPORTED_FUTURE_CAPABILITY`
- Event-history included in R1: `NO`

## Authorized R1 Paths

- `services/services_intake_trust_bridge.py` — existing canonical Continuity
  profile write service requiring the bounded Trust/firm/bridge validation.
- `tests/test_v3_aud_service_contracts_r1.py` — one focused disposable service
  and route regression contract for valid, missing, cross-firm, mismatched, and
  unbound contexts without modifying broad legacy test files.
- `docs/v3_service_contracts_r1_trust_binding_repair_2026-08-21.md` — required
  R1 implementation, regression, browser, and preservation evidence.
- `docs/v3_service_contracts_r1_path_registration_2026-08-21.md` — this
  control-preservation record.

No route source path is registered because the existing route already passes
`trust_id` and `bridge_id` into the canonical service; the bounded service
validation repairs both direct and HTTP callers. No schema/migration path is
registered because `continuity_profiles.trust_id` and its context index already
exist.

## Explicitly Excluded Paths

- suspended P03 files;
- `app.py`, `routes_tpd1c.py`, and all templates;
- migrations, schema, and governed database files;
- unrelated service modules and broad test suites;
- event-history implementation, routes, templates, and new event-history tests;
- child lifecycle, idempotency, automatic authority/access, and other future
  capabilities.

## Manifest Mechanism

- Field: `allowed_dirty_paths`
- Semantics: exact repository-relative file paths, matched by the existing V3
  control guard after Git path normalization
- Integrity/hash update: none; the ledger and guard were not changed, and no
  new manifest schema or integrity field was introduced

## Guard

- Before registration: `PASS` for `V3-AUD-SERVICE-CONTRACTS-R1`
- After registration and remote anchoring: required `PASS` for the same phase

## Source DB Preservation

`data/trustee_app.db` remained byte-identical at SHA-256
`3fcbbe1092072c47fe7e43fb1ab075f6ff626079511c948a1275936776b71d3c`.

## P03 Preservation

`V3-MOD-WLH-P03C.4C` remained `PRESERVED / SUSPENDED / UNSTAGED`.

## Browser

`NOT APPLICABLE  CONTROL-ONLY PATH REGISTRATION`

## Final Control State

`V3-AUD-SERVICE-CONTRACTS-R1 — AUTHORIZED NEXT / NOT STARTED`

## Stop Boundary

`DO NOT BEGIN R1 IMPLEMENTATION IN THIS RUN.`
