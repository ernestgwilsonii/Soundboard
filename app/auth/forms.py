import sqlite3

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from config import Config


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=64)]
    )
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=3)])
    password_confirm = PasswordField(
        "Repeat Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Register")

    def validate_username(self, username):
        with sqlite3.connect(Config.ACCOUNTS_DB) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username = ?", (username.data,))
            if cur.fetchone():
                raise ValidationError(
                    "This username is already taken. Please choose another."
                )

    def validate_email(self, email):
        with sqlite3.connect(Config.ACCOUNTS_DB) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE email = ?", (email.data,))
            if cur.fetchone():
                raise ValidationError("This email address is already registered.")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class UpdateProfileForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    avatar = FileField(
        "Update Profile Picture",
        validators=[FileAllowed(["jpg", "png", "jpeg"], "Images only!")],
    )
    bio = StringField("Bio", validators=[Length(max=250)])
    social_x = StringField("X (Twitter) URL", validators=[Length(max=255)])
    social_youtube = StringField("YouTube URL", validators=[Length(max=255)])
    social_website = StringField("Personal Website", validators=[Length(max=255)])
    submit = SubmitField("Update Profile")

    def validate_email(self, email):
        from flask_login import current_user

        if email.data != current_user.email:
            with sqlite3.connect(Config.ACCOUNTS_DB) as conn:
                cur = conn.cursor()
                cur.execute("SELECT id FROM users WHERE email = ?", (email.data,))
                if cur.fetchone():
                    raise ValidationError(
                        "This email address is already in use by another account."
                    )


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Current Password", validators=[DataRequired()])
    password = PasswordField("New Password", validators=[DataRequired(), Length(min=3)])
    password_confirm = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Change Password")


class PasswordResetRequestForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired(), Length(min=3)])
    password_confirm = PasswordField(
        "Repeat Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Reset Password")


class DeleteAccountForm(FlaskForm):
    confirmation = StringField('Type "DELETE" to confirm', validators=[DataRequired()])
    submit = SubmitField("Permanently Delete My Account")

    def validate_confirmation(self, field):
        if field.data != "DELETE":
            raise ValidationError("You must type DELETE to confirm.")
