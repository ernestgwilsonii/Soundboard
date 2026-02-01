# Technology Stack - Soundboard Website

## Core Backend
- **Language:** Python
- **Web Framework:** Flask
- **Real-time:** Flask-SocketIO with Redis message queue for horizontal scaling.
- **Form Handling:** Flask-WTF
- **Email Service:** Flask-Mail for SMTP integration.
- **Security:** CSRFProtect for CSRF defense and **Flask-Limiter** for rate limiting and brute-force protection.
- **Authentication:** Custom session-based authentication with secure password hashing (using a library like `werkzeug.security`).
- **Logging:** Python's built-in `logging` module, configured with separate handlers for account and user activity.
- **Audio Processing:** **Mutagen** for metadata and **Pydub** for server-side audio normalization.
- **System Dependencies:** **FFmpeg** (required for `pydub` to process MP3 and OGG formats).

## Data Storage
- **ORM:** SQLAlchemy (via **Flask-SQLAlchemy**).
- **Migrations:** Alembic (via **Flask-Migrate**).
- **Database:** SQLite (two distinct database files for isolation via SQLAlchemy Binds: `accounts.sqlite3` and `soundboards.sqlite3`).
- **In-Memory Store:** Redis 7 (Alpine) for WebSocket state and Pub/Sub.
- **File System:** Structured local directory storage for user-uploaded audio files (MP3, WAV, OGG).

## Frontend
- **Languages:** HTML5, CSS3, JavaScript (ES6+).
- **Styling:** Bootstrap CSS for a responsive, grid-based layout.
- **Icons:** Font Awesome (CDN or local integration).
- **Interactivity:** Vanilla JavaScript and **SortableJS** for drag-and-drop features.
- **Audio Visualization:** **WaveSurfer.js** for interactive waveforms and visual trimming.
- **UX Components:** **SweetAlert2** for modern, responsive dialogs and toasts.
- **Data Fetching:** Fetch API for asynchronous sidebar loading and sound reordering.

## Development and Deployment
- **Configuration:** Environment-based settings via `.env` or Flask configuration objects.
- **Server:** Gunicorn for production-ready serving.
- **Testing:** **Pytest** for unit/integration testing and **Playwright** for end-to-end automation and visual verification.
- **Code Quality:** **Black** (formatting), **Isort** (imports), **Flake8** (linting), **Pydocstyle** (Google-style docstrings), **Mypy** (strict static typing), **Bandit** (SAST), and **Pip-Audit** (dependency scanning).
