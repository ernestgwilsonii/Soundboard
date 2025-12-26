# Track Plan: Version 2.4 - Community Polish and Notifications

## Phase 1: Notification System
- [x] Task: Create `notifications` table via `migrate.py`. b327e86
- [x] Task: Create `Notification` model in `app/models.py`. a6109bc
- [x] Task: Create a `add_notification(user_id, type, message, link)` helper. a6109bc
- [x] Task: Hook into `post_comment` and `rate_board` routes to send notifications. 36244af
- [x] Task: Implement navbar bell icon and dropdown in `base.html`. 36244af
- [x] Task: Create AJAX route `/notifications/mark_read` and `/notifications/unread_count`. 36244af
- [x] Task: Conductor - User Manual Verification 'Notification System' (Protocol in workflow.md) 36244af

## Phase 2: Account Deactivation
- [x] Task: Implement `User.delete()` method to handle recursive cleanup (boards, files, comments). 576b307
- [x] Task: Create the `/auth/delete_account` route and a confirmation form. 576b307
- [x] Task: Add "Delete Account" button to the Profile page. 576b307
- [x] Task: Conductor - User Manual Verification 'Account Deactivation' (Protocol in workflow.md) 576b307

## Phase 3: Advanced Discovery & Errors
- [x] Task: Update `Soundboard.get_public()` and `search()` to support dynamic ordering. 106b08f
- [x] Task: Add "Sort By" dropdown to Gallery and Search templates. 106b08f
- [x] Task: Create `templates/404.html` and `templates/500.html`. 106b08f
- [x] Task: Register global error handlers in `app/__init__.py`. 106b08f
- [x] Task: Conductor - User Manual Verification 'Discovery and Error Pages' (Protocol in workflow.md) 6bf7548
