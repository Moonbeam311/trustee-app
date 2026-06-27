# IIA-1 — Institutional Information Architecture

## Purpose

Define the master operating architecture for the Trustee App.

This document determines where every screen, route, workflow, record, and future module belongs.

## Core Principle

The application is not organized by pages.

It is organized by institutional function.

## Primary Institutional Departments

1. EXECUTIVE HOME
2. CREATE
3. ADMINISTER
4. REVIEW
5. REPORTS
6. LIBRARY
7. SYSTEM

## EXECUTIVE HOME

Purpose:
Show the operator where they are, what needs attention, what changed, what to do next, and where to go.

Includes:
- Continue Previous Work
- Today's Priorities
- Institutional Alerts
- Recent Activity
- Quick Actions
- Institution Health
- Workspace Launcher

Does NOT include:
- Full operational dashboards
- Raw system tools
- Long link lists
- Developer functions

## CREATE

Purpose:
Start new institutional work.

Includes:
- New Matter
- New Trust
- New Person
- New Entity
- New Asset
- New Document
- New Instrument
- New Meeting
- Import Existing Trust
- Template-Based Creation
- Guided Intake

## ADMINISTER

Purpose:
Operate active institutional records.

Includes:
- Trust Registry
- Matter Registry
- Funding
- Execution
- Assets
- Beneficiaries
- Trustees
- Fiduciaries
- Property
- Insurance
- Tax
- Minutes
- Certificates
- Transfers
- Relationship Registry

## REVIEW

Purpose:
Control institutional judgment, verification, readiness, risk, and governance.

Includes:
- Matter Review
- Execution Readiness
- Funding Readiness
- Compliance Review
- Risk Engine
- Verification
- Relationship Validation
- Authenticity
- Evidence Review
- Provenance
- Governance Decisions
- Approval Queues

## REPORTS

Purpose:
Produce controlled institutional outputs.

Includes:
- Trust Reports
- Matter Reports
- Audit Reports
- Compliance Reports
- Funding Reports
- Tax Reports
- Inventory Reports
- Certificates
- Export Center
- Print Center
- Evidence Packages
- Archive Packages

## LIBRARY

Purpose:
Hold institutional knowledge and learning materials.

Includes:
- Learning Hub
- Trust Types
- Forms Guide
- Videos
- Playbooks
- Templates
- Checklists
- Glossary
- Reference Law
- Sample Trusts
- Research Notes

## SYSTEM

Purpose:
Operate the platform itself.

Includes:
- Users
- Roles
- Permissions
- Security
- Database
- Backups
- Deployment
- Railway Readiness
- Hosted Seed
- Policy Controls
- Feature Flags
- Logs
- Developer Tools
- Legacy Compatibility

## Future Trust Modules

Future trust types must be mapped before being added.

Examples:
- ILIT
- Dynasty Trust
- Pet Trust
- Firearms Trust
- Charitable Trust
- Business Trust
- Special Needs Trust
- Ecclesiastical Trust
- Hybrid Trust Structures

These belong in CREATE for creation, ADMINISTER for operation, REVIEW for readiness/governance, REPORTS for outputs, and LIBRARY for education.

## Institutional Record Standard

Every major record should eventually support:

- Overview
- People / Parties
- Relationships
- Timeline
- Documents
- Evidence
- Review
- Governance
- Compliance
- Reports
- Archive
- Notes

## Migration Rule

Do not delete existing routes.

Do not break current workflows.

First classify.

Then extract.

Then simplify.

Then enhance.

## Success Criteria

IIA is successful when:

- `/admin` becomes Executive Home.
- Operational tools move into departments.
- Users navigate by institutional purpose.
- Future modules have a clear place before they are built.
- The platform feels like an institutional operating system, not a collection of dashboards.
