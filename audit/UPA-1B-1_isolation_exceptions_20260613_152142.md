# UPA-1B-1 — Isolation Exceptions Forensic Audit

Generated: 2026-06-13T15:21:44.166141

## Summary

- Tables: **88**
- Tenant Scoped Tables: **68**
- Scope Review Tables: **20**
- Null Firm Records: **6**
- Cross Firm Duplicate Groups: **7**
- Hardcoded Firm References: **166**
- Unscoped Query Candidates: **206**
- Route Scope Candidates: **136**

## Null or Blank Firm Records

### `audit_log`

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
### `audit_log`

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
### `audit_log`

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
### `documents`

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
### `documents`

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
### `documents`

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

## Tables Requiring Scope Classification

- `chart_of_accounts` — tenant_review_required — 0 rows
- `decision_rules` — probable_global — 5 rows
- `discussion_messages` — tenant_review_required — 5 rows
- `discussion_threads` — tenant_review_required — 5 rows
- `document_templates` — probable_global — 3 rows
- `genealogy_records` — tenant_review_required — 0 rows
- `intake_module_ledger` — probable_global — 16 rows
- `learning_articles` — probable_global — 9 rows
- `permissions` — probable_global — 15 rows
- `role_permissions` — probable_global — 23873 rows
- `tax_form_guides` — probable_global — 10 rows
- `transfer_actions` — tenant_review_required — 95 rows
- `transfer_records` — tenant_review_required — 11 rows
- `transfer_support_docs` — tenant_review_required — 0 rows
- `trust_article_assignments` — tenant_review_required — 3 rows
- `trust_article_conditions` — probable_global — 0 rows
- `trust_articles` — probable_global — 3 rows
- `trust_template_types` — probable_global — 0 rows
- `tutorial_videos` — probable_global — 5 rows
- `user_permission_overrides` — tenant_review_required — 1 rows

## Cross-Firm Duplicate Identifier Groups

### `audit_log.entity_id` = `TR-001`

- Firms: `FIRM-001,FIRM-002`
- Rows: 16

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
### `audit_log.entity_id` = `admin123`

- Firms: `FIRM-001,FIRM-002`
- Rows: 75

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
### `intake_document_recommendations.intake_id` = `INTAKE-0005`

- Firms: `FIRM-001,FIRM-002`
- Rows: 15

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
### `intake_export_logs.intake_id` = `INTAKE-0005`

- Firms: `FIRM-001,FIRM-002`
- Rows: 10

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
### `intake_final_draft_gate_actions.intake_id` = `INTAKE-0005`

- Firms: `FIRM-001,FIRM-002`
- Rows: 6

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
### `intake_review_gate_actions.intake_id` = `INTAKE-0005`

- Firms: `FIRM-001,FIRM-002`
- Rows: 2

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
### `workspaces.owner_id` = `ADMIN_OWNER_001`

- Firms: `FIRM-001,FIRM-002`
- Rows: 7

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

## Hard-Coded Firm References

- `app.py:338` — `FIRM-002` — password = os.getenv("HOSTED_BOOTSTRAP_PASSWORD", "").strip() firm_id = os.getenv("HOSTED_BOOTSTRAP_FIRM_ID", "FIRM-002").strip() if not username or not password or not firm_id: print("⚠️ Hosted startup self-heal skipped: missing username/password/firm_id.") return try:
- `app.py:551` — `FIRM-002` — nt("⚠️ Hosted startup self-heal wrapper failed:", e) def run_hosted_test_trust_seed(): """ Permanent hosted FIRM-002 test trust seed. Runs only when ENSURE_HOSTED_TEST_TRUST=1. Provides one stable hosted trust record for Report Center, firewall testing, and Trust Summary PDF validat
- `app.py:562` — `FIRM-002` — RE_HOSTED_TEST_TRUST") != "1": return import sqlite3 firm_id = os.getenv("HOSTED_BOOTSTRAP_FIRM_ID", "FIRM-002").strip() or "FIRM-002" username = os.getenv("HOSTED_BOOTSTRAP_USERNAME", "admin123").strip() or "admin123" try: DB_PATH.parent.mkdir(parents=True, exist_ok=True)
- `app.py:562` — `FIRM-002` — != "1": return import sqlite3 firm_id = os.getenv("HOSTED_BOOTSTRAP_FIRM_ID", "FIRM-002").strip() or "FIRM-002" username = os.getenv("HOSTED_BOOTSTRAP_USERNAME", "admin123").strip() or "admin123" try: DB_PATH.parent.mkdir(parents=True, exist_ok=True) conn = sqlite
- `app.py:744` — `FIRM-002` — print("⚠️ Hosted test trust seed wrapper failed:", e) def run_hosted_portfolio_seed(): """ Permanent hosted FIRM-002 portfolio seed. Seeds one property, account, document, and ledger entry for TR-001 under FIRM-002. """ if os.getenv("ENSURE_HOSTED_PORTFOLIO_SEED") != "1":
- `app.py:747` — `FIRM-002` — anent hosted FIRM-002 portfolio seed. Seeds one property, account, document, and ledger entry for TR-001 under FIRM-002. """ if os.getenv("ENSURE_HOSTED_PORTFOLIO_SEED") != "1": return import sqlite3 from datetime import datetime trust_id = "TR-001" firm_id = "FIRM
- `app.py:756` — `FIRM-002` — ") != "1": return import sqlite3 from datetime import datetime trust_id = "TR-001" firm_id = "FIRM-002" owner_id = "admin123" try: DB_PATH.parent.mkdir(parents=True, exist_ok=True) conn = sqlite3.connect(DB_PATH) conn.row_factory = sqlite3.Row
- `app.py:1006` — `FIRM-001` — ts = get_all_trusts() if is_master_admin(): return trusts active_firm_id = session.get("firm_id") or "FIRM-001" def trust_firm_id(trust): try: return trust.get("firm_id") or trust.get("firm") or "FIRM-001" except Exception: try:
- `app.py:1010` — `FIRM-001` — "FIRM-001" def trust_firm_id(trust): try: return trust.get("firm_id") or trust.get("firm") or "FIRM-001" except Exception: try: return getattr(trust, "firm_id", None) or getattr(trust, "firm", None) or "FIRM-001" except Exception:
- `app.py:1013` — `FIRM-001` — Exception: try: return getattr(trust, "firm_id", None) or getattr(trust, "firm", None) or "FIRM-001" except Exception: return "FIRM-001" # Tenant isolation rule: # A non-master Admin may see all trusts inside the active firm only. # Trust
- `app.py:1015` — `FIRM-001` — t, "firm_id", None) or getattr(trust, "firm", None) or "FIRM-001" except Exception: return "FIRM-001" # Tenant isolation rule: # A non-master Admin may see all trusts inside the active firm only. # Trustee/Viewer visibility remains assignment-based. if session.ge
- `app.py:1051` — `FIRM-001` — n.get("role") == "Admin": trust = get_trust_by_id(trust_id) active_firm_id = session.get("firm_id") or "FIRM-001" if not trust: return False try: trust_firm_id = trust.get("firm_id") or trust.get("firm") or "FIRM-001" except Exception:
- `app.py:1055` — `FIRM-001` — trust: return False try: trust_firm_id = trust.get("firm_id") or trust.get("firm") or "FIRM-001" except Exception: trust_firm_id = getattr(trust, "firm_id", None) or getattr(trust, "firm", None) or "FIRM-001" return trust_firm_id == active_firm_id
- `app.py:1057` — `FIRM-001` — except Exception: trust_firm_id = getattr(trust, "firm_id", None) or getattr(trust, "firm", None) or "FIRM-001" return trust_firm_id == active_firm_id role_rows = get_roles_by_trust_id(trust_id) for row in role_rows: full_name = (row.get("full_name") or "").strip()
- `app.py:1168` — `FIRM-001` — , e) return "" def get_transfer_for_active_firm_or_404(transfer_id): firm_id = session.get("firm_id") or "FIRM-001" transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404() if transfer.firm_id != firm_id: log_change( "security", trans
- `app.py:6636` — `FIRM-001` — icy", policy_key, "toggle", f"Admin {session.get('username')} for firm {session.get('firm_id', 'FIRM-001')} set {policy_key} to {policy[policy_key]}" ) flash(f"System policy updated: {policy_key} = {policy[policy_key]}") return redirect(url_for("admin_index")) @app.route
- `app.py:8607` — `FIRM-001` — .close() return dict(row) if row else None def get_generated_documents(): firm_id = session.get("firm_id") or "FIRM-001" conn = _learning_conn() rows = conn.execute(""" SELECT * FROM generated_documents WHERE owner_id = ? AND firm_id = ? ORDER BY created_at
- `app.py:8619` — `FIRM-001` — ict(r) for r in rows] def get_generated_documents_by_workspace(workspace_id): firm_id = session.get("firm_id") or "FIRM-001" conn = _learning_conn() rows = conn.execute(""" SELECT * FROM generated_documents WHERE workspace_id = ? AND owner_id = ? AND firm_id
- `app.py:8632` — `FIRM-001` — return [dict(r) for r in rows] def get_generated_document_by_id(document_id): firm_id = session.get("firm_id") or "FIRM-001" conn = _learning_conn() row = conn.execute(""" SELECT * FROM generated_documents WHERE document_id = ? AND firm_id = ? """, (document_id, fi
- `app.py:8644` — `FIRM-001` — e_generated_document(payload): payload = dict(payload) payload.setdefault("firm_id", session.get("firm_id") or "FIRM-001") conn = _learning_conn() conn.execute(""" INSERT INTO generated_documents ( document_id, workspace_id, trust_id, template_id, title, content, status,
- `app.py:8672` — `FIRM-001` — + key + "}}", value or "") return content def get_all_execution_tasks(): firm_id = session.get("firm_id") or "FIRM-001" conn = _learning_conn() rows = conn.execute(""" SELECT * FROM execution_tasks WHERE owner_id = ? AND firm_id = ? ORDER BY created_at DES
- `app.py:8684` — `FIRM-001` — n [dict(r) for r in rows] def get_execution_tasks_by_workspace(workspace_id): firm_id = session.get("firm_id") or "FIRM-001" conn = _learning_conn() rows = conn.execute(""" SELECT * FROM execution_tasks WHERE workspace_id = ? AND owner_id = ? AND firm_id = ?
- `app.py:8697` — `FIRM-001` — e() return [dict(r) for r in rows] def get_execution_task_by_id(task_id): firm_id = session.get("firm_id") or "FIRM-001" conn = _learning_conn() row = conn.execute(""" SELECT * FROM execution_tasks WHERE task_id = ? AND firm_id = ? """, (task_id, firm_id)).fetc
- `app.py:8709` — `FIRM-001` — reate_execution_task(payload): payload = dict(payload) payload.setdefault("firm_id", session.get("firm_id") or "FIRM-001") conn = _learning_conn() conn.execute(""" INSERT INTO execution_tasks ( task_id, workspace_id, trust_id, title, task_type, description, r
- `app.py:8738` — `FIRM-001` — .commit() conn.close() def update_execution_task_status(task_id, status): firm_id = session.get("firm_id") or "FIRM-001" conn = _learning_conn() conn.execute(""" UPDATE execution_tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE task_id = ? AND fir
- `app.py:8883` — `FIRM-001` — uestions", "video_linked_discussion", ] def get_all_workspaces(): firm_id = session.get("firm_id") or "FIRM-001" conn = _learning_conn() rows = conn.execute(""" SELECT * FROM workspaces WHERE firm_id = ? ORDER BY created_at DESC, title """, (firm_id,)).fe
- `app.py:8894` — `FIRM-001` — e() return [dict(r) for r in rows] def get_workspace_by_id(workspace_id): firm_id = session.get("firm_id") or "FIRM-001" conn = _learning_conn() row = conn.execute(""" SELECT * FROM workspaces WHERE workspace_id = ? AND firm_id = ? """, (workspace_id, firm_id))
- `app.py:8906` — `FIRM-001` — def create_workspace(payload): payload = dict(payload) payload.setdefault("firm_id", session.get("firm_id") or "FIRM-001") payload.setdefault("owner_id", get_current_owner()) conn = _learning_conn() conn.execute(""" INSERT INTO workspaces ( workspace_id, title, works
- `app.py:8929` — `FIRM-001` — conn.commit() conn.close() def update_workspace(workspace_id, payload): firm_id = session.get("firm_id") or "FIRM-001" conn = _learning_conn() conn.execute(""" UPDATE workspaces SET title = ?, workspace_type = ?, trust_type_focus = ?, pu
- `app.py:8956` — `FIRM-001` — )) conn.commit() conn.close() def get_workspace_notes(workspace_id): firm_id = session.get("firm_id") or "FIRM-001" conn = _learning_conn() rows = conn.execute(""" SELECT * FROM workspace_notes WHERE workspace_id = ? AND firm_id = ? ORDER BY section_na
- `app.py:8969` — `FIRM-001` — reate_workspace_note(payload): payload = dict(payload) payload.setdefault("firm_id", session.get("firm_id") or "FIRM-001") conn = _learning_conn() conn.execute(""" INSERT INTO workspace_notes ( note_id, workspace_id, section_name, content, firm_id ) VALUES (?, ?,
- `app.py:10053` — `FIRM-002` — FROM {table_name} WHERE trust_id = 'TR-001' AND firm_id = 'FIRM-002' """) row = cur.fetchone() count = row["count"] if row else 0 add_check("Portfolio", label, count >= 1, f"{count} r
- `app.py:11448` — `FIRM-001` — e_handoff_table, ensure_transfer_archive_handoff_correction_table, ) firm_id = session.get("firm_id", "FIRM-001") active_export_filter = request.args.get("export_filter", "all") ensure_transfer_archive_handoff_table() ensure_transfer_archive_handoff_correction_table() conn
- `app.py:11680` — `FIRM-001` — e_handoff_table, ensure_transfer_archive_handoff_correction_table, ) firm_id = session.get("firm_id", "FIRM-001") ensure_transfer_archive_handoff_table() ensure_transfer_archive_handoff_correction_table() conn = get_connection() conn.row_factory = sqlite3.Row cur = conn
- `app.py:11891` — `FIRM-001` — try: import sqlite3 from database.db import get_connection firm_id = session.get("firm_id", "FIRM-001") conn = get_connection() conn.row_factory = sqlite3.Row cur = conn.cursor() cur.execute("PRAGMA table_info(trust_minutes)") minute_cols =
- `app.py:11966` — `FIRM-001` — ble, ensure_transfer_archive_handoff_correction_table, ) firm_id = session.get("firm_id", "FIRM-001") ensure_transfer_archive_handoff_table() ensure_transfer_archive_handoff_correction_table() conn = get_connection() conn.row_factory = sqlite3.Ro
- `app.py:12197` — `FIRM-001` — trust_id=str(trust_id), transfer_id=generate_transfer_id(), firm_id=session.get("firm_id") or "FIRM-001", mode=mode, status="draft", current_capacity=current_capacity, created_by=session.get("username") or "unknown", )
- `app.py:12660` — `FIRM-001` — nsfer_intake_id = getattr(transfer, "intake_id", None) or "" transfer_firm_id = session.get("firm_id", "FIRM-001") if transfer_intake_id: upsert_intake_orchestration_state( intake_id=transfer_intake_id, firm
- `app.py:12884` — `FIRM-001` — e_handoff_table, ensure_transfer_archive_handoff_correction_table, ) firm_id = session.get("firm_id", "FIRM-001") ensure_transfer_archive_handoff_table() ensure_transfer_archive_handoff_correction_table() conn = get_connection() conn.row_factory = sqlite3.Row cur = conn
- `app.py:12945` — `FIRM-001` — e_handoff_table, ensure_transfer_archive_handoff_correction_table, ) firm_id = session.get("firm_id", "FIRM-001") ensure_transfer_archive_handoff_table() ensure_transfer_archive_handoff_correction_table() conn = get_connection() conn.row_factory = sqlite3.Row cur = conn
- `app.py:13046` — `FIRM-001` — from database.db import get_connection, ensure_transfer_archive_handoff_table firm_id = session.get("firm_id", "FIRM-001") ensure_transfer_archive_handoff_table() conn = get_connection() conn.row_factory = sqlite3.Row cur = conn.cursor() cur.execute(""" SELECT *
- `app.py:13119` — `FIRM-001` — e_handoff_table, ensure_transfer_archive_handoff_correction_table, ) firm_id = session.get("firm_id", "FIRM-001") generated_by = session.get("username") or session.get("user_email") or "System User" generated_at = datetime.utcnow().isoformat() + " UTC" package_scope = "Transfer
- `app.py:13467` — `FIRM-001` — e_handoff_table, ensure_transfer_archive_handoff_correction_table, ) firm_id = session.get("firm_id", "FIRM-001") generated_by = session.get("username") or session.get("user_email") or "System User" generated_at = datetime.utcnow().isoformat() + " UTC" export_scope = "Transfer A
- `app.py:13648` — `FIRM-001` — e_handoff_table, ensure_transfer_archive_handoff_correction_table, ) firm_id = session.get("firm_id", "FIRM-001") ensure_transfer_archive_handoff_table() ensure_transfer_archive_handoff_correction_table() conn = get_connection() conn.row_factory = sqlite3.Row cur = conn
- `app.py:13827` — `FIRM-001` — e_handoff_table, ensure_transfer_archive_handoff_correction_table, ) firm_id = session.get("firm_id", "FIRM-001") ensure_transfer_archive_handoff_table() ensure_transfer_archive_handoff_correction_table() conn = get_connection() conn.row_factory = sqlite3.Row cur = conn
- `app.py:13930` — `FIRM-001` — from database.db import get_connection, ensure_transfer_archive_handoff_table firm_id = session.get("firm_id", "FIRM-001") ensure_transfer_archive_handoff_table() transfer_ledger_records = [ row for row in get_ledger_entries_by_trust_id(transfer.trust_id) if transfer.transfe
- `app.py:14095` — `FIRM-001` — try: import sqlite3 from database.db import get_connection firm_id = session.get("firm_id", "FIRM-001") minute_like = f"%{transfer.transfer_id}%" conn = get_connection() conn.row_factory = sqlite3.Row cur = conn.cursor() cur.execute("PRAGM
- `app.py:14241` — `FIRM-001` — user["username"] session["firm_id"] = user["firm_id"] if "firm_id" in user.keys() and user["firm_id"] else "FIRM-001" session["last_activity"] = datetime.now(UTC).timestamp() login_attempts.pop(username, None) log_change("auth", username, "login_success", "Us
- `app.py:14373` — `FIRM-001` — ated for username: {username}" @app.route("/resume") def resume_process(): firm_id = session.get("firm_id") or "FIRM-001" transfer = ( Transfer.query .filter(Transfer.status != "completed") .filter(Transfer.firm_id == firm_id) .order_by(Transfer.id.desc())
- `app.py:14483` — `FIRM-002` — password = os.getenv("HOSTED_BOOTSTRAP_PASSWORD", "").strip() firm_id = os.getenv("HOSTED_BOOTSTRAP_FIRM_ID", "FIRM-002").strip() if not username or not password: return render_template( "access_denied.html", reason="HOSTED_BOOTSTRAP_USERNAME and HOSTED_BOOTSTRA
- `app.py:14565` — `FIRM-002` — password = os.getenv("HOSTED_BOOTSTRAP_PASSWORD", "").strip() firm_id = os.getenv("HOSTED_BOOTSTRAP_FIRM_ID", "FIRM-002").strip() if not username or not password: return render_template( "access_denied.html", reason="HOSTED_BOOTSTRAP_USERNAME and HOSTED_BOOTSTRA
- `app.py:14784` — `FIRM-002` — password = os.getenv("HOSTED_BOOTSTRAP_PASSWORD", "").strip() firm_id = os.getenv("HOSTED_BOOTSTRAP_FIRM_ID", "FIRM-002").strip() output = [] output.append(f"DB_PATH={DB_PATH}") output.append(f"USERNAME={username!r}") output.append(f"PASSWORD_PRESENT={bool(password)}") output.a
- `app.py:15392` — `FIRM-001` — ?, ?, ?, ?, ?, ?, ?, ?) """, ( asset_id, intake_id, session.get("firm_id", "FIRM-001"), request.form.get("asset_category"), request.form.get("asset_name"), request.form.get("ownership_type"), request.form.get("estima
- `app.py:15408` — `FIRM-001` — upsert_intake_orchestration_state( intake_id=intake_id, firm_id=session.get("firm_id", "FIRM-001"), asset_status="in_progress", overall_stage="asset_inventory_started", readiness_label="Partially Ready", next_recommended_action=
- `app.py:15502` — `FIRM-001` — ?, ?, ?, ?, ?, ?, ?) """, ( document_id, intake_id, session.get("firm_id", "FIRM-001"), request.form.get("document_category"), request.form.get("document_name"), file_name, request.form.get("notes") ))
- `app.py:15513` — `FIRM-001` — upsert_intake_orchestration_state( intake_id=intake_id, firm_id=session.get("firm_id", "FIRM-001"), document_status="in_progress", overall_stage="document_gathering_started", readiness_label="Review In Progress", next_recommende
- `app.py:15554` — `FIRM-001` — build_intake_readiness_summary, upsert_intake_orchestration_state ) firm_id = session.get("firm_id", "FIRM-001") summary = build_intake_readiness_summary(intake_id, firm_id) upsert_intake_orchestration_state( intake_id=intake_id, firm_id=firm_id, review_sta
- `app.py:15593` — `FIRM-001` — build_intake_readiness_summary, upsert_intake_orchestration_state ) firm_id = session.get("firm_id", "FIRM-001") ensure_deep_review_table() summary = build_intake_readiness_summary(intake_id, firm_id) conn = get_connection() conn.row_factory = sqlite3.Row cur = conn.c
- `app.py:15685` — `FIRM-001` — build_intake_readiness_summary, upsert_intake_orchestration_state ) firm_id = session.get("firm_id", "FIRM-001") ensure_drafting_prep_gate_table() summary = build_intake_readiness_summary(intake_id, firm_id) conn = get_connection() conn.row_factory = sqlite3.Row cur =
- `app.py:15820` — `FIRM-001` — ?, ?, ?, ?, ?) """, ( draft_session_id, intake_id, session.get("firm_id", "FIRM-001"), document_type, "initialized", "guided", session.get("username", "unknown"), request.form.get("launch_notes")
- `app.py:15832` — `FIRM-001` — upsert_intake_orchestration_state( intake_id=intake_id, firm_id=session.get("firm_id", "FIRM-001"), drafting_status="draft_session_active", overall_stage="drafting_active", readiness_label="Drafting Active", next_recommended_act
- `app.py:15959` — `FIRM-001` — ", ( workspace_id, draft_session_id, intake_id, session.get("firm_id", "FIRM-001"), draft_session["document_type"], intake["primary_full_name"], intake["trustee_candidate"], intake["successor_trustee_candidate"],
- `app.py:15975` — `FIRM-001` — upsert_intake_orchestration_state( intake_id=intake_id, firm_id=session.get("firm_id", "FIRM-001"), drafting_status="workspace_active", overall_stage="guided_drafting_workspace", readiness_label="Draft Workspace Active", next_re
- `app.py:16046` — `FIRM-001` — _id = workspace["intake_id"] draft_session_id = workspace["draft_session_id"] firm_id = session.get("firm_id", "FIRM-001") default_bindings = { "primary_person": workspace["primary_person"], "trustee_candidate": workspace["trustee_candidate"], "successor_trustee_candidat
- `app.py:16143` — `FIRM-001` — ensure_variable_binding_table, upsert_intake_orchestration_state ) firm_id = session.get("firm_id", "FIRM-001") ensure_dynamic_draft_preview_table() ensure_variable_binding_table() conn = get_connection() conn.row_factory = sqlite3.Row cur = conn.cursor() cur.ex
- `app.py:16309` — `FIRM-001` — ure_dynamic_draft_preview_table, upsert_intake_orchestration_state ) firm_id = session.get("firm_id", "FIRM-001") ensure_section_review_gate_table() ensure_dynamic_draft_preview_table() conn = get_connection() conn.row_factory = sqlite3.Row cur = conn.cursor() cur
- `app.py:16438` — `FIRM-001` — nsure_section_review_gate_table, upsert_intake_orchestration_state ) firm_id = session.get("firm_id", "FIRM-001") ensure_controlled_export_prep_table() ensure_section_review_gate_table() conn = get_connection() conn.row_factory = sqlite3.Row cur = conn.cursor() cu
- `app.py:16587` — `FIRM-001` — re_controlled_export_prep_table, upsert_intake_orchestration_state ) firm_id = session.get("firm_id", "FIRM-001") ensure_controlled_docx_export_table() ensure_controlled_export_prep_table() conn = get_connection() conn.row_factory = sqlite3.Row cur = conn.cursor()
- `app.py:16772` — `FIRM-001` — sqlite3 from pathlib import Path from database.db import get_connection firm_id = session.get("firm_id", "FIRM-001") conn = get_connection() conn.row_factory = sqlite3.Row cur = conn.cursor() cur.execute(""" SELECT * FROM controlled_docx_exports WHERE
- `app.py:16824` — `FIRM-001` — re_docx_verification_gate_table, upsert_intake_orchestration_state ) firm_id = session.get("firm_id", "FIRM-001") ensure_docx_verification_gate_table() conn = get_connection() conn.row_factory = sqlite3.Row cur = conn.cursor() cur.execute(""" SELECT * F
- `app.py:16965` — `FIRM-001` — re_docx_verification_gate_table, upsert_intake_orchestration_state ) firm_id = session.get("firm_id", "FIRM-001") ensure_controlled_pdf_export_table() ensure_docx_verification_gate_table() conn = get_connection() conn.row_factory = sqlite3.Row cur = conn.cursor()
- `app.py:17156` — `FIRM-001` — sqlite3 from pathlib import Path from database.db import get_connection firm_id = session.get("firm_id", "FIRM-001") conn = get_connection() conn.row_factory = sqlite3.Row cur = conn.cursor() cur.execute(""" SELECT * FROM controlled_pdf_exports WHERE p
- `app.py:17208` — `FIRM-001` — re_pdf_execution_approval_table, upsert_intake_orchestration_state ) firm_id = session.get("firm_id", "FIRM-001") ensure_pdf_execution_approval_table() conn = get_connection() conn.row_factory = sqlite3.Row cur = conn.cursor() cur.execute(""" SELECT * F
- `app.py:17350` — `FIRM-001` — re_pdf_execution_approval_table, upsert_intake_orchestration_state ) firm_id = session.get("firm_id", "FIRM-001") ensure_execution_packet_prep_table() ensure_pdf_execution_approval_table() conn = get_connection() conn.row_factory = sqlite3.Row cur = conn.cursor()
- `app.py:17517` — `FIRM-001` — ure_execution_packet_prep_table, upsert_intake_orchestration_state ) firm_id = session.get("firm_id", "FIRM-001") ensure_execution_event_log_table() ensure_execution_packet_prep_table() conn = get_connection() conn.row_factory = sqlite3.Row cur = conn.cursor() cur
- `app.py:17707` — `FIRM-001` — nsure_execution_event_log_table, upsert_intake_orchestration_state ) firm_id = session.get("firm_id", "FIRM-001") ensure_final_record_archive_table() ensure_execution_event_log_table() conn = get_connection() conn.row_factory = sqlite3.Row cur = conn.cursor() cur.
- `app.py:17835` — `FIRM-001` — ect(url_for("login")) from database.db import build_lifecycle_master_ledger firm_id = session.get("firm_id", "FIRM-001") ledger = build_lifecycle_master_ledger(intake_id, firm_id) if not ledger["identity"]: flash("Lifecycle ledger could not find the intake record.", "warning")
- `app.py:18825` — `FIRM-001` — (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) """, ( intake_id, session.get("firm_id", "FIRM-001"), request.form.get("intake_type"), request.form.get("primary_full_name"), request.form.get("preferred_name"), request.form.get("ma
- `app.py:18845` — `FIRM-001` — upsert_intake_orchestration_state( intake_id=intake_id, firm_id=session.get("firm_id", "FIRM-001"), identity_status="complete", overall_stage="identity_complete", readiness_label="Partially Ready", next_recommended_action="Add a
- `app.py:18876` — `FIRM-001` — SELECT * FROM identity_intake WHERE intake_id = ? AND firm_id = ? """, (intake_id, session.get("firm_id", "FIRM-001"))) intake = cur.fetchone() conn.close() if not intake: flash("Identity intake record not found.", "warning") return redirect(url_for("identity_intake
- `app.py:18887` — `FIRM-001` — hestration_state orchestration = get_intake_orchestration_state( intake_id, session.get("firm_id", "FIRM-001") ) return render_template( "intake_identity_summary.html", intake=intake, orchestration=orchestration ) @app.route("/admin/diag/execution
- `database/db.py:13` — `FIRM-001` — () def get_current_firm_id(): """ Return the active tenant/firm scope for the current request. Defaults to FIRM-001 only outside request context or legacy sessions. """ try: from flask import session, has_request_context if has_request_context(): return sessi
- `database/db.py:18` — `FIRM-001` — ask import session, has_request_context if has_request_context(): return session.get("firm_id") or "FIRM-001" except Exception: pass return "FIRM-001" def ensure_identity_intake_table(): """ Create Step 1 identity/family intake table. Minimal Operational V
- `database/db.py:21` — `FIRM-001` — quest_context(): return session.get("firm_id") or "FIRM-001" except Exception: pass return "FIRM-001" def ensure_identity_intake_table(): """ Create Step 1 identity/family intake table. Minimal Operational Version for guided intake. """ conn = get_connecti
- `database/db.py:37` — `FIRM-001` — id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT UNIQUE, firm_id TEXT DEFAULT 'FIRM-001', intake_type TEXT, primary_full_name TEXT, preferred_name TEXT, marital_status TEXT, state_jurisdiction TEXT,
- `database/db.py:74` — `FIRM-001` — id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT UNIQUE, firm_id TEXT DEFAULT 'FIRM-001', identity_status TEXT DEFAULT 'not_started', asset_status TEXT DEFAULT 'not_started', document_status TEXT DEFAULT 'not_started',
- `database/db.py:116` — `FIRM-001` — MARY KEY AUTOINCREMENT, asset_id TEXT UNIQUE, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', asset_category TEXT, asset_name TEXT, ownership_type TEXT, estimated_value TEXT, has_title_document TEXT,
- `database/db.py:154` — `FIRM-001` — KEY AUTOINCREMENT, document_id TEXT UNIQUE, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', document_category TEXT, document_name TEXT, file_name TEXT, upload_status TEXT DEFAULT 'uploaded', review_status T
- `database/db.py:1978` — `FIRM-001` — ashlib, json try: from flask import has_request_context, session firm_id = session.get("firm_id", "FIRM-001") if has_request_context() else "FIRM-001" except Exception: firm_id = "FIRM-001" conn = get_connection() cur = conn.cursor() # 1. Get previous hash
- `database/db.py:1978` — `FIRM-001` — import has_request_context, session firm_id = session.get("firm_id", "FIRM-001") if has_request_context() else "FIRM-001" except Exception: firm_id = "FIRM-001" conn = get_connection() cur = conn.cursor() # 1. Get previous hash cur.execute("SELECT entry_hash FROM audit_
- `database/db.py:1980` — `FIRM-001` — = session.get("firm_id", "FIRM-001") if has_request_context() else "FIRM-001" except Exception: firm_id = "FIRM-001" conn = get_connection() cur = conn.cursor() # 1. Get previous hash cur.execute("SELECT entry_hash FROM audit_log ORDER BY id DESC LIMIT 1") row = cur.fetcho
- `database/db.py:3513` — `FIRM-001` — column_type}") conn.commit() conn.close() def upsert_intake_orchestration_state( intake_id, firm_id="FIRM-001", identity_status=None, asset_status=None, document_status=None, review_status=None, drafting_status=None, execution_status=None, archive_status=None,
- `database/db.py:3581` — `FIRM-001` — d = ? """, values) conn.commit() conn.close() def get_intake_orchestration_state(intake_id, firm_id="FIRM-001"): ensure_intake_orchestration_table() conn = get_connection() conn.row_factory = sqlite3.Row cur = conn.cursor() cur.execute(""" SELECT * FR
- `database/db.py:3598` — `FIRM-001` — _id)) row = cur.fetchone() conn.close() return row def build_intake_readiness_summary(intake_id, firm_id="FIRM-001"): """ Basic readiness engine for Identity + Assets + Documents. Returns a structured readiness summary. """ ensure_identity_intake_table() ensure_asset_in
- `database/db.py:3707` — `FIRM-001` — ARY KEY AUTOINCREMENT, review_id TEXT UNIQUE, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', reviewer_name TEXT, review_status TEXT DEFAULT 'open', issue_flag TEXT, correction_required TEXT, reviewer_notes TEX
- `database/db.py:3738` — `FIRM-001` — ARY KEY AUTOINCREMENT, review_id TEXT UNIQUE, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', reviewer_name TEXT, review_status TEXT DEFAULT 'open', issue_flag TEXT, correction_required TEXT, reviewer_notes TEX
- `database/db.py:3769` — `FIRM-001` — IMARY KEY AUTOINCREMENT, prep_id TEXT UNIQUE, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', selected_document_type TEXT, drafting_purpose TEXT, required_inputs TEXT, missing_inputs TEXT, reviewer_approval TE
- `database/db.py:3803` — `FIRM-001` — AUTOINCREMENT, draft_session_id TEXT UNIQUE, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', document_type TEXT, workflow_status TEXT DEFAULT 'initialized', drafting_mode TEXT DEFAULT 'guided', launched_by TEXT,
- `database/db.py:3839` — `FIRM-001` — kspace_id TEXT UNIQUE, draft_session_id TEXT, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', document_type TEXT, primary_person TEXT, trustee_candidate TEXT, successor_trustee_candidate TEXT, primary_goal TE
- `database/db.py:3883` — `FIRM-001` — workspace_id TEXT, draft_session_id TEXT, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', document_type TEXT, variable_key TEXT, variable_value TEXT, variable_source TEXT, created_at TEXT DEFAULT CURRENT_
- `database/db.py:3915` — `FIRM-001` — workspace_id TEXT, draft_session_id TEXT, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', document_type TEXT, variable_key TEXT, variable_value TEXT, variable_source TEXT, created_at TEXT DEFAULT CURRENT_
- `database/db.py:3947` — `FIRM-001` — workspace_id TEXT, draft_session_id TEXT, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', document_type TEXT, preview_status TEXT DEFAULT 'non_final_preview', preview_body TEXT, created_at TEXT DEFAULT CURRENT_TIMEST
- `database/db.py:3978` — `FIRM-001` — workspace_id TEXT, draft_session_id TEXT, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', document_type TEXT, section_name TEXT, clause_status TEXT DEFAULT 'pending_review', clause_flag TEXT, correction_re
- `database/db.py:4015` — `FIRM-001` — workspace_id TEXT, draft_session_id TEXT, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', document_type TEXT, export_status TEXT DEFAULT 'not_ready', document_control_id TEXT, version_label TEXT DEFAULT 'v0.1-preview'
- `database/db.py:4054` — `FIRM-001` — workspace_id TEXT, draft_session_id TEXT, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', document_type TEXT, export_status TEXT DEFAULT 'not_ready', document_control_id TEXT, version_label TEXT DEFAULT 'v0.1-preview'
- `database/db.py:4092` — `FIRM-001` — workspace_id TEXT, draft_session_id TEXT, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', export_prep_id TEXT, document_control_id TEXT, document_type TEXT, version_label TEXT, file_name TEXT,
- `database/db.py:4130` — `FIRM-001` — workspace_id TEXT, draft_session_id TEXT, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', document_control_id TEXT, file_name TEXT, file_path TEXT, file_exists_status TEXT, reviewer_name TEXT,
- `database/db.py:4171` — `FIRM-001` — workspace_id TEXT, draft_session_id TEXT, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', document_control_id TEXT, document_type TEXT, version_label TEXT, source_docx_file_name TEXT, source_docx_file_path
- `database/db.py:4211` — `FIRM-001` — workspace_id TEXT, draft_session_id TEXT, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', document_control_id TEXT, pdf_file_name TEXT, pdf_file_path TEXT, file_exists_status TEXT, reviewer_name TEXT,
- `database/db.py:4253` — `FIRM-001` — workspace_id TEXT, draft_session_id TEXT, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', document_control_id TEXT, document_type TEXT, version_label TEXT, signer_name TEXT, signer_capacity TEXT,
- `database/db.py:4306` — `FIRM-001` — workspace_id TEXT, draft_session_id TEXT, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', document_control_id TEXT, document_type TEXT, version_label TEXT, signer_name TEXT, signer_capacity TEXT,
- `database/db.py:4360` — `FIRM-001` — workspace_id TEXT, draft_session_id TEXT, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', document_control_id TEXT, document_type TEXT, version_label TEXT, signer_name TEXT, signer_capacity TEXT,
- `database/db.py:4421` — `FIRM-001` — workspace_id TEXT, draft_session_id TEXT, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', document_control_id TEXT, document_type TEXT, version_label TEXT, final_status TEXT DEFAULT 'sealed_record', archiv
- `database/db.py:4493` — `FIRM-001` — handoff_id TEXT, transfer_id TEXT, trust_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', corrected_archive_status TEXT, corrected_custody_classification TEXT, corrected_seal_reference TEXT, corrected_handoff_capacity
- `database/db.py:4529` — `FIRM-001` — handoff_id TEXT UNIQUE, transfer_id TEXT, trust_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', archive_status TEXT DEFAULT 'handoff_prepared', custody_classification TEXT DEFAULT 'internal_record', seal_reference TEXT, hand
- `database/db.py:4551` — `FIRM-001` — TIMESTAMP ) """) conn.commit() conn.close() def build_lifecycle_master_ledger(intake_id, firm_id="FIRM-001"): """ Lifecycle Master Ledger. Builds a read-only linked status map from intake through final archive. """ ensure_identity_intake_table() ensure_intake_or
- `database/db.py:4731` — `FIRM-001` — workspace_id TEXT, draft_session_id TEXT, intake_id TEXT, firm_id TEXT DEFAULT 'FIRM-001', variable_key TEXT, variable_value TEXT, source_layer TEXT DEFAULT 'guided_workspace', created_at TEXT DEFAULT CURRENT_TIMESTAMP
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md:20` — `FIRM-002` — ed/maintained on startup. - Admin role is active. - Admin permissions include `view_dashboard`. - Firm scope is set to `FIRM-002`. - Startup log confirms hosted self-heal completion. Required Railway variable: - `ENSURE_HOSTED_ADMIN=1` ### G-7E — Permanent hosted FIRM-002 test trust seed Status: LOCKED C
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md:26` — `FIRM-002` — onfirms hosted self-heal completion. Required Railway variable: - `ENSURE_HOSTED_ADMIN=1` ### G-7E — Permanent hosted FIRM-002 test trust seed Status: LOCKED Confirmed behavior: - Hosted test trust seed runs at startup. - Seeded trust exists as `TR-001 — Redirect Test Trust 2`. - Trust is assigned to `FI
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md:32` — `FIRM-002` — ted test trust seed runs at startup. - Seeded trust exists as `TR-001 — Redirect Test Trust 2`. - Trust is assigned to `FIRM-002`. - Owner is `admin123`. - Status is `Finalized`. - Report Center sees the trust. - Trust Summary PDF generates successfully. Required Railway variable: - `ENSURE_HOSTED_TEST_TRU
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md:58` — `FIRM-002` — /summary.pdf` opens. - Invalid/cross-firm direct trust routes such as `TR-002` and `TR-999` do not expose trust data. - FIRM-002 isolation is confirmed across Admin, Reports, PDF, and direct trust routes. ## Keep ON These variables should remain enabled: ```text ENSURE_HOSTED_ADMIN=1 ENSURE_HOSTED_TEST_T
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md:68` — `FIRM-002` — : ```text ENSURE_HOSTED_ADMIN=1 ENSURE_HOSTED_TEST_TRUST=1 HOSTED_BOOTSTRAP_USERNAME=admin123 HOSTED_BOOTSTRAP_FIRM_ID=FIRM-002 DB_PATH=/data/trustee_app.db APP_ENV=production ``` `HOSTED_BOOTSTRAP_PASSWORD` must remain set to the current hosted admin password value. ## Keep OFF Unless Emergency Recovery
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md:89` — `FIRM-002` — STED_LOGIN_UNLOCK=0 ``` ## Confirmed Hosted Trust ```text Trust ID: TR-001 Trust Name: Redirect Test Trust 2 Firm ID: FIRM-002 Owner ID: admin123 Status: Finalized Effective Date: 2026-05-14 ``` ## Confirmed Browser Routes ```text https://trustee-app-production.up.railway.app/login https://trustee-app-p
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md:116` — `FIRM-002` — commended Phase G-8 — Hosted production data expansion and firewall regression suite. Candidate checks: - Create real FIRM-002 trust data beyond seeded test trust. - Add properties/accounts/documents/ledger records scoped to FIRM-002. - Confirm reports and direct routes remain firm-scoped. - Add repeatabl
- `docs/GLOBAL_411_FIREWALL_G7H_HOSTED_PRODUCTION_LOCK_MEMO.md:117` — `FIRM-002` — Create real FIRM-002 trust data beyond seeded test trust. - Add properties/accounts/documents/ledger records scoped to FIRM-002. - Confirm reports and direct routes remain firm-scoped. - Add repeatable regression script or checklist for hosted firewall validation.
- `docs/GLOBAL_411_FIREWALL_G8D_HOSTED_REGRESSION_CHECKLIST.md:14` — `FIRM-002` — eport changes, and route additions. The goal is to confirm that hosted production remains scoped to: ```text Firm ID: FIRM-002 Admin User: admin123 Seed Trust: TR-001 — Redirect Test Trust 2 ``` ## Required Railway Variables Keep ON: ```text ENSURE_HOSTED_ADMIN=1 ENSURE_HOSTED_TEST_TRUST=1 ENSURE_HOSTE
- `docs/GLOBAL_411_FIREWALL_G8D_HOSTED_REGRESSION_CHECKLIST.md:28` — `FIRM-002` — 1 ENSURE_HOSTED_TEST_TRUST=1 ENSURE_HOSTED_PORTFOLIO_SEED=1 HOSTED_BOOTSTRAP_USERNAME=admin123 HOSTED_BOOTSTRAP_FIRM_ID=FIRM-002 DB_PATH=/data/trustee_app.db APP_ENV=production ``` Keep OFF unless emergency recovery is intentionally needed: ```text ALLOW_HOSTED_ADMIN_BOOTSTRAP=0 ALLOW_HOSTED_FIRM_MIGRATIO
- `docs/GLOBAL_411_FIREWALL_G8D_HOSTED_REGRESSION_CHECKLIST.md:64` — `FIRM-002` — : no such table: transfers ``` ## Seeded Production Test Data Trust: ```text TR-001 — Redirect Test Trust 2 Firm ID: FIRM-002 Owner ID: admin123 Status: Finalized ``` Portfolio records: ```text PROP-001 — Hosted Test Property ACCT-001 — Checking DOC-001 — Hosted Portfolio Seed Document LEDGER-001 — Ass
- `docs/GLOBAL_411_FIREWALL_G8D_HOSTED_REGRESSION_CHECKLIST.md:116` — `FIRM-002` — on.up.railway.app/admin ``` Expected: ```text Admin dashboard opens. No Access Denied. No Internal Server Error. Only FIRM-002 scoped data appears. ``` --- # Regression Test B — Report Center Dropdown Open: ```text https://trustee-app-production.up.railway.app/reports ``` Expected dropdown: ```text
- `docs/GLOBAL_411_FIREWALL_G8D_HOSTED_REGRESSION_CHECKLIST.md:140` — `FIRM-001` — -001 — Redirect Test Trust 2 ``` Failure signatures: ```text Dropdown empty Dropdown shows only TR-002 Dropdown shows FIRM-001 records Internal Server Error Access Denied for Admin ``` --- # Regression Test C — Trust Summary PDF Open: ```text https://trustee-app-production.up.railway.app/reports/trust
- `scripts/migrate_hosted_firm_scope.py:62` — `FIRM-001` — D: add_column_if_missing(cur, table, "firm_id", "TEXT") conn.commit() # Default legacy hosted rows to FIRM-001. for table in TABLES_WITH_FIRM_ID: if not table_exists(cur, table) or not column_exists(cur, table, "firm_id"): continue cur.execute(f"""
- `scripts/migrate_hosted_firm_scope.py:68` — `FIRM-001` — table, "firm_id"): continue cur.execute(f""" UPDATE {table} SET firm_id = 'FIRM-001' WHERE firm_id IS NULL OR TRIM(firm_id) = '' """) print(f"{table}: defaulted rows to FIRM-001:", cur.rowcount) conn.commit() # Ensure FIRM-00
- `scripts/migrate_hosted_firm_scope.py:71` — `FIRM-001` — RM-001' WHERE firm_id IS NULL OR TRIM(firm_id) = '' """) print(f"{table}: defaulted rows to FIRM-001:", cur.rowcount) conn.commit() # Ensure FIRM-002 test/admin users can exist if app_users table exists. if table_exists(cur, "app_users"): cur.execute("PRAGMA
- `scripts/migrate_hosted_firm_scope.py:75` — `FIRM-002` — = '' """) print(f"{table}: defaulted rows to FIRM-001:", cur.rowcount) conn.commit() # Ensure FIRM-002 test/admin users can exist if app_users table exists. if table_exists(cur, "app_users"): cur.execute("PRAGMA table_info(app_users)") cols = [r["name"] for r in
- `scripts/migrate_hosted_firm_scope.py:82` — `FIRM-002` — if "firm_id" in cols: cur.execute(""" UPDATE app_users SET firm_id = 'FIRM-002' WHERE LOWER(username) IN ('admin123', 'testadmin1') """) print("app_users: assigned admin123/testadmin1 to FIRM-002:", cur.rowcount)
- `scripts/migrate_hosted_firm_scope.py:85` — `FIRM-002` — (username) IN ('admin123', 'testadmin1') """) print("app_users: assigned admin123/testadmin1 to FIRM-002:", cur.rowcount) conn.commit() print("\nVERIFY COUNTS BY FIRM") for table in TABLES_WITH_FIRM_ID: if not table_exists(cur, table) or not column_exists(cur, t
- `services/services_intake.py:80` — `FIRM-001` — id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT UNIQUE NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', client_id TEXT, intake_lane TEXT NOT NULL, user_posture TEXT, default_depth TEXT, risk_posture TEXT, prof
- `services/services_intake.py:101` — `FIRM-001` — id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', event_type TEXT, event_label TEXT, event_value TEXT, created_at TEXT, created_by TEXT ) """) conn.co
- `services/services_intake.py:863` — `FIRM-001` — id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', question_key TEXT NOT NULL, answer_key TEXT NOT NULL, answer_label TEXT, created_at TEXT, created_by TEXT )
- `services/services_intake.py:876` — `FIRM-001` — id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', source_key TEXT NOT NULL, system_category TEXT, system_meaning TEXT, module_trigger TEXT, document_request TEXT,
- `services/services_intake.py:1169` — `FIRM-001` — id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', complexity_score INTEGER DEFAULT 0, complexity_level TEXT, urgency_score INTEGER DEFAULT 0, urgency_level TEXT, readi
- `services/services_intake.py:1567` — `FIRM-001` — id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT UNIQUE NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', snapshot_json TEXT, created_at TEXT, updated_at TEXT, created_by TEXT ) """) conn.commit() conn.close() de
- `services/services_intake.py:2033` — `FIRM-001` — id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', note_type TEXT DEFAULT 'general', priority TEXT DEFAULT 'normal', followup_status TEXT DEFAULT 'open', note_body TEXT NOT NULL,
- `services/services_intake.py:2229` — `FIRM-001` — id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', task_type TEXT DEFAULT 'staff_action', priority TEXT DEFAULT 'normal', status TEXT DEFAULT 'open', title TEXT NOT NULL,
- `services/services_intake.py:2922` — `FIRM-001` — id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', export_type TEXT, export_status TEXT, file_path TEXT, message TEXT, created_at TEXT, created_by TEXT
- `services/services_intake.py:3915` — `FIRM-001` — id INTEGER PRIMARY KEY AUTOINCREMENT, intake_id TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', workflow_key TEXT NOT NULL, title TEXT, workflow_type TEXT, priority TEXT, confidence INTEGER, reason TEX
- `services/services_intake.py:5070` — `FIRM-001` — CREMENT, intake_id TEXT NOT NULL, workflow_key TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', question_key TEXT NOT NULL, answer_key TEXT, answer_label TEXT, created_at TEXT, updated_at TEXT, created
- `services/services_intake.py:5445` — `FIRM-001` — CREMENT, intake_id TEXT NOT NULL, workflow_key TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', draft_packet_type TEXT, readiness TEXT, open_issue_count INTEGER DEFAULT 0, open_task_count INTEGER DEFAULT 0, comple
- `services/services_intake.py:6070` — `FIRM-001` — NULL, workflow_key TEXT NOT NULL, document_key TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', question_key TEXT NOT NULL, answer_key TEXT, answer_label TEXT, created_at TEXT, updated_at TEXT, created
- `services/services_intake.py:6417` — `FIRM-001` — NULL, workflow_key TEXT NOT NULL, document_key TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', gate_name TEXT, gate_status TEXT DEFAULT 'pending', gate_reason TEXT, missing_answer_count INTEGER DEFAULT 0, open_is
- `services/services_intake.py:6731` — `FIRM-001` — _key TEXT NOT NULL, gate_name TEXT DEFAULT 'non_final_draft_review_gate', firm_id TEXT DEFAULT 'FIRM-001', action_key TEXT, action_label TEXT, resulting_status TEXT, note TEXT, created_at TEXT, created_by TEXT
- `services/services_intake.py:6941` — `FIRM-001` — NULL, workflow_key TEXT NOT NULL, document_key TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', gate_status TEXT DEFAULT 'blocked', gate_reason TEXT, questionnaire_complete INTEGER DEFAULT 0, open_issues_reviewed INTEGER DEFA
- `services/services_intake.py:7313` — `FIRM-001` — NULL, workflow_key TEXT NOT NULL, document_key TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', action_key TEXT, action_label TEXT, note TEXT, created_at TEXT, created_by TEXT ) """) conn.commit()
- `services/services_intake.py:7615` — `FIRM-001` — NULL, workflow_key TEXT NOT NULL, document_key TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', approval_status TEXT DEFAULT 'approved_for_final_draft_preparation', approval_note TEXT NOT NULL, gate_status_before TEXT, gate_s
- `services/services_intake.py:7996` — `FIRM-001` — NULL, workflow_key TEXT NOT NULL, document_key TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', section_order INTEGER, section_heading TEXT, section_source TEXT, section_body TEXT, section_status TEXT DEFAULT 'dra
- `services/services_intake.py:8420` — `FIRM-001` — NULL, workflow_key TEXT NOT NULL, document_key TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', version_label TEXT, export_type TEXT DEFAULT 'docx', file_path TEXT, preview_status TEXT, ready_count INTEGER DEFAULT
- `services/services_intake.py:8628` — `FIRM-001` — NULL, workflow_key TEXT NOT NULL, document_key TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', gate_status TEXT DEFAULT 'blocked', gate_reason TEXT, total_sections INTEGER DEFAULT 0, ready_sections INTEGER DEFAULT 0,
- `services/services_intake.py:8651` — `FIRM-001` — NULL, workflow_key TEXT NOT NULL, document_key TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', action_status TEXT, note TEXT, created_at TEXT, created_by TEXT ) """) conn.commit() conn.close() def eval
- `services/services_matters.py:12` — `FIRM-001` — id INTEGER PRIMARY KEY AUTOINCREMENT, matter_id TEXT UNIQUE NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', title TEXT NOT NULL, matter_type TEXT NOT NULL, status TEXT DEFAULT 'Open', priority TEXT DEFAULT 'Normal', jurisdict
- `services/services_matters.py:34` — `FIRM-001` — MENT, event_id TEXT UNIQUE NOT NULL, matter_id TEXT NOT NULL, firm_id TEXT DEFAULT 'FIRM-001', event_type TEXT NOT NULL, actor TEXT, authority_basis TEXT, description TEXT NOT NULL, linked_record_type TEXT,
- `docs/security/GLOBAL_411_FIREWALL_PRODUCTION_HARDENING_CHECKLIST.md:5` — `FIRM-002` — EWALL — Production Hardening Checklist ## Locked Status The Global 411 Firewall is confirmed for restricted Admin 2 / FIRM-002. Confirmed: - FIRM-002 Admin can access own firm records. - FIRM-002 Admin cannot access FIRM-001 trust packet export. - FIRM-002 Admin cannot access FIRM-001 report by internal
- `docs/security/GLOBAL_411_FIREWALL_PRODUCTION_HARDENING_CHECKLIST.md:8` — `FIRM-002` — ning Checklist ## Locked Status The Global 411 Firewall is confirmed for restricted Admin 2 / FIRM-002. Confirmed: - FIRM-002 Admin can access own firm records. - FIRM-002 Admin cannot access FIRM-001 trust packet export. - FIRM-002 Admin cannot access FIRM-001 report by internal ID. - System health is M
- `docs/security/GLOBAL_411_FIREWALL_PRODUCTION_HARDENING_CHECKLIST.md:9` — `FIRM-002` — 11 Firewall is confirmed for restricted Admin 2 / FIRM-002. Confirmed: - FIRM-002 Admin can access own firm records. - FIRM-002 Admin cannot access FIRM-001 trust packet export. - FIRM-002 Admin cannot access FIRM-001 report by internal ID. - System health is Master Admin only. - Storage diagnostics are Ma
- `docs/security/GLOBAL_411_FIREWALL_PRODUCTION_HARDENING_CHECKLIST.md:9` — `FIRM-001` — restricted Admin 2 / FIRM-002. Confirmed: - FIRM-002 Admin can access own firm records. - FIRM-002 Admin cannot access FIRM-001 trust packet export. - FIRM-002 Admin cannot access FIRM-001 report by internal ID. - System health is Master Admin only. - Storage diagnostics are Master Admin only. - Database b
- `docs/security/GLOBAL_411_FIREWALL_PRODUCTION_HARDENING_CHECKLIST.md:10` — `FIRM-002` — Confirmed: - FIRM-002 Admin can access own firm records. - FIRM-002 Admin cannot access FIRM-001 trust packet export. - FIRM-002 Admin cannot access FIRM-001 report by internal ID. - System health is Master Admin only. - Storage diagnostics are Master Admin only. - Database backup routes are Master Admin on
- `docs/security/GLOBAL_411_FIREWALL_PRODUCTION_HARDENING_CHECKLIST.md:10` — `FIRM-001` — an access own firm records. - FIRM-002 Admin cannot access FIRM-001 trust packet export. - FIRM-002 Admin cannot access FIRM-001 report by internal ID. - System health is Master Admin only. - Storage diagnostics are Master Admin only. - Database backup routes are Master Admin only. - Certificate registry is

## Possible Unscoped Queries

- `app.py:380` — tables: `app_users`
  - `SELECT user_id FROM app_users WHERE TRIM(LOWER(username)) = TRIM(LOWER(?))`
- `app.py:398` — tables: `app_users`
  - `SELECT COUNT(*) AS count FROM app_users`
- `app.py:624` — tables: `trusts`
  - `SELECT trust_id FROM trusts WHERE trust_id = ?`
- `app.py:11467` — tables: `transfers`
  - `SELECT * FROM transfers WHERE trust_id = ? ORDER BY created_at DESC`
- `app.py:11698` — tables: `transfers`
  - `SELECT * FROM transfers WHERE trust_id = ? ORDER BY created_at DESC`
- `app.py:11918` — tables: `trust_minutes`
  - `SELECT COUNT(*) AS count FROM trust_minutes WHERE {" AND ".join(where_parts)}`
- `app.py:13248` — tables: `transfers`
  - `SELECT * FROM transfers WHERE trust_id = ? ORDER BY created_at DESC`
- `app.py:13967` — tables: `trust_minutes`
  - `SELECT * FROM trust_minutes WHERE {" AND ".join(where_parts)} ORDER BY {order_col} DESC`
- `app.py:14124` — tables: `trust_minutes`
  - `SELECT * FROM trust_minutes WHERE {" AND ".join(where_parts)} ORDER BY {order_col} DESC`
- `app.py:14521` — tables: `app_users`
  - `SELECT user_id FROM app_users WHERE username = ?`
- `app.py:14538` — tables: `app_users`
  - `SELECT COUNT(*) AS count FROM app_users`
- `app.py:14603` — tables: `app_users`
  - `SELECT user_id FROM app_users WHERE username = ?`
- `app.py:14620` — tables: `app_users`
  - `SELECT COUNT(*) AS count FROM app_users`
- `app.py:14725` — tables: `app_users`
  - `SELECT name FROM sqlite_master WHERE type='table' AND name='app_users'`
- `app.py:14829` — tables: `app_users`
  - `SELECT user_id FROM app_users WHERE TRIM(LOWER(username)) = TRIM(LOWER(?))`
- `app.py:14845` — tables: `app_users`
  - `SELECT COUNT(*) AS count FROM app_users`
- `app.py:15356` — tables: `identity_intake`
  - `SELECT * FROM identity_intake WHERE intake_id = ?`
- `app.py:15420` — tables: `asset_intake`
  - `SELECT * FROM asset_intake WHERE intake_id = ? ORDER BY created_at DESC`
- `app.py:15465` — tables: `identity_intake`
  - `SELECT * FROM identity_intake WHERE intake_id = ?`
- `app.py:15523` — tables: `document_intake`
  - `SELECT * FROM document_intake WHERE intake_id = ? ORDER BY created_at DESC`
- `app.py:15786` — tables: `identity_intake`
  - `SELECT * FROM identity_intake WHERE intake_id = ?`
- `app.py:15842` — tables: `draft_sessions`
  - `SELECT * FROM draft_sessions WHERE intake_id = ? ORDER BY created_at DESC`
- `app.py:15885` — tables: `draft_sessions`
  - `SELECT * FROM draft_sessions WHERE draft_session_id = ?`
- `app.py:15900` — tables: `identity_intake`
  - `SELECT * FROM identity_intake WHERE intake_id = ?`
- `app.py:15908` — tables: `asset_intake`
  - `SELECT * FROM asset_intake WHERE intake_id = ?`
- `app.py:15916` — tables: `document_intake`
  - `SELECT * FROM document_intake WHERE intake_id = ?`
- `app.py:15985` — tables: `guided_draft_workspace`
  - `SELECT * FROM guided_draft_workspace WHERE draft_session_id = ? ORDER BY created_at DESC`
- `app.py:16031` — tables: `guided_draft_workspace`
  - `SELECT * FROM guided_draft_workspace WHERE workspace_id = ?`
- `app.py:16152` — tables: `guided_draft_workspace`
  - `SELECT * FROM guided_draft_workspace WHERE workspace_id = ?`
- `app.py:16318` — tables: `guided_draft_workspace`
  - `SELECT * FROM guided_draft_workspace WHERE workspace_id = ?`
- `app.py:16447` — tables: `guided_draft_workspace`
  - `SELECT * FROM guided_draft_workspace WHERE workspace_id = ?`
- `app.py:16596` — tables: `guided_draft_workspace`
  - `SELECT * FROM guided_draft_workspace WHERE workspace_id = ?`
- `database/db.py:431` — tables: `trusts`
  - `SELECT COUNT(*) AS count FROM trusts`
- `database/db.py:558` — tables: `trusts`
  - `UPDATE trusts SET {fields} WHERE trust_id = ?`
- `database/db.py:565` — tables: `properties`
  - `SELECT COUNT(*) AS count FROM properties`
- `database/db.py:654` — tables: `accounts`
  - `SELECT COUNT(*) AS count FROM accounts`
- `database/db.py:707` — tables: `documents`
  - `SELECT COUNT(*) AS count FROM documents`
- `database/db.py:715` — tables: `documents`
  - `INSERT INTO documents ( document_id, trust_id, property_id, account_id, document_category, document_title, notes, original_filename, stored_filename, file_path ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
- `database/db.py:755` — tables: `documents`
  - `SELECT * FROM documents WHERE property_id = ? ORDER BY document_id`
- `database/db.py:765` — tables: `ledger_entries`
  - `SELECT COUNT(*) AS count FROM ledger_entries`
- `database/db.py:773` — tables: `ledger_entries`
  - `INSERT INTO ledger_entries ( entry_id, trust_id, property_id, account_id, entry_type, amount, entry_date, description, entry_category, accounting_method, recognition_date, due_date, paid_date, chart_account ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
- `database/db.py:793` — tables: `ledger_entries`
  - `SELECT * FROM ledger_entries WHERE trust_id = ? AND owner_id = ? ORDER BY entry_id`
- `database/db.py:804` — tables: `ledger_entries`
  - `SELECT * FROM ledger_entries WHERE property_id = ? AND owner_id = ? ORDER BY entry_id`
- `database/db.py:888` — tables: `properties`
  - `SELECT * FROM properties WHERE custodian IS NULL OR custodian = '' ORDER BY property_id`
- `database/db.py:896` — tables: `properties`
  - `SELECT * FROM properties WHERE review_date IS NULL OR review_date = '' ORDER BY property_id`
- `database/db.py:904` — tables: `properties`
  - `SELECT * FROM properties WHERE expiration_date IS NOT NULL AND expiration_date != '' ORDER BY expiration_date`
- `database/db.py:912` — tables: `properties`
  - `SELECT * FROM properties WHERE trust_id IS NULL OR trust_id = '' ORDER BY property_id`
- `database/db.py:930` — tables: `properties`
  - `SELECT * FROM properties WHERE {field_name} IS NOT NULL AND {field_name} != ''`
- `database/db.py:939` — tables: `properties`
  - `SELECT * FROM properties WHERE {field_name} IS NOT NULL AND {field_name} != ''`
- `database/db.py:1154` — tables: `beneficiaries`
  - `SELECT COUNT(*) AS count FROM beneficiaries`
- `database/db.py:1163` — tables: `distributions`
  - `SELECT COUNT(*) AS count FROM distributions`
- `database/db.py:1195` — tables: `beneficiaries`
  - `UPDATE beneficiaries SET {fields} WHERE beneficiary_id = ?`
- `database/db.py:1253` — tables: `distributions`
  - `UPDATE distributions SET {fields} WHERE distribution_id = ?`
- `database/db.py:1363` — tables: `beneficiaries`
  - `SELECT * FROM beneficiaries WHERE beneficiary_id = ? AND trust_id = ?`
- `database/db.py:1384` — tables: `beneficiaries, distributions`
  - `SELECT d.*, b.full_name AS beneficiary_name, b.tax_id AS beneficiary_tax_id FROM distributions d LEFT JOIN beneficiaries b ON d.beneficiary_id = b.beneficiary_id WHERE d.distribution_id = ? AND d.trust_id = ?`
- `database/db.py:1538` — tables: `ledger_entries`
  - `SELECT * FROM ledger_entries WHERE trust_id = ? ORDER BY entry_date DESC, entry_id DESC`
- `database/db.py:1654` — tables: `instruments`
  - `SELECT COUNT(*) AS count FROM instruments`
- `database/db.py:1663` — tables: `instruments`
  - `INSERT INTO instruments ( instrument_id, trust_id, instrument_number, instrument_type, issue_date, maturity_date, face_value, backing_type, backing_reference, status, affidavit_reference, custody_reference, notes ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
- `database/db.py:1686` — tables: `instruments`
  - `UPDATE instruments SET {fields} WHERE instrument_id = ?`
- `database/db.py:1694` — tables: `instruments`
  - `SELECT * FROM instruments WHERE instrument_id = ?`
- `database/db.py:1703` — tables: `instruments`
  - `SELECT * FROM instruments WHERE trust_id = ? ORDER BY issue_date DESC, instrument_id DESC`
- `database/db.py:1768` — tables: `instruments`
  - `SELECT COUNT(*) AS count FROM instruments`
- `database/db.py:1986` — tables: `audit_log`
  - `SELECT entry_hash FROM audit_log ORDER BY id DESC LIMIT 1`
- `database/db.py:1999` — tables: `audit_log`
  - `SELECT created_at FROM audit_log WHERE id = ?`
- `database/db.py:2020` — tables: `audit_log`
  - `UPDATE audit_log SET previous_hash = ?, entry_hash = ?, hash_algorithm = ? WHERE id = ?`
- `database/db.py:2082` — tables: `audit_log`
  - `SELECT * FROM audit_log ORDER BY id ASC`
- `database/db.py:2359` — tables: `fiduciaries`
  - `SELECT COUNT(*) AS count FROM fiduciaries`
- `database/db.py:2556` — tables: `media_records`
  - `SELECT COUNT(*) AS count FROM media_records`
- `database/db.py:2711` — tables: `user_roles`
  - `SELECT COUNT(*) AS count FROM user_roles`
- `database/db.py:2811` — tables: `app_users`
  - `SELECT * FROM app_users WHERE username = ? LIMIT 1`
- `database/db.py:2845` — tables: `app_users`
  - `SELECT COUNT(*) AS count FROM app_users`
- `database/db.py:2854` — tables: `app_users`
  - `SELECT * FROM app_users ORDER BY username`
- `database/db.py:2866` — tables: `app_users`
  - `UPDATE app_users SET role_name = ?, status = ? WHERE username = ?`
- `database/db.py:2882` — tables: `app_users`
  - `UPDATE app_users SET password_hash = ? WHERE username = ?`
- `database/db.py:2987` — tables: `app_users`
  - `SELECT * FROM app_users WHERE username = ? LIMIT 1`
- `database/db.py:3255` — tables: `trust_minutes`
  - `SELECT COUNT(*) AS count FROM trust_minutes`
- `database/db.py:3265` — tables: `trust_minutes`
  - `INSERT INTO trust_minutes ( minute_id, trust_id, meeting_date, meeting_type, title, purpose, resolutions, action_items, status, created_by ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
- `database/db.py:3291` — tables: `trust_minutes`
  - `SELECT minute_id FROM trust_minutes WHERE status IN ('Executed', 'Archived') AND (certificate_id IS NULL OR TRIM(certificate_id) = '') ORDER BY minute_id ASC`
- `database/db.py:3306` — tables: `trust_minutes`
  - `UPDATE trust_minutes SET certificate_id = ? WHERE minute_id = ? AND (certificate_id IS NULL OR TRIM(certificate_id) = '')`
- `database/db.py:3327` — tables: `trust_minutes`
  - `SELECT * FROM trust_minutes WHERE certificate_id = ? LIMIT 1`
- `database/db.py:3343` — tables: `trust_minutes`
  - `SELECT minute_id, trust_id, title, status, executed_at, archived_at, locked, certificate_id, trustee_1_capacity, trustee_2_capacity, trustee_3_capacity FROM trust_minutes WHERE status IN ('Executed', 'Archived') ORDER BY executed_at DESC, minute_id DESC`
- `database/db.py:3439` — tables: `trust_minutes`
  - `UPDATE trust_minutes SET trustee_1_name = ?, trustee_1_capacity = ?, trustee_1_signed_date = ?, trustee_1_signature_image = ?, trustee_2_name = ?, trustee_2_capacity = ?, trustee_2_signed_date = ?, trustee_2_signature_image = ?, trustee_3_name = ?, trustee_3_capacity = ?, trustee_3_signed_date = ?, trustee_3_signature_image = ?, certificate_id = ?, approved_at = ?, executed_at = ?, archived_at = ?, status = ?, locked = ? WHERE minute_id = ?`
- `services/services_continuity_assets.py:50` — tables: `properties`
  - `SELECT property_id, trust_id, property_name, property_type, asset_class, asset_subtype, custodian, continuity_classification, custody_classification, continuity_priority, heritage_significance, preservation_requirements, restricted_access_level, lineage_association, memorial_status, sacred_status, continuity_notes FROM properties WHERE property_id = ?`
- `services/services_continuity_assets.py:109` — tables: `properties`
  - `UPDATE properties SET {assignments} WHERE property_id = ?`
- `services/services_continuity_assets.py:127` — tables: `properties`
  - `SELECT * FROM properties WHERE trust_id = ? AND ( continuity_classification IS NOT NULL OR custody_classification IS NOT NULL OR memorial_status = 1 OR sacred_status = 1 ) ORDER BY continuity_priority DESC, property_id ASC`
- `services/services_continuity_assets.py:154` — tables: `continuity_custody_log`
  - `SELECT COUNT(*) AS count FROM continuity_custody_log`
- `services/services_continuity_assets.py:213` — tables: `continuity_custody_log`
  - `SELECT * FROM continuity_custody_log WHERE property_id = ? ORDER BY event_date DESC, id DESC`
- `services/services_continuity_assets.py:230` — tables: `continuity_custody_log`
  - `SELECT * FROM continuity_custody_log WHERE custody_event_id = ?`
- `services/services_continuity_assets.py:351` — tables: `documents`
  - `SELECT * FROM documents WHERE property_id = ? ORDER BY document_id ASC`
- `services/services_continuity_assets.py:368` — tables: `media_records`
  - `SELECT * FROM media_records WHERE related_entity_type = 'property' AND related_entity_id = ? ORDER BY created_at DESC`
- `services/services_continuity_assets.py:606` — tables: `continuity_custody_log`
  - `UPDATE continuity_custody_log SET supporting_document_reference = ? WHERE custody_event_id = ?`
- `services/services_continuity_assets.py:858` — tables: `archive_packet_finalization`
  - `SELECT COUNT(*) AS count FROM archive_packet_finalization`
- `services/services_continuity_assets.py:912` — tables: `archive_packet_finalization`
  - `SELECT * FROM archive_packet_finalization WHERE property_id = ? ORDER BY finalized_at DESC, id DESC`
- `services/services_intake.py:123` — tables: `intake_sessions`
  - `SELECT intake_id FROM intake_sessions ORDER BY id DESC LIMIT 1`
- `services/services_intake.py:1008` — tables: `intake_sessions`
  - `UPDATE intake_sessions SET status = ?, updated_at = ? WHERE intake_id = ?`
- `services/services_intake.py:1054` — tables: `intake_sessions`
  - `SELECT intake_id, intake_lane, user_posture, default_depth, risk_posture, professional_review_recommended, automation_limits, next_screen, status, created_at, updated_at FROM intake_sessions WHERE intake_id = ?`
- `services/services_intake.py:1295` — tables: `intake_sessions`
  - `UPDATE intake_sessions SET status = ?, updated_at = ? WHERE intake_id = ?`
- `services/services_intake.py:1611` — tables: `intake_sessions`
  - `UPDATE intake_sessions SET status = ?, updated_at = ? WHERE intake_id = ?`
- `services/services_intake.py:1628` — tables: `intake_scores`
  - `SELECT s1.intake_id, s1.complexity_score, s1.complexity_level, s1.urgency_score, s1.urgency_level, s1.readiness_score, s1.readiness_level FROM intake_scores s1 INNER JOIN ( SELECT intake_id, MAX(id) AS max_id FROM intake_scores GROUP BY intake_id ) latest ON s1.id = latest.max_id`
- `services/services_intake.py:1710` — tables: `intake_answers`
  - `SELECT question_key, answer_key, answer_label FROM intake_answers WHERE intake_id = ? ORDER BY id ASC`
- `services/services_intake.py:1735` — tables: `intake_translations`
  - `SELECT source_key, system_category, system_meaning, module_trigger, document_request, next_session, risk_flag FROM intake_translations WHERE intake_id = ? ORDER BY id ASC`
- `services/services_intake.py:1765` — tables: `intake_scores`
  - `SELECT complexity_score, complexity_level, urgency_score, urgency_level, readiness_score, readiness_level, scoring_notes FROM intake_scores WHERE intake_id = ? ORDER BY id DESC LIMIT 1`
- `services/services_intake.py:1814` — tables: `intake_snapshots`
  - `SELECT snapshot_json FROM intake_snapshots WHERE intake_id = ? LIMIT 1`
- `services/services_intake.py:2095` — tables: `intake_sessions`
  - `UPDATE intake_sessions SET updated_at = ? WHERE intake_id = ?`
- `services/services_intake.py:2121` — tables: `intake_review_notes`
  - `SELECT id, intake_id, note_type, priority, followup_status, note_body, created_at, updated_at, created_by FROM intake_review_notes WHERE intake_id = ? ORDER BY id DESC`
- `services/services_intake.py:2301` — tables: `intake_sessions`
  - `UPDATE intake_sessions SET updated_at = ? WHERE intake_id = ?`
- `services/services_intake.py:2329` — tables: `intake_followup_tasks`
  - `SELECT id, intake_id, task_type, priority, status, title, description, source, created_at, updated_at, created_by, completed_at, completed_by FROM intake_followup_tasks WHERE intake_id = ? ORDER BY CASE status WHEN 'open' THEN 1 WHEN 'pending_client' THEN 2 WHEN 'pending_staff' THEN 3 WHEN 'pending_professional' THEN 4 WHEN 'deferred' THEN 5 WHEN 'completed' THEN 6 ELSE 7 END, CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'normal' THEN 3 WHEN 'low' THEN 4 ELSE 5 END, id ASC`
- `services/services_intake.py:2417` — tables: `intake_followup_tasks`
  - `SELECT COUNT(*) FROM intake_followup_tasks WHERE intake_id = ? AND title = ?`
- `services/services_intake.py:2513` — tables: `intake_followup_tasks`
  - `UPDATE intake_followup_tasks SET status = ?, updated_at = ?, completed_at = ?, completed_by = ? WHERE id = ?`
- `services/services_intake.py:2982` — tables: `intake_export_logs`
  - `SELECT export_type, export_status, file_path, message, created_at, created_by FROM intake_export_logs WHERE intake_id = ? ORDER BY id DESC LIMIT 25`
- `services/services_intake.py:3107` — tables: `intake_export_logs`
  - `SELECT COALESCE(MAX(version_number), 0) FROM intake_export_logs WHERE intake_id = ? AND export_type = ? AND packet_type = ? AND export_status IN ('success', 'failed', 'error')`
- `services/services_intake.py:3221` — tables: `intake_export_logs`
  - `SELECT export_type, export_status, file_path, message, created_at, created_by, version_number, packet_type FROM intake_export_logs WHERE intake_id = ? ORDER BY id DESC LIMIT 100`
- `services/services_intake.py:3980` — tables: `intake_document_recommendations`
  - `SELECT id, status FROM intake_document_recommendations WHERE intake_id = ? AND workflow_key = ? LIMIT 1`
- `services/services_intake.py:3999` — tables: `intake_document_recommendations`
  - `UPDATE intake_document_recommendations SET title = ?, workflow_type = ?, priority = ?, confidence = ?, reason = ?, source = ?, status = ?, updated_at = ?, created_by = ? WHERE id = ?`
- `services/services_intake.py:4056` — tables: `intake_document_recommendations`
  - `SELECT workflow_key, title, workflow_type, priority, confidence, reason, source, status, created_at, updated_at, created_by FROM intake_document_recommendations WHERE intake_id = ? ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'normal' THEN 3 WHEN 'low' THEN 4 ELSE 5 END, confidence DESC, id ASC`
- `services/services_intake.py:4451` — tables: `intake_document_recommendations`
  - `UPDATE intake_document_recommendations SET status = ?, updated_at = ?, created_by = ? WHERE intake_id = ? AND workflow_key = ?`
- `services/services_intake.py:4473` — tables: `intake_document_recommendations`
  - `SELECT workflow_key, title, workflow_type, priority, confidence, reason, source, status, created_at, updated_at, created_by FROM intake_document_recommendations WHERE intake_id = ? AND workflow_key = ? LIMIT 1`
- `services/services_intake.py:5099` — tables: `intake_workflow_bridge_answers`
  - `DELETE FROM intake_workflow_bridge_answers WHERE intake_id = ? AND workflow_key = ?`
- `services/services_intake.py:5143` — tables: `intake_document_recommendations`
  - `UPDATE intake_document_recommendations SET status = ?, updated_at = ?, created_by = ? WHERE intake_id = ? AND workflow_key = ?`
- `services/services_intake.py:5168` — tables: `intake_workflow_bridge_answers`
  - `SELECT question_key, answer_key, answer_label, created_at, updated_at, created_by FROM intake_workflow_bridge_answers WHERE intake_id = ? AND workflow_key = ? ORDER BY id ASC`
- `services/services_intake.py:5535` — tables: `intake_draft_readiness_ledger`
  - `SELECT intake_id, workflow_key, draft_packet_type, readiness, open_issue_count, open_task_count, completed_task_count, document_count, drafting_question_count, status, created_at, updated_at, updated_by, notes FROM intake_draft_readiness_ledger WHERE intake_id = ? ORDER BY updated_at DESC`
- `services/services_intake.py:5545` — tables: `intake_draft_readiness_ledger`
  - `SELECT intake_id, workflow_key, draft_packet_type, readiness, open_issue_count, open_task_count, completed_task_count, document_count, drafting_question_count, status, created_at, updated_at, updated_by, notes FROM intake_draft_readiness_ledger ORDER BY updated_at DESC LIMIT 200`
- `services/services_intake.py:6098` — tables: `intake_document_draft_answers`
  - `DELETE FROM intake_document_draft_answers WHERE intake_id = ? AND workflow_key = ? AND document_key = ?`
- `services/services_intake.py:6152` — tables: `intake_document_draft_answers`
  - `SELECT question_key, answer_key, answer_label, created_at, updated_at, created_by FROM intake_document_draft_answers WHERE intake_id = ? AND workflow_key = ? AND document_key = ? ORDER BY id ASC`
- `services/services_intake.py:6530` — tables: `intake_review_gate_ledger`
  - `SELECT intake_id, workflow_key, document_key, gate_name, gate_status, gate_reason, missing_answer_count, open_issue_count, open_task_count, document_status, created_at, updated_at, updated_by, notes FROM intake_review_gate_ledger WHERE intake_id = ? ORDER BY updated_at DESC`
- `services/services_intake.py:6540` — tables: `intake_review_gate_ledger`
  - `SELECT intake_id, workflow_key, document_key, gate_name, gate_status, gate_reason, missing_answer_count, open_issue_count, open_task_count, document_status, created_at, updated_at, updated_by, notes FROM intake_review_gate_ledger ORDER BY updated_at DESC LIMIT 200`
- `services/services_intake.py:6751` — tables: `intake_review_gate_ledger`
  - `SELECT intake_id, workflow_key, document_key, gate_name, gate_status, gate_reason, missing_answer_count, open_issue_count, open_task_count, document_status, created_at, updated_at, updated_by, notes FROM intake_review_gate_ledger WHERE intake_id = ? AND workflow_key = ? AND document_key = ? AND gate_name = ? LIMIT 1`
- `services/services_intake.py:6795` — tables: `intake_review_gate_actions`
  - `SELECT action_key, action_label, resulting_status, note, created_at, created_by FROM intake_review_gate_actions WHERE intake_id = ? AND workflow_key = ? AND document_key = ? AND gate_name = ? ORDER BY id DESC`
- `services/services_intake.py:6885` — tables: `intake_review_gate_ledger`
  - `UPDATE intake_review_gate_ledger SET gate_status = ?, gate_reason = ?, updated_at = ?, updated_by = ?, notes = ? WHERE intake_id = ? AND workflow_key = ? AND document_key = ? AND gate_name = ?`
- `services/services_intake.py:7073` — tables: `intake_final_draft_prep_gate`
  - `SELECT admin_approved, approval_note FROM intake_final_draft_prep_gate WHERE intake_id = ? AND workflow_key = ? AND document_key = ? LIMIT 1`
- `services/services_intake.py:7151` — tables: `intake_final_draft_prep_gate`
  - `SELECT intake_id, workflow_key, document_key, gate_status, gate_reason, questionnaire_complete, open_issues_reviewed, open_tasks_reviewed, professional_review_recorded, required_documents_acknowledged, admin_approved, approval_note, created_at, updated_at, updated_by FROM intake_final_draft_prep_gate WHERE intake_id = ? AND workflow_key = ? AND document_key = ? LIMIT 1`
- `services/services_intake.py:7209` — tables: `intake_final_draft_prep_gate`
  - `UPDATE intake_final_draft_prep_gate SET gate_status = ?, gate_reason = ?, admin_approved = 1, approval_note = ?, updated_at = ?, updated_by = ? WHERE intake_id = ? AND workflow_key = ? AND document_key = ?`
- `services/services_intake.py:7242` — tables: `intake_final_draft_prep_gate`
  - `SELECT intake_id, workflow_key, document_key, gate_status, gate_reason, questionnaire_complete, open_issues_reviewed, open_tasks_reviewed, professional_review_recorded, required_documents_acknowledged, admin_approved, approval_note, updated_at, updated_by FROM intake_final_draft_prep_gate WHERE intake_id = ? ORDER BY updated_at DESC`
- `services/services_intake.py:7253` — tables: `intake_final_draft_prep_gate`
  - `SELECT intake_id, workflow_key, document_key, gate_status, gate_reason, questionnaire_complete, open_issues_reviewed, open_tasks_reviewed, professional_review_recorded, required_documents_acknowledged, admin_approved, approval_note, updated_at, updated_by FROM intake_final_draft_prep_gate ORDER BY updated_at DESC LIMIT 200`
- `services/services_intake.py:7332` — tables: `intake_final_draft_gate_actions`
  - `SELECT action_key, action_label, note, created_at, created_by FROM intake_final_draft_gate_actions WHERE intake_id = ? AND workflow_key = ? AND document_key = ? ORDER BY id DESC`
- `services/services_intake.py:7499` — tables: `intake_final_draft_prep_gate`
  - `SELECT admin_approved, approval_note FROM intake_final_draft_prep_gate WHERE intake_id = ? AND workflow_key = ? AND document_key = ? LIMIT 1`
- `services/services_intake.py:7666` — tables: `intake_final_draft_prep_gate`
  - `UPDATE intake_final_draft_prep_gate SET gate_status = ?, gate_reason = ?, admin_approved = 1, approval_note = ?, updated_at = ?, updated_by = ? WHERE intake_id = ? AND workflow_key = ? AND document_key = ?`
- `services/services_intake.py:7732` — tables: `intake_final_draft_admin_approvals`
  - `SELECT intake_id, workflow_key, document_key, approval_status, approval_note, gate_status_before, gate_status_after, created_at, created_by FROM intake_final_draft_admin_approvals`
- `services/services_intake.py:8067` — tables: `intake_final_draft_sections`
  - `SELECT id, section_order, section_heading, section_source, section_body, section_status, created_at, updated_at, updated_by FROM intake_final_draft_sections WHERE intake_id = ? AND workflow_key = ? AND document_key = ? ORDER BY section_order ASC`
- `services/services_intake.py:8101` — tables: `intake_final_draft_sections`
  - `SELECT id, section_order, section_heading, section_source, section_body, section_status, created_at, updated_at, updated_by FROM intake_final_draft_sections WHERE intake_id = ? AND workflow_key = ? AND document_key = ? AND id = ? LIMIT 1`
- `services/services_intake.py:8152` — tables: `intake_final_draft_sections`
  - `UPDATE intake_final_draft_sections SET section_heading = ?, section_body = ?, section_status = ?, updated_at = ?, updated_by = ? WHERE intake_id = ? AND workflow_key = ? AND document_key = ? AND id = ?`
- `services/services_intake.py:8445` — tables: `intake_final_draft_version_register`
  - `SELECT COUNT(*) FROM intake_final_draft_version_register WHERE intake_id = ? AND workflow_key = ? AND document_key = ?`
- `services/services_intake.py:8534` — tables: `intake_final_draft_version_register`
  - `SELECT intake_id, workflow_key, document_key, version_label, export_type, file_path, preview_status, ready_count, total_sections, preparation_classification, finality_status, created_at, created_by, notes FROM intake_final_draft_version_register`
- `services/services_intake.py:8720` — tables: `intake_final_draft_completion_gate`
  - `SELECT intake_id, workflow_key, document_key, gate_status, gate_reason, total_sections, ready_sections, not_ready_sections, latest_version_label, completion_note, completed_at, completed_by, created_at, updated_at, updated_by FROM intake_final_draft_completion_gate WHERE intake_id = ? AND workflow_key = ? AND document_key = ? LIMIT 1`
- `services/services_intake.py:8769` — tables: `intake_final_draft_completion_gate`
  - `SELECT gate_status, completion_note, completed_at, completed_by FROM intake_final_draft_completion_gate WHERE intake_id = ? AND workflow_key = ? AND document_key = ? LIMIT 1`
- `services/services_intake.py:8845` — tables: `intake_final_draft_completion_actions`
  - `SELECT action_status, note, created_at, created_by FROM intake_final_draft_completion_actions WHERE intake_id = ? AND workflow_key = ? AND document_key = ? ORDER BY id DESC`
- `services/services_intake.py:8893` — tables: `intake_final_draft_completion_gate`
  - `UPDATE intake_final_draft_completion_gate SET gate_status = ?, gate_reason = ?, completion_note = ?, completed_at = ?, completed_by = ?, updated_at = ?, updated_by = ? WHERE intake_id = ? AND workflow_key = ? AND document_key = ?`
- `services/services_matters.py:467` — tables: `matter_relationships`
  - `SELECT relationship_id FROM matter_relationships ORDER BY id DESC LIMIT 1`
- `package_export/database/db.py:165` — tables: `trusts`
  - `SELECT COUNT(*) AS count FROM trusts`
- `package_export/database/db.py:173` — tables: `trusts`
  - `INSERT INTO trusts ( trust_id, trust_name, short_name, jurisdiction, effective_date, trust_type, trust_purpose, accounting_method, workflow_mode, settlor_name, trustee_name, successor_trustee_name, beneficiary_name, record_visibility, workflow_mode_confirmed, ai_explanations, recommended_guidance, initial_corpus_description, property_mapping_timing, asset_categories, generate_schedule_recommendations, status ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
- `package_export/database/db.py:198` — tables: `trusts`
  - `SELECT * FROM trusts ORDER BY trust_id`
- `package_export/database/db.py:206` — tables: `trusts`
  - `SELECT * FROM trusts WHERE trust_id = ?`
- `package_export/database/db.py:216` — tables: `trusts`
  - `UPDATE trusts SET {fields} WHERE trust_id = ?`
- `package_export/database/db.py:223` — tables: `properties`
  - `SELECT COUNT(*) AS count FROM properties`
- `package_export/database/db.py:231` — tables: `properties`
  - `INSERT INTO properties ( property_id, trust_id, property_name, property_type, address_or_identifier, acquisition_date, title_notes, beneficial_notes, status, asset_class, asset_subtype, established_date, effective_date, review_date, expiration_date, responsible_party, custodian ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
- `package_export/database/db.py:253` — tables: `properties`
  - `SELECT * FROM properties WHERE property_id = ?`
- `package_export/database/db.py:261` — tables: `properties`
  - `SELECT * FROM properties WHERE trust_id = ? ORDER BY property_id`
- `package_export/database/db.py:269` — tables: `properties, trusts`
  - `SELECT p.*, t.trust_name FROM properties p LEFT JOIN trusts t ON p.trust_id = t.trust_id ORDER BY p.property_id`
- `package_export/database/db.py:282` — tables: `properties`
  - `SELECT COALESCE(asset_class, property_type, 'unclassified') AS asset_class, COUNT(*) AS count FROM properties GROUP BY COALESCE(asset_class, property_type, 'unclassified') ORDER BY asset_class`
- `package_export/database/db.py:295` — tables: `accounts`
  - `SELECT COUNT(*) AS count FROM accounts`
- `package_export/database/db.py:303` — tables: `accounts`
  - `INSERT INTO accounts ( account_id, trust_id, property_id, account_type, institution, account_label, masked_number, purpose ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
- `package_export/database/db.py:319` — tables: `accounts`
  - `SELECT * FROM accounts WHERE trust_id = ? ORDER BY account_id`
- `package_export/database/db.py:327` — tables: `accounts`
  - `SELECT * FROM accounts WHERE property_id = ? ORDER BY account_id`
- `package_export/database/db.py:335` — tables: `documents`
  - `SELECT COUNT(*) AS count FROM documents`
- `package_export/database/db.py:343` — tables: `documents`
  - `INSERT INTO documents ( document_id, trust_id, property_id, account_id, document_category, document_title, notes, original_filename, stored_filename, file_path ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
- `package_export/database/db.py:360` — tables: `documents`
  - `SELECT * FROM documents WHERE trust_id = ? ORDER BY document_id`
- `package_export/database/db.py:368` — tables: `documents`
  - `SELECT * FROM documents WHERE property_id = ? ORDER BY document_id`
- `package_export/database/db.py:376` — tables: `ledger_entries`
  - `SELECT COUNT(*) AS count FROM ledger_entries`
- `package_export/database/db.py:384` — tables: `ledger_entries`
  - `INSERT INTO ledger_entries ( entry_id, trust_id, property_id, account_id, entry_type, amount, entry_date, description, entry_category, accounting_method, recognition_date, due_date, paid_date, chart_account ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
- `package_export/database/db.py:403` — tables: `ledger_entries`
  - `SELECT * FROM ledger_entries WHERE trust_id = ? ORDER BY entry_id`
- `package_export/database/db.py:411` — tables: `ledger_entries`
  - `SELECT * FROM ledger_entries WHERE property_id = ? ORDER BY entry_id`
- `package_export/database/db.py:493` — tables: `properties`
  - `SELECT * FROM properties WHERE custodian IS NULL OR custodian = '' ORDER BY property_id`
- `package_export/database/db.py:501` — tables: `properties`
  - `SELECT * FROM properties WHERE review_date IS NULL OR review_date = '' ORDER BY property_id`
- `package_export/database/db.py:509` — tables: `properties`
  - `SELECT * FROM properties WHERE expiration_date IS NOT NULL AND expiration_date != '' ORDER BY expiration_date`
- `package_export/database/db.py:517` — tables: `properties`
  - `SELECT * FROM properties WHERE trust_id IS NULL OR trust_id = '' ORDER BY property_id`
- `package_export/database/db.py:535` — tables: `properties`
  - `SELECT * FROM properties WHERE {field_name} IS NOT NULL AND {field_name} != ''`
- `package_export/database/db.py:544` — tables: `properties`
  - `SELECT * FROM properties WHERE {field_name} IS NOT NULL AND {field_name} != ''`
- `package_export/database/db.py:759` — tables: `beneficiaries`
  - `SELECT COUNT(*) AS count FROM beneficiaries`
- `package_export/database/db.py:768` — tables: `distributions`
  - `SELECT COUNT(*) AS count FROM distributions`
- `package_export/database/db.py:777` — tables: `beneficiaries`
  - `INSERT INTO beneficiaries ( beneficiary_id, trust_id, full_name, tax_id, beneficiary_type, email, address, allocation_method, fixed_percentage, is_active, notes ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
- `package_export/database/db.py:797` — tables: `beneficiaries`
  - `UPDATE beneficiaries SET {fields} WHERE beneficiary_id = ?`
- `package_export/database/db.py:805` — tables: `beneficiaries`
  - `SELECT * FROM beneficiaries WHERE beneficiary_id = ?`
- `package_export/database/db.py:814` — tables: `beneficiaries`
  - `SELECT * FROM beneficiaries WHERE trust_id = ? ORDER BY full_name`
- `package_export/database/db.py:823` — tables: `distributions`
  - `INSERT INTO distributions ( distribution_id, trust_id, beneficiary_id, tax_year, distribution_date, distribution_type, description, gross_amount, taxable_amount, principal_amount, source_reference, status ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
- `package_export/database/db.py:844` — tables: `distributions`
  - `UPDATE distributions SET {fields} WHERE distribution_id = ?`
- `package_export/database/db.py:852` — tables: `distributions`
  - `SELECT * FROM distributions WHERE distribution_id = ?`
- `package_export/database/db.py:862` — tables: `beneficiaries, distributions`
  - `SELECT d.*, b.full_name AS beneficiary_name, b.tax_id AS beneficiary_tax_id FROM distributions d LEFT JOIN beneficiaries b ON d.beneficiary_id = b.beneficiary_id WHERE d.trust_id = ? AND d.tax_year = ? ORDER BY d.distribution_date DESC, d.distribution_id DESC`
- `package_export/database/db.py:870` — tables: `beneficiaries, distributions`
  - `SELECT d.*, b.full_name AS beneficiary_name, b.tax_id AS beneficiary_tax_id FROM distributions d LEFT JOIN beneficiaries b ON d.beneficiary_id = b.beneficiary_id WHERE d.trust_id = ? ORDER BY d.distribution_date DESC, d.distribution_id DESC`
- `package_export/database/db.py:949` — tables: `beneficiaries`
  - `SELECT * FROM beneficiaries WHERE beneficiary_id = ? AND trust_id = ?`
- `package_export/database/db.py:970` — tables: `beneficiaries, distributions`
  - `SELECT d.*, b.full_name AS beneficiary_name, b.tax_id AS beneficiary_tax_id FROM distributions d LEFT JOIN beneficiaries b ON d.beneficiary_id = b.beneficiary_id WHERE d.distribution_id = ? AND d.trust_id = ?`
- `package_export/database/db.py:1033` — tables: `ledger_entries`
  - `SELECT * FROM ledger_entries WHERE trust_id = ? ORDER BY entry_date DESC, entry_id DESC`
- `package_export/database/db.py:1123` — tables: `ledger_entries`
  - `SELECT * FROM ledger_entries WHERE trust_id = ? ORDER BY entry_date DESC, entry_id DESC`
- `package_export/database/db.py:1239` — tables: `instruments`
  - `SELECT COUNT(*) AS count FROM instruments`
- `package_export/database/db.py:1248` — tables: `instruments`
  - `INSERT INTO instruments ( instrument_id, trust_id, instrument_number, instrument_type, issue_date, maturity_date, face_value, backing_type, backing_reference, status, affidavit_reference, custody_reference, notes ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
- `package_export/database/db.py:1271` — tables: `instruments`
  - `UPDATE instruments SET {fields} WHERE instrument_id = ?`
- `package_export/database/db.py:1279` — tables: `instruments`
  - `SELECT * FROM instruments WHERE instrument_id = ?`
- `package_export/database/db.py:1288` — tables: `instruments`
  - `SELECT * FROM instruments WHERE trust_id = ? ORDER BY issue_date DESC, instrument_id DESC`
- `package_export/database/db.py:1301` — tables: `instruments`
  - `SELECT * FROM instruments ORDER BY issue_date DESC, instrument_id DESC`
- `package_export/database/db.py:1350` — tables: `instruments`
  - `SELECT COUNT(*) AS count FROM instruments`
- `package_export/database/db.py:1359` — tables: `instruments`
  - `INSERT INTO instruments ( instrument_id, trust_id, instrument_number, instrument_type, issue_date, maturity_date, face_value, backing_type, backing_reference, status, affidavit_reference, custody_reference, notes ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
- `package_export/database/db.py:1382` — tables: `instruments`
  - `UPDATE instruments SET {fields} WHERE instrument_id = ?`
- `package_export/database/db.py:1390` — tables: `instruments`
  - `SELECT * FROM instruments WHERE instrument_id = ?`
- `package_export/database/db.py:1399` — tables: `instruments`
  - `SELECT * FROM instruments WHERE trust_id = ? ORDER BY issue_date DESC, instrument_id DESC`
- `package_export/database/db.py:1412` — tables: `instruments`
  - `SELECT * FROM instruments ORDER BY issue_date DESC, instrument_id DESC`
- `package_export/database/db.py:1438` — tables: `instruments`
  - `SELECT status, COUNT(*) AS count FROM instruments WHERE trust_id = ? GROUP BY status`
- `package_export/database/db.py:1445` — tables: `instruments`
  - `SELECT status, COUNT(*) AS count FROM instruments GROUP BY status`

## Record Routes Without Obvious Scope Markers

- `app.py:2979` — `create_trust_step2_grantor` — `"/create_trust_step2_grantor/<trust_id>", methods=["GET", "POST"]`
- `app.py:3001` — `create_trust_step2` — `"/create_trust_step2/<trust_id>", methods=["GET", "POST"]`
- `app.py:3021` — `create_trust_step3` — `"/create_trust_step3/<trust_id>", methods=["GET", "POST"]`
- `app.py:3041` — `create_trust_step4` — `"/create_trust_step4/<trust_id>", methods=["GET", "POST"]`
- `app.py:3061` — `create_trust_step5` — `"/create_trust_step5/<trust_id>", methods=["GET", "POST"]`
- `app.py:3081` — `create_trust_step6` — `"/create_trust_step6/<trust_id>", methods=["GET", "POST"]`
- `app.py:3095` — `create_trust_step7` — `"/create_trust_step7/<trust_id>"`
- `app.py:6244` — `k1_trust_view` — `"/k1/trust/<trust_id>"`
- `app.py:6278` — `k1_new_beneficiary` — `"/k1/trust/<trust_id>/beneficiary/new", methods=["GET", "POST"]`
- `app.py:6327` — `k1_new_distribution` — `"/k1/trust/<trust_id>/distribution/new", methods=["GET", "POST"]`
- `app.py:6387` — `k1_year_end_summary` — `"/k1/trust/<trust_id>/year_end_summary"`
- `app.py:6450` — `form1041_preview` — `"/form1041/preview/<trust_id>"`
- `app.py:6457` — `form1041_print` — `"/form1041/print/<trust_id>"`
- `app.py:7471` — `trust_minute_certificate_pdf` — `"/minutes/<minute_id>/certificate.pdf"`
- `app.py:7549` — `trust_minute_execution_packet_pdf` — `"/minutes/<minute_id>/packet.pdf"`
- `app.py:7696` — `trust_minute_execute` — `"/minutes/<minute_id>/execute", methods=["POST"]`
- `app.py:7818` — `trust_minute_detail` — `"/minutes/<minute_id>"`
- `app.py:8025` — `k1_edit_beneficiary` — `"/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/edit", methods=["GET", "POST"]`
- `app.py:8064` — `k1_toggle_beneficiary` — `"/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/toggle", methods=["POST"]`
- `app.py:8073` — `k1_edit_distribution` — `"/k1/trust/<trust_id>/distribution/<distribution_id>/edit", methods=["GET", "POST"]`
- `app.py:9414` — `media_file` — `"/media/file/<media_id>"`
- `app.py:9456` — `k1_report_view` — `"/reports/k1/<trust_id>"`
- `app.py:9486` — `form1041_report_view` — `"/reports/1041/<trust_id>"`
- `app.py:9561` — `k1_report_print` — `"/reports/k1/<trust_id>/print"`
- `app.py:9593` — `form1041_report_print` — `"/reports/1041/<trust_id>/print"`
- `app.py:9896` — `trust_summary_pdf` — `"/reports/trust/<trust_id>/summary.pdf"`
- `app.py:9913` — `k1_readiness_pdf` — `"/reports/k1/trust/<trust_id>/<tax_year>.pdf"`
- `app.py:9946` — `ledger_report_pdf` — `"/reports/ledger/trust/<trust_id>.pdf"`
- `app.py:9956` — `form1041_report_pdf` — `"/reports/1041/trust/<trust_id>/<tax_year>.pdf"`
- `app.py:10344` — `video_trust_type` — `"/videos/trust-type/<trust_type>"`
- `app.py:10444` — `workspace_detail` — `"/workspaces/<workspace_id>"`
- `app.py:10469` — `workspace_edit` — `"/workspaces/<workspace_id>/edit", methods=["GET", "POST"]`
- `app.py:10493` — `workspace_note_new` — `"/workspaces/<workspace_id>/notes/new", methods=["GET", "POST"]`
- `app.py:10608` — `workspace_discussions` — `"/workspaces/<workspace_id>/discussions"`
- `app.py:10617` — `workspace_discussion_new` — `"/workspaces/<workspace_id>/discussions/new", methods=["GET", "POST"]`
- `app.py:10820` — `workspace_tasks` — `"/workspaces/<workspace_id>/tasks"`
- `app.py:10829` — `workspace_task_new` — `"/workspaces/<workspace_id>/tasks/new", methods=["GET", "POST"]`
- `app.py:10952` — `document_detail` — `"/documents/<document_id>"`
- `app.py:10969` — `workspace_documents` — `"/workspaces/<workspace_id>/documents"`
- `app.py:10978` — `workspace_document_generate` — `"/workspaces/<workspace_id>/documents/generate", methods=["GET", "POST"]`
- `app.py:11050` — `trust_post_create_review` — `"/trust/<trust_id>/post-create-review"`
- `app.py:11058` — `trust_formation_preview_hub` — `"/trust/<trust_id>/formation-preview-hub"`
- `app.py:11075` — `trust_successor_trustee_preview` — `"/trust/<trust_id>/successor-trustee-preview"`
- `app.py:11088` — `trust_successor_trustee_output_surface` — `"/trust/<trust_id>/successor-trustee-output-surface"`
- `app.py:11102` — `trust_successor_trustee_output_surface_pdf` — `"/trust/<trust_id>/successor-trustee-output-surface/pdf"`
- `app.py:11174` — `trust_general_assignment_preview` — `"/trust/<trust_id>/general-assignment-preview"`
- `app.py:11187` — `trust_general_assignment_output_surface` — `"/trust/<trust_id>/general-assignment-output-surface"`
- `app.py:11201` — `trust_general_assignment_output_surface_pdf` — `"/trust/<trust_id>/general-assignment-output-surface/pdf"`
- `app.py:11216` — `trust_organizational_minutes_preview` — `"/trust/<trust_id>/organizational-minutes-preview"`
- `app.py:11229` — `trust_organizational_minutes_output_surface` — `"/trust/<trust_id>/organizational-minutes-output-surface"`
- `app.py:11243` — `trust_organizational_minutes_output_surface_pdf` — `"/trust/<trust_id>/organizational-minutes-output-surface/pdf"`
- `app.py:11258` — `trust_trustee_acceptance_preview` — `"/trust/<trust_id>/trustee-acceptance-preview"`
- `app.py:11271` — `trust_trustee_acceptance_output_surface` — `"/trust/<trust_id>/trustee-acceptance-output-surface"`
- `app.py:11285` — `trust_trustee_acceptance_output_surface_pdf` — `"/trust/<trust_id>/trustee-acceptance-output-surface/pdf"`
- `app.py:11300` — `trust_articles_preview` — `"/trust/<trust_id>/articles-preview"`
- `app.py:11313` — `trust_declaration_output_surface` — `"/trust/<trust_id>/declaration-output-surface"`
- `app.py:11326` — `trust_declaration_output_surface_pdf` — `"/trust/<trust_id>/declaration-output-surface/pdf"`
- `app.py:11341` — `trust_certificate_of_trust_output_surface` — `"/trust/<trust_id>/certificate-of-trust-output-surface"`
- `app.py:11354` — `trust_certificate_of_trust_output_surface_pdf` — `"/trust/<trust_id>/certificate-of-trust-output-surface/pdf"`
- `app.py:11369` — `trust_articles_output_surface` — `"/trust/<trust_id>/articles-output-surface"`
- `app.py:11384` — `trust_articles_output_surface_pdf` — `"/trust/<trust_id>/articles-output-surface/pdf"`
- `app.py:15054` — `trust_dynamic_declaration` — `"/trust/<trust_id>/dynamic-declaration"`
- `app.py:15151` — `trust_dynamic_declaration_pdf` — `"/trust/<trust_id>/dynamic-declaration/pdf"`
- `app.py:15178` — `trust_article_assignments` — `"/trust/<trust_id>/article-assignments"`
- `app.py:15209` — `trust_article_assignment_add` — `"/trust/<trust_id>/article-assignments/add", methods=["POST"]`
- `app.py:15272` — `intake_universal_profile` — `"/intake/<intake_id>/universal-profile", methods=["GET", "POST"]`
- `app.py:17857` — `intake_saved_snapshot` — `"/intake/<intake_id>/snapshot"`
- `app.py:17890` — `intake_resume` — `"/intake/<intake_id>/resume"`
- `app.py:17904` — `intake_export_prep` — `"/intake/<intake_id>/export-prep"`
- `app.py:17920` — `intake_add_review_note` — `"/intake/<intake_id>/notes/add", methods=["POST"]`
- `app.py:17938` — `intake_add_followup_task` — `"/intake/<intake_id>/tasks/add", methods=["POST"]`
- `app.py:17958` — `intake_update_followup_task_status` — `"/intake/<intake_id>/tasks/<int:task_id>/status", methods=["POST"]`
- `app.py:17973` — `intake_followup_packet` — `"/intake/<intake_id>/packet"`
- `app.py:17990` — `intake_followup_packet_docx` — `"/intake/<intake_id>/packet/docx"`
- `app.py:18004` — `intake_followup_packet_pdf` — `"/intake/<intake_id>/packet/pdf"`
- `app.py:18033` — `intake_export_history_detail` — `"/intake/<intake_id>/exports"`
- `app.py:18059` — `intake_document_recommendations` — `"/intake/<intake_id>/recommendations"`
- `app.py:18084` — `intake_update_recommendation_status` — `"/intake/<intake_id>/recommendations/<workflow_key>/status", methods=["POST"]`
- `app.py:18100` — `intake_workflow_launch_prep` — `"/intake/<intake_id>/recommendations/<workflow_key>/launch-prep"`
- `app.py:18121` — `intake_workflow_bridge` — `"/intake/<intake_id>/recommendations/<workflow_key>/bridge", methods=["GET", "POST"]`
- `app.py:18203` — `intake_workflow_bridge_summary` — `"/intake/<intake_id>/recommendations/<workflow_key>/bridge-summary"`
- `app.py:18217` — `intake_workflow_draft_packet` — `"/intake/<intake_id>/recommendations/<workflow_key>/draft-packet"`
- `app.py:18238` — `intake_workflow_draft_packet_docx` — `"/intake/<intake_id>/recommendations/<workflow_key>/draft-packet/docx"`
- `app.py:18263` — `intake_draft_readiness_ledger_detail` — `"/intake/<intake_id>/draft-readiness"`
- `app.py:18273` — `intake_document_draft_choose` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft"`
- `app.py:18291` — `intake_document_draft_questionnaire` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>", methods=["GET", "POST"]`
- `app.py:18330` — `intake_document_draft_preview` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/preview"`
- `app.py:18344` — `intake_nonfinal_draft_document` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/nonfinal"`
- `app.py:18371` — `intake_nonfinal_draft_docx` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/nonfinal/docx"`
- `app.py:18402` — `intake_review_gate_ledger_detail` — `"/intake/<intake_id>/review-gates"`
- `app.py:18412` — `intake_review_gate_detail` — `"/intake/<intake_id>/review-gates/<workflow_key>/<document_key>"`
- `app.py:18430` — `intake_review_gate_resolve` — `"/intake/<intake_id>/review-gates/<workflow_key>/<document_key>/resolve", methods=["POST"]`
- `app.py:18452` — `intake_final_draft_gate_ledger_detail` — `"/intake/<intake_id>/final-draft-gate"`
- `app.py:18474` — `intake_final_draft_gate_detail` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate"`
- `app.py:18495` — `intake_final_draft_gate_approve` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate/approve", methods=["POST"]`
- `app.py:18516` — `intake_final_draft_gate_resolution` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-gate/resolve", methods=["GET", "POST"]`
- `app.py:18561` — `intake_final_draft_admin_approval` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/admin-approval", methods=["GET", "POST"]`
- `app.py:18604` — `intake_final_draft_admin_approval_ledger_detail` — `"/intake/<intake_id>/final-draft-approvals"`
- `app.py:18615` — `intake_final_draft_workspace` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-workspace"`
- `app.py:18629` — `intake_final_draft_section_editor` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-section-editor"`
- `app.py:18640` — `intake_final_draft_section_edit` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-section-editor/<int:section_id>", methods=["GET", "POST"]`
- `app.py:18682` — `intake_final_draft_preview` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-preview"`
- `app.py:18692` — `intake_final_draft_preview_docx` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-preview/docx"`
- `app.py:18722` — `intake_final_draft_version_register_intake` — `"/intake/<intake_id>/final-draft-version-register"`
- `app.py:18731` — `intake_final_draft_version_register_detail` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-draft-version-register"`
- `app.py:18744` — `intake_final_draft_completion_gate` — `"/intake/<intake_id>/recommendations/<workflow_key>/document-draft/<document_key>/final-completion-gate", methods=["GET", "POST"]`
- `app.py:18777` — `intake_trust_instrument_menu` — `"/intake/<intake_id>/trust-instruments"`
- `app.py:18787` — `intake_instrument_draft_packet` — `"/intake/<intake_id>/recommendations/<workflow_key>/instrument-draft-packet"`
- `app.py:19062` — `matter_governance_state` — `"/matters/<matter_id>/governance", methods=["POST"]`
- `app.py:19090` — `matter_risk_update` — `"/matters/<matter_id>/risk", methods=["POST"]`
- `app.py:19114` — `matter_detail` — `"/matters/<matter_id>"`
- `app.py:19127` — `matter_relationship_detail` — `"/matters/<matter_id>/relationships/<relationship_id>"`
- `app.py:19207` — `matter_relationship_clearance` — `"/matters/<matter_id>/relationships/" "<relationship_id>/clearance", methods=["POST"]`
- `app.py:19249` — `matter_relationship_relink` — `"/matters/<matter_id>/relationships/" "<relationship_id>/relink", methods=["POST"]`
- `app.py:19296` — `matter_relationship_validate_link` — `"/matters/<matter_id>/relationships/" "<relationship_id>/validate-link", methods=["POST"]`
- `app.py:19335` — `matter_relationship_verification_update` — `"/matters/<matter_id>/relationships/" "<relationship_id>/verification", methods=["POST"]`
- `app.py:19384` — `matter_relationship_status_update` — `"/matters/<matter_id>/relationships/<relationship_id>/status", methods=["POST"]`
- `app.py:19418` — `new_matter_relationship` — `"/matters/<matter_id>/relationships/new", methods=["GET", "POST"]`
- `app.py:19458` — `new_matter_event` — `"/matters/<matter_id>/events/new", methods=["GET", "POST"]`
- `package_export/app.py:215` — `create_trust_step2` — `"/create_trust_step2/<trust_id>", methods=["GET", "POST"]`
- `package_export/app.py:231` — `create_trust_step3` — `"/create_trust_step3/<trust_id>", methods=["GET", "POST"]`
- `package_export/app.py:247` — `create_trust_step4` — `"/create_trust_step4/<trust_id>", methods=["GET", "POST"]`
- `package_export/app.py:263` — `create_trust_step5` — `"/create_trust_step5/<trust_id>", methods=["GET", "POST"]`
- `package_export/app.py:279` — `create_trust_step6` — `"/create_trust_step6/<trust_id>", methods=["GET", "POST"]`
- `package_export/app.py:289` — `create_trust_step7` — `"/create_trust_step7/<trust_id>"`
- `package_export/app.py:407` — `trust_detail` — `"/trust/<trust_id>"`
- `package_export/app.py:452` — `k1_trust_view` — `"/k1/trust/<trust_id>"`
- `package_export/app.py:469` — `k1_new_beneficiary` — `"/k1/trust/<trust_id>/beneficiary/new", methods=["GET", "POST"]`
- `package_export/app.py:489` — `k1_new_distribution` — `"/k1/trust/<trust_id>/distribution/new", methods=["GET", "POST"]`
- `package_export/app.py:511` — `k1_year_end_summary` — `"/k1/trust/<trust_id>/year_end_summary"`
- `package_export/app.py:542` — `form1041_preview` — `"/form1041/preview/<trust_id>"`
- `package_export/app.py:549` — `form1041_print` — `"/form1041/print/<trust_id>"`
- `package_export/app.py:665` — `k1_edit_beneficiary` — `"/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/edit", methods=["GET", "POST"]`
- `package_export/app.py:687` — `k1_toggle_beneficiary` — `"/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/toggle", methods=["POST"]`
- `package_export/app.py:693` — `k1_edit_distribution` — `"/k1/trust/<trust_id>/distribution/<distribution_id>/edit", methods=["GET", "POST"]`
- `package_export/app.py:722` — `k1_export_csv` — `"/k1/trust/<trust_id>/export.csv"`

## Interpretation Rule

These are audit candidates, not automatic defects. Dynamic helper functions, decorators, globally shared catalogs, and tenant-local identifier reuse may explain some findings.
