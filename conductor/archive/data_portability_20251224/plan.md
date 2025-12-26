# Track Plan: Version 2.3 - Portable Archives and AI Integration

## Phase 1: Archive Engine (Export)
- [x] Task: Create a `Packager` utility in `app/utils/packager.py` to generate ZIP archives. 2b5039b
- [x] Task: Implement manifest generation (JSON) including all soundboard/sound properties. 2b5039b
- [x] Task: Create the `/soundboard/<id>/export` route to download the pack. 2b5039b
- [x] Task: Add "Export to Pack" button to `templates/soundboard/edit.html`. 2b5039b
- [x] Task: Conductor - User Manual Verification 'Export Logic' (Protocol in workflow.md) 2b5039b

## Phase 2: Reconstruction Engine (Import)
- [x] Task: Create an `Importer` utility to validate and extract Soundboard Packs. 2b5039b
- [x] Task: Implement the `/soundboard/import` route and form. b327e86
- [x] Task: Add database reconstruction logic (creating boards, sounds, and tags from manifest). b327e86
- [x] Task: Add "Import Soundboard" button to the User Dashboard. b327e86
- [x] Task: Conductor - User Manual Verification 'Import Logic' (Protocol in workflow.md) b327e86

## Phase 3: AI Integration and Audio Polish
- [x] Task: Integrate audio normalization logic (format conversion) into the import process. b327e86
- [x] Task: Implement auto-transcription fallback for sounds with missing names. b327e86
- [x] Task: Create unit tests for the archive/unarchive cycle. b327e86
- [x] Task: Conductor - User Manual Verification 'AI and Audio Polish' (Protocol in workflow.md) b327e86
