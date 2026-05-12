# GLOBAL 411 FIREWALL — Production Hardening Checklist

## Locked Status

The Global 411 Firewall is confirmed for restricted Admin 2 / FIRM-002.

Confirmed:
- FIRM-002 Admin can access own firm records.
- FIRM-002 Admin cannot access FIRM-001 trust packet export.
- FIRM-002 Admin cannot access FIRM-001 report by internal ID.
- System health is Master Admin only.
- Storage diagnostics are Master Admin only.
- Database backup routes are Master Admin only.
- Certificate registry is Master Admin only.
- Report Center displays firm-local trust codes.
- Financial tables and helpers are firm-scoped.

## Restricted Admin 2 Allowed Surfaces
- /admin
- /reports
- /execution
- /workspaces
- /documents
- /media
- /audit
- /permissions
- /instruments
- own firm packet exports
- own firm reports

## Master Admin Only Routes
- /system/health
- /system/health/export.zip
- /system/health/export.json
- /system/health/export.txt
- /admin/storage-diagnostics
- /admin/backup/database
- /admin/backup/database.zip
- /certificates

## Safe Commit Checklist
Run py_compile, git diff --check, and git status before security-sensitive commits.
Never commit database.db, data/database.db, *.db, or data/backups/.
