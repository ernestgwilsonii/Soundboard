# Track Plan: Version 3.5 - Content Intelligence & Discovery

## Phase 1: Audio Intelligence (Normalization) [checkpoint: 4485521]
- [x] Task: Install `pydub` and update `requirements.txt`. 35d223f
- [x] Task: Implement `AudioProcessor.normalize(file_path)` using `pydub`. 4485521
- [x] Task: Create a test suite to verify volume leveling for different file types. abdf55d
- [x] Task: Conductor - User Manual Verification 'Audio Normalization' 4485521

## Phase 2: Trending Discovery Engine
- [x] Task: Update `Soundboard` model with a `get_trending()` method. 7dd0771
- [x] Task: Integrate "Trending" sort option into the `/soundboard/gallery` route and template. 7dd0771
- [ ] Task: Update the Home page "Featured" fallback to prefer Trending boards over Newest.
- [~] Task: Conductor - User Manual Verification 'Trending Algorithm'

## Phase 3: Real-Time UI Validation
- [x] Task: Create the `/auth/check-availability` AJAX route. 656332e
- [x] Task: Build `app/static/js/form_validator.js` for live field feedback. 656332e
- [x] Task: Integrate the validator into the Signup and Soundboard Create templates. 656332e
- [x] Task: Add a visual password strength meter to the Signup form. 656332e
- [x] Task: Conductor - User Manual Verification 'Live Validation' 656332e
