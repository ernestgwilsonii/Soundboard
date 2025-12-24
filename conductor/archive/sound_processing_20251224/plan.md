# Track Plan: Version 2.0 - Advanced Sound Processing

## Phase 1: Database Migration and Model Updates
- [x] Task: Add new columns to `sounds` table via `migrate.py`. d82f4c0
- [x] Task: Update `Sound` model in `app/models.py` to include new playback fields. ee182bf
- [x] Task: Create unit tests for the updated `Sound` model. ee182bf
- [ ] Task: Conductor - User Manual Verification 'Database and Model Updates' (Protocol in workflow.md)

## Phase 2: Playback Engine Overhaul
- [x] Task: Update the `playSound` function in `templates/soundboard/view.html` to support volume and looping. a3c8f08
- [x] Task: Implement virtual trimming (start/end points) in the playback logic. a3c8f08
- [x] Task: Add a global "Stop All" button to the soundboard view. a3c8f08
- [x] Task: Conductor - User Manual Verification 'Playback Engine Overhaul' (Protocol in workflow.md) a3c8f08

## Phase 3: Configuration UI
- [x] Task: Create a "Sound Settings" modal in `templates/soundboard/edit.html`. ee182bf
- [x] Task: Implement an AJAX endpoint to save individual sound settings. ee182bf
- [x] Task: Connect the modal sliders/toggles to the persistence API. ee182bf
- [x] Task: Conductor - User Manual Verification 'Configuration UI' (Protocol in workflow.md) ee182bf
