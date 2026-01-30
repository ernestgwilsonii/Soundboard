# Implementation Plan - Horizontal Scaling with Redis

- [x] **Infrastructure Setup**
  - [x] Add `redis` service to `docker-compose.yml`.
  - [x] Update `config.py` to include `REDIS_URL` with a default value.
  - [x] Add `redis` (and `msgpack` if recommended for `flask-socketio`) to `requirements.txt`.
  - [x] Verify local Docker environment starts with Redis.

- [x] **Socket.IO Configuration**
  - [x] Update `app/extensions.py` to initialize `SocketIO` with the `message_queue` parameter using the `REDIS_URL`.
  - [x] Ensure `eventlet` or `gevent` is correctly configured to work with the Redis backend (usually automatic, but verify).

- [x] **State Management Refactor (Part 1: Abstraction)**
  - [x] Create a `RedisState` helper class (or similar utility in `app/utils/redis_store.py`) to handle Redis operations (Connect, Set, Get, Add to Set, Remove from Set). This abstracts the raw Redis commands from the business logic.

- [x] **State Management Refactor (Part 2: Migration)**
  - [x] Refactor `app/socket_events.py` to remove `active_users` and `global_users` dictionaries.
  - [x] Update `on_join` to use Redis Sets for tracking users in a board.
  - [x] Update `on_leave` and `on_disconnect` to clean up Redis state.
  - [x] Update any "Get Active Users" logic to query Redis instead of the local dict.

- [x] **Testing & Verification**
  - [x] Write a test case (or update existing) that mocks Redis to ensure logic correctness.
  - [x] Manual verification:
    1. Start the app.
    2. Open two browser windows (Client A and Client B).
    3. Verify they can see each other in the same board.
    4. (Optional but recommended) Manually run two separate app processes on different ports pointing to the same Redis, and verify communication.

- [x] **Cleanup**
  - [x] Remove unused imports or commented-out legacy code related to in-memory dicts.
