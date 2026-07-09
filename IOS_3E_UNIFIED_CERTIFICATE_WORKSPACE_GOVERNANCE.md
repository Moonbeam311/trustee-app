# IOS-3E — Unified Certificate Workspace Governance

## Renamed Milestone

Former working title:

IOS-3E — Certificate ↔ Governance Integration

Renamed to:

IOS-3E — Unified Certificate Workspace Governance

## Reason for Rename

The IOS now contains multiple certificate surfaces:

- Legacy Certificate Registry
- Trust Minute Certificates
- Certificate of Trust outputs
- Transfer Certificates
- Continuity Certificates
- Unified Certificate Studio
- Certificate Workspace
- Certificate Object API
- Certificate Event Bus
- Certificate Relationship Graph

Because the Certificate Studio / Workspace is becoming the institutional certificate object layer, governance should be integrated into the Unified Certificate Workspace rather than scattered across legacy certificate pages.

## Architectural Direction

Governance integration will follow the successful Matter and Trust pattern:

1. Governance relationship surface
2. Governance summary
3. Governance timeline
4. Governance impact analysis
5. Smoke audit

## IOS-3E Checkpoints

- IOS-3E.1 — Certificate Workspace Governance Surface
- IOS-3E.2 — Certificate Workspace Governance Timeline & Summary
- IOS-3E.3 — Certificate Workspace Governance Impact Analysis
- IOS-3E.4 — Certificate Workspace Governance Smoke Audit

## Scope Boundary

IOS-3E will begin with the Unified Certificate Workspace route:

/certificate-studio/workspace/<certificate_type>/<certificate_id>

Do not add governance panels to every legacy certificate page at this stage.

No schema changes unless a later checkpoint proves they are necessary.
No new governance record types.
No changes to Matter or Trust governance behavior.
