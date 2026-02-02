"""Collaborator management routes."""

from typing import Any

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required

from app.enums import UserRole
from app.models import BoardCollaborator, Notification, Soundboard, User
from app.socket_events import send_instant_notification


def register_collaborator_routes(bp: Any) -> None:
    """Register collaborator management routes on the blueprint."""

    @bp.route("/<int:id>/collaborators/add", methods=["POST"])  # type: ignore
    @login_required  # type: ignore
    def add_collaborator(id: int) -> Any:
        """
        Add a collaborator to a soundboard.

        Args:
            id (int): The soundboard ID.
        """
        soundboard = Soundboard.get_by_id(id)
        if soundboard is None:
            flash("Soundboard not found.")
            return redirect(url_for("soundboard.dashboard"))

        if (
            soundboard.user_id != current_user.id
            and current_user.role != UserRole.ADMIN
        ):
            flash("Permission denied.")
            return redirect(url_for("soundboard.dashboard"))

        username = request.form.get("username")
        assert username is not None
        user = User.get_by_username(username)
        if user is None:
            flash("User not found.")
            return redirect(url_for("soundboard.edit", id=soundboard.id))

        assert user.id is not None
        assert soundboard.id is not None
        if user.id == soundboard.user_id:
            flash("Owner is already a collaborator.")
            return redirect(url_for("soundboard.edit", id=soundboard.id))

        existing = BoardCollaborator.get_by_user_and_board(user.id, soundboard.id)
        if existing:
            flash("User is already a collaborator.")
            return redirect(url_for("soundboard.edit", id=soundboard.id))

        assert soundboard.id is not None
        assert user.id is not None
        collab = BoardCollaborator(
            soundboard_id=soundboard.id, user_id=user.id, role="editor"
        )
        collab.save()

        # Notify user
        notification_message = (
            f'{current_user.username} invited you to collaborate on "{soundboard.name}"'
        )
        link = url_for("soundboard.view", id=soundboard.id)
        Notification.add(user.id, "collab_invite", notification_message, link)
        send_instant_notification(user.id, notification_message, link)

        flash(f"{username} added as collaborator.")
        return redirect(url_for("soundboard.edit", id=soundboard.id))

    @bp.route("/collaborators/<int:id>/delete", methods=["POST"])  # type: ignore
    @login_required  # type: ignore
    def delete_collaborator(id: int) -> Any:
        """
        Remove a collaborator from a soundboard.

        Args:
            id (int): The user ID of the collaborator (from URL).
        """
        u_id_raw = request.form.get("user_id")
        b_id_raw = request.form.get("board_id")
        assert u_id_raw is not None
        assert b_id_raw is not None
        user_id = int(u_id_raw)
        board_id = int(b_id_raw)

        collab = BoardCollaborator.get_by_user_and_board(user_id, board_id)

        if collab is None:
            flash("Collaborator not found.")
            return redirect(url_for("soundboard.dashboard"))

        assert collab.soundboard_id is not None
        soundboard = Soundboard.get_by_id(collab.soundboard_id)
        assert soundboard is not None
        assert current_user.id is not None
        if (
            soundboard.user_id != current_user.id
            and current_user.role != UserRole.ADMIN
        ):
            flash("Permission denied.")
            return redirect(url_for("soundboard.dashboard"))

        collab.delete()
        flash("Collaborator removed.")
        assert soundboard.id is not None
        return redirect(url_for("soundboard.edit", id=soundboard.id))
