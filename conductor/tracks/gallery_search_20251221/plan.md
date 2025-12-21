# Track Plan: Public Soundboard Gallery and Global Search

## Phase 1: Model Update and Visibility Toggle
- [ ] Task: Add `is_public` column to the `soundboards` table in `app/schema_soundboards.sql`.
- [ ] Task: Update the `Soundboard` model in `app/models.py` to support the `is_public` field.
- [ ] Task: Update `SoundboardForm` in `app/soundboard/forms.py` to include the "Public" checkbox.
- [ ] Task: Update CRUD routes to correctly save and update the `is_public` status.
- [ ] Task: Conductor - User Manual Verification 'Model Update and Visibility Toggle' (Protocol in workflow.md)

## Phase 2: Public Gallery Implementation
- [ ] Task: Implement `Soundboard.get_public()` and `Soundboard.get_recent_public()` methods.
- [ ] Task: Create the `/gallery` route in `app/soundboard/routes.py` and its corresponding template.
- [ ] Task: Update the main index route (`/`) to display recent public soundboards.
- [ ] Task: Add a "Gallery" link to the navigation bar.
- [ ] Task: Conductor - User Manual Verification 'Public Gallery Implementation' (Protocol in workflow.md)

## Phase 3: Global Search Functionality
- [ ] Task: Implement a `search` helper or model method that performs the multi-criteria SQL search.
- [ ] Task: Create the `/search` route and its corresponding template.
- [ ] Task: Add a search bar to the home page and gallery page.
- [ ] Task: Verify that search results include board names, creator names, and sound names.
- [ ] Task: Conductor - User Manual Verification 'Global Search Functionality' (Protocol in workflow.md)

## Phase 4: Access Control and Final Polish
- [ ] Task: Ensure the `view` route allows anonymous access for public boards.
- [ ] Task: Verify that private boards are inaccessible to anyone but the owner.
- [ ] Task: Refine the UI for search results and the gallery grid.
- [ ] Task: Conductor - User Manual Verification 'Access Control and Final Polish' (Protocol in workflow.md)
