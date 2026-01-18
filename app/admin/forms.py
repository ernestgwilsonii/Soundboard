"""Administrative forms."""

from typing import Any

from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError


class AdminPasswordResetForm(FlaskForm):
    """Form to reset a user's password as an admin."""

    password = PasswordField("New Password", validators=[DataRequired(), Length(min=3)])
    password_confirm = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Reset Password")


class AdminUpdateEmailForm(FlaskForm):
    """Form to update a user's email address as an admin."""

    email = StringField(
        "New Email", validators=[DataRequired(), Email(), Length(max=120)]
    )
    submit = SubmitField("Update Email")

    def __init__(self, user_id: int, *args: Any, **kwargs: Any) -> None:
        """Initialize the form with the user's ID."""
        super(AdminUpdateEmailForm, self).__init__(*args, **kwargs)
        self.user_id = user_id

    def validate_email(self, email: StringField) -> None:
        """Ensure the new email is not already taken by another user."""
        from app.models.user import User

        user_to_update = User.get_by_id(self.user_id)
        if user_to_update and email.data != user_to_update.email:
            if User.exists_by_email(email.data):
                raise ValidationError("This email is already in use by another user.")


class PlatformSettingsForm(FlaskForm):
    """Form to update platform settings."""

    featured_soundboard_id = StringField("Featured Soundboard ID")

    announcement_message = StringField("Announcement Banner Message")
    announcement_type = SelectField(
        "Banner Type",
        choices=[
            ("info", "Info (Blue)"),
            ("warning", "Warning (Yellow)"),
            ("danger", "Critical (Red)"),
            ("success", "Success (Green)"),
        ],
        default="info",
    )

    maintenance_mode = BooleanField("Enable Maintenance Mode")

    submit = SubmitField("Save Settings")
