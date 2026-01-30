"""
Socket.IO event handlers.

This module defines the server-side event handlers for real-time communication,
including joining/leaving boards, presence tracking, and action synchronization.
"""

from typing import Any, Dict, Optional, cast

from flask import current_app, request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room

from app import socketio
from app.utils.redis_store import get_redis_store


@socketio.on("connect")  # type: ignore
def on_connect() -> None:
    """Handle a client connection."""
    if current_user.is_authenticated:
        store = get_redis_store()
        store.add_global_connection(current_user.id, cast(Any, request).sid)
        current_app.logger.info(f"User {current_user.username} connected globally.")


@socketio.on("join_board")  # type: ignore
def on_join(data: Dict[str, Any]) -> None:
    """Handle a client joining a board room."""
    board_id = data.get("board_id")
    current_app.logger.debug(
        f"on_join board_id={board_id}, user={current_user.username if current_user.is_authenticated else 'Anonymous'}"
    )
    if not board_id:
        return

    join_room(str(board_id))

    if current_user.is_authenticated:
        user_info = {
            "id": current_user.id,
            "username": current_user.username,
            "sid": cast(Any, request).sid,
        }

        store = get_redis_store()
        store.add_board_user(str(board_id), current_user.id, user_info)

        # Broadcast presence update to everyone in the room
        members = store.get_board_members(str(board_id))
        emit("presence_update", members, to=str(board_id))

        current_app.logger.info(f"User {current_user.username} joined board {board_id}")


@socketio.on("leave_board")  # type: ignore
def on_leave(data: Dict[str, Any]) -> None:
    """Handle a client leaving a board room."""
    board_id = data.get("board_id")
    if not board_id:
        return

    leave_room(str(board_id))

    if current_user.is_authenticated:
        store = get_redis_store()
        store.remove_board_user(
            str(board_id), current_user.id, sid=cast(Any, request).sid
        )
        members = store.get_board_members(str(board_id))
        emit(
            "presence_update",
            members,
            to=str(board_id),
        )


@socketio.on("disconnect")  # type: ignore
def on_disconnect() -> None:
    """Handle a client disconnection."""
    store = get_redis_store()
    affected_boards = store.handle_disconnect(cast(Any, request).sid)

    # Update presence for all affected boards
    for board_id in affected_boards:
        members = store.get_board_members(board_id)
        emit("presence_update", members, to=str(board_id))


# --- Action Synchronization ---


def broadcast_board_update(
    board_id: int, action: str, data: Optional[Dict[str, Any]] = None
) -> None:
    """Utility to notify all collaborators that the board state has changed."""
    username = "System"
    try:
        if current_user and current_user.is_authenticated:
            username = current_user.username
    except Exception:
        current_app.logger.debug(
            "Failed to get current_user for board update broadcast"
        )

    socketio.emit(
        "board_updated",
        {"action": action, "data": data, "user": username},
        to=str(board_id),
    )


def send_instant_notification(
    user_id: int, message: str, link: Optional[str] = None
) -> None:
    """Pushes a notification event to all connected sessions of a user."""
    store = get_redis_store()
    sids = store.get_user_sids(user_id)
    for sid in sids:
        socketio.emit("new_notification", {"message": message, "link": link}, to=sid)


@socketio.on("request_lock")  # type: ignore
def on_request_lock(data: Dict[str, Any]) -> None:
    """Handle a request to lock a sound slot."""
    board_id = data.get("board_id")
    sound_id = data.get("sound_id")
    if not board_id or not sound_id:
        return

    username = "Someone"
    try:
        if current_user and current_user.is_authenticated:
            username = current_user.username
    except (RuntimeError, AttributeError):
        # Fallback if accessed outside request context
        pass
    except Exception:
        current_app.logger.debug("Failed to get current_user for lock request")
        pass

    # In a production app, we'd store this in Redis/DB.
    # For now, we broadcast the lock to others in the room.
    socketio.emit(
        "slot_locked",
        {"sound_id": sound_id, "user": username},
        to=str(board_id),
        include_self=False,
    )


@socketio.on("release_lock")  # type: ignore
def on_release_lock(data: Dict[str, Any]) -> None:
    """Handle a request to release a lock on a sound slot."""
    board_id = data.get("board_id")
    sound_id = data.get("sound_id")
    if not board_id or not sound_id:
        return

    socketio.emit(
        "slot_released", {"sound_id": sound_id}, to=str(board_id), include_self=False
    )


@socketio.on("sound_reordered")  # type: ignore
def on_reorder(data: Dict[str, Any]) -> None:
    """Handle sound reordering."""
    board_id = data.get("board_id")
    sound_ids = data.get("sound_ids")
    if not board_id or not sound_ids:
        return

    # Broadcast the new order to others
    socketio.emit(
        "update_sound_order",
        {"sound_ids": sound_ids},
        to=str(board_id),
        include_self=False,
    )


@socketio.on("send_reaction")  # type: ignore
def on_send_reaction(data: Dict[str, Any]) -> None:
    """Handle sending a reaction."""
    board_id = data.get("board_id")
    emoji = data.get("emoji")
    if not board_id or not emoji:
        return

    username = "Someone"
    try:
        if current_user and current_user.is_authenticated:
            username = current_user.username
    except (RuntimeError, AttributeError):
        # Fallback if accessed outside request context
        pass
    except Exception:
        current_app.logger.debug("Failed to get current_user for reaction")
        pass

    # Broadcast to EVERYONE in the room including sender
    socketio.emit(
        "receive_reaction", {"emoji": emoji, "user": username}, to=str(board_id)
    )
