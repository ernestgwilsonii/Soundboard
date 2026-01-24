# SQLAlchemy Migration Plan

## Phase 1: Infrastructure & Configuration
- [x] Task: Add `Flask-SQLAlchemy` and `Flask-Migrate` to `requirements.txt`.
- [x] Task: Update `config.py` to define `SQLALCHEMY_DATABASE_URI` (Accounts) and `SQLALCHEMY_BINDS` (Soundboards) using environment variables.
- [x] Task: Initialize `SQLAlchemy` in `app/__init__.py` (or `app/extensions.py` if created) and register it with the app factory.
- [x] Task: Create a base `BaseModel` class (inheriting from `db.Model`) that provides common helpers (like `save()`, `delete()`) to mimic existing behavior.

## Phase 2: Accounts Database Migration
- [x] Task: Convert `User` model to SQLAlchemy.
- [x] Task: Convert `AdminSettings` model to SQLAlchemy.
- [x] Task: Convert `Follow` (association table/model), `Notification`, and `Favorite` models.
- [x] Task: Update `app/db.py` (or replace usage) to handle global session management for `Accounts` related queries during the transition.
- [x] Task: Verify Authentication and Profile tests (partial run).

## Phase 3: Soundboards Database Migration
- [x] Task: Convert `Soundboard` model to SQLAlchemy.
- [x] Task: Convert `Sound` model.
- [x] Task: Convert `Playlist` and `PlaylistItem` models.
- [x] Task: Convert `Tag`, `SoundboardTag`, `Rating`, `Comment`, `Activity`, `BoardCollaborator`.
- [x] Task: Verify Soundboard CRUD and Social tests.

## Phase 4: Test Suite & Cleanup
- [x] Task: Refactor `tests/conftest.py` to use `db.create_all()` and `db.drop_all()` for fixture setup/teardown instead of raw SQL scripts. [d71b266]
- [ ] Task: Remove `app/schema_accounts.sql` and `app/schema_soundboards.sql` (after verifying models match schema).
- [ ] Task: Remove or archive `init_db.py` and `migrate.py` (legacy).
- [ ] Task: Create new `manage.py` or update `entrypoint.sh` to use `flask db upgrade` (Alembic).
- [ ] Task: Final full test suite run to ensure 100% pass rate.
- [ ] Task: Search and destroy any remaining `import sqlite3` or `cursor.execute` in `app/`.

## Phase 5: Documentation
- [ ] Task: Update `tech-stack.md` to reflect SQLAlchemy usage.
- [ ] Task: Update `README.md` with new database initialization commands.
- [ ] Task: Update `CONTRIBUTING.md` with migration guidelines.
