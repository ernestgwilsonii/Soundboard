"""Soundboard social routes."""

from typing import Any

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required

from app import limiter
from app.auth.decorators import verification_required
from app.constants import COMMENT_LIMIT, RATING_LIMIT
from app.enums import UserRole
from app.models import Activity, Comment, Notification, Rating, Soundboard
from app.socket_events import send_instant_notification
from app.soundboard.forms import CommentForm


def register_social_routes(bp: Any) -> None:
    """Register social routes on the blueprint."""

    @bp.route("/<int:id>/favorite", methods=["POST"])  # type: ignore
    @login_required  # type: ignore
    def toggle_favorite(id: int) -> Any:
        """
        Toggle favorite status for a soundboard.

        Args:
            id (int): The soundboard ID.

        Returns:
            JSON: Dictionary with 'is_favorite' status.
        """
        from flask import jsonify

        soundboard = Soundboard.get_by_id(id)
        if soundboard is None:
            return jsonify({"error": "Soundboard not found"}), 404

        if not soundboard.is_public:
            return jsonify({"error": "Cannot favorite private soundboards"}), 403

        favorites = current_user.get_favorites()
        if soundboard.id in favorites:
            current_user.remove_favorite(soundboard.id)
            is_favorite = False
        else:
            current_user.add_favorite(soundboard.id)
            is_favorite = True

        return jsonify({"status": "success", "is_favorite": is_favorite})

    @bp.route("/<int:id>/rate", methods=["POST"])  # type: ignore
    @login_required  # type: ignore
    @limiter.limit(RATING_LIMIT)  # type: ignore
    def rate_board(id: int) -> Any:
        """
        Submit a rating for a soundboard.

        Args:
            id (int): The soundboard ID.

        Returns:
            JSON: Dictionary with status and updated rating stats.
        """
        from flask import jsonify

        soundboard = Soundboard.get_by_id(id)
        if soundboard is None:
            return jsonify({"error": "Soundboard not found"}), 404

        if not soundboard.is_public:
            return jsonify({"error": "Cannot rate private soundboards"}), 403

        data = request.get_json()
        if not data or "score" not in data:
            return jsonify({"error": "Score required"}), 400

        score = int(data["score"])
        if score < 1 or score > 5:
            return jsonify({"error": "Score must be between 1 and 5"}), 400

        assert current_user.id is not None
        assert soundboard.id is not None
        rating = Rating(
            user_id=current_user.id, soundboard_id=soundboard.id, score=score
        )
        rating.save()

        Activity.record(
            current_user.id, "rate_board", f'Rated "{soundboard.name}" {score} stars'
        )

        # Notify owner (if not same person)
        if soundboard.user_id != current_user.id:
            notification_message = f'{current_user.username} rated your soundboard "{soundboard.name}" {score} stars.'
            link = url_for("soundboard.view", id=soundboard.id)
            assert soundboard.user_id is not None
            Notification.add(soundboard.user_id, "rating", notification_message, link)
            send_instant_notification(soundboard.user_id, notification_message, link)

        stats = soundboard.get_average_rating()
        return jsonify(
            {"status": "success", "average": stats["average"], "count": stats["count"]}
        )

    @bp.route("/<int:id>/comment", methods=["POST"])  # type: ignore
    @verification_required  # type: ignore
    @limiter.limit(COMMENT_LIMIT)  # type: ignore
    def post_comment(id: int) -> Any:
        """
        Post a comment on a soundboard.

        Args:
            id (int): The soundboard ID.
        """
        soundboard = Soundboard.get_by_id(id)
        if soundboard is None:
            flash("Soundboard not found.")
            return redirect(url_for("main.index"))

        if not soundboard.is_public:
            flash("Cannot comment on private soundboards.")
            return redirect(url_for("main.index"))

        form = CommentForm()
        if form.validate_on_submit():
            assert current_user.id is not None
            assert soundboard.id is not None
            comment = Comment(
                user_id=current_user.id,
                soundboard_id=soundboard.id,
                text=form.text.data,
            )
            comment.save()

            # Notify owner (if not the same person)
            if soundboard.user_id != current_user.id:
                notification_message = f'{current_user.username} commented on your soundboard: "{soundboard.name}"'
                link = url_for("soundboard.view", id=soundboard.id)
                assert soundboard.user_id is not None
                Notification.add(
                    soundboard.user_id, "comment", notification_message, link
                )
                send_instant_notification(
                    soundboard.user_id, notification_message, link
                )

            flash("Comment posted!")

        return redirect(url_for("soundboard.view", id=soundboard.id))

    @bp.route("/comment/<int:id>/delete", methods=["POST"])  # type: ignore
    @login_required  # type: ignore
    def delete_comment(id: int) -> Any:
        """
        Delete a comment.

        Args:
            id (int): The comment ID.
        """
        comment = Comment.get_by_id(id)
        if comment is None:
            flash("Comment not found.")
            return redirect(url_for("main.index"))

        assert comment.soundboard_id is not None
        soundboard = Soundboard.get_by_id(comment.soundboard_id)
        assert soundboard is not None

        # Permission check: Author OR Board Owner OR Admin
        assert current_user.id is not None
        if (
            comment.user_id != current_user.id
            and soundboard.user_id != current_user.id
            and current_user.role != UserRole.ADMIN
        ):
            flash("Permission denied.")
            return redirect(url_for("soundboard.view", id=soundboard.id))

        comment.delete()
        flash("Comment deleted.")
        assert soundboard.id is not None
        return redirect(url_for("soundboard.view", id=soundboard.id))
