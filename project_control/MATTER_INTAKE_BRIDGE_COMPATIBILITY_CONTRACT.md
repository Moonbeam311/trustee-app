# MIA-1A — Matter–Intake Bridge Schema and Compatibility Contract

**Status:** Implemented for additive schema validation  
**Operational linkage workflow:** Not yet activated  
**Live-database migration:** Not performed by MIA-1A

## Purpose

The Matter–Intake bridge creates a governed and auditable relationship between an Intake record and an Institutional Matter.

It does not merge the two subsystems.

It does not make Intake authoritative over the Matter lifecycle.

It does not infer a relationship merely because identifiers, names, users, or trust records appear similar.

## Architectural ownership

### Intake owns

- intake-question progress;
- supplied-information completeness;
- initial assessment;
- preliminary complexity;
- preliminary risk;
- preliminary priority;
- recommendations;
- and intake-review completion.

### Matter owns

- active operational status;
- final risk;
- final priority;
- governance state;
- institutional events;
- assignments;
- active work;
- closure;
- and archive.

### Matter–Intake bridge owns

- the existence of the governed linkage;
- whether the linkage is primary or supplemental;
- handoff status;
- recommendation disposition;
- effective and ended dates;
- correction basis;
- and immutable linkage history.

## Schema

### `matter_intake_links`

The authoritative bridge record.

Required identity:

- `bridge_id`
- `firm_id`
- `matter_id`
- `intake_id`

Lifecycle fields:

- `link_type`
- `link_status`
- `is_primary`
- `handoff_status`
- `handoff_by`
- `handoff_at`
- `recommendation_disposition`
- `intake_snapshot_id`
- `effective_at`
- `ended_at`
- `correction_basis`

Audit fields:

- `created_by`
- `created_at`
- `updated_by`
- `updated_at`

### `matter_intake_link_events`

Immutable evidence of bridge creation, acceptance, modification, rejection, suspension, ending, primary-link change, or correction.

## Isolation rules

A bridge may be created only when:

1. the Matter exists;
2. the Intake exists;
3. the Matter belongs to the stated firm;
4. the Intake belongs to the same stated firm.

The same human-readable Matter or Intake identifier in another physical runtime does not establish identity or authority.

## Cardinality rules

- One Intake may have no active primary Matter before handoff.
- One Intake may have only one active primary Matter at a time.
- One Matter may receive multiple Intake records.
- Supplemental, renewal, corrective, and historical links may coexist when their status and dates do not violate active-primary rules.

## No silent synchronization

Creating a bridge does not automatically:

- change Matter status;
- change Intake status;
- accept Intake risk;
- accept Intake priority;
- mark drafting ready;
- mark execution ready;
- verify a trust or document;
- close an Intake;
- close a Matter;
- or establish legal effect.

Every operational consequence requires a separately recorded decision or event.

## Compatibility requirements

The bridge is additive.

Existing Matter and Intake fields remain in place until:

- operational services are implemented;
- existing routes are adapted;
- regression testing succeeds;
- Firm 1 and Firm 2 runtime validation succeeds;
- and an explicit migration gate authorizes deprecation.

## MIA-1A completion boundary

MIA-1A provides:

- schema;
- constraints;
- same-firm enforcement;
- primary-link enforcement;
- immutable bridge events;
- idempotent installation;
- tests;
- and sandbox validation.

MIA-1A does not provide:

- user-facing routes;
- forms;
- automatic Matter creation;
- automatic Intake handoff;
- existing-record migration;
- status synchronization;
- or live-database installation.

## Next phase

**MIA-1B — Bridge Repository Services and ID Generation**

MIA-1B will implement tenant-scoped create, read, list, update, handoff, end, and event-recording services without adding the final user interface.
