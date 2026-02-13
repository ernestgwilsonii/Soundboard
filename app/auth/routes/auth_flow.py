"""Authentication flow routes."""

from typing import Any

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app import limiter
from app.auth.forms import LoginForm, RegistrationForm
from app.constants import LOGIN_LIMIT, REGISTRATION_LIMIT
from app.enums import UserRole
from app.models import Activity, User


def register_auth_flow_routes(bp: Any) -> None:
    """Register auth flow routes on the blueprint."""

    @bp.route("/login", methods=["GET", "POST"])  # type: ignore
    @limiter.limit(LOGIN_LIMIT)  # type: ignore
    def login() -> Any:
        """
        Handle user login.

        Validates credentials, checks for account lockout, and redirects to the next page.
        """
        from urllib.parse import urlparse

        from flask_login import login_user

        if current_user.is_authenticated:
            return redirect(url_for("main.index"))

        form = LoginForm()
        if not form.validate_on_submit():
            return render_template("auth/login.html", title="Sign In", form=form)

        # Support login by username or email
        user = User.get_by_username(form.username.data) or User.get_by_email(
            form.username.data
        )

        if user is None:
            flash("Invalid username or password")
            return redirect(url_for("auth.login"))

        if user.is_locked():
            flash(
                f"Account is locked due to too many failed attempts. Please try again after {user.lockout_until}."
            )
            return redirect(url_for("auth.login"))

        if not user.check_password(form.password.data):
            user.increment_failed_attempts()
            flash("Invalid username or password")
            return redirect(url_for("auth.login"))

        user.reset_failed_attempts()
        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get("next")
        if not next_page or urlparse(next_page).netloc != "":
            next_page = url_for("main.index")

        return redirect(next_page)

    @bp.route("/logout")  # type: ignore
    def logout() -> Any:
        """Log out the current user and redirect to the index page."""
        from flask_login import logout_user

        logout_user()
        return redirect(url_for("main.index"))

    @bp.route("/register", methods=["GET", "POST"])  # type: ignore
    @limiter.limit(REGISTRATION_LIMIT)  # type: ignore
    def register() -> Any:
        """
        Handle user registration.

        Creates a new user, sends a verification email, and sets the first user as admin.
        """
        from app.email import send_verification_email

        if current_user.is_authenticated:
            return redirect(url_for("main.index"))

        form = RegistrationForm()
        if not form.validate_on_submit():
            if request.method == "POST":
                current_app.logger.debug(f"Registration form errors: {form.errors}")
            return render_template("auth/signup.html", title="Register", form=form)

        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)

        # Expert Logic: The very first user is automatically an Administrator and Verified
        if User.count_all() == 0:
            user.role = UserRole.ADMIN
            user.is_verified = True
            flash(
                "Welcome! As the first user, you have been promoted to Administrator."
            )
        else:
            user.is_verified = False

        user.save()

        assert user.id is not None
        Activity.record(user.id, "registration", "Joined the community!")

        send_verification_email(user)
        flash(
            "Congratulations, you are now a registered user! Please check your email to verify your account."
        )
        return redirect(url_for("auth.login"))

    @bp.route("/google_login_success")  # type: ignore
    def google_login_success() -> Any:
        """Helper route to redirect after successful Google login."""
        return redirect(url_for("main.index"))
