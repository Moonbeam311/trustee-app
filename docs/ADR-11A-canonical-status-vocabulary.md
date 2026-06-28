# ADR-11A — Canonical Status Vocabulary

## Purpose

Define the canonical status vocabulary used across institutional objects.

ADR-11 defines lifecycles.
ADR-11A defines the words used to describe lifecycle state.

## Core Rule

Different modules may have specialized lifecycle steps, but they must map back to canonical status values.

No module should invent unrelated status names without mapping them here.

## Universal Status Values

| Internal Value | Display Label | Meaning |
|---|---|---|
| proposed | Proposed | Work has been identified but not formally opened. |
| draft | Draft | Work exists but is incomplete. |
| intake | Intake | Information is being collected. |
| review | Review | Work is under institutional review. |
| approved | Approved | Work has been approved but not necessarily executed. |
| active | Active | Work is currently operative. |
| blocked | Blocked | Work cannot proceed due to missing information, defect, or dependency. |
| corrective_action | Corrective Action | Work requires correction before proceeding. |
| pending_external | Pending External Action | Waiting for another person, institution, filing, signature, or record. |
| executed | Executed | Required execution step has occurred. |
| funded | Funded | Funding or asset transfer has been confirmed. |
| completed | Completed | Operational work is complete. |
| closed | Closed | Matter or workflow is closed but preserved. |
| archived | Archived | Record is preserved and no longer active. |
| legacy_reference | Legacy Reference | Preserved for institutional memory, history, or reference. |
| disputed | Disputed | Status, record, authority, or relationship is contested. |
| superseded | Superseded | Replaced by a later version or controlling record. |
| retired | Retired | No longer active, but not deleted. |
| deleted_prohibited | Deletion Prohibited | Deletion is not permitted because institutional preservation applies. |

## Display Rules

- Internal values use lowercase snake_case.
- Display labels may be user-friendly.
- Archived is not deleted.
- Retired is not deleted.
- Superseded is not deleted.
- Legacy Reference is preserved knowledge, not active work.
- Blocked and Corrective Action must be visible to users.

## Object-Specific Mappings

### Trust

| Lifecycle Term | Canonical Status |
|---|---|
| Proposed | proposed |
| Drafting | draft |
| Review | review |
| Approved | approved |
| Executed | executed |
| Funded | funded |
| Active Administration | active |
| Amendment / Restatement | corrective_action |
| Closed / Terminated | closed |
| Archived | archived |
| Legacy Reference | legacy_reference |

### Matter

| Lifecycle Term | Canonical Status |
|---|---|
| Opened | active |
| Intake | intake |
| Review | review |
| Active Work | active |
| Pending External Action | pending_external |
| Resolution Drafting | draft |
| Closed | closed |
| Archived | archived |

### Asset

| Lifecycle Term | Canonical Status |
|---|---|
| Identified | proposed |
| Verified | review |
| Valued | review |
| Assigned | approved |
| Transferred | executed |
| Funded | funded |
| Monitored | active |
| Disposed / Replaced | retired |
| Archived | archived |

### Person / Role

| Lifecycle Term | Canonical Status |
|---|---|
| Identified | proposed |
| Verified | review |
| Role Proposed | proposed |
| Accepted | approved |
| Active | active |
| Suspended / Replaced | corrective_action |
| Former | retired |
| Archived | archived |

### Instrument

| Lifecycle Term | Canonical Status |
|---|---|
| Requested | proposed |
| Drafting | draft |
| Review | review |
| Approved | approved |
| Executed | executed |
| Certified | completed |
| Recorded / Stored | archived |
| Superseded | superseded |
| Archived | archived |

### Relationship

| Lifecycle Term | Canonical Status |
|---|---|
| Proposed | proposed |
| Verified | review |
| Active | active |
| Disputed | disputed |
| Corrected | corrective_action |
| Retired | retired |
| Archived | archived |

### Evidence / Archive

| Lifecycle Term | Canonical Status |
|---|---|
| Received | intake |
| Logged | active |
| Verified | review |
| Linked | approved |
| Preserved | archived |
| Exported | completed |
| Retention Review | review |

## ADR-11A Rules

- All status fields should eventually use canonical internal values.
- UI may show display labels, not raw internal values.
- State transitions must be governed by ADR-12.
- Events caused by status changes must be governed by ADR-13.
- A record may be inactive without being deleted.
- Deletion is not a lifecycle state for institutional records.

## ADR-11A Findings

This vocabulary prevents future fragmentation across trusts, matters, assets, people, instruments, relationships, evidence, reports, archive, and research modules.
