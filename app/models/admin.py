"""Administrative settings models."""

from __future__ import annotations

from typing import Any, Dict

from app.db import get_accounts_db


class AdminSettings:
    """Manages global application settings stored in the database."""

    @staticmethod
    def get_setting(key: str, default: Any = None) -> Any:
        """
        Retrieve a setting value by key.

        Args:
            key (str): The setting key.
            default (any, optional): Default value if key not found.

        Returns:
            any: The setting value or default.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "SELECT value FROM admin_settings WHERE key = ?", (key,)
        )
        row = database_cursor.fetchone()
        if row:
            return row["value"]
        return default

    @staticmethod
    def get_all_settings() -> Dict[str, Any]:
        """Retrieve all settings as a dictionary."""
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute("SELECT key, value FROM admin_settings")
        rows = database_cursor.fetchall()
        return {row["key"]: row["value"] for row in rows}

    @staticmethod
    def set_setting(key: str, value: Any) -> None:
        """
        Set or update a setting value.

        Args:
            key (str): The setting key.
            value (any): The value to store.
        """
        database_connection = get_accounts_db()
        database_cursor = database_connection.cursor()
        database_cursor.execute(
            "INSERT INTO admin_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        database_connection.commit()
