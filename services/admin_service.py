
from sqlalchemy import func

from extensions import db

from models.user import User
from models.complaint import Complaint
from models.category import Category

from constants.roles import UserRole


class AdminService:

    # ==========================================================
    # ADMIN DASHBOARD
    # ==========================================================

    @staticmethod
    def dashboard():

        total_users = User.query.filter_by(
            role=UserRole.CUSTOMER
        ).count()

        total_staff = User.query.filter(
            User.role.in_(
                [
                    UserRole.STAFF,
                    UserRole.ENGINEER,
                    UserRole.ADMIN
                ]
            )
        ).count()

        total_complaints = Complaint.query.count()

        pending = Complaint.query.filter_by(
            status="Pending"
        ).count()

        in_progress = Complaint.query.filter(
            Complaint.status.in_(
                [
                    "Assigned",
                    "In Progress"
                ]
            )
        ).count()

        resolved = Complaint.query.filter(
            Complaint.status.in_(
                [
                    "Resolved",
                    "Closed"
                ]
            )
        ).count()

        level1 = Complaint.query.filter_by(
            escalation_level=1
        ).count()

        level2 = Complaint.query.filter_by(
            escalation_level=2
        ).count()

        level3 = Complaint.query.filter_by(
            escalation_level=3
        ).count()

        total_escalated = Complaint.query.filter(
            Complaint.escalation_level > 0
        ).count()

        recent = (
            Complaint.query
            .order_by(
                Complaint.created_at.desc()
            )
            .limit(10)
            .all()
        )

        recent_escalated = (
            Complaint.query
            .filter(
                Complaint.escalation_level > 0
            )
            .order_by(
                Complaint.created_at.desc()
            )
            .limit(10)
            .all()
        )

        return {
            "total_users": total_users,
            "total_staff": total_staff,
            "total_complaints": total_complaints,
            "pending": pending,
            "in_progress": in_progress,
            "resolved": resolved,

            "escalation": {
                "level1": level1,
                "level2": level2,
                "level3": level3,
                "total": total_escalated
            },

            "recent": recent,
            "recent_escalated": recent_escalated
        }

    # ==========================================================
    # COMPLAINTS BY PRIORITY
    # ==========================================================

    @staticmethod
    def complaints_by_priority():

        rows = (
            db.session.query(
                Complaint.priority.label("priority"),
                func.count(
                    Complaint.id
                ).label("total")
            )
            .group_by(
                Complaint.priority
            )
            .order_by(
                Complaint.priority
            )
            .all()
        )

        return [
            {
                "priority": row.priority,
                "total": row.total
            }
            for row in rows
        ]

    # ==========================================================
    # COMPLAINTS BY STATUS
    # ==========================================================

    @staticmethod
    def complaints_by_status():

        rows = (
            db.session.query(
                Complaint.status.label("status"),
                func.count(
                    Complaint.id
                ).label("total")
            )
            .group_by(
                Complaint.status
            )
            .order_by(
                Complaint.status
            )
            .all()
        )

        return [
            {
                "status": row.status,
                "total": row.total
            }
            for row in rows
        ]

    # ==========================================================
    # COMPLAINTS BY CATEGORY
    # ==========================================================

    @staticmethod
    def complaints_by_category():

        rows = (
            db.session.query(
                Category.name.label("category"),
                func.count(
                    Complaint.id
                ).label("total")
            )
            .join(
                Complaint,
                Complaint.category_id == Category.id
            )
            .group_by(
                Category.id,
                Category.name
            )
            .order_by(
                Category.name
            )
            .all()
        )

        return [
            {
                "category": row.category,
                "total": row.total
            }
            for row in rows
        ]

    # ==========================================================
    # MONTHLY COMPLAINT STATISTICS
    # Supports SQLite and PostgreSQL
    # ==========================================================

    @staticmethod
    def monthly_statistics():

        database_type = db.session.get_bind().dialect.name

        if database_type == "postgresql":

            month_expression = func.to_char(
                Complaint.created_at,
                "YYYY-MM"
            )

        else:

            month_expression = func.strftime(
                "%Y-%m",
                Complaint.created_at
            )

        rows = (
            db.session.query(
                month_expression.label("month"),
                func.count(
                    Complaint.id
                ).label("total")
            )
            .group_by(
                month_expression
            )
            .order_by(
                month_expression
            )
            .all()
        )

        return [
            {
                "month": row.month,
                "total": row.total
            }
            for row in rows
        ]

    # ==========================================================
    # STAFF PERFORMANCE
    # ==========================================================

    @staticmethod
    def staff_performance():

        rows = (
            db.session.query(
                User.full_name.label("staff"),
                func.count(
                    Complaint.id
                ).label("total")
            )
            .outerjoin(
                Complaint,
                (User.id == Complaint.assigned_to)
                &
                (
                    Complaint.status.in_(
                        [
                            "Resolved",
                            "Closed"
                        ]
                    )
                )
            )
            .filter(
                User.role.in_(
                    [
                        UserRole.STAFF,
                        UserRole.ENGINEER
                    ]
                )
            )
            .group_by(
                User.id,
                User.full_name
            )
            .order_by(
                func.count(
                    Complaint.id
                ).desc()
            )
            .all()
        )

        return [
            {
                "staff": row.staff,
                "total": row.total
            }
            for row in rows
        ]

    # ==========================================================
    # HIGH PRIORITY COMPLAINTS
    # ==========================================================

    @staticmethod
    def high_priority():

        return (
            Complaint.query
            .filter(
                Complaint.priority.in_(
                    [
                        "High",
                        "Critical"
                    ]
                )
            )
            .order_by(
                Complaint.created_at.desc()
            )
            .limit(10)
            .all()
        )

    # ==========================================================
    # RECENTLY RESOLVED COMPLAINTS
    # ==========================================================

    @staticmethod
    def recently_resolved():

        return (
            Complaint.query
            .filter(
                Complaint.status.in_(
                    [
                        "Resolved",
                        "Closed"
                    ]
                )
            )
            .order_by(
                Complaint.created_at.desc()
            )
            .limit(10)
            .all()
        )

    # ==========================================================
    # OVERDUE COMPLAINTS
    # ==========================================================

    @staticmethod
    def overdue():

        return (
            Complaint.query
            .filter(
                Complaint.status.notin_(
                    [
                        "Resolved",
                        "Closed"
                    ]
                )
            )
            .order_by(
                Complaint.created_at.asc()
            )
            .all()
        )

    # ==========================================================
    # GET ALL USERS
    # ==========================================================

    @staticmethod
    def get_all_users():

        return (
            User.query
            .order_by(
                User.created_at.desc()
            )
            .all()
        )

    # ==========================================================
    # GET USER BY ID
    # ==========================================================

    @staticmethod
    def get_user(user_id):

        return User.query.get_or_404(user_id)

    # ==========================================================
    # ACTIVATE / DEACTIVATE USER
    # ==========================================================

    @staticmethod
    def toggle_user_status(user_id):

        user = User.query.get_or_404(user_id)

        if not hasattr(user, "is_active"):
            return None

        user.is_active = not user.is_active

        db.session.commit()

        return user

    # ==========================================================
    # DELETE USER
    # ==========================================================

    @staticmethod
    def delete_user(user_id):

        user = User.query.get_or_404(user_id)

        db.session.delete(user)

        db.session.commit()

        return True

    # ==========================================================
    # DASHBOARD SUMMARY
    # ==========================================================

    @staticmethod
    def dashboard_summary():

        return {
            "dashboard": AdminService.dashboard(),

            "status": AdminService.complaints_by_status(),

            "priority": AdminService.complaints_by_priority(),

            "category": AdminService.complaints_by_category(),

            "monthly": AdminService.monthly_statistics(),

            "staff": AdminService.staff_performance(),

            "high_priority": AdminService.high_priority(),

            "recently_resolved": AdminService.recently_resolved(),

            "overdue": AdminService.overdue()
        }
