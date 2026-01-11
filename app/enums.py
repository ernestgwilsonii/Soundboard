"""Enumerations for the application."""

from enum import StrEnum


class UserRole(StrEnum):
    """User roles."""

    ADMIN = "admin"
    USER = "user"


class Visibility(StrEnum):
    """Resource visibility."""

    PUBLIC = "public"
    PRIVATE = "private"
