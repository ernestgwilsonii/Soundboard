"""
Soundboard management routes.

This module handles soundboard creation, editing, viewing, and sound management.
It also includes playlist functionality and social interactions (likes, comments).
"""

from typing import List

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import limiter
from app.auth.routes import verification_required
from app.db import get_soundboards_db
from app.models import Sound, Soundboard
from app.socket_events import broadcast_board_update
from app.soundboard import bp
from app.utils.audio import AudioProcessor


@bp.route("/dashboard")
@login_required
def dashboard():
    """
    Render the user's dashboard.

    Displays a list of the user's soundboards.
    """
    assert current_user.id is not None
    sbs = Soundboard.get_by_user_id(current_user.id)
    return render_template(
        "soundboard/dashboard.html", title="My Soundboards", soundboards=sbs
    )


@bp.route("/view/<int:id>")
def view(id):
    """
    Render the soundboard view page.

    Args:
        id (int): The soundboard ID.
    """
    from flask_login import current_user

    s = Soundboard.get_by_id(id)
    if s is None:
        flash("Soundboard not found.")
        return redirect(url_for("main.index"))

    # Access control: Private boards only accessible by owner
    if not s.is_public:
        if not current_user.is_authenticated or s.user_id != current_user.id:
            flash("This soundboard is private.")
            return redirect(url_for("main.index"))

    is_favorite = False
    user_rating = 0
    if current_user.is_authenticated:
        assert current_user.id is not None
        favorites = current_user.get_favorites()
        if s.id in favorites:
            is_favorite = True
        user_rating = s.get_user_rating(current_user.id)

    sounds = s.get_sounds()
    return render_template(
        "soundboard/view.html",
        title=s.name,
        soundboard=s,
        sounds=sounds,
        is_favorite=is_favorite,
        user_rating=user_rating,
    )


@bp.route("/<int:id>/favorite", methods=["POST"])
@login_required
def toggle_favorite(id):
    """
    Toggle favorite status for a soundboard.

    Args:
        id (int): The soundboard ID.

    Returns:
        JSON: Dictionary with 'is_favorite' status.
    """
    from flask import jsonify

    s = Soundboard.get_by_id(id)
    if s is None:
        return jsonify({"error": "Soundboard not found"}), 404

    if not s.is_public:
        return jsonify({"error": "Cannot favorite private soundboards"}), 403

    favorites = current_user.get_favorites()
    if s.id in favorites:
        current_user.remove_favorite(s.id)
        is_favorite = False
    else:
        current_user.add_favorite(s.id)
        is_favorite = True

    return jsonify({"is_favorite": is_favorite})


@bp.route("/<int:id>/rate", methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def rate_board(id):
    """
    Submit a rating for a soundboard.

    Args:
        id (int): The soundboard ID.

    Returns:
        JSON: Dictionary with status and updated rating stats.
    """
    from flask import jsonify

    from app.models import Rating

    s = Soundboard.get_by_id(id)
    if s is None:
        return jsonify({"error": "Soundboard not found"}), 404

    if not s.is_public:
        return jsonify({"error": "Cannot rate private soundboards"}), 403

    data = request.get_json()
    if not data or "score" not in data:
        return jsonify({"error": "Score required"}), 400

    score = int(data["score"])
    if score < 1 or score > 5:
        return jsonify({"error": "Score must be between 1 and 5"}), 400

    assert current_user.id is not None
    assert s.id is not None
    rating = Rating(user_id=current_user.id, soundboard_id=s.id, score=score)
    rating.save()

    from app.models import Activity

    Activity.record(current_user.id, "rate_board", f'Rated "{s.name}" {score} stars')

    # Notify owner (if not same person)
    if s.user_id != current_user.id:
        from app.models import Notification
        from app.socket_events import send_instant_notification

        msg = f'{current_user.username} rated your soundboard "{s.name}" {score} stars.'
        link = url_for("soundboard.view", id=s.id)
        assert s.user_id is not None
        Notification.add(s.user_id, "rating", msg, link)
        send_instant_notification(s.user_id, msg, link)

    stats = s.get_average_rating()
    return jsonify(
        {"status": "success", "average": stats["average"], "count": stats["count"]}
    )


@bp.route("/<int:id>/comment", methods=["POST"])
@verification_required
@limiter.limit("10 per minute")
def post_comment(id):
    """
    Post a comment on a soundboard.

    Args:
        id (int): The soundboard ID.
    """
    from app.models import Comment
    from app.soundboard.forms import CommentForm

    s = Soundboard.get_by_id(id)
    if s is None:
        flash("Soundboard not found.")
        return redirect(url_for("main.index"))

    if not s.is_public:
        flash("Cannot comment on private soundboards.")
        return redirect(url_for("main.index"))

    form = CommentForm()
    if form.validate_on_submit():
        assert current_user.id is not None
        assert s.id is not None
        comment = Comment(
            user_id=current_user.id, soundboard_id=s.id, text=form.text.data
        )
        comment.save()

        # Notify owner (if not the same person)
        if s.user_id != current_user.id:
            from app.models import Notification
            from app.socket_events import send_instant_notification

            msg = f'{current_user.username} commented on your soundboard: "{s.name}"'
            link = url_for("soundboard.view", id=s.id)
            assert s.user_id is not None
            Notification.add(s.user_id, "comment", msg, link)
            send_instant_notification(s.user_id, msg, link)

        flash("Comment posted!")

    return redirect(url_for("soundboard.view", id=s.id))


@bp.route("/comment/<int:id>/delete", methods=["POST"])
@login_required
def delete_comment(id):
    """
    Delete a comment.

    Args:
        id (int): The comment ID.
    """
    from app.models import Comment

    comment = Comment.get_by_id(id)
    if comment is None:
        flash("Comment not found.")
        return redirect(url_for("main.index"))

    assert comment.soundboard_id is not None
    s = Soundboard.get_by_id(comment.soundboard_id)
    assert s is not None

    # Permission check: Author OR Board Owner OR Admin
    assert current_user.id is not None
    if (
        comment.user_id != current_user.id
        and s.user_id != current_user.id
        and current_user.role != "admin"
    ):
        flash("Permission denied.")
        return redirect(url_for("soundboard.view", id=s.id))

    comment.delete()
    flash("Comment deleted.")
    assert s.id is not None
    return redirect(url_for("soundboard.view", id=s.id))


@bp.route("/<int:id>/reorder", methods=["POST"])
@login_required
def reorder_sounds(id):
    """
    Update the display order of sounds in a board.

    Args:
        id (int): The soundboard ID.

    Returns:
        JSON: Status message.
    """
    from flask import jsonify

    s = Soundboard.get_by_id(id)
    if s is None:
        return jsonify({"error": "Soundboard not found"}), 404

    assert current_user.id is not None
    if s.user_id != current_user.id and current_user.role != "admin":
        return jsonify({"error": "Permission denied"}), 403

    data = request.get_json()
    if not data or "ids" not in data:
        return jsonify({"error": "Invalid data"}), 400

    sound_ids = data["ids"]
    db = get_soundboards_db()
    cur = db.cursor()

    try:
        assert s.id is not None
        for index, sound_id in enumerate(sound_ids):
            cur.execute(
                "UPDATE sounds SET display_order = ? WHERE id = ? AND soundboard_id = ?",
                (index + 1, sound_id, s.id),
            )
        db.commit()
        broadcast_board_update(s.id, "sound_reordered")
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "success"})


@bp.route("/gallery")
def gallery():
    """
    Render the public gallery of soundboards.

    Query Args:
        sort (str): Sorting criteria ('recent', 'top', etc.).
    """
    sort = request.args.get("sort", "recent")
    sbs = Soundboard.get_public(order_by=sort)
    return render_template(
        "soundboard/gallery.html",
        title="Public Gallery",
        soundboards=sbs,
        current_sort=sort,
    )


@bp.route("/<int:id>/collaborators/add", methods=["POST"])
@login_required
def add_collaborator(id):
    """
    Add a collaborator to a soundboard.

    Args:
        id (int): The soundboard ID.
    """
    from app.models import BoardCollaborator, User

    s = Soundboard.get_by_id(id)
    if s is None:
        flash("Soundboard not found.")
        return redirect(url_for("soundboard.dashboard"))

    if s.user_id != current_user.id and current_user.role != "admin":
        flash("Permission denied.")
        return redirect(url_for("soundboard.dashboard"))

    username = request.form.get("username")
    assert username is not None
    user = User.get_by_username(username)
    if user is None:
        flash("User not found.")
        return redirect(url_for("soundboard.edit", id=s.id))

    assert user.id is not None
    assert s.id is not None
    if user.id == s.user_id:
        flash("Owner is already a collaborator.")
        return redirect(url_for("soundboard.edit", id=s.id))

    existing = BoardCollaborator.get_by_user_and_board(user.id, s.id)
    if existing:
        flash("User is already a collaborator.")
        return redirect(url_for("soundboard.edit", id=s.id))

    assert s.id is not None
    assert user.id is not None
    collab = BoardCollaborator(soundboard_id=s.id, user_id=user.id, role="editor")
    collab.save()

    # Notify user
    from app.models import Notification
    from app.socket_events import send_instant_notification

    msg = f'{current_user.username} invited you to collaborate on "{s.name}"'
    link = url_for("soundboard.view", id=s.id)
    Notification.add(user.id, "collab_invite", msg, link)
    send_instant_notification(user.id, msg, link)

    flash(f"{username} added as collaborator.")
    return redirect(url_for("soundboard.edit", id=s.id))


@bp.route("/collaborators/<int:id>/delete", methods=["POST"])
@login_required
def delete_collaborator(id):
    """
    Remove a collaborator from a soundboard.

    Args:
        id (int): The user ID of the collaborator (from URL).
    """
    from app.models import BoardCollaborator

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
    s = Soundboard.get_by_id(collab.soundboard_id)
    assert s is not None
    assert current_user.id is not None
    if s.user_id != current_user.id and current_user.role != "admin":
        flash("Permission denied.")
        return redirect(url_for("soundboard.dashboard"))

    collab.delete()
    flash("Collaborator removed.")
    assert s.id is not None
    return redirect(url_for("soundboard.edit", id=s.id))


@bp.route("/check-name")
@login_required
def check_name():
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
    from app.models import Soundboard

    assert current_user.id is not None
    user_boards = Soundboard.get_by_user_id(current_user.id)
    exists = any(sb.name and sb.name.lower() == name.lower() for sb in user_boards)
    return jsonify({"available": not exists})


@bp.route("/search")
def search():
    """
    Perform a global search for soundboards.

    Query Args:
        q (str): Search query.
        sort (str): Sorting criteria.
    """
    query = request.args.get("q", "")
    sort = request.args.get("sort", "recent")
    if query:
        sbs = Soundboard.search(query, order_by=sort)
    else:
        sbs = []
    return render_template(
        "soundboard/search.html",
        title="Search Results",
        soundboards=sbs,
        query=query,
        current_sort=sort,
    )


@bp.route("/create", methods=["GET", "POST"])
@verification_required
def create():
    """Handle soundboard creation."""
    import os

    from flask import current_app
    from werkzeug.utils import secure_filename

    from app.soundboard.forms import SoundboardForm

    form = SoundboardForm()
    if form.validate_on_submit():
        icon = form.icon.data
        if form.icon_image.data:
            f = form.icon_image.data
            filename = secure_filename(f.filename)
            icon_path = os.path.join("icons", filename)
            full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], icon_path)
            if not os.path.exists(os.path.dirname(full_path)):
                os.makedirs(os.path.dirname(full_path))
            f.save(full_path)
            icon = icon_path

        assert current_user.id is not None
        s = Soundboard(
            name=form.name.data,
            user_id=current_user.id,
            icon=icon,
            is_public=form.is_public.data,
            theme_color=form.theme_color.data,
            theme_preset=form.theme_preset.data,
        )
        s.save()

        # Process tags
        if form.tags.data:
            tag_data: str = form.tags.data
            tag_list = [t.strip() for t in tag_data.split(",") if t.strip()]
            for tag_name in tag_list:
                s.add_tag(tag_name)

        from app.models import Activity

        Activity.record(
            current_user.id,
            "create_soundboard",
            f'Created a new soundboard: "{s.name}"',
        )

        flash(f'Soundboard "{s.name}" created!')
        return redirect(url_for("soundboard.dashboard"))
    return render_template(
        "soundboard/create.html", title="Create Soundboard", form=form
    )


@bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    """
    Handle soundboard editing.

    Args:
        id (int): The soundboard ID.
    """
    import os

    from flask import current_app
    from werkzeug.utils import secure_filename

    from app.soundboard.forms import SoundboardForm

    s = Soundboard.get_by_id(id)
    if s is None:
        flash("Soundboard not found.")
        return redirect(url_for("soundboard.dashboard"))

    # Ownership check with admin override
    assert current_user.id is not None
    if s.user_id != current_user.id and current_user.role != "admin":
        flash("You do not have permission to edit this soundboard.")
        return redirect(url_for("soundboard.dashboard"))

    form = SoundboardForm()
    if form.validate_on_submit():
        assert s.id is not None
        s.name = form.name.data
        s.is_public = form.is_public.data
        s.theme_color = form.theme_color.data
        s.theme_preset = form.theme_preset.data
        if form.icon_image.data:
            f = form.icon_image.data
            filename = secure_filename(f.filename)
            icon_path = os.path.join("icons", filename)
            full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], icon_path)
            if not os.path.exists(os.path.dirname(full_path)):
                os.makedirs(os.path.dirname(full_path))
            f.save(full_path)
            s.icon = icon_path
        else:
            s.icon = form.icon.data
        s.save()
        broadcast_board_update(s.id, "board_metadata_updated")

        # Process tags (replace existing)
        current_tags: List[str] = [t.name for t in s.get_tags() if t.name is not None]
        new_tags: List[str] = (
            [t.strip().lower() for t in form.tags.data.split(",") if t.strip()]
            if form.tags.data
            else []
        )

        for nt in new_tags:
            if nt not in current_tags:
                s.add_tag(nt)

        for ct in current_tags:
            if ct not in new_tags:
                s.remove_tag(ct)

        flash(f'Soundboard "{s.name}" updated!')
        return redirect(url_for("soundboard.view", id=s.id))
    elif request.method == "GET":
        form.name.data = s.name
        form.icon.data = s.icon
        form.is_public.data = s.is_public
        form.theme_color.data = s.theme_color
        form.theme_preset.data = s.theme_preset
        form.tags.data = ", ".join([t.name for t in s.get_tags() if t.name is not None])

    # Get sounds for this board
    sounds = s.get_sounds()
    return render_template(
        "soundboard/edit.html",
        title="Edit Soundboard",
        form=form,
        soundboard=s,
        sounds=sounds,
    )


@bp.route("/<int:id>/upload", methods=["GET", "POST"])
@verification_required
@limiter.limit("5 per minute")
def upload_sound(id):
    """
    Handle sound upload.

    Args:
        id (int): The soundboard ID.
    """
    import os

    from flask import current_app
    from werkzeug.utils import secure_filename

    from app.soundboard.forms import SoundForm

    s = Soundboard.get_by_id(id)
    if s is None:
        flash("Soundboard not found.")
        return redirect(url_for("soundboard.dashboard"))

    # Ownership check with admin override
    assert current_user.id is not None
    if s.user_id != current_user.id and current_user.role != "admin":
        flash("Permission denied.")
        return redirect(url_for("soundboard.dashboard"))

    form = SoundForm()
    if form.validate_on_submit():
        f = form.audio_file.data
        filename = secure_filename(f.filename)

        # Create directory for soundboard if it doesn't exist
        assert s.id is not None
        sb_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], str(s.id))
        if not os.path.exists(sb_dir):
            os.makedirs(sb_dir)

        file_path = os.path.join(str(s.id), filename)
        full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], file_path)
        f.save(full_path)

        icon = form.icon.data
        if form.icon_image.data:
            fi = form.icon_image.data
            iname = secure_filename(fi.filename)
            icon_path = os.path.join("icons", iname)
            if not os.path.exists(
                os.path.join(current_app.config["UPLOAD_FOLDER"], "icons")
            ):
                os.makedirs(os.path.join(current_app.config["UPLOAD_FOLDER"], "icons"))
            fi.save(os.path.join(current_app.config["UPLOAD_FOLDER"], icon_path))
            icon = icon_path

        sound = Sound(
            soundboard_id=s.id, name=form.name.data, file_path=file_path, icon=icon
        )

        # Audio Processing Hooks
        metadata = AudioProcessor.get_metadata(full_path)
        if metadata:
            sound.end_time = metadata.get("duration")
            sound.bitrate = metadata.get("bitrate")
            sound.file_size = metadata.get("file_size")
            sound.format = metadata.get("format")

        AudioProcessor.normalize(full_path)

        sound.save()
        broadcast_board_update(s.id, "sound_uploaded", {"name": sound.name})

        from app.models import Activity

        Activity.record(
            current_user.id,
            "upload_sound",
            f'Uploaded sound "{sound.name}" to "{s.name}"',
        )

        flash(f'Sound "{sound.name}" uploaded!')
        return redirect(url_for("soundboard.edit", id=s.id))

    return render_template(
        "soundboard/upload.html", title="Upload Sound", form=form, soundboard=s
    )


@bp.route("/sound/<int:id>/delete", methods=["POST"])
@login_required
def delete_sound(id):
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
    s = Soundboard.get_by_id(sound.soundboard_id)
    assert s is not None
    assert current_user.id is not None
    if s.user_id != current_user.id and current_user.role != "admin":
        flash("Permission denied.")
        return redirect(url_for("soundboard.dashboard"))

    sound.delete()
    assert s.id is not None
    broadcast_board_update(s.id, "sound_deleted", {"id": id})
    flash("Sound deleted.")
    return redirect(url_for("soundboard.edit", id=s.id))


@bp.route("/sound/<int:id>/settings", methods=["POST"])
@login_required
def update_sound_settings(id):
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
    s = Soundboard.get_by_id(sound.soundboard_id)
    if s is None:
        return jsonify({"error": "Soundboard not found"}), 404

    assert current_user.id is not None
    if s.user_id != current_user.id and current_user.role != "admin":
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
    assert s.id is not None
    broadcast_board_update(s.id, "sound_updated", {"id": id, "name": sound.name})

    return jsonify({"status": "success"})


@bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    """
    Delete a soundboard.

    Args:
        id (int): The soundboard ID.
    """
    s = Soundboard.get_by_id(id)
    if s is None:
        flash("Soundboard not found.")
        return redirect(url_for("soundboard.dashboard"))

    # Ownership check with admin override
    assert current_user.id is not None
    if s.user_id != current_user.id and current_user.role != "admin":
        flash("You do not have permission to delete this soundboard.")
        return redirect(url_for("soundboard.dashboard"))

    s.delete()
    flash("Soundboard deleted.")
    return redirect(url_for("soundboard.dashboard"))


# Playlist Routes
@bp.route("/playlists")
@login_required
def playlists():
    """Render the playlists management page."""
    from app.models import Playlist

    assert current_user.id is not None
    user_playlists = Playlist.get_by_user_id(current_user.id)
    return render_template(
        "soundboard/playlists.html", title="My Playlists", playlists=user_playlists
    )


@bp.route("/playlist/create", methods=["GET", "POST"])
@login_required
def create_playlist():
    """Handle playlist creation."""
    from app.models import Playlist
    from app.soundboard.forms import PlaylistForm

    form = PlaylistForm()
    if form.validate_on_submit():
        assert current_user.id is not None
        pl = Playlist(
            user_id=current_user.id,
            name=form.name.data,
            description=form.description.data,
            is_public=form.is_public.data,
        )
        pl.save()
        flash(f'Playlist "{pl.name}" created!')
        return redirect(url_for("soundboard.playlists"))
    return render_template(
        "soundboard/create_playlist.html", title="Create Playlist", form=form
    )


@bp.route("/playlist/<int:playlist_id>/add/<int:sound_id>", methods=["POST"])
@login_required
def add_to_playlist(playlist_id, sound_id):
    """
    Add a sound to a playlist.

    Args:
        playlist_id (int): Playlist ID.
        sound_id (int): Sound ID.

    Returns:
        JSON: Status message.
    """
    from flask import jsonify

    from app.models import Playlist, Sound

    pl = Playlist.get_by_id(playlist_id)
    if pl is None:
        return jsonify({"error": "Playlist not found"}), 404

    assert current_user.id is not None
    if pl.user_id != current_user.id and current_user.role != "admin":
        return jsonify({"error": "Permission denied"}), 403

    sound = Sound.get_by_id(sound_id)
    if sound is None:
        return jsonify({"error": "Sound not found"}), 404

    # Check if sound is accessible (own board or public)
    assert sound.soundboard_id is not None
    s = Soundboard.get_by_id(sound.soundboard_id)
    assert s is not None
    if (
        not s.is_public
        and s.user_id != current_user.id
        and current_user.role != "admin"
    ):
        return jsonify({"error": "Sound is private"}), 403

    assert sound.id is not None
    pl.add_sound(sound.id)
    return jsonify({"status": "success"})


@bp.route("/playlist/<int:id>")
def view_playlist(id):
    """
    Render the playlist view page.

    Args:
        id (int): The playlist ID.
    """
    from app.models import Playlist

    pl = Playlist.get_by_id(id)
    if pl is None:
        flash("Playlist not found.")
        return redirect(url_for("main.index"))

    if not pl.is_public:
        if not current_user.is_authenticated or pl.user_id != current_user.id:
            flash("This playlist is private.")
            return redirect(url_for("main.index"))

    sounds = pl.get_sounds()
    return render_template(
        "soundboard/view_playlist.html", title=pl.name, playlist=pl, sounds=sounds
    )


@bp.route("/playlist/<int:id>/delete", methods=["POST"])
@login_required
def delete_playlist(id):
    """
    Delete a playlist.

    Args:
        id (int): The playlist ID.
    """
    from app.models import Playlist

    pl = Playlist.get_by_id(id)
    if pl is None:
        flash("Playlist not found.")
        return redirect(url_for("soundboard.playlists"))

    assert current_user.id is not None
    if pl.user_id != current_user.id and current_user.role != "admin":
        flash("Permission denied.")
        return redirect(url_for("soundboard.playlists"))

    pl.delete()
    flash("Playlist deleted.")
    return redirect(url_for("soundboard.playlists"))


@bp.route("/tag/<tag_name>")
def tag_search(tag_name):
    """
    Search soundboards by tag.

    Args:
        tag_name (str): The tag name.
    """
    from app.models import Soundboard

    assert tag_name is not None
    sbs = Soundboard.get_by_tag(tag_name)

    return render_template(
        "soundboard/search.html",
        title=f"Tag: {tag_name}",
        soundboards=sbs,
        query=tag_name,
    )


@bp.route("/<int:id>/export")
@login_required
def export_soundboard(id):
    """
    Export a soundboard as a ZIP pack.

    Args:
        id (int): The soundboard ID.

    Returns:
        Response: File download response.
    """
    from flask import send_file

    from app.utils.packager import Packager

    s = Soundboard.get_by_id(id)

    if s is None:
        flash("Soundboard not found.")
        return redirect(url_for("soundboard.dashboard"))

    assert current_user.id is not None
    if s.user_id != current_user.id and current_user.role != "admin":
        flash("Permission denied.")
        return redirect(url_for("soundboard.dashboard"))

    pack_data = Packager.create_soundboard_pack(s)
    assert s.name is not None
    safe_name = (
        "".join([c for c in s.name if c.isalnum() or c in (" ", "_")])
        .strip()
        .replace(" ", "_")
    )

    return send_file(
        pack_data,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{safe_name}.sbp",
    )


@bp.route("/import", methods=["GET", "POST"])
@verification_required
def import_soundboard():
    """Handle soundboard import from a ZIP pack."""
    from app.models import Activity
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
            flash(f"Error importing soundboard: {e}")

    return render_template(
        "soundboard/import.html", title="Import Soundboard", form=form
    )
