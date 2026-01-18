"""
Authentication routes.

This module handles user authentication (login, logout, registration),
password resets, and profile management.
"""

from functools import wraps
from typing import Any, Callable

from flask import (
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app import limiter
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from app.constants import DEFAULT_PAGE_SIZE, LOGIN_LIMIT, REGISTRATION_LIMIT
from app.enums import UserRole
from app.models import Activity, Notification, Soundboard, User


def admin_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to ensure the current user is an administrator.

    Redirects to index if not authenticated or not an admin.
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        """Wrapper to perform the check."""
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            flash("You do not have permission to access this page.")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)

    return decorated_function


def verification_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to ensure the current user has verified their email.

    Redirects to login if not authenticated, or profile if not verified.
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        """Wrapper to perform the check."""
        from flask import current_app

        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

        # In testing mode, the DB might update behind the server's back.
        # Force a refresh of the verified status if needed.
        if not current_user.is_verified and current_app.config.get("TESTING"):
            user_from_db = User.get_by_id(current_user.id)
            if user_from_db and user_from_db.is_verified:
                current_user.is_verified = True

        if not current_user.is_verified:
            flash("Please verify your email address to access this feature.")
            return redirect(url_for("auth.profile"))
        return f(*args, **kwargs)

    return decorated_function


@bp.route("/login", methods=["GET", "POST"])  # type: ignore
@limiter.limit(LOGIN_LIMIT)  # type: ignore
def login() -> Any:
    """
    Handle user login.

    Validates credentials, checks for account lockout, and redirects to the next page.
    """
    from urllib.parse import urlparse

    from flask import request
    from flask_login import login_user

    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if not form.validate_on_submit():
        return render_template("auth/login.html", title="Sign In", form=form)

    # Support login by username or email
    user = User.get_by_username(form.username.data) or User.get_by_email(
        form.username.data
    )

    if user is None:
        flash("Invalid username or password")
        return redirect(url_for("auth.login"))

    if user.is_locked():
        flash(
            f"Account is locked due to too many failed attempts. Please try again after {user.lockout_until}."
        )
        return redirect(url_for("auth.login"))

    if not user.check_password(form.password.data):
        user.increment_failed_attempts()
        flash("Invalid username or password")
        return redirect(url_for("auth.login"))

    user.reset_failed_attempts()
    login_user(user, remember=form.remember_me.data)

    next_page = request.args.get("next")
    if not next_page or urlparse(next_page).netloc != "":
        next_page = url_for("main.index")

    return redirect(next_page)


@bp.route("/logout")  # type: ignore
def logout() -> Any:
    """Log out the current user and redirect to the index page."""
    from flask_login import logout_user

    logout_user()
    return redirect(url_for("main.index"))


@bp.route("/register", methods=["GET", "POST"])  # type: ignore
@limiter.limit(REGISTRATION_LIMIT)  # type: ignore
def register() -> Any:
    """
    Handle user registration.

    Creates a new user, sends a verification email, and sets the first user as admin.
    """
    from flask_login import current_user

    from app.email import send_verification_email

    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()
    if not form.validate_on_submit():
        if request.method == "POST":
            current_app.logger.debug(f"Registration form errors: {form.errors}")
        return render_template("auth/signup.html", title="Register", form=form)

    user = User(username=form.username.data, email=form.email.data)
    user.set_password(form.password.data)

    # Expert Logic: The very first user is automatically an Administrator and Verified
    if User.count_all() == 0:
        user.role = UserRole.ADMIN
        user.is_verified = True
        flash("Welcome! As the first user, you have been promoted to Administrator.")
    else:
        user.is_verified = False

    user.save()

    assert user.id is not None
    Activity.record(user.id, "registration", "Joined the community!")

    send_verification_email(user)
    flash(
        "Congratulations, you are now a registered user! Please check your email to verify your account."
    )
    return redirect(url_for("auth.login"))


@bp.route("/verify/<token>")  # type: ignore
def verify_email(token: str) -> Any:
    """
    Verify a user's email address using a token.

    Args:
        token (str): The verification token.
    """
    from app.models import User

    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    verified_user = User.verify_token(token, salt="email-verify")
    if verified_user:
        if verified_user.is_verified:
            flash("Account already verified.")
        else:
            verified_user.is_verified = True
            verified_user.save()
            flash("Your account has been verified!")
    else:
        flash("The confirmation link is invalid or has expired.")
    return redirect(url_for("auth.login"))


@bp.route("/notifications/mark_read", methods=["POST"])  # type: ignore
@login_required  # type: ignore
def mark_notifications_read() -> Any:
    """Mark all notifications as read for the current user."""
    from flask import jsonify

    from app.models import Notification

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
    return jsonify({"count": len(unread_notifications), "notifications": response_data})


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
    from app.models import User

    username = request.args.get("username")
    email = request.args.get("email")

    if username:
        user = User.get_by_username(username)
        return jsonify({"available": user is None})
    if email:
        user = User.get_by_email(email)
        return jsonify({"available": user is None})

    return jsonify({"error": "No field provided"}), 400


@bp.route("/reset_password_request", methods=["GET", "POST"])  # type: ignore
def reset_password_request() -> Any:
    """
    Handle requests for password reset.

    Sends an email with a reset link if the email exists.
    """
    from app.auth.forms import PasswordResetRequestForm
    from app.email import send_password_reset_email

    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data)
        if user:
            send_password_reset_email(user)
        flash("Check your email for the instructions to reset your password")
        return redirect(url_for("auth.login"))
    return render_template(
        "auth/reset_password_request.html", title="Reset Password", form=form
    )


@bp.route("/reset_password/<token>", methods=["GET", "POST"])  # type: ignore
def reset_password(token: str) -> Any:
    """
    Reset the user's password using a valid token.

    Args:
        token (str): The password reset token.
    """
    from app.auth.forms import ResetPasswordForm
    from app.models import User

    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    user_to_reset = User.verify_token(token, salt="password-reset")
    if not user_to_reset:
        flash("The reset link is invalid or has expired.")
        return redirect(url_for("main.index"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user_to_reset.set_password(form.password.data)
        user_to_reset.save()
        flash("Your password has been reset.")
        return redirect(url_for("auth.login"))
    return render_template(
        "auth/reset_password.html", title="Reset Password", form=form
    )


@bp.route("/profile")  # type: ignore
@login_required  # type: ignore
def profile() -> Any:
    """Render the user's private profile page."""
    return render_template("auth/profile.html", title="Profile")


@bp.route("/members")  # type: ignore
@login_required  # type: ignore
def members() -> Any:
    """Browse registered members with pagination and search."""
    from app.models import User

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


@bp.route("/user/<username>/followers")  # type: ignore
@login_required  # type: ignore
def followers(username: str) -> Any:
    """
    Show list of followers for a specific user.

    Args:
        username (str): The username of the user.
    """
    from app.models import User

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
    from app.models import User

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
    # Filter for public only if it's not the owner viewing their own public profile
    # (actually public profile should always show only public sbs)
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
            full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], avatar_path)
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


@bp.route("/follow/<username>", methods=["POST"])  # type: ignore
@login_required  # type: ignore
def follow(username: str) -> Any:
    """
    Follow a user.

    Args:
        username (str): The username of the user to follow.
    """
    from app.models import User

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
    from app.models import User

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
