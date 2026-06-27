# IOS-2 — Workspace Migration Engine

## Purpose

Convert the Trustee App from one long admin dashboard into a workspace-based institutional operating system.

## Core Decision

Do not create a separate `/ios` route tree.

Use the existing workspace router:

`/admin/workspace/<workspace_key>`

This becomes the IOS routing spine.

## Workspace Keys

- home
- create
- administer
- people
- governance
- compliance
- legacy
- library
- research
- archive
- reports
- system
- developer

## Migration Rule

Do not delete legacy routes.

Do not break `/admin`.

Do not remove existing dashboard functionality.

Instead:

1. Create workspace template.
2. Link workspace route.
3. Move or mirror one logical section.
4. Verify.
5. Then simplify `/admin`.

## Migration Order

1. HOME Workspace
2. CREATE Workspace
3. ADMINISTER Workspace
4. PEOPLE Workspace
5. GOVERNANCE Workspace
6. COMPLIANCE Workspace
7. LEGACY Workspace
8. LIBRARY Workspace
9. RESEARCH Workspace
10. ARCHIVE Workspace
11. REPORTS Workspace
12. SYSTEM Workspace
13. DEVELOPER Workspace

## HOME Workspace

Executive overview only.

Includes:

- Institution Health
- Continue Work
- Recommended Next Action
- Recent Activity
- Notifications
- Workspace Launcher

## CREATE Workspace

Includes:

- Start New Intake
- Review Saved Intakes
- Create Trust
- Create Instrument
- Generate Document
- Templates
- Future Trust Types

## ADMINISTER Workspace

Includes:

- Trust Operations
- Matter Operations
- Funding
- Execution
- Assets
- Trustees
- Beneficiaries
- Minutes
- Certificates
- Relationships

## PEOPLE Workspace

Includes:

- Persons
- Families
- Organizations
- Trustees
- Beneficiaries
- Advisors
- Witnesses
- Notaries

## GOVERNANCE Workspace

Includes:

- Governance States
- Decisions
- Review Queue
- Risk Engine
- Approvals
- Findings
- Recommendations

## COMPLIANCE Workspace

Includes:

- Execution Readiness
- Funding Readiness
- Missing Items
- Signature Status
- Witness/Notary Status
- Legal Holds
- Annual Reviews

## LEGACY Workspace

Includes:

- Genealogy
- Family History
- Media
- Artifacts
- Foundation
- Stories
- Historical Timeline

## LIBRARY Workspace

Includes:

- Learning Hub
- Trust Types
- Forms Guide
- Videos
- Playbooks
- Templates
- Glossary

## RESEARCH Workspace

Includes:

- ILIT Research
- Dynasty Trust Research
- Pet Trust Research
- Firearms Trust Research
- Ecclesiastical Trust Research
- Comparative Notes
- Future Trust Concepts

## ARCHIVE Workspace

Includes:

- Evidence
- Provenance
- Chain of Custody
- Snapshots
- Transfer Packages
- Continuity Packages
- Retention

## REPORTS Workspace

Includes:

- Report Center
- Portfolio PDF
- Audit PDF
- Fiduciary PDF
- Certificates
- Exports
- Evidence Packages

## SYSTEM Workspace

Includes:

- Users
- Roles
- Permissions
- Security
- System Health
- Backups
- Hosted Seed
- Policy Controls

## DEVELOPER Workspace

Hidden/admin-only.

Includes:

- ADR Library
- Route Registry
- Diagnostics
- Migration Center
- Seed Data
- Testing
- Experimental Features

## Success Criteria

IOS-2 is successful when every major admin dashboard section has a workspace destination and `/admin` can be simplified into an Executive Home without losing access to legacy functionality.
