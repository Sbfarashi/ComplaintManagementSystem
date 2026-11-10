from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash
)

from decorators.auth import login_required
from services.notification_service import NotificationService

notification = Blueprint(
    "notification",
    __name__
)


# ==========================================================
# ALL NOTIFICATIONS
# ==========================================================

@notification.route("/notifications")
@login_required
def notifications():

    notifications = NotificationService.get_notifications(

        session["user_id"]

    )

    unread = NotificationService.unread_count(

        session["user_id"]

    )

    return render_template(

        "notification/index.html",

        notifications=notifications,

        unread=unread

    )


# ==========================================================
# MARK AS READ
# ==========================================================

@notification.route(
    "/notification/read/<int:notification_id>"
)
@login_required
def mark_read(notification_id):

    NotificationService.mark_as_read(

        notification_id

    )

    flash(

        "Notification marked as read.",

        "success"

    )

    return redirect(

        url_for(

            "notification.notifications"

        )

    )


# ==========================================================
# MARK ALL AS READ
# ==========================================================

@notification.route(
    "/notification/read-all"
)
@login_required
def mark_all_read():

    NotificationService.mark_all_as_read(

        session["user_id"]

    )

    flash(

        "All notifications marked as read.",

        "success"

    )

    return redirect(

        url_for(

            "notification.notifications"

        )

    )


# ==========================================================
# DELETE
# ==========================================================

@notification.route(
    "/notification/delete/<int:notification_id>"
)
@login_required
def delete_notification(notification_id):

    NotificationService.delete(

        notification_id

    )

    flash(

        "Notification deleted.",

        "success"

    )

    return redirect(

        url_for(

            "notification.notifications"

        )

    )