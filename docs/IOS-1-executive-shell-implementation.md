# IOS-1 — Executive Shell Implementation

## Purpose

Begin implementing the Institutional Operating System defined by IIA-1 through IIA-4.

## Core Rule

Do not break existing routes.

Do not delete existing dashboards.

Do not remove legacy access.

Build the IOS shell beside the existing system first, then progressively migrate.

## IOS Implementation Sequence

1. IOS-1 — Executive Shell
2. IOS-2 — Workspace Engine
3. IOS-3 — Module Registry
4. IOS-4 — Universal Record Layout
5. IOS-5 — Relationship Explorer
6. IOS-6 — Workflow Engine

## IOS-1 Objective

Create the permanent Executive Shell that will eventually replace the long admin dashboard.

The shell must provide:

- Institution identity
- Operator context
- Executive Home
- Workspace navigation
- Continue work
- Recent activity placeholder
- Alerts placeholder
- System health shortcut
- Legacy admin fallback

## IOS-1 Safety Rule

The current `/admin` route remains active.

The new shell begins at:

`/ios`

This allows controlled testing before replacing `/admin`.

## IOS-1 Success Criteria

IOS-1 is successful when:

- `/ios` loads.
- It uses the same platform shell styling.
- It displays the executive operating surface.
- It links back to `/admin`.
- Existing routes remain untouched.
