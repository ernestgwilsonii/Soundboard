# Track Specification: Version 2.5 - Audio Intelligence & Visual Polish

## Overview
This track addresses the remaining core architectural and UX goals of the project. It introduces a backend "post-processing" pipeline for audio files to fulfill the "AI-Ready" goal and implements a visual Icon Picker to replace manual text entry for icons.

## Functional Requirements

### 1. Audio Processing Pipeline (AI-Ready Hooks)
- **Metadata Extraction:** Automatically extract audio metadata (duration, sample rate) upon upload using a library like `mutagen`.
- **Processing Hooks:** Create a structured `AudioProcessor` utility that can be easily extended with AI features (transcription, normalization, tagging) in the future.
- **Normalization (Optional):** If possible (depending on environment), implement a stub or basic volume normalization hook.

### 2. Visual Icon Picker
- **Browse & Select:** Instead of typing "fas fa-music", users should see a modal or searchable dropdown with FontAwesome icons.
- **Unified UI:** Apply the picker to Soundboard creation/editing and Sound uploads.

### 3. Enhanced Theming
- **Theme Presets:** Allow users to choose from presets (e.g., "Dark Mode", "Neon", "Minimalist") that apply custom CSS classes to the soundboard view.

## Technical Considerations
- **Dependencies:** Add `mutagen` to `requirements.txt`.
- **Models:** Add `theme_preset` to the `Soundboard` table (optional but recommended).
- **Frontend:** Use a JSON list of FontAwesome icons to populate a custom picker modal.

## Acceptance Criteria
- Uploading a sound automatically populates its `end_time` (duration) metadata.
- Users can create a soundboard by clicking an icon from a list instead of typing a name.
- Changing a soundboard's theme preset immediately updates its visual style in the view page.
