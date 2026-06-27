# UPA-1B-6B-4A — Three-Application Identity and Isolation Audit

Generated: 2026-06-14T12:02:47.694275
Status: **THREE_APPLICATION_ALIGNMENT_REVIEW_REQUIRED**

## Declared Roles

- `trustee-app-clean` — Firm 1 / primary application
- `trustee-app-private` — Firm 2 / private testing application
- `trustee-app-clean_ALIGNED_PHASE8E_20260429_072701` — historical or alignment snapshot pending verification

## Summary

- Applications Expected: **3**
- Applications Found: **3**
- Applications Missing: **0**
- Firm2 Only Database Candidates: **0**
- Mixed Database Instances: **1**
- Blockers: **2**

## Application Results

### `trustee-app-clean`

- Exists: **True**
- Git branch: `strapback/stable-661bb66`
- Git HEAD: `1cf6497598d9d294bc0453847b896316f863c241`
- Last commit: `1cf6497598d9d294bc0453847b896316f863c241|2026-06-13T14:41:22-04:00|Complete IC-1 relationship audit summary and closeout gate`
- Git status: `?? audit/`
- Database files: **5**
  - `C:\Users\LunaMishoe\Desktop\trustee-app-clean\data\database.db`
    - firms: `[]`
    - row counts: `{}`
    - null-firm rows: **0**
  - `C:\Users\LunaMishoe\Desktop\trustee-app-clean\data\trustee_app.db`
    - firms: `['FIRM-001']`
    - row counts: `{'FIRM-001': 123}`
    - null-firm rows: **3**
  - `C:\Users\LunaMishoe\Desktop\trustee-app-clean\database\app.db`
    - firms: `[]`
    - row counts: `{}`
    - null-firm rows: **0**
  - `C:\Users\LunaMishoe\Desktop\trustee-app-clean\database.db`
    - firms: `[]`
    - row counts: `{}`
    - null-firm rows: **0**
  - `C:\Users\LunaMishoe\Desktop\trustee-app-clean\trustee_app.db`
    - firms: `['FIRM-001', 'FIRM-002']`
    - row counts: `{'FIRM-001': 395, 'FIRM-002': 351}`
    - null-firm rows: **6**

### `trustee-app-clean_ALIGNED_PHASE8E_20260429_072701`

- Exists: **True**
- Git branch: `strapback/stable-661bb66`
- Git HEAD: `4a2b5882296981c96a4c8f15339799b7bbd78ff2`
- Last commit: `4a2b5882296981c96a4c8f15339799b7bbd78ff2|2026-04-29T07:18:08-04:00|Initialize permission matrix tables on startup`
- Git status: `D FULL_SYSTEM_HANDOFF.txt
 D KNOWN_ISSUES_WATCHLIST_V1.txt
 D PHASE9_TRACK_C_STATUS.txt
 D POST_CREATE_CONSOLE_CHECKPOINT.txt
 D QA_CHECKLIST_V1.txt
 D RELEASE_READINESS_V1.txt
 D REPORT_SUBSYSTEM_HANDOFF.txt
 D ROUTE_TEST_MATRIX_V1.txt
 D VERSION_SUMMARY_V1.txt
 D app.py
 D app.py.BACKUP_BEFORE_FIX
 D backups_sqlite_export_center/_nav.html.bak
 D backups_sqlite_export_center/admin_index.html.bak
 D backups_sqlite_export_center/app.py.bak
 D backups_sqlite_export_generation/app.py.bak
 D backups_sqlite_export_generation/export_center.html.bak
 D backups_sqlite_instruments/app.py.bak
 D backups_sqlite_instruments/db.py.bak
 D backups_sqlite_k1/app.py.bak
 D backups_sqlite_k1/db.py.bak
 D backups_sqlite_k1_phase_a/app.py.bak
 D backups_sqlite_k1_phase_a/db.py.bak
 D backups_sqlite_k1_phase_a/k1_readiness.html.bak
 D backups_sqlite_packaging/admin_index.html.bak
 D backups_sqlite_packaging/app.py.bak
 D backups_sqlite_route_cleanup/app.py.bak
 D backups_sqlite_ui_polish/_nav.html.bak
 D backups_sqlite_ui_polish/admin_index.html.bak
 D backups_sqlite_ui_polish/form1041_dashboard.html.bak
 D backups_sqlite_ui_polish/instrument_dashboard.html.bak
 D backups_sqlite_ui_polish/k1_dashboard.html.bak
 D backups_sqlite_ui_polish/workflow_hub.html.bak
 D data/trustee_app.db
 D database/app.db
 D database/db.py
 D deployment/DEPLOYMENT_CHECKLIST.txt
 D deployment/start_gunicorn_example.txt
 D extensions.py
 D pdf_utils.py
 D requirements.txt
 D roadmap/FEATURE_ROADMAP.md
 D roadmap/PRIORITY_QUEUE.txt
 D security/SECURITY_CHECKLIST.txt
 D static/trust_ui.css
 D templates/_create_trust_progress.html
 D templates/_platform_nav.html
 D templates/_platform_shell.html
 D templates/access_denied.html
 D templates/add_property.html
 D templates/admin_index.html
 D templates/analytics_dashboard.html
 D templates/audit_dashboard.html
 D templates/audit_log_viewer.html
 D templates/auth/login.html
 D templates/bootstrap_admin_once.html
 D templates/change_password.html
 D templates/create_trust_launch.html
 D templates/create_trust_step2_grantor.html
 D templates/decision_dashboard.html
 D templates/decision_result.html
 D templates/discussion_dashboard.html
 D templates/discussion_form.html
 D templates/discussion_thread.html
 D templates/document_dashboard.html
 D templates/document_detail.html
 D templates/document_generate_form.html
 D templates/execution_dashboard.html
 D templates/execution_task_detail.html
 D templates/execution_task_form.html
 D templates/fiduciary_dashboard.html
 D templates/financial_summary.html
 D templates/form1041_dashboard.html
 D templates/form1041_preview.html
 D templates/form_1041.html
 D templates/form_guide_form.html
 D templates/genealogy_dashboard.html
 D templates/genealogy_form.html
 D templates/guide_page.html
 D templates/instrument_create.html
 D templates/instrument_dashboard.html
 D templates/instrument_print.html
 D templates/k1_beneficiary_edit.html
 D templates/k1_dashboard.html
 D templates/k1_distribution_edit.html
 D templates/k1_year_end_summary.html
 D templates/learning_article.html
 D templates/learning_article_form.html
 D templates/learning_category.html
 D templates/learning_dashboard.html
 D templates/media_dashboard.html
 D templates/media_form.html
 D templates/portfolio_dashboard.html
 D templates/report_center.html
 D templates/role_dashboard.html
 D templates/security_dashboard.html
 D templates/tax_assistant.html
 D templates/transfer_asset.html
 D templates/transfer_assignment.html
 D templates/transfer_bank_support_docs.html
 D templates/transfer_classification.html
 D templates/transfer_control_evidence.html
 D templates/transfer_detail.html
 D templates/transfer_document_support_docs.html
 D templates/transfer_execution_dashboard.html
 D templates/transfer_instruction_template.html
 D templates/transfer_optional_support_docs.html
 D templates/transfer_personal_property_support_docs.html
 D templates/transfer_print_view.html
 D templates/transfer_recommended_support_docs.html
 D templates/transfer_records.html
 D templates/transfer_review.html
 D templates/transfer_start.html
 D templates/transfer_support_doc_edit.html
 D templates/transfer_template_center.html
 D templates/transfer_trustee_acceptance.html
 D templates/trust_articles_output_surface.html
 D templates/trust_formation_preview_hub.html
 D templates/trust_general_assignment_output_surface.html
 D templates/trust_general_assignment_preview.html
 D templates/trust_map_dashboard.html
 D templates/trust_organizational_minutes_output_surface.html
 D templates/trust_organizational_minutes_preview.html
 D templates/trust_packet_preview.html
 D templates/trust_successor_trustee_output_surface.html
 D templates/trust_successor_trustee_preview.html
 D templates/trust_trustee_acceptance_output_surface.html
 D templates/trust_trustee_acceptance_preview.html
 D templates/trust_type_index.html
 D templates/user_dashboard.html
 D templates/user_edit.html
 D templates/user_form.html
 D templates/user_reset_password.html
 D templates/video_category.html
 D templates/video_dashboard.html
 D templates/video_detail.html
 D templates/visualization_dashboard.html
 D templates/workflow_hub.html
 D templates/workspace_dashboard.html
 D templates/workspace_detail.html
 D templates/workspace_documents.html
 D templates/workspace_tasks.html`
- Database files: **0**

### `trustee-app-private`

- Exists: **True**
- Git branch: `main`
- Git HEAD: `3d20171a529e7f9a6ae20fd616929021e6955a59`
- Last commit: `3d20171a529e7f9a6ae20fd616929021e6955a59|2026-05-06T13:21:58-04:00|Your message`
- Git status: `clean`
- Database files: **2**
  - `C:\Users\LunaMishoe\Desktop\trustee-app-private\data\trustee_app.db`
    - firms: `['FIRM-001']`
    - row counts: `{'FIRM-001': 123}`
    - null-firm rows: **3**
  - `C:\Users\LunaMishoe\Desktop\trustee-app-private\database\app.db`
    - firms: `[]`
    - row counts: `{}`
    - null-firm rows: **0**

## Code Comparisons

- `trustee-app-clean` vs `trustee-app-private`
  - app.py same: **False**
  - database/db.py same: **False**
  - requirements same: **False**
- `trustee-app-clean` vs `trustee-app-clean_ALIGNED_PHASE8E_20260429_072701`
  - app.py same: **False**
  - database/db.py same: **False**
  - requirements same: **False**
- `trustee-app-private` vs `trustee-app-clean_ALIGNED_PHASE8E_20260429_072701`
  - app.py same: **False**
  - database/db.py same: **False**
  - requirements same: **False**

## Blockers

- 1 database(s) contain both FIRM-001 and FIRM-002.
- No database containing only FIRM-002 was identified.
