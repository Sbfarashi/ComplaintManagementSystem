from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from services.category_service import CategoryService

from extensions import bcrypt

from decorators.auth import admin_required

# ==========================================================
# Models
# ==========================================================

from models.user import User
from models.department import Department
from models.category import Category
from models.complaint import Complaint

# ==========================================================
# Forms
# ==========================================================

from forms.user_form import UserForm
from forms.search_form import SearchForm
from forms.assign_complaint_form import AssignComplaintForm
from forms.update_complaint_form import UpdateComplaintForm

# ==========================================================
# Services
# ==========================================================

from services.admin_service import AdminService
from services.admin_user_service import AdminUserService
from services.admin_update_service import AdminUpdateService
from services.assignment_service import AssignmentService
from services.search_service import SearchService
from services.performance_service import PerformanceService
from services.escalation_service import EscalationService

# ==========================================================
# Blueprint
# ==========================================================

admin = Blueprint(
    "admin",
    __name__
)



# ==========================================================
# DASHBOARD
# ==========================================================

@admin.route("/admin/dashboard")
@admin_required
def dashboard():

    # Run automatic escalation
    EscalationService.run()

    # Dashboard summary
    dashboard = AdminService.dashboard()

    return render_template(

        "admin/dashboard.html",

        dashboard=dashboard,

        # Existing Charts
        status=AdminService.complaints_by_status(),
        priority=AdminService.complaints_by_priority(),

        # New Dashboard Analytics
        monthly=AdminService.monthly_statistics(),
        category=AdminService.complaints_by_category(),
        staff=AdminService.staff_performance(),

        # Dashboard Widgets
        high_priority=AdminService.high_priority(),
        recently_resolved=AdminService.recently_resolved(),
        overdue=AdminService.overdue()

    )


# ==========================================================
# COMPLAINT LIST
# ==========================================================

@admin.route("/admin/complaints")
@admin_required
def complaints():

    EscalationService.run()

    form = SearchForm(request.args)

    form.category.choices = [

        ("", "All Categories")

    ] + [

        (category.name, category.name)

        for category in
        Category.query.order_by(
            Category.name
        ).all()

    ]

    page = request.args.get(
        "page",
        1,
        type=int
    )

    filters = {

        "complaint_number": request.args.get(
            "complaint_number",
            ""
        ),

        "customer": request.args.get(
            "customer",
            ""
        ),

        "meter_number": request.args.get(
            "meter_number",
            ""
        ),

        "status": request.args.get(
            "status",
            ""
        ),

        "priority": request.args.get(
            "priority",
            ""
        ),

        "category": request.args.get(
            "category",
            ""
        ),

        "date_from": request.args.get(
            "date_from",
            ""
        ),

        "date_to": request.args.get(
            "date_to",
            ""
        )

    }

    complaints = (

        SearchService

        .search(filters)

        .paginate(

            page=page,

            per_page=10,

            error_out=False

        )

    )

    return render_template(

        "admin/complaints.html",

        form=form,

        complaints=complaints,

        filters=filters

    )

# ==========================================================
# COMPLAINT DETAILS
# ==========================================================

@admin.route("/admin/complaint/<int:complaint_id>")
@admin_required
def complaint_details(complaint_id):

    complaint = Complaint.query.get_or_404(
        complaint_id
    )

    return render_template(

        "admin/complaint_details.html",

        complaint=complaint

    )


# ==========================================================
# ASSIGN COMPLAINT
# ==========================================================

@admin.route(
    "/admin/assign/<int:complaint_id>",
    methods=["GET", "POST"]
)
@admin_required
def assign_complaint(complaint_id):

    complaint = Complaint.query.get_or_404(
        complaint_id
    )

    form = AssignComplaintForm()

    staff = AssignmentService.get_staff()

    form.staff.choices = [

        (user.id, user.full_name)

        for user in staff

    ]

    if form.validate_on_submit():

        success, message, _ = AssignmentService.assign_complaint(

            complaint_id=complaint.id,

            staff_id=form.staff.data,

            admin_id=session["user_id"]

        )

        flash(

            message,

            "success" if success else "danger"

        )

        if success:

            return redirect(

                url_for(

                    "admin.complaint_details",

                    complaint_id=complaint.id

                )

            )

    return render_template(

        "admin/assign_complaint.html",

        form=form,

        complaint=complaint

    )


# ==========================================================
# UPDATE COMPLAINT
# ==========================================================

@admin.route(
    "/admin/update/<int:complaint_id>",
    methods=["GET", "POST"]
)
@admin_required
def update_complaint(complaint_id):

    complaint = AdminUpdateService.get_complaint(
        complaint_id
    )

    if complaint is None:

        flash(
            "Complaint not found.",
            "danger"
        )

        return redirect(
            url_for("admin.complaints")
        )

    form = UpdateComplaintForm()

    if request.method == "GET":

        form.status.data = complaint.status

        form.resolution.data = complaint.resolution

    if form.validate_on_submit():

        AdminUpdateService.update_complaint(

            complaint_id=complaint.id,

            form=form,

            admin_id=session["user_id"]

        )

        flash(

            "Complaint updated successfully.",

            "success"

        )

        return redirect(

            url_for(

                "admin.complaint_details",

                complaint_id=complaint.id

            )

        )

    return render_template(

        "admin/update_complaint.html",

        form=form,

        complaint=complaint

    )


# ==========================================================
# REPORTS
# ==========================================================

@admin.route("/admin/reports")
@admin_required
def reports():

    return render_template(

        "admin/reports.html",

        monthly=AdminService.monthly_statistics(),

        priority=AdminService.complaints_by_priority(),

        status=AdminService.complaints_by_status(),

        category=AdminService.complaints_by_category(),

        staff=AdminService.staff_performance(),

        high_priority=AdminService.high_priority(),

        overdue=AdminService.overdue(),

        recently_resolved=AdminService.recently_resolved()

    )

@admin.route("/admin/performance")
@admin_required
def performance():

    statistics = PerformanceService.staff_statistics()

    return render_template(

        "admin/performance.html",

        statistics=statistics

    )


# ==========================================================
# USER MANAGEMENT
# ==========================================================

@admin.route("/admin/users")
@admin_required
def users():

    keyword = request.args.get(
        "search",
        ""
    )

    if keyword:

        users = AdminUserService.search(
            keyword
        )

    else:

        users = AdminUserService.get_all_users()

    return render_template(

        "admin/users.html",

        users=users,

        keyword=keyword

    )


# ==========================================================
# USER DETAILS
# ==========================================================

@admin.route("/admin/user/<int:user_id>")
@admin_required
def user_details(user_id):

    user = AdminUserService.get_user(
        user_id
    )

    complaints = AdminUserService.complaints(
        user.id
    )

    return render_template(

        "admin/user_details.html",

        user=user,

        complaints=complaints

    )
# ==========================================================
# ADD USER
# ==========================================================

@admin.route(
    "/admin/user/add",
    methods=["GET", "POST"]
)
@admin_required
def add_user():

    form = UserForm()

    departments = Department.query.order_by(
        Department.name
    ).all()

    form.department.choices = [

        (0, "-- Select Department --")

    ] + [

        (department.id, department.name)

        for department in departments

    ]

    if form.validate_on_submit():

        password = bcrypt.generate_password_hash(

            form.password.data

        ).decode("utf-8")

        AdminUserService.create_user(

            full_name=form.full_name.data,

            employee_id=form.employee_id.data,

            designation=form.designation.data,

            email=form.email.data,

            phone=form.phone.data,

            password=password,

            role=form.role.data,

            department_id=form.department.data

        )

        flash(

            "User created successfully.",

            "success"

        )

        return redirect(

            url_for("admin.users")

        )

    return render_template(

        "admin/add_user.html",

        form=form

    )


# ==========================================================
# EDIT USER
# ==========================================================

@admin.route(
    "/admin/user/edit/<int:user_id>",
    methods=["GET", "POST"]
)
@admin_required
def edit_user(user_id):

    user = AdminUserService.get_user(
        user_id
    )

    form = UserForm(obj=user)

    departments = Department.query.order_by(
        Department.name
    ).all()

    form.department.choices = [

        (0, "-- Select Department --")

    ] + [

        (department.id, department.name)

        for department in departments

    ]

    if request.method == "GET":

        form.department.data = (

            user.department_id

            if user.department_id

            else 0

        )

    if form.validate_on_submit():

        AdminUserService.update_user(

            user=user,

            form=form

        )

        flash(

            "User updated successfully.",

            "success"

        )

        return redirect(

            url_for(

                "admin.user_details",

                user_id=user.id

            )

        )

    return render_template(

        "admin/edit_user.html",

        form=form,

        user=user

    )


# ==========================================================
# ACTIVATE / DEACTIVATE USER
# ==========================================================

@admin.route(
    "/admin/user/toggle/<int:user_id>",
    methods=["POST"]
)
@admin_required
def toggle_user(user_id):

    user = AdminUserService.get_user(
        user_id
    )

    AdminUserService.toggle_status(
        user
    )

    status = (

        "activated"

        if user.is_active

        else "deactivated"

    )

    flash(

        f"User {status} successfully.",

        "success"

    )

    return redirect(

        url_for(

            "admin.users"

        )

    )
# ==========================================================
# CATEGORY MANAGEMENT
# ==========================================================

@admin.route("/admin/categories")
@admin_required
def categories():

    categories = CategoryService.get_all()

    return render_template(

        "admin/categories.html",

        categories=categories

    )


# ==========================================================
# ADD CATEGORY
# ==========================================================

@admin.route(
    "/admin/category/add",
    methods=["GET", "POST"]
)
@admin_required
def add_category():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        success, message = CategoryService.create(

            name,

            description

        )

        flash(

            message,

            "success" if success else "danger"

        )

        if success:

            return redirect(

                url_for(

                    "admin.categories"

                )

            )

    return render_template(

        "admin/add_category.html"

    )


# ==========================================================
# EDIT CATEGORY
# ==========================================================

@admin.route(
    "/admin/category/edit/<int:category_id>",
    methods=["GET", "POST"]
)
@admin_required
def edit_category(category_id):

    category = CategoryService.get(
        category_id
    )

    if request.method == "POST":

        success, message = CategoryService.update(

            category,

            request.form.get(
                "name",
                ""
            ).strip(),

            request.form.get(
                "description",
                ""
            ).strip()

        )

        flash(

            message,

            "success" if success else "danger"

        )

        if success:

            return redirect(

                url_for(

                    "admin.categories"

                )

            )

    return render_template(

        "admin/edit_category.html",

        category=category

    )


# ==========================================================
# DELETE CATEGORY
# ==========================================================

@admin.route(
    "/admin/category/delete/<int:category_id>",
    methods=["POST"]
)
@admin_required
def delete_category(category_id):

    success, message = CategoryService.delete(
        category_id
    )

    flash(

        message,

        "success" if success else "danger"

    )

    return redirect(

        url_for(

            "admin.categories"

        )

    )