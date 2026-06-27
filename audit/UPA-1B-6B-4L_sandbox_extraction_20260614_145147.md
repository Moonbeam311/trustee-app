# UPA-1B-6B-4L — Sandbox Dual-Database Extraction and Reconciliation

Generated: 2026-06-14T14:51:48.672636
Status: **SANDBOX_EXTRACTION_RECONCILIATION_FAILED**

## Source Safety

- Source integrity: `ok`
- Source database unchanged: **True**

## Final Manifest

- Total source rows: **24809**
- Firm 1 only: **523**
- Firm 2 only: **365**
- Shared/global: **23921**

## Firm 1 Sandbox

- Database: `C:\Users\LunaMishoe\Desktop\trustee-app-clean\audit\runtime_sandbox\UPA-1B-6B-4L_20260614_145147\trustee_app_firm1_sandbox.db`
- Expected rows: **24444**
- Actual rows: **24446**
- Integrity: `ok`
- Reconciled: **False**
- Explicit opposite-firm violations: **0**

## Firm 2 Sandbox

- Database: `C:\Users\LunaMishoe\Desktop\trustee-app-clean\audit\runtime_sandbox\UPA-1B-6B-4L_20260614_145147\trustee_app_firm2_sandbox.db`
- Expected rows: **24286**
- Actual rows: **24288**
- Integrity: `ok`
- Reconciled: **False**
- Explicit opposite-firm violations: **0**

## Referential Review

- Foreign-key warnings: **0**

## Authorization

- Sandbox runtime validation authorized: **False**
- Production cutover authorized: **False**
- Live database replacement authorized: **False**
