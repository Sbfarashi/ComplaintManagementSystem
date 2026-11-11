from flask import Flask, render_template

from config import Config

# ==========================================================
# Extensions
# ==========================================================

from extensions import db, bcrypt, migrate

# ==========================================================
# Bootstrap Service
# ==========================================================

from services.bootstrap_service import BootstrapService

# ==========================================================
# Models
# ==========================================================

from models.user import User
from models.complaint import Complaint
from models.category import Category
from models.department import Department
from models.complaint_status import ComplaintStatus
from models.priority import Priority
from models.complaint_history import ComplaintHistory
from models.notification import Notification
from models.password_reset_request import PasswordResetRequest
from models.field_visit import FieldVisit
from models.login_history import LoginHistory
from routes.activity_log import activity_log
from models.support_conversation import SupportConversation
from models.support_message import SupportMessage

# ==========================================================
# Blueprints
# ==========================================================

from routes.auth import auth
from routes.customer import customer
from routes.complaint import complaint
from routes.staff import staff
from routes.supervisor import supervisor
from routes.admin import admin
from routes.notification import notification
from routes.engineer import engineer_bp
from routes.login_history import login_history
from models.activity_log import ActivityLog
from routes.report import report
from routes.support import support


def create_app():

    app = Flask(__name__)

    # ==========================================================
    # Configuration
    # ==========================================================

    app.config.from_object(Config)

    # ==========================================================
    # Initialize Extensions
    # ==========================================================

    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    # ==========================================================
    # Register Blueprints
    # ==========================================================

    app.register_blueprint(auth)
    app.register_blueprint(customer)
    app.register_blueprint(complaint)
    app.register_blueprint(staff)
    app.register_blueprint(supervisor)
    app.register_blueprint(admin)
    app.register_blueprint(notification)
    app.register_blueprint(engineer_bp)
    app.register_blueprint(login_history)
    app.register_blueprint(activity_log)
    app.register_blueprint(report)
    app.register_blueprint(support)

    # ==========================================================
    # Create Database Tables
    # ==========================================================

    with app.app_context():

        db.create_all()

        BootstrapService.bootstrap()

    # ==========================================================
    # Public Routes
    # ==========================================================

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/services")
    def services():
        return render_template("services.html")

    @app.route("/contact")
    def contact():
        return render_template("contact.html")

    # ==========================================================
    # Context Processor
    # ==========================================================

    @app.context_processor
    def inject_notifications():

        from flask import session

        unread_notifications = 0

        if session.get("logged_in"):

            unread_notifications = Notification.query.filter_by(
                user_id=session["user_id"],
                is_read=False
            ).count()

        return {
            "unread_notifications": unread_notifications
        }

    print("=" * 60)
    print("Smart Meters Company Ltd")
    print("Intelligent Customer Complaint Management System")
    print("Application initialized successfully.")
    print("=" * 60)

    return app


# ==========================================================
# Run Application
# ==========================================================

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)