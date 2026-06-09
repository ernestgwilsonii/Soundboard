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
*   **HTTPS Out of the Box:** Traefik reverse proxy with automatic Let's Encrypt certificates.

## Architecture (Docker Stack)

| Service   | Image                  | Purpose                                                       | Exposed Ports                  |
|-----------|------------------------|---------------------------------------------------------------|--------------------------------|
| `traefik` | `traefik:v3.3`         | Reverse proxy, TLS termination, Let's Encrypt, 80→443 redirect | `80`, `443` (public)           |
| `app`     | built from `Dockerfile`| Flask + Socket.IO app (Gunicorn/eventlet on port 8000)         | none (only via Traefik)        |
| `redis`   | `redis:7-alpine`       | Socket.IO message queue for horizontal scaling                 | `127.0.0.1:6379` (local only)  |
| `mailpit` | `axllent/mailpit`      | Captures outgoing email for development                        | `127.0.0.1:8025`, `127.0.0.1:1025` (local only) |
| `test`    | built from `Dockerfile`| Playwright-based test runner (`docker compose run --rm test`)  | none                           |

Databases (SQLite), uploads, and TLS certificates persist in named Docker volumes (`db_data`, `upload_data`, `traefik_letsencrypt`, etc.) — nothing sensitive is stored in the repository.

## Quick Start

### Option 1: Docker (Recommended)

**Prerequisites:** Docker Engine with the Compose v2 plugin (`docker compose version` must work — see the Amazon Linux notes below if it doesn't).

1.  **Create your environment file:**
    ```bash
    cp .env.example .env
    ```
    The defaults work for local use (`DOMAIN=localhost`). For a public deployment, see [Deploying to a Server](#deploying-to-a-server-any-domain).

2.  **Build and start:**
    ```bash
    make build
    make run
    ```
    Access the site at `https://localhost` — port 80 automatically redirects to HTTPS. Locally Traefik serves a self-signed certificate, so accept the browser warning (or use `curl -k`).

3.  **Generate Demo Sounds (Optional but recommended):**
    ```bash
    docker compose exec app ./scripts/fetch_demo_sounds.sh
    ```

4.  **Run Tests:**
    ```bash
    make test
    ```

5.  **Stop:**
    ```bash
    make stop
    ```

**Make targets:** `make help` lists everything (`build`, `run`, `stop`, `test`, `scan`, `debug`, `clean`, `promote user=NAME`).

> ⚠️ **`make clean` deletes all Docker volumes** — databases, uploaded sounds, **and the Let's Encrypt certificate**. On a production host prefer `make stop`. (If you do clean, a new certificate is requested on next start; Let's Encrypt rate-limits to 5 identical certificates per week.)

### Option 2: Local Development (without Docker)

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
    The development server listens on `http://localhost:5000` (plain HTTP, hot-reloading when `DEBUG=True`; change the port with `FLASK_RUN_PORT`). Traefik/HTTPS is part of the Docker stack only.

## Deploying to a Server (Any Domain)

A repeatable checklist for putting this site on the public internet under any domain name:

1.  **Server:** any Linux host (EC2, Lightsail, VPS...) with Docker + Compose v2 installed and the repo cloned.
2.  **DNS:** at your DNS provider (Route 53, Cloudflare, Namecheap...), create an **A record** for your domain — e.g. `soundboard.example.com` — pointing to the server's **public IP**. No TXT or other special records are needed. Verify with `getent hosts soundboard.example.com` (or `dig`/`nslookup`).
3.  **Firewall:** allow inbound **TCP 80 and 443** from `0.0.0.0/0` (EC2: security group; Lightsail: instance Networking tab). Port 80 must stay open permanently — Let's Encrypt validates the domain over it (Traefik answers ACME challenges before the HTTPS redirect applies), including at every renewal.
4.  **Configure `.env`** (never committed to git):
    ```env
    DOMAIN=soundboard.example.com
    LETSENCRYPT_EMAIL=you@example.com
    SECRET_KEY=<generate a long random string, e.g. `openssl rand -hex 32`>
    ```
5.  **Start:** `make build && make run`. Traefik requests the certificate within seconds of startup; check progress with `docker compose logs traefik`.
6.  **Verify:**
    ```bash
    curl -s -o /dev/null -w "%{http_code} -> %{redirect_url}\n" http://soundboard.example.com/   # expect 301 -> https
    curl -s -o /dev/null -w "%{http_code}\n" https://soundboard.example.com/                      # expect 200, trusted cert
    ```

The stack survives reboots without intervention: Docker is enabled at boot and every service uses a restart policy.

## HTTPS (Traefik + Let's Encrypt)

The Docker stack includes a **Traefik** reverse proxy that terminates TLS on port 443 and permanently redirects all port-80 traffic to HTTPS.

*   **Local development:** with `DOMAIN=localhost` (the default), Traefik serves its built-in self-signed certificate. Browse to `https://localhost` and accept the warning, or use `curl -k`. (A log line about failing to obtain an ACME certificate for `localhost` is expected and harmless.)
*   **Production:** set `DOMAIN` and `LETSENCRYPT_EMAIL` in `.env` and Traefik automatically obtains a real, browser-trusted Let's Encrypt certificate via the HTTP-01 challenge.
*   **Renewal — no cron needed:** Traefik re-checks its certificates every 24 hours (and at startup) and automatically renews any with fewer than 30 days remaining, hot-swapping them with zero downtime. The only external requirements are that the DNS A record keeps pointing at the server and port 80 stays open.
*   **Storage:** the ACME account key and certificates live in the `traefik_letsencrypt` Docker volume — never in the repository.
*   **Proxy headers:** the app container sets `TRUST_PROXY=true` so Flask honors `X-Forwarded-*` headers from Traefik (correct `https://` URLs and OAuth redirects). Leave this off when the app is not behind a proxy.

*Tip: when testing certificate issuance repeatedly, uncomment the staging `caserver` line in `docker-compose.yml` to avoid Let's Encrypt rate limits, then comment it back out (and clear the `traefik_letsencrypt` volume) for the real certificate.*

## Configuration

The application is configured via the `.env` file (see `.env.example` for a template). Key settings:

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | dev placeholder | Flask session/CSRF signing key. **Set a strong random value in production.** |
| `DEBUG` | `False` | Enables Flask debug mode and hot-reloading (local dev only). |
| `DOMAIN` | `localhost` | Public hostname Traefik routes and requests a certificate for. |
| `LETSENCRYPT_EMAIL` | — | Contact email for Let's Encrypt (expiry notices). |
| `ACCOUNTS_DB` / `SOUNDBOARDS_DB` | repo root | SQLite database paths (the Docker stack stores them in the `db_data` volume). |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection for the Socket.IO message queue. |
| `USE_REDIS_QUEUE` | `False` | Set `true` to enable distributed Socket.IO across multiple app instances. |
| `TRUST_PROXY` | `False` | Honor `X-Forwarded-*` headers. Set automatically in the Docker stack; only enable behind a reverse proxy. |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER` | Mailpit | SMTP settings for verification/password-reset email. |
| `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` | unset | Enables "Sign in with Google" when both are present. |
| `FLASK_RUN_PORT` | `5000` | Port for the non-Docker development server. |

### Local Email (Mailpit)
For development, we use **Mailpit** to capture outgoing emails without needing a real SMTP server.

1.  **Start Services:** Run `make run`.
2.  **View Emails:** Open `http://localhost:8025` in your browser.
    *   All system emails (verification, password reset) will appear here instantly.
    *   No username or password configuration is required.
    *   The Mailpit UI is bound to `127.0.0.1` only (not reachable from the internet). On a remote server, open an SSH tunnel: `ssh -L 8025:localhost:8025 user@server`, then browse `http://localhost:8025` on your own machine.

*For production you would point `MAIL_SERVER`/`MAIL_PORT` (and credentials) at a real SMTP provider in `.env` instead.*

### Social Login (Google OAuth)

To enable "Sign in with Google", create credentials in the [Google Cloud Console](https://console.cloud.google.com/):

1.  **Create Project:** Create a new project (e.g. "Soundboard").
2.  **OAuth Consent Screen:** Configure as "External". Add scopes `.../auth/userinfo.email` and `.../auth/userinfo.profile`.
    *   While the consent screen is in **Testing** mode, only email addresses added as *Test users* can sign in. **Publish** the app to allow anyone.
3.  **Credentials:** Create an "OAuth 2.0 Client ID" of type "Web application". Register an origin/redirect pair for **each environment** you use (Google matches them exactly — scheme, host, and port):
    | Environment | Authorized JavaScript origin | Authorized redirect URI |
    |---|---|---|
    | Production | `https://yourdomain.com` | `https://yourdomain.com/auth/login/google/authorized` |
    | Docker local | `https://localhost` | `https://localhost/auth/login/google/authorized` |
    | Dev server (`./dev.sh`) | `http://localhost:5000` | `http://localhost:5000/auth/login/google/authorized` |
4.  **Environment Setup:** Add the credentials to `.env` (never commit them):
    ```env
    GOOGLE_OAUTH_CLIENT_ID=your-client-id
    GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
    # Only needed when running the dev server directly over plain HTTP (./dev.sh):
    OAUTHLIB_INSECURE_TRANSPORT=1
    ```

**Generic OAuth notes:**
*   If the ID/secret variables are missing, the Google login button is simply not displayed — the rest of the site works normally.
*   A `redirect_uri_mismatch` error means the URI Google received doesn't exactly match a registered one. Behind the Docker/Traefik stack the app generates `https://` URIs automatically (via `TRUST_PROXY`); if you see `http://` in the error, that's the cause.
*   Changes in the Google Console can take a few minutes to propagate.
*   The same `.env` pattern applies to any future provider: keep secrets out of git, register exact redirect URIs per environment.
*   Documentation for additional providers will be added as they are implemented.

## Backups & Disaster Recovery

All user data lives in named Docker volumes on the host (`docker volume ls`): account and soundboard SQLite databases (`db_data`) and uploaded media (`upload_data`). Host/instance snapshots (e.g. Lightsail automatic snapshots) include these volumes, but a snapshot taken mid-write is only *crash-consistent*. For guaranteed-consistent copies, use the backup script:

```bash
make backup            # or: ./scripts/backup.sh [backup_root]
```

It performs, while the site keeps running:
1.  A **SQLite online backup** of both databases (safe under concurrent writes) with an automatic `PRAGMA integrity_check` on each copy.
2.  A tarball of all **uploaded media**.
3.  A copy of **`.env`** (your runtime secrets, which are not in git).

Backups land in timestamped directories under `~/soundboard-backups/` (override with `BACKUP_ROOT`), with the most recent 14 kept (`KEEP_BACKUPS`). Because they're plain files on the host disk, every instance snapshot automatically contains consistent copies — no data is "trapped" inside Docker.

**Schedule it (cron):**
```bash
sudo dnf install -y cronie && sudo systemctl enable --now crond   # AL2023 ships without cron
( crontab -l 2>/dev/null; \
  echo "15 3 * * * cd $PWD && ./scripts/backup.sh >> $HOME/soundboard-backups/backup.log 2>&1" ) | crontab -
```
Pick a time shortly **before** your daily snapshot window so each snapshot includes a fresh backup.

**Restore:**
```bash
make restore dir=~/soundboard-backups/20260609-031500
```
This stops the app, replaces both databases and all uploads from the backup, and restarts. To rebuild a server from scratch: clone the repo, copy the backup's `env` file to `.env`, run `make build && make run`, then restore.

**Test your restores.** A backup is only proven when it has been restored at least once — run a restore after first setup and after major changes.

*Offsite copies (optional, recommended):* host snapshots and on-disk backups both die with the AWS account/region. For true offsite protection, sync the backup directory to object storage, e.g. `aws s3 sync ~/soundboard-backups s3://your-backup-bucket/` (requires an instance role or credentials with S3 write access) — easy to add to the same cron line.

*Not backed up (by design):* Redis (transient Socket.IO message queue), Mailpit (dev-only captured email), and TLS certificates (Traefik re-issues them automatically from Let's Encrypt).

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
Run the full test suite in Docker (recommended — includes Playwright browsers):
```bash
make test
```
Or locally (requires the venv dependencies installed):
```bash
PYTHONPATH=. venv/bin/pytest
```

**Security Scans:**
```bash
make scan   # Bandit + pip-audit inside the test container
```

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and development workflow.
