# UPA-1B-6B-4N — Permission Duplicate-Multiplicity and Locator-Collision Trace

Generated: 2026-06-14T15:03:25.723161
Status: **PERMISSION_LOCATOR_COLLISION_CONFIRMED_CONTENT_REVIEW_REQUIRED**

## Safety

- Integrity: `ok`
- Live database unchanged: **True**

## Permissions Reconciliation

- Source permission rows: **15**
- Manifest permission rows: **13**
- Multiplicity gap: **2**
- Duplicate locator groups: **1**
- Exact duplicate content groups: **0**
- Locator difference groups: **1**
- Locator difference total: **2**

## Primary-Key and Index Review

- Primary-key columns: `['permission_id']`
- Index `sqlite_autoindex_permissions_2` | unique=True | columns=['permission_name']
- Index `sqlite_autoindex_permissions_1` | unique=True | columns=['permission_id']

## Locator Differences

- `permissions|{"permission_id":null}` | source=3 | manifest=1 | difference=2 | distinct-content=3

## Authorization

- Manifest correction authorized: **False**
- Sandbox rebuild: **NOT AUTHORIZED**
- Runtime validation: **NOT AUTHORIZED**
- Production cutover: **NOT AUTHORIZED**
- Live database modification: **PROHIBITED**
