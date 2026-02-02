"""State storage abstraction for WebSocket presence and connections."""

import json
from typing import Any, Dict, List, Optional, cast


class StateStore:
    """Interface for state storage."""

    def add_global_connection(self, user_id: int, sid: str) -> None:
        """Register a user's global connection."""
        raise NotImplementedError

    def remove_global_connection(self, sid: str) -> Optional[int]:
        """Remove a connection and return the user_id if found."""
        raise NotImplementedError

    def get_user_sids(self, user_id: int) -> List[str]:
        """Get all active SIDs for a user."""
        raise NotImplementedError

    def add_board_user(
        self, board_id: str, user_id: int, user_info: Dict[str, Any]
    ) -> None:
        """Register a user present on a board."""
        raise NotImplementedError

    def remove_board_user(
        self, board_id: str, user_id: int, sid: Optional[str] = None
    ) -> None:
        """Remove a user from a board."""
        raise NotImplementedError

    def get_board_members(self, board_id: str) -> List[Dict[str, Any]]:
        """Get all users currently on a board."""
        raise NotImplementedError

    def handle_disconnect(self, sid: str) -> List[str]:
        """Clean up all state for a disconnected SID."""
        raise NotImplementedError


class InMemoryState(StateStore):
    """In-memory implementation for single-node / testing."""

    def __init__(self) -> None:
        """Initialize in-memory state."""
        # { user_id: [sid1, sid2, ...] }
        self.global_users: Dict[int, List[str]] = {}
        # { sid: user_id }
        self.sid_to_user: Dict[str, int] = {}
        # { board_id: { user_id: info } }
        self.active_users: Dict[str, Dict[int, Dict[str, Any]]] = {}
        # { sid: set(board_ids) }
        self.sid_to_boards: Dict[str, set] = {}

    def add_global_connection(self, user_id: int, sid: str) -> None:
        """Register a user's global connection."""
        if user_id not in self.global_users:
            self.global_users[user_id] = []
        if sid not in self.global_users[user_id]:
            self.global_users[user_id].append(sid)
        self.sid_to_user[sid] = user_id

    def remove_global_connection(self, sid: str) -> Optional[int]:
        """Remove a connection and return the user_id if found."""
        user_id = self.sid_to_user.pop(sid, None)
        if user_id and user_id in self.global_users:
            if sid in self.global_users[user_id]:
                self.global_users[user_id].remove(sid)
            if not self.global_users[user_id]:
                del self.global_users[user_id]
        return user_id

    def get_user_sids(self, user_id: int) -> List[str]:
        """Get all active SIDs for a user."""
        return self.global_users.get(user_id, [])

    def add_board_user(
        self, board_id: str, user_id: int, user_info: Dict[str, Any]
    ) -> None:
        """Register a user present on a board."""
        if board_id not in self.active_users:
            self.active_users[board_id] = {}
        self.active_users[board_id][user_id] = user_info

        sid = user_info.get("sid")
        if sid:
            if sid not in self.sid_to_boards:
                self.sid_to_boards[sid] = set()
            self.sid_to_boards[sid].add(board_id)

    def remove_board_user(
        self, board_id: str, user_id: int, sid: Optional[str] = None
    ) -> None:
        """Remove a user from a board."""
        if board_id in self.active_users:
            self.active_users[board_id].pop(user_id, None)
        if sid and sid in self.sid_to_boards:
            self.sid_to_boards[sid].discard(board_id)

    def get_board_members(self, board_id: str) -> List[Dict[str, Any]]:
        """Get all users currently on a board."""
        return list(self.active_users.get(board_id, {}).values())

    def handle_disconnect(self, sid: str) -> List[str]:
        """Clean up all state for a disconnected SID."""
        user_id = self.remove_global_connection(sid)
        affected_boards = list(self.sid_to_boards.pop(sid, []))
        for board_id in affected_boards:
            if user_id:
                self.remove_board_user(board_id, user_id)
        return affected_boards


class RedisState(StateStore):
    """Redis implementation for distributed horizontal scaling."""

    def __init__(self, redis_url: str):
        """Initialize Redis connection."""
        import redis

        self.client = redis.from_url(redis_url)
        self.TTL = 86400

    def add_global_connection(self, user_id: int, sid: str) -> None:
        """Register a user's global connection."""
        self.client.sadd(f"global:user:{user_id}", sid)
        self.client.set(f"sid:{sid}:user", str(user_id), ex=self.TTL)

    def remove_global_connection(self, sid: str) -> Optional[int]:
        """Remove a connection and return the user_id if found."""
        user_id_bytes = self.client.get(f"sid:{sid}:user")
        if not user_id_bytes:
            return None
        user_id = int(user_id_bytes)
        self.client.srem(f"global:user:{user_id}", sid)
        self.client.delete(f"sid:{sid}:user")
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
        self.client.hset(
            f"board:{board_id}:presence", str(user_id), json.dumps(user_info)
        )
        if sid:
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
        """Clean up all state for a disconnected SID."""
        affected_boards = []
        user_id = self.remove_global_connection(sid)
        board_ids_bytes = self.client.smembers(f"sid:{sid}:boards")
        for b_bytes in board_ids_bytes:
            board_id = b_bytes.decode("utf-8")
            affected_boards.append(board_id)
            if user_id:
                self.client.hdel(f"board:{board_id}:presence", str(user_id))
        self.client.delete(f"sid:{sid}:boards")
        return affected_boards


# Singleton instance
_store: Optional[StateStore] = None


def init_state_store(app: Any) -> None:
    """Initialize the state store based on application configuration."""
    global _store
    if app.config.get("USE_REDIS_QUEUE"):
        try:
            _store = RedisState(app.config["REDIS_URL"])
            # Ping to verify connection
            cast(RedisState, _store).client.ping()
        except Exception as e:
            app.logger.warning(
                f"Redis connection failed: {e}. Falling back to InMemoryState."
            )
            _store = InMemoryState()
    else:
        _store = InMemoryState()


def get_state_store() -> StateStore:
    """Get the initialized state store."""
    if _store is None:
        raise RuntimeError("StateStore not initialized")
    return _store
