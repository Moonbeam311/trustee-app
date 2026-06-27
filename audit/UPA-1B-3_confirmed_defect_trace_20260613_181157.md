# UPA-1B-3 — Confirmed Isolation Defect Trace

Generated: 2026-06-13T18:12:01.386581
Source: `audit\UPA-1B-2_isolation_classification_20260613_160037.json`

## Summary

- Null Firm Records Traced: **6**
- High Review Tables Traced: **4**
- High Review Queries Traced: **137**
- High Review Routes Traced: **128**
- Duplicate Groups Traced: **7**
- Confirmed Defects: **15**
- Probable Defects: **96**

## Classification Counts

### Null Firm

- `PROBABLE_DEFECT_REPAIRABLE`: 6

### Tables

- `PROBABLE_UNSCOPED_TABLE_DEFECT`: 4

### Queries

- `CONFIRMED_HIGH_RISK_UNSCOPED_WRITE`: 8
- `PROBABLE_UNSCOPED_READ_DEFECT`: 47
- `PROTECTED_BY_CALLED_HELPER`: 36
- `PROTECTED_IN_FUNCTION`: 46

### Routes

- `PROBABLE_UNGATED_MUTATION_DEFECT`: 7
- `PROBABLE_UNGATED_READ_DEFECT`: 32
- `PROTECTED_BY_CALLED_HELPER`: 89

### Duplicates

- `CONFIRMED_IDENTIFIER_COLLISION_RISK`: 7

## Confirmed Defects

### DEFECT-001 — CONFIRMED_HIGH_RISK_UNSCOPED_WRITE

- Reason: Tenant-table write query has no detected direct, function, or helper scope.
- Source: `database/db.py:558`
- Function: `update_trust_fields`

```json
{
  "file": "database/db.py",
  "line": 558,
  "tables": [
    "trusts"
  ],
  "sql": "UPDATE trusts SET {fields} WHERE trust_id = ?",
  "action": "UPDATE",
  "table_risks": [
    "HIGH_REVIEW"
  ],
  "helper_context_detected": false,
  "function": "update_trust_fields",
  "scope_markers": [],
  "auth_markers": [],
  "helper_scope": [],
  "classification": "CONFIRMED_HIGH_RISK_UNSCOPED_WRITE",
  "reason": "Tenant-table write query has no detected direct, function, or helper scope.",
  "context": {
    "start_line": 553,
    "end_line": 560,
    "text": "def update_trust_fields(trust_id, updates):\n    conn = get_connection()\n    cur = conn.cursor()\n    fields = \", \".join([f\"{k} = ?\" for k in updates.keys()])\n    values = list(updates.values()) + [trust_id]\n    cur.execute(f\"UPDATE trusts SET {fields} WHERE trust_id = ?\", values)\n    conn.commit()\n    conn.close()"
  }
}
```

### DEFECT-002 — CONFIRMED_HIGH_RISK_UNSCOPED_WRITE

- Reason: Tenant-table write query has no detected direct, function, or helper scope.
- Source: `database/db.py:1253`
- Function: `update_distribution_record`

```json
{
  "file": "database/db.py",
  "line": 1253,
  "tables": [
    "distributions"
  ],
  "sql": "UPDATE distributions SET {fields} WHERE distribution_id = ?",
  "action": "UPDATE",
  "table_risks": [
    "HIGH_REVIEW"
  ],
  "helper_context_detected": false,
  "function": "update_distribution_record",
  "scope_markers": [],
  "auth_markers": [],
  "helper_scope": [],
  "classification": "CONFIRMED_HIGH_RISK_UNSCOPED_WRITE",
  "reason": "Tenant-table write query has no detected direct, function, or helper scope.",
  "context": {
    "start_line": 1248,
    "end_line": 1255,
    "text": "def update_distribution_record(distribution_id, updates):\n    conn = get_connection()\n    cur = conn.cursor()\n    fields = \", \".join([f\"{k} = ?\" for k in updates.keys()])\n    values = list(updates.values()) + [distribution_id]\n    cur.execute(f\"UPDATE distributions SET {fields} WHERE distribution_id = ?\", values)\n    conn.commit()\n    conn.close()"
  }
}
```

### DEFECT-003 — CONFIRMED_HIGH_RISK_UNSCOPED_WRITE

- Reason: Tenant-table write query has no detected direct, function, or helper scope.
- Source: `database/db.py:2866`
- Function: `update_app_user`

```json
{
  "file": "database/db.py",
  "line": 2866,
  "tables": [
    "app_users"
  ],
  "sql": "UPDATE app_users SET role_name = ?, status = ? WHERE username = ?",
  "action": "UPDATE",
  "table_risks": [
    "HIGH_REVIEW"
  ],
  "helper_context_detected": false,
  "function": "update_app_user",
  "scope_markers": [],
  "auth_markers": [],
  "helper_scope": [],
  "classification": "CONFIRMED_HIGH_RISK_UNSCOPED_WRITE",
  "reason": "Tenant-table write query has no detected direct, function, or helper scope.",
  "context": {
    "start_line": 2863,
    "end_line": 2876,
    "text": "def update_app_user(username, data):\n    conn = get_connection()\n    cur = conn.cursor()\n    cur.execute(\"\"\"\n        UPDATE app_users\n        SET role_name = ?, status = ?\n        WHERE username = ?\n    \"\"\", (\n        data[\"role_name\"],\n        data[\"status\"],\n        username,\n    ))\n    conn.commit()\n    conn.close()"
  }
}
```

### DEFECT-004 — CONFIRMED_HIGH_RISK_UNSCOPED_WRITE

- Reason: Tenant-table write query has no detected direct, function, or helper scope.
- Source: `database/db.py:2882`
- Function: `update_app_user_password`

```json
{
  "file": "database/db.py",
  "line": 2882,
  "tables": [
    "app_users"
  ],
  "sql": "UPDATE app_users SET password_hash = ? WHERE username = ?",
  "action": "UPDATE",
  "table_risks": [
    "HIGH_REVIEW"
  ],
  "helper_context_detected": false,
  "function": "update_app_user_password",
  "scope_markers": [],
  "auth_markers": [],
  "helper_scope": [],
  "classification": "CONFIRMED_HIGH_RISK_UNSCOPED_WRITE",
  "reason": "Tenant-table write query has no detected direct, function, or helper scope.",
  "context": {
    "start_line": 2879,
    "end_line": 2891,
    "text": "def update_app_user_password(username, password_hash):\n    conn = get_connection()\n    cur = conn.cursor()\n    cur.execute(\"\"\"\n        UPDATE app_users\n        SET password_hash = ?\n        WHERE username = ?\n    \"\"\", (\n        password_hash,\n        username,\n    ))\n    conn.commit()\n    conn.close()"
  }
}
```

### DEFECT-005 — CONFIRMED_HIGH_RISK_UNSCOPED_WRITE

- Reason: Tenant-table write query has no detected direct, function, or helper scope.
- Source: `database/db.py:3306`
- Function: `backfill_trust_minute_certificate_ids`

```json
{
  "file": "database/db.py",
  "line": 3306,
  "tables": [
    "trust_minutes"
  ],
  "sql": "UPDATE trust_minutes SET certificate_id = ? WHERE minute_id = ? AND (certificate_id IS NULL OR TRIM(certificate_id) = '')",
  "action": "UPDATE",
  "table_risks": [
    "HIGH_REVIEW"
  ],
  "helper_context_detected": false,
  "function": "backfill_trust_minute_certificate_ids",
  "scope_markers": [],
  "auth_markers": [],
  "helper_scope": [],
  "classification": "CONFIRMED_HIGH_RISK_UNSCOPED_WRITE",
  "reason": "Tenant-table write query has no detected direct, function, or helper scope.",
  "context": {
    "start_line": 3287,
    "end_line": 3320,
    "text": "def backfill_trust_minute_certificate_ids():\n    conn = get_connection()\n    cur = conn.cursor()\n\n    cur.execute(\"\"\"\n        SELECT minute_id\n        FROM trust_minutes\n        WHERE status IN ('Executed', 'Archived')\n          AND (certificate_id IS NULL OR TRIM(certificate_id) = '')\n        ORDER BY minute_id ASC\n    \"\"\")\n\n    rows = cur.fetchall()\n    updated = []\n\n    for row in rows:\n        minute_id = row[\"minute_id\"]\n        certificate_id = f\"CERT-{minute_id}\"\n\n        cur.execute(\"\"\"\n            UPDATE trust_minutes\n            SET certificate_id = ?\n            WHERE minute_id = ?\n              AND (certificate_id IS NULL OR TRIM(certificate_id) = '')\n        \"\"\", (certificate_id, minute_id))\n\n        updated.append({\n            \"minute_id\": minute_id,\n            \"certificate_id\": certificate_id\n        })\n\n    conn.commit()\n    conn.close()\n    return updated"
  }
}
```

### DEFECT-006 — CONFIRMED_HIGH_RISK_UNSCOPED_WRITE

- Reason: Tenant-table write query has no detected direct, function, or helper scope.
- Source: `database/db.py:3439`
- Function: `update_trust_minute_execution`

```json
{
  "file": "database/db.py",
  "line": 3439,
  "tables": [
    "trust_minutes"
  ],
  "sql": "UPDATE trust_minutes SET trustee_1_name = ?, trustee_1_capacity = ?, trustee_1_signed_date = ?, trustee_1_signature_image = ?, trustee_2_name = ?, trustee_2_capacity = ?, trustee_2_signed_date = ?, trustee_2_signature_image = ?, trustee_3_name = ?, trustee_3_capacity = ?, trustee_3_signed_date = ?, trustee_3_signature_image = ?, certificate_id = ?, approved_at = ?, executed_at = ?, archived_at = ?, status = ?, locked = ? WHERE minute_id = ?",
  "action": "UPDATE",
  "table_risks": [
    "HIGH_REVIEW"
  ],
  "helper_context_detected": false,
  "function": "update_trust_minute_execution",
  "scope_markers": [],
  "auth_markers": [],
  "helper_scope": [],
  "classification": "CONFIRMED_HIGH_RISK_UNSCOPED_WRITE",
  "reason": "Tenant-table write query has no detected direct, function, or helper scope.",
  "context": {
    "start_line": 3435,
    "end_line": 3484,
    "text": "def update_trust_minute_execution(minute_id, data):\n    conn = get_connection()\n    cur = conn.cursor()\n\n    cur.execute(\"\"\"\n        UPDATE trust_minutes\n        SET\n            trustee_1_name = ?,\n            trustee_1_capacity = ?,\n            trustee_1_signed_date = ?,\n            trustee_1_signature_image = ?,\n            trustee_2_name = ?,\n            trustee_2_capacity = ?,\n            trustee_2_signed_date = ?,\n            trustee_2_signature_image = ?,\n            trustee_3_name = ?,\n            trustee_3_capacity = ?,\n            trustee_3_signed_date = ?,\n            trustee_3_signature_image = ?,\n            certificate_id = ?,\n            approved_at = ?,\n            executed_at = ?,\n            archived_at = ?,\n            status = ?,\n            locked = ?\n        WHERE minute_id = ?\n    \"\"\", (\n        data.get(\"trustee_1_name\"),\n        data.get(\"trustee_1_capacity\"),\n        data.get(\"trustee_1_signed_date\"),\n        data.get(\"trustee_1_signature_image\"),\n        data.get(\"trustee_2_name\"),\n        data.get(\"trustee_2_capacity\"),\n        data.get(\"trustee_2_signed_date\"),\n        data.get(\"trustee_2_signature_image\"),\n        data.get(\"trustee_3_name\"),\n        data.get(\"trustee_3_capacity\"),\n        data.get(\"trustee_3_signed_date\"),\n        data.get(\"trustee_3_signature_image\"),\n        data.get(\"certificate_id\"),\n        data.get(\"approved_at\"),\n        data.get(\"executed_at\"),\n        data.get(\"archived_at\"),\n        data.get(\"status\"),\n        int(data.get(\"locked\", 0)),\n        minute_id,\n    ))\n\n    conn.commit()\n    conn.close()"
  }
}
```

### DEFECT-007 — CONFIRMED_HIGH_RISK_UNSCOPED_WRITE

- Reason: Tenant-table write query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:216`
- Function: `update_trust_fields`

```json
{
  "file": "package_export/database/db.py",
  "line": 216,
  "tables": [
    "trusts"
  ],
  "sql": "UPDATE trusts SET {fields} WHERE trust_id = ?",
  "action": "UPDATE",
  "table_risks": [
    "HIGH_REVIEW"
  ],
  "helper_context_detected": false,
  "function": "update_trust_fields",
  "scope_markers": [],
  "auth_markers": [],
  "helper_scope": [],
  "classification": "CONFIRMED_HIGH_RISK_UNSCOPED_WRITE",
  "reason": "Tenant-table write query has no detected direct, function, or helper scope.",
  "context": {
    "start_line": 211,
    "end_line": 218,
    "text": "def update_trust_fields(trust_id, updates):\n    conn = get_connection()\n    cur = conn.cursor()\n    fields = \", \".join([f\"{k} = ?\" for k in updates.keys()])\n    values = list(updates.values()) + [trust_id]\n    cur.execute(f\"UPDATE trusts SET {fields} WHERE trust_id = ?\", values)\n    conn.commit()\n    conn.close()"
  }
}
```

### DEFECT-008 — CONFIRMED_HIGH_RISK_UNSCOPED_WRITE

- Reason: Tenant-table write query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:844`
- Function: `update_distribution_record`

```json
{
  "file": "package_export/database/db.py",
  "line": 844,
  "tables": [
    "distributions"
  ],
  "sql": "UPDATE distributions SET {fields} WHERE distribution_id = ?",
  "action": "UPDATE",
  "table_risks": [
    "HIGH_REVIEW"
  ],
  "helper_context_detected": false,
  "function": "update_distribution_record",
  "scope_markers": [],
  "auth_markers": [],
  "helper_scope": [],
  "classification": "CONFIRMED_HIGH_RISK_UNSCOPED_WRITE",
  "reason": "Tenant-table write query has no detected direct, function, or helper scope.",
  "context": {
    "start_line": 839,
    "end_line": 846,
    "text": "def update_distribution_record(distribution_id, updates):\n    conn = get_connection()\n    cur = conn.cursor()\n    fields = \", \".join([f\"{k} = ?\" for k in updates.keys()])\n    values = list(updates.values()) + [distribution_id]\n    cur.execute(f\"UPDATE distributions SET {fields} WHERE distribution_id = ?\", values)\n    conn.commit()\n    conn.close()"
  }
}
```

### DEFECT-009 — CONFIRMED_IDENTIFIER_COLLISION_RISK

- Reason: Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter.
- Table: `audit_log`

```json
{
  "table": "audit_log",
  "identifier_column": "entity_id",
  "identifier": "TR-001",
  "firms": "FIRM-001,FIRM-002",
  "firm_count": 2,
  "row_count": 16,
  "records": [
    {
      "id": 94,
      "entity_type": "1041_export",
      "entity_id": "TR-001",
      "action": "export",
      "note": "1041 TXT export generated for tax year 2026",
      "created_at": "2026-04-29 02:07:16",
      "previous_hash": "719a4584df2761996c00e90b671f6a87f12628378dbf38caf3551c6ab9ba09ed",
      "entry_hash": "9ed936efc8b7d69d820538478c25f0475d1ca2a4491f15a1d47359257b0a0c8e",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-001"
    },
    {
      "id": 96,
      "entity_type": "1041_export",
      "entity_id": "TR-001",
      "action": "export",
      "note": "1041 TXT export generated for tax year 2026",
      "created_at": "2026-04-29 02:16:00",
      "previous_hash": "9c02046cfe097c3ea3d56ebab9cb12fb7f8fd6e96e69d2d0d4e3623de3ba5c75",
      "entry_hash": "67e3d01b59d33740a9e45da92e1caef167488559dbc07a1f15d36a9a04e7ea27",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-001"
    },
    {
      "id": 99,
      "entity_type": "k1_export",
      "entity_id": "TR-001",
      "action": "export",
      "note": "K-1 CSV export generated for tax year 2026",
      "created_at": "2026-04-29 02:35:52",
      "previous_hash": "9d10358c96d10282f25ef70bf753fd9ba17d7b4f432ca9c8f8f8326254c39690",
      "entry_hash": "c28f714f55767db7c6491c547405e7cf659302d2ec49c1b910d2811187623aba",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-001"
    },
    {
      "id": 213,
      "entity_type": "trust_branding",
      "entity_id": "TR-001",
      "action": "branding_settings_updated",
      "note": "Trust branding settings updated",
      "created_at": "2026-05-02 02:11:04",
      "previous_hash": "0dd723df729f3c712bc0a3b1075637d9800f40e439a5d6741e5b050b3d416ace",
      "entry_hash": "aacafb7962699aec5242f13f720228dccc245c885942fb4dec98aa58660d349f",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-001"
    },
    {
      "id": 214,
      "entity_type": "trust_branding",
      "entity_id": "TR-001",
      "action": "trust_branding_seal_uploaded",
      "note": "Seal uploaded: seal_20260501222305_river_delta_map.png",
      "created_at": "2026-05-02 02:23:05",
      "previous_hash": "aacafb7962699aec5242f13f720228dccc245c885942fb4dec98aa58660d349f",
      "entry_hash": "65ea6a688bcb6b26b994ebed7d69957d2a70e0c7aac5c6d4df73f14d883b9ba5",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-001"
    },
    {
      "id": 215,
      "entity_type": "trust_branding",
      "entity_id": "TR-001",
      "action": "branding_settings_updated",
      "note": "Trust branding settings updated",
      "created_at": "2026-05-02 02:23:05",
      "previous_hash": "65ea6a688bcb6b26b994ebed7d69957d2a70e0c7aac5c6d4df73f14d883b9ba5",
      "entry_hash": "aae52cd4ce475218c1be6e0f841eea54ffdc73b8c036d3e3d957c47bc0c44e4a",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-001"
    },
    {
      "id": 216,
      "entity_type": "trust_branding",
      "entity_id": "TR-001",
      "action": "trust_branding_seal_uploaded",
      "note": "Seal uploaded: seal_20260501223056_river_delta_map.png",
      "created_at": "2026-05-02 02:30:56",
      "previous_hash": "aae52cd4ce475218c1be6e0f841eea54ffdc73b8c036d3e3d957c47bc0c44e4a",
      "entry_hash": "3008832d7284d79736e1303e06e3a26051141ff5ed1abab79b9fd87a9664dfbd",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-001"
    },
    {
      "id": 217,
      "entity_type": "trust_branding",
      "entity_id": "TR-001",
      "action": "branding_settings_updated",
      "note": "Trust branding settings updated",
      "created_at": "2026-05-02 02:30:56",
      "previous_hash": "3008832d7284d79736e1303e06e3a26051141ff5ed1abab79b9fd87a9664dfbd",
      "entry_hash": "9e7f52d17f0801b5c15bfa6d101663292e35d6cc7753038e33e2f05149656d7f",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-001"
    },
    {
      "id": 218,
      "entity_type": "trust_branding",
      "entity_id": "TR-001",
      "action": "branding_settings_updated",
      "note": "Trust branding settings updated",
      "created_at": "2026-05-02 02:40:14",
      "previous_hash": "9e7f52d17f0801b5c15bfa6d101663292e35d6cc7753038e33e2f05149656d7f",
      "entry_hash": "868ae670dc289d3786cdf80c0bc63ac3398c8a9ceea53df136824444437fdd90",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-001"
    },
    {
      "id": 222,
      "entity_type": "trust_branding",
      "entity_id": "TR-001",
      "action": "branding_settings_updated",
      "note": "Trust branding settings updated",
      "created_at": "2026-05-02 15:08:37",
      "previous_hash": "37f2ee2f8b4ff05cd5dcad4f2f98beb313e45de24f40b37871a0f57a3b2fee43",
      "entry_hash": "4d75912fd80a9dc6641b3fcc1c6c7dfc14767b29c086e74e4d47d6b43b17447d",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-001"
    },
    {
      "id": 223,
      "entity_type": "trust_branding",
      "entity_id": "TR-001",
      "action": "branding_settings_updated",
      "note": "Trust branding settings updated",
      "created_at": "2026-05-02 15:08:42",
      "previous_hash": "4d75912fd80a9dc6641b3fcc1c6c7dfc14767b29c086e74e4d47d6b43b17447d",
      "entry_hash": "c5ed8411a0c439ffb51f7bd4ab41a331615aacbd7073cb31ac83edfa6aba0d2d",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-001"
    },
    {
      "id": 224,
      "entity_type": "trust_branding",
      "entity_id": "TR-001",
      "action": "branding_settings_updated",
      "note": "Trust branding settings updated",
      "created_at": "2026-05-02 15:08:49",
      "previous_hash": "c5ed8411a0c439ffb51f7bd4ab41a331615aacbd7073cb31ac83edfa6aba0d2d",
      "entry_hash": "83c826eb89e73c07d3834cecb92f15d957156d26cb848698eab84399002f7532",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-001"
    },
    {
      "id": 225,
      "entity_type": "trust_branding",
      "entity_id": "TR-001",
      "action": "branding_settings_updated",
      "note": "Trust branding settings updated",
      "created_at": "2026-05-02 15:08:56",
      "previous_hash": "83c826eb89e73c07d3834cecb92f15d957156d26cb848698eab84399002f7532",
      "entry_hash": "17742a9940199fb617540231c6ddbf4f98e13708350b894549af93b178e101d8",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-001"
    },
    {
      "id": 302,
      "entity_type": "security",
      "entity_id": "TR-001",
      "action": "trust_export_scope_denied",
      "note": "Attempted access to controlled packet export outside active firm scope. User=admin123; Firm=FIRM-002",
      "created_at": "2026-05-12 10:50:41",
      "previous_hash": "81f461763e5f75e99be1b5dcac2f4b4657baa385b7b54e2e0b3d8eee28a5c405",
      "entry_hash": "8967c6bb03e43407f8ddab336badcaa188db55b6b113c500227105a4d1b53b77",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 304,
      "entity_type": "security",
      "entity_id": "TR-001",
      "action": "trust_export_scope_denied",
      "note": "Attempted access to controlled packet export outside active firm scope. User=admin123; Firm=FIRM-002",
      "created_at": "2026-05-12 11:17:49",
      "previous_hash": "390be6cdd62793c0151c3779a106e5f1e8588e264a479dc2ca4dae13704319e9",
      "entry_hash": "a52b571dfa80d9237c86957e7f527c590ee057cbe0f0782789bd629082378be2",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 306,
      "entity_type": "security",
      "entity_id": "TR-001",
      "action": "trust_export_scope_denied",
      "note": "Attempted access to controlled packet export outside active firm scope. User=admin123; Firm=FIRM-002",
      "created_at": "2026-05-12 12:10:43",
      "previous_hash": "6fa59b5ed63ed89c601db35bef55f9a8ce52a6c1b87194cd14845f8fcb02c3a8",
      "entry_hash": "3982ca000fb373695d00c9f9d409318ca1d4b819251ae5eb4499f4505528017f",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    }
  ],
  "audit_classification": "LIKELY_VALID_TENANT_LOCAL_REUSE",
  "identical_payload_except_scope": false,
  "audit_reason": "Same business identifier appears in multiple firms. This is valid only if every lookup also includes firm_id.",
  "references": [
    {
      "file": "app.py",
      "function": "trust_minute_execution_packet_pdf",
      "line": 7550,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "trust_minute_detail",
      "line": 7819,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "verify_certificate",
      "line": 7857,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "audit_dashboard",
      "line": 7995,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "audit_log_report_pdf",
      "line": 10146,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "admin_audit_log",
      "line": 14193,
      "scope_markers": []
    },
    {
      "file": "pdf_utils.py",
      "function": "audit_log_report_story",
      "line": 529,
      "scope_markers": []
    },
    {
      "file": "database/db.py",
      "function": "init_audit_table",
      "line": 1939,
      "scope_markers": []
    },
    {
      "file": "database/db.py",
      "function": "log_change",
      "line": 1973,
      "scope_markers": [
        "firm_id"
      ]
    },
    {
      "file": "database/db.py",
      "function": "get_audit_log_by_entity",
      "line": 2044,
      "scope_markers": [
        "current_firm",
        "firm_id",
        "get_current_firm_id"
      ]
    },
    {
      "file": "database/db.py",
      "function": "verify_audit_log_chain",
      "line": 2076,
      "scope_markers": [
        "firm_id"
      ]
    },
    {
      "file": "database/db.py",
      "function": "build_system_health_report",
      "line": 3047,
      "scope_markers": []
    }
  ],
  "unsafe_references": [
    {
      "file": "app.py",
      "function": "trust_minute_execution_packet_pdf",
      "line": 7550,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "trust_minute_detail",
      "line": 7819,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "verify_certificate",
      "line": 7857,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "audit_dashboard",
      "line": 7995,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "audit_log_report_pdf",
      "line": 10146,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "admin_audit_log",
      "line": 14193,
      "scope_markers": []
    },
    {
      "file": "pdf_utils.py",
      "function": "audit_log_report_story",
      "line": 529,
      "scope_markers": []
    },
    {
      "file": "database/db.py",
      "function": "init_audit_table",
      "line": 1939,
      "scope_markers": []
    },
    {
      "file": "database/db.py",
      "function": "build_system_health_report",
      "line": 3047,
      "scope_markers": []
    }
  ],
  "classification": "CONFIRMED_IDENTIFIER_COLLISION_RISK",
  "reason": "Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter."
}
```

### DEFECT-010 — CONFIRMED_IDENTIFIER_COLLISION_RISK

- Reason: Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter.
- Table: `audit_log`

```json
{
  "table": "audit_log",
  "identifier_column": "entity_id",
  "identifier": "admin123",
  "firms": "FIRM-001,FIRM-002",
  "firm_count": 2,
  "row_count": 75,
  "records": [
    {
      "id": 288,
      "entity_type": "app_user",
      "entity_id": "admin123",
      "action": "create",
      "note": "Master admin created user 'admin123' with role 'Admin' and status 'active'",
      "created_at": "2026-05-11 13:32:03",
      "previous_hash": "ac1b595717abcf0ff744cfbdee034fa179151835d8d98c6b4a5fc30ac0c6e833",
      "entry_hash": "396645e35cea78b15cca2b9fd11d39d8bde83fef375da5ea7a18d1ef9bd8b824",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-001"
    },
    {
      "id": 289,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-11 13:33:28",
      "previous_hash": "396645e35cea78b15cca2b9fd11d39d8bde83fef375da5ea7a18d1ef9bd8b824",
      "entry_hash": "3f2d8c211a4cb4b17459a4529d53a8db71008d2b590b49837eabf579e701afb7",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-001"
    },
    {
      "id": 290,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-11 15:40:23",
      "previous_hash": "3f2d8c211a4cb4b17459a4529d53a8db71008d2b590b49837eabf579e701afb7",
      "entry_hash": "8dbc6a30f24c330ff5f89e3558393017b11b1cdd1e92d51b7444e87b11eafcce",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 291,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-11 16:10:16",
      "previous_hash": "8dbc6a30f24c330ff5f89e3558393017b11b1cdd1e92d51b7444e87b11eafcce",
      "entry_hash": "ee3916f16948fcebbcdb1066dcd2e7cac23ecc957a7db81228ca740dc2a8ed44",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 293,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-11 16:50:34",
      "previous_hash": "cd9a452fd89024eb770cbfbd6f3f95948677943077c0825b1956928c8b84c44b",
      "entry_hash": "5d0b6f6a12f1c8aea232c3fba831acf8aa16a8c9fae8ab67c51d31f1ddfc9dce",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 294,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-11 17:16:19",
      "previous_hash": "5d0b6f6a12f1c8aea232c3fba831acf8aa16a8c9fae8ab67c51d31f1ddfc9dce",
      "entry_hash": "1e4c817d0092f43878285abd3a8fa8877fb30e83a371021a9dabe72ee7812433",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 296,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-12 02:49:33",
      "previous_hash": "2e75c2b4e7ffdccccc2b020d6898b86ca114e716ab41301206889b6f568b78ec",
      "entry_hash": "d9342ef77f4f2b75f864f20cbab659c4e5e69bc9bc1b3934ae8c3f69aefbb095",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 297,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-12 02:52:44",
      "previous_hash": "d9342ef77f4f2b75f864f20cbab659c4e5e69bc9bc1b3934ae8c3f69aefbb095",
      "entry_hash": "634c888b9a4d49e608fdddc0b76644f805349a2cbcaf96546034d09fa3400612",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 298,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-12 03:12:16",
      "previous_hash": "634c888b9a4d49e608fdddc0b76644f805349a2cbcaf96546034d09fa3400612",
      "entry_hash": "e6121fe3826bda526a4aced640bae7f47246fc1e86df958193e17560619d3cb8",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 299,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-12 03:43:08",
      "previous_hash": "e6121fe3826bda526a4aced640bae7f47246fc1e86df958193e17560619d3cb8",
      "entry_hash": "241f9bb7b775ff25524be1fab7fb6a81e7e5b32fa3319b5e86ec5a1ce704aa6a",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 300,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-12 03:58:07",
      "previous_hash": "241f9bb7b775ff25524be1fab7fb6a81e7e5b32fa3319b5e86ec5a1ce704aa6a",
      "entry_hash": "bd2b382c69930f6bede09c0ee22d3f700bf0fcbce2fcc63d1b75fa419976b4d7",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 301,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-12 10:49:38",
      "previous_hash": "bd2b382c69930f6bede09c0ee22d3f700bf0fcbce2fcc63d1b75fa419976b4d7",
      "entry_hash": "81f461763e5f75e99be1b5dcac2f4b4657baa385b7b54e2e0b3d8eee28a5c405",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 303,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-12 11:13:15",
      "previous_hash": "8967c6bb03e43407f8ddab336badcaa188db55b6b113c500227105a4d1b53b77",
      "entry_hash": "390be6cdd62793c0151c3779a106e5f1e8588e264a479dc2ca4dae13704319e9",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 305,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-12 11:57:23",
      "previous_hash": "a52b571dfa80d9237c86957e7f527c590ee057cbe0f0782789bd629082378be2",
      "entry_hash": "6fa59b5ed63ed89c601db35bef55f9a8ce52a6c1b87194cd14845f8fcb02c3a8",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 307,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-19 15:23:24",
      "previous_hash": "3982ca000fb373695d00c9f9d409318ca1d4b819251ae5eb4499f4505528017f",
      "entry_hash": "fad703087ae9f0f2640cf313c92e17c33b094cf1129b055d3a4fa10d2bcc77a0",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 308,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-19 15:23:52",
      "previous_hash": "fad703087ae9f0f2640cf313c92e17c33b094cf1129b055d3a4fa10d2bcc77a0",
      "entry_hash": "fd999b738f03f63545d40ab31eaff5bbb2a01922fa8865c453135ed6e2350793",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 309,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-19 15:41:46",
      "previous_hash": "fd999b738f03f63545d40ab31eaff5bbb2a01922fa8865c453135ed6e2350793",
      "entry_hash": "fc34698f316eab58e6690c36b3e6eca28695a416b5f15e67e53b204e2268630f",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 310,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-19 17:12:51",
      "previous_hash": "fc34698f316eab58e6690c36b3e6eca28695a416b5f15e67e53b204e2268630f",
      "entry_hash": "b9eace1dbbeba09cff301c540022dfc49a9b042fbe6c4c19fee020192ff5f9dd",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 311,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-19 19:43:25",
      "previous_hash": "b9eace1dbbeba09cff301c540022dfc49a9b042fbe6c4c19fee020192ff5f9dd",
      "entry_hash": "b9fe39bd344c64c08b1fc4c221a85b86aea4a6d2528190c4e9d2bc160487c58d",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 312,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-20 00:30:46",
      "previous_hash": "b9fe39bd344c64c08b1fc4c221a85b86aea4a6d2528190c4e9d2bc160487c58d",
      "entry_hash": "6658cc8bd07aa848b88ef1704a94c572cd3e7b17fd19081f9e0c847334dc2c55",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 314,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-20 01:08:51",
      "previous_hash": "dd26cac34d60fce2e6af9a3cf64d2090dc4489e507bdde53d052361bd39d2b85",
      "entry_hash": "80dd41d01bdc9a1b906047b869e85bfadf31466b2dd8df19b4efab58dfeb7b60",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 315,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-20 02:55:00",
      "previous_hash": "80dd41d01bdc9a1b906047b869e85bfadf31466b2dd8df19b4efab58dfeb7b60",
      "entry_hash": "20dda5a757abc8a5642b4c0c8bce7082d8f49eea14b6c9356ead18b52f685b41",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 316,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-20 14:26:25",
      "previous_hash": "20dda5a757abc8a5642b4c0c8bce7082d8f49eea14b6c9356ead18b52f685b41",
      "entry_hash": "10b7d57df83b1b74e0869331c2877c32f65dcb837d0e0ac153fe60f0aedcfc81",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 317,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-20 15:08:30",
      "previous_hash": "10b7d57df83b1b74e0869331c2877c32f65dcb837d0e0ac153fe60f0aedcfc81",
      "entry_hash": "3feec0b7d50d5c58b41eca7ba6a35d55f4228874ea7f00edec1ea074a7f102b0",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 318,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-20 16:18:50",
      "previous_hash": "3feec0b7d50d5c58b41eca7ba6a35d55f4228874ea7f00edec1ea074a7f102b0",
      "entry_hash": "050983f5a5e0bb07ceddaf96c3c8bba041afc408d34ab759c5d7db4c805732db",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 319,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-20 18:40:43",
      "previous_hash": "050983f5a5e0bb07ceddaf96c3c8bba041afc408d34ab759c5d7db4c805732db",
      "entry_hash": "61f5cef5abf8a67bcf4959175806bb5e9be66c2e356342d41d81488accbe30bf",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 320,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-20 19:50:43",
      "previous_hash": "61f5cef5abf8a67bcf4959175806bb5e9be66c2e356342d41d81488accbe30bf",
      "entry_hash": "9429cfe5b7a67c2a7aaf7b48f64f7d881a9f982498835207c4d4ec7095057892",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 321,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-20 20:44:54",
      "previous_hash": "9429cfe5b7a67c2a7aaf7b48f64f7d881a9f982498835207c4d4ec7095057892",
      "entry_hash": "10dae456502f095bfb6f6f678024ea94e8f5a3d0de5dff7fb8d516a97b90d7a5",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 322,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-20 22:42:29",
      "previous_hash": "10dae456502f095bfb6f6f678024ea94e8f5a3d0de5dff7fb8d516a97b90d7a5",
      "entry_hash": "aafbfb3137f1b0879fa0bcf4a424bcf8cff6b98149bed75c0a2e3ac9af21f2ba",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 323,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-20 23:47:15",
      "previous_hash": "aafbfb3137f1b0879fa0bcf4a424bcf8cff6b98149bed75c0a2e3ac9af21f2ba",
      "entry_hash": "fa553a2fc2397dd78346bd32854627dca86722e5fdfec3e92e3cc9392493e65e",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 324,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-21 00:35:47",
      "previous_hash": "fa553a2fc2397dd78346bd32854627dca86722e5fdfec3e92e3cc9392493e65e",
      "entry_hash": "7e048a38fa1ad514dc135c54b23303659f1d9a58c53ee1e8c594434c5782b5cf",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 325,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-21 01:06:37",
      "previous_hash": "7e048a38fa1ad514dc135c54b23303659f1d9a58c53ee1e8c594434c5782b5cf",
      "entry_hash": "c06fa2173b1cf61f16ec3cc1efc602f4d17964bf287cde1f381904afdc843897",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 326,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-21 01:48:33",
      "previous_hash": "c06fa2173b1cf61f16ec3cc1efc602f4d17964bf287cde1f381904afdc843897",
      "entry_hash": "5bc483e22e292f1fce008e6f226eaedb3a73cc956a752888b256c81a43caea05",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 327,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-21 12:04:08",
      "previous_hash": "5bc483e22e292f1fce008e6f226eaedb3a73cc956a752888b256c81a43caea05",
      "entry_hash": "48f67c4da815faec6dcd529b94161d7ae5233b5358b892c421179bcbce39c6ec",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 328,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-21 13:38:34",
      "previous_hash": "48f67c4da815faec6dcd529b94161d7ae5233b5358b892c421179bcbce39c6ec",
      "entry_hash": "22ecf42c5e77414a243cdb3e40e2c8bdd66a178dd36005711abf9d644f9effe6",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 329,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-21 17:40:15",
      "previous_hash": "22ecf42c5e77414a243cdb3e40e2c8bdd66a178dd36005711abf9d644f9effe6",
      "entry_hash": "2e732300eaa567447639613194605838ecb590e895974e9c73154631ffb9aece",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 330,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-21 21:28:40",
      "previous_hash": "2e732300eaa567447639613194605838ecb590e895974e9c73154631ffb9aece",
      "entry_hash": "9079fcb57e75f6f2ad4e71d8fbc57cabb85d9b356a213cff5d81bedb07a9b973",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 331,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-21 22:15:43",
      "previous_hash": "9079fcb57e75f6f2ad4e71d8fbc57cabb85d9b356a213cff5d81bedb07a9b973",
      "entry_hash": "5d62b5d24182c45af4d960290e0fe0a2dfa65382b18ade9af99f1726de66728b",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 332,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-21 22:54:48",
      "previous_hash": "5d62b5d24182c45af4d960290e0fe0a2dfa65382b18ade9af99f1726de66728b",
      "entry_hash": "e7a8a476c2a88e61e953b819e2af16203143a84b630f92891ad0ac4fa66c20d8",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 333,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-22 12:37:07",
      "previous_hash": "e7a8a476c2a88e61e953b819e2af16203143a84b630f92891ad0ac4fa66c20d8",
      "entry_hash": "e4875436327f8dfeda08240ee958b06c49dc76b3417d14d86fcec512e54fe963",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 334,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-22 12:57:11",
      "previous_hash": "e4875436327f8dfeda08240ee958b06c49dc76b3417d14d86fcec512e54fe963",
      "entry_hash": "9815246e120d5a58e3176f751b35355ac9bc10e79b863a7cf2adc4afc9281cba",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 335,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-22 14:00:04",
      "previous_hash": "9815246e120d5a58e3176f751b35355ac9bc10e79b863a7cf2adc4afc9281cba",
      "entry_hash": "92ab25b1dd3f293d8a1a09456c2e18c488a3a55fc3e5b33fe6a2f012bcea005b",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 336,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-22 19:29:37",
      "previous_hash": "92ab25b1dd3f293d8a1a09456c2e18c488a3a55fc3e5b33fe6a2f012bcea005b",
      "entry_hash": "fbc2b487742738ac1f0f4dcaff9470d85d6747c05e22c5a4b22380459757279f",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 337,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-22 19:48:04",
      "previous_hash": "fbc2b487742738ac1f0f4dcaff9470d85d6747c05e22c5a4b22380459757279f",
      "entry_hash": "a9488487b7c3dafc665661be9b4066860725abcf540c5aa8a21929efd38b8204",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 338,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-22 20:08:27",
      "previous_hash": "a9488487b7c3dafc665661be9b4066860725abcf540c5aa8a21929efd38b8204",
      "entry_hash": "cfd675cc0512cf815f83497fc75dadbd5aa53764c684c8815138fd14af29c52d",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 339,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-22 21:43:24",
      "previous_hash": "cfd675cc0512cf815f83497fc75dadbd5aa53764c684c8815138fd14af29c52d",
      "entry_hash": "c14529a9a6548a71b94d3ed2f63ee95f554a62c97e3fde7110805cd7867594bf",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 340,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-22 22:56:55",
      "previous_hash": "c14529a9a6548a71b94d3ed2f63ee95f554a62c97e3fde7110805cd7867594bf",
      "entry_hash": "f36d3ed5900ac09f0d00403ccc4b6079e17d48ffcb41e42ef5536e05ffe8dc8f",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 341,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-23 00:50:05",
      "previous_hash": "f36d3ed5900ac09f0d00403ccc4b6079e17d48ffcb41e42ef5536e05ffe8dc8f",
      "entry_hash": "42374304f3c5fcb490a9c1c7e12a51b220ae660e9e7d22ca0dc28044cde4f612",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 342,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-23 01:28:12",
      "previous_hash": "42374304f3c5fcb490a9c1c7e12a51b220ae660e9e7d22ca0dc28044cde4f612",
      "entry_hash": "c6fcb345278270bbd236fd115a3f3ea3831609577a776ce266a741be8823bcf3",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 343,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-23 11:20:06",
      "previous_hash": "c6fcb345278270bbd236fd115a3f3ea3831609577a776ce266a741be8823bcf3",
      "entry_hash": "39a0e3bb4852735ba1ff275b7db453312ca6888a4d59a62bc05e1d4d461f5768",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 344,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-23 12:21:54",
      "previous_hash": "39a0e3bb4852735ba1ff275b7db453312ca6888a4d59a62bc05e1d4d461f5768",
      "entry_hash": "e4a897c93a1eeedbf72f9f1f73f381e636bc032893f8b780f4fe21f12a17fbdc",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 345,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-23 13:11:42",
      "previous_hash": "e4a897c93a1eeedbf72f9f1f73f381e636bc032893f8b780f4fe21f12a17fbdc",
      "entry_hash": "bf37ab021ba880b587eb062b75ef3ccffed506c880358717c86af9400c5fc851",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 346,
      "entity_type": "security",
      "entity_id": "admin123",
      "action": "export_blocked",
      "note": "Endpoint=controlled_docx_export; Policy=allow_exports_false",
      "created_at": "2026-05-23 13:11:49",
      "previous_hash": "bf37ab021ba880b587eb062b75ef3ccffed506c880358717c86af9400c5fc851",
      "entry_hash": "a8d3d8bf1321cf3fd5ed8db5f3a51c652e8d02008b9f9cab234f1596f9dca9c4",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 347,
      "entity_type": "security",
      "entity_id": "admin123",
      "action": "export_blocked",
      "note": "Endpoint=controlled_pdf_conversion; Policy=allow_exports_false",
      "created_at": "2026-05-23 13:12:01",
      "previous_hash": "a8d3d8bf1321cf3fd5ed8db5f3a51c652e8d02008b9f9cab234f1596f9dca9c4",
      "entry_hash": "737c3f46cf09debe0b0472ecb4713c4f58b70bf7beee06bfc620116dd1cd5a6a",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 348,
      "entity_type": "security",
      "entity_id": "admin123",
      "action": "export_blocked",
      "note": "Endpoint=download_controlled_docx_export; Policy=allow_exports_false",
      "created_at": "2026-05-23 13:12:12",
      "previous_hash": "737c3f46cf09debe0b0472ecb4713c4f58b70bf7beee06bfc620116dd1cd5a6a",
      "entry_hash": "5d9c9f36bd19f7c3149de1592d97a99751b93e4bd7b1c06bb8280d127eaefcce",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 349,
      "entity_type": "security",
      "entity_id": "admin123",
      "action": "export_blocked",
      "note": "Endpoint=download_controlled_pdf_export; Policy=allow_exports_false",
      "created_at": "2026-05-23 13:12:23",
      "previous_hash": "5d9c9f36bd19f7c3149de1592d97a99751b93e4bd7b1c06bb8280d127eaefcce",
      "entry_hash": "b4a394b086ae649f0687c27cef17ac0afa1973665b644f1404fbc508ce4915e2",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 350,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-23 13:37:32",
      "previous_hash": "b4a394b086ae649f0687c27cef17ac0afa1973665b644f1404fbc508ce4915e2",
      "entry_hash": "e7489bc1b6bfeb8a3a2d13c4a1d4a3496ec050e7238baf595cabf9cc47cc0be1",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 351,
      "entity_type": "security",
      "entity_id": "admin123",
      "action": "export_blocked",
      "note": "Endpoint=controlled_docx_export; Policy=allow_exports_false",
      "created_at": "2026-05-23 13:37:39",
      "previous_hash": "e7489bc1b6bfeb8a3a2d13c4a1d4a3496ec050e7238baf595cabf9cc47cc0be1",
      "entry_hash": "daed4be136a115121e770a4576d85a01a5d1a2f8e258bbe4080c0c6ca5c48fd0",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 352,
      "entity_type": "security",
      "entity_id": "admin123",
      "action": "export_blocked",
      "note": "Endpoint=controlled_docx_export; Policy=allow_exports_false",
      "created_at": "2026-05-23 13:46:14",
      "previous_hash": "daed4be136a115121e770a4576d85a01a5d1a2f8e258bbe4080c0c6ca5c48fd0",
      "entry_hash": "c3f61ce3347b2a9e790155be9ae12b3f91b16c009304527a5222f352f68d72f5",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 353,
      "entity_type": "security",
      "entity_id": "admin123",
      "action": "export_blocked",
      "note": "Endpoint=controlled_pdf_conversion; Policy=allow_exports_false",
      "created_at": "2026-05-23 13:46:30",
      "previous_hash": "c3f61ce3347b2a9e790155be9ae12b3f91b16c009304527a5222f352f68d72f5",
      "entry_hash": "b8ad3c044e62726be86639c4c32c06b0b7cac13715ba8b2ac97766ab6bd7c73a",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 354,
      "entity_type": "security",
      "entity_id": "admin123",
      "action": "export_blocked",
      "note": "Endpoint=controlled_docx_export; Policy=allow_exports_false",
      "created_at": "2026-05-23 13:51:59",
      "previous_hash": "b8ad3c044e62726be86639c4c32c06b0b7cac13715ba8b2ac97766ab6bd7c73a",
      "entry_hash": "8e9af7496c89446392f8757f20982240d9db24d8d04df220d55d3d355c87117a",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 355,
      "entity_type": "security",
      "entity_id": "admin123",
      "action": "export_blocked",
      "note": "Endpoint=controlled_pdf_conversion; Policy=allow_exports_false",
      "created_at": "2026-05-23 13:52:25",
      "previous_hash": "8e9af7496c89446392f8757f20982240d9db24d8d04df220d55d3d355c87117a",
      "entry_hash": "720510522dfc2fb39fd33cff28e036dcfbd38dbe0b9c5b8ee773ded7a54ea99b",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 356,
      "entity_type": "security",
      "entity_id": "admin123",
      "action": "export_blocked",
      "note": "Endpoint=controlled_docx_export; Policy=allow_exports_false",
      "created_at": "2026-05-23 13:55:20",
      "previous_hash": "720510522dfc2fb39fd33cff28e036dcfbd38dbe0b9c5b8ee773ded7a54ea99b",
      "entry_hash": "aeae77cbd98a9c9e0f2b181c4b0645058a8055af71208888d9ef97ec6eb8a50e",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 357,
      "entity_type": "security",
      "entity_id": "admin123",
      "action": "export_blocked",
      "note": "Endpoint=controlled_pdf_conversion; Policy=allow_exports_false",
      "created_at": "2026-05-23 13:55:39",
      "previous_hash": "aeae77cbd98a9c9e0f2b181c4b0645058a8055af71208888d9ef97ec6eb8a50e",
      "entry_hash": "58a633446a61b2ca5c61e0913905143e9a087cc14fa28479eb03a2862e9d5a14",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 358,
      "entity_type": "security",
      "entity_id": "admin123",
      "action": "export_blocked",
      "note": "Endpoint=controlled_docx_export; Path=/docx-export/FAKE-TEST; Policy=allow_exports_false",
      "created_at": "2026-05-23 13:59:06",
      "previous_hash": "58a633446a61b2ca5c61e0913905143e9a087cc14fa28479eb03a2862e9d5a14",
      "entry_hash": "82f831f48e4b0ba892eab49ec2844ec80fa2b3227b9abe63ed8234afcde147e3",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 359,
      "entity_type": "security",
      "entity_id": "admin123",
      "action": "export_blocked",
      "note": "Endpoint=controlled_pdf_conversion; Path=/pdf-convert/FAKE-DOCX; Policy=allow_exports_false",
      "created_at": "2026-05-23 13:59:23",
      "previous_hash": "82f831f48e4b0ba892eab49ec2844ec80fa2b3227b9abe63ed8234afcde147e3",
      "entry_hash": "27f38b245333f687f99d618515bca118d7ace8fa3e77b981c1ee8f01b4c462e5",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 360,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-23 14:12:45",
      "previous_hash": "27f38b245333f687f99d618515bca118d7ace8fa3e77b981c1ee8f01b4c462e5",
      "entry_hash": "1562ccac43e05e87508b148506910164b721f082b43a74b2940c833c18e85571",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 361,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-25 17:06:36",
      "previous_hash": "1562ccac43e05e87508b148506910164b721f082b43a74b2940c833c18e85571",
      "entry_hash": "31aa3538ef4e8fad7967df0199b162fbf747d18b5b396f21e5eb9bc2216e337d",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 362,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-25 17:41:09",
      "previous_hash": "31aa3538ef4e8fad7967df0199b162fbf747d18b5b396f21e5eb9bc2216e337d",
      "entry_hash": "6cb8312853f8554b9bc9ebfbd6da62a806f6e81f1955c4814070e21cc0f7b21e",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 363,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-05-25 18:11:36",
      "previous_hash": "6cb8312853f8554b9bc9ebfbd6da62a806f6e81f1955c4814070e21cc0f7b21e",
      "entry_hash": "3072bfa6f6db6180b333bb4e057ad7988928f7862ad579b9e19bf2c97ee8485b",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 364,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-06-13 01:59:48",
      "previous_hash": "3072bfa6f6db6180b333bb4e057ad7988928f7862ad579b9e19bf2c97ee8485b",
      "entry_hash": "ecefca84c0518086e2b415a7d6f6cc065ff5b81dce50d4d09b3f039f54ff0ef9",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 365,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-06-13 11:53:02",
      "previous_hash": "ecefca84c0518086e2b415a7d6f6cc065ff5b81dce50d4d09b3f039f54ff0ef9",
      "entry_hash": "9d78fccd17021d6aa4f0743f7fe993ac6d671287ab7245ca43bc2e79d4f5be93",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 366,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-06-13 17:03:18",
      "previous_hash": "9d78fccd17021d6aa4f0743f7fe993ac6d671287ab7245ca43bc2e79d4f5be93",
      "entry_hash": "291047609efd5208ec6c310e495cb03dfa3bc38c6f5ea21c9b9ceb140abfc3ec",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 367,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-06-13 17:32:15",
      "previous_hash": "291047609efd5208ec6c310e495cb03dfa3bc38c6f5ea21c9b9ceb140abfc3ec",
      "entry_hash": "fbb43014f7c6505dafb0c32134a0d289fc24de209413bade4e20eb57cc2bf641",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    },
    {
      "id": 368,
      "entity_type": "auth",
      "entity_id": "admin123",
      "action": "login_success",
      "note": "User logged in successfully",
      "created_at": "2026-06-13 18:21:45",
      "previous_hash": "fbb43014f7c6505dafb0c32134a0d289fc24de209413bade4e20eb57cc2bf641",
      "entry_hash": "60c40b1d8279c816b3baea6a8cbbe59c859204925ae9c815048397482056b4bf",
      "hash_algorithm": "sha256",
      "firm_id": "FIRM-002"
    }
  ],
  "audit_classification": "LIKELY_VALID_TENANT_LOCAL_REUSE",
  "identical_payload_except_scope": false,
  "audit_reason": "Same business identifier appears in multiple firms. This is valid only if every lookup also includes firm_id.",
  "references": [
    {
      "file": "app.py",
      "function": "trust_minute_execution_packet_pdf",
      "line": 7550,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "trust_minute_detail",
      "line": 7819,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "verify_certificate",
      "line": 7857,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "audit_dashboard",
      "line": 7995,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "audit_log_report_pdf",
      "line": 10146,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "admin_audit_log",
      "line": 14193,
      "scope_markers": []
    },
    {
      "file": "pdf_utils.py",
      "function": "audit_log_report_story",
      "line": 529,
      "scope_markers": []
    },
    {
      "file": "database/db.py",
      "function": "init_audit_table",
      "line": 1939,
      "scope_markers": []
    },
    {
      "file": "database/db.py",
      "function": "log_change",
      "line": 1973,
      "scope_markers": [
        "firm_id"
      ]
    },
    {
      "file": "database/db.py",
      "function": "get_audit_log_by_entity",
      "line": 2044,
      "scope_markers": [
        "current_firm",
        "firm_id",
        "get_current_firm_id"
      ]
    },
    {
      "file": "database/db.py",
      "function": "verify_audit_log_chain",
      "line": 2076,
      "scope_markers": [
        "firm_id"
      ]
    },
    {
      "file": "database/db.py",
      "function": "build_system_health_report",
      "line": 3047,
      "scope_markers": []
    }
  ],
  "unsafe_references": [
    {
      "file": "app.py",
      "function": "trust_minute_execution_packet_pdf",
      "line": 7550,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "trust_minute_detail",
      "line": 7819,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "verify_certificate",
      "line": 7857,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "audit_dashboard",
      "line": 7995,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "audit_log_report_pdf",
      "line": 10146,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "admin_audit_log",
      "line": 14193,
      "scope_markers": []
    },
    {
      "file": "pdf_utils.py",
      "function": "audit_log_report_story",
      "line": 529,
      "scope_markers": []
    },
    {
      "file": "database/db.py",
      "function": "init_audit_table",
      "line": 1939,
      "scope_markers": []
    },
    {
      "file": "database/db.py",
      "function": "build_system_health_report",
      "line": 3047,
      "scope_markers": []
    }
  ],
  "classification": "CONFIRMED_IDENTIFIER_COLLISION_RISK",
  "reason": "Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter."
}
```

### DEFECT-011 — CONFIRMED_IDENTIFIER_COLLISION_RISK

- Reason: Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter.
- Table: `intake_document_recommendations`

```json
{
  "table": "intake_document_recommendations",
  "identifier_column": "intake_id",
  "identifier": "INTAKE-0005",
  "firms": "FIRM-001,FIRM-002",
  "firm_count": 2,
  "row_count": 15,
  "records": [
    {
      "id": 1,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-001",
      "workflow_key": "professional_review_checklist",
      "title": "Professional Review Checklist",
      "workflow_type": "professional_review",
      "priority": "urgent",
      "confidence": 99,
      "reason": "High urgency or review flags were detected during intake. Additional signal: Tax, legal, court, creditor, or professional-review signals were detected.",
      "source": "engine",
      "status": "recommended",
      "created_at": "2026-05-21T12:17:20",
      "updated_at": "2026-05-22T20:13:38",
      "created_by": "admin123"
    },
    {
      "id": 2,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-001",
      "workflow_key": "beneficiary_guardian_planning",
      "title": "Beneficiary / Guardian Planning",
      "workflow_type": "family",
      "priority": "high",
      "confidence": 97,
      "reason": "Beneficiary, child, guardian, or family planning issues were detected. Additional signal: Beneficiary, child, guardian, dependent, or family-planning signals were detected.",
      "source": "engine",
      "status": "recommended",
      "created_at": "2026-05-21T12:17:20",
      "updated_at": "2026-05-22T20:13:38",
      "created_by": "admin123"
    },
    {
      "id": 3,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-001",
      "workflow_key": "asset_inventory_packet",
      "title": "Asset Inventory Packet",
      "workflow_type": "inventory",
      "priority": "normal",
      "confidence": 92,
      "reason": "Assets and supporting records need to be organized before deeper review. Additional signal: Asset, account, title, statement, or inventory signals were detected.",
      "source": "engine",
      "status": "recommended",
      "created_at": "2026-05-21T12:17:20",
      "updated_at": "2026-05-22T20:13:38",
      "created_by": "admin123"
    },
    {
      "id": 4,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-001",
      "workflow_key": "next_session_agenda",
      "title": "Next Session Agenda",
      "workflow_type": "session",
      "priority": "normal",
      "confidence": 87,
      "reason": "A recommended next session was generated from the intake snapshot. Additional signal: Recommended next session exists and should be converted into a working agenda.",
      "source": "engine",
      "status": "recommended",
      "created_at": "2026-05-21T12:17:20",
      "updated_at": "2026-05-22T20:13:38",
      "created_by": "admin123"
    },
    {
      "id": 5,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-001",
      "workflow_key": "business_continuity_packet",
      "title": "Business Continuity Packet",
      "workflow_type": "business",
      "priority": "high",
      "confidence": 99,
      "reason": "Business-related documents, liability signals, partner/entity references, or business continuity tasks were detected.",
      "source": "engine_tuned",
      "status": "launch_prepared",
      "created_at": "2026-05-21T12:21:17",
      "updated_at": "2026-05-22T20:13:38",
      "created_by": "admin123"
    },
    {
      "id": 6,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-001",
      "workflow_key": "real_property_review",
      "title": "Real Property Review",
      "workflow_type": "asset",
      "priority": "high",
      "confidence": 99,
      "reason": "Property documents or real-property task signals were detected.",
      "source": "engine_tuned",
      "status": "recommended",
      "created_at": "2026-05-21T12:21:17",
      "updated_at": "2026-05-22T20:13:38",
      "created_by": "admin123"
    },
    {
      "id": 7,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-001",
      "workflow_key": "foundational_estate_package",
      "title": "Foundational Estate Planning Package",
      "workflow_type": "planning",
      "priority": "high",
      "confidence": 97,
      "reason": "Readiness is low or foundational planning/document gaps were detected.",
      "source": "engine_tuned",
      "status": "recommended",
      "created_at": "2026-05-21T12:21:17",
      "updated_at": "2026-05-22T20:13:38",
      "created_by": "admin123"
    },
    {
      "id": 8,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-001",
      "workflow_key": "document_audit",
      "title": "Existing Document Audit",
      "workflow_type": "review",
      "priority": "high",
      "confidence": 95,
      "reason": "Document gaps, existing document references, or document follow-up tasks were detected.",
      "source": "engine_tuned",
      "status": "recommended",
      "created_at": "2026-05-21T12:21:17",
      "updated_at": "2026-05-22T20:13:38",
      "created_by": "admin123"
    },
    {
      "id": 9,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-002",
      "workflow_key": "certificate_of_trust",
      "title": "Certificate of Trust",
      "workflow_type": "Trust Instrument",
      "priority": "High",
      "confidence": 94,
      "reason": "A Certificate of Trust can summarize trust existence, authority, trustees, and limited certification details without exposing the full trust instrument.",
      "source": "instrument_menu",
      "status": "launch_prepared",
      "created_at": "2026-05-21T22:22:33",
      "updated_at": "2026-05-22T20:13:38",
      "created_by": "admin123"
    },
    {
      "id": 10,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-002",
      "workflow_key": "trust_articles_builder",
      "title": "Trust Articles / Article Builder",
      "workflow_type": "Trust Instrument",
      "priority": "High",
      "confidence": 93,
      "reason": "Trust articles allow controlled drafting of governing provisions, powers, limitations, fiduciary terms, and administrative structure.",
      "source": "instrument_menu",
      "status": "recommended",
      "created_at": "2026-05-21T22:22:33",
      "updated_at": "2026-05-22T20:13:38",
      "created_by": "admin123"
    },
    {
      "id": 11,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-002",
      "workflow_key": "declaration_of_trust",
      "title": "Declaration of Trust",
      "workflow_type": "Trust Instrument",
      "priority": "High",
      "confidence": 92,
      "reason": "A Declaration of Trust can organize the trust name, settlor/grantor role, trustee authority, trust purpose, property, beneficiaries, and administration terms.",
      "source": "instrument_menu",
      "status": "recommended",
      "created_at": "2026-05-21T22:22:33",
      "updated_at": "2026-05-22T20:13:38",
      "created_by": "admin123"
    },
    {
      "id": 12,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-002",
      "workflow_key": "schedule_a_asset_schedule",
      "title": "Schedule A / Asset Schedule",
      "workflow_type": "Trust Funding",
      "priority": "High",
      "confidence": 91,
      "reason": "A Schedule A or asset schedule organizes initial trust property, later contributions, asset descriptions, supporting records, and transfer readiness.",
      "source": "instrument_menu",
      "status": "recommended",
      "created_at": "2026-05-21T22:22:33",
      "updated_at": "2026-05-22T20:13:38",
      "created_by": "admin123"
    },
    {
      "id": 13,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-002",
      "workflow_key": "execution_notary_witness_packet",
      "title": "Execution / Notary / Witness Packet",
      "workflow_type": "Execution",
      "priority": "High",
      "confidence": 91,
      "reason": "Execution packets organize signature blocks, witness sections, jurat/notary language, execution checklist, and completion controls.",
      "source": "instrument_menu",
      "status": "recommended",
      "created_at": "2026-05-21T22:22:33",
      "updated_at": "2026-05-22T20:13:38",
      "created_by": "admin123"
    },
    {
      "id": 14,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-002",
      "workflow_key": "trustee_acceptance",
      "title": "Trustee Acceptance",
      "workflow_type": "Trust Instrument",
      "priority": "Normal",
      "confidence": 90,
      "reason": "Trustee acceptance records formal acceptance of appointment and fiduciary responsibilities.",
      "source": "instrument_menu",
      "status": "recommended",
      "created_at": "2026-05-21T22:22:33",
      "updated_at": "2026-05-22T20:13:38",
      "created_by": "admin123"
    },
    {
      "id": 15,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-002",
      "workflow_key": "trust_minutes_resolution",
      "title": "Trust Minutes / Resolution",
      "workflow_type": "Trust Governance",
      "priority": "Normal",
      "confidence": 89,
      "reason": "Trust minutes and resolutions document trustee decisions, approvals, appointments, authority, and administrative actions.",
      "source": "instrument_menu",
      "status": "recommended",
      "created_at": "2026-05-21T22:22:33",
      "updated_at": "2026-05-22T20:13:38",
      "created_by": "admin123"
    }
  ],
  "audit_classification": "LIKELY_VALID_TENANT_LOCAL_REUSE",
  "identical_payload_except_scope": false,
  "audit_reason": "Same business identifier appears in multiple firms. This is valid only if every lookup also includes firm_id.",
  "references": [
    {
      "file": "app.py",
      "function": "intake_document_recommendations",
      "line": 18060,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "intake_update_recommendation_status",
      "line": 18085,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "intake_workflow_launch_prep",
      "line": 18101,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "intake_workflow_bridge",
      "line": 18122,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "intake_workflow_bridge_summary",
      "line": 18204,
      "scope_markers": []
    },
    {
      "file": "services/services_intake.py",
      "function": "ensure_intake_document_recommendation_tables",
      "line": 3905,
      "scope_markers": [
        "firm_id"
      ]
    },
    {
      "file": "services/services_intake.py",
      "function": "save_document_recommendations",
      "line": 3966,
      "scope_markers": [
        "current_firm",
        "firm_id",
        "get_current_firm_id"
      ]
    },
    {
      "file": "services/services_intake.py",
      "function": "list_saved_document_recommendations",
      "line": 4050,
      "scope_markers": []
    },
    {
      "file": "services/services_intake.py",
      "function": "update_document_recommendation_status",
      "line": 4435,
      "scope_markers": []
    },
    {
      "file": "services/services_intake.py",
      "function": "get_document_recommendation",
      "line": 4467,
      "scope_markers": []
    },
    {
      "file": "services/services_intake.py",
      "function": "save_workflow_bridge_answers",
      "line": 5084,
      "scope_markers": [
        "current_firm",
        "firm_id",
        "get_current_firm_id"
      ]
    }
  ],
  "unsafe_references": [
    {
      "file": "app.py",
      "function": "intake_document_recommendations",
      "line": 18060,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "intake_update_recommendation_status",
      "line": 18085,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "intake_workflow_launch_prep",
      "line": 18101,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "intake_workflow_bridge",
      "line": 18122,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "intake_workflow_bridge_summary",
      "line": 18204,
      "scope_markers": []
    },
    {
      "file": "services/services_intake.py",
      "function": "list_saved_document_recommendations",
      "line": 4050,
      "scope_markers": []
    },
    {
      "file": "services/services_intake.py",
      "function": "update_document_recommendation_status",
      "line": 4435,
      "scope_markers": []
    },
    {
      "file": "services/services_intake.py",
      "function": "get_document_recommendation",
      "line": 4467,
      "scope_markers": []
    }
  ],
  "classification": "CONFIRMED_IDENTIFIER_COLLISION_RISK",
  "reason": "Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter."
}
```

### DEFECT-012 — CONFIRMED_IDENTIFIER_COLLISION_RISK

- Reason: Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter.
- Table: `intake_export_logs`

```json
{
  "table": "intake_export_logs",
  "identifier_column": "intake_id",
  "identifier": "INTAKE-0005",
  "firms": "FIRM-001,FIRM-002",
  "firm_count": 2,
  "row_count": 10,
  "records": [
    {
      "id": 1,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-001",
      "export_type": "test",
      "export_status": "success",
      "file_path": null,
      "message": "INT-1M export log table test.",
      "created_at": "2026-05-21T02:57:43",
      "created_by": "system_check",
      "version_number": 1,
      "packet_type": "follow_up_packet"
    },
    {
      "id": 2,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-001",
      "export_type": "version_test",
      "export_status": "success",
      "file_path": null,
      "message": "INT-1N versioning test.",
      "created_at": "2026-05-21T03:03:20",
      "created_by": "system_check",
      "version_number": 1,
      "packet_type": "follow_up_packet"
    },
    {
      "id": 3,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-001",
      "export_type": "draft_docx",
      "export_status": "success",
      "file_path": "exports\\draft_packets\\INTAKE-0005_business_continuity_packet_Draft_Packet.docx",
      "message": "Draft packet DOCX generated for business_continuity_packet.",
      "created_at": "2026-05-21T13:02:44",
      "created_by": "system_check",
      "version_number": 1,
      "packet_type": "draft_packet"
    },
    {
      "id": 4,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-001",
      "export_type": "nonfinal_docx",
      "export_status": "success",
      "file_path": "exports\\nonfinal_drafts\\INTAKE-0005_business_continuity_packet_business_continuity_memo_NON_FINAL_DRAFT.docx",
      "message": "Non-final draft DOCX generated for business_continuity_packet/business_continuity_memo. Gate=blocked.",
      "created_at": "2026-05-21T14:03:06",
      "created_by": "system_check",
      "version_number": 1,
      "packet_type": "nonfinal_draft"
    },
    {
      "id": 7,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-001",
      "export_type": "final_draft_preview_docx",
      "export_status": "success",
      "file_path": "exports\\final_draft_previews\\INTAKE-0005_business_continuity_packet_business_continuity_memo_FINAL_DRAFT_PREVIEW.docx",
      "message": "Final-draft preview DOCX generated for business_continuity_packet/business_continuity_memo. Status=Final-Draft Preview Incomplete.",
      "created_at": "2026-05-21T15:25:53",
      "created_by": "system_check",
      "version_number": 1,
      "packet_type": "final_draft_preview"
    },
    {
      "id": 9,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-001",
      "export_type": "final_draft_preview_docx",
      "export_status": "success",
      "file_path": "exports\\final_draft_previews\\INTAKE-0005_business_continuity_packet_business_continuity_memo_FINAL_DRAFT_PREVIEW.docx",
      "message": "Final-draft preview DOCX generated for business_continuity_packet/business_continuity_memo. Status=Final-Draft Preview Incomplete.",
      "created_at": "2026-05-21T15:30:32",
      "created_by": "system_check",
      "version_number": 3,
      "packet_type": "final_draft_preview"
    },
    {
      "id": 10,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-001",
      "export_type": "final_draft_preview_docx",
      "export_status": "success",
      "file_path": "exports\\final_draft_previews\\INTAKE-0005_business_continuity_packet_business_continuity_memo_FINAL_DRAFT_PREVIEW.docx",
      "message": "Final-draft preview DOCX generated for business_continuity_packet/business_continuity_memo. Status=Final-Draft Preview Incomplete.",
      "created_at": "2026-05-21T15:32:08",
      "created_by": "system_check",
      "version_number": 4,
      "packet_type": "final_draft_preview"
    },
    {
      "id": 5,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-002",
      "export_type": "nonfinal_docx",
      "export_status": "success",
      "file_path": "exports\\nonfinal_drafts\\INTAKE-0005_business_continuity_packet_business_continuity_memo_NON_FINAL_DRAFT.docx",
      "message": "Non-final draft DOCX generated for business_continuity_packet/business_continuity_memo. Gate=blocked.",
      "created_at": "2026-05-21T14:07:03",
      "created_by": "admin123",
      "version_number": 2,
      "packet_type": "nonfinal_draft"
    },
    {
      "id": 6,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-002",
      "export_type": "nonfinal_docx",
      "export_status": "success",
      "file_path": "exports\\nonfinal_drafts\\INTAKE-0005_business_continuity_packet_business_continuity_memo_NON_FINAL_DRAFT.docx",
      "message": "Non-final draft DOCX generated for business_continuity_packet/business_continuity_memo. Gate=blocked.",
      "created_at": "2026-05-21T14:08:21",
      "created_by": "admin123",
      "version_number": 3,
      "packet_type": "nonfinal_draft"
    },
    {
      "id": 8,
      "intake_id": "INTAKE-0005",
      "firm_id": "FIRM-002",
      "export_type": "final_draft_preview_docx",
      "export_status": "success",
      "file_path": "exports\\final_draft_previews\\INTAKE-0005_business_continuity_packet_business_continuity_memo_FINAL_DRAFT_PREVIEW.docx",
      "message": "Final-draft preview DOCX generated for business_continuity_packet/business_continuity_memo. Status=Final-Draft Preview Incomplete.",
      "created_at": "2026-05-21T15:26:27",
      "created_by": "admin123",
      "version_number": 2,
      "packet_type": "final_draft_preview"
    }
  ],
  "audit_classification": "LIKELY_VALID_TENANT_LOCAL_REUSE",
  "identical_payload_except_scope": false,
  "audit_reason": "Same business identifier appears in multiple firms. This is valid only if every lookup also includes firm_id.",
  "references": [
    {
      "file": "app.py",
      "function": "intake_export_prep",
      "line": 17905,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "intake_export_history_detail",
      "line": 18034,
      "scope_markers": []
    },
    {
      "file": "services/services_intake.py",
      "function": "ensure_intake_export_log_tables",
      "line": 2913,
      "scope_markers": [
        "firm_id"
      ]
    },
    {
      "file": "services/services_intake.py",
      "function": "log_intake_export",
      "line": 2936,
      "scope_markers": [
        "current_firm",
        "firm_id",
        "get_current_firm_id"
      ]
    },
    {
      "file": "services/services_intake.py",
      "function": "list_intake_export_logs",
      "line": 2976,
      "scope_markers": []
    },
    {
      "file": "services/services_intake.py",
      "function": "get_next_export_version",
      "line": 3101,
      "scope_markers": []
    },
    {
      "file": "services/services_intake.py",
      "function": "log_intake_export_versioned",
      "line": 3123,
      "scope_markers": [
        "current_firm",
        "firm_id",
        "get_current_firm_id"
      ]
    },
    {
      "file": "services/services_intake.py",
      "function": "list_all_intake_export_logs",
      "line": 3180,
      "scope_markers": [
        "current_firm",
        "firm_id",
        "get_current_firm_id"
      ]
    },
    {
      "file": "services/services_intake.py",
      "function": "list_intake_export_logs_versioned",
      "line": 3215,
      "scope_markers": []
    },
    {
      "file": "services/services_intake.py",
      "function": "list_all_intake_export_logs_any_scope",
      "line": 3371,
      "scope_markers": [
        "firm_id"
      ]
    }
  ],
  "unsafe_references": [
    {
      "file": "app.py",
      "function": "intake_export_prep",
      "line": 17905,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "intake_export_history_detail",
      "line": 18034,
      "scope_markers": []
    },
    {
      "file": "services/services_intake.py",
      "function": "list_intake_export_logs",
      "line": 2976,
      "scope_markers": []
    },
    {
      "file": "services/services_intake.py",
      "function": "get_next_export_version",
      "line": 3101,
      "scope_markers": []
    },
    {
      "file": "services/services_intake.py",
      "function": "list_intake_export_logs_versioned",
      "line": 3215,
      "scope_markers": []
    }
  ],
  "classification": "CONFIRMED_IDENTIFIER_COLLISION_RISK",
  "reason": "Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter."
}
```

### DEFECT-013 — CONFIRMED_IDENTIFIER_COLLISION_RISK

- Reason: Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter.
- Table: `intake_final_draft_gate_actions`

```json
{
  "table": "intake_final_draft_gate_actions",
  "identifier_column": "intake_id",
  "identifier": "INTAKE-0005",
  "firms": "FIRM-001,FIRM-002",
  "firm_count": 2,
  "row_count": 6,
  "records": [
    {
      "id": 1,
      "intake_id": "INTAKE-0005",
      "workflow_key": "business_continuity_packet",
      "document_key": "business_continuity_memo",
      "firm_id": "FIRM-001",
      "action_key": "professional_review_confirmed",
      "action_label": "Professional Review Status Confirmed",
      "note": "INT-2L system test action.",
      "created_at": "2026-05-21T14:37:29",
      "created_by": "system_check"
    },
    {
      "id": 2,
      "intake_id": "INTAKE-0005",
      "workflow_key": "business_continuity_packet",
      "document_key": "business_continuity_memo",
      "firm_id": "FIRM-002",
      "action_key": "missing_answers_acknowledged",
      "action_label": "Missing Answers Reviewed / Acknowledged",
      "note": "Administrative review completed for test workflow. Final-draft preparation may proceed, but no signing, filing, execution, or final use is authorized.",
      "created_at": "2026-05-21T14:40:19",
      "created_by": "admin123"
    },
    {
      "id": 3,
      "intake_id": "INTAKE-0005",
      "workflow_key": "business_continuity_packet",
      "document_key": "business_continuity_memo",
      "firm_id": "FIRM-002",
      "action_key": "open_issues_reviewed",
      "action_label": "Open Issues Reviewed / Accepted",
      "note": "Administrative review completed for test workflow. Final-draft preparation may proceed, but no signing, filing, execution, or final use is authorized.",
      "created_at": "2026-05-21T14:40:19",
      "created_by": "admin123"
    },
    {
      "id": 4,
      "intake_id": "INTAKE-0005",
      "workflow_key": "business_continuity_packet",
      "document_key": "business_continuity_memo",
      "firm_id": "FIRM-002",
      "action_key": "open_tasks_reviewed",
      "action_label": "Open Tasks Reviewed / Accepted",
      "note": "Administrative review completed for test workflow. Final-draft preparation may proceed, but no signing, filing, execution, or final use is authorized.",
      "created_at": "2026-05-21T14:40:19",
      "created_by": "admin123"
    },
    {
      "id": 5,
      "intake_id": "INTAKE-0005",
      "workflow_key": "business_continuity_packet",
      "document_key": "business_continuity_memo",
      "firm_id": "FIRM-002",
      "action_key": "required_documents_acknowledged",
      "action_label": "Required Documents Acknowledged",
      "note": "Administrative review completed for test workflow. Final-draft preparation may proceed, but no signing, filing, execution, or final use is authorized.",
      "created_at": "2026-05-21T14:40:19",
      "created_by": "admin123"
    },
    {
      "id": 6,
      "intake_id": "INTAKE-0005",
      "workflow_key": "business_continuity_packet",
      "document_key": "business_continuity_memo",
      "firm_id": "FIRM-002",
      "action_key": "professional_review_confirmed",
      "action_label": "Professional Review Status Confirmed",
      "note": "Administrative review completed for test workflow. Final-draft preparation may proceed, but no signing, filing, execution, or final use is authorized.",
      "created_at": "2026-05-21T14:40:19",
      "created_by": "admin123"
    }
  ],
  "audit_classification": "LIKELY_VALID_TENANT_LOCAL_REUSE",
  "identical_payload_except_scope": false,
  "audit_reason": "Same business identifier appears in multiple firms. This is valid only if every lookup also includes firm_id.",
  "references": [
    {
      "file": "services/services_intake.py",
      "function": "ensure_final_draft_resolution_tables",
      "line": 7301,
      "scope_markers": [
        "firm_id"
      ]
    },
    {
      "file": "services/services_intake.py",
      "function": "list_final_draft_resolution_actions",
      "line": 7326,
      "scope_markers": []
    },
    {
      "file": "services/services_intake.py",
      "function": "record_final_draft_resolution_actions",
      "line": 7361,
      "scope_markers": [
        "current_firm",
        "firm_id",
        "get_current_firm_id"
      ]
    }
  ],
  "unsafe_references": [
    {
      "file": "services/services_intake.py",
      "function": "list_final_draft_resolution_actions",
      "line": 7326,
      "scope_markers": []
    }
  ],
  "classification": "CONFIRMED_IDENTIFIER_COLLISION_RISK",
  "reason": "Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter."
}
```

### DEFECT-014 — CONFIRMED_IDENTIFIER_COLLISION_RISK

- Reason: Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter.
- Table: `intake_review_gate_actions`

```json
{
  "table": "intake_review_gate_actions",
  "identifier_column": "intake_id",
  "identifier": "INTAKE-0005",
  "firms": "FIRM-001,FIRM-002",
  "firm_count": 2,
  "row_count": 2,
  "records": [
    {
      "id": 1,
      "intake_id": "INTAKE-0005",
      "workflow_key": "business_continuity_packet",
      "document_key": "business_continuity_memo",
      "gate_name": "non_final_draft_review_gate",
      "firm_id": "FIRM-001",
      "action_key": "professional_review_required",
      "action_label": "Professional Review Required",
      "resulting_status": "professional_review_required",
      "note": "INT-2J system test action.",
      "created_at": "2026-05-21T14:18:31",
      "created_by": "system_check"
    },
    {
      "id": 2,
      "intake_id": "INTAKE-0005",
      "workflow_key": "business_continuity_packet",
      "document_key": "business_continuity_memo",
      "gate_name": "non_final_draft_review_gate",
      "firm_id": "FIRM-002",
      "action_key": "missing_answers_resolved",
      "action_label": "Missing Answers Resolved",
      "resulting_status": "review_required",
      "note": "",
      "created_at": "2026-05-21T14:29:27",
      "created_by": "admin123"
    }
  ],
  "audit_classification": "LIKELY_VALID_TENANT_LOCAL_REUSE",
  "identical_payload_except_scope": false,
  "audit_reason": "Same business identifier appears in multiple firms. This is valid only if every lookup also includes firm_id.",
  "references": [
    {
      "file": "services/services_intake.py",
      "function": "ensure_review_gate_resolution_tables",
      "line": 6718,
      "scope_markers": [
        "firm_id"
      ]
    },
    {
      "file": "services/services_intake.py",
      "function": "list_review_gate_actions",
      "line": 6789,
      "scope_markers": []
    },
    {
      "file": "services/services_intake.py",
      "function": "resolve_review_gate_action",
      "line": 6822,
      "scope_markers": [
        "current_firm",
        "firm_id",
        "get_current_firm_id"
      ]
    }
  ],
  "unsafe_references": [
    {
      "file": "services/services_intake.py",
      "function": "list_review_gate_actions",
      "line": 6789,
      "scope_markers": []
    }
  ],
  "classification": "CONFIRMED_IDENTIFIER_COLLISION_RISK",
  "reason": "Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter."
}
```

### DEFECT-015 — CONFIRMED_IDENTIFIER_COLLISION_RISK

- Reason: Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter.
- Table: `workspaces`

```json
{
  "table": "workspaces",
  "identifier_column": "owner_id",
  "identifier": "ADMIN_OWNER_001",
  "firms": "FIRM-001,FIRM-002",
  "firm_count": 2,
  "row_count": 7,
  "records": [
    {
      "workspace_id": "WS-001",
      "title": "Family Trust Design Sandbox",
      "workspace_type": "trust_design",
      "trust_type_focus": "revocable",
      "purpose": "Plan and compare family trust structure options before formal buildout.",
      "owner": "admin",
      "status": "draft",
      "created_at": "2026-04-12 22:40:34",
      "updated_at": "2026-04-12 22:40:34",
      "owner_id": "ADMIN_OWNER_001",
      "firm_id": "FIRM-001"
    },
    {
      "workspace_id": "WS-002",
      "title": "Fiduciary Filing Planning Sandbox",
      "workspace_type": "filing_planning",
      "trust_type_focus": "other",
      "purpose": "Organize filing questions, tax form links, and reporting workflow notes.",
      "owner": "admin",
      "status": "draft",
      "created_at": "2026-04-12 22:40:34",
      "updated_at": "2026-04-12 22:40:34",
      "owner_id": "ADMIN_OWNER_001",
      "firm_id": "FIRM-001"
    },
    {
      "workspace_id": "WS-010",
      "title": "Land Holding Structure Sandbox",
      "workspace_type": "trust_design",
      "trust_type_focus": "land",
      "purpose": "Explore real-property holding structure and related recordkeeping questions.",
      "owner": "admin",
      "status": "draft",
      "created_at": "2026-04-13 02:11:23",
      "updated_at": "2026-04-13 02:11:23",
      "owner_id": "ADMIN_OWNER_001",
      "firm_id": "FIRM-001"
    },
    {
      "workspace_id": "WS-011",
      "title": "Insurance Planning Sandbox",
      "workspace_type": "trust_design",
      "trust_type_focus": "insurance",
      "purpose": "Explore insurance-related trust planning and documentation questions.",
      "owner": "admin",
      "status": "draft",
      "created_at": "2026-04-13 02:11:23",
      "updated_at": "2026-04-13 02:11:23",
      "owner_id": "ADMIN_OWNER_001",
      "firm_id": "FIRM-001"
    },
    {
      "workspace_id": "WS-012",
      "title": "Tax Workflow Sandbox",
      "workspace_type": "filing_planning",
      "trust_type_focus": "complex",
      "purpose": "Organize filing guides, reporting flow, and amendment considerations.",
      "owner": "admin",
      "status": "draft",
      "created_at": "2026-04-13 02:11:23",
      "updated_at": "2026-04-13 02:11:23",
      "owner_id": "ADMIN_OWNER_001",
      "firm_id": "FIRM-001"
    },
    {
      "workspace_id": "admin 01",
      "title": "too much",
      "workspace_type": "too short",
      "trust_type_focus": "too long",
      "purpose": "too fat",
      "owner": "admin",
      "status": "draft",
      "created_at": "2026-04-14 22:43:10",
      "updated_at": "2026-04-14 22:43:10",
      "owner_id": "ADMIN_OWNER_001",
      "firm_id": "FIRM-001"
    },
    {
      "workspace_id": "FIRM-002",
      "title": "Luna I Mishoe III Revocable Trust",
      "workspace_type": "Trust Creation",
      "trust_type_focus": "Beneficiary",
      "purpose": "Too Create a Trust",
      "owner": "Luna Mishoe",
      "status": "draft",
      "created_at": "2026-05-12 03:52:31",
      "updated_at": "2026-05-12 03:52:31",
      "owner_id": "ADMIN_OWNER_001",
      "firm_id": "FIRM-002"
    }
  ],
  "audit_classification": "LIKELY_VALID_TENANT_LOCAL_REUSE",
  "identical_payload_except_scope": false,
  "audit_reason": "Same business identifier appears in multiple firms. This is valid only if every lookup also includes firm_id.",
  "references": [
    {
      "file": "app.py",
      "function": "run_hosted_startup_self_heal",
      "line": 318,
      "scope_markers": [
        "firm_id"
      ]
    },
    {
      "file": "app.py",
      "function": "create_workspace",
      "line": 8904,
      "scope_markers": [
        "firm_id",
        "session.get(\"firm_id\")"
      ]
    },
    {
      "file": "app.py",
      "function": "discussion_new",
      "line": 10528,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "document_generate",
      "line": 10888,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "hosted_repair_admin_access_once",
      "line": 14760,
      "scope_markers": [
        "firm_id"
      ]
    }
  ],
  "unsafe_references": [
    {
      "file": "app.py",
      "function": "discussion_new",
      "line": 10528,
      "scope_markers": []
    },
    {
      "file": "app.py",
      "function": "document_generate",
      "line": 10888,
      "scope_markers": []
    }
  ],
  "classification": "CONFIRMED_IDENTIFIER_COLLISION_RISK",
  "reason": "Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter."
}
```


## Probable Defects

### PROBABLE-001 — PROBABLE_DEFECT_REPAIRABLE

- Reason: Null-firm record has one unambiguous tenant owner through related scoped records.
- Table: `audit_log`

### PROBABLE-002 — PROBABLE_DEFECT_REPAIRABLE

- Reason: Null-firm record has one unambiguous tenant owner through related scoped records.
- Table: `audit_log`

### PROBABLE-003 — PROBABLE_DEFECT_REPAIRABLE

- Reason: Null-firm record has one unambiguous tenant owner through related scoped records.
- Table: `audit_log`

### PROBABLE-004 — PROBABLE_DEFECT_REPAIRABLE

- Reason: Null-firm record has one unambiguous tenant owner through related scoped records.
- Table: `documents`

### PROBABLE-005 — PROBABLE_DEFECT_REPAIRABLE

- Reason: Null-firm record has one unambiguous tenant owner through related scoped records.
- Table: `documents`

### PROBABLE-006 — PROBABLE_DEFECT_REPAIRABLE

- Reason: Null-firm record has one unambiguous tenant owner through related scoped records.
- Table: `documents`

### PROBABLE-007 — PROBABLE_UNSCOPED_TABLE_DEFECT

- Reason: Tenant-sensitive table lacks firm_id and is referenced from functions without an obvious tenant-scope marker.
- Table: `chart_of_accounts`

### PROBABLE-008 — PROBABLE_UNSCOPED_TABLE_DEFECT

- Reason: Tenant-sensitive table lacks firm_id and is referenced from functions without an obvious tenant-scope marker.
- Table: `discussion_threads`

### PROBABLE-009 — PROBABLE_UNSCOPED_TABLE_DEFECT

- Reason: Tenant-sensitive table lacks firm_id and is referenced from functions without an obvious tenant-scope marker.
- Table: `genealogy_records`

### PROBABLE-010 — PROBABLE_UNSCOPED_TABLE_DEFECT

- Reason: Tenant-sensitive table lacks firm_id and is referenced from functions without an obvious tenant-scope marker.
- Table: `user_permission_overrides`

### PROBABLE-011 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:431`
- Function: `get_next_trust_id`

### PROBABLE-012 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:654`
- Function: `get_next_account_id`

### PROBABLE-013 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:707`
- Function: `get_next_document_id`

### PROBABLE-014 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:755`
- Function: `get_documents_by_property_id`

### PROBABLE-015 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:765`
- Function: `get_next_entry_id`

### PROBABLE-016 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:793`
- Function: `get_ledger_by_trust`

### PROBABLE-017 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:804`
- Function: `get_ledger_by_property`

### PROBABLE-018 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:1163`
- Function: `get_next_distribution_id`

### PROBABLE-019 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:1384`
- Function: `get_distribution_by_id_and_trust`

### PROBABLE-020 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:1538`
- Function: `get_ledger_entries_by_trust_id`

### PROBABLE-021 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:2556`
- Function: `get_next_media_id`

### PROBABLE-022 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:2711`
- Function: `get_next_role_id`

### PROBABLE-023 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:2811`
- Function: `get_user_by_username`

### PROBABLE-024 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:2845`
- Function: `get_next_user_id`

### PROBABLE-025 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:2854`
- Function: `get_all_app_users`

### PROBABLE-026 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:2987`
- Function: `get_effective_permissions_for_user`

### PROBABLE-027 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:3255`
- Function: `get_next_minute_id`

### PROBABLE-028 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:3291`
- Function: `backfill_trust_minute_certificate_ids`

### PROBABLE-029 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:3327`
- Function: `get_trust_minute_by_certificate_id`

### PROBABLE-030 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `database/db.py:3343`
- Function: `get_certificate_registry_records`

### PROBABLE-031 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `services/services_continuity_assets.py:351`
- Function: `get_evidence_documents_for_property`

### PROBABLE-032 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `services/services_continuity_assets.py:368`
- Function: `get_evidence_media_for_property`

### PROBABLE-033 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `services/services_continuity_assets.py:858`
- Function: `get_next_archive_finalization_id`

### PROBABLE-034 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `services/services_continuity_assets.py:912`
- Function: `get_archive_finalizations_for_property`

### PROBABLE-035 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `services/services_intake.py:123`
- Function: `_next_intake_id`

### PROBABLE-036 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `services/services_intake.py:3107`
- Function: `get_next_export_version`

### PROBABLE-037 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `services/services_intake.py:3221`
- Function: `list_intake_export_logs_versioned`

### PROBABLE-038 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:165`
- Function: `get_next_trust_id`

### PROBABLE-039 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:198`
- Function: `get_all_trusts`

### PROBABLE-040 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:206`
- Function: `get_trust_by_id`

### PROBABLE-041 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:269`
- Function: `get_all_assets`

### PROBABLE-042 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:295`
- Function: `get_next_account_id`

### PROBABLE-043 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:319`
- Function: `get_accounts_by_trust_id`

### PROBABLE-044 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:327`
- Function: `get_accounts_by_property_id`

### PROBABLE-045 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:335`
- Function: `get_next_document_id`

### PROBABLE-046 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:360`
- Function: `get_documents_by_trust_id`

### PROBABLE-047 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:368`
- Function: `get_documents_by_property_id`

### PROBABLE-048 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:376`
- Function: `get_next_entry_id`

### PROBABLE-049 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:403`
- Function: `get_ledger_by_trust`

### PROBABLE-050 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:411`
- Function: `get_ledger_by_property`

### PROBABLE-051 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:768`
- Function: `get_next_distribution_id`

### PROBABLE-052 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:852`
- Function: `get_distribution_by_id`

### PROBABLE-053 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:862`
- Function: `get_distributions_by_trust_id`

### PROBABLE-054 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:870`
- Function: `get_distributions_by_trust_id`

### PROBABLE-055 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:970`
- Function: `get_distribution_by_id_and_trust`

### PROBABLE-056 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:1033`

### PROBABLE-057 — PROBABLE_UNSCOPED_READ_DEFECT

- Reason: Tenant-table read query has no detected direct, function, or helper scope.
- Source: `package_export/database/db.py:1123`
- Function: `get_ledger_entries_by_trust_id`

### PROBABLE-058 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:6450`
- Function: `form1041_preview`

### PROBABLE-059 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:6457`
- Function: `form1041_print`

### PROBABLE-060 — PROBABLE_UNGATED_MUTATION_DEFECT

- Reason: Record-mutating route has no detected tenant-scope protection.
- Source: `app.py:8064`
- Function: `k1_toggle_beneficiary`

### PROBABLE-061 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:10344`
- Function: `video_trust_type`

### PROBABLE-062 — PROBABLE_UNGATED_MUTATION_DEFECT

- Reason: Record-mutating route has no detected tenant-scope protection.
- Source: `app.py:15209`
- Function: `trust_article_assignment_add`

### PROBABLE-063 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:17857`
- Function: `intake_saved_snapshot`

### PROBABLE-064 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:17890`
- Function: `intake_resume`

### PROBABLE-065 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:17904`
- Function: `intake_export_prep`

### PROBABLE-066 — PROBABLE_UNGATED_MUTATION_DEFECT

- Reason: Record-mutating route has no detected tenant-scope protection.
- Source: `app.py:17958`
- Function: `intake_update_followup_task_status`

### PROBABLE-067 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:17973`
- Function: `intake_followup_packet`

### PROBABLE-068 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:17990`
- Function: `intake_followup_packet_docx`

### PROBABLE-069 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18004`
- Function: `intake_followup_packet_pdf`

### PROBABLE-070 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18033`
- Function: `intake_export_history_detail`

### PROBABLE-071 — PROBABLE_UNGATED_MUTATION_DEFECT

- Reason: Record-mutating route has no detected tenant-scope protection.
- Source: `app.py:18084`
- Function: `intake_update_recommendation_status`

### PROBABLE-072 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18100`
- Function: `intake_workflow_launch_prep`

### PROBABLE-073 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18203`
- Function: `intake_workflow_bridge_summary`

### PROBABLE-074 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18238`
- Function: `intake_workflow_draft_packet_docx`

### PROBABLE-075 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18263`
- Function: `intake_draft_readiness_ledger_detail`

### PROBABLE-076 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18273`
- Function: `intake_document_draft_choose`

### PROBABLE-077 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18330`
- Function: `intake_document_draft_preview`

### PROBABLE-078 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18371`
- Function: `intake_nonfinal_draft_docx`

### PROBABLE-079 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18402`
- Function: `intake_review_gate_ledger_detail`

### PROBABLE-080 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18412`
- Function: `intake_review_gate_detail`

### PROBABLE-081 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18452`
- Function: `intake_final_draft_gate_ledger_detail`

### PROBABLE-082 — PROBABLE_UNGATED_MUTATION_DEFECT

- Reason: Record-mutating route has no detected tenant-scope protection.
- Source: `app.py:18495`
- Function: `intake_final_draft_gate_approve`

### PROBABLE-083 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18604`
- Function: `intake_final_draft_admin_approval_ledger_detail`

### PROBABLE-084 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18615`
- Function: `intake_final_draft_workspace`

### PROBABLE-085 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18629`
- Function: `intake_final_draft_section_editor`

### PROBABLE-086 — PROBABLE_UNGATED_MUTATION_DEFECT

- Reason: Record-mutating route has no detected tenant-scope protection.
- Source: `app.py:18640`
- Function: `intake_final_draft_section_edit`

### PROBABLE-087 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18682`
- Function: `intake_final_draft_preview`

### PROBABLE-088 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18692`
- Function: `intake_final_draft_preview_docx`

### PROBABLE-089 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18722`
- Function: `intake_final_draft_version_register_intake`

### PROBABLE-090 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18731`
- Function: `intake_final_draft_version_register_detail`

### PROBABLE-091 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18777`
- Function: `intake_trust_instrument_menu`

### PROBABLE-092 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `app.py:18787`
- Function: `intake_instrument_draft_packet`

### PROBABLE-093 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `package_export/app.py:542`
- Function: `form1041_preview`

### PROBABLE-094 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `package_export/app.py:549`
- Function: `form1041_print`

### PROBABLE-095 — PROBABLE_UNGATED_MUTATION_DEFECT

- Reason: Record-mutating route has no detected tenant-scope protection.
- Source: `package_export/app.py:687`
- Function: `k1_toggle_beneficiary`

### PROBABLE-096 — PROBABLE_UNGATED_READ_DEFECT

- Reason: Record-specific route has no detected tenant-scope protection.
- Source: `package_export/app.py:722`
- Function: `k1_export_csv`


## Null-Firm Trace

- `audit_log` — `PROBABLE_DEFECT_REPAIRABLE` — inferred firms: `FIRM-001`
- `audit_log` — `PROBABLE_DEFECT_REPAIRABLE` — inferred firms: `FIRM-001`
- `audit_log` — `PROBABLE_DEFECT_REPAIRABLE` — inferred firms: `FIRM-001`
- `documents` — `PROBABLE_DEFECT_REPAIRABLE` — inferred firms: `FIRM-002`
- `documents` — `PROBABLE_DEFECT_REPAIRABLE` — inferred firms: `FIRM-002`
- `documents` — `PROBABLE_DEFECT_REPAIRABLE` — inferred firms: `FIRM-002`

## High-Review Table Trace

- `chart_of_accounts` — `PROBABLE_UNSCOPED_TABLE_DEFECT` — Tenant-sensitive table lacks firm_id and is referenced from functions without an obvious tenant-scope marker.
- `discussion_threads` — `PROBABLE_UNSCOPED_TABLE_DEFECT` — Tenant-sensitive table lacks firm_id and is referenced from functions without an obvious tenant-scope marker.
- `genealogy_records` — `PROBABLE_UNSCOPED_TABLE_DEFECT` — Tenant-sensitive table lacks firm_id and is referenced from functions without an obvious tenant-scope marker.
- `user_permission_overrides` — `PROBABLE_UNSCOPED_TABLE_DEFECT` — Tenant-sensitive table lacks firm_id and is referenced from functions without an obvious tenant-scope marker.

## Query Trace Summary

- `CONFIRMED_HIGH_RISK_UNSCOPED_WRITE`: 8
- `PROBABLE_UNSCOPED_READ_DEFECT`: 47
- `PROTECTED_BY_CALLED_HELPER`: 36
- `PROTECTED_IN_FUNCTION`: 46

## Route Trace Summary

- `PROBABLE_UNGATED_MUTATION_DEFECT`: 7
- `PROBABLE_UNGATED_READ_DEFECT`: 32
- `PROTECTED_BY_CALLED_HELPER`: 89

## Duplicate Identifier Trace

- `audit_log.entity_id` = `TR-001` — `CONFIRMED_IDENTIFIER_COLLISION_RISK`
- `audit_log.entity_id` = `admin123` — `CONFIRMED_IDENTIFIER_COLLISION_RISK`
- `intake_document_recommendations.intake_id` = `INTAKE-0005` — `CONFIRMED_IDENTIFIER_COLLISION_RISK`
- `intake_export_logs.intake_id` = `INTAKE-0005` — `CONFIRMED_IDENTIFIER_COLLISION_RISK`
- `intake_final_draft_gate_actions.intake_id` = `INTAKE-0005` — `CONFIRMED_IDENTIFIER_COLLISION_RISK`
- `intake_review_gate_actions.intake_id` = `INTAKE-0005` — `CONFIRMED_IDENTIFIER_COLLISION_RISK`
- `workspaces.owner_id` = `ADMIN_OWNER_001` — `CONFIRMED_IDENTIFIER_COLLISION_RISK`

## Control Rule

No remediation should be applied until each confirmed or probable defect is reviewed against actual runtime behavior, intended global-versus-tenant design, and existing database relationships.
