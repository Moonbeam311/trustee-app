from datetime import date
from flask_sqlalchemy import SQLAlchemy

try:
    from extensions import db
except Exception:
    db = SQLAlchemy()


class Beneficiary(db.Model):
    __tablename__ = "beneficiaries"

    id = db.Column(db.Integer, primary_key=True)
    trust_id = db.Column(db.Integer, db.ForeignKey("trusts.id"), nullable=False)

    full_name = db.Column(db.String(255), nullable=False)
    tax_id = db.Column(db.String(64), nullable=True)
    beneficiary_type = db.Column(db.String(50), nullable=False, default="individual")
    email = db.Column(db.String(255), nullable=True)
    address = db.Column(db.Text, nullable=True)

    allocation_method = db.Column(db.String(50), nullable=False, default="discretionary")
    fixed_percentage = db.Column(db.Float, nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.Date, nullable=False, default=date.today)
    updated_at = db.Column(db.Date, nullable=False, default=date.today, onupdate=date.today)

    distributions = db.relationship(
        "Distribution",
        backref="beneficiary",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Distribution(db.Model):
    __tablename__ = "distributions"

    id = db.Column(db.Integer, primary_key=True)
    trust_id = db.Column(db.Integer, db.ForeignKey("trusts.id"), nullable=False)
    beneficiary_id = db.Column(db.Integer, db.ForeignKey("beneficiaries.id"), nullable=False)

    tax_year = db.Column(db.Integer, nullable=False)
    distribution_date = db.Column(db.Date, nullable=False, default=date.today)

    distribution_type = db.Column(db.String(50), nullable=False, default="cash")
    description = db.Column(db.Text, nullable=True)

    gross_amount = db.Column(db.Float, nullable=False, default=0.0)
    taxable_amount = db.Column(db.Float, nullable=False, default=0.0)
    principal_amount = db.Column(db.Float, nullable=False, default=0.0)

    source_reference = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=False, default="recorded")

    created_at = db.Column(db.Date, nullable=False, default=date.today)
    updated_at = db.Column(db.Date, nullable=False, default=date.today, onupdate=date.today)
