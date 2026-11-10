
from datetime import datetime

from extensions import db


class PasswordResetRequest(db.Model):

    __tablename__ = "password_reset_requests"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="Pending",
        nullable=False
    )

    requested_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    reviewed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    reviewed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    completed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    requested_user = db.relationship(
        "User",
        foreign_keys=[user_id]
    )

    reviewed_by_admin = db.relationship(
        "User",
        foreign_keys=[reviewed_by]
    )

    def __repr__(self):
        return f"<PasswordResetRequest {self.id}: {self.status}>"
