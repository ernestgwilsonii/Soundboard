# Technology Stack - Soundboard Website

## Core Backend
- **Language:** Python
- **Web Framework:** Flask
- **Form Handling:** Flask-WTF
- **Email Service:** Flask-Mail for SMTP integration.
- **Security:** CSRFProtect for CSRF defense and **Flask-Limiter** for rate limiting and brute-force protection.
- **Authentication:** Custom session-based authentication with secure password hashing (using a library like `werkzeug.security`).
- **Logging:** Python's built-in `logging` module, configured with separate handlers for account and user activity.
- **Audio Processing:** **Mutagen** for server-side audio metadata extraction (duration, sample rate).

## Data Storage
- **Database:** SQLite (two distinct database files for isolation: `accounts.sqlite3` and `soundboards.sqlite3`).
- **File System:** Structured local directory storage for user-uploaded audio files (MP3, WAV, OGG).

## Frontend
- **Languages:** HTML5, CSS3, JavaScript (ES6+).
- **Styling:** Bootstrap CSS for a responsive, grid-based layout.
- **Icons:** Font Awesome (CDN or local integration).
- **Interactivity:** Vanilla JavaScript and **SortableJS** for drag-and-drop features.
- **UX Components:** **SweetAlert2** for modern, responsive dialogs and toasts.
- **Data Fetching:** Fetch API for asynchronous sidebar loading and sound reordering.

## Development and Deployment
- **Configuration:** Environment-based settings via `.env` or Flask configuration objects.
- **Server:** Gunicorn for production-ready serving.
- **Testing:** `pytest` for unit and integration testing.
