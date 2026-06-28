# ADR-14 — Executive Resume Engine Data Model

## Purpose

Define the data model for the IOS HOME Executive Resume Engine.

ADR-10 defined the concept.
ADR-14 defines the data sources, panels, and computed outputs.

## Core Rule

HOME should not duplicate every dashboard.

HOME should answer:

- Where did I leave off?
- What needs attention?
- What is blocked?
- What should I do next?
- Is the institution healthy?

## Primary Data Sources

| Source | Purpose |
|---|---|
| Events | Recent institutional activity and status changes |
| Lifecycle Status | Current state of objects |
| Matters | Active work, blocked work, pending external action |
| Trusts | Trust health, execution, funding, administration |
| Assets | Funding, transfer, verification, custody |
| Relationships | Verification, disputes, corrections |
| Compliance Reviews | Defects, readiness, corrective actions |
| Archive Records | Evidence, custody, exports, preservation |
| Tasks | Follow-ups, deadlines, pending actions |
| System Health | Runtime, database, permissions, security |
| Reports | Generated outputs and institutional summaries |

## Executive Resume Panels

### Continue Work

Shows the most recent actionable work.

Inputs:

- recent events
- active matters
- draft records
- pending tasks
- recently opened object detail screens

Output fields:

- title
- object_type
- object_id
- workspace
- last_event
- last_updated
- resume_url
- recommended_action

### Pending Reviews

Shows records waiting for review or approval.

Inputs:

- lifecycle status = review
- lifecycle status = approved but not executed
- compliance reviews
- governance recommendations
- draft instruments

Output fields:

- review_type
- object_type
- object_id
- priority
- owner
- reason
- review_url

### Blocked Work

Shows records that cannot proceed.

Inputs:

- lifecycle status = blocked
- lifecycle status = corrective_action
- lifecycle status = pending_external
- missing execution readiness items
- relationship disputes
- evidence defects

Output fields:

- blocker_type
- object_type
- object_id
- blocker_reason
- required_action
- source_workspace
- correction_url

### Execution Readiness

Shows execution-related readiness.

Inputs:

- trust packet readiness
- signature status
- witness status
- notary status
- PDF/DOCX readiness
- certificate readiness
- archive readiness

Output fields:

- object_id
- object_type
- readiness_score
- missing_items
- ready_for_execution
- execution_url

### Trust Health

Shows operational trust status.

Inputs:

- trust lifecycle status
- funding status
- asset count
- relationship verification
- instrument readiness
- minutes / governance activity
- archive integrity

Output fields:

- trust_id
- trust_name
- lifecycle_status
- funding_status
- asset_status
- governance_status
- archive_status
- recommended_action

### Matter Health

Shows matter status and urgency.

Inputs:

- matter lifecycle status
- matter events
- active tasks
- related relationships
- governance notes
- risk level

Output fields:

- matter_id
- matter_title
- lifecycle_status
- risk_level
- open_tasks
- last_event
- next_action

### Archive Integrity

Shows preservation and evidence issues.

Inputs:

- archive events
- evidence records
- custody records
- export records
- verification status

Output fields:

- object_type
- object_id
- archive_status
- evidence_status
- custody_status
- export_status
- integrity_alert

### Compliance Alerts

Shows compliance problems.

Inputs:

- failed requirements
- missing execution items
- unresolved review gates
- blocked lifecycle states
- disputed relationships
- missing evidence

Output fields:

- alert_type
- severity
- object_type
- object_id
- message
- recommended_action
- alert_url

### Recent Activity

Shows institutional event stream.

Inputs:

- ADR-13 institutional events

Output fields:

- event_id
- event_type
- object_type
- object_id
- actor
- description
- created_at
- event_url

### Recommended Next Action

Computes the most important next action.

Inputs:

- blocked work
- pending reviews
- execution readiness
- matter risk
- trust health
- compliance alerts
- recent activity

Priority order:

1. Critical compliance alert
2. Blocked execution
3. Pending external dependency
4. Trust not funded
5. Matter high risk
6. Pending review
7. Draft incomplete
8. Archive integrity issue
9. System health issue
10. Continue most recent work

Output fields:

- recommendation_title
- reason
- workspace
- object_type
- object_id
- action_url
- urgency

### System Health

Shows platform condition.

Inputs:

- database status
- route integrity
- workspace integrity
- permissions
- security
- export policy
- recent errors

Output fields:

- health_status
- alerts
- last_checked
- system_url

## Recommended Severity Vocabulary

| Severity | Meaning |
|---|---|
| info | Informational only |
| low | Needs attention eventually |
| medium | Needs normal review |
| high | Blocks important work |
| critical | Must be addressed before proceeding |

## Recommended Urgency Vocabulary

| Urgency | Meaning |
|---|---|
| later | Safe to defer |
| soon | Should be handled soon |
| next | Recommended next action |
| immediate | Should be handled before continuing |

## Engine Rules

- HOME summarizes; it does not own operational records.
- HOME links back to the workspace that owns the object.
- Recommendations should explain why they appear.
- Alerts should be traceable to events, lifecycle states, or missing requirements.
- The engine should favor real data over placeholder counts.
- Placeholder metrics must be clearly marked as pilot or pending.
- No recommendation should silently override governance or compliance state.

## Future Implementation Notes

The Executive Resume Engine can begin as a service function that returns a dictionary:

- continue_work
- pending_reviews
- blocked_work
- execution_readiness
- trust_health
- matter_health
- archive_integrity
- compliance_alerts
- recent_activity
- recommended_next_action
- system_health

This dictionary can feed the HOME workspace without restructuring existing dashboards.

## ADR-14 Findings

ADR-14 converts the HOME workspace from a static landing page into a data-driven institutional resume engine.

The next layer is ADR-15, the Universal Institutional Dashboard Engine.
