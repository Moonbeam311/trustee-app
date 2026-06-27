# UPA-1B-4 — Critical Defect Evidence Extraction

Generated: 2026-06-13T18:14:38.434265
Source: `audit\UPA-1B-3_confirmed_defect_trace_20260613_181157.json`

## Summary

- Total critical findings: **25**
- `CONFIRMED_HIGH_RISK_UNSCOPED_WRITE`: **8**
- `CONFIRMED_IDENTIFIER_COLLISION_RISK`: **7**
- `PROBABLE_DEFECT_REPAIRABLE`: **6**
- `PROBABLE_UNSCOPED_TABLE_DEFECT`: **4**

## Findings

### ISO-001 — CONFIRMED_HIGH_RISK_UNSCOPED_WRITE

- Source: `database/db.py:558`
- Function: `update_trust_fields`
- SQL action: `UPDATE`
- Reason: Tenant-table write query has no detected direct, function, or helper scope.

```sql
UPDATE trusts SET {fields} WHERE trust_id = ?
```

**Required runtime test:** Execute only against an isolated database copy. Attempt the same record mutation while logged into the other firm and verify whether any row changes.

### ISO-002 — CONFIRMED_HIGH_RISK_UNSCOPED_WRITE

- Source: `database/db.py:1253`
- Function: `update_distribution_record`
- SQL action: `UPDATE`
- Reason: Tenant-table write query has no detected direct, function, or helper scope.

```sql
UPDATE distributions SET {fields} WHERE distribution_id = ?
```

**Required runtime test:** Execute only against an isolated database copy. Attempt the same record mutation while logged into the other firm and verify whether any row changes.

### ISO-003 — CONFIRMED_HIGH_RISK_UNSCOPED_WRITE

- Source: `database/db.py:2866`
- Function: `update_app_user`
- SQL action: `UPDATE`
- Reason: Tenant-table write query has no detected direct, function, or helper scope.

```sql
UPDATE app_users SET role_name = ?, status = ? WHERE username = ?
```

**Required runtime test:** Execute only against an isolated database copy. Attempt the same record mutation while logged into the other firm and verify whether any row changes.

### ISO-004 — CONFIRMED_HIGH_RISK_UNSCOPED_WRITE

- Source: `database/db.py:2882`
- Function: `update_app_user_password`
- SQL action: `UPDATE`
- Reason: Tenant-table write query has no detected direct, function, or helper scope.

```sql
UPDATE app_users SET password_hash = ? WHERE username = ?
```

**Required runtime test:** Execute only against an isolated database copy. Attempt the same record mutation while logged into the other firm and verify whether any row changes.

### ISO-005 — CONFIRMED_HIGH_RISK_UNSCOPED_WRITE

- Source: `database/db.py:3306`
- Function: `backfill_trust_minute_certificate_ids`
- SQL action: `UPDATE`
- Reason: Tenant-table write query has no detected direct, function, or helper scope.

```sql
UPDATE trust_minutes SET certificate_id = ? WHERE minute_id = ? AND (certificate_id IS NULL OR TRIM(certificate_id) = '')
```

**Required runtime test:** Execute only against an isolated database copy. Attempt the same record mutation while logged into the other firm and verify whether any row changes.

### ISO-006 — CONFIRMED_HIGH_RISK_UNSCOPED_WRITE

- Source: `database/db.py:3439`
- Function: `update_trust_minute_execution`
- SQL action: `UPDATE`
- Reason: Tenant-table write query has no detected direct, function, or helper scope.

```sql
UPDATE trust_minutes SET trustee_1_name = ?, trustee_1_capacity = ?, trustee_1_signed_date = ?, trustee_1_signature_image = ?, trustee_2_name = ?, trustee_2_capacity = ?, trustee_2_signed_date = ?, trustee_2_signature_image = ?, trustee_3_name = ?, trustee_3_capacity = ?, trustee_3_signed_date = ?, trustee_3_signature_image = ?, certificate_id = ?, approved_at = ?, executed_at = ?, archived_at = ?, status = ?, locked = ? WHERE minute_id = ?
```

**Required runtime test:** Execute only against an isolated database copy. Attempt the same record mutation while logged into the other firm and verify whether any row changes.

### ISO-007 — CONFIRMED_HIGH_RISK_UNSCOPED_WRITE

- Source: `package_export/database/db.py:216`
- Function: `update_trust_fields`
- SQL action: `UPDATE`
- Reason: Tenant-table write query has no detected direct, function, or helper scope.

```sql
UPDATE trusts SET {fields} WHERE trust_id = ?
```

**Required runtime test:** Execute only against an isolated database copy. Attempt the same record mutation while logged into the other firm and verify whether any row changes.

### ISO-008 — CONFIRMED_HIGH_RISK_UNSCOPED_WRITE

- Source: `package_export/database/db.py:844`
- Function: `update_distribution_record`
- SQL action: `UPDATE`
- Reason: Tenant-table write query has no detected direct, function, or helper scope.

```sql
UPDATE distributions SET {fields} WHERE distribution_id = ?
```

**Required runtime test:** Execute only against an isolated database copy. Attempt the same record mutation while logged into the other firm and verify whether any row changes.

### ISO-009 — CONFIRMED_IDENTIFIER_COLLISION_RISK

- Table: `audit_log`
- Identifier: `entity_id` = `TR-001`
- Firms: `FIRM-001,FIRM-002`
- Reason: Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter.
- Unsafe references: **9**

```json
[
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
]
```

Unsafe references:

- `app.py:7550` — `trust_minute_execution_packet_pdf`
- `app.py:7819` — `trust_minute_detail`
- `app.py:7857` — `verify_certificate`
- `app.py:7995` — `audit_dashboard`
- `app.py:10146` — `audit_log_report_pdf`
- `app.py:14193` — `admin_audit_log`
- `pdf_utils.py:529` — `audit_log_report_story`
- `database/db.py:1939` — `init_audit_table`
- `database/db.py:3047` — `build_system_health_report`

**Required runtime test:** Load the repeated identifier under each firm session and confirm whether the route or helper resolves only the active firm's row.

### ISO-010 — CONFIRMED_IDENTIFIER_COLLISION_RISK

- Table: `audit_log`
- Identifier: `entity_id` = `admin123`
- Firms: `FIRM-001,FIRM-002`
- Reason: Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter.
- Unsafe references: **9**

```json
[
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
]
```

Unsafe references:

- `app.py:7550` — `trust_minute_execution_packet_pdf`
- `app.py:7819` — `trust_minute_detail`
- `app.py:7857` — `verify_certificate`
- `app.py:7995` — `audit_dashboard`
- `app.py:10146` — `audit_log_report_pdf`
- `app.py:14193` — `admin_audit_log`
- `pdf_utils.py:529` — `audit_log_report_story`
- `database/db.py:1939` — `init_audit_table`
- `database/db.py:3047` — `build_system_health_report`

**Required runtime test:** Load the repeated identifier under each firm session and confirm whether the route or helper resolves only the active firm's row.

### ISO-011 — CONFIRMED_IDENTIFIER_COLLISION_RISK

- Table: `intake_document_recommendations`
- Identifier: `intake_id` = `INTAKE-0005`
- Firms: `FIRM-001,FIRM-002`
- Reason: Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter.
- Unsafe references: **8**

```json
[
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
]
```

Unsafe references:

- `app.py:18060` — `intake_document_recommendations`
- `app.py:18085` — `intake_update_recommendation_status`
- `app.py:18101` — `intake_workflow_launch_prep`
- `app.py:18122` — `intake_workflow_bridge`
- `app.py:18204` — `intake_workflow_bridge_summary`
- `services/services_intake.py:4050` — `list_saved_document_recommendations`
- `services/services_intake.py:4435` — `update_document_recommendation_status`
- `services/services_intake.py:4467` — `get_document_recommendation`

**Required runtime test:** Load the repeated identifier under each firm session and confirm whether the route or helper resolves only the active firm's row.

### ISO-012 — CONFIRMED_IDENTIFIER_COLLISION_RISK

- Table: `intake_export_logs`
- Identifier: `intake_id` = `INTAKE-0005`
- Firms: `FIRM-001,FIRM-002`
- Reason: Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter.
- Unsafe references: **5**

```json
[
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
]
```

Unsafe references:

- `app.py:17905` — `intake_export_prep`
- `app.py:18034` — `intake_export_history_detail`
- `services/services_intake.py:2976` — `list_intake_export_logs`
- `services/services_intake.py:3101` — `get_next_export_version`
- `services/services_intake.py:3215` — `list_intake_export_logs_versioned`

**Required runtime test:** Load the repeated identifier under each firm session and confirm whether the route or helper resolves only the active firm's row.

### ISO-013 — CONFIRMED_IDENTIFIER_COLLISION_RISK

- Table: `intake_final_draft_gate_actions`
- Identifier: `intake_id` = `INTAKE-0005`
- Firms: `FIRM-001,FIRM-002`
- Reason: Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter.
- Unsafe references: **1**

```json
[
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
]
```

Unsafe references:

- `services/services_intake.py:7326` — `list_final_draft_resolution_actions`

**Required runtime test:** Load the repeated identifier under each firm session and confirm whether the route or helper resolves only the active firm's row.

### ISO-014 — CONFIRMED_IDENTIFIER_COLLISION_RISK

- Table: `intake_review_gate_actions`
- Identifier: `intake_id` = `INTAKE-0005`
- Firms: `FIRM-001,FIRM-002`
- Reason: Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter.
- Unsafe references: **1**

```json
[
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
]
```

Unsafe references:

- `services/services_intake.py:6789` — `list_review_gate_actions`

**Required runtime test:** Load the repeated identifier under each firm session and confirm whether the route or helper resolves only the active firm's row.

### ISO-015 — CONFIRMED_IDENTIFIER_COLLISION_RISK

- Table: `workspaces`
- Identifier: `owner_id` = `ADMIN_OWNER_001`
- Firms: `FIRM-001,FIRM-002`
- Reason: Identifier is reused across firms and at least one lookup reference lacks an obvious firm filter.
- Unsafe references: **2**

```json
[
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
]
```

Unsafe references:

- `app.py:10528` — `discussion_new`
- `app.py:10888` — `document_generate`

**Required runtime test:** Load the repeated identifier under each firm session and confirm whether the route or helper resolves only the active firm's row.

### ISO-016 — PROBABLE_DEFECT_REPAIRABLE

- Table: `audit_log`
- Reason: Null-firm record has one unambiguous tenant owner through related scoped records.
- Inferred firms: `FIRM-001`

```json
{
  "id": 114,
  "entity_type": "auth",
  "entity_id": "trustee",
  "action": "login_success",
  "note": "User logged in successfully",
  "created_at": "2026-04-29 16:42:03",
  "previous_hash": "f5d247f6a6faaa52f50c060bdbb8bda2760dca7b62663080257f80f7872dc89c",
  "entry_hash": "58772444f918fa176739034f73f4452fd1bb7c7740d274873ec09c760223c12e",
  "hash_algorithm": "sha256",
  "firm_id": null
}
```

**Required review:** Verify inferred firm ownership from authoritative parent records before preparing any UPDATE statement.

### ISO-017 — PROBABLE_DEFECT_REPAIRABLE

- Table: `audit_log`
- Reason: Null-firm record has one unambiguous tenant owner through related scoped records.
- Inferred firms: `FIRM-001`

```json
{
  "id": 115,
  "entity_type": "auth",
  "entity_id": "trustee",
  "action": "login_success",
  "note": "User logged in successfully",
  "created_at": "2026-04-29 16:43:36",
  "previous_hash": "58772444f918fa176739034f73f4452fd1bb7c7740d274873ec09c760223c12e",
  "entry_hash": "c3754a2db8fb998685c0bfdfcdb922c26ce38e2475ee592434150fddc9edbe6b",
  "hash_algorithm": "sha256",
  "firm_id": null
}
```

**Required review:** Verify inferred firm ownership from authoritative parent records before preparing any UPDATE statement.

### ISO-018 — PROBABLE_DEFECT_REPAIRABLE

- Table: `audit_log`
- Reason: Null-firm record has one unambiguous tenant owner through related scoped records.
- Inferred firms: `FIRM-001`

```json
{
  "id": 116,
  "entity_type": "auth",
  "entity_id": "admin",
  "action": "login_success",
  "note": "User logged in successfully",
  "created_at": "2026-04-29 16:43:58",
  "previous_hash": "c3754a2db8fb998685c0bfdfcdb922c26ce38e2475ee592434150fddc9edbe6b",
  "entry_hash": "22ee34aafe54ee2be4d0e5819b2cca5d7a30345c66b07a07835a2add97568382",
  "hash_algorithm": "sha256",
  "firm_id": null
}
```

**Required review:** Verify inferred firm ownership from authoritative parent records before preparing any UPDATE statement.

### ISO-019 — PROBABLE_DEFECT_REPAIRABLE

- Table: `documents`
- Reason: Null-firm record has one unambiguous tenant owner through related scoped records.
- Inferred firms: `FIRM-002`

```json
{
  "document_id": "DOC-001",
  "trust_id": "TR-022",
  "property_id": "PR-001",
  "account_id": "",
  "document_category": "property_record",
  "document_title": "PR-001 Supporting Evidence for PR-001",
  "notes": "Test evidence upload for AC-1 readiness recovery.",
  "original_filename": "PR-001_Continuity_Custody_Log (2).pdf",
  "stored_filename": "DOC-001_PR-001_Continuity_Custody_Log_2.pdf",
  "file_path": "C:\\Users\\LunaMishoe\\Desktop\\trustee-app-clean\\uploads\\DOC-001_PR-001_Continuity_Custody_Log_2.pdf",
  "owner_id": null,
  "firm_id": null
}
```

**Required review:** Verify inferred firm ownership from authoritative parent records before preparing any UPDATE statement.

### ISO-020 — PROBABLE_DEFECT_REPAIRABLE

- Table: `documents`
- Reason: Null-firm record has one unambiguous tenant owner through related scoped records.
- Inferred firms: `FIRM-002`

```json
{
  "document_id": "DOC-002",
  "trust_id": "TR-022",
  "property_id": "PR-001",
  "account_id": "",
  "document_category": "property_record",
  "document_title": "Supporting Evidence for PR-001",
  "notes": "",
  "original_filename": "Continuity_Asset_Dashboard_Report (3).pdf",
  "stored_filename": "DOC-002_Continuity_Asset_Dashboard_Report_3.pdf",
  "file_path": "C:\\Users\\LunaMishoe\\Desktop\\trustee-app-clean\\uploads\\DOC-002_Continuity_Asset_Dashboard_Report_3.pdf",
  "owner_id": null,
  "firm_id": null
}
```

**Required review:** Verify inferred firm ownership from authoritative parent records before preparing any UPDATE statement.

### ISO-021 — PROBABLE_DEFECT_REPAIRABLE

- Table: `documents`
- Reason: Null-firm record has one unambiguous tenant owner through related scoped records.
- Inferred firms: `FIRM-002`

```json
{
  "document_id": "DOC-003",
  "trust_id": "TR-022",
  "property_id": "PR-001",
  "account_id": "",
  "document_category": "property_record",
  "document_title": "Supporting Evidence for PR-001",
  "notes": "Test evidence upload for AC-1 readiness recovery.",
  "original_filename": "PR-001_Continuity_Custody_Log (2).pdf",
  "stored_filename": "DOC-003_PR-001_Continuity_Custody_Log_2.pdf",
  "file_path": "C:\\Users\\LunaMishoe\\Desktop\\trustee-app-clean\\uploads\\DOC-003_PR-001_Continuity_Custody_Log_2.pdf",
  "owner_id": null,
  "firm_id": null
}
```

**Required review:** Verify inferred firm ownership from authoritative parent records before preparing any UPDATE statement.

### ISO-022 — PROBABLE_UNSCOPED_TABLE_DEFECT

- Table: `chart_of_accounts`
- Reason: Tenant-sensitive table lacks firm_id and is referenced from functions without an obvious tenant-scope marker.

**Required review:** Determine whether this table is global, directly tenant-scoped, or tenant-scoped through a mandatory parent relation.

### ISO-023 — PROBABLE_UNSCOPED_TABLE_DEFECT

- Table: `discussion_threads`
- Reason: Tenant-sensitive table lacks firm_id and is referenced from functions without an obvious tenant-scope marker.

**Required review:** Determine whether this table is global, directly tenant-scoped, or tenant-scoped through a mandatory parent relation.

### ISO-024 — PROBABLE_UNSCOPED_TABLE_DEFECT

- Table: `genealogy_records`
- Reason: Tenant-sensitive table lacks firm_id and is referenced from functions without an obvious tenant-scope marker.

**Required review:** Determine whether this table is global, directly tenant-scoped, or tenant-scoped through a mandatory parent relation.

### ISO-025 — PROBABLE_UNSCOPED_TABLE_DEFECT

- Table: `user_permission_overrides`
- Reason: Tenant-sensitive table lacks firm_id and is referenced from functions without an obvious tenant-scope marker.

**Required review:** Determine whether this table is global, directly tenant-scoped, or tenant-scoped through a mandatory parent relation.

## Audit Control

The word confirmed in the source classification means the static scanner found no visible scope control. It does not by itself prove that a cross-firm request succeeds at runtime.
