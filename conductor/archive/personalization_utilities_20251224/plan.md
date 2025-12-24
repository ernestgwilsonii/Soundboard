# Track Plan: Version 2.1 - Personalization and Utilities

## Phase 1: User Avatars and Profile Polish
- [x] Task: Add `avatar_path` column to `users` table via `migrate.py`. 258e383
- [x] Task: Update `User` model and `UpdateProfileForm` to handle image uploads. d62f6ed
- [x] Task: Update Profile page to allow avatar selection. d62f6ed
- [x] Task: Update Navbar and Comments to display user avatars. d62f6ed
- [x] Task: Conductor - User Manual Verification 'User Avatars' (Protocol in workflow.md) d62f6ed

## Phase 2: Keyboard Hotkeys for Streamers
- [x] Task: Add `hotkey` column to `sounds` table via `migrate.py`. d62f6ed
- [x] Task: Update `Sound` model and settings logic to persist hotkeys. a6109bc
- [x] Task: Add Hotkey input to the "Sound Settings" modal. a6109bc
- [x] Task: Implement global JS listener in `view.html` to trigger sounds via keys. a6109bc
- [x] Task: Conductor - User Manual Verification 'Keyboard Hotkeys' (Protocol in workflow.md) a6109bc

## Phase 3: Community Activity Feed
- [x] Task: Create `activities` table via `migrate.py`. a6109bc
- [x] Task: Create `Activity` model and a helper function `record_activity(user, type, description)`. a6109bc
- [x] Task: Hook into existing routes (Create Soundboard, Add Sound, Register) to record activities. ddb9a4c
- [x] Task: Implement the Activity Feed UI on the Home page. ddb9a4c
- [x] Task: Conductor - User Manual Verification 'Activity Feed' (Protocol in workflow.md) ddb9a4c

## Phase 4: Account Lockout Security
- [x] Task: Add `failed_login_attempts` and `lockout_until` to `users` table. ee920ea
- [x] Task: Update `User` model with `increment_failed_attempts()`, `reset_failed_attempts()`, and `is_locked()`. ee182bf
- [x] Task: Modify login route logic to enforce lockout and track attempts. ee182bf
- [x] Task: Conductor - User Manual Verification 'Account Lockout' (Protocol in workflow.md) ee182bf
