# Track Plan: Version 2.0 - Tagging System

## Phase 1: Models and Database for Tagging
- [x] Task: Create `tags` and `soundboard_tags` tables via `migrate.py`. ee920ea
- [x] Task: Create `Tag` model in `app/models.py`. a1c9696
- [x] Task: Add tagging methods to `Soundboard` model (`add_tag`, `remove_tag`, `get_tags`). a1c9696
- [x] Task: Create unit tests for tagging relationships. a1c9696
- [x] Task: Conductor - User Manual Verification 'Tagging Models' (Protocol in workflow.md) a1c9696

## Phase 2: Tag UI and CRUD
- [x] Task: Update `SoundboardForm` to include a `tags` field. 9b9b8a4
- [x] Task: Implement tag processing logic in Create/Edit routes (parse comma-separated strings). 9b9b8a4
- [x] Task: Update `view.html` to display tag badges. 9b9b8a4
- [x] Task: Add a "Popular Tags" component to the Sidebar. 9b9b8a4
- [ ] Task: Conductor - User Manual Verification 'Tag CRUD and UI' (Protocol in workflow.md)

## Phase 3: Tag-Based Discovery and Search
- [x] Task: Create `/soundboard/tag/<tag_name>` route to filter boards. ee920ea
- [x] Task: Update `Soundboard.search()` to include tags in the query logic. ee920ea
- [x] Task: Display tag badges on Gallery and Search result cards. ee920ea
- [ ] Task: Conductor - User Manual Verification 'Tag Discovery' (Protocol in workflow.md)
