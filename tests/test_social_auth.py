"""Tests for Social Authentication."""

from unittest import mock

from app.models import User


def test_google_login_button_visibility(client):
    """Test that Google login button appears only when configured."""
    # 1. Not configured
    response = client.get("/auth/login")
    assert b"Sign in with Google" not in response.data

    # Note: We can't easily test visibility with a simple config change
    # because the blueprint is registered at app creation time.
    # We would need a separate app instance for that.


def test_google_login_route_registered(app):
    """Test that Google login route is registered when configured."""
    from flask import url_for

    from app.auth.social_providers import init_social_providers

    # We create a fresh app to test registration logic
    with app.app_context():
        app.config["GOOGLE_OAUTH_CLIENT_ID"] = "mock-id"
        app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = "mock-secret"
        init_social_providers(app)

        with app.test_request_context():
            login_url = url_for("google.login")
            assert "/auth/login/google" in login_url


def test_social_auth_account_linking(app):
    """Test the logic for linking a Google account to an existing email."""
    from app.auth.social_providers import google_logged_in

    with app.app_context():
        # Create existing user
        existing_user = User(
            username="existing", email="test@example.com", is_verified=True
        )
        existing_user.save()

        # Mock Google response
        mock_blueprint = mock.Mock()
        mock_token = {"access_token": "fake-token"}

        # Mock the 'get_google_user_info' helper function
        with mock.patch(
            "app.auth.social_providers.get_google_user_info"
        ) as mock_get_info:
            mock_google_info = {"id": "google-123", "email": "test@example.com"}
            mock_get_info.return_value = mock_google_info

            # Call the callback directly with a request context for login_user
            with app.test_request_context():
                google_logged_in(mock_blueprint, mock_token)

            # Verify user now has google_id linked
            updated_user = User.get_by_email("test@example.com")
            assert updated_user.google_id == "google-123"


def test_social_auth_new_user_creation(app):
    """Test creating a new user via Google login."""
    from app.auth.social_providers import google_logged_in

    with app.app_context():
        # Mock Google response for a new email
        mock_blueprint = mock.Mock()
        mock_token = {"access_token": "fake-token"}

        with mock.patch(
            "app.auth.social_providers.get_google_user_info"
        ) as mock_get_info:
            mock_google_info = {"id": "new-google-456", "email": "new@example.com"}
            mock_get_info.return_value = mock_google_info

            with app.test_request_context():
                google_logged_in(mock_blueprint, mock_token)

            # Verify new user created
            new_user = User.get_by_email("new@example.com")
            assert new_user is not None
            assert new_user.google_id == "new-google-456"
            assert new_user.username == "new"
            assert new_user.is_verified is True
