"""Email sending utilities."""

from collections.abc import Sequence
from threading import Thread
from typing import TYPE_CHECKING, Any, cast

from flask import Flask, current_app, render_template
from flask_mail import Message

if TYPE_CHECKING:
    from app.models.user import User

from app import mail


def send_async_email(app: Flask, message: Message) -> None:
    """
    Send an email asynchronously.

    Args:
        app (Flask): The Flask application instance.
        message (Message): The message object to send.
    """
    with app.app_context():
        try:
            mail.send(message)
        except Exception:
            app.logger.exception("Failed to send email")


def send_email(
    subject: str,
    sender: str,
    recipients: Sequence[str],
    text_body: str,
    html_body: str,
) -> None:
    """
    Construct and send an email using a background thread.

    Args:
        subject (str): The email subject.
        sender (str): The sender email address.
        recipients (Sequence[str]): A list of recipient email addresses.
        text_body (str): The plain text body.
        html_body (str): The HTML body.
    """
    message = Message(subject, sender=sender, recipients=list(recipients))
    message.body = text_body
    message.html = html_body
    Thread(
        target=send_async_email,
        args=(cast(Any, current_app)._get_current_object(), message),
    ).start()


def send_verification_email(user: "User") -> None:
    """
    Send account verification email.

    Args:
        user (User): The user object.
    """
    token = user.get_token(salt="email-verify")
    send_email(
        "[Soundboard] Verify Your Account",
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
        recipients=[user.email] if user.email else [],
        text_body=render_template("email/verify_account.txt", user=user, token=token),
        html_body=render_template("email/verify_account.html", user=user, token=token),
    )


def send_password_reset_email(user: "User") -> None:
    """
    Send password reset email.

    Args:
        user (User): The user object.
    """
    token = user.get_token(salt="password-reset")
    send_email(
        "[Soundboard] Reset Your Password",
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
        recipients=[user.email] if user.email else [],
        text_body=render_template("email/reset_password.txt", user=user, token=token),
        html_body=render_template("email/reset_password.html", user=user, token=token),
    )
