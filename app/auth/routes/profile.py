"""User profile routes."""

from typing import Any

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.constants import DEFAULT_PAGE_SIZE
from app.models import Soundboard, User


def register_profile_routes(bp: Any) -> None:
    """Register profile routes on the blueprint."""

    @bp.route("/profile")  # type: ignore
    @login_required  # type: ignore
    def profile() -> Any:
        """Render the user's private profile page."""
        return render_template("auth/profile.html", title="Profile")

    @bp.route("/members")  # type: ignore
    @login_required  # type: ignore
    def members() -> Any:
        """Browse registered members with pagination and search."""
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", DEFAULT_PAGE_SIZE, type=int)
        sort = request.args.get("sort", "newest")
        query = request.args.get("q", "")

        offset = (page - 1) * limit
        users_list = User.get_all(
            limit=limit, offset=offset, sort_by=sort, search_query=query
        )
        total_users = User.count_all(search_query=query)

        total_pages = (total_users + limit - 1) // limit

        return render_template(
            "auth/members.html",
            title="Browse Members",
            users=users_list,
            page=page,
            limit=limit,
            sort=sort,
            q=query,
            total_pages=total_pages,
            total_users=total_users,
        )

    @bp.route("/user/<username>")  # type: ignore
    def public_profile(username: str) -> Any:
        """
        Render the public profile of a user.

        Args:
            username (str): The username.
        """
        user = User.get_by_username(username)
        if not user:
            flash("User not found.")
            return redirect(url_for("main.index"))

        assert user.id is not None
        public_soundboards = Soundboard.get_by_user_id(user.id)
        public_soundboards = [
            soundboard for soundboard in public_soundboards if soundboard.is_public
        ]

        return render_template(
            "auth/public_profile.html",
            title=f"{user.username}'s Profile",
            user=user,
            soundboards=public_soundboards,
        )

    @bp.route("/update_profile", methods=["GET", "POST"])  # type: ignore
    @login_required  # type: ignore
    def update_profile() -> Any:
        """Handle profile updates (bio, social links, avatar)."""
        import os

        from flask import current_app
        from werkzeug.utils import secure_filename

        from app.auth.forms import UpdateProfileForm

        form = UpdateProfileForm()
        if form.validate_on_submit():
            current_user.email = form.email.data
            current_user.bio = form.bio.data
            current_user.social_x = form.social_x.data
            current_user.social_youtube = form.social_youtube.data
            current_user.social_website = form.social_website.data

            if form.avatar.data:
                uploaded_avatar_file = form.avatar.data
                filename = secure_filename(
                    f"{current_user.id}_{uploaded_avatar_file.filename}"
                )
                avatar_path = os.path.join("avatars", filename)
                full_path = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], avatar_path
                )
                if not os.path.exists(os.path.dirname(full_path)):
                    os.makedirs(os.path.dirname(full_path))
                uploaded_avatar_file.save(full_path)
                current_user.avatar_path = avatar_path

            current_user.save()
            flash("Your profile has been updated.")
            return redirect(url_for("auth.profile"))
        elif request.method == "GET":
            form.email.data = current_user.email
            form.bio.data = current_user.bio
            form.social_x.data = current_user.social_x
            form.social_youtube.data = current_user.social_youtube
            form.social_website.data = current_user.social_website
        return render_template(
            "auth/update_profile.html", title="Update Profile", form=form
        )

    @bp.route("/change_password", methods=["GET", "POST"])  # type: ignore
    @login_required  # type: ignore
    def change_password() -> Any:
        """Handle password changes for authenticated users."""
        from app.auth.forms import ChangePasswordForm

        form = ChangePasswordForm()
        if form.validate_on_submit():
            if not current_user.check_password(form.old_password.data):
                flash("Invalid current password.")
                return redirect(url_for("auth.change_password"))
            current_user.set_password(form.password.data)
            current_user.save()
            flash("Your password has been updated.")
            return redirect(url_for("auth.profile"))
        return render_template(
            "auth/change_password.html", title="Change Password", form=form
        )

    @bp.route("/delete_account", methods=["GET", "POST"])  # type: ignore
    @login_required  # type: ignore
    def delete_account() -> Any:
        """Handle permanent account deletion."""
        from flask_login import logout_user

        from app.auth.forms import DeleteAccountForm

        form = DeleteAccountForm()
        if form.validate_on_submit():
            user = current_user
            logout_user()
            user.delete()
            flash("Your account and all associated data have been permanently deleted.")
            return redirect(url_for("main.index"))
        return render_template(
            "auth/delete_account.html", title="Delete Account", form=form
        )
