# Track Specification: Featured Soundboard and Dynamic Sidebar

## Overview
This track polishes the navigation and discovery features of the platform. It introduces a dynamic sidebar (burger menu) for global access to personal and community content, and an administrator-controlled "Featured Soundboard" to highlight quality content on the home page.

## Functional Requirements
- **Administrator Featured Board:**
    - A settings page for administrators to select a specific public soundboard ID as "Featured".
    - Fallback logic: If no board is selected, the most recent public board is automatically featured.
    - Display a "Featured" badge on the highlighted board on the home page.
- **Dynamic Sidebar (Burger Menu):**
    - A globally accessible sidebar containing three primary sections:
        1. **My Soundboards:** A direct list of the authenticated user's own boards.
        2. **Favorites & Pinned:** A personalized list of boards the user has marked for quick access.
        3. **Explore Public Boards:** A comprehensive list of all public boards, grouped by creator and sorted alphabetically.
- **Favorites Management:**
    - Users can "Pin" or "Favorite" any public soundboard.
    - A toggle button on the soundboard view page to add/remove from favorites.
    - Database support for tracking user-soundboard favorite relationships.

## Functional Requirements (UI/UX)
- Responsive burger menu implementation (mobile-friendly).
- Smooth transitions for opening/closing the sidebar.
- Consistent rendering of icons (library vs custom) in the sidebar list.

## Acceptance Criteria
- Administrators can change the featured soundboard via the UI.
- Users can see their own boards at the top of the sidebar.
- Users can mark a public board as a favorite and see it in their "Pinned" section.
- The sidebar accurately reflects alphabetical sorting (by user, then by board name).

## Out of Scope
- Drag-and-drop reordering within the sidebar list (sorting is automatic).
- Social sharing integrations from the sidebar.
