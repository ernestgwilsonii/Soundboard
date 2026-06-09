# Soundboard

A robust, Flask-based platform for creating, customizing, and sharing interactive soundboards.

## Overview

The Soundboard Website allows users to create personalized soundboards, upload audio files, and share them with the community. It features a responsive design, real-time collaboration updates, and a comprehensive administration system.

## Key Features

*   **Custom Soundboards:** Create, edit, and organize multiple soundboards.
*   **Audio Management:** Upload, normalize, and trim audio files (MP3, WAV, OGG).
*   **User Accounts:** Secure registration, login, and profile management.
*   **Social Features:** Follow users, favorite boards, rate, and comment.
*   **Real-time Updates:** Live collaboration support (sockets) with Redis-backed horizontal scaling.
*   **Distributed Architecture:** Ready for multi-node deployments.
*   **Admin Dashboard:** Manage users and content efficiently.
*   **Responsive Design:** Works on desktop and mobile.

## Quick Start

### Option 1: Docker (Recommended)

The easiest way to run the application is using Docker.

1.  **Start the Application:**
    ```bash
    make run
    ```
    Access the site at `https://localhost` (port 80 redirects to HTTPS).

2.  **Generate Demo Sounds (Optional but recommended):**
    ```bash
    docker compose exec app ./scripts/fetch_demo_sounds.sh
    ```

3.  **Run Tests:**
    ```bash
    make test
    ```

4.  **Stop & Clean:**
    ```bash
    make clean
    ```

### Option 2: Local Development

**Prerequisites:**
*   Python 3.12+
*   SQLite3
*   FFmpeg (required for audio processing)
*   Redis (optional, for horizontal scaling)

**Amazon Linux 2023 / RHEL-family notes:**
The default `python3` is 3.9, FFmpeg is not packaged, and the Docker Compose plugin is not in the repos:
```bash
# Python 3.12 (use it explicitly when creating the venv below)
sudo dnf install -y python3.12 python3.12-pip python3.12-devel

# Docker Compose v2 plugin (needed for `make run` etc.)
sudo curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
  -o /usr/libexec/docker/cli-plugins/docker-compose
sudo chmod +x /usr/libexec/docker/cli-plugins/docker-compose

# FFmpeg static build (for local non-Docker development)
curl -fsSL -o /tmp/ffmpeg.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf /tmp/ffmpeg.tar.xz -C /tmp
sudo install /tmp/ffmpeg-*-amd64-static/ffmpeg /tmp/ffmpeg-*-amd64-static/ffprobe /usr/local/bin/
```

**Setup:**

1.  **Create Virtual Environment:**
    ```bash
    python3.12 -m venv venv   # plain `python3 -m venv venv` is fine if python3 is 3.12+
    source venv/bin/activate
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    # If running E2E tests:
    playwright install --with-deps chromium
    ```

3.  **Environment Setup:**
    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
    *Note: Update `.env` with your specific configuration (email, secret keys, etc).*

4.  **Initialize/Update Database:**
    ```bash
    # Option A: Quick init (creates tables directly)
    python3 manage.py

    # Option B: Run migrations (recommended for existing DBs)
    export FLASK_APP=soundboard.py
    flask db upgrade
    ```

5.  **Generate Demo Sounds:**
    ```bash
    ./scripts/fetch_demo_sounds.sh
    ```

6.  **Run Server:**
    ```bash
    ./dev.sh
    ```

## HTTPS (Traefik + Let's Encrypt)

The Docker stack includes a **Traefik** reverse proxy that terminates TLS on port 443 and permanently redirects all port-80 traffic to HTTPS.

*   **Local development:** with `DOMAIN=localhost` (the default), Traefik serves its built-in self-signed certificate. Browse to `https://localhost` and accept the warning, or use `curl -k`.
*   **Production:** set `DOMAIN` and `LETSENCRYPT_EMAIL` in `.env` and Traefik automatically obtains and renews a real Let's Encrypt certificate via the HTTP-01 challenge.

**Route 53 / AWS setup for Let's Encrypt:**

1.  In Route 53, create an **A record** for your domain (e.g. `soundboard.example.com`) pointing to this server's **public IP**. No special/TXT records are needed for the HTTP-01 challenge.
2.  Ensure the EC2/Lightsail firewall (security group) allows inbound **TCP 80 and 443** from `0.0.0.0/0`. Port 80 must stay open — Let's Encrypt uses it to validate the domain (Traefik answers the challenge before the HTTPS redirect applies).
3.  In `.env`, set:
    ```env
    DOMAIN=soundboard.example.com
    LETSENCRYPT_EMAIL=you@example.com
    ```
4.  Restart: `docker compose up -d`. The certificate is stored in the `traefik_letsencrypt` Docker volume (never in the repo) and renews automatically.

*Tip: when testing repeatedly, uncomment the staging `caserver` line in `docker-compose.yml` to avoid Let's Encrypt rate limits, then comment it back out for the real certificate.*

## Configuration

The application is configured via the `.env` file. Key settings include:

*   **Database Paths:** `ACCOUNTS_DB`, `SOUNDBOARDS_DB`
*   **Email Settings:** `MAIL_SERVER`, `MAIL_PORT`, etc. (Required for verification/password reset)
*   **Security:** `SECRET_KEY`
*   **Redis (Scaling):** `REDIS_URL` (default: `redis://localhost:6379/0`), `USE_REDIS_QUEUE` (set to `true` to enable distributed Socket.IO).

### Local Email (Mailpit)
For development, we use **Mailpit** to capture outgoing emails without needing a real SMTP server.

1.  **Start Services:** Run `make run`.
2.  **View Emails:** Open `http://localhost:8025` in your browser.
    *   All system emails (verification, password reset) will appear here instantly.
    *   No username or password configuration is required.

### Social Login (Google)
To enable "Sign in with Google", you must provide credentials from the [Google Cloud Console](https://console.cloud.google.com/):

1.  **Create Project:** Create a new project for "Soundboard".
2.  **OAuth Consent Screen:** Configure as "External". Add scopes `.../auth/userinfo.email` and `.../auth/userinfo.profile`.
3.  **Credentials:** Create an "OAuth 2.0 Client ID" for a "Web application".
    *   **Authorized JavaScript origins:** `https://localhost` (or your real `https://` domain)
    *   **Authorized redirect URIs:** `https://localhost/auth/login/google/authorized`
4.  **Environment Setup:** Add the following to your `.env`:
    ```env
    GOOGLE_OAUTH_CLIENT_ID=your-client-id
    GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
    # Only needed when running the dev server directly over plain HTTP (./dev.sh):
    OAUTHLIB_INSECURE_TRANSPORT=1
    ```
*Note: If these variables are missing, the Google login button will not be displayed. Documentation for additional providers will be added as they are implemented.*

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
