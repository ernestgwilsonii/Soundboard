"""Redis state management utility."""

import json
from typing import Any, Dict, List, Optional

import redis


class RedisState:
    """
    Manages WebSocket state in Redis to allow horizontal scaling.

    Replaces in-memory active_users and global_users dictionaries.
    """

    def __init__(self, redis_url: str):
        self.client = redis.from_url(redis_url)
        # Expiry for temporary keys (24 hours) to prevent orphans if crash occurs
        self.TTL = 86400

    def add_global_connection(self, user_id: int, sid: str) -> None:
        """Register a user's global connection (track all their tabs)."""
        self.client.sadd(f"global:user:{user_id}", sid)
        # Reverse lookup: SID -> User ID
        self.client.set(f"sid:{sid}:user", str(user_id), ex=self.TTL)

    def remove_global_connection(self, sid: str) -> Optional[int]:
        """Remove a connection and return the user_id if found."""
        user_id_bytes = self.client.get(f"sid:{sid}:user")
        if not user_id_bytes:
            return None

        user_id = int(user_id_bytes)
        self.client.srem(f"global:user:{user_id}", sid)
        self.client.delete(f"sid:{sid}:user")

        # Check if user has no more connections?
        # We might want to know if they are completely offline,
        # but for now we just manage the set.
        return user_id

    def get_user_sids(self, user_id: int) -> List[str]:
        """Get all active SIDs for a user."""
        members = self.client.smembers(f"global:user:{user_id}")
        return [m.decode("utf-8") for m in members]

    def add_board_user(
        self, board_id: str, user_id: int, user_info: Dict[str, Any]
    ) -> None:
        """Register a user present on a board."""
        sid = user_info.get("sid")
        # Store user info in the board's presence hash
        self.client.hset(
            f"board:{board_id}:presence", str(user_id), json.dumps(user_info)
        )

        if sid:
            # Track which boards this SID is watching (Reverse lookup)
            self.client.sadd(f"sid:{sid}:boards", board_id)
            self.client.expire(f"sid:{sid}:boards", self.TTL)

    def remove_board_user(
        self, board_id: str, user_id: int, sid: Optional[str] = None
    ) -> None:
        """Remove a user from a board."""
        self.client.hdel(f"board:{board_id}:presence", str(user_id))

        if sid:
            self.client.srem(f"sid:{sid}:boards", board_id)

    def get_board_members(self, board_id: str) -> List[Dict[str, Any]]:
        """Get all users currently on a board."""
        raw_values = self.client.hvals(f"board:{board_id}:presence")
        return [json.loads(v) for v in raw_values]

    def handle_disconnect(self, sid: str) -> List[str]:
        """
        Clean up all state for a disconnected SID.

        Returns a list of board_ids that were affected (so we can emit updates).
        """
        affected_boards = []

        # 1. Get User ID
        user_id = self.remove_global_connection(sid)

        # 2. Get Boards this SID was watching
        board_ids_bytes = self.client.smembers(f"sid:{sid}:boards")

        for b_bytes in board_ids_bytes:
            board_id = b_bytes.decode("utf-8")
            affected_boards.append(board_id)
            if user_id:
                # Remove from board presence
                # Note: This logic assumes 1 user = 1 presence entry per board.
                # If they had multiple tabs, removing based on user_id removes them entirely
                # from the list, even if another tab is open.
                # To fix this, we should check if they have other SIDs on this board?
                # BUT the original code did: active_users[board_id][user_id] = info.
                # It overwrote. So we just delete it.
                self.client.hdel(f"board:{board_id}:presence", str(user_id))

        self.client.delete(f"sid:{sid}:boards")

        return affected_boards


# Singleton instance placeholder
redis_store: Optional[RedisState] = None


def init_redis_store(app: Any) -> None:
    """Initialize the Redis store with the Flask app config."""
    global redis_store
    redis_store = RedisState(app.config["REDIS_URL"])


def get_redis_store() -> RedisState:
    """Get the initialized Redis store instance."""
    if redis_store is None:
        raise RuntimeError("RedisStore not initialized")
    return redis_store
