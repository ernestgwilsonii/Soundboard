"""Sound management routes."""

from typing import Any

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import limiter
from app.auth.decorators import verification_required
from app.constants import UPLOAD_LIMIT
from app.enums import UserRole
from app.models import Activity, Sound, Soundboard
from app.socket_events import broadcast_board_update
from app.soundboard.forms import SoundForm
from app.utils.audio import AudioProcessor
from app.utils.storage import Storage


def register_sound_mgmt_routes(bp: Any) -> None:
    """Register sound management routes on the blueprint."""

    @bp.route("/<int:id>/upload", methods=["GET", "POST"])  # type: ignore
    @verification_required  # type: ignore
    @limiter.limit(UPLOAD_LIMIT)  # type: ignore
    def upload_sound(id: int) -> Any:
        """
        Handle sound upload.

        Args:
            id (int): The soundboard ID.
        """
        soundboard = Soundboard.get_by_id(id)
        if soundboard is None:
            flash("Soundboard not found.")
            return redirect(url_for("soundboard.dashboard"))

        # Ownership check with admin override
        assert current_user.id is not None
        if (
            soundboard.user_id != current_user.id
            and current_user.role != UserRole.ADMIN
        ):
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

        assert soundboard.id is not None
        # Save audio file
        file_path = Storage.save_file(
            form.audio_file.data, subfolder=str(soundboard.id), use_uuid=False
        )
        full_audio_path = Storage.get_full_path(file_path)

        icon_path_or_class = form.icon.data
        if form.icon_image.data:
            icon_path_or_class = Storage.save_file(
                form.icon_image.data, subfolder="icons", use_uuid=True
            )

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
        if (
            soundboard.user_id != current_user.id
            and current_user.role != UserRole.ADMIN
        ):
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
        if (
            soundboard.user_id != current_user.id
            and current_user.role != UserRole.ADMIN
        ):
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
        if (
            soundboard.user_id != current_user.id
            and current_user.role != UserRole.ADMIN
        ):
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
