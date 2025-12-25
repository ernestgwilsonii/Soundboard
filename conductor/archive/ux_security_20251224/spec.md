# Track Specification: Version 2.2 - UX Polish and Security Hardening

## Overview
This track strengthens the platform's security and provides users with deeper personalization options. It introduces rate limiting to prevent automated abuse, richer user profiles with social connectivity, and custom visual themes for soundboards.

## Functional Requirements

### 1. Rate Limiting (Security)
- **Global Limits:** Implement a limit on sensitive routes (Login, Register, Sound Upload, Commenting).
- **Graceful Rejection:** Show a "Too Many Requests" (429) error or flash message when limits are exceeded.
- **Whitelist:** Ensure administrators are not restricted by rate limits.

### 2. Enhanced User Profiles
- **Profile Bio:** Users can add a short biography (max 250 chars) to their profile.
- **Social Links:** Fields for Twitter/X, YouTube, and Website.
- **Public Profile View:** A public-facing profile page where others can see a user's bio, avatar, and their public soundboards.

### 3. Soundboard Themes
- **Color Selection:** Owners can choose a "Theme Color" for their soundboard.
- **Custom CSS:** The selected color is applied to buttons, badges, and card borders on the soundboard's View page.
- **Presets:** Provide 5-6 default professional color presets (e.g., Midnight, Forest, Sunset, Classic Blue).

## Technical Considerations
- **Security:** Use `Flask-Limiter` for robust, IP-based rate limiting.
- **Database:**
  - `users` table: `bio` (text), `social_x` (text), `social_youtube` (text), `social_website` (text).
  - `soundboards` table: `theme_color` (text, hex code).
- **Frontend:**
  - Dynamic inline CSS in `view.html` to apply the `theme_color`.
  - Update `UpdateProfileForm` to include bio and social link fields.

## Acceptance Criteria
- Multiple rapid login attempts trigger a "Rate limit exceeded" warning.
- User bio and social links appear on their public profile page.
- Changing a soundboard's theme color instantly updates its primary buttons and badges.
- All new profile fields are validated for length and format (URLs).

## Out of Scope
- Full dark/light mode toggle (to be handled in a separate UI track).
- Custom background images for soundboards.
