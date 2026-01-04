import os
import sqlite3

import pytest

from app import create_app
from app.models import Soundboard, User
from config import Config


@pytest.fixture
def client(monkeypatch):
    accounts_db = os.path.abspath("test_accounts_email.sqlite3")
    soundboards_db = os.path.abspath("test_soundboards_email.sqlite3")

    monkeypatch.setattr(Config, "ACCOUNTS_DB", accounts_db)
    monkeypatch.setattr(Config, "SOUNDBOARDS_DB", soundboards_db)

    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    for db_path in [accounts_db, soundboards_db]:
        if os.path.exists(db_path):
            os.remove(db_path)

    with app.app_context():
        with sqlite3.connect(accounts_db) as conn:
            with open("app/schema_accounts.sql", "r") as f:
                conn.executescript(f.read())
        with sqlite3.connect(soundboards_db) as conn:
            with open("app/schema_soundboards.sql", "r") as f:
                conn.executescript(f.read())
        yield app.test_client()

    for db_path in [accounts_db, soundboards_db]:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_unverified_user_restrictions(client):
    with client.application.app_context():
        u = User(username="unverified", email="un@example.com", is_verified=False)
        u.set_password("pass")
        u.save()

    client.post(
        "/auth/login",
        data={"username": "unverified", "password": "pass", "submit": "Sign In"},
    )

    # Try to create soundboard
    response = client.get("/soundboard/create", follow_redirects=True)
    assert b"Please verify your email address" in response.data

    # Verify profile still accessible
    response = client.get("/auth/profile")
    assert response.status_code == 200


def test_verification_flow(client):
    with client.application.app_context():
        u = User(username="verify_me", email="v@example.com", is_verified=False)
        u.set_password("pass")
        u.save()
        token = u.get_token(salt="email-verify")

    # Verify with token
    response = client.get(f"/auth/verify/{token}", follow_redirects=True)
    assert b"Your account has been verified!" in response.data

    with client.application.app_context():
        u = User.get_by_username("verify_me")
        assert u.is_verified == True


def test_password_reset_flow(client):
    with client.application.app_context():
        u = User(username="reset_me", email="reset@example.com")
        u.set_password("oldpass")
        u.save()
        token = u.get_token(salt="password-reset")

    # Request reset
    response = client.post(
        "/auth/reset_password_request",
        data={"email": "reset@example.com"},
        follow_redirects=True,
    )
    assert b"Check your email" in response.data

    # Use token to reset
    response = client.post(
        f"/auth/reset_password/{token}",
        data={"password": "newpassword", "password_confirm": "newpassword"},
        follow_redirects=True,
    )
    assert b"Your password has been reset" in response.data

    # Verify login
    response = client.post(
        "/auth/login",
        data={"username": "reset_me", "password": "newpassword", "submit": "Sign In"},
        follow_redirects=True,
    )
    assert b"Logout" in response.data
