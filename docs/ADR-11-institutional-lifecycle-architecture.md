# ADR-11 — Institutional Lifecycle Architecture

## Purpose

Define the lifecycle architecture for canonical institutional objects.

The app should not treat records as static pages. Every major institutional object should move through a recognized lifecycle.

## Core Principle

Every institutional object has:

- Creation state
- Review state
- Active operating state
- Exception/problem state
- Closure/archive state
- Legacy/reference state

## Universal Lifecycle

1. Proposed
2. Draft
3. Intake
4. Review
5. Approved
6. Active
7. Blocked
8. Corrective Action
9. Completed
10. Archived
11. Legacy Reference

## Trust Lifecycle

Proposed → Drafting → Review → Approved → Executed → Funded → Active Administration → Amendment / Restatement → Closed / Terminated → Archived → Legacy Reference

## Matter Lifecycle

Opened → Intake → Review → Active Work → Pending External Action → Resolution Drafting → Closed → Archived

## Asset Lifecycle

Identified → Verified → Valued → Assigned → Transferred → Funded → Monitored → Disposed / Replaced → Archived

## Person / Role Lifecycle

Identified → Verified → Role Proposed → Accepted → Active → Suspended / Replaced → Former → Archived

## Instrument Lifecycle

Requested → Drafting → Review → Approved → Executed → Certified → Recorded / Stored → Superseded → Archived

## Relationship Lifecycle

Proposed → Verified → Active → Disputed → Corrected → Retired → Archived

## Decision Lifecycle

Question Raised → Evidence Gathered → Recommendation Drafted → Decision Made → Implemented → Reviewed → Archived

## Evidence / Archive Lifecycle

Received → Logged → Verified → Linked → Preserved → Exported → Archived → Retention Review

## Research Lifecycle

Question Opened → Sources Collected → Analysis Drafted → Finding Proposed → Reviewed → Adopted / Rejected → Archived

## Compliance Lifecycle

Requirement Identified → Checklist Opened → Evidence Gathered → Review → Passed / Failed → Corrective Action → Closed → Archived

## Funding Lifecycle

Funding Need Identified → Source Proposed → Source Verified → Transfer Prepared → Transfer Executed → Receipt Confirmed → Ledgered → Monitored → Archived

## Execution Lifecycle

Execution Need Identified → Packet Prepared → Readiness Review → Signature / Witness / Notary → Defect Review → Final Record Archive → Certified Copy / Export

## ADR-11 Rules

- No major record should remain lifecycle-neutral.
- Lifecycle state should be visible on detail screens.
- Lifecycle transitions should be logged as institutional events.
- Archived does not mean deleted.
- Legacy Reference means preserved for institutional memory, not active work.
- Blocked and Corrective Action must be first-class states, not hidden notes.

## ADR-11 Findings

ADR-11 prepares the app for ADR-12, where lifecycle transitions become explicit state-machine rules.
