"""Social and notification routes for auth blueprint."""

from typing import Any

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models import Activity, Notification, User


def register_social_routes(bp: Any) -> None:
    """Register social routes on the blueprint."""

    @bp.route("/notifications/mark_read", methods=["POST"])  # type: ignore
    @login_required  # type: ignore
    def mark_notifications_read() -> Any:
        """Mark all notifications as read for the current user."""
        assert current_user.id is not None
        Notification.mark_all_read(current_user.id)
        return jsonify({"status": "success"})

    @bp.route("/notifications/unread_count")  # type: ignore
    @login_required  # type: ignore
    def unread_notifications_count() -> Any:
        """
        Get the count and details of unread notifications.

        Returns:
            JSON: Dictionary with count and list of notification objects.
        """
        assert current_user.id is not None
        unread_notifications = Notification.get_unread_for_user(current_user.id)
        response_data = [
            {
                "message": notification.message,
                "link": notification.link or "#",
                "created_at": str(notification.created_at),
            }
            for notification in unread_notifications[:5]
        ]
        return jsonify(
            {"count": len(unread_notifications), "notifications": response_data}
        )

    @bp.route("/check-availability")  # type: ignore
    def check_availability() -> Any:
        """
        Check if a username or email is available.

        Query Args:
            username (str, optional): Username to check.
            email (str, optional): Email to check.

        Returns:
            JSON: Dictionary with 'available' boolean.
        """
        username = request.args.get("username")
        email = request.args.get("email")

        if username:
            user = User.get_by_username(username)
            return jsonify({"available": user is None})
        if email:
            user = User.get_by_email(email)
            return jsonify({"available": user is None})

        return jsonify({"error": "No field provided"}), 400

    @bp.route("/user/<username>/followers")  # type: ignore
    @login_required  # type: ignore
    def followers(username: str) -> Any:
        """
        Show list of followers for a specific user.

        Args:
            username (str): The username of the user.
        """
        user = User.get_by_username(username)
        if user is None:
            flash(f"User {username} not found.")
            return redirect(url_for("main.index"))
        users_list = user.get_followers()
        return render_template(
            "auth/members.html",
            title=f"Followers of {username}",
            users=users_list,
            heading=f"Followers of {username}",
        )

    @bp.route("/user/<username>/following")  # type: ignore
    @login_required  # type: ignore
    def following(username: str) -> Any:
        """
        Show list of users followed by a specific user.

        Args:
            username (str): The username of the user.
        """
        user = User.get_by_username(username)
        if user is None:
            flash(f"User {username} not found.")
            return redirect(url_for("main.index"))
        users_list = user.get_following()
        return render_template(
            "auth/members.html",
            title=f"Users {username} Follows",
            users=users_list,
            heading=f"Users {username} Follows",
        )

    @bp.route("/follow/<username>", methods=["POST"])  # type: ignore
    @login_required  # type: ignore
    def follow(username: str) -> Any:
        """
        Follow a user.

        Args:
            username (str): The username of the user to follow.
        """
        user = User.get_by_username(username)
        if user is None:
            flash(f"User {username} not found.")
            return redirect(url_for("main.index"))
        if user.id == current_user.id:
            flash("You cannot follow yourself!")
            return redirect(url_for("auth.public_profile", username=username))

        assert current_user.id is not None
        assert user.id is not None
        current_user.follow(user.id)

        Activity.record(current_user.id, "follow", f"Started following {username}")

        flash(f"You are now following {username}!")
        return redirect(url_for("auth.public_profile", username=username))

    @bp.route("/unfollow/<username>", methods=["POST"])  # type: ignore
    @login_required  # type: ignore
    def unfollow(username: str) -> Any:
        """
        Unfollow a user.

        Args:
            username (str): The username of the user to unfollow.
        """
        user = User.get_by_username(username)
        if user is None:
            flash(f"User {username} not found.")
            return redirect(url_for("main.index"))
        if user.id == current_user.id:
            flash("You cannot unfollow yourself!")
            return redirect(url_for("auth.public_profile", username=username))
        current_user.unfollow(user.id)
        flash(f"You have unfollowed {username}.")
        return redirect(url_for("auth.public_profile", username=username))
