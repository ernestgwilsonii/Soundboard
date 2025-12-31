# Track Specification: Version 3.5 - Content Intelligence & Discovery

## Overview
This track focuses on data quality and the intelligence of the platform's discovery mechanisms. It ensures all community content meets a high standard of volume consistency and makes it easier for users to find what is currently popular.

## Functional Requirements

### 1. Automated Audio Normalization
- **Volume Consistency:** Every uploaded audio file must be analyzed and normalized to a target loudness (e.g., -20 LUFS or peak normalization) to prevent "ear-blasting" when switching between sounds.
- **Backend Task:** Implement this in the `AudioProcessor.normalize()` hook using `pydub`. 
- **Requirement:** This requires `ffmpeg` to be installed on the system for handling compressed formats like MP3/OGG.

### 2. "Trending" Discovery Algorithm
- **Weighted Popularity:** Implement a new "Trending" sort order in the Gallery.
- **Algorithm:** Score = (Ratings * 5) + (Follows * 10) + (Recent Comments * 2).
- **Time Decay:** Content from the last 7 days should be weighted higher to ensure the list stays fresh.

### 3. Real-Time Form Validation
- **Instant Feedback:** As users type their username or email during signup, the site should check availability via AJAX and show a green check or red error immediately.
- **Strength Meter:** Add a password strength indicator.
- **Live Board Validation:** Ensure soundboard names are unique for that user as they type.

## Technical Considerations
- **Dependencies:** Add `pydub` to `requirements.txt`.
- **API:** Create a new internal endpoint `/auth/check-availability` for live validation.
- **Database:** No new tables required, but `Soundboard.get_public()` will need complex SQL logic for the trending score.

## Acceptance Criteria
- Uploading a very quiet or very loud sound results in a file that plays at a standard, comfortable volume.
- The Gallery "Sort By" dropdown includes "Trending".
- The Signup form shows "Username already taken" before the user even clicks "Register".
