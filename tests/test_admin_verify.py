import os
import sqlite3

import pytest

from app import create_app
from app.models import User
from config import Config


@pytest.fixture
def client(monkeypatch):
    accounts_db = os.path.abspath("test_accounts_admin_verify.sqlite3")
    soundboards_db = os.path.abspath("test_soundboards_admin_verify.sqlite3")

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


def test_admin_toggle_verify(client):
    with client.application.app_context():
        # Create admin
        admin = User(
            username="admin_v", email="admin_v@test.com", role="admin", is_verified=True
        )
        admin.set_password("admin")
        admin.save()

        # Create unverified user
        user = User(username="user_v", email="user_v@test.com", is_verified=False)
        user.set_password("user")
        user.save()
        assert user.id is not None
        user_id = user.id

    # Login as admin
    client.post("/auth/login", data={"username": "admin_v", "password": "admin"})

    # Toggle verification
    response = client.post(
        f"/admin/user/{user_id}/toggle_verified", follow_redirects=True
    )
    assert response.status_code == 200
    assert b"is now verified" in response.data

    with client.application.app_context():
        u = User.get_by_id(user_id)
        assert u is not None
        assert u.is_verified is True

    # Toggle back
    response = client.post(
        f"/admin/user/{user_id}/toggle_verified", follow_redirects=True
    )
    assert b"is now unverified" in response.data

    with client.application.app_context():
        u = User.get_by_id(user_id)
        assert u is not None
        assert u.is_verified is False
