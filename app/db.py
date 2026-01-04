import sqlite3

from flask import current_app, g

from config import Config


def get_accounts_db():
    if current_app.config.get("TESTING"):
        db = sqlite3.connect(
            current_app.config["ACCOUNTS_DB"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        db.row_factory = sqlite3.Row
        return db

    if "accounts_db" not in g:
        g.accounts_db = sqlite3.connect(
            current_app.config["ACCOUNTS_DB"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.accounts_db.row_factory = sqlite3.Row
    return g.accounts_db


def get_soundboards_db():
    if current_app.config.get("TESTING"):
        db = sqlite3.connect(
            current_app.config["SOUNDBOARDS_DB"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        db.row_factory = sqlite3.Row
        return db

    if "soundboards_db" not in g:
        g.soundboards_db = sqlite3.connect(
            current_app.config["SOUNDBOARDS_DB"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.soundboards_db.row_factory = sqlite3.Row
    return g.soundboards_db


def close_db(e=None):
    accounts_db = g.pop("accounts_db", None)
    if accounts_db is not None:
        accounts_db.close()

    soundboards_db = g.pop("soundboards_db", None)
    if soundboards_db is not None:
        soundboards_db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
