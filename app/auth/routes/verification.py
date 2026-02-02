"""Email verification and password reset routes."""

from typing import Any

from flask import flash, redirect, render_template, url_for
from flask_login import current_user

from app.models import User


def register_verification_routes(bp: Any) -> None:
    """Register verification routes on the blueprint."""

    @bp.route("/verify/<token>")  # type: ignore
    def verify_email(token: str) -> Any:
        """
        Verify a user's email address using a token.

        Args:
            token (str): The verification token.
        """
        if current_user.is_authenticated:
            return redirect(url_for("main.index"))
        verified_user = User.verify_token(token, salt="email-verify")
        if verified_user:
            if verified_user.is_verified:
                flash("Account already verified.")
            else:
                verified_user.is_verified = True
                verified_user.save()
                flash("Your account has been verified!")
        else:
            flash("The confirmation link is invalid or has expired.")
        return redirect(url_for("auth.login"))

    @bp.route("/reset_password_request", methods=["GET", "POST"])  # type: ignore
    def reset_password_request() -> Any:
        """
        Handle requests for password reset.

        Sends an email with a reset link if the email exists.
        """
        from app.auth.forms import PasswordResetRequestForm
        from app.email import send_password_reset_email

        if current_user.is_authenticated:
            return redirect(url_for("main.index"))
        form = PasswordResetRequestForm()
        if form.validate_on_submit():
            user = User.get_by_email(form.email.data)
            if user:
                send_password_reset_email(user)
            flash("Check your email for the instructions to reset your password")
            return redirect(url_for("auth.login"))
        return render_template(
            "auth/reset_password_request.html", title="Reset Password", form=form
        )

    @bp.route("/reset_password/<token>", methods=["GET", "POST"])  # type: ignore
    def reset_password(token: str) -> Any:
        """
        Reset the user's password using a valid token.

        Args:
            token (str): The password reset token.
        """
        from app.auth.forms import ResetPasswordForm

        if current_user.is_authenticated:
            return redirect(url_for("main.index"))
        user_to_reset = User.verify_token(token, salt="password-reset")
        if not user_to_reset:
            flash("The reset link is invalid or has expired.")
            return redirect(url_for("main.index"))
        form = ResetPasswordForm()
        if form.validate_on_submit():
            user_to_reset.set_password(form.password.data)
            user_to_reset.save()
            flash("Your password has been reset.")
            return redirect(url_for("auth.login"))
        return render_template(
            "auth/reset_password.html", title="Reset Password", form=form
        )
