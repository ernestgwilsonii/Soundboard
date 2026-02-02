"""Decorators for authentication and authorization."""

from functools import wraps
from typing import Any, Callable

from flask import flash, redirect, url_for
from flask_login import current_user

from app.enums import UserRole
from app.models import User


def admin_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to ensure the current user is an administrator.

    Redirects to index if not authenticated or not an admin.
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        """Wrapper to perform the check."""
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            flash("You do not have permission to access this page.")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)

    return decorated_function


def verification_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to ensure the current user has verified their email.

    Redirects to login if not authenticated, or profile if not verified.
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        """Wrapper to perform the check."""
        from flask import current_app

        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

        # In testing mode, the DB might update behind the server's back.
        # Force a refresh of the verified status if needed.
        if not current_user.is_verified and current_app.config.get("TESTING"):
            user_from_db = User.get_by_id(current_user.id)
            if user_from_db and user_from_db.is_verified:
                current_user.is_verified = True

        if not current_user.is_verified:
            flash("Please verify your email address to access this feature.")
            return redirect(url_for("auth.profile"))
        return f(*args, **kwargs)

    return decorated_function
