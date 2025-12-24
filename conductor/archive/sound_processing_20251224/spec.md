# Track Specification: Version 2.0 - Advanced Sound Processing

## Overview
This track enhances the core soundboard experience by allowing users to customize the playback behavior of individual sounds. It introduces settings for looping, volume control, and basic start/end trimming without modifying the original files.

## Functional Requirements

### 1. Per-Sound Playback Settings
- **Looping:** Users can toggle "Loop" for any sound. When enabled, the sound repeats until manually stopped or another sound is triggered.
- **Volume Normalization:** Users can set a specific volume level (0% to 100%) for each sound to ensure consistent audio levels across the board.
- **Fade In/Out:** Optional fade effects (in milliseconds) to smooth the start and end of sounds.

### 2. Basic Sound Trimming
- **Start/End Points:** Users can specify a `start_time` and `end_time` (in seconds) for each sound.
- **Virtual Trimming:** The original audio file is preserved; the playback engine (JavaScript) handles skipping to the start point and stopping at the end point.

### 3. Management UI
- Update the "Edit Soundboard" page to include a "Settings" button/modal for each uploaded sound.
- Provide a simple UI (sliders and toggles) to configure these properties.

## Technical Considerations
- **Database (Soundboards DB):**
  - Update `sounds` table with new columns: `volume` (float), `is_loop` (boolean), `fade_in` (int), `fade_out` (int), `start_time` (float), `end_time` (float).
- **Frontend Playback Engine:**
  - Update the `playSound` function in `view.html` to respect these new properties using the Web Audio API or HTML5 Audio properties.
- **Migration:**
  - Use `migrate.py` to add these columns to the production database.

## Acceptance Criteria
- Sounds marked as "Loop" repeat correctly.
- Volume settings are accurately reflected during playback.
- Setting a "Start Time" skips the beginning of the audio file as expected.
- All settings persist after page refresh and across different users.

## Out of Scope
- Server-side audio processing (ffmpeg).
- Waveform visualization for trimming (to be considered for a future "UI Polish" track).
