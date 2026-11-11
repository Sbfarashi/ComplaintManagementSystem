
from datetime import datetime

from extensions import db


class SupportMessage(db.Model):

    __tablename__ = "support_messages"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    conversation_id = db.Column(
        db.Integer,
        db.ForeignKey("support_conversations.id"),
        nullable=False,
        index=True
    )

    sender_type = db.Column(
        db.String(20),
        nullable=False
    )

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    conversation = db.relationship(
        "SupportConversation",
        back_populates="messages"
    )

    sender = db.relationship(
        "User",
        foreign_keys=[sender_id]
    )

    def __repr__(self):

        return (
            f"<SupportMessage("
            f"id={self.id}, "
            f"sender_type={self.sender_type}, "
            f"conversation_id={self.conversation_id})>"
        )
