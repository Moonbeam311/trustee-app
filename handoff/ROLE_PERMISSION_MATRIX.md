# ROLE PERMISSION MATRIX

## Admin
- Full access to admin, roles, permissions, security, users, reports, exports, operational dashboards, and shared platform areas.

## Trustee
- Operational trust-management access
- No admin control panel
- No roles / permissions / security dashboards
- Access to fiduciaries, genealogy, media, reports, exports, and most working layers

## Viewer
- Read-safe shared platform layers only
- Viewer expansion for nav is intentionally deferred
- Portfolio and home should be explicitly reviewed/confirmed as safe viewer destinations

## Confirmed Backend Strength
`ROLE_RULES` is broadly well-structured and already enforces most intended boundaries in `before_request`.

## Known Permission Map Gaps to Reconcile
Recommended explicit `ROLE_RULES` entries:
- `home`
- `workflow_hub`
- `portfolio_dashboard`

## Confirmed Admin-only
- `admin_index`
- `users_dashboard`
- `users_new`
- `users_edit`
- `users_reset_password`
- `role_dashboard`
- `permissions_dashboard`
- `security_dashboard`
- `audit_dashboard`

## Confirmed Admin/Trustee
- `fiduciary_dashboard`
- `genealogy_dashboard`
- `media_dashboard`
- `report_center`
- `export_center`
- trust creation steps
- property/account/document/ledger create flows

## Confirmed Admin/Trustee/Viewer
- `learning_dashboard`
- `video_dashboard`
- `workspace_dashboard`
- `discussion_dashboard`
- `decision_dashboard`
- `execution_dashboard`
- `document_dashboard`
- `visualization_dashboard`
