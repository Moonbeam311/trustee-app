# PHASE 9 — RENDER DRY-RUN PLAN

## Status
This is a planning note only. No live deployment has been executed yet.

---

## Render Deployment Fit
The application is structurally compatible with Render because it now includes:
- `render.yaml`
- `wsgi.py`
- `requirements.txt`
- `gunicorn`
- `.env.example`

The current Render start command is:
- `gunicorn wsgi:app --bind 0.0.0.0:$PORT`

---

## Required Render Environment Variables
Set these in Render:

- `APP_ENV=production`
- `FLASK_DEBUG=0`
- `SECRET_KEY=<real long random secret>`
- `PORT` is usually injected by Render, but the current config includes `"5000"` as a default

---

## Critical Deployment Caveat — Persistence
The app currently relies on local filesystem persistence for:
- `trustee_app.db`
- `uploads/`

This means a Render deployment is only appropriate if:
- persistent disk is configured, OR
- the app is treated as a temporary/demo deployment only

Without persistent storage:
- uploaded files may disappear on restart/redeploy
- SQLite data may be lost or reset
- media/document links may break

---

## Dry-Run Goals
The goal of the first Render dry run is NOT full production launch.
The goal is to verify:

1. App boots successfully under Gunicorn
2. `SECRET_KEY` and env vars are wired correctly
3. login works
4. role redirects work
5. nav renders correctly
6. file upload path is writable
7. SQLite path is writable
8. no immediate import/runtime errors appear in production mode

---

## First Post-Deploy Smoke Test
After first Render deploy, verify:

### App boot
- landing page loads
- no 500 on first request

### Authentication
- Admin login works
- Trustee login works
- Viewer login works

### Navigation / Roles
- Admin sees Admin controls
- Trustee does not see Admin controls
- Viewer sees only Viewer-safe nav

### Upload / Media
- document upload succeeds
- media upload succeeds
- uploaded media can still be served

### Exports
- export center loads for Admin/Trustee
- protected export routes do not open for unauthorized roles

---

## Go / No-Go Rule
Proceed with a live Render deployment only if one of the following is true:

### GO
- persistent disk/storage strategy is confirmed
- OR deployment is explicitly temporary/demo only

### NO-GO
- if persistence is required but not configured

---

## Recommended Follow-up
Before real Render launch, decide:

1. Is this a demo deployment or persistent deployment?
2. If persistent:
   - how will `trustee_app.db` persist?
   - how will `uploads/` persist?

