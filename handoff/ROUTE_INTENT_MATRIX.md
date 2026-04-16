# ROUTE INTENT MATRIX

| Route | Function | Current Purpose | Intended Role Exposure | Notes |
|---|---|---|---|---|
| `/` | `home` | Trustee Dashboard / main landing | Admin, Trustee, Viewer (recommended explicit) | Template says "Trustee Dashboard" |
| `/workflow` | `workflow_hub` | Workflow Hub / operational continuity page | Admin, Trustee (recommended explicit) | Currently exposed in nav |
| `/admin` | `admin_index` | Admin control panel | Admin only | Confirmed |
| `/exports` | `export_center` | Export center | Admin, Trustee | Confirmed in ROLE_RULES |
| `/audit` | `audit_dashboard` | Audit log / system oversight | Admin only | Confirmed mismatch previously with nav |
| `/portfolio` | `portfolio_dashboard` | Multi-trust portfolio view | Admin, Trustee, Viewer (recommended explicit) | Also used as Viewer redirect target |
| `/fiduciaries` | `fiduciary_dashboard` | Fiduciary role layer | Admin, Trustee | Not trustee home |
| `/genealogy` | `genealogy_dashboard` | Genealogy layer | Admin, Trustee | Confirmed |
| `/media` | `media_dashboard` | Media / evidence layer | Admin, Trustee | Confirmed |
| `/roles` | `role_dashboard` | Role management | Admin only | Confirmed |
| `/permissions` | `permissions_dashboard` | Permissions dashboard | Admin only | Confirmed |
| `/security` | `security_dashboard` | Security dashboard | Admin only | Confirmed |
| `/reports` | `report_center` | Report center | Admin, Trustee | Confirmed |
| `/learning` | `learning_dashboard` | Learning resources | Admin, Trustee, Viewer | Confirmed |
| `/videos` | `video_dashboard` | Video resources | Admin, Trustee, Viewer | Confirmed |
| `/workspaces` | `workspace_dashboard` | Workspace layer | Admin, Trustee, Viewer | Confirmed |
| `/discussions` | `discussion_dashboard` | Discussion layer | Admin, Trustee, Viewer | Confirmed |
| `/decision` | `decision_dashboard` | Decision layer | Admin, Trustee, Viewer | Confirmed |
| `/execution` | `execution_dashboard` | Execution layer | Admin, Trustee, Viewer | Confirmed |
| `/documents` | `document_dashboard` | Generated documents layer | Admin, Trustee, Viewer | Confirmed |
| `/visualization` | `visualization_dashboard` | Visualization layer | Admin, Trustee, Viewer | Confirmed |
