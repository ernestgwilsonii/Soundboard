"""Enumerations for the application."""

from enum import Enum

try:
    from enum import StrEnum
except ImportError:

    class StrEnum(str, Enum):
        """String enum backport."""

        pass


class UserRole(StrEnum):
    """User roles."""

    ADMIN = "admin"
    USER = "user"


class Visibility(StrEnum):
    """Resource visibility."""

    PUBLIC = "public"
    PRIVATE = "private"
