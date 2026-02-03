# Implementation Plan - Modular Routes Refactor

- [x] **Phase 1: Soundboard Blueprint Modularization** 32a6481
  - [x] Create `app/soundboard/routes/` directory with `__init__.py`. 32a6481
  - [x] Extract `board_mgmt.py`: Create, View, Edit, Dashboard, Delete. 32a6481
  - [x] Extract `sound_mgmt.py`: Upload, Delete Sound, Reorder, Waveform processing. 32a6481
  - [x] Extract `collaborators.py`: Add Editor, Remove Editor. 32a6481
  - [x] Extract `discovery.py`: Gallery, Search, Trending. 32a6481
  - [x] Extract `social.py`: Comments, Ratings, Playlists (if applicable). 32a6481
  - [x] Update `app/soundboard/__init__.py` to import and register all modules to the `soundboard` blueprint. 32a6481
  - [x] Verify functionality with full test suite. 32a6481

- [x] **Phase 2: Auth Blueprint Modularization** 32a6481
  - [x] Create `app/auth/routes/` directory with `__init__.py`. 32a6481
  - [x] Extract `auth_flow.py`: Login, Register, Logout. 32a6481
  - [x] Extract `verification.py`: Email verification, Password reset. 32a6481
  - [x] Extract `profile.py`: Public profile, Edit profile, Avatars. 32a6481
  - [x] Extract `social.py`: Follow/Unfollow, Notifications. 32a6481
  - [x] Update `app/auth/__init__.py` to register all modules. 32a6481
  - [x] Verify functionality with full test suite. 32a6481

- [x] **Phase 3: Code Quality and Testing** 32a6481
  - [x] Run `black`, `isort`, `flake8`, and `pydocstyle` on all new modules. 32a6481
  - [x] Ensure all new modules have 100% type hint coverage. 32a6481
  - [x] Run full E2E Playwright suite to ensure no regressions in browser interaction. 32a6481
  - [x] Add 2-3 new unit tests per blueprint covering complex route logic discovered during refactor. 32a6481

- [x] **Phase 4: Cleanup** 32a6481
  - [x] Remove the original `app/soundboard/routes.py` and `app/auth/routes.py` files. 32a6481
  - [x] Update any references in the project (e.g., `soundboard.py` if it imports routes explicitly, though usually it imports the blueprint). 32a6481
