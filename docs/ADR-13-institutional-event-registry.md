# ADR-13 — Institutional Event Registry

## Purpose

Define the canonical event registry for the Trustee App institutional operating system.

ADR-11 defines lifecycle architecture.
ADR-11A defines status vocabulary.
ADR-12 defines allowed state transitions.
ADR-13 defines the events that record institutional action.

## Core Rule

Every significant institutional action should create an event.

Events explain:

- What happened
- Who did it
- When it happened
- Why it happened
- What object was affected
- What evidence supports it
- What status changed, if any

## Event Categories

| Category | Purpose |
|---|---|
| identity | Person, organization, role, or authority event |
| trust | Trust formation, execution, funding, administration |
| matter | Matter intake, review, action, closure |
| asset | Asset identification, verification, transfer, custody |
| instrument | Drafting, review, execution, certification |
| relationship | Relationship creation, verification, correction |
| governance | Decision, recommendation, approval, risk finding |
| compliance | Readiness, defect, checklist, corrective action |
| archive | Evidence, custody, export, preservation |
| report | Report generation, review, certification |
| system | User, permission, security, health, configuration |
| research | Research question, source, finding, adoption |
| execution | Signature, witness, notary, packet, finalization |
| funding | Source verification, transfer, receipt, ledgering |

## Canonical Event Fields

| Field | Required | Meaning |
|---|---|---|
| event_id | Yes | Unique institutional event id |
| event_type | Yes | Canonical event type |
| event_category | Yes | Category from registry |
| object_type | Yes | Affected object type |
| object_id | Yes | Affected object id |
| actor | Yes | User, system, or external actor |
| actor_role | No | Admin, Trustee, Viewer, System, etc. |
| prior_status | No | Previous lifecycle status |
| new_status | No | New lifecycle status |
| authority_basis | No | Authority, rule, document, approval, or reason |
| description | Yes | Human-readable event description |
| evidence_ref | No | Linked evidence, document, archive, or file |
| related_trust_id | No | Related trust id |
| related_matter_id | No | Related matter id |
| related_asset_id | No | Related asset id |
| source_workspace | No | IOS workspace where event occurred |
| created_at | Yes | Timestamp |
| hash | Future | Optional integrity hash |
| prior_event_id | Future | Optional event chain pointer |

## Core Event Types

### Trust Events

| Event Type | Meaning |
|---|---|
| trust_proposed | Trust concept identified |
| trust_drafted | Trust drafting started or updated |
| trust_reviewed | Trust reviewed |
| trust_approved | Trust approved for execution |
| trust_executed | Trust execution completed |
| trust_funded | Trust funding confirmed |
| trust_active | Trust entered active administration |
| trust_amended | Trust amended |
| trust_restated | Trust restated |
| trust_superseded | Trust replaced by controlling version |
| trust_closed | Trust closed or terminated |
| trust_archived | Trust archived |

### Matter Events

| Event Type | Meaning |
|---|---|
| matter_opened | Matter opened |
| matter_intake_completed | Matter intake completed |
| matter_reviewed | Matter reviewed |
| matter_status_changed | Matter lifecycle status changed |
| matter_note_added | Governance or case note added |
| matter_external_pending | Matter waiting on external action |
| matter_completed | Matter work completed |
| matter_closed | Matter closed |
| matter_archived | Matter archived |

### Asset Events

| Event Type | Meaning |
|---|---|
| asset_identified | Asset identified |
| asset_verified | Asset verified |
| asset_valued | Asset valued |
| asset_assigned | Asset assigned |
| asset_transfer_prepared | Transfer prepared |
| asset_transferred | Asset transferred |
| asset_funded | Asset funding confirmed |
| asset_monitored | Asset monitoring event |
| asset_retired | Asset retired |
| asset_archived | Asset archived |

### Relationship Events

| Event Type | Meaning |
|---|---|
| relationship_proposed | Relationship proposed |
| relationship_verified | Relationship verified |
| relationship_activated | Relationship made active |
| relationship_disputed | Relationship disputed |
| relationship_corrected | Relationship corrected |
| relationship_retired | Relationship retired |
| relationship_archived | Relationship archived |

### Governance Events

| Event Type | Meaning |
|---|---|
| question_raised | Governance question opened |
| recommendation_drafted | Recommendation drafted |
| decision_made | Decision made |
| approval_recorded | Approval recorded |
| risk_identified | Risk identified |
| risk_changed | Risk level changed |
| finding_recorded | Finding recorded |
| corrective_action_opened | Corrective action opened |
| corrective_action_closed | Corrective action closed |

### Compliance Events

| Event Type | Meaning |
|---|---|
| checklist_opened | Compliance checklist opened |
| readiness_reviewed | Readiness reviewed |
| defect_identified | Defect identified |
| defect_corrected | Defect corrected |
| requirement_passed | Requirement passed |
| requirement_failed | Requirement failed |
| compliance_closed | Compliance workflow closed |

### Archive / Evidence Events

| Event Type | Meaning |
|---|---|
| evidence_received | Evidence received |
| evidence_logged | Evidence logged |
| evidence_verified | Evidence verified |
| evidence_linked | Evidence linked to object |
| evidence_disputed | Evidence disputed |
| custody_event_recorded | Custody event recorded |
| archive_packet_created | Archive packet created |
| export_generated | Export generated |
| record_archived | Record archived |
| retention_reviewed | Retention reviewed |

### System Events

| Event Type | Meaning |
|---|---|
| user_created | User created |
| user_updated | User updated |
| role_changed | Role changed |
| permission_changed | Permission changed |
| login_success | Login succeeded |
| login_failed | Login failed |
| security_event | Security event recorded |
| system_health_checked | System health checked |
| configuration_changed | Configuration changed |

## Event Rules

- Events should be append-only.
- Events explain state transitions but do not replace object records.
- Status changes must create events.
- Evidence changes must create events.
- Relationship verification must create events.
- Archive exports must create events.
- Administrative overrides must create events.
- Events should never be silently deleted.

## Event Integrity Rules

- Future versions should support event hashing.
- Future versions should support event chaining.
- Future versions should support exportable event ledgers.
- Events should be visible from object detail screens.
- Events should feed the Executive Resume Engine.

## ADR-13 Findings

ADR-13 establishes events as the institutional memory layer.

The next layer is ADR-14, which defines how the Executive Resume Engine consumes events, statuses, alerts, readiness, and pending work.
