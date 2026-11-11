from datetime import datetime

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)

from extensions import db
from constants.roles import UserRole
from models.user import User
from models.support_conversation import SupportConversation
from models.support_message import SupportMessage
from services.ai_support_service import (
    generate_support_response,
    analyze_complaint
)

support = Blueprint("support", __name__)


def current_user():
    if "user_id" not in session:
        return None
    return User.query.get(session["user_id"])


def staff_required():
    user = current_user()
    return user and (
        user.role in UserRole.STAFF_ROLES
        or user.role == UserRole.ADMIN
    )


@support.route("/customer/support", methods=["GET", "POST"])
def customer_support():
    user = current_user()

    if not user:
        return redirect(url_for("auth.login"))

    if user.role != UserRole.CUSTOMER:
        flash("Customer access only.", "danger")
        return redirect(url_for("customer.dashboard"))

    conversations = (
        SupportConversation.query
        .filter_by(customer_id=user.id)
        .order_by(SupportConversation.updated_at.desc())
        .all()
    )

    return render_template(
        "customer/support.html",
        conversations=conversations
    )


@support.route("/customer/support/start", methods=["POST"])
def start_conversation():
    user = current_user()

    if not user or user.role != UserRole.CUSTOMER:
        return redirect(url_for("auth.login"))

    message = request.form.get("message", "").strip()
    meter_number = request.form.get("meter_number", "").strip()
    location = request.form.get("location", "").strip()

    if not message:
        flash("Please describe your problem.", "danger")
        return redirect(url_for("support.customer_support"))

    analysis = analyze_complaint(message)

    conversation = SupportConversation(
        customer_id=user.id,
        meter_number=meter_number or None,
        location=location or None,
        status=(
            "HUMAN_REQUESTED"
            if analysis["safety_alert"]
            else "AI_ACTIVE"
        ),
        ai_summary=message[:1000],
        recommended_priority=analysis["recommended_priority"],
        sentiment=analysis["sentiment"]
    )

    db.session.add(conversation)
    db.session.flush()

    db.session.add(SupportMessage(
        conversation_id=conversation.id,
        sender_type="customer",
        sender_id=user.id,
        message=message
    ))

    if analysis["safety_alert"]:
        reply = analysis["support_response"]
    else:
        reply = generate_support_response(
            message,
            analysis["category"]
        )

    db.session.add(SupportMessage(
        conversation_id=conversation.id,
        sender_type="ai",
        message=reply
    ))

    conversation.updated_at = datetime.utcnow()
    db.session.commit()

    flash("Support conversation started.", "success")

    return redirect(
        url_for("support.view_conversation", conversation_id=conversation.id)
    )


@support.route("/customer/support/<int:conversation_id>")
def view_conversation(conversation_id):
    user = current_user()

    if not user or user.role != UserRole.CUSTOMER:
        return redirect(url_for("auth.login"))

    conversation = SupportConversation.query.filter_by(
        id=conversation_id,
        customer_id=user.id
    ).first_or_404()

    return render_template(
        "customer/support_conversation.html",
        conversation=conversation
    )


@support.route(
    "/customer/support/<int:conversation_id>/message",
    methods=["POST"]
)
def customer_message(conversation_id):
    user = current_user()

    if not user or user.role != UserRole.CUSTOMER:
        return redirect(url_for("auth.login"))

    conversation = SupportConversation.query.filter_by(
        id=conversation_id,
        customer_id=user.id
    ).first_or_404()

    message = request.form.get("message", "").strip()

    if not message:
        flash("Please enter a message.", "danger")
        return redirect(url_for(
            "support.view_conversation",
            conversation_id=conversation.id
        ))

    db.session.add(SupportMessage(
        conversation_id=conversation.id,
        sender_type="customer",
        sender_id=user.id,
        message=message
    ))

    if conversation.status in ["AI_ACTIVE", "AI_RESOLVED"]:
        analysis = analyze_complaint(message)

        conversation.sentiment = analysis["sentiment"]
        conversation.recommended_priority = analysis["recommended_priority"]

        if analysis["safety_alert"]:
            conversation.status = "HUMAN_REQUESTED"
            reply = analysis["support_response"]
        else:
            reply = generate_support_response(message)

        db.session.add(SupportMessage(
            conversation_id=conversation.id,
            sender_type="ai",
            message=reply
        ))

    elif conversation.status == "HUMAN_REQUESTED":
        reply = (
            "Your request is awaiting a human support officer. "
            "Please wait for our team to respond."
        )
        db.session.add(SupportMessage(
            conversation_id=conversation.id,
            sender_type="ai",
            message=reply
        ))

    else:
        flash("Your conversation is being handled by staff.", "info")

    conversation.updated_at = datetime.utcnow()
    db.session.commit()

    return redirect(url_for(
        "support.view_conversation",
        conversation_id=conversation.id
    ))


@support.route(
    "/customer/support/<int:conversation_id>/request-human",
    methods=["POST"]
)
def request_human(conversation_id):
    user = current_user()

    if not user or user.role != UserRole.CUSTOMER:
        return redirect(url_for("auth.login"))

    conversation = SupportConversation.query.filter_by(
        id=conversation_id,
        customer_id=user.id
    ).first_or_404()

    if conversation.status not in ["HUMAN_ACTIVE", "RESOLVED"]:
        conversation.status = "HUMAN_REQUESTED"
        conversation.updated_at = datetime.utcnow()

        db.session.add(SupportMessage(
            conversation_id=conversation.id,
            sender_type="customer",
            sender_id=user.id,
            message="Customer requested assistance from a human support officer."
        ))

        db.session.commit()
        flash("Your request has been sent to human support.", "success")

    return redirect(url_for(
        "support.view_conversation",
        conversation_id=conversation.id
    ))


@support.route("/staff/support")
def staff_inbox():
    if not staff_required():
        return redirect(url_for("auth.login"))

    conversations = (
        SupportConversation.query
        .filter(
            SupportConversation.status.in_(
                ["HUMAN_REQUESTED", "HUMAN_ACTIVE"]
            )
        )
        .order_by(SupportConversation.updated_at.asc())
        .all()
    )

    return render_template(
        "staff/support_inbox.html",
        conversations=conversations
    )


@support.route("/staff/support/<int:conversation_id>")
def staff_conversation(conversation_id):
    if not staff_required():
        return redirect(url_for("auth.login"))

    conversation = SupportConversation.query.get_or_404(
        conversation_id
    )

    return render_template(
        "staff/support_conversation.html",
        conversation=conversation
    )


@support.route(
    "/staff/support/<int:conversation_id>/reply",
    methods=["POST"]
)
def staff_reply(conversation_id):
    user = current_user()

    if not user or not staff_required():
        return redirect(url_for("auth.login"))

    conversation = SupportConversation.query.get_or_404(
        conversation_id
    )

    message = request.form.get("message", "").strip()

    if not message:
        flash("Please enter a reply.", "danger")
        return redirect(url_for(
            "support.staff_conversation",
            conversation_id=conversation.id
        ))

    conversation.assigned_staff_id = user.id
    conversation.assigned_at = conversation.assigned_at or datetime.utcnow()
    conversation.status = "HUMAN_ACTIVE"
    conversation.updated_at = datetime.utcnow()

    db.session.add(SupportMessage(
        conversation_id=conversation.id,
        sender_type="staff",
        sender_id=user.id,
        message=message
    ))

    db.session.commit()

    flash("Reply sent successfully.", "success")

    return redirect(url_for(
        "support.staff_conversation",
        conversation_id=conversation.id
    ))


@support.route(
    "/staff/support/<int:conversation_id>/resolve",
    methods=["POST"]
)
def resolve_conversation(conversation_id):
    user = current_user()

    if not user or not staff_required():
        return redirect(url_for("auth.login"))

    conversation = SupportConversation.query.get_or_404(
        conversation_id
    )

    conversation.status = "RESOLVED"
    conversation.resolved_at = datetime.utcnow()
    conversation.updated_at = datetime.utcnow()

    db.session.commit()

    flash("Conversation marked as resolved.", "success")

    return redirect(url_for("support.staff_inbox"))
