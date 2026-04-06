from flask import Flask, request, render_template, redirect, url_for, make_response
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
)
from pathlib import Path
from werkzeug.utils import secure_filename
from datetime import date
from io import BytesIO

app = Flask(__name__)

init_audit_table()

init_db()
ensure_k1_tables()
ensure_instrument_tables()
ensure_fiduciary_tables()

UPLOAD_FOLDER = Path("uploads")
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "jpg", "jpeg", "png"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

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
            "status": "Draft"
        }
        create_trust_record(trust)
        return redirect(url_for("create_trust_step2", trust_id=trust_id))
    return render_template("create_trust_step1.html")

@app.route("/create_trust_step2/<trust_id>", methods=["GET", "POST"])
def create_trust_step2(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    if request.method == "POST":
        update_trust_fields(trust_id, {
            "trust_type": request.form.get("trust_type"),
            "trust_purpose": request.form.get("trust_purpose"),
            "accounting_method": request.form.get("accounting_method"),
            "workflow_mode": request.form.get("workflow_mode"),
            "status": "Draft - Step 2 Complete",
        })
        return redirect(url_for("create_trust_step3", trust_id=trust_id))
    return render_template("create_trust_step2.html", trust=trust)

@app.route("/create_trust_step3/<trust_id>", methods=["GET", "POST"])
def create_trust_step3(trust_id):
    trust = get_trust_by_id(trust_id)
    if not trust:
        return f"Trust {trust_id} not found"
    if request.method == "POST":
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


@app.route("/exports")
def export_center():
    trusts = get_all_trusts()
    return render_template("export_center.html", trusts=trusts)


@app.route("/exports/handoff/<filename>")
def export_handoff_file(filename):
    from flask import send_from_directory
    return send_from_directory("handoff", filename, as_attachment=True)


@app.route("/exports/roadmap/<filename>")
def export_roadmap_file(filename):
    from flask import send_from_directory
    return send_from_directory("roadmap", filename, as_attachment=True)


@app.route("/exports/package/<filename>")
def export_package_file(filename):
    from flask import send_from_directory
    return send_from_directory("package_export", filename, as_attachment=True)


@app.route("/exports/zip")
def export_zip_snapshot():
    from flask import send_file
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
    toggle_beneficiary_active(beneficiary_id, trust_id)
    return redirect(url_for("k1_trust_view", trust_id=trust_id))


@app.route("/k1/trust/<trust_id>/distribution/<distribution_id>/edit", methods=["GET", "POST"])
def k1_edit_distribution(trust_id, distribution_id):
    trust = get_trust_by_id(trust_id)
    distribution = get_distribution_by_id_and_trust(distribution_id, trust_id)
    beneficiaries = get_beneficiaries_by_trust_id(trust_id)

    if request.method == "POST":
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


if __name__ == "__main__":
    app.run(debug=True)
