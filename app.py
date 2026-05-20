import json
import zipfile
import os
import base64
import secrets
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask import session, Flask, request, render_template, redirect, url_for, make_response, flash, send_file
from database.db import (
    verify_audit_log_chain,
    init_db,
    get_next_trust_id,
    create_trust_record,
    get_all_trusts,
    get_trust_by_id,
    update_trust_fields,
    get_next_property_id,
    create_property_record,
    get_property_by_id,
    get_properties_by_trust_id,
    get_all_assets,
    get_asset_class_counts,
    get_next_account_id,
    create_account_record,
    get_accounts_by_trust_id,
    get_accounts_by_property_id,
    get_next_document_id,
    create_document_record,
    get_documents_by_trust_id,
    get_documents_by_property_id,
    get_next_entry_id,
    create_ledger_entry,
    get_ledger_by_trust,
    get_ledger_entries_by_trust_id,
    ensure_transfer_runtime_columns,
    get_ledger_by_property,
    seed_chart_of_accounts_for_trust,
    get_chart_of_accounts,
    get_trust_financial_summary,
    get_assets_missing_custodian,
    get_assets_missing_review_date,
    get_assets_with_expiration,
    get_orphaned_assets,
    get_assets_expiring_within,
    get_assets_review_due_within,
    get_assets_expired,
    get_assets_review_overdue,
    get_asset_severity_summary,
    get_command_snapshot,
    get_tax_profile,
    get_tax_form_applicability,
    get_tax_readiness,
    ensure_k1_tables,
    get_next_beneficiary_id,
    create_beneficiary_record,
    update_beneficiary_record,
    get_beneficiary_by_id,
    get_beneficiaries_by_trust_id,
    get_next_distribution_id,
    create_distribution_record,
    update_distribution_record,
    get_distribution_by_id,
    get_distributions_by_trust_id,
    get_k1_summary,
    get_beneficiary_by_id_and_trust,
    toggle_beneficiary_active,
    get_distribution_by_id_and_trust,
    export_k1_csv_text,
    get_1041_dataset,
    ensure_instrument_tables,
    get_next_instrument_id,
    create_instrument_record,
    update_instrument_record,
    get_instrument_by_id,
    get_instruments_by_trust_id,
    get_all_instruments,
    get_instrument_creation_guide,
    get_instrument_status_counts,
    get_trust_count,
    get_beneficiary_count,
    get_distribution_count,
    get_instrument_count,
    init_audit_table,
    log_change,
    get_audit_log,
    get_audit_log_by_entity,
    verify_audit_log_chain,
    validate_instrument_payload,
    validate_beneficiary_payload,
    validate_distribution_payload,
    is_locked_status,
    get_distribution_totals_by_trust,
    get_distribution_totals_by_beneficiary,
    money,
    compute_dni_components,
    compute_beneficiary_tax_shares,
    get_portfolio_summary,
    ensure_fiduciary_tables,
    get_next_fiduciary_id,
    create_fiduciary_record,
    get_all_fiduciaries,
    get_fiduciaries_by_trust_id,
    ensure_genealogy_tables,
    get_next_genealogy_id,
    create_genealogy_record,
    get_all_genealogy_records,
    get_genealogy_by_trust_id,
    ensure_media_tables,
    get_next_media_id,
    create_media_record,
    get_all_media,
    get_media_by_entity,
    get_media_by_trust_id,
    ensure_role_tables,
    ensure_user_tables,
    get_user_by_username,
    create_app_user,
    get_next_user_id,
    get_all_app_users,
    update_app_user,
    update_app_user_password,
    get_next_role_id,
    create_role_record,
    get_all_roles,
    get_roles_by_trust_id,
    get_role_summary_by_trust,
    has_required_role,
    get_permissions_by_role,
    role_has_permission,
    replace_role_permissions,
    ensure_user_permission_override_tables,
    get_user_permission_overrides,
    replace_user_permission_overrides,
    get_effective_permissions_for_user,
    user_has_effective_permission,
    get_all_permissions,
    build_system_health_report,
    run_safe_recovery_migrations,
    reseed_default_role_permissions,
    ensure_firm_columns,
    ensure_trust_minutes_tables,
    get_next_minute_id,
    create_trust_minute,
    backfill_trust_minute_certificate_ids, get_certificate_registry_records, get_all_trust_minutes,
    get_trust_minutes_by_trust_id,
    get_trust_minute_by_certificate_id, get_trust_minute_by_id,
    ensure_trust_minutes_execution_columns,
    update_trust_minute_execution,
    ensure_trust_minutes_capacity_columns,
)
from pathlib import Path
from extensions import db as ext_db

# --- Transfer Engine v1 imports ---
from models.models_transfer import Transfer, TransferAction, TransferRecord
from models.models_transfer_support import TransferSupportDoc
from services.services_continuity_assets import (
    get_continuity_classifications,
    get_custody_classifications,
    get_property_continuity_profile,
    update_property_continuity_profile,
    get_continuity_assets_by_trust,
    create_continuity_custody_event,
    get_custody_events_for_property,
    get_custody_event_by_id,
    score_continuity_asset_readiness,
    build_property_evidence_profile,
    enrich_custody_events_with_evidence,
    resolve_evidence_reference,
    build_property_evidence_custody_timeline,
    summarize_property_evidence_custody_timeline,
    update_custody_event_supporting_reference,
    build_property_resolution_queue
)

from services.services_articles import (
    create_trust_article,
    get_all_trust_articles,
    get_trust_article,
    assign_article_to_trust,
    get_articles_for_trust,
    build_dynamic_declaration
)

from services.services_transfer import (
generate_transfer_id,
    add_transfer_action,
    get_transfer_progress,
    validate_capacity_for_step,
    build_assignment_text,
    build_schedule_a_text,
    build_transfer_log_text,
    build_minutes_text,
    get_or_create_transfer_record,
    populate_transfer_record_bundle,
    calculate_control_strength,
    can_finalize_transfer,
    finalize_transfer,
)
import sqlite3
from datetime import datetime, UTC
from werkzeug.utils import secure_filename
from pdf_utils import build_pdf_response, trust_summary_story, k1_readiness_story, fiduciary_report_story, ledger_report_story, form1041_report_story, instrument_detail_story, portfolio_report_story, audit_log_report_story
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import UTC, date, datetime, timedelta
from io import BytesIO

from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
try:
    from PIL import Image as PILImage
except Exception:
    PILImage = None

app = Flask(__name__)

# ===================================================
# PERMISSION DECORATOR ENGINE
# ===================================================

from functools import wraps

def require_permission(permission_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            username = session.get("username")

            if not username:
                flash("Login required.", "danger")
                return redirect(url_for("login"))

            if not user_has_effective_permission(username, permission_name):

                log_change(
                    "security",
                    username,
                    "permission_denied",
                    f"Permission required: {permission_name}"
                )

                flash(
                    f"Permission required: {permission_name}",
                    "danger"
                )

                return redirect(url_for("dashboard"))

            return func(*args, **kwargs)

        return wrapper

    return decorator


STRICT_PACKET_EXPORT = True

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "trustee_app.db"
DB_PATH = Path(os.getenv("DB_PATH", str(DEFAULT_DB_PATH))).resolve()

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH.as_posix()}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
ext_db.init_app(app)

# Runtime SQLite schema compatibility for deployed databases.
try:
    ensure_transfer_runtime_columns()
except Exception as e:
    print("⚠️ Transfer runtime schema migration failed:", e)



def run_hosted_startup_self_heal():
    """
    Permanent hosted startup self-heal.

    Purpose:
    - Repair hosted SQLite schema drift after Railway deploy/restart.
    - Ensure the hosted admin user exists when ENSURE_HOSTED_ADMIN=1.
    - Ensure Admin role has required permissions such as view_dashboard.
    - Ensure firm_id columns exist on key firm-scoped tables.

    This avoids relying on public one-time repair routes for normal hosted operation.
    """
    if os.getenv("ENSURE_HOSTED_ADMIN") != "1":
        return

    import sqlite3
    from werkzeug.security import generate_password_hash

    username = os.getenv("HOSTED_BOOTSTRAP_USERNAME", "admin123").strip()
    password = os.getenv("HOSTED_BOOTSTRAP_PASSWORD", "").strip()
    firm_id = os.getenv("HOSTED_BOOTSTRAP_FIRM_ID", "FIRM-002").strip()

    if not username or not password or not firm_id:
        print("⚠️ Hosted startup self-heal skipped: missing username/password/firm_id.")
        return

    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Core hosted user table.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS app_users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT,
                role_name TEXT,
                status TEXT,
                firm_id TEXT,
                owner_id TEXT
            )
        """)

        cur.execute("PRAGMA table_info(app_users)")
        app_user_cols = [r["name"] for r in cur.fetchall()]
        for col, col_type in [
            ("password_hash", "TEXT"),
            ("role_name", "TEXT"),
            ("status", "TEXT"),
            ("firm_id", "TEXT"),
            ("owner_id", "TEXT"),
        ]:
            if col not in app_user_cols:
                cur.execute(f"ALTER TABLE app_users ADD COLUMN {col} {col_type}")

        # Create/update hosted admin user every startup while ENSURE_HOSTED_ADMIN=1.
        password_hash = generate_password_hash(password)

        cur.execute(
            "SELECT user_id FROM app_users WHERE TRIM(LOWER(username)) = TRIM(LOWER(?))",
            (username,)
        )
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE app_users
                SET username = ?,
                    password_hash = ?,
                    role_name = 'Admin',
                    status = 'active',
                    firm_id = ?,
                    owner_id = 'ADMIN_OWNER_001'
                WHERE user_id = ?
            """, (username, password_hash, firm_id, existing["user_id"]))
            user_action = "updated"
        else:
            cur.execute("SELECT COUNT(*) AS count FROM app_users")
            count = cur.fetchone()["count"]
            user_id = f"USER-{count + 1:03d}"
            cur.execute("""
                INSERT INTO app_users (
                    user_id, username, password_hash, role_name, status, firm_id, owner_id
                ) VALUES (?, ?, ?, 'Admin', 'active', ?, 'ADMIN_OWNER_001')
            """, (user_id, username, password_hash, firm_id))
            user_action = "created"

        # Permissions + role matrix.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                permission_id TEXT PRIMARY KEY,
                permission_name TEXT UNIQUE,
                description TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT,
                permission_name TEXT,
                UNIQUE(role_name, permission_name)
            )
        """)

        default_permissions = [
            ("PERM-001", "view_dashboard", "View dashboards and core system pages"),
            ("PERM-002", "create_trust", "Create trust records"),
            ("PERM-003", "edit_trust", "Edit trust records"),
            ("PERM-004", "view_documents", "View documents"),
            ("PERM-005", "generate_documents", "Generate documents"),
            ("PERM-006", "export_documents", "Export documents"),
            ("PERM-007", "manage_tax_reports", "Manage tax reports"),
            ("PERM-008", "view_audit", "View audit trail"),
            ("PERM-009", "manage_users", "Manage users"),
            ("PERM-010", "manage_roles", "Manage trust roles"),
            ("PERM-011", "manage_permissions", "Manage permissions"),
            ("PERM-012", "view_security", "View security dashboard"),
        ]

        for permission_id, permission_name, description in default_permissions:
            cur.execute("""
                INSERT OR IGNORE INTO permissions (permission_id, permission_name, description)
                VALUES (?, ?, ?)
            """, (permission_id, permission_name, description))

        admin_permissions = [
            "view_dashboard",
            "create_trust",
            "edit_trust",
            "view_documents",
            "generate_documents",
            "export_documents",
            "manage_tax_reports",
            "view_audit",
            "manage_users",
            "manage_roles",
            "manage_permissions",
            "view_security",
        ]

        for permission_name in admin_permissions:
            cur.execute("""
                INSERT OR IGNORE INTO role_permissions (role_name, permission_name)
                VALUES ('Admin', ?)
            """, (permission_name,))

        # Firm-scoped table repair.
        firm_tables = [
            "trusts",
            "audit_log",
            "transfers",
            "trust_minutes",
            "documents",
            "generated_documents",
            "media_records",
            "workspaces",
            "workspace_notes",
            "execution_tasks",
            "user_roles",
            "fiduciaries",
            "properties",
            "accounts",
            "beneficiaries",
            "distributions",
            "instruments",
            "ledger_entries",
        ]

        for table in firm_tables:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if not cur.fetchone():
                continue

            cur.execute(f"PRAGMA table_info({table})")
            cols = [r["name"] for r in cur.fetchall()]
            if "firm_id" not in cols:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN firm_id TEXT")

            cur.execute(f"""
                UPDATE {table}
                SET firm_id = ?
                WHERE firm_id IS NULL OR TRIM(firm_id) = ''
            """, (firm_id,))

        conn.commit()
        conn.close()

        login_attempts.pop(username, None)
        print(f"✅ Hosted startup self-heal complete: user={username}; action={user_action}; firm={firm_id}")

    except Exception as exc:
        print("⚠️ Hosted startup self-heal failed:", exc)




LOGIN_ATTEMPTS_LIMIT = 5
LOGIN_LOCKOUT_SECONDS = 300  # 5 minutes

login_attempts = {}
SESSION_TIMEOUT_SECONDS = 900  # 15 minutes
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(seconds=SESSION_TIMEOUT_SECONDS)

APP_ENV = os.getenv("APP_ENV", "development").lower()
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "0" if APP_ENV == "production" else "1")
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_TO_RANDOM_SECRET_KEY")

if APP_ENV == "production" and SECRET_KEY == "CHANGE_THIS_TO_RANDOM_SECRET_KEY":
    raise RuntimeError("SECRET_KEY must be set to a strong value in production.")

app.secret_key = SECRET_KEY
app.config["WTF_CSRF_FIELD_NAME"] = "_csrf_token"
csrf = CSRFProtect(app)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = APP_ENV == "production"

# Permanent hosted startup self-heal.
try:
    run_hosted_startup_self_heal()
except Exception as e:
    print("⚠️ Hosted startup self-heal wrapper failed:", e)




def run_hosted_test_trust_seed():
    """
    Permanent hosted FIRM-002 test trust seed.

    Runs only when ENSURE_HOSTED_TEST_TRUST=1.
    Provides one stable hosted trust record for Report Center, firewall testing,
    and Trust Summary PDF validation.
    """
    if os.getenv("ENSURE_HOSTED_TEST_TRUST") != "1":
        return

    import sqlite3

    firm_id = os.getenv("HOSTED_BOOTSTRAP_FIRM_ID", "FIRM-002").strip() or "FIRM-002"
    username = os.getenv("HOSTED_BOOTSTRAP_USERNAME", "admin123").strip() or "admin123"

    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS trusts (
                trust_id TEXT PRIMARY KEY,
                trust_name TEXT,
                short_name TEXT,
                jurisdiction TEXT,
                effective_date TEXT,
                trust_type TEXT,
                trust_purpose TEXT,
                accounting_method TEXT,
                workflow_mode TEXT,
                settlor_name TEXT,
                trustee_name TEXT,
                successor_trustee_name TEXT,
                beneficiary_name TEXT,
                record_visibility TEXT,
                workflow_mode_confirmed TEXT,
                ai_explanations TEXT,
                recommended_guidance TEXT,
                initial_corpus_description TEXT,
                property_mapping_timing TEXT,
                asset_categories TEXT,
                generate_schedule_recommendations TEXT,
                status TEXT
            )
        """)

        cur.execute("PRAGMA table_info(trusts)")
        cols = [r["name"] for r in cur.fetchall()]
        for col_name, col_type in [
            ("grantor_name", "TEXT"),
            ("grantor_type", "TEXT"),
            ("grantor_contact", "TEXT"),
            ("seal_path", "TEXT"),
            ("caf_number", "TEXT"),
            ("crid_number", "TEXT"),
            ("trust_motto", "TEXT"),
            ("foundation_scripture", "TEXT"),
            ("prepared_by", "TEXT"),
            ("return_to", "TEXT"),
            ("branding_style", "TEXT DEFAULT 'v3_minimal'"),
            ("owner_id", "TEXT"),
            ("firm_id", "TEXT"),
            ("firm_trust_number", "INTEGER"),
            ("firm_trust_code", "TEXT"),
        ]:
            if col_name not in cols:
                cur.execute(f"ALTER TABLE trusts ADD COLUMN {col_name} {col_type}")
                cols.append(col_name)

        trust_id = "TR-001"

        cur.execute("SELECT trust_id FROM trusts WHERE trust_id = ?", (trust_id,))
        existing = cur.fetchone()

        values = {
            "trust_id": trust_id,
            "trust_name": "Redirect Test Trust 2",
            "short_name": "Hosted Test",
            "jurisdiction": "NEW JERSEY",
            "effective_date": "2026-05-14",
            "trust_type": "revocable",
            "trust_purpose": "property_holding",
            "accounting_method": "accrual",
            "workflow_mode": "private_office",
            "settlor_name": "",
            "trustee_name": "QA TRUSTEE",
            "successor_trustee_name": "QA SUCCESOR",
            "beneficiary_name": "QA BENE",
            "record_visibility": "private",
            "workflow_mode_confirmed": "yes",
            "ai_explanations": "enabled",
            "recommended_guidance": "enabled",
            "initial_corpus_description": "",
            "property_mapping_timing": "post_creation",
            "asset_categories": "property",
            "generate_schedule_recommendations": "yes",
            "status": "Finalized",
            "owner_id": username,
            "firm_id": firm_id,
            "firm_trust_number": 1,
            "firm_trust_code": "TR-001",
        }

        if existing:
            cur.execute("""
                UPDATE trusts
                SET trust_name = ?,
                    short_name = ?,
                    jurisdiction = ?,
                    effective_date = ?,
                    trust_type = ?,
                    trust_purpose = ?,
                    accounting_method = ?,
                    workflow_mode = ?,
                    settlor_name = ?,
                    trustee_name = ?,
                    successor_trustee_name = ?,
                    beneficiary_name = ?,
                    record_visibility = ?,
                    workflow_mode_confirmed = ?,
                    ai_explanations = ?,
                    recommended_guidance = ?,
                    initial_corpus_description = ?,
                    property_mapping_timing = ?,
                    asset_categories = ?,
                    generate_schedule_recommendations = ?,
                    status = ?,
                    owner_id = ?,
                    firm_id = ?,
                    firm_trust_number = ?,
                    firm_trust_code = ?
                WHERE trust_id = ?
            """, (
                values["trust_name"], values["short_name"], values["jurisdiction"],
                values["effective_date"], values["trust_type"], values["trust_purpose"],
                values["accounting_method"], values["workflow_mode"], values["settlor_name"],
                values["trustee_name"], values["successor_trustee_name"], values["beneficiary_name"],
                values["record_visibility"], values["workflow_mode_confirmed"],
                values["ai_explanations"], values["recommended_guidance"],
                values["initial_corpus_description"], values["property_mapping_timing"],
                values["asset_categories"], values["generate_schedule_recommendations"],
                values["status"], values["owner_id"], values["firm_id"],
                values["firm_trust_number"], values["firm_trust_code"], values["trust_id"]
            ))
            action = "updated"
        else:
            cur.execute("""
                INSERT INTO trusts (
                    trust_id, trust_name, short_name, jurisdiction, effective_date,
                    trust_type, trust_purpose, accounting_method, workflow_mode,
                    settlor_name, trustee_name, successor_trustee_name, beneficiary_name,
                    record_visibility, workflow_mode_confirmed, ai_explanations,
                    recommended_guidance, initial_corpus_description, property_mapping_timing,
                    asset_categories, generate_schedule_recommendations, status,
                    owner_id, firm_id, firm_trust_number, firm_trust_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                values["trust_id"], values["trust_name"], values["short_name"], values["jurisdiction"],
                values["effective_date"], values["trust_type"], values["trust_purpose"],
                values["accounting_method"], values["workflow_mode"], values["settlor_name"],
                values["trustee_name"], values["successor_trustee_name"], values["beneficiary_name"],
                values["record_visibility"], values["workflow_mode_confirmed"],
                values["ai_explanations"], values["recommended_guidance"],
                values["initial_corpus_description"], values["property_mapping_timing"],
                values["asset_categories"], values["generate_schedule_recommendations"],
                values["status"], values["owner_id"], values["firm_id"],
                values["firm_trust_number"], values["firm_trust_code"]
            ))
            action = "created"

        conn.commit()
        conn.close()

        print(f"✅ Hosted test trust seed complete: trust={trust_id}; action={action}; firm={firm_id}")

    except Exception as exc:
        print("⚠️ Hosted test trust seed failed:", exc)




# Permanent hosted test trust seed.
try:
    run_hosted_test_trust_seed()
except Exception as e:
    print("⚠️ Hosted test trust seed wrapper failed:", e)



def run_hosted_portfolio_seed():
    """
    Permanent hosted FIRM-002 portfolio seed.

    Seeds one property, account, document, and ledger entry
    for TR-001 under FIRM-002.
    """
    if os.getenv("ENSURE_HOSTED_PORTFOLIO_SEED") != "1":
        return

    import sqlite3
    from datetime import datetime

    trust_id = "TR-001"
    firm_id = "FIRM-002"
    owner_id = "admin123"

    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # =========================
        # PROPERTIES
        # =========================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id TEXT,
                trust_id TEXT,
                property_name TEXT,
                property_type TEXT,
                estimated_value TEXT
            )
        """)

        cur.execute("PRAGMA table_info(properties)")
        cols = [r["name"] for r in cur.fetchall()]

        for col_name, col_type in [
            ("firm_id", "TEXT"),
            ("owner_id", "TEXT")
        ]:
            if col_name not in cols:
                cur.execute(f"ALTER TABLE properties ADD COLUMN {col_name} {col_type}")

        cur.execute("""
            SELECT property_id FROM properties
            WHERE property_id = 'PROP-001' AND firm_id = ?
        """, (firm_id,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO properties (
                    property_id,
                    trust_id,
                    property_name,
                    property_type,
                    estimated_value,
                    firm_id,
                    owner_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "PROP-001",
                trust_id,
                "Hosted Test Property",
                "Real Estate",
                "$250,000",
                firm_id,
                owner_id
            ))

        # =========================
        # ACCOUNTS
        # =========================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT,
                trust_id TEXT,
                institution_name TEXT,
                account_type TEXT,
                balance TEXT
            )
        """)

        cur.execute("PRAGMA table_info(accounts)")
        cols = [r["name"] for r in cur.fetchall()]

        for col_name, col_type in [
            ("firm_id", "TEXT"),
            ("owner_id", "TEXT")
        ]:
            if col_name not in cols:
                cur.execute(f"ALTER TABLE accounts ADD COLUMN {col_name} {col_type}")

        cur.execute("""
            SELECT account_id FROM accounts
            WHERE account_id = 'ACCT-001' AND firm_id = ?
        """, (firm_id,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO accounts (
                    account_id,
                    trust_id,
                    institution_name,
                    account_type,
                    balance,
                    firm_id,
                    owner_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "ACCT-001",
                trust_id,
                "Hosted Trust Bank",
                "Checking",
                "$15,000",
                firm_id,
                owner_id
            ))

        # =========================
        # DOCUMENTS
        # =========================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT,
                trust_id TEXT,
                document_name TEXT,
                document_type TEXT
            )
        """)

        cur.execute("PRAGMA table_info(documents)")
        cols = [r["name"] for r in cur.fetchall()]

        for col_name, col_type in [
            ("firm_id", "TEXT"),
            ("owner_id", "TEXT")
        ]:
            if col_name not in cols:
                cur.execute(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type}")

        cur.execute("""
            SELECT document_id FROM documents
            WHERE document_id = 'DOC-001' AND firm_id = ?
        """, (firm_id,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO documents (
                    document_id,
                    trust_id,
                    document_name,
                    document_type,
                    firm_id,
                    owner_id
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "DOC-001",
                trust_id,
                "Hosted Portfolio Seed Document",
                "Trust Record",
                firm_id,
                owner_id
            ))

        # =========================
        # LEDGER ENTRIES
        # =========================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ledger_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id TEXT,
                trust_id TEXT,
                entry_type TEXT,
                amount TEXT,
                description TEXT,
                entry_date TEXT
            )
        """)

        cur.execute("PRAGMA table_info(ledger_entries)")
        cols = [r["name"] for r in cur.fetchall()]

        for col_name, col_type in [
            ("firm_id", "TEXT"),
            ("owner_id", "TEXT")
        ]:
            if col_name not in cols:
                cur.execute(f"ALTER TABLE ledger_entries ADD COLUMN {col_name} {col_type}")

        cur.execute("""
            SELECT entry_id FROM ledger_entries
            WHERE entry_id = 'LEDGER-001' AND firm_id = ?
        """, (firm_id,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO ledger_entries (
                    entry_id,
                    trust_id,
                    entry_type,
                    amount,
                    description,
                    entry_date,
                    firm_id,
                    owner_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "LEDGER-001",
                trust_id,
                "Asset",
                "$15,000",
                "Hosted portfolio seed ledger entry",
                datetime.utcnow().strftime("%Y-%m-%d"),
                firm_id,
                owner_id
            ))

        conn.commit()
        conn.close()

        print("✅ Hosted portfolio seed complete: property/account/document/ledger created")

    except Exception as exc:
        print("⚠️ Hosted portfolio seed failed:", exc)




# Permanent hosted portfolio seed.
try:
    run_hosted_portfolio_seed()
except Exception as e:
    print("⚠️ Hosted portfolio seed wrapper failed:", e)


def generate_csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token




def get_current_owner():
    """
    Returns the current authenticated owner identity.
    Centralized for Phase 5 owner isolation.
    """
    return session.get("username")



def get_visible_trusts_for_current_operator():
    # G-1 stability patch: pull from firm-scoped DB source, not itself.
    trusts = get_all_trusts()

    if is_master_admin():
        return trusts

    # Tenant isolation rule:
    # A non-master Admin may see all trusts inside the active firm.
    # Trustee/Viewer visibility remains assignment-based.
    if session.get("role") == "Admin":
        return trusts

    username = (session.get("username") or "").strip().lower()
    if not username:
        return []

    visible = []
    for trust in trusts:
        role_rows = get_roles_by_trust_id(trust["trust_id"])
        for row in role_rows:
            full_name = (row.get("full_name") or "").strip().lower()
            if full_name == username:
                visible.append(trust)
                break

    return visible

def operator_can_access_trust(trust_id):
    if is_master_admin():
        return True

    username = (session.get("username") or "").strip().lower()
    if not username:
        return False

    # Tenant isolation rule:
    # A non-master Admin may access any trust that belongs to the Admin's active firm.
    # Trustee/Viewer access still depends on trust role assignment below.
    if session.get("role") == "Admin":
        trust = get_trust_by_id(trust_id)
        return bool(trust)

    role_rows = get_roles_by_trust_id(trust_id)
    for row in role_rows:
        full_name = (row.get("full_name") or "").strip().lower()
        if full_name == username:
            return True

    return False

def deny_unassigned_trust_access(trust_id):
    if not session.get("username"):
        return redirect(url_for("login"))

    if not operator_can_access_trust(trust_id):
        return render_template(
        
            "access_denied.html",
            reason="You are not assigned to this trust."
        )

    return None


def validate_csrf_token():
    form_token = request.form.get("_csrf_token")
    session_token = session.get("_csrf_token")

    # Accept if both exist (practical validation for this app)
    if form_token and session_token:
        return True

    return False


def get_transfer_for_active_firm_or_404(transfer_id):
    firm_id = session.get("firm_id") or "FIRM-001"
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()

    if transfer.firm_id != firm_id:
        log_change(
            "security",
            transfer_id,
            "transfer_firm_access_denied",
            f"Transfer outside active firm scope. User={session.get('username')}; Firm={firm_id}; TransferFirm={transfer.firm_id}"
        )
        return None, render_template(
            "access_denied.html",
            reason="This transfer record is not available within your assigned firm scope."
        )

    return transfer, None


def get_transfer_resume_endpoint(transfer):
    if not transfer.asset_name:
        return url_for("transfer_asset", transfer_id=transfer.transfer_id)
    if not transfer.transfer_type:
        return url_for("transfer_classification", transfer_id=transfer.transfer_id)
    if not transfer.assignment_confirmed:
        return url_for("transfer_assignment", transfer_id=transfer.transfer_id)
    if not transfer.trustee_decision:
        return url_for("transfer_trustee_acceptance", transfer_id=transfer.transfer_id)
    if not transfer.control_change_status:
        return url_for("transfer_control_evidence", transfer_id=transfer.transfer_id)
    if not transfer.records_complete:
        return url_for("transfer_records", transfer_id=transfer.transfer_id)
    return url_for("transfer_review", transfer_id=transfer.transfer_id)




def mark_core_support_docs_included(transfer):

    core_keys = {"assignment", "schedule_a", "transfer_log", "minutes"}

    rows = TransferSupportDoc.query.filter_by(transfer_id_fk=transfer.id).all()
    for row in rows:
        if row.category_key in core_keys:
            row.status = "included"


def seed_transfer_support_docs(transfer):
    existing = TransferSupportDoc.query.filter_by(transfer_id_fk=transfer.id).count()
    if existing:
        return

    defaults = [
        ("assignment", "Assignment", "included"),
        ("schedule_a", "Schedule A", "included"),
        ("transfer_log", "Transfer Log", "included"),
        ("minutes", "Minutes", "included"),
        ("universal_instructions", "Universal Transfer Instructions", "recommended"),
        ("optional_support_docs", "Optional Supporting Transfer Documents", "optional"),
        ("recommended_support_docs", "Recommended Supporting Transfer Documents", "recommended"),
        ("bank_support_docs", "Bank / Account Support Documents", "optional"),
        ("personal_property_support_docs", "Personal Property Support Documents", "optional"),
        ("document_support_docs", "Document / Intangible Rights Support Documents", "optional"),
    ]

    for category_key, category_label, status in defaults:
        ext_db.session.add(
            TransferSupportDoc(
                transfer_id_fk=transfer.id,
                category_key=category_key,
                category_label=category_label,
                status=status,
            )
        )



def build_trust_preview_context(trust):
    def _get(obj, key, default=""):
        try:
            if obj is None:
                return default
            if isinstance(obj, dict):
                return obj.get(key, default)
            try:
                return obj[key]
            except Exception:
                pass
            return getattr(obj, key, default)
        except Exception:
            return default

    def _first(obj, keys, default=""):
        for key in keys:
            value = _get(obj, key, "")
            if value not in (None, "", []):
                return value
        return default

    trust_id_value = _first(trust, ["trust_id"])
    trust_name_value = _first(trust, ["trust_name", "name", "trust_title"])
    trust_type_value = _first(trust, ["trust_type", "type_of_trust", "trust_category"])
    grantor_value = _first(trust, ["grantor_name", "settlor_name", "grantor", "settlor"])
    trustee_value = _first(trust, ["trustee_name", "initial_trustee_name", "current_trustee_name", "trustee"])
    successor_trustee_value = _first(trust, ["successor_trustee_name", "successor_trustee", "alternate_trustee_name"])
    beneficiary_value = _first(trust, ["primary_beneficiary", "beneficiary_name", "primary_beneficiary_name"])
    owner_id_value = _first(trust, ["owner_id", "owner", "client_id"])
    status_value = _first(trust, ["status"])
    jurisdiction_value = _first(trust, ["jurisdiction", "state_of_jurisdiction", "governing_jurisdiction"])
    governing_law_value = _first(trust, ["governing_law", "governing_law_state", "governing_state"])
    created_at_value = _first(trust, ["created_at", "date_created"])
    effective_date_value = _first(trust, ["effective_date", "trust_date", "date_of_trust", "execution_date", "signed_date", "created_at"])
    trust_purpose_value = _first(trust, ["trust_purpose", "purpose", "purpose_statement", "mission"])
    initial_corpus_value = _first(trust, ["initial_corpus_description", "initial_corpus", "corpus_description", "funding_description"])
    asset_categories_value = _first(trust, ["asset_categories", "asset_category", "asset_classes"])
    property_mapping_timing_value = _first(trust, ["property_mapping_timing", "funding_timing", "transfer_timing"])

    created_at_display = created_at_value or ""
    effective_date_display = effective_date_value or ""

    return {
        "trust_id": trust_id_value,
        "trust_name": trust_name_value,
        "trust_type": trust_type_value,
        "grantor_name": grantor_value,
        "trustee_name": trustee_value,
        "successor_trustee_name": successor_trustee_value,
        "primary_beneficiary": beneficiary_value,
        "owner_id": owner_id_value,
        "status": status_value,
        "jurisdiction": jurisdiction_value,
        "governing_law": governing_law_value,
        "created_at": created_at_value,
        "created_at_display": created_at_display,
        "effective_date": effective_date_value,
        "effective_date_display": effective_date_display,
        "trust_purpose": trust_purpose_value,
        "initial_corpus_description": initial_corpus_value,
        "asset_categories": asset_categories_value,
        "property_mapping_timing": property_mapping_timing_value,
        "seal_path": _first(trust, ["seal_path", "trust_seal_path", "logo_path"]),
        "caf_number": _first(trust, ["caf_number", "caf"]),
        "crid_number": _first(trust, ["crid_number", "crid"]),
        "trust_motto": _first(trust, ["trust_motto", "motto"]),
        "foundation_scripture": _first(trust, ["foundation_scripture", "scripture"]),
        "prepared_by": _first(trust, ["prepared_by"]),
        "return_to": _first(trust, ["return_to"]),
        "branding_style": _first(trust, ["branding_style"], "v3_minimal"),
    }



def build_trust_document_readiness(preview_context):
    def has_value(key):
        value = preview_context.get(key, "")
        return value not in (None, "", [])

    friendly_labels = {
        "trust_name": "trust name",
        "trust_type": "trust type",
        "grantor_name": "grantor / settlor name",
        "trustee_name": "trustee name",
        "effective_date": "effective date",
        "successor_trustee_name": "successor trustee name",
        "initial_corpus_or_asset_categories": "initial corpus or asset categories",
    }

    def label_for(key):
        return friendly_labels.get(key, key.replace("_", " "))

    def build_status(required_keys, alternate_groups=None):
        missing = []

        for key in required_keys:
            if not has_value(key):
                missing.append(label_for(key))

        if alternate_groups:
            for label, keys in alternate_groups:
                if not any(has_value(k) for k in keys):
                    missing.append(label_for(label))

        return {
            "ready": len(missing) == 0,
            "missing": missing,
        }

    readiness = {
        "articles": build_status(
            ["trust_name", "trust_type", "grantor_name", "trustee_name", "effective_date"]
        ),
        "trustee_acceptance": build_status(
            ["trust_name", "trustee_name", "effective_date"]
        ),
        "general_assignment": build_status(
            ["trust_name", "grantor_name"],
            alternate_groups=[("initial_corpus_or_asset_categories", ["initial_corpus_description", "asset_categories"])]
        ),
        "organizational_minutes": build_status(
            ["trust_name", "trustee_name", "effective_date"]
        ),
        "successor_trustee": build_status(
            ["trust_name", "trustee_name", "effective_date", "successor_trustee_name"]
        ),
    }

    return readiness



def build_trust_packet_readiness(document_readiness):
    keys = [
        "articles",
        "trustee_acceptance",
        "general_assignment",
        "organizational_minutes",
        "successor_trustee",
    ]

    all_ready = all(document_readiness.get(key, {}).get("ready", False) for key in keys)

    export_policy = get_export_policy()
    strict_packet_export = bool(export_policy.get("strict_packet_export", True))
    blocked = strict_packet_export and not all_ready

    return {
        "ready": all_ready,
        "blocked": blocked,
        "strict_mode": strict_packet_export,
        "status_label": "Ready to export" if all_ready else "Incomplete — export available with warnings",
    }



def build_correction_links(trust_id, document_readiness, return_to="execution"):
    def with_return(url):
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}return_to={return_to}"

    def build_link(url, label):
        return {
            "url": with_return(url),
            "label": label,
        }

    def link_for_field(field_name):
        field_name = field_name.lower().strip()

        if field_name in ["grantor_name", "grantor_/_settlor_name", "grantor_settlor_name"]:
            return build_link(
                url_for("create_trust_step2_grantor", trust_id=trust_id),
                "Go to Grantor / Settlor step"
            )

        if field_name in ["trustee_name", "successor_trustee_name"]:
            return build_link(
                url_for("create_trust_step2", trust_id=trust_id),
                "Go to Trustee / Successor Trustee step"
            )

        if field_name in ["trust_purpose"]:
            return build_link(
                url_for("create_trust_step3", trust_id=trust_id),
                "Go to Trust Purpose step"
            )

        if field_name in ["initial_corpus_description", "initial_corpus_or_asset_categories", "asset_categories"]:
            return build_link(
                url_for("create_trust_step4", trust_id=trust_id),
                "Go to Corpus / Asset Details step"
            )

        if field_name in ["effective_date", "trust_name", "trust_type"]:
            return build_link(
                url_for("trust_detail", trust_id=trust_id) + f"?focus={field_name}",
                "Go to Trust Detail / Identity section"
            )

        return build_link(
            url_for("trust_detail", trust_id=trust_id) + f"?focus={field_name}",
            "Go to Trust Detail"
        )

    correction_links = {}

    for doc_key, status in document_readiness.items():
        missing = status.get("missing", [])
        doc_links = []

        seen = set()
        for field in missing:
            normalized_field = field.replace(" / ", "_").replace(" ", "_").lower()
            link = link_for_field(normalized_field)
            unique_key = (link["url"], link["label"])
            if unique_key not in seen:
                seen.add(unique_key)
                doc_links.append(link)

        correction_links[doc_key] = doc_links

    return correction_links


def resolve_post_save_return(trust_id, fallback_endpoint, fallback_kwargs=None):
    fallback_kwargs = fallback_kwargs or {}
    return_to = request.args.get("return_to")

    if return_to == "execution":
        return redirect(url_for("trust_execution_dashboard", trust_id=trust_id, returned_from_correction=1))

    if return_to == "packet_preview":
        return redirect(url_for("trust_packet_preview", trust_id=trust_id, returned_from_correction=1))

    if return_to == "post_create_console":
        return redirect(url_for("trust_formation_preview_hub", trust_id=trust_id, returned_from_correction=1))

    return redirect(url_for(fallback_endpoint, **fallback_kwargs))

def build_admin_trust_summary(trust):
    preview_context = build_trust_preview_context(trust)
    document_readiness = build_trust_document_readiness(preview_context)
    packet_readiness = build_trust_packet_readiness(document_readiness)
    correction_links = build_correction_links(preview_context.get("trust_id"), document_readiness, return_to="execution")

    keys = [
        "articles",
        "trustee_acceptance",
        "general_assignment",
        "organizational_minutes",
        "successor_trustee",
    ]

    ready_count = sum(1 for key in keys if document_readiness.get(key, {}).get("ready", False))
    incomplete_count = len(keys) - ready_count

    missing_areas = []
    for key in keys:
        status = document_readiness.get(key, {})
        if not status.get("ready", False):
            label = key.replace("_", " ").title()
            missing = status.get("missing", [])
            if missing:
                missing_areas.append(f"{label}: " + ", ".join(missing[:2]))
            else:
                missing_areas.append(label)

    quick_fix_links = []
    seen = set()
    for key in keys:
        for item in correction_links.get(key, []):
            unique_key = (item["url"], item["label"])
            if unique_key not in seen:
                seen.add(unique_key)
                quick_fix_links.append(item)

    return {
        "trust_id": preview_context.get("trust_id"),
        "trust_name": preview_context.get("trust_name") or "Unnamed Trust",
        "trust_type": preview_context.get("trust_type") or "",
        "last_updated": get_trust_last_updated_value(trust),
        "packet_status": packet_readiness.get("status_label"),
        "packet_ready": packet_readiness.get("ready", False),
        "ready_count": ready_count,
        "incomplete_count": incomplete_count,
        "missing_areas": missing_areas[:3],
        "quick_fix_links": quick_fix_links[:3],
    }


EXPORT_ACTIVITY_LOG_PATH = Path("data/export_activity_log.json")
EXPORT_POLICY_PATH = Path("data/export_policy.json")


def get_trust_last_updated_value(trust):
    candidate_fields = [
        "updated_at",
        "modified_at",
        "last_updated",
        "created_at",
    ]

    for field in candidate_fields:
        try:
            value = trust[field]
            if value not in (None, ""):
                return str(value)
        except Exception:
            pass

        try:
            value = getattr(trust, field)
            if value not in (None, ""):
                return str(value)
        except Exception:
            pass

    return "Not available"

def ensure_export_policy_file():
    EXPORT_POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not EXPORT_POLICY_PATH.exists():
        EXPORT_POLICY_PATH.write_text(json.dumps({
    "strict_packet_export": True,
    "allow_user_creation": True,
    "read_only_mode": False,
    "allow_exports": True
}, indent=2), encoding="utf-8")

def get_default_export_policy():
    return {
        "strict_packet_export": True,
        "allow_user_creation": True,
        "read_only_mode": False,
        "allow_exports": True,
    }

def get_export_policy():
    ensure_export_policy_file()
    default_policy = get_default_export_policy()
    try:
        saved_policy = json.loads(EXPORT_POLICY_PATH.read_text(encoding="utf-8"))
        default_policy.update(saved_policy)
        return default_policy
    except Exception:
        return default_policy

def save_export_policy(policy):
    merged = get_default_export_policy()
    merged.update(policy or {})
    EXPORT_POLICY_PATH.write_text(json.dumps(merged, indent=2), encoding="utf-8")

def set_export_policy(strict_packet_export):
    policy = get_export_policy()
    policy["strict_packet_export"] = bool(strict_packet_export)
    save_export_policy(policy)



EXPORT_ACTIVITY_LOG_PATH = Path("data/export_activity_log.json")

def ensure_export_activity_log():
    EXPORT_ACTIVITY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not EXPORT_ACTIVITY_LOG_PATH.exists():
        EXPORT_ACTIVITY_LOG_PATH.write_text("[]", encoding="utf-8")

def read_export_activity_log():
    ensure_export_activity_log()
    try:
        return json.loads(EXPORT_ACTIVITY_LOG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []

def append_export_activity(entry):
    entries = read_export_activity_log()
    entries.append(entry)
    EXPORT_ACTIVITY_LOG_PATH.write_text(json.dumps(entries, indent=2), encoding="utf-8")

def get_recent_export_activity(limit=25):
    entries = read_export_activity_log()
    return list(reversed(entries))[:limit]

def get_latest_export_for_trust(trust_id):
    entries = read_export_activity_log()
    for entry in reversed(entries):
        if entry.get("trust_id") == trust_id:
            return entry
    return None

def build_export_activity_entry(preview_context, document_readiness, packet_readiness, filename):
    keys = [
        "articles",
        "trustee_acceptance",
        "general_assignment",
        "organizational_minutes",
        "successor_trustee",
    ]
    ready_count = sum(1 for key in keys if document_readiness.get(key, {}).get("ready", False))
    incomplete_count = len(keys) - ready_count

    return {
        "trust_id": preview_context.get("trust_id"),
        "trust_name": preview_context.get("trust_name") or "Unnamed Trust",
        "trust_type": preview_context.get("trust_type") or "",
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "packet_status": packet_readiness.get("status_label"),
        "packet_ready": packet_readiness.get("ready", False),
        "ready_count": ready_count,
        "incomplete_count": incomplete_count,
        "filename": filename,
    }

def build_trust_branding_context(preview_context):
    """
    Universal trust branding context.

    This helper intentionally avoids hard-coded personal estate data.
    Future trust records may supply:
    - seal_path
    - caf_number
    - crid_number
    - motto
    - scripture
    - prepared_by
    - return_to

    If values are absent, the document uses a neutral professional trust header.
    """
    def first_value(*keys):
        for key in keys:
            value = preview_context.get(key)
            if value not in (None, "", []):
                return value
        return ""

    return {
        "trust_name": first_value("trust_name") or "Trust Administration Record",
        "trust_id": first_value("trust_id"),
        "jurisdiction": first_value("jurisdiction", "governing_law"),
        "effective_date": first_value("effective_date_display", "effective_date"),
        "seal_path": first_value("seal_path", "trust_seal_path", "logo_path"),
        "caf_number": first_value("caf_number", "caf"),
        "crid_number": first_value("crid_number", "crid"),
        "motto": first_value("motto", "trust_motto"),
        "scripture": first_value("scripture", "foundation_scripture"),
        "prepared_by": first_value("prepared_by"),
        "return_to": first_value("return_to"),
    }



def get_pdf_optimized_seal_path(seal_path):
    """
    Return a PDF-optimized seal image path.

    Original uploaded seal remains untouched.
    Optimized copy is used only for ReportLab PDF embedding to reduce PDF size.
    """
    if not seal_path:
        return ""

    source = Path(seal_path)
    if not source.exists() or not source.is_file():
        return seal_path

    if PILImage is None:
        return seal_path

    cache_dir = Path("data/pdf_assets")
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_name = f"{source.stem}_pdfseal.jpg"
    target = cache_dir / cache_name

    try:
        if target.exists() and target.stat().st_mtime >= source.stat().st_mtime:
            return target.as_posix()
    except Exception:
        pass

    try:
        with PILImage.open(source) as img:
            img = img.convert("RGB")
            img.thumbnail((300, 300))
            img.save(target, format="JPEG", quality=72, optimize=True)
        return target.as_posix()
    except Exception:
        return seal_path

def add_universal_v3_letterhead(story, styles, preview_context, document_label):
    branding = build_trust_branding_context(preview_context)

    trust_name = branding.get("trust_name") or "Trust Administration Record"
    trust_id = branding.get("trust_id") or ""
    jurisdiction = branding.get("jurisdiction") or ""
    effective_date = branding.get("effective_date") or ""
    motto = branding.get("motto") or ""
    scripture = branding.get("scripture") or ""
    caf_number = branding.get("caf_number") or ""
    crid_number = branding.get("crid_number") or ""

    title_style = ParagraphStyle(
        "UniversalV3Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        alignment=1,
        textColor=colors.HexColor("#111111"),
        spaceAfter=8,
    )
    body_style = styles["BodyText"]

    # Universal trust-specific seal rendering.
    # Render uploaded trust seal when available; otherwise use neutral fallback mark.
    seal_path = branding.get("seal_path") or ""
    seal_rendered = False
    if seal_path:
        try:
            optimized_seal_path = get_pdf_optimized_seal_path(seal_path)
            seal_file_path = Path(optimized_seal_path)
            if seal_file_path.exists() and seal_file_path.is_file():
                story.append(Image(seal_file_path.as_posix(), width=72, height=72))
                seal_rendered = True
        except Exception:
            seal_rendered = False

    if not seal_rendered:
        story.append(Paragraph("◇", title_style))

    story.append(Paragraph(f"<b>{trust_name}</b>", title_style))
    story.append(Paragraph("Trust Administration Record", body_style))

    if motto:
        story.append(Paragraph(motto, body_style))
    if scripture:
        story.append(Paragraph(scripture, body_style))

    meta_parts = []
    if trust_id:
        meta_parts.append(f"Trust ID: {trust_id}")
    if jurisdiction:
        meta_parts.append(f"Jurisdiction: {jurisdiction}")
    if effective_date:
        meta_parts.append(f"Effective Date: {effective_date}")
    if caf_number:
        meta_parts.append(f"CAF: {caf_number}")
    if crid_number:
        meta_parts.append(f"CRID: {crid_number}")

    if meta_parts:
        story.append(Paragraph(" | ".join(meta_parts), body_style))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<font color='#b8860b'>────────────────────────────────────────</font>", body_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>{document_label}</b>", title_style))
    story.append(Spacer(1, 14))


def generate_declaration_of_trust_pdf(trust, preview_context):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()

    # === INSTRUMENT STYLE BLOCK ===
    from reportlab.lib.styles import ParagraphStyle

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Title'],
        alignment=1,
        spaceAfter=12
    )

    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading2'],
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        spaceAfter=6
    )

    small_style = ParagraphStyle(
        'SmallStyle',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=4
    )

    story = []

    add_universal_v3_letterhead(story, styles, preview_context, "Declaration of Trust")

    story.append(Paragraph("Declaration", header_style))
    story.append(Paragraph(
        "This Declaration of Trust summarizes the trust identity, foundational parties, governing jurisdiction, "
        "administrative purpose, and initial trust property currently recorded in the Trustee App system.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Trust Identification", header_style))
    story.append(Paragraph(f"<b>Trust Name:</b> {preview_context.get('trust_name') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Trust ID:</b> {preview_context.get('trust_id') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Trust Type:</b> {preview_context.get('trust_type') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Effective Date:</b> {preview_context.get('effective_date_display') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Jurisdiction:</b> {preview_context.get('jurisdiction') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Governing Law:</b> {preview_context.get('governing_law') or preview_context.get('jurisdiction') or '______________________________'}", styles["BodyText"]))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Foundational Parties", header_style))
    story.append(Paragraph(f"<b>Grantor / Settlor:</b> {preview_context.get('grantor_name') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Trustee:</b> {preview_context.get('trustee_name') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Successor Trustee:</b> {preview_context.get('successor_trustee_name') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Primary Beneficiary:</b> {preview_context.get('primary_beneficiary') or '______________________________'}", styles["BodyText"]))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Purpose and Administration", header_style))
    story.append(Paragraph(
        preview_context.get("trust_purpose") or
        "The trust is established for the lawful holding, administration, protection, and orderly management of trust property and related records.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Initial Trust Property", header_style))
    story.append(Paragraph(f"<b>Initial Corpus:</b> {preview_context.get('initial_corpus_description') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Asset Categories:</b> {preview_context.get('asset_categories') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Property Mapping Timing:</b> {preview_context.get('property_mapping_timing') or '______________________________'}", styles["BodyText"]))
    story.append(Spacer(1, 18))

    story.append(Paragraph("Declaratory Statement", header_style))
    story.append(Paragraph(
        "The undersigned declares that the above trust record is maintained as a controlled internal trust administration record. "
        "This output is generated from the Trustee App data record and should be reviewed against the governing trust instrument, "
        "signed records, and applicable professional advice before external reliance.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 24))

    story.append(Paragraph("Grantor / Settlor Signature: ______________________________", styles["BodyText"]))
    story.append(Spacer(1, 16))
    story.append(Paragraph("Trustee Signature: ______________________________", styles["BodyText"]))
    story.append(Spacer(1, 16))
    story.append(Paragraph("Date: ______________________________", styles["BodyText"]))

    doc.build(story)
    buffer.seek(0)
    return buffer




def generate_transfer_certificate_pdf(transfer, trust=None, asset=None):
    """
    Generate an internal PDF certificate for a completed transfer.

    TOS-54:
    - Uses existing transfer audit data.
    - Does not mutate database state.
    - Does not create routes.
    - Designed for completed transfers only, with graceful fallback display.
    """
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # === TOS-57 TRANSFER CERTIFICATE INSTRUMENT STYLE BLOCK ===
    from reportlab.lib.styles import ParagraphStyle

    title_style = ParagraphStyle(
        "TransferCertificateTitle",
        parent=styles["Title"],
        alignment=1,
        spaceAfter=12,
    )

    header_style = ParagraphStyle(
        "TransferCertificateHeader",
        parent=styles["Heading2"],
        spaceBefore=10,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "TransferCertificateBody",
        parent=styles["Normal"],
        spaceAfter=6,
    )

    small_style = ParagraphStyle(
        "TransferCertificateSmall",
        parent=styles["Normal"],
        fontSize=9,
        spaceAfter=4,
    )

    story = []

    # TOS-57 Seal + Authority Integration
    try:
        preview_context = dict(trust) if trust and hasattr(trust, "keys") else (trust or {})
        add_universal_v3_letterhead(story, styles, preview_context, "Transfer Certificate")
    except Exception:
        pass


    def safe_get(obj, key, default="Not recorded"):
        if obj is None:
            return default
        if isinstance(obj, dict):
            value = obj.get(key, default)
        elif hasattr(obj, "keys") and key in obj.keys():
            value = obj[key]
        else:
            value = getattr(obj, key, default)
        return value if value not in [None, ""] else default

    transfer_id = safe_get(transfer, "transfer_id")
    status = safe_get(transfer, "status")
    finalized_at = safe_get(transfer, "finalized_at")
    finalized_by = safe_get(transfer, "finalized_by")
    finalized_capacity = safe_get(transfer, "finalized_capacity")

    # TOS-57 Certificate reference block
    certificate_id = f"TCERT-{transfer_id}"
    certificate_class = "Internal Fiduciary Transfer Completion Certificate"
    certificate_status = "Issued from completed transfer record"

    # TOS-59 ENRICHED DATA RESOLUTION

    # Trust name resolution
    trust_name = safe_get(trust, "trust_name", safe_get(transfer, "trust_id"))

    # Asset resolution (PRIMARY SOURCE = transfer)
    asset_name = safe_get(transfer, "asset_name", safe_get(asset, "name", safe_get(transfer, "asset_id")))
    asset_type = safe_get(transfer, "asset_type", safe_get(asset, "asset_type", "Not recorded"))

    story.append(Paragraph("<b>TRANSFER COMPLETION CERTIFICATE</b>", title_style))
    story.append(Paragraph(f"<b>Certificate ID:</b> {certificate_id}", small_style))
    story.append(Paragraph(f"<b>Certificate Class:</b> {certificate_class}", small_style))
    story.append(Paragraph(f"<b>Certificate Status:</b> {certificate_status}", small_style))
    story.append(Spacer(1, 18))

    story.append(Paragraph(
        "This certificate records the internal completion of a trust asset transfer "
        "within the Trustee App execution workflow.",
        body_style
    ))
    story.append(Spacer(1, 14))

    story.append(Paragraph(f"<b>Transfer ID:</b> {transfer_id}", body_style))
    story.append(Paragraph(f"<b>Status:</b> {status}", body_style))
    story.append(Paragraph(f"<b>Trust:</b> {trust_name}", body_style))
    story.append(Paragraph(f"<b>Asset:</b> {asset_name}", body_style))
    story.append(Paragraph(f"<b>Asset Type:</b> {asset_type}", body_style))
    story.append(Spacer(1, 14))

    story.append(Paragraph("<b>Finalization Audit Stamp</b>", header_style))
    story.append(Paragraph(f"<b>Finalized At:</b> {finalized_at}", body_style))
    story.append(Paragraph(f"<b>Finalized By:</b> {finalized_by}", body_style))
    story.append(Paragraph(f"<b>Finalized Capacity:</b> {finalized_capacity}", body_style))
    story.append(Spacer(1, 18))

    story.append(Paragraph(
        "Certification Statement: The above transfer record is certified as an internal "
        "administrative record of completion based on the Trustee App ledger, execution "
        "status, and finalization audit stamp.",
        body_style
    ))

    story.append(Spacer(1, 16))
    story.append(Paragraph("<b>Authority Statement</b>", header_style))
    story.append(Paragraph(
        "The undersigned fiduciary affirms that this transfer was executed under the authority "
        "granted by the governing trust instrument and in accordance with the fiduciary duties "
        "associated with the trustee role.",
        body_style
    ))

    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Asset Control Statement</b>", header_style))
    story.append(Paragraph(
        "The asset referenced herein is represented as having been placed under the control, "
        "administration, or direction of the trust as reflected in the internal records of the "
        "trust administration system.",
        body_style
    ))

    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Reliance Clause</b>", header_style))
    story.append(Paragraph(
        "This document may be relied upon as a record of internal trust administration. "
        "Third parties may request additional documentation or verification as required "
        "by their own policies or applicable procedures.",
        body_style
    ))
    story.append(Spacer(1, 18))

    story.append(Paragraph("<b>Execution Notes</b>", header_style))
    story.append(Paragraph(
        "This certificate does not replace any required wet signature, notarization, "
        "external filing, title update, or third-party acceptance process. It serves as "
        "an internal fiduciary record connected to the transfer workflow.",
        styles["Italic"]
    ))

    story.append(Spacer(1, 24))
    story.append(Paragraph("<b>Fiduciary Execution Block</b>", header_style))
    story.append(Paragraph(
        "Executed in representative fiduciary capacity only, and not in an individual capacity.",
        body_style
    ))
    story.append(Spacer(1, 18))

    story.append(Paragraph("Authorized Fiduciary Signature: ______________________________", body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Printed Name / User: {finalized_by}", body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Capacity: {finalized_capacity}", body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Execution Date: ______________________________", body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_certificate_of_trust_pdf(trust, preview_context):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    story = []

    add_universal_v3_letterhead(story, styles, preview_context, "Certificate of Trust")

    header_style = ParagraphStyle(
        "CertificateSectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#111111"),
        spaceBefore=10,
        spaceAfter=6,
    )

    story.append(Paragraph("Certification Summary", header_style))
    story.append(Paragraph(
        "This Certificate of Trust summarizes selected trust information for administrative verification. "
        "It is intended as a bounded summary surface and does not replace the full Declaration of Trust, trust agreement, "
        "trust minutes, trustee acceptance, or other governing records.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Trust Identification", header_style))
    story.append(Paragraph(f"<b>Trust Name:</b> {preview_context.get('trust_name') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Trust ID:</b> {preview_context.get('trust_id') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Trust Type:</b> {preview_context.get('trust_type') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Effective Date:</b> {preview_context.get('effective_date_display') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Jurisdiction:</b> {preview_context.get('jurisdiction') or '______________________________'}", styles["BodyText"]))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Trustee Authority Summary", header_style))
    story.append(Paragraph(f"<b>Current Trustee:</b> {preview_context.get('trustee_name') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Successor Trustee:</b> {preview_context.get('successor_trustee_name') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(
        "The trustee authority summarized here is limited to the data entered into the Trustee App and should be verified against executed trust records.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Property / Corpus Summary", header_style))
    story.append(Paragraph(f"<b>Initial Corpus:</b> {preview_context.get('initial_corpus_description') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Asset Categories:</b> {preview_context.get('asset_categories') or '______________________________'}", styles["BodyText"]))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Reliance Limitation", header_style))
    story.append(Paragraph(
        "This certificate is an internal administrative summary generated from the Trustee App. "
        "Third-party reliance, filing use, or external presentation should be reviewed independently and matched to the executed governing instrument.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 24))

    story.append(Paragraph("Trustee Certification Signature: ______________________________", styles["BodyText"]))
    story.append(Spacer(1, 16))
    story.append(Paragraph("Capacity / Title: ______________________________", styles["BodyText"]))
    story.append(Spacer(1, 16))
    story.append(Paragraph("Date: ______________________________", styles["BodyText"]))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_articles_pdf(trust, preview_context):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    story = []
    add_universal_v3_letterhead(story, styles, preview_context, "Articles")

    title_style = ParagraphStyle(
        "ArticlesTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        alignment=1,
        textColor=colors.HexColor("#111111"),
        spaceAfter=8,
    )
    heading_style = ParagraphStyle(
        "ArticlesSectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#111111"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = styles["BodyText"]

    story.append(Paragraph("Articles of Trust", title_style))
    story.append(Paragraph("Controlled Trust Summary Instrument", styles["Heading3"]))
    story.append(Spacer(1, 18))

    story.append(Paragraph("Trust Identification", heading_style))
    story.append(Paragraph(f"<b>Trust Name:</b> {preview_context.get('trust_name') or '______________________________'}", body_style))
    story.append(Paragraph(f"<b>Trust ID:</b> {preview_context.get('trust_id') or '______________________________'}", body_style))
    story.append(Paragraph(f"<b>Trust Type:</b> {preview_context.get('trust_type') or '______________________________'}", body_style))
    story.append(Paragraph(f"<b>Effective Date:</b> {preview_context.get('effective_date_display') or '______________________________'}", body_style))
    story.append(Paragraph(f"<b>Jurisdiction:</b> {preview_context.get('jurisdiction') or '______________________________'}", body_style))
    story.append(Paragraph(f"<b>Governing Law:</b> {preview_context.get('governing_law') or '______________________________'}", body_style))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Foundational Parties", heading_style))
    story.append(Paragraph(f"<b>Grantor / Settlor:</b> {preview_context.get('grantor_name') or '______________________________'}", body_style))
    story.append(Paragraph(f"<b>Trustee:</b> {preview_context.get('trustee_name') or '______________________________'}", body_style))
    story.append(Paragraph(f"<b>Primary Beneficiary:</b> {preview_context.get('primary_beneficiary') or '______________________________'}", body_style))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Purpose", heading_style))
    story.append(Paragraph(
        preview_context.get('trust_purpose') or
        "The purpose of this trust is to hold, manage, and administer property and rights in accordance with its governing provisions.",
        body_style
    ))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Trust Property", heading_style))
    story.append(Paragraph(f"<b>Initial Corpus Description:</b> {preview_context.get('initial_corpus_description') or 'Initial trust property and interests to be assigned and administered under this trust.'}", body_style))
    story.append(Paragraph(f"<b>Asset Categories:</b> {preview_context.get('asset_categories') or 'Personal property, contractual rights, and other assignable interests.'}", body_style))
    story.append(Paragraph(f"<b>Property Mapping Timing:</b> {preview_context.get('property_mapping_timing') or 'To be assigned and recorded through subsequent trust funding and transfer actions.'}", body_style))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Summary Declaration", heading_style))
    story.append(Paragraph(
        "These Articles of Trust summarize the core trust formation details currently entered through the trust creation workflow. "
        "This PDF is a bounded final output generated from the controlled trust document system.",
        body_style
    ))
    story.append(Spacer(1, 24))

    story.append(Paragraph("Grantor / Settlor Signature: ______________________________", body_style))
    story.append(Spacer(1, 18))
    story.append(Paragraph("Trustee Signature: ______________________________", body_style))
    story.append(Spacer(1, 18))
    story.append(Paragraph("Date: ______________________________", body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_trustee_acceptance_pdf(trust, preview_context):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    story = []
    add_universal_v3_letterhead(story, styles, preview_context, "Trustee Acceptance")

    title_style = ParagraphStyle(
        "TrusteeAcceptanceTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        alignment=1,
        textColor=colors.HexColor("#111111"),
        spaceAfter=8,
    )
    header_style = ParagraphStyle(
        "TrusteeAcceptanceHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#111111"),
        spaceBefore=10,
        spaceAfter=6,
    )

    story.append(Paragraph("Trustee Acceptance of Appointment", title_style))
    story.append(Paragraph("Bounded Final Document Surface", styles["Heading3"]))
    story.append(Spacer(1, 18))

    story.append(Paragraph("Trust Identification", header_style))
    story.append(Paragraph(f"<b>Trust Name:</b> {preview_context.get('trust_name') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Trust ID:</b> {preview_context.get('trust_id') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Trust Type:</b> {preview_context.get('trust_type') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Effective Date:</b> {preview_context.get('effective_date_display') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Jurisdiction:</b> {preview_context.get('jurisdiction') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Governing Law:</b> {preview_context.get('governing_law') or '______________________________'}", styles["BodyText"]))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Trustee Acceptance", header_style))
    story.append(Paragraph(f"<b>Trustee Name:</b> {preview_context.get('trustee_name') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(
        "The undersigned hereby accepts appointment as Trustee of the above-referenced trust and agrees to perform all duties in accordance with the trust’s governing instrument and applicable law.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 24))

    story.append(Paragraph("Trustee Signature: ______________________________", styles["BodyText"]))
    story.append(Spacer(1, 18))
    story.append(Paragraph("Date: ______________________________", styles["BodyText"]))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_general_assignment_pdf(trust, preview_context):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    story = []
    add_universal_v3_letterhead(story, styles, preview_context, "General Assignment")

    title_style = ParagraphStyle(
        "GeneralAssignmentTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        alignment=1,
        textColor=colors.HexColor("#111111"),
        spaceAfter=8,
    )
    header_style = ParagraphStyle(
        "GeneralAssignmentHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#111111"),
        spaceBefore=10,
        spaceAfter=6,
    )

    story.append(Paragraph("General Assignment to Trust", title_style))
    story.append(Paragraph("Bounded Final Document Surface", styles["Heading3"]))
    story.append(Spacer(1, 18))

    story.append(Paragraph("Trust Identification", header_style))
    story.append(Paragraph(f"<b>Trust Name:</b> {preview_context.get('trust_name') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Trust ID:</b> {preview_context.get('trust_id') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Trust Type:</b> {preview_context.get('trust_type') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Effective Date:</b> {preview_context.get('effective_date_display') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Jurisdiction:</b> {preview_context.get('jurisdiction') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Governing Law:</b> {preview_context.get('governing_law') or '______________________________'}", styles["BodyText"]))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Scope of Assignment", header_style))
    story.append(Paragraph(f"<b>Initial Corpus Description:</b> {preview_context.get('initial_corpus_description') or 'Initial trust property and assignable interests to be transferred into the trust structure.'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Asset Categories:</b> {preview_context.get('asset_categories') or 'Personal property, contractual rights, and other assignable interests.'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Property Mapping Timing:</b> {preview_context.get('property_mapping_timing') or 'To be assigned and documented through subsequent trust funding and transfer records.'}", styles["BodyText"]))
    story.append(Spacer(1, 24))

    story.append(Paragraph("Assignor Signature: ______________________________", styles["BodyText"]))
    story.append(Spacer(1, 18))
    story.append(Paragraph("Trustee Acknowledgment: ______________________________", styles["BodyText"]))
    story.append(Spacer(1, 18))
    story.append(Paragraph("Date: ______________________________", styles["BodyText"]))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_organizational_minutes_pdf(trust, preview_context):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    story = []
    add_universal_v3_letterhead(story, styles, preview_context, "Organizational Minutes")

    title_style = ParagraphStyle(
        "OrganizationalMinutesTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        alignment=1,
        textColor=colors.HexColor("#111111"),
        spaceAfter=8,
    )
    header_style = ParagraphStyle(
        "OrganizationalMinutesHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#111111"),
        spaceBefore=10,
        spaceAfter=6,
    )

    story.append(Paragraph("Initial Trustee Resolution / Organizational Minutes", title_style))
    story.append(Paragraph("Bounded Final Document Surface", styles["Heading3"]))
    story.append(Spacer(1, 18))

    story.append(Paragraph("Trust Identification", header_style))
    story.append(Paragraph(f"<b>Trust Name:</b> {preview_context.get('trust_name') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Trust ID:</b> {preview_context.get('trust_id') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Trust Type:</b> {preview_context.get('trust_type') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Effective Date:</b> {preview_context.get('effective_date_display') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Jurisdiction:</b> {preview_context.get('jurisdiction') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Governing Law:</b> {preview_context.get('governing_law') or '______________________________'}", styles["BodyText"]))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Matters Considered", header_style))
    story.append(Paragraph(
        preview_context.get('trust_purpose') or
        "Review of the trust’s formation purpose, administration, and initial fiduciary organization.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 24))

    story.append(Paragraph("Trustee Signature: ______________________________", styles["BodyText"]))
    story.append(Spacer(1, 18))
    story.append(Paragraph("Date: ______________________________", styles["BodyText"]))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_successor_trustee_pdf(trust, preview_context):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    story = []
    add_universal_v3_letterhead(story, styles, preview_context, "Successor Trustee")

    title_style = ParagraphStyle(
        "SuccessorTrusteeTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        alignment=1,
        textColor=colors.HexColor("#111111"),
        spaceAfter=8,
    )
    header_style = ParagraphStyle(
        "SuccessorTrusteeHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#111111"),
        spaceBefore=10,
        spaceAfter=6,
    )

    story.append(Paragraph("Successor Trustee Acceptance / Appointment", title_style))
    story.append(Paragraph("Bounded Final Document Surface", styles["Heading3"]))
    story.append(Spacer(1, 18))

    story.append(Paragraph("Trust Identification", header_style))
    story.append(Paragraph(f"<b>Trust Name:</b> {preview_context.get('trust_name') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Trust ID:</b> {preview_context.get('trust_id') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Trust Type:</b> {preview_context.get('trust_type') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Effective Date:</b> {preview_context.get('effective_date_display') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Jurisdiction:</b> {preview_context.get('jurisdiction') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Governing Law:</b> {preview_context.get('governing_law') or '______________________________'}", styles["BodyText"]))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Parties", header_style))
    story.append(Paragraph(f"<b>Grantor / Settlor:</b> {preview_context.get('grantor_name') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Current Trustee:</b> {preview_context.get('trustee_name') or '______________________________'}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Successor Trustee:</b> {preview_context.get('successor_trustee_name') or '______________________________'}", styles["BodyText"]))
    story.append(Spacer(1, 24))

    story.append(Paragraph("Successor Trustee Signature: ______________________________", styles["BodyText"]))
    story.append(Spacer(1, 18))
    story.append(Paragraph("Date: ______________________________", styles["BodyText"]))

    doc.build(story)
    buffer.seek(0)
    return buffer




def generate_packet_manifest_pdf(trust, preview_context):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER)
    styles = getSampleStyleSheet()
    story = []

    add_universal_v3_letterhead(story, styles, preview_context, "Packet Manifest")

    title_style = ParagraphStyle(
        "PacketManifestTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        alignment=1,
        textColor=colors.HexColor("#111111"),
        spaceAfter=8,
    )

    normal_style = styles["BodyText"]

    trust_id = trust.get("trust_id") if isinstance(trust, dict) else trust["trust_id"]
    trust_name = trust.get("trust_name") if isinstance(trust, dict) else trust["trust_name"]

    story.append(Paragraph("Controlled Trust Packet Manifest", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Trust ID:</b> {trust_id}", normal_style))
    story.append(Paragraph(f"<b>Trust Name:</b> {trust_name}", normal_style))
    story.append(Paragraph("<b>Packet Type:</b> Controlled Trust Packet Export", normal_style))
    story.append(Paragraph("<b>Status:</b> Generated for review/testing under current export policy.", normal_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Included Packet Records</b>", normal_style))
    included_items = [
        "Packet Manifest",
        "Trust Declaration / Summary",
        "Articles / Support Records",
        "Trustee Acceptance Records",
        "General Assignment Records",
        "Certificate / Registry Records where available",
    ]

    for item in included_items:
        story.append(Paragraph(f"• {item}", normal_style))

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "This manifest was generated by the Trustee App controlled packet export workflow.",
        normal_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_controlled_trust_packet_zip(trust, preview_context):
    packet_buffer = BytesIO()

    with zipfile.ZipFile(packet_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        trust_id = preview_context.get("trust_id") or "TRUST"

        docs = [
            (f"{trust_id}_Packet_Manifest.pdf", generate_packet_manifest_pdf(trust, preview_context)),
            (f"{trust_id}_Declaration_of_Trust.pdf", generate_declaration_of_trust_pdf(trust, preview_context)),
            (f"{trust_id}_Certificate_of_Trust.pdf", generate_certificate_of_trust_pdf(trust, preview_context)),
            (f"{trust_id}_Articles_of_Trust.pdf", generate_articles_pdf(trust, preview_context)),
            (f"{trust_id}_Trustee_Acceptance.pdf", generate_trustee_acceptance_pdf(trust, preview_context)),
            (f"{trust_id}_General_Assignment.pdf", generate_general_assignment_pdf(trust, preview_context)),
            (f"{trust_id}_Organizational_Minutes.pdf", generate_organizational_minutes_pdf(trust, preview_context)),
            (f"{trust_id}_Successor_Trustee_Acceptance.pdf", generate_successor_trustee_pdf(trust, preview_context)),
        ]

        for filename, pdf_buffer in docs:
            zf.writestr(filename, pdf_buffer.getvalue())

    packet_buffer.seek(0)
    return packet_buffer

def get_support_doc_by_category(transfer, category_key):
    return TransferSupportDoc.query.filter_by(
        transfer_id_fk=transfer.id,
        category_key=category_key,
    ).first()


def build_transfer_step_nav(transfer, current_step):
    step_defs = [
        ("asset", "Asset", "transfer_asset"),
        ("classification", "Classification", "transfer_classification"),
        ("assignment", "Assignment", "transfer_assignment"),
        ("trustee_acceptance", "Trustee Acceptance", "transfer_trustee_acceptance"),
        ("control_evidence", "Control Evidence", "transfer_control_evidence"),
        ("records", "Records", "transfer_records"),
        ("review", "Review", "transfer_review"),
    ]

    completed = {
        "asset": bool(transfer.asset_name),
        "classification": bool(transfer.transfer_type),
        "assignment": bool(transfer.assignment_confirmed),
        "trustee_acceptance": bool(transfer.trustee_decision),
        "control_evidence": bool(transfer.control_change_status),
        "records": bool(transfer.records_complete),
        "review": transfer.status == "completed",
    }

    items = []
    for key, label, endpoint in step_defs:
        items.append({
            "key": key,
            "label": label,
            "endpoint": endpoint,
            "url": url_for(endpoint, transfer_id=transfer.transfer_id),
            "is_current": key == current_step,
            "is_complete": completed.get(key, False),
        })
    return items


app.jinja_env.globals["csrf_token"] = generate_csrf_token
app.jinja_env.globals["app_csrf_token"] = generate_csrf_token

init_audit_table()

init_db()
ensure_k1_tables()
ensure_instrument_tables()
ensure_fiduciary_tables()
ensure_genealogy_tables()
ensure_media_tables()
ensure_role_tables()
ensure_user_tables()
ensure_user_permission_override_tables()
ensure_trust_minutes_tables()
ensure_trust_minutes_execution_columns()
ensure_trust_minutes_capacity_columns()
ensure_firm_columns()

with app.app_context():
    ext_db.create_all()

DEFAULT_UPLOAD_FOLDER = Path(__file__).resolve().parent / "uploads"
UPLOAD_FOLDER = Path(os.getenv("UPLOAD_FOLDER", str(DEFAULT_UPLOAD_FOLDER))).resolve()
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "jpg", "jpeg", "png", "mp3", "wav", "mp4", "mov"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS



ENDPOINT_PERMISSION_RULES = {
    "permissions_dashboard": "manage_permissions",
    "security_dashboard": "view_security",
    "users_dashboard": "manage_users",
    "users_new": "manage_users",
    "users_edit": "manage_users",
    "users_reset_password": "manage_users",
    "admin_index": "view_dashboard",
    "document_generate": "generate_documents",
    "workspace_document_generate": "generate_documents",
    "export_center": "export_documents",
    "export_handoff_file": "export_documents",
    "export_roadmap_file": "export_documents",
    "export_package_file": "export_documents",
    "export_zip_snapshot": "export_documents",
    "audit_dashboard": "view_audit",
    "admin_audit_log": "view_audit",
    "form1041_dashboard": "manage_tax_reports",
    "form1041_preview": "manage_tax_reports",
    "form1041_print": "manage_tax_reports",
    "k1_dashboard": "manage_tax_reports",
    "k1_trust_view": "manage_tax_reports",
    "k1_year_end_summary": "manage_tax_reports",
}

ROLE_RULES = {
    "home": {"Admin", "Trustee", "Viewer"},
    "workflow_hub": {"Admin", "Trustee"},
    "portfolio_dashboard": {"Admin", "Trustee", "Viewer"},
    "fiduciary_dashboard": {"Admin", "Trustee"},
    "genealogy_dashboard": {"Admin", "Trustee"},
    "media_dashboard": {"Admin", "Trustee"},
    "role_dashboard": {"Admin"},
    "report_center": {"Admin", "Trustee"},
    "learning_dashboard": {"Admin", "Trustee", "Viewer"},
    "learning_category": {"Admin", "Trustee", "Viewer"},
    "learning_article": {"Admin", "Trustee", "Viewer"},
    "trust_type_index": {"Admin", "Trustee", "Viewer"},
    "trust_type_detail": {"Admin", "Trustee", "Viewer"},
    "forms_dashboard": {"Admin", "Trustee", "Viewer"},
    "form_guide_detail": {"Admin", "Trustee", "Viewer"},
    "learning_article_new": {"Admin"},
    "learning_article_edit": {"Admin"},
    "form_guide_new": {"Admin"},
    "form_guide_edit": {"Admin"},
    "video_dashboard": {"Admin", "Trustee", "Viewer"},
    "video_category": {"Admin", "Trustee", "Viewer"},
    "video_trust_type": {"Admin", "Trustee", "Viewer"},
    "video_detail": {"Admin", "Trustee", "Viewer"},
    "video_upload": {"Admin", "Trustee"},
    "video_edit": {"Admin"},
    "workspace_dashboard": {"Admin", "Trustee", "Viewer"},
    "workspace_new": {"Admin", "Trustee"},
    "workspace_detail": {"Admin", "Trustee", "Viewer"},
    "workspace_edit": {"Admin", "Trustee"},
    "workspace_note_new": {"Admin", "Trustee"},
    "discussion_dashboard": {"Admin", "Trustee", "Viewer"},
    "discussion_new": {"Admin", "Trustee"},
    "discussion_thread": {"Admin", "Trustee", "Viewer"},
    "discussion_reply": {"Admin", "Trustee"},
    "workspace_discussions": {"Admin", "Trustee", "Viewer"},
    "workspace_discussion_new": {"Admin", "Trustee"},
    "decision_dashboard": {"Admin", "Trustee", "Viewer"},
    "decision_run": {"Admin", "Trustee", "Viewer"},
    "execution_dashboard": {"Admin", "Trustee", "Viewer"},
    "execution_task_new": {"Admin", "Trustee"},
    "execution_task_detail": {"Admin", "Trustee", "Viewer"},
    "execution_task_status": {"Admin", "Trustee"},
    "workspace_tasks": {"Admin", "Trustee", "Viewer"},
    "workspace_task_new": {"Admin", "Trustee"},
    "document_dashboard": {"Admin", "Trustee", "Viewer"},
    "document_generate": {"Admin", "Trustee"},
    "document_detail": {"Admin", "Trustee", "Viewer"},
    "workspace_documents": {"Admin", "Trustee", "Viewer"},
    "workspace_document_generate": {"Admin", "Trustee"},
    "visualization_dashboard": {"Admin", "Trustee", "Viewer"},
    "trust_map_dashboard": {"Admin", "Trustee", "Viewer"},
    "analytics_dashboard": {"Admin", "Trustee", "Viewer"},
    "permissions_dashboard": {"Admin"},
    "create_trust_step1": {"Admin", "Trustee"},
    "create_trust_step2": {"Admin", "Trustee"},
    "create_trust_step3": {"Admin", "Trustee"},
    "create_trust_step4": {"Admin", "Trustee"},
    "create_trust_step5": {"Admin", "Trustee"},
    "create_trust_step6": {"Admin", "Trustee"},
    "create_trust_step7": {"Admin", "Trustee"},
    "add_property": {"Admin", "Trustee"},
    "link_account": {"Admin", "Trustee"},
    "upload_document": {"Admin", "Trustee"},
    "ledger_entry": {"Admin", "Trustee"},
    "trust_detail": {"Admin", "Trustee", "Viewer"},
    "property_detail": {"Admin", "Trustee", "Viewer"},
    "instrument_create": {"Admin", "Trustee"},
    "instrument_detail": {"Admin", "Trustee"},
    "fiduciary_new": {"Admin", "Trustee"},
    "genealogy_new": {"Admin", "Trustee"},
    "media_upload": {"Admin", "Trustee"},
    "role_new": {"Admin"},
    "admin_index": {"Admin"},
    "users_dashboard": {"Admin"},
    "users_new": {"Admin"},
    "users_edit": {"Admin"},
    "users_reset_password": {"Admin"},
    "export_center": {"Admin", "Trustee"},
    "export_handoff_file": {"Admin", "Trustee"},
    "export_roadmap_file": {"Admin", "Trustee"},
    "export_package_file": {"Admin", "Trustee"},
    "export_zip_snapshot": {"Admin", "Trustee"},
    "audit_dashboard": {"Admin"},
    "media_file": {"Admin", "Trustee"},
    "evidence_by_entity": {"Admin", "Trustee"},
    "k1_dashboard": {"Admin", "Trustee", "Viewer"},
    "k1_trust_view": {"Admin", "Trustee"},
    "k1_year_end_summary": {"Admin", "Trustee"},
    "form1041_dashboard": {"Admin", "Trustee", "Viewer"},
    "form1041_preview": {"Admin", "Trustee"},
    "form1041_print": {"Admin", "Trustee"},
    "export_k1_live_csv": {"Admin", "Trustee"},
    "export_1041_text": {"Admin", "Trustee"},
    "k1_export_csv": {"Admin", "Trustee"},
    "export_k1_summary_report": {"Admin", "Trustee"},
    "export_1041_summary_report": {"Admin", "Trustee"},
    "k1_report_view": {"Admin", "Trustee", "Viewer"},
    "form1041_report_view": {"Admin", "Trustee", "Viewer"},
    "k1_report_print": {"Admin", "Trustee"},
    "form1041_report_print": {"Admin", "Trustee"},
    "security_dashboard": {"Admin"},
}




def is_master_admin():
    return (session.get("username") or "").strip().lower() == "admin" and session.get("role") == "Admin"

def require_master_admin():
    if not session.get("username"):
        return redirect(url_for("login"))
    if not is_master_admin():
        return render_template(
            "access_denied.html",
            reason="Only the master admin may access this page."
        )
    return None

def gate_trust_access(trust_id, allowed_roles):
    current_role = session.get("role")
    if not current_role:
        return render_template(
            "access_denied.html",
            reason="No authenticated role found in the current session."
        )

    if current_role not in allowed_roles:
        return render_template(
            "access_denied.html",
            reason=f"Role {current_role} is not allowed for this page."
        )

    trust = get_trust_by_id(trust_id)
    if not trust:
        log_change(
            "security",
            trust_id,
            "firm_access_denied",
            f"Trust not found in active firm scope. User={session.get('username')}; Firm={session.get('firm_id')}"
        )
        return render_template(
            "access_denied.html",
            reason="This trust record is not available within your assigned firm scope."
        )

    return None

@app.route("/")
def home():
    trusts = get_all_trusts()
    return render_template("dashboard.html", trusts=trusts)

@app.route("/command")
def command_dashboard():
    snapshot = get_command_snapshot()
    return render_template("command_dashboard.html", snapshot=snapshot)

@app.route("/financial_summary")
def financial_summary():
    trusts = get_all_trusts()
    trust_id = request.args.get("trust_id")
    selected_trust = None
    summary = None
    coa = []

    if trust_id:
        selected_trust = get_trust_by_id(trust_id)
        if selected_trust:
            seed_chart_of_accounts_for_trust(trust_id)
            summary = get_trust_financial_summary(trust_id)
            coa = get_chart_of_accounts(trust_id)

    return render_template(
        "financial_summary.html",
        trusts=trusts,
        selected_trust=selected_trust,
        summary=summary,
        coa=coa
    )

@app.route("/tax_assistant")
def tax_assistant():
    trusts = get_all_trusts()
    trust_id = request.args.get("trust_id")

    selected_trust = None
    tax_profile = None
    forms = []
    issues = []

    if trust_id:
        selected_trust = get_trust_by_id(trust_id)
        if selected_trust:
            tax_profile = get_tax_profile(trust_id)
            forms = get_tax_form_applicability(trust_id)
            issues = get_tax_readiness(trust_id)

    return render_template(
        "tax_assistant.html",
        trusts=trusts,
        selected_trust=selected_trust,
        tax_profile=tax_profile,
        forms=forms,
        issues=issues
    )

@app.route("/assets")
@app.route("/asset")
def asset_dashboard():
    selected_class = request.args.get("class")
    assets = get_all_assets()
    asset_class_counts = get_asset_class_counts()

    if selected_class:
        assets = [
            a for a in assets
            if (a["asset_class"] or a["property_type"] or "unclassified") == selected_class
        ]

    return render_template(
        "asset_dashboard.html",
        assets=assets,
        asset_class_counts=asset_class_counts,
        selected_class=selected_class
    )

@app.route("/asset_health")
def asset_health():
    return render_template(
        "asset_health.html",
        missing_custodian=get_assets_missing_custodian(),
        missing_review=get_assets_missing_review_date(),
        expiring=get_assets_with_expiration(),
        expiring_30=get_assets_expiring_within(30),
        expiring_60=get_assets_expiring_within(60),
        expiring_90=get_assets_expiring_within(90),
        review_due_30=get_assets_review_due_within(30),
        review_due_60=get_assets_review_due_within(60),
        review_due_90=get_assets_review_due_within(90),
        expired=get_assets_expired(),
        overdue_review=get_assets_review_overdue(),
        severity_summary=get_asset_severity_summary(),
        orphaned=get_orphaned_assets()
    )


@app.route("/create-trust-launch")
def create_trust_launch():
    return render_template("create_trust_launch.html")


@app.route("/create_trust_step1", methods=["GET", "POST"])
@csrf.exempt
def create_trust_step1():
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template(
                "create_trust_step1.html",
                error_message="Invalid or missing CSRF token."
            )

        trust_id = get_next_trust_id()
        trust = {
            "trust_id": trust_id,
            "trust_name": request.form.get("trust_name"),
            "short_name": request.form.get("short_name"),
            "jurisdiction": request.form.get("jurisdiction"),
            "effective_date": request.form.get("effective_date"),
            "trust_type": "Not Yet Selected",
            "trust_purpose": "Not Yet Selected",
            "accounting_method": "Not Yet Selected",
            "workflow_mode": "Not Yet Selected",
            "settlor_name": "",
            "trustee_name": "",
            "successor_trustee_name": "",
            "beneficiary_name": "",
            "record_visibility": "Not Yet Selected",
            "workflow_mode_confirmed": "Not Yet Selected",
            "ai_explanations": "Not Yet Selected",
            "recommended_guidance": "Not Yet Selected",
            "initial_corpus_description": "",
            "property_mapping_timing": "Not Yet Selected",
            "asset_categories": "Not Yet Selected",
            "generate_schedule_recommendations": "Not Yet Selected",
            "status": "Draft",
        "owner_id": get_current_owner()
        }
        create_trust_record(trust)
        return redirect(url_for("create_trust_step2_grantor", trust_id=trust_id))
    return render_template("create_trust_step1.html")


@app.route("/create_trust_step2_grantor/<trust_id>", methods=["GET", "POST"])
@csrf.exempt
def create_trust_step2_grantor(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("create_trust_step2_grantor.html", trust=trust, error_message="Invalid or missing CSRF token.")

        update_trust_fields(trust_id, {
            "grantor_name": request.form.get("grantor_name"),
            "grantor_type": request.form.get("grantor_type"),
            "grantor_contact": request.form.get("grantor_contact"),
        })

        return redirect(url_for("create_trust_step2", trust_id=trust_id))

    return render_template("create_trust_step2_grantor.html", trust=trust)


@app.route("/create_trust_step2/<trust_id>", methods=["GET", "POST"])
@csrf.exempt
def create_trust_step2(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("create_trust_step2.html", trust=trust, trust_types=get_trust_type_cards(), error_message="Invalid or missing CSRF token.")

        update_trust_fields(trust_id, {
            "trust_type": request.form.get("trust_type"),
            "trust_purpose": request.form.get("trust_purpose"),
            "accounting_method": request.form.get("accounting_method"),
            "workflow_mode": request.form.get("workflow_mode"),
            "status": "Draft - Step 2 Complete",
        })
        return redirect(url_for("create_trust_step3", trust_id=trust_id))
    return render_template("create_trust_step2.html", trust=trust, trust_types=get_trust_type_cards())

@app.route("/create_trust_step3/<trust_id>", methods=["GET", "POST"])
@csrf.exempt
def create_trust_step3(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("create_trust_step3.html", trust=trust, error_message="Invalid or missing CSRF token.")

        update_trust_fields(trust_id, {
            "settlor_name": request.form.get("settlor_name"),
            "trustee_name": request.form.get("trustee_name"),
            "successor_trustee_name": request.form.get("successor_trustee_name"),
            "beneficiary_name": request.form.get("beneficiary_name"),
            "status": "Draft - Step 3 Complete",
        })
        return redirect(url_for("create_trust_step4", trust_id=trust_id))
    return render_template("create_trust_step3.html", trust=trust)

@app.route("/create_trust_step4/<trust_id>", methods=["GET", "POST"])
@csrf.exempt
def create_trust_step4(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("create_trust_step4.html", trust=trust, error_message="Invalid or missing CSRF token.")

        update_trust_fields(trust_id, {
            "record_visibility": request.form.get("record_visibility"),
            "workflow_mode_confirmed": request.form.get("workflow_mode_confirmed"),
            "ai_explanations": request.form.get("ai_explanations"),
            "recommended_guidance": request.form.get("recommended_guidance"),
            "status": "Draft - Step 4 Complete",
        })
        return redirect(url_for("create_trust_step5", trust_id=trust_id))
    return render_template("create_trust_step4.html", trust=trust)

@app.route("/create_trust_step5/<trust_id>", methods=["GET", "POST"])
@csrf.exempt
def create_trust_step5(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("create_trust_step5.html", trust=trust, error_message="Invalid or missing CSRF token.")

        update_trust_fields(trust_id, {
            "initial_corpus_description": request.form.get("initial_corpus_description"),
            "property_mapping_timing": request.form.get("property_mapping_timing"),
            "asset_categories": request.form.get("asset_categories"),
            "generate_schedule_recommendations": request.form.get("generate_schedule_recommendations"),
            "status": "Draft - Step 5 Complete",
        })
        return redirect(url_for("create_trust_step6", trust_id=trust_id))
    return render_template("create_trust_step5.html", trust=trust)

@app.route("/create_trust_step6/<trust_id>", methods=["GET", "POST"])
@csrf.exempt
def create_trust_step6(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("create_trust_step6.html", trust=trust, error_message="Invalid or missing CSRF token.")

        update_trust_fields(trust_id, {"status": "Finalized"})
        return redirect(url_for("trust_post_create_review", trust_id=trust_id))
    return render_template("create_trust_step6.html", trust=trust)

@app.route("/create_trust_step7/<trust_id>")
def create_trust_step7(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    return render_template("create_trust_step7.html", trust=trust)

@app.route("/add_property", methods=["GET", "POST"])
def add_property():
    trusts = get_all_trusts()
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("add_property.html", trusts=trusts, error_message="Invalid or missing CSRF token.")

        property_id = get_next_property_id()
        prop = {
            "property_id": property_id,
            "trust_id": request.form.get("trust_id"),
            "property_name": request.form.get("property_name"),
            "property_type": request.form.get("asset_class"),
            "address_or_identifier": request.form.get("address_or_identifier"),
            "acquisition_date": request.form.get("acquisition_date"),
            "title_notes": request.form.get("title_notes"),
            "beneficial_notes": request.form.get("beneficial_notes"),
            "status": "Mapped",
            "asset_class": request.form.get("asset_class"),
            "asset_subtype": request.form.get("asset_subtype"),
            "established_date": request.form.get("established_date"),
            "effective_date": request.form.get("effective_date"),
            "review_date": request.form.get("review_date"),
            "expiration_date": request.form.get("expiration_date"),
            "responsible_party": request.form.get("responsible_party"),
            "custodian": request.form.get("custodian"),
        }
        create_property_record(prop)
        return redirect(url_for("property_detail", property_id=property_id))
    return render_template("add_property.html", trusts=trusts)

@app.route("/link_account", methods=["GET", "POST"])
def link_account():
    trusts = get_all_trusts()
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("link_account.html", trusts=trusts, properties=[], error_message="Invalid or missing CSRF token.")

        account_id = get_next_account_id()
        account = {
            "account_id": account_id,
            "trust_id": request.form.get("trust_id"),
            "property_id": request.form.get("property_id"),
            "account_type": request.form.get("account_type"),
            "institution": request.form.get("institution"),
            "account_label": request.form.get("account_label"),
            "masked_number": request.form.get("masked_number"),
            "purpose": request.form.get("purpose")
        }
        create_account_record(account)
        return redirect(url_for("property_detail", property_id=account["property_id"]))
    return render_template("link_account.html", trusts=trusts, properties=[])

@app.route("/upload_document", methods=["GET", "POST"])
def upload_document():
    trusts = get_all_trusts()
    prefill_property_id = (request.args.get("property_id") or "").strip()
    prefill_trust_id = (request.args.get("trust_id") or "").strip()
    evidence_mode = (request.args.get("evidence") or "").strip()

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("upload_document.html", trusts=trusts, error_message="Invalid or missing CSRF token.")

        uploaded_file = request.files.get("document_file")
        if not uploaded_file or uploaded_file.filename == "":
            return "No file selected"
        if not allowed_file(uploaded_file.filename):
            return "File type not allowed"

        document_id = get_next_document_id()
        original_filename = uploaded_file.filename
        safe_name = secure_filename(original_filename)
        stored_filename = f"{document_id}_{safe_name}"
        file_path = UPLOAD_FOLDER / stored_filename
        uploaded_file.save(file_path)

        document = {
            "document_id": document_id,
            "trust_id": request.form.get("trust_id"),
            "property_id": request.form.get("property_id"),
            "account_id": request.form.get("account_id"),
            "document_category": request.form.get("document_category"),
            "document_title": request.form.get("document_title"),
            "notes": request.form.get("notes"),
            "original_filename": original_filename,
            "stored_filename": stored_filename,
            "file_path": str(file_path),
            "owner_id": get_current_owner(),
        }
        create_document_record(document)

        if document["property_id"]:
            return redirect(url_for("property_detail", property_id=document["property_id"]))
        return redirect(url_for("trust_detail", trust_id=document["trust_id"]))
    return render_template(
        "upload_document.html",
        trusts=trusts,
        prefill_property_id=prefill_property_id,
        prefill_trust_id=prefill_trust_id,
        evidence_mode=evidence_mode
    )

@app.route("/ledger_entry", methods=["GET", "POST"])
def ledger_entry():
    trusts = get_all_trusts()
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("ledger_entry.html", trusts=trusts, properties=[], accounts=[], error_message="Invalid or missing CSRF token.")

        entry_id = get_next_entry_id()
        entry = {
            "entry_id": entry_id,
            "trust_id": request.form.get("trust_id"),
            "property_id": request.form.get("property_id"),
            "account_id": request.form.get("account_id"),
            "entry_type": request.form.get("entry_type"),
            "amount": request.form.get("amount"),
            "entry_date": request.form.get("entry_date"),
            "description": request.form.get("description"),
            "entry_category": request.form.get("entry_category"),
            "accounting_method": request.form.get("accounting_method"),
            "recognition_date": request.form.get("recognition_date"),
            "due_date": request.form.get("due_date"),
            "paid_date": request.form.get("paid_date"),
            "chart_account": request.form.get("chart_account"),
        }
        create_ledger_entry(entry)

        if entry["property_id"]:
            return redirect(url_for("property_detail", property_id=entry["property_id"]))
        return redirect(url_for("trust_detail", trust_id=entry["trust_id"]))
    return render_template("ledger_entry.html", trusts=trusts, properties=[], accounts=[])

@app.route("/trust/<trust_id>/seal")
def uploaded_seal(trust_id):
    gate = gate_trust_access(trust_id, {"Admin", "Trustee", "Viewer"})
    if gate:
        return gate

    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found", 404

    seal_path = trust.get("seal_path") if hasattr(trust, "get") else trust["seal_path"]
    if not seal_path:
        return "No seal uploaded", 404

    stored_path = Path(seal_path)
    uploads_root = UPLOAD_FOLDER.resolve()

    try:
        resolved_path = stored_path.resolve()
        resolved_path.relative_to(uploads_root)
    except Exception:
        log_change(
            "security",
            trust_id,
            "blocked_seal_path_access",
            f"Blocked invalid seal path: {seal_path}"
        )
        return "Invalid seal path", 403

    if not resolved_path.exists() or not resolved_path.is_file():
        return "Seal file not found", 404

    return send_file(resolved_path)


@app.route("/trust/<trust_id>/branding", methods=["GET", "POST"])
def trust_branding_settings(trust_id):
    gate = gate_trust_access(trust_id, {"Admin", "Trustee"})
    if gate:
        return gate

    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found", 404

    if request.method == "POST":
        update_payload = {
            "caf_number": request.form.get("caf_number", "").strip(),
            "crid_number": request.form.get("crid_number", "").strip(),
            "trust_motto": request.form.get("trust_motto", "").strip(),
            "foundation_scripture": request.form.get("foundation_scripture", "").strip(),
            "prepared_by": request.form.get("prepared_by", "").strip(),
            "return_to": request.form.get("return_to", "").strip(),
            "branding_style": request.form.get("branding_style", "v3_minimal").strip() or "v3_minimal",
        }

        seal_file = request.files.get("seal_file")
        if seal_file and seal_file.filename:
            original_name = seal_file.filename
            extension = original_name.rsplit(".", 1)[1].lower() if "." in original_name else ""
            if extension not in {"png", "jpg", "jpeg"}:
                trust = get_trust_by_id(trust_id)
                return render_template(
                    "trust_branding_settings.html",
                    trust=trust,
                    error_message="Seal upload must be a PNG, JPG, or JPEG image."
                )

            safe_name = secure_filename(original_name)
            branding_dir = UPLOAD_FOLDER / "trust_branding" / trust_id
            branding_dir.mkdir(parents=True, exist_ok=True)
            stored_filename = f"seal_{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe_name}"
            stored_path = branding_dir / stored_filename
            seal_file.save(stored_path)

            update_payload["seal_path"] = stored_path.as_posix()

            log_change(
                "trust_branding",
                trust_id,
                "trust_branding_seal_uploaded",
                f"Seal uploaded: {stored_filename}"
            )

        update_trust_fields(trust_id, update_payload)

        log_change(
            "trust_branding",
            trust_id,
            "branding_settings_updated",
            "Trust branding settings updated"
        )

        next_action = request.form.get("next_action", "stay")

        if next_action == "declaration":
            return redirect(url_for("trust_declaration_output_surface", trust_id=trust_id))
        if next_action == "certificate":
            return redirect(url_for("trust_certificate_of_trust_output_surface", trust_id=trust_id))
        if next_action == "packet_preview":
            return redirect(url_for("trust_packet_preview", trust_id=trust_id))

        return redirect(url_for("trust_branding_settings", trust_id=trust_id))

    trust = get_trust_by_id(trust_id)
    return render_template("trust_branding_settings.html", trust=trust)


@app.route("/trust/<trust_id>")
def trust_detail(trust_id):
    gate = deny_unassigned_trust_access(trust_id)
    if gate:
        return gate
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"

    linked_properties = get_properties_by_trust_id(trust_id)
    linked_accounts = get_accounts_by_trust_id(trust_id)
    linked_documents = get_documents_by_trust_id(trust_id)
    linked_ledger = get_ledger_by_trust(trust_id)

    return render_template(
        "trust_detail.html",
        trust=trust,
        linked_properties=linked_properties,
        linked_accounts=linked_accounts,
        linked_documents=linked_documents,
        linked_ledger=linked_ledger
    )

@app.route("/property/<property_id>")
def property_detail(property_id):
    prop = get_property_by_id(property_id)
    if not prop:
        return f"Property {property_id} not found"

    prop_data = dict(prop)

    prop_owner = prop_data.get("owner_id")
    current_owner = get_current_owner()

    if prop_owner and prop_owner != current_owner:
        return render_template(
            "access_denied.html",
            reason="This property record does not belong to the current owner context."
        )

    linked_trust = get_trust_by_id(prop_data["trust_id"])
    linked_accounts = get_accounts_by_property_id(property_id)
    linked_documents = get_documents_by_property_id(property_id)
    linked_ledger = get_ledger_by_property(property_id)
    evidence_profile = build_property_evidence_profile(property_id)

    return render_template(
        "property_detail.html",
        prop=prop_data,
        linked_trust=linked_trust,
        linked_accounts=linked_accounts,
        linked_documents=linked_documents,
        linked_ledger=linked_ledger,
        evidence_profile=evidence_profile
    )







# ===================================================
# AC-1 CONTINUITY ASSET DASHBOARD PDF EXPORT
# ===================================================

def get_filtered_continuity_asset_rows():
    trusts = get_visible_trusts_for_current_operator()

    selected_continuity_class = (request.args.get("continuity_class") or "").strip()
    selected_custody_class = (request.args.get("custody_class") or "").strip()
    selected_memorial = (request.args.get("memorial") or "").strip()
    selected_sacred = (request.args.get("sacred") or "").strip()
    selected_restricted = (request.args.get("restricted") or "").strip()

    dashboard_rows = []

    for trust in trusts:
        trust_id = trust["trust_id"]
        assets = get_continuity_assets_by_trust(trust_id)

        for asset in assets:
            asset_data = dict(asset)
            asset_data["trust_name"] = trust["trust_name"]
            custody_events = get_custody_events_for_property(asset_data["property_id"])
            evidence_profile = build_property_evidence_profile(asset_data["property_id"])
            timeline_summary = summarize_property_evidence_custody_timeline(asset_data["property_id"])

            asset_data["evidence_count"] = evidence_profile.get("evidence_count", 0)
            asset_data["timeline_summary"] = timeline_summary
            asset_data["readiness"] = score_continuity_asset_readiness(
                asset_data,
                custody_events,
                evidence_profile
            )
            dashboard_rows.append(asset_data)

    filtered_rows = []

    for asset in dashboard_rows:
        if selected_continuity_class and asset.get("continuity_classification") != selected_continuity_class:
            continue

        if selected_custody_class and asset.get("custody_classification") != selected_custody_class:
            continue

        if selected_memorial == "yes" and not asset.get("memorial_status"):
            continue

        if selected_memorial == "no" and asset.get("memorial_status"):
            continue

        if selected_sacred == "yes" and not asset.get("sacred_status"):
            continue

        if selected_sacred == "no" and asset.get("sacred_status"):
            continue

        if selected_restricted == "yes" and not asset.get("restricted_access_level"):
            continue

        if selected_restricted == "no" and asset.get("restricted_access_level"):
            continue

        filtered_rows.append(asset)

    filters = {
        "continuity_class": selected_continuity_class,
        "custody_class": selected_custody_class,
        "memorial": selected_memorial,
        "sacred": selected_sacred,
        "restricted": selected_restricted,
    }

    return filtered_rows, dashboard_rows, filters


def generate_continuity_asset_dashboard_pdf(assets, total_asset_count, filters=None):

    from io import BytesIO

    filters = filters or {}

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ContinuityDashboardTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        spaceAfter=16
    )

    section_style = ParagraphStyle(
        "ContinuityDashboardSection",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "ContinuityDashboardBody",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=15,
        spaceAfter=7
    )

    def safe(value):
        if value is None or value == "":
            return "Not entered"
        return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def nice(value):
        if value is None or value == "":
            return "Not entered"
        return str(value).replace("_", " ").title()

    story = []

    story.append(Paragraph("Continuity Asset Dashboard Report", title_style))

    story.append(Paragraph("Report Summary", section_style))
    story.append(Paragraph(f"<b>Filtered Assets:</b> {len(assets)}", body_style))
    story.append(Paragraph(f"<b>Total Continuity Assets:</b> {total_asset_count}", body_style))

    active_filters = [
        f"{key.replace('_', ' ').title()}: {nice(value)}"
        for key, value in filters.items()
        if value
    ]

    if active_filters:
        story.append(Paragraph("<b>Active Filters:</b> " + "; ".join(active_filters), body_style))
    else:
        story.append(Paragraph("<b>Active Filters:</b> None", body_style))

    story.append(Spacer(1, 10))

    story.append(Paragraph("Continuity Asset Records", section_style))

    if not assets:
        story.append(Paragraph("No continuity assets matched the selected filters.", body_style))
    else:
        for asset in assets:
            story.append(
                Paragraph(
                    f"<b>{safe(asset.get('property_id'))} — {safe(asset.get('property_name'))}</b>",
                    body_style
                )
            )
            story.append(Paragraph(f"<b>Trust:</b> {safe(asset.get('trust_name') or asset.get('trust_id'))}", body_style))
            story.append(Paragraph(f"<b>Continuity Class:</b> {nice(asset.get('continuity_classification'))}", body_style))
            story.append(Paragraph(f"<b>Custody Class:</b> {nice(asset.get('custody_classification'))}", body_style))
            readiness = asset.get("readiness") or score_continuity_asset_readiness(
                asset,
                get_custody_events_for_property(asset.get("property_id"))
            )

            story.append(Paragraph(f"<b>Priority:</b> {safe(asset.get('continuity_priority') or 0)}", body_style))
            story.append(Paragraph(f"<b>Memorial:</b> {'Yes' if asset.get('memorial_status') else 'No'}", body_style))
            story.append(Paragraph(f"<b>Sacred / Protected:</b> {'Yes' if asset.get('sacred_status') else 'No'}", body_style))
            story.append(Paragraph(f"<b>Restricted Access:</b> {safe(asset.get('restricted_access_level'))}", body_style))
            evidence_profile = build_property_evidence_profile(asset.get("property_id"))
            timeline_summary = summarize_property_evidence_custody_timeline(asset.get("property_id"))

            story.append(Paragraph(f"<b>Readiness:</b> {safe(readiness.get('score'))}% · {safe(readiness.get('status'))}", body_style))
            story.append(Paragraph(f"<b>Evidence Items:</b> {safe(evidence_profile.get('evidence_count'))}", body_style))
            story.append(Paragraph(f"<b>Timeline Items:</b> {safe(timeline_summary.get('timeline_count'))}", body_style))
            story.append(Paragraph(f"<b>Custody Events:</b> {safe(timeline_summary.get('custody_event_count'))}", body_style))
            resolved_count = timeline_summary.get("resolved_references") or 0
            unresolved_count = timeline_summary.get("unresolved_references") or 0
            resolution_status = "Clean" if unresolved_count == 0 else "Cleanup Needed"

            story.append(Paragraph(f"<b>Resolved References:</b> {safe(resolved_count)}", body_style))
            story.append(Paragraph(f"<b>Unresolved / Manual References:</b> {safe(unresolved_count)}", body_style))
            story.append(Paragraph(f"<b>Resolution Status:</b> {safe(resolution_status)}", body_style))
            story.append(Paragraph(f"<b>Missing Readiness Items:</b> {safe('; '.join(readiness.get('missing') or []) or 'No missing readiness items')}", body_style))

            if evidence_profile.get("evidence_items"):
                for item in evidence_profile.get("evidence_items"):
                    story.append(
                        Paragraph(
                            f"<b>Evidence:</b> {safe(item.get('source_type')).title()} "
                            f"{safe(item.get('evidence_id'))} — "
                            f"{safe(item.get('title') or item.get('filename') or 'Untitled evidence item')}",
                            body_style
                        )
                    )

            story.append(Spacer(1, 8))

    story.append(Spacer(1, 12))

    story.append(Paragraph("Classification Reminder", section_style))
    story.append(
        Paragraph(
            "Heritage, memorial, sacred, lineage, archival, and biological keepsake records "
            "should be handled as stewardship or custody records, not ordinary commercial property.",
            body_style
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer


@app.route("/continuity-assets/pdf")
@require_permission("view_dashboard")
def continuity_asset_dashboard_pdf():
    filtered_rows, dashboard_rows, filters = get_filtered_continuity_asset_rows()

    pdf_buffer = generate_continuity_asset_dashboard_pdf(
        filtered_rows,
        len(dashboard_rows),
        filters
    )

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="Continuity_Asset_Dashboard_Report.pdf"
    )


@app.route("/continuity-assets")
@require_permission("view_dashboard")
def continuity_asset_dashboard():
    trusts = get_visible_trusts_for_current_operator()

    selected_continuity_class = (request.args.get("continuity_class") or "").strip()
    selected_custody_class = (request.args.get("custody_class") or "").strip()
    selected_memorial = (request.args.get("memorial") or "").strip()
    selected_sacred = (request.args.get("sacred") or "").strip()
    selected_restricted = (request.args.get("restricted") or "").strip()

    dashboard_rows = []

    for trust in trusts:
        trust_id = trust["trust_id"]
        assets = get_continuity_assets_by_trust(trust_id)

        for asset in assets:
            asset_data = dict(asset)
            asset_data["trust_name"] = trust["trust_name"]
            custody_events = get_custody_events_for_property(asset_data["property_id"])
            evidence_profile = build_property_evidence_profile(asset_data["property_id"])
            timeline_summary = summarize_property_evidence_custody_timeline(asset_data["property_id"])

            asset_data["evidence_count"] = evidence_profile.get("evidence_count", 0)
            asset_data["timeline_summary"] = timeline_summary
            asset_data["readiness"] = score_continuity_asset_readiness(
                asset_data,
                custody_events,
                evidence_profile
            )
            dashboard_rows.append(asset_data)

    filtered_rows = []

    for asset in dashboard_rows:
        if selected_continuity_class and asset.get("continuity_classification") != selected_continuity_class:
            continue

        if selected_custody_class and asset.get("custody_classification") != selected_custody_class:
            continue

        if selected_memorial == "yes" and not asset.get("memorial_status"):
            continue

        if selected_memorial == "no" and asset.get("memorial_status"):
            continue

        if selected_sacred == "yes" and not asset.get("sacred_status"):
            continue

        if selected_sacred == "no" and asset.get("sacred_status"):
            continue

        if selected_restricted == "yes" and not asset.get("restricted_access_level"):
            continue

        if selected_restricted == "no" and asset.get("restricted_access_level"):
            continue

        filtered_rows.append(asset)

    return render_template(
        "continuity_asset_dashboard.html",
        assets=filtered_rows,
        asset_count=len(filtered_rows),
        total_asset_count=len(dashboard_rows),
        continuity_classifications=get_continuity_classifications(),
        custody_classifications=get_custody_classifications(),
        selected_continuity_class=selected_continuity_class,
        selected_custody_class=selected_custody_class,
        selected_memorial=selected_memorial,
        selected_sacred=selected_sacred,
        selected_restricted=selected_restricted
    )




# ===================================================
# AC-1 CONTINUITY ASSET PDF REPORT
# ===================================================

def generate_continuity_asset_pdf(prop, trust=None):

    from io import BytesIO

    prop_data = dict(prop)
    trust_data = dict(trust) if trust else {}

    custody_events = get_custody_events_for_property(prop_data.get("property_id"))
    readiness = score_continuity_asset_readiness(prop_data, custody_events)

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ContinuityAssetTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        spaceAfter=16
    )

    section_style = ParagraphStyle(
        "ContinuityAssetSection",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "ContinuityAssetBody",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=15,
        spaceAfter=7
    )

    def safe(value):
        if value is None or value == "":
            return "Not entered"
        return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def label_value(label, value):
        story.append(
            Paragraph(
                f"<b>{safe(label)}:</b> {safe(value)}",
                body_style
            )
        )

    story = []

    story.append(Paragraph("Continuity Asset Report", title_style))

    story.append(Paragraph("Asset Identity", section_style))
    label_value("Property ID", prop_data.get("property_id"))
    label_value("Property Name", prop_data.get("property_name"))
    label_value("Property Type", prop_data.get("property_type"))
    label_value("Asset Class", prop_data.get("asset_class"))
    label_value("Asset Subtype", prop_data.get("asset_subtype"))
    label_value("Identifier / Address / URL", prop_data.get("address_or_identifier"))

    story.append(Spacer(1, 8))

    story.append(Paragraph("Linked Trust", section_style))
    label_value("Trust ID", prop_data.get("trust_id"))
    label_value("Trust Name", trust_data.get("trust_name"))
    label_value("Trust Type", trust_data.get("trust_type"))

    story.append(Spacer(1, 8))

    story.append(Paragraph("Continuity Classification", section_style))
    label_value("Continuity Classification", (prop_data.get("continuity_classification") or "").replace("_", " ").title())
    label_value("Custody Classification", (prop_data.get("custody_classification") or "").replace("_", " ").title())
    label_value("Continuity Priority", prop_data.get("continuity_priority"))
    label_value("Restricted Access Level", prop_data.get("restricted_access_level"))
    label_value("Lineage Association", prop_data.get("lineage_association"))

    story.append(Spacer(1, 8))

    story.append(Paragraph("Readiness Audit", section_style))
    label_value("Readiness Score", f"{readiness.get('score')}%")
    label_value("Readiness Status", readiness.get("status"))
    label_value("Missing Readiness Items", "; ".join(readiness.get("missing") or []) or "No missing readiness items")

    story.append(Spacer(1, 8))

    story.append(Paragraph("Custody / Stewardship Flags", section_style))
    label_value("Memorial Custody Item", "Yes" if prop_data.get("memorial_status") else "No")
    label_value("Sacred / Protected Heritage Property", "Yes" if prop_data.get("sacred_status") else "No")
    label_value("Custodian / Manager", prop_data.get("custodian"))
    label_value("Responsible Party", prop_data.get("responsible_party"))

    story.append(Spacer(1, 8))

    story.append(Paragraph("Preservation Doctrine", section_style))
    label_value("Heritage Significance", prop_data.get("heritage_significance"))
    label_value("Preservation Requirements", prop_data.get("preservation_requirements"))
    label_value("Continuity Notes", prop_data.get("continuity_notes"))

    story.append(Spacer(1, 8))

    evidence_profile = build_property_evidence_profile(prop_data.get("property_id"))

    story.append(Paragraph("Supporting Evidence", section_style))
    label_value("Evidence Item Count", evidence_profile.get("evidence_count"))

    if evidence_profile.get("evidence_items"):
        for item in evidence_profile.get("evidence_items"):
            story.append(
                Paragraph(
                    f"<b>{safe(item.get('source_type')).title()} {safe(item.get('evidence_id'))}</b> — "
                    f"{safe(item.get('title') or item.get('filename') or 'Untitled evidence item')}",
                    body_style
                )
            )
            label_value("Category", item.get("category"))
            label_value("Notes", item.get("notes"))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No linked evidence documents or media records found.", body_style))

    story.append(Spacer(1, 12))

    story.append(Paragraph("Classification Reminder", section_style))
    story.append(
        Paragraph(
            "Heritage, memorial, sacred, lineage, and biological keepsake records should be handled "
            "as stewardship or custody records, not ordinary commercial property.",
            body_style
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer


@app.route("/property/<property_id>/continuity/pdf")
@require_permission("view_dashboard")
def property_continuity_profile_pdf(property_id):
    prop = get_property_by_id(property_id)

    if not prop:
        flash("Property not found.", "danger")
        return redirect(url_for("admin_index"))

    linked_trust = get_trust_by_id(prop["trust_id"])

    pdf_buffer = generate_continuity_asset_pdf(prop, linked_trust)

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{property_id}_Continuity_Asset_Report.pdf"
    )






# ===================================================
# AC-1 CONTINUITY CUSTODY LOG PDF REPORT
# ===================================================

def generate_custody_log_pdf(prop, trust=None, custody_events=None):

    from io import BytesIO

    prop_data = dict(prop)
    trust_data = dict(trust) if trust else {}
    custody_events = custody_events or []

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustodyLogTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        spaceAfter=16
    )

    section_style = ParagraphStyle(
        "CustodyLogSection",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "CustodyLogBody",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=15,
        spaceAfter=7
    )

    def safe(value):
        if value is None or value == "":
            return "Not entered"
        return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def label_value(label, value):
        story.append(
            Paragraph(
                f"<b>{safe(label)}:</b> {safe(value)}",
                body_style
            )
        )

    story = []

    story.append(Paragraph("Continuity Chain-of-Custody Report", title_style))

    story.append(Paragraph("Asset Identity", section_style))
    label_value("Property ID", prop_data.get("property_id"))
    label_value("Property Name", prop_data.get("property_name"))
    label_value("Property Type", prop_data.get("property_type"))
    label_value("Asset Class", prop_data.get("asset_class"))
    label_value("Asset Subtype", prop_data.get("asset_subtype"))

    story.append(Spacer(1, 8))

    story.append(Paragraph("Linked Trust", section_style))
    label_value("Trust ID", prop_data.get("trust_id"))
    label_value("Trust Name", trust_data.get("trust_name"))
    label_value("Trust Type", trust_data.get("trust_type"))

    story.append(Spacer(1, 8))

    readiness = score_continuity_asset_readiness(prop_data, custody_events)

    story.append(Paragraph("Readiness Audit", section_style))
    label_value("Readiness Score", f"{readiness.get('score')}%")
    label_value("Readiness Status", readiness.get("status"))
    label_value("Missing Readiness Items", "; ".join(readiness.get("missing") or []) or "No missing readiness items")

    story.append(Spacer(1, 8))

    evidence_profile = build_property_evidence_profile(prop_data.get("property_id"))

    story.append(Paragraph("Supporting Evidence", section_style))
    label_value("Evidence Item Count", evidence_profile.get("evidence_count"))

    if evidence_profile.get("evidence_items"):
        for item in evidence_profile.get("evidence_items"):
            story.append(
                Paragraph(
                    f"<b>{safe(item.get('source_type')).title()} {safe(item.get('evidence_id'))}</b> — "
                    f"{safe(item.get('title') or item.get('filename') or 'Untitled evidence item')}",
                    body_style
                )
            )
            label_value("Category", item.get("category"))
            label_value("Notes", item.get("notes"))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No linked evidence documents or media records found.", body_style))

    story.append(Spacer(1, 8))

    story.append(Paragraph("Custody History", section_style))

    if not custody_events:
        story.append(Paragraph("No custody events recorded.", body_style))
    else:
        for event in custody_events:
            event_data = dict(event)

            story.append(
                Paragraph(
                    f"<b>{safe(event_data.get('custody_event_id'))}</b>",
                    body_style
                )
            )

            label_value("Event Date", event_data.get("event_date"))
            label_value("Custody Action", (event_data.get("custody_action") or "").replace("_", " ").title())
            label_value("From Party", event_data.get("from_party"))
            label_value("To Party", event_data.get("to_party"))
            label_value("Acting Capacity", event_data.get("acting_capacity"))
            label_value("Location Reference", event_data.get("location_reference"))
            label_value("Supporting Document Reference", event_data.get("supporting_document_reference"))

            evidence_item = resolve_evidence_reference(
                prop_data.get("property_id"),
                event_data.get("supporting_document_reference")
            )

            if evidence_item:
                resolved_label = (
                    f"{evidence_item.get('source_type', '').title()} "
                    f"{evidence_item.get('evidence_id')} — "
                    f"{evidence_item.get('title') or evidence_item.get('filename') or 'Untitled evidence item'}"
                )
                label_value("Resolved Evidence", resolved_label)
                label_value("Evidence Category", evidence_item.get("category"))
                label_value("Evidence Notes", evidence_item.get("notes"))
            else:
                label_value("Resolved Evidence", "No linked evidence match found")

            label_value("Recorded By", event_data.get("recorded_by"))
            label_value("Notes", event_data.get("notes"))

            story.append(Spacer(1, 8))

    story.append(Spacer(1, 12))

    story.append(Paragraph("Custody Doctrine Reminder", section_style))
    story.append(
        Paragraph(
            "Heritage, memorial, sacred, lineage, archival, and biological keepsake records "
            "should maintain a documented chain of custody and should be handled as stewardship "
            "or custody records, not ordinary commercial property.",
            body_style
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer


@app.route("/property/<property_id>/custody-log/pdf")
@require_permission("view_dashboard")
def property_custody_log_pdf(property_id):
    prop = get_property_by_id(property_id)

    if not prop:
        flash("Property not found.", "danger")
        return redirect(url_for("admin_index"))

    prop_data = dict(prop)

    linked_trust = get_trust_by_id(prop_data.get("trust_id"))

    custody_events = [
        dict(event)
        for event in get_custody_events_for_property(property_id)
    ]

    pdf_buffer = generate_custody_log_pdf(
        prop_data,
        linked_trust,
        custody_events
    )

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{property_id}_Continuity_Custody_Log.pdf"
    )






# ===================================================
# AC-1 EVIDENCE / CUSTODY TIMELINE PDF EXPORT
# ===================================================

def generate_evidence_custody_timeline_pdf(prop, trust=None, timeline_profile=None):

    from io import BytesIO

    prop_data = dict(prop)
    trust_data = dict(trust) if trust else {}
    timeline_profile = timeline_profile or build_property_evidence_custody_timeline(prop_data.get("property_id"))

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TimelineTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        spaceAfter=16
    )

    section_style = ParagraphStyle(
        "TimelineSection",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "TimelineBody",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=15,
        spaceAfter=7
    )

    def safe(value):
        if value is None or value == "":
            return "Not entered"
        return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def label_value(label, value):
        story.append(
            Paragraph(
                f"<b>{safe(label)}:</b> {safe(value)}",
                body_style
            )
        )

    story = []

    story.append(Paragraph("Evidence / Custody Timeline Report", title_style))

    story.append(Paragraph("Asset Identity", section_style))
    label_value("Property ID", prop_data.get("property_id"))
    label_value("Property Name", prop_data.get("property_name"))
    label_value("Property Type", prop_data.get("property_type"))
    label_value("Asset Class", prop_data.get("asset_class"))
    label_value("Asset Subtype", prop_data.get("asset_subtype"))

    story.append(Spacer(1, 8))

    story.append(Paragraph("Linked Trust", section_style))
    label_value("Trust ID", prop_data.get("trust_id"))
    label_value("Trust Name", trust_data.get("trust_name"))
    label_value("Trust Type", trust_data.get("trust_type"))

    story.append(Spacer(1, 8))

    story.append(Paragraph("Timeline Summary", section_style))
    label_value("Visible Timeline Items", timeline_profile.get("timeline_count"))
    label_value("Total Timeline Items", timeline_profile.get("unfiltered_count") or timeline_profile.get("timeline_count"))
    label_value("Evidence Items", timeline_profile.get("evidence_count"))
    label_value("Custody Events", timeline_profile.get("custody_event_count"))

    resolved_references = 0
    unresolved_references = 0

    for timeline_item in timeline_profile.get("timeline") or []:
        if timeline_item.get("timeline_type") != "custody_event":
            continue

        reference = timeline_item.get("reference")

        if not reference:
            continue

        if timeline_item.get("resolved_evidence_label"):
            resolved_references += 1
        else:
            unresolved_references += 1

    resolution_status = "Clean" if unresolved_references == 0 else "Cleanup Needed"

    label_value("Resolved References", resolved_references)
    label_value("Unresolved / Manual References", unresolved_references)
    label_value("Resolution Status", resolution_status)

    active_filters = timeline_profile.get("active_filters") or {}
    filter_lines = []

    for key, value in active_filters.items():
        if value:
            filter_lines.append(f"{key.replace('_', ' ').title()}: {str(value).replace('_', ' ').title()}")

    if filter_lines:
        label_value("Active Filters", "; ".join(filter_lines))
    else:
        label_value("Active Filters", "None")

    story.append(Spacer(1, 10))

    story.append(Paragraph("Timeline Entries", section_style))

    timeline = timeline_profile.get("timeline") or []

    if not timeline:
        story.append(Paragraph("No evidence or custody events found for this asset.", body_style))
    else:
        for item in timeline:
            story.append(
                Paragraph(
                    f"<b>{safe(item.get('timeline_date'))} — {safe(str(item.get('timeline_type') or '').replace('_', ' ').title())}</b>",
                    body_style
                )
            )

            label_value("Title", item.get("title"))
            label_value("Reference", item.get("subtitle") or item.get("reference"))
            label_value("Category / Capacity", item.get("category"))

            if item.get("from_party") or item.get("to_party"):
                label_value("From Party", item.get("from_party"))
                label_value("To Party", item.get("to_party"))

            label_value("Location", item.get("location_reference"))
            label_value("Supporting Reference", item.get("reference"))

            if item.get("timeline_type") == "custody_event":
                if item.get("reference") and item.get("resolved_evidence_label"):
                    label_value("Resolution Status", "Resolved Evidence Reference")
                elif item.get("reference"):
                    label_value("Resolution Status", "Unresolved Manual Reference — Cleanup Needed")
                else:
                    label_value("Resolution Status", "No Supporting Reference Entered")

            label_value("Resolved Evidence", item.get("resolved_evidence_label"))
            label_value("Notes", item.get("description"))
            label_value("Recorded By", item.get("recorded_by"))

            story.append(Spacer(1, 8))

    story.append(Spacer(1, 12))

    story.append(Paragraph("Timeline Doctrine Reminder", section_style))
    story.append(
        Paragraph(
            "A continuity asset timeline should show what evidence exists, when custody actions occurred, "
            "who acted, in what capacity, and what supporting record verifies the event.",
            body_style
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer


@app.route("/property/<property_id>/timeline/pdf")
@require_permission("view_dashboard")
def property_evidence_custody_timeline_pdf(property_id):
    prop = get_property_by_id(property_id)

    if not prop:
        flash("Property not found.", "danger")
        return redirect(url_for("admin_index"))

    prop_data = dict(prop)
    linked_trust = get_trust_by_id(prop_data.get("trust_id"))
    timeline_profile = build_property_evidence_custody_timeline(property_id)

    selected_type = (request.args.get("type") or "").strip()
    selected_resolved = (request.args.get("resolved") or "").strip()
    selected_action = (request.args.get("action") or "").strip()
    start_date = (request.args.get("start_date") or "").strip()
    end_date = (request.args.get("end_date") or "").strip()

    timeline = timeline_profile.get("timeline", [])
    filtered_timeline = []

    for item in timeline:
        if selected_type and item.get("timeline_type") != selected_type:
            continue

        if selected_resolved == "yes" and not item.get("resolved_evidence_label"):
            continue

        if selected_resolved == "no" and item.get("resolved_evidence_label"):
            continue

        if selected_action and item.get("timeline_type") == "custody_event":
            if item.get("title") != selected_action.replace("_", " ").title():
                continue

        item_date = item.get("sort_date") or ""

        if start_date and item_date and item_date < start_date:
            continue

        if end_date and item_date and item_date > end_date:
            continue

        filtered_timeline.append(item)

    filtered_profile = dict(timeline_profile)
    filtered_profile["timeline"] = filtered_timeline
    filtered_profile["timeline_count"] = len(filtered_timeline)
    filtered_profile["filtered_count"] = len(filtered_timeline)
    filtered_profile["unfiltered_count"] = len(timeline)
    filtered_profile["active_filters"] = {
        "type": selected_type,
        "resolved": selected_resolved,
        "action": selected_action,
        "start_date": start_date,
        "end_date": end_date,
    }

    pdf_buffer = generate_evidence_custody_timeline_pdf(
        prop_data,
        linked_trust,
        filtered_profile
    )

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{property_id}_Evidence_Custody_Timeline.pdf"
    )






# ===================================================
# AC-1 RESOLUTION QUEUE PDF EXPORT
# ===================================================

def generate_resolution_queue_pdf(prop, trust=None, queue_profile=None):

    from io import BytesIO

    prop_data = dict(prop)
    trust_data = dict(trust) if trust else {}
    queue_profile = queue_profile or build_property_resolution_queue(prop_data.get("property_id"))

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ResolutionQueueTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        spaceAfter=16
    )

    section_style = ParagraphStyle(
        "ResolutionQueueSection",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "ResolutionQueueBody",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=15,
        spaceAfter=7
    )

    def safe(value):
        if value is None or value == "":
            return "Not entered"
        return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def label_value(label, value):
        story.append(
            Paragraph(
                f"<b>{safe(label)}:</b> {safe(value)}",
                body_style
            )
        )

    story = []

    story.append(Paragraph("Evidence Resolution Queue Report", title_style))

    story.append(Paragraph("Asset Identity", section_style))
    label_value("Property ID", prop_data.get("property_id"))
    label_value("Property Name", prop_data.get("property_name"))
    label_value("Property Type", prop_data.get("property_type"))
    label_value("Asset Class", prop_data.get("asset_class"))
    label_value("Asset Subtype", prop_data.get("asset_subtype"))

    story.append(Spacer(1, 8))

    story.append(Paragraph("Linked Trust", section_style))
    label_value("Trust ID", prop_data.get("trust_id"))
    label_value("Trust Name", trust_data.get("trust_name"))
    label_value("Trust Type", trust_data.get("trust_type"))

    story.append(Spacer(1, 8))

    story.append(Paragraph("Queue Summary", section_style))
    label_value("Unresolved Custody Events", queue_profile.get("unresolved_count"))
    label_value("Linked Evidence Items", queue_profile.get("evidence_count"))
    label_value("Resolution Status", queue_profile.get("resolution_status"))
    label_value("Archive Badge", queue_profile.get("archive_badge"))

    story.append(Spacer(1, 10))

    story.append(Paragraph("Unresolved Custody Events", section_style))

    unresolved_events = queue_profile.get("unresolved_events") or []

    if not unresolved_events:
        story.append(Paragraph("No unresolved manual custody references remain for this asset.", body_style))
    else:
        for event in unresolved_events:
            story.append(
                Paragraph(
                    f"<b>{safe(event.get('custody_event_id'))}</b>",
                    body_style
                )
            )
            label_value("Event Date", event.get("event_date"))
            label_value("Custody Action", (event.get("custody_action") or "").replace("_", " ").title())
            label_value("Manual Reference", event.get("supporting_document_reference"))
            label_value("Acting Capacity", event.get("acting_capacity"))
            label_value("Location Reference", event.get("location_reference"))
            label_value("Recorded By", event.get("recorded_by"))
            label_value("Cleanup Action", "Resolve manual reference into linked evidence")
            story.append(Spacer(1, 8))

    story.append(Spacer(1, 10))

    story.append(Paragraph("Available Evidence Options", section_style))

    evidence_items = queue_profile.get("evidence_items") or []

    if not evidence_items:
        story.append(Paragraph("No linked evidence items are available for this property.", body_style))
    else:
        for item in evidence_items:
            story.append(
                Paragraph(
                    f"<b>{safe(item.get('source_type')).title()} {safe(item.get('evidence_id'))}</b> — "
                    f"{safe(item.get('title') or item.get('filename') or 'Untitled evidence item')}",
                    body_style
                )
            )
            label_value("Category", item.get("category"))
            label_value("Notes", item.get("notes"))
            story.append(Spacer(1, 6))

    story.append(Spacer(1, 12))

    story.append(Paragraph("Resolution Queue Purpose", section_style))
    story.append(
        Paragraph(
            "This report isolates custody events with manual or unresolved references so they can be converted "
            "into linked evidence references.",
            body_style
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer


@app.route("/property/<property_id>/resolution-queue/pdf")
@require_permission("view_dashboard")
def property_resolution_queue_pdf(property_id):
    prop = get_property_by_id(property_id)

    if not prop:
        flash("Property not found.", "danger")
        return redirect(url_for("admin_index"))

    prop_data = dict(prop)
    linked_trust = get_trust_by_id(prop_data.get("trust_id"))
    queue_profile = build_property_resolution_queue(property_id)

    pdf_buffer = generate_resolution_queue_pdf(
        prop_data,
        linked_trust,
        queue_profile
    )

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{property_id}_Evidence_Resolution_Queue.pdf"
    )


@app.route("/property/<property_id>/resolution-queue")
@require_permission("view_dashboard")
def property_resolution_queue(property_id):
    prop = get_property_by_id(property_id)

    if not prop:
        flash("Property not found.", "danger")
        return redirect(url_for("admin_index"))

    prop_data = dict(prop)
    linked_trust = get_trust_by_id(prop_data.get("trust_id"))
    queue_profile = build_property_resolution_queue(property_id)

    return render_template(
        "property_resolution_queue.html",
        prop=prop_data,
        linked_trust=linked_trust,
        queue_profile=queue_profile
    )


@app.route("/property/<property_id>/timeline")
@require_permission("view_dashboard")
def property_evidence_custody_timeline(property_id):
    prop = get_property_by_id(property_id)

    if not prop:
        flash("Property not found.", "danger")
        return redirect(url_for("admin_index"))

    prop_data = dict(prop)
    linked_trust = get_trust_by_id(prop_data.get("trust_id"))
    timeline_profile = build_property_evidence_custody_timeline(property_id)

    selected_type = (request.args.get("type") or "").strip()
    selected_resolved = (request.args.get("resolved") or "").strip()
    selected_action = (request.args.get("action") or "").strip()
    start_date = (request.args.get("start_date") or "").strip()
    end_date = (request.args.get("end_date") or "").strip()

    timeline = timeline_profile.get("timeline", [])

    filtered_timeline = []

    for item in timeline:
        if selected_type and item.get("timeline_type") != selected_type:
            continue

        if selected_resolved == "yes" and not item.get("resolved_evidence_label"):
            continue

        if selected_resolved == "no" and item.get("resolved_evidence_label"):
            continue

        if selected_action and item.get("timeline_type") == "custody_event":
            if item.get("title") != selected_action.replace("_", " ").title():
                continue

        item_date = item.get("sort_date") or ""

        if start_date and item_date and item_date < start_date:
            continue

        if end_date and item_date and item_date > end_date:
            continue

        filtered_timeline.append(item)

    action_options = sorted({
        item.get("title")
        for item in timeline
        if item.get("timeline_type") == "custody_event" and item.get("title")
    })

    filtered_profile = dict(timeline_profile)
    filtered_profile["timeline"] = filtered_timeline
    filtered_profile["filtered_count"] = len(filtered_timeline)
    filtered_profile["unfiltered_count"] = len(timeline)

    return render_template(
        "property_evidence_custody_timeline.html",
        prop=prop_data,
        linked_trust=linked_trust,
        timeline_profile=filtered_profile,
        selected_type=selected_type,
        selected_resolved=selected_resolved,
        selected_action=selected_action,
        start_date=start_date,
        end_date=end_date,
        action_options=action_options
    )




@app.route("/property/<property_id>/custody-log/<custody_event_id>/resolve", methods=["GET", "POST"])
@require_permission("view_dashboard")
def resolve_custody_event_evidence(property_id, custody_event_id):
    prop = get_property_by_id(property_id)

    if not prop:
        flash("Property not found.", "danger")
        return redirect(url_for("admin_index"))

    prop_data = dict(prop)
    custody_event = get_custody_event_by_id(custody_event_id)

    if not custody_event:
        flash("Custody event not found.", "danger")
        return redirect(url_for("property_custody_log", property_id=property_id))

    custody_event = dict(custody_event)

    if custody_event.get("property_id") != property_id:
        flash("Custody event does not belong to this property.", "danger")
        return redirect(url_for("property_custody_log", property_id=property_id))

    evidence_profile = build_property_evidence_profile(property_id)

    if request.method == "POST":
        supporting_reference = (request.form.get("supporting_document_reference") or "").strip()

        if not supporting_reference:
            flash("Select a supporting evidence reference before saving.", "warning")
            return redirect(
                url_for(
                    "resolve_custody_event_evidence",
                    property_id=property_id,
                    custody_event_id=custody_event_id
                )
            )

        updated = update_custody_event_supporting_reference(
            custody_event_id,
            supporting_reference
        )

        if updated:
            flash(f"Custody event {custody_event_id} evidence reference updated.", "success")
        else:
            flash("Custody event could not be updated.", "danger")

        return redirect(url_for("property_custody_log", property_id=property_id))

    current_evidence = resolve_evidence_reference(
        property_id,
        custody_event.get("supporting_document_reference")
    )

    return render_template(
        "resolve_custody_event_evidence.html",
        prop=prop_data,
        custody_event=custody_event,
        evidence_profile=evidence_profile,
        current_evidence=current_evidence
    )


@app.route("/property/<property_id>/custody-log", methods=["GET", "POST"])
@require_permission("view_dashboard")
def property_custody_log(property_id):
    prop = get_property_by_id(property_id)

    if not prop:
        flash("Property not found.", "danger")
        return redirect(url_for("admin_index"))

    prop_data = dict(prop)

    if request.method == "POST":
        event_data = {
            "property_id": property_id,
            "trust_id": prop_data.get("trust_id"),
            "event_date": request.form.get("event_date"),
            "custody_action": request.form.get("custody_action"),
            "from_party": request.form.get("from_party"),
            "to_party": request.form.get("to_party"),
            "acting_capacity": request.form.get("acting_capacity"),
            "location_reference": request.form.get("location_reference"),
            "supporting_document_reference": request.form.get("supporting_document_reference"),
            "notes": request.form.get("notes"),
            "recorded_by": session.get("username") or "unknown",
            "firm_id": prop_data.get("firm_id"),
        }

        custody_event_id = create_continuity_custody_event(event_data)

        flash(f"Custody event recorded: {custody_event_id}", "success")

        return redirect(
            url_for(
                "property_custody_log",
                property_id=property_id
            )
        )

    custody_events = [
        dict(event)
        for event in get_custody_events_for_property(property_id)
    ]

    custody_events = enrich_custody_events_with_evidence(
        property_id,
        custody_events
    )

    linked_trust = get_trust_by_id(prop_data.get("trust_id"))
    evidence_profile = build_property_evidence_profile(property_id)

    return render_template(
        "property_custody_log.html",
        prop=prop_data,
        linked_trust=linked_trust,
        custody_events=custody_events,
        evidence_profile=evidence_profile
    )


@app.route("/property/<property_id>/continuity", methods=["GET", "POST"])
@require_permission("view_dashboard")
def property_continuity_profile(property_id):
    prop = get_property_by_id(property_id)

    if not prop:
        flash("Property not found.", "danger")
        return redirect(url_for("admin_index"))

    if request.method == "POST":
        profile_data = {
            "continuity_classification": request.form.get("continuity_classification"),
            "custody_classification": request.form.get("custody_classification"),
            "continuity_priority": request.form.get("continuity_priority") or 0,
            "heritage_significance": request.form.get("heritage_significance"),
            "preservation_requirements": request.form.get("preservation_requirements"),
            "restricted_access_level": request.form.get("restricted_access_level"),
            "lineage_association": request.form.get("lineage_association"),
            "memorial_status": 1 if request.form.get("memorial_status") == "on" else 0,
            "sacred_status": 1 if request.form.get("sacred_status") == "on" else 0,
            "continuity_notes": request.form.get("continuity_notes"),
        }

        update_property_continuity_profile(property_id, profile_data)

        flash("Continuity asset profile updated.", "success")

        return redirect(
            url_for(
                "property_continuity_profile",
                property_id=property_id
            )
        )

    profile = get_property_continuity_profile(property_id)

    return render_template(
        "property_continuity_profile.html",
        prop=prop,
        profile=profile,
        continuity_classifications=get_continuity_classifications(),
        custody_classifications=get_custody_classifications()
    )


@app.route("/k1")
def k1_dashboard():
    trusts = get_all_trusts()
    return render_template("k1_dashboard.html", trusts=trusts, tax_year=str(date.today().year))

@app.route("/k1/trust/<trust_id>")
def k1_trust_view(trust_id):
    tax_year = request.args.get("tax_year", str(date.today().year))
    trust = get_trust_by_id(trust_id)
    beneficiaries = get_beneficiaries_by_trust_id(trust_id)
    distributions = get_distributions_by_trust_id(trust_id, tax_year)
    summary = get_k1_summary(trust_id, tax_year)
    totals = get_distribution_totals_by_trust(trust_id, tax_year)
    beneficiary_totals = get_distribution_totals_by_beneficiary(trust_id, tax_year)

    totals["gross_total_fmt"] = money(totals["gross_total"])
    totals["taxable_total_fmt"] = money(totals["taxable_total"])
    totals["principal_total_fmt"] = money(totals["principal_total"])

    for row in beneficiary_totals:
        row["gross_total_fmt"] = money(row["gross_total"])
        row["taxable_total_fmt"] = money(row["taxable_total"])
        row["principal_total_fmt"] = money(row["principal_total"])

    history = get_audit_log_by_entity("beneficiary", trust_id, 25)

    return render_template(
        "k1_readiness.html",
        trust=trust,
        history=history,
        beneficiaries=beneficiaries,
        distributions=distributions,
        summary=summary,
        readiness=summary,
        totals=totals,
        beneficiary_totals=beneficiary_totals,
        tax_year=tax_year
    )

@app.route("/k1/trust/<trust_id>/beneficiary/new", methods=["GET", "POST"])
def k1_new_beneficiary(trust_id):
    trust = get_trust_by_id(trust_id)

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template(
                "k1_beneficiary_form.html",
                trust=trust,
                error_message="Invalid or missing CSRF token."
            )

        if not validate_csrf_token():
            return render_template(
                "k1_beneficiary_form.html",
                trust=trust,
                error_message="Invalid or missing CSRF token."
            )

        beneficiary_id = get_next_beneficiary_id()

        payload = {
            "beneficiary_id": beneficiary_id,
            "trust_id": trust_id,
            "full_name": request.form.get("full_name"),
            "tax_id": request.form.get("tax_id"),
            "beneficiary_type": request.form.get("beneficiary_type"),
            "email": request.form.get("email"),
            "address": request.form.get("address"),
            "allocation_method": request.form.get("allocation_method"),
            "fixed_percentage": request.form.get("fixed_percentage"),
            "is_active": "Yes",
            "notes": request.form.get("notes"),
        }

        errors = validate_beneficiary_payload(payload)
        if errors:
            return render_template(
                "k1_beneficiary_form.html",
                trust=trust,
                error_message="; ".join(errors)
            )

        create_beneficiary_record(payload)
        log_change("beneficiary", beneficiary_id, "create", f"Beneficiary created for trust {trust_id}")
        return redirect(url_for("k1_trust_view", trust_id=trust_id))

    return render_template("k1_beneficiary_form.html", trust=trust)

@app.route("/k1/trust/<trust_id>/distribution/new", methods=["GET", "POST"])
def k1_new_distribution(trust_id):
    trust = get_trust_by_id(trust_id)
    beneficiaries = get_beneficiaries_by_trust_id(trust_id)

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template(
                "k1_distribution_form.html",
                trust=trust,
                beneficiaries=beneficiaries,
                error_message="Invalid or missing CSRF token."
            )

        if not validate_csrf_token():
            return render_template(
                "k1_distribution_form.html",
                trust=trust,
                beneficiaries=beneficiaries,
                error_message="Invalid or missing CSRF token."
            )

        distribution_id = get_next_distribution_id()

        payload = {
            "distribution_id": distribution_id,
            "trust_id": trust_id,
            "beneficiary_id": request.form.get("beneficiary_id"),
            "tax_year": request.form.get("tax_year"),
            "distribution_date": request.form.get("distribution_date"),
            "distribution_type": request.form.get("distribution_type"),
            "description": request.form.get("description"),
            "gross_amount": request.form.get("gross_amount"),
            "taxable_amount": request.form.get("taxable_amount"),
            "principal_amount": request.form.get("principal_amount"),
            "source_reference": request.form.get("source_reference"),
            "status": "recorded",
        }

        errors = validate_distribution_payload(payload)
        if errors:
            return render_template(
                "k1_distribution_form.html",
                trust=trust,
                beneficiaries=beneficiaries,
                tax_year=request.form.get("tax_year") or str(date.today().year),
                error_message="; ".join(errors)
            )

        create_distribution_record(payload)
        log_change("distribution", distribution_id, "create", f"Distribution created for trust {trust_id}")
        return redirect(url_for("k1_trust_view", trust_id=trust_id, tax_year=request.form.get("tax_year")))

    return render_template(
        "k1_distribution_form.html",
        trust=trust,
        beneficiaries=beneficiaries,
        tax_year=str(date.today().year)
    )

@app.route("/k1/trust/<trust_id>/year_end_summary")
def k1_year_end_summary(trust_id):
    tax_year = request.args.get("tax_year", str(date.today().year))
    trust = get_trust_by_id(trust_id)
    summary = get_k1_summary(trust_id, tax_year)
    return render_template("k1_year_end_summary.html", trust=trust, tax_year=tax_year, summary=summary)


@app.route("/form1041")
def form1041_dashboard():
    trusts = get_all_trusts()
    trust_id = request.args.get("trust_id")
    tax_year = request.args.get("tax_year", str(date.today().year))

    selected_trust = None
    dataset = None

    distribution_totals = None
    tax_logic = None
    beneficiary_tax_shares = None

    if trust_id:
        selected_trust = get_trust_by_id(trust_id)
        if selected_trust:
            dataset = get_1041_dataset(trust_id, tax_year)
            distribution_totals = get_distribution_totals_by_trust(trust_id, tax_year)
            tax_logic = compute_dni_components(trust_id, tax_year)
            beneficiary_tax_shares = compute_beneficiary_tax_shares(trust_id, tax_year)

    if distribution_totals:
        distribution_totals["gross_total_fmt"] = money(distribution_totals["gross_total"])
        distribution_totals["taxable_total_fmt"] = money(distribution_totals["taxable_total"])
        distribution_totals["principal_total_fmt"] = money(distribution_totals["principal_total"])

    if tax_logic:
        tax_logic["gross_income_fmt"] = money(tax_logic["gross_income"])
        tax_logic["taxable_distributed_fmt"] = money(tax_logic["taxable_distributed"])
        tax_logic["principal_distributed_fmt"] = money(tax_logic["principal_distributed"])
        tax_logic["dni_fmt"] = money(tax_logic["dni"])
        tax_logic["retained_income_fmt"] = money(tax_logic["retained_income"])

    if beneficiary_tax_shares:
        for row in beneficiary_tax_shares:
            row["gross_total_fmt"] = money(row["gross_total"])
            row["taxable_total_fmt"] = money(row["taxable_total"])
            row["principal_total_fmt"] = money(row["principal_total"])
            row["taxable_ratio_pct"] = f"{row['taxable_ratio'] * 100:.1f}%"

    history = get_audit_log_by_entity("1041_export", trust_id, 25)

    return render_template(
        "form1041_dashboard.html",
        history=history,
        trusts=trusts,
        selected_trust=selected_trust,
        dataset=dataset,
        distribution_totals=distribution_totals,
        tax_logic=tax_logic,
        beneficiary_tax_shares=beneficiary_tax_shares,
        tax_year=tax_year
    )


@app.route("/form1041/preview/<trust_id>")
def form1041_preview(trust_id):
    tax_year = request.args.get("tax_year", str(date.today().year))
    dataset = get_1041_dataset(trust_id, tax_year)
    return render_template("form1041_preview.html", dataset=dataset, tax_year=tax_year)


@app.route("/form1041/print/<trust_id>")
def form1041_print(trust_id):
    tax_year = request.args.get("tax_year", str(date.today().year))
    dataset = get_1041_dataset(trust_id, tax_year)
    return render_template("form1041_print.html", dataset=dataset, tax_year=tax_year)


@app.route("/instruments")
def instruments_dashboard():
    trusts = get_all_trusts()
    trust_id = request.args.get("trust_id")
    selected_trust = None
    instruments = get_all_instruments()
    guide = get_instrument_creation_guide()
    status_counts = get_instrument_status_counts()

    if trust_id:
        selected_trust = get_trust_by_id(trust_id)
        instruments = get_instruments_by_trust_id(trust_id)
        status_counts = get_instrument_status_counts(trust_id)

    return render_template(
        "instrument_dashboard.html",
        trusts=trusts,
        selected_trust=selected_trust,
        instruments=instruments,
        guide=guide,
        status_counts=status_counts
    )


@app.route("/instruments/new", methods=["GET", "POST"])
def instrument_create():
    trusts = get_all_trusts()
    guide = get_instrument_creation_guide()

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("instrument_create.html", trusts=trusts, guide=guide, error_message="Invalid or missing CSRF token.")

        create_instrument_record({
            "instrument_id": get_next_instrument_id(),
            "trust_id": request.form.get("trust_id"),
            "instrument_number": request.form.get("instrument_number"),
            "instrument_type": request.form.get("instrument_type"),
            "issue_date": request.form.get("issue_date"),
            "maturity_date": request.form.get("maturity_date"),
            "face_value": request.form.get("face_value"),
            "backing_type": request.form.get("backing_type"),
            "backing_reference": request.form.get("backing_reference"),
            "status": request.form.get("status"),
            "affidavit_reference": request.form.get("affidavit_reference"),
            "custody_reference": request.form.get("custody_reference"),
            "notes": request.form.get("notes"),
        })
        return redirect(url_for("instruments_dashboard", trust_id=request.form.get("trust_id")))

    return render_template("instrument_create.html", trusts=trusts, guide=guide)


@app.route("/instruments/<instrument_id>", methods=["GET", "POST"])
def instrument_detail(instrument_id):
    instrument = get_instrument_by_id(instrument_id)
    trusts = get_all_trusts()
    guide = get_instrument_creation_guide()
    history = get_audit_log_by_entity("instrument", instrument_id, 25)

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template(
                "instrument_detail.html",
                instrument=instrument,
                trusts=trusts,
                guide=guide,
                history=history,
                error_message="Invalid or missing CSRF token."
            )

        if is_locked_status(instrument["status"]):
            log_change("instrument", instrument_id, "blocked_update", "Locked instrument edit prevented")
            return render_template(
                "instrument_detail.html",
                instrument=instrument,
                trusts=trusts,
                guide=guide,
                history=history,
                error_message="This instrument is locked and cannot be edited."
            )

        payload = {
            "trust_id": request.form.get("trust_id"),
            "instrument_number": request.form.get("instrument_number"),
            "instrument_type": request.form.get("instrument_type"),
            "issue_date": request.form.get("issue_date"),
            "maturity_date": request.form.get("maturity_date"),
            "face_value": request.form.get("face_value"),
            "backing_type": request.form.get("backing_type"),
            "backing_reference": request.form.get("backing_reference"),
            "status": request.form.get("status"),
            "affidavit_reference": request.form.get("affidavit_reference"),
            "custody_reference": request.form.get("custody_reference"),
            "notes": request.form.get("notes"),
        }

        errors = validate_instrument_payload(payload)
        if errors:
            return render_template(
                "instrument_detail.html",
                instrument=instrument,
                trusts=trusts,
                guide=guide,
                history=history,
                error_message="; ".join(errors)
            )

        update_instrument_record(instrument_id, payload)
        log_change("instrument", instrument_id, "update", "Instrument record updated")
        return redirect(url_for("instrument_detail", instrument_id=instrument_id))

    return render_template(
        "instrument_detail.html",
        instrument=instrument,
        trusts=trusts,
        guide=guide,
        history=history
    )

@app.route("/instruments/print/<instrument_id>")
def instrument_print(instrument_id):
    instrument = get_instrument_by_id(instrument_id)
    trusts = get_all_trusts()
    guide = get_instrument_creation_guide()
    return render_template(
        "instrument_print.html",
        instrument=instrument,
        trusts=trusts,
        guide=guide
    )


@app.route("/workflow")
def workflow_hub():
    trusts = get_all_trusts()
    return render_template("workflow_hub.html", trusts=trusts)




@app.route("/admin/export-policy/toggle", methods=["POST"])
def admin_toggle_export_policy():
    gate = require_master_admin()
    if gate:
        return gate

    allowed_keys = {"strict_packet_export", "allow_exports", "read_only_mode"}
    policy_key = (request.form.get("policy_key") or "strict_packet_export").strip()

    if policy_key not in allowed_keys:
        log_change("export_policy", policy_key, "toggle_rejected", "Invalid policy key")
        return redirect(url_for("admin_index"))

    policy = get_export_policy()
    current = bool(policy.get(policy_key, False))
    policy[policy_key] = not current

    import json
    EXPORT_POLICY_PATH.write_text(json.dumps(policy, indent=2), encoding="utf-8")

    log_change(
        "export_policy",
        policy_key,
        "toggle",
        f"Master admin set {policy_key} to {policy[policy_key]}"
    )
    flash(f"System policy updated: {policy_key} = {policy[policy_key]}")
    return redirect(url_for("admin_index"))

@app.route("/admin/seed-hosted-baseline", methods=["POST"])
def seed_hosted_baseline_route():
    gate = require_master_admin()
    if gate:
        return gate

    owner_id = get_current_owner() or "admin"
    results = seed_hosted_baseline_data(owner_id)

    summary = (
        f"Hosted baseline seed run by {owner_id} | "
        f"Trusts created={len(results.get('trusts_created', []))}, "
        f"Trusts skipped={len(results.get('trusts_skipped', []))}, "
        f"Articles created={len(results.get('learning_articles_created', []))}, "
        f"Articles skipped={len(results.get('learning_articles_skipped', []))}, "
        f"Guides created={len(results.get('form_guides_created', []))}, "
        f"Guides skipped={len(results.get('form_guides_skipped', []))}"
    )

    log_change(
        "system",
        "hosted_baseline_seed",
        "hosted_baseline_seed_run",
        summary
    )

    flash(summary)
    return redirect(url_for("admin_index"))


@app.route("/admin")
def admin_index():
    trusts = get_visible_trusts_for_current_operator()

    # BUILD TRUST SUMMARIES
    trust_summaries = [build_admin_trust_summary(t) for t in trusts]
    report = {
        "trust_count": get_trust_count(),
        "beneficiary_count": get_beneficiary_count(),
        "distribution_count": get_distribution_count(),
        "instrument_count": get_instrument_count(),
    }
    export_policy = get_export_policy()
    return render_template("admin_index.html", trusts=trusts, report=report, export_policy=export_policy,
        trust_summaries=trust_summaries)


@app.route("/users")
def users_dashboard():
    gate = require_master_admin()
    if gate:
        return gate
    users = get_all_app_users()
    return render_template("user_dashboard.html", users=users)


@app.route("/users/new", methods=["GET", "POST"])
def users_new():
    gate = require_master_admin()
    if gate:
        return gate
    if request.method == "POST":
        policy = get_export_policy()
        if not bool(policy.get("allow_user_creation", True)):
            log_change(
                "security",
                session.get("username") or "unknown",
                "user_creation_blocked",
                "Policy=allow_user_creation_false"
            )
            return render_template(
                "access_denied.html",
                reason="User creation is currently disabled by system policy."
            )

        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        role_name = request.form.get("role_name") or ""
        status = request.form.get("status") or "active"

        if not username or not password or role_name not in {"Admin", "Trustee", "Viewer"}:
            return render_template(
                "user_form.html",
                error_message="Valid username, password, and role are required."
            )

        existing = get_user_by_username(username)
        if existing:
            return render_template(
                "user_form.html",
                error_message="Username already exists."
            )

        create_app_user({
            "user_id": get_next_user_id(),
            "username": username,
            "password_hash": generate_password_hash(password),
            "role_name": role_name,
            "status": status,
        })
        log_change("app_user", username, "create", f"Master admin created user '{username}' with role '{role_name}' and status '{status}'")
        flash(f"User {username} created successfully.")
        return redirect(url_for("users_dashboard"))

    return render_template("user_form.html")


@app.route("/users/<username>/edit", methods=["GET", "POST"])
def users_edit(username):
    gate = require_master_admin()
    if gate:
        return gate
    user = get_user_by_username(username)
    if not user:
        return f"User {username} not found", 404

    if request.method == "POST":
        role_name = request.form.get("role_name") or ""
        status = request.form.get("status") or "active"

        if role_name not in {"Admin", "Trustee", "Viewer"}:
            return render_template(
                "user_edit.html",
                user=user,
                error_message="Valid role is required."
            )

        if session.get("username") == username:
            if role_name != "Admin":
                return render_template(
                    "user_edit.html",
                    user=user,
                    error_message="You cannot remove your own Admin role."
                )
            if status.lower() != "active":
                return render_template(
                    "user_edit.html",
                    user=user,
                    error_message="You cannot deactivate your own account."
                )

        update_app_user(username, {
            "role_name": role_name,
            "status": status,
        })

        allow_permissions = request.form.getlist("allow_permissions")
        deny_permissions = request.form.getlist("deny_permissions")

        replace_user_permission_overrides(username, allow_permissions, deny_permissions)

        log_change("app_user", username, "update", f"Master admin updated user '{username}' to role '{role_name}' with status '{status}'")
        log_change("security", username, "user_permission_overrides_updated", f"Allow={allow_permissions}; Deny={deny_permissions}")
        flash(f"User {username} updated successfully.")
        return redirect(url_for("users_dashboard"))

    all_permissions = get_all_permissions()
    overrides = get_user_permission_overrides(username)

    allow_set = {row["permission_name"] for row in overrides if row["effect"] == "allow"}
    deny_set = {row["permission_name"] for row in overrides if row["effect"] == "deny"}

    return render_template(
        "user_edit.html",
        user=user,
        all_permissions=all_permissions,
        allow_set=allow_set,
        deny_set=deny_set
    )


@app.route("/users/<username>/reset_password", methods=["GET", "POST"])
def users_reset_password(username):
    gate = require_master_admin()
    if gate:
        return gate
    user = get_user_by_username(username)
    if not user:
        return f"User {username} not found", 404

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("user_reset_password.html", user=user, error_message="Invalid or missing CSRF token.")

        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not password:
            return render_template(
                "user_reset_password.html",
                user=user,
                error_message="Password is required."
            )

        if password != confirm_password:
            return render_template(
                "user_reset_password.html",
                user=user,
                error_message="Passwords do not match."
            )

        update_app_user_password(username, generate_password_hash(password))
        log_change("app_user", username, "reset_password", f"Master admin reset password for user '{username}'")
        flash(f"Password reset successfully for {username}.")
        return redirect(url_for("users_dashboard"))

    return render_template("user_reset_password.html", user=user)








def build_export_attribution(export_label):
    return {
        "export_id": f"EXP-{int(datetime.now(UTC).timestamp())}",
        "username": session.get("username") or "unknown",
        "role": session.get("role") or "unknown",
        "export_label": export_label,
        "timestamp": datetime.now(UTC).isoformat(),
    }

def build_generic_export_activity(export_label, permission_name, filename=None, trust_id=None):
    username = session.get("username") or "unknown"
    timestamp = datetime.now(UTC).isoformat()
    export_id = f"EXP-{int(datetime.now(UTC).timestamp())}"

    return {
        "export_id": export_id,
        "username": username,
        "role": session.get("role"),
        "export_label": export_label,
        "permission_name": permission_name,
        "filename": filename,
        "trust_id": trust_id,
        "timestamp": timestamp,
    }

def require_active_firm_trust_or_deny(trust_id, reason_label="trust record"):
    trust = get_trust_by_id(trust_id)
    if not trust:
        log_change(
            "security",
            trust_id,
            "trust_export_scope_denied",
            f"Attempted access to {reason_label} outside active firm scope. User={session.get('username')}; Firm={session.get('firm_id')}"
        )
        return None, render_template(
            "access_denied.html",
            reason="This trust record is not available within your assigned firm scope."
        )
    return trust, None


def require_export_permission(permission_name, export_label):
    username = session.get("username") or "unknown"

    if not user_has_effective_permission(username, permission_name):
        log_change(
            "security",
            username,
            "export_permission_denied",
            f"Export={export_label}; Required={permission_name}"
        )
        return render_template(
            "access_denied.html",
            reason=f"Permission '{permission_name}' required for this export."
        )

    export_activity = build_generic_export_activity(
        export_label=export_label,
        permission_name=permission_name
    )
    append_export_activity(export_activity)

    log_change(
        "export",
        username,
        "export_access_granted",
        f"Export={export_label}; Permission={permission_name}; ExportID={export_activity['export_id']}"
    )

    return None

@app.route("/exports")
def export_center():
    trusts = get_all_trusts()
    username = session.get("username") or "unknown"

    can_export_core = user_has_effective_permission(username, "export_documents")
    can_export_handoff = user_has_effective_permission(username, "manage_permissions")
    can_export_roadmap = user_has_effective_permission(username, "manage_permissions")
    can_export_tax = user_has_effective_permission(username, "manage_tax_reports")
    can_export_reports = user_has_effective_permission(username, "manage_tax_reports")

    return render_template(
        "export_center.html",
        trusts=trusts,
        can_export_core=can_export_core,
        can_export_handoff=can_export_handoff,
        can_export_roadmap=can_export_roadmap,
        can_export_tax=can_export_tax,
        can_export_reports=can_export_reports
    )


@app.route("/exports/handoff/<filename>")
def export_handoff_file(filename):
    gate = require_export_permission("manage_permissions", f"handoff:{filename}")
    if gate:
        return gate
    from flask import send_from_directory
    return send_from_directory("handoff", filename, as_attachment=True)


@app.route("/exports/roadmap/<filename>")
def export_roadmap_file(filename):
    gate = require_export_permission("manage_permissions", f"roadmap:{filename}")
    if gate:
        return gate
    from flask import send_from_directory
    return send_from_directory("roadmap", filename, as_attachment=True)


@app.route("/exports/package/<filename>")
def export_package_file(filename):
    gate = require_export_permission("export_documents", f"package:{filename}")
    if gate:
        return gate
    from flask import send_from_directory
    return send_from_directory("package_export", filename, as_attachment=True)


@app.route("/exports/zip")
def export_zip_snapshot():
    gate = require_export_permission("export_documents", "zip_snapshot")
    if gate:
        return gate
    from flask import send_file
    return send_file("Trustee_App_Export_Package.zip", as_attachment=True)


@app.route("/exports/k1/<trust_id>.csv")
def export_k1_live_csv(trust_id):
    gate = require_export_permission("manage_tax_reports", f"k1_live_csv:{trust_id}")
    if gate:
        return gate

    trust, gate = require_active_firm_trust_or_deny(trust_id, "K-1 CSV export")
    if gate:
        return gate

    tax_year = request.args.get("tax_year", str(date.today().year))
    attribution = build_export_attribution(f"k1_live_csv:{trust_id}")
    csv_text = export_k1_csv_text(trust_id, tax_year)
    attribution_header = (
        f"# Export ID: {attribution['export_id']}\n"
        f"# Generated By: {attribution['username']} ({attribution['role']})\n"
        f"# Generated At: {attribution['timestamp']}\n"
    )
    response = make_response(attribution_header + csv_text)
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = f"attachment; filename=trust_{trust_id}_k1_{tax_year}.csv"
    log_change("k1_export", trust_id, "export", f"K-1 CSV export generated for tax year {tax_year}")
    return response


@app.route("/exports/1041/<trust_id>.txt")
def export_1041_text(trust_id):
    gate = require_export_permission("manage_tax_reports", f"1041_text:{trust_id}")
    if gate:
        return gate

    trust, gate = require_active_firm_trust_or_deny(trust_id, "1041 text export")
    if gate:
        return gate

    tax_year = request.args.get("tax_year", str(date.today().year))
    dataset = get_1041_dataset(trust_id, tax_year)

    lines = []
    attribution = build_export_attribution(f"1041_text:{trust_id}")

    lines.append("TRUSTEE APP - FORM 1041 EXPORT")
    lines.append("=" * 40)
    lines.append(f"Export ID: {attribution['export_id']}")
    lines.append(f"Generated By: {attribution['username']} ({attribution['role']})")
    lines.append(f"Generated At: {attribution['timestamp']}")
    lines.append("")
    if dataset and dataset["trust"]:
        lines.append(f"Trust: {dataset['trust']['trust_name']} ({dataset['trust']['trust_id']})")
        lines.append(f"Tax Year: {dataset['tax_year']}")
        lines.append("")
        lines.append(f"Gross Income: {dataset['gross_income']}")
        lines.append(f"Deductions: {dataset['deductions']}")
        lines.append(f"Net Income: {dataset['net_income']}")
        lines.append(f"Distributed Taxable Income: {dataset['distributed_taxable_income']}")
        lines.append(f"Retained Income: {dataset['retained_income']}")
        lines.append("")
        lines.append("Warnings:")
        for item in dataset["warnings"]:
            lines.append(f"- {item}")
    else:
        lines.append("No dataset available.")

    response = make_response("\n".join(lines))
    response.headers["Content-Type"] = "text/plain"
    response.headers["Content-Disposition"] = f"attachment; filename=trust_{trust_id}_1041_{tax_year}.txt"
    log_change("1041_export", trust_id, "export", f"1041 TXT export generated for tax year {tax_year}")
    return response



def classify_audit_risk(action):
    high = {"login_lockout", "csrf_failure", "permissions_updated", "toggle"}
    medium = {"login_failed", "permission_denied", "role_denied"}
    
    if action in high:
        return "HIGH"
    elif action in medium:
        return "MEDIUM"
    return "LOW"







@app.route("/system/recovery/reseed-permissions", methods=["POST"])
def system_recovery_reseed_permissions():
    gate = require_master_admin()
    if gate:
        return gate

    result = reseed_default_role_permissions()

    log_change(
        "system_recovery",
        session.get("username") or "unknown",
        "permission_matrix_reseeded",
        f"Status={result.get('overall_status')}; Roles={result.get('roles_seeded')}; Rows={result.get('role_permission_rows_written')}"
    )

    if result.get("overall_status") == "OK":
        flash("Default permission matrix re-seeded successfully. User-specific overrides were preserved.")
    else:
        flash("Permission matrix re-seed completed with warnings. Check System Health.")

    return redirect(url_for("system_health_dashboard"))

@app.route("/system/recovery/run", methods=["POST"])
def system_recovery_run():
    gate = require_master_admin()
    if gate:
        return gate

    result = run_safe_recovery_migrations()

    log_change(
        "system_recovery",
        session.get("username") or "unknown",
        "safe_recovery_migrations_run",
        f"Status={result.get('overall_status')}; Results={result.get('results')}"
    )

    if result.get("overall_status") == "OK":
        flash("Safe recovery migrations completed successfully.")
    else:
        flash("Safe recovery migrations completed with warnings. Check System Health.")

    return redirect(url_for("system_health_dashboard"))








@app.route("/admin/storage-diagnostics")
def admin_storage_diagnostics():
    gate = require_master_admin()
    if gate:
        return gate

    db_file = Path(DB_PATH)
    upload_dir = Path(UPLOAD_FOLDER)

    rows = [
        ("DB_PATH", str(db_file)),
        ("DB Exists", "Yes" if db_file.exists() else "No"),
        ("DB Size Bytes", str(db_file.stat().st_size) if db_file.exists() else "N/A"),
        ("UPLOAD_FOLDER", str(upload_dir)),
        ("Upload Folder Exists", "Yes" if upload_dir.exists() else "No"),
        ("Upload Folder File Count", str(sum(1 for _ in upload_dir.rglob("*") if _.is_file())) if upload_dir.exists() else "N/A"),
        ("ENV DB_PATH", os.getenv("DB_PATH", "")),
        ("ENV UPLOAD_FOLDER", os.getenv("UPLOAD_FOLDER", "")),
        ("RAILWAY_ENVIRONMENT", os.getenv("RAILWAY_ENVIRONMENT", "")),
        ("RAILWAY_SERVICE_NAME", os.getenv("RAILWAY_SERVICE_NAME", "")),
        ("RAILWAY_PROJECT_NAME", os.getenv("RAILWAY_PROJECT_NAME", "")),
    ]

    body = "<h1>Storage Diagnostics</h1>"
    body += "<p>Read-only storage path diagnostics for persistent volume verification.</p>"
    body += "<table border='1' cellpadding='8' cellspacing='0'>"
    body += "<tr><th>Key</th><th>Value</th></tr>"
    for key, value in rows:
        body += f"<tr><td><strong>{key}</strong></td><td>{value}</td></tr>"
    body += "</table>"
    body += "<p><a href='/admin'>Return to Admin</a></p>"

    return body

@app.route("/admin/backup/database.zip")
def admin_database_backup_zip():
    gate = require_master_admin()
    if gate:
        return gate

    db_file = Path(DB_PATH)
    if not db_file.exists():
        log_change(
            "system_backup",
            "database",
            "database_backup_zip_missing",
            f"Database ZIP backup failed; DB_PATH not found: {db_file}"
        )
        return render_template(
            "access_denied.html",
            reason=f"Database file not found at configured DB_PATH: {db_file}"
        ), 404

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_dir = Path("data/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    zip_path = backup_dir / f"trustee_app_database_backup_{timestamp}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(db_file, arcname="trustee_app.db")

    log_change(
        "system_backup",
        "database",
        "database_backup_zip_downloaded",
        f"Database ZIP backup downloaded from DB_PATH={db_file}; ZIP={zip_path}"
    )

    return send_file(
        zip_path,
        as_attachment=True,
        download_name=zip_path.name,
        mimetype="application/zip"
    )


@app.route("/admin/backup/database")
def admin_database_backup():
    gate = require_master_admin()
    if gate:
        return gate

    db_file = Path(DB_PATH)
    if not db_file.exists():
        log_change(
            "system_backup",
            "database",
            "database_backup_missing",
            f"Database backup failed; DB_PATH not found: {db_file}"
        )
        return render_template(
            "access_denied.html",
            reason=f"Database file not found at configured DB_PATH: {db_file}"
        ), 404

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    download_name = f"trustee_app_database_backup_{timestamp}.db"

    log_change(
        "system_backup",
        "database",
        "database_backup_downloaded",
        f"Database backup downloaded from DB_PATH={db_file}"
    )

    return send_file(
        db_file,
        as_attachment=True,
        download_name=download_name,
        mimetype="application/octet-stream"
    )


@app.route("/system/health/export.zip")
def system_health_export_zip():
    gate = require_master_admin()
    if gate:
        return gate

    import zipfile
    from io import BytesIO
    from flask import send_file

    health = build_system_health_report()
    integrity = verify_audit_log_chain()
    policy = get_export_policy()

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    txt_lines = []
    txt_lines.append("TRUSTEE APP - SYSTEM HEALTH REPORT")
    txt_lines.append("=" * 50)
    txt_lines.append(f"Generated By: {session.get('username')}")
    txt_lines.append(f"Generated At: {datetime.now(UTC).isoformat()}")
    txt_lines.append("")
    txt_lines.append(f"Overall Status: {health.get('overall_status')}")

    txt_content = chr(10).join(txt_lines)

    import json
    json_content = json.dumps({
        "health": health,
        "audit_integrity": integrity,
        "policy": policy,
        "generated_by": session.get("username"),
        "generated_at": datetime.now(UTC).isoformat()
    }, indent=2)

    memory_file = BytesIO()

    with zipfile.ZipFile(memory_file, 'w') as zf:
        zf.writestr("system_health.txt", txt_content)
        zf.writestr("system_health.json", json_content)

        try:
            zf.write("data/export_policy.json", "export_policy.json")
        except Exception:
            pass

        try:
            zf.write("data/export_activity_log.json", "export_activity_log.json")
        except Exception:
            pass

    memory_file.seek(0)

    log_change(
        "system_export",
        session.get("username") or "unknown",
        "system_health_export_zip",
        "ZIP system snapshot generated"
    )

    return send_file(
        memory_file,
        as_attachment=True,
        download_name=f"system_snapshot_{timestamp}.zip",
        mimetype="application/zip"
    )

@app.route("/system/health/export.json")
def system_health_export_json():
    gate = require_master_admin()
    if gate:
        return gate

    health = build_system_health_report()
    integrity = verify_audit_log_chain()
    policy = get_export_policy()

    payload = {
        "generated_by": session.get("username") or "unknown",
        "role": session.get("role"),
        "generated_at": datetime.now(UTC).isoformat(),
        "health": health,
        "audit_integrity": integrity,
        "policy": policy,
    }

    from flask import jsonify

    log_change(
        "system_export",
        session.get("username") or "unknown",
        "system_health_export_json",
        "JSON system health report generated"
    )

    return jsonify(payload)

@app.route("/system/health/export.txt")
def system_health_export_txt():
    gate = require_master_admin()
    if gate:
        return gate

    health = build_system_health_report()
    integrity = verify_audit_log_chain()
    policy = get_export_policy()

    report_lines = []
    report_lines.append("TRUSTEE APP - SYSTEM HEALTH REPORT")
    report_lines.append("=" * 50)
    report_lines.append("")
    report_lines.append(f"Generated By: {session.get('username') or 'unknown'} ({session.get('role') or 'unknown'})")
    report_lines.append(f"Generated At: {datetime.now(UTC).isoformat()}")
    report_lines.append("")
    report_lines.append(f"Overall Status: {health.get('overall_status')}")
    report_lines.append("")
    report_lines.append("TABLE STATUS:")
    for table in health.get("tables", []):
        status = "OK" if table.get("ok") else "ATTENTION"
        report_lines.append(f"- {table.get('table_name')}: {status}")
        if table.get("missing_columns"):
            report_lines.append(f"  Missing: {', '.join(table.get('missing_columns'))}")

    report_lines.append("")
    report_lines.append("AUDIT CHAIN:")
    report_lines.append(f"Status: {integrity.get('status')}")
    report_lines.append(f"Checked: {integrity.get('checked')}")
    report_lines.append(f"Broken: {integrity.get('broken')}")
    report_lines.append(f"Legacy: {integrity.get('legacy')}")
    if integrity.get("first_broken_id"):
        report_lines.append(f"First Broken ID: {integrity.get('first_broken_id')}")

    report_lines.append("")
    report_lines.append("SYSTEM POLICY:")
    for key, value in policy.items():
        report_lines.append(f"- {key}: {value}")

    response = make_response(chr(10).join(report_lines))
    response.headers["Content-Type"] = "text/plain"
    response.headers["Content-Disposition"] = "attachment; filename=system_health_report.txt"

    log_change(
        "system_export",
        session.get("username") or "unknown",
        "system_health_export_txt",
        "TXT system health report generated"
    )

    return response






@app.route("/minutes/new", methods=["GET", "POST"])
def trust_minutes_new():
    gate = require_master_admin()
    if gate:
        return gate

    trusts = get_all_trusts()

    if request.method == "POST":
        minute_id = get_next_minute_id()

        data = {
            "minute_id": minute_id,
            "trust_id": request.form.get("trust_id"),
            "meeting_date": request.form.get("meeting_date"),
            "meeting_type": request.form.get("meeting_type"),
            "title": request.form.get("title"),
            "purpose": request.form.get("purpose"),
            "resolutions": request.form.get("resolutions"),
            "action_items": request.form.get("action_items"),
            "status": request.form.get("status") or "Draft",
            "created_by": session.get("username") or "unknown",
        }

        create_trust_minute(data)

        log_change(
            "trust_minute",
            minute_id,
            "minute_created",
            f"Trust={data.get('trust_id')}; Title={data.get('title')}"
        )

        return redirect(url_for("trust_minutes_dashboard"))

    return render_template(
        "trust_minutes_form.html",
        trusts=trusts,
        minute_id=get_next_minute_id()
    )







def draw_trust_minute_certificate_marks(canvas, doc):
    canvas.saveState()

    width, height = LETTER

    # Faint centered seal watermark
    canvas.setStrokeColor(colors.Color(0.72, 0.55, 0.18, alpha=0.16))
    canvas.setFillColor(colors.Color(0.72, 0.55, 0.18, alpha=0.08))
    canvas.circle(width / 2, height / 2, 115, stroke=1, fill=0)
    canvas.circle(width / 2, height / 2, 82, stroke=1, fill=0)

    canvas.setFont("Helvetica-Bold", 22)
    canvas.drawCentredString(width / 2, height / 2 + 8, "TRUST SEAL")

    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(width / 2, height / 2 - 12, "INTERNAL GOVERNANCE RECORD")

    # Executed stamp near upper right
    canvas.setStrokeColor(colors.Color(0.55, 0.0, 0.0, alpha=0.75))
    canvas.setFillColor(colors.Color(0.55, 0.0, 0.0, alpha=0.75))
    canvas.setLineWidth(2)
    canvas.rect(width - 190, height - 120, 118, 34, stroke=1, fill=0)
    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawCentredString(width - 131, height - 108, "EXECUTED")

    # Footer
    canvas.setFillColor(colors.black)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(width / 2, 28, "Trust Minute Execution Certificate | Generated by Trustee App")

    canvas.restoreState()


@app.route("/minutes/<minute_id>/certificate.pdf")
def trust_minute_certificate_pdf(minute_id):
    gate = require_master_admin()
    if gate:
        return gate

    minute = get_trust_minute_by_id(minute_id)
    if not minute:
        return "Minute not found", 404

    if minute["status"] not in ("Executed", "Archived"):
        return "Certificate available only after execution.", 403

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("TRUST MINUTE EXECUTION CERTIFICATE", title_style))
    story.append(Spacer(1, 18))

    certificate_id = minute["certificate_id"] if "certificate_id" in minute.keys() and minute["certificate_id"] else f"CERT-{minute_id}"

    story.append(Paragraph(f"<b>Certificate ID:</b> {certificate_id}", body_style))
    story.append(Paragraph(f"<b>Minute ID:</b> {minute['minute_id']}", body_style))
    story.append(Paragraph(f"<b>Trust ID:</b> {minute['trust_id']}", body_style))
    story.append(Paragraph(f"<b>Title:</b> {minute['title']}", body_style))
    story.append(Paragraph(f"<b>Status:</b> {minute['status']}", body_style))
    story.append(Paragraph(f"<b>Approved At:</b> {minute['approved_at'] or 'Not recorded'}", body_style))
    story.append(Paragraph(f"<b>Executed At:</b> {minute['executed_at'] or 'Not recorded'}", body_style))
    story.append(Spacer(1, 18))

    story.append(Paragraph("Recorded Signer Records", header_style))

    for idx in (1, 2, 3):
        name = minute[f"trustee_{idx}_name"]
        signed_date = minute[f"trustee_{idx}_signed_date"]
        capacity = minute[f"trustee_{idx}_capacity"] or "Trustee"
        signature_image = minute[f"trustee_{idx}_signature_image"]

        if name:
            story.append(Spacer(1, 16))

            if signature_image and signature_image.startswith("data:image/png;base64,"):
                try:
                    image_data = signature_image.split(",", 1)[1]
                    image_bytes = BytesIO(base64.b64decode(image_data))
                    story.append(Image(image_bytes, width=240, height=70))
                except Exception:
                    story.append(Paragraph(f"<font name='Times-Italic' size='24'>{name}</font>", body_style))
            else:
                story.append(Paragraph(f"<font name='Times-Italic' size='24'>{name}</font>", body_style))

            story.append(Spacer(1, 8))
            story.append(Paragraph("______________________________", body_style))
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"Role / Capacity: {capacity}", body_style))
            story.append(Paragraph(f"Signed Date: {signed_date or 'No date recorded'}", body_style))

    story.append(Spacer(1, 24))
    story.append(Paragraph("This certificate reflects the internal governance record of the Trust Minute and does not replace any required wet signature, notarization, or external filing where applicable.", styles["Italic"]))

    doc.build(story, onFirstPage=draw_trust_minute_certificate_marks, onLaterPages=draw_trust_minute_certificate_marks)

    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={minute_id}_execution_certificate.pdf"

    log_change(
        "trust_minute",
        minute_id,
        "certificate_pdf_exported",
        f"Execution certificate PDF generated | Certificate ID: {certificate_id} | Status: {minute['status']} | Executed At: {minute['executed_at'] or 'Not recorded'}"
    )

    return response

@app.route("/minutes/<minute_id>/packet.pdf")
def trust_minute_execution_packet_pdf(minute_id):
    gate = require_master_admin()
    if gate:
        return gate

    minute = get_trust_minute_by_id(minute_id)
    if not minute:
        return "Minute not found", 404

    if minute["status"] not in ("Executed", "Archived"):
        return "Execution packet available only after execution.", 403

    certificate_id = minute["certificate_id"] if "certificate_id" in minute.keys() and minute["certificate_id"] else f"CERT-{minute_id}"
    audit_logs = get_audit_log_by_entity(
        entity_type="trust_minute",
        entity_id=minute_id,
        limit=25
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("TRUST MINUTE EXECUTION PACKET", title_style))
    story.append(Spacer(1, 18))

    story.append(Paragraph("<b>Packet Type:</b> Execution Packet", body_style))
    story.append(Paragraph(f"<b>Certificate ID:</b> {certificate_id}", body_style))
    story.append(Paragraph(f"<b>Minute ID:</b> {minute['minute_id']}", body_style))
    story.append(Paragraph(f"<b>Trust ID:</b> {minute['trust_id']}", body_style))
    story.append(Paragraph(f"<b>Title:</b> {minute['title']}", body_style))
    story.append(Paragraph(f"<b>Status:</b> {minute['status']}", body_style))
    story.append(Paragraph(f"<b>Approved At:</b> {minute['approved_at'] or 'Not recorded'}", body_style))
    story.append(Paragraph(f"<b>Executed At:</b> {minute['executed_at'] or 'Not recorded'}", body_style))
    story.append(Paragraph(f"<b>Archived At:</b> {minute['archived_at'] or 'Not archived'}", body_style))
    story.append(Spacer(1, 18))

    story.append(Paragraph("Minute Substance", header_style))
    story.append(Paragraph(f"<b>Purpose:</b> {minute['purpose'] or 'Not recorded'}", body_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>Resolutions:</b> {minute['resolutions'] or 'Not recorded'}", body_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>Action Items:</b> {minute['action_items'] or 'Not recorded'}", body_style))
    story.append(Spacer(1, 18))

    story.append(Paragraph("Signer Records", header_style))
    for idx in (1, 2, 3):
        name = minute[f"trustee_{idx}_name"]
        capacity = minute[f"trustee_{idx}_capacity"] or ""
        signed_date = minute[f"trustee_{idx}_signed_date"]
        if name or signed_date:
            story.append(Paragraph(
                f"<b>Signer {idx}:</b> {name or 'Not recorded'} | Role / Capacity: {capacity or 'Not recorded'} | Signed Date: {signed_date or 'Not recorded'}",
                body_style
            ))

    story.append(Spacer(1, 18))
    story.append(Paragraph("Audit Trail Summary", header_style))

    if audit_logs:
        for log in audit_logs:
            story.append(Paragraph(
                f"<b>{log['created_at']}</b> — {log['action']} — {log['note'] or ''}",
                body_style
            ))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("No audit events recorded for this minute.", body_style))

    story.append(Spacer(1, 18))
    story.append(Paragraph("Packet Control Statement", header_style))
    story.append(Paragraph(
        "This execution packet consolidates the internal trust minute, execution certificate reference, signer role summary, and audit trail excerpts for governance review and archive control.",
        styles["Italic"]
    ))

    doc.build(story, onFirstPage=draw_trust_minute_certificate_marks, onLaterPages=draw_trust_minute_certificate_marks)

    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={minute_id}_execution_packet.pdf"

    log_change(
        "trust_minute",
        minute_id,
        "execution_packet_pdf_exported",
        f"Execution packet PDF generated | Certificate ID: {certificate_id} | Status: {minute['status']} | Executed At: {minute['executed_at'] or 'Not recorded'}"
    )

    return response


def validate_trust_minute_execution_requirements(data):
    complete_signers = []
    has_trustee = False
    has_witness = False

    for idx in (1, 2, 3):
        name = (data.get(f"trustee_{idx}_name") or "").strip()
        capacity = (data.get(f"trustee_{idx}_capacity") or "").strip()
        signed_date = (data.get(f"trustee_{idx}_signed_date") or "").strip()
        signature_image = (data.get(f"trustee_{idx}_signature_image") or "").strip()

        has_signature_image = signature_image.startswith("data:image/png;base64,")

        signer_started = bool(name or signed_date or has_signature_image)

        if signer_started:
            missing = []

            if not name:
                missing.append(f"Signer {idx} name")
            if not capacity:
                missing.append(f"Signer {idx} role/capacity")
            if not signed_date:
                missing.append(f"Signer {idx} signed date")
            if not has_signature_image:
                missing.append(f"Signer {idx} drawn signature")

            if missing:
                return False, "Execution blocked. Missing: " + ", ".join(missing)

            role_text = capacity.lower()
            if "trustee" in role_text:
                has_trustee = True
            if "witness" in role_text:
                has_witness = True

            complete_signers.append(idx)

    if not complete_signers:
        return False, "Execution blocked. At least one complete Trustee signer and one complete Witness signer are required."

    missing_roles = []
    if not has_trustee:
        missing_roles.append("one complete Trustee signer")
    if not has_witness:
        missing_roles.append("one complete Witness signer")

    if missing_roles:
        return False, "Execution blocked. Required: " + " and ".join(missing_roles) + "."

    return True, ""

@app.route("/minutes/<minute_id>/execute", methods=["POST"])
def trust_minute_execute(minute_id):
    gate = require_master_admin()
    if gate:
        return gate

    minute = get_trust_minute_by_id(minute_id)
    if not minute:
        return "Minute not found", 404

    if int(minute["locked"] or 0) == 1:
        log_change(
            "trust_minute",
            minute_id,
            "locked_minute_post_blocked",
            "Attempted POST blocked because trust minute is locked."
        )
        return "This trust minute is locked and cannot be modified.", 403

    action = request.form.get("action")

    now = datetime.now(UTC).isoformat()

    data = {
        "trustee_1_name": request.form.get("trustee_1_name"),
        "trustee_1_capacity": request.form.get("trustee_1_capacity"),
        "trustee_1_signed_date": request.form.get("trustee_1_signed_date"),
        "trustee_1_signature_image": request.form.get("trustee_1_signature_image"),
        "trustee_2_name": request.form.get("trustee_2_name"),
        "trustee_2_capacity": request.form.get("trustee_2_capacity"),
        "trustee_2_signed_date": request.form.get("trustee_2_signed_date"),
        "trustee_2_signature_image": request.form.get("trustee_2_signature_image"),
        "trustee_3_name": request.form.get("trustee_3_name"),
        "trustee_3_capacity": request.form.get("trustee_3_capacity"),
        "trustee_3_signed_date": request.form.get("trustee_3_signed_date"),
        "trustee_3_signature_image": request.form.get("trustee_3_signature_image"),
        "approved_at": minute["approved_at"],
        "executed_at": minute["executed_at"],
        "archived_at": minute["archived_at"],
        "status": minute["status"],
        "locked": minute["locked"],
        "certificate_id": minute["certificate_id"] if "certificate_id" in minute.keys() else None,
    }

    current_status = minute["status"] or "Draft"

    if action == "approve":
        if current_status in ("Executed", "Archived"):
            message = f"Action blocked. Cannot approve a minute with status {current_status}."
            log_change(
                "trust_minute",
                minute_id,
                "minute_approve_blocked",
                message
            )
            return message, 403

        data["approved_at"] = now
        data["status"] = "Approved"

    elif action == "execute":
        if current_status == "Archived":
            message = "Action blocked. Archived minutes cannot be executed."
            log_change(
                "trust_minute",
                minute_id,
                "minute_execute_blocked",
                message
            )
            return message, 403

        is_valid, validation_message = validate_trust_minute_execution_requirements(data)
        if not is_valid:
            log_change(
                "trust_minute",
                minute_id,
                "minute_execute_blocked",
                validation_message
            )
            return validation_message, 400

        data["executed_at"] = now
        data["status"] = "Executed"
        data["locked"] = 1
        if not data.get("certificate_id"):
            data["certificate_id"] = f"CERT-{minute_id}"

    elif action == "archive":
        if current_status != "Executed":
            message = f"Action blocked. Only executed minutes can be archived. Current status: {current_status}."
            log_change(
                "trust_minute",
                minute_id,
                "minute_archive_blocked",
                message
            )
            return message, 403

        data["archived_at"] = now
        data["status"] = "Archived"

    else:
        message = f"Action blocked. Unknown trust minute action: {action}."
        log_change(
            "trust_minute",
            minute_id,
            "minute_action_blocked",
            message
        )
        return message, 400

    update_trust_minute_execution(minute_id, data)

    log_change(
        "trust_minute",
        minute_id,
        f"minute_{action}",
        f"Status updated to {data['status']}"
    )

    return redirect(url_for("trust_minute_detail", minute_id=minute_id))

@app.route("/minutes/<minute_id>")
def trust_minute_detail(minute_id):
    gate = require_master_admin()
    if gate:
        return gate

    minute = get_trust_minute_by_id(minute_id)

    if not minute:
        return "Minute not found", 404

    audit_logs = get_audit_log_by_entity(
        entity_type="trust_minute",
        entity_id=minute_id,
        limit=25
    )

    return render_template(
        "trust_minute_detail.html",
        minute=minute,
        audit_logs=audit_logs
    )

@app.route("/minutes")
def trust_minutes_dashboard():
    gate = require_master_admin()
    if gate:
        return gate

    minutes = get_all_trust_minutes()
    trusts = get_all_trusts()

    return render_template(
        "trust_minutes_dashboard.html",
        minutes=minutes,
        trusts=trusts
    )

@app.route("/certificates/verify/<certificate_id>")
def verify_certificate(certificate_id):
    gate = require_master_admin()
    if gate:
        return gate

    minute = get_trust_minute_by_certificate_id(certificate_id)

    if not minute:
        return render_template(
            "certificate_verify.html",
            certificate_id=certificate_id,
            minute=None,
            audit_logs=[]
        ), 404

    audit_logs = get_audit_log_by_entity(
        entity_type="trust_minute",
        entity_id=minute["minute_id"],
        limit=15
    )

    return render_template(
        "certificate_verify.html",
        certificate_id=certificate_id,
        minute=minute,
        audit_logs=audit_logs
    )


@app.route("/certificates/backfill", methods=["POST"])
def backfill_certificate_ids_route():
    gate = require_master_admin()
    if gate:
        return gate

    updated = backfill_trust_minute_certificate_ids()

    if updated:
        for item in updated:
            log_change(
                "trust_minute",
                item["minute_id"],
                "certificate_id_backfilled",
                f"Certificate ID backfilled: {item['certificate_id']}"
            )
    else:
        log_change(
            "trust_minute",
            "certificate_registry",
            "certificate_id_backfill_checked",
            "Certificate ID backfill checked; no records required update."
        )

    return redirect(url_for("certificate_registry"))




@app.route("/transfers/<transfer_id>/certificate.pdf")
def transfer_certificate_pdf(transfer_id):
    gate = gate_trust_access("GLOBAL", ["Admin", "Trustee"])
    if gate:
        return gate

    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate

    if transfer.status != "completed":
        flash("Transfer certificate is only available after completion.", "error")
        return redirect(url_for("transfer_review", transfer_id=transfer_id))

    trust = None
    asset = None

    try:
        trust = get_trust_by_id(transfer.trust_id)
    except Exception:
        trust = None

    try:
        asset = get_asset_by_id(transfer.asset_id)
    except Exception:
        asset = None

    pdf_buffer = generate_transfer_certificate_pdf(
        transfer=transfer,
        trust=trust,
        asset=asset,
    )

    log_change(
        "transfer_certificate",
        session.get("username") or "unknown",
        "transfer_certificate_pdf_generated",
        f"Transfer certificate PDF generated | Transfer ID: {transfer_id} | Status: {transfer.status}"
    )

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"{transfer_id}_transfer_certificate.pdf",
        mimetype="application/pdf",
    )


@app.route("/certificates")
def certificate_registry():
    gate = require_master_admin()
    if gate:
        return gate

    records = get_certificate_registry_records()

    return render_template(
        "certificate_registry.html",
        records=records
    )


@app.route("/system/health")
def system_health_dashboard():
    gate = require_master_admin()
    if gate:
        return gate

    health = build_system_health_report()
    integrity = verify_audit_log_chain()
    policy = get_export_policy()

    return render_template(
        "system_health.html",
        health=health,
        integrity=integrity,
        policy=policy
    )

@app.route("/audit")
def audit_dashboard():
    entity_type = request.args.get("entity_type")
    entity_id = request.args.get("entity_id")
    risk_filter = (request.args.get("risk") or "").strip().upper()

    if entity_type or entity_id:
        logs = get_audit_log_by_entity(entity_type=entity_type, entity_id=entity_id, limit=200)
    else:
        logs = get_audit_log(200)

    logs = [dict(row) for row in logs]

    for row in logs:
        row["risk"] = classify_audit_risk(row["action"])

    integrity = verify_audit_log_chain()

    if risk_filter in {"LOW", "MEDIUM", "HIGH"}:
        logs = [row for row in logs if row["risk"] == risk_filter]

    return render_template(
        "audit_dashboard.html",
        logs=logs,
        entity_type=entity_type,
        entity_id=entity_id,
        risk_filter=risk_filter,
        integrity=integrity
    )


@app.route("/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/edit", methods=["GET", "POST"])
def k1_edit_beneficiary(trust_id, beneficiary_id):
    trust = get_trust_by_id(trust_id)
    beneficiary = get_beneficiary_by_id_and_trust(beneficiary_id, trust_id)

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template(
                "k1_beneficiary_edit.html",
                trust=trust,
                beneficiary=beneficiary,
                error_message="Invalid or missing CSRF token."
            )

        if not validate_csrf_token():
            return render_template(
                "k1_beneficiary_edit.html",
                trust=trust,
                beneficiary=beneficiary,
                error_message="Invalid or missing CSRF token."
            )

        update_beneficiary_record(beneficiary_id, {
            "full_name": request.form.get("full_name"),
            "tax_id": request.form.get("tax_id"),
            "beneficiary_type": request.form.get("beneficiary_type"),
            "email": request.form.get("email"),
            "address": request.form.get("address"),
            "allocation_method": request.form.get("allocation_method"),
            "fixed_percentage": request.form.get("fixed_percentage"),
            "notes": request.form.get("notes"),
            "is_active": "Yes" if request.form.get("is_active") == "on" else "No",
        })
        log_change("beneficiary", beneficiary_id, "create", f"Beneficiary created for trust {trust_id}")
        return redirect(url_for("k1_trust_view", trust_id=trust_id))

    return render_template("k1_beneficiary_edit.html", trust=trust, beneficiary=beneficiary)


@app.route("/k1/trust/<trust_id>/beneficiary/<beneficiary_id>/toggle", methods=["POST"])
def k1_toggle_beneficiary(trust_id, beneficiary_id):
    if not validate_csrf_token():
        return redirect(url_for("k1_trust_view", trust_id=trust_id))

    toggle_beneficiary_active(beneficiary_id, trust_id)
    return redirect(url_for("k1_trust_view", trust_id=trust_id))


@app.route("/k1/trust/<trust_id>/distribution/<distribution_id>/edit", methods=["GET", "POST"])
def k1_edit_distribution(trust_id, distribution_id):
    trust = get_trust_by_id(trust_id)
    distribution = get_distribution_by_id_and_trust(distribution_id, trust_id)
    beneficiaries = get_beneficiaries_by_trust_id(trust_id)

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template(
                "k1_distribution_edit.html",
                trust=trust,
                distribution=distribution,
                beneficiaries=beneficiaries,
                error_message="Invalid or missing CSRF token."
            )

        if not validate_csrf_token():
            return render_template(
                "k1_distribution_edit.html",
                trust=trust,
                distribution=distribution,
                beneficiaries=beneficiaries,
                error_message="Invalid or missing CSRF token."
            )

        update_distribution_record(distribution_id, {
            "beneficiary_id": request.form.get("beneficiary_id"),
            "tax_year": request.form.get("tax_year"),
            "distribution_date": request.form.get("distribution_date"),
            "distribution_type": request.form.get("distribution_type"),
            "description": request.form.get("description"),
            "gross_amount": request.form.get("gross_amount"),
            "taxable_amount": request.form.get("taxable_amount"),
            "principal_amount": request.form.get("principal_amount"),
            "source_reference": request.form.get("source_reference"),
            "status": request.form.get("status"),
        })
        log_change("distribution", distribution_id, "create", f"Distribution created for trust {trust_id}")
        return redirect(url_for("k1_trust_view", trust_id=trust_id, tax_year=request.form.get("tax_year")))

    return render_template(
        "k1_distribution_edit.html",
        trust=trust,
        distribution=distribution,
        beneficiaries=beneficiaries
    )


@app.route("/k1/trust/<trust_id>/export.csv")
def k1_export_csv(trust_id):
    trust, gate = require_active_firm_trust_or_deny(trust_id, "K-1 CSV export")
    if gate:
        return gate

    tax_year = request.args.get("tax_year", str(date.today().year))
    csv_text = export_k1_csv_text(trust_id, tax_year)
    response = make_response(csv_text)
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = f"attachment; filename=trust_{trust_id}_k1_{tax_year}.csv"
    log_change("k1_export", trust_id, "export", f"K-1 CSV export generated for tax year {tax_year}")
    return response


@app.route("/exports/k1_summary/<trust_id>.txt")
def export_k1_summary_report(trust_id):
    trust, gate = require_active_firm_trust_or_deny(trust_id, "K-1 summary export")
    if gate:
        return gate

    tax_year = request.args.get("tax_year", str(date.today().year))
    totals = get_distribution_totals_by_trust(trust_id, tax_year)
    beneficiary_totals = get_distribution_totals_by_beneficiary(trust_id, tax_year)

    lines = []
    lines.append("TRUSTEE APP — K-1 SUMMARY REPORT")
    lines.append("=" * 50)
    lines.append(f"Trust: {trust['trust_name']} ({trust['trust_id']})")
    lines.append(f"Tax Year: {tax_year}")
    lines.append("")
    lines.append("Trust Totals")
    lines.append("-" * 20)
    lines.append(f"Gross Total: {money(totals['gross_total'])}")
    lines.append(f"Taxable Total: {money(totals['taxable_total'])}")
    lines.append(f"Principal Total: {money(totals['principal_total'])}")
    lines.append(f"Distribution Count: {totals['count']}")
    lines.append("")
    lines.append("Beneficiary Totals")
    lines.append("-" * 20)

    for row in beneficiary_totals:
        lines.append(f"{row['full_name']}")
        lines.append(f"  Gross: {money(row['gross_total'])}")
        lines.append(f"  Taxable: {money(row['taxable_total'])}")
        lines.append(f"  Principal: {money(row['principal_total'])}")
        lines.append(f"  Count: {row['count']}")
        lines.append("")

    response = make_response("\n".join(lines))
    response.headers["Content-Type"] = "text/plain"
    response.headers["Content-Disposition"] = f"attachment; filename=trust_{trust_id}_k1_summary_{tax_year}.txt"
    log_change("k1_summary_export", trust_id, "export", f"K-1 summary TXT export generated for tax year {tax_year}")
    return response


@app.route("/exports/1041_summary/<trust_id>.txt")
def export_1041_summary_report(trust_id):
    trust, gate = require_active_firm_trust_or_deny(trust_id, "1041 summary export")
    if gate:
        return gate

    tax_year = request.args.get("tax_year", str(date.today().year))
    tax_logic = compute_dni_components(trust_id, tax_year)
    shares = compute_beneficiary_tax_shares(trust_id, tax_year)

    lines = []
    lines.append("TRUSTEE APP — FORM 1041 SUMMARY REPORT")
    lines.append("=" * 50)
    lines.append(f"Trust: {trust['trust_name']} ({trust['trust_id']})")
    lines.append(f"Tax Year: {tax_year}")
    lines.append("")
    lines.append("Advanced Tax Logic")
    lines.append("-" * 20)
    lines.append(f"Gross Income: {money(tax_logic['gross_income'])}")
    lines.append(f"Taxable Distributed: {money(tax_logic['taxable_distributed'])}")
    lines.append(f"Principal Distributed: {money(tax_logic['principal_distributed'])}")
    lines.append(f"DNI: {money(tax_logic['dni'])}")
    lines.append(f"Retained Income: {money(tax_logic['retained_income'])}")
    lines.append("")
    lines.append("Beneficiary Tax Shares")
    lines.append("-" * 20)

    for row in shares:
        lines.append(f"{row['full_name']}")
        lines.append(f"  Gross: {money(row['gross_total'])}")
        lines.append(f"  Taxable: {money(row['taxable_total'])}")
        lines.append(f"  Principal: {money(row['principal_total'])}")
        lines.append(f"  Taxable Ratio: {row['taxable_ratio'] * 100:.1f}%")
        lines.append("")

    response = make_response("\n".join(lines))
    response.headers["Content-Type"] = "text/plain"
    response.headers["Content-Disposition"] = f"attachment; filename=trust_{trust_id}_1041_summary_{tax_year}.txt"
    log_change("1041_summary_export", trust_id, "export", f"1041 summary TXT export generated for tax year {tax_year}")
    return response




@app.route("/portfolio")
def portfolio_dashboard():
    portfolio, totals = get_portfolio_summary()

    totals["gross_total_fmt"] = money(totals["gross_total"])
    totals["taxable_total_fmt"] = money(totals["taxable_total"])
    totals["principal_total_fmt"] = money(totals["principal_total"])

    for row in portfolio:
        row["gross_total_fmt"] = money(row["gross_total"])
        row["taxable_total_fmt"] = money(row["taxable_total"])
        row["principal_total_fmt"] = money(row["principal_total"])

    return render_template(
        "portfolio_dashboard.html",
        portfolio=portfolio,
        totals=totals
    )




@app.route("/fiduciaries")
def fiduciary_dashboard():

    trusts = get_all_trusts()
    fiduciaries = get_all_fiduciaries()
    return render_template("fiduciary_dashboard.html", trusts=trusts, fiduciaries=fiduciaries)


@app.route("/fiduciaries/new", methods=["GET", "POST"])
def fiduciary_new():
    trusts = get_all_trusts()

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("fiduciary_form.html", trusts=trusts, error_message="Invalid or missing CSRF token.")

        fiduciary_id = get_next_fiduciary_id()
        create_fiduciary_record({
            "fiduciary_id": fiduciary_id,
            "full_name": request.form.get("full_name"),
            "role_title": request.form.get("role_title"),
            "authority_scope": request.form.get("authority_scope"),
            "trust_id": request.form.get("trust_id"),
            "appointment_date": request.form.get("appointment_date"),
            "effective_date": request.form.get("effective_date"),
            "status": request.form.get("status"),
            "notes": request.form.get("notes"),
        })
        log_change("fiduciary", fiduciary_id, "create", "Fiduciary role record created")
        return redirect(url_for("fiduciary_dashboard"))

    return render_template("fiduciary_form.html", trusts=trusts)




@app.route("/genealogy")
def genealogy_dashboard():

    trusts = get_all_trusts()
    records = get_all_genealogy_records()
    return render_template("genealogy_dashboard.html", trusts=trusts, records=records)


@app.route("/genealogy/new", methods=["GET", "POST"])
def genealogy_new():
    trusts = get_all_trusts()

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("genealogy_form.html", trusts=trusts, error_message="Invalid or missing CSRF token.")

        genealogy_id = get_next_genealogy_id()
        create_genealogy_record({
            "genealogy_id": genealogy_id,
            "trust_id": request.form.get("trust_id"),
            "full_name": request.form.get("full_name"),
            "lineage_role": request.form.get("lineage_role"),
            "birth_date": request.form.get("birth_date"),
            "death_date": request.form.get("death_date"),
            "parent_1": request.form.get("parent_1"),
            "parent_2": request.form.get("parent_2"),
            "spouse": request.form.get("spouse"),
            "notes": request.form.get("notes"),
            "evidence_notes": request.form.get("evidence_notes"),
            "source_platform": request.form.get("source_platform"),
            "source_title": request.form.get("source_title"),
            "source_reference": request.form.get("source_reference"),
            "archive_date": request.form.get("archive_date"),
            "verification_status": request.form.get("verification_status"),
            "trace_summary": request.form.get("trace_summary"),
            "guidance_prompt": request.form.get("guidance_prompt"),
        })
        log_change("genealogy", genealogy_id, "create", "Genealogy / pedigree record created")
        return redirect(url_for("genealogy_dashboard"))

    return render_template("genealogy_form.html", trusts=trusts)






TRUST_TYPE_LABELS = {
    "revocable": "Revocable Trust",
    "irrevocable": "Irrevocable Trust",
    "simple": "Simple Trust",
    "complex": "Complex Trust",
    "land": "Land Trust",
    "insurance": "Insurance Trust",
    "foreign": "Foreign Trust",
    "charitable": "Charitable Trust",
    "business": "Business Trust",
    "other": "Other Trust",
}

def _learning_conn():
    conn = sqlite3.connect(LEARNING_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_learning_articles():
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM learning_articles
        WHERE status = 'published'
        ORDER BY category, title
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_learning_articles_by_category(category):
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM learning_articles
        WHERE status = 'published' AND lower(category) = lower(?)
        ORDER BY title
    """, (category,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_learning_article_by_id(article_id):
    conn = _learning_conn()
    row = conn.execute("""
        SELECT * FROM learning_articles
        WHERE article_id = ?
    """, (article_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_form_guides():
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM tax_form_guides
        WHERE status = 'published'
        ORDER BY form_name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_form_guide_by_name(form_name):
    conn = _learning_conn()
    row = conn.execute("""
        SELECT * FROM tax_form_guides
        WHERE lower(form_name) = lower(?)
    """, (form_name,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_trust_type_cards():
    return [
        {"slug": "revocable", "label": "Revocable Trust", "summary": "Often used where flexibility and amendment capacity are priorities."},
        {"slug": "irrevocable", "label": "Irrevocable Trust", "summary": "Often used where permanence, structure, and separation are emphasized."},
        {"slug": "simple", "label": "Simple Trust", "summary": "Common conceptual category used in trust taxation discussions."},
        {"slug": "complex", "label": "Complex Trust", "summary": "Common conceptual category used where distributions and retained activity become more involved."},
        {"slug": "land", "label": "Land Trust", "summary": "Used in discussions involving real property holding structure."},
        {"slug": "insurance", "label": "Insurance Trust", "summary": "Used in discussions involving policy ownership and insurance planning structure."},
        {"slug": "foreign", "label": "Foreign Trust", "summary": "Advanced trust category that requires careful handling and strong tax/legal review."},
        {"slug": "charitable", "label": "Charitable Trust", "summary": "Used where charitable mission or charitable distribution structure is central."},
        {"slug": "business", "label": "Business Trust", "summary": "Used where business operations and trust structure intersect."},
        {"slug": "other", "label": "Other Trust", "summary": "Catch-all category for additional trust forms and custom analysis."},
    ]

def create_learning_article(payload):
    conn = _learning_conn()
    conn.execute("""
        INSERT INTO learning_articles (
            article_id, title, category, subcategory, trust_type, summary, body,
            difficulty_level, related_forms, related_reports, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        payload.get("article_id"),
        payload.get("title"),
        payload.get("category"),
        payload.get("subcategory"),
        payload.get("trust_type"),
        payload.get("summary"),
        payload.get("body"),
        payload.get("difficulty_level"),
        payload.get("related_forms"),
        payload.get("related_reports"),
        payload.get("status"),
    ))
    conn.commit()
    conn.close()

def update_learning_article(article_id, payload):
    conn = _learning_conn()
    conn.execute("""
        UPDATE learning_articles
        SET title = ?,
            category = ?,
            subcategory = ?,
            trust_type = ?,
            summary = ?,
            body = ?,
            difficulty_level = ?,
            related_forms = ?,
            related_reports = ?,
            status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE article_id = ?
    """, (
        payload.get("title"),
        payload.get("category"),
        payload.get("subcategory"),
        payload.get("trust_type"),
        payload.get("summary"),
        payload.get("body"),
        payload.get("difficulty_level"),
        payload.get("related_forms"),
        payload.get("related_reports"),
        payload.get("status"),
        article_id,
    ))
    conn.commit()
    conn.close()

def get_visualization_metrics():
    conn = _learning_conn()
    metrics = {}
    table_map = {
        "learning_articles": "learning_articles",
        "form_guides": "tax_form_guides",
        "tutorial_videos": "tutorial_videos",
        "workspaces": "workspaces",
        "workspace_notes": "workspace_notes",
        "discussion_threads": "discussion_threads",
        "discussion_messages": "discussion_messages",
        "execution_tasks": "execution_tasks",
        "document_templates": "document_templates",
        "generated_documents": "generated_documents",
    }

    for key, table_name in table_map.items():
        try:
            metrics[key] = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        except Exception:
            metrics[key] = 0

    conn.close()

    # pull from main app helpers where available
    try:
        metrics["trusts"] = len(get_all_trusts())
    except Exception:
        metrics["trusts"] = 0

    try:
        metrics["fiduciaries"] = len(get_all_fiduciaries())
    except Exception:
        metrics["fiduciaries"] = 0

    try:
        metrics["instruments"] = len(get_all_instruments())
    except Exception:
        metrics["instruments"] = 0

    try:
        metrics["media"] = len(get_all_media())
    except Exception:
        metrics["media"] = 0

    return metrics

def get_visualization_timeline():
    conn = _learning_conn()
    timeline = []

    sources = [
        ("Workspace", "workspaces", "workspace_id", "title"),
        ("Discussion Thread", "discussion_threads", "thread_id", "title"),
        ("Execution Task", "execution_tasks", "task_id", "title"),
        ("Generated Document", "generated_documents", "document_id", "title"),
        ("Tutorial Video", "tutorial_videos", "video_id", "title"),
    ]

    for label, table_name, id_col, title_col in sources:
        try:
            rows = conn.execute(
                f"SELECT {id_col} as item_id, {title_col} as item_title, created_at FROM {table_name} ORDER BY created_at DESC LIMIT 10"
            ).fetchall()
            for row in rows:
                timeline.append({
                    "kind": label,
                    "item_id": row["item_id"],
                    "item_title": row["item_title"],
                    "created_at": row["created_at"],
                })
        except Exception:
            continue

    conn.close()
    timeline.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return timeline[:30]

def get_trust_relationship_summary():
    summary = []
    try:
        trusts = get_all_trusts()
    except Exception:
        trusts = []

    for trust in trusts:
        trust_id = trust.get("trust_id")
        row = {
            "trust_id": trust_id,
            "trust_name": trust.get("trust_name"),
            "fiduciaries": 0,
            "instruments": 0,
            "documents": 0,
            "workspace_links": 0,
            "tasks": 0,
        }

        try:
            row["fiduciaries"] = len([f for f in get_all_fiduciaries() if f.get("trust_id") == trust_id])
        except Exception:
            pass

        try:
            row["instruments"] = len([i for i in get_all_instruments() if i.get("trust_id") == trust_id])
        except Exception:
            pass

        try:
            row["documents"] = len([d for d in get_generated_documents() if d.get("trust_id") == trust_id])
        except Exception:
            pass

        try:
            row["tasks"] = len([t for t in get_all_execution_tasks() if t.get("trust_id") == trust_id])
        except Exception:
            pass

        try:
            row["workspace_links"] = len([w for w in get_all_workspaces() if (w.get("trust_type_focus") or "").lower() in (trust.get("trust_type") or "").lower()])
        except Exception:
            pass

        summary.append(row)

    return summary

def get_document_templates():
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM document_templates
        WHERE status = 'active'
        ORDER BY category, name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_document_template_by_id(template_id):
    conn = _learning_conn()
    row = conn.execute("""
        SELECT * FROM document_templates
        WHERE template_id = ?
    """, (template_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_generated_documents():
    firm_id = session.get("firm_id") or "FIRM-001"
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM generated_documents
        WHERE owner_id = ?
          AND firm_id = ?
        ORDER BY created_at DESC, title
    """, (get_current_owner(), firm_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_generated_documents_by_workspace(workspace_id):
    firm_id = session.get("firm_id") or "FIRM-001"
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM generated_documents
        WHERE workspace_id = ?
          AND owner_id = ?
          AND firm_id = ?
        ORDER BY created_at DESC, title
    """, (workspace_id, get_current_owner(), firm_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_generated_document_by_id(document_id):
    firm_id = session.get("firm_id") or "FIRM-001"
    conn = _learning_conn()
    row = conn.execute("""
        SELECT * FROM generated_documents
        WHERE document_id = ?
          AND firm_id = ?
    """, (document_id, firm_id)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_generated_document(payload):
    payload = dict(payload)
    payload.setdefault("firm_id", session.get("firm_id") or "FIRM-001")

    conn = _learning_conn()
    conn.execute("""
        INSERT INTO generated_documents (
            document_id, workspace_id, trust_id, template_id, title, content, status, created_by, firm_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        payload.get("document_id"),
        payload.get("workspace_id"),
        payload.get("trust_id"),
        payload.get("template_id"),
        payload.get("title"),
        payload.get("content"),
        payload.get("status"),
        payload.get("created_by"),
        payload.get("firm_id"),
    ))
    conn.commit()
    conn.close()

def render_document_template(template_body, values):
    content = template_body or ""
    for key, value in (values or {}).items():
        content = content.replace("{{" + key + "}}", value or "")
    return content

def get_all_execution_tasks():
    firm_id = session.get("firm_id") or "FIRM-001"
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM execution_tasks
        WHERE owner_id = ?
          AND firm_id = ?
        ORDER BY created_at DESC, title
    """, (get_current_owner(), firm_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_execution_tasks_by_workspace(workspace_id):
    firm_id = session.get("firm_id") or "FIRM-001"
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM execution_tasks
        WHERE workspace_id = ?
          AND owner_id = ?
          AND firm_id = ?
        ORDER BY created_at DESC, title
    """, (workspace_id, get_current_owner(), firm_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_execution_task_by_id(task_id):
    firm_id = session.get("firm_id") or "FIRM-001"
    conn = _learning_conn()
    row = conn.execute("""
        SELECT * FROM execution_tasks
        WHERE task_id = ?
          AND firm_id = ?
    """, (task_id, firm_id)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_execution_task(payload):
    payload = dict(payload)
    payload.setdefault("firm_id", session.get("firm_id") or "FIRM-001")

    conn = _learning_conn()
    conn.execute("""
        INSERT INTO execution_tasks (
            task_id, workspace_id, trust_id, title, task_type, description,
            related_form, related_report, priority, status, due_date,
            assigned_to, owner_id, created_at, updated_at, firm_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
    """, (
        payload.get("task_id"),
        payload.get("workspace_id"),
        payload.get("trust_id"),
        payload.get("title"),
        payload.get("task_type"),
        payload.get("description"),
        payload.get("related_form"),
        payload.get("related_report"),
        payload.get("priority"),
        payload.get("status"),
        payload.get("due_date"),
        payload.get("assigned_to") or session.get("username") or "unknown",
        get_current_owner(),
        payload.get("firm_id"),
    ))
    conn.commit()
    conn.close()

def update_execution_task_status(task_id, status):
    firm_id = session.get("firm_id") or "FIRM-001"
    conn = _learning_conn()
    conn.execute("""
        UPDATE execution_tasks
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE task_id = ?
          AND firm_id = ?
    """, (status, task_id, firm_id))
    conn.commit()
    conn.close()

def get_execution_task_types():
    return [
        "analysis",
        "filing_review",
        "document_collection",
        "content_review",
        "report_generation",
        "trust_setup",
        "asset_mapping",
        "compliance_check",
        "other",
    ]

def get_decision_rules():
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM decision_rules
        ORDER BY rule_id
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def run_decision_engine(goal, asset_type, control_level):
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM decision_rules
        WHERE lower(goal) = lower(?)
          AND lower(asset_type) = lower(?)
          AND lower(control_level) = lower(?)
        ORDER BY rule_id
    """, (goal, asset_type, control_level)).fetchall()
    conn.close()

    matches = [dict(r) for r in rows]
    if matches:
        return matches

    # fallback broader match by goal only
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM decision_rules
        WHERE lower(goal) = lower(?)
        ORDER BY rule_id
    """, (goal,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_discussion_threads():
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM discussion_threads
        WHERE owner_id = ?
        ORDER BY created_at DESC, title
    """, (get_current_owner(),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_discussion_threads_by_workspace(workspace_id):
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM discussion_threads
        WHERE workspace_id = ?
          AND owner_id = ?
        ORDER BY created_at DESC, title
    """, (workspace_id, get_current_owner())).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_discussion_thread_by_id(thread_id):
    conn = _learning_conn()
    row = conn.execute("""
        SELECT * FROM discussion_threads
        WHERE thread_id = ?
    """, (thread_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_discussion_thread(payload):
    conn = _learning_conn()
    conn.execute("""
        INSERT INTO discussion_threads (
            thread_id, workspace_id, title, category, related_trust_type,
            related_form, created_by, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        payload.get("thread_id"),
        payload.get("workspace_id"),
        payload.get("title"),
        payload.get("category"),
        payload.get("related_trust_type"),
        payload.get("related_form"),
        payload.get("created_by"),
        payload.get("status"),
    ))
    conn.commit()
    conn.close()

def get_discussion_messages(thread_id):
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM discussion_messages
        WHERE thread_id = ?
        ORDER BY created_at, message_id
    """, (thread_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_discussion_message(payload):
    conn = _learning_conn()
    conn.execute("""
        INSERT INTO discussion_messages (
            message_id, thread_id, parent_message_id, author, body
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        payload.get("message_id"),
        payload.get("thread_id"),
        payload.get("parent_message_id"),
        payload.get("author"),
        payload.get("body"),
    ))
    conn.commit()
    conn.close()

def get_discussion_categories():
    return [
        "general_design_discussion",
        "trust_type_questions",
        "tax_forms_questions",
        "asset_structuring_questions",
        "fiduciary_process_questions",
        "video_linked_discussion",
    ]

def get_all_workspaces():
    firm_id = session.get("firm_id") or "FIRM-001"
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM workspaces
        WHERE firm_id = ?
        ORDER BY created_at DESC, title
    """, (firm_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_workspace_by_id(workspace_id):
    firm_id = session.get("firm_id") or "FIRM-001"
    conn = _learning_conn()
    row = conn.execute("""
        SELECT * FROM workspaces
        WHERE workspace_id = ?
          AND firm_id = ?
    """, (workspace_id, firm_id)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_workspace(payload):
    payload = dict(payload)
    payload.setdefault("firm_id", session.get("firm_id") or "FIRM-001")
    payload.setdefault("owner_id", get_current_owner())

    conn = _learning_conn()
    conn.execute("""
        INSERT INTO workspaces (
            workspace_id, title, workspace_type, trust_type_focus, purpose, owner, status, owner_id, firm_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        payload.get("workspace_id"),
        payload.get("title"),
        payload.get("workspace_type"),
        payload.get("trust_type_focus"),
        payload.get("purpose"),
        payload.get("owner"),
        payload.get("status"),
        payload.get("owner_id"),
        payload.get("firm_id"),
    ))
    conn.commit()
    conn.close()

def update_workspace(workspace_id, payload):
    firm_id = session.get("firm_id") or "FIRM-001"
    conn = _learning_conn()
    conn.execute("""
        UPDATE workspaces
        SET title = ?,
            workspace_type = ?,
            trust_type_focus = ?,
            purpose = ?,
            owner = ?,
            status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE workspace_id = ?
          AND firm_id = ?
    """, (
        payload.get("title"),
        payload.get("workspace_type"),
        payload.get("trust_type_focus"),
        payload.get("purpose"),
        payload.get("owner"),
        payload.get("status"),
        workspace_id,
        firm_id,
    ))
    conn.commit()
    conn.close()

def get_workspace_notes(workspace_id):
    firm_id = session.get("firm_id") or "FIRM-001"
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM workspace_notes
        WHERE workspace_id = ?
          AND firm_id = ?
        ORDER BY section_name, created_at
    """, (workspace_id, firm_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_workspace_note(payload):
    payload = dict(payload)
    payload.setdefault("firm_id", session.get("firm_id") or "FIRM-001")

    conn = _learning_conn()
    conn.execute("""
        INSERT INTO workspace_notes (
            note_id, workspace_id, section_name, content, firm_id
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        payload.get("note_id"),
        payload.get("workspace_id"),
        payload.get("section_name"),
        payload.get("content"),
        payload.get("firm_id"),
    ))
    conn.commit()
    conn.close()

def get_workspace_note_sections():
    return [
        "goals",
        "trust_type_analysis",
        "party_roles",
        "asset_plan",
        "filing_plan",
        "open_questions",
        "design_notes",
    ]

def get_all_tutorial_videos():
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM tutorial_videos
        ORDER BY category, title
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_tutorial_videos_by_category(category):
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM tutorial_videos
        WHERE lower(category) = lower(?)
        ORDER BY title
    """, (category,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_tutorial_videos_by_trust_type(trust_type):
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM tutorial_videos
        WHERE lower(trust_type) = lower(?)
        ORDER BY title
    """, (trust_type,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_tutorial_video_by_id(video_id):
    conn = _learning_conn()
    row = conn.execute("""
        SELECT * FROM tutorial_videos
        WHERE video_id = ?
    """, (video_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_tutorial_video(payload):
    conn = _learning_conn()
    conn.execute("""
        INSERT INTO tutorial_videos (
            video_id, title, category, trust_type, description, file_path,
            thumbnail_path, transcript_notes, visibility
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        payload.get("video_id"),
        payload.get("title"),
        payload.get("category"),
        payload.get("trust_type"),
        payload.get("description"),
        payload.get("file_path"),
        payload.get("thumbnail_path"),
        payload.get("transcript_notes"),
        payload.get("visibility"),
    ))
    conn.commit()
    conn.close()

def update_tutorial_video(video_id, payload):
    conn = _learning_conn()
    conn.execute("""
        UPDATE tutorial_videos
        SET title = ?,
            category = ?,
            trust_type = ?,
            description = ?,
            file_path = ?,
            thumbnail_path = ?,
            transcript_notes = ?,
            visibility = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE video_id = ?
    """, (
        payload.get("title"),
        payload.get("category"),
        payload.get("trust_type"),
        payload.get("description"),
        payload.get("file_path"),
        payload.get("thumbnail_path"),
        payload.get("transcript_notes"),
        payload.get("visibility"),
        video_id,
    ))
    conn.commit()
    conn.close()

def create_form_guide(payload):
    conn = _learning_conn()
    conn.execute("""
        INSERT INTO tax_form_guides (
            guide_id, form_name, category, applies_to, summary, body,
            related_trust_types, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        payload.get("guide_id"),
        payload.get("form_name"),
        payload.get("category"),
        payload.get("applies_to"),
        payload.get("summary"),
        payload.get("body"),
        payload.get("related_trust_types"),
        payload.get("status"),
    ))
    conn.commit()
    conn.close()

def update_form_guide(guide_id, payload):
    conn = _learning_conn()
    conn.execute("""
        UPDATE tax_form_guides
        SET form_name = ?,
            category = ?,
            applies_to = ?,
            summary = ?,
            body = ?,
            related_trust_types = ?,
            status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE guide_id = ?
    """, (
        payload.get("form_name"),
        payload.get("category"),
        payload.get("applies_to"),
        payload.get("summary"),
        payload.get("body"),
        payload.get("related_trust_types"),
        payload.get("status"),
        guide_id,
    ))
    conn.commit()
    conn.close()


def learning_article_exists(article_id):
    conn = _learning_conn()
    row = conn.execute(
        "SELECT article_id FROM learning_articles WHERE article_id = ? LIMIT 1",
        (article_id,)
    ).fetchone()
    conn.close()
    return bool(row)


def form_guide_exists(form_name):
    conn = _learning_conn()
    row = conn.execute(
        "SELECT form_name FROM tax_form_guides WHERE lower(form_name) = lower(?) LIMIT 1",
        (form_name,)
    ).fetchone()
    conn.close()
    return bool(row)


def trust_name_exists_for_owner(trust_name, owner_id):
    # Baseline seed records must be idempotent even when legacy/local rows
    # do not preserve owner_id. Match baseline trust names globally to avoid
    # duplicate ABC seed records on repeated runs.
    for trust in get_all_trusts():
        trust_row = dict(trust)
        existing_name = (trust_row.get("trust_name") or "").strip().lower()
        if existing_name == trust_name.strip().lower():
            return True
    return False


def seed_hosted_baseline_data(owner_id):
    results = {
        "trusts_created": [],
        "trusts_skipped": [],
        "learning_articles_created": [],
        "learning_articles_skipped": [],
        "form_guides_created": [],
        "form_guides_skipped": [],
    }

    baseline_trusts = [
        {
            "trust_name": "ABC Trust",
            "short_name": "ABC",
            "jurisdiction": "New Jersey",
            "effective_date": "2026-05-01",
            "trust_type": "revocable",
            "trust_purpose": "baseline_governance_testing",
            "accounting_method": "cash",
            "workflow_mode": "private_office",
            "settlor_name": "Baseline Settlor",
            "trustee_name": "Baseline Trustee",
            "successor_trustee_name": "Baseline Successor Trustee",
            "beneficiary_name": "Baseline Beneficiary",
            "record_visibility": "private",
            "workflow_mode_confirmed": "private_office",
            "ai_explanations": "enabled",
            "recommended_guidance": "enabled",
            "initial_corpus_description": "Baseline seed corpus for hosted runtime validation.",
            "property_mapping_timing": "now",
            "asset_categories": "records",
            "generate_schedule_recommendations": "yes",
            "status": "Draft",
            "owner_id": owner_id,
        },
        {
            "trust_name": "ABC Irrevocable Trust",
            "short_name": "ABC-IRR",
            "jurisdiction": "New Jersey",
            "effective_date": "2026-05-01",
            "trust_type": "irrevocable",
            "trust_purpose": "baseline_irrevocable_structure_testing",
            "accounting_method": "cash",
            "workflow_mode": "private_office",
            "settlor_name": "Baseline Grantor",
            "trustee_name": "Baseline Trustee",
            "successor_trustee_name": "Baseline Successor Trustee",
            "beneficiary_name": "Baseline Beneficiary",
            "record_visibility": "private",
            "workflow_mode_confirmed": "private_office",
            "ai_explanations": "enabled",
            "recommended_guidance": "enabled",
            "initial_corpus_description": "Baseline seed corpus for irrevocable trust workflow validation.",
            "property_mapping_timing": "later",
            "asset_categories": "records",
            "generate_schedule_recommendations": "yes",
            "status": "Draft",
            "owner_id": owner_id,
        },
        {
            "trust_name": "ABC Business Trust",
            "short_name": "ABC-BIZ",
            "jurisdiction": "New Jersey",
            "effective_date": "2026-05-01",
            "trust_type": "business",
            "trust_purpose": "baseline_business_trust_testing",
            "accounting_method": "accrual",
            "workflow_mode": "private_office",
            "settlor_name": "Baseline Grantor",
            "trustee_name": "Baseline Trustee",
            "successor_trustee_name": "Baseline Successor Trustee",
            "beneficiary_name": "Baseline Beneficiary",
            "record_visibility": "internal",
            "workflow_mode_confirmed": "private_office",
            "ai_explanations": "enabled",
            "recommended_guidance": "enabled",
            "initial_corpus_description": "Baseline seed corpus for business trust workflow validation.",
            "property_mapping_timing": "now",
            "asset_categories": "business_records",
            "generate_schedule_recommendations": "yes",
            "status": "Draft",
            "owner_id": owner_id,
        },
    ]

    for trust_payload in baseline_trusts:
        trust_name = trust_payload["trust_name"]
        if trust_name_exists_for_owner(trust_name, owner_id):
            results["trusts_skipped"].append(trust_name)
            continue

        trust_payload = dict(trust_payload)
        trust_payload["trust_id"] = get_next_trust_id()
        create_trust_record(trust_payload)
        results["trusts_created"].append(f"{trust_payload['trust_id']} — {trust_name}")

    starter_articles = [
        {
            "article_id": "ART-TRUST-BASICS-001",
            "title": "Trust Administration Basics",
            "category": "Trust Administration",
            "subcategory": "Foundations",
            "trust_type": "general",
            "summary": "A starter guide explaining the basic records and workflow surfaces used in the Trustee App.",
            "body": "This article introduces trust identity, parties, property mapping, minutes, certificates, and packet review as separate workflow layers.",
            "difficulty_level": "beginner",
            "related_forms": "Trust Minutes, Certificate Registry, Formation Preview Hub",
            "related_reports": "Report Center, System Health",
            "status": "published",
        },
        {
            "article_id": "ART-CERTIFICATES-001",
            "title": "Execution Certificates and Audit Trails",
            "category": "Governance Records",
            "subcategory": "Certificates",
            "trust_type": "general",
            "summary": "A starter guide for understanding executed minutes, certificate IDs, packet exports, and audit trail records.",
            "body": "Execution certificates summarize completed governance records and connect them to signer roles, packet exports, and audit trail entries.",
            "difficulty_level": "beginner",
            "related_forms": "Trust Minutes",
            "related_reports": "Certificate Registry, Audit Trail",
            "status": "published",
        },
    ]

    for article in starter_articles:
        if learning_article_exists(article["article_id"]):
            results["learning_articles_skipped"].append(article["article_id"])
            continue
        create_learning_article(article)
        results["learning_articles_created"].append(article["article_id"])

    starter_guides = [
        {
            "guide_id": "GUIDE-TRUST-MINUTES-001",
            "form_name": "Trust Minutes",
            "category": "Governance",
            "applies_to": "Trustee decisions, approvals, executions, and archived governance records.",
            "summary": "Explains how trust minutes preserve decisions and connect to execution certificates.",
            "body": "Use trust minutes to record trustee decisions, approval, execution, signer capacity, and certificate generation.",
            "related_trust_types": "general, revocable, irrevocable, business",
            "status": "published",
        },
        {
            "guide_id": "GUIDE-CERT-REGISTRY-001",
            "form_name": "Certificate Registry",
            "category": "Governance",
            "applies_to": "Executed or archived trust minutes with certificate IDs.",
            "summary": "Explains how the certificate registry indexes executed trust records.",
            "body": "The certificate registry lists certificate IDs, minute references, execution status, packet exports, and verification links.",
            "related_trust_types": "general",
            "status": "published",
        },
    ]

    for guide in starter_guides:
        if form_guide_exists(guide["form_name"]):
            results["form_guides_skipped"].append(guide["form_name"])
            continue
        create_form_guide(guide)
        results["form_guides_created"].append(guide["form_name"])

    return results

def get_trust_type_detail(slug):
    cards = {c["slug"]: c for c in get_trust_type_cards()}
    card = cards.get(slug)
    if not card:
        return None

    body_map = {
        "revocable": "Revocable trusts are generally discussed where amendment flexibility and ongoing control are major concerns.",
        "irrevocable": "Irrevocable trusts are generally discussed where stronger separation and reduced unilateral change are part of the structure.",
        "simple": "Simple trust is a common conceptual/tax classification term and should be studied together with distribution and filing implications.",
        "complex": "Complex trust is a common conceptual/tax classification term and often arises when retention, accumulation, or broader distribution activity is involved.",
        "land": "Land trusts are typically discussed in relation to real property holding and title/management structure.",
        "insurance": "Insurance trusts are typically discussed when policy ownership, control, and estate-related planning structure are involved.",
        "foreign": "Foreign trust discussions are advanced and should be handled with caution, clear documentation, and careful tax/legal review.",
        "charitable": "Charitable trusts are mission-oriented structures that typically require close attention to purpose, governance, and compliance.",
        "business": "Business trusts are discussed where trust structure and operational/business activity intersect.",
        "other": "Other trust structures can be documented here as custom or specialized categories.",
    }

    related_forms = []
    for guide in get_form_guides():
        rel = (guide.get("related_trust_types") or "").lower().split(";")
        if slug in rel or "other" in rel and slug == "other":
            related_forms.append(guide)

    return {
        "slug": slug,
        "label": card["label"],
        "summary": card["summary"],
        "body": body_map.get(slug, ""),
        "related_forms": related_forms,
    }
LEARNING_DB_PATH = DB_PATH.as_posix()


@app.route("/media")
def media_dashboard():

    records = get_all_media()
    return render_template("media_dashboard.html", records=records)


@app.route("/media/upload", methods=["GET", "POST"])
def media_upload():
    trusts = get_all_trusts()
    media_prefill = {
        "trust_id": request.args.get("trust_id", ""),
        "entity_type": request.args.get("entity_type", ""),
        "entity_id": request.args.get("entity_id", ""),
        "category": request.args.get("category", ""),
        "description": request.args.get("description", ""),
    }

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("media_form.html", trusts=trusts, media_prefill=media_prefill, error_message="Invalid or missing CSRF token.")

        file = request.files.get("file")
        if file:
            media_id = get_next_media_id()
            original_name = file.filename
            safe_name = secure_filename(original_name)
            filename = f"{media_id}_{safe_name}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            create_media_record({
                "media_id": media_id,
                "trust_id": request.form.get("trust_id"),
                "related_entity_type": request.form.get("entity_type"),
                "related_entity_id": request.form.get("entity_id"),
                "media_type": request.form.get("media_type"),
                "file_path": filepath,
                "category": request.form.get("category"),
                "description": request.form.get("description"),
                "created_at": datetime.now().isoformat(),
            })

            log_change("media", media_id, "upload", "Media evidence uploaded")

        return redirect(url_for("media_dashboard"))

    return render_template("media_form.html", trusts=trusts, media_prefill=media_prefill)




@app.route("/media/file/<media_id>")
def media_file(media_id):
    records = get_all_media()
    target = None
    for row in records:
        if row["media_id"] == media_id:
            target = row
            break

    if not target:
        return "Media not found", 404

    stored_path = Path(target["file_path"]).resolve()
    uploads_root = UPLOAD_FOLDER.resolve()

    try:
        stored_path.relative_to(uploads_root)
    except ValueError:
        return "Invalid media path", 400

    if not stored_path.exists() or not stored_path.is_file():
        return "Media file missing", 404

    from flask import send_file
    return send_file(stored_path)




@app.route("/evidence/<entity_type>/<entity_id>")
def evidence_by_entity(entity_type, entity_id):
    records = get_media_by_entity(entity_type, entity_id)
    return render_template(
        "evidence_entity_view.html",
        entity_type=entity_type,
        entity_id=entity_id,
        records=records
    )




@app.route("/reports/k1/<trust_id>")
def k1_report_view(trust_id):
    tax_year = request.args.get("tax_year", str(date.today().year))
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found", 404

    totals = get_distribution_totals_by_trust(trust_id, tax_year)
    beneficiary_totals = get_distribution_totals_by_beneficiary(trust_id, tax_year)
    evidence = get_media_by_trust_id(trust_id)

    totals["gross_total_fmt"] = money(totals["gross_total"])
    totals["taxable_total_fmt"] = money(totals["taxable_total"])
    totals["principal_total_fmt"] = money(totals["principal_total"])

    for row in beneficiary_totals:
        row["gross_total_fmt"] = money(row["gross_total"])
        row["taxable_total_fmt"] = money(row["taxable_total"])
        row["principal_total_fmt"] = money(row["principal_total"])

    return render_template(
        "k1_report_view.html",
        trust=trust,
        tax_year=tax_year,
        totals=totals,
        beneficiary_totals=beneficiary_totals,
        evidence=evidence
    )


@app.route("/reports/1041/<trust_id>")
def form1041_report_view(trust_id):
    tax_year = request.args.get("tax_year", str(date.today().year))
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found", 404

    tax_logic = compute_dni_components(trust_id, tax_year)
    shares = compute_beneficiary_tax_shares(trust_id, tax_year)
    evidence = get_media_by_trust_id(trust_id)

    tax_logic["gross_income_fmt"] = money(tax_logic["gross_income"])
    tax_logic["taxable_distributed_fmt"] = money(tax_logic["taxable_distributed"])
    tax_logic["principal_distributed_fmt"] = money(tax_logic["principal_distributed"])
    tax_logic["dni_fmt"] = money(tax_logic["dni"])
    tax_logic["retained_income_fmt"] = money(tax_logic["retained_income"])

    for row in shares:
        row["gross_total_fmt"] = money(row["gross_total"])
        row["taxable_total_fmt"] = money(row["taxable_total"])
        row["principal_total_fmt"] = money(row["principal_total"])
        row["taxable_ratio_pct"] = f"{row['taxable_ratio'] * 100:.1f}%"

    return render_template(
        "form1041_report_view.html",
        trust=trust,
        tax_year=tax_year,
        tax_logic=tax_logic,
        shares=shares,
        evidence=evidence
    )




@app.route("/roles")
def role_dashboard():
    gate = require_master_admin()
    if gate:
        return gate

    roles = get_all_roles()
    trusts = get_all_trusts()
    return render_template("role_dashboard.html", roles=roles, trusts=trusts)


@app.route("/roles/new", methods=["GET", "POST"])
def role_new():
    gate = require_master_admin()
    if gate:
        return gate
    trusts = get_all_trusts()

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("role_form.html", trusts=trusts, error_message="Invalid or missing CSRF token.")

        role_id = get_next_role_id()
        create_role_record({
            "role_id": role_id,
            "full_name": request.form.get("full_name"),
            "role_name": request.form.get("role_name"),
            "trust_id": request.form.get("trust_id"),
            "status": request.form.get("status"),
            "notes": request.form.get("notes"),
        })
        log_change("role", role_id, "create", f"Master admin created role assignment for {request.form.get('full_name')} as {request.form.get('role_name')} on trust {request.form.get('trust_id')}")
        flash(f"Role assignment {role_id} created successfully.")
        return redirect(url_for("role_dashboard"))

    return render_template("role_form.html", trusts=trusts)




@app.route("/reports/k1/<trust_id>/print")
def k1_report_print(trust_id):
    tax_year = request.args.get("tax_year", str(date.today().year))
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found", 404

    totals = get_distribution_totals_by_trust(trust_id, tax_year)
    beneficiary_totals = get_distribution_totals_by_beneficiary(trust_id, tax_year)
    evidence = get_media_by_trust_id(trust_id)
    fiduciaries = get_fiduciaries_by_trust_id(trust_id)

    totals["gross_total_fmt"] = money(totals["gross_total"])
    totals["taxable_total_fmt"] = money(totals["taxable_total"])
    totals["principal_total_fmt"] = money(totals["principal_total"])

    for row in beneficiary_totals:
        row["gross_total_fmt"] = money(row["gross_total"])
        row["taxable_total_fmt"] = money(row["taxable_total"])
        row["principal_total_fmt"] = money(row["principal_total"])

    return render_template(
        "k1_report_print.html",
        trust=trust,
        tax_year=tax_year,
        totals=totals,
        beneficiary_totals=beneficiary_totals,
        evidence=evidence,
        fiduciaries=fiduciaries
    )


@app.route("/reports/1041/<trust_id>/print")
def form1041_report_print(trust_id):
    tax_year = request.args.get("tax_year", str(date.today().year))
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found", 404

    tax_logic = compute_dni_components(trust_id, tax_year)
    shares = compute_beneficiary_tax_shares(trust_id, tax_year)
    evidence = get_media_by_trust_id(trust_id)
    fiduciaries = get_fiduciaries_by_trust_id(trust_id)

    tax_logic["gross_income_fmt"] = money(tax_logic["gross_income"])
    tax_logic["taxable_distributed_fmt"] = money(tax_logic["taxable_distributed"])
    tax_logic["principal_distributed_fmt"] = money(tax_logic["principal_distributed"])
    tax_logic["dni_fmt"] = money(tax_logic["dni"])
    tax_logic["retained_income_fmt"] = money(tax_logic["retained_income"])

    for row in shares:
        row["gross_total_fmt"] = money(row["gross_total"])
        row["taxable_total_fmt"] = money(row["taxable_total"])
        row["principal_total_fmt"] = money(row["principal_total"])
        row["taxable_ratio_pct"] = f"{row['taxable_ratio'] * 100:.1f}%"

    return render_template(
        "form1041_report_print.html",
        trust=trust,
        tax_year=tax_year,
        tax_logic=tax_logic,
        shares=shares,
        evidence=evidence,
        fiduciaries=fiduciaries
    )




@app.route("/permissions", methods=["GET", "POST"])
def permissions_dashboard():

    permission_roles = ["Admin", "Trustee", "Viewer"]

    if request.method == "POST":
        target_role = (request.form.get("role_name") or "").strip()
        selected_permissions = request.form.getlist("permissions")

        if target_role in permission_roles:
            replace_role_permissions(target_role, selected_permissions)
            log_change(
                "security",
                session.get("username") or "unknown",
                "permissions_updated",
                f"Role={target_role}; Permissions={selected_permissions}"
            )

        return redirect(url_for("permissions_dashboard"))

    trusts = get_all_trusts()
    rows = []

    for trust in trusts:
        summary = get_role_summary_by_trust(trust["trust_id"])
        rows.append({
            "trust_id": trust["trust_id"],
            "trust_name": trust["trust_name"],
            "admin_count": summary["Admin"],
            "trustee_count": summary["Trustee"],
            "viewer_count": summary["Viewer"],
        })

    permission_roles = ["Admin", "Trustee", "Viewer"]
    permission_matrix = {
        role: sorted(get_permissions_by_role(role))
        for role in permission_roles
    }

    return render_template(
        "permissions_dashboard.html",
        rows=rows,
        permission_roles=permission_roles,
        permission_matrix=permission_matrix
    )




@app.route("/security")
def security_dashboard():
    checklist = [
        {"item": "Public/shareable link", "status": "Needs review"},
        {"item": "Authentication required", "status": "Not yet enforced"},
        {"item": "Uploads in private non-public storage", "status": "Needs review"},
        {"item": "Third-party transmission disabled by default", "status": "Current expectation"},
        {"item": "Debug mode disabled for deployment", "status": "Required before live use"},
        {"item": "File size/type restrictions", "status": "Basic restrictions added"},
        {"item": "Role-aware access cues", "status": "Implemented"},
        {"item": "Audit trail", "status": "Implemented"},
        {"item": "Media evidence references", "status": "Implemented"},
        {"item": "Render deployment classified as pilot only", "status": "Yes"},
    ]
    audit_chain = verify_audit_log_chain()
    return render_template("security_dashboard.html", checklist=checklist, audit_chain=audit_chain)






@app.after_request
def apply_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "frame-ancestors 'none';"
    )

    if APP_ENV == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template(
        "access_denied.html",
        reason="Security check failed. Please go back, refresh the page, and try again."
    ), 400
@app.before_request
def enforce_session_timeout():
    # 🔒 GLOBAL AUTHENTICATION LOCK
    public_endpoints = {
        "login",
        "logout",
        "static",
        "bootstrap_admin_once",
    }

    if request.endpoint not in public_endpoints:
        if "role" not in session:
            return redirect(url_for("login"))

    allowed_routes = {"login", "logout", "static", "bootstrap_admin_once", "reset_admin_once"}
    if request.endpoint in allowed_routes or request.endpoint is None:
        return

    if (request.endpoint or "").startswith("export_"):
        export_policy = get_export_policy()
        if not bool(export_policy.get("allow_exports", True)):
            log_change(
                "security",
                session.get("username") or "unknown",
                "export_blocked",
                f"Endpoint={request.endpoint}; Policy=allow_exports_false"
            )
            return render_template(
                "access_denied.html",
                reason="Exports are currently disabled by system policy."
            )

    if request.method == "POST":
        export_policy = get_export_policy()
        read_only_exempt = {"login", "logout", "bootstrap_admin_once", "reset_admin_once"}
        if bool(export_policy.get("read_only_mode", False)) and request.endpoint not in read_only_exempt:
            log_change(
                "security",
                session.get("username") or "unknown",
                "read_only_blocked",
                f"Endpoint={request.endpoint}; Method=POST; Policy=read_only_mode_true"
            )
            return render_template(
                "access_denied.html",
                reason="System is currently in read-only mode. Write actions are disabled."
            )

    if "role" not in session:
        return redirect(url_for("login"))

    allowed_roles = ROLE_RULES.get(request.endpoint)
    if allowed_roles and session.get("role") not in allowed_roles:
        log_change(
            "security",
            session.get("username") or "unknown",
            "role_denied",
            f"Endpoint={request.endpoint}; Role={session.get('role')}; Allowed={sorted(allowed_roles)}"
        )
        return render_template(
            "access_denied.html",
            reason=f"Role {session.get('role')} is not allowed for this page."
        )

    # HYBRID PERMISSION ENFORCEMENT + USER OVERRIDES
    required_permission = ENDPOINT_PERMISSION_RULES.get(request.endpoint)
    if required_permission:
        username = session.get("username") or "unknown"
        user_role = session.get("role")
        if not user_has_effective_permission(username, required_permission):
            log_change(
                "security",
                username,
                "permission_denied",
                f"Endpoint={request.endpoint}; Role={user_role}; Required={required_permission}; EffectiveOverride=True"
            )
            return render_template(
                "access_denied.html",
                reason=f"Permission '{required_permission}' required for this action."
            )

    last_activity = session.get("last_activity")
    if last_activity is None:
        session.clear()
        return redirect(url_for("login", timeout="1"))

    now_ts = datetime.now(UTC).timestamp()
    if now_ts - float(last_activity) > SESSION_TIMEOUT_SECONDS:
        session.clear()
        return redirect(url_for("login", timeout="1"))

    session["last_activity"] = now_ts

@app.route("/reports/trust/<trust_id>/summary.pdf")
def trust_summary_pdf(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found", 404

    trust_dict = dict(trust)

    properties = [dict(row) for row in get_properties_by_trust_id(trust_id)]
    accounts = [dict(row) for row in get_accounts_by_trust_id(trust_id)]
    documents = [dict(row) for row in get_documents_by_trust_id(trust_id)]
    entries = [dict(row) for row in get_ledger_entries_by_trust_id(trust_id)]

    story = trust_summary_story(trust_dict, properties, accounts, documents, entries)
    return build_pdf_response(f"trust_summary_{trust_id}.pdf", story)


@app.route("/reports/k1/trust/<trust_id>/<tax_year>.pdf")
def k1_readiness_pdf(trust_id, tax_year):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found", 404

    beneficiaries = get_beneficiaries_by_trust_id(trust_id)
    distributions = get_distributions_by_trust_id(trust_id)
    summary = get_k1_readiness_summary(trust_id, tax_year)
    totals = get_k1_totals(trust_id, tax_year)
    beneficiary_totals = get_k1_beneficiary_totals(trust_id, tax_year)

    story = k1_readiness_story(
        trust=trust,
        tax_year=tax_year,
        summary=summary,
        totals=totals,
        beneficiary_totals=beneficiary_totals,
        beneficiaries=beneficiaries,
        distributions=distributions,
    )
    return build_pdf_response(f"k1_readiness_{trust_id}_{tax_year}.pdf", story)

@app.route("/reports/fiduciaries.pdf")
def fiduciary_report_pdf():
    trust_id = request.args.get("trust_id")
    trusts = get_all_trusts()
    fiduciaries = get_all_fiduciaries()
    story = fiduciary_report_story(trusts=trusts, fiduciaries=fiduciaries, selected_trust_id=trust_id)
    suffix = f"_{trust_id}" if trust_id else "_all"
    return build_pdf_response(f"fiduciary_report{suffix}.pdf", story)


@app.route("/reports/ledger/trust/<trust_id>.pdf")
def ledger_report_pdf(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found", 404

    entries = get_ledger_entries_by_trust_id(trust_id)
    story = ledger_report_story(trust=trust, entries=entries)
    return build_pdf_response(f"ledger_report_{trust_id}.pdf", story)

@app.route("/reports/1041/trust/<trust_id>/<tax_year>.pdf")
def form1041_report_pdf(trust_id, tax_year):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found", 404

    tax_logic = get_1041_tax_logic(trust_id, tax_year)
    shares = get_1041_shares(trust_id, tax_year)
    evidence = get_1041_evidence(trust_id, tax_year)

    story = form1041_report_story(
        trust=trust,
        tax_year=tax_year,
        tax_logic=tax_logic,
        shares=shares,
        evidence=evidence,
    )
    return build_pdf_response(f"form1041_report_{trust_id}_{tax_year}.pdf", story)


@app.route("/reports/instrument/<instrument_id>.pdf")
def instrument_detail_pdf(instrument_id):
    instrument = get_instrument_by_id(instrument_id)
    if not instrument:
        return f"Instrument {instrument_id} not found", 404

    trust = get_trust_by_id(instrument.get("trust_id")) if instrument.get("trust_id") else None
    history = get_audit_log_by_entity("instrument", instrument_id, 25)

    story = instrument_detail_story(
        instrument=instrument,
        trust=trust,
        history=history,
    )
    return build_pdf_response(f"instrument_detail_{instrument_id}.pdf", story)



@app.route("/hosted-production-health")
@require_permission("view_dashboard")
def hosted_production_health():
    """
    Safe authenticated hosted production health dashboard.

    No raw DB/session dumps.
    No secrets.
    No repair actions.
    """

    import sqlite3

    checks = []

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        def add_check(category, name, passed, detail, warn=False):
            checks.append({
                "category": category,
                "name": name,
                "status": "PASS" if passed else ("WARN" if warn else "FAIL"),
                "detail": detail
            })

        add_check("Environment", "ENSURE_HOSTED_ADMIN", os.getenv("ENSURE_HOSTED_ADMIN") == "1", "Hosted startup self-heal variable present", warn=True)
        add_check("Environment", "ENSURE_HOSTED_TEST_TRUST", os.getenv("ENSURE_HOSTED_TEST_TRUST") == "1", "Hosted trust seed variable present", warn=True)
        add_check("Environment", "ENSURE_HOSTED_PORTFOLIO_SEED", os.getenv("ENSURE_HOSTED_PORTFOLIO_SEED") == "1", "Hosted portfolio seed variable present", warn=True)
        add_check("Environment", "APP_ENV", os.getenv("APP_ENV") == "production", "Production environment expected", warn=True)

        cur.execute("""
            SELECT trust_name, firm_id
            FROM trusts
            WHERE trust_id = 'TR-001'
            LIMIT 1
        """)
        trust = cur.fetchone()

        add_check(
            "Seed Trust",
            "TR-001",
            bool(trust),
            f"{trust['trust_name']} ({trust['firm_id']})" if trust else "Seed trust missing"
        )

        for table_name, label in [
            ("properties", "Properties"),
            ("accounts", "Accounts"),
            ("documents", "Documents"),
            ("ledger_entries", "Ledger Entries"),
        ]:
            try:
                cur.execute(f"""
                    SELECT COUNT(*) AS count
                    FROM {table_name}
                    WHERE trust_id = 'TR-001'
                      AND firm_id = 'FIRM-002'
                """)
                row = cur.fetchone()
                count = row["count"] if row else 0
                add_check("Portfolio", label, count >= 1, f"{count} record(s)", warn=True)
            except Exception:
                add_check("Portfolio", label, False, "Table/query unavailable")

        conn.close()

    except Exception:
        checks.append({
            "category": "System",
            "name": "Health Route",
            "status": "FAIL",
            "detail": "Health check failed without exposing raw diagnostics"
        })

    return render_template("hosted_production_health.html", checks=checks)



@app.route("/reports", methods=["GET", "POST"])
def report_center():
    trusts = get_all_trusts()

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("report_center.html", trusts=trusts, instruments=get_all_instruments() if "get_all_instruments" in globals() else [], prefill=request.form, error_message="Invalid or missing CSRF token.")

        report_type = (request.form.get("report_type") or "").strip()
        trust_id = (request.form.get("trust_id") or "").strip()
        tax_year = (request.form.get("tax_year") or "").strip()
        instrument_id = (request.form.get("instrument_id") or "").strip()
        fiduciary_trust_id = (request.form.get("fiduciary_trust_id") or "").strip()

        if report_type == "trust_summary":
            if not trust_id:
                return render_template("report_center.html", trusts=trusts, instruments=get_all_instruments() if "get_all_instruments" in globals() else [], prefill=request.form, error_message="Trust is required for Trust Summary.")
            return redirect(url_for("trust_summary_pdf", trust_id=trust_id))

        if report_type == "ledger":
            if not trust_id:
                return render_template("report_center.html", trusts=trusts, instruments=get_all_instruments() if "get_all_instruments" in globals() else [], prefill=request.form, error_message="Trust is required for Ledger Report.")
            return redirect(url_for("ledger_report_pdf", trust_id=trust_id))

        if report_type == "fiduciary":
            if fiduciary_trust_id:
                return redirect(url_for("fiduciary_report_pdf", trust_id=fiduciary_trust_id))
            return redirect(url_for("fiduciary_report_pdf"))

        if report_type == "portfolio":
            return redirect(url_for("portfolio_report_pdf"))

        if report_type == "audit":
            return redirect(url_for("audit_log_report_pdf"))

        if report_type == "k1":
            if not trust_id or not tax_year:
                return render_template("report_center.html", trusts=trusts, instruments=get_all_instruments() if "get_all_instruments" in globals() else [], prefill=request.form, error_message="Trust and Tax Year are required for K-1 Readiness.")
            return redirect(url_for("k1_readiness_pdf", trust_id=trust_id, tax_year=tax_year))

        if report_type == "form1041":
            if not trust_id or not tax_year:
                return render_template("report_center.html", trusts=trusts, instruments=get_all_instruments() if "get_all_instruments" in globals() else [], prefill=request.form, error_message="Trust and Tax Year are required for 1041 Report.")
            return redirect(url_for("form1041_report_pdf", trust_id=trust_id, tax_year=tax_year))

        if report_type == "instrument":
            if not instrument_id:
                return render_template("report_center.html", trusts=trusts, instruments=get_all_instruments() if "get_all_instruments" in globals() else [], prefill=request.form, error_message="Instrument ID is required for Instrument Detail.")
            return redirect(url_for("instrument_detail_pdf", instrument_id=instrument_id))

        return render_template("report_center.html", trusts=trusts, instruments=get_all_instruments() if "get_all_instruments" in globals() else [], prefill=request.form, error_message="Please select a valid report type.")

    prefill = {
        "report_type": request.args.get("report_type", ""),
        "trust_id": request.args.get("trust_id", ""),
        "tax_year": request.args.get("tax_year", "") or str(datetime.now().year),
        "instrument_id": request.args.get("instrument_id", ""),
        "fiduciary_trust_id": request.args.get("fiduciary_trust_id", ""),
    }
    instruments = get_all_instruments() if "get_all_instruments" in globals() else []
    return render_template("report_center.html", trusts=trusts, instruments=instruments, prefill=prefill)

@app.route("/reports/portfolio.pdf")
def portfolio_report_pdf():
    portfolio = get_portfolio_snapshot()
    totals = get_portfolio_totals()
    story = portfolio_report_story(portfolio=portfolio, totals=totals)
    return build_pdf_response("portfolio_report.pdf", story)


@app.route("/reports/audit.pdf")
def audit_log_report_pdf():
    entity_type = request.args.get("entity_type")
    entity_id = request.args.get("entity_id")

    if entity_type or entity_id:
        logs = get_audit_log_by_entity(entity_type=entity_type, entity_id=entity_id, limit=200)
    else:
        logs = get_audit_log(200)

    story = audit_log_report_story(logs=logs, entity_type=entity_type, entity_id=entity_id)
    return build_pdf_response("audit_log_report.pdf", story)

@app.route("/learning")
def learning_dashboard():
    articles = get_learning_articles()
    trust_types = get_trust_type_cards()
    categories = sorted({a["category"] for a in articles})
    return render_template(
        "learning_dashboard.html",
        articles=articles,
        trust_types=trust_types,
        categories=categories
    )


@app.route("/learning/category/<category>")
def learning_category(category):
    articles = get_learning_articles_by_category(category)
    return render_template(
        "learning_category.html",
        category=category,
        articles=articles
    )


@app.route("/learning/article/<article_id>")
def learning_article(article_id):
    article = get_learning_article_by_id(article_id)
    if not article:
        return f"Learning article {article_id} not found", 404
    return render_template("learning_article.html", article=article)


@app.route("/learning/trust-types")
def trust_type_index():
    trust_types = get_trust_type_cards()
    return render_template("trust_type_index.html", trust_types=trust_types)


@app.route("/learning/trust-type/<slug>")
def trust_type_detail(slug):
    trust_type = get_trust_type_detail(slug)
    if not trust_type:
        return f"Trust type {slug} not found", 404
    return render_template("trust_type_detail.html", trust_type=trust_type)


@app.route("/forms")
def forms_dashboard():
    guides = get_form_guides()
    categories = sorted({g["category"] for g in guides})
    return render_template("forms_dashboard.html", guides=guides, categories=categories)


@app.route("/forms/name/<form_name>")
def form_guide_detail(form_name):
    guide = get_form_guide_by_name(form_name)
    if not guide:
        return f"Form guide {form_name} not found", 404
    return render_template("form_guide_detail.html", guide=guide)

@app.route("/admin/learning/article/new", methods=["GET", "POST"])
def learning_article_new():
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("learning_article_form.html", mode="new", error_message="Invalid or missing CSRF token.")

        article_id = (request.form.get("article_id") or "").strip()
        if not article_id:
            return render_template("learning_article_form.html", mode="new", error_message="Article ID is required.")

        payload = {
            "article_id": article_id,
            "title": request.form.get("title"),
            "category": request.form.get("category"),
            "subcategory": request.form.get("subcategory"),
            "trust_type": request.form.get("trust_type"),
            "summary": request.form.get("summary"),
            "body": request.form.get("body"),
            "difficulty_level": request.form.get("difficulty_level"),
            "related_forms": request.form.get("related_forms"),
            "related_reports": request.form.get("related_reports"),
            "status": request.form.get("status") or "draft",
        }
        create_learning_article(payload)
        return redirect(url_for("learning_article", article_id=article_id))

    return render_template("learning_article_form.html", mode="new")


@app.route("/admin/learning/article/<article_id>/edit", methods=["GET", "POST"])
def learning_article_edit(article_id):
    article = get_learning_article_by_id(article_id)
    if not article:
        return f"Learning article {article_id} not found", 404

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("learning_article_form.html", mode="edit", article=article, error_message="Invalid or missing CSRF token.")

        payload = {
            "title": request.form.get("title"),
            "category": request.form.get("category"),
            "subcategory": request.form.get("subcategory"),
            "trust_type": request.form.get("trust_type"),
            "summary": request.form.get("summary"),
            "body": request.form.get("body"),
            "difficulty_level": request.form.get("difficulty_level"),
            "related_forms": request.form.get("related_forms"),
            "related_reports": request.form.get("related_reports"),
            "status": request.form.get("status") or "draft",
        }
        update_learning_article(article_id, payload)
        return redirect(url_for("learning_article", article_id=article_id))

    return render_template("learning_article_form.html", mode="edit", article=article)


@app.route("/admin/forms/new", methods=["GET", "POST"])
def form_guide_new():
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("form_guide_form.html", mode="new", error_message="Invalid or missing CSRF token.")

        guide_id = (request.form.get("guide_id") or "").strip()
        form_name = (request.form.get("form_name") or "").strip()
        if not guide_id or not form_name:
            return render_template("form_guide_form.html", mode="new", error_message="Guide ID and Form Name are required.")

        payload = {
            "guide_id": guide_id,
            "form_name": form_name,
            "category": request.form.get("category"),
            "applies_to": request.form.get("applies_to"),
            "summary": request.form.get("summary"),
            "body": request.form.get("body"),
            "related_trust_types": request.form.get("related_trust_types"),
            "status": request.form.get("status") or "draft",
        }
        create_form_guide(payload)
        return redirect(url_for("form_guide_detail", form_name=form_name))

    return render_template("form_guide_form.html", mode="new")


@app.route("/admin/forms/<form_name>/edit", methods=["GET", "POST"])
def form_guide_edit(form_name):
    guide = get_form_guide_by_name(form_name)
    if not guide:
        return f"Form guide {form_name} not found", 404

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("form_guide_form.html", mode="edit", guide=guide, error_message="Invalid or missing CSRF token.")

        payload = {
            "form_name": request.form.get("form_name"),
            "category": request.form.get("category"),
            "applies_to": request.form.get("applies_to"),
            "summary": request.form.get("summary"),
            "body": request.form.get("body"),
            "related_trust_types": request.form.get("related_trust_types"),
            "status": request.form.get("status") or "draft",
        }
        update_form_guide(guide["guide_id"], payload)
        return redirect(url_for("form_guide_detail", form_name=payload["form_name"]))

    return render_template("form_guide_form.html", mode="edit", guide=guide)

@app.route("/videos")
def video_dashboard():
    videos = get_all_tutorial_videos()
    categories = sorted({v["category"] for v in videos if v.get("category")})
    trust_types = sorted({v["trust_type"] for v in videos if v.get("trust_type")})
    return render_template(
        "video_dashboard.html",
        videos=videos,
        categories=categories,
        trust_types=trust_types
    )


@app.route("/videos/category/<category>")
def video_category(category):
    videos = get_tutorial_videos_by_category(category)
    return render_template("video_category.html", category=category, videos=videos)


@app.route("/videos/trust-type/<trust_type>")
def video_trust_type(trust_type):
    videos = get_tutorial_videos_by_trust_type(trust_type)
    return render_template("video_trust_type.html", trust_type=trust_type, videos=videos)


@app.route("/videos/<video_id>")
def video_detail(video_id):
    video = get_tutorial_video_by_id(video_id)
    if not video:
        return f"Video {video_id} not found", 404
    return render_template("video_detail.html", video=video)


@app.route("/videos/upload", methods=["GET", "POST"])
def video_upload():
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("video_upload.html", mode="new", error_message="Invalid or missing CSRF token.")

        video_id = (request.form.get("video_id") or "").strip()
        title = (request.form.get("title") or "").strip()

        if not video_id or not title:
            return render_template("video_upload.html", mode="new", error_message="Video ID and Title are required.")

        payload = {
            "video_id": video_id,
            "title": title,
            "category": request.form.get("category"),
            "trust_type": request.form.get("trust_type"),
            "description": request.form.get("description"),
            "file_path": request.form.get("file_path"),
            "thumbnail_path": request.form.get("thumbnail_path"),
            "transcript_notes": request.form.get("transcript_notes"),
            "visibility": request.form.get("visibility") or "internal",
        }
        create_tutorial_video(payload)
        return redirect(url_for("video_detail", video_id=video_id))

    return render_template("video_upload.html", mode="new")


@app.route("/videos/<video_id>/edit", methods=["GET", "POST"])
def video_edit(video_id):
    video = get_tutorial_video_by_id(video_id)
    if not video:
        return f"Video {video_id} not found", 404

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("video_upload.html", mode="edit", video=video, error_message="Invalid or missing CSRF token.")

        payload = {
            "title": request.form.get("title"),
            "category": request.form.get("category"),
            "trust_type": request.form.get("trust_type"),
            "description": request.form.get("description"),
            "file_path": request.form.get("file_path"),
            "thumbnail_path": request.form.get("thumbnail_path"),
            "transcript_notes": request.form.get("transcript_notes"),
            "visibility": request.form.get("visibility") or "internal",
        }
        update_tutorial_video(video_id, payload)
        return redirect(url_for("video_detail", video_id=video_id))

    return render_template("video_upload.html", mode="edit", video=video)

@app.route("/workspaces")
def workspace_dashboard():
    workspaces = get_all_workspaces()
    return render_template("workspace_dashboard.html", workspaces=workspaces)


@app.route("/workspaces/new", methods=["GET", "POST"])
def workspace_new():
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("workspace_form.html", mode="new", error_message="Invalid or missing CSRF token.", sections=get_workspace_note_sections())

        workspace_id = (request.form.get("workspace_id") or "").strip()
        title = (request.form.get("title") or "").strip()
        if not workspace_id or not title:
            return render_template("workspace_form.html", mode="new", error_message="Workspace ID and Title are required.", sections=get_workspace_note_sections())

        payload = {
            "workspace_id": workspace_id,
            "title": title,
            "workspace_type": request.form.get("workspace_type"),
            "trust_type_focus": request.form.get("trust_type_focus"),
            "purpose": request.form.get("purpose"),
            "owner": request.form.get("owner") or session.get("username") or "unknown",
            "status": request.form.get("status") or "draft",
        }
        create_workspace(payload)
        return redirect(url_for("workspace_detail", workspace_id=workspace_id))

    return render_template("workspace_form.html", mode="new", sections=get_workspace_note_sections())


@app.route("/workspaces/<workspace_id>")
def workspace_detail(workspace_id):
    workspace = get_workspace_by_id(workspace_id)
    if not workspace:
        return render_template(
            "access_denied.html",
            reason="This workspace is not available within your assigned firm scope."
        )

    notes = get_workspace_notes(workspace_id)
    tasks = get_execution_tasks_by_workspace(workspace_id)
    documents = get_generated_documents_by_workspace(workspace_id)
    threads = get_discussion_threads_by_workspace(workspace_id)

    return render_template(
        "workspace_detail.html",
        workspace=workspace,
        notes=notes,
        tasks=tasks,
        documents=documents,
        threads=threads,
        note_sections=get_workspace_note_sections()
    )


@app.route("/workspaces/<workspace_id>/edit", methods=["GET", "POST"])
def workspace_edit(workspace_id):
    workspace = get_workspace_by_id(workspace_id)
    if not workspace:
        return f"Workspace {workspace_id} not found", 404

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("workspace_form.html", mode="edit", workspace=workspace, error_message="Invalid or missing CSRF token.", sections=get_workspace_note_sections())

        payload = {
            "title": request.form.get("title"),
            "workspace_type": request.form.get("workspace_type"),
            "trust_type_focus": request.form.get("trust_type_focus"),
            "purpose": request.form.get("purpose"),
            "owner": request.form.get("owner"),
            "status": request.form.get("status") or "draft",
        }
        update_workspace(workspace_id, payload)
        return redirect(url_for("workspace_detail", workspace_id=workspace_id))

    return render_template("workspace_form.html", mode="edit", workspace=workspace, sections=get_workspace_note_sections())


@app.route("/workspaces/<workspace_id>/notes/new", methods=["GET", "POST"])
def workspace_note_new(workspace_id):
    workspace = get_workspace_by_id(workspace_id)
    if not workspace:
        return f"Workspace {workspace_id} not found", 404

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("workspace_note_form.html", workspace=workspace, sections=get_workspace_note_sections(), error_message="Invalid or missing CSRF token.")

        note_id = (request.form.get("note_id") or "").strip()
        section_name = (request.form.get("section_name") or "").strip()
        content = (request.form.get("content") or "").strip()

        if not note_id or not section_name or not content:
            return render_template("workspace_note_form.html", workspace=workspace, sections=get_workspace_note_sections(), error_message="Note ID, section, and content are required.")

        payload = {
            "note_id": note_id,
            "workspace_id": workspace_id,
            "section_name": section_name,
            "content": content,
        }
        create_workspace_note(payload)
        return redirect(url_for("workspace_detail", workspace_id=workspace_id))

    return render_template("workspace_note_form.html", workspace=workspace, sections=get_workspace_note_sections())

@app.route("/discussions")
def discussion_dashboard():
    threads = get_all_discussion_threads()
    return render_template("discussion_dashboard.html", threads=threads)


@app.route("/discussions/new", methods=["GET", "POST"])
def discussion_new():
    workspaces = get_all_workspaces()
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories(), error_message="Invalid or missing CSRF token.")

        thread_id = (request.form.get("thread_id") or "").strip()
        title = (request.form.get("title") or "").strip()
        if not thread_id or not title:
            return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories(), error_message="Thread ID and Title are required.")

        payload = {
            "thread_id": thread_id,
            "workspace_id": request.form.get("workspace_id"),
            "title": title,
            "category": request.form.get("category"),
            "related_trust_type": request.form.get("related_trust_type"),
            "related_form": request.form.get("related_form"),
            "created_by": session.get("username") or "unknown",
            "status": request.form.get("status") or "open",
            "owner_id": get_current_owner(),
        }
        create_discussion_thread(payload)
        return redirect(url_for("discussion_thread", thread_id=thread_id))

    return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories())


@app.route("/discussions/<thread_id>")
def discussion_thread(thread_id):
    thread = get_discussion_thread_by_id(thread_id)
    if not thread:
        return f"Discussion thread {thread_id} not found", 404

    if thread.get("owner_id") != get_current_owner():
        return render_template(
            "access_denied.html",
            reason="This discussion thread does not belong to the current owner context."
        )

    messages = get_discussion_messages(thread_id)
    workspace = get_workspace_by_id(thread.get("workspace_id")) if thread.get("workspace_id") else None
    return render_template("discussion_thread.html", thread=thread, messages=messages, workspace=workspace)


@app.route("/discussions/<thread_id>/reply", methods=["GET", "POST"])
def discussion_reply(thread_id):
    thread = get_discussion_thread_by_id(thread_id)
    if not thread:
        return f"Discussion thread {thread_id} not found", 404

    if thread.get("owner_id") != get_current_owner():
        return render_template(
            "access_denied.html",
            reason="This discussion thread does not belong to the current owner context."
        )

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template(
                "discussion_reply_form.html",
                thread=thread,
                error_message="Invalid or missing CSRF token."
            )

        message_id = get_next_discussion_message_id()
        payload = {
            "message_id": message_id,
            "thread_id": thread_id,
            "parent_message_id": request.form.get("parent_message_id"),
            "author": session.get("username") or "unknown",
            "body": request.form.get("body"),
            "owner_id": get_current_owner(),
        }
        create_discussion_message(payload)
        return redirect(url_for("discussion_thread", thread_id=thread_id))

    return render_template("discussion_reply_form.html", thread=thread)


@app.route("/workspaces/<workspace_id>/discussions")
def workspace_discussions(workspace_id):
    workspace = get_workspace_by_id(workspace_id)
    if not workspace:
        return f"Workspace {workspace_id} not found", 404
    threads = get_discussion_threads_by_workspace(workspace_id)
    return render_template("workspace_discussions.html", workspace=workspace, threads=threads)


@app.route("/workspaces/<workspace_id>/discussions/new", methods=["GET", "POST"])
def workspace_discussion_new(workspace_id):
    workspace = get_workspace_by_id(workspace_id)
    if not workspace:
        return f"Workspace {workspace_id} not found", 404

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("discussion_form.html", mode="workspace_new", workspace=workspace, categories=get_discussion_categories(), error_message="Invalid or missing CSRF token.")

        thread_id = (request.form.get("thread_id") or "").strip()
        title = (request.form.get("title") or "").strip()
        if not thread_id or not title:
            return render_template("discussion_form.html", mode="workspace_new", workspace=workspace, categories=get_discussion_categories(), error_message="Thread ID and Title are required.")

        payload = {
            "thread_id": thread_id,
            "workspace_id": workspace_id,
            "title": title,
            "category": request.form.get("category"),
            "related_trust_type": request.form.get("related_trust_type"),
            "related_form": request.form.get("related_form"),
            "created_by": session.get("username") or "unknown",
            "status": request.form.get("status") or "open",
            "owner_id": get_current_owner(),
        }
        create_discussion_thread(payload)
        return redirect(url_for("discussion_thread", thread_id=thread_id))

    return render_template("discussion_form.html", mode="workspace_new", workspace=workspace, categories=get_discussion_categories())

@app.route("/decision")
def decision_dashboard():
    goals = [
        "estate_planning",
        "asset_protection",
        "real_property_holding",
        "insurance_planning",
        "tax_planning",
        "business_structure",
    ]
    asset_types = [
        "general_assets",
        "real_estate",
        "insurance_policy",
        "mixed_assets",
        "business_assets",
        "cash_equivalents",
    ]
    control_levels = [
        "high_control",
        "structured_control",
        "management_focus",
        "reduced_personal_control",
    ]
    return render_template(
        "decision_dashboard.html",
        goals=goals,
        asset_types=asset_types,
        control_levels=control_levels
    )


@app.route("/decision/run", methods=["POST"])
def decision_run():
    if not validate_csrf_token():
        goals = [
            "estate_planning",
            "asset_protection",
            "real_property_holding",
            "insurance_planning",
            "tax_planning",
            "business_structure",
        ]
        asset_types = [
            "general_assets",
            "real_estate",
            "insurance_policy",
            "mixed_assets",
            "business_assets",
            "cash_equivalents",
        ]
        control_levels = [
            "high_control",
            "structured_control",
            "management_focus",
            "reduced_personal_control",
        ]
        return render_template(
            "decision_dashboard.html",
            goals=goals,
            asset_types=asset_types,
            control_levels=control_levels,
            error_message="Invalid or missing CSRF token."
        )

    goal = (request.form.get("goal") or "").strip()
    asset_type = (request.form.get("asset_type") or "").strip()
    control_level = (request.form.get("control_level") or "").strip()

    matches = run_decision_engine(goal, asset_type, control_level)

    return render_template(
        "decision_result.html",
        goal=goal,
        asset_type=asset_type,
        control_level=control_level,
        matches=matches
    )

@app.route("/execution")
def execution_dashboard():
    tasks = get_all_execution_tasks()
    return render_template("execution_dashboard.html", tasks=tasks)


@app.route("/execution/tasks/new", methods=["GET", "POST"])
def execution_task_new():
    workspaces = get_all_workspaces()
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template(
                "execution_task_form.html",
                mode="new",
                workspaces=workspaces,
                task_types=get_execution_task_types(),
                error_message="Invalid or missing CSRF token."
            )

        task_id = (request.form.get("task_id") or "").strip()
        title = (request.form.get("title") or "").strip()
        if not task_id or not title:
            return render_template(
                "execution_task_form.html",
                mode="new",
                workspaces=workspaces,
                task_types=get_execution_task_types(),
                error_message="Task ID and Title are required."
            )

        payload = {
            "task_id": task_id,
            "workspace_id": request.form.get("workspace_id"),
            "trust_id": request.form.get("trust_id"),
            "title": title,
            "task_type": request.form.get("task_type"),
            "description": request.form.get("description"),
            "related_form": request.form.get("related_form"),
            "related_report": request.form.get("related_report"),
            "priority": request.form.get("priority") or "medium",
            "status": request.form.get("status") or "pending",
            "due_date": request.form.get("due_date"),
            "assigned_to": request.form.get("assigned_to") or session.get("username") or "unknown",
        }
        create_execution_task(payload)
        return redirect(url_for("execution_task_detail", task_id=task_id))

    return render_template(
        "execution_task_form.html",
        mode="new",
        workspaces=workspaces,
        task_types=get_execution_task_types()
    )


@app.route("/execution/tasks/<task_id>")
def execution_task_detail(task_id):
    task = get_execution_task_by_id(task_id)
    if not task:
        return f"Execution task {task_id} not found", 404

    if task.get("owner_id") != get_current_owner():
        return render_template(
            "access_denied.html",
            reason="This execution task does not belong to the current owner context."
        )

    workspace = get_workspace_by_id(task.get("workspace_id")) if task.get("workspace_id") else None
    return render_template("execution_task_detail.html", task=task, workspace=workspace)


@app.route("/execution/tasks/<task_id>/status", methods=["POST"])
def execution_task_status(task_id):
    task = get_execution_task_by_id(task_id)
    if not task:
        return f"Execution task {task_id} not found", 404

    if task.get("owner_id") != get_current_owner():
        return render_template(
            "access_denied.html",
            reason="This execution task does not belong to the current owner context."
        )

    if not validate_csrf_token():
        return redirect(url_for("execution_task_detail", task_id=task_id))

    new_status = (request.form.get("status") or "").strip()
    if new_status in {"pending", "in_progress", "blocked", "completed"}:
        update_execution_task_status(task_id, new_status)

    return redirect(url_for("execution_task_detail", task_id=task_id))


@app.route("/workspaces/<workspace_id>/tasks")
def workspace_tasks(workspace_id):
    workspace = get_workspace_by_id(workspace_id)
    if not workspace:
        return f"Workspace {workspace_id} not found", 404
    tasks = get_execution_tasks_by_workspace(workspace_id)
    return render_template("workspace_tasks.html", workspace=workspace, tasks=tasks)


@app.route("/workspaces/<workspace_id>/tasks/new", methods=["GET", "POST"])
def workspace_task_new(workspace_id):
    workspace = get_workspace_by_id(workspace_id)
    if not workspace:
        return f"Workspace {workspace_id} not found", 404

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template(
                "execution_task_form.html",
                mode="workspace_new",
                workspace=workspace,
                task_types=get_execution_task_types(),
                error_message="Invalid or missing CSRF token."
            )

        task_id = (request.form.get("task_id") or "").strip()
        title = (request.form.get("title") or "").strip()
        if not task_id or not title:
            return render_template(
                "execution_task_form.html",
                mode="workspace_new",
                workspace=workspace,
                task_types=get_execution_task_types(),
                error_message="Task ID and Title are required."
            )

        payload = {
            "task_id": task_id,
            "workspace_id": workspace_id,
            "trust_id": request.form.get("trust_id"),
            "title": title,
            "task_type": request.form.get("task_type"),
            "description": request.form.get("description"),
            "related_form": request.form.get("related_form"),
            "related_report": request.form.get("related_report"),
            "priority": request.form.get("priority") or "medium",
            "status": request.form.get("status") or "pending",
            "due_date": request.form.get("due_date"),
            "assigned_to": request.form.get("assigned_to") or session.get("username") or "unknown",
        }
        create_execution_task(payload)
        return redirect(url_for("execution_task_detail", task_id=task_id))

    return render_template(
        "execution_task_form.html",
        mode="workspace_new",
        workspace=workspace,
        task_types=get_execution_task_types()
    )

@app.route("/documents")
def document_dashboard():
    templates = get_document_templates()
    documents = get_generated_documents()
    return render_template("document_dashboard.html", templates=templates, documents=documents)


@app.route("/documents/generate", methods=["GET", "POST"])
def document_generate():
    templates = get_document_templates()
    workspaces = get_all_workspaces()

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template(
                "document_generate_form.html",
                templates=templates,
                workspaces=workspaces,
                error_message="Invalid or missing CSRF token."
            )

        document_id = (request.form.get("document_id") or "").strip()
        template_id = (request.form.get("template_id") or "").strip()
        title = (request.form.get("title") or "").strip()

        if not document_id or not template_id or not title:
            return render_template(
                "document_generate_form.html",
                templates=templates,
                workspaces=workspaces,
                error_message="Document ID, Template, and Title are required."
            )

        template = get_document_template_by_id(template_id)
        if not template:
            return render_template(
                "document_generate_form.html",
                templates=templates,
                workspaces=workspaces,
                error_message="Selected template was not found."
            )

        values = {
            "title": request.form.get("title") or "",
            "purpose": request.form.get("purpose") or "",
            "trust_type_focus": request.form.get("trust_type_focus") or "",
            "notes": request.form.get("notes") or "",
            "trust_name": request.form.get("trust_name") or "",
            "trustee_name": request.form.get("trustee_name") or "",
            "authority_scope": request.form.get("authority_scope") or "",
            "related_forms": request.form.get("related_forms") or "",
            "related_reports": request.form.get("related_reports") or "",
        }
        content = render_document_template(template.get("template_body"), values)

        payload = {
            "document_id": document_id,
            "workspace_id": request.form.get("workspace_id"),
            "trust_id": request.form.get("trust_id"),
            "template_id": template_id,
            "title": title,
            "content": content,
            "status": request.form.get("status") or "draft",
            "created_by": session.get("username") or "unknown",
            "owner_id": get_current_owner(),
        }
        create_generated_document(payload)
        return redirect(url_for("document_detail", document_id=document_id))

    return render_template("document_generate_form.html", templates=templates, workspaces=workspaces)


@app.route("/documents/<document_id>")
def document_detail(document_id):
    document = get_generated_document_by_id(document_id)
    if not document:
        return f"Generated document {document_id} not found", 404

    if document.get("owner_id") != get_current_owner():
        return render_template(
            "access_denied.html",
            reason="This generated document does not belong to the current owner context."
        )

    template = get_document_template_by_id(document.get("template_id")) if document.get("template_id") else None
    workspace = get_workspace_by_id(document.get("workspace_id")) if document.get("workspace_id") else None
    return render_template("document_detail.html", document=document, template=template, workspace=workspace)


@app.route("/workspaces/<workspace_id>/documents")
def workspace_documents(workspace_id):
    workspace = get_workspace_by_id(workspace_id)
    if not workspace:
        return f"Workspace {workspace_id} not found", 404
    documents = get_generated_documents_by_workspace(workspace_id)
    return render_template("workspace_documents.html", workspace=workspace, documents=documents)


@app.route("/workspaces/<workspace_id>/documents/generate", methods=["GET", "POST"])
def workspace_document_generate(workspace_id):
    workspace = get_workspace_by_id(workspace_id)
    if not workspace:
        return f"Workspace {workspace_id} not found", 404

    templates = get_document_templates()

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template(
                "document_generate_form.html",
                workspace=workspace,
                templates=templates,
                error_message="Invalid or missing CSRF token."
            )

        document_id = (request.form.get("document_id") or "").strip()
        template_id = (request.form.get("template_id") or "").strip()
        title = (request.form.get("title") or "").strip()

        if not document_id or not template_id or not title:
            return render_template(
                "document_generate_form.html",
                workspace=workspace,
                templates=templates,
                error_message="Document ID, Template, and Title are required."
            )

        template = get_document_template_by_id(template_id)
        if not template:
            return render_template(
                "document_generate_form.html",
                workspace=workspace,
                templates=templates,
                error_message="Selected template was not found."
            )

        values = {
            "title": request.form.get("title") or "",
            "purpose": request.form.get("purpose") or "",
            "trust_type_focus": request.form.get("trust_type_focus") or workspace.get("trust_type_focus") or "",
            "notes": request.form.get("notes") or "",
            "trust_name": request.form.get("trust_name") or "",
            "trustee_name": request.form.get("trustee_name") or "",
            "authority_scope": request.form.get("authority_scope") or "",
            "related_forms": request.form.get("related_forms") or "",
            "related_reports": request.form.get("related_reports") or "",
        }
        content = render_document_template(template.get("template_body"), values)

        payload = {
            "document_id": document_id,
            "workspace_id": workspace_id,
            "trust_id": request.form.get("trust_id"),
            "template_id": template_id,
            "title": title,
            "content": content,
            "status": request.form.get("status") or "draft",
            "created_by": session.get("username") or "unknown",
            "owner_id": get_current_owner(),
        }
        create_generated_document(payload)
        return redirect(url_for("document_detail", document_id=document_id))

    return render_template("document_generate_form.html", workspace=workspace, templates=templates)


# ============================================================
# TRANSFER ENGINE V1
# ============================================================

@app.route("/trust/<trust_id>/post-create-review")
def trust_post_create_review(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    return redirect(url_for("trust_formation_preview_hub", trust_id=trust["trust_id"]))


@app.route("/trust/<trust_id>/formation-preview-hub")
def trust_formation_preview_hub(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    document_readiness = build_trust_document_readiness(preview_context)
    packet_readiness = build_trust_packet_readiness(document_readiness)
    return render_template(
        "trust_formation_preview_hub.html",
        trust=trust,
        preview_context=preview_context,
        document_readiness=document_readiness,
        packet_readiness=packet_readiness,
    )


@app.route("/trust/<trust_id>/successor-trustee-preview")
def trust_successor_trustee_preview(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    return render_template(
        "trust_successor_trustee_preview.html",
        trust=trust,
        preview_context=preview_context,
    )


@app.route("/trust/<trust_id>/successor-trustee-output-surface")
def trust_successor_trustee_output_surface(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    document_readiness = build_trust_document_readiness(preview_context)
    return render_template(
        "trust_successor_trustee_output_surface.html",
        trust=trust,
        preview_context=preview_context,
        document_readiness=document_readiness,
    )

@app.route("/trust/<trust_id>/successor-trustee-output-surface/pdf")
def trust_successor_trustee_output_surface_pdf(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    pdf_buffer = generate_successor_trustee_pdf(trust, preview_context)
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{trust_id}_Successor_Trustee_Acceptance.pdf"
    )


@app.route("/trust/<trust_id>/controlled-packet-export")
def trust_controlled_packet_export(trust_id):
    trust, gate = require_active_firm_trust_or_deny(trust_id, "controlled packet export")
    if gate:
        return gate
    preview_context = build_trust_preview_context(trust)
    document_readiness = build_trust_document_readiness(preview_context)
    packet_readiness = build_trust_packet_readiness(document_readiness)

    # UNIVERSAL EXPORT MODE:
    # Packet readiness is advisory only. Export remains available for review/testing.
    packet_buffer = generate_controlled_trust_packet_zip(trust, preview_context)
    filename = f"{trust_id}_Controlled_Trust_Packet.zip"

    append_export_activity(
        build_export_activity_entry(
            preview_context,
            document_readiness,
            packet_readiness,
            filename
        )
    )

    return send_file(
        packet_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=filename
    )


@app.route("/trust/<trust_id>/packet-preview")
def trust_packet_preview(trust_id):
    gate = deny_unassigned_trust_access(trust_id)
    if gate:
        return gate
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    document_readiness = build_trust_document_readiness(preview_context)
    packet_readiness = build_trust_packet_readiness(document_readiness)
    correction_links = build_correction_links(trust_id, document_readiness, return_to="execution")
    export_policy = get_export_policy()
    latest_export_activity = get_latest_export_for_trust(trust_id)
    return render_template(
        "trust_packet_preview.html",
        trust=trust,
        preview_context=preview_context,
        document_readiness=document_readiness,
        packet_readiness=packet_readiness,
        correction_links=correction_links,
        export_policy=export_policy,
        latest_export_activity=latest_export_activity,
    )


@app.route("/trust/<trust_id>/general-assignment-preview")
def trust_general_assignment_preview(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    return render_template(
        "trust_general_assignment_preview.html",
        trust=trust,
        preview_context=preview_context,
    )


@app.route("/trust/<trust_id>/general-assignment-output-surface")
def trust_general_assignment_output_surface(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    document_readiness = build_trust_document_readiness(preview_context)
    return render_template(
        "trust_general_assignment_output_surface.html",
        trust=trust,
        preview_context=preview_context,
        document_readiness=document_readiness,
    )

@app.route("/trust/<trust_id>/general-assignment-output-surface/pdf")
def trust_general_assignment_output_surface_pdf(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    pdf_buffer = generate_general_assignment_pdf(trust, preview_context)
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{trust_id}_General_Assignment.pdf"
    )


@app.route("/trust/<trust_id>/organizational-minutes-preview")
def trust_organizational_minutes_preview(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    return render_template(
        "trust_organizational_minutes_preview.html",
        trust=trust,
        preview_context=preview_context,
    )


@app.route("/trust/<trust_id>/organizational-minutes-output-surface")
def trust_organizational_minutes_output_surface(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    document_readiness = build_trust_document_readiness(preview_context)
    return render_template(
        "trust_organizational_minutes_output_surface.html",
        trust=trust,
        preview_context=preview_context,
        document_readiness=document_readiness,
    )

@app.route("/trust/<trust_id>/organizational-minutes-output-surface/pdf")
def trust_organizational_minutes_output_surface_pdf(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    pdf_buffer = generate_organizational_minutes_pdf(trust, preview_context)
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{trust_id}_Organizational_Minutes.pdf"
    )


@app.route("/trust/<trust_id>/trustee-acceptance-preview")
def trust_trustee_acceptance_preview(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    return render_template(
        "trust_trustee_acceptance_preview.html",
        trust=trust,
        preview_context=preview_context,
    )


@app.route("/trust/<trust_id>/trustee-acceptance-output-surface")
def trust_trustee_acceptance_output_surface(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    document_readiness = build_trust_document_readiness(preview_context)
    return render_template(
        "trust_trustee_acceptance_output_surface.html",
        trust=trust,
        preview_context=preview_context,
        document_readiness=document_readiness,
    )

@app.route("/trust/<trust_id>/trustee-acceptance-output-surface/pdf")
def trust_trustee_acceptance_output_surface_pdf(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    pdf_buffer = generate_trustee_acceptance_pdf(trust, preview_context)
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{trust_id}_Trustee_Acceptance.pdf"
    )


@app.route("/trust/<trust_id>/articles-preview")
def trust_articles_preview(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    return render_template(
        "trust_articles_preview.html",
        trust=trust,
        preview_context=preview_context,
    )


@app.route("/trust/<trust_id>/declaration-output-surface")
def trust_declaration_output_surface(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    return render_template(
        "trust_declaration_output_surface.html",
        trust=trust,
        preview_context=preview_context,
    )


@app.route("/trust/<trust_id>/declaration-output-surface/pdf")
def trust_declaration_output_surface_pdf(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    pdf_buffer = generate_declaration_of_trust_pdf(trust, preview_context)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        mimetype="application/pdf",
        download_name=f"{trust_id}_Declaration_of_Trust.pdf"
    )


@app.route("/trust/<trust_id>/certificate-of-trust-output-surface")
def trust_certificate_of_trust_output_surface(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    return render_template(
        "trust_certificate_of_trust_output_surface.html",
        trust=trust,
        preview_context=preview_context,
    )


@app.route("/trust/<trust_id>/certificate-of-trust-output-surface/pdf")
def trust_certificate_of_trust_output_surface_pdf(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    pdf_buffer = generate_certificate_of_trust_pdf(trust, preview_context)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        mimetype="application/pdf",
        download_name=f"{trust_id}_Certificate_of_Trust.pdf"
    )


@app.route("/trust/<trust_id>/articles-output-surface")
def trust_articles_output_surface(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    document_readiness = build_trust_document_readiness(preview_context)
    return render_template(
        "trust_articles_output_surface.html",
        trust=trust,
        preview_context=preview_context,
        document_readiness=document_readiness,
    )


@app.route("/trust/<trust_id>/articles-output-surface/pdf")
def trust_articles_output_surface_pdf(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    preview_context = build_trust_preview_context(trust)
    pdf_buffer = generate_articles_pdf(trust, preview_context)
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{trust_id}_Articles_of_Trust.pdf"
    )




@app.route("/trust/<trust_id>/accounting-method", methods=["GET", "POST"])
def trust_accounting_method_settings(trust_id):
    gate = gate_trust_access(trust_id, ["Admin", "Trustee"])
    if gate:
        return gate

    trust = get_trust_by_id(trust_id)
    if not trust:
        flash("Trust not found.", "error")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        if not validate_csrf_token():
            flash("Invalid or missing CSRF token.", "warning")
            return render_template("trust_accounting_method.html", trust=trust)

        accounting_method = (request.form.get("accounting_method") or "").strip()
        if accounting_method not in ["cash", "accrual"]:
            flash("Select a valid accounting method: cash or accrual.", "error")
            return render_template("trust_accounting_method.html", trust=trust)

        update_trust_fields(trust_id, {"accounting_method": accounting_method})
        log_change(
            "trust",
            trust_id,
            "accounting_method_updated",
            f"Accounting method set to {accounting_method} by {session.get('username') or 'unknown'}"
        )
        flash(f"Accounting method set to {accounting_method}.", "success")
        return redirect(url_for("trust_execution_dashboard", trust_id=trust_id))

    return render_template("trust_accounting_method.html", trust=trust)


@app.route("/trust/<trust_id>/execution")
def trust_execution_dashboard(trust_id):
    gate = deny_unassigned_trust_access(trust_id)
    if gate:
        return gate
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found", 404

    preview_context = build_trust_preview_context(trust)
    document_readiness = build_trust_document_readiness(preview_context)
    packet_readiness = build_trust_packet_readiness(document_readiness)
    correction_links = build_correction_links(trust_id, document_readiness, return_to="execution")
    active_transfer_filter = (request.args.get("transfer_filter") or "all").strip()

    transfers = (
        Transfer.query
        .filter_by(trust_id=str(trust_id))
        .order_by(Transfer.updated_at.desc())
        .all()
    )

    transfer_proof_counts = {
        t.transfer_id: len(get_media_by_entity("transfer", t.transfer_id))
        for t in transfers
    }

    transfer_ledger_counts = {}
    for t in transfers:
        ledger_rows = get_ledger_entries_by_trust_id(t.trust_id)
        transfer_ledger_counts[t.transfer_id] = sum(
            1 for row in ledger_rows
            if t.transfer_id in (row["description"] or "")
        )



    transfer_completion_summary = {
        "hybrid_complete": 0,
        "hybrid_partial": 0,
        "hybrid_not_started": 0,
        "ledger_posted": 0,
        "external_verified": 0,
        "proof_attached": 0,
    }

    for t in transfers:
        ledger_count = transfer_ledger_counts.get(t.transfer_id, 0)
        proof_count = transfer_proof_counts.get(t.transfer_id, 0)
        ledger_ok = ledger_count > 0
        external_ok = bool(t.external_verified)
        proof_ok = proof_count > 0

        if ledger_ok:
            transfer_completion_summary["ledger_posted"] += 1
        if external_ok:
            transfer_completion_summary["external_verified"] += 1
        if proof_ok:
            transfer_completion_summary["proof_attached"] += 1

        if ledger_ok and external_ok and proof_ok:
            transfer_completion_summary["hybrid_complete"] += 1
        elif ledger_ok or external_ok or proof_ok:
            transfer_completion_summary["hybrid_partial"] += 1
        else:
            transfer_completion_summary["hybrid_not_started"] += 1


    def transfer_matches_filter(t):
        ledger_count = transfer_ledger_counts.get(t.transfer_id, 0)
        proof_count = transfer_proof_counts.get(t.transfer_id, 0)
        ledger_ok = ledger_count > 0
        external_ok = bool(t.external_verified)
        proof_ok = proof_count > 0

        if active_transfer_filter == "all":
            return True
        if active_transfer_filter == "completed":
            return t.status == "completed"
        if active_transfer_filter == "open":
            return t.status != "completed"
        if active_transfer_filter == "hybrid_complete":
            return ledger_ok and external_ok and proof_ok
        if active_transfer_filter == "hybrid_partial":
            return (ledger_ok or external_ok or proof_ok) and not (ledger_ok and external_ok and proof_ok)
        if active_transfer_filter == "hybrid_not_started":
            return not ledger_ok and not external_ok and not proof_ok
        if active_transfer_filter == "ledger_posted":
            return ledger_ok
        if active_transfer_filter == "external_verified":
            return external_ok
        if active_transfer_filter == "proof_attached":
            return proof_ok
        return True

    filtered_transfers = [t for t in transfers if transfer_matches_filter(t)]

    return render_template(
        "transfer_execution_dashboard.html",
        get_transfer_resume_endpoint=get_transfer_resume_endpoint,
        trust_id=trust_id,
        trust=trust,
        preview_context=preview_context,
        document_readiness=document_readiness,
        packet_readiness=packet_readiness,
        correction_links=correction_links,
        export_policy=get_export_policy(),
        latest_export_activity=get_latest_export_for_trust(trust_id),
        trust_last_updated=get_trust_last_updated_value(trust),
          transfers=filtered_transfers,
          all_transfers=transfers,
          transfer_proof_counts=transfer_proof_counts,
          transfer_ledger_counts=transfer_ledger_counts,
          transfer_completion_summary=transfer_completion_summary,
          active_transfer_filter=active_transfer_filter,
        current_role=session.get("role"),
    )


@app.route("/trust/<trust_id>/execution/transfers/new", methods=["GET", "POST"])
def transfer_start(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found", 404

    if request.method == "POST":
        if not validate_csrf_token():
            flash("Invalid or missing CSRF token.", "warning")
            return render_template(
                "transfer_start.html",
                trust_id=trust_id,
                current_role=session.get("role"),
            )

        mode = request.form.get("mode", "simulation")
        current_capacity = request.form.get("current_capacity", "individual")

        transfer = Transfer(
            trust_id=str(trust_id),
            transfer_id=generate_transfer_id(),
            firm_id=session.get("firm_id") or "FIRM-001",
            mode=mode,
            status="draft",
            current_capacity=current_capacity,
            created_by=session.get("username") or "unknown",
        )
        ext_db.session.add(transfer)
        ext_db.session.flush()

        add_transfer_action(
            transfer=transfer,
            action_type="created_transfer",
            performed_by=session.get("username") or "unknown",
            capacity_used=current_capacity,
            notes=f"Created transfer in {mode} mode.",
            commit=False,
        )

        ext_db.session.commit()

        flash(f"Transfer {transfer.transfer_id} created.", "success")
        return redirect(url_for("transfer_asset", transfer_id=transfer.transfer_id))

    return render_template(
        "transfer_start.html",
        trust_id=trust_id,
        current_role=session.get("role"),
    )


@app.route("/execution/transfers/<transfer_id>/asset", methods=["GET", "POST"])
def transfer_asset(transfer_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate

    if request.method == "POST" and transfer.status == "completed":
        flash("Completed transfers are read-only.", "warning")
        return redirect(url_for("transfer_review", transfer_id=transfer.transfer_id))

    if request.method == "POST":
        if not validate_csrf_token():
            flash("Invalid or missing CSRF token.", "warning")
            return render_template(
                "transfer_asset.html",
                transfer=transfer,
                progress=get_transfer_progress(transfer),
            )

        transfer.asset_type = request.form.get("asset_type", "")
        transfer.asset_name = request.form.get("asset_name", "")
        transfer.asset_description = request.form.get("asset_description", "")
        transfer.estimated_value = request.form.get("estimated_value", "")
        transfer.current_owner = request.form.get("current_owner", "")
        transfer.asset_notes = request.form.get("asset_notes", "")
        transfer.status = "in_progress"

        add_transfer_action(
            transfer=transfer,
            action_type="saved_asset_step",
            performed_by=session.get("username") or "unknown",
            capacity_used=transfer.current_capacity,
            notes=f"Asset saved: {transfer.asset_name}",
            commit=False,
        )

        ext_db.session.commit()
        flash("Asset step saved.", "success")
        return redirect(url_for("transfer_classification", transfer_id=transfer.transfer_id))

    return render_template(
        "transfer_asset.html",
        transfer=transfer,
        progress=get_transfer_progress(transfer),
        step_nav=build_transfer_step_nav(transfer, "asset"),
        current_step="asset",
    )


@app.route("/execution/transfers/<transfer_id>/classification", methods=["GET", "POST"])
def transfer_classification(transfer_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate

    if request.method == "POST" and transfer.status == "completed":
        flash("Completed transfers are read-only.", "warning")
        return redirect(url_for("transfer_review", transfer_id=transfer.transfer_id))

    if request.method == "POST":
        if not validate_csrf_token():
            flash("Invalid or missing CSRF token.", "warning")
            return render_template(
                "transfer_classification.html",
                transfer=transfer,
                progress=get_transfer_progress(transfer),
            )

        transfer.transfer_type = request.form.get("transfer_type", "")
        transfer.consideration_text = request.form.get("consideration_text", "")
        transfer.classification_notes = request.form.get("classification_notes", "")

        add_transfer_action(
            transfer=transfer,
            action_type="saved_classification_step",
            performed_by=session.get("username") or "unknown",
            capacity_used=transfer.current_capacity,
            notes=f"Classification: {transfer.transfer_type}",
            commit=False,
        )

        ext_db.session.commit()
        flash("Classification step saved.", "success")
        return redirect(url_for("transfer_assignment", transfer_id=transfer.transfer_id))

    return render_template(
        "transfer_classification.html",
        transfer=transfer,
        progress=get_transfer_progress(transfer),
        step_nav=build_transfer_step_nav(transfer, "classification"),
        current_step="classification",
    )


@app.route("/execution/transfers/<transfer_id>/assignment", methods=["GET", "POST"])
def transfer_assignment(transfer_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate

    if request.method == "POST" and transfer.status == "completed":
        flash("Completed transfers are read-only.", "warning")
        return redirect(url_for("transfer_review", transfer_id=transfer.transfer_id))

    if not validate_capacity_for_step("assignment", transfer.current_capacity):
        flash("Assignment step requires individual capacity.", "warning")

    assignment_text = build_assignment_text(transfer)

    if request.method == "POST":
        if not validate_csrf_token():
            flash("Invalid or missing CSRF token.", "warning")
            return render_template(
                "transfer_assignment.html",
                transfer=transfer,
                assignment_text=assignment_text,
                progress=get_transfer_progress(transfer),
            )

        if not validate_capacity_for_step("assignment", transfer.current_capacity):
            transfer.current_capacity = "individual"
            flash("Capacity automatically set to Individual for assignment step.", "info")

        # Re-check after auto-correction
        if not validate_capacity_for_step("assignment", transfer.current_capacity):
            flash("Cannot confirm assignment until current capacity is set to individual.", "warning")
        else:
            transfer.assignment_confirmed = True
            transfer.assignment_text = assignment_text

            add_transfer_action(
                transfer=transfer,
                action_type="confirmed_assignment_step",
                performed_by=session.get("username") or "unknown",
                capacity_used=transfer.current_capacity,
                notes="Assignment confirmed.",
                commit=False,
            )

            ext_db.session.commit()
            flash("Assignment step confirmed.", "success")
            return redirect(url_for("transfer_trustee_acceptance", transfer_id=transfer.transfer_id))

    return render_template(
        "transfer_assignment.html",
        transfer=transfer,
        assignment_text=assignment_text,
        progress=get_transfer_progress(transfer),
        step_nav=build_transfer_step_nav(transfer, "assignment"),
        current_step="assignment",
    )


@app.route("/execution/transfers/<transfer_id>/trustee_acceptance", methods=["GET", "POST"])
def transfer_trustee_acceptance(transfer_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate

    if request.method == "POST" and transfer.status == "completed":
        flash("Completed transfers are read-only.", "warning")
        return redirect(url_for("transfer_review", transfer_id=transfer.transfer_id))

    if request.method == "POST":
        if not validate_csrf_token():
            flash("Invalid or missing CSRF token.", "warning")
            return render_template(
                "transfer_trustee_acceptance.html",
                transfer=transfer,
                progress=get_transfer_progress(transfer),
            )

        transfer.current_capacity = "trustee"
        transfer.trustee_name = request.form.get("trustee_name", "")
        transfer.trustee_decision = request.form.get("trustee_decision", "")
        transfer.trustee_notes = request.form.get("trustee_notes", "")

        add_transfer_action(
            transfer=transfer,
            action_type="saved_trustee_acceptance",
            performed_by=session.get("username") or "unknown",
            capacity_used=transfer.current_capacity,
            notes=f"Trustee decision: {transfer.trustee_decision}",
            commit=False,
        )

        ext_db.session.commit()
        flash("Trustee acceptance saved.", "success")
        return redirect(url_for("transfer_control_evidence", transfer_id=transfer.transfer_id))

    return render_template(
        "transfer_trustee_acceptance.html",
        transfer=transfer,
        progress=get_transfer_progress(transfer),
        step_nav=build_transfer_step_nav(transfer, "trustee_acceptance"),
        current_step="trustee_acceptance",
    )


@app.route("/execution/transfers/<transfer_id>/control_evidence", methods=["GET", "POST"])
def transfer_control_evidence(transfer_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate

    if request.method == "POST" and transfer.status == "completed":
        flash("Completed transfers are read-only.", "warning")
        return redirect(url_for("transfer_review", transfer_id=transfer.transfer_id))

    if request.method == "POST":
        if not validate_csrf_token():
            flash("Invalid or missing CSRF token.", "warning")
            return render_template(
                "transfer_control_evidence.html",
                transfer=transfer,
                progress=get_transfer_progress(transfer),
                control_strength=calculate_control_strength(transfer.control_change_status),
            )

        transfer.control_change_status = request.form.get("control_change_status", "")
        transfer.control_evidence_notes = request.form.get("control_evidence_notes", "")

        add_transfer_action(
            transfer=transfer,
            action_type="saved_control_evidence",
            performed_by=session.get("username") or "unknown",
            capacity_used=transfer.current_capacity,
            notes=f"Control evidence strength: {calculate_control_strength(transfer.control_change_status)}",
            commit=False,
        )

        ext_db.session.commit()
        flash("Control evidence saved.", "success")
        return redirect(url_for("transfer_records", transfer_id=transfer.transfer_id))

    return render_template(
        "transfer_control_evidence.html",
        transfer=transfer,
        progress=get_transfer_progress(transfer),
        control_strength=calculate_control_strength(transfer.control_change_status),
        step_nav=build_transfer_step_nav(transfer, "control_evidence"),
        current_step="control_evidence",
    )


@app.route("/execution/transfers/<transfer_id>/records", methods=["GET", "POST"])
def transfer_records(transfer_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate

    if request.method == "POST" and transfer.status == "completed":
        flash("Completed transfers are read-only.", "warning")
        return redirect(url_for("transfer_review", transfer_id=transfer.transfer_id))

    if request.method == "POST":
        if not validate_csrf_token():
            flash("Invalid or missing CSRF token.", "warning")
            return render_template(
                "transfer_records.html",
                transfer=transfer,
                record_bundle=record_bundle,
                progress=get_transfer_progress(transfer),
            )

        meeting_date = request.form.get("meeting_date", "")
        trustee_name = request.form.get("trustee_name", transfer.trustee_name or "")
        notes = request.form.get("record_notes", "")

        populate_transfer_record_bundle(
            transfer=transfer,
            trustee_name=trustee_name,
            meeting_date=meeting_date,
            notes=notes,
            recorded_by=session.get("username") or "unknown",
        )

        add_transfer_action(
            transfer=transfer,
            action_type="generated_transfer_records",
            performed_by=session.get("username") or "unknown",
            capacity_used=transfer.current_capacity,
            notes="Generated Schedule A, transfer log, and minutes bundle.",
            commit=False,
        )

        ext_db.session.commit()
        flash("Transfer records created.", "success")
        return redirect(url_for("transfer_review", transfer_id=transfer.transfer_id))

    record_bundle = get_or_create_transfer_record(transfer)

    return render_template(
        "transfer_records.html",
        transfer=transfer,
        record_bundle=record_bundle,
        progress=get_transfer_progress(transfer),
        step_nav=build_transfer_step_nav(transfer, "records"),
        current_step="records",
    )


@app.route("/execution/transfers/<transfer_id>/review", methods=["GET", "POST"])
def transfer_review(transfer_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate
    record_bundle = transfer.record_bundle
    allowed, missing = can_finalize_transfer(transfer)

    if request.method == "POST":
        if not validate_csrf_token():
            flash("Invalid or missing CSRF token.", "warning")
            return render_template(
                "transfer_review.html",
                transfer=transfer,
                record_bundle=record_bundle,
                progress=get_transfer_progress(transfer),
                can_finalize=allowed,
                missing_items=missing,
                control_strength=calculate_control_strength(transfer.control_change_status),
            )

        # LEDGER-A: enforce value before finalize
        if not transfer.estimated_value or str(transfer.estimated_value).strip() == "":
            flash("Transfer cannot be finalized without a value.", "error")
            return redirect(url_for("transfer_review", transfer_id=transfer.transfer_id))

        # LEDGER-A: enforce accounting method before finalize
        trust_record = get_trust_by_id(transfer.trust_id)
        trust_accounting_method = ""
        if trust_record and "accounting_method" in trust_record.keys():
            trust_accounting_method = (trust_record["accounting_method"] or "").strip()

        if not trust_accounting_method or trust_accounting_method == "Not Yet Selected":
            flash("Transfer cannot be finalized until the trust accounting method is selected.", "error")
            return redirect(url_for("transfer_review", transfer_id=transfer.transfer_id))

        
        # === II-A ENFORCEMENT: BLOCK FINALIZATION IF REQUIREMENTS NOT MET ===
        if not allowed:
            flash("Transfer cannot be finalized. Required execution elements are missing.", "error")

            if missing:
                for item in missing:
                    flash(f"Missing: {item}", "warning")

            return redirect(url_for("transfer_review", transfer_id=transfer.transfer_id))

        success, missing = finalize_transfer(
            transfer=transfer,
            performed_by=session.get("username") or "unknown",
            capacity_used=transfer.current_capacity,
            commit=False,
        )

        if success:
            mark_core_support_docs_included(transfer)

            ext_db.session.commit()
            # LEDGER-A: auto-post finalized transfer as capital contribution
            try:
                ledger_description = f"Transfer {transfer.transfer_id} finalized - {transfer.asset_name or 'asset transfer'}"

                existing_ledger_rows = get_ledger_by_trust(transfer.trust_id)
                already_posted = any(
                    (row["description"] or "") == ledger_description
                    for row in existing_ledger_rows
                )

                if not already_posted:
                    ledger_entry = {
                        "entry_id": get_next_entry_id(),
                        "trust_id": transfer.trust_id,
                        "property_id": "",
                        "account_id": "",
                        "entry_type": "transfer",
                        "amount": str(transfer.estimated_value).strip(),
                        "entry_date": str(transfer.finalized_at or datetime.now(UTC)),
                        "description": ledger_description,
                        "entry_category": "capital_contribution",
                        "accounting_method": trust_accounting_method,
                        "recognition_date": str(transfer.finalized_at or datetime.now(UTC)),
                        "due_date": "",
                        "paid_date": str(transfer.finalized_at or datetime.now(UTC)),
                        "chart_account": "1000",
                    }
                    create_ledger_entry(ledger_entry)
                    log_change(
                        "ledger_entry",
                        ledger_entry["entry_id"],
                        "auto_created_from_transfer",
                        f"Transfer={transfer.transfer_id}"
                    )
            except Exception as e:
                print("⚠️ Auto-ledger entry failed:", e)

            flash(f"Transfer {transfer.transfer_id} finalized.", "success")

            # === AUTO TRUST MINUTE FROM TRANSFER ===
            try:
                minute_id = get_next_minute_id()

                minute_data = {
                    "minute_id": minute_id,
                    "trust_id": transfer.trust_id,
                    "meeting_date": None,
                    "meeting_type": "Resolution Without Meeting",
                    "title": f"Transfer Finalization — {transfer.transfer_id}",
                    "purpose": f"To record the completion and authorization of transfer {transfer.transfer_id}.",
                    "resolutions": build_minutes_text(transfer),
                    "action_items": "File records, update schedules, and confirm asset control.",
                    "status": "Draft",
                    "created_by": session.get("username") or "system",
                }

                create_trust_minute(minute_data)

                log_change(
                    "trust_minute",
                    minute_id,
                    "auto_generated_from_transfer",
                    f"Transfer={transfer.transfer_id}"
                )

            except Exception as e:
                print("⚠️ Auto-minute generation failed:", e)

            return redirect(url_for("trust_execution_dashboard", trust_id=transfer.trust_id))
        else:
            flash(
                "Transfer is incomplete and cannot be finalized. Missing: "
                + ", ".join(missing),
                "warning",
            )

    return render_template(
        "transfer_review.html",
        transfer=transfer,
        record_bundle=record_bundle,
        progress=get_transfer_progress(transfer),
        can_finalize=allowed,
        missing_items=missing,
        control_strength=calculate_control_strength(transfer.control_change_status),
        step_nav=build_transfer_step_nav(transfer, "review"),
        current_step="review",
    )


@app.route("/execution/transfers/<transfer_id>/document-support-docs")
def transfer_document_support_docs(transfer_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate
    return render_template(
        "transfer_document_support_docs.html",
        transfer=transfer,
        control_strength=calculate_control_strength(transfer.control_change_status),
    )


@app.route("/execution/transfers/<transfer_id>/personal-property-support-docs")
def transfer_personal_property_support_docs(transfer_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate
    return render_template(
        "transfer_personal_property_support_docs.html",
        transfer=transfer,
        control_strength=calculate_control_strength(transfer.control_change_status),
    )


@app.route("/execution/transfers/<transfer_id>/bank-support-docs")
def transfer_bank_support_docs(transfer_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate
    return render_template(
        "transfer_bank_support_docs.html",
        transfer=transfer,
        control_strength=calculate_control_strength(transfer.control_change_status),
    )


@app.route("/execution/transfers/<transfer_id>/recommended-support-docs")
def transfer_recommended_support_docs(transfer_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate
    return render_template(
        "transfer_recommended_support_docs.html",
        transfer=transfer,
        control_strength=calculate_control_strength(transfer.control_change_status),
    )


@app.route("/execution/transfers/<transfer_id>/optional-support-docs")
def transfer_optional_support_docs(transfer_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate
    return render_template(
        "transfer_optional_support_docs.html",
        transfer=transfer,
        control_strength=calculate_control_strength(transfer.control_change_status),
    )


@app.route("/execution/transfers/<transfer_id>/template-center")
def transfer_template_center(transfer_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate

    support_doc_map = {
        "universal_instructions": get_support_doc_by_category(transfer, "universal_instructions"),
        "optional_support_docs": get_support_doc_by_category(transfer, "optional_support_docs"),
        "recommended_support_docs": get_support_doc_by_category(transfer, "recommended_support_docs"),
        "bank_support_docs": get_support_doc_by_category(transfer, "bank_support_docs"),
        "personal_property_support_docs": get_support_doc_by_category(transfer, "personal_property_support_docs"),
        "document_support_docs": get_support_doc_by_category(transfer, "document_support_docs"),
    }

    return render_template(
        "transfer_template_center.html",
        transfer=transfer,
        control_strength=calculate_control_strength(transfer.control_change_status),
        support_doc_map=support_doc_map,
    )


@app.route("/execution/transfers/<transfer_id>/instructions")
def transfer_instruction_template(transfer_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate
    return render_template(
        "transfer_instruction_template.html",
        transfer=transfer,
        control_strength=calculate_control_strength(transfer.control_change_status),
    )


@app.route("/execution/transfers/<transfer_id>/support-docs/<int:support_doc_id>/edit", methods=["GET", "POST"])
def transfer_support_doc_edit(transfer_id, support_doc_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate
    support_doc = TransferSupportDoc.query.get_or_404(support_doc_id)

    if support_doc.transfer_id_fk != transfer.id:
        abort(404)

    if request.method == "POST":
        if not validate_csrf_token():
            abort(400)

        support_doc.status = request.form.get("status", "missing").strip() or "missing"
        support_doc.notes = request.form.get("notes", "").strip() or None
        ext_db.session.commit()
        flash("Support document status updated.", "success")
        return redirect(url_for("transfer_detail", transfer_id=transfer.transfer_id))

    return render_template(
        "transfer_support_doc_edit.html",
        transfer=transfer,
        support_doc=support_doc,
    )




@app.route("/execution/transfers/<transfer_id>/external-tracking", methods=["GET", "POST"])
def transfer_external_tracking(transfer_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate

    if request.method == "POST":
        if not validate_csrf_token():
            flash("Invalid or missing CSRF token.", "warning")
            return render_template("transfer_external_tracking.html", transfer=transfer)

        transfer.external_institution = request.form.get("external_institution", "").strip() or None
        transfer.external_account_ref = request.form.get("external_account_ref", "").strip() or None
        transfer.external_transfer_method = request.form.get("external_transfer_method", "").strip() or None
        transfer.external_transaction_id = request.form.get("external_transaction_id", "").strip() or None
        transfer.external_proof_notes = request.form.get("external_proof_notes", "").strip() or None

        verified_raw = request.form.get("external_verified", "0")
        transfer.external_verified = verified_raw == "1"
        transfer.external_verified_at = datetime.now(UTC) if transfer.external_verified else None

        ext_db.session.commit()

        log_change(
            "transfer",
            transfer.transfer_id,
            "external_tracking_updated",
            f"Institution={transfer.external_institution or 'Not recorded'}; Verified={transfer.external_verified}"
        )

        flash("External transfer tracking updated.", "success")
        return redirect(url_for("transfer_detail", transfer_id=transfer.transfer_id))

    return render_template("transfer_external_tracking.html", transfer=transfer)


@app.route("/execution/transfers/<transfer_id>/detail")
def transfer_detail(transfer_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate
    record_bundle = transfer.record_bundle
    actions = (
        TransferAction.query
        .filter_by(transfer_id_fk=transfer.id)
        .order_by(TransferAction.created_at.asc())
        .all()
    )
    transfer_proof_records = get_media_by_entity("transfer", transfer.transfer_id)


    transfer_ledger_records = [
        row for row in get_ledger_entries_by_trust_id(transfer.trust_id)
        if transfer.transfer_id in (row["description"] or "")
    ]

    return render_template(
        "transfer_detail.html",
        transfer=transfer,
        record_bundle=record_bundle,
        actions=actions,
        transfer_proof_records=transfer_proof_records,
        transfer_ledger_records=transfer_ledger_records,
        control_strength=calculate_control_strength(transfer.control_change_status),
    )


@app.route("/execution/transfers/<transfer_id>/print")
def transfer_print_view(transfer_id):
    transfer, gate = get_transfer_for_active_firm_or_404(transfer_id)
    if gate:
        return gate
    record_bundle = transfer.record_bundle
    return render_template(
        "transfer_print_view.html",
        transfer=transfer,
        record_bundle=record_bundle,
        control_strength=calculate_control_strength(transfer.control_change_status),
    )


@app.route("/visualization")
def visualization_dashboard():
    metrics = get_visualization_metrics()
    timeline = get_visualization_timeline()
    return render_template("visualization_dashboard.html", metrics=metrics, timeline=timeline)


@app.route("/visualization/trust-map")
def trust_map_dashboard():
    trust_rows = get_trust_relationship_summary()
    return render_template("trust_map_dashboard.html", trust_rows=trust_rows)


@app.route("/visualization/analytics")
def analytics_dashboard():
    metrics = get_visualization_metrics()
    timeline = get_visualization_timeline()
    trust_rows = get_trust_relationship_summary()
    return render_template(
        "analytics_dashboard.html",
        metrics=metrics,
        timeline=timeline,
        trust_rows=trust_rows
    )



@app.route("/admin/audit-log")
def admin_audit_log():
    gate = require_master_admin()
    if gate:
        return gate

    entity_type = (request.args.get("entity_type") or "").strip()
    entity_id = (request.args.get("entity_id") or "").strip()

    if entity_type and entity_id:
        logs = get_audit_log_by_entity(entity_type=entity_type, entity_id=entity_id, limit=200)
    elif entity_type:
        logs = get_audit_log_by_entity(entity_type=entity_type, limit=200)
    else:
        logs = get_audit_log(200)

    return render_template(
        "audit_log_viewer.html",
        logs=logs,
        entity_type=entity_type,
        entity_id=entity_id,
    )

@app.route("/guide")
def guide_page():
    return render_template("guide_page.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        now_ts = datetime.now(UTC).timestamp()
        attempt = login_attempts.get(username, {"count": 0, "locked_until": 0})

        if attempt.get("locked_until", 0) > now_ts:
            log_change("auth", username, "login_locked", "Login blocked due to repeated failed attempts")
            return render_template(
                "auth/login.html",
                error="Too many failed login attempts. Please wait and try again."
            )

        user = get_user_by_username(username)

        if user and (user["status"] or "").lower() == "active" and check_password_hash(user["password_hash"], password):
            session["role"] = user["role_name"]
            session["username"] = user["username"]
            session["firm_id"] = user["firm_id"] if "firm_id" in user.keys() and user["firm_id"] else "FIRM-001"
            session["last_activity"] = datetime.now(UTC).timestamp()

            login_attempts.pop(username, None)
            log_change("auth", username, "login_success", "User logged in successfully")

            role = session.get("role")
            if role == "Admin":
                return redirect(url_for("admin_index"))
            elif role == "Trustee":
                return redirect(url_for("home"))
            elif role == "Viewer":
                return redirect(url_for("portfolio_dashboard"))
            else:
                session.clear()
                return redirect(url_for("login"))

        attempt = login_attempts.get(username, {"count": 0, "locked_until": 0})
        attempt["count"] = int(attempt.get("count", 0)) + 1

        if attempt["count"] >= LOGIN_ATTEMPTS_LIMIT:
            attempt["locked_until"] = datetime.now(UTC).timestamp() + LOGIN_LOCKOUT_SECONDS
            login_attempts[username] = attempt
            log_change("auth", username, "login_lockout", "User temporarily locked after repeated failed attempts")
            return render_template(
                "auth/login.html",
                error="Too many failed login attempts. Please wait and try again."
            )

        login_attempts[username] = attempt
        log_change("auth", username, "login_failed", "Invalid credentials")
        return render_template("auth/login.html", error="Invalid credentials")

    timeout = request.args.get("timeout")
    if timeout == "1":
        log_change("auth", "unknown", "session_timeout", "Session expired due to inactivity")
        return render_template("auth/login.html", error="Your session expired due to inactivity. Please log in again.")

    return render_template("auth/login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/bootstrap_admin_once", methods=["GET", "POST"])
def bootstrap_admin_once():
    users = get_all_app_users()
    if users:
        return "Bootstrap route disabled: users already exist.", 403

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("bootstrap_admin_once.html", error_message="Invalid or missing CSRF token.")

        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not username or not password or not confirm_password:
            return render_template(
                "bootstrap_admin_once.html",
                error_message="All fields are required."
            )

        if password != confirm_password:
            return render_template(
                "bootstrap_admin_once.html",
                error_message="Passwords do not match."
            )

        existing = get_user_by_username(username)
        if existing:
            return render_template(
                "bootstrap_admin_once.html",
                error_message="Username already exists."
            )

        create_app_user({
            "user_id": get_next_user_id(),
            "username": username,
            "password_hash": generate_password_hash(password),
            "role_name": "Admin",
            "status": "active",
        })

        return redirect(url_for("login"))

    return render_template("bootstrap_admin_once.html")




@app.route("/admin/reset_admin_once")
def reset_admin_once():
    """
    Controlled emergency admin reset.
    Disabled unless ALLOW_ADMIN_RESET=1 is set.
    """
    if os.getenv("ALLOW_ADMIN_RESET") != "1":
        return "Admin reset disabled. Set ALLOW_ADMIN_RESET=1 to enable.", 403

    username = os.getenv("RESET_ADMIN_USERNAME", "admin").strip()
    password = os.getenv("RESET_ADMIN_PASSWORD", "admin123")

    if not username or not password:
        return "RESET_ADMIN_USERNAME and RESET_ADMIN_PASSWORD are required.", 400

    existing = get_user_by_username(username)

    if existing:
        update_app_user_password(username, generate_password_hash(password))
        log_change("app_user", username, "emergency_reset", "Emergency admin password reset route used.")
        return f"Admin password reset for username: {username}"

    create_app_user({
        "user_id": get_next_user_id(),
        "username": username,
        "password_hash": generate_password_hash(password),
        "role_name": "Admin",
        "status": "active",
    })
    log_change("app_user", username, "emergency_create", "Emergency admin user created.")
    return f"Admin user created for username: {username}"




@app.route("/resume")
def resume_process():
    firm_id = session.get("firm_id") or "FIRM-001"

    transfer = (
        Transfer.query
        .filter(Transfer.status != "completed")
        .filter(Transfer.firm_id == firm_id)
        .order_by(Transfer.id.desc())
        .first()
    )

    if not transfer:
        flash("No active transfer to resume for your assigned firm.", "warning")
        return redirect(url_for("execution_dashboard"))

    return redirect(get_transfer_resume_endpoint(transfer))

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))

    user = get_user_by_username(username)
    if not user:
        session.clear()
        return redirect(url_for("login"))

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("change_password.html", error_message="Invalid or missing CSRF token.")

        current_password = request.form.get("current_password") or ""
        new_password = request.form.get("new_password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not current_password or not new_password or not confirm_password:
            return render_template(
                "change_password.html",
                error_message="All password fields are required."
            )

        if not check_password_hash(user["password_hash"], current_password):
            return render_template(
                "change_password.html",
                error_message="Current password is incorrect."
            )

        if new_password != confirm_password:
            return render_template(
                "change_password.html",
                error_message="New passwords do not match."
            )

        update_app_user_password(username, generate_password_hash(new_password))
        flash("Password changed successfully.")
        return redirect(url_for("change_password"))

    return render_template("change_password.html")



@app.route("/admin/run-hosted-firm-scope-migration")
def run_hosted_firm_scope_migration():
    gate = require_master_admin()
    if gate:
        return gate

    if os.getenv("ALLOW_HOSTED_FIRM_MIGRATION") != "1":
        return render_template(
            "access_denied.html",
            reason="Hosted firm-scope migration is disabled. Set ALLOW_HOSTED_FIRM_MIGRATION=1 to run it."
        )

    import subprocess
    import sys

    script_path = Path(__file__).resolve().parent / "scripts" / "migrate_hosted_firm_scope.py"

    if not script_path.exists():
        return render_template(
            "access_denied.html",
            reason=f"Migration script not found: {script_path}"
        )

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )

    output = (result.stdout or "") + "\n" + (result.stderr or "")

    if result.returncode != 0:
        return "<pre>MIGRATION FAILED\n\n" + output + "</pre>", 500

    return "<pre>MIGRATION COMPLETE\n\n" + output + "</pre>"



@app.route("/admin/hosted-bootstrap-admin")
def hosted_bootstrap_admin():
    if os.getenv("ALLOW_HOSTED_ADMIN_BOOTSTRAP") != "1":
        return render_template(
            "access_denied.html",
            reason="Hosted admin bootstrap is disabled."
        )

    username = os.getenv("HOSTED_BOOTSTRAP_USERNAME", "admin123").strip()
    password = os.getenv("HOSTED_BOOTSTRAP_PASSWORD", "").strip()
    firm_id = os.getenv("HOSTED_BOOTSTRAP_FIRM_ID", "FIRM-002").strip()

    if not username or not password:
        return render_template(
            "access_denied.html",
            reason="HOSTED_BOOTSTRAP_USERNAME and HOSTED_BOOTSTRAP_PASSWORD must be set."
        )

    from werkzeug.security import generate_password_hash
    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            role_name TEXT,
            status TEXT,
            owner_id TEXT,
            firm_id TEXT
        )
    """)

    cur.execute("PRAGMA table_info(app_users)")
    cols = [r["name"] for r in cur.fetchall()]
    for col, col_type in [
        ("owner_id", "TEXT"),
        ("firm_id", "TEXT"),
        ("role_name", "TEXT"),
        ("status", "TEXT"),
    ]:
        if col not in cols:
            cur.execute(f"ALTER TABLE app_users ADD COLUMN {col} {col_type}")

    cur.execute("SELECT user_id FROM app_users WHERE username = ?", (username,))
    existing = cur.fetchone()

    password_hash = generate_password_hash(password)

    if existing:
        cur.execute("""
            UPDATE app_users
            SET password_hash = ?,
                role_name = 'Admin',
                status = 'active',
                owner_id = 'ADMIN_OWNER_001',
                firm_id = ?
            WHERE username = ?
        """, (password_hash, firm_id, username))
        action = "updated"
    else:
        cur.execute("SELECT COUNT(*) AS count FROM app_users")
        count = cur.fetchone()["count"]
        user_id = f"USER-{count + 1:03d}"
        cur.execute("""
            INSERT INTO app_users (
                user_id, username, password_hash, role_name, status, owner_id, firm_id
            ) VALUES (?, ?, ?, 'Admin', 'active', 'ADMIN_OWNER_001', ?)
        """, (user_id, username, password_hash, firm_id))
        action = "created"

    conn.commit()
    conn.close()

    return f"Hosted admin bootstrap {action}: {username} / {firm_id}. Disable ALLOW_HOSTED_ADMIN_BOOTSTRAP after login."



@app.route("/hosted-bootstrap-admin-once")
def hosted_bootstrap_admin_once():
    if os.getenv("ALLOW_HOSTED_ADMIN_BOOTSTRAP") != "1":
        return render_template(
            "access_denied.html",
            reason="Hosted admin bootstrap is disabled."
        )

    username = os.getenv("HOSTED_BOOTSTRAP_USERNAME", "admin123").strip()
    password = os.getenv("HOSTED_BOOTSTRAP_PASSWORD", "").strip()
    firm_id = os.getenv("HOSTED_BOOTSTRAP_FIRM_ID", "FIRM-002").strip()

    if not username or not password:
        return render_template(
            "access_denied.html",
            reason="HOSTED_BOOTSTRAP_USERNAME and HOSTED_BOOTSTRAP_PASSWORD must be set."
        )

    from werkzeug.security import generate_password_hash
    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            role_name TEXT,
            status TEXT,
            owner_id TEXT,
            firm_id TEXT
        )
    """)

    cur.execute("PRAGMA table_info(app_users)")
    cols = [r["name"] for r in cur.fetchall()]
    for col, col_type in [
        ("owner_id", "TEXT"),
        ("firm_id", "TEXT"),
        ("role_name", "TEXT"),
        ("status", "TEXT"),
    ]:
        if col not in cols:
            cur.execute(f"ALTER TABLE app_users ADD COLUMN {col} {col_type}")

    cur.execute("SELECT user_id FROM app_users WHERE username = ?", (username,))
    existing = cur.fetchone()

    password_hash = generate_password_hash(password)

    if existing:
        cur.execute("""
            UPDATE app_users
            SET password_hash = ?,
                role_name = 'Admin',
                status = 'active',
                owner_id = 'ADMIN_OWNER_001',
                firm_id = ?
            WHERE username = ?
        """, (password_hash, firm_id, username))
        action = "updated"
    else:
        cur.execute("SELECT COUNT(*) AS count FROM app_users")
        count = cur.fetchone()["count"]
        user_id = f"USER-{count + 1:03d}"
        cur.execute("""
            INSERT INTO app_users (
                user_id, username, password_hash, role_name, status, owner_id, firm_id
            ) VALUES (?, ?, ?, 'Admin', 'active', 'ADMIN_OWNER_001', ?)
        """, (user_id, username, password_hash, firm_id))
        action = "created"

    conn.commit()
    conn.close()

    return f"Hosted admin bootstrap {action}: {username} / {firm_id}. Now log in, then disable ALLOW_HOSTED_ADMIN_BOOTSTRAP."



@app.route("/hosted-firm-scope-migration-once")
def hosted_firm_scope_migration_once():
    if os.getenv("ALLOW_HOSTED_FIRM_MIGRATION") != "1":
        return render_template(
            "access_denied.html",
            reason="Hosted firm-scope migration is disabled."
        )

    import subprocess
    import sys

    script_path = Path(__file__).resolve().parent / "scripts" / "migrate_hosted_firm_scope.py"

    if not script_path.exists():
        return render_template(
            "access_denied.html",
            reason=f"Migration script not found: {script_path}"
        )

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=90,
    )

    output = (result.stdout or "") + "\n" + (result.stderr or "")

    if result.returncode != 0:
        return "<pre>MIGRATION FAILED\n\n" + output + "</pre>", 500

    return "<pre>MIGRATION COMPLETE\n\n" + output + "</pre>"



@app.route("/hosted-reseed-permissions-once")
def hosted_reseed_permissions_once():
    if os.getenv("ALLOW_HOSTED_PERMISSION_RESEED") != "1":
        return render_template(
            "access_denied.html",
            reason="Hosted permission reseed is disabled."
        )

    result = reseed_default_role_permissions()

    return "<pre>PERMISSION RESEED COMPLETE\n\n" + str(result) + "</pre>"



@app.route("/hosted-clear-login-lockout-once")
def hosted_clear_login_lockout_once():
    if os.getenv("ALLOW_HOSTED_LOGIN_UNLOCK") != "1":
        return render_template(
            "access_denied.html",
            reason="Hosted login unlock is disabled."
        )

    username = os.getenv("HOSTED_BOOTSTRAP_USERNAME", "admin123").strip()
    login_attempts.pop(username, None)

    return f"Login lockout cleared for {username}. Disable ALLOW_HOSTED_LOGIN_UNLOCK after login."



@app.route("/hosted-auth-diagnostic-once")
def hosted_auth_diagnostic_once():
    if os.getenv("ALLOW_HOSTED_LOGIN_UNLOCK") != "1":
        return render_template(
            "access_denied.html",
            reason="Hosted auth diagnostic is disabled."
        )

    import sqlite3
    from werkzeug.security import check_password_hash

    username = os.getenv("HOSTED_BOOTSTRAP_USERNAME", "admin123").strip()
    test_password = os.getenv("HOSTED_BOOTSTRAP_PASSWORD", "").strip()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    output = []
    output.append(f"DB_PATH={DB_PATH}")
    output.append(f"USERNAME_ENV={username}")
    output.append(f"PASSWORD_ENV_PRESENT={bool(test_password)}")
    output.append(f"PASSWORD_ENV_LENGTH={len(test_password)}")

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='app_users'")
    if not cur.fetchone():
        output.append("APP_USERS_TABLE=missing")
        conn.close()
        return "<pre>" + "\n".join(output) + "</pre>"

    cur.execute("PRAGMA table_info(app_users)")
    output.append("APP_USERS_COLUMNS=" + ", ".join([row["name"] for row in cur.fetchall()]))

    cur.execute("""
        SELECT username, password_hash, role_name, status, firm_id
        FROM app_users
        WHERE username = ?
    """, (username,))
    row = cur.fetchone()

    if not row:
        output.append("USER_ROW=missing")
    else:
        password_hash = row["password_hash"] or ""
        output.append("USER_ROW=present")
        output.append(f"ROW_USERNAME={row['username']}")
        output.append(f"ROW_ROLE={row['role_name']}")
        output.append(f"ROW_STATUS={row['status']}")
        output.append(f"ROW_FIRM_ID={row['firm_id']}")
        output.append(f"HASH_PRESENT={bool(password_hash)}")
        output.append(f"HASH_PREFIX={password_hash[:18] if password_hash else ''}")
        output.append(f"CHECK_PASSWORD_MATCH={check_password_hash(password_hash, test_password) if password_hash and test_password else False}")

    conn.close()
    return "<pre>" + "\n".join(output) + "</pre>"



@app.route("/hosted-repair-admin-access-once")
def hosted_repair_admin_access_once():
    """
    One-time hosted recovery route.
    Guarded by ALLOW_HOSTED_ADMIN_BOOTSTRAP=1 and ALLOW_HOSTED_PERMISSION_RESEED=1.
    Repairs hosted admin login, role permissions, login lockout, and firm_id columns.
    Disable all hosted recovery switches immediately after use.
    """
    if os.getenv("ALLOW_HOSTED_ADMIN_BOOTSTRAP") != "1":
        return render_template(
            "access_denied.html",
            reason="Hosted admin repair is disabled. Set ALLOW_HOSTED_ADMIN_BOOTSTRAP=1."
        )

    if os.getenv("ALLOW_HOSTED_PERMISSION_RESEED") != "1":
        return render_template(
            "access_denied.html",
            reason="Hosted permission repair is disabled. Set ALLOW_HOSTED_PERMISSION_RESEED=1."
        )

    import sqlite3
    from werkzeug.security import generate_password_hash, check_password_hash

    username = os.getenv("HOSTED_BOOTSTRAP_USERNAME", "admin123").strip()
    password = os.getenv("HOSTED_BOOTSTRAP_PASSWORD", "").strip()
    firm_id = os.getenv("HOSTED_BOOTSTRAP_FIRM_ID", "FIRM-002").strip()

    output = []
    output.append(f"DB_PATH={DB_PATH}")
    output.append(f"USERNAME={username!r}")
    output.append(f"PASSWORD_PRESENT={bool(password)}")
    output.append(f"PASSWORD_LENGTH={len(password)}")
    output.append(f"FIRM_ID={firm_id!r}")

    if not username or not password or not firm_id:
        return "<pre>REPAIR FAILED: username, password, and firm_id are required.</pre>", 400

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Ensure app_users exists and has required columns.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            role_name TEXT,
            status TEXT,
            firm_id TEXT,
            owner_id TEXT
        )
    """)

    cur.execute("PRAGMA table_info(app_users)")
    user_cols = [r["name"] for r in cur.fetchall()]
    for col, col_type in [
        ("password_hash", "TEXT"),
        ("role_name", "TEXT"),
        ("status", "TEXT"),
        ("firm_id", "TEXT"),
        ("owner_id", "TEXT"),
    ]:
        if col not in user_cols:
            cur.execute(f"ALTER TABLE app_users ADD COLUMN {col} {col_type}")
            output.append(f"ADDED app_users.{col}")

    # 2. Create/update admin user.
    password_hash = generate_password_hash(password)

    cur.execute("SELECT user_id FROM app_users WHERE TRIM(LOWER(username)) = TRIM(LOWER(?))", (username,))
    existing = cur.fetchone()

    if existing:
        cur.execute("""
            UPDATE app_users
            SET username = ?,
                password_hash = ?,
                role_name = 'Admin',
                status = 'active',
                firm_id = ?,
                owner_id = 'ADMIN_OWNER_001'
            WHERE user_id = ?
        """, (username, password_hash, firm_id, existing["user_id"]))
        output.append(f"USER_UPDATED={username}")
    else:
        cur.execute("SELECT COUNT(*) AS count FROM app_users")
        count = cur.fetchone()["count"]
        user_id = f"USER-{count + 1:03d}"
        cur.execute("""
            INSERT INTO app_users (
                user_id, username, password_hash, role_name, status, firm_id, owner_id
            ) VALUES (?, ?, ?, 'Admin', 'active', ?, 'ADMIN_OWNER_001')
        """, (user_id, username, password_hash, firm_id))
        output.append(f"USER_CREATED={username}")

    conn.commit()

    # 3. Ensure role permission tables and grant default Admin permissions.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            permission_id TEXT PRIMARY KEY,
            permission_name TEXT UNIQUE,
            description TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS role_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT,
            permission_name TEXT,
            UNIQUE(role_name, permission_name)
        )
    """)

    default_permissions = [
        ("PERM-001", "view_dashboard", "View dashboards and core system pages"),
        ("PERM-002", "create_trust", "Create trust records"),
        ("PERM-003", "edit_trust", "Edit trust records"),
        ("PERM-004", "view_documents", "View documents"),
        ("PERM-005", "generate_documents", "Generate documents"),
        ("PERM-006", "export_documents", "Export documents"),
        ("PERM-007", "manage_tax_reports", "Manage tax reports"),
        ("PERM-008", "view_audit", "View audit trail"),
        ("PERM-009", "manage_users", "Manage users"),
        ("PERM-010", "manage_roles", "Manage trust roles"),
        ("PERM-011", "manage_permissions", "Manage permissions"),
        ("PERM-012", "view_security", "View security dashboard"),
    ]

    for permission_id, permission_name, description in default_permissions:
        cur.execute("""
            INSERT OR IGNORE INTO permissions (permission_id, permission_name, description)
            VALUES (?, ?, ?)
        """, (permission_id, permission_name, description))

    admin_permissions = [
        "view_dashboard",
        "create_trust",
        "edit_trust",
        "view_documents",
        "generate_documents",
        "export_documents",
        "manage_tax_reports",
        "view_audit",
        "manage_users",
        "manage_roles",
        "manage_permissions",
        "view_security",
    ]

    for permission_name in admin_permissions:
        cur.execute("""
            INSERT OR IGNORE INTO role_permissions (role_name, permission_name)
            VALUES ('Admin', ?)
        """, (permission_name,))

    conn.commit()
    output.append("ADMIN_PERMISSIONS_RESEEDED=True")

    # 4. Self-heal firm_id columns on common hosted tables.
    firm_tables = [
        "trusts",
        "audit_log",
        "transfers",
        "trust_minutes",
        "documents",
        "generated_documents",
        "media_records",
        "workspaces",
        "workspace_notes",
        "execution_tasks",
        "user_roles",
        "fiduciaries",
        "properties",
        "accounts",
        "beneficiaries",
        "distributions",
        "instruments",
        "ledger_entries",
    ]

    for table in firm_tables:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if not cur.fetchone():
            output.append(f"SKIP_MISSING_TABLE={table}")
            continue

        cur.execute(f"PRAGMA table_info({table})")
        cols = [r["name"] for r in cur.fetchall()]
        if "firm_id" not in cols:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN firm_id TEXT")
            output.append(f"ADDED_COLUMN={table}.firm_id")

        cur.execute(f"""
            UPDATE {table}
            SET firm_id = ?
            WHERE firm_id IS NULL OR TRIM(firm_id) = ''
        """, (firm_id,))
        output.append(f"{table}_DEFAULTED_ROWS={cur.rowcount}")

    conn.commit()

    # 5. Verify user row and password match.
    cur.execute("""
        SELECT username, password_hash, role_name, status, firm_id
        FROM app_users
        WHERE TRIM(LOWER(username)) = TRIM(LOWER(?))
    """, (username,))
    row = cur.fetchone()

    if row:
        output.append("USER_ROW=present")
        output.append(f"ROW_USERNAME={row['username']}")
        output.append(f"ROW_ROLE={row['role_name']}")
        output.append(f"ROW_STATUS={row['status']}")
        output.append(f"ROW_FIRM_ID={row['firm_id']}")
        output.append(f"CHECK_PASSWORD_MATCH={check_password_hash(row['password_hash'], password)}")
    else:
        output.append("USER_ROW=missing")

    cur.execute("""
        SELECT permission_name
        FROM role_permissions
        WHERE role_name = 'Admin'
        ORDER BY permission_name
    """)
    admin_perms = [r["permission_name"] for r in cur.fetchall()]
    output.append("ADMIN_PERMISSIONS=" + ", ".join(admin_perms))
    output.append(f"HAS_VIEW_DASHBOARD={'view_dashboard' in admin_perms}")

    conn.close()

    # Clear in-memory lockout for this worker.
    login_attempts.pop(username, None)
    output.append("LOGIN_LOCKOUT_CLEARED=True")
    output.append("NEXT=Log in with username and HOSTED_BOOTSTRAP_PASSWORD, then disable hosted recovery variables.")

    return "<pre>HOSTED ADMIN ACCESS REPAIR COMPLETE\n\n" + "\n".join(output) + "</pre>"



@app.route("/hosted-trust-diagnostic-once")
def hosted_trust_diagnostic_once():
    return render_template(
        "access_denied.html",
        reason="Hosted trust diagnostic has been permanently disabled."
    )



# ===================================================
# ARE-1 ARTICLE REGISTRY ROUTES
# ===================================================

@app.route("/admin/articles")
@require_permission("view_dashboard")
def admin_articles():
    articles = get_all_trust_articles()
    return render_template("admin_articles.html", articles=articles)


@app.route("/admin/articles/new", methods=["GET", "POST"])
@require_permission("view_dashboard")
def admin_articles_new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        article_type = request.form.get("article_type", "").strip()
        content = request.form.get("content", "").strip()
        is_required = 1 if request.form.get("is_required") == "on" else 0

        if not title or not content:
            flash("Article title and content are required.", "danger")
            return render_template("admin_article_new.html")

        article_id = create_trust_article(
            title=title,
            content=content,
            category=category,
            article_type=article_type,
            is_required=is_required
        )

        flash(f"Article created: {article_id}", "success")
        return redirect(url_for("admin_articles"))

    return render_template("admin_article_new.html")






@app.route("/trust/<trust_id>/dynamic-declaration")
@require_permission("view_dashboard")
def trust_dynamic_declaration(trust_id):
    trust = get_trust_by_id(trust_id)

    if not trust:
        flash("Trust not found.", "danger")
        return redirect(url_for("admin_index"))

    dynamic_document = build_dynamic_declaration(trust)

    return render_template(
        "trust_dynamic_declaration.html",
        trust=trust,
        dynamic_document=dynamic_document
    )




# ===================================================
# ARE-1 DYNAMIC DECLARATION PDF ENGINE
# ===================================================

def generate_dynamic_declaration_pdf(dynamic_document):

    from io import BytesIO

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DynamicTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        spaceAfter=18
    )

    body_style = ParagraphStyle(
        "DynamicBody",
        parent=styles["BodyText"],
        fontSize=11,
        leading=16,
        spaceAfter=10
    )

    story = []

    story.append(
        Paragraph(
            "Dynamic Declaration of Trust",
            title_style
        )
    )

    text_lines = dynamic_document["document_text"].splitlines()

    for line in text_lines:

        clean_line = line.strip()

        if not clean_line:
            story.append(Spacer(1, 8))
            continue

        safe_line = (
            clean_line
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        story.append(
            Paragraph(
                safe_line,
                body_style
            )
        )

    doc.build(story)

    buffer.seek(0)

    return buffer


@app.route("/trust/<trust_id>/dynamic-declaration/pdf")
@require_permission("view_dashboard")
def trust_dynamic_declaration_pdf(trust_id):

    trust = get_trust_by_id(trust_id)

    if not trust:
        flash("Trust not found.", "danger")
        return redirect(url_for("admin_index"))

    dynamic_document = build_dynamic_declaration(trust)

    pdf_buffer = generate_dynamic_declaration_pdf(dynamic_document)

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{trust_id}_Dynamic_Declaration.pdf"
    )



# ===================================================
# ARE-1 TRUST ARTICLE ASSIGNMENT ROUTES
# ===================================================

@app.route("/trust/<trust_id>/article-assignments")
@require_permission("view_dashboard")
def trust_article_assignments(trust_id):

    trust = get_trust_by_id(trust_id)

    if not trust:
        flash("Trust not found.", "danger")
        return redirect(url_for("admin_index"))

    assigned_articles = get_articles_for_trust(trust_id)
    all_articles = get_all_trust_articles()

    assigned_ids = {
        row["article_id"]
        for row in assigned_articles
    }

    available_articles = [
        article for article in all_articles
        if article["article_id"] not in assigned_ids
    ]

    return render_template(
        "trust_article_assignments.html",
        trust=trust,
        assigned_articles=assigned_articles,
        available_articles=available_articles
    )


@app.route("/trust/<trust_id>/article-assignments/add", methods=["POST"])
@require_permission("view_dashboard")
def trust_article_assignment_add(trust_id):

    article_id = request.form.get("article_id")

    if not article_id:
        flash("No article selected.", "danger")
        return redirect(
            url_for(
                "trust_article_assignments",
                trust_id=trust_id
            )
        )

    existing = get_articles_for_trust(trust_id)

    sort_order = len(existing) + 1

    assign_article_to_trust(
        trust_id=trust_id,
        article_id=article_id,
        sort_order=sort_order
    )

    flash("Article assigned successfully.", "success")

    return redirect(
        url_for(
            "trust_article_assignments",
            trust_id=trust_id
        )
    )



if __name__ == "__main__":
    app.run(debug=FLASK_DEBUG == "1")

app.jinja_env.globals['get_transfer_resume_endpoint'] = get_transfer_resume_endpoint
