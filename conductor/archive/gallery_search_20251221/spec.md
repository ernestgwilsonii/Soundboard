# Track Specification: Public Soundboard Gallery and Global Search

## Overview
This track introduces a public discovery layer to the platform. Users can now share their creations with the community by marking them as public. A global search functionality will allow users to find soundboards by name, creator, or even specific sound effects.

## Functional Requirements
- **Visibility Control:**
    - Add a `is_public` boolean field to the `Soundboard` model.
    - Update `SoundboardForm` to include a "Public" checkbox.
    - Allow users to toggle this status at any time via the edit form.
- **Public Gallery:**
    - **Dedicated Page:** A new `/gallery` route that displays all soundboards marked as public.
    - **Home Page Integration:** The home page (`/`) will now display a "Recent" selection of public soundboards.
- **Global Search:**
    - A search bar accessible from the gallery and home page.
    - Search results should include soundboards matching the name query, creator username, or containing sounds matching the sound name query.
- **Access Control:**
    - Public soundboards can be viewed and played by anyone (including anonymous users).
    - Editing and deleting remain restricted to the owner.

## Acceptance Criteria
- A user can mark a soundboard as public and see it appear in the gallery.
- A user can uncheck the public box and the board is immediately hidden from the gallery and search.
- An anonymous user can browse the gallery and play sounds from public boards.
- Searching for a creator or sound name returns the correct soundboards.

## Out of Scope
- Advanced search filters (e.g., filter by date, popularity).
- "Like" or "Favorite" functionality for public boards.
