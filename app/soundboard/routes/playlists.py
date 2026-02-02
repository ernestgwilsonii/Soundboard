"""Playlist management routes."""

from typing import Any

from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.enums import UserRole
from app.models import Playlist, Sound, Soundboard


def register_playlist_routes(bp: Any) -> None:
    """Register playlist management routes on the blueprint."""

    @bp.route("/playlists")  # type: ignore
    @login_required  # type: ignore
    def playlists() -> Any:
        """Render the playlists management page."""
        assert current_user.id is not None
        user_playlists = Playlist.get_by_user_id(current_user.id)
        return render_template(
            "soundboard/playlists.html", title="My Playlists", playlists=user_playlists
        )

    @bp.route("/playlist/create", methods=["GET", "POST"])  # type: ignore
    @login_required  # type: ignore
    def create_playlist() -> Any:
        """Handle playlist creation."""
        from app.soundboard.forms import PlaylistForm

        form = PlaylistForm()
        if form.validate_on_submit():
            assert current_user.id is not None
            new_playlist = Playlist(
                user_id=current_user.id,
                name=form.name.data,
                description=form.description.data,
                is_public=form.is_public.data,
            )
            new_playlist.save()
            flash(f'Playlist "{new_playlist.name}" created!')
            return redirect(url_for("soundboard.playlists"))
        return render_template(
            "soundboard/create_playlist.html", title="Create Playlist", form=form
        )

    @bp.route("/playlist/<int:playlist_id>/add/<int:sound_id>", methods=["POST"])  # type: ignore
    @login_required  # type: ignore
    def add_to_playlist(playlist_id: int, sound_id: int) -> Any:
        """
        Add a sound to a playlist.

        Args:
            playlist_id (int): Playlist ID.
            sound_id (int): Sound ID.

        Returns:
            JSON: Status message.
        """
        from flask import jsonify

        playlist = Playlist.get_by_id(playlist_id)
        if playlist is None:
            return jsonify({"error": "Playlist not found"}), 404

        assert current_user.id is not None
        if playlist.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            return jsonify({"error": "Permission denied"}), 403

        sound = Sound.get_by_id(sound_id)
        if sound is None:
            return jsonify({"error": "Sound not found"}), 404

        # Check if sound is accessible (own board or public)
        assert sound.soundboard_id is not None
        soundboard = Soundboard.get_by_id(sound.soundboard_id)
        assert soundboard is not None
        if (
            not soundboard.is_public
            and soundboard.user_id != current_user.id
            and current_user.role != UserRole.ADMIN
        ):
            return jsonify({"error": "Sound is private"}), 403

        assert sound.id is not None
        playlist.add_sound(sound.id)
        return jsonify({"status": "success"})

    @bp.route("/playlist/<int:id>")  # type: ignore
    def view_playlist(id: int) -> Any:
        """
        Render the playlist view page.

        Args:
            id (int): The playlist ID.
        """
        playlist = Playlist.get_by_id(id)
        if playlist is None:
            flash("Playlist not found.")
            return redirect(url_for("main.index"))

        if not playlist.is_public:
            if not current_user.is_authenticated or playlist.user_id != current_user.id:
                flash("This playlist is private.")
                return redirect(url_for("main.index"))

        sounds = playlist.get_sounds()
        return render_template(
            "soundboard/view_playlist.html",
            title=playlist.name,
            playlist=playlist,
            sounds=sounds,
        )

    @bp.route("/playlist/<int:id>/delete", methods=["POST"])  # type: ignore
    @login_required  # type: ignore
    def delete_playlist(id: int) -> Any:
        """
        Delete a playlist.

        Args:
            id (int): The playlist ID.
        """
        playlist = Playlist.get_by_id(id)
        if playlist is None:
            flash("Playlist not found.")
            return redirect(url_for("soundboard.playlists"))

        assert current_user.id is not None
        if playlist.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            flash("Permission denied.")
            return redirect(url_for("soundboard.playlists"))

        playlist.delete()
        flash("Playlist deleted.")
        return redirect(url_for("soundboard.playlists"))
