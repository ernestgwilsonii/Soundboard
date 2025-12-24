# Track Plan: Version 2.0 - Social Community Features

## Phase 0: Documentation and Automation
- [x] Task: Reorganize and format `README.md` (Platinum Rule at top, numbered Golden Rules). 0d65a25
- [x] Task: Create a `migrate.py` utility to automate future schema updates. 0d65a25

## Phase 1: Database and Models for Social [checkpoint: 0d65a25]
- [x] Task: Create `ratings` and `comments` tables in `app/schema_soundboards.sql`. 8fb0d36
- [x] Task: Create `Rating` and `Comment` models in `app/models.py`. 0d65a25
- [x] Task: Add methods to `Soundboard` model to fetch average rating and comments list. 0d65a25
- [x] Task: Create unit tests for social relationships and models. 0d65a25
- [x] Task: Conductor - User Manual Verification 'Database and Models for Social' (Protocol in workflow.md) 0d65a25

## Phase 2: Ratings UI and API [checkpoint: d82f4c0]
- [x] Task: Implement the `/soundboard/<id>/rate` POST endpoint (AJAX). d82f4c0
- [x] Task: Create a star-rating component in `templates/soundboard/view.html`. d82f4c0
- [x] Task: Add logic to update the average rating display on the page. d82f4c0
- [x] Task: Update the Gallery and Search templates to show average ratings. d82f4c0
- [x] Task: Conductor - User Manual Verification 'Ratings UI and API' (Protocol in workflow.md) d82f4c0

## Phase 3: Comments UI and Moderation
- [x] Task: Create the `CommentForm` in `app/soundboard/forms.py`. 0d65a25
- [x] Task: Implement the `/soundboard/<id>/comment` POST route. ee920ea
- [x] Task: Create the comments display section in `templates/soundboard/view.html`. ee920ea
- [x] Task: Implement the `/comment/<id>/delete` route with permission checks. ee920ea
- [x] Task: Add "Delete" buttons to comments based on permissions (Owner/Admin/Self). ee920ea
- [x] Task: Conductor - User Manual Verification 'Comments UI and Moderation' (Protocol in workflow.md) ee920ea
