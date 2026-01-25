# Soundboard

A robust, Flask-based platform for creating, customizing, and sharing interactive soundboards.

## Overview

The Soundboard Website allows users to create personalized soundboards, upload audio files, and share them with the community. It features a responsive design, real-time collaboration updates, and a comprehensive administration system.

## Key Features

*   **Custom Soundboards:** Create, edit, and organize multiple soundboards.
*   **Audio Management:** Upload, normalize, and trim audio files (MP3, WAV, OGG).
*   **User Accounts:** Secure registration, login, and profile management.
*   **Social Features:** Follow users, favorite boards, rate, and comment.
*   **Real-time Updates:** Live collaboration support (sockets).
*   **Admin Dashboard:** Manage users and content efficiently.
*   **Responsive Design:** Works on desktop and mobile.

## Quick Start

### Option 1: Docker (Recommended)

The easiest way to run the application is using Docker.

1.  **Start the Application:**
    ```bash
    make run
    ```
    Access the site at `http://localhost:5000`.

2.  **Run Tests:**
    ```bash
    make test
    ```

3.  **Stop & Clean:**
    ```bash
    make clean
    ```

### Option 2: Local Development

**Prerequisites:**
*   Python 3.9+
*   SQLite3
*   FFmpeg (required for audio processing)

**Setup:**

1.  **Create Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Setup:**
    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
    *Note: Update `.env` with your specific configuration (email, secret keys, etc).*

4.  **Initialize/Update Database:**
    ```bash
    # Run migrations to bring DB to latest version
    export FLASK_APP=soundboard.py
    venv/bin/flask db upgrade
    ```
    *Note: For a fresh installation, you can also use `venv/bin/python3 manage.py` to create tables directly.*

5.  **Run Server:**
    ```bash
    ./dev.sh
    ```

## Configuration

The application is configured via the `.env` file. Key settings include:

*   **Database Paths:** `ACCOUNTS_DB`, `SOUNDBOARDS_DB`
*   **Email Settings:** `MAIL_SERVER`, `MAIL_PORT`, etc. (Required for verification/password reset)
*   **Security:** `SECRET_KEY`

### Email Setup (Gmail Example)
To enable email features, use an App Password from your Google Account:
```env
MAIL_SERVER=smtp.googlemail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com
```

## Administration

**Auto-Admin:** The **first user** to register on a fresh installation is automatically granted the `admin` role and is verified.

**Promoting Users:**
To promote subsequent users to admin (using Docker):
```bash
make promote user=target_username
```

## Development

**Code Quality:**
We enforce strict code quality standards. Run the quality check script before committing:
```bash
./scripts/check_quality.sh
```

**Testing:**
Run the full test suite (requires dependencies installed):
```bash
PYTHONPATH=. venv/bin/pytest
```

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and development workflow.
