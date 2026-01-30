import json
import unittest
from unittest.mock import MagicMock, patch

from app.utils.redis_store import RedisState


class TestRedisState(unittest.TestCase):
    def setUp(self):
        self.mock_redis = MagicMock()
        # Patch redis.from_url to return our mock
        self.patcher = patch("redis.from_url", return_value=self.mock_redis)
        self.patcher.start()
        self.store = RedisState("redis://localhost:6379/0")

    def tearDown(self):
        self.patcher.stop()

    def test_add_global_connection(self):
        self.store.add_global_connection(1, "sid_123")
        self.mock_redis.sadd.assert_called_with("global:user:1", "sid_123")
        self.mock_redis.set.assert_called_with("sid:sid_123:user", "1", ex=86400)

    def test_remove_global_connection(self):
        # Mock finding the user ID
        self.mock_redis.get.return_value = b"1"

        user_id = self.store.remove_global_connection("sid_123")

        self.assertEqual(user_id, 1)
        self.mock_redis.srem.assert_called_with("global:user:1", "sid_123")
        self.mock_redis.delete.assert_called_with("sid:sid_123:user")

    def test_add_board_user(self):
        info = {"id": 1, "username": "test", "sid": "sid_123"}
        self.store.add_board_user("board_1", 1, info)

        self.mock_redis.hset.assert_called_with(
            "board:board_1:presence", "1", json.dumps(info)
        )
        self.mock_redis.sadd.assert_called_with("sid:sid_123:boards", "board_1")

    def test_get_board_members(self):
        info = {"id": 1, "username": "test"}
        self.mock_redis.hvals.return_value = [json.dumps(info)]

        members = self.store.get_board_members("board_1")
        self.assertEqual(members, [info])

    def test_handle_disconnect(self):
        # Mock global user lookup
        self.mock_redis.get.return_value = b"1"
        # Mock board lookup
        self.mock_redis.smembers.return_value = [b"board_1", b"board_2"]

        affected = self.store.handle_disconnect("sid_123")

        self.assertEqual(set(affected), {"board_1", "board_2"})
        # Should have removed user from both boards
        self.mock_redis.hdel.assert_any_call("board:board_1:presence", "1")
        self.mock_redis.hdel.assert_any_call("board:board_2:presence", "1")
