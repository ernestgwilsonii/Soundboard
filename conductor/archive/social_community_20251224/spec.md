# Track Specification: Version 2.0 - Social Community Features

## Overview
This track initiates Version 2.0 by introducing community interaction features. Users will be able to leave comments on public soundboards and provide numeric ratings, helping to identify the most popular and high-quality content.

## Functional Requirements

### 1. Soundboard Ratings
- **Star Rating System:** Users can rate any public soundboard on a scale of 1 to 5 stars.
- **Average Display:** The Soundboard View page and Gallery will display the average star rating and total number of ratings.
- **Single Vote:** Each authenticated user can only rate a specific soundboard once (but can change their rating).

### 2. User Comments
- **Comment Section:** Add a comments section at the bottom of the Soundboard View page.
- **Threaded View:** Simple flat list of comments ordered by date (newest first).
- **Moderation (Delete):**
  - Users can delete their own comments.
  - Soundboard owners can delete any comment on their board.
  - Administrators can delete any comment site-wide.
- **Character Limit:** Comments are restricted to 500 characters.

## Technical Considerations
- **Database (Soundboards DB):**
  - New table `ratings`: `id`, `user_id`, `soundboard_id`, `score`, `created_at`.
  - New table `comments`: `id`, `user_id`, `soundboard_id`, `text`, `created_at`.
- **Frontend:**
  - Font Awesome for star icons.
  - AJAX for submitting ratings to avoid page refresh.
  - Standard form submission for comments (or AJAX if preferred for UX).

## Acceptance Criteria
- Users can click stars to submit a rating.
- Ratings update the average display instantly (via AJAX) or on refresh.
- Comments appear immediately after posting.
- Owners and Admins successfully see the 'Delete' option on comments.
- Average ratings are visible in the Gallery grid.

## Out of Scope
- Replying to comments (nested threads).
- Image uploads in comments.
- Upvoting/Downvoting comments.
