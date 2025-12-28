# Track Specification: Version 3.0 - Visual Audio & Social Connectivity

## Overview
This major version focuses on deepening user engagement through a social graph (Following system) and providing professional-grade audio tools (Visual Waveform trimming). It aims to transition the site from a simple utility to a more interactive community platform.

## Functional Requirements

### 1. User Following System
- **Follow/Unfollow:** Users can follow other creators from their public profiles.
- **Social Counters:** Profiles will display "Followers" and "Following" counts.
- **Following Feed:** A new "Following" tab on the home page that shows soundboards and activity ONLY from people the user follows.

### 2. Visual Waveform Trimming (WaveSurfer.js)
- **Interactive Waveform:** In the "Sound Settings" modal, users will see a visual representation of the audio file.
- **Visual Trimming:** Users can drag handles on the waveform to set the `start_time` and `end_time` instead of typing numbers.
- **Real-time Preview:** Ability to play back only the selected segment within the modal.

### 3. Enhanced Community Activity
- **Rich Activity Feed:** Expand the homepage feed to include:
  - "User A followed User B"
  - "User X rated Soundboard Y"
  - "User Z joined the community"
- **High-Frequency Polling:** Update the feed automatically every 60 seconds without a page refresh.

### 4. Technical Metadata Expansion
- **Detailed Stats:** Extract and display:
  - File Size (MB)
  - Bitrate (kbps)
  - Audio Format (MPEG, WAV, etc.)
- **Storage in DB:** Store these fields in the `sounds` table during the `AudioProcessor` pipeline.

## Technical Considerations
- **Database:** 
  - New table `follows` in `accounts.sqlite3`: `follower_id`, `followed_id`, `created_at`.
  - Migration to add `bitrate`, `file_size`, `format` to `sounds` table.
- **Frontend:**
  - Include `WaveSurfer.js` via CDN.
  - Create specialized JS component for the Waveform Modal.
- **Backend:**
  - Update `AudioProcessor` to extract advanced metadata using `mutagen`.

## Acceptance Criteria
- Users can follow a creator and see their name in a "Following" list in the sidebar.
- The "Sound Settings" modal renders a waveform for any uploaded sound.
- Dragging on the waveform updates the Start/End time fields automatically.
- The home page activity feed shows at least 3 distinct types of social actions.
