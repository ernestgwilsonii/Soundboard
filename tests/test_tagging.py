import os
import sqlite3

import pytest

from app import create_app
from app.models import Soundboard, Tag, User
from config import Config


@pytest.fixture
def app_context(monkeypatch):
    accounts_db = os.path.abspath("test_accounts_tags.sqlite3")
    soundboards_db = os.path.abspath("test_soundboards_tags.sqlite3")

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


def test_tagging_logic(app_context):
    with app_context.app_context():
        u = User(username="tagger", email="t@example.com")
        u.set_password("p")
        u.save()

        sb = Soundboard(name="Tag Board", user_id=u.id, is_public=True)
        sb.save()

        # Add tags
        sb.add_tag("fun")
        sb.add_tag("meme ")  # Should be normalized

        tags = sb.get_tags()
        assert len(tags) == 2
        assert tags[0].name == "fun"
        assert tags[1].name == "meme"

        # Test popularity
        sb2 = Soundboard(name="Another Board", user_id=u.id, is_public=True)
        sb2.save()
        sb2.add_tag("fun")

        popular = Tag.get_popular()
        assert popular[0].name == "fun"

        # Remove tag
        sb.remove_tag("meme")
        assert len(sb.get_tags()) == 1
