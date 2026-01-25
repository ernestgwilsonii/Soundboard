# SQLAlchemy Migration Plan

## Phase 1: Infrastructure & Configuration
- [x] Task: Add `Flask-SQLAlchemy` and `Flask-Migrate` to `requirements.txt`. [2cae97f]
- [x] Task: Update `config.py` to define `SQLALCHEMY_DATABASE_URI` (Accounts) and `SQLALCHEMY_BINDS` (Soundboards) using environment variables. [2cae97f]
- [x] Task: Initialize `SQLAlchemy` in `app/__init__.py` (or `app/extensions.py` if created) and register it with the app factory. [2cae97f]
- [x] Task: Create a base `BaseModel` class (inheriting from `db.Model`) that provides common helpers (like `save()`, `delete()`) to mimic existing behavior. [2cae97f]

## Phase 2: Accounts Database Migration
- [x] Task: Convert `User` model to SQLAlchemy. [60576cd]
- [x] Task: Convert `AdminSettings` model to SQLAlchemy. [60576cd]
- [x] Task: Convert `Follow` (association table/model), `Notification`, and `Favorite` models. [60576cd]
- [x] Task: Update `app/db.py` (or replace usage) to handle global session management for `Accounts` related queries during the transition. [60576cd]
- [x] Task: Verify Authentication and Profile tests (partial run). [60576cd]

## Phase 3: Soundboards Database Migration
- [x] Task: Convert `Soundboard` model to SQLAlchemy. [60576cd]
- [x] Task: Convert `Sound` model. [60576cd]
- [x] Task: Convert `Playlist` and `PlaylistItem` models. [60576cd]
- [x] Task: Convert `Tag`, `SoundboardTag`, `Rating`, `Comment`, `Activity`, `BoardCollaborator`. [60576cd]
- [x] Task: Verify Soundboard CRUD and Social tests. [60576cd]

## Phase 4: Test Suite & Cleanup
- [x] Task: Refactor `tests/conftest.py` to use `db.create_all()` and `db.drop_all()` for fixture setup/teardown instead of raw SQL scripts. [d71b266]
- [x] Task: Remove `app/schema_accounts.sql` and `app/schema_soundboards.sql` (after verifying models match schema). [9199e60]
- [x] Task: Remove or archive `init_db.py` and `migrate.py` (legacy). [9199e60]
- [x] Task: Create new `manage.py` or update `entrypoint.sh` to use `flask db upgrade` (Alembic). [bbb3bf0]
- [x] Task: Final full test suite run to ensure 100% pass rate. [d104850]
- [x] Task: Search and destroy any remaining `import sqlite3` or `cursor.execute` in `app/`. [d104850]

## Phase 5: Documentation
- [x] Task: Update `tech-stack.md` to reflect SQLAlchemy usage. [ea1fbcb]
- [x] Task: Update `README.md` with new database initialization commands. [ea1fbcb]
- [x] Task: Update `CONTRIBUTING.md` with migration guidelines. [ea1fbcb]