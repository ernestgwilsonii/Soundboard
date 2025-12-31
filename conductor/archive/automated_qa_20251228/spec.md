# Track Specification: Version 4.0 - Autonomous Testing & Verification

## Overview
This track transforms the project into a self-verifying codebase. It establishes a robust automation harness using Playwright and Pytest that allows the AI agent to independently verify every feature, from backend logic to complex Shadow DOM UI interactions.

## Functional Requirements

### 1. Reliable Test Harness
- **Auto-Server:** A pytest fixture that finds an open port, starts the Flask server in a subprocess, and provides the base URL.
- **Log Capture:** All server stdout/stderr must be piped to `logs/test_server.log` during the test run.
- **Clean Shutdown:** Guaranteed server termination using process groups or signal handling.

### 2. Comprehensive E2E Coverage
- **Auth Flow:** Automated testing of Signup, Verify (via DB update), and Login (both Username and Email).
- **Core CRUD:** Automate the creation of a soundboard, uploading a real audio file, and deleting it.
- **Visual Tools:** Automated verification that the WaveSurfer handles appear and are draggable.
- **Social Graph:** Verify the Follow/Unfollow loop and real-time notification polling.

### 3. Automated Error Diagnostics
- **Log Inspection:** Logic to read `test_server.log` upon failure to identify Tracebacks or 500 errors.
- **Console Capture:** Capture and report browser console errors during Playwright runs.

## Technical Considerations
- **Tooling:** Playwright (already installed), Pytest-Playwright.
- **Isolation:** Use a dedicated `test_automation.sqlite3` database for all E2E runs to avoid corrupting development data.

## Acceptance Criteria
- A single command `CI=true venv/bin/pytest tests/e2e/` can verify the entire website's health.
- The AI agent can report "Success" based on these tests rather than asking the user to click buttons.
