# Track Plan: Version 2.5 - Audio Intelligence & Visual Polish

## Phase 1: Audio Processing Architecture [checkpoint: da5c3fa]
- [x] Task: Install `mutagen` and update `requirements.txt`. 3924b23
- [x] Task: Create `app/utils/audio.py` with an `AudioProcessor` utility class. efdd6e4
- [x] Task: Integrate the processing hook into the sound upload route. f5b8ee2
- [x] Task: Verify that audio duration is automatically extracted and saved. f5b8ee2
- [x] Task: Conductor - User Manual Verification 'Audio Processing' 33f1268

## Phase 2: Visual Icon Picker
- [ ] Task: Create a JSON configuration of supported FontAwesome icons.
- [ ] Task: Build a reusable JavaScript icon picker modal.
- [ ] Task: Update Soundboard and Sound forms to use the icon picker.
- [ ] Task: Conductor - User Manual Verification 'Icon Picker UI'

## Phase 3: Enhanced Theming
- [ ] Task: Add `theme_preset` column to the `soundboards` table.
- [ ] Task: Create a theme-specific CSS file with at least 3 presets.
- [ ] Task: Update the soundboard view page to apply the selected preset.
- [ ] Task: Conductor - User Manual Verification 'Visual Themes'
