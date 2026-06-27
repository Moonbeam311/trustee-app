# UPA-1B-6B-4V-5 — Startup Call-Graph Resolution

Generated: 2026-06-14T15:53:03.465404
Status: **AUTOMATIC_STARTUP_WRITER_CHAIN_RESOLVED_TARGETED_REPAIR_AUTHORIZED**

## Resolution

- `init_db()` calls `ensure_role_tables()`: **False**
- `ensure_role_tables()` reachable from startup: **True**
- Module directly calls hosted self-heal: **True**
- Hosted self-heal reachable from module startup: **True**
- Automatic role-permission write sites: **2**

## Authorization

- Targeted code repair: **True**
- Historical duplicate cleanup: **False**
- Runtime-profile build: **False**
- Production cutover: **False**
