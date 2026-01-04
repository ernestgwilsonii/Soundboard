import os
import sqlite3

import pytest

from app import create_app
from app.models import User
from config import Config


@pytest.fixture
def client(monkeypatch):
    accounts_db = os.path.abspath("test_accounts_login.sqlite3")
    soundboards_db = os.path.abspath("test_soundboards_login.sqlite3")

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

    with app.test_client() as client:
        yield client

    for db_path in [accounts_db, soundboards_db]:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_login_with_username_and_email(client):
    with client.application.app_context():
        u = User(username="testuser", email="test@example.com", is_verified=True)
        u.set_password("password")
        u.save()

    # Test login with username
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "password"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Logout" in response.data

    # Logout
    client.get("/auth/logout")

    # Test login with email
    response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "password"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Logout" in response.data
