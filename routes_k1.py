from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response

from models.models_k1 import db, Beneficiary, Distribution
from services.services_k1 import get_tax_year, summarize_distributions_for_trust, k1_readiness_check
from services.services_k1_exports import build_distribution_csv, build_year_end_summary

from models import Trust, LedgerEntry

k1_bp = Blueprint("k1", __name__)


@k1_bp.route("/k1")
def k1_home():
    trusts = Trust.query.order_by(Trust.id.desc()).all()
    return render_template("k1_dashboard.html", trusts=trusts, tax_year=get_tax_year())


@k1_bp.route("/k1/trust/<int:trust_id>")
def k1_trust_view(trust_id):
    tax_year = request.args.get("tax_year", default=get_tax_year(), type=int)

    trust = Trust.query.get_or_404(trust_id)
    beneficiaries = Beneficiary.query.filter_by(trust_id=trust_id).order_by(Beneficiary.full_name.asc()).all()
    distributions = Distribution.query.filter_by(trust_id=trust_id, tax_year=tax_year).order_by(
        Distribution.distribution_date.desc()
    ).all()

    ledger_entries = []
    try:
        ledger_entries = LedgerEntry.query.filter_by(trust_id=trust_id).all()
    except Exception:
        ledger_entries = []

    summary = summarize_distributions_for_trust(trust_id, tax_year)
    readiness = k1_readiness_check(trust, tax_year, ledger_entries)

    return render_template(
        "k1_readiness.html",
        trust=trust,
        beneficiaries=beneficiaries,
        distributions=distributions,
        summary=summary,
        readiness=readiness,
        tax_year=tax_year
    )


@k1_bp.route("/k1/trust/<int:trust_id>/beneficiary/new", methods=["GET", "POST"])
def new_beneficiary(trust_id):
    trust = Trust.query.get_or_404(trust_id)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        tax_id = request.form.get("tax_id", "").strip() or None
        beneficiary_type = request.form.get("beneficiary_type", "individual").strip()
        email = request.form.get("email", "").strip() or None
        address = request.form.get("address", "").strip() or None
        allocation_method = request.form.get("allocation_method", "discretionary").strip()
        fixed_percentage_raw = request.form.get("fixed_percentage", "").strip()
        notes = request.form.get("notes", "").strip() or None

        if not full_name:
            flash("Beneficiary name is required.", "danger")
            return render_template("k1_beneficiary_form.html", trust=trust)

        fixed_percentage = None
        if fixed_percentage_raw:
            try:
                fixed_percentage = float(fixed_percentage_raw)
            except ValueError:
                flash("Fixed percentage must be numeric.", "danger")
                return render_template("k1_beneficiary_form.html", trust=trust)

        beneficiary = Beneficiary(
            trust_id=trust.id,
            full_name=full_name,
            tax_id=tax_id,
            beneficiary_type=beneficiary_type,
            email=email,
            address=address,
            allocation_method=allocation_method,
            fixed_percentage=fixed_percentage,
            notes=notes,
            is_active=True
        )

        db.session.add(beneficiary)
        db.session.commit()
        flash("Beneficiary added successfully.", "success")
        return redirect(url_for("k1.k1_trust_view", trust_id=trust.id))

    return render_template("k1_beneficiary_form.html", trust=trust)


@k1_bp.route("/k1/trust/<int:trust_id>/distribution/new", methods=["GET", "POST"])
def new_distribution(trust_id):
    trust = Trust.query.get_or_404(trust_id)
    beneficiaries = Beneficiary.query.filter_by(trust_id=trust.id, is_active=True).order_by(Beneficiary.full_name.asc()).all()

    if request.method == "POST":
        beneficiary_id = request.form.get("beneficiary_id", type=int)
        tax_year = request.form.get("tax_year", type=int)
        distribution_date_raw = request.form.get("distribution_date", "").strip()
        distribution_type = request.form.get("distribution_type", "cash").strip()
        description = request.form.get("description", "").strip() or None

        gross_amount = request.form.get("gross_amount", type=float, default=0.0)
        taxable_amount = request.form.get("taxable_amount", type=float, default=0.0)
        principal_amount = request.form.get("principal_amount", type=float, default=0.0)
        source_reference = request.form.get("source_reference", "").strip() or None

        if not beneficiary_id:
            flash("Beneficiary selection is required.", "danger")
            return render_template("k1_distribution_form.html", trust=trust, beneficiaries=beneficiaries)

        if not tax_year:
            flash("Tax year is required.", "danger")
            return render_template("k1_distribution_form.html", trust=trust, beneficiaries=beneficiaries)

        try:
            distribution_date = datetime.strptime(distribution_date_raw, "%Y-%m-%d").date()
        except ValueError:
            flash("Distribution date must be YYYY-MM-DD.", "danger")
            return render_template("k1_distribution_form.html", trust=trust, beneficiaries=beneficiaries)

        record = Distribution(
            trust_id=trust.id,
            beneficiary_id=beneficiary_id,
            tax_year=tax_year,
            distribution_date=distribution_date,
            distribution_type=distribution_type,
            description=description,
            gross_amount=gross_amount or 0.0,
            taxable_amount=taxable_amount or 0.0,
            principal_amount=principal_amount or 0.0,
            source_reference=source_reference,
            status="recorded"
        )

        db.session.add(record)
        db.session.commit()
        flash("Distribution recorded successfully.", "success")
        return redirect(url_for("k1.k1_trust_view", trust_id=trust.id, tax_year=tax_year))

    return render_template(
        "k1_distribution_form.html",
        trust=trust,
        beneficiaries=beneficiaries,
        tax_year=get_tax_year()
    )


@k1_bp.route("/k1/trust/<int:trust_id>/export.csv")
def export_k1_csv(trust_id):
    tax_year = request.args.get("tax_year", default=get_tax_year(), type=int)
    trust = Trust.query.get_or_404(trust_id)

    csv_content = build_distribution_csv(trust, tax_year)
    response = make_response(csv_content)
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = f"attachment; filename=trust_{trust.id}_k1_{tax_year}.csv"
    return response


@k1_bp.route("/k1/trust/<int:trust_id>/year_end_summary")
def year_end_summary(trust_id):
    tax_year = request.args.get("tax_year", default=get_tax_year(), type=int)
    trust = Trust.query.get_or_404(trust_id)
    summary = build_year_end_summary(trust.id, tax_year)

    return render_template(
        "k1_year_end_summary.html",
        trust=trust,
        tax_year=tax_year,
        summary=summary
    )
