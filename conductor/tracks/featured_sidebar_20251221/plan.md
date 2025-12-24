# Track Plan: Featured Soundboard and Dynamic Sidebar

## Phase 1: Database and Model for Favorites [checkpoint: 1294de3]
- [x] Task: Create a `favorites` table in `app/schema_accounts.sql` (linking users to soundboards). e9e68f7
- [x] Task: Update the `User` model to include methods for adding, removing, and listing favorites. f43f44e
- [x] Task: Create unit tests for the favorites relationship. f43f44e
- [x] Task: Conductor - User Manual Verification 'Database and Model for Favorites' (Protocol in workflow.md) 1294de3

## Phase 2: Administrative Control for Featured Board [checkpoint: c1a090e]
- [x] Task: Create an `admin_settings` table or a simple config entry for the featured board ID. ac0fe97
- [x] Task: Implement the admin settings route and form to select the featured board. 4d2801e
- [x] Task: Implement the fallback logic in `Soundboard.get_featured()` model method. 2f569fe
- [x] Task: Update the home page template to render the "Featured" badge. 5e0bef1
- [x] Task: Conductor - User Manual Verification 'Administrative Control for Featured Board' (Protocol in workflow.md) c1a090e

## Phase 3: Dynamic Sidebar (Burger Menu) UI
- [ ] Task: Create a new global component/fragment for the sidebar.
- [ ] Task: Implement the "Burger" toggle button in the navbar.
- [ ] Task: Implement the "My Soundboards" section (alphabetical list).
- [ ] Task: Implement the "Explore" section (all public boards, grouped by user).
- [ ] Task: Add CSS/JS for responsive sidebar behavior.
- [ ] Task: Conductor - User Manual Verification 'Dynamic Sidebar (Burger Menu) UI' (Protocol in workflow.md)

## Phase 4: Favorites and Pinned Functionality
- [ ] Task: Implement the "Favorite/Pin" toggle button on the soundboard view page.
- [ ] Task: Create the AJAX or standard route to handle the toggle action.
- [ ] Task: Implement the "Favorites & Pinned" section in the sidebar.
- [ ] Task: Verify that pinning a board instantly updates the sidebar list.
- [ ] Task: Conductor - User Manual Verification 'Favorites and Pinned Functionality' (Protocol in workflow.md)
