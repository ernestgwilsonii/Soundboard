# Specification: Live Soundboard Collaboration

## Overview
Enable real-time synchronization between multiple users viewing or editing the same soundboard.

## Architecture
- **Transport**: WebSockets via `Flask-SocketIO`.
- **Rooms**: Each Soundboard ID will correspond to a SocketIO "Room".
- **Concurrency Control**: Optimistic slot-locking.

## Data Models
### BoardCollaborator
| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER | Primary Key |
| soundboard_id | INTEGER | FK to soundboards |
| user_id | INTEGER | FK to users |
| role | TEXT | 'editor' or 'viewer' |
| created_at | TIMESTAMP | |

## WebSocket Events
### Client to Server
- `join_board`: { "board_id": 123 }
- `leave_board`: { "board_id": 123 }
- `request_lock`: { "board_id": 123, "sound_id": 456 }
- `release_lock`: { "board_id": 123, "sound_id": 456 }

### Server to Client
- `presence_update`: List of active users in the room.
- `board_updated`: Signals that the board state has changed (trigger AJAX refresh or partial update).
- `slot_locked`: { "sound_id": 456, "user": "username" }
- `slot_released`: { "sound_id": 456 }

## Permission Matrix
| Action | Owner | Editor | Viewer | Anonymous |
|--------|-------|--------|--------|-----------|
| Play Sound | Yes | Yes | Yes | Yes (if public) |
| Add Sound | Yes | Yes | No | No |
| Delete Sound | Yes | Yes | No | No |
| Manage Collaborators | Yes | No | No | No |
| Delete Board | Yes | No | No | No |
