"""
Soundboard management routes.

This module handles soundboard creation, editing, viewing, and sound management.
It also includes playlist functionality and social interactions (likes, comments).
"""

from typing import Any, List

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import limiter
from app.auth.routes import verification_required
from app.constants import COMMENT_LIMIT, RATING_LIMIT, UPLOAD_LIMIT
from app.enums import UserRole
from app.models import (
    Activity,
    BoardCollaborator,
    Comment,
    Notification,
    Playlist,
    Rating,
    Sound,
    Soundboard,
    User,
)
from app.socket_events import broadcast_board_update
from app.soundboard import bp
from app.utils.audio import AudioProcessor


@bp.route("/dashboard")  # type: ignore
@login_required  # type: ignore
def dashboard() -> Any:
    """
    Render the user's dashboard.

    Displays a list of the user's soundboards.
    """
    assert current_user.id is not None
    user_soundboards = Soundboard.get_by_user_id(current_user.id)
    return render_template(
        "soundboard/dashboard.html",
        title="My Soundboards",
        soundboards=user_soundboards,
    )


@bp.route("/view/<int:id>")  # type: ignore
def view(id: int) -> Any:
    """
    Render the soundboard view page.

    Args:
        id (int): The soundboard ID.
    """
    from flask_login import current_user

    soundboard = Soundboard.get_by_id(id)
    if soundboard is None:
        flash("Soundboard not found.")
        return redirect(url_for("main.index"))

    # Access control: Private boards only accessible by owner
    if not soundboard.is_public:
        if not current_user.is_authenticated or soundboard.user_id != current_user.id:
            flash("This soundboard is private.")
            return redirect(url_for("main.index"))

    is_favorite = False
    user_rating = 0
    if current_user.is_authenticated:
        assert current_user.id is not None
        favorites = current_user.get_favorites()
        if soundboard.id in favorites:
            is_favorite = True
        user_rating = soundboard.get_user_rating(current_user.id)

    sounds = soundboard.get_sounds()
    return render_template(
        "soundboard/view.html",
        title=soundboard.name,
        soundboard=soundboard,
        sounds=sounds,
        is_favorite=is_favorite,
        user_rating=user_rating,
    )


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
    rating = Rating(user_id=current_user.id, soundboard_id=soundboard.id, score=score)
    rating.save()

    Activity.record(
        current_user.id, "rate_board", f'Rated "{soundboard.name}" {score} stars'
    )

    # Notify owner (if not same person)
    if soundboard.user_id != current_user.id:
        from app.socket_events import send_instant_notification

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
    from app.soundboard.forms import CommentForm

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
            from app.models import Notification
            from app.socket_events import send_instant_notification

            notification_message = f'{current_user.username} commented on your soundboard: "{soundboard.name}"'
            link = url_for("soundboard.view", id=soundboard.id)
            assert soundboard.user_id is not None
            Notification.add(soundboard.user_id, "comment", notification_message, link)
            send_instant_notification(soundboard.user_id, notification_message, link)

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


@bp.route("/<int:id>/reorder", methods=["POST"])  # type: ignore
@login_required  # type: ignore
def reorder_sounds(id: int) -> Any:
    """
    Update the display order of sounds in a board.

    Args:
        id (int): The soundboard ID.

    Returns:
        JSON: Status message.
    """
    from flask import jsonify

    soundboard = Soundboard.get_by_id(id)
    if soundboard is None:
        return jsonify({"error": "Soundboard not found"}), 404

    assert current_user.id is not None
    if soundboard.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        return jsonify({"error": "Permission denied"}), 403

    request_data = request.get_json()
    if not request_data or "ids" not in request_data:
        return jsonify({"error": "Invalid data"}), 400

    sound_ids = request_data["ids"]

    try:
        assert soundboard.id is not None
        Sound.reorder_multiple(soundboard.id, sound_ids)
        broadcast_board_update(soundboard.id, "sound_reordered")
    except Exception as error:
        current_app.logger.exception(f"Sound reordering failed: {error}")
        return jsonify({"error": str(error)}), 500

    return jsonify({"status": "success"})


@bp.route("/gallery")  # type: ignore
def gallery() -> Any:
    """
    Render the public gallery of soundboards.

    Query Args:
        sort (str): Sorting criteria ('recent', 'top', etc.).
    """
    sort_criteria = request.args.get("sort", "recent")
    public_soundboards = Soundboard.get_public(order_by=sort_criteria)
    return render_template(
        "soundboard/gallery.html",
        title="Public Gallery",
        soundboards=public_soundboards,
        current_sort=sort_criteria,
    )


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

    if soundboard.user_id != current_user.id and current_user.role != UserRole.ADMIN:
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
    from app.models import Notification
    from app.socket_events import send_instant_notification

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
    if soundboard.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        flash("Permission denied.")
        return redirect(url_for("soundboard.dashboard"))

    collab.delete()
    flash("Collaborator removed.")
    assert soundboard.id is not None
    return redirect(url_for("soundboard.edit", id=soundboard.id))


@bp.route("/check-name")  # type: ignore
@login_required  # type: ignore
def check_name() -> Any:
    """
    Check if a soundboard name is available for the current user.

    Query Args:
        name (str): The name to check.

    Returns:
        JSON: Dictionary with 'available' boolean.
    """
    from flask import jsonify

    name = request.args.get("name")
    if not name:
        return jsonify({"error": "Name required"}), 400

    # Check if this user already has a board with this name

    assert current_user.id is not None
    user_soundboards = Soundboard.get_by_user_id(current_user.id)
    name_exists = any(
        soundboard.name and soundboard.name.lower() == name.lower()
        for soundboard in user_soundboards
    )
    return jsonify({"available": not name_exists})


@bp.route("/search")  # type: ignore
def search() -> Any:
    """
    Perform a global search for soundboards.

    Query Args:
        q (str): Search query.
        sort (str): Sorting criteria.
    """
    query_string = request.args.get("q", "")
    sort_criteria = request.args.get("sort", "recent")
    if query_string:
        matching_soundboards = Soundboard.search(query_string, order_by=sort_criteria)
    else:
        matching_soundboards = []
    return render_template(
        "soundboard/search.html",
        title="Search Results",
        soundboards=matching_soundboards,
        query=query_string,
        current_sort=sort_criteria,
    )


@bp.route("/create", methods=["GET", "POST"])  # type: ignore
@verification_required  # type: ignore
def create() -> Any:
    """Handle soundboard creation."""
    import os

    from flask import current_app
    from werkzeug.utils import secure_filename

    from app.soundboard.forms import SoundboardForm

    form = SoundboardForm()
    if form.validate_on_submit():
        icon_path_or_class = form.icon.data
        if form.icon_image.data:
            uploaded_file = form.icon_image.data
            filename = secure_filename(uploaded_file.filename)
            icon_relative_path = os.path.join("icons", filename)
            full_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"], icon_relative_path
            )
            if not os.path.exists(os.path.dirname(full_path)):
                os.makedirs(os.path.dirname(full_path))
            uploaded_file.save(full_path)
            icon_path_or_class = icon_relative_path

        assert current_user.id is not None
        new_soundboard = Soundboard(
            name=form.name.data,
            user_id=current_user.id,
            icon=icon_path_or_class,
            is_public=form.is_public.data,
            theme_color=form.theme_color.data,
            theme_preset=form.theme_preset.data,
        )
        new_soundboard.save()

        # Process tags
        if form.tags.data:
            tag_data_string: str = form.tags.data
            tag_name_list = [
                tag_name.strip()
                for tag_name in tag_data_string.split(",")
                if tag_name.strip()
            ]
            for tag_name in tag_name_list:
                new_soundboard.add_tag(tag_name)

        Activity.record(
            current_user.id,
            "create_soundboard",
            f'Created a new soundboard: "{new_soundboard.name}"',
        )

        flash(f'Soundboard "{new_soundboard.name}" created!')
        return redirect(url_for("soundboard.dashboard"))
    return render_template(
        "soundboard/create.html", title="Create Soundboard", form=form
    )


@bp.route("/edit/<int:id>", methods=["GET", "POST"])  # type: ignore
@login_required  # type: ignore
def edit(id: int) -> Any:
    """
    Handle soundboard editing.

    Args:
        id (int): The soundboard ID.
    """
    import os

    from flask import current_app
    from werkzeug.utils import secure_filename

    from app.soundboard.forms import SoundboardForm

    soundboard = Soundboard.get_by_id(id)
    if soundboard is None:
        flash("Soundboard not found.")
        return redirect(url_for("soundboard.dashboard"))

    # Ownership check with admin override
    assert current_user.id is not None
    if soundboard.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        flash("You do not have permission to edit this soundboard.")
        return redirect(url_for("soundboard.dashboard"))

    form = SoundboardForm()
    if form.validate_on_submit():
        assert soundboard.id is not None
        soundboard.name = form.name.data
        soundboard.is_public = form.is_public.data
        soundboard.theme_color = form.theme_color.data
        soundboard.theme_preset = form.theme_preset.data
        if form.icon_image.data:
            uploaded_icon_file = form.icon_image.data
            filename = secure_filename(uploaded_icon_file.filename)
            icon_relative_path = os.path.join("icons", filename)
            full_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"], icon_relative_path
            )
            if not os.path.exists(os.path.dirname(full_path)):
                os.makedirs(os.path.dirname(full_path))
            uploaded_icon_file.save(full_path)
            soundboard.icon = icon_relative_path
        else:
            soundboard.icon = form.icon.data
        soundboard.save()
        broadcast_board_update(soundboard.id, "board_metadata_updated")

        # Process tags (replace existing)
        current_tags: List[str] = [
            t.name for t in soundboard.get_tags() if t.name is not None
        ]
        new_tags: List[str] = (
            [t.strip().lower() for t in form.tags.data.split(",") if t.strip()]
            if form.tags.data
            else []
        )

        for nt in new_tags:
            if nt not in current_tags:
                soundboard.add_tag(nt)

        for ct in current_tags:
            if ct not in new_tags:
                soundboard.remove_tag(ct)

        flash(f'Soundboard "{soundboard.name}" updated!')
        return redirect(url_for("soundboard.view", id=soundboard.id))
    elif request.method == "GET":
        form.name.data = soundboard.name
        form.icon.data = soundboard.icon
        form.is_public.data = soundboard.is_public
        form.theme_color.data = soundboard.theme_color
        form.theme_preset.data = soundboard.theme_preset
        form.tags.data = ", ".join(
            [t.name for t in soundboard.get_tags() if t.name is not None]
        )

    # Get sounds for this board
    sounds = soundboard.get_sounds()
    return render_template(
        "soundboard/edit.html",
        title="Edit Soundboard",
        form=form,
        soundboard=soundboard,
        sounds=sounds,
    )


@bp.route("/<int:id>/upload", methods=["GET", "POST"])  # type: ignore
@verification_required  # type: ignore
@limiter.limit(UPLOAD_LIMIT)  # type: ignore
def upload_sound(id: int) -> Any:
    """
    Handle sound upload.

    Args:
        id (int): The soundboard ID.
    """
    import os

    from flask import current_app
    from werkzeug.utils import secure_filename

    from app.soundboard.forms import SoundForm

    soundboard = Soundboard.get_by_id(id)
    if soundboard is None:
        flash("Soundboard not found.")
        return redirect(url_for("soundboard.dashboard"))

    # Ownership check with admin override
    assert current_user.id is not None
    if soundboard.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        flash("Permission denied.")
        return redirect(url_for("soundboard.dashboard"))

    form = SoundForm()
    if not form.validate_on_submit():
        return render_template(
            "soundboard/upload.html",
            title="Upload Sound",
            form=form,
            soundboard=soundboard,
        )

    uploaded_audio_file = form.audio_file.data
    audio_filename = secure_filename(uploaded_audio_file.filename)

    # Create directory for soundboard if it doesn't exist
    assert soundboard.id is not None
    sb_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], str(soundboard.id))
    if not os.path.exists(sb_dir):
        os.makedirs(sb_dir)

    file_path = os.path.join(str(soundboard.id), audio_filename)
    full_audio_path = os.path.join(current_app.config["UPLOAD_FOLDER"], file_path)
    uploaded_audio_file.save(full_audio_path)

    icon_path_or_class = form.icon.data
    if form.icon_image.data:
        uploaded_icon_file = form.icon_image.data
        icon_filename = secure_filename(uploaded_icon_file.filename)
        icon_relative_path = os.path.join("icons", icon_filename)
        if not os.path.exists(
            os.path.join(current_app.config["UPLOAD_FOLDER"], "icons")
        ):
            os.makedirs(os.path.join(current_app.config["UPLOAD_FOLDER"], "icons"))
        uploaded_icon_file.save(
            os.path.join(current_app.config["UPLOAD_FOLDER"], icon_relative_path)
        )
        icon_path_or_class = icon_relative_path

    sound = Sound(
        soundboard_id=soundboard.id,
        name=form.name.data,
        file_path=file_path,
        icon=icon_path_or_class,
    )

    # Audio Processing Hooks
    metadata = AudioProcessor.get_metadata(full_audio_path)
    if metadata:
        sound.end_time = metadata.get("duration")
        sound.bitrate = metadata.get("bitrate")
        sound.file_size = metadata.get("file_size")
        sound.format = metadata.get("format")

    AudioProcessor.normalize(full_audio_path)

    sound.save()
    broadcast_board_update(soundboard.id, "sound_uploaded", {"name": sound.name})

    Activity.record(
        current_user.id,
        "upload_sound",
        f'Uploaded sound "{sound.name}" to "{soundboard.name}"',
    )

    flash(f'Sound "{sound.name}" uploaded!')
    return redirect(url_for("soundboard.edit", id=soundboard.id))


@bp.route("/sound/<int:id>/delete", methods=["POST"])  # type: ignore
@login_required  # type: ignore
def delete_sound(id: int) -> Any:
    """
    Delete a sound.

    Args:
        id (int): The sound ID.
    """
    sound = Sound.get_by_id(id)
    if sound is None:
        flash("Sound not found.")
        return redirect(url_for("soundboard.dashboard"))

    # Check board ownership with admin override
    assert sound.soundboard_id is not None
    soundboard = Soundboard.get_by_id(sound.soundboard_id)
    assert soundboard is not None
    assert current_user.id is not None
    if soundboard.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        flash("Permission denied.")
        return redirect(url_for("soundboard.dashboard"))

    sound.delete()
    assert soundboard.id is not None
    broadcast_board_update(soundboard.id, "sound_deleted", {"id": id})
    flash("Sound deleted.")
    return redirect(url_for("soundboard.edit", id=soundboard.id))


@bp.route("/sound/<int:id>/settings", methods=["POST"])  # type: ignore
@login_required  # type: ignore
def update_sound_settings(id: int) -> Any:
    """
    Update sound settings (volume, loop, start/end time, hotkey).

    Args:
        id (int): The sound ID.

    Returns:
        JSON: Status message.
    """
    from flask import jsonify

    sound = Sound.get_by_id(id)
    if sound is None:
        return jsonify({"error": "Sound not found"}), 404

    assert sound.soundboard_id is not None
    soundboard = Soundboard.get_by_id(sound.soundboard_id)
    if soundboard is None:
        return jsonify({"error": "Soundboard not found"}), 404

    assert current_user.id is not None
    if soundboard.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        return jsonify({"error": "Permission denied"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    sound.volume = data.get("volume", sound.volume)
    sound.is_loop = data.get("is_loop", sound.is_loop)
    sound.start_time = data.get("start_time", sound.start_time)
    sound.end_time = data.get("end_time", sound.end_time)
    sound.hotkey = data.get("hotkey", sound.hotkey)
    sound.icon = data.get("icon", sound.icon)

    sound.save()
    assert soundboard.id is not None
    broadcast_board_update(
        soundboard.id, "sound_updated", {"id": id, "name": sound.name}
    )

    return jsonify({"status": "success"})


@bp.route("/delete/<int:id>", methods=["POST"])  # type: ignore
@login_required  # type: ignore
def delete(id: int) -> Any:
    """
    Delete a soundboard.

    Args:
        id (int): The soundboard ID.
    """
    soundboard = Soundboard.get_by_id(id)
    if soundboard is None:
        flash("Soundboard not found.")
        return redirect(url_for("soundboard.dashboard"))

    # Ownership check with admin override
    assert current_user.id is not None
    if soundboard.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        flash("You do not have permission to delete this soundboard.")
        return redirect(url_for("soundboard.dashboard"))

    soundboard.delete()
    flash("Soundboard deleted.")
    return redirect(url_for("soundboard.dashboard"))


# Playlist Routes
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


@bp.route("/tag/<tag_name>")  # type: ignore
def tag_search(tag_name: str) -> Any:
    """
    Search soundboards by tag.

    Args:
        tag_name (str): The tag name.
    """
    assert tag_name is not None
    soundboards = Soundboard.get_by_tag(tag_name)

    return render_template(
        "soundboard/search.html",
        title=f"Tag: {tag_name}",
        soundboards=soundboards,
        query=tag_name,
    )


@bp.route("/<int:id>/export")  # type: ignore
@login_required  # type: ignore
def export_soundboard(id: int) -> Any:
    """
    Export a soundboard as a ZIP pack.

    Args:
        id (int): The soundboard ID.

    Returns:
        Response: File download response.
    """
    from flask import send_file

    from app.utils.packager import Packager

    soundboard = Soundboard.get_by_id(id)

    if soundboard is None:
        flash("Soundboard not found.")
        return redirect(url_for("soundboard.dashboard"))

    assert current_user.id is not None
    if soundboard.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        flash("Permission denied.")
        return redirect(url_for("soundboard.dashboard"))

    pack_data = Packager.create_soundboard_pack(soundboard)
    assert soundboard.name is not None
    safe_name = (
        "".join([c for c in soundboard.name if c.isalnum() or c in (" ", "_")])
        .strip()
        .replace(" ", "_")
    )

    return send_file(
        pack_data,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{safe_name}.sbp",
    )


@bp.route("/import", methods=["GET", "POST"])  # type: ignore
@verification_required  # type: ignore
def import_soundboard() -> Any:
    """Handle soundboard import from a ZIP pack."""
    from app.soundboard.forms import ImportPackForm
    from app.utils.importer import Importer

    form = ImportPackForm()
    if form.validate_on_submit():
        try:
            assert current_user.id is not None
            new_sb = Importer.import_soundboard_pack(
                form.pack_file.data, current_user.id
            )
            Activity.record(
                current_user.id,
                "import_soundboard",
                f'Imported soundboard: "{new_sb.name}"',
            )
            flash(f'Soundboard "{new_sb.name}" successfully imported!')
            return redirect(url_for("soundboard.dashboard"))
        except Exception as e:
            current_app.logger.exception(f"Soundboard import failed: {e}")
            flash(f"Error importing soundboard: {e}")

    return render_template(
        "soundboard/import.html", title="Import Soundboard", form=form
    )
