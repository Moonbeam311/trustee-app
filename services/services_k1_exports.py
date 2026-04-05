import csv
import io
from collections import defaultdict
from models.models_k1 import Beneficiary, Distribution

def build_distribution_csv(trust, tax_year):
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "trust_id","trust_name","beneficiary_id","beneficiary_name",
        "beneficiary_tax_id","tax_year","distribution_date",
        "distribution_type","gross_amount","taxable_amount",
        "principal_amount","status","source_reference","description"
    ])

    rows = Distribution.query.filter_by(trust_id=trust.id, tax_year=tax_year).all()

    for r in rows:
        b = r.beneficiary
        writer.writerow([
            trust.id,
            getattr(trust, "name", ""),
            r.beneficiary_id,
            b.full_name if b else "",
            b.tax_id if b else "",
            r.tax_year,
            r.distribution_date,
            r.distribution_type,
            r.gross_amount,
            r.taxable_amount,
            r.principal_amount,
            r.status,
            r.source_reference,
            r.description
        ])

    return output.getvalue()

def build_year_end_summary(trust_id, tax_year):
    beneficiaries = Beneficiary.query.filter_by(trust_id=trust_id).all()
    distributions = Distribution.query.filter_by(trust_id=trust_id, tax_year=tax_year).all()

    total_gross = sum(d.gross_amount or 0 for d in distributions)
    total_taxable = sum(d.taxable_amount or 0 for d in distributions)
    total_principal = sum(d.principal_amount or 0 for d in distributions)

    by_beneficiary = defaultdict(lambda: {"gross":0,"taxable":0,"principal":0,"count":0})

    for d in distributions:
        entry = by_beneficiary[d.beneficiary_id]
        entry["gross"] += d.gross_amount or 0
        entry["taxable"] += d.taxable_amount or 0
        entry["principal"] += d.principal_amount or 0
        entry["count"] += 1

    return {
        "total_gross": total_gross,
        "total_taxable": total_taxable,
        "total_principal": total_principal,
        "by_beneficiary": dict(by_beneficiary)
    }
