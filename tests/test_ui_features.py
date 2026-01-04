import os
import sqlite3

import pytest

from app import create_app
from app.models import Soundboard, User
from config import Config


@pytest.fixture
def client(monkeypatch):
    accounts_db = os.path.abspath("test_accounts_ui.sqlite3")
    soundboards_db = os.path.abspath("test_soundboards_ui.sqlite3")

    monkeypatch.setattr(Config, "ACCOUNTS_DB", accounts_db)
    monkeypatch.setattr(Config, "SOUNDBOARDS_DB", soundboards_db)

    app = create_app()
    app.config["TESTING"] = True

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


def test_share_button_presence(client):
    with client.application.app_context():
        u = User(username="shareuser", email="share@example.com")
        u.set_password("pass")
        u.save()
        sb = Soundboard(name="Shareable Board", user_id=u.id, is_public=True)
        sb.save()
        sb_id = sb.id

    response = client.get(f"/soundboard/view/{sb_id}")
    assert b"Share" in response.data
    assert b"shareBoard()" in response.data
    assert b"share-toast" in response.data


def test_share_button_absence_private(client):
    with client.application.app_context():
        u = User(username="privateuser", email="private@example.com")
        u.set_password("pass")
        u.save()
        sb = Soundboard(name="Private Board", user_id=u.id, is_public=False)
        sb.save()
        sb_id = sb.id

    # Need to be logged in to view private board
    with client.application.app_context():
        # Mock login not needed if we just check page content?
        # No, view route redirects if private and not owner.
        pass

    # Login
    client.post(
        "/auth/login",
        data={"username": "privateuser", "password": "cat", "submit": "Sign In"},
    )  # Oh wait user has no password set in this test setup?
    # Let's fix user setup

    with client.application.app_context():
        u = User.get_by_username("privateuser")
        u.set_password("pass")
        u.save()

    client.post(
        "/auth/login",
        data={"username": "privateuser", "password": "pass", "submit": "Sign In"},
    )

    response = client.get(f"/soundboard/view/{sb_id}")
    assert b"Share" not in response.data
    assert b"shareBoard()" not in response.data
