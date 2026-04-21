# PROJECT CONTINUITY — SUPERSEDING NOTE (CANONICAL)

## PURPOSE
This document supersedes fragmented handoff notes across prior threads and files.
It defines the CURRENT authoritative architecture, intent, and constraints.

All future work must reconcile with this document before making changes.

---

# 1. ARCHITECTURE — LOCKED

## Core Architecture
- Native SQLite helper architecture (database/db.py)
- app.py = route + application logic
- templates/ = UI layer

## Non-Negotiable Rule
DO NOT:
- introduce ORM abstractions
- refactor to SQLAlchemy
- replace helper-based data access

EXTEND ONLY:
- existing helper functions
- existing route patterns

---

# 2. AUTHENTICATION + SESSION MODEL — LOCKED

## Identity Sources
- Role → session["role"]
- User → session["username"]
- Activity → session["last_activity"]

## Enforcement
- All access control is session-based
- Query-string role injection is deprecated and removed

## Removed
- `acting_role` URL pattern (DEPRECATED)
- user guidance suggesting role via URL (REMOVED)

---

# 3. OWNER ISOLATION — LOCKED

## Current Model
- Owner = get_current_owner()
- Source = session["username"]

## Fully Removed
- ADMIN_OWNER_001 (no longer valid anywhere)

## Enforcement
- Route guards use owner_id == get_current_owner()
- Create paths assign owner_id = get_current_owner()
- Data reads filter by owner_id

---

# 4. DASHBOARD INTENT — LOCKED

## Trustee Dashboard
Route: `/`
Function: home
Purpose:
- primary operational landing
- NOT limited to trustee-only semantics anymore
- functions as general authenticated dashboard

## Fiduciary Layer
Route: `/fiduciaries`
Function: fiduciary_dashboard
Purpose:
- fiduciary role management layer
- NOT a landing page

## Admin Panel
Route: `/admin`
Function: admin_index
Purpose:
- system-level control
- Admin only

---

# 5. LOGIN / REDIRECT — LOCKED

## Correct Behavior
- Admin → /admin
- Trustee → /
- Viewer → /portfolio

## Critical Correction (Already Applied)
Trustee must NOT redirect to `/fiduciaries`

---

# 6. ROLE SYSTEM — LOCKED

## Enforcement Engine
- ROLE_RULES
- enforced in before_request

## Role Definitions

### Admin
- full system access
- exclusive access to:
  - admin_index
  - role_dashboard
  - permissions_dashboard
  - security_dashboard
  - audit_dashboard

### Trustee
- operational access layer
- no system-control privileges

### Viewer
- read-safe layer only
- no operational or administrative actions

---

# 7. NAVIGATION MODEL — LOCKED

## _nav.html
- role-aware (IMPLEMENTED)
- Admin block → Admin only
- operational block → Admin + Trustee
- Viewer currently minimal (intentional)

## _platform_nav.html
- role-aware (IMPLEMENTED)
- Admin → Admin link
- Trustee → Reports + shared modules
- Viewer → shared read-safe modules

## Principle
A link MUST NOT be visible if the role cannot access the route.

---

# 8. CONFIRMED PERMISSION MAP

## Admin-only
- /admin
- /roles
- /permissions
- /security
- /audit

## Admin + Trustee
- /exports
- /fiduciaries
- /genealogy
- /media
- /reports
- workflow + trust operations

## Admin + Trustee + Viewer
- /learning
- /videos
- /workspaces
- /discussions
- /decision
- /execution
- /documents
- /visualization

---

# 9. KNOWN GAPS (INTENTIONAL — DO NOT GUESS)

The following routes must be explicitly defined in ROLE_RULES:

- home
- workflow_hub
- portfolio_dashboard

## Recommended (NOT AUTO-APPLIED)

- home → Admin, Trustee, Viewer
- workflow_hub → Admin, Trustee
- portfolio_dashboard → Admin, Trustee, Viewer

These must be confirmed before enforcement patching.

---

# 10. CONTINUITY ALIGNMENT

## Legacy Notes (Still Valid)
- SQLite helper architecture is correct
- Workflow Hub is a core system module
- Admin index / manifest is intentional
- Route consistency cleanup was already a known priority

## Superseding Clarifications
- Trustee dashboard is `/`
- fiduciary_dashboard is NOT a dashboard landing
- acting_role is fully deprecated
- owner isolation is now real (not placeholder)
- nav must always reflect ROLE_RULES

---

# 11. DEVELOPMENT RULES — MANDATORY

## DO
- inspect before modifying
- patch surgically
- verify with grep + compile
- preserve stable modules
- align UI with backend permissions

## DO NOT
- guess route purpose
- expose links without permission check
- overwrite working modules
- introduce parallel architecture

---

# 12. CURRENT PHASE STATUS

## Phase 4
- placeholder owner isolation COMPLETE

## Phase 5
- real session owner integration COMPLETE
- login redirect correction COMPLETE
- acting_role removal COMPLETE

## Phase 6 (ACTIVE)
- nav role-awareness COMPLETE
- continuity audit COMPLETE
- mismatch audit COMPLETE

## Next Safe Step
- explicitly define ROLE_RULES for:
  - home
  - workflow_hub
  - portfolio_dashboard

---

# 13. FINAL DIRECTIVE

This document is the PRIMARY reference.

If any future instruction conflicts with this:
- STOP
- AUDIT
- RECONCILE BEFORE PATCHING

No further architectural decisions should be made without referencing this file.
