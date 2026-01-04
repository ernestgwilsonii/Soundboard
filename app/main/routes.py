"""
Main application routes.

This module handles the main public-facing routes, including the landing page,
dashboard, and general search functionality.
"""
from flask import abort, jsonify, render_template, request, url_for
from flask_login import current_user

from app.main import bp
from app.models import Activity, AdminSettings, Soundboard, User


@bp.app_context_processor
def inject_announcement():
    """
    Inject announcement details and unread notification counts into the template context.

    Returns:
        dict: Context variables (announcement_message, announcement_type, unread_notifications, unread_count).
    """
    from app.models import Notification

    unread_notifications = []
    unread_count = 0
    if current_user.is_authenticated:
        unread_notifications = Notification.get_unread_for_user(current_user.id)[:5]
        # Count all unread
        from app.db import get_accounts_db

        db = get_accounts_db()
        cur = db.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
            (current_user.id,),
        )
        unread_count = cur.fetchone()[0]

    return {
        "announcement_message": AdminSettings.get_setting("announcement_message"),
        "announcement_type": AdminSettings.get_setting("announcement_type") or "info",
        "unread_notifications": unread_notifications,
        "unread_count": unread_count,
    }


@bp.before_app_request
def check_maintenance():
    """
    Check if maintenance mode is enabled before processing the request.

    Allows access to static files, auth routes, and admins.
    Returns 503 Maintenance page if active.
    """
    # Allow static files and auth routes (login/logout)
    if request.path.startswith("/static") or request.path.startswith("/auth"):
        return

    is_maintenance = AdminSettings.get_setting("maintenance_mode") == "1"
    if is_maintenance:
        # Admins bypass maintenance
        if current_user.is_authenticated and current_user.role == "admin":
            return

        return render_template("maintenance.html"), 503


@bp.route("/")
@bp.route("/index")
def index():
    """
    Render the home page (dashboard/explore view).

    Handles 'tab' parameter to switch between 'explore' and 'following' views.
    """
    tab = request.args.get("tab", "explore")
    featured = Soundboard.get_featured()

    if tab == "following" and current_user.is_authenticated:
        # Get boards and activity only from followed users
        following_ids = [u.id for u in current_user.get_following()]
        if following_ids:
            # Soundboards from followed users
            from app.db import get_soundboards_db

            db = get_soundboards_db()
            placeholders = ",".join(["?"] * len(following_ids))
            cur = db.cursor()
            cur.execute(
                f"SELECT * FROM soundboards WHERE user_id IN ({placeholders}) AND is_public = 1 ORDER BY created_at DESC",
                following_ids,
            )
            rows = cur.fetchall()
            soundboards = [
                Soundboard(
                    id=row["id"],
                    name=row["name"],
                    user_id=row["user_id"],
                    icon=row["icon"],
                    is_public=row["is_public"],
                    theme_color=row["theme_color"],
                    theme_preset=row["theme_preset"],
                )
                for row in rows
            ]

            # Activities from followed users
            cur.execute(
                f"SELECT * FROM activities WHERE user_id IN ({placeholders}) ORDER BY created_at DESC LIMIT 10",
                following_ids,
            )
            act_rows = cur.fetchall()
            activities = [
                Activity(
                    id=row["id"],
                    user_id=row["user_id"],
                    action_type=row["action_type"],
                    description=row["description"],
                    created_at=row["created_at"],
                )
                for row in act_rows
            ]
        else:
            soundboards = []
            activities = []
    else:
        # Standard Explore view
        recent_all = Soundboard.get_recent_public(limit=7)
        activities = Activity.get_recent(limit=10)

        # Filter out featured from recent list to avoid duplication
        if featured:
            soundboards = [sb for sb in recent_all if sb.id != featured.id][:6]
        else:
            soundboards = recent_all[:6]

    return render_template(
        "index.html",
        title="Home",
        featured=featured,
        soundboards=soundboards,
        activities=activities,
        current_tab=tab,
    )


@bp.route("/activities")
def get_activities():
    """
    Retrieve recent activities as JSON.

    Query Args:
        limit (int): Number of activities to return (default: 10).

    Returns:
        JSON: List of activity objects.
    """
    limit = request.args.get("limit", 10, type=int)
    activities = Activity.get_recent(limit=limit)
    data = []
    for a in activities:
        user = a.get_user()
        data.append(
            {
                "username": user.username if user else "New Member",
                "avatar": user.avatar_path if user else None,
                "description": a.description,
                "created_at": a.created_at,
                "profile_url": (
                    url_for("auth.public_profile", username=user.username)
                    if user
                    else "#"
                ),
            }
        )
    return jsonify(data)


@bp.route("/sidebar-data")
def sidebar_data():
    """
    Retrieve data for the sidebar (user boards, playlists, following, etc.).

    Returns:
        JSON: Dictionary containing lists of my_boards, favorites, my_playlists, following, popular_tags, and explore.
    """
    my_boards = []
    favorites = []
    my_playlists = []
    following = []
    popular_tags = []

    if current_user.is_authenticated:
        from app.models import Playlist, Tag

        my_boards = [
            {"id": sb.id, "name": sb.name, "icon": sb.icon}
            for sb in Soundboard.get_by_user_id(current_user.id)
        ]

        fav_ids = current_user.get_favorites()
        for fid in fav_ids:
            sb = Soundboard.get_by_id(fid)
            if sb:
                favorites.append({"id": sb.id, "name": sb.name, "icon": sb.icon})

        my_playlists = [
            {"id": pl.id, "name": pl.name}
            for pl in Playlist.get_by_user_id(current_user.id)
        ]

        following = [
            {"username": u.username, "avatar": u.avatar_path}
            for u in current_user.get_following()
        ]

        popular_tags = [{"name": t.name} for t in Tag.get_popular(limit=10)]
    else:
        from app.models import Tag

        popular_tags = [{"name": t.name} for t in Tag.get_popular(limit=10)]

    # Explore section: All public boards grouped by user
    public_boards = Soundboard.get_public()
    explore = {}
    for sb in public_boards:
        creator = sb.get_creator_username()
        if creator not in explore:
            explore[creator] = []
        explore[creator].append({"id": sb.id, "name": sb.name, "icon": sb.icon})

    return jsonify(
        {
            "my_boards": my_boards,
            "favorites": favorites,
            "my_playlists": my_playlists,
            "following": following,
            "popular_tags": popular_tags,
            "explore": explore,
        }
    )
