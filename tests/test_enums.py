"""Tests for application enums."""

from app.enums import UserRole, Visibility


def test_user_role_enum():
    """Verify UserRole enum values."""
    assert UserRole.ADMIN == "admin"
    assert UserRole.USER == "user"
    assert str(UserRole.ADMIN) == "admin"


def test_visibility_enum():
    """Verify Visibility enum values."""
    assert Visibility.PUBLIC == "public"
    assert Visibility.PRIVATE == "private"
    assert str(Visibility.PUBLIC) == "public"
