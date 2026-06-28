# ADR-15 — Universal Institutional Dashboard Engine

## Purpose

Define a universal dashboard engine for canonical institutional objects.

The app should not build unrelated dashboards for every object type.

Instead, every major institutional object should render through a shared dashboard pattern.

## Core Principle

Dashboard = Object + Lifecycle + Events + Relationships + Tasks + Evidence + Actions

## Supported Object Types

- Trust
- Matter
- Person
- Organization
- Role
- Asset
- Instrument
- Relationship
- Decision
- Discussion
- Evidence
- Archive Record
- Report
- Task
- Event
- Workspace
- Research Project
- Compliance Review
- Funding Record
- Execution Record

## Universal Dashboard Panels

| Panel | Purpose |
|---|---|
| Identity | Object name, id, type, owner, jurisdiction, status |
| Lifecycle | Current status, allowed transitions, blockers |
| Summary | Human-readable institutional summary |
| Relationships | Linked people, trusts, matters, assets, records |
| Events | Institutional event stream |
| Tasks | Open and completed work |
| Evidence | Documents, archive records, custody, verification |
| Compliance | Defects, readiness, review gates, approvals |
| Actions | Allowed next actions |
| Reports | Generated outputs and exports |
| Archive | Preservation, retention, continuity |
| History | Change history and prior versions |

## Object-Specific Extensions

### Trust Dashboard

Additional panels:

- Funding
- Execution Readiness
- Trust Minutes
- Certificates
- Instruments
- Beneficiaries
- Trustees
- Assets
- Amendments / Restatements

### Matter Dashboard

Additional panels:

- Matter Events
- Governance Notes
- Risk Level
- Related Trusts
- Related Assets
- Resolution Status

### Asset Dashboard

Additional panels:

- Valuation
- Title / Ownership
- Transfer Status
- Custody
- Funding Status
- Evidence

### Person Dashboard

Additional panels:

- Roles
- Authority
- Contact / Identity
- Accepted Appointments
- Related Trusts / Matters

### Instrument Dashboard

Additional panels:

- Drafting Status
- Clause / Article Readiness
- Execution Status
- Version / Supersession
- Export / Certification

### Archive / Evidence Dashboard

Additional panels:

- Chain of Custody
- Verification
- Export History
- Retention
- Integrity Alerts

### Research Dashboard

Additional panels:

- Research Question
- Sources
- Findings
- Adoption Status
- Related Trust Type
- Implementation Notes

## Dashboard Engine Data Contract

Each dashboard should eventually be driven by:

- object_type
- object_id
- title
- lifecycle_status
- status_label
- workspace_owner
- summary
- relationships
- events
- tasks
- evidence
- compliance
- actions
- reports
- archive
- history
- extensions

## Action Rules

Actions shown on a dashboard must be determined by:

- object type
- lifecycle status
- user role
- permissions
- compliance state
- unresolved blockers
- source workspace
- relationship verification
- archive status

## Dashboard Routing Rule

Canonical route pattern:

`/objects/<object_type>/<object_id>`

Legacy routes may remain, but should eventually link into the universal object dashboard.

Examples:

- `/objects/trust/TR-022`
- `/objects/matter/MAT-000001`
- `/objects/asset/AST-000001`
- `/objects/person/PER-000001`
- `/objects/research/RES-000001`

## Legacy Preservation Rule

Existing dashboards should not be deleted immediately.

They should be progressively surfaced through the universal dashboard engine while preserving legacy access.

## Migration Strategy

1. Define dashboard data contract.
2. Build service function that assembles object dashboard context.
3. Build universal dashboard template.
4. Route one low-risk object type first.
5. Preserve legacy route.
6. Add cross-link from legacy detail to universal dashboard.
7. Expand by object type.
8. Eventually reduce duplicate dashboard logic.

## First Recommended Object Type

Matter is the best first object type because:

- Matter already acts as an institutional container.
- Matter connects trusts, events, relationships, governance, risk, and intake.
- Matter migration will improve the entire app without disturbing trust execution logic first.

## ADR-15 Rules

- Do not create another isolated dashboard unless it maps to a canonical object.
- Do not delete legacy dashboards during migration.
- Universal dashboards must show lifecycle and events.
- Object dashboards must link back to owning workspace.
- Object dashboards must expose evidence and archive status when available.
- Actions must respect permissions and lifecycle state.

## ADR-15 Findings

ADR-15 creates the path from many separate dashboards to one institutional dashboard engine.

The next implementation phase should be ADR-15A: Universal Dashboard Engine Precheck.
