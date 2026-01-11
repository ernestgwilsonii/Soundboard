"""Administrative settings models."""

from __future__ import annotations

from typing import Any

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
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute("SELECT value FROM admin_settings WHERE key = ?", (key,))
        row = cur.fetchone()
        if row:
            return row["value"]
        return default

    @staticmethod
    def set_setting(key: str, value: Any) -> None:
        """
        Set or update a setting value.

        Args:
            key (str): The setting key.
            value (any): The value to store.
        """
        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO admin_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        db.commit()
