# Technology Stack - Soundboard Website

## Core Backend
- **Language:** Python
- **Web Framework:** Flask
- **Form Handling:** Flask-WTF
- **Authentication:** Custom session-based authentication with secure password hashing (using a library like `werkzeug.security`).
- **Logging:** Python's built-in `logging` module, configured with separate handlers for account and user activity.

## Data Storage
- **Database:** SQLite (two distinct database files for isolation: `accounts.sqlite3` and `soundboards.sqlite3`).
- **File System:** Structured local directory storage for user-uploaded audio files (MP3, WAV, OGG).

## Frontend
- **Languages:** HTML5, CSS3, JavaScript (ES6+).
- **Styling:** Bootstrap CSS for a responsive, grid-based layout.
- **Icons:** Font Awesome (CDN or local integration).
- **Interactivity:** Vanilla JavaScript or small libraries (e.g., for drag-and-drop features).

## Development and Deployment
- **Configuration:** Environment-based settings via `.env` or Flask configuration objects.
- **Server:** Gunicorn for production-ready serving.
- **Testing:** `pytest` for unit and integration testing.
