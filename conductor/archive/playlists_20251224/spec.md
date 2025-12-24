# Track Specification: Version 2.0 - Playlists

## Overview
This track introduces the ability for users to create "Playlists" of sounds. A playlist is an ordered collection of sounds (potentially from different soundboards) that can be played in sequence or shuffled.

## Functional Requirements

### 1. Playlist Management (CRUD)
- **Create:** Logged-in users can create new playlists with a name and optional description.
- **Add/Remove Sounds:** Users can add any sound they have access to (their own or public) to a playlist.
- **Delete:** Users can delete their playlists.
- **Visibility:** Playlists can be private or public (sharing enabled).

### 2. Sequential & Shuffle Playback
- **Play All:** A button to start the playlist from the beginning.
- **Automatic Advance:** When one sound ends, the next one in the list starts automatically (respecting trimming settings).
- **Shuffle Mode:** Toggle to play sounds in a random order.
- **Loop Playlist:** Option to repeat the entire playlist once finished.

### 3. Navigation and Integration
- **My Playlists:** A new section in the Sidebar and User Dashboard to manage playlists.
- **Add to Playlist Button:** A small "+" icon on every sound card (in View and Gallery pages) to quickly add a sound to an existing or new playlist.

## Technical Considerations
- **Database (Soundboards DB):**
  - New table `playlists`: `id`, `user_id`, `name`, `description`, `is_public`, `created_at`.
  - New table `playlist_items`: `id`, `playlist_id`, `sound_id`, `display_order`.
- **Frontend Playback:**
  - Update the JavaScript playback engine to handle a "Queue" of sounds.
  - Maintain a state for the currently playing playlist index.

## Acceptance Criteria
- Users can create a playlist and add sounds to it.
- Clicking "Play All" triggers sounds one after another.
- Shuffle mode correctly randomizes the sequence.
- Users can see their playlists in the global sidebar.

## Out of Scope
- Shared/Collaborative playlists (multiple owners).
- Exporting playlists as single audio files.
