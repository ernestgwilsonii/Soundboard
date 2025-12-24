# Track Specification: Version 2.1 - Personalization and Utilities

## Overview
This track focuses on enhancing user identity and providing high-value utilities for power users (like streamers). It introduces visual personalization through avatars, efficiency through keyboard shortcuts, community visibility via an activity feed, and enhanced security with account lockouts.

## Functional Requirements

### 1. User Avatars
- **Upload:** Users can upload a profile picture (JPG, PNG) from their Profile page.
- **Display:** Avatars appear in the navbar (small circle), on soundboard cards in the gallery, and next to comments.
- **Default:** A generic placeholder is used if no avatar is uploaded.

### 2. Keyboard Hotkeys
- **Assignment:** In the "Sound Settings" modal, users can assign a single key (0-9, A-Z) to a sound.
- **Trigger:** Pressing the assigned key while viewing the soundboard triggers the sound playback.
- **Feedback:** Visual "press" animation on the sound card when triggered via hotkey.

### 3. Community Activity Feed
- **Feed:** A new section on the Home page showing the last 10-20 major actions across the platform.
- **Events:** "User X created board Y", "User Z added 5 sounds to board A", "New user joined".
- **Real-time-ish:** Updated on every page load (no WebSockets required for now).

### 4. Account Lockout Security
- **Detection:** Track failed login attempts per user.
- **Lockout:** After 5 consecutive failures, the account is locked for 15 minutes.
- **Notification:** Inform the user they are locked out and when they can try again.

## Technical Considerations
- **Database:**
  - `users` table: `avatar_path` (text), `failed_login_attempts` (int), `lockout_until` (timestamp).
  - `sounds` table: `hotkey` (char).
  - New table `activities`: `id`, `user_id`, `action_type`, `target_id`, `description`, `created_at`.
- **File System:** Store avatars in `static/uploads/avatars/`.
- **Keyboard Events:** Use global `keydown` listeners in `view.html`.

## Acceptance Criteria
- Profile picture is successfully saved and displayed globally.
- Pressing 'A' plays the sound assigned to 'A' on the current board.
- The Home page correctly lists the most recent community actions.
- After 5 bad passwords, the login form rejects even correct passwords for 15 mins.

## Out of Scope
- Global hotkeys (must be on the browser tab).
- Cropping/Editing avatars in-browser.
