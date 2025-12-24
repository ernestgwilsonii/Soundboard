# Track Plan: Version 2.0 - Playlists

## Phase 1: Models and Database for Playlists
- [x] Task: Add `playlists` and `playlist_items` tables via `migrate.py`. ee182bf
- [x] Task: Create `Playlist` and `PlaylistItem` models in `app/models.py`. a1c9696
- [x] Task: Implement CRUD methods for Playlists. a1c9696
- [x] Task: Create unit tests for Playlist relationships. a1c9696
- [ ] Task: Conductor - User Manual Verification 'Playlist Models' (Protocol in workflow.md)

## Phase 2: User Interface and Sidebar
- [x] Task: Create `/playlists` dashboard and `create_playlist.html` form. 9b9b8a4
- [x] Task: Update Sidebar to include a "My Playlists" section. 9b9b8a4
- [x] Task: Implement the "Add to Playlist" modal/dropdown on sound cards. 9b9b8a4
- [x] Task: Create the Playlist View page (`view_playlist.html`). 9b9b8a4
- [x] Task: Conductor - User Manual Verification 'Playlist UI' (Protocol in workflow.md) 9b9b8a4

## Phase 3: Playback Logic (Sequence & Shuffle)
- [x] Task: Update `view.html` and `view_playlist.html` JS to support sound queues. 9b9b8a4
- [x] Task: Implement "Play All" and "Shuffle" buttons. 9b9b8a4
- [x] Task: Ensure sequential playback respects sound settings (trimming, volume). 9b9b8a4
- [x] Task: Conductor - User Manual Verification 'Sequential Playback' (Protocol in workflow.md) 9b9b8a4
