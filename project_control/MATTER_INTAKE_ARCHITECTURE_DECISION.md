# MIA-0C — Matter–Intake Architectural Adoption and Repair Decision

**Decision Date:** 2026-06-14T19:52:48.577737
**Repository:** `C:\Users\LunaMishoe\Desktop\trustee-app-clean`
**Branch:** `strapback/stable-661bb66`
**HEAD:** `1cf6497598d9d294bc0453847b896316f863c241`
**Decision Status:** ADOPTED WITH REQUIRED INTEGRATION REPAIR

## Evidence Reviewed

- `audit/MIA-0A_matter_intake_baseline_20260614_194425.json`
- `audit/MIA-0B_matter_intake_linkage_authority_20260614_195116.json`

## Verified Baseline

- Matter tables identified: **3**
- Intake tables identified: **42**
- Direct bridge tables identified: **0**
- Matter–Intake integration routes identified: **1**
- Matter–Intake integration functions identified: **1**
- Matter–Intake integration templates identified: **6**
- Shared or duplicated authority areas: **5**
- Broadly relevant mixed-firm tables: **10**

## Architectural Decision

The Matter system is adopted as the authoritative operational and governance spine of the application.

The Intake system is adopted as the upstream information-gathering, assessment, and recommendation process.

The Matter Relationship system is adopted as the governed linkage layer connecting Matters to trusts, people, assets, documents, transfers, policies, businesses, and other institutional records.

The present implementation is not considered fully integrated because no direct Matter–Intake bridge table was identified and the only detected integration route is an administrative lifecycle-table repair route rather than an operational handoff.

## Required Lifecycle

```text
Intake created
→ Intake information gathered
→ Intake assessment completed
→ Intake reviewed
→ Matter created or selected
→ Intake formally linked to Matter
→ Preliminary findings accepted, modified, or rejected
→ Matter governance and risk controls activated
→ Relationships and workstreams created
→ Drafting, execution, funding, and administration governed
→ Matter closure and archive
```

## Authority Allocation

| Concept | Authoritative Owner | Rule |
|---|---|---|
| Intake questionnaire progress | Intake | Intake controls completion of intake questions and modules. |
| Intake completeness | Intake | Intake determines whether required information has been supplied. |
| Initial complexity | Intake | Intake records an assessment, not the final Matter governance decision. |
| Preliminary risk | Intake | Intake recommends risk; Matter accepts or changes it. |
| Preliminary priority | Intake | Intake recommends priority; Matter owns active priority. |
| Submitted-information review | Intake | Review proves review of supplied information only. |
| Matter lifecycle status | Matter | Matter controls open, active, held, closed, and archived states. |
| Governance state | Matter | Matter owns governance progression. |
| Final operational risk | Matter | Matter owns the active risk classification. |
| Final operational priority | Matter | Matter owns active work priority. |
| Tasks and institutional events | Matter | Matter controls operational work and history. |
| Record relationship verification | Matter Relationship | Verification applies to the governed link and its stated basis. |
| Trust drafting and execution | Trust/document subsystems | Subsystem state is surfaced through Matter but not duplicated by Matter. |
| Matter closure and archive | Matter | Intake cannot close or archive a Matter. |

## Required Integration Repair

A formal Matter–Intake bridge must be implemented.

The bridge must support:

- one Intake linked to zero or one primary Matter;
- one Matter linked to one or more Intake records when supplemental or renewed intake is required;
- tenant-scoped Matter and Intake identifiers;
- linkage status and effective date;
- handoff actor and handoff date;
- acceptance, modification, or rejection of Intake recommendations;
- preserved Intake snapshot at handoff;
- Matter event creation when the linkage is established or changed;
- prohibition against silent synchronization;
- audit history for every linkage correction;
- no automatic legal-effect or authenticity presumption.

## Required Authority Repair

- `status` currently requires authority clarification; MIA-0B assessment: `DUPLICATED_OR_SHARED_AUTHORITY_REVIEW_REQUIRED`.
- `risk` currently requires authority clarification; MIA-0B assessment: `DUPLICATED_OR_SHARED_AUTHORITY_REVIEW_REQUIRED`.
- `priority` currently requires authority clarification; MIA-0B assessment: `DUPLICATED_OR_SHARED_AUTHORITY_REVIEW_REQUIRED`.
- `archive` currently requires authority clarification; MIA-0B assessment: `DUPLICATED_OR_SHARED_AUTHORITY_REVIEW_REQUIRED`.
- `verification` currently requires authority clarification; MIA-0B assessment: `DUPLICATED_OR_SHARED_AUTHORITY_REVIEW_REQUIRED`.

The repair must not delete existing Intake or Matter status fields until compatibility, migration, and regression testing are complete.

## Firm-Isolation Rule

The Matter–Intake bridge must be scoped by deployment-bound firm identity. Matching identifiers alone must never establish a cross-record link.

Firm 1 and Firm 2 may use the same human-readable identifier format only when their physical databases and runtimes remain isolated.

## Prohibited Changes During Initial Repair

- No production database split or replacement.
- No deletion of existing Intake tables.
- No replacement of the Matter Relationship subsystem.
- No admin-dashboard redesign.
- No specialty-trust expansion.
- No automatic migration of Intake authority into Matter without an evidence record.
- No marking of an Intake or Matter complete solely because a bridge exists.

## Next Authorized Action

**MIA-1A — Matter–Intake Bridge Schema and Compatibility Contract**

MIA-1A may design and implement the bridge schema in a backward-compatible manner. It must include migration safety, tenant scoping, event logging, rollback, and automated verification.

## Completion Gate

MIA-0C is complete when this decision is committed without adding the full untracked audit directory.
