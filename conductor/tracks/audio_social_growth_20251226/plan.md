# Track Plan: Version 3.0 - Visual Audio & Social Connectivity

## Phase 1: Social Connectivity (Enhanced Following)
- [x] Task: Create `follows` table via `migrate.py`. 4f64811
- [x] Task: Update `User` model with `follow()`, `unfollow()`, and relationship methods. b982c95
- [x] Task: Implement `/auth/follow/<username>` and `/auth/unfollow/<username>` routes. 04ef265
- [x] Task: Add "Follow" button and social counters to the Public Profile template. 1cd5ba2
- [x] Task: Implement `/auth/members` route and template. 9104b93
- [x] Task: Add "Browse Members" link to the sidebar for verified users. 9c98e52
- [x] Task: Create Followers and Following list templates and routes. ded21a7
- [x] Task: Add pagination (10/50), sorting, and search to the "Browse Members" page. 684dbfe
- [ ] Task: Conductor - User Manual Verification 'Social Following'

## Phase 2: Visual Audio Tools (WaveSurfer.js)
- [ ] Task: Integrate `WaveSurfer.js` CDN in `base.html`.
- [ ] Task: Create `app/static/js/waveform_editor.js`.
- [ ] Task: Update the "Sound Settings" modal to display the interactive waveform.
- [ ] Task: Sync waveform selection with the existing start/end time form fields.
- [ ] Task: Conductor - User Manual Verification 'Visual Trimming'

## Phase 3: Advanced Activity & Metadata
- [ ] Task: Update `migrate.py` to add `bitrate`, `file_size`, and `format` to `sounds` table.
- [ ] Task: Update `AudioProcessor` to extract advanced metadata.
- [ ] Task: Enhance the homepage "Community Activity" feed with polling and new event types.
- [ ] Task: Create a "Following" tab on the Home page.
- [ ] Task: Conductor - User Manual Verification 'Advanced Feed & Stats'

## Phase 4: Site-Wide UX Polish & Auth
- [ ] Task: Update Login logic to support both Username and Email as identity.
- [ ] Task: Replace all remaining native browser `confirm()` and `alert()` calls if any exist.
- [ ] Task: Conductor - User Manual Verification 'UX & Auth Polish'