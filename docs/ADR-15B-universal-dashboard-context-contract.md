# ADR-15B — Universal Dashboard Context Contract

## Purpose
Define the context dictionary required to render a universal institutional object dashboard.

## Context Contract

Object dashboard context must include object_type, object_id, title, status, status_label, workspace_owner, summary, identity, lifecycle, relationships, events, tasks, evidence, compliance, actions, reports, archive, history, and extensions.

## Required Guarantees
- Missing data returns empty lists or dictionaries.
- Templates do not perform deep database logic.
- Every dashboard shows identity, lifecycle, relationships, events, evidence, archive status, and actions.
- Legacy routes remain available during migration.
- Object-specific data belongs in extensions.

## First Target
Matter is first because it connects governance, events, relationships, documents, archive, and risk.
