# Trustee App — Feature Roadmap

## Architecture Rule
Continue using:
- `database/db.py` for helper/data logic
- `app.py` for routes
- `templates/` for UI

Do **not** introduce ORM architecture.

---

## Current Completed Base
- SQLite-native K-1
- SQLite-native Form 1041
- Instrument registry shell
- Shared navigation
- Workflow continuity
- Admin index + manifest
- Export bundle
- Final stabilization
- UI polish
- README / repo documentation pass

---

## Priority Queue

### Priority 1 — Safe Refinement
1. K-1 UX polish
   - better empty states
   - better success messaging
   - trust-year selection persistence

2. 1041 refinement
   - clearer worksheet labels
   - cleaner print output
   - improved warning tiers

3. Instrument registry refinement
   - stronger status workflow
   - safer record editing
   - better summary blocks

---

### Priority 2 — Operational Continuity
4. Export / download center
   - central export page
   - one-click package links
   - grouped handoff outputs

5. Admin reporting
   - trust counts
   - beneficiary counts
   - distribution counts
   - instrument counts

6. Route consistency cleanup
   - naming consistency
   - route grouping notes
   - template linkage checks

---

### Priority 3 — Later Controlled Expansion
7. Instrument class refinement
   - administrative voucher
   - trust note
   - evidentiary certificate
   - money order class
   - bill of exchange class

8. Module-level audit trails
   - record changes
   - timestamps
   - edit history notes

9. Repo/documentation growth
   - setup notes
   - screenshots
   - module usage guide

---

## Recommended Next Build Order
1. Export / download center
2. Admin reporting dashboard
3. K-1 / 1041 minor UX refinement
4. Later instrument class design

