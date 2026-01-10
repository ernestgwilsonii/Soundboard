"""
Authentication routes.

This module handles user authentication (login, logout, registration),
password resets, and profile management.
"""

from functools import wraps

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import limiter
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm


def admin_required(f):
    """
    Decorator to ensure the current user is an administrator.

    Redirects to index if not authenticated or not an admin.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        """Wrapper to perform the check."""
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("You do not have permission to access this page.")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)

    return decorated_function


def verification_required(f):
    """
    Decorator to ensure the current user has verified their email.

    Redirects to login if not authenticated, or profile if not verified.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        """Wrapper to perform the check."""
        from flask import current_app

        from app.models import User

        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

        # In testing mode, the DB might update behind the server's back.
        # Force a refresh of the verified status if needed.
        if not current_user.is_verified and current_app.config.get("TESTING"):
            u = User.get_by_id(current_user.id)
            if u and u.is_verified:
                current_user.is_verified = True

        if not current_user.is_verified:
            flash("Please verify your email address to access this feature.")
            return redirect(url_for("auth.profile"))
        return f(*args, **kwargs)

    return decorated_function


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    """
    Handle user login.

    Validates credentials, checks for account lockout, and redirects to the next page.
    """
    from urllib.parse import urlparse

    from flask import request
    from flask_login import current_user, login_user

    from app.models import User

    # flash('TEST LOGIN FLASH') # Temporary test
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        # Support login by username or email
        user = User.get_by_username(form.username.data)
        if user is None:
            user = User.get_by_email(form.username.data)

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
    return render_template("auth/login.html", title="Sign In", form=form)


@bp.route("/logout")
def logout():
    """Log out the current user and redirect to the index page."""
    from flask_login import logout_user

    logout_user()
    return redirect(url_for("main.index"))


@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def register():
    """
    Handle user registration.

    Creates a new user, sends a verification email, and sets the first user as admin.
    """
    from flask_login import current_user

    from app.email import send_verification_email
    from app.models import User

    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)

        # Expert Logic: The very first user is automatically an Administrator and Verified
        if User.count_all() == 0:
            user.role = "admin"
            user.is_verified = True
            flash(
                "Welcome! As the first user, you have been promoted to Administrator."
            )
        else:
            user.is_verified = False

        user.save()

        from app.models import Activity

        assert user.id is not None
        Activity.record(user.id, "registration", "Joined the community!")

        send_verification_email(user)
        flash(
            "Congratulations, you are now a registered user! Please check your email to verify your account."
        )
        return redirect(url_for("auth.login"))
    elif request.method == "POST":
        print(f"DEBUG: Form errors: {form.errors}")
    return render_template("auth/signup.html", title="Register", form=form)


@bp.route("/verify/<token>")
def verify_email(token):
    """
    Verify a user's email address using a token.

    Args:
        token (str): The verification token.
    """
    from app.models import User

    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    user = User.verify_token(token, salt="email-verify")
    if user:
        if user.is_verified:
            flash("Account already verified.")
        else:
            user.is_verified = True
            user.save()
            flash("Your account has been verified!")
    else:
        flash("The confirmation link is invalid or has expired.")
    return redirect(url_for("auth.login"))


@bp.route("/notifications/mark_read", methods=["POST"])
@login_required
def mark_notifications_read():
    """Mark all notifications as read for the current user."""
    from flask import jsonify

    from app.models import Notification

    assert current_user.id is not None
    Notification.mark_all_read(current_user.id)
    return jsonify({"status": "success"})


@bp.route("/notifications/unread_count")
@login_required
def unread_notifications_count():
    """
    Get the count and details of unread notifications.

    Returns:
        JSON: Dictionary with count and list of notification objects.
    """
    from app.models import Notification

    assert current_user.id is not None
    unread = Notification.get_unread_for_user(current_user.id)
    data = [
        {"message": n.message, "link": n.link or "#", "created_at": str(n.created_at)}
        for n in unread[:5]
    ]
    return jsonify({"count": len(unread), "notifications": data})


@bp.route("/check-availability")
def check_availability():
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


@bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    """
    Handle requests for password reset.

    Sends an email with a reset link if the email exists.
    """
    from app.auth.forms import PasswordResetRequestForm
    from app.email import send_password_reset_email
    from app.models import User

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


@bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """
    Reset the user's password using a valid token.

    Args:
        token (str): The password reset token.
    """
    from app.auth.forms import ResetPasswordForm
    from app.models import User

    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    user = User.verify_token(token, salt="password-reset")
    if not user:
        flash("The reset link is invalid or has expired.")
        return redirect(url_for("main.index"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.save()
        flash("Your password has been reset.")
        return redirect(url_for("auth.login"))
    return render_template(
        "auth/reset_password.html", title="Reset Password", form=form
    )


@bp.route("/profile")
@login_required
def profile():
    """Render the user's private profile page."""
    return render_template("auth/profile.html", title="Profile")


@bp.route("/members")
@login_required
def members():
    """Browse registered members with pagination and search."""
    from app.models import User

    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
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


@bp.route("/user/<username>/followers")
@login_required
def followers(username):
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


@bp.route("/user/<username>/following")
@login_required
def following(username):
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


@bp.route("/user/<username>")
def public_profile(username):
    """
    Render the public profile of a user.

    Args:
        username (str): The username.
    """
    from app.models import Soundboard, User

    user = User.get_by_username(username)
    if not user:
        flash("User not found.")
        return redirect(url_for("main.index"))

    assert user.id is not None
    public_sbs = Soundboard.get_by_user_id(user.id)
    # Filter for public only if it's not the owner viewing their own public profile
    # (actually public profile should always show only public sbs)
    public_sbs = [sb for sb in public_sbs if sb.is_public]

    return render_template(
        "auth/public_profile.html",
        title=f"{user.username}'s Profile",
        user=user,
        soundboards=public_sbs,
    )


@bp.route("/update_profile", methods=["GET", "POST"])
@login_required
def update_profile():
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
            f = form.avatar.data
            filename = secure_filename(f"{current_user.id}_{f.filename}")
            avatar_path = os.path.join("avatars", filename)
            full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], avatar_path)
            if not os.path.exists(os.path.dirname(full_path)):
                os.makedirs(os.path.dirname(full_path))
            f.save(full_path)
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


@bp.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
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


@bp.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
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


@bp.route("/follow/<username>", methods=["POST"])
@login_required
def follow(username):
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

    from app.models import Activity

    Activity.record(current_user.id, "follow", f"Started following {username}")

    flash(f"You are now following {username}!")
    return redirect(url_for("auth.public_profile", username=username))


@bp.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):
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
