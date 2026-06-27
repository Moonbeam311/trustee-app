# UPA-1B-5 — Active Runtime Defect Triage

Generated: 2026-06-13T18:16:38.978783
Source: `audit\UPA-1B-4_critical_evidence_20260613_181438.json`

## Summary

- Write Findings: **8**
- Active Runtime Write Tests Required: **5**
- Non Runtime Write Findings: **2**
- Migration Write Findings: **1**
- Collision Findings: **7**
- Collision Runtime Tests Required: **7**
- Null Firm Records: **6**
- Ownership Maps Ready: **6**
- Unscoped Tables: **4**
- Tables Requiring Schema Review: **4**

## Write Findings

### ISO-001 — ACTIVE_RUNTIME_WRITE_REQUIRES_TEST

- Source: `database/db.py:558`
- Function: `update_trust_fields`
- Function classification: `ORDINARY_RUNTIME_LOGIC`
- Runtime source: **True**
- Contains firm scope marker: **False**

```python
def update_trust_fields(trust_id, updates):
    conn = get_connection()
    cur = conn.cursor()
    fields = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [trust_id]
    cur.execute(f"UPDATE trusts SET {fields} WHERE trust_id = ?", values)
    conn.commit()
    conn.close()
```

### ISO-002 — ACTIVE_RUNTIME_WRITE_REQUIRES_TEST

- Source: `database/db.py:1253`
- Function: `update_distribution_record`
- Function classification: `ORDINARY_RUNTIME_LOGIC`
- Runtime source: **True**
- Contains firm scope marker: **False**

```python
def update_distribution_record(distribution_id, updates):
    conn = get_connection()
    cur = conn.cursor()
    fields = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [distribution_id]
    cur.execute(f"UPDATE distributions SET {fields} WHERE distribution_id = ?", values)
    conn.commit()
    conn.close()
```

### ISO-003 — ACTIVE_RUNTIME_WRITE_REQUIRES_TEST

- Source: `database/db.py:2866`
- Function: `update_app_user`
- Function classification: `ORDINARY_RUNTIME_LOGIC`
- Runtime source: **True**
- Contains firm scope marker: **False**

```python
def update_app_user(username, data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE app_users
        SET role_name = ?, status = ?
        WHERE username = ?
    """, (
        data["role_name"],
        data["status"],
        username,
    ))
    conn.commit()
    conn.close()
```

### ISO-004 — ACTIVE_RUNTIME_WRITE_REQUIRES_TEST

- Source: `database/db.py:2882`
- Function: `update_app_user_password`
- Function classification: `ORDINARY_RUNTIME_LOGIC`
- Runtime source: **True**
- Contains firm scope marker: **False**

```python
def update_app_user_password(username, password_hash):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE app_users
        SET password_hash = ?
        WHERE username = ?
    """, (
        password_hash,
        username,
    ))
    conn.commit()
    conn.close()
```

### ISO-005 — MIGRATION_REVIEW

- Source: `database/db.py:3306`
- Function: `backfill_trust_minute_certificate_ids`
- Function classification: `SCHEMA_OR_MIGRATION`
- Runtime source: **True**
- Contains firm scope marker: **False**

```python
def backfill_trust_minute_certificate_ids():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT minute_id
        FROM trust_minutes
        WHERE status IN ('Executed', 'Archived')
          AND (certificate_id IS NULL OR TRIM(certificate_id) = '')
        ORDER BY minute_id ASC
    """)

    rows = cur.fetchall()
    updated = []

    for row in rows:
        minute_id = row["minute_id"]
        certificate_id = f"CERT-{minute_id}"

        cur.execute("""
            UPDATE trust_minutes
            SET certificate_id = ?
            WHERE minute_id = ?
              AND (certificate_id IS NULL OR TRIM(certificate_id) = '')
        """, (certificate_id, minute_id))

        updated.append({
            "minute_id": minute_id,
            "certificate_id": certificate_id
        })

    conn.commit()
    conn.close()
    return updated
```

### ISO-006 — ACTIVE_RUNTIME_WRITE_REQUIRES_TEST

- Source: `database/db.py:3439`
- Function: `update_trust_minute_execution`
- Function classification: `ORDINARY_RUNTIME_LOGIC`
- Runtime source: **True**
- Contains firm scope marker: **False**

```python
def update_trust_minute_execution(minute_id, data):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE trust_minutes
        SET
            trustee_1_name = ?,
            trustee_1_capacity = ?,
            trustee_1_signed_date = ?,
            trustee_1_signature_image = ?,
            trustee_2_name = ?,
            trustee_2_capacity = ?,
            trustee_2_signed_date = ?,
            trustee_2_signature_image = ?,
            trustee_3_name = ?,
            trustee_3_capacity = ?,
            trustee_3_signed_date = ?,
            trustee_3_signature_image = ?,
            certificate_id = ?,
            approved_at = ?,
            executed_at = ?,
            archived_at = ?,
            status = ?,
            locked = ?
        WHERE minute_id = ?
    """, (
        data.get("trustee_1_name"),
        data.get("trustee_1_capacity"),
        data.get("trustee_1_signed_date"),
        data.get("trustee_1_signature_image"),
        data.get("trustee_2_name"),
        data.get("trustee_2_capacity"),
        data.get("trustee_2_signed_date"),
        data.get("trustee_2_signature_image"),
        data.get("trustee_3_name"),
        data.get("trustee_3_capacity"),
        data.get("trustee_3_signed_date"),
        data.get("trustee_3_signature_image"),
        data.get("certificate_id"),
        data.get("approved_at"),
        data.get("executed_at"),
        data.get("archived_at"),
        data.get("status"),
        int(data.get("locked", 0)),
        minute_id,
    ))

    conn.commit()
    conn.close()
```

### ISO-007 — NON_RUNTIME_COPY

- Source: `package_export/database/db.py:216`
- Function: `update_trust_fields`
- Function classification: `ORDINARY_RUNTIME_LOGIC`
- Runtime source: **False**
- Contains firm scope marker: **False**

```python
def update_trust_fields(trust_id, updates):
    conn = get_connection()
    cur = conn.cursor()
    fields = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [trust_id]
    cur.execute(f"UPDATE trusts SET {fields} WHERE trust_id = ?", values)
    conn.commit()
    conn.close()
```

### ISO-008 — NON_RUNTIME_COPY

- Source: `package_export/database/db.py:844`
- Function: `update_distribution_record`
- Function classification: `ORDINARY_RUNTIME_LOGIC`
- Runtime source: **False**
- Contains firm scope marker: **False**

```python
def update_distribution_record(distribution_id, updates):
    conn = get_connection()
    cur = conn.cursor()
    fields = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [distribution_id]
    cur.execute(f"UPDATE distributions SET {fields} WHERE distribution_id = ?", values)
    conn.commit()
    conn.close()
```

## Identifier Collision Findings

### ISO-009 — LOOKUP_REQUIRES_RUNTIME_TEST

- `audit_log.entity_id` = `TR-001`
- Active references: **5**
- Unsafe references: **2**
  - `database/db.py:1939` — `init_audit_table`
  - `database/db.py:3047` — `build_system_health_report`

### ISO-010 — LOOKUP_REQUIRES_RUNTIME_TEST

- `audit_log.entity_id` = `admin123`
- Active references: **5**
- Unsafe references: **2**
  - `database/db.py:1939` — `init_audit_table`
  - `database/db.py:3047` — `build_system_health_report`

### ISO-011 — LOOKUP_REQUIRES_RUNTIME_TEST

- `intake_document_recommendations.intake_id` = `INTAKE-0005`
- Active references: **11**
- Unsafe references: **8**
  - `app.py:18060` — `intake_document_recommendations`
  - `app.py:18085` — `intake_update_recommendation_status`
  - `app.py:18101` — `intake_workflow_launch_prep`
  - `app.py:18122` — `intake_workflow_bridge`
  - `app.py:18204` — `intake_workflow_bridge_summary`
  - `services/services_intake.py:4050` — `list_saved_document_recommendations`
  - `services/services_intake.py:4435` — `update_document_recommendation_status`
  - `services/services_intake.py:4467` — `get_document_recommendation`

### ISO-012 — LOOKUP_REQUIRES_RUNTIME_TEST

- `intake_export_logs.intake_id` = `INTAKE-0005`
- Active references: **8**
- Unsafe references: **3**
  - `services/services_intake.py:2976` — `list_intake_export_logs`
  - `services/services_intake.py:3101` — `get_next_export_version`
  - `services/services_intake.py:3215` — `list_intake_export_logs_versioned`

### ISO-013 — LOOKUP_REQUIRES_RUNTIME_TEST

- `intake_final_draft_gate_actions.intake_id` = `INTAKE-0005`
- Active references: **3**
- Unsafe references: **1**
  - `services/services_intake.py:7326` — `list_final_draft_resolution_actions`

### ISO-014 — LOOKUP_REQUIRES_RUNTIME_TEST

- `intake_review_gate_actions.intake_id` = `INTAKE-0005`
- Active references: **3**
- Unsafe references: **1**
  - `services/services_intake.py:6789` — `list_review_gate_actions`

### ISO-015 — LOOKUP_REQUIRES_RUNTIME_TEST

- `workspaces.owner_id` = `ADMIN_OWNER_001`
- Active references: **5**
- Unsafe references: **2**
  - `app.py:10528` — `discussion_new`
  - `app.py:10888` — `document_generate`

## Null-Firm Ownership Map

- `ISO-016` — `audit_log` — OWNERSHIP_MAP_READY_FOR_REVIEW — proposed firm: `FIRM-001`
- `ISO-017` — `audit_log` — OWNERSHIP_MAP_READY_FOR_REVIEW — proposed firm: `FIRM-001`
- `ISO-018` — `audit_log` — OWNERSHIP_MAP_READY_FOR_REVIEW — proposed firm: `FIRM-001`
- `ISO-019` — `documents` — OWNERSHIP_MAP_READY_FOR_REVIEW — proposed firm: `FIRM-002`
- `ISO-020` — `documents` — OWNERSHIP_MAP_READY_FOR_REVIEW — proposed firm: `FIRM-002`
- `ISO-021` — `documents` — OWNERSHIP_MAP_READY_FOR_REVIEW — proposed firm: `FIRM-002`

## Unscoped Table Classification

- `chart_of_accounts` — LIKELY_GLOBAL_ACCOUNT_CATALOG_OR_NEEDS_TRUST_PARENT — ACTIVE_SCHEMA_REVIEW_REQUIRED — rows: 0 — unscoped references: 3
- `discussion_threads` — LIKELY_TENANT_DATA — ACTIVE_SCHEMA_REVIEW_REQUIRED — rows: 5 — unscoped references: 6
- `genealogy_records` — LIKELY_TENANT_DATA — ACTIVE_SCHEMA_REVIEW_REQUIRED — rows: 0 — unscoped references: 5
- `user_permission_overrides` — LIKELY_FIRM_OR_USER_SCOPED — ACTIVE_SCHEMA_REVIEW_REQUIRED — rows: 1 — unscoped references: 6

## Control Rule

Only findings classified as ACTIVE_RUNTIME_WRITE_REQUIRES_TEST, LOOKUP_REQUIRES_RUNTIME_TEST, OWNERSHIP_MAP_READY_FOR_REVIEW, or ACTIVE_SCHEMA_REVIEW_REQUIRED should advance to the next phase.
