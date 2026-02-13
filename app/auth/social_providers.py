"""
Social Login Provider Registry.

This module manages the configuration and registration of social OAuth providers
(Google, etc.) using Flask-Dance.
"""

from flask import flash
from flask_dance.consumer import oauth_authorized
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_dance.contrib.google import google, make_google_blueprint
from flask_login import current_user, login_user

from app.extensions import db_orm
from app.models import Activity, User


def init_social_providers(app):
    """Initialize and register social login blueprints if configured."""
    # Google Configuration
    google_id = app.config.get("GOOGLE_OAUTH_CLIENT_ID")
    google_secret = app.config.get("GOOGLE_OAUTH_CLIENT_SECRET")

    if google_id and google_secret:
        google_bp = make_google_blueprint(
            client_id=google_id,
            client_secret=google_secret,
            scope=["profile", "email"],
            storage=SQLAlchemyStorage(User, db_orm.session, user=current_user),
            redirect_to="auth.google_login_success",
        )
        app.register_blueprint(google_bp, url_prefix="/auth/login")
        app.logger.info("Google OAuth provider registered.")


def get_google_user_info():
    """Helper to fetch user info from Google. Extracted for testability."""
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return None
    return resp.json()


@oauth_authorized.connect
def google_logged_in(blueprint, token):
    """Callback handled when Google OAuth authorization is successful."""
    if not token:
        flash("Failed to log in with Google.", "danger")
        return False

    google_info = get_google_user_info()
    if not google_info:
        flash("Failed to fetch user info from Google.", "danger")
        return False

    google_user_id = str(google_info["id"])
    email = google_info["email"]

    # 1. Try to find user by google_id
    user = User.query.filter_by(google_id=google_user_id).first()

    if user:
        login_user(user)
        Activity.record(user.id, "login", "Logged in via Google")
    else:
        # 2. Try to find user by email to link accounts
        user = User.get_by_email(email)
        if user:
            user.google_id = google_user_id
            user.save()
            login_user(user)
            flash(
                "Your Google account has been linked to your existing profile.", "info"
            )
            Activity.record(user.id, "login", "Logged in via Google (linked)")
        else:
            # 3. Create new user
            # Generate a unique username based on the first part of the email
            base_username = email.split("@")[0]
            username = base_username
            counter = 1
            while User.exists_by_username(username):
                username = f"{base_username}{counter}"
                counter += 1

            user = User(
                username=username,
                email=email,
                google_id=google_user_id,
                is_verified=True,  # OAuth emails are considered verified
            )
            user.save()
            login_user(user)
            flash("Welcome! Your account has been created via Google.", "success")
            Activity.record(user.id, "signup", "Signed up via Google")

    return False  # Disable default Flask-Dance storage behavior since we handled it
