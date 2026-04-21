from datetime import datetime
from extensions import db


class TransferSupportDoc(db.Model):
    __tablename__ = "transfer_support_docs"

    id = db.Column(db.Integer, primary_key=True)

    transfer_id_fk = db.Column(
        db.Integer,
        db.ForeignKey("transfers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    category_key = db.Column(db.String(100), nullable=False, index=True)
    category_label = db.Column(db.String(255), nullable=False)

    status = db.Column(db.String(50), nullable=False, default="missing")
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __repr__(self) -> str:
        return f"<TransferSupportDoc transfer={self.transfer_id_fk} category={self.category_key} status={self.status}>"
