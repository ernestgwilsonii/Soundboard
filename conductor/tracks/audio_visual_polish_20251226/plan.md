# Track Plan: Version 2.5 - Audio Intelligence & Visual Polish

## Phase 1: Audio Processing Architecture [checkpoint: da5c3fa]
- [x] Task: Install `mutagen` and update `requirements.txt`. 3924b23
- [x] Task: Create `app/utils/audio.py` with an `AudioProcessor` utility class. efdd6e4
- [x] Task: Integrate the processing hook into the sound upload route. f5b8ee2
- [x] Task: Verify that audio duration is automatically extracted and saved. f5b8ee2
- [x] Task: Conductor - User Manual Verification 'Audio Processing' 33f1268

## Phase 2: Dynamic Icon Picker (Full Library) [checkpoint: 1ff68e8]
- [x] Task: Remove the manual `app/static/icons.json`. 15135
- [x] Task: Update `app/static/js/icon_picker.js` to dynamically fetch the full FontAwesome 6 Free icon set from a reliable metadata source. 3f2c511
- [x] Task: Enhance the Icon Picker UI with categories and high-performance filtering for the larger icon set. 3f2c511
- [x] Task: Update Soundboard and Sound forms to use the dynamic picker. 3f2c511
- [x] Task: Conductor - User Manual Verification 'Dynamic Icon Picker' 6cf560d

## Phase 3: Enhanced Theming
- [x] Task: Add `theme_preset` column to the `soundboards` table. cc8917b
- [x] Task: Create a theme-specific CSS file with at least 3 presets. 7d701e3
- [x] Task: Update the soundboard view page to apply the selected preset. 29974d2
- [~] Task: Conductor - User Manual Verification 'Visual Themes'

## Phase 4: Site-Wide UX Polish (Modern Dialogs)
- [ ] Task: Implement a global "Confirm" and "Alert" system using Bootstrap Modals or a library like SweetAlert2.
- [ ] Task: Replace all native browser `confirm()` and `alert()` calls with the new modern dialogs.
- [ ] Task: Conductor - User Manual Verification 'UX Polish'