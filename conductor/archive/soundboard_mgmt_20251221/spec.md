# Track Specification: Soundboard Management and File Uploads

## Overview
This track implements the core functionality of the Soundboard Website, enabling users to create, manage, and interact with personalized soundboards. Users can upload various audio formats and customize their boards with a mix of library-provided and custom icons.

## Functional Requirements
- **Soundboard CRUD:**
    - Logged-in users can create new soundboards with a name and a chosen icon.
    - Users can view a list/grid of their own soundboards and browse public ones.
    - Owners can rename boards and update their primary icon.
    - Owners can delete soundboards, which also removes all associated sounds and files.
- **Audio Management:**
    - Support for uploading audio files in MP3, WAV, and OGG formats.
    - Secure storage of audio files in a structured directory system.
    - Users can name each sound and assign it an icon.
- **Icon Customization:**
    - Integration with Font Awesome for a searchable icon library.
    - Support for small custom image uploads (PNG, JPG) to be used as icons.
- **Interactive UI:**
    - A responsive grid-based interface for soundboards.
    - Instant audio playback when an icon is clicked.

## Non-Functional Requirements
- **Security:** Strict ownership checks for all CRUD operations. Validate all uploaded files for type and size (e.g., max 5MB per audio file).
- **Performance:** Ensure low-latency playback by optimizing sound loading (e.g., using audio preloading where appropriate).

## Acceptance Criteria
- A user can create a soundboard and see it in their dashboard.
- A user can upload an MP3 file, assign it an icon, and hear it play when clicked.
- A user cannot edit or delete a soundboard they do not own.
- Deleting a soundboard successfully removes its database record and all associated files from the server.

## Out of Scope
- Real-time collaboration on soundboards.
- Advanced audio editing (trimming, fading) within the browser.