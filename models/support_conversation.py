
from datetime import datetime

from extensions import db


class SupportConversation(db.Model):

    __tablename__ = "support_conversations"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaints.id"),
        nullable=True
    )

    assigned_staff_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    meter_number = db.Column(
        db.String(50),
        nullable=True
    )

    location = db.Column(
        db.String(200),
        nullable=True
    )

    status = db.Column(
        db.String(30),
        default="AI_ACTIVE",
        nullable=False,
        index=True
    )

    ai_summary = db.Column(
        db.Text,
        nullable=True
    )

    recommended_priority = db.Column(
        db.String(20),
        nullable=True
    )

    sentiment = db.Column(
        db.String(30),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    assigned_at = db.Column(
        db.DateTime,
        nullable=True
    )

    resolved_at = db.Column(
        db.DateTime,
        nullable=True
    )

    customer = db.relationship(
        "User",
        foreign_keys=[customer_id]
    )

    assigned_staff = db.relationship(
        "User",
        foreign_keys=[assigned_staff_id]
    )

    complaint = db.relationship(
        "Complaint",
        foreign_keys=[complaint_id]
    )

    messages = db.relationship(
        "SupportMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="SupportMessage.created_at"
    )

    def __repr__(self):

        return (
            f"<SupportConversation("
            f"id={self.id}, "
            f"customer_id={self.customer_id}, "
            f"status={self.status})>"
        )
