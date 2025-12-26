# Track Specification: Version 2.4 - Community Polish and Notifications

## Overview
This final polish track enhances the communication layer between users and the platform. It introduces a notification system for social engagement, allows users to self-manage their account lifecycle, adds discovery depth with search filters, and ensures a professional experience with custom error handling.

## Functional Requirements

### 1. In-App Notification System
- **Alerts:** Users receive notifications when:
  - Someone comments on their soundboard.
  - Someone rates their soundboard.
- **Display:** A bell icon in the navbar with a badge showing the unread count.
- **Management:** A dropdown list where users can see the last 10 notifications and "Mark all as read".

### 2. Account Deactivation (The "Delete Account" feature)
- **Self-Service:** A "Delete My Account" button on the Profile Settings page.
- **Safety:** Requires users to type their password or a confirmation string to proceed.
- **Cleanup:** Permanently removes the user, their soundboards, sounds, playlists, and associated files from the server.

### 3. Advanced Search Filters
- **Sorting:** On the Search and Gallery pages, allow users to sort results by:
  - **Most Recent** (default).
  - **Highest Rated** (based on average star score).
  - **Alphabetical**.
- **UI:** A simple dropdown menu next to the "Search Results" title.

### 4. Professional Error Pages
- **Custom 404:** A themed "Page Not Found" page with a link back to the homepage.
- **Custom 500:** A themed "Internal Server Error" page that encourages users to report the issue.

## Technical Considerations
- **Database (Accounts DB):**
  - New table `notifications`: `id`, `user_id`, `type`, `message`, `link`, `is_read`, `created_at`.
- **Search Logic:** Update `Soundboard.search()` and `Soundboard.get_public()` to accept an `order_by` parameter.
- **Global Error Handlers:** Register `app.errorhandler(404)` and `app.errorhandler(500)` in `app/__init__.py`.

## Acceptance Criteria
- Receiving a comment triggers a notification for the board owner immediately.
- The notification badge updates without a page refresh (simple AJAX poll or on next load).
- Deleting an account successfully logs the user out and wipes all their data.
- Search results correctly re-order when selecting "Highest Rated".
- Accessing a non-existent URL shows the custom 404 page instead of the browser default.

## Out of Scope
- Push notifications (browser/mobile).
- Restoring a deleted account (permanent deletion only).
