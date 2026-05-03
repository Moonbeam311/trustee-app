# Trustee App Hosted Smoke Test Checklist

## Production App

Use the confirmed active Railway production service:

https://trustee-app-production.up.railway.app

Confirmed Railway production project/service:

charismatic-tranquility / trustee-app

## Required Local Pre-Check

Before browser validation, run:

python -m py_compile app.py database/db.py scripts/smoke_routes.py
python scripts/smoke_routes.py

Expected:

ALL SMOKE TEST ROUTES PASSED

## Browser Login

Open:

https://trustee-app-production.up.railway.app/login

Log in with the active admin credentials.

## Hosted Browser Route Checklist

Use test trust:

TR-001

### Admin + Diagnostics

Open:

https://trustee-app-production.up.railway.app/admin

Confirm:
- Admin dashboard loads.
- No 500 error.

Open:

https://trustee-app-production.up.railway.app/admin/storage-diagnostics

Confirm:
- DB_PATH points to persistent path.
- UPLOAD_FOLDER points to persistent path.
- RAILWAY_SERVICE_NAME is trustee-app.
- RAILWAY_PROJECT_NAME is charismatic-tranquility.

### Branding

Open:

https://trustee-app-production.up.railway.app/trust/TR-001/branding

Confirm:
- Branding page loads.
- V3 Minimal and V1 Formal options are available.
- Save buttons are visible.

### Packet Preview

Open:

https://trustee-app-production.up.railway.app/trust/TR-001/packet-preview

Confirm:
- Readiness Advisory appears.
- Branding Readiness appears.
- Export Policy says Advisory mode.
- Packet Export Status uses advisory wording.
- Download Controlled Trust Packet ZIP is visible.
- No strict-mode blocked language appears.

### Final Document Surfaces

Open each:

https://trustee-app-production.up.railway.app/trust/TR-001/articles-output-surface
https://trustee-app-production.up.railway.app/trust/TR-001/trustee-acceptance-output-surface
https://trustee-app-production.up.railway.app/trust/TR-001/general-assignment-output-surface
https://trustee-app-production.up.railway.app/trust/TR-001/organizational-minutes-output-surface
https://trustee-app-production.up.railway.app/trust/TR-001/successor-trustee-output-surface
https://trustee-app-production.up.railway.app/trust/TR-001/declaration-output-surface
https://trustee-app-production.up.railway.app/trust/TR-001/certificate-of-trust-output-surface

Confirm each:
- Page loads with no 500.
- Universal letterhead appears.
- Document title appears once.
- Readiness advisory appears where applicable.
- Print/download actions are visible.

### PDF Routes

Open or download each:

https://trustee-app-production.up.railway.app/trust/TR-001/articles-output-surface/pdf
https://trustee-app-production.up.railway.app/trust/TR-001/trustee-acceptance-output-surface/pdf
https://trustee-app-production.up.railway.app/trust/TR-001/general-assignment-output-surface/pdf
https://trustee-app-production.up.railway.app/trust/TR-001/organizational-minutes-output-surface/pdf
https://trustee-app-production.up.railway.app/trust/TR-001/successor-trustee-output-surface/pdf
https://trustee-app-production.up.railway.app/trust/TR-001/declaration-output-surface/pdf
https://trustee-app-production.up.railway.app/trust/TR-001/certificate-of-trust-output-surface/pdf

Confirm:
- PDF downloads or opens.
- No 500 error.
- Branding appears in PDF output.

### Controlled Packet ZIP

Open:

https://trustee-app-production.up.railway.app/trust/TR-001/controlled-packet-export

Confirm:
- ZIP downloads.
- Export is not blocked.

## Hosted Smoke Test Pass Criteria

Hosted smoke test passes only if:
- Admin loads.
- Storage diagnostics confirm production/persistent paths.
- Packet preview shows advisory mode.
- All final surfaces load.
- All PDFs load/download.
- Controlled packet ZIP downloads.
- No 500 errors.
- No strict-mode blocked language.

## Failure Rule

If any route returns 404, 500, Internal Server Error, or Packet export blocked, stop and diagnose before pushing the next patch phase.
