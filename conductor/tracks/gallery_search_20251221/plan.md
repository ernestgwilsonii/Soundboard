# Track Plan: Public Soundboard Gallery and Global Search

## Phase 1: Model Update and Visibility Toggle [checkpoint: 5326853]
- [x] Task: Add `is_public` column to the `soundboards` table in `app/schema_soundboards.sql`. d505b47
- [x] Task: Update the `Soundboard` model in `app/models.py` to support the `is_public` field. 2c52de0
- [x] Task: Update `SoundboardForm` in `app/soundboard/forms.py` to include the "Public" checkbox. a12db8e
- [x] Task: Update CRUD routes to correctly save and update the `is_public` status. a656247
- [x] Task: Conductor - User Manual Verification 'Model Update and Visibility Toggle' (Protocol in workflow.md) 5326853

## Phase 2: Public Gallery Implementation [checkpoint: e245fb6]
- [x] Task: Implement `Soundboard.get_public()` and `Soundboard.get_recent_public()` methods. a73aac9
- [x] Task: Create the `/gallery` route in `app/soundboard/routes.py` and its corresponding template. f29c789
- [x] Task: Update the main index route (`/`) to display recent public soundboards. 003df28
- [x] Task: Add a "Gallery" link to the navigation bar. 512825b
- [x] Task: Conductor - User Manual Verification 'Public Gallery Implementation' (Protocol in workflow.md) e245fb6

## Phase 3: Global Search Functionality [checkpoint: e7df30a]
- [x] Task: Implement a `search` helper or model method that performs the multi-criteria SQL search. cf0c1cf
- [x] Task: Create the `/search` route and its corresponding template. bdc327a
- [x] Task: Add a search bar to the home page and gallery page. 922ed72
- [x] Task: Verify that search results include board names, creator names, and sound names. cf0c1cf
- [x] Task: Conductor - User Manual Verification 'Global Search Functionality' (Protocol in workflow.md) e7df30a

## Phase 4: Access Control and Final Polish
- [ ] Task: Ensure the `view` route allows anonymous access for public boards.
- [ ] Task: Verify that private boards are inaccessible to anyone but the owner.
- [ ] Task: Refine the UI for search results and the gallery grid.
- [ ] Task: Conductor - User Manual Verification 'Access Control and Final Polish' (Protocol in workflow.md)
