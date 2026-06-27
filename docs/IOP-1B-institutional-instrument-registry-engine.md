# IOP-1B — Institutional Instrument Registry Engine

## Purpose

Create a foundational Instrument Registry subsystem for the Trustee App.

This is not merely an enhancement to “Create Instruments.”

It is the institutional catalog and control layer for every present and future instrument used by the platform.

## Core Principle

Instrument creation must be expandable.

The app must support today's instruments and future trust, estate, fiduciary, governance, funding, legacy, administrative, and custom instruments without requiring a redesign.

## Relationship to IOP-1A

IOP-1A established that intake and matter creation come before trust creation.

IOP-1B establishes that instruments are selected, recommended, created, reviewed, executed, and archived through a registry-driven system.

The workflow becomes:

1. Start New Matter
2. Intake
3. Decision Engine
4. Institutional Plan
5. Recommended Instruments
6. Instrument Registry
7. Drafting
8. Review
9. Execution
10. Funding
11. Governance
12. Archive

## Registry Categories

The Instrument Registry must support:

- Trust Formation Instruments
- Estate Instruments
- Fiduciary Instruments
- Governance Instruments
- Funding Instruments
- Execution Instruments
- Financial Instruments
- Property Instruments
- Litigation / Evidence Instruments
- Legacy Instruments
- Administrative Instruments
- Custom Instruments
- Future Organization Templates

## Instrument Metadata

Every instrument should capture:

- Instrument ID
- Matter ID
- Trust ID, if applicable
- Estate ID, if applicable
- Category
- Instrument Type
- Instrument Name
- Purpose
- Status
- Version
- Required Signers
- Required Witnesses
- Notary Required
- Funding Related
- Execution Related
- Governance Related
- Archive Required
- Related Instruments
- Template Source
- Notes

## Status Values

Recommended default status values:

- Draft
- In Review
- Approved
- Ready for Execution
- Executed
- Funded
- Archived
- Superseded
- Retired

## Instrument Selection Types

The registry must distinguish:

- Required Instruments
- Recommended Instruments
- Optional Instruments
- Custom Instruments
- User-Added Instruments
- Admin-Added Templates
- Future Instrument Types

## Design Requirement

Do not hard-code the final instrument list.

The app should allow future instrument types to be added by database seed, admin template, or later UI without changing the core workflow.

## Initial Build Goal

IOP-1B begins as a blueprint and registry schema plan.

Later build steps will add:

1. instrument_registry table
2. instrument_templates table
3. matter_instruments table
4. admin registry dashboard
5. matter-level instrument selection
6. custom instrument creation
7. instrument status tracking
8. instrument archive linkage

## Success Criteria

IOP-1B is successful when the application no longer treats instruments as isolated templates.

Instead, every instrument becomes a governed institutional record connected to matter, trust, review, execution, funding, governance, and archive workflows.
