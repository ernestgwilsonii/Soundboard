# Plan: Live Soundboard Collaboration

Real-time collaboration enabling multiple users to manage and interact with a soundboard simultaneously.

## Phase 1: Real-Time Infrastructure (MVP)
- [x] **Dependency Setup**: Add `flask-socketio` and `python-socketio` to `requirements.txt`.
- [x] **App Configuration**: Initialize `SocketIO` in the Flask app factory (`app/__init__.py`).
- [x] **Database Schema**: Add `board_collaborators` table to `schema_soundboards.sql` and update `models.py`.
- [x] **Collaboration API**: 
    - [x] Endpoint to invite a user to a board.
    - [x] Endpoint to remove a collaborator.
- [x] **WebSocket Basics**: 
    - [x] `join_room` when viewing a soundboard.
    - [x] Presence system: Track and broadcast "Who's Online".
    - [x] Broadcast notification when a collaborator joins/leaves.

## Phase 2: Action Synchronization
- [x] **Live Edit Sync**: Broadcast WebSocket events when a sound is added, edited, or deleted.
- [x] **Presence Indicators**: Show visual cues on the UI when a collaborator is active.
- [x] **Atomic Locking**: Implement "Slot Locking" (WebSocket event `lock_sound`) to prevent concurrent edits of the same sound.

## Phase 3: Conflict Resolution & UI Polish
- [ ] **Undo/Redo Log**: Track recent collaborative actions for quick recovery.
- [ ] **Live Chat/Activity Overlay**: A small overlay showing recent actions (e.g., "User A uploaded 'Meme.mp3'").
- [ ] **Notification Integration**: Push in-app notifications when invited to collaborate.

## Verification Plan
- [ ] **Unit Tests**: Test `BoardCollaborator` model and permissions logic.
- [ ] **Integration Tests**: Verify WebSocket event broadcasting using a Python socketio client.
- [ ] **E2E Tests**: Use Playwright to simulate two browser instances interacting with the same board.
