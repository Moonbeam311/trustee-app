# UPA-1B-6B-4R — 4Q Exception and Opposite-Firm Evidence Trace

Generated: 2026-06-14T15:12:05.167254
Status: **COMMON_RUNTIME_HARNESS_EXCEPTION_AND_SINGLE_FIRM2_SCOPE_ANOMALY_CONFIRMED**

## Summary

- Firm 1 route exceptions: **7**
- Firm 2 route exceptions: **7**
- Distinct exception signatures: **1**
- Common exception signature: **True**
- Firm 1 opposite-firm rows: **0**
- Firm 2 opposite-firm rows: **1**

## Firm 1 Exceptions

- `7x` `TypeError: Response.get_data() got an unexpected keyword argument 'errors'`

## Firm 2 Exceptions

- `7x` `TypeError: Response.get_data() got an unexpected keyword argument 'errors'`

## Firm 2 Opposite-Firm Rows

- Table `audit_log` | firm value `FIRM-001` | count **1**

## Authorization

- Runtime harness correction: **AUTHORIZED**
- Runtime profile build: **NOT AUTHORIZED**
- Production cutover: **NOT AUTHORIZED**
- Live database replacement: **NOT AUTHORIZED**
