
from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo


class PasswordResetForm(FlaskForm):

    new_password = PasswordField(
        "New Password",
        validators=[
            DataRequired(message="Please enter a new password."),
            Length(
                min=8,
                max=128,
                message="Password must be between 8 and 128 characters."
            )
        ]
    )

    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(message="Please confirm the new password."),
            EqualTo(
                "new_password",
                message="The passwords do not match."
            )
        ]
    )

    submit = SubmitField("Reset Password")
