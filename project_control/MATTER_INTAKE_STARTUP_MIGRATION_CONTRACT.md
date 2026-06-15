# MIA-1C — Live Migration Registration and Dual-Sandbox Validation Contract

**Status:** Startup registration implemented  
**Operational bridge creation:** Not activated automatically  
**Production cutover:** Not authorized by this phase

## Startup registration

The application startup sequence now runs:

1. existing `init_db()`;
2. additive startup migrations;
3. normal application initialization.

The Matter–Intake startup migration may create only:

- `matter_intake_links`;
- `matter_intake_link_events`;
- required indexes;
- required triggers.

It must not automatically create a bridge row or bridge-event row.

## Idempotency rule

Repeated application startup must not:

- create duplicate bridge tables;
- create duplicate indexes;
- create duplicate triggers;
- create Matter–Intake operational records;
- expand role-permission assignments;
- change Matter status;
- change Intake status;
- or infer a link from existing data.

## Dual-runtime rule

Firm 1 and Firm 2 use physically separate databases.

The same local identifier, including `MIB-000001`, may exist independently in both databases. Physical database identity and deployment-bound firm identity provide the isolation boundary.

No service call may retrieve a bridge unless both:

- the supplied firm matches the bridge firm;
- and the bridge exists in the active database.

## Validation gate

MIA-1C must prove:

- both isolated sandbox databases pass integrity checks;
- startup migration is idempotent in both;
- each database can independently create `MIB-000001`;
- each database independently creates `MIBE-000001`;
- Firm 1 data cannot be retrieved through a Firm 2 scope;
- Firm 2 data cannot be retrieved through a Firm 1 scope;
- repeated application startup does not grow `role_permissions`;
- the certified extraction sandboxes remain unchanged;
- and the live database remains unchanged during validation.

## Live startup effect

After this phase is committed, the next normal application startup may create the empty Matter–Intake schema in the active runtime database.

This does not establish a relationship between any existing Intake and Matter.

## Next phase

**MIA-1D — Matter and Intake Linkage Routes, Review Gate, and Matter Event Integration**
