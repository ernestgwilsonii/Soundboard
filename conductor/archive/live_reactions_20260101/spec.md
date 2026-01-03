# Specification: Live Visual Reactions

## Overview
A lightweight engagement feature allowing users to send emojis that float up the screen.

## WebSocket Events
### Client -> Server
`send_reaction`: { "board_id": 123, "emoji": "🔥" }

### Server -> Client
`receive_reaction`: { "emoji": "🔥", "user": "username" }

## UI/UX
- **Position**: Bottom-right floating bar.
- **Selection**: Default set of popular emojis: 🔥, 😂, 👏, ❤️, 😮, 🚀.
- **Animation**: Emoji appears at a random horizontal position at the bottom and floats upward while fading out over 2-3 seconds.
- **Throttling**: 500ms cooldown per user to prevent screen-flooding.
