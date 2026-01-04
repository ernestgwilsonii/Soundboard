import os
import sqlite3

import pytest

from app import create_app
from app.models import Sound, Soundboard, User
from config import Config


@pytest.fixture
def app_context(monkeypatch):
    accounts_db = os.path.abspath("test_accounts_reorder.sqlite3")
    soundboards_db = os.path.abspath("test_soundboards_reorder.sqlite3")

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
        yield app

    for db_path in [accounts_db, soundboards_db]:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_sound_default_ordering(app_context):
    with app_context.app_context():
        u = User(username="test", email="test@example.com")
        u.set_password("pass")
        u.save()

        sb = Soundboard(name="Order Board", user_id=u.id, is_public=True)
        sb.save()

        s1 = Sound(soundboard_id=sb.id, name="First", file_path="1/1.mp3")
        s1.save()
        assert s1.display_order == 1

        s2 = Sound(soundboard_id=sb.id, name="Second", file_path="1/2.mp3")
        s2.save()
        assert s2.display_order == 2

        # Verify retrieval order
        sounds = sb.get_sounds()
        assert sounds[0].name == "First"
        assert sounds[1].name == "Second"


def test_explicit_ordering(app_context):
    with app_context.app_context():
        u = User(username="test2", email="test2@example.com")
        u.set_password("pass")
        u.save()

        sb = Soundboard(name="Explicit Board", user_id=u.id, is_public=True)
        sb.save()

        # Create sounds with explicit swapped orders
        s1 = Sound(
            soundboard_id=sb.id, name="Later", file_path="1/1.mp3", display_order=10
        )
        s1.save()

        s2 = Sound(
            soundboard_id=sb.id, name="Earlier", file_path="1/2.mp3", display_order=5
        )
        s2.save()

        sounds = sb.get_sounds()
        assert sounds[0].name == "Earlier"
        assert sounds[1].name == "Later"


def test_reorder_api(app_context):
    client = app_context.test_client()
    from app.models import Sound, Soundboard, User

    with app_context.app_context():
        u = User(username="reorder", email="reorder@example.com")
        u.set_password("pass")
        u.save()

        from app.models import AdminSettings

        AdminSettings.set_setting("maintenance_mode", "0")

        sb = Soundboard(name="API Board", user_id=u.id, is_public=True)
        sb.save()

        s1 = Sound(soundboard_id=sb.id, name="S1", file_path="1/1.mp3")
        s1.save()
        s2 = Sound(soundboard_id=sb.id, name="S2", file_path="1/2.mp3")
        s2.save()

        sb_id = sb.id
        s1_id = s1.id
        s2_id = s2.id

    login_resp = client.post(
        "/auth/login",
        data={"username": "reorder", "password": "pass", "submit": "Sign In"},
        follow_redirects=True,
    )
    assert b"Logout" in login_resp.data

    # Send new order (S2 first)
    response = client.post(f"/soundboard/{sb_id}/reorder", json={"ids": [s2_id, s1_id]})
    assert response.status_code == 200

    with app_context.app_context():
        sb = Soundboard.get_by_id(sb_id)
        sounds = sb.get_sounds()
        assert sounds[0].id == s2_id
        assert sounds[1].id == s1_id
        assert sounds[0].display_order == 1
        assert sounds[1].display_order == 2


def test_playback_fields_persistence(app_context):
    with app_context.app_context():
        u = User(username="pb", email="pb@example.com")
        u.set_password("p")
        u.save()
        sb = Soundboard(name="PB Board", user_id=u.id, is_public=True)
        sb.save()

        s = Sound(
            soundboard_id=sb.id,
            name="S",
            file_path="1/1.mp3",
            volume=0.5,
            is_loop=True,
            start_time=1.5,
            end_time=10.0,
        )
        s.save()
        sid = s.id

    with app_context.app_context():
        s = Sound.get_by_id(sid)
        assert s.volume == 0.5
        assert s.is_loop == True
        assert s.start_time == 1.5
        assert s.end_time == 10.0
