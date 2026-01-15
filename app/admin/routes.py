"""
Administrator routes.

This module handles administrative tasks such as user management,
system settings, and soundboard moderation.
"""

from typing import Any

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.admin import bp
from app.auth.routes import admin_required
from app.enums import UserRole
from app.models import AdminSettings, Soundboard, User


@bp.route("/users")  # type: ignore
@admin_required  # type: ignore
def users() -> Any:
    """
    Render the user management page.

    Displays all users sorted alphabetically.
    """
    # Admin view still shows all users, but sorted alphabetically by default
    users_list = User.get_all(limit=1000, sort_by="alpha")
    return render_template(
        "admin/users.html", title="User Management", users=users_list
    )


@bp.route("/settings", methods=["GET", "POST"])  # type: ignore
@admin_required  # type: ignore
def settings() -> Any:
    """
    Handle global platform settings.

    Allows admins to change featured soundboard, announcement, and maintenance mode.
    """
    from app.admin.forms import PlatformSettingsForm

    form = PlatformSettingsForm()
    if form.validate_on_submit():
        AdminSettings.set_setting(
            "featured_soundboard_id", form.featured_soundboard_id.data
        )
        AdminSettings.set_setting(
            "announcement_message", form.announcement_message.data
        )
        AdminSettings.set_setting("announcement_type", form.announcement_type.data)
        AdminSettings.set_setting(
            "maintenance_mode", "1" if form.maintenance_mode.data else "0"
        )
        flash("Settings updated.")
        return redirect(url_for("admin.settings"))
    elif request.method == "GET":
        form.featured_soundboard_id.data = AdminSettings.get_setting(
            "featured_soundboard_id"
        )
        form.announcement_message.data = AdminSettings.get_setting(
            "announcement_message"
        )
        form.announcement_type.data = (
            AdminSettings.get_setting("announcement_type") or "info"
        )
        form.maintenance_mode.data = (
            AdminSettings.get_setting("maintenance_mode") == "1"
        )

    return render_template("admin/settings.html", title="Admin Settings", form=form)


@bp.route("/soundboards")  # type: ignore
@admin_required  # type: ignore
def soundboards() -> Any:
    """
    Render the soundboard management page.

    Lists all soundboards for moderation.
    """
    all_soundboards = Soundboard.get_all()
    return render_template(
        "admin/soundboards.html",
        title="Content Management",
        soundboards=all_soundboards,
    )


@bp.route("/user/<int:id>/toggle_active", methods=["POST"])  # type: ignore
@admin_required  # type: ignore
def toggle_user_active(id: int) -> Any:
    """
    Toggle a user's active status (enable/disable account).

    Args:
        id (int): The user ID.
    """
    user = User.get_by_id(id)
    if user is None:
        flash("User not found.")
        return redirect(url_for("admin.users"))
    if user.id == current_user.id:
        flash("You cannot disable your own account!")
        return redirect(url_for("admin.users"))

    user.active = not user.active
    user.save()
    status = "enabled" if user.active else "disabled"
    flash(f"User {user.username} has been {status}.")
    return redirect(url_for("admin.users"))


@bp.route("/user/<int:id>/toggle_role", methods=["POST"])  # type: ignore
@admin_required  # type: ignore
def toggle_user_role(id: int) -> Any:
    """
    Toggle a user's role between USER and ADMIN.

    Args:
        id (int): The user ID.
    """
    user = User.get_by_id(id)
    if user is None:
        flash("User not found.")
        return redirect(url_for("admin.users"))
    if user.id == current_user.id:
        flash("You cannot change your own role!")
        return redirect(url_for("admin.users"))

    user.role = UserRole.ADMIN if user.role == UserRole.USER else UserRole.USER
    user.save()
    flash(f"User {user.username} role changed to {user.role}.")
    return redirect(url_for("admin.users"))


@bp.route("/user/<int:id>/toggle_verified", methods=["POST"])  # type: ignore
@admin_required  # type: ignore
def toggle_user_verified(id: int) -> Any:
    """
    Toggle a user's email verification status.

    Args:
        id (int): The user ID.
    """
    user = User.get_by_id(id)
    if user is None:
        flash("User not found.")
        return redirect(url_for("admin.users"))

    user.is_verified = not user.is_verified
    user.save()
    status = "verified" if user.is_verified else "unverified"
    flash(f"User {user.username} is now {status}.")
    return redirect(url_for("admin.users"))


@bp.route("/user/<int:id>/reset_password", methods=["GET", "POST"])  # type: ignore
@admin_required  # type: ignore
def reset_password(id: int) -> Any:
    """
    Manually reset a user's password.

    Args:
        id (int): The user ID.
    """
    from app.admin.forms import AdminPasswordResetForm

    user = User.get_by_id(id)
    if user is None:
        flash("User not found.")
        return redirect(url_for("admin.users"))

    form = AdminPasswordResetForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.save()
        flash(f"Password for {user.username} has been reset.")
        return redirect(url_for("admin.users"))
    return render_template(
        "admin/reset_password.html", title="Reset Password", form=form, user=user
    )


@bp.route("/user/<int:id>/update_email", methods=["GET", "POST"])  # type: ignore
@admin_required  # type: ignore
def update_email(id: int) -> Any:
    """
    Manually update a user's email address.

    Args:
        id (int): The user ID.
    """
    from app.admin.forms import AdminUpdateEmailForm

    user = User.get_by_id(id)
    if user is None:
        flash("User not found.")
        return redirect(url_for("admin.users"))

    assert user.id is not None
    form = AdminUpdateEmailForm(user_id=user.id)
    if form.validate_on_submit():
        user.email = form.email.data
        user.save()
        flash(f"Email for {user.username} has been updated.")
        return redirect(url_for("admin.users"))
    elif request.method == "GET":
        form.email.data = user.email
    return render_template(
        "admin/update_email.html", title="Update Email", form=form, user=user
    )
