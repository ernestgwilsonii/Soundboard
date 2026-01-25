"""Administrative settings models."""

from __future__ import annotations

from typing import Any, Dict

from app.extensions import db_orm as db
from app.models.base import BaseModel


class AdminSettings(BaseModel):
    """Manages global application settings stored in the database."""

    __tablename__ = "admin_settings"

    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Text)

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
        setting = db.session.get(AdminSettings, key)
        return setting.value if setting else default

    @staticmethod
    def get_all_settings() -> Dict[str, Any]:
        """Retrieve all settings as a dictionary."""
        settings = AdminSettings.query.all()
        return {s.key: s.value for s in settings}

    @staticmethod
    def set_setting(key: str, value: Any) -> None:
        """
        Set or update a setting value.

        Args:
            key (str): The setting key.
            value (any): The value to store.
        """
        # Ensure value is string if stored as Text (SQLite is loose, but let's be safe)
        if value is not None and not isinstance(value, str):
            value = str(value)

        setting = db.session.get(AdminSettings, key)
        if setting:
            setting.value = value
        else:
            setting = AdminSettings(key=key, value=value)
            db.session.add(setting)
        db.session.commit()
