"""Database connection utilities."""

import sqlite3
from typing import Optional, cast

from flask import Flask, current_app, g


def get_accounts_db() -> sqlite3.Connection:
    """Get the accounts database connection."""
    if current_app.config.get("TESTING"):
        database_connection: sqlite3.Connection = sqlite3.connect(
            current_app.config["ACCOUNTS_DB"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        database_connection.row_factory = sqlite3.Row
        return database_connection

    if "accounts_db" not in g:
        g.accounts_db = sqlite3.connect(
            current_app.config["ACCOUNTS_DB"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.accounts_db.row_factory = sqlite3.Row
    return cast(sqlite3.Connection, g.accounts_db)


def get_soundboards_db() -> sqlite3.Connection:
    """Get the soundboards database connection."""
    if current_app.config.get("TESTING"):
        database_connection: sqlite3.Connection = sqlite3.connect(
            current_app.config["SOUNDBOARDS_DB"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        database_connection.row_factory = sqlite3.Row
        return database_connection

    if "soundboards_db" not in g:
        g.soundboards_db = sqlite3.connect(
            current_app.config["SOUNDBOARDS_DB"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.soundboards_db.row_factory = sqlite3.Row
    return cast(sqlite3.Connection, g.soundboards_db)


def close_db(exception: Optional[BaseException] = None) -> None:
    """Close database connections."""
    accounts_db = g.pop("accounts_db", None)
    if accounts_db is not None:
        accounts_db.close()

    soundboards_db = g.pop("soundboards_db", None)
    if soundboards_db is not None:
        soundboards_db.close()


def init_app(app: Flask) -> None:
    """Register database functions with the Flask app."""
    app.teardown_appcontext(close_db)
