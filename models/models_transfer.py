from datetime import datetime

from extensions import db


class Transfer(db.Model):
    __tablename__ = "transfers"

    id = db.Column(db.Integer, primary_key=True)
    trust_id = db.Column(db.String(64), nullable=False, index=True)
    transfer_id = db.Column(db.String(32), nullable=False, unique=True, index=True)

    mode = db.Column(db.String(20), nullable=False, default="simulation")
    status = db.Column(db.String(20), nullable=False, default="draft")
    current_capacity = db.Column(db.String(20), nullable=False, default="individual")

    asset_type = db.Column(db.String(50), nullable=True)
    asset_name = db.Column(db.String(255), nullable=True)
    asset_description = db.Column(db.Text, nullable=True)
    estimated_value = db.Column(db.String(100), nullable=True)
    current_owner = db.Column(db.String(255), nullable=True)
    asset_notes = db.Column(db.Text, nullable=True)

    transfer_type = db.Column(db.String(50), nullable=True)
    consideration_text = db.Column(db.Text, nullable=True)
    classification_notes = db.Column(db.Text, nullable=True)

    assignment_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    assignment_text = db.Column(db.Text, nullable=True)

    trustee_name = db.Column(db.String(255), nullable=True)
    trustee_decision = db.Column(db.String(50), nullable=True)
    trustee_notes = db.Column(db.Text, nullable=True)

    control_change_status = db.Column(db.String(50), nullable=True)
    control_evidence_notes = db.Column(db.Text, nullable=True)

    records_complete = db.Column(db.Boolean, nullable=False, default=False)

    created_by = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    finalized_at = db.Column(db.DateTime, nullable=True)
    finalized_by = db.Column(db.String(255), nullable=True)
    finalized_capacity = db.Column(db.String(50), nullable=True)

    # B: real-world external transfer tracking
    external_institution = db.Column(db.String(255), nullable=True)
    external_account_ref = db.Column(db.String(255), nullable=True)
    external_transfer_method = db.Column(db.String(100), nullable=True)
    external_transaction_id = db.Column(db.String(255), nullable=True)
    external_verified = db.Column(db.Boolean, nullable=False, default=False)
    external_verified_at = db.Column(db.DateTime, nullable=True)
    external_proof_notes = db.Column(db.Text, nullable=True)


    actions = db.relationship(
        "TransferAction",
        backref="transfer",
        lazy=True,
        cascade="all, delete-orphan",
    )
    record_bundle = db.relationship(
        "TransferRecord",
        backref="transfer",
        uselist=False,
        lazy=True,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Transfer {self.transfer_id} trust={self.trust_id} status={self.status}>"

    @property
    def is_simulation(self) -> bool:
        return self.mode == "simulation"

    @property
    def is_real(self) -> bool:
        return self.mode == "real"


class TransferAction(db.Model):
    __tablename__ = "transfer_actions"

    id = db.Column(db.Integer, primary_key=True)
    transfer_id_fk = db.Column(
        db.Integer,
        db.ForeignKey("transfers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action_type = db.Column(db.String(100), nullable=False)
    performed_by = db.Column(db.String(255), nullable=True)
    capacity_used = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<TransferAction transfer={self.transfer_id_fk} action={self.action_type}>"


class TransferRecord(db.Model):
    __tablename__ = "transfer_records"

    id = db.Column(db.Integer, primary_key=True)
    transfer_id_fk = db.Column(
        db.Integer,
        db.ForeignKey("transfers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    schedule_a_text = db.Column(db.Text, nullable=True)
    transfer_log_text = db.Column(db.Text, nullable=True)
    minutes_text = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<TransferRecord transfer={self.transfer_id_fk}>"
