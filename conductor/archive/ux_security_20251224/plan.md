# Track Plan: Version 2.2 - UX Polish and Security Hardening

## Phase 1: Rate Limiting
- [x] Task: Install `Flask-Limiter` and update `requirements.txt`. ee182bf
- [x] Task: Initialize `Limiter` in `app/__init__.py`. a19bf08
- [x] Task: Apply limits to Auth routes (Login, Register). a19bf08
- [x] Task: Apply limits to Soundboard interaction routes (Upload, Comment, Rate). a19bf08
- [x] Task: Conductor - User Manual Verification 'Rate Limiting' (Protocol in workflow.md) a19bf08

## Phase 2: Rich User Profiles
- [x] Task: Add profile columns (bio, social links) to `users` table via `migrate.py`. 55d9b2b
- [x] Task: Update `User` model and `UpdateProfileForm` with new fields. 55d9b2b
- [x] Task: Implement the public profile route `/user/<username>`. 55d9b2b
- [x] Task: Update `profile.html` and `update_profile.html` templates. 55d9b2b
- [x] Task: Conductor - User Manual Verification 'Rich Profiles' (Protocol in workflow.md) 55d9b2b

## Phase 3: Soundboard Themes
- [x] Task: Add `theme_color` column to `soundboards` table via `migrate.py`. 106b08f
- [x] Task: Update `Soundboard` model and `SoundboardForm` to support theme colors. 106b08f
- [x] Task: Implement dynamic CSS in `view.html` to apply the selected theme. 106b08f
- [x] Task: Update Edit Soundboard page to include color selection. 106b08f
- [x] Task: Conductor - User Manual Verification 'Custom Themes' (Protocol in workflow.md) 106b08f
