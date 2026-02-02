"""Soundboard management routes."""

from typing import Any

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.auth.decorators import verification_required
from app.enums import UserRole
from app.models import Activity, Soundboard
from app.socket_events import broadcast_board_update
from app.soundboard.forms import SoundboardForm
from app.utils.storage import Storage


def register_board_mgmt_routes(bp: Any) -> None:
    """Register board management routes on the blueprint."""

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
        soundboard = Soundboard.get_by_id(id)
        if soundboard is None:
            flash("Soundboard not found.")
            return redirect(url_for("main.index"))

        # Access control: Private boards only accessible by owner
        if not soundboard.is_public:
            if (
                not current_user.is_authenticated
                or soundboard.user_id != current_user.id
            ):
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

    @bp.route("/create", methods=["GET", "POST"])  # type: ignore
    @verification_required  # type: ignore
    def create() -> Any:
        """Handle soundboard creation."""
        form = SoundboardForm()
        if form.validate_on_submit():
            icon_path_or_class = form.icon.data
            if form.icon_image.data:
                icon_path_or_class = Storage.save_file(
                    form.icon_image.data, subfolder="icons", use_uuid=True
                )

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
                soundboard.icon = Storage.save_file(
                    form.icon_image.data, subfolder="icons", use_uuid=True
                )
            else:
                soundboard.icon = form.icon.data
            soundboard.save()
            broadcast_board_update(soundboard.id, "board_metadata_updated")

            # Process tags (replace existing)
            from typing import List

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
        if (
            soundboard.user_id != current_user.id
            and current_user.role != UserRole.ADMIN
        ):
            flash("You do not have permission to delete this soundboard.")
            return redirect(url_for("soundboard.dashboard"))

        soundboard.delete()
        flash("Soundboard deleted.")
        return redirect(url_for("soundboard.dashboard"))

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
        if (
            soundboard.user_id != current_user.id
            and current_user.role != UserRole.ADMIN
        ):
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
