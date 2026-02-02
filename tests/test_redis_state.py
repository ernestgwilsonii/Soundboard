import json
import unittest
from unittest.mock import MagicMock, patch

from app.utils.state_store import InMemoryState, RedisState


class TestInMemoryState(unittest.TestCase):
    def setUp(self):
        self.store = InMemoryState()

    def test_add_global_connection(self):
        self.store.add_global_connection(1, "sid_123")
        self.assertEqual(self.store.get_user_sids(1), ["sid_123"])
        self.assertEqual(self.store.sid_to_user["sid_123"], 1)

    def test_remove_global_connection(self):
        self.store.add_global_connection(1, "sid_123")
        user_id = self.store.remove_global_connection("sid_123")
        self.assertEqual(user_id, 1)
        self.assertEqual(self.store.get_user_sids(1), [])

    def test_add_board_user(self):
        info = {"id": 1, "username": "test", "sid": "sid_123"}
        self.store.add_board_user("board_1", 1, info)
        self.assertEqual(self.store.get_board_members("board_1"), [info])
        self.assertIn("board_1", self.store.sid_to_boards["sid_123"])


class TestRedisState(unittest.TestCase):
    def setUp(self):
        self.mock_redis = MagicMock()
        with patch("redis.from_url", return_value=self.mock_redis):
            self.store = RedisState("redis://localhost:6379/0")

    def test_add_global_connection(self):
        self.store.add_global_connection(1, "sid_123")
        self.mock_redis.sadd.assert_called_with("global:user:1", "sid_123")
        self.mock_redis.set.assert_called_with("sid:sid_123:user", "1", ex=86400)

    def test_get_board_members(self):
        info = {"id": 1, "username": "test"}
        self.mock_redis.hvals.return_value = [json.dumps(info).encode("utf-8")]
        members = self.store.get_board_members("board_1")
        self.assertEqual(members, [info])
