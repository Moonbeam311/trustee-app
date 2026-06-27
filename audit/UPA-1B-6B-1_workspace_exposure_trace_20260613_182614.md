# UPA-1B-6B-1 — Workspace Exposure and Sandbox Mutation Trace

Generated: 2026-06-13T18:26:15.086148
Status: **CONFIRMED_WORKSPACE_CROSS_FIRM_EXPOSURE**
Source: `audit\UPA-1B-6B_runtime_verification_20260613_182046.json`

## Database Safety

- Live database unchanged: **True**
- Sandbox unchanged during this trace: **True**

## Summary

- Workspace Rows For Repeated Owner: **7**
- Exposure Events: **2**
- Source Trace Locations: **133**
- Database Tables Changed In Sandbox: **2**
- Workspace Indexes: **1**
- Workspace Foreign Keys: **0**

## Exposure Events

### Exposure 1

- Active firm: `FIRM-002`
- Route: `/discussions/new`
- Source: `app.py:10528`
- Function: `discussion_new`
- Status: `200`
- Opposite-firm markers: `['admin']`

### Exposure 2

- Active firm: `FIRM-002`
- Route: `/documents/generate`
- Source: `app.py:10888`
- Function: `document_generate`
- Status: `200`
- Opposite-firm markers: `['admin']`


## Workspace Rows

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

## Workspace Indexes

```json
[
  {
    "sequence": 0,
    "name": "sqlite_autoindex_workspaces_1",
    "unique": true,
    "origin": "pk",
    "partial": false,
    "columns": [
      "workspace_id"
    ]
  }
]
```

## Source Trace

### `app.py:360`

- Scope markers: `firm_id`

```python
345:         DB_PATH.parent.mkdir(parents=True, exist_ok=True)
346: 
347:         conn = sqlite3.connect(DB_PATH)
348:         conn.row_factory = sqlite3.Row
349:         cur = conn.cursor()
350: 
351:         # Core hosted user table.
352:         cur.execute("""
353:             CREATE TABLE IF NOT EXISTS app_users (
354:                 user_id TEXT PRIMARY KEY,
355:                 username TEXT UNIQUE,
356:                 password_hash TEXT,
357:                 role_name TEXT,
358:                 status TEXT,
359:                 firm_id TEXT,
360:                 owner_id TEXT
361:             )
362:         """)
363: 
364:         cur.execute("PRAGMA table_info(app_users)")
365:         app_user_cols = [r["name"] for r in cur.fetchall()]
366:         for col, col_type in [
367:             ("password_hash", "TEXT"),
368:             ("role_name", "TEXT"),
369:             ("status", "TEXT"),
370:             ("firm_id", "TEXT"),
371:             ("owner_id", "TEXT"),
372:         ]:
373:             if col not in app_user_cols:
374:                 cur.execute(f"ALTER TABLE app_users ADD COLUMN {col} {col_type}")
375: 
376:         # Create/update hosted admin user every startup while ENSURE_HOSTED_ADMIN=1.
377:         password_hash = generate_password_hash(password)
378: 
379:         cur.execute(
380:             "SELECT user_id FROM app_users WHERE TRIM(LOWER(username)) = TRIM(LOWER(?))",
381:             (username,)
382:         )
383:         existing = cur.fetchone()
384: 
385:         if existing:
```

### `app.py:371`

- Scope markers: `firm_id`

```python
356:                 password_hash TEXT,
357:                 role_name TEXT,
358:                 status TEXT,
359:                 firm_id TEXT,
360:                 owner_id TEXT
361:             )
362:         """)
363: 
364:         cur.execute("PRAGMA table_info(app_users)")
365:         app_user_cols = [r["name"] for r in cur.fetchall()]
366:         for col, col_type in [
367:             ("password_hash", "TEXT"),
368:             ("role_name", "TEXT"),
369:             ("status", "TEXT"),
370:             ("firm_id", "TEXT"),
371:             ("owner_id", "TEXT"),
372:         ]:
373:             if col not in app_user_cols:
374:                 cur.execute(f"ALTER TABLE app_users ADD COLUMN {col} {col_type}")
375: 
376:         # Create/update hosted admin user every startup while ENSURE_HOSTED_ADMIN=1.
377:         password_hash = generate_password_hash(password)
378: 
379:         cur.execute(
380:             "SELECT user_id FROM app_users WHERE TRIM(LOWER(username)) = TRIM(LOWER(?))",
381:             (username,)
382:         )
383:         existing = cur.fetchone()
384: 
385:         if existing:
386:             cur.execute("""
387:                 UPDATE app_users
388:                 SET username = ?,
389:                     password_hash = ?,
390:                     role_name = 'Admin',
391:                     status = 'active',
392:                     firm_id = ?,
393:                     owner_id = 'ADMIN_OWNER_001'
394:                 WHERE user_id = ?
395:             """, (username, password_hash, firm_id, existing["user_id"]))
396:             user_action = "updated"
```

### `app.py:393`

- Scope markers: `firm_id`

```python
378: 
379:         cur.execute(
380:             "SELECT user_id FROM app_users WHERE TRIM(LOWER(username)) = TRIM(LOWER(?))",
381:             (username,)
382:         )
383:         existing = cur.fetchone()
384: 
385:         if existing:
386:             cur.execute("""
387:                 UPDATE app_users
388:                 SET username = ?,
389:                     password_hash = ?,
390:                     role_name = 'Admin',
391:                     status = 'active',
392:                     firm_id = ?,
393:                     owner_id = 'ADMIN_OWNER_001'
394:                 WHERE user_id = ?
395:             """, (username, password_hash, firm_id, existing["user_id"]))
396:             user_action = "updated"
397:         else:
398:             cur.execute("SELECT COUNT(*) AS count FROM app_users")
399:             count = cur.fetchone()["count"]
400:             user_id = f"USER-{count + 1:03d}"
401:             cur.execute("""
402:                 INSERT INTO app_users (
403:                     user_id, username, password_hash, role_name, status, firm_id, owner_id
404:                 ) VALUES (?, ?, ?, 'Admin', 'active', ?, 'ADMIN_OWNER_001')
405:             """, (user_id, username, password_hash, firm_id))
406:             user_action = "created"
407: 
408:         # Permissions + role matrix.
409:         cur.execute("""
410:             CREATE TABLE IF NOT EXISTS permissions (
411:                 permission_id TEXT PRIMARY KEY,
412:                 permission_name TEXT UNIQUE,
413:                 description TEXT
414:             )
415:         """)
416: 
417:         cur.execute("""
418:             CREATE TABLE IF NOT EXISTS role_permissions (
```

### `app.py:403`

- Scope markers: `firm_id`

```python
388:                 SET username = ?,
389:                     password_hash = ?,
390:                     role_name = 'Admin',
391:                     status = 'active',
392:                     firm_id = ?,
393:                     owner_id = 'ADMIN_OWNER_001'
394:                 WHERE user_id = ?
395:             """, (username, password_hash, firm_id, existing["user_id"]))
396:             user_action = "updated"
397:         else:
398:             cur.execute("SELECT COUNT(*) AS count FROM app_users")
399:             count = cur.fetchone()["count"]
400:             user_id = f"USER-{count + 1:03d}"
401:             cur.execute("""
402:                 INSERT INTO app_users (
403:                     user_id, username, password_hash, role_name, status, firm_id, owner_id
404:                 ) VALUES (?, ?, ?, 'Admin', 'active', ?, 'ADMIN_OWNER_001')
405:             """, (user_id, username, password_hash, firm_id))
406:             user_action = "created"
407: 
408:         # Permissions + role matrix.
409:         cur.execute("""
410:             CREATE TABLE IF NOT EXISTS permissions (
411:                 permission_id TEXT PRIMARY KEY,
412:                 permission_name TEXT UNIQUE,
413:                 description TEXT
414:             )
415:         """)
416: 
417:         cur.execute("""
418:             CREATE TABLE IF NOT EXISTS role_permissions (
419:                 id INTEGER PRIMARY KEY AUTOINCREMENT,
420:                 role_name TEXT,
421:                 permission_name TEXT,
422:                 UNIQUE(role_name, permission_name)
423:             )
424:         """)
425: 
426:         default_permissions = [
427:             ("PERM-001", "view_dashboard", "View dashboards and core system pages"),
428:             ("PERM-002", "create_trust", "Create trust records"),
```

### `app.py:404`

- Scope markers: `firm_id`

```python
389:                     password_hash = ?,
390:                     role_name = 'Admin',
391:                     status = 'active',
392:                     firm_id = ?,
393:                     owner_id = 'ADMIN_OWNER_001'
394:                 WHERE user_id = ?
395:             """, (username, password_hash, firm_id, existing["user_id"]))
396:             user_action = "updated"
397:         else:
398:             cur.execute("SELECT COUNT(*) AS count FROM app_users")
399:             count = cur.fetchone()["count"]
400:             user_id = f"USER-{count + 1:03d}"
401:             cur.execute("""
402:                 INSERT INTO app_users (
403:                     user_id, username, password_hash, role_name, status, firm_id, owner_id
404:                 ) VALUES (?, ?, ?, 'Admin', 'active', ?, 'ADMIN_OWNER_001')
405:             """, (user_id, username, password_hash, firm_id))
406:             user_action = "created"
407: 
408:         # Permissions + role matrix.
409:         cur.execute("""
410:             CREATE TABLE IF NOT EXISTS permissions (
411:                 permission_id TEXT PRIMARY KEY,
412:                 permission_name TEXT UNIQUE,
413:                 description TEXT
414:             )
415:         """)
416: 
417:         cur.execute("""
418:             CREATE TABLE IF NOT EXISTS role_permissions (
419:                 id INTEGER PRIMARY KEY AUTOINCREMENT,
420:                 role_name TEXT,
421:                 permission_name TEXT,
422:                 UNIQUE(role_name, permission_name)
423:             )
424:         """)
425: 
426:         default_permissions = [
427:             ("PERM-001", "view_dashboard", "View dashboards and core system pages"),
428:             ("PERM-002", "create_trust", "Create trust records"),
429:             ("PERM-003", "edit_trust", "Edit trust records"),
```

### `app.py:477`

- Scope markers: `firm_id`

```python
462:         for permission_name in admin_permissions:
463:             cur.execute("""
464:                 INSERT OR IGNORE INTO role_permissions (role_name, permission_name)
465:                 VALUES ('Admin', ?)
466:             """, (permission_name,))
467: 
468:         # Firm-scoped table repair.
469:         firm_tables = [
470:             "trusts",
471:             "audit_log",
472:             "transfers",
473:             "trust_minutes",
474:             "documents",
475:             "generated_documents",
476:             "media_records",
477:             "workspaces",
478:             "workspace_notes",
479:             "execution_tasks",
480:             "user_roles",
481:             "fiduciaries",
482:             "properties",
483:             "accounts",
484:             "beneficiaries",
485:             "distributions",
486:             "instruments",
487:             "ledger_entries",
488:         ]
489: 
490:         for table in firm_tables:
491:             cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
492:             if not cur.fetchone():
493:                 continue
494: 
495:             cur.execute(f"PRAGMA table_info({table})")
496:             cols = [r["name"] for r in cur.fetchall()]
497:             if "firm_id" not in cols:
498:                 cur.execute(f"ALTER TABLE {table} ADD COLUMN firm_id TEXT")
499: 
500:             cur.execute(f"""
501:                 UPDATE {table}
502:                 SET firm_id = ?
```

### `app.py:613`

- Scope markers: `firm_id`

```python
598: 
599:         cur.execute("PRAGMA table_info(trusts)")
600:         cols = [r["name"] for r in cur.fetchall()]
601:         for col_name, col_type in [
602:             ("grantor_name", "TEXT"),
603:             ("grantor_type", "TEXT"),
604:             ("grantor_contact", "TEXT"),
605:             ("seal_path", "TEXT"),
606:             ("caf_number", "TEXT"),
607:             ("crid_number", "TEXT"),
608:             ("trust_motto", "TEXT"),
609:             ("foundation_scripture", "TEXT"),
610:             ("prepared_by", "TEXT"),
611:             ("return_to", "TEXT"),
612:             ("branding_style", "TEXT DEFAULT 'v3_minimal'"),
613:             ("owner_id", "TEXT"),
614:             ("firm_id", "TEXT"),
615:             ("firm_trust_number", "INTEGER"),
616:             ("firm_trust_code", "TEXT"),
617:         ]:
618:             if col_name not in cols:
619:                 cur.execute(f"ALTER TABLE trusts ADD COLUMN {col_name} {col_type}")
620:                 cols.append(col_name)
621: 
622:         trust_id = "TR-001"
623: 
624:         cur.execute("SELECT trust_id FROM trusts WHERE trust_id = ?", (trust_id,))
625:         existing = cur.fetchone()
626: 
627:         values = {
628:             "trust_id": trust_id,
629:             "trust_name": "Redirect Test Trust 2",
630:             "short_name": "Hosted Test",
631:             "jurisdiction": "NEW JERSEY",
632:             "effective_date": "2026-05-14",
633:             "trust_type": "revocable",
634:             "trust_purpose": "property_holding",
635:             "accounting_method": "accrual",
636:             "workflow_mode": "private_office",
637:             "settlor_name": "",
638:             "trustee_name": "QA TRUSTEE",
```

### `app.py:650`

- Scope markers: `firm_id`

```python
635:             "accounting_method": "accrual",
636:             "workflow_mode": "private_office",
637:             "settlor_name": "",
638:             "trustee_name": "QA TRUSTEE",
639:             "successor_trustee_name": "QA SUCCESOR",
640:             "beneficiary_name": "QA BENE",
641:             "record_visibility": "private",
642:             "workflow_mode_confirmed": "yes",
643:             "ai_explanations": "enabled",
644:             "recommended_guidance": "enabled",
645:             "initial_corpus_description": "",
646:             "property_mapping_timing": "post_creation",
647:             "asset_categories": "property",
648:             "generate_schedule_recommendations": "yes",
649:             "status": "Finalized",
650:             "owner_id": username,
651:             "firm_id": firm_id,
652:             "firm_trust_number": 1,
653:             "firm_trust_code": "TR-001",
654:         }
655: 
656:         if existing:
657:             cur.execute("""
658:                 UPDATE trusts
659:                 SET trust_name = ?,
660:                     short_name = ?,
661:                     jurisdiction = ?,
662:                     effective_date = ?,
663:                     trust_type = ?,
664:                     trust_purpose = ?,
665:                     accounting_method = ?,
666:                     workflow_mode = ?,
667:                     settlor_name = ?,
668:                     trustee_name = ?,
669:                     successor_trustee_name = ?,
670:                     beneficiary_name = ?,
671:                     record_visibility = ?,
672:                     workflow_mode_confirmed = ?,
673:                     ai_explanations = ?,
674:                     recommended_guidance = ?,
675:                     initial_corpus_description = ?,
```

### `app.py:680`

- Scope markers: `firm_id`

```python
665:                     accounting_method = ?,
666:                     workflow_mode = ?,
667:                     settlor_name = ?,
668:                     trustee_name = ?,
669:                     successor_trustee_name = ?,
670:                     beneficiary_name = ?,
671:                     record_visibility = ?,
672:                     workflow_mode_confirmed = ?,
673:                     ai_explanations = ?,
674:                     recommended_guidance = ?,
675:                     initial_corpus_description = ?,
676:                     property_mapping_timing = ?,
677:                     asset_categories = ?,
678:                     generate_schedule_recommendations = ?,
679:                     status = ?,
680:                     owner_id = ?,
681:                     firm_id = ?,
682:                     firm_trust_number = ?,
683:                     firm_trust_code = ?
684:                 WHERE trust_id = ?
685:             """, (
686:                 values["trust_name"], values["short_name"], values["jurisdiction"],
687:                 values["effective_date"], values["trust_type"], values["trust_purpose"],
688:                 values["accounting_method"], values["workflow_mode"], values["settlor_name"],
689:                 values["trustee_name"], values["successor_trustee_name"], values["beneficiary_name"],
690:                 values["record_visibility"], values["workflow_mode_confirmed"],
691:                 values["ai_explanations"], values["recommended_guidance"],
692:                 values["initial_corpus_description"], values["property_mapping_timing"],
693:                 values["asset_categories"], values["generate_schedule_recommendations"],
694:                 values["status"], values["owner_id"], values["firm_id"],
695:                 values["firm_trust_number"], values["firm_trust_code"], values["trust_id"]
696:             ))
697:             action = "updated"
698:         else:
699:             cur.execute("""
700:                 INSERT INTO trusts (
701:                     trust_id, trust_name, short_name, jurisdiction, effective_date,
702:                     trust_type, trust_purpose, accounting_method, workflow_mode,
703:                     settlor_name, trustee_name, successor_trustee_name, beneficiary_name,
704:                     record_visibility, workflow_mode_confirmed, ai_explanations,
705:                     recommended_guidance, initial_corpus_description, property_mapping_timing,
```

### `app.py:694`

- Scope markers: `firm_id`

```python
679:                     status = ?,
680:                     owner_id = ?,
681:                     firm_id = ?,
682:                     firm_trust_number = ?,
683:                     firm_trust_code = ?
684:                 WHERE trust_id = ?
685:             """, (
686:                 values["trust_name"], values["short_name"], values["jurisdiction"],
687:                 values["effective_date"], values["trust_type"], values["trust_purpose"],
688:                 values["accounting_method"], values["workflow_mode"], values["settlor_name"],
689:                 values["trustee_name"], values["successor_trustee_name"], values["beneficiary_name"],
690:                 values["record_visibility"], values["workflow_mode_confirmed"],
691:                 values["ai_explanations"], values["recommended_guidance"],
692:                 values["initial_corpus_description"], values["property_mapping_timing"],
693:                 values["asset_categories"], values["generate_schedule_recommendations"],
694:                 values["status"], values["owner_id"], values["firm_id"],
695:                 values["firm_trust_number"], values["firm_trust_code"], values["trust_id"]
696:             ))
697:             action = "updated"
698:         else:
699:             cur.execute("""
700:                 INSERT INTO trusts (
701:                     trust_id, trust_name, short_name, jurisdiction, effective_date,
702:                     trust_type, trust_purpose, accounting_method, workflow_mode,
703:                     settlor_name, trustee_name, successor_trustee_name, beneficiary_name,
704:                     record_visibility, workflow_mode_confirmed, ai_explanations,
705:                     recommended_guidance, initial_corpus_description, property_mapping_timing,
706:                     asset_categories, generate_schedule_recommendations, status,
707:                     owner_id, firm_id, firm_trust_number, firm_trust_code
708:                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
709:             """, (
710:                 values["trust_id"], values["trust_name"], values["short_name"], values["jurisdiction"],
711:                 values["effective_date"], values["trust_type"], values["trust_purpose"],
712:                 values["accounting_method"], values["workflow_mode"], values["settlor_name"],
713:                 values["trustee_name"], values["successor_trustee_name"], values["beneficiary_name"],
714:                 values["record_visibility"], values["workflow_mode_confirmed"],
715:                 values["ai_explanations"], values["recommended_guidance"],
716:                 values["initial_corpus_description"], values["property_mapping_timing"],
717:                 values["asset_categories"], values["generate_schedule_recommendations"],
718:                 values["status"], values["owner_id"], values["firm_id"],
719:                 values["firm_trust_number"], values["firm_trust_code"]
```

### `app.py:707`

- Scope markers: `firm_id`

```python
692:                 values["initial_corpus_description"], values["property_mapping_timing"],
693:                 values["asset_categories"], values["generate_schedule_recommendations"],
694:                 values["status"], values["owner_id"], values["firm_id"],
695:                 values["firm_trust_number"], values["firm_trust_code"], values["trust_id"]
696:             ))
697:             action = "updated"
698:         else:
699:             cur.execute("""
700:                 INSERT INTO trusts (
701:                     trust_id, trust_name, short_name, jurisdiction, effective_date,
702:                     trust_type, trust_purpose, accounting_method, workflow_mode,
703:                     settlor_name, trustee_name, successor_trustee_name, beneficiary_name,
704:                     record_visibility, workflow_mode_confirmed, ai_explanations,
705:                     recommended_guidance, initial_corpus_description, property_mapping_timing,
706:                     asset_categories, generate_schedule_recommendations, status,
707:                     owner_id, firm_id, firm_trust_number, firm_trust_code
708:                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
709:             """, (
710:                 values["trust_id"], values["trust_name"], values["short_name"], values["jurisdiction"],
711:                 values["effective_date"], values["trust_type"], values["trust_purpose"],
712:                 values["accounting_method"], values["workflow_mode"], values["settlor_name"],
713:                 values["trustee_name"], values["successor_trustee_name"], values["beneficiary_name"],
714:                 values["record_visibility"], values["workflow_mode_confirmed"],
715:                 values["ai_explanations"], values["recommended_guidance"],
716:                 values["initial_corpus_description"], values["property_mapping_timing"],
717:                 values["asset_categories"], values["generate_schedule_recommendations"],
718:                 values["status"], values["owner_id"], values["firm_id"],
719:                 values["firm_trust_number"], values["firm_trust_code"]
720:             ))
721:             action = "created"
722: 
723:         conn.commit()
724:         conn.close()
725: 
726:         print(f"✅ Hosted test trust seed complete: trust={trust_id}; action={action}; firm={firm_id}")
727: 
728:     except Exception as exc:
729:         print("⚠️ Hosted test trust seed failed:", exc)
730: 
731: 
732: 
```

### `app.py:718`

- Scope markers: `firm_id`

```python
703:                     settlor_name, trustee_name, successor_trustee_name, beneficiary_name,
704:                     record_visibility, workflow_mode_confirmed, ai_explanations,
705:                     recommended_guidance, initial_corpus_description, property_mapping_timing,
706:                     asset_categories, generate_schedule_recommendations, status,
707:                     owner_id, firm_id, firm_trust_number, firm_trust_code
708:                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
709:             """, (
710:                 values["trust_id"], values["trust_name"], values["short_name"], values["jurisdiction"],
711:                 values["effective_date"], values["trust_type"], values["trust_purpose"],
712:                 values["accounting_method"], values["workflow_mode"], values["settlor_name"],
713:                 values["trustee_name"], values["successor_trustee_name"], values["beneficiary_name"],
714:                 values["record_visibility"], values["workflow_mode_confirmed"],
715:                 values["ai_explanations"], values["recommended_guidance"],
716:                 values["initial_corpus_description"], values["property_mapping_timing"],
717:                 values["asset_categories"], values["generate_schedule_recommendations"],
718:                 values["status"], values["owner_id"], values["firm_id"],
719:                 values["firm_trust_number"], values["firm_trust_code"]
720:             ))
721:             action = "created"
722: 
723:         conn.commit()
724:         conn.close()
725: 
726:         print(f"✅ Hosted test trust seed complete: trust={trust_id}; action={action}; firm={firm_id}")
727: 
728:     except Exception as exc:
729:         print("⚠️ Hosted test trust seed failed:", exc)
730: 
731: 
732: 
733: 
734: # Permanent hosted test trust seed.
735: try:
736:     run_hosted_test_trust_seed()
737: except Exception as e:
738:     print("⚠️ Hosted test trust seed wrapper failed:", e)
739: 
740: 
741: 
742: def run_hosted_portfolio_seed():
743:     """
```

### `app.py:757`

- Scope markers: `firm_id`

```python
742: def run_hosted_portfolio_seed():
743:     """
744:     Permanent hosted FIRM-002 portfolio seed.
745: 
746:     Seeds one property, account, document, and ledger entry
747:     for TR-001 under FIRM-002.
748:     """
749:     if os.getenv("ENSURE_HOSTED_PORTFOLIO_SEED") != "1":
750:         return
751: 
752:     import sqlite3
753:     from datetime import datetime
754: 
755:     trust_id = "TR-001"
756:     firm_id = "FIRM-002"
757:     owner_id = "admin123"
758: 
759:     try:
760:         DB_PATH.parent.mkdir(parents=True, exist_ok=True)
761: 
762:         conn = sqlite3.connect(DB_PATH)
763:         conn.row_factory = sqlite3.Row
764:         cur = conn.cursor()
765: 
766:         # =========================
767:         # PROPERTIES
768:         # =========================
769:         cur.execute("""
770:             CREATE TABLE IF NOT EXISTS properties (
771:                 id INTEGER PRIMARY KEY AUTOINCREMENT,
772:                 property_id TEXT,
773:                 trust_id TEXT,
774:                 property_name TEXT,
775:                 property_type TEXT,
776:                 estimated_value TEXT
777:             )
778:         """)
779: 
780:         cur.execute("PRAGMA table_info(properties)")
781:         cols = [r["name"] for r in cur.fetchall()]
782: 
```

### `app.py:785`

- Scope markers: `firm_id`

```python
770:             CREATE TABLE IF NOT EXISTS properties (
771:                 id INTEGER PRIMARY KEY AUTOINCREMENT,
772:                 property_id TEXT,
773:                 trust_id TEXT,
774:                 property_name TEXT,
775:                 property_type TEXT,
776:                 estimated_value TEXT
777:             )
778:         """)
779: 
780:         cur.execute("PRAGMA table_info(properties)")
781:         cols = [r["name"] for r in cur.fetchall()]
782: 
783:         for col_name, col_type in [
784:             ("firm_id", "TEXT"),
785:             ("owner_id", "TEXT")
786:         ]:
787:             if col_name not in cols:
788:                 cur.execute(f"ALTER TABLE properties ADD COLUMN {col_name} {col_type}")
789: 
790:         cur.execute("""
791:             SELECT property_id FROM properties
792:             WHERE property_id = 'PROP-001' AND firm_id = ?
793:         """, (firm_id,))
794:         if not cur.fetchone():
795:             cur.execute("""
796:                 INSERT INTO properties (
797:                     property_id,
798:                     trust_id,
799:                     property_name,
800:                     property_type,
801:                     estimated_value,
802:                     firm_id,
803:                     owner_id
804:                 ) VALUES (?, ?, ?, ?, ?, ?, ?)
805:             """, (
806:                 "PROP-001",
807:                 trust_id,
808:                 "Hosted Test Property",
809:                 "Real Estate",
810:                 "$250,000",
```

### `app.py:803`

- Scope markers: `firm_id`

```python
788:                 cur.execute(f"ALTER TABLE properties ADD COLUMN {col_name} {col_type}")
789: 
790:         cur.execute("""
791:             SELECT property_id FROM properties
792:             WHERE property_id = 'PROP-001' AND firm_id = ?
793:         """, (firm_id,))
794:         if not cur.fetchone():
795:             cur.execute("""
796:                 INSERT INTO properties (
797:                     property_id,
798:                     trust_id,
799:                     property_name,
800:                     property_type,
801:                     estimated_value,
802:                     firm_id,
803:                     owner_id
804:                 ) VALUES (?, ?, ?, ?, ?, ?, ?)
805:             """, (
806:                 "PROP-001",
807:                 trust_id,
808:                 "Hosted Test Property",
809:                 "Real Estate",
810:                 "$250,000",
811:                 firm_id,
812:                 owner_id
813:             ))
814: 
815:         # =========================
816:         # ACCOUNTS
817:         # =========================
818:         cur.execute("""
819:             CREATE TABLE IF NOT EXISTS accounts (
820:                 id INTEGER PRIMARY KEY AUTOINCREMENT,
821:                 account_id TEXT,
822:                 trust_id TEXT,
823:                 institution_name TEXT,
824:                 account_type TEXT,
825:                 balance TEXT
826:             )
827:         """)
828: 
```

### `app.py:812`

- Scope markers: `firm_id`

```python
797:                     property_id,
798:                     trust_id,
799:                     property_name,
800:                     property_type,
801:                     estimated_value,
802:                     firm_id,
803:                     owner_id
804:                 ) VALUES (?, ?, ?, ?, ?, ?, ?)
805:             """, (
806:                 "PROP-001",
807:                 trust_id,
808:                 "Hosted Test Property",
809:                 "Real Estate",
810:                 "$250,000",
811:                 firm_id,
812:                 owner_id
813:             ))
814: 
815:         # =========================
816:         # ACCOUNTS
817:         # =========================
818:         cur.execute("""
819:             CREATE TABLE IF NOT EXISTS accounts (
820:                 id INTEGER PRIMARY KEY AUTOINCREMENT,
821:                 account_id TEXT,
822:                 trust_id TEXT,
823:                 institution_name TEXT,
824:                 account_type TEXT,
825:                 balance TEXT
826:             )
827:         """)
828: 
829:         cur.execute("PRAGMA table_info(accounts)")
830:         cols = [r["name"] for r in cur.fetchall()]
831: 
832:         for col_name, col_type in [
833:             ("firm_id", "TEXT"),
834:             ("owner_id", "TEXT")
835:         ]:
836:             if col_name not in cols:
837:                 cur.execute(f"ALTER TABLE accounts ADD COLUMN {col_name} {col_type}")
```

### `app.py:834`

- Scope markers: `firm_id`

```python
819:             CREATE TABLE IF NOT EXISTS accounts (
820:                 id INTEGER PRIMARY KEY AUTOINCREMENT,
821:                 account_id TEXT,
822:                 trust_id TEXT,
823:                 institution_name TEXT,
824:                 account_type TEXT,
825:                 balance TEXT
826:             )
827:         """)
828: 
829:         cur.execute("PRAGMA table_info(accounts)")
830:         cols = [r["name"] for r in cur.fetchall()]
831: 
832:         for col_name, col_type in [
833:             ("firm_id", "TEXT"),
834:             ("owner_id", "TEXT")
835:         ]:
836:             if col_name not in cols:
837:                 cur.execute(f"ALTER TABLE accounts ADD COLUMN {col_name} {col_type}")
838: 
839:         cur.execute("""
840:             SELECT account_id FROM accounts
841:             WHERE account_id = 'ACCT-001' AND firm_id = ?
842:         """, (firm_id,))
843:         if not cur.fetchone():
844:             cur.execute("""
845:                 INSERT INTO accounts (
846:                     account_id,
847:                     trust_id,
848:                     institution_name,
849:                     account_type,
850:                     balance,
851:                     firm_id,
852:                     owner_id
853:                 ) VALUES (?, ?, ?, ?, ?, ?, ?)
854:             """, (
855:                 "ACCT-001",
856:                 trust_id,
857:                 "Hosted Trust Bank",
858:                 "Checking",
859:                 "$15,000",
```

### `app.py:852`

- Scope markers: `firm_id`

```python
837:                 cur.execute(f"ALTER TABLE accounts ADD COLUMN {col_name} {col_type}")
838: 
839:         cur.execute("""
840:             SELECT account_id FROM accounts
841:             WHERE account_id = 'ACCT-001' AND firm_id = ?
842:         """, (firm_id,))
843:         if not cur.fetchone():
844:             cur.execute("""
845:                 INSERT INTO accounts (
846:                     account_id,
847:                     trust_id,
848:                     institution_name,
849:                     account_type,
850:                     balance,
851:                     firm_id,
852:                     owner_id
853:                 ) VALUES (?, ?, ?, ?, ?, ?, ?)
854:             """, (
855:                 "ACCT-001",
856:                 trust_id,
857:                 "Hosted Trust Bank",
858:                 "Checking",
859:                 "$15,000",
860:                 firm_id,
861:                 owner_id
862:             ))
863: 
864:         # =========================
865:         # DOCUMENTS
866:         # =========================
867:         cur.execute("""
868:             CREATE TABLE IF NOT EXISTS documents (
869:                 id INTEGER PRIMARY KEY AUTOINCREMENT,
870:                 document_id TEXT,
871:                 trust_id TEXT,
872:                 document_name TEXT,
873:                 document_type TEXT
874:             )
875:         """)
876: 
877:         cur.execute("PRAGMA table_info(documents)")
```

### `app.py:861`

- Scope markers: `firm_id`

```python
846:                     account_id,
847:                     trust_id,
848:                     institution_name,
849:                     account_type,
850:                     balance,
851:                     firm_id,
852:                     owner_id
853:                 ) VALUES (?, ?, ?, ?, ?, ?, ?)
854:             """, (
855:                 "ACCT-001",
856:                 trust_id,
857:                 "Hosted Trust Bank",
858:                 "Checking",
859:                 "$15,000",
860:                 firm_id,
861:                 owner_id
862:             ))
863: 
864:         # =========================
865:         # DOCUMENTS
866:         # =========================
867:         cur.execute("""
868:             CREATE TABLE IF NOT EXISTS documents (
869:                 id INTEGER PRIMARY KEY AUTOINCREMENT,
870:                 document_id TEXT,
871:                 trust_id TEXT,
872:                 document_name TEXT,
873:                 document_type TEXT
874:             )
875:         """)
876: 
877:         cur.execute("PRAGMA table_info(documents)")
878:         cols = [r["name"] for r in cur.fetchall()]
879: 
880:         for col_name, col_type in [
881:             ("firm_id", "TEXT"),
882:             ("owner_id", "TEXT")
883:         ]:
884:             if col_name not in cols:
885:                 cur.execute(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type}")
886: 
```

### `app.py:882`

- Scope markers: `firm_id`

```python
867:         cur.execute("""
868:             CREATE TABLE IF NOT EXISTS documents (
869:                 id INTEGER PRIMARY KEY AUTOINCREMENT,
870:                 document_id TEXT,
871:                 trust_id TEXT,
872:                 document_name TEXT,
873:                 document_type TEXT
874:             )
875:         """)
876: 
877:         cur.execute("PRAGMA table_info(documents)")
878:         cols = [r["name"] for r in cur.fetchall()]
879: 
880:         for col_name, col_type in [
881:             ("firm_id", "TEXT"),
882:             ("owner_id", "TEXT")
883:         ]:
884:             if col_name not in cols:
885:                 cur.execute(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type}")
886: 
887:         cur.execute("""
888:             SELECT document_id FROM documents
889:             WHERE document_id = 'DOC-001' AND firm_id = ?
890:         """, (firm_id,))
891:         if not cur.fetchone():
892:             cur.execute("""
893:                 INSERT INTO documents (
894:                     document_id,
895:                     trust_id,
896:                     document_name,
897:                     document_type,
898:                     firm_id,
899:                     owner_id
900:                 ) VALUES (?, ?, ?, ?, ?, ?)
901:             """, (
902:                 "DOC-001",
903:                 trust_id,
904:                 "Hosted Portfolio Seed Document",
905:                 "Trust Record",
906:                 firm_id,
907:                 owner_id
```

### `app.py:899`

- Scope markers: `firm_id`

```python
884:             if col_name not in cols:
885:                 cur.execute(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type}")
886: 
887:         cur.execute("""
888:             SELECT document_id FROM documents
889:             WHERE document_id = 'DOC-001' AND firm_id = ?
890:         """, (firm_id,))
891:         if not cur.fetchone():
892:             cur.execute("""
893:                 INSERT INTO documents (
894:                     document_id,
895:                     trust_id,
896:                     document_name,
897:                     document_type,
898:                     firm_id,
899:                     owner_id
900:                 ) VALUES (?, ?, ?, ?, ?, ?)
901:             """, (
902:                 "DOC-001",
903:                 trust_id,
904:                 "Hosted Portfolio Seed Document",
905:                 "Trust Record",
906:                 firm_id,
907:                 owner_id
908:             ))
909: 
910:         # =========================
911:         # LEDGER ENTRIES
912:         # =========================
913:         cur.execute("""
914:             CREATE TABLE IF NOT EXISTS ledger_entries (
915:                 id INTEGER PRIMARY KEY AUTOINCREMENT,
916:                 entry_id TEXT,
917:                 trust_id TEXT,
918:                 entry_type TEXT,
919:                 amount TEXT,
920:                 description TEXT,
921:                 entry_date TEXT
922:             )
923:         """)
924: 
```

### `app.py:907`

- Scope markers: `firm_id`

```python
892:             cur.execute("""
893:                 INSERT INTO documents (
894:                     document_id,
895:                     trust_id,
896:                     document_name,
897:                     document_type,
898:                     firm_id,
899:                     owner_id
900:                 ) VALUES (?, ?, ?, ?, ?, ?)
901:             """, (
902:                 "DOC-001",
903:                 trust_id,
904:                 "Hosted Portfolio Seed Document",
905:                 "Trust Record",
906:                 firm_id,
907:                 owner_id
908:             ))
909: 
910:         # =========================
911:         # LEDGER ENTRIES
912:         # =========================
913:         cur.execute("""
914:             CREATE TABLE IF NOT EXISTS ledger_entries (
915:                 id INTEGER PRIMARY KEY AUTOINCREMENT,
916:                 entry_id TEXT,
917:                 trust_id TEXT,
918:                 entry_type TEXT,
919:                 amount TEXT,
920:                 description TEXT,
921:                 entry_date TEXT
922:             )
923:         """)
924: 
925:         cur.execute("PRAGMA table_info(ledger_entries)")
926:         cols = [r["name"] for r in cur.fetchall()]
927: 
928:         for col_name, col_type in [
929:             ("firm_id", "TEXT"),
930:             ("owner_id", "TEXT")
931:         ]:
932:             if col_name not in cols:
```

### `app.py:930`

- Scope markers: `firm_id`

```python
915:                 id INTEGER PRIMARY KEY AUTOINCREMENT,
916:                 entry_id TEXT,
917:                 trust_id TEXT,
918:                 entry_type TEXT,
919:                 amount TEXT,
920:                 description TEXT,
921:                 entry_date TEXT
922:             )
923:         """)
924: 
925:         cur.execute("PRAGMA table_info(ledger_entries)")
926:         cols = [r["name"] for r in cur.fetchall()]
927: 
928:         for col_name, col_type in [
929:             ("firm_id", "TEXT"),
930:             ("owner_id", "TEXT")
931:         ]:
932:             if col_name not in cols:
933:                 cur.execute(f"ALTER TABLE ledger_entries ADD COLUMN {col_name} {col_type}")
934: 
935:         cur.execute("""
936:             SELECT entry_id FROM ledger_entries
937:             WHERE entry_id = 'LEDGER-001' AND firm_id = ?
938:         """, (firm_id,))
939:         if not cur.fetchone():
940:             cur.execute("""
941:                 INSERT INTO ledger_entries (
942:                     entry_id,
943:                     trust_id,
944:                     entry_type,
945:                     amount,
946:                     description,
947:                     entry_date,
948:                     firm_id,
949:                     owner_id
950:                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
951:             """, (
952:                 "LEDGER-001",
953:                 trust_id,
954:                 "Asset",
955:                 "$15,000",
```

### `app.py:949`

- Scope markers: `firm_id`

```python
934: 
935:         cur.execute("""
936:             SELECT entry_id FROM ledger_entries
937:             WHERE entry_id = 'LEDGER-001' AND firm_id = ?
938:         """, (firm_id,))
939:         if not cur.fetchone():
940:             cur.execute("""
941:                 INSERT INTO ledger_entries (
942:                     entry_id,
943:                     trust_id,
944:                     entry_type,
945:                     amount,
946:                     description,
947:                     entry_date,
948:                     firm_id,
949:                     owner_id
950:                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
951:             """, (
952:                 "LEDGER-001",
953:                 trust_id,
954:                 "Asset",
955:                 "$15,000",
956:                 "Hosted portfolio seed ledger entry",
957:                 datetime.utcnow().strftime("%Y-%m-%d"),
958:                 firm_id,
959:                 owner_id
960:             ))
961: 
962:         conn.commit()
963:         conn.close()
964: 
965:         print("✅ Hosted portfolio seed complete: property/account/document/ledger created")
966: 
967:     except Exception as exc:
968:         print("⚠️ Hosted portfolio seed failed:", exc)
969: 
970: 
971: 
972: 
973: # Permanent hosted portfolio seed.
974: try:
```

### `app.py:959`

- Scope markers: `firm_id`

```python
944:                     entry_type,
945:                     amount,
946:                     description,
947:                     entry_date,
948:                     firm_id,
949:                     owner_id
950:                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
951:             """, (
952:                 "LEDGER-001",
953:                 trust_id,
954:                 "Asset",
955:                 "$15,000",
956:                 "Hosted portfolio seed ledger entry",
957:                 datetime.utcnow().strftime("%Y-%m-%d"),
958:                 firm_id,
959:                 owner_id
960:             ))
961: 
962:         conn.commit()
963:         conn.close()
964: 
965:         print("✅ Hosted portfolio seed complete: property/account/document/ledger created")
966: 
967:     except Exception as exc:
968:         print("⚠️ Hosted portfolio seed failed:", exc)
969: 
970: 
971: 
972: 
973: # Permanent hosted portfolio seed.
974: try:
975:     run_hosted_portfolio_seed()
976: except Exception as e:
977:     print("⚠️ Hosted portfolio seed wrapper failed:", e)
978: 
979: 
980: def generate_csrf_token():
981:     token = session.get("_csrf_token")
982:     if not token:
983:         token = secrets.token_urlsafe(32)
984:         session["_csrf_token"] = token
```

### `app.py:1273`

- Scope markers: `none detected`

```python
1258: 
1259:     def _first(obj, keys, default=""):
1260:         for key in keys:
1261:             value = _get(obj, key, "")
1262:             if value not in (None, "", []):
1263:                 return value
1264:         return default
1265: 
1266:     trust_id_value = _first(trust, ["trust_id"])
1267:     trust_name_value = _first(trust, ["trust_name", "name", "trust_title"])
1268:     trust_type_value = _first(trust, ["trust_type", "type_of_trust", "trust_category"])
1269:     grantor_value = _first(trust, ["grantor_name", "settlor_name", "grantor", "settlor"])
1270:     trustee_value = _first(trust, ["trustee_name", "initial_trustee_name", "current_trustee_name", "trustee"])
1271:     successor_trustee_value = _first(trust, ["successor_trustee_name", "successor_trustee", "alternate_trustee_name"])
1272:     beneficiary_value = _first(trust, ["primary_beneficiary", "beneficiary_name", "primary_beneficiary_name"])
1273:     owner_id_value = _first(trust, ["owner_id", "owner", "client_id"])
1274:     status_value = _first(trust, ["status"])
1275:     jurisdiction_value = _first(trust, ["jurisdiction", "state_of_jurisdiction", "governing_jurisdiction"])
1276:     governing_law_value = _first(trust, ["governing_law", "governing_law_state", "governing_state"])
1277:     created_at_value = _first(trust, ["created_at", "date_created"])
1278:     effective_date_value = _first(trust, ["effective_date", "trust_date", "date_of_trust", "execution_date", "signed_date", "created_at"])
1279:     trust_purpose_value = _first(trust, ["trust_purpose", "purpose", "purpose_statement", "mission"])
1280:     initial_corpus_value = _first(trust, ["initial_corpus_description", "initial_corpus", "corpus_description", "funding_description"])
1281:     asset_categories_value = _first(trust, ["asset_categories", "asset_category", "asset_classes"])
1282:     property_mapping_timing_value = _first(trust, ["property_mapping_timing", "funding_timing", "transfer_timing"])
1283: 
1284:     created_at_display = created_at_value or ""
1285:     effective_date_display = effective_date_value or ""
1286: 
1287:     return {
1288:         "trust_id": trust_id_value,
1289:         "trust_name": trust_name_value,
1290:         "trust_type": trust_type_value,
1291:         "grantor_name": grantor_value,
1292:         "trustee_name": trustee_value,
1293:         "successor_trustee_name": successor_trustee_value,
1294:         "primary_beneficiary": beneficiary_value,
1295:         "owner_id": owner_id_value,
1296:         "status": status_value,
1297:         "jurisdiction": jurisdiction_value,
1298:         "governing_law": governing_law_value,
```

### `app.py:1295`

- Scope markers: `none detected`

```python
1280:     initial_corpus_value = _first(trust, ["initial_corpus_description", "initial_corpus", "corpus_description", "funding_description"])
1281:     asset_categories_value = _first(trust, ["asset_categories", "asset_category", "asset_classes"])
1282:     property_mapping_timing_value = _first(trust, ["property_mapping_timing", "funding_timing", "transfer_timing"])
1283: 
1284:     created_at_display = created_at_value or ""
1285:     effective_date_display = effective_date_value or ""
1286: 
1287:     return {
1288:         "trust_id": trust_id_value,
1289:         "trust_name": trust_name_value,
1290:         "trust_type": trust_type_value,
1291:         "grantor_name": grantor_value,
1292:         "trustee_name": trustee_value,
1293:         "successor_trustee_name": successor_trustee_value,
1294:         "primary_beneficiary": beneficiary_value,
1295:         "owner_id": owner_id_value,
1296:         "status": status_value,
1297:         "jurisdiction": jurisdiction_value,
1298:         "governing_law": governing_law_value,
1299:         "created_at": created_at_value,
1300:         "created_at_display": created_at_display,
1301:         "effective_date": effective_date_value,
1302:         "effective_date_display": effective_date_display,
1303:         "trust_purpose": trust_purpose_value,
1304:         "initial_corpus_description": initial_corpus_value,
1305:         "asset_categories": asset_categories_value,
1306:         "property_mapping_timing": property_mapping_timing_value,
1307:         "seal_path": _first(trust, ["seal_path", "trust_seal_path", "logo_path"]),
1308:         "caf_number": _first(trust, ["caf_number", "caf"]),
1309:         "crid_number": _first(trust, ["crid_number", "crid"]),
1310:         "trust_motto": _first(trust, ["trust_motto", "motto"]),
1311:         "foundation_scripture": _first(trust, ["foundation_scripture", "scripture"]),
1312:         "prepared_by": _first(trust, ["prepared_by"]),
1313:         "return_to": _first(trust, ["return_to"]),
1314:         "branding_style": _first(trust, ["branding_style"], "v3_minimal"),
1315:     }
1316: 
1317: 
1318: 
1319: def build_trust_document_readiness(preview_context):
1320:     def has_value(key):
```

### `app.py:2972`

- Scope markers: `none detected`

```python
2957:             "accounting_method": "Not Yet Selected",
2958:             "workflow_mode": "Not Yet Selected",
2959:             "settlor_name": "",
2960:             "trustee_name": "",
2961:             "successor_trustee_name": "",
2962:             "beneficiary_name": "",
2963:             "record_visibility": "Not Yet Selected",
2964:             "workflow_mode_confirmed": "Not Yet Selected",
2965:             "ai_explanations": "Not Yet Selected",
2966:             "recommended_guidance": "Not Yet Selected",
2967:             "initial_corpus_description": "",
2968:             "property_mapping_timing": "Not Yet Selected",
2969:             "asset_categories": "Not Yet Selected",
2970:             "generate_schedule_recommendations": "Not Yet Selected",
2971:             "status": "Draft",
2972:         "owner_id": get_current_owner()
2973:         }
2974:         create_trust_record(trust)
2975:         return redirect(url_for("create_trust_step2_grantor", trust_id=trust_id))
2976:     return render_template("create_trust_step1.html")
2977: 
2978: 
2979: @app.route("/create_trust_step2_grantor/<trust_id>", methods=["GET", "POST"])
2980: @csrf.exempt
2981: def create_trust_step2_grantor(trust_id):
2982:     trust = get_trust_by_id(trust_id)
2983:     if not trust:
2984:         return f"Trust {trust_id} not found"
2985: 
2986:     if request.method == "POST":
2987:         if not validate_csrf_token():
2988:             return render_template("create_trust_step2_grantor.html", trust=trust, error_message="Invalid or missing CSRF token.")
2989: 
2990:         update_trust_fields(trust_id, {
2991:             "grantor_name": request.form.get("grantor_name"),
2992:             "grantor_type": request.form.get("grantor_type"),
2993:             "grantor_contact": request.form.get("grantor_contact"),
2994:         })
2995: 
2996:         return redirect(url_for("create_trust_step2", trust_id=trust_id))
2997: 
```

### `app.py:3190`

- Scope markers: `none detected`

```python
3175:         stored_filename = f"{document_id}_{safe_name}"
3176:         file_path = UPLOAD_FOLDER / stored_filename
3177:         uploaded_file.save(file_path)
3178: 
3179:         document = {
3180:             "document_id": document_id,
3181:             "trust_id": request.form.get("trust_id"),
3182:             "property_id": request.form.get("property_id"),
3183:             "account_id": request.form.get("account_id"),
3184:             "document_category": request.form.get("document_category"),
3185:             "document_title": request.form.get("document_title"),
3186:             "notes": request.form.get("notes"),
3187:             "original_filename": original_filename,
3188:             "stored_filename": stored_filename,
3189:             "file_path": str(file_path),
3190:             "owner_id": get_current_owner(),
3191:         }
3192:         create_document_record(document)
3193: 
3194:         if document["property_id"]:
3195:             return redirect(url_for("property_detail", property_id=document["property_id"]))
3196:         return redirect(url_for("trust_detail", trust_id=document["trust_id"]))
3197:     return render_template(
3198:         "upload_document.html",
3199:         trusts=trusts,
3200:         prefill_property_id=prefill_property_id,
3201:         prefill_trust_id=prefill_trust_id,
3202:         evidence_mode=evidence_mode
3203:     )
3204: 
3205: @app.route("/ledger_entry", methods=["GET", "POST"])
3206: def ledger_entry():
3207:     trusts = get_all_trusts()
3208:     if request.method == "POST":
3209:         if not validate_csrf_token():
3210:             return render_template("ledger_entry.html", trusts=trusts, properties=[], accounts=[], error_message="Invalid or missing CSRF token.")
3211: 
3212:         entry_id = get_next_entry_id()
3213:         entry = {
3214:             "entry_id": entry_id,
3215:             "trust_id": request.form.get("trust_id"),
```

### `app.py:3375`

- Scope markers: `none detected`

```python
3360:         trust=trust,
3361:         linked_properties=linked_properties,
3362:         linked_accounts=linked_accounts,
3363:         linked_documents=linked_documents,
3364:         linked_ledger=linked_ledger
3365:     )
3366: 
3367: @app.route("/property/<property_id>")
3368: def property_detail(property_id):
3369:     prop = get_property_by_id(property_id)
3370:     if not prop:
3371:         return f"Property {property_id} not found"
3372: 
3373:     prop_data = dict(prop)
3374: 
3375:     prop_owner = prop_data.get("owner_id")
3376:     current_owner = get_current_owner()
3377: 
3378:     if prop_owner and prop_owner != current_owner:
3379:         return render_template(
3380:             "access_denied.html",
3381:             reason="This property record does not belong to the current owner context."
3382:         )
3383: 
3384:     linked_trust = get_trust_by_id(prop_data["trust_id"])
3385:     linked_accounts = get_accounts_by_property_id(property_id)
3386:     linked_documents = get_documents_by_property_id(property_id)
3387:     linked_ledger = get_ledger_by_property(property_id)
3388:     evidence_profile = build_property_evidence_profile(property_id)
3389: 
3390:     return render_template(
3391:         "property_detail.html",
3392:         prop=prop_data,
3393:         linked_trust=linked_trust,
3394:         linked_accounts=linked_accounts,
3395:         linked_documents=linked_documents,
3396:         linked_ledger=linked_ledger,
3397:         evidence_profile=evidence_profile
3398:     )
3399: 
3400: 
```

### `app.py:6647`

- Scope markers: `firm_id`

```python
6632:     log_change(
6633:         "export_policy",
6634:         policy_key,
6635:         "toggle",
6636:         f"Admin {session.get('username')} for firm {session.get('firm_id', 'FIRM-001')} set {policy_key} to {policy[policy_key]}"
6637:     )
6638:     flash(f"System policy updated: {policy_key} = {policy[policy_key]}")
6639:     return redirect(url_for("admin_index"))
6640: 
6641: @app.route("/admin/seed-hosted-baseline", methods=["POST"])
6642: def seed_hosted_baseline_route():
6643:     gate = require_master_admin()
6644:     if gate:
6645:         return gate
6646: 
6647:     owner_id = get_current_owner() or "admin"
6648:     results = seed_hosted_baseline_data(owner_id)
6649: 
6650:     summary = (
6651:         f"Hosted baseline seed run by {owner_id} | "
6652:         f"Trusts created={len(results.get('trusts_created', []))}, "
6653:         f"Trusts skipped={len(results.get('trusts_skipped', []))}, "
6654:         f"Articles created={len(results.get('learning_articles_created', []))}, "
6655:         f"Articles skipped={len(results.get('learning_articles_skipped', []))}, "
6656:         f"Guides created={len(results.get('form_guides_created', []))}, "
6657:         f"Guides skipped={len(results.get('form_guides_skipped', []))}"
6658:     )
6659: 
6660:     log_change(
6661:         "system",
6662:         "hosted_baseline_seed",
6663:         "hosted_baseline_seed_run",
6664:         summary
6665:     )
6666: 
6667:     flash(summary)
6668:     return redirect(url_for("admin_index"))
6669: 
6670: 
6671: @app.route("/admin")
6672: def admin_index():
```

### `app.py:6648`

- Scope markers: `firm_id`

```python
6633:         "export_policy",
6634:         policy_key,
6635:         "toggle",
6636:         f"Admin {session.get('username')} for firm {session.get('firm_id', 'FIRM-001')} set {policy_key} to {policy[policy_key]}"
6637:     )
6638:     flash(f"System policy updated: {policy_key} = {policy[policy_key]}")
6639:     return redirect(url_for("admin_index"))
6640: 
6641: @app.route("/admin/seed-hosted-baseline", methods=["POST"])
6642: def seed_hosted_baseline_route():
6643:     gate = require_master_admin()
6644:     if gate:
6645:         return gate
6646: 
6647:     owner_id = get_current_owner() or "admin"
6648:     results = seed_hosted_baseline_data(owner_id)
6649: 
6650:     summary = (
6651:         f"Hosted baseline seed run by {owner_id} | "
6652:         f"Trusts created={len(results.get('trusts_created', []))}, "
6653:         f"Trusts skipped={len(results.get('trusts_skipped', []))}, "
6654:         f"Articles created={len(results.get('learning_articles_created', []))}, "
6655:         f"Articles skipped={len(results.get('learning_articles_skipped', []))}, "
6656:         f"Guides created={len(results.get('form_guides_created', []))}, "
6657:         f"Guides skipped={len(results.get('form_guides_skipped', []))}"
6658:     )
6659: 
6660:     log_change(
6661:         "system",
6662:         "hosted_baseline_seed",
6663:         "hosted_baseline_seed_run",
6664:         summary
6665:     )
6666: 
6667:     flash(summary)
6668:     return redirect(url_for("admin_index"))
6669: 
6670: 
6671: @app.route("/admin")
6672: def admin_index():
6673:     trusts = get_visible_trusts_for_current_operator()
```

### `app.py:6651`

- Scope markers: `firm_id`

```python
6636:         f"Admin {session.get('username')} for firm {session.get('firm_id', 'FIRM-001')} set {policy_key} to {policy[policy_key]}"
6637:     )
6638:     flash(f"System policy updated: {policy_key} = {policy[policy_key]}")
6639:     return redirect(url_for("admin_index"))
6640: 
6641: @app.route("/admin/seed-hosted-baseline", methods=["POST"])
6642: def seed_hosted_baseline_route():
6643:     gate = require_master_admin()
6644:     if gate:
6645:         return gate
6646: 
6647:     owner_id = get_current_owner() or "admin"
6648:     results = seed_hosted_baseline_data(owner_id)
6649: 
6650:     summary = (
6651:         f"Hosted baseline seed run by {owner_id} | "
6652:         f"Trusts created={len(results.get('trusts_created', []))}, "
6653:         f"Trusts skipped={len(results.get('trusts_skipped', []))}, "
6654:         f"Articles created={len(results.get('learning_articles_created', []))}, "
6655:         f"Articles skipped={len(results.get('learning_articles_skipped', []))}, "
6656:         f"Guides created={len(results.get('form_guides_created', []))}, "
6657:         f"Guides skipped={len(results.get('form_guides_skipped', []))}"
6658:     )
6659: 
6660:     log_change(
6661:         "system",
6662:         "hosted_baseline_seed",
6663:         "hosted_baseline_seed_run",
6664:         summary
6665:     )
6666: 
6667:     flash(summary)
6668:     return redirect(url_for("admin_index"))
6669: 
6670: 
6671: @app.route("/admin")
6672: def admin_index():
6673:     trusts = get_visible_trusts_for_current_operator()
6674: 
6675:     # BUILD TRUST SUMMARIES
6676:     trust_summaries = [build_admin_trust_summary(t) for t in trusts]
```

### `app.py:8468`

- Scope markers: `none detected`

```python
8453:         payload.get("related_forms"),
8454:         payload.get("related_reports"),
8455:         payload.get("status"),
8456:         article_id,
8457:     ))
8458:     conn.commit()
8459:     conn.close()
8460: 
8461: def get_visualization_metrics():
8462:     conn = _learning_conn()
8463:     metrics = {}
8464:     table_map = {
8465:         "learning_articles": "learning_articles",
8466:         "form_guides": "tax_form_guides",
8467:         "tutorial_videos": "tutorial_videos",
8468:         "workspaces": "workspaces",
8469:         "workspace_notes": "workspace_notes",
8470:         "discussion_threads": "discussion_threads",
8471:         "discussion_messages": "discussion_messages",
8472:         "execution_tasks": "execution_tasks",
8473:         "document_templates": "document_templates",
8474:         "generated_documents": "generated_documents",
8475:     }
8476: 
8477:     for key, table_name in table_map.items():
8478:         try:
8479:             metrics[key] = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
8480:         except Exception:
8481:             metrics[key] = 0
8482: 
8483:     conn.close()
8484: 
8485:     # pull from main app helpers where available
8486:     try:
8487:         metrics["trusts"] = len(get_all_trusts())
8488:     except Exception:
8489:         metrics["trusts"] = 0
8490: 
8491:     try:
8492:         metrics["fiduciaries"] = len(get_all_fiduciaries())
8493:     except Exception:
```

### `app.py:8513`

- Scope markers: `none detected`

```python
8498:     except Exception:
8499:         metrics["instruments"] = 0
8500: 
8501:     try:
8502:         metrics["media"] = len(get_all_media())
8503:     except Exception:
8504:         metrics["media"] = 0
8505: 
8506:     return metrics
8507: 
8508: def get_visualization_timeline():
8509:     conn = _learning_conn()
8510:     timeline = []
8511: 
8512:     sources = [
8513:         ("Workspace", "workspaces", "workspace_id", "title"),
8514:         ("Discussion Thread", "discussion_threads", "thread_id", "title"),
8515:         ("Execution Task", "execution_tasks", "task_id", "title"),
8516:         ("Generated Document", "generated_documents", "document_id", "title"),
8517:         ("Tutorial Video", "tutorial_videos", "video_id", "title"),
8518:     ]
8519: 
8520:     for label, table_name, id_col, title_col in sources:
8521:         try:
8522:             rows = conn.execute(
8523:                 f"SELECT {id_col} as item_id, {title_col} as item_title, created_at FROM {table_name} ORDER BY created_at DESC LIMIT 10"
8524:             ).fetchall()
8525:             for row in rows:
8526:                 timeline.append({
8527:                     "kind": label,
8528:                     "item_id": row["item_id"],
8529:                     "item_title": row["item_title"],
8530:                     "created_at": row["created_at"],
8531:                 })
8532:         except Exception:
8533:             continue
8534: 
8535:     conn.close()
8536:     timeline.sort(key=lambda x: x.get("created_at") or "", reverse=True)
8537:     return timeline[:30]
8538: 
```

### `app.py:8579`

- Scope markers: `none detected`

```python
8564:             row["instruments"] = len([i for i in get_all_instruments() if i.get("trust_id") == trust_id])
8565:         except Exception:
8566:             pass
8567: 
8568:         try:
8569:             row["documents"] = len([d for d in get_generated_documents() if d.get("trust_id") == trust_id])
8570:         except Exception:
8571:             pass
8572: 
8573:         try:
8574:             row["tasks"] = len([t for t in get_all_execution_tasks() if t.get("trust_id") == trust_id])
8575:         except Exception:
8576:             pass
8577: 
8578:         try:
8579:             row["workspace_links"] = len([w for w in get_all_workspaces() if (w.get("trust_type_focus") or "").lower() in (trust.get("trust_type") or "").lower()])
8580:         except Exception:
8581:             pass
8582: 
8583:         summary.append(row)
8584: 
8585:     return summary
8586: 
8587: def get_document_templates():
8588:     conn = _learning_conn()
8589:     rows = conn.execute("""
8590:         SELECT * FROM document_templates
8591:         WHERE status = 'active'
8592:         ORDER BY category, name
8593:     """).fetchall()
8594:     conn.close()
8595:     return [dict(r) for r in rows]
8596: 
8597: def get_document_template_by_id(template_id):
8598:     conn = _learning_conn()
8599:     row = conn.execute("""
8600:         SELECT * FROM document_templates
8601:         WHERE template_id = ?
8602:     """, (template_id,)).fetchone()
8603:     conn.close()
8604:     return dict(row) if row else None
```

### `app.py:8611`

- Scope markers: `firm_id, session.get("firm_id")`

```python
8596: 
8597: def get_document_template_by_id(template_id):
8598:     conn = _learning_conn()
8599:     row = conn.execute("""
8600:         SELECT * FROM document_templates
8601:         WHERE template_id = ?
8602:     """, (template_id,)).fetchone()
8603:     conn.close()
8604:     return dict(row) if row else None
8605: 
8606: def get_generated_documents():
8607:     firm_id = session.get("firm_id") or "FIRM-001"
8608:     conn = _learning_conn()
8609:     rows = conn.execute("""
8610:         SELECT * FROM generated_documents
8611:         WHERE owner_id = ?
8612:           AND firm_id = ?
8613:         ORDER BY created_at DESC, title
8614:     """, (get_current_owner(), firm_id)).fetchall()
8615:     conn.close()
8616:     return [dict(r) for r in rows]
8617: 
8618: def get_generated_documents_by_workspace(workspace_id):
8619:     firm_id = session.get("firm_id") or "FIRM-001"
8620:     conn = _learning_conn()
8621:     rows = conn.execute("""
8622:         SELECT * FROM generated_documents
8623:         WHERE workspace_id = ?
8624:           AND owner_id = ?
8625:           AND firm_id = ?
8626:         ORDER BY created_at DESC, title
8627:     """, (workspace_id, get_current_owner(), firm_id)).fetchall()
8628:     conn.close()
8629:     return [dict(r) for r in rows]
8630: 
8631: def get_generated_document_by_id(document_id):
8632:     firm_id = session.get("firm_id") or "FIRM-001"
8633:     conn = _learning_conn()
8634:     row = conn.execute("""
8635:         SELECT * FROM generated_documents
8636:         WHERE document_id = ?
```

### `app.py:8624`

- Scope markers: `firm_id, session.get("firm_id")`

```python
8609:     rows = conn.execute("""
8610:         SELECT * FROM generated_documents
8611:         WHERE owner_id = ?
8612:           AND firm_id = ?
8613:         ORDER BY created_at DESC, title
8614:     """, (get_current_owner(), firm_id)).fetchall()
8615:     conn.close()
8616:     return [dict(r) for r in rows]
8617: 
8618: def get_generated_documents_by_workspace(workspace_id):
8619:     firm_id = session.get("firm_id") or "FIRM-001"
8620:     conn = _learning_conn()
8621:     rows = conn.execute("""
8622:         SELECT * FROM generated_documents
8623:         WHERE workspace_id = ?
8624:           AND owner_id = ?
8625:           AND firm_id = ?
8626:         ORDER BY created_at DESC, title
8627:     """, (workspace_id, get_current_owner(), firm_id)).fetchall()
8628:     conn.close()
8629:     return [dict(r) for r in rows]
8630: 
8631: def get_generated_document_by_id(document_id):
8632:     firm_id = session.get("firm_id") or "FIRM-001"
8633:     conn = _learning_conn()
8634:     row = conn.execute("""
8635:         SELECT * FROM generated_documents
8636:         WHERE document_id = ?
8637:           AND firm_id = ?
8638:     """, (document_id, firm_id)).fetchone()
8639:     conn.close()
8640:     return dict(row) if row else None
8641: 
8642: def create_generated_document(payload):
8643:     payload = dict(payload)
8644:     payload.setdefault("firm_id", session.get("firm_id") or "FIRM-001")
8645: 
8646:     conn = _learning_conn()
8647:     conn.execute("""
8648:         INSERT INTO generated_documents (
8649:             document_id, workspace_id, trust_id, template_id, title, content, status, created_by, firm_id
```

### `app.py:8676`

- Scope markers: `firm_id, session.get("firm_id")`

```python
8661:     ))
8662:     conn.commit()
8663:     conn.close()
8664: 
8665: def render_document_template(template_body, values):
8666:     content = template_body or ""
8667:     for key, value in (values or {}).items():
8668:         content = content.replace("{{" + key + "}}", value or "")
8669:     return content
8670: 
8671: def get_all_execution_tasks():
8672:     firm_id = session.get("firm_id") or "FIRM-001"
8673:     conn = _learning_conn()
8674:     rows = conn.execute("""
8675:         SELECT * FROM execution_tasks
8676:         WHERE owner_id = ?
8677:           AND firm_id = ?
8678:         ORDER BY created_at DESC, title
8679:     """, (get_current_owner(), firm_id)).fetchall()
8680:     conn.close()
8681:     return [dict(r) for r in rows]
8682: 
8683: def get_execution_tasks_by_workspace(workspace_id):
8684:     firm_id = session.get("firm_id") or "FIRM-001"
8685:     conn = _learning_conn()
8686:     rows = conn.execute("""
8687:         SELECT * FROM execution_tasks
8688:         WHERE workspace_id = ?
8689:           AND owner_id = ?
8690:           AND firm_id = ?
8691:         ORDER BY created_at DESC, title
8692:     """, (workspace_id, get_current_owner(), firm_id)).fetchall()
8693:     conn.close()
8694:     return [dict(r) for r in rows]
8695: 
8696: def get_execution_task_by_id(task_id):
8697:     firm_id = session.get("firm_id") or "FIRM-001"
8698:     conn = _learning_conn()
8699:     row = conn.execute("""
8700:         SELECT * FROM execution_tasks
8701:         WHERE task_id = ?
```

### `app.py:8689`

- Scope markers: `firm_id, session.get("firm_id")`

```python
8674:     rows = conn.execute("""
8675:         SELECT * FROM execution_tasks
8676:         WHERE owner_id = ?
8677:           AND firm_id = ?
8678:         ORDER BY created_at DESC, title
8679:     """, (get_current_owner(), firm_id)).fetchall()
8680:     conn.close()
8681:     return [dict(r) for r in rows]
8682: 
8683: def get_execution_tasks_by_workspace(workspace_id):
8684:     firm_id = session.get("firm_id") or "FIRM-001"
8685:     conn = _learning_conn()
8686:     rows = conn.execute("""
8687:         SELECT * FROM execution_tasks
8688:         WHERE workspace_id = ?
8689:           AND owner_id = ?
8690:           AND firm_id = ?
8691:         ORDER BY created_at DESC, title
8692:     """, (workspace_id, get_current_owner(), firm_id)).fetchall()
8693:     conn.close()
8694:     return [dict(r) for r in rows]
8695: 
8696: def get_execution_task_by_id(task_id):
8697:     firm_id = session.get("firm_id") or "FIRM-001"
8698:     conn = _learning_conn()
8699:     row = conn.execute("""
8700:         SELECT * FROM execution_tasks
8701:         WHERE task_id = ?
8702:           AND firm_id = ?
8703:     """, (task_id, firm_id)).fetchone()
8704:     conn.close()
8705:     return dict(row) if row else None
8706: 
8707: def create_execution_task(payload):
8708:     payload = dict(payload)
8709:     payload.setdefault("firm_id", session.get("firm_id") or "FIRM-001")
8710: 
8711:     conn = _learning_conn()
8712:     conn.execute("""
8713:         INSERT INTO execution_tasks (
8714:             task_id, workspace_id, trust_id, title, task_type, description,
```

### `app.py:8716`

- Scope markers: `firm_id, session.get("firm_id")`

```python
8701:         WHERE task_id = ?
8702:           AND firm_id = ?
8703:     """, (task_id, firm_id)).fetchone()
8704:     conn.close()
8705:     return dict(row) if row else None
8706: 
8707: def create_execution_task(payload):
8708:     payload = dict(payload)
8709:     payload.setdefault("firm_id", session.get("firm_id") or "FIRM-001")
8710: 
8711:     conn = _learning_conn()
8712:     conn.execute("""
8713:         INSERT INTO execution_tasks (
8714:             task_id, workspace_id, trust_id, title, task_type, description,
8715:             related_form, related_report, priority, status, due_date,
8716:             assigned_to, owner_id, created_at, updated_at, firm_id
8717:         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
8718:     """, (
8719:         payload.get("task_id"),
8720:         payload.get("workspace_id"),
8721:         payload.get("trust_id"),
8722:         payload.get("title"),
8723:         payload.get("task_type"),
8724:         payload.get("description"),
8725:         payload.get("related_form"),
8726:         payload.get("related_report"),
8727:         payload.get("priority"),
8728:         payload.get("status"),
8729:         payload.get("due_date"),
8730:         payload.get("assigned_to") or session.get("username") or "unknown",
8731:         get_current_owner(),
8732:         payload.get("firm_id"),
8733:     ))
8734:     conn.commit()
8735:     conn.close()
8736: 
8737: def update_execution_task_status(task_id, status):
8738:     firm_id = session.get("firm_id") or "FIRM-001"
8739:     conn = _learning_conn()
8740:     conn.execute("""
8741:         UPDATE execution_tasks
```

### `app.py:8800`

- Scope markers: `none detected`

```python
8785: 
8786:     # fallback broader match by goal only
8787:     conn = _learning_conn()
8788:     rows = conn.execute("""
8789:         SELECT * FROM decision_rules
8790:         WHERE lower(goal) = lower(?)
8791:         ORDER BY rule_id
8792:     """, (goal,)).fetchall()
8793:     conn.close()
8794:     return [dict(r) for r in rows]
8795: 
8796: def get_all_discussion_threads():
8797:     conn = _learning_conn()
8798:     rows = conn.execute("""
8799:         SELECT * FROM discussion_threads
8800:         WHERE owner_id = ?
8801:         ORDER BY created_at DESC, title
8802:     """, (get_current_owner(),)).fetchall()
8803:     conn.close()
8804:     return [dict(r) for r in rows]
8805: 
8806: def get_discussion_threads_by_workspace(workspace_id):
8807:     conn = _learning_conn()
8808:     rows = conn.execute("""
8809:         SELECT * FROM discussion_threads
8810:         WHERE workspace_id = ?
8811:           AND owner_id = ?
8812:         ORDER BY created_at DESC, title
8813:     """, (workspace_id, get_current_owner())).fetchall()
8814:     conn.close()
8815:     return [dict(r) for r in rows]
8816: 
8817: def get_discussion_thread_by_id(thread_id):
8818:     conn = _learning_conn()
8819:     row = conn.execute("""
8820:         SELECT * FROM discussion_threads
8821:         WHERE thread_id = ?
8822:     """, (thread_id,)).fetchone()
8823:     conn.close()
8824:     return dict(row) if row else None
8825: 
```

### `app.py:8811`

- Scope markers: `none detected`

```python
8796: def get_all_discussion_threads():
8797:     conn = _learning_conn()
8798:     rows = conn.execute("""
8799:         SELECT * FROM discussion_threads
8800:         WHERE owner_id = ?
8801:         ORDER BY created_at DESC, title
8802:     """, (get_current_owner(),)).fetchall()
8803:     conn.close()
8804:     return [dict(r) for r in rows]
8805: 
8806: def get_discussion_threads_by_workspace(workspace_id):
8807:     conn = _learning_conn()
8808:     rows = conn.execute("""
8809:         SELECT * FROM discussion_threads
8810:         WHERE workspace_id = ?
8811:           AND owner_id = ?
8812:         ORDER BY created_at DESC, title
8813:     """, (workspace_id, get_current_owner())).fetchall()
8814:     conn.close()
8815:     return [dict(r) for r in rows]
8816: 
8817: def get_discussion_thread_by_id(thread_id):
8818:     conn = _learning_conn()
8819:     row = conn.execute("""
8820:         SELECT * FROM discussion_threads
8821:         WHERE thread_id = ?
8822:     """, (thread_id,)).fetchone()
8823:     conn.close()
8824:     return dict(row) if row else None
8825: 
8826: def create_discussion_thread(payload):
8827:     conn = _learning_conn()
8828:     conn.execute("""
8829:         INSERT INTO discussion_threads (
8830:             thread_id, workspace_id, title, category, related_trust_type,
8831:             related_form, created_by, status
8832:         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
8833:     """, (
8834:         payload.get("thread_id"),
8835:         payload.get("workspace_id"),
8836:         payload.get("title"),
```

### `app.py:8882`

- Scope markers: `firm_id, session.get("firm_id")`

```python
8867:         payload.get("body"),
8868:     ))
8869:     conn.commit()
8870:     conn.close()
8871: 
8872: def get_discussion_categories():
8873:     return [
8874:         "general_design_discussion",
8875:         "trust_type_questions",
8876:         "tax_forms_questions",
8877:         "asset_structuring_questions",
8878:         "fiduciary_process_questions",
8879:         "video_linked_discussion",
8880:     ]
8881: 
8882: def get_all_workspaces():
8883:     firm_id = session.get("firm_id") or "FIRM-001"
8884:     conn = _learning_conn()
8885:     rows = conn.execute("""
8886:         SELECT * FROM workspaces
8887:         WHERE firm_id = ?
8888:         ORDER BY created_at DESC, title
8889:     """, (firm_id,)).fetchall()
8890:     conn.close()
8891:     return [dict(r) for r in rows]
8892: 
8893: def get_workspace_by_id(workspace_id):
8894:     firm_id = session.get("firm_id") or "FIRM-001"
8895:     conn = _learning_conn()
8896:     row = conn.execute("""
8897:         SELECT * FROM workspaces
8898:         WHERE workspace_id = ?
8899:           AND firm_id = ?
8900:     """, (workspace_id, firm_id)).fetchone()
8901:     conn.close()
8902:     return dict(row) if row else None
8903: 
8904: def create_workspace(payload):
8905:     payload = dict(payload)
8906:     payload.setdefault("firm_id", session.get("firm_id") or "FIRM-001")
8907:     payload.setdefault("owner_id", get_current_owner())
```

### `app.py:8886`

- Scope markers: `firm_id, session.get("firm_id")`

```python
8871: 
8872: def get_discussion_categories():
8873:     return [
8874:         "general_design_discussion",
8875:         "trust_type_questions",
8876:         "tax_forms_questions",
8877:         "asset_structuring_questions",
8878:         "fiduciary_process_questions",
8879:         "video_linked_discussion",
8880:     ]
8881: 
8882: def get_all_workspaces():
8883:     firm_id = session.get("firm_id") or "FIRM-001"
8884:     conn = _learning_conn()
8885:     rows = conn.execute("""
8886:         SELECT * FROM workspaces
8887:         WHERE firm_id = ?
8888:         ORDER BY created_at DESC, title
8889:     """, (firm_id,)).fetchall()
8890:     conn.close()
8891:     return [dict(r) for r in rows]
8892: 
8893: def get_workspace_by_id(workspace_id):
8894:     firm_id = session.get("firm_id") or "FIRM-001"
8895:     conn = _learning_conn()
8896:     row = conn.execute("""
8897:         SELECT * FROM workspaces
8898:         WHERE workspace_id = ?
8899:           AND firm_id = ?
8900:     """, (workspace_id, firm_id)).fetchone()
8901:     conn.close()
8902:     return dict(row) if row else None
8903: 
8904: def create_workspace(payload):
8905:     payload = dict(payload)
8906:     payload.setdefault("firm_id", session.get("firm_id") or "FIRM-001")
8907:     payload.setdefault("owner_id", get_current_owner())
8908: 
8909:     conn = _learning_conn()
8910:     conn.execute("""
8911:         INSERT INTO workspaces (
```

### `app.py:8897`

- Scope markers: `firm_id, session.get("firm_id")`

```python
8882: def get_all_workspaces():
8883:     firm_id = session.get("firm_id") or "FIRM-001"
8884:     conn = _learning_conn()
8885:     rows = conn.execute("""
8886:         SELECT * FROM workspaces
8887:         WHERE firm_id = ?
8888:         ORDER BY created_at DESC, title
8889:     """, (firm_id,)).fetchall()
8890:     conn.close()
8891:     return [dict(r) for r in rows]
8892: 
8893: def get_workspace_by_id(workspace_id):
8894:     firm_id = session.get("firm_id") or "FIRM-001"
8895:     conn = _learning_conn()
8896:     row = conn.execute("""
8897:         SELECT * FROM workspaces
8898:         WHERE workspace_id = ?
8899:           AND firm_id = ?
8900:     """, (workspace_id, firm_id)).fetchone()
8901:     conn.close()
8902:     return dict(row) if row else None
8903: 
8904: def create_workspace(payload):
8905:     payload = dict(payload)
8906:     payload.setdefault("firm_id", session.get("firm_id") or "FIRM-001")
8907:     payload.setdefault("owner_id", get_current_owner())
8908: 
8909:     conn = _learning_conn()
8910:     conn.execute("""
8911:         INSERT INTO workspaces (
8912:             workspace_id, title, workspace_type, trust_type_focus, purpose, owner, status, owner_id, firm_id
8913:         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
8914:     """, (
8915:         payload.get("workspace_id"),
8916:         payload.get("title"),
8917:         payload.get("workspace_type"),
8918:         payload.get("trust_type_focus"),
8919:         payload.get("purpose"),
8920:         payload.get("owner"),
8921:         payload.get("status"),
8922:         payload.get("owner_id"),
```

### `app.py:8907`

- Scope markers: `firm_id, session.get("firm_id")`

```python
8892: 
8893: def get_workspace_by_id(workspace_id):
8894:     firm_id = session.get("firm_id") or "FIRM-001"
8895:     conn = _learning_conn()
8896:     row = conn.execute("""
8897:         SELECT * FROM workspaces
8898:         WHERE workspace_id = ?
8899:           AND firm_id = ?
8900:     """, (workspace_id, firm_id)).fetchone()
8901:     conn.close()
8902:     return dict(row) if row else None
8903: 
8904: def create_workspace(payload):
8905:     payload = dict(payload)
8906:     payload.setdefault("firm_id", session.get("firm_id") or "FIRM-001")
8907:     payload.setdefault("owner_id", get_current_owner())
8908: 
8909:     conn = _learning_conn()
8910:     conn.execute("""
8911:         INSERT INTO workspaces (
8912:             workspace_id, title, workspace_type, trust_type_focus, purpose, owner, status, owner_id, firm_id
8913:         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
8914:     """, (
8915:         payload.get("workspace_id"),
8916:         payload.get("title"),
8917:         payload.get("workspace_type"),
8918:         payload.get("trust_type_focus"),
8919:         payload.get("purpose"),
8920:         payload.get("owner"),
8921:         payload.get("status"),
8922:         payload.get("owner_id"),
8923:         payload.get("firm_id"),
8924:     ))
8925:     conn.commit()
8926:     conn.close()
8927: 
8928: def update_workspace(workspace_id, payload):
8929:     firm_id = session.get("firm_id") or "FIRM-001"
8930:     conn = _learning_conn()
8931:     conn.execute("""
8932:         UPDATE workspaces
```

### `app.py:8911`

- Scope markers: `firm_id, session.get("firm_id")`

```python
8896:     row = conn.execute("""
8897:         SELECT * FROM workspaces
8898:         WHERE workspace_id = ?
8899:           AND firm_id = ?
8900:     """, (workspace_id, firm_id)).fetchone()
8901:     conn.close()
8902:     return dict(row) if row else None
8903: 
8904: def create_workspace(payload):
8905:     payload = dict(payload)
8906:     payload.setdefault("firm_id", session.get("firm_id") or "FIRM-001")
8907:     payload.setdefault("owner_id", get_current_owner())
8908: 
8909:     conn = _learning_conn()
8910:     conn.execute("""
8911:         INSERT INTO workspaces (
8912:             workspace_id, title, workspace_type, trust_type_focus, purpose, owner, status, owner_id, firm_id
8913:         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
8914:     """, (
8915:         payload.get("workspace_id"),
8916:         payload.get("title"),
8917:         payload.get("workspace_type"),
8918:         payload.get("trust_type_focus"),
8919:         payload.get("purpose"),
8920:         payload.get("owner"),
8921:         payload.get("status"),
8922:         payload.get("owner_id"),
8923:         payload.get("firm_id"),
8924:     ))
8925:     conn.commit()
8926:     conn.close()
8927: 
8928: def update_workspace(workspace_id, payload):
8929:     firm_id = session.get("firm_id") or "FIRM-001"
8930:     conn = _learning_conn()
8931:     conn.execute("""
8932:         UPDATE workspaces
8933:         SET title = ?,
8934:             workspace_type = ?,
8935:             trust_type_focus = ?,
8936:             purpose = ?,
```

### `app.py:8912`

- Scope markers: `firm_id, session.get("firm_id")`

```python
8897:         SELECT * FROM workspaces
8898:         WHERE workspace_id = ?
8899:           AND firm_id = ?
8900:     """, (workspace_id, firm_id)).fetchone()
8901:     conn.close()
8902:     return dict(row) if row else None
8903: 
8904: def create_workspace(payload):
8905:     payload = dict(payload)
8906:     payload.setdefault("firm_id", session.get("firm_id") or "FIRM-001")
8907:     payload.setdefault("owner_id", get_current_owner())
8908: 
8909:     conn = _learning_conn()
8910:     conn.execute("""
8911:         INSERT INTO workspaces (
8912:             workspace_id, title, workspace_type, trust_type_focus, purpose, owner, status, owner_id, firm_id
8913:         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
8914:     """, (
8915:         payload.get("workspace_id"),
8916:         payload.get("title"),
8917:         payload.get("workspace_type"),
8918:         payload.get("trust_type_focus"),
8919:         payload.get("purpose"),
8920:         payload.get("owner"),
8921:         payload.get("status"),
8922:         payload.get("owner_id"),
8923:         payload.get("firm_id"),
8924:     ))
8925:     conn.commit()
8926:     conn.close()
8927: 
8928: def update_workspace(workspace_id, payload):
8929:     firm_id = session.get("firm_id") or "FIRM-001"
8930:     conn = _learning_conn()
8931:     conn.execute("""
8932:         UPDATE workspaces
8933:         SET title = ?,
8934:             workspace_type = ?,
8935:             trust_type_focus = ?,
8936:             purpose = ?,
8937:             owner = ?,
```

### `app.py:8922`

- Scope markers: `firm_id, session.get("firm_id")`

```python
8907:     payload.setdefault("owner_id", get_current_owner())
8908: 
8909:     conn = _learning_conn()
8910:     conn.execute("""
8911:         INSERT INTO workspaces (
8912:             workspace_id, title, workspace_type, trust_type_focus, purpose, owner, status, owner_id, firm_id
8913:         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
8914:     """, (
8915:         payload.get("workspace_id"),
8916:         payload.get("title"),
8917:         payload.get("workspace_type"),
8918:         payload.get("trust_type_focus"),
8919:         payload.get("purpose"),
8920:         payload.get("owner"),
8921:         payload.get("status"),
8922:         payload.get("owner_id"),
8923:         payload.get("firm_id"),
8924:     ))
8925:     conn.commit()
8926:     conn.close()
8927: 
8928: def update_workspace(workspace_id, payload):
8929:     firm_id = session.get("firm_id") or "FIRM-001"
8930:     conn = _learning_conn()
8931:     conn.execute("""
8932:         UPDATE workspaces
8933:         SET title = ?,
8934:             workspace_type = ?,
8935:             trust_type_focus = ?,
8936:             purpose = ?,
8937:             owner = ?,
8938:             status = ?,
8939:             updated_at = CURRENT_TIMESTAMP
8940:         WHERE workspace_id = ?
8941:           AND firm_id = ?
8942:     """, (
8943:         payload.get("title"),
8944:         payload.get("workspace_type"),
8945:         payload.get("trust_type_focus"),
8946:         payload.get("purpose"),
8947:         payload.get("owner"),
```

### `app.py:8932`

- Scope markers: `firm_id, session.get("firm_id")`

```python
8917:         payload.get("workspace_type"),
8918:         payload.get("trust_type_focus"),
8919:         payload.get("purpose"),
8920:         payload.get("owner"),
8921:         payload.get("status"),
8922:         payload.get("owner_id"),
8923:         payload.get("firm_id"),
8924:     ))
8925:     conn.commit()
8926:     conn.close()
8927: 
8928: def update_workspace(workspace_id, payload):
8929:     firm_id = session.get("firm_id") or "FIRM-001"
8930:     conn = _learning_conn()
8931:     conn.execute("""
8932:         UPDATE workspaces
8933:         SET title = ?,
8934:             workspace_type = ?,
8935:             trust_type_focus = ?,
8936:             purpose = ?,
8937:             owner = ?,
8938:             status = ?,
8939:             updated_at = CURRENT_TIMESTAMP
8940:         WHERE workspace_id = ?
8941:           AND firm_id = ?
8942:     """, (
8943:         payload.get("title"),
8944:         payload.get("workspace_type"),
8945:         payload.get("trust_type_focus"),
8946:         payload.get("purpose"),
8947:         payload.get("owner"),
8948:         payload.get("status"),
8949:         workspace_id,
8950:         firm_id,
8951:     ))
8952:     conn.commit()
8953:     conn.close()
8954: 
8955: def get_workspace_notes(workspace_id):
8956:     firm_id = session.get("firm_id") or "FIRM-001"
8957:     conn = _learning_conn()
```

### `app.py:9151`

- Scope markers: `none detected`

```python
9136:     ).fetchone()
9137:     conn.close()
9138:     return bool(row)
9139: 
9140: 
9141: def form_guide_exists(form_name):
9142:     conn = _learning_conn()
9143:     row = conn.execute(
9144:         "SELECT form_name FROM tax_form_guides WHERE lower(form_name) = lower(?) LIMIT 1",
9145:         (form_name,)
9146:     ).fetchone()
9147:     conn.close()
9148:     return bool(row)
9149: 
9150: 
9151: def trust_name_exists_for_owner(trust_name, owner_id):
9152:     # Baseline seed records must be idempotent even when legacy/local rows
9153:     # do not preserve owner_id. Match baseline trust names globally to avoid
9154:     # duplicate ABC seed records on repeated runs.
9155:     for trust in get_all_trusts():
9156:         trust_row = dict(trust)
9157:         existing_name = (trust_row.get("trust_name") or "").strip().lower()
9158:         if existing_name == trust_name.strip().lower():
9159:             return True
9160:     return False
9161: 
9162: 
9163: def seed_hosted_baseline_data(owner_id):
9164:     results = {
9165:         "trusts_created": [],
9166:         "trusts_skipped": [],
9167:         "learning_articles_created": [],
9168:         "learning_articles_skipped": [],
9169:         "form_guides_created": [],
9170:         "form_guides_skipped": [],
9171:     }
9172: 
9173:     baseline_trusts = [
9174:         {
9175:             "trust_name": "ABC Trust",
9176:             "short_name": "ABC",
```

### `app.py:9153`

- Scope markers: `none detected`

```python
9138:     return bool(row)
9139: 
9140: 
9141: def form_guide_exists(form_name):
9142:     conn = _learning_conn()
9143:     row = conn.execute(
9144:         "SELECT form_name FROM tax_form_guides WHERE lower(form_name) = lower(?) LIMIT 1",
9145:         (form_name,)
9146:     ).fetchone()
9147:     conn.close()
9148:     return bool(row)
9149: 
9150: 
9151: def trust_name_exists_for_owner(trust_name, owner_id):
9152:     # Baseline seed records must be idempotent even when legacy/local rows
9153:     # do not preserve owner_id. Match baseline trust names globally to avoid
9154:     # duplicate ABC seed records on repeated runs.
9155:     for trust in get_all_trusts():
9156:         trust_row = dict(trust)
9157:         existing_name = (trust_row.get("trust_name") or "").strip().lower()
9158:         if existing_name == trust_name.strip().lower():
9159:             return True
9160:     return False
9161: 
9162: 
9163: def seed_hosted_baseline_data(owner_id):
9164:     results = {
9165:         "trusts_created": [],
9166:         "trusts_skipped": [],
9167:         "learning_articles_created": [],
9168:         "learning_articles_skipped": [],
9169:         "form_guides_created": [],
9170:         "form_guides_skipped": [],
9171:     }
9172: 
9173:     baseline_trusts = [
9174:         {
9175:             "trust_name": "ABC Trust",
9176:             "short_name": "ABC",
9177:             "jurisdiction": "New Jersey",
9178:             "effective_date": "2026-05-01",
```

### `app.py:9163`

- Scope markers: `none detected`

```python
9148:     return bool(row)
9149: 
9150: 
9151: def trust_name_exists_for_owner(trust_name, owner_id):
9152:     # Baseline seed records must be idempotent even when legacy/local rows
9153:     # do not preserve owner_id. Match baseline trust names globally to avoid
9154:     # duplicate ABC seed records on repeated runs.
9155:     for trust in get_all_trusts():
9156:         trust_row = dict(trust)
9157:         existing_name = (trust_row.get("trust_name") or "").strip().lower()
9158:         if existing_name == trust_name.strip().lower():
9159:             return True
9160:     return False
9161: 
9162: 
9163: def seed_hosted_baseline_data(owner_id):
9164:     results = {
9165:         "trusts_created": [],
9166:         "trusts_skipped": [],
9167:         "learning_articles_created": [],
9168:         "learning_articles_skipped": [],
9169:         "form_guides_created": [],
9170:         "form_guides_skipped": [],
9171:     }
9172: 
9173:     baseline_trusts = [
9174:         {
9175:             "trust_name": "ABC Trust",
9176:             "short_name": "ABC",
9177:             "jurisdiction": "New Jersey",
9178:             "effective_date": "2026-05-01",
9179:             "trust_type": "revocable",
9180:             "trust_purpose": "baseline_governance_testing",
9181:             "accounting_method": "cash",
9182:             "workflow_mode": "private_office",
9183:             "settlor_name": "Baseline Settlor",
9184:             "trustee_name": "Baseline Trustee",
9185:             "successor_trustee_name": "Baseline Successor Trustee",
9186:             "beneficiary_name": "Baseline Beneficiary",
9187:             "record_visibility": "private",
9188:             "workflow_mode_confirmed": "private_office",
```

### `app.py:9196`

- Scope markers: `none detected`

```python
9181:             "accounting_method": "cash",
9182:             "workflow_mode": "private_office",
9183:             "settlor_name": "Baseline Settlor",
9184:             "trustee_name": "Baseline Trustee",
9185:             "successor_trustee_name": "Baseline Successor Trustee",
9186:             "beneficiary_name": "Baseline Beneficiary",
9187:             "record_visibility": "private",
9188:             "workflow_mode_confirmed": "private_office",
9189:             "ai_explanations": "enabled",
9190:             "recommended_guidance": "enabled",
9191:             "initial_corpus_description": "Baseline seed corpus for hosted runtime validation.",
9192:             "property_mapping_timing": "now",
9193:             "asset_categories": "records",
9194:             "generate_schedule_recommendations": "yes",
9195:             "status": "Draft",
9196:             "owner_id": owner_id,
9197:         },
9198:         {
9199:             "trust_name": "ABC Irrevocable Trust",
9200:             "short_name": "ABC-IRR",
9201:             "jurisdiction": "New Jersey",
9202:             "effective_date": "2026-05-01",
9203:             "trust_type": "irrevocable",
9204:             "trust_purpose": "baseline_irrevocable_structure_testing",
9205:             "accounting_method": "cash",
9206:             "workflow_mode": "private_office",
9207:             "settlor_name": "Baseline Grantor",
9208:             "trustee_name": "Baseline Trustee",
9209:             "successor_trustee_name": "Baseline Successor Trustee",
9210:             "beneficiary_name": "Baseline Beneficiary",
9211:             "record_visibility": "private",
9212:             "workflow_mode_confirmed": "private_office",
9213:             "ai_explanations": "enabled",
9214:             "recommended_guidance": "enabled",
9215:             "initial_corpus_description": "Baseline seed corpus for irrevocable trust workflow validation.",
9216:             "property_mapping_timing": "later",
9217:             "asset_categories": "records",
9218:             "generate_schedule_recommendations": "yes",
9219:             "status": "Draft",
9220:             "owner_id": owner_id,
9221:         },
```

### `app.py:9220`

- Scope markers: `none detected`

```python
9205:             "accounting_method": "cash",
9206:             "workflow_mode": "private_office",
9207:             "settlor_name": "Baseline Grantor",
9208:             "trustee_name": "Baseline Trustee",
9209:             "successor_trustee_name": "Baseline Successor Trustee",
9210:             "beneficiary_name": "Baseline Beneficiary",
9211:             "record_visibility": "private",
9212:             "workflow_mode_confirmed": "private_office",
9213:             "ai_explanations": "enabled",
9214:             "recommended_guidance": "enabled",
9215:             "initial_corpus_description": "Baseline seed corpus for irrevocable trust workflow validation.",
9216:             "property_mapping_timing": "later",
9217:             "asset_categories": "records",
9218:             "generate_schedule_recommendations": "yes",
9219:             "status": "Draft",
9220:             "owner_id": owner_id,
9221:         },
9222:         {
9223:             "trust_name": "ABC Business Trust",
9224:             "short_name": "ABC-BIZ",
9225:             "jurisdiction": "New Jersey",
9226:             "effective_date": "2026-05-01",
9227:             "trust_type": "business",
9228:             "trust_purpose": "baseline_business_trust_testing",
9229:             "accounting_method": "accrual",
9230:             "workflow_mode": "private_office",
9231:             "settlor_name": "Baseline Grantor",
9232:             "trustee_name": "Baseline Trustee",
9233:             "successor_trustee_name": "Baseline Successor Trustee",
9234:             "beneficiary_name": "Baseline Beneficiary",
9235:             "record_visibility": "internal",
9236:             "workflow_mode_confirmed": "private_office",
9237:             "ai_explanations": "enabled",
9238:             "recommended_guidance": "enabled",
9239:             "initial_corpus_description": "Baseline seed corpus for business trust workflow validation.",
9240:             "property_mapping_timing": "now",
9241:             "asset_categories": "business_records",
9242:             "generate_schedule_recommendations": "yes",
9243:             "status": "Draft",
9244:             "owner_id": owner_id,
9245:         },
```

### `app.py:9244`

- Scope markers: `none detected`

```python
9229:             "accounting_method": "accrual",
9230:             "workflow_mode": "private_office",
9231:             "settlor_name": "Baseline Grantor",
9232:             "trustee_name": "Baseline Trustee",
9233:             "successor_trustee_name": "Baseline Successor Trustee",
9234:             "beneficiary_name": "Baseline Beneficiary",
9235:             "record_visibility": "internal",
9236:             "workflow_mode_confirmed": "private_office",
9237:             "ai_explanations": "enabled",
9238:             "recommended_guidance": "enabled",
9239:             "initial_corpus_description": "Baseline seed corpus for business trust workflow validation.",
9240:             "property_mapping_timing": "now",
9241:             "asset_categories": "business_records",
9242:             "generate_schedule_recommendations": "yes",
9243:             "status": "Draft",
9244:             "owner_id": owner_id,
9245:         },
9246:     ]
9247: 
9248:     for trust_payload in baseline_trusts:
9249:         trust_name = trust_payload["trust_name"]
9250:         if trust_name_exists_for_owner(trust_name, owner_id):
9251:             results["trusts_skipped"].append(trust_name)
9252:             continue
9253: 
9254:         trust_payload = dict(trust_payload)
9255:         trust_payload["trust_id"] = get_next_trust_id()
9256:         create_trust_record(trust_payload)
9257:         results["trusts_created"].append(f"{trust_payload['trust_id']} — {trust_name}")
9258: 
9259:     starter_articles = [
9260:         {
9261:             "article_id": "ART-TRUST-BASICS-001",
9262:             "title": "Trust Administration Basics",
9263:             "category": "Trust Administration",
9264:             "subcategory": "Foundations",
9265:             "trust_type": "general",
9266:             "summary": "A starter guide explaining the basic records and workflow surfaces used in the Trustee App.",
9267:             "body": "This article introduces trust identity, parties, property mapping, minutes, certificates, and packet review as separate workflow layers.",
9268:             "difficulty_level": "beginner",
9269:             "related_forms": "Trust Minutes, Certificate Registry, Formation Preview Hub",
```

### `app.py:9250`

- Scope markers: `none detected`

```python
9235:             "record_visibility": "internal",
9236:             "workflow_mode_confirmed": "private_office",
9237:             "ai_explanations": "enabled",
9238:             "recommended_guidance": "enabled",
9239:             "initial_corpus_description": "Baseline seed corpus for business trust workflow validation.",
9240:             "property_mapping_timing": "now",
9241:             "asset_categories": "business_records",
9242:             "generate_schedule_recommendations": "yes",
9243:             "status": "Draft",
9244:             "owner_id": owner_id,
9245:         },
9246:     ]
9247: 
9248:     for trust_payload in baseline_trusts:
9249:         trust_name = trust_payload["trust_name"]
9250:         if trust_name_exists_for_owner(trust_name, owner_id):
9251:             results["trusts_skipped"].append(trust_name)
9252:             continue
9253: 
9254:         trust_payload = dict(trust_payload)
9255:         trust_payload["trust_id"] = get_next_trust_id()
9256:         create_trust_record(trust_payload)
9257:         results["trusts_created"].append(f"{trust_payload['trust_id']} — {trust_name}")
9258: 
9259:     starter_articles = [
9260:         {
9261:             "article_id": "ART-TRUST-BASICS-001",
9262:             "title": "Trust Administration Basics",
9263:             "category": "Trust Administration",
9264:             "subcategory": "Foundations",
9265:             "trust_type": "general",
9266:             "summary": "A starter guide explaining the basic records and workflow surfaces used in the Trustee App.",
9267:             "body": "This article introduces trust identity, parties, property mapping, minutes, certificates, and packet review as separate workflow layers.",
9268:             "difficulty_level": "beginner",
9269:             "related_forms": "Trust Minutes, Certificate Registry, Formation Preview Hub",
9270:             "related_reports": "Report Center, System Health",
9271:             "status": "published",
9272:         },
9273:         {
9274:             "article_id": "ART-CERTIFICATES-001",
9275:             "title": "Execution Certificates and Audit Trails",
```

### `app.py:10412`

- Scope markers: `none detected`

```python
10397:         payload = {
10398:             "title": request.form.get("title"),
10399:             "category": request.form.get("category"),
10400:             "trust_type": request.form.get("trust_type"),
10401:             "description": request.form.get("description"),
10402:             "file_path": request.form.get("file_path"),
10403:             "thumbnail_path": request.form.get("thumbnail_path"),
10404:             "transcript_notes": request.form.get("transcript_notes"),
10405:             "visibility": request.form.get("visibility") or "internal",
10406:         }
10407:         update_tutorial_video(video_id, payload)
10408:         return redirect(url_for("video_detail", video_id=video_id))
10409: 
10410:     return render_template("video_upload.html", mode="edit", video=video)
10411: 
10412: @app.route("/workspaces")
10413: def workspace_dashboard():
10414:     workspaces = get_all_workspaces()
10415:     return render_template("workspace_dashboard.html", workspaces=workspaces)
10416: 
10417: 
10418: @app.route("/workspaces/new", methods=["GET", "POST"])
10419: def workspace_new():
10420:     if request.method == "POST":
10421:         if not validate_csrf_token():
10422:             return render_template("workspace_form.html", mode="new", error_message="Invalid or missing CSRF token.", sections=get_workspace_note_sections())
10423: 
10424:         workspace_id = (request.form.get("workspace_id") or "").strip()
10425:         title = (request.form.get("title") or "").strip()
10426:         if not workspace_id or not title:
10427:             return render_template("workspace_form.html", mode="new", error_message="Workspace ID and Title are required.", sections=get_workspace_note_sections())
10428: 
10429:         payload = {
10430:             "workspace_id": workspace_id,
10431:             "title": title,
10432:             "workspace_type": request.form.get("workspace_type"),
10433:             "trust_type_focus": request.form.get("trust_type_focus"),
10434:             "purpose": request.form.get("purpose"),
10435:             "owner": request.form.get("owner") or session.get("username") or "unknown",
10436:             "status": request.form.get("status") or "draft",
10437:         }
```

### `app.py:10414`

- Scope markers: `none detected`

```python
10399:             "category": request.form.get("category"),
10400:             "trust_type": request.form.get("trust_type"),
10401:             "description": request.form.get("description"),
10402:             "file_path": request.form.get("file_path"),
10403:             "thumbnail_path": request.form.get("thumbnail_path"),
10404:             "transcript_notes": request.form.get("transcript_notes"),
10405:             "visibility": request.form.get("visibility") or "internal",
10406:         }
10407:         update_tutorial_video(video_id, payload)
10408:         return redirect(url_for("video_detail", video_id=video_id))
10409: 
10410:     return render_template("video_upload.html", mode="edit", video=video)
10411: 
10412: @app.route("/workspaces")
10413: def workspace_dashboard():
10414:     workspaces = get_all_workspaces()
10415:     return render_template("workspace_dashboard.html", workspaces=workspaces)
10416: 
10417: 
10418: @app.route("/workspaces/new", methods=["GET", "POST"])
10419: def workspace_new():
10420:     if request.method == "POST":
10421:         if not validate_csrf_token():
10422:             return render_template("workspace_form.html", mode="new", error_message="Invalid or missing CSRF token.", sections=get_workspace_note_sections())
10423: 
10424:         workspace_id = (request.form.get("workspace_id") or "").strip()
10425:         title = (request.form.get("title") or "").strip()
10426:         if not workspace_id or not title:
10427:             return render_template("workspace_form.html", mode="new", error_message="Workspace ID and Title are required.", sections=get_workspace_note_sections())
10428: 
10429:         payload = {
10430:             "workspace_id": workspace_id,
10431:             "title": title,
10432:             "workspace_type": request.form.get("workspace_type"),
10433:             "trust_type_focus": request.form.get("trust_type_focus"),
10434:             "purpose": request.form.get("purpose"),
10435:             "owner": request.form.get("owner") or session.get("username") or "unknown",
10436:             "status": request.form.get("status") or "draft",
10437:         }
10438:         create_workspace(payload)
10439:         return redirect(url_for("workspace_detail", workspace_id=workspace_id))
```

### `app.py:10415`

- Scope markers: `none detected`

```python
10400:             "trust_type": request.form.get("trust_type"),
10401:             "description": request.form.get("description"),
10402:             "file_path": request.form.get("file_path"),
10403:             "thumbnail_path": request.form.get("thumbnail_path"),
10404:             "transcript_notes": request.form.get("transcript_notes"),
10405:             "visibility": request.form.get("visibility") or "internal",
10406:         }
10407:         update_tutorial_video(video_id, payload)
10408:         return redirect(url_for("video_detail", video_id=video_id))
10409: 
10410:     return render_template("video_upload.html", mode="edit", video=video)
10411: 
10412: @app.route("/workspaces")
10413: def workspace_dashboard():
10414:     workspaces = get_all_workspaces()
10415:     return render_template("workspace_dashboard.html", workspaces=workspaces)
10416: 
10417: 
10418: @app.route("/workspaces/new", methods=["GET", "POST"])
10419: def workspace_new():
10420:     if request.method == "POST":
10421:         if not validate_csrf_token():
10422:             return render_template("workspace_form.html", mode="new", error_message="Invalid or missing CSRF token.", sections=get_workspace_note_sections())
10423: 
10424:         workspace_id = (request.form.get("workspace_id") or "").strip()
10425:         title = (request.form.get("title") or "").strip()
10426:         if not workspace_id or not title:
10427:             return render_template("workspace_form.html", mode="new", error_message="Workspace ID and Title are required.", sections=get_workspace_note_sections())
10428: 
10429:         payload = {
10430:             "workspace_id": workspace_id,
10431:             "title": title,
10432:             "workspace_type": request.form.get("workspace_type"),
10433:             "trust_type_focus": request.form.get("trust_type_focus"),
10434:             "purpose": request.form.get("purpose"),
10435:             "owner": request.form.get("owner") or session.get("username") or "unknown",
10436:             "status": request.form.get("status") or "draft",
10437:         }
10438:         create_workspace(payload)
10439:         return redirect(url_for("workspace_detail", workspace_id=workspace_id))
10440: 
```

### `app.py:10418`

- Scope markers: `none detected`

```python
10403:             "thumbnail_path": request.form.get("thumbnail_path"),
10404:             "transcript_notes": request.form.get("transcript_notes"),
10405:             "visibility": request.form.get("visibility") or "internal",
10406:         }
10407:         update_tutorial_video(video_id, payload)
10408:         return redirect(url_for("video_detail", video_id=video_id))
10409: 
10410:     return render_template("video_upload.html", mode="edit", video=video)
10411: 
10412: @app.route("/workspaces")
10413: def workspace_dashboard():
10414:     workspaces = get_all_workspaces()
10415:     return render_template("workspace_dashboard.html", workspaces=workspaces)
10416: 
10417: 
10418: @app.route("/workspaces/new", methods=["GET", "POST"])
10419: def workspace_new():
10420:     if request.method == "POST":
10421:         if not validate_csrf_token():
10422:             return render_template("workspace_form.html", mode="new", error_message="Invalid or missing CSRF token.", sections=get_workspace_note_sections())
10423: 
10424:         workspace_id = (request.form.get("workspace_id") or "").strip()
10425:         title = (request.form.get("title") or "").strip()
10426:         if not workspace_id or not title:
10427:             return render_template("workspace_form.html", mode="new", error_message="Workspace ID and Title are required.", sections=get_workspace_note_sections())
10428: 
10429:         payload = {
10430:             "workspace_id": workspace_id,
10431:             "title": title,
10432:             "workspace_type": request.form.get("workspace_type"),
10433:             "trust_type_focus": request.form.get("trust_type_focus"),
10434:             "purpose": request.form.get("purpose"),
10435:             "owner": request.form.get("owner") or session.get("username") or "unknown",
10436:             "status": request.form.get("status") or "draft",
10437:         }
10438:         create_workspace(payload)
10439:         return redirect(url_for("workspace_detail", workspace_id=workspace_id))
10440: 
10441:     return render_template("workspace_form.html", mode="new", sections=get_workspace_note_sections())
10442: 
10443: 
```

### `app.py:10444`

- Scope markers: `none detected`

```python
10429:         payload = {
10430:             "workspace_id": workspace_id,
10431:             "title": title,
10432:             "workspace_type": request.form.get("workspace_type"),
10433:             "trust_type_focus": request.form.get("trust_type_focus"),
10434:             "purpose": request.form.get("purpose"),
10435:             "owner": request.form.get("owner") or session.get("username") or "unknown",
10436:             "status": request.form.get("status") or "draft",
10437:         }
10438:         create_workspace(payload)
10439:         return redirect(url_for("workspace_detail", workspace_id=workspace_id))
10440: 
10441:     return render_template("workspace_form.html", mode="new", sections=get_workspace_note_sections())
10442: 
10443: 
10444: @app.route("/workspaces/<workspace_id>")
10445: def workspace_detail(workspace_id):
10446:     workspace = get_workspace_by_id(workspace_id)
10447:     if not workspace:
10448:         return render_template(
10449:             "access_denied.html",
10450:             reason="This workspace is not available within your assigned firm scope."
10451:         )
10452: 
10453:     notes = get_workspace_notes(workspace_id)
10454:     tasks = get_execution_tasks_by_workspace(workspace_id)
10455:     documents = get_generated_documents_by_workspace(workspace_id)
10456:     threads = get_discussion_threads_by_workspace(workspace_id)
10457: 
10458:     return render_template(
10459:         "workspace_detail.html",
10460:         workspace=workspace,
10461:         notes=notes,
10462:         tasks=tasks,
10463:         documents=documents,
10464:         threads=threads,
10465:         note_sections=get_workspace_note_sections()
10466:     )
10467: 
10468: 
10469: @app.route("/workspaces/<workspace_id>/edit", methods=["GET", "POST"])
```

### `app.py:10469`

- Scope markers: `none detected`

```python
10454:     tasks = get_execution_tasks_by_workspace(workspace_id)
10455:     documents = get_generated_documents_by_workspace(workspace_id)
10456:     threads = get_discussion_threads_by_workspace(workspace_id)
10457: 
10458:     return render_template(
10459:         "workspace_detail.html",
10460:         workspace=workspace,
10461:         notes=notes,
10462:         tasks=tasks,
10463:         documents=documents,
10464:         threads=threads,
10465:         note_sections=get_workspace_note_sections()
10466:     )
10467: 
10468: 
10469: @app.route("/workspaces/<workspace_id>/edit", methods=["GET", "POST"])
10470: def workspace_edit(workspace_id):
10471:     workspace = get_workspace_by_id(workspace_id)
10472:     if not workspace:
10473:         return f"Workspace {workspace_id} not found", 404
10474: 
10475:     if request.method == "POST":
10476:         if not validate_csrf_token():
10477:             return render_template("workspace_form.html", mode="edit", workspace=workspace, error_message="Invalid or missing CSRF token.", sections=get_workspace_note_sections())
10478: 
10479:         payload = {
10480:             "title": request.form.get("title"),
10481:             "workspace_type": request.form.get("workspace_type"),
10482:             "trust_type_focus": request.form.get("trust_type_focus"),
10483:             "purpose": request.form.get("purpose"),
10484:             "owner": request.form.get("owner"),
10485:             "status": request.form.get("status") or "draft",
10486:         }
10487:         update_workspace(workspace_id, payload)
10488:         return redirect(url_for("workspace_detail", workspace_id=workspace_id))
10489: 
10490:     return render_template("workspace_form.html", mode="edit", workspace=workspace, sections=get_workspace_note_sections())
10491: 
10492: 
10493: @app.route("/workspaces/<workspace_id>/notes/new", methods=["GET", "POST"])
10494: def workspace_note_new(workspace_id):
```

### `app.py:10493`

- Scope markers: `none detected`

```python
10478: 
10479:         payload = {
10480:             "title": request.form.get("title"),
10481:             "workspace_type": request.form.get("workspace_type"),
10482:             "trust_type_focus": request.form.get("trust_type_focus"),
10483:             "purpose": request.form.get("purpose"),
10484:             "owner": request.form.get("owner"),
10485:             "status": request.form.get("status") or "draft",
10486:         }
10487:         update_workspace(workspace_id, payload)
10488:         return redirect(url_for("workspace_detail", workspace_id=workspace_id))
10489: 
10490:     return render_template("workspace_form.html", mode="edit", workspace=workspace, sections=get_workspace_note_sections())
10491: 
10492: 
10493: @app.route("/workspaces/<workspace_id>/notes/new", methods=["GET", "POST"])
10494: def workspace_note_new(workspace_id):
10495:     workspace = get_workspace_by_id(workspace_id)
10496:     if not workspace:
10497:         return f"Workspace {workspace_id} not found", 404
10498: 
10499:     if request.method == "POST":
10500:         if not validate_csrf_token():
10501:             return render_template("workspace_note_form.html", workspace=workspace, sections=get_workspace_note_sections(), error_message="Invalid or missing CSRF token.")
10502: 
10503:         note_id = (request.form.get("note_id") or "").strip()
10504:         section_name = (request.form.get("section_name") or "").strip()
10505:         content = (request.form.get("content") or "").strip()
10506: 
10507:         if not note_id or not section_name or not content:
10508:             return render_template("workspace_note_form.html", workspace=workspace, sections=get_workspace_note_sections(), error_message="Note ID, section, and content are required.")
10509: 
10510:         payload = {
10511:             "note_id": note_id,
10512:             "workspace_id": workspace_id,
10513:             "section_name": section_name,
10514:             "content": content,
10515:         }
10516:         create_workspace_note(payload)
10517:         return redirect(url_for("workspace_detail", workspace_id=workspace_id))
10518: 
```

### `app.py:10529`

- Scope markers: `none detected`

```python
10514:             "content": content,
10515:         }
10516:         create_workspace_note(payload)
10517:         return redirect(url_for("workspace_detail", workspace_id=workspace_id))
10518: 
10519:     return render_template("workspace_note_form.html", workspace=workspace, sections=get_workspace_note_sections())
10520: 
10521: @app.route("/discussions")
10522: def discussion_dashboard():
10523:     threads = get_all_discussion_threads()
10524:     return render_template("discussion_dashboard.html", threads=threads)
10525: 
10526: 
10527: @app.route("/discussions/new", methods=["GET", "POST"])
10528: def discussion_new():
10529:     workspaces = get_all_workspaces()
10530:     if request.method == "POST":
10531:         if not validate_csrf_token():
10532:             return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories(), error_message="Invalid or missing CSRF token.")
10533: 
10534:         thread_id = (request.form.get("thread_id") or "").strip()
10535:         title = (request.form.get("title") or "").strip()
10536:         if not thread_id or not title:
10537:             return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories(), error_message="Thread ID and Title are required.")
10538: 
10539:         payload = {
10540:             "thread_id": thread_id,
10541:             "workspace_id": request.form.get("workspace_id"),
10542:             "title": title,
10543:             "category": request.form.get("category"),
10544:             "related_trust_type": request.form.get("related_trust_type"),
10545:             "related_form": request.form.get("related_form"),
10546:             "created_by": session.get("username") or "unknown",
10547:             "status": request.form.get("status") or "open",
10548:             "owner_id": get_current_owner(),
10549:         }
10550:         create_discussion_thread(payload)
10551:         return redirect(url_for("discussion_thread", thread_id=thread_id))
10552: 
10553:     return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories())
10554: 
```

### `app.py:10532`

- Scope markers: `none detected`

```python
10517:         return redirect(url_for("workspace_detail", workspace_id=workspace_id))
10518: 
10519:     return render_template("workspace_note_form.html", workspace=workspace, sections=get_workspace_note_sections())
10520: 
10521: @app.route("/discussions")
10522: def discussion_dashboard():
10523:     threads = get_all_discussion_threads()
10524:     return render_template("discussion_dashboard.html", threads=threads)
10525: 
10526: 
10527: @app.route("/discussions/new", methods=["GET", "POST"])
10528: def discussion_new():
10529:     workspaces = get_all_workspaces()
10530:     if request.method == "POST":
10531:         if not validate_csrf_token():
10532:             return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories(), error_message="Invalid or missing CSRF token.")
10533: 
10534:         thread_id = (request.form.get("thread_id") or "").strip()
10535:         title = (request.form.get("title") or "").strip()
10536:         if not thread_id or not title:
10537:             return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories(), error_message="Thread ID and Title are required.")
10538: 
10539:         payload = {
10540:             "thread_id": thread_id,
10541:             "workspace_id": request.form.get("workspace_id"),
10542:             "title": title,
10543:             "category": request.form.get("category"),
10544:             "related_trust_type": request.form.get("related_trust_type"),
10545:             "related_form": request.form.get("related_form"),
10546:             "created_by": session.get("username") or "unknown",
10547:             "status": request.form.get("status") or "open",
10548:             "owner_id": get_current_owner(),
10549:         }
10550:         create_discussion_thread(payload)
10551:         return redirect(url_for("discussion_thread", thread_id=thread_id))
10552: 
10553:     return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories())
10554: 
10555: 
10556: @app.route("/discussions/<thread_id>")
10557: def discussion_thread(thread_id):
```

### `app.py:10537`

- Scope markers: `none detected`

```python
10522: def discussion_dashboard():
10523:     threads = get_all_discussion_threads()
10524:     return render_template("discussion_dashboard.html", threads=threads)
10525: 
10526: 
10527: @app.route("/discussions/new", methods=["GET", "POST"])
10528: def discussion_new():
10529:     workspaces = get_all_workspaces()
10530:     if request.method == "POST":
10531:         if not validate_csrf_token():
10532:             return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories(), error_message="Invalid or missing CSRF token.")
10533: 
10534:         thread_id = (request.form.get("thread_id") or "").strip()
10535:         title = (request.form.get("title") or "").strip()
10536:         if not thread_id or not title:
10537:             return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories(), error_message="Thread ID and Title are required.")
10538: 
10539:         payload = {
10540:             "thread_id": thread_id,
10541:             "workspace_id": request.form.get("workspace_id"),
10542:             "title": title,
10543:             "category": request.form.get("category"),
10544:             "related_trust_type": request.form.get("related_trust_type"),
10545:             "related_form": request.form.get("related_form"),
10546:             "created_by": session.get("username") or "unknown",
10547:             "status": request.form.get("status") or "open",
10548:             "owner_id": get_current_owner(),
10549:         }
10550:         create_discussion_thread(payload)
10551:         return redirect(url_for("discussion_thread", thread_id=thread_id))
10552: 
10553:     return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories())
10554: 
10555: 
10556: @app.route("/discussions/<thread_id>")
10557: def discussion_thread(thread_id):
10558:     thread = get_discussion_thread_by_id(thread_id)
10559:     if not thread:
10560:         return f"Discussion thread {thread_id} not found", 404
10561: 
10562:     if thread.get("owner_id") != get_current_owner():
```

### `app.py:10548`

- Scope markers: `none detected`

```python
10533: 
10534:         thread_id = (request.form.get("thread_id") or "").strip()
10535:         title = (request.form.get("title") or "").strip()
10536:         if not thread_id or not title:
10537:             return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories(), error_message="Thread ID and Title are required.")
10538: 
10539:         payload = {
10540:             "thread_id": thread_id,
10541:             "workspace_id": request.form.get("workspace_id"),
10542:             "title": title,
10543:             "category": request.form.get("category"),
10544:             "related_trust_type": request.form.get("related_trust_type"),
10545:             "related_form": request.form.get("related_form"),
10546:             "created_by": session.get("username") or "unknown",
10547:             "status": request.form.get("status") or "open",
10548:             "owner_id": get_current_owner(),
10549:         }
10550:         create_discussion_thread(payload)
10551:         return redirect(url_for("discussion_thread", thread_id=thread_id))
10552: 
10553:     return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories())
10554: 
10555: 
10556: @app.route("/discussions/<thread_id>")
10557: def discussion_thread(thread_id):
10558:     thread = get_discussion_thread_by_id(thread_id)
10559:     if not thread:
10560:         return f"Discussion thread {thread_id} not found", 404
10561: 
10562:     if thread.get("owner_id") != get_current_owner():
10563:         return render_template(
10564:             "access_denied.html",
10565:             reason="This discussion thread does not belong to the current owner context."
10566:         )
10567: 
10568:     messages = get_discussion_messages(thread_id)
10569:     workspace = get_workspace_by_id(thread.get("workspace_id")) if thread.get("workspace_id") else None
10570:     return render_template("discussion_thread.html", thread=thread, messages=messages, workspace=workspace)
10571: 
10572: 
10573: @app.route("/discussions/<thread_id>/reply", methods=["GET", "POST"])
```

### `app.py:10553`

- Scope markers: `none detected`

```python
10538: 
10539:         payload = {
10540:             "thread_id": thread_id,
10541:             "workspace_id": request.form.get("workspace_id"),
10542:             "title": title,
10543:             "category": request.form.get("category"),
10544:             "related_trust_type": request.form.get("related_trust_type"),
10545:             "related_form": request.form.get("related_form"),
10546:             "created_by": session.get("username") or "unknown",
10547:             "status": request.form.get("status") or "open",
10548:             "owner_id": get_current_owner(),
10549:         }
10550:         create_discussion_thread(payload)
10551:         return redirect(url_for("discussion_thread", thread_id=thread_id))
10552: 
10553:     return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories())
10554: 
10555: 
10556: @app.route("/discussions/<thread_id>")
10557: def discussion_thread(thread_id):
10558:     thread = get_discussion_thread_by_id(thread_id)
10559:     if not thread:
10560:         return f"Discussion thread {thread_id} not found", 404
10561: 
10562:     if thread.get("owner_id") != get_current_owner():
10563:         return render_template(
10564:             "access_denied.html",
10565:             reason="This discussion thread does not belong to the current owner context."
10566:         )
10567: 
10568:     messages = get_discussion_messages(thread_id)
10569:     workspace = get_workspace_by_id(thread.get("workspace_id")) if thread.get("workspace_id") else None
10570:     return render_template("discussion_thread.html", thread=thread, messages=messages, workspace=workspace)
10571: 
10572: 
10573: @app.route("/discussions/<thread_id>/reply", methods=["GET", "POST"])
10574: def discussion_reply(thread_id):
10575:     thread = get_discussion_thread_by_id(thread_id)
10576:     if not thread:
10577:         return f"Discussion thread {thread_id} not found", 404
10578: 
```

### `app.py:10562`

- Scope markers: `none detected`

```python
10547:             "status": request.form.get("status") or "open",
10548:             "owner_id": get_current_owner(),
10549:         }
10550:         create_discussion_thread(payload)
10551:         return redirect(url_for("discussion_thread", thread_id=thread_id))
10552: 
10553:     return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories())
10554: 
10555: 
10556: @app.route("/discussions/<thread_id>")
10557: def discussion_thread(thread_id):
10558:     thread = get_discussion_thread_by_id(thread_id)
10559:     if not thread:
10560:         return f"Discussion thread {thread_id} not found", 404
10561: 
10562:     if thread.get("owner_id") != get_current_owner():
10563:         return render_template(
10564:             "access_denied.html",
10565:             reason="This discussion thread does not belong to the current owner context."
10566:         )
10567: 
10568:     messages = get_discussion_messages(thread_id)
10569:     workspace = get_workspace_by_id(thread.get("workspace_id")) if thread.get("workspace_id") else None
10570:     return render_template("discussion_thread.html", thread=thread, messages=messages, workspace=workspace)
10571: 
10572: 
10573: @app.route("/discussions/<thread_id>/reply", methods=["GET", "POST"])
10574: def discussion_reply(thread_id):
10575:     thread = get_discussion_thread_by_id(thread_id)
10576:     if not thread:
10577:         return f"Discussion thread {thread_id} not found", 404
10578: 
10579:     if thread.get("owner_id") != get_current_owner():
10580:         return render_template(
10581:             "access_denied.html",
10582:             reason="This discussion thread does not belong to the current owner context."
10583:         )
10584: 
10585:     if request.method == "POST":
10586:         if not validate_csrf_token():
10587:             return render_template(
```

### `app.py:10579`

- Scope markers: `none detected`

```python
10564:             "access_denied.html",
10565:             reason="This discussion thread does not belong to the current owner context."
10566:         )
10567: 
10568:     messages = get_discussion_messages(thread_id)
10569:     workspace = get_workspace_by_id(thread.get("workspace_id")) if thread.get("workspace_id") else None
10570:     return render_template("discussion_thread.html", thread=thread, messages=messages, workspace=workspace)
10571: 
10572: 
10573: @app.route("/discussions/<thread_id>/reply", methods=["GET", "POST"])
10574: def discussion_reply(thread_id):
10575:     thread = get_discussion_thread_by_id(thread_id)
10576:     if not thread:
10577:         return f"Discussion thread {thread_id} not found", 404
10578: 
10579:     if thread.get("owner_id") != get_current_owner():
10580:         return render_template(
10581:             "access_denied.html",
10582:             reason="This discussion thread does not belong to the current owner context."
10583:         )
10584: 
10585:     if request.method == "POST":
10586:         if not validate_csrf_token():
10587:             return render_template(
10588:                 "discussion_reply_form.html",
10589:                 thread=thread,
10590:                 error_message="Invalid or missing CSRF token."
10591:             )
10592: 
10593:         message_id = get_next_discussion_message_id()
10594:         payload = {
10595:             "message_id": message_id,
10596:             "thread_id": thread_id,
10597:             "parent_message_id": request.form.get("parent_message_id"),
10598:             "author": session.get("username") or "unknown",
10599:             "body": request.form.get("body"),
10600:             "owner_id": get_current_owner(),
10601:         }
10602:         create_discussion_message(payload)
10603:         return redirect(url_for("discussion_thread", thread_id=thread_id))
10604: 
```

### `app.py:10600`

- Scope markers: `none detected`

```python
10585:     if request.method == "POST":
10586:         if not validate_csrf_token():
10587:             return render_template(
10588:                 "discussion_reply_form.html",
10589:                 thread=thread,
10590:                 error_message="Invalid or missing CSRF token."
10591:             )
10592: 
10593:         message_id = get_next_discussion_message_id()
10594:         payload = {
10595:             "message_id": message_id,
10596:             "thread_id": thread_id,
10597:             "parent_message_id": request.form.get("parent_message_id"),
10598:             "author": session.get("username") or "unknown",
10599:             "body": request.form.get("body"),
10600:             "owner_id": get_current_owner(),
10601:         }
10602:         create_discussion_message(payload)
10603:         return redirect(url_for("discussion_thread", thread_id=thread_id))
10604: 
10605:     return render_template("discussion_reply_form.html", thread=thread)
10606: 
10607: 
10608: @app.route("/workspaces/<workspace_id>/discussions")
10609: def workspace_discussions(workspace_id):
10610:     workspace = get_workspace_by_id(workspace_id)
10611:     if not workspace:
10612:         return f"Workspace {workspace_id} not found", 404
10613:     threads = get_discussion_threads_by_workspace(workspace_id)
10614:     return render_template("workspace_discussions.html", workspace=workspace, threads=threads)
10615: 
10616: 
10617: @app.route("/workspaces/<workspace_id>/discussions/new", methods=["GET", "POST"])
10618: def workspace_discussion_new(workspace_id):
10619:     workspace = get_workspace_by_id(workspace_id)
10620:     if not workspace:
10621:         return f"Workspace {workspace_id} not found", 404
10622: 
10623:     if request.method == "POST":
10624:         if not validate_csrf_token():
10625:             return render_template("discussion_form.html", mode="workspace_new", workspace=workspace, categories=get_discussion_categories(), error_message="Invalid or missing CSRF token.")
```

### `app.py:10608`

- Scope markers: `none detected`

```python
10593:         message_id = get_next_discussion_message_id()
10594:         payload = {
10595:             "message_id": message_id,
10596:             "thread_id": thread_id,
10597:             "parent_message_id": request.form.get("parent_message_id"),
10598:             "author": session.get("username") or "unknown",
10599:             "body": request.form.get("body"),
10600:             "owner_id": get_current_owner(),
10601:         }
10602:         create_discussion_message(payload)
10603:         return redirect(url_for("discussion_thread", thread_id=thread_id))
10604: 
10605:     return render_template("discussion_reply_form.html", thread=thread)
10606: 
10607: 
10608: @app.route("/workspaces/<workspace_id>/discussions")
10609: def workspace_discussions(workspace_id):
10610:     workspace = get_workspace_by_id(workspace_id)
10611:     if not workspace:
10612:         return f"Workspace {workspace_id} not found", 404
10613:     threads = get_discussion_threads_by_workspace(workspace_id)
10614:     return render_template("workspace_discussions.html", workspace=workspace, threads=threads)
10615: 
10616: 
10617: @app.route("/workspaces/<workspace_id>/discussions/new", methods=["GET", "POST"])
10618: def workspace_discussion_new(workspace_id):
10619:     workspace = get_workspace_by_id(workspace_id)
10620:     if not workspace:
10621:         return f"Workspace {workspace_id} not found", 404
10622: 
10623:     if request.method == "POST":
10624:         if not validate_csrf_token():
10625:             return render_template("discussion_form.html", mode="workspace_new", workspace=workspace, categories=get_discussion_categories(), error_message="Invalid or missing CSRF token.")
10626: 
10627:         thread_id = (request.form.get("thread_id") or "").strip()
10628:         title = (request.form.get("title") or "").strip()
10629:         if not thread_id or not title:
10630:             return render_template("discussion_form.html", mode="workspace_new", workspace=workspace, categories=get_discussion_categories(), error_message="Thread ID and Title are required.")
10631: 
10632:         payload = {
10633:             "thread_id": thread_id,
```

### `app.py:10617`

- Scope markers: `none detected`

```python
10602:         create_discussion_message(payload)
10603:         return redirect(url_for("discussion_thread", thread_id=thread_id))
10604: 
10605:     return render_template("discussion_reply_form.html", thread=thread)
10606: 
10607: 
10608: @app.route("/workspaces/<workspace_id>/discussions")
10609: def workspace_discussions(workspace_id):
10610:     workspace = get_workspace_by_id(workspace_id)
10611:     if not workspace:
10612:         return f"Workspace {workspace_id} not found", 404
10613:     threads = get_discussion_threads_by_workspace(workspace_id)
10614:     return render_template("workspace_discussions.html", workspace=workspace, threads=threads)
10615: 
10616: 
10617: @app.route("/workspaces/<workspace_id>/discussions/new", methods=["GET", "POST"])
10618: def workspace_discussion_new(workspace_id):
10619:     workspace = get_workspace_by_id(workspace_id)
10620:     if not workspace:
10621:         return f"Workspace {workspace_id} not found", 404
10622: 
10623:     if request.method == "POST":
10624:         if not validate_csrf_token():
10625:             return render_template("discussion_form.html", mode="workspace_new", workspace=workspace, categories=get_discussion_categories(), error_message="Invalid or missing CSRF token.")
10626: 
10627:         thread_id = (request.form.get("thread_id") or "").strip()
10628:         title = (request.form.get("title") or "").strip()
10629:         if not thread_id or not title:
10630:             return render_template("discussion_form.html", mode="workspace_new", workspace=workspace, categories=get_discussion_categories(), error_message="Thread ID and Title are required.")
10631: 
10632:         payload = {
10633:             "thread_id": thread_id,
10634:             "workspace_id": workspace_id,
10635:             "title": title,
10636:             "category": request.form.get("category"),
10637:             "related_trust_type": request.form.get("related_trust_type"),
10638:             "related_form": request.form.get("related_form"),
10639:             "created_by": session.get("username") or "unknown",
10640:             "status": request.form.get("status") or "open",
10641:             "owner_id": get_current_owner(),
10642:         }
```

### `app.py:10641`

- Scope markers: `none detected`

```python
10626: 
10627:         thread_id = (request.form.get("thread_id") or "").strip()
10628:         title = (request.form.get("title") or "").strip()
10629:         if not thread_id or not title:
10630:             return render_template("discussion_form.html", mode="workspace_new", workspace=workspace, categories=get_discussion_categories(), error_message="Thread ID and Title are required.")
10631: 
10632:         payload = {
10633:             "thread_id": thread_id,
10634:             "workspace_id": workspace_id,
10635:             "title": title,
10636:             "category": request.form.get("category"),
10637:             "related_trust_type": request.form.get("related_trust_type"),
10638:             "related_form": request.form.get("related_form"),
10639:             "created_by": session.get("username") or "unknown",
10640:             "status": request.form.get("status") or "open",
10641:             "owner_id": get_current_owner(),
10642:         }
10643:         create_discussion_thread(payload)
10644:         return redirect(url_for("discussion_thread", thread_id=thread_id))
10645: 
10646:     return render_template("discussion_form.html", mode="workspace_new", workspace=workspace, categories=get_discussion_categories())
10647: 
10648: @app.route("/decision")
10649: def decision_dashboard():
10650:     goals = [
10651:         "estate_planning",
10652:         "asset_protection",
10653:         "real_property_holding",
10654:         "insurance_planning",
10655:         "tax_planning",
10656:         "business_structure",
10657:     ]
10658:     asset_types = [
10659:         "general_assets",
10660:         "real_estate",
10661:         "insurance_policy",
10662:         "mixed_assets",
10663:         "business_assets",
10664:         "cash_equivalents",
10665:     ]
10666:     control_levels = [
```

### `app.py:10735`

- Scope markers: `none detected`

```python
10720:         "decision_result.html",
10721:         goal=goal,
10722:         asset_type=asset_type,
10723:         control_level=control_level,
10724:         matches=matches
10725:     )
10726: 
10727: @app.route("/execution")
10728: def execution_dashboard():
10729:     tasks = get_all_execution_tasks()
10730:     return render_template("execution_dashboard.html", tasks=tasks)
10731: 
10732: 
10733: @app.route("/execution/tasks/new", methods=["GET", "POST"])
10734: def execution_task_new():
10735:     workspaces = get_all_workspaces()
10736:     if request.method == "POST":
10737:         if not validate_csrf_token():
10738:             return render_template(
10739:                 "execution_task_form.html",
10740:                 mode="new",
10741:                 workspaces=workspaces,
10742:                 task_types=get_execution_task_types(),
10743:                 error_message="Invalid or missing CSRF token."
10744:             )
10745: 
10746:         task_id = (request.form.get("task_id") or "").strip()
10747:         title = (request.form.get("title") or "").strip()
10748:         if not task_id or not title:
10749:             return render_template(
10750:                 "execution_task_form.html",
10751:                 mode="new",
10752:                 workspaces=workspaces,
10753:                 task_types=get_execution_task_types(),
10754:                 error_message="Task ID and Title are required."
10755:             )
10756: 
10757:         payload = {
10758:             "task_id": task_id,
10759:             "workspace_id": request.form.get("workspace_id"),
10760:             "trust_id": request.form.get("trust_id"),
```

### `app.py:10741`

- Scope markers: `none detected`

```python
10726: 
10727: @app.route("/execution")
10728: def execution_dashboard():
10729:     tasks = get_all_execution_tasks()
10730:     return render_template("execution_dashboard.html", tasks=tasks)
10731: 
10732: 
10733: @app.route("/execution/tasks/new", methods=["GET", "POST"])
10734: def execution_task_new():
10735:     workspaces = get_all_workspaces()
10736:     if request.method == "POST":
10737:         if not validate_csrf_token():
10738:             return render_template(
10739:                 "execution_task_form.html",
10740:                 mode="new",
10741:                 workspaces=workspaces,
10742:                 task_types=get_execution_task_types(),
10743:                 error_message="Invalid or missing CSRF token."
10744:             )
10745: 
10746:         task_id = (request.form.get("task_id") or "").strip()
10747:         title = (request.form.get("title") or "").strip()
10748:         if not task_id or not title:
10749:             return render_template(
10750:                 "execution_task_form.html",
10751:                 mode="new",
10752:                 workspaces=workspaces,
10753:                 task_types=get_execution_task_types(),
10754:                 error_message="Task ID and Title are required."
10755:             )
10756: 
10757:         payload = {
10758:             "task_id": task_id,
10759:             "workspace_id": request.form.get("workspace_id"),
10760:             "trust_id": request.form.get("trust_id"),
10761:             "title": title,
10762:             "task_type": request.form.get("task_type"),
10763:             "description": request.form.get("description"),
10764:             "related_form": request.form.get("related_form"),
10765:             "related_report": request.form.get("related_report"),
10766:             "priority": request.form.get("priority") or "medium",
```

### `app.py:10752`

- Scope markers: `none detected`

```python
10737:         if not validate_csrf_token():
10738:             return render_template(
10739:                 "execution_task_form.html",
10740:                 mode="new",
10741:                 workspaces=workspaces,
10742:                 task_types=get_execution_task_types(),
10743:                 error_message="Invalid or missing CSRF token."
10744:             )
10745: 
10746:         task_id = (request.form.get("task_id") or "").strip()
10747:         title = (request.form.get("title") or "").strip()
10748:         if not task_id or not title:
10749:             return render_template(
10750:                 "execution_task_form.html",
10751:                 mode="new",
10752:                 workspaces=workspaces,
10753:                 task_types=get_execution_task_types(),
10754:                 error_message="Task ID and Title are required."
10755:             )
10756: 
10757:         payload = {
10758:             "task_id": task_id,
10759:             "workspace_id": request.form.get("workspace_id"),
10760:             "trust_id": request.form.get("trust_id"),
10761:             "title": title,
10762:             "task_type": request.form.get("task_type"),
10763:             "description": request.form.get("description"),
10764:             "related_form": request.form.get("related_form"),
10765:             "related_report": request.form.get("related_report"),
10766:             "priority": request.form.get("priority") or "medium",
10767:             "status": request.form.get("status") or "pending",
10768:             "due_date": request.form.get("due_date"),
10769:             "assigned_to": request.form.get("assigned_to") or session.get("username") or "unknown",
10770:         }
10771:         create_execution_task(payload)
10772:         return redirect(url_for("execution_task_detail", task_id=task_id))
10773: 
10774:     return render_template(
10775:         "execution_task_form.html",
10776:         mode="new",
10777:         workspaces=workspaces,
```

### `app.py:10777`

- Scope markers: `none detected`

```python
10762:             "task_type": request.form.get("task_type"),
10763:             "description": request.form.get("description"),
10764:             "related_form": request.form.get("related_form"),
10765:             "related_report": request.form.get("related_report"),
10766:             "priority": request.form.get("priority") or "medium",
10767:             "status": request.form.get("status") or "pending",
10768:             "due_date": request.form.get("due_date"),
10769:             "assigned_to": request.form.get("assigned_to") or session.get("username") or "unknown",
10770:         }
10771:         create_execution_task(payload)
10772:         return redirect(url_for("execution_task_detail", task_id=task_id))
10773: 
10774:     return render_template(
10775:         "execution_task_form.html",
10776:         mode="new",
10777:         workspaces=workspaces,
10778:         task_types=get_execution_task_types()
10779:     )
10780: 
10781: 
10782: @app.route("/execution/tasks/<task_id>")
10783: def execution_task_detail(task_id):
10784:     task = get_execution_task_by_id(task_id)
10785:     if not task:
10786:         return f"Execution task {task_id} not found", 404
10787: 
10788:     if task.get("owner_id") != get_current_owner():
10789:         return render_template(
10790:             "access_denied.html",
10791:             reason="This execution task does not belong to the current owner context."
10792:         )
10793: 
10794:     workspace = get_workspace_by_id(task.get("workspace_id")) if task.get("workspace_id") else None
10795:     return render_template("execution_task_detail.html", task=task, workspace=workspace)
10796: 
10797: 
10798: @app.route("/execution/tasks/<task_id>/status", methods=["POST"])
10799: def execution_task_status(task_id):
10800:     task = get_execution_task_by_id(task_id)
10801:     if not task:
10802:         return f"Execution task {task_id} not found", 404
```

### `app.py:10788`

- Scope markers: `none detected`

```python
10773: 
10774:     return render_template(
10775:         "execution_task_form.html",
10776:         mode="new",
10777:         workspaces=workspaces,
10778:         task_types=get_execution_task_types()
10779:     )
10780: 
10781: 
10782: @app.route("/execution/tasks/<task_id>")
10783: def execution_task_detail(task_id):
10784:     task = get_execution_task_by_id(task_id)
10785:     if not task:
10786:         return f"Execution task {task_id} not found", 404
10787: 
10788:     if task.get("owner_id") != get_current_owner():
10789:         return render_template(
10790:             "access_denied.html",
10791:             reason="This execution task does not belong to the current owner context."
10792:         )
10793: 
10794:     workspace = get_workspace_by_id(task.get("workspace_id")) if task.get("workspace_id") else None
10795:     return render_template("execution_task_detail.html", task=task, workspace=workspace)
10796: 
10797: 
10798: @app.route("/execution/tasks/<task_id>/status", methods=["POST"])
10799: def execution_task_status(task_id):
10800:     task = get_execution_task_by_id(task_id)
10801:     if not task:
10802:         return f"Execution task {task_id} not found", 404
10803: 
10804:     if task.get("owner_id") != get_current_owner():
10805:         return render_template(
10806:             "access_denied.html",
10807:             reason="This execution task does not belong to the current owner context."
10808:         )
10809: 
10810:     if not validate_csrf_token():
10811:         return redirect(url_for("execution_task_detail", task_id=task_id))
10812: 
10813:     new_status = (request.form.get("status") or "").strip()
```

### `app.py:10804`

- Scope markers: `none detected`

```python
10789:         return render_template(
10790:             "access_denied.html",
10791:             reason="This execution task does not belong to the current owner context."
10792:         )
10793: 
10794:     workspace = get_workspace_by_id(task.get("workspace_id")) if task.get("workspace_id") else None
10795:     return render_template("execution_task_detail.html", task=task, workspace=workspace)
10796: 
10797: 
10798: @app.route("/execution/tasks/<task_id>/status", methods=["POST"])
10799: def execution_task_status(task_id):
10800:     task = get_execution_task_by_id(task_id)
10801:     if not task:
10802:         return f"Execution task {task_id} not found", 404
10803: 
10804:     if task.get("owner_id") != get_current_owner():
10805:         return render_template(
10806:             "access_denied.html",
10807:             reason="This execution task does not belong to the current owner context."
10808:         )
10809: 
10810:     if not validate_csrf_token():
10811:         return redirect(url_for("execution_task_detail", task_id=task_id))
10812: 
10813:     new_status = (request.form.get("status") or "").strip()
10814:     if new_status in {"pending", "in_progress", "blocked", "completed"}:
10815:         update_execution_task_status(task_id, new_status)
10816: 
10817:     return redirect(url_for("execution_task_detail", task_id=task_id))
10818: 
10819: 
10820: @app.route("/workspaces/<workspace_id>/tasks")
10821: def workspace_tasks(workspace_id):
10822:     workspace = get_workspace_by_id(workspace_id)
10823:     if not workspace:
10824:         return f"Workspace {workspace_id} not found", 404
10825:     tasks = get_execution_tasks_by_workspace(workspace_id)
10826:     return render_template("workspace_tasks.html", workspace=workspace, tasks=tasks)
10827: 
10828: 
10829: @app.route("/workspaces/<workspace_id>/tasks/new", methods=["GET", "POST"])
```

### `app.py:10820`

- Scope markers: `none detected`

```python
10805:         return render_template(
10806:             "access_denied.html",
10807:             reason="This execution task does not belong to the current owner context."
10808:         )
10809: 
10810:     if not validate_csrf_token():
10811:         return redirect(url_for("execution_task_detail", task_id=task_id))
10812: 
10813:     new_status = (request.form.get("status") or "").strip()
10814:     if new_status in {"pending", "in_progress", "blocked", "completed"}:
10815:         update_execution_task_status(task_id, new_status)
10816: 
10817:     return redirect(url_for("execution_task_detail", task_id=task_id))
10818: 
10819: 
10820: @app.route("/workspaces/<workspace_id>/tasks")
10821: def workspace_tasks(workspace_id):
10822:     workspace = get_workspace_by_id(workspace_id)
10823:     if not workspace:
10824:         return f"Workspace {workspace_id} not found", 404
10825:     tasks = get_execution_tasks_by_workspace(workspace_id)
10826:     return render_template("workspace_tasks.html", workspace=workspace, tasks=tasks)
10827: 
10828: 
10829: @app.route("/workspaces/<workspace_id>/tasks/new", methods=["GET", "POST"])
10830: def workspace_task_new(workspace_id):
10831:     workspace = get_workspace_by_id(workspace_id)
10832:     if not workspace:
10833:         return f"Workspace {workspace_id} not found", 404
10834: 
10835:     if request.method == "POST":
10836:         if not validate_csrf_token():
10837:             return render_template(
10838:                 "execution_task_form.html",
10839:                 mode="workspace_new",
10840:                 workspace=workspace,
10841:                 task_types=get_execution_task_types(),
10842:                 error_message="Invalid or missing CSRF token."
10843:             )
10844: 
10845:         task_id = (request.form.get("task_id") or "").strip()
```

### `app.py:10829`

- Scope markers: `none detected`

```python
10814:     if new_status in {"pending", "in_progress", "blocked", "completed"}:
10815:         update_execution_task_status(task_id, new_status)
10816: 
10817:     return redirect(url_for("execution_task_detail", task_id=task_id))
10818: 
10819: 
10820: @app.route("/workspaces/<workspace_id>/tasks")
10821: def workspace_tasks(workspace_id):
10822:     workspace = get_workspace_by_id(workspace_id)
10823:     if not workspace:
10824:         return f"Workspace {workspace_id} not found", 404
10825:     tasks = get_execution_tasks_by_workspace(workspace_id)
10826:     return render_template("workspace_tasks.html", workspace=workspace, tasks=tasks)
10827: 
10828: 
10829: @app.route("/workspaces/<workspace_id>/tasks/new", methods=["GET", "POST"])
10830: def workspace_task_new(workspace_id):
10831:     workspace = get_workspace_by_id(workspace_id)
10832:     if not workspace:
10833:         return f"Workspace {workspace_id} not found", 404
10834: 
10835:     if request.method == "POST":
10836:         if not validate_csrf_token():
10837:             return render_template(
10838:                 "execution_task_form.html",
10839:                 mode="workspace_new",
10840:                 workspace=workspace,
10841:                 task_types=get_execution_task_types(),
10842:                 error_message="Invalid or missing CSRF token."
10843:             )
10844: 
10845:         task_id = (request.form.get("task_id") or "").strip()
10846:         title = (request.form.get("title") or "").strip()
10847:         if not task_id or not title:
10848:             return render_template(
10849:                 "execution_task_form.html",
10850:                 mode="workspace_new",
10851:                 workspace=workspace,
10852:                 task_types=get_execution_task_types(),
10853:                 error_message="Task ID and Title are required."
10854:             )
```

### `app.py:10890`

- Scope markers: `none detected`

```python
10875:         mode="workspace_new",
10876:         workspace=workspace,
10877:         task_types=get_execution_task_types()
10878:     )
10879: 
10880: @app.route("/documents")
10881: def document_dashboard():
10882:     templates = get_document_templates()
10883:     documents = get_generated_documents()
10884:     return render_template("document_dashboard.html", templates=templates, documents=documents)
10885: 
10886: 
10887: @app.route("/documents/generate", methods=["GET", "POST"])
10888: def document_generate():
10889:     templates = get_document_templates()
10890:     workspaces = get_all_workspaces()
10891: 
10892:     if request.method == "POST":
10893:         if not validate_csrf_token():
10894:             return render_template(
10895:                 "document_generate_form.html",
10896:                 templates=templates,
10897:                 workspaces=workspaces,
10898:                 error_message="Invalid or missing CSRF token."
10899:             )
10900: 
10901:         document_id = (request.form.get("document_id") or "").strip()
10902:         template_id = (request.form.get("template_id") or "").strip()
10903:         title = (request.form.get("title") or "").strip()
10904: 
10905:         if not document_id or not template_id or not title:
10906:             return render_template(
10907:                 "document_generate_form.html",
10908:                 templates=templates,
10909:                 workspaces=workspaces,
10910:                 error_message="Document ID, Template, and Title are required."
10911:             )
10912: 
10913:         template = get_document_template_by_id(template_id)
10914:         if not template:
10915:             return render_template(
```

### `app.py:10897`

- Scope markers: `none detected`

```python
10882:     templates = get_document_templates()
10883:     documents = get_generated_documents()
10884:     return render_template("document_dashboard.html", templates=templates, documents=documents)
10885: 
10886: 
10887: @app.route("/documents/generate", methods=["GET", "POST"])
10888: def document_generate():
10889:     templates = get_document_templates()
10890:     workspaces = get_all_workspaces()
10891: 
10892:     if request.method == "POST":
10893:         if not validate_csrf_token():
10894:             return render_template(
10895:                 "document_generate_form.html",
10896:                 templates=templates,
10897:                 workspaces=workspaces,
10898:                 error_message="Invalid or missing CSRF token."
10899:             )
10900: 
10901:         document_id = (request.form.get("document_id") or "").strip()
10902:         template_id = (request.form.get("template_id") or "").strip()
10903:         title = (request.form.get("title") or "").strip()
10904: 
10905:         if not document_id or not template_id or not title:
10906:             return render_template(
10907:                 "document_generate_form.html",
10908:                 templates=templates,
10909:                 workspaces=workspaces,
10910:                 error_message="Document ID, Template, and Title are required."
10911:             )
10912: 
10913:         template = get_document_template_by_id(template_id)
10914:         if not template:
10915:             return render_template(
10916:                 "document_generate_form.html",
10917:                 templates=templates,
10918:                 workspaces=workspaces,
10919:                 error_message="Selected template was not found."
10920:             )
10921: 
10922:         values = {
```

### `app.py:10909`

- Scope markers: `none detected`

```python
10894:             return render_template(
10895:                 "document_generate_form.html",
10896:                 templates=templates,
10897:                 workspaces=workspaces,
10898:                 error_message="Invalid or missing CSRF token."
10899:             )
10900: 
10901:         document_id = (request.form.get("document_id") or "").strip()
10902:         template_id = (request.form.get("template_id") or "").strip()
10903:         title = (request.form.get("title") or "").strip()
10904: 
10905:         if not document_id or not template_id or not title:
10906:             return render_template(
10907:                 "document_generate_form.html",
10908:                 templates=templates,
10909:                 workspaces=workspaces,
10910:                 error_message="Document ID, Template, and Title are required."
10911:             )
10912: 
10913:         template = get_document_template_by_id(template_id)
10914:         if not template:
10915:             return render_template(
10916:                 "document_generate_form.html",
10917:                 templates=templates,
10918:                 workspaces=workspaces,
10919:                 error_message="Selected template was not found."
10920:             )
10921: 
10922:         values = {
10923:             "title": request.form.get("title") or "",
10924:             "purpose": request.form.get("purpose") or "",
10925:             "trust_type_focus": request.form.get("trust_type_focus") or "",
10926:             "notes": request.form.get("notes") or "",
10927:             "trust_name": request.form.get("trust_name") or "",
10928:             "trustee_name": request.form.get("trustee_name") or "",
10929:             "authority_scope": request.form.get("authority_scope") or "",
10930:             "related_forms": request.form.get("related_forms") or "",
10931:             "related_reports": request.form.get("related_reports") or "",
10932:         }
10933:         content = render_document_template(template.get("template_body"), values)
10934: 
```

### `app.py:10918`

- Scope markers: `none detected`

```python
10903:         title = (request.form.get("title") or "").strip()
10904: 
10905:         if not document_id or not template_id or not title:
10906:             return render_template(
10907:                 "document_generate_form.html",
10908:                 templates=templates,
10909:                 workspaces=workspaces,
10910:                 error_message="Document ID, Template, and Title are required."
10911:             )
10912: 
10913:         template = get_document_template_by_id(template_id)
10914:         if not template:
10915:             return render_template(
10916:                 "document_generate_form.html",
10917:                 templates=templates,
10918:                 workspaces=workspaces,
10919:                 error_message="Selected template was not found."
10920:             )
10921: 
10922:         values = {
10923:             "title": request.form.get("title") or "",
10924:             "purpose": request.form.get("purpose") or "",
10925:             "trust_type_focus": request.form.get("trust_type_focus") or "",
10926:             "notes": request.form.get("notes") or "",
10927:             "trust_name": request.form.get("trust_name") or "",
10928:             "trustee_name": request.form.get("trustee_name") or "",
10929:             "authority_scope": request.form.get("authority_scope") or "",
10930:             "related_forms": request.form.get("related_forms") or "",
10931:             "related_reports": request.form.get("related_reports") or "",
10932:         }
10933:         content = render_document_template(template.get("template_body"), values)
10934: 
10935:         payload = {
10936:             "document_id": document_id,
10937:             "workspace_id": request.form.get("workspace_id"),
10938:             "trust_id": request.form.get("trust_id"),
10939:             "template_id": template_id,
10940:             "title": title,
10941:             "content": content,
10942:             "status": request.form.get("status") or "draft",
10943:             "created_by": session.get("username") or "unknown",
```

### `app.py:10944`

- Scope markers: `none detected`

```python
10929:             "authority_scope": request.form.get("authority_scope") or "",
10930:             "related_forms": request.form.get("related_forms") or "",
10931:             "related_reports": request.form.get("related_reports") or "",
10932:         }
10933:         content = render_document_template(template.get("template_body"), values)
10934: 
10935:         payload = {
10936:             "document_id": document_id,
10937:             "workspace_id": request.form.get("workspace_id"),
10938:             "trust_id": request.form.get("trust_id"),
10939:             "template_id": template_id,
10940:             "title": title,
10941:             "content": content,
10942:             "status": request.form.get("status") or "draft",
10943:             "created_by": session.get("username") or "unknown",
10944:             "owner_id": get_current_owner(),
10945:         }
10946:         create_generated_document(payload)
10947:         return redirect(url_for("document_detail", document_id=document_id))
10948: 
10949:     return render_template("document_generate_form.html", templates=templates, workspaces=workspaces)
10950: 
10951: 
10952: @app.route("/documents/<document_id>")
10953: def document_detail(document_id):
10954:     document = get_generated_document_by_id(document_id)
10955:     if not document:
10956:         return f"Generated document {document_id} not found", 404
10957: 
10958:     if document.get("owner_id") != get_current_owner():
10959:         return render_template(
10960:             "access_denied.html",
10961:             reason="This generated document does not belong to the current owner context."
10962:         )
10963: 
10964:     template = get_document_template_by_id(document.get("template_id")) if document.get("template_id") else None
10965:     workspace = get_workspace_by_id(document.get("workspace_id")) if document.get("workspace_id") else None
10966:     return render_template("document_detail.html", document=document, template=template, workspace=workspace)
10967: 
10968: 
10969: @app.route("/workspaces/<workspace_id>/documents")
```

### `app.py:10949`

- Scope markers: `none detected`

```python
10934: 
10935:         payload = {
10936:             "document_id": document_id,
10937:             "workspace_id": request.form.get("workspace_id"),
10938:             "trust_id": request.form.get("trust_id"),
10939:             "template_id": template_id,
10940:             "title": title,
10941:             "content": content,
10942:             "status": request.form.get("status") or "draft",
10943:             "created_by": session.get("username") or "unknown",
10944:             "owner_id": get_current_owner(),
10945:         }
10946:         create_generated_document(payload)
10947:         return redirect(url_for("document_detail", document_id=document_id))
10948: 
10949:     return render_template("document_generate_form.html", templates=templates, workspaces=workspaces)
10950: 
10951: 
10952: @app.route("/documents/<document_id>")
10953: def document_detail(document_id):
10954:     document = get_generated_document_by_id(document_id)
10955:     if not document:
10956:         return f"Generated document {document_id} not found", 404
10957: 
10958:     if document.get("owner_id") != get_current_owner():
10959:         return render_template(
10960:             "access_denied.html",
10961:             reason="This generated document does not belong to the current owner context."
10962:         )
10963: 
10964:     template = get_document_template_by_id(document.get("template_id")) if document.get("template_id") else None
10965:     workspace = get_workspace_by_id(document.get("workspace_id")) if document.get("workspace_id") else None
10966:     return render_template("document_detail.html", document=document, template=template, workspace=workspace)
10967: 
10968: 
10969: @app.route("/workspaces/<workspace_id>/documents")
10970: def workspace_documents(workspace_id):
10971:     workspace = get_workspace_by_id(workspace_id)
10972:     if not workspace:
10973:         return f"Workspace {workspace_id} not found", 404
10974:     documents = get_generated_documents_by_workspace(workspace_id)
```

### `app.py:10958`

- Scope markers: `none detected`

```python
10943:             "created_by": session.get("username") or "unknown",
10944:             "owner_id": get_current_owner(),
10945:         }
10946:         create_generated_document(payload)
10947:         return redirect(url_for("document_detail", document_id=document_id))
10948: 
10949:     return render_template("document_generate_form.html", templates=templates, workspaces=workspaces)
10950: 
10951: 
10952: @app.route("/documents/<document_id>")
10953: def document_detail(document_id):
10954:     document = get_generated_document_by_id(document_id)
10955:     if not document:
10956:         return f"Generated document {document_id} not found", 404
10957: 
10958:     if document.get("owner_id") != get_current_owner():
10959:         return render_template(
10960:             "access_denied.html",
10961:             reason="This generated document does not belong to the current owner context."
10962:         )
10963: 
10964:     template = get_document_template_by_id(document.get("template_id")) if document.get("template_id") else None
10965:     workspace = get_workspace_by_id(document.get("workspace_id")) if document.get("workspace_id") else None
10966:     return render_template("document_detail.html", document=document, template=template, workspace=workspace)
10967: 
10968: 
10969: @app.route("/workspaces/<workspace_id>/documents")
10970: def workspace_documents(workspace_id):
10971:     workspace = get_workspace_by_id(workspace_id)
10972:     if not workspace:
10973:         return f"Workspace {workspace_id} not found", 404
10974:     documents = get_generated_documents_by_workspace(workspace_id)
10975:     return render_template("workspace_documents.html", workspace=workspace, documents=documents)
10976: 
10977: 
10978: @app.route("/workspaces/<workspace_id>/documents/generate", methods=["GET", "POST"])
10979: def workspace_document_generate(workspace_id):
10980:     workspace = get_workspace_by_id(workspace_id)
10981:     if not workspace:
10982:         return f"Workspace {workspace_id} not found", 404
10983: 
```

### `app.py:10969`

- Scope markers: `none detected`

```python
10954:     document = get_generated_document_by_id(document_id)
10955:     if not document:
10956:         return f"Generated document {document_id} not found", 404
10957: 
10958:     if document.get("owner_id") != get_current_owner():
10959:         return render_template(
10960:             "access_denied.html",
10961:             reason="This generated document does not belong to the current owner context."
10962:         )
10963: 
10964:     template = get_document_template_by_id(document.get("template_id")) if document.get("template_id") else None
10965:     workspace = get_workspace_by_id(document.get("workspace_id")) if document.get("workspace_id") else None
10966:     return render_template("document_detail.html", document=document, template=template, workspace=workspace)
10967: 
10968: 
10969: @app.route("/workspaces/<workspace_id>/documents")
10970: def workspace_documents(workspace_id):
10971:     workspace = get_workspace_by_id(workspace_id)
10972:     if not workspace:
10973:         return f"Workspace {workspace_id} not found", 404
10974:     documents = get_generated_documents_by_workspace(workspace_id)
10975:     return render_template("workspace_documents.html", workspace=workspace, documents=documents)
10976: 
10977: 
10978: @app.route("/workspaces/<workspace_id>/documents/generate", methods=["GET", "POST"])
10979: def workspace_document_generate(workspace_id):
10980:     workspace = get_workspace_by_id(workspace_id)
10981:     if not workspace:
10982:         return f"Workspace {workspace_id} not found", 404
10983: 
10984:     templates = get_document_templates()
10985: 
10986:     if request.method == "POST":
10987:         if not validate_csrf_token():
10988:             return render_template(
10989:                 "document_generate_form.html",
10990:                 workspace=workspace,
10991:                 templates=templates,
10992:                 error_message="Invalid or missing CSRF token."
10993:             )
10994: 
```

### `app.py:10978`

- Scope markers: `none detected`

```python
10963: 
10964:     template = get_document_template_by_id(document.get("template_id")) if document.get("template_id") else None
10965:     workspace = get_workspace_by_id(document.get("workspace_id")) if document.get("workspace_id") else None
10966:     return render_template("document_detail.html", document=document, template=template, workspace=workspace)
10967: 
10968: 
10969: @app.route("/workspaces/<workspace_id>/documents")
10970: def workspace_documents(workspace_id):
10971:     workspace = get_workspace_by_id(workspace_id)
10972:     if not workspace:
10973:         return f"Workspace {workspace_id} not found", 404
10974:     documents = get_generated_documents_by_workspace(workspace_id)
10975:     return render_template("workspace_documents.html", workspace=workspace, documents=documents)
10976: 
10977: 
10978: @app.route("/workspaces/<workspace_id>/documents/generate", methods=["GET", "POST"])
10979: def workspace_document_generate(workspace_id):
10980:     workspace = get_workspace_by_id(workspace_id)
10981:     if not workspace:
10982:         return f"Workspace {workspace_id} not found", 404
10983: 
10984:     templates = get_document_templates()
10985: 
10986:     if request.method == "POST":
10987:         if not validate_csrf_token():
10988:             return render_template(
10989:                 "document_generate_form.html",
10990:                 workspace=workspace,
10991:                 templates=templates,
10992:                 error_message="Invalid or missing CSRF token."
10993:             )
10994: 
10995:         document_id = (request.form.get("document_id") or "").strip()
10996:         template_id = (request.form.get("template_id") or "").strip()
10997:         title = (request.form.get("title") or "").strip()
10998: 
10999:         if not document_id or not template_id or not title:
11000:             return render_template(
11001:                 "document_generate_form.html",
11002:                 workspace=workspace,
11003:                 templates=templates,
```

### `app.py:11038`

- Scope markers: `none detected`

```python
11023:             "authority_scope": request.form.get("authority_scope") or "",
11024:             "related_forms": request.form.get("related_forms") or "",
11025:             "related_reports": request.form.get("related_reports") or "",
11026:         }
11027:         content = render_document_template(template.get("template_body"), values)
11028: 
11029:         payload = {
11030:             "document_id": document_id,
11031:             "workspace_id": workspace_id,
11032:             "trust_id": request.form.get("trust_id"),
11033:             "template_id": template_id,
11034:             "title": title,
11035:             "content": content,
11036:             "status": request.form.get("status") or "draft",
11037:             "created_by": session.get("username") or "unknown",
11038:             "owner_id": get_current_owner(),
11039:         }
11040:         create_generated_document(payload)
11041:         return redirect(url_for("document_detail", document_id=document_id))
11042: 
11043:     return render_template("document_generate_form.html", workspace=workspace, templates=templates)
11044: 
11045: 
11046: # ============================================================
11047: # TRANSFER ENGINE V1
11048: # ============================================================
11049: 
11050: @app.route("/trust/<trust_id>/post-create-review")
11051: def trust_post_create_review(trust_id):
11052:     trust = get_trust_by_id(trust_id)
11053:     if not trust:
11054:         return f"Trust {trust_id} not found"
11055:     return redirect(url_for("trust_formation_preview_hub", trust_id=trust["trust_id"]))
11056: 
11057: 
11058: @app.route("/trust/<trust_id>/formation-preview-hub")
11059: def trust_formation_preview_hub(trust_id):
11060:     trust = get_trust_by_id(trust_id)
11061:     if not trust:
11062:         return f"Trust {trust_id} not found"
11063:     preview_context = build_trust_preview_context(trust)
```

### `app.py:14505`

- Scope markers: `firm_id`

```python
14490: 
14491:     from werkzeug.security import generate_password_hash
14492:     import sqlite3
14493: 
14494:     conn = sqlite3.connect(DB_PATH)
14495:     conn.row_factory = sqlite3.Row
14496:     cur = conn.cursor()
14497: 
14498:     cur.execute("""
14499:         CREATE TABLE IF NOT EXISTS app_users (
14500:             user_id TEXT PRIMARY KEY,
14501:             username TEXT UNIQUE,
14502:             password_hash TEXT,
14503:             role_name TEXT,
14504:             status TEXT,
14505:             owner_id TEXT,
14506:             firm_id TEXT
14507:         )
14508:     """)
14509: 
14510:     cur.execute("PRAGMA table_info(app_users)")
14511:     cols = [r["name"] for r in cur.fetchall()]
14512:     for col, col_type in [
14513:         ("owner_id", "TEXT"),
14514:         ("firm_id", "TEXT"),
14515:         ("role_name", "TEXT"),
14516:         ("status", "TEXT"),
14517:     ]:
14518:         if col not in cols:
14519:             cur.execute(f"ALTER TABLE app_users ADD COLUMN {col} {col_type}")
14520: 
14521:     cur.execute("SELECT user_id FROM app_users WHERE username = ?", (username,))
14522:     existing = cur.fetchone()
14523: 
14524:     password_hash = generate_password_hash(password)
14525: 
14526:     if existing:
14527:         cur.execute("""
14528:             UPDATE app_users
14529:             SET password_hash = ?,
14530:                 role_name = 'Admin',
```

### `app.py:14513`

- Scope markers: `firm_id`

```python
14498:     cur.execute("""
14499:         CREATE TABLE IF NOT EXISTS app_users (
14500:             user_id TEXT PRIMARY KEY,
14501:             username TEXT UNIQUE,
14502:             password_hash TEXT,
14503:             role_name TEXT,
14504:             status TEXT,
14505:             owner_id TEXT,
14506:             firm_id TEXT
14507:         )
14508:     """)
14509: 
14510:     cur.execute("PRAGMA table_info(app_users)")
14511:     cols = [r["name"] for r in cur.fetchall()]
14512:     for col, col_type in [
14513:         ("owner_id", "TEXT"),
14514:         ("firm_id", "TEXT"),
14515:         ("role_name", "TEXT"),
14516:         ("status", "TEXT"),
14517:     ]:
14518:         if col not in cols:
14519:             cur.execute(f"ALTER TABLE app_users ADD COLUMN {col} {col_type}")
14520: 
14521:     cur.execute("SELECT user_id FROM app_users WHERE username = ?", (username,))
14522:     existing = cur.fetchone()
14523: 
14524:     password_hash = generate_password_hash(password)
14525: 
14526:     if existing:
14527:         cur.execute("""
14528:             UPDATE app_users
14529:             SET password_hash = ?,
14530:                 role_name = 'Admin',
14531:                 status = 'active',
14532:                 owner_id = 'ADMIN_OWNER_001',
14533:                 firm_id = ?
14534:             WHERE username = ?
14535:         """, (password_hash, firm_id, username))
14536:         action = "updated"
14537:     else:
14538:         cur.execute("SELECT COUNT(*) AS count FROM app_users")
```

### `app.py:14532`

- Scope markers: `firm_id`

```python
14517:     ]:
14518:         if col not in cols:
14519:             cur.execute(f"ALTER TABLE app_users ADD COLUMN {col} {col_type}")
14520: 
14521:     cur.execute("SELECT user_id FROM app_users WHERE username = ?", (username,))
14522:     existing = cur.fetchone()
14523: 
14524:     password_hash = generate_password_hash(password)
14525: 
14526:     if existing:
14527:         cur.execute("""
14528:             UPDATE app_users
14529:             SET password_hash = ?,
14530:                 role_name = 'Admin',
14531:                 status = 'active',
14532:                 owner_id = 'ADMIN_OWNER_001',
14533:                 firm_id = ?
14534:             WHERE username = ?
14535:         """, (password_hash, firm_id, username))
14536:         action = "updated"
14537:     else:
14538:         cur.execute("SELECT COUNT(*) AS count FROM app_users")
14539:         count = cur.fetchone()["count"]
14540:         user_id = f"USER-{count + 1:03d}"
14541:         cur.execute("""
14542:             INSERT INTO app_users (
14543:                 user_id, username, password_hash, role_name, status, owner_id, firm_id
14544:             ) VALUES (?, ?, ?, 'Admin', 'active', 'ADMIN_OWNER_001', ?)
14545:         """, (user_id, username, password_hash, firm_id))
14546:         action = "created"
14547: 
14548:     conn.commit()
14549:     conn.close()
14550: 
14551:     return f"Hosted admin bootstrap {action}: {username} / {firm_id}. Disable ALLOW_HOSTED_ADMIN_BOOTSTRAP after login."
14552: 
14553: 
14554: 
14555: @app.route("/hosted-bootstrap-admin-once")
14556: def hosted_bootstrap_admin_once():
14557:     if os.getenv("ALLOW_HOSTED_ADMIN_BOOTSTRAP") != "1":
```

### `app.py:14543`

- Scope markers: `firm_id`

```python
14528:             UPDATE app_users
14529:             SET password_hash = ?,
14530:                 role_name = 'Admin',
14531:                 status = 'active',
14532:                 owner_id = 'ADMIN_OWNER_001',
14533:                 firm_id = ?
14534:             WHERE username = ?
14535:         """, (password_hash, firm_id, username))
14536:         action = "updated"
14537:     else:
14538:         cur.execute("SELECT COUNT(*) AS count FROM app_users")
14539:         count = cur.fetchone()["count"]
14540:         user_id = f"USER-{count + 1:03d}"
14541:         cur.execute("""
14542:             INSERT INTO app_users (
14543:                 user_id, username, password_hash, role_name, status, owner_id, firm_id
14544:             ) VALUES (?, ?, ?, 'Admin', 'active', 'ADMIN_OWNER_001', ?)
14545:         """, (user_id, username, password_hash, firm_id))
14546:         action = "created"
14547: 
14548:     conn.commit()
14549:     conn.close()
14550: 
14551:     return f"Hosted admin bootstrap {action}: {username} / {firm_id}. Disable ALLOW_HOSTED_ADMIN_BOOTSTRAP after login."
14552: 
14553: 
14554: 
14555: @app.route("/hosted-bootstrap-admin-once")
14556: def hosted_bootstrap_admin_once():
14557:     if os.getenv("ALLOW_HOSTED_ADMIN_BOOTSTRAP") != "1":
14558:         return render_template(
14559:             "access_denied.html",
14560:             reason="Hosted admin bootstrap is disabled."
14561:         )
14562: 
14563:     username = os.getenv("HOSTED_BOOTSTRAP_USERNAME", "admin123").strip()
14564:     password = os.getenv("HOSTED_BOOTSTRAP_PASSWORD", "").strip()
14565:     firm_id = os.getenv("HOSTED_BOOTSTRAP_FIRM_ID", "FIRM-002").strip()
14566: 
14567:     if not username or not password:
14568:         return render_template(
```

### `app.py:14544`

- Scope markers: `firm_id`

```python
14529:             SET password_hash = ?,
14530:                 role_name = 'Admin',
14531:                 status = 'active',
14532:                 owner_id = 'ADMIN_OWNER_001',
14533:                 firm_id = ?
14534:             WHERE username = ?
14535:         """, (password_hash, firm_id, username))
14536:         action = "updated"
14537:     else:
14538:         cur.execute("SELECT COUNT(*) AS count FROM app_users")
14539:         count = cur.fetchone()["count"]
14540:         user_id = f"USER-{count + 1:03d}"
14541:         cur.execute("""
14542:             INSERT INTO app_users (
14543:                 user_id, username, password_hash, role_name, status, owner_id, firm_id
14544:             ) VALUES (?, ?, ?, 'Admin', 'active', 'ADMIN_OWNER_001', ?)
14545:         """, (user_id, username, password_hash, firm_id))
14546:         action = "created"
14547: 
14548:     conn.commit()
14549:     conn.close()
14550: 
14551:     return f"Hosted admin bootstrap {action}: {username} / {firm_id}. Disable ALLOW_HOSTED_ADMIN_BOOTSTRAP after login."
14552: 
14553: 
14554: 
14555: @app.route("/hosted-bootstrap-admin-once")
14556: def hosted_bootstrap_admin_once():
14557:     if os.getenv("ALLOW_HOSTED_ADMIN_BOOTSTRAP") != "1":
14558:         return render_template(
14559:             "access_denied.html",
14560:             reason="Hosted admin bootstrap is disabled."
14561:         )
14562: 
14563:     username = os.getenv("HOSTED_BOOTSTRAP_USERNAME", "admin123").strip()
14564:     password = os.getenv("HOSTED_BOOTSTRAP_PASSWORD", "").strip()
14565:     firm_id = os.getenv("HOSTED_BOOTSTRAP_FIRM_ID", "FIRM-002").strip()
14566: 
14567:     if not username or not password:
14568:         return render_template(
14569:             "access_denied.html",
```

### `app.py:14587`

- Scope markers: `firm_id`

```python
14572: 
14573:     from werkzeug.security import generate_password_hash
14574:     import sqlite3
14575: 
14576:     conn = sqlite3.connect(DB_PATH)
14577:     conn.row_factory = sqlite3.Row
14578:     cur = conn.cursor()
14579: 
14580:     cur.execute("""
14581:         CREATE TABLE IF NOT EXISTS app_users (
14582:             user_id TEXT PRIMARY KEY,
14583:             username TEXT UNIQUE,
14584:             password_hash TEXT,
14585:             role_name TEXT,
14586:             status TEXT,
14587:             owner_id TEXT,
14588:             firm_id TEXT
14589:         )
14590:     """)
14591: 
14592:     cur.execute("PRAGMA table_info(app_users)")
14593:     cols = [r["name"] for r in cur.fetchall()]
14594:     for col, col_type in [
14595:         ("owner_id", "TEXT"),
14596:         ("firm_id", "TEXT"),
14597:         ("role_name", "TEXT"),
14598:         ("status", "TEXT"),
14599:     ]:
14600:         if col not in cols:
14601:             cur.execute(f"ALTER TABLE app_users ADD COLUMN {col} {col_type}")
14602: 
14603:     cur.execute("SELECT user_id FROM app_users WHERE username = ?", (username,))
14604:     existing = cur.fetchone()
14605: 
14606:     password_hash = generate_password_hash(password)
14607: 
14608:     if existing:
14609:         cur.execute("""
14610:             UPDATE app_users
14611:             SET password_hash = ?,
14612:                 role_name = 'Admin',
```

### `app.py:14595`

- Scope markers: `firm_id`

```python
14580:     cur.execute("""
14581:         CREATE TABLE IF NOT EXISTS app_users (
14582:             user_id TEXT PRIMARY KEY,
14583:             username TEXT UNIQUE,
14584:             password_hash TEXT,
14585:             role_name TEXT,
14586:             status TEXT,
14587:             owner_id TEXT,
14588:             firm_id TEXT
14589:         )
14590:     """)
14591: 
14592:     cur.execute("PRAGMA table_info(app_users)")
14593:     cols = [r["name"] for r in cur.fetchall()]
14594:     for col, col_type in [
14595:         ("owner_id", "TEXT"),
14596:         ("firm_id", "TEXT"),
14597:         ("role_name", "TEXT"),
14598:         ("status", "TEXT"),
14599:     ]:
14600:         if col not in cols:
14601:             cur.execute(f"ALTER TABLE app_users ADD COLUMN {col} {col_type}")
14602: 
14603:     cur.execute("SELECT user_id FROM app_users WHERE username = ?", (username,))
14604:     existing = cur.fetchone()
14605: 
14606:     password_hash = generate_password_hash(password)
14607: 
14608:     if existing:
14609:         cur.execute("""
14610:             UPDATE app_users
14611:             SET password_hash = ?,
14612:                 role_name = 'Admin',
14613:                 status = 'active',
14614:                 owner_id = 'ADMIN_OWNER_001',
14615:                 firm_id = ?
14616:             WHERE username = ?
14617:         """, (password_hash, firm_id, username))
14618:         action = "updated"
14619:     else:
14620:         cur.execute("SELECT COUNT(*) AS count FROM app_users")
```

### `app.py:14614`

- Scope markers: `firm_id`

```python
14599:     ]:
14600:         if col not in cols:
14601:             cur.execute(f"ALTER TABLE app_users ADD COLUMN {col} {col_type}")
14602: 
14603:     cur.execute("SELECT user_id FROM app_users WHERE username = ?", (username,))
14604:     existing = cur.fetchone()
14605: 
14606:     password_hash = generate_password_hash(password)
14607: 
14608:     if existing:
14609:         cur.execute("""
14610:             UPDATE app_users
14611:             SET password_hash = ?,
14612:                 role_name = 'Admin',
14613:                 status = 'active',
14614:                 owner_id = 'ADMIN_OWNER_001',
14615:                 firm_id = ?
14616:             WHERE username = ?
14617:         """, (password_hash, firm_id, username))
14618:         action = "updated"
14619:     else:
14620:         cur.execute("SELECT COUNT(*) AS count FROM app_users")
14621:         count = cur.fetchone()["count"]
14622:         user_id = f"USER-{count + 1:03d}"
14623:         cur.execute("""
14624:             INSERT INTO app_users (
14625:                 user_id, username, password_hash, role_name, status, owner_id, firm_id
14626:             ) VALUES (?, ?, ?, 'Admin', 'active', 'ADMIN_OWNER_001', ?)
14627:         """, (user_id, username, password_hash, firm_id))
14628:         action = "created"
14629: 
14630:     conn.commit()
14631:     conn.close()
14632: 
14633:     return f"Hosted admin bootstrap {action}: {username} / {firm_id}. Now log in, then disable ALLOW_HOSTED_ADMIN_BOOTSTRAP."
14634: 
14635: 
14636: 
14637: @app.route("/hosted-firm-scope-migration-once")
14638: def hosted_firm_scope_migration_once():
14639:     if os.getenv("ALLOW_HOSTED_FIRM_MIGRATION") != "1":
```

### `app.py:14625`

- Scope markers: `firm_id`

```python
14610:             UPDATE app_users
14611:             SET password_hash = ?,
14612:                 role_name = 'Admin',
14613:                 status = 'active',
14614:                 owner_id = 'ADMIN_OWNER_001',
14615:                 firm_id = ?
14616:             WHERE username = ?
14617:         """, (password_hash, firm_id, username))
14618:         action = "updated"
14619:     else:
14620:         cur.execute("SELECT COUNT(*) AS count FROM app_users")
14621:         count = cur.fetchone()["count"]
14622:         user_id = f"USER-{count + 1:03d}"
14623:         cur.execute("""
14624:             INSERT INTO app_users (
14625:                 user_id, username, password_hash, role_name, status, owner_id, firm_id
14626:             ) VALUES (?, ?, ?, 'Admin', 'active', 'ADMIN_OWNER_001', ?)
14627:         """, (user_id, username, password_hash, firm_id))
14628:         action = "created"
14629: 
14630:     conn.commit()
14631:     conn.close()
14632: 
14633:     return f"Hosted admin bootstrap {action}: {username} / {firm_id}. Now log in, then disable ALLOW_HOSTED_ADMIN_BOOTSTRAP."
14634: 
14635: 
14636: 
14637: @app.route("/hosted-firm-scope-migration-once")
14638: def hosted_firm_scope_migration_once():
14639:     if os.getenv("ALLOW_HOSTED_FIRM_MIGRATION") != "1":
14640:         return render_template(
14641:             "access_denied.html",
14642:             reason="Hosted firm-scope migration is disabled."
14643:         )
14644: 
14645:     import subprocess
14646:     import sys
14647: 
14648:     script_path = Path(__file__).resolve().parent / "scripts" / "migrate_hosted_firm_scope.py"
14649: 
14650:     if not script_path.exists():
```

### `app.py:14626`

- Scope markers: `firm_id`

```python
14611:             SET password_hash = ?,
14612:                 role_name = 'Admin',
14613:                 status = 'active',
14614:                 owner_id = 'ADMIN_OWNER_001',
14615:                 firm_id = ?
14616:             WHERE username = ?
14617:         """, (password_hash, firm_id, username))
14618:         action = "updated"
14619:     else:
14620:         cur.execute("SELECT COUNT(*) AS count FROM app_users")
14621:         count = cur.fetchone()["count"]
14622:         user_id = f"USER-{count + 1:03d}"
14623:         cur.execute("""
14624:             INSERT INTO app_users (
14625:                 user_id, username, password_hash, role_name, status, owner_id, firm_id
14626:             ) VALUES (?, ?, ?, 'Admin', 'active', 'ADMIN_OWNER_001', ?)
14627:         """, (user_id, username, password_hash, firm_id))
14628:         action = "created"
14629: 
14630:     conn.commit()
14631:     conn.close()
14632: 
14633:     return f"Hosted admin bootstrap {action}: {username} / {firm_id}. Now log in, then disable ALLOW_HOSTED_ADMIN_BOOTSTRAP."
14634: 
14635: 
14636: 
14637: @app.route("/hosted-firm-scope-migration-once")
14638: def hosted_firm_scope_migration_once():
14639:     if os.getenv("ALLOW_HOSTED_FIRM_MIGRATION") != "1":
14640:         return render_template(
14641:             "access_denied.html",
14642:             reason="Hosted firm-scope migration is disabled."
14643:         )
14644: 
14645:     import subprocess
14646:     import sys
14647: 
14648:     script_path = Path(__file__).resolve().parent / "scripts" / "migrate_hosted_firm_scope.py"
14649: 
14650:     if not script_path.exists():
14651:         return render_template(
```

### `app.py:14809`

- Scope markers: `firm_id`

```python
14794:         return "<pre>REPAIR FAILED: username, password, and firm_id are required.</pre>", 400
14795: 
14796:     conn = sqlite3.connect(DB_PATH)
14797:     conn.row_factory = sqlite3.Row
14798:     cur = conn.cursor()
14799: 
14800:     # 1. Ensure app_users exists and has required columns.
14801:     cur.execute("""
14802:         CREATE TABLE IF NOT EXISTS app_users (
14803:             user_id TEXT PRIMARY KEY,
14804:             username TEXT UNIQUE,
14805:             password_hash TEXT,
14806:             role_name TEXT,
14807:             status TEXT,
14808:             firm_id TEXT,
14809:             owner_id TEXT
14810:         )
14811:     """)
14812: 
14813:     cur.execute("PRAGMA table_info(app_users)")
14814:     user_cols = [r["name"] for r in cur.fetchall()]
14815:     for col, col_type in [
14816:         ("password_hash", "TEXT"),
14817:         ("role_name", "TEXT"),
14818:         ("status", "TEXT"),
14819:         ("firm_id", "TEXT"),
14820:         ("owner_id", "TEXT"),
14821:     ]:
14822:         if col not in user_cols:
14823:             cur.execute(f"ALTER TABLE app_users ADD COLUMN {col} {col_type}")
14824:             output.append(f"ADDED app_users.{col}")
14825: 
14826:     # 2. Create/update admin user.
14827:     password_hash = generate_password_hash(password)
14828: 
14829:     cur.execute("SELECT user_id FROM app_users WHERE TRIM(LOWER(username)) = TRIM(LOWER(?))", (username,))
14830:     existing = cur.fetchone()
14831: 
14832:     if existing:
14833:         cur.execute("""
14834:             UPDATE app_users
```

### `app.py:14820`

- Scope markers: `firm_id`

```python
14805:             password_hash TEXT,
14806:             role_name TEXT,
14807:             status TEXT,
14808:             firm_id TEXT,
14809:             owner_id TEXT
14810:         )
14811:     """)
14812: 
14813:     cur.execute("PRAGMA table_info(app_users)")
14814:     user_cols = [r["name"] for r in cur.fetchall()]
14815:     for col, col_type in [
14816:         ("password_hash", "TEXT"),
14817:         ("role_name", "TEXT"),
14818:         ("status", "TEXT"),
14819:         ("firm_id", "TEXT"),
14820:         ("owner_id", "TEXT"),
14821:     ]:
14822:         if col not in user_cols:
14823:             cur.execute(f"ALTER TABLE app_users ADD COLUMN {col} {col_type}")
14824:             output.append(f"ADDED app_users.{col}")
14825: 
14826:     # 2. Create/update admin user.
14827:     password_hash = generate_password_hash(password)
14828: 
14829:     cur.execute("SELECT user_id FROM app_users WHERE TRIM(LOWER(username)) = TRIM(LOWER(?))", (username,))
14830:     existing = cur.fetchone()
14831: 
14832:     if existing:
14833:         cur.execute("""
14834:             UPDATE app_users
14835:             SET username = ?,
14836:                 password_hash = ?,
14837:                 role_name = 'Admin',
14838:                 status = 'active',
14839:                 firm_id = ?,
14840:                 owner_id = 'ADMIN_OWNER_001'
14841:             WHERE user_id = ?
14842:         """, (username, password_hash, firm_id, existing["user_id"]))
14843:         output.append(f"USER_UPDATED={username}")
14844:     else:
14845:         cur.execute("SELECT COUNT(*) AS count FROM app_users")
```

### `app.py:14840`

- Scope markers: `firm_id`

```python
14825: 
14826:     # 2. Create/update admin user.
14827:     password_hash = generate_password_hash(password)
14828: 
14829:     cur.execute("SELECT user_id FROM app_users WHERE TRIM(LOWER(username)) = TRIM(LOWER(?))", (username,))
14830:     existing = cur.fetchone()
14831: 
14832:     if existing:
14833:         cur.execute("""
14834:             UPDATE app_users
14835:             SET username = ?,
14836:                 password_hash = ?,
14837:                 role_name = 'Admin',
14838:                 status = 'active',
14839:                 firm_id = ?,
14840:                 owner_id = 'ADMIN_OWNER_001'
14841:             WHERE user_id = ?
14842:         """, (username, password_hash, firm_id, existing["user_id"]))
14843:         output.append(f"USER_UPDATED={username}")
14844:     else:
14845:         cur.execute("SELECT COUNT(*) AS count FROM app_users")
14846:         count = cur.fetchone()["count"]
14847:         user_id = f"USER-{count + 1:03d}"
14848:         cur.execute("""
14849:             INSERT INTO app_users (
14850:                 user_id, username, password_hash, role_name, status, firm_id, owner_id
14851:             ) VALUES (?, ?, ?, 'Admin', 'active', ?, 'ADMIN_OWNER_001')
14852:         """, (user_id, username, password_hash, firm_id))
14853:         output.append(f"USER_CREATED={username}")
14854: 
14855:     conn.commit()
14856: 
14857:     # 3. Ensure role permission tables and grant default Admin permissions.
14858:     cur.execute("""
14859:         CREATE TABLE IF NOT EXISTS permissions (
14860:             permission_id TEXT PRIMARY KEY,
14861:             permission_name TEXT UNIQUE,
14862:             description TEXT
14863:         )
14864:     """)
14865: 
```

### `app.py:14850`

- Scope markers: `firm_id`

```python
14835:             SET username = ?,
14836:                 password_hash = ?,
14837:                 role_name = 'Admin',
14838:                 status = 'active',
14839:                 firm_id = ?,
14840:                 owner_id = 'ADMIN_OWNER_001'
14841:             WHERE user_id = ?
14842:         """, (username, password_hash, firm_id, existing["user_id"]))
14843:         output.append(f"USER_UPDATED={username}")
14844:     else:
14845:         cur.execute("SELECT COUNT(*) AS count FROM app_users")
14846:         count = cur.fetchone()["count"]
14847:         user_id = f"USER-{count + 1:03d}"
14848:         cur.execute("""
14849:             INSERT INTO app_users (
14850:                 user_id, username, password_hash, role_name, status, firm_id, owner_id
14851:             ) VALUES (?, ?, ?, 'Admin', 'active', ?, 'ADMIN_OWNER_001')
14852:         """, (user_id, username, password_hash, firm_id))
14853:         output.append(f"USER_CREATED={username}")
14854: 
14855:     conn.commit()
14856: 
14857:     # 3. Ensure role permission tables and grant default Admin permissions.
14858:     cur.execute("""
14859:         CREATE TABLE IF NOT EXISTS permissions (
14860:             permission_id TEXT PRIMARY KEY,
14861:             permission_name TEXT UNIQUE,
14862:             description TEXT
14863:         )
14864:     """)
14865: 
14866:     cur.execute("""
14867:         CREATE TABLE IF NOT EXISTS role_permissions (
14868:             id INTEGER PRIMARY KEY AUTOINCREMENT,
14869:             role_name TEXT,
14870:             permission_name TEXT,
14871:             UNIQUE(role_name, permission_name)
14872:         )
14873:     """)
14874: 
14875:     default_permissions = [
```

### `app.py:14851`

- Scope markers: `firm_id`

```python
14836:                 password_hash = ?,
14837:                 role_name = 'Admin',
14838:                 status = 'active',
14839:                 firm_id = ?,
14840:                 owner_id = 'ADMIN_OWNER_001'
14841:             WHERE user_id = ?
14842:         """, (username, password_hash, firm_id, existing["user_id"]))
14843:         output.append(f"USER_UPDATED={username}")
14844:     else:
14845:         cur.execute("SELECT COUNT(*) AS count FROM app_users")
14846:         count = cur.fetchone()["count"]
14847:         user_id = f"USER-{count + 1:03d}"
14848:         cur.execute("""
14849:             INSERT INTO app_users (
14850:                 user_id, username, password_hash, role_name, status, firm_id, owner_id
14851:             ) VALUES (?, ?, ?, 'Admin', 'active', ?, 'ADMIN_OWNER_001')
14852:         """, (user_id, username, password_hash, firm_id))
14853:         output.append(f"USER_CREATED={username}")
14854: 
14855:     conn.commit()
14856: 
14857:     # 3. Ensure role permission tables and grant default Admin permissions.
14858:     cur.execute("""
14859:         CREATE TABLE IF NOT EXISTS permissions (
14860:             permission_id TEXT PRIMARY KEY,
14861:             permission_name TEXT UNIQUE,
14862:             description TEXT
14863:         )
14864:     """)
14865: 
14866:     cur.execute("""
14867:         CREATE TABLE IF NOT EXISTS role_permissions (
14868:             id INTEGER PRIMARY KEY AUTOINCREMENT,
14869:             role_name TEXT,
14870:             permission_name TEXT,
14871:             UNIQUE(role_name, permission_name)
14872:         )
14873:     """)
14874: 
14875:     default_permissions = [
14876:         ("PERM-001", "view_dashboard", "View dashboards and core system pages"),
```

### `app.py:14929`

- Scope markers: `firm_id`

```python
14914:             VALUES ('Admin', ?)
14915:         """, (permission_name,))
14916: 
14917:     conn.commit()
14918:     output.append("ADMIN_PERMISSIONS_RESEEDED=True")
14919: 
14920:     # 4. Self-heal firm_id columns on common hosted tables.
14921:     firm_tables = [
14922:         "trusts",
14923:         "audit_log",
14924:         "transfers",
14925:         "trust_minutes",
14926:         "documents",
14927:         "generated_documents",
14928:         "media_records",
14929:         "workspaces",
14930:         "workspace_notes",
14931:         "execution_tasks",
14932:         "user_roles",
14933:         "fiduciaries",
14934:         "properties",
14935:         "accounts",
14936:         "beneficiaries",
14937:         "distributions",
14938:         "instruments",
14939:         "ledger_entries",
14940:     ]
14941: 
14942:     for table in firm_tables:
14943:         cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
14944:         if not cur.fetchone():
14945:             output.append(f"SKIP_MISSING_TABLE={table}")
14946:             continue
14947: 
14948:         cur.execute(f"PRAGMA table_info({table})")
14949:         cols = [r["name"] for r in cur.fetchall()]
14950:         if "firm_id" not in cols:
14951:             cur.execute(f"ALTER TABLE {table} ADD COLUMN firm_id TEXT")
14952:             output.append(f"ADDED_COLUMN={table}.firm_id")
14953: 
14954:         cur.execute(f"""
```

### `app.py:15992`

- Scope markers: `none detected`

```python
15977:             overall_stage="guided_drafting_workspace",
15978:             readiness_label="Draft Workspace Active",
15979:             next_recommended_action="Continue guided drafting workflow.",
15980:             next_route=f"/guided-draft/{draft_session_id}"
15981:         )
15982: 
15983:         flash("Guided draft workspace initialized.", "success")
15984: 
15985:     cur.execute("""
15986:         SELECT *
15987:         FROM guided_draft_workspace
15988:         WHERE draft_session_id = ?
15989:         ORDER BY created_at DESC
15990:     """, (draft_session_id,))
15991: 
15992:     workspaces = cur.fetchall()
15993: 
15994:     conn.close()
15995: 
15996:     return render_template(
15997:         "guided_draft_workspace.html",
15998:         draft_session=draft_session,
15999:         intake=intake,
16000:         asset_summary=asset_summary,
16001:         document_summary=document_summary,
16002:         workspaces=workspaces
16003:     )
16004: 
16005: 
16006: 
16007: 
16008: 
16009: @app.route("/draft-bind/<workspace_id>", methods=["GET", "POST"])
16010: @csrf.exempt
16011: def draft_variable_binding(workspace_id):
16012: 
16013:     if not session.get("user_id") and not session.get("username"):
16014:         return redirect(url_for("login"))
16015: 
16016:     import uuid
16017:     import sqlite3
```

### `app.py:16002`

- Scope markers: `none detected`

```python
15987:         FROM guided_draft_workspace
15988:         WHERE draft_session_id = ?
15989:         ORDER BY created_at DESC
15990:     """, (draft_session_id,))
15991: 
15992:     workspaces = cur.fetchall()
15993: 
15994:     conn.close()
15995: 
15996:     return render_template(
15997:         "guided_draft_workspace.html",
15998:         draft_session=draft_session,
15999:         intake=intake,
16000:         asset_summary=asset_summary,
16001:         document_summary=document_summary,
16002:         workspaces=workspaces
16003:     )
16004: 
16005: 
16006: 
16007: 
16008: 
16009: @app.route("/draft-bind/<workspace_id>", methods=["GET", "POST"])
16010: @csrf.exempt
16011: def draft_variable_binding(workspace_id):
16012: 
16013:     if not session.get("user_id") and not session.get("username"):
16014:         return redirect(url_for("login"))
16015: 
16016:     import uuid
16017:     import sqlite3
16018: 
16019:     from database.db import (
16020:         get_connection,
16021:         ensure_variable_binding_table,
16022:         upsert_intake_orchestration_state
16023:     )
16024: 
16025:     ensure_variable_binding_table()
16026: 
16027:     conn = get_connection()
```

### `database/db.py:384`

- Scope markers: `current_firm, firm_id, get_current_firm_id`

```python
369: 
370:     ledger_cols = [row["name"] for row in cur.execute("PRAGMA table_info(ledger_entries)").fetchall()]
371:     for col in [
372:         ("entry_category", "TEXT"),
373:         ("accounting_method", "TEXT"),
374:         ("recognition_date", "TEXT"),
375:         ("due_date", "TEXT"),
376:         ("paid_date", "TEXT"),
377:         ("chart_account", "TEXT"),
378:     ]:
379:         if col[0] not in ledger_cols:
380:             cur.execute(f"ALTER TABLE ledger_entries ADD COLUMN {col[0]} {col[1]}")
381: 
382:     for table_name in ["properties", "accounts", "documents", "ledger_entries", "trusts"]:
383:         cols = [row["name"] for row in cur.execute(f"PRAGMA table_info({table_name})").fetchall()]
384:         if "owner_id" not in cols:
385:             cur.execute(f"ALTER TABLE {table_name} ADD COLUMN owner_id TEXT")
386: 
387:     conn.commit()
388:     conn.close()
389: 
390: def get_next_firm_trust_number(firm_id):
391:     firm_id = firm_id or get_current_firm_id()
392:     conn = get_connection()
393:     cur = conn.cursor()
394: 
395:     # Hosted/legacy DB safety: ensure firm trust columns exist before MAX query.
396:     cur.execute("PRAGMA table_info(trusts)")
397:     trust_cols = [row["name"] for row in cur.fetchall()]
398:     for col_name, col_type in [
399:         ("firm_id", "TEXT"),
400:         ("firm_trust_number", "INTEGER"),
401:         ("firm_trust_code", "TEXT"),
402:         ("owner_id", "TEXT"),
403:     ]:
404:         if col_name not in trust_cols:
405:             cur.execute(f"ALTER TABLE trusts ADD COLUMN {col_name} {col_type}")
406:             trust_cols.append(col_name)
407: 
408:     cur.execute("""
409:         UPDATE trusts
```

### `database/db.py:385`

- Scope markers: `current_firm, firm_id, get_current_firm_id`

```python
370:     ledger_cols = [row["name"] for row in cur.execute("PRAGMA table_info(ledger_entries)").fetchall()]
371:     for col in [
372:         ("entry_category", "TEXT"),
373:         ("accounting_method", "TEXT"),
374:         ("recognition_date", "TEXT"),
375:         ("due_date", "TEXT"),
376:         ("paid_date", "TEXT"),
377:         ("chart_account", "TEXT"),
378:     ]:
379:         if col[0] not in ledger_cols:
380:             cur.execute(f"ALTER TABLE ledger_entries ADD COLUMN {col[0]} {col[1]}")
381: 
382:     for table_name in ["properties", "accounts", "documents", "ledger_entries", "trusts"]:
383:         cols = [row["name"] for row in cur.execute(f"PRAGMA table_info({table_name})").fetchall()]
384:         if "owner_id" not in cols:
385:             cur.execute(f"ALTER TABLE {table_name} ADD COLUMN owner_id TEXT")
386: 
387:     conn.commit()
388:     conn.close()
389: 
390: def get_next_firm_trust_number(firm_id):
391:     firm_id = firm_id or get_current_firm_id()
392:     conn = get_connection()
393:     cur = conn.cursor()
394: 
395:     # Hosted/legacy DB safety: ensure firm trust columns exist before MAX query.
396:     cur.execute("PRAGMA table_info(trusts)")
397:     trust_cols = [row["name"] for row in cur.fetchall()]
398:     for col_name, col_type in [
399:         ("firm_id", "TEXT"),
400:         ("firm_trust_number", "INTEGER"),
401:         ("firm_trust_code", "TEXT"),
402:         ("owner_id", "TEXT"),
403:     ]:
404:         if col_name not in trust_cols:
405:             cur.execute(f"ALTER TABLE trusts ADD COLUMN {col_name} {col_type}")
406:             trust_cols.append(col_name)
407: 
408:     cur.execute("""
409:         UPDATE trusts
410:         SET firm_id = ?
```

### `database/db.py:402`

- Scope markers: `current_firm, firm_id, get_current_firm_id`

```python
387:     conn.commit()
388:     conn.close()
389: 
390: def get_next_firm_trust_number(firm_id):
391:     firm_id = firm_id or get_current_firm_id()
392:     conn = get_connection()
393:     cur = conn.cursor()
394: 
395:     # Hosted/legacy DB safety: ensure firm trust columns exist before MAX query.
396:     cur.execute("PRAGMA table_info(trusts)")
397:     trust_cols = [row["name"] for row in cur.fetchall()]
398:     for col_name, col_type in [
399:         ("firm_id", "TEXT"),
400:         ("firm_trust_number", "INTEGER"),
401:         ("firm_trust_code", "TEXT"),
402:         ("owner_id", "TEXT"),
403:     ]:
404:         if col_name not in trust_cols:
405:             cur.execute(f"ALTER TABLE trusts ADD COLUMN {col_name} {col_type}")
406:             trust_cols.append(col_name)
407: 
408:     cur.execute("""
409:         UPDATE trusts
410:         SET firm_id = ?
411:         WHERE firm_id IS NULL OR TRIM(firm_id) = ''
412:     """, (firm_id,))
413:     conn.commit()
414: 
415:     cur.execute(
416:         "SELECT COALESCE(MAX(firm_trust_number), 0) AS max_num FROM trusts WHERE firm_id = ?",
417:         (firm_id,)
418:     )
419:     row = cur.fetchone()
420:     conn.close()
421:     return int(row["max_num"] or 0) + 1
422: 
423: def get_next_firm_trust_code(firm_id=None):
424:     number = get_next_firm_trust_number(firm_id)
425:     return f"TR-{number:03d}"
426: 
427: 
```

### `database/db.py:441`

- Scope markers: `current_firm, firm_id, get_current_firm_id`

```python
426: 
427: 
428: def get_next_trust_id():
429:     conn = get_connection()
430:     cur = conn.cursor()
431:     cur.execute("SELECT COUNT(*) AS count FROM trusts")
432:     count = cur.fetchone()["count"]
433:     conn.close()
434:     return f"TR-{count + 1:03d}"
435: 
436: def create_trust_record(trust_data):
437:     trust_data = dict(trust_data)
438:     trust_data.setdefault("firm_id", get_current_firm_id())
439:     trust_data.setdefault("firm_trust_number", get_next_firm_trust_number(trust_data.get("firm_id")))
440:     trust_data.setdefault("firm_trust_code", f"TR-{int(trust_data.get('firm_trust_number')):03d}")
441:     trust_data.setdefault("owner_id", get_current_owner() if "get_current_owner" in globals() else None)
442: 
443:     conn = get_connection()
444:     cur = conn.cursor()
445: 
446:     # Hosted/legacy DB safety: ensure required trust scope columns exist before insert.
447:     cur.execute("PRAGMA table_info(trusts)")
448:     trust_cols = [row["name"] for row in cur.fetchall()]
449:     for col_name, col_type in [
450:         ("firm_id", "TEXT"),
451:         ("firm_trust_number", "INTEGER"),
452:         ("firm_trust_code", "TEXT"),
453:         ("owner_id", "TEXT"),
454:     ]:
455:         if col_name not in trust_cols:
456:             cur.execute(f"ALTER TABLE trusts ADD COLUMN {col_name} {col_type}")
457: 
458:     cur.execute("""
459:         INSERT INTO trusts (
460:             trust_id, trust_name, short_name, jurisdiction, effective_date,
461:             trust_type, trust_purpose, accounting_method, workflow_mode,
462:             settlor_name, trustee_name, successor_trustee_name, beneficiary_name,
463:             record_visibility, workflow_mode_confirmed, ai_explanations,
464:             recommended_guidance, initial_corpus_description, property_mapping_timing,
465:             asset_categories, generate_schedule_recommendations, status,
466:             firm_id, firm_trust_number, firm_trust_code, owner_id
```

### `database/db.py:453`

- Scope markers: `current_firm, firm_id, get_current_firm_id`

```python
438:     trust_data.setdefault("firm_id", get_current_firm_id())
439:     trust_data.setdefault("firm_trust_number", get_next_firm_trust_number(trust_data.get("firm_id")))
440:     trust_data.setdefault("firm_trust_code", f"TR-{int(trust_data.get('firm_trust_number')):03d}")
441:     trust_data.setdefault("owner_id", get_current_owner() if "get_current_owner" in globals() else None)
442: 
443:     conn = get_connection()
444:     cur = conn.cursor()
445: 
446:     # Hosted/legacy DB safety: ensure required trust scope columns exist before insert.
447:     cur.execute("PRAGMA table_info(trusts)")
448:     trust_cols = [row["name"] for row in cur.fetchall()]
449:     for col_name, col_type in [
450:         ("firm_id", "TEXT"),
451:         ("firm_trust_number", "INTEGER"),
452:         ("firm_trust_code", "TEXT"),
453:         ("owner_id", "TEXT"),
454:     ]:
455:         if col_name not in trust_cols:
456:             cur.execute(f"ALTER TABLE trusts ADD COLUMN {col_name} {col_type}")
457: 
458:     cur.execute("""
459:         INSERT INTO trusts (
460:             trust_id, trust_name, short_name, jurisdiction, effective_date,
461:             trust_type, trust_purpose, accounting_method, workflow_mode,
462:             settlor_name, trustee_name, successor_trustee_name, beneficiary_name,
463:             record_visibility, workflow_mode_confirmed, ai_explanations,
464:             recommended_guidance, initial_corpus_description, property_mapping_timing,
465:             asset_categories, generate_schedule_recommendations, status,
466:             firm_id, firm_trust_number, firm_trust_code, owner_id
467:         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
468:     """, (
469:         trust_data["trust_id"], trust_data["trust_name"], trust_data["short_name"],
470:         trust_data["jurisdiction"], trust_data["effective_date"], trust_data["trust_type"],
471:         trust_data["trust_purpose"], trust_data["accounting_method"], trust_data["workflow_mode"],
472:         trust_data["settlor_name"], trust_data["trustee_name"], trust_data["successor_trustee_name"],
473:         trust_data["beneficiary_name"], trust_data["record_visibility"], trust_data["workflow_mode_confirmed"],
474:         trust_data["ai_explanations"], trust_data["recommended_guidance"], trust_data["initial_corpus_description"],
475:         trust_data["property_mapping_timing"], trust_data["asset_categories"],
476:         trust_data["generate_schedule_recommendations"], trust_data["status"],
477:         trust_data.get("firm_id"),
478:         trust_data.get("firm_trust_number"),
```

### `database/db.py:466`

- Scope markers: `current_firm, firm_id, get_current_firm_id`

```python
451:         ("firm_trust_number", "INTEGER"),
452:         ("firm_trust_code", "TEXT"),
453:         ("owner_id", "TEXT"),
454:     ]:
455:         if col_name not in trust_cols:
456:             cur.execute(f"ALTER TABLE trusts ADD COLUMN {col_name} {col_type}")
457: 
458:     cur.execute("""
459:         INSERT INTO trusts (
460:             trust_id, trust_name, short_name, jurisdiction, effective_date,
461:             trust_type, trust_purpose, accounting_method, workflow_mode,
462:             settlor_name, trustee_name, successor_trustee_name, beneficiary_name,
463:             record_visibility, workflow_mode_confirmed, ai_explanations,
464:             recommended_guidance, initial_corpus_description, property_mapping_timing,
465:             asset_categories, generate_schedule_recommendations, status,
466:             firm_id, firm_trust_number, firm_trust_code, owner_id
467:         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
468:     """, (
469:         trust_data["trust_id"], trust_data["trust_name"], trust_data["short_name"],
470:         trust_data["jurisdiction"], trust_data["effective_date"], trust_data["trust_type"],
471:         trust_data["trust_purpose"], trust_data["accounting_method"], trust_data["workflow_mode"],
472:         trust_data["settlor_name"], trust_data["trustee_name"], trust_data["successor_trustee_name"],
473:         trust_data["beneficiary_name"], trust_data["record_visibility"], trust_data["workflow_mode_confirmed"],
474:         trust_data["ai_explanations"], trust_data["recommended_guidance"], trust_data["initial_corpus_description"],
475:         trust_data["property_mapping_timing"], trust_data["asset_categories"],
476:         trust_data["generate_schedule_recommendations"], trust_data["status"],
477:         trust_data.get("firm_id"),
478:         trust_data.get("firm_trust_number"),
479:         trust_data.get("firm_trust_code"),
480:         trust_data.get("owner_id"),
481:     ))
482:     conn.commit()
483:     conn.close()
484: 
485: def ensure_table_firm_id_column(table_name, default_firm_id=None):
486:     """
487:     Hosted/legacy SQLite safety helper.
488:     Ensures a table has firm_id before firm-scoped queries run.
489:     """
490:     firm_id = default_firm_id or get_current_firm_id()
491:     conn = get_connection()
```

### `database/db.py:480`

- Scope markers: `current_firm, firm_id, get_current_firm_id`

```python
465:             asset_categories, generate_schedule_recommendations, status,
466:             firm_id, firm_trust_number, firm_trust_code, owner_id
467:         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
468:     """, (
469:         trust_data["trust_id"], trust_data["trust_name"], trust_data["short_name"],
470:         trust_data["jurisdiction"], trust_data["effective_date"], trust_data["trust_type"],
471:         trust_data["trust_purpose"], trust_data["accounting_method"], trust_data["workflow_mode"],
472:         trust_data["settlor_name"], trust_data["trustee_name"], trust_data["successor_trustee_name"],
473:         trust_data["beneficiary_name"], trust_data["record_visibility"], trust_data["workflow_mode_confirmed"],
474:         trust_data["ai_explanations"], trust_data["recommended_guidance"], trust_data["initial_corpus_description"],
475:         trust_data["property_mapping_timing"], trust_data["asset_categories"],
476:         trust_data["generate_schedule_recommendations"], trust_data["status"],
477:         trust_data.get("firm_id"),
478:         trust_data.get("firm_trust_number"),
479:         trust_data.get("firm_trust_code"),
480:         trust_data.get("owner_id"),
481:     ))
482:     conn.commit()
483:     conn.close()
484: 
485: def ensure_table_firm_id_column(table_name, default_firm_id=None):
486:     """
487:     Hosted/legacy SQLite safety helper.
488:     Ensures a table has firm_id before firm-scoped queries run.
489:     """
490:     firm_id = default_firm_id or get_current_firm_id()
491:     conn = get_connection()
492:     cur = conn.cursor()
493: 
494:     cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
495:     if not cur.fetchone():
496:         conn.close()
497:         return False
498: 
499:     cur.execute(f"PRAGMA table_info({table_name})")
500:     cols = [row["name"] for row in cur.fetchall()]
501: 
502:     if "firm_id" not in cols:
503:         cur.execute(f"ALTER TABLE {table_name} ADD COLUMN firm_id TEXT")
504:         cur.execute(f"""
505:             UPDATE {table_name}
```

### `database/db.py:749`

- Scope markers: `firm_id`

```python
734:     cur = conn.cursor()
735:     cur.execute(
736:         "SELECT * FROM documents WHERE trust_id = ? AND firm_id = ? ORDER BY document_id",
737:         (trust_id, firm_id)
738:     )
739:     rows = cur.fetchall()
740:     conn.close()
741:     return rows
742: 
743: def get_documents_by_property_id(property_id):
744:     """
745:     Return documents linked directly to a property/asset record.
746: 
747:     AC-1 alignment:
748:     The continuity evidence bridge links documents through documents.property_id.
749:     Do not restrict by legacy owner_id here, because older document rows and
750:     evidence uploads may not have owner_id populated consistently.
751:     """
752:     conn = get_connection()
753:     cur = conn.cursor()
754:     cur.execute(
755:         "SELECT * FROM documents WHERE property_id = ? ORDER BY document_id",
756:         (property_id,)
757:     )
758:     rows = cur.fetchall()
759:     conn.close()
760:     return rows
761: 
762: def get_next_entry_id():
763:     conn = get_connection()
764:     cur = conn.cursor()
765:     cur.execute("SELECT COUNT(*) AS count FROM ledger_entries")
766:     count = cur.fetchone()["count"]
767:     conn.close()
768:     return f"LD-{count + 1:03d}"
769: 
770: def create_ledger_entry(entry_data):
771:     conn = get_connection()
772:     cur = conn.cursor()
773:     cur.execute("""
774:         INSERT INTO ledger_entries (
```

### `database/db.py:750`

- Scope markers: `firm_id`

```python
735:     cur.execute(
736:         "SELECT * FROM documents WHERE trust_id = ? AND firm_id = ? ORDER BY document_id",
737:         (trust_id, firm_id)
738:     )
739:     rows = cur.fetchall()
740:     conn.close()
741:     return rows
742: 
743: def get_documents_by_property_id(property_id):
744:     """
745:     Return documents linked directly to a property/asset record.
746: 
747:     AC-1 alignment:
748:     The continuity evidence bridge links documents through documents.property_id.
749:     Do not restrict by legacy owner_id here, because older document rows and
750:     evidence uploads may not have owner_id populated consistently.
751:     """
752:     conn = get_connection()
753:     cur = conn.cursor()
754:     cur.execute(
755:         "SELECT * FROM documents WHERE property_id = ? ORDER BY document_id",
756:         (property_id,)
757:     )
758:     rows = cur.fetchall()
759:     conn.close()
760:     return rows
761: 
762: def get_next_entry_id():
763:     conn = get_connection()
764:     cur = conn.cursor()
765:     cur.execute("SELECT COUNT(*) AS count FROM ledger_entries")
766:     count = cur.fetchone()["count"]
767:     conn.close()
768:     return f"LD-{count + 1:03d}"
769: 
770: def create_ledger_entry(entry_data):
771:     conn = get_connection()
772:     cur = conn.cursor()
773:     cur.execute("""
774:         INSERT INTO ledger_entries (
775:             entry_id, trust_id, property_id, account_id,
```

### `database/db.py:793`

- Scope markers: `none detected`

```python
778:             due_date, paid_date, chart_account
779:         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
780:     """, (
781:         entry_data["entry_id"], entry_data["trust_id"], entry_data["property_id"], entry_data["account_id"],
782:         entry_data["entry_type"], entry_data["amount"], entry_data["entry_date"], entry_data["description"],
783:         entry_data.get("entry_category"), entry_data.get("accounting_method"), entry_data.get("recognition_date"),
784:         entry_data.get("due_date"), entry_data.get("paid_date"), entry_data.get("chart_account"),
785:     ))
786:     conn.commit()
787:     conn.close()
788: 
789: def get_ledger_by_trust(trust_id):
790:     conn = get_connection()
791:     cur = conn.cursor()
792:     cur.execute(
793:         "SELECT * FROM ledger_entries WHERE trust_id = ? AND owner_id = ? ORDER BY entry_id",
794:         (trust_id, "ADMIN_OWNER_001")
795:     )
796:     rows = cur.fetchall()
797:     conn.close()
798:     return rows
799: 
800: def get_ledger_by_property(property_id):
801:     conn = get_connection()
802:     cur = conn.cursor()
803:     cur.execute(
804:         "SELECT * FROM ledger_entries WHERE property_id = ? AND owner_id = ? ORDER BY entry_id",
805:         (property_id, "ADMIN_OWNER_001")
806:     )
807:     rows = cur.fetchall()
808:     conn.close()
809:     return rows
810: 
811: def seed_chart_of_accounts_for_trust(trust_id):
812:     defaults = [
813:         ("1000", "Cash", "asset", "debit"),
814:         ("1100", "Accounts Receivable", "asset", "debit"),
815:         ("1200", "Prepaid Expense", "asset", "debit"),
816:         ("2000", "Accounts Payable", "liability", "credit"),
817:         ("2100", "Deferred Revenue", "liability", "credit"),
818:         ("4000", "Trust Income", "income", "credit"),
```

### `database/db.py:794`

- Scope markers: `none detected`

```python
779:         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
780:     """, (
781:         entry_data["entry_id"], entry_data["trust_id"], entry_data["property_id"], entry_data["account_id"],
782:         entry_data["entry_type"], entry_data["amount"], entry_data["entry_date"], entry_data["description"],
783:         entry_data.get("entry_category"), entry_data.get("accounting_method"), entry_data.get("recognition_date"),
784:         entry_data.get("due_date"), entry_data.get("paid_date"), entry_data.get("chart_account"),
785:     ))
786:     conn.commit()
787:     conn.close()
788: 
789: def get_ledger_by_trust(trust_id):
790:     conn = get_connection()
791:     cur = conn.cursor()
792:     cur.execute(
793:         "SELECT * FROM ledger_entries WHERE trust_id = ? AND owner_id = ? ORDER BY entry_id",
794:         (trust_id, "ADMIN_OWNER_001")
795:     )
796:     rows = cur.fetchall()
797:     conn.close()
798:     return rows
799: 
800: def get_ledger_by_property(property_id):
801:     conn = get_connection()
802:     cur = conn.cursor()
803:     cur.execute(
804:         "SELECT * FROM ledger_entries WHERE property_id = ? AND owner_id = ? ORDER BY entry_id",
805:         (property_id, "ADMIN_OWNER_001")
806:     )
807:     rows = cur.fetchall()
808:     conn.close()
809:     return rows
810: 
811: def seed_chart_of_accounts_for_trust(trust_id):
812:     defaults = [
813:         ("1000", "Cash", "asset", "debit"),
814:         ("1100", "Accounts Receivable", "asset", "debit"),
815:         ("1200", "Prepaid Expense", "asset", "debit"),
816:         ("2000", "Accounts Payable", "liability", "credit"),
817:         ("2100", "Deferred Revenue", "liability", "credit"),
818:         ("4000", "Trust Income", "income", "credit"),
819:         ("5000", "Trust Expense", "expense", "debit"),
```

### `database/db.py:804`

- Scope markers: `none detected`

```python
789: def get_ledger_by_trust(trust_id):
790:     conn = get_connection()
791:     cur = conn.cursor()
792:     cur.execute(
793:         "SELECT * FROM ledger_entries WHERE trust_id = ? AND owner_id = ? ORDER BY entry_id",
794:         (trust_id, "ADMIN_OWNER_001")
795:     )
796:     rows = cur.fetchall()
797:     conn.close()
798:     return rows
799: 
800: def get_ledger_by_property(property_id):
801:     conn = get_connection()
802:     cur = conn.cursor()
803:     cur.execute(
804:         "SELECT * FROM ledger_entries WHERE property_id = ? AND owner_id = ? ORDER BY entry_id",
805:         (property_id, "ADMIN_OWNER_001")
806:     )
807:     rows = cur.fetchall()
808:     conn.close()
809:     return rows
810: 
811: def seed_chart_of_accounts_for_trust(trust_id):
812:     defaults = [
813:         ("1000", "Cash", "asset", "debit"),
814:         ("1100", "Accounts Receivable", "asset", "debit"),
815:         ("1200", "Prepaid Expense", "asset", "debit"),
816:         ("2000", "Accounts Payable", "liability", "credit"),
817:         ("2100", "Deferred Revenue", "liability", "credit"),
818:         ("4000", "Trust Income", "income", "credit"),
819:         ("5000", "Trust Expense", "expense", "debit"),
820:     ]
821:     conn = get_connection()
822:     cur = conn.cursor()
823:     for code, name, grp, normal in defaults:
824:         coa_id = f"{trust_id}-{code}"
825:         cur.execute("""
826:             INSERT OR IGNORE INTO chart_of_accounts (
827:                 coa_id, trust_id, account_code, account_name,
828:                 account_group, normal_balance, is_active
829:             ) VALUES (?, ?, ?, ?, ?, ?, ?)
```

### `database/db.py:805`

- Scope markers: `none detected`

```python
790:     conn = get_connection()
791:     cur = conn.cursor()
792:     cur.execute(
793:         "SELECT * FROM ledger_entries WHERE trust_id = ? AND owner_id = ? ORDER BY entry_id",
794:         (trust_id, "ADMIN_OWNER_001")
795:     )
796:     rows = cur.fetchall()
797:     conn.close()
798:     return rows
799: 
800: def get_ledger_by_property(property_id):
801:     conn = get_connection()
802:     cur = conn.cursor()
803:     cur.execute(
804:         "SELECT * FROM ledger_entries WHERE property_id = ? AND owner_id = ? ORDER BY entry_id",
805:         (property_id, "ADMIN_OWNER_001")
806:     )
807:     rows = cur.fetchall()
808:     conn.close()
809:     return rows
810: 
811: def seed_chart_of_accounts_for_trust(trust_id):
812:     defaults = [
813:         ("1000", "Cash", "asset", "debit"),
814:         ("1100", "Accounts Receivable", "asset", "debit"),
815:         ("1200", "Prepaid Expense", "asset", "debit"),
816:         ("2000", "Accounts Payable", "liability", "credit"),
817:         ("2100", "Deferred Revenue", "liability", "credit"),
818:         ("4000", "Trust Income", "income", "credit"),
819:         ("5000", "Trust Expense", "expense", "debit"),
820:     ]
821:     conn = get_connection()
822:     cur = conn.cursor()
823:     for code, name, grp, normal in defaults:
824:         coa_id = f"{trust_id}-{code}"
825:         cur.execute("""
826:             INSERT OR IGNORE INTO chart_of_accounts (
827:                 coa_id, trust_id, account_code, account_name,
828:                 account_group, normal_balance, is_active
829:             ) VALUES (?, ?, ?, ?, ?, ?, ?)
830:         """, (coa_id, trust_id, code, name, grp, normal, "yes"))
```

### `database/db.py:3870`

- Scope markers: `firm_id`

```python
3855:             generated_output_status TEXT DEFAULT 'not_generated',
3856: 
3857:             draft_notes TEXT,
3858: 
3859:             created_at TEXT DEFAULT CURRENT_TIMESTAMP,
3860:             updated_at TEXT DEFAULT CURRENT_TIMESTAMP
3861:         )
3862:     """)
3863: 
3864:     conn.commit()
3865:     conn.close()
3866: 
3867: def ensure_variable_binding_table():
3868:     """
3869:     Variable binding table.
3870:     Stores controlled draft variables extracted from guided draft workspaces.
3871:     """
3872:     conn = get_connection()
3873:     cur = conn.cursor()
3874: 
3875:     cur.execute("""
3876:         CREATE TABLE IF NOT EXISTS draft_variable_bindings (
3877:             id INTEGER PRIMARY KEY AUTOINCREMENT,
3878: 
3879:             binding_id TEXT UNIQUE,
3880:             workspace_id TEXT,
3881:             draft_session_id TEXT,
3882:             intake_id TEXT,
3883:             firm_id TEXT DEFAULT 'FIRM-001',
3884: 
3885:             document_type TEXT,
3886: 
3887:             variable_key TEXT,
3888:             variable_value TEXT,
3889:             variable_source TEXT,
3890: 
3891:             created_at TEXT DEFAULT CURRENT_TIMESTAMP,
3892:             updated_at TEXT DEFAULT CURRENT_TIMESTAMP
3893:         )
3894:     """)
3895: 
```

### `database/db.py:3902`

- Scope markers: `firm_id`

```python
3887:             variable_key TEXT,
3888:             variable_value TEXT,
3889:             variable_source TEXT,
3890: 
3891:             created_at TEXT DEFAULT CURRENT_TIMESTAMP,
3892:             updated_at TEXT DEFAULT CURRENT_TIMESTAMP
3893:         )
3894:     """)
3895: 
3896:     conn.commit()
3897:     conn.close()
3898: 
3899: def ensure_variable_binding_table():
3900:     """
3901:     Variable binding table.
3902:     Stores controlled draft variables extracted from guided draft workspaces.
3903:     """
3904:     conn = get_connection()
3905:     cur = conn.cursor()
3906: 
3907:     cur.execute("""
3908:         CREATE TABLE IF NOT EXISTS draft_variable_bindings (
3909:             id INTEGER PRIMARY KEY AUTOINCREMENT,
3910: 
3911:             binding_id TEXT UNIQUE,
3912:             workspace_id TEXT,
3913:             draft_session_id TEXT,
3914:             intake_id TEXT,
3915:             firm_id TEXT DEFAULT 'FIRM-001',
3916: 
3917:             document_type TEXT,
3918: 
3919:             variable_key TEXT,
3920:             variable_value TEXT,
3921:             variable_source TEXT,
3922: 
3923:             created_at TEXT DEFAULT CURRENT_TIMESTAMP,
3924:             updated_at TEXT DEFAULT CURRENT_TIMESTAMP
3925:         )
3926:     """)
3927: 
```

### `database/db.py:4571`

- Scope markers: `firm_id`

```python
4556:     ensure_identity_intake_table()
4557:     ensure_intake_orchestration_table()
4558: 
4559:     conn = get_connection()
4560:     conn.row_factory = sqlite3.Row
4561:     cur = conn.cursor()
4562: 
4563:     ledger = {
4564:         "intake_id": intake_id,
4565:         "firm_id": firm_id,
4566:         "identity": None,
4567:         "orchestration": None,
4568:         "assets": [],
4569:         "documents": [],
4570:         "draft_sessions": [],
4571:         "workspaces": [],
4572:         "bindings": [],
4573:         "previews": [],
4574:         "section_reviews": [],
4575:         "export_prep": [],
4576:         "docx_exports": [],
4577:         "docx_verifications": [],
4578:         "pdf_exports": [],
4579:         "pdf_execution_approvals": [],
4580:         "execution_packets": [],
4581:         "execution_events": [],
4582:         "final_archives": [],
4583:         "latest_ids": {},
4584:         "missing_gates": [],
4585:         "current_stage": "unknown",
4586:         "archive_complete": False,
4587:     }
4588: 
4589:     cur.execute("""
4590:         SELECT *
4591:         FROM identity_intake
4592:         WHERE intake_id = ? AND firm_id = ?
4593:     """, (intake_id, firm_id))
4594:     ledger["identity"] = cur.fetchone()
4595: 
4596:     cur.execute("""
```

### `database/db.py:4607`

- Scope markers: `firm_id`

```python
4592:         WHERE intake_id = ? AND firm_id = ?
4593:     """, (intake_id, firm_id))
4594:     ledger["identity"] = cur.fetchone()
4595: 
4596:     cur.execute("""
4597:         SELECT *
4598:         FROM intake_orchestration
4599:         WHERE intake_id = ? AND firm_id = ?
4600:     """, (intake_id, firm_id))
4601:     ledger["orchestration"] = cur.fetchone()
4602: 
4603:     table_queries = {
4604:         "assets": ("asset_intake", "created_at"),
4605:         "documents": ("document_intake", "created_at"),
4606:         "draft_sessions": ("draft_sessions", "created_at"),
4607:         "workspaces": ("guided_draft_workspace", "created_at"),
4608:         "bindings": ("draft_variable_bindings", "created_at"),
4609:         "previews": ("dynamic_draft_previews", "created_at"),
4610:         "section_reviews": ("section_review_gate", "created_at"),
4611:         "export_prep": ("controlled_export_prep", "created_at"),
4612:         "docx_exports": ("controlled_docx_exports", "created_at"),
4613:         "docx_verifications": ("docx_verification_gate", "created_at"),
4614:         "pdf_exports": ("controlled_pdf_exports", "created_at"),
4615:         "pdf_execution_approvals": ("pdf_execution_approval_gate", "created_at"),
4616:         "execution_packets": ("execution_packet_prep", "created_at"),
4617:         "execution_events": ("execution_event_log", "created_at"),
4618:         "final_archives": ("final_record_archive", "created_at"),
4619:     }
4620: 
4621:     for key, (table, order_col) in table_queries.items():
4622:         try:
4623:             cur.execute(f"""
4624:                 SELECT *
4625:                 FROM {table}
4626:                 WHERE intake_id = ? AND firm_id = ?
4627:                 ORDER BY {order_col} DESC
4628:             """, (intake_id, firm_id))
4629:             ledger[key] = cur.fetchall()
4630:         except Exception:
4631:             ledger[key] = []
4632: 
```

### `database/db.py:4642`

- Scope markers: `firm_id`

```python
4627:                 ORDER BY {order_col} DESC
4628:             """, (intake_id, firm_id))
4629:             ledger[key] = cur.fetchall()
4630:         except Exception:
4631:             ledger[key] = []
4632: 
4633:     def latest(list_key, id_key):
4634:         rows = ledger.get(list_key) or []
4635:         if rows:
4636:             return rows[0][id_key]
4637:         return None
4638: 
4639:     ledger["latest_ids"] = {
4640:         "intake_id": intake_id,
4641:         "draft_session_id": latest("draft_sessions", "draft_session_id"),
4642:         "workspace_id": latest("workspaces", "workspace_id"),
4643:         "preview_id": latest("previews", "preview_id"),
4644:         "section_review_id": latest("section_reviews", "section_review_id"),
4645:         "export_prep_id": latest("export_prep", "export_prep_id"),
4646:         "docx_export_id": latest("docx_exports", "export_id"),
4647:         "docx_verification_id": latest("docx_verifications", "verification_id"),
4648:         "pdf_export_id": latest("pdf_exports", "pdf_export_id"),
4649:         "execution_approval_id": latest("pdf_execution_approvals", "approval_id"),
4650:         "packet_id": latest("execution_packets", "packet_id"),
4651:         "event_id": latest("execution_events", "event_id"),
4652:         "final_record_id": latest("final_archives", "final_record_id"),
4653:     }
4654: 
4655:     required_steps = [
4656:         ("identity", ledger["identity"]),
4657:         ("asset intake", ledger["assets"]),
4658:         ("document intake", ledger["documents"]),
4659:         ("draft session", ledger["draft_sessions"]),
4660:         ("guided workspace", ledger["workspaces"]),
4661:         ("variable bindings", ledger["bindings"]),
4662:         ("draft preview", ledger["previews"]),
4663:         ("section review", ledger["section_reviews"]),
4664:         ("export prep", ledger["export_prep"]),
4665:         ("DOCX export", ledger["docx_exports"]),
4666:         ("DOCX verification", ledger["docx_verifications"]),
4667:         ("PDF export", ledger["pdf_exports"]),
```

### `database/db.py:4660`

- Scope markers: `none detected`

```python
4645:         "export_prep_id": latest("export_prep", "export_prep_id"),
4646:         "docx_export_id": latest("docx_exports", "export_id"),
4647:         "docx_verification_id": latest("docx_verifications", "verification_id"),
4648:         "pdf_export_id": latest("pdf_exports", "pdf_export_id"),
4649:         "execution_approval_id": latest("pdf_execution_approvals", "approval_id"),
4650:         "packet_id": latest("execution_packets", "packet_id"),
4651:         "event_id": latest("execution_events", "event_id"),
4652:         "final_record_id": latest("final_archives", "final_record_id"),
4653:     }
4654: 
4655:     required_steps = [
4656:         ("identity", ledger["identity"]),
4657:         ("asset intake", ledger["assets"]),
4658:         ("document intake", ledger["documents"]),
4659:         ("draft session", ledger["draft_sessions"]),
4660:         ("guided workspace", ledger["workspaces"]),
4661:         ("variable bindings", ledger["bindings"]),
4662:         ("draft preview", ledger["previews"]),
4663:         ("section review", ledger["section_reviews"]),
4664:         ("export prep", ledger["export_prep"]),
4665:         ("DOCX export", ledger["docx_exports"]),
4666:         ("DOCX verification", ledger["docx_verifications"]),
4667:         ("PDF export", ledger["pdf_exports"]),
4668:         ("PDF execution approval", ledger["pdf_execution_approvals"]),
4669:         ("execution packet", ledger["execution_packets"]),
4670:         ("execution event", ledger["execution_events"]),
4671:         ("final archive", ledger["final_archives"]),
4672:     ]
4673: 
4674:     for label, value in required_steps:
4675:         if not value:
4676:             ledger["missing_gates"].append(label)
4677: 
4678:     if ledger["final_archives"]:
4679:         ledger["current_stage"] = "final_record_archive"
4680:         ledger["archive_complete"] = True
4681:     elif ledger["execution_events"]:
4682:         ledger["current_stage"] = "execution_event_log"
4683:     elif ledger["execution_packets"]:
4684:         ledger["current_stage"] = "execution_packet_preparation"
4685:     elif ledger["pdf_execution_approvals"]:
```

### `database/db.py:4701`

- Scope markers: `none detected`

```python
4686:         ledger["current_stage"] = "pdf_execution_approval"
4687:     elif ledger["pdf_exports"]:
4688:         ledger["current_stage"] = "controlled_pdf_conversion"
4689:     elif ledger["docx_verifications"]:
4690:         ledger["current_stage"] = "docx_verification"
4691:     elif ledger["docx_exports"]:
4692:         ledger["current_stage"] = "controlled_docx_export"
4693:     elif ledger["export_prep"]:
4694:         ledger["current_stage"] = "controlled_export_preparation"
4695:     elif ledger["section_reviews"]:
4696:         ledger["current_stage"] = "section_review"
4697:     elif ledger["previews"]:
4698:         ledger["current_stage"] = "dynamic_draft_preview"
4699:     elif ledger["bindings"]:
4700:         ledger["current_stage"] = "variable_binding"
4701:     elif ledger["workspaces"]:
4702:         ledger["current_stage"] = "guided_draft_workspace"
4703:     elif ledger["draft_sessions"]:
4704:         ledger["current_stage"] = "draft_session"
4705:     elif ledger["documents"]:
4706:         ledger["current_stage"] = "document_intake"
4707:     elif ledger["assets"]:
4708:         ledger["current_stage"] = "asset_intake"
4709:     elif ledger["identity"]:
4710:         ledger["current_stage"] = "identity_intake"
4711: 
4712:     conn.close()
4713:     return ledger
4714: 
4715: def ensure_draft_variable_binding_table():
4716:     """
4717:     Ensure table exists for guided draft variable bindings.
4718:     Used by INT lifecycle variable binding gate.
4719:     """
4720:     conn = get_connection()
4721:     cur = conn.cursor()
4722: 
4723:     cur.execute("""
4724:         CREATE TABLE IF NOT EXISTS draft_variable_binding (
4725:             id INTEGER PRIMARY KEY AUTOINCREMENT,
4726: 
```

### `scripts/migrate_hosted_firm_scope.py:16`

- Scope markers: `none detected`

```python
1: import sqlite3
2: from pathlib import Path
3: import os
4: 
5: DB_PATH = Path(os.getenv("DB_PATH", "trustee_app.db")).resolve()
6: 
7: TABLES_WITH_FIRM_ID = [
8:     "trusts",
9:     "app_users",
10:     "audit_log",
11:     "transfers",
12:     "trust_minutes",
13:     "documents",
14:     "generated_documents",
15:     "media_records",
16:     "workspaces",
17:     "workspace_notes",
18:     "execution_tasks",
19:     "user_roles",
20:     "fiduciaries",
21:     "properties",
22:     "accounts",
23:     "beneficiaries",
24:     "distributions",
25:     "instruments",
26:     "ledger_entries",
27: ]
28: 
29: def table_exists(cur, table):
30:     cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
31:     return cur.fetchone() is not None
32: 
33: def column_exists(cur, table, column):
34:     cur.execute(f"PRAGMA table_info({table})")
35:     return column in [row[1] for row in cur.fetchall()]
36: 
37: def add_column_if_missing(cur, table, column, column_type="TEXT"):
38:     if not table_exists(cur, table):
39:         print(f"SKIP missing table: {table}")
40:         return
41:     if column_exists(cur, table, column):
```

## Sandbox Differences

- `audit_log` — `['ROW_COUNT_CHANGED', 'ROW_CONTENT_CHANGED']`
- `role_permissions` — `['ROW_COUNT_CHANGED', 'ROW_CONTENT_CHANGED']`

## Required Remediation Direction

- Treat `owner_id` as tenant-local, not globally unique.
- Require `firm_id` in every workspace read and mutation.
- Require the active session firm to match the workspace row.
- Review composite workspace indexes and uniqueness rules.
- Add a regression test proving Firm 1 cannot resolve Firm 2's `ADMIN_OWNER_001` workspace and vice versa.
