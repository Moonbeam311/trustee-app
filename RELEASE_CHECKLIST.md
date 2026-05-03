# Trustee App Release Checklist

## Required Pre-Release Checks

Run these commands from the project root before committing, pushing, or deploying:



Expected smoke test result:



## What the Smoke Test Covers

The authenticated local route smoke test verifies:

- Admin dashboard
- Storage diagnostics
- Trust branding page
- Packet preview
- Controlled packet ZIP export
- Articles final surface and PDF
- Trustee Acceptance final surface and PDF
- General Assignment final surface and PDF
- Organizational Minutes final surface and PDF
- Successor Trustee final surface and PDF
- Declaration final surface and PDF
- Certificate final surface and PDF

## Release Rule

Do not deploy a new patch phase unless:



If the smoke test fails, stop and fix the failing route before pushing or deploying.
