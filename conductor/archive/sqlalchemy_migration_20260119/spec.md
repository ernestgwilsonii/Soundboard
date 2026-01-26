# SQLAlchemy Migration Specification

## 1. Objective
Migrate the persistence layer from raw `sqlite3` queries to **SQLAlchemy ORM** via **Flask-SQLAlchemy**.
The goal is to provide a robust database abstraction that allows switching underlying database engines (e.g., to PostgreSQL or MySQL) purely through configuration (environment variables), while currently maintaining **SQLite** as the backing engine.

## 2. Core Requirements

### 2.1. Multi-Database Support (Binds)
The application currently isolates data into two physical files:
- `accounts.sqlite3`: Users, Auth, Settings.
- `soundboards.sqlite3`: Soundboards, Sounds, Playlists, Comments, Ratings, Tags.

**Requirement:** The migration MUST preserve this isolation using **SQLAlchemy Binds**.
- Default Bind (or `accounts`): Mapped to `accounts.sqlite3`.
- `soundboards` Bind: Mapped to `soundboards.sqlite3`.

### 2.2. Configuration Abstraction
- All database connection strings must be defined in `config.py` and sourced from environment variables (`.env`).
- No hardcoded `sqlite:///` strings in the application logic.
- Users must be able to switch to `postgresql://...` by changing *only* the `.env` file.

### 2.3. Data Access Layer (Repository Pattern / Active Record)
- Existing Model classes (`User`, `Soundboard`, etc.) effectively act as their own Data Access Objects (Active Record pattern).
- **Strategy:** Retain the existing method signatures (`save()`, `delete()`, `get_by_id()`, `search()`) on the models but rewrite their *internals* to use `db.session` instead of `sqlite3.cursor`.
- **Outcome:** Routes and Controllers require minimal to no changes, reducing regression risk.

### 2.4. Migration & Initialization
- Replace the custom `init_db.py` and `migrate.py` scripts with standard **Flask-Migrate (Alembic)** workflows where possible, or updated initialization scripts that use `db.create_all()`.
- Ensure new database schemas can be generated automatically from the Python models.

## 3. Scope of Changes

### 3.1. Infrastructure
- Add `Flask-SQLAlchemy` and `Flask-Migrate` to `requirements.txt`.
- Initialize `db` extension in `app/__init__.py`.
- Configure `SQLALCHEMY_DATABASE_URI` and `SQLALCHEMY_BINDS` in `Config`.

### 3.2. Models
Convert the following classes to `db.Model`:
- **Accounts DB:** `User`, `AdminSettings`, `Follow`, `Notification`, `Favorite`.
- **Soundboards DB:** `Soundboard`, `Sound`, `Playlist`, `PlaylistItem`, `Tag`, `SoundboardTag`, `Rating`, `Comment`, `Activity`, `BoardCollaborator`.

### 3.3. Tests
- Refactor `tests/conftest.py` to set up SQLAlchemy sessions/engines instead of raw SQLite connections.
- Ensure all 160+ tests pass without modifying the *logic* of the tests (only their setup/teardown).

## 4. Success Criteria
1.  **Zero Regressions:** All existing tests pass.
2.  **No Raw SQL:** A grep for `sqlite3` or `execute("SELECT` in the `app/` directory (excluding migration scripts) returns no results.
3.  **Configurable:** Changing `.env` to point to a test PostgreSQL instance (hypothetically) allows the app to boot and run (even if we only test with SQLite).
