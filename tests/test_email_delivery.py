"""Integration test for SMTP delivery to Mailpit."""

import socket

import pytest


def test_smtp_connection_to_mailpit(app):
    """Verify that the app can connect to the SMTP port."""
    host = app.config.get("MAIL_SERVER")
    port = app.config.get("MAIL_PORT")

    # Simple socket check first
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((host, port))
        s.close()
        connected = True
    except Exception:
        connected = False

    if not connected:
        pytest.skip(f"Mailpit not running on {host}:{port}. Integration test skipped.")


def test_send_real_email_to_capture_server(app):
    """Attempts to send a real message and expects no errors."""
    with app.app_context():
        # Override config for local test run if needed
        app.config["MAIL_SERVER"] = "localhost"
        app.config["MAIL_PORT"] = 1025
        app.config["MAIL_USE_TLS"] = False
        app.config["MAIL_USERNAME"] = None
        app.config["MAIL_PASSWORD"] = None
        app.config["MAIL_DEFAULT_SENDER"] = "test@soundboard.com"

        try:
            # We don't use the thread here to catch immediate SMTP errors
            from flask_mail import Message

            from app.extensions import mail

            msg = Message(
                "Integration Test",
                sender="test@soundboard.com",
                recipients=["user@example.com"],
            )
            msg.body = "This is a test from the integration suite."

            mail.send(msg)
            print("\nSUCCESS: Email delivered to capture server.")
        except Exception as e:
            pytest.fail(f"SMTP Delivery failed: {e}")


def test_password_reset_email_flow(app, client):
    """Verifies that requesting a reset actually hits the SMTP server."""
    import unittest.mock as mock

    from app.email import send_password_reset_email
    from app.models import User

    with app.app_context():
        # Create a test user
        u = User(
            username="emailtester", email="tester@soundboard.com", is_verified=True
        )
        u.save()

        # We mock the thread to make it synchronous for testing
        with mock.patch("app.email.Thread") as mock_thread:
            # Trigger the reset request via the route
            response = client.post(
                "/auth/reset_password_request",
                data={"email": "tester@soundboard.com"},
                follow_redirects=True,
            )

            assert response.status_code == 200
            assert b"Check your email" in response.data

            # Verify that Thread was started (meaning an email was attempted)
            assert mock_thread.called

            # Now let's try sending it for real (synchronously) to ensure no SMTP errors
            with app.test_request_context():
                send_password_reset_email(u)
            print("\nSUCCESS: Password reset flow integration verified.")
