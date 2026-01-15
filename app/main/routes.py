"""
Main application routes.

This module handles the main public-facing routes, including the landing page,
dashboard, and general search functionality.
"""

from typing import Any, Dict, List

from flask import jsonify, render_template, request, url_for
from flask_login import current_user

from app.constants import (
    DEFAULT_PAGE_SIZE,
    EXPLORE_BOARD_LIMIT,
    POPULAR_TAGS_LIMIT,
    SIDEBAR_ACTIVITY_LIMIT,
    SIDEBAR_NOTIFICATION_LIMIT,
)
from app.enums import UserRole
from app.main import bp
from app.models import Activity, AdminSettings, Notification, Playlist, Soundboard, Tag


@bp.app_context_processor  # type: ignore
def inject_announcement() -> Dict[str, Any]:
    """
    Inject announcement details and unread notification counts into the template context.

    Returns:
        dict: Context variables (announcement_message, announcement_type, unread_notifications, unread_count).
    """
    unread_notifications = []
    unread_count = 0
    if current_user.is_authenticated:
        unread_notifications = Notification.get_unread_for_user(current_user.id)[
            :SIDEBAR_NOTIFICATION_LIMIT
        ]
        unread_count = Notification.count_unread_for_user(current_user.id)

    return {
        "announcement_message": AdminSettings.get_setting("announcement_message"),
        "announcement_type": AdminSettings.get_setting("announcement_type") or "info",
        "unread_notifications": unread_notifications,
        "unread_count": unread_count,
    }


@bp.before_app_request  # type: ignore
def check_maintenance() -> Any:
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
        if current_user.is_authenticated and current_user.role == UserRole.ADMIN:
            return

        return render_template("maintenance.html"), 503


@bp.route("/")  # type: ignore
@bp.route("/index")  # type: ignore
def index() -> Any:
    """
    Render the home page (dashboard/explore view).

    Handles 'tab' parameter to switch between 'explore' and 'following' views.
    """
    tab = request.args.get("tab", "explore")
    featured_soundboard = Soundboard.get_featured()

    if tab == "following" and current_user.is_authenticated:
        # Get boards and activity only from followed users
        following_ids = [
            followed_user.id for followed_user in current_user.get_following()
        ]
        if following_ids:
            soundboards = Soundboard.get_from_following(following_ids)
            activities = Activity.get_from_following(
                following_ids, limit=SIDEBAR_ACTIVITY_LIMIT
            )
        else:
            soundboards = []
            activities = []
    else:
        # Standard Explore view
        # We fetch one extra in case we need to filter out the featured board
        recent_all = Soundboard.get_recent_public(limit=EXPLORE_BOARD_LIMIT + 1)
        activities = Activity.get_recent(limit=SIDEBAR_ACTIVITY_LIMIT)

        # Filter out featured from recent list to avoid duplication
        if featured_soundboard:
            soundboards = [
                soundboard
                for soundboard in recent_all
                if soundboard.id != featured_soundboard.id
            ][:EXPLORE_BOARD_LIMIT]
        else:
            soundboards = recent_all[:EXPLORE_BOARD_LIMIT]

    return render_template(
        "index.html",
        title="Home",
        featured=featured_soundboard,
        soundboards=soundboards,
        activities=activities,
        current_tab=tab,
    )


@bp.route("/activities")  # type: ignore
def get_activities() -> Any:
    """
    Retrieve recent activities as JSON.

    Query Args:
        limit (int): Number of activities to return (default: 10).

    Returns:
        JSON: List of activity objects.
    """
    limit = request.args.get("limit", DEFAULT_PAGE_SIZE, type=int)
    activities = Activity.get_recent(limit=limit)
    response_data = []
    for activity in activities:
        user = activity.get_user()
        response_data.append(
            {
                "username": user.username if user else "New Member",
                "avatar": user.avatar_path if user else None,
                "description": activity.description,
                "created_at": activity.created_at,
                "profile_url": (
                    url_for("auth.public_profile", username=user.username)
                    if user
                    else "#"
                ),
            }
        )
    return jsonify(response_data)


@bp.route("/sidebar-data")  # type: ignore
def sidebar_data() -> Any:
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
        my_boards = [
            {"id": soundboard.id, "name": soundboard.name, "icon": soundboard.icon}
            for soundboard in Soundboard.get_by_user_id(current_user.id)
        ]

        favorite_ids = current_user.get_favorites()
        for favorite_id in favorite_ids:
            soundboard = Soundboard.get_by_id(favorite_id)
            if soundboard:
                favorites.append(
                    {
                        "id": soundboard.id,
                        "name": soundboard.name,
                        "icon": soundboard.icon,
                    }
                )

        my_playlists = [
            {"id": playlist.id, "name": playlist.name}
            for playlist in Playlist.get_by_user_id(current_user.id)
        ]

        following = [
            {"username": followed_user.username, "avatar": followed_user.avatar_path}
            for followed_user in current_user.get_following()
        ]

        popular_tags = [
            {"name": tag.name} for tag in Tag.get_popular(limit=POPULAR_TAGS_LIMIT)
        ]
    else:
        popular_tags = [
            {"name": tag.name} for tag in Tag.get_popular(limit=POPULAR_TAGS_LIMIT)
        ]

    # Explore section: All public boards grouped by user
    public_boards = Soundboard.get_public()
    explore_section: Dict[str, List[Dict[str, Any]]] = {}
    for soundboard in public_boards:
        creator_username = soundboard.get_creator_username()
        if creator_username not in explore_section:
            explore_section[creator_username] = []
        explore_section[creator_username].append(
            {"id": soundboard.id, "name": soundboard.name, "icon": soundboard.icon}
        )

    return jsonify(
        {
            "my_boards": my_boards,
            "favorites": favorites,
            "my_playlists": my_playlists,
            "following": following,
            "popular_tags": popular_tags,
            "explore": explore_section,
        }
    )
