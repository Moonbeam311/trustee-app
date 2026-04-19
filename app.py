import os
import secrets
from flask import session, Flask, request, render_template, redirect, url_for, make_response, flash
from database.db import (
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
)
from pathlib import Path
from extensions import db as ext_db

# --- Transfer Engine v1 imports ---
from models.models_transfer import Transfer, TransferAction, TransferRecord
from models.models_transfer_support import TransferSupportDoc
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
from datetime import datetime
from werkzeug.utils import secure_filename
from pdf_utils import build_pdf_response, trust_summary_story, k1_readiness_story, fiduciary_report_story, ledger_report_story, form1041_report_story, instrument_detail_story, portfolio_report_story, audit_log_report_story
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import UTC, date, datetime, timedelta
from io import BytesIO

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{(Path(__file__).resolve().parent / 'trustee_app.db').as_posix()}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
ext_db.init_app(app)

SESSION_TIMEOUT_SECONDS = 900  # 15 minutes
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(seconds=SESSION_TIMEOUT_SECONDS)

APP_ENV = os.getenv("APP_ENV", "development").lower()
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "1")
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_TO_RANDOM_SECRET_KEY")

app.secret_key = SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = APP_ENV == "production"


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

def validate_csrf_token():
    session_token = session.get("_csrf_token")
    form_token = request.form.get("_csrf_token")
    return bool(session_token and form_token and session_token == form_token)


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
    created_at_value = trust.created_at
    if created_at_value:
        try:
            created_at_display = created_at_value.strftime("%Y-%m-%d %H:%M")
        except Exception:
            created_at_display = str(created_at_value)
    else:
        created_at_display = ""

    return {
        "trust_id": trust.trust_id or "",
        "trust_name": trust.trust_name or "",
        "trust_type": trust.trust_type or "",
        "grantor_name": trust.grantor_name or "",
        "owner_id": trust.owner_id or "",
        "status": trust.status or "",
        "created_at_display": created_at_display,
    }


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

init_audit_table()

init_db()
ensure_k1_tables()
ensure_instrument_tables()
ensure_fiduciary_tables()
ensure_genealogy_tables()
ensure_media_tables()
ensure_role_tables()
ensure_user_tables()

with app.app_context():
    ext_db.create_all()

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "jpg", "jpeg", "png", "mp3", "wav", "mp4", "mov"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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

@app.route("/create_trust_step1", methods=["GET", "POST"])
def create_trust_step1():
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("create_trust_step1.html", error_message="Invalid or missing CSRF token.")

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
def create_trust_step6(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("create_trust_step6.html", trust=trust, error_message="Invalid or missing CSRF token.")

        update_trust_fields(trust_id, {"status": "Finalized"})
        return redirect(url_for("create_trust_step7", trust_id=trust_id))
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
    return render_template("upload_document.html", trusts=trusts)

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

@app.route("/trust/<trust_id>")
def trust_detail(trust_id):
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

    if prop.get("owner_id") != get_current_owner():
        return render_template(
            "access_denied.html",
            reason="This property record does not belong to the current owner context."
        )

    linked_trust = get_trust_by_id(prop["trust_id"])
    linked_accounts = get_accounts_by_property_id(property_id)
    linked_documents = get_documents_by_property_id(property_id)
    linked_ledger = get_ledger_by_property(property_id)

    return render_template(
        "property_detail.html",
        prop=prop,
        linked_trust=linked_trust,
        linked_accounts=linked_accounts,
        linked_documents=linked_documents,
        linked_ledger=linked_ledger
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


@app.route("/admin")
def admin_index():
    trusts = get_all_trusts()
    report = {
        "trust_count": get_trust_count(),
        "beneficiary_count": get_beneficiary_count(),
        "distribution_count": get_distribution_count(),
        "instrument_count": get_instrument_count(),
    }
    return render_template("admin_index.html", trusts=trusts, report=report)


@app.route("/users")
def users_dashboard():
    users = get_all_app_users()
    return render_template("user_dashboard.html", users=users)


@app.route("/users/new", methods=["GET", "POST"])
def users_new():
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("user_form.html", error_message="Invalid or missing CSRF token.")

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
        flash(f"User {username} created successfully.")
        return redirect(url_for("users_dashboard"))

    return render_template("user_form.html")


@app.route("/users/<username>/edit", methods=["GET", "POST"])
def users_edit(username):
    user = get_user_by_username(username)
    if not user:
        return f"User {username} not found", 404

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("user_edit.html", user=user, error_message="Invalid or missing CSRF token.")

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
        flash(f"User {username} updated successfully.")
        return redirect(url_for("users_dashboard"))

    return render_template("user_edit.html", user=user)


@app.route("/users/<username>/reset_password", methods=["GET", "POST"])
def users_reset_password(username):
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
        flash(f"Password reset successfully for {username}.")
        return redirect(url_for("users_dashboard"))

    return render_template("user_reset_password.html", user=user)


@app.route("/exports")
def export_center():
    trusts = get_all_trusts()
    return render_template("export_center.html", trusts=trusts)


@app.route("/exports/handoff/<filename>")
def export_handoff_file(filename):
    from flask import session, send_from_directory
    return send_from_directory("handoff", filename, as_attachment=True)


@app.route("/exports/roadmap/<filename>")
def export_roadmap_file(filename):
    from flask import session, send_from_directory
    return send_from_directory("roadmap", filename, as_attachment=True)


@app.route("/exports/package/<filename>")
def export_package_file(filename):
    from flask import session, send_from_directory
    return send_from_directory("package_export", filename, as_attachment=True)


@app.route("/exports/zip")
def export_zip_snapshot():
    from flask import session, send_file
    return send_file("Trustee_App_Export_Package.zip", as_attachment=True)


@app.route("/exports/k1/<trust_id>.csv")
def export_k1_live_csv(trust_id):
    tax_year = request.args.get("tax_year", str(date.today().year))
    csv_text = export_k1_csv_text(trust_id, tax_year)
    response = make_response(csv_text)
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = f"attachment; filename=trust_{trust_id}_k1_{tax_year}.csv"
    log_change("k1_export", trust_id, "export", f"K-1 CSV export generated for tax year {tax_year}")
    return response


@app.route("/exports/1041/<trust_id>.txt")
def export_1041_text(trust_id):
    tax_year = request.args.get("tax_year", str(date.today().year))
    dataset = get_1041_dataset(trust_id, tax_year)

    lines = []
    lines.append("TRUSTEE APP — FORM 1041 EXPORT")
    lines.append("=" * 40)
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



@app.route("/audit")
def audit_dashboard():
    entity_type = request.args.get("entity_type")
    entity_id = request.args.get("entity_id")

    if entity_type or entity_id:
        logs = get_audit_log_by_entity(entity_type=entity_type, entity_id=entity_id, limit=200)
    else:
        logs = get_audit_log(200)

    return render_template(
        "audit_dashboard.html",
        logs=logs,
        entity_type=entity_type,
        entity_id=entity_id
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
    tax_year = request.args.get("tax_year", str(date.today().year))
    csv_text = export_k1_csv_text(trust_id, tax_year)
    response = make_response(csv_text)
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = f"attachment; filename=trust_{trust_id}_k1_{tax_year}.csv"
    log_change("k1_export", trust_id, "export", f"K-1 CSV export generated for tax year {tax_year}")
    return response


@app.route("/exports/k1_summary/<trust_id>.txt")
def export_k1_summary_report(trust_id):
    tax_year = request.args.get("tax_year", str(date.today().year))
    trust = get_trust_by_id(trust_id)
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
    tax_year = request.args.get("tax_year", str(date.today().year))
    trust = get_trust_by_id(trust_id)
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
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM generated_documents
        WHERE owner_id = ?
        ORDER BY created_at DESC, title
    """, (get_current_owner(),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_generated_documents_by_workspace(workspace_id):
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM generated_documents
        WHERE workspace_id = ?
          AND owner_id = ?
        ORDER BY created_at DESC, title
    """, (workspace_id, get_current_owner())).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_generated_document_by_id(document_id):
    conn = _learning_conn()
    row = conn.execute("""
        SELECT * FROM generated_documents
        WHERE document_id = ?
    """, (document_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_generated_document(payload):
    conn = _learning_conn()
    conn.execute("""
        INSERT INTO generated_documents (
            document_id, workspace_id, trust_id, template_id, title, content, status, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        payload.get("document_id"),
        payload.get("workspace_id"),
        payload.get("trust_id"),
        payload.get("template_id"),
        payload.get("title"),
        payload.get("content"),
        payload.get("status"),
        payload.get("created_by"),
    ))
    conn.commit()
    conn.close()

def render_document_template(template_body, values):
    content = template_body or ""
    for key, value in (values or {}).items():
        content = content.replace("{{" + key + "}}", value or "")
    return content

def get_all_execution_tasks():
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM execution_tasks
        WHERE owner_id = ?
        ORDER BY
            CASE priority
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                ELSE 3
            END,
            created_at DESC
    """, (get_current_owner(),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_execution_tasks_by_workspace(workspace_id):
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM execution_tasks
        WHERE workspace_id = ?
        ORDER BY
            CASE priority
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                ELSE 3
            END,
            created_at DESC
    """, (workspace_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_execution_task_by_id(task_id):
    conn = _learning_conn()
    row = conn.execute("""
        SELECT * FROM execution_tasks
        WHERE task_id = ?
    """, (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_execution_task(payload):
    conn = _learning_conn()
    conn.execute("""
        INSERT INTO execution_tasks (
            task_id, workspace_id, trust_id, title, task_type, description,
            related_form, related_report, priority, status, due_date, assigned_to
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        payload.get("assigned_to"),
    ))
    conn.commit()
    conn.close()

def update_execution_task_status(task_id, status):
    conn = _learning_conn()
    conn.execute("""
        UPDATE execution_tasks
        SET status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE task_id = ?
    """, (status, task_id))
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
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM workspaces
        ORDER BY created_at DESC, title
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_workspace_by_id(workspace_id):
    conn = _learning_conn()
    row = conn.execute("""
        SELECT * FROM workspaces
        WHERE workspace_id = ?
    """, (workspace_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_workspace(payload):
    conn = _learning_conn()
    conn.execute("""
        INSERT INTO workspaces (
            workspace_id, title, workspace_type, trust_type_focus, purpose, owner, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        payload.get("workspace_id"),
        payload.get("title"),
        payload.get("workspace_type"),
        payload.get("trust_type_focus"),
        payload.get("purpose"),
        payload.get("owner"),
        payload.get("status"),
    ))
    conn.commit()
    conn.close()

def update_workspace(workspace_id, payload):
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
    """, (
        payload.get("title"),
        payload.get("workspace_type"),
        payload.get("trust_type_focus"),
        payload.get("purpose"),
        payload.get("owner"),
        payload.get("status"),
        workspace_id,
    ))
    conn.commit()
    conn.close()

def get_workspace_notes(workspace_id):
    conn = _learning_conn()
    rows = conn.execute("""
        SELECT * FROM workspace_notes
        WHERE workspace_id = ?
        ORDER BY section_name, created_at
    """, (workspace_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_workspace_note(payload):
    conn = _learning_conn()
    conn.execute("""
        INSERT INTO workspace_notes (
            note_id, workspace_id, section_name, content
        ) VALUES (?, ?, ?, ?)
    """, (
        payload.get("note_id"),
        payload.get("workspace_id"),
        payload.get("section_name"),
        payload.get("content"),
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
LEARNING_DB_PATH = r"trustee_app.db"


@app.route("/media")
def media_dashboard():

    records = get_all_media()
    return render_template("media_dashboard.html", records=records)


@app.route("/media/upload", methods=["GET", "POST"])
def media_upload():
    trusts = get_all_trusts()

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("media_form.html", trusts=trusts, error_message="Invalid or missing CSRF token.")

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

    return render_template("media_form.html", trusts=trusts)




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

    if trust.get("owner_id") != get_current_owner():
        return render_template(
            "access_denied.html",
            reason="This trust report does not belong to the current owner context."
        )

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

    if trust.get("owner_id") != get_current_owner():
        return render_template(
            "access_denied.html",
            reason="This trust report does not belong to the current owner context."
        )

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

    roles = get_all_roles()
    trusts = get_all_trusts()
    return render_template("role_dashboard.html", roles=roles, trusts=trusts)


@app.route("/roles/new", methods=["GET", "POST"])
def role_new():
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
        log_change("role", role_id, "create", "User role created")
        flash(f"Role assignment {role_id} created successfully.")
        return redirect(url_for("role_dashboard"))

    return render_template("role_form.html", trusts=trusts)




@app.route("/reports/k1/<trust_id>/print")
def k1_report_print(trust_id):
    tax_year = request.args.get("tax_year", str(date.today().year))
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found", 404

    if trust.get("owner_id") != get_current_owner():
        return render_template(
            "access_denied.html",
            reason="This trust report does not belong to the current owner context."
        )

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

    if trust.get("owner_id") != get_current_owner():
        return render_template(
            "access_denied.html",
            reason="This trust report does not belong to the current owner context."
        )

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




@app.route("/permissions")
def permissions_dashboard():

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

    return render_template("permissions_dashboard.html", rows=rows)




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
    return render_template("security_dashboard.html", checklist=checklist)






@app.before_request
def enforce_session_timeout():
    allowed_routes = {"login", "logout", "static", "bootstrap_admin_once"}
    if request.endpoint in allowed_routes or request.endpoint is None:
        return

    if "role" not in session:
        return redirect(url_for("login"))

    allowed_roles = ROLE_RULES.get(request.endpoint)
    if allowed_roles and session.get("role") not in allowed_roles:
        return render_template(
            "access_denied.html",
            reason=f"Role {session.get('role')} is not allowed for this page."
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

    if trust.get("owner_id") != get_current_owner():
        return render_template(
            "access_denied.html",
            reason="This trust report does not belong to the current owner context."
        )

    properties = get_properties_by_trust_id(trust_id)
    accounts = get_accounts_by_trust_id(trust_id)
    documents = get_documents_by_trust_id(trust_id)
    entries = get_ledger_entries_by_trust_id(trust_id)

    story = trust_summary_story(trust, properties, accounts, documents, entries)
    return build_pdf_response(f"trust_summary_{trust_id}.pdf", story)


@app.route("/reports/k1/trust/<trust_id>/<tax_year>.pdf")
def k1_readiness_pdf(trust_id, tax_year):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found", 404

    if trust.get("owner_id") != get_current_owner():
        return render_template(
            "access_denied.html",
            reason="This trust report does not belong to the current owner context."
        )

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

    if trust.get("owner_id") != get_current_owner():
        return render_template(
            "access_denied.html",
            reason="This trust report does not belong to the current owner context."
        )

    entries = get_ledger_entries_by_trust_id(trust_id)
    story = ledger_report_story(trust=trust, entries=entries)
    return build_pdf_response(f"ledger_report_{trust_id}.pdf", story)

@app.route("/reports/1041/trust/<trust_id>/<tax_year>.pdf")
def form1041_report_pdf(trust_id, tax_year):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found", 404

    if trust.get("owner_id") != get_current_owner():
        return render_template(
            "access_denied.html",
            reason="This trust report does not belong to the current owner context."
        )

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
        return f"Workspace {workspace_id} not found", 404

    if workspace.get("owner_id") != get_current_owner():
        return render_template(
            "access_denied.html",
            reason="This workspace does not belong to the current owner context."
        )

    notes = get_workspace_notes(workspace_id)
    return render_template("workspace_detail.html", workspace=workspace, notes=notes)


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

@app.route("/trust/<trust_id>/formation-preview-hub")
def trust_formation_preview_hub(trust_id):
    trust = Trust.query.filter_by(trust_id=trust_id).first_or_404()
    return render_template(
        "trust_formation_preview_hub.html",
        trust=trust,
    )


@app.route("/trust/<trust_id>/successor-trustee-preview")
def trust_successor_trustee_preview(trust_id):
    trust = Trust.query.filter_by(trust_id=trust_id).first_or_404()
    return render_template(
        "trust_successor_trustee_preview.html",
        trust=trust,
    )


@app.route("/trust/<trust_id>/general-assignment-preview")
def trust_general_assignment_preview(trust_id):
    trust = Trust.query.filter_by(trust_id=trust_id).first_or_404()
    return render_template(
        "trust_general_assignment_preview.html",
        trust=trust,
    )


@app.route("/trust/<trust_id>/organizational-minutes-preview")
def trust_organizational_minutes_preview(trust_id):
    trust = Trust.query.filter_by(trust_id=trust_id).first_or_404()
    return render_template(
        "trust_organizational_minutes_preview.html",
        trust=trust,
    )


@app.route("/trust/<trust_id>/trustee-acceptance-preview")
def trust_trustee_acceptance_preview(trust_id):
    trust = Trust.query.filter_by(trust_id=trust_id).first_or_404()
    return render_template(
        "trust_trustee_acceptance_preview.html",
        trust=trust,
    )


@app.route("/trust/<trust_id>/articles-preview")
def trust_articles_preview(trust_id):
    trust = Trust.query.filter_by(trust_id=trust_id).first_or_404()
    preview_context = build_trust_preview_context(trust)
    return render_template(
        "trust_articles_preview.html",
        trust=trust,
        preview_context=preview_context,
    )


@app.route("/trust/<trust_id>/execution")
def trust_execution_dashboard(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found", 404

    transfers = (
        Transfer.query
        .filter_by(trust_id=str(trust_id))
        .order_by(Transfer.updated_at.desc())
        .all()
    )

    return render_template(
        "transfer_execution_dashboard.html",
        trust_id=trust_id,
        transfers=transfers,
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
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()

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
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()

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
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()

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
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()

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

        transfer.current_capacity = request.form.get("current_capacity", transfer.current_capacity)

        if not validate_capacity_for_step("trustee_acceptance", transfer.current_capacity):
            flash("Trustee acceptance requires trustee capacity.", "warning")
        else:
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
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()

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
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()

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
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()
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

        success, missing = finalize_transfer(
            transfer=transfer,
            performed_by=session.get("username") or "unknown",
            capacity_used=transfer.current_capacity,
            commit=False,
        )

        if success:
            mark_core_support_docs_included(transfer)
            ext_db.session.commit()
            flash(f"Transfer {transfer.transfer_id} finalized.", "success")
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
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()
    return render_template(
        "transfer_document_support_docs.html",
        transfer=transfer,
        control_strength=calculate_control_strength(transfer.control_change_status),
    )


@app.route("/execution/transfers/<transfer_id>/personal-property-support-docs")
def transfer_personal_property_support_docs(transfer_id):
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()
    return render_template(
        "transfer_personal_property_support_docs.html",
        transfer=transfer,
        control_strength=calculate_control_strength(transfer.control_change_status),
    )


@app.route("/execution/transfers/<transfer_id>/bank-support-docs")
def transfer_bank_support_docs(transfer_id):
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()
    return render_template(
        "transfer_bank_support_docs.html",
        transfer=transfer,
        control_strength=calculate_control_strength(transfer.control_change_status),
    )


@app.route("/execution/transfers/<transfer_id>/recommended-support-docs")
def transfer_recommended_support_docs(transfer_id):
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()
    return render_template(
        "transfer_recommended_support_docs.html",
        transfer=transfer,
        control_strength=calculate_control_strength(transfer.control_change_status),
    )


@app.route("/execution/transfers/<transfer_id>/optional-support-docs")
def transfer_optional_support_docs(transfer_id):
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()
    return render_template(
        "transfer_optional_support_docs.html",
        transfer=transfer,
        control_strength=calculate_control_strength(transfer.control_change_status),
    )


@app.route("/execution/transfers/<transfer_id>/template-center")
def transfer_template_center(transfer_id):
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()

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
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()
    return render_template(
        "transfer_instruction_template.html",
        transfer=transfer,
        control_strength=calculate_control_strength(transfer.control_change_status),
    )


@app.route("/execution/transfers/<transfer_id>/support-docs/<int:support_doc_id>/edit", methods=["GET", "POST"])
def transfer_support_doc_edit(transfer_id, support_doc_id):
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()
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


@app.route("/execution/transfers/<transfer_id>/detail")
def transfer_detail(transfer_id):
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()
    record_bundle = transfer.record_bundle
    actions = (
        TransferAction.query
        .filter_by(transfer_id_fk=transfer.id)
        .order_by(TransferAction.created_at.asc())
        .all()
    )
    return render_template(
        "transfer_detail.html",
        transfer=transfer,
        record_bundle=record_bundle,
        actions=actions,
        control_strength=calculate_control_strength(transfer.control_change_status),
    )


@app.route("/execution/transfers/<transfer_id>/print")
def transfer_print_view(transfer_id):
    transfer = Transfer.query.filter_by(transfer_id=transfer_id).first_or_404()
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

@app.route("/guide")
def guide_page():
    return render_template("guide_page.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("auth/login.html", error="Invalid or missing CSRF token.")

        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        user = get_user_by_username(username)

        if user and (user["status"] or "").lower() == "active" and check_password_hash(user["password_hash"], password):
            session["role"] = user["role_name"]
            session["username"] = user["username"]
            session["last_activity"] = datetime.now(UTC).timestamp()

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

        return render_template("auth/login.html", error="Invalid credentials")

    timeout = request.args.get("timeout")
    if timeout == "1":
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


if __name__ == "__main__":
    app.run(debug=FLASK_DEBUG == "1")
