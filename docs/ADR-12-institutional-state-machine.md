# ADR-12 — Institutional State Machine

## Purpose

Define legal lifecycle transitions for institutional objects.

ADR-11 defines lifecycle architecture.
ADR-11A defines status vocabulary.
ADR-12 defines which status changes are allowed.

## Core Rule

No institutional object should move between lifecycle states arbitrarily.

Every status change should be:

- Allowed
- Intentional
- Logged
- Attributed
- Reversible only by correction or supersession

## Universal State Machine

| From | Allowed To |
|---|---|
| proposed | draft, intake, review, archived |
| draft | intake, review, blocked, archived |
| intake | draft, review, blocked, pending_external, archived |
| review | approved, blocked, corrective_action, disputed, archived |
| approved | active, executed, pending_external, archived |
| pending_external | review, approved, active, blocked, archived |
| executed | funded, active, completed, corrective_action, archived |
| funded | active, completed, corrective_action, archived |
| active | pending_external, corrective_action, completed, closed, archived |
| blocked | draft, intake, review, corrective_action, pending_external, archived |
| corrective_action | draft, review, approved, active, completed, archived |
| disputed | review, corrective_action, active, retired, archived |
| completed | closed, archived, legacy_reference |
| closed | archived, legacy_reference |
| retired | archived, legacy_reference |
| superseded | archived, legacy_reference |
| archived | legacy_reference |
| legacy_reference | archived |
| deleted_prohibited | archived |

## Trust State Machine

| From | Allowed To |
|---|---|
| proposed | draft, intake, review, archived |
| draft | review, blocked, archived |
| review | approved, corrective_action, blocked, archived |
| approved | executed, pending_external, archived |
| executed | funded, active, corrective_action, archived |
| funded | active, corrective_action, archived |
| active | corrective_action, superseded, closed, archived |
| corrective_action | review, approved, active, superseded, archived |
| superseded | archived, legacy_reference |
| closed | archived, legacy_reference |
| archived | legacy_reference |

## Matter State Machine

| From | Allowed To |
|---|---|
| intake | review, active, blocked, archived |
| review | active, pending_external, corrective_action, closed, archived |
| active | pending_external, corrective_action, completed, closed, archived |
| pending_external | active, review, blocked, closed |
| corrective_action | review, active, completed, closed |
| completed | closed, archived |
| closed | archived, legacy_reference |

## Asset State Machine

| From | Allowed To |
|---|---|
| proposed | intake, review, archived |
| intake | review, blocked, archived |
| review | approved, blocked, corrective_action, archived |
| approved | executed, pending_external, archived |
| executed | funded, active, corrective_action, archived |
| funded | active, archived |
| active | corrective_action, retired, archived |
| retired | archived, legacy_reference |

## Relationship State Machine

| From | Allowed To |
|---|---|
| proposed | review, active, archived |
| review | active, disputed, corrective_action, archived |
| active | disputed, corrective_action, retired, archived |
| disputed | review, corrective_action, retired, archived |
| corrective_action | review, active, retired, archived |
| retired | archived, legacy_reference |

## Evidence / Archive State Machine

| From | Allowed To |
|---|---|
| intake | active, review, blocked |
| active | review, approved, archived |
| review | approved, disputed, corrective_action, archived |
| approved | archived, completed |
| disputed | review, corrective_action, archived |
| corrective_action | review, approved, archived |
| completed | archived, legacy_reference |
| archived | legacy_reference |

## Transition Rules

- Status changes must be recorded as institutional events.
- No transition should silently overwrite prior state.
- Invalid transitions should be rejected or routed through corrective_action.
- Archived records may not return to active status without a restoration event.
- Superseded records may not become active again unless explicitly restored.
- Deleted is not a valid institutional lifecycle transition.
- Deletion-prohibited records must move to archived, not deleted.
- State changes should include actor, timestamp, reason, source workspace, and object id.

## Required Transition Metadata

Every lifecycle transition should eventually capture:

- Object type
- Object id
- Prior status
- New status
- Actor
- Authority / basis
- Timestamp
- Reason
- Related event id
- Related matter id, if applicable
- Related trust id, if applicable
- Evidence reference, if applicable

## ADR-12 Findings

ADR-12 converts lifecycle language into controlled institutional behavior.

The next layer is ADR-13, which defines the event registry that records and explains these transitions.
