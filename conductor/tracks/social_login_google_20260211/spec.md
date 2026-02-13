# Specification: Social Login Integration (Google)

## Objective
Implement a robust OAuth 2.0 social authentication system for the Soundboard platform, beginning with Google.

## Requirements
- **Extensibility:** The system must allow adding other providers (Facebook, GitHub, etc.) with minimal changes.
- **Conditional Activation:** Social login buttons must only appear if the provider is configured in the environment.
- **Account Linking:** If a user logs in via Google and their email already exists in the system, the accounts should be safely linked (after verifying ownership if necessary).
- **Security:** Must follow OAuth 2.0 best practices (state parameters, PKCE if applicable, secure token storage).
- **Graceful Degradation:** If no providers are configured, the standard email/password login remains the only option without errors.

## Technical Approach
- **Library:** `Flask-Dance` or `Authlib` (industry standard for Flask OAuth).
- **Configuration:** `.env` variables:
    - `GOOGLE_OAUTH_CLIENT_ID`
    - `GOOGLE_OAUTH_CLIENT_SECRET`
- **Database:** Update `User` model to store social IDs (e.g., `google_id`).
- **UI:** Partial template for social buttons in `templates/auth/login.html`.
