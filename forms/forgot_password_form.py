
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class ForgotPasswordForm(FlaskForm):

    email = StringField(
        "Registered Email Address",
        validators=[
            DataRequired(
                message="Please enter your email address."
            ),
            Email(
                message="Please enter a valid email address."
            ),
            Length(
                max=120,
                message="Email address is too long."
            )
        ]
    )

    submit = SubmitField("Submit Password Reset Request")
