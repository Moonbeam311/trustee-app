from collections import defaultdict
from datetime import date

from models.models_k1 import Beneficiary, Distribution


def get_tax_year():
    return date.today().year


def summarize_distributions_for_trust(trust_id: int, tax_year: int):
    rows = Distribution.query.filter_by(trust_id=trust_id, tax_year=tax_year).all()

    total_gross = sum(r.gross_amount or 0 for r in rows)
    total_taxable = sum(r.taxable_amount or 0 for r in rows)
    total_principal = sum(r.principal_amount or 0 for r in rows)

    by_beneficiary = defaultdict(lambda: {
        "gross": 0.0,
        "taxable": 0.0,
        "principal": 0.0,
        "count": 0,
        "beneficiary_name": ""
    })

    for r in rows:
        key = r.beneficiary_id
        by_beneficiary[key]["gross"] += r.gross_amount or 0
        by_beneficiary[key]["taxable"] += r.taxable_amount or 0
        by_beneficiary[key]["principal"] += r.principal_amount or 0
        by_beneficiary[key]["count"] += 1
        by_beneficiary[key]["beneficiary_name"] = r.beneficiary.full_name if r.beneficiary else "Unknown"

    return {
        "total_gross": total_gross,
        "total_taxable": total_taxable,
        "total_principal": total_principal,
        "by_beneficiary": dict(by_beneficiary)
    }


def k1_readiness_check(trust, tax_year: int, ledger_entries=None):
    active_beneficiaries = Beneficiary.query.filter_by(trust_id=trust.id, is_active=True).all()
    distributions = Distribution.query.filter_by(trust_id=trust.id, tax_year=tax_year).all()

    has_beneficiaries = len(active_beneficiaries) > 0
    has_distributions = len(distributions) > 0

    has_ledger_activity = False
    if ledger_entries:
        has_ledger_activity = len(ledger_entries) > 0

    likely_k1_required = has_beneficiaries and has_distributions

    reasons = []
    warnings = []

    if has_beneficiaries:
        reasons.append("Active beneficiaries exist.")
    else:
        warnings.append("No active beneficiaries found.")

    if has_distributions:
        reasons.append("Distributions have been recorded for the selected tax year.")
    else:
        warnings.append("No distributions recorded for the selected tax year.")

    if has_ledger_activity:
        reasons.append("Trust ledger activity detected.")
    else:
        warnings.append("No ledger activity was supplied to the K-1 readiness check.")

    for b in active_beneficiaries:
        if not b.tax_id:
            warnings.append(f"Beneficiary '{b.full_name}' is missing tax identification data.")

    return {
        "likely_k1_required": likely_k1_required,
        "has_beneficiaries": has_beneficiaries,
        "has_distributions": has_distributions,
        "has_ledger_activity": has_ledger_activity,
        "reasons": reasons,
        "warnings": warnings
    }
