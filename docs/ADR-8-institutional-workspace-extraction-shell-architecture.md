# ADR-8 — Institutional Workspace Extraction & Shell Architecture

## Purpose

Stop treating `/admin` as one long page.

Convert the Trustee App into an institutional shell with separate workspace dashboards.

## Core Rule

The Executive Home should not display every tool.

The Executive Home should show:

- Institution health
- Continue where you left off
- Recommended next action
- Recent institutional activity
- Notifications
- Workspace launcher

All operational tools belong inside one of the seven workspaces.

## Permanent Workspaces

1. HOME
2. CREATE
3. ADMINISTER
4. LEGACY
5. LEARN
6. REPORTS
7. SYSTEM

## Workspace Routes

- `/admin/workspace/home`
- `/admin/workspace/create`
- `/admin/workspace/administer`
- `/admin/workspace/legacy`
- `/admin/workspace/learn`
- `/admin/workspace/reports`
- `/admin/workspace/system`

## Workspace Templates

- `admin_workspace_home.html`
- `admin_workspace_create.html`
- `admin_workspace_administer.html`
- `admin_workspace_legacy.html`
- `admin_workspace_learn.html`
- `admin_workspace_reports.html`
- `admin_workspace_system.html`

## Migration Rule

Do not delete old sections immediately.

First extract them into workspace templates.

Then verify routes.

Then simplify `/admin`.

## Workspace Content Map

### HOME

Executive overview only.

### CREATE

- Start New Intake
- Create Trust
- Import Existing Trust
- Instrument Registry
- Document Generator
- Templates

### ADMINISTER

- Matter Operations
- Trust Operations
- Funding
- Execution
- Assets
- Trustees
- Beneficiaries
- Minutes
- Certificates
- Relationships
- Compliance

### LEGACY

- Genealogy
- Media
- Family History
- Workspaces
- Discussions
- Legacy Compatibility
- Archive Memory

### LEARN

- Learning Hub
- Trust Types
- Forms Guide
- Videos
- Articles
- Playbooks

### REPORTS

- Report Center
- Portfolio PDF
- Audit PDF
- Fiduciary PDF
- Certificates
- Exports
- Lifecycle Ledger
- Archive Proof

### SYSTEM

- Users
- Roles
- Permissions
- Security
- System Health
- Database Backup
- Railway Checklist
- Hosted Seed
- Export Policy
- Read-Only Mode

## Success Criteria

ADR-8 is successful when `/admin` becomes an executive home and each major function has a dedicated workspace dashboard.
