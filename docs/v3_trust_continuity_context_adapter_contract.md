# V3 Trust–Continuity Context Adapter Contract

## Owner and sources

`services/services_trust_continuity_context.py` owns context composition only. Trust facts remain owned by `services/services_trust_contract.py` and Trust persistence. Continuity facts, readiness, activation, and events remain owned by the TPD-1C service and Continuity persistence.

## Cardinality

`TRUST_TO_CONTINUITY_CARDINALITY=ZERO_OR_MANY`. `continuity_profiles.trust_id` is nullable and non-unique. The schema provides a lookup index but no uniqueness or primary-profile rule. Trust-facing results therefore return every authorized same-firm linked profile ordered by `created_at` and `continuity_profile_id`; the adapter never silently selects a latest, first, or primary profile. One profile stores zero-or-one Trust identifier.

## Public interface

- `resolve_continuity_contexts_for_trust(trust_id, db_path=..., trust_authorization_check=..., continuity_authorization_check=...)`
- `resolve_trust_context_for_continuity(continuity_profile_id, db_path=..., trust_authorization_check=..., continuity_authorization_check=...)`

The Trust-facing result contains a small canonical Trust summary plus small profile/readiness/provenance summaries. The profile-facing result contains one profile summary and, when accessible, a small canonical Trust summary. Full source records and child records are not duplicated.

## Scope and authorization

Both calls require explicit caller-owned Trust and Continuity authorization decisions. Trust resolution uses the canonical Trust contract and active firm. Continuity retrieval uses the existing firm-scoped TPD-1C getter. Direct linking queries require both active `firm_id` and exact `trust_id`. Missing, denied, and cross-firm profile identifiers return no context. A stored Trust link that cannot be resolved safely returns `NOT_FOUND_OR_NOT_ACCESSIBLE` without exposing Trust details.

## Relationship states

- `LINKED`: at least one authorized same-firm profile is returned, or a profile resolves to an accessible canonical Trust.
- `UNLINKED`: an accessible Trust has no authorized linked profile, or an accessible profile has no recorded `trust_id`.
- `NOT_FOUND_OR_NOT_ACCESSIBLE`: an accessible profile records a Trust relationship that the canonical Trust boundary cannot safely resolve.
- A missing or inaccessible starting Trust/Profile returns `None`.

## Read-only guarantee

The adapter performs schema preflight and SELECT operations only. It does not invoke the Continuity migration, create a Trust or profile, change `trust_id`, link records, update readiness, transition activation, write Continuity events/audits, or create successor-handoff state. Reads are deterministic and emit no event.

## Navigation and limitations

The adapter supplies future navigation context but this phase changes no route or template. Trust-detail and Continuity-detail adoption belongs to the separately proposed UI phase. Route permissions remain unchanged; successor designation, Fiduciary authority, Continuity responsibility, and application permissions remain distinct. A primary Continuity profile, unified handoff aggregate, successor acceptance, activation bridging, and handoff workspace are not implemented and remain `NOT DOCUMENTED` or deferred as recorded by the planning artifact.
