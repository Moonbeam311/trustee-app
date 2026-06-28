# ADR-9 — Workspace Dependency Map

Defines allowed workspace dependencies.

HOME may summarize all workspaces.
CREATE may create objects used by ADMINISTER, PEOPLE, GOVERNANCE, and COMPLIANCE.
ADMINISTER may depend on PEOPLE, ASSETS, EXECUTION, FUNDING, and ARCHIVE.
GOVERNANCE may depend on ADMINISTER, PEOPLE, COMPLIANCE, and ARCHIVE.
COMPLIANCE may depend on CREATE, ADMINISTER, GOVERNANCE, and ARCHIVE.
REPORTS may read from all workspaces but should not own operational records.
SYSTEM owns users, permissions, security, and health.
DEVELOPER owns diagnostics, ADRs, seed data, migrations, and internal tools.

Rule: avoid circular ownership. One workspace owns; others reference.
