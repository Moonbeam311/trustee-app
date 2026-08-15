# V3-1 Admin Dashboard / Institutional Command Center Reconstruction

## Consolidation provenance

Integrated on 2026-08-13 under HOS-BRAND-1E from the read-only source state:

- Source: verified predecessor working state retained in restricted recovery evidence; publication uses repository-relative provenance only
- Branch: `post-v2-successor`
- HEAD: `0047fc053c4dfecaa4103af9b20c3811a0f564ad`
- `app.py`: `DAE28526D6585F08D9F1D7A2C321218F019C0D6777ABBABD532A5462B3E34607`
- `templates/admin_index.html`: `8893E039EDC70A20D8B0EAC8DEABD25D0468D8CB82D2567E140F4B7BF71361C7`
- `docs/v3_1_admin_command_center_reconstruction.md`: `CFE56DC1BCB3044441E57BBD7579EC9A0F1BB9D5328A00E1E47ED9E5F74BCA33`
- `scripts/audit_v3_1_admin_command_center_reconstruction.py`: `129A23FE2C7F13268F915EDAB0E46235892B582FB76C277C3A2D7075462079FD`

The `app.py` context hunk was integrated semantically so the target repository's
TPD lifecycle enforcement and Hindsfoot OS introduction/authentication changes
remain intact. The verified V3-1 template composition was preserved exactly.

## Prior dashboard problems

The prior Admin page had accumulated many large panels, repeated navigation,
placeholder activity content, mixed daily work with protected controls, and an
unbounded trust table. Important destinations were present, but their hierarchy
did not answer the operator's basic questions about context, attention, current
work, or the next safe action.

## Reconstructed information architecture

The command center now presents institutional context first, followed by bounded
attention indicators, eight task-oriented work lanes, continue-work and recent
activity panels, trust operations, and progressively disclosed secondary and
protected controls. The lanes are Create, Administer, Govern, Execute, Document
and Certify, Preserve, Learn and Research, and System Administration.

## Preserved entry points

The reconstruction preserves the established destinations for intake, matters,
trust creation and administration, portfolio, property, accounts, ledger,
transfers, fiduciaries, beneficiaries, people, genealogy, governance, execution,
documents, certificates, reports, audit, archive, continuity, learning, articles,
research, media, security, users, roles, permissions, exports, system health, and
authorized developer tools. Where a concept has no standalone registry route,
its visible label routes to the existing governed workspace or operational
dashboard instead of introducing a speculative endpoint.

## Role and firm behavior

The route continues to use the existing authentication and authorization
framework. Admin context is resolved from the active session. Master-admin-only
user, role, permission, certificate-framework, backup, and developer controls
remain separated. Recent activity uses the existing firm-scoped audit service,
is limited to eight entries, and excludes raw payloads.

## Files changed

- `app.py`: bounded Admin context construction only.
- `templates/admin_index.html`: command-center information architecture and
  responsive presentation.
- `scripts/audit_v3_1_admin_command_center_reconstruction.py`: static, route,
  role, firm, and preservation coverage.
- `docs/v3_1_admin_command_center_reconstruction.md`: implementation and test
  record.

No schema, migration, authentication, permission-definition, certificate,
execution, document-generation, archive, or recovery implementation changed.

## Validation record

Compilation and the focused V3-1 audit pass. An authenticated live HTTP smoke
against the disposable Flask runtime returned HTTP 200 for `/admin` and one
destination from every lane; login, logout, and post-logout protection also
passed. All application execution used a disposable byte-exact copy after the
operational database SHA and sidecar state were verified.

The in-app browser target was unavailable in the execution environment, so the
required manual visual, narrow-window, keyboard, and return-navigation review is
not certified by this phase. Those checks remain a user-review limitation rather
than an application failure.

## Route continuity matrix

| Capability | Prior destination | Reconstructed destination |
| --- | --- | --- |
| Trusts | `/` in the source repository | `/workspace` in the Hindsfoot-branded target |
| Intake | `/intake/identity`, `/intake` | unchanged |
| Matters | `/matters` | unchanged |
| Portfolio | `/portfolio` | unchanged |
| Property / Accounts / Ledger | existing create-entry routes | `/add_property`, `/link_account`, `/ledger_entry` |
| Transfers / signatures / execution objects | trust and execution surfaces | `/execution` governed entry surface |
| Fiduciaries | `/fiduciaries` | unchanged |
| Beneficiaries / People | contextual records | `/admin/workspace/people` governed entry surface |
| Governance records | `/governance`, registry and detail routes | `/governance/dashboard`, `/governance/registry` |
| Documents / certificates | existing document and certificate surfaces | unchanged |
| Evidence / manifests | governance evidence exports | unchanged governed evidence routes |
| Audit / Archive / Continuity | existing audit and workspace surfaces | unchanged or `/admin/workspace/archive` |
| Learning / Research / Media | existing learning and IOS workspaces | unchanged or `/admin/workspace/research` |
| Security / Users / Roles / Permissions | existing protected routes | unchanged; visibility remains role-aware |

## Known limitations and deferred enhancements

- Counts are shown only for reliable existing services; speculative readiness
  categories are omitted.
- Continue Work links to existing dashboards because no new workflow persistence
  is authorized.
- V3-0 Master Register, compliance activation, hosted hardening and recovery,
  workspace redesigns, and trust-type expansion remain deferred and out of scope.
