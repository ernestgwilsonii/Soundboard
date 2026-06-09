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

### What needs backing up, and where it lives

All user data lives in named Docker volumes on the host (`docker volume ls`):

| Data | Volume | In backups? |
|------|--------|-------------|
| User accounts, passwords, profiles | `db_data` (`accounts.sqlite3`) | ✅ |
| Soundboards, sounds metadata, customizations | `db_data` (`soundboards.sqlite3`) | ✅ |
| Uploaded media (audio files, images) | `upload_data` | ✅ |
| Runtime secrets (`.env`: domain, keys, OAuth) | repo root (not in git) | ✅ |
| Redis (transient Socket.IO message queue) | `redis_data` | ❌ by design |
| Mailpit (dev-only captured email) | `mailpit_data` | ❌ by design |
| TLS certificates (auto re-issued by Traefik) | `traefik_letsencrypt` | ❌ by design |

Host/instance snapshots (e.g. Lightsail automatic snapshots) image the whole disk, so they include these volumes — but a snapshot taken mid-write is only *crash-consistent*. The backup script below produces **guaranteed-consistent** copies as plain files on the host disk, so every snapshot also contains known-good backups. Belt and suspenders.

### One-time installation of the nightly backup job

The backup/restore scripts ship in the repo (`scripts/backup.sh`, `scripts/restore.sh`); only the cron schedule needs installing on each server:

1.  **Install the cron daemon** (Amazon Linux 2023 ships without one):
    ```bash
    sudo dnf install -y cronie
    sudo systemctl enable --now crond
    ```

2.  **Schedule the nightly backup** (run from the repo root; this preserves any existing crontab entries):
    ```bash
    ( crontab -l 2>/dev/null; \
      echo "15 3 * * * cd $PWD && ./scripts/backup.sh >> $HOME/soundboard-backups/backup.log 2>&1" ) | crontab -
    ```
    *   `15 3 * * *` = daily at 03:15 **UTC** (cron uses the server clock — check with `date`). Pick a time shortly **before** your daily snapshot window so each snapshot includes a fresh backup.
    *   Verify the entry with `crontab -l`.

3.  **Verify it works end-to-end:** run the exact cron command once by hand and check the log:
    ```bash
    cd ~/Soundboard && ./scripts/backup.sh >> $HOME/soundboard-backups/backup.log 2>&1
    tail ~/soundboard-backups/backup.log
    ```

### Making a backup (manual)

```bash
make backup            # or: ./scripts/backup.sh [backup_root]
```

The Docker stack must be running. While the site keeps serving traffic, the script:
1.  Copies both databases via the **SQLite online backup API** (safe under concurrent writes) and runs `PRAGMA integrity_check` on each copy — the backup fails loudly if a copy is unhealthy.
2.  Creates a tarball of all **uploaded media**.
3.  Copies **`.env`** (your runtime secrets, which are not in git).

Backups land in timestamped directories: `~/soundboard-backups/20260609-031500/` containing `accounts.sqlite3`, `soundboards.sqlite3`, `uploads.tar.gz`, and `env`. Defaults can be overridden with environment variables: `BACKUP_ROOT` (location) and `KEEP_BACKUPS` (rotation; the 14 most recent are kept).

### Restoring a backup

List available backups, then restore one:

```bash
ls ~/soundboard-backups/
make restore dir=~/soundboard-backups/20260609-031500
```

The script asks for confirmation (`FORCE=1 ./scripts/restore.sh <dir>` skips the prompt for scripted use), then stops the app, **replaces** both databases and all uploaded media with the backup contents, and restarts the app. Allow ~10 seconds of downtime. `.env` is never touched by restore — copy it manually if needed.

**Rebuilding a server from scratch** (new instance, same data):
1.  Set up the server (Docker + Compose, clone the repo — see [Deploying to a Server](#deploying-to-a-server-any-domain)).
2.  Copy your backup directory onto the new server (from a snapshot-restored disk, `scp`, or offsite storage).
3.  Restore the runtime config: `cp <backup-dir>/env .env` (review `DOMAIN` if the IP/domain changed, and update DNS).
4.  Start the stack: `make build && make run`.
5.  Restore the data: `make restore dir=<backup-dir>`.

**Test your restores.** A backup is only proven when it has been restored at least once — run a restore after first setup and after major changes.

### TODO: Offsite copies to Amazon S3 (instructions only — not yet set up)

Snapshots and on-disk backups both live in the same AWS account/region; offsite object storage protects against account-level disasters and accidental deletion. When ready to enable this:

1.  **Create a bucket** (one-time, from any machine with AWS admin credentials):
    ```bash
    aws s3 mb s3://YOUR-UNIQUE-BUCKET-NAME --region us-east-2
    aws s3api put-bucket-versioning --bucket YOUR-UNIQUE-BUCKET-NAME \
      --versioning-configuration Status=Enabled
    aws s3api put-public-access-block --bucket YOUR-UNIQUE-BUCKET-NAME \
      --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
    ```

2.  **Grant the server write access.** Lightsail instances cannot have IAM roles attached (their built-in role has no S3 permissions), so either:
    *   **Option A — IAM user:** create an IAM user whose policy allows only `s3:PutObject`/`s3:ListBucket` on this bucket, generate an access key, and run `aws configure` on the server; or
    *   **Option B — Lightsail bucket:** create a Lightsail object-storage bucket instead and attach it to the instance (Lightsail console → bucket → Resource access), which needs no credentials.

3.  **Add the sync to the existing cron line** so it runs right after each backup:
    ```
    15 3 * * * cd /home/ec2-user/Soundboard && ./scripts/backup.sh >> $HOME/soundboard-backups/backup.log 2>&1 && aws s3 sync $HOME/soundboard-backups s3://YOUR-UNIQUE-BUCKET-NAME/soundboard-backups/ --delete >> $HOME/soundboard-backups/backup.log 2>&1
    ```
    (Omit `--delete` if you want S3 to keep backups beyond the local 14-day rotation.)

4.  **Verify:** `aws s3 ls s3://YOUR-UNIQUE-BUCKET-NAME/soundboard-backups/` after the next nightly run, and consider an S3 lifecycle rule to expire objects after e.g. 90 days to control cost.

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
