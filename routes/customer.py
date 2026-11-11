from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    current_app
)

from models.complaint import Complaint

customer = Blueprint("customer", __name__)


@customer.route("/dashboard")
def dashboard():

    # Verify customer authentication
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Retrieve logged-in customer ID
    user_id = session.get("user_id")

    current_app.logger.info(
        "ICCMS Dashboard - Customer ID: %s", user_id
    )

    # Retrieve complaints belonging to this customer
    base_query = Complaint.query.filter_by(
        customer_id=user_id
    )

    complaints = (
        base_query
        .order_by(Complaint.created_at.desc())
        .limit(5)
        .all()
    )

    # Dashboard statistics
    total = base_query.count()

    pending = base_query.filter_by(
        status="Pending"
    ).count()

    resolved = base_query.filter_by(
        status="Resolved"
    ).count()

    escalated = base_query.filter_by(
        status="Escalated"
    ).count()

    # Diagnostic information
    current_app.logger.info(
        "Customer complaint count: %s", total
    )

    current_app.logger.info(
        "Retrieved complaint IDs: %s",
        [complaint.id for complaint in complaints]
    )

    # Render customer dashboard
    return render_template(
        "customer/dashboard.html",
        complaints=complaints,
        total_complaints=total,
        pending=pending,
        resolved=resolved,
        escalated=escalated
    )
