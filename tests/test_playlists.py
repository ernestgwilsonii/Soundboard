"""Tests for playlist models and logic."""

import os
import sqlite3

import pytest

from app import create_app
from app.models import Playlist, Sound, Soundboard, User
from config import Config


@pytest.fixture
def app_context(monkeypatch):
    """
    App context fixture with temporary databases.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    accounts_db = os.path.abspath("test_accounts_playlists.sqlite3")
    soundboards_db = os.path.abspath("test_soundboards_playlists.sqlite3")

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


def test_playlist_crud(app_context):
    """Test Create, Read, Update, and Delete operations for Playlist."""
    with app_context.app_context():
        u = User(username="pl_user", email="pl@example.com")
        u.set_password("p")
        u.save()
        assert u.id is not None

        # Create
        pl = Playlist(user_id=u.id, name="Chill Mix", description="Vibes")
        pl.save()
        pl_id = pl.id
        assert pl_id is not None

        # Read
        pl_loaded = Playlist.get_by_id(pl_id)
        assert pl_loaded is not None
        assert pl_loaded.name == "Chill Mix"

        # Update
        pl_loaded.name = "Party Mix"
        pl_loaded.save()
        updated_pl = Playlist.get_by_id(pl_id)
        assert updated_pl is not None
        assert updated_pl.name == "Party Mix"

        # List by user
        pls = Playlist.get_by_user_id(u.id)
        assert len(pls) == 1

        # Delete
        pl_loaded.delete()
        assert Playlist.get_by_id(pl_id) is None


def test_playlist_items(app_context):
    """Test adding and removing sounds from a playlist."""
    with app_context.app_context():
        u = User(username="item_user", email="i@example.com")
        u.set_password("p")
        u.save()
        assert u.id is not None

        sb = Soundboard(name="B", user_id=u.id, is_public=True)
        sb.save()
        assert sb.id is not None

        s1 = Sound(soundboard_id=sb.id, name="S1", file_path="1.mp3")
        s1.save()
        assert s1.id is not None
        s2 = Sound(soundboard_id=sb.id, name="S2", file_path="2.mp3")
        s2.save()
        assert s2.id is not None

        pl = Playlist(user_id=u.id, name="PL")
        pl.save()
        assert pl.id is not None

        # Add items
        pl.add_sound(s1.id)
        pl.add_sound(s2.id)

        sounds = pl.get_sounds()
        assert len(sounds) == 2
        assert sounds[0].name == "S1"
        assert sounds[1].name == "S2"

        # Remove item
        pl.remove_sound(s1.id)
        remaining_sounds = pl.get_sounds()
        assert len(remaining_sounds) == 1
        assert remaining_sounds[0].name == "S2"
