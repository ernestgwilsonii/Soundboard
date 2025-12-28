# Track Plan: Version 3.5 - Content Intelligence & Discovery

## Phase 1: Audio Intelligence (Normalization)
- [x] Task: Install `pydub` and update `requirements.txt`. 35d223f
- [ ] Task: Implement `AudioProcessor.normalize(file_path)` using `pydub`.
- [ ] Task: Create a test suite to verify volume leveling for different file types.
- [ ] Task: Conductor - User Manual Verification 'Audio Normalization'

## Phase 2: Trending Discovery Engine
- [ ] Task: Update `Soundboard` model with a `get_trending()` method.
- [ ] Task: Integrate "Trending" sort option into the `/soundboard/gallery` route and template.
- [ ] Task: Update the Home page "Featured" fallback to prefer Trending boards over Newest.
- [ ] Task: Conductor - User Manual Verification 'Trending Algorithm'

## Phase 3: Real-Time UI Validation
- [ ] Task: Create the `/auth/check-availability` AJAX route.
- [ ] Task: Build `app/static/js/form_validator.js` for live field feedback.
- [ ] Task: Integrate the validator into the Signup and Soundboard Create templates.
- [ ] Task: Add a visual password strength meter to the Signup form.
- [ ] Task: Conductor - User Manual Verification 'Live Validation'
