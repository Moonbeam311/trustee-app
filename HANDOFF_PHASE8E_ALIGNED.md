# Trustee App — Phase 8E Aligned Checkpoint

## Stable Status
Local code, GitHub branch, Railway deployment, and hosted database migrations are aligned.

## Stable Branch
strapback/stable-661bb66

## Stable Tag
aligned-phase8e-railway-stable

## Completed Security / Governance Layers
- Role-based access control
- User-level permission allow/deny overrides
- Effective permission enforcement
- Export route protection
- Export activity logging
- Export attribution headers for K-1 CSV and 1041 TXT
- System policy controls
- Read-only mode enforcement
- Export enable/disable enforcement
- User creation policy enforcement
- Audit risk classification
- Audit dashboard filters
- Tamper-evident audit hash chain
- Audit Chain Integrity dashboard display

## Hosted Migration Fixes Completed
- Added Flask-WTF dependency
- Added audit_log hash-column migrations
- Added permissions and role_permissions startup initialization
- Seeded default permission matrix for Admin, Trustee, Viewer

## Verified Hosted Flow
- Admin login works
- Trustee login works
- Admin dashboard works
- Audit dashboard works
- Audit Chain Integrity shows VERIFIED
- Admin export works
- Trustee export denial works when export_documents is denied

## Do Not Touch Without Checkpoint
- app.py session gate
- require_export_permission()
- get_effective_permissions_for_user()
- ensure_role_tables()
- init_audit_table()
- Railway deployment branch
- requirements.txt dependency list
