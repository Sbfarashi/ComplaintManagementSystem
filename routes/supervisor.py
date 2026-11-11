from flask import Blueprint, render_template
from sqlalchemy import func

from decorators.auth import login_required, supervisor_required
from extensions import db
from models.complaint import Complaint
from models.user import User
from constants.roles import UserRole

supervisor = Blueprint("supervisor", __name__, url_prefix="/supervisor")


@supervisor.route("/dashboard")
@login_required
@supervisor_required
def dashboard():
    """High-level operational overview for supervisors."""
    total_complaints = Complaint.query.count()
    pending = Complaint.query.filter(func.lower(Complaint.status) == "pending").count()
    in_progress = Complaint.query.filter(func.lower(Complaint.status) == "in progress").count()
    resolved = Complaint.query.filter(
        func.lower(Complaint.status).in_(["resolved", "closed"])
    ).count()

    active_staff = User.query.filter(
        User.role.in_([UserRole.STAFF, UserRole.ENGINEER]),
        User.is_active.is_(True)
    ).count()

    recent_complaints = Complaint.query.order_by(
        Complaint.created_at.desc()
    ).limit(10).all()

    return render_template(
        "supervisor/dashboard.html",
        total_complaints=total_complaints,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved,
        active_staff=active_staff,
        recent_complaints=recent_complaints,
    )
