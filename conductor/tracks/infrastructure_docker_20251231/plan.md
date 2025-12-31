# Track Plan: Infrastructure & Dockerization

## Phase 1: Preparation
- [ ] Task: Add `gunicorn` to `requirements.txt`.
- [ ] Task: Create `.dockerignore` to prevent clutter (venv, logs, db) from entering the build context.

## Phase 2: The Container Definition
- [ ] Task: Create the multi-stage `Dockerfile`.
    - Stage 1: Base (System deps like ffmpeg).
    - Stage 2: Production (Gunicorn, Non-root user).
    - Stage 3: Test (Playwright browsers, Dev tools).

## Phase 3: Orchestration
- [ ] Task: Create `docker-compose.yml` for the standard app (Production/Dev mix).
- [ ] Task: Create `docker-compose.test.yml` (or similar override) for running the robust test suite.

## Phase 4: Verification & Documentation
- [ ] Task: Verify the build: `docker compose build`.
- [ ] Task: Verify the run: `docker compose up`.
- [ ] Task: Verify the tests: `docker compose run test pytest`.
- [ ] Task: Update `README.md` with "Quick Start via Docker" instructions.
