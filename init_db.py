import os
import sqlite3

from config import Config


def init_db(accounts_db=None, soundboards_db=None):
    accounts_db = accounts_db or os.environ.get("ACCOUNTS_DB") or Config.ACCOUNTS_DB
    soundboards_db = (
        soundboards_db or os.environ.get("SOUNDBOARDS_DB") or Config.SOUNDBOARDS_DB
    )

    # Initialize Accounts Database
    print(f"Initializing accounts database at {accounts_db}...")
    with sqlite3.connect(accounts_db) as conn:
        with open("app/schema_accounts.sql", "r") as f:
            conn.executescript(f.read())

    # Initialize Soundboards Database
    print(f"Initializing soundboards database at {soundboards_db}...")
    with sqlite3.connect(soundboards_db) as conn:
        with open("app/schema_soundboards.sql", "r") as f:
            conn.executescript(f.read())

    print("Database initialization complete.")


if __name__ == "__main__":
    init_db()
