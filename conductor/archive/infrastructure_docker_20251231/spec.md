# Track Specification: Version 5.0 - Infrastructure & Dockerization

## Overview
This track focuses on creating a "Developer Friendly" containerized environment. The goal is to allow anyone to clone the repo and run `docker compose up` to get a fully functional, production-like environment with minimal friction. It also provides a robust mechanism for running tests inside a containerized environment to ensure consistency.

## Functional Requirements

### 1. Production-Ready Dockerfile
- **Multi-Stage Build:** distinct stages for `builder`, `production`, and `dev-test` to keep the final image size optimized while allowing for rich debugging tools in dev.
- **Audio Support:** Must include `ffmpeg` (required by `pydub`/`mutagen`) at the system level.
- **Security:** Run as a non-root user in production.
- **Server:** Use `Gunicorn` as the production WSGI server.

### 2. Developer-Friendly Compose
- **Orchestration:** `docker-compose.yml` to define the web service and volume mounts.
- **Persistence:** Named volumes for `db_data` (SQLite files) and `uploads` (User audio/images).
- **Hot Reloading:** In development mode, mount the source code so changes reflect immediately without rebuilding.

### 3. Containerized Verification
- **Test Service:** A specialized service definition that includes Playwright browsers, allowing E2E tests to run inside the Docker network.
- **Troubleshooting:** Ability to `docker compose run test bash` to get a shell with all tools installed.

## Technical Considerations
- **Base Image:** `python:3.12-slim` for balance of size and compatibility.
- **Playwright:** Requires specific system dependencies or a specific base image. We will use `mcr.microsoft.com/playwright/python:v1.40.0-jammy` for the *test* stage to ensure browsers work out of the box.

## Acceptance Criteria
- `docker compose up` starts the site on port 5000 (or 8000).
- Data persists across container restarts.
- `docker compose run test pytest` executes the test suite successfully.
