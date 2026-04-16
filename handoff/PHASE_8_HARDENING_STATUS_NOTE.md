# PHASE 8 HARDENING STATUS NOTE

## Status
Phase 8 security/deployment hardening has begun and completed the highest-value code-level fixes that were safe to apply without architectural change.

---

## Completed Hardening Changes

### Upload Path Integrity
- Removed duplicate `UPLOAD_FOLDER` definition
- Standardized on `UPLOAD_FOLDER = Path("uploads")`
- Added startup directory creation:
  - `UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)`

### Upload Filename Safety
- Document uploads already used `secure_filename`
- Media uploads were updated to also use `secure_filename`

### Media File Serving Safety
- `media_file` no longer blindly trusts stored DB paths
- Added checks to ensure:
  - file path resolves under `UPLOAD_FOLDER`
  - file exists
  - file is a regular file

### Export Endpoint Protection
- Added explicit `ROLE_RULES` entries for:
  - `export_handoff_file`
  - `export_roadmap_file`
  - `export_package_file`
  - `export_zip_snapshot`

This prevents relying only on Export Center visibility while leaving direct download routes implicitly open.

---

## Current Security Strengths

- Session-based auth
- Session-based role enforcement
- Session timeout enforcement
- Session cookie HttpOnly
- SameSite cookie policy set
- SESSION_COOKIE_SECURE tied to production mode
- MAX_CONTENT_LENGTH configured
- Owner isolation integrated

---

## Remaining Production Tasks (Not Yet Finalized)

### 1. Environment Hardening
Current code still allows:
- `FLASK_DEBUG` defaulting to `"1"`
- `SECRET_KEY` defaulting to a placeholder string

These are acceptable for development only and must be overridden in real deployment.

### 2. Deployment Runtime
Before production:
- use a production WSGI server
- ensure HTTPS is enabled
- ensure writable SQLite path is stable
- ensure writable uploads path is stable

### 3. File/Export Review
File-serving and export routes are improved, but production deployment should still include:
- path review
- file existence review
- least-privilege deployment checks

---

## Architectural Constraint
All hardening was performed without:
- ORM introduction
- architecture rewrite
- helper-layer replacement

SQLite helper architecture remains locked.

---

## Recommended Next Phase
Proceed to either:
- deployment environment configuration pass
or
- UI/UX polish / operational refinement

