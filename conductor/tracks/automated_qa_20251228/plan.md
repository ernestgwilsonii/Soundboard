# Track Plan: Version 4.0 - Autonomous Testing & Verification

## Phase 1: Test Infrastructure
- [x] Task: Create `tests/conftest.py` with a robust, auto-starting server fixture. 23754
- [x] Task: Implement automatic database isolation for E2E tests (fresh DB per run). 23754
- [x] Task: Create a `PlaywrightHelper` class for common actions (Login, Upload). 23765
- [x] Task: Verify the harness by loading the homepage in a headless browser. 23975

## Phase 2: Core User Flows (E2E) [checkpoint: 7a4f3dd]
- [x] Task: Implement `tests/e2e/test_auth_flow.py` (Signup, Email/User Login, Logout). e0bb0f1
- [x] Task: Implement `tests/e2e/test_board_management.py` (Create, Edit, Delete). 0bb1127
- [x] Task: Implement `tests/e2e/test_social_loop.py` (Follow, Rate, Real-time feed). 92e2039

## Phase 3: Visual & Advanced Tools (E2E)
- [ ] Task: Implement `tests/e2e/test_waveform_editor.py` (Verify handles and trimming).
- [ ] Task: Implement `tests/e2e/test_icon_picker.js` (Verify dynamic library load).
- [ ] Task: Verify all tests pass in a single CI-style run.
