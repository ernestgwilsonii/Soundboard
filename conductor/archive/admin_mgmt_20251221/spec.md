# Track Specification: Administrator Dashboard and User Management

## Overview
This track implements a centralized administrative interface, allowing authorized system managers to oversee the user base and moderate all platform content. It establishes a clear permission hierarchy and provides tools for maintenance and security.

## Functional Requirements
- **Administrative Access Control:**
    - Implementation of an `@admin_required` decorator to protect administrative routes.
    - Enforcement of role-based access using the `role` field in the `User` model.
- **User Management Dashboard:**
    - A dedicated page (`/admin/users`) listing all registered users with their status and roles.
    - **Account Controls:** Enable or disable user accounts to prevent login without data deletion.
    - **Role Management:** Promote users to 'admin' or demote them to 'user'.
    - **Password Management:** Allow admins to set new passwords for any user account.
- **Global Content Moderation:**
    - An administrative view of all soundboards on the platform.
    - Full CRUD overrides allowing admins to edit or delete any soundboard or sound file, regardless of ownership.
- **Navigation:**
    - A visible "Admin Dashboard" link in the navbar, appearing only for authenticated administrators.

## Non-Functional Requirements
- **Security:** Strict server-side verification for every administrative action. Unauthorized access attempts to `/admin` routes should redirect to the home page with a warning.
- **Logging:** All administrative actions (e.g., role changes, account disabling) must be logged to `logs/soundboard.log` including the admin's ID.

## Acceptance Criteria
- A user with the 'admin' role can access the dashboard and see all other users.
- Disabling a user account immediately prevents that user from logging in or maintaining a session.
- An admin can successfully rename or delete a soundboard they did not create.
- Regular users trying to access `/admin` routes are blocked and redirected.

## Out of Scope
- Granular permissions (e.g., custom roles with specific subsets of admin rights).
- Automated user banning based on activity.
