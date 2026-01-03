# Plan: Live Visual Reactions (Emoji Bursts)

Enable users to send real-time emoji reactions that animate across the screen for all participants.

## Phase 1: Real-Time Transport
- [ ] **WebSocket Event**: Add `send_reaction` event to `app/socket_events.py`.
- [ ] **Broadcasting**: Broadcast the reaction emoji and user info to the soundboard room.

## Phase 2: Frontend Animation System
- [ ] **CSS Animations**: Create "burst" and "float-up" keyframes in `static/css/themes.css`.
- [ ] **JS Implementation**: Add `renderReaction(emoji)` to `CollaborationManager` in `collaboration.js`.
- [ ] **DOM Management**: Dynamically create and clean up reaction elements.

## Phase 3: User Interface
- [ ] **Reaction Bar**: Add a floating emoji picker bar to `templates/soundboard/view.html`.
- [ ] **Polish**: Ensure reactions are throttled to prevent spam abuse.

## Verification
- [ ] **Manual Test**: Open two windows and verify emojis sent from one appear in both.
- [ ] **E2E Test**: Playwright test simulating simultaneous emoji clicks.
