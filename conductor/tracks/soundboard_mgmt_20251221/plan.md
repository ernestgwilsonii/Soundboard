# Track Plan: Soundboard Management and File Uploads

## Phase 1: Soundboard and Sound Models
- [ ] Task: Implement `Soundboard` model in `app/models.py` with methods for save, delete, and retrieval.
- [ ] Task: Implement `Sound` model in `app/models.py` with methods for save, delete, and retrieval.
- [ ] Task: Add tests for `Soundboard` and `Sound` model CRUD operations.
- [ ] Task: Conductor - User Manual Verification 'Soundboard and Sound Models' (Protocol in workflow.md)

## Phase 2: Soundboard Blueprint and Creation
- [ ] Task: Create `app/soundboard/` directory and `app/soundboard/forms.py` for creation/edit forms.
- [ ] Task: Create the `soundboard` blueprint and register it in `app/__init__.py`.
- [ ] Task: Implement route and template for creating a new soundboard.
- [ ] Task: Implement a "Dashboard" or "My Soundboards" page.
- [ ] Task: Conductor - User Manual Verification 'Soundboard Blueprint and Creation' (Protocol in workflow.md)

## Phase 3: Sound Uploads and File Handling
- [ ] Task: Configure upload folder and allowed extensions in `config.py`.
- [ ] Task: Implement sound upload route and form.
- [ ] Task: Implement secure file saving logic.
- [ ] Task: Implement sound deletion (including file removal).
- [ ] Task: Conductor - User Manual Verification 'Sound Uploads and File Handling' (Protocol in workflow.md)

## Phase 4: Soundboard View and Playback
- [ ] Task: Implement the interactive soundboard view template.
- [ ] Task: Add JavaScript to handle icon clicks and audio playback.
- [ ] Task: Implement route to serve uploaded audio files if not using static directly.
- [ ] Task: Add delete/edit buttons to the soundboard view for owners.
- [ ] Task: Conductor - User Manual Verification 'Soundboard View and Playback' (Protocol in workflow.md)
