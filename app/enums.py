"""Enumerations for the application."""

from enum import Enum

try:
    from enum import StrEnum
except ImportError:

    class StrEnum(str, Enum):
        """String enum backport."""

        def __str__(self) -> str:
            return str(self.value)


class UserRole(StrEnum):
    """User roles."""

    ADMIN = "admin"
    USER = "user"


class Visibility(StrEnum):
    """Resource visibility."""

    PUBLIC = "public"
    PRIVATE = "private"
