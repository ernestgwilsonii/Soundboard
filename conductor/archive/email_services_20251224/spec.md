# Track Specification: Version 2.0 - Email Services

## Overview
This track transitions the platform from local prototyping to production-ready user management by integrating an email service. It enables critical security features: mandatory email verification for new accounts and a secure password reset flow via unique tokens.

## Functional Requirements

### 1. Email Integration
- **Infrastructure:** Integrate `Flask-Mail` or a compatible SMTP client.
- **Environment Config:** Support SMTP server details (host, port, user, password) via `.env`.
- **Async Sending:** (Optional but preferred) Send emails without blocking the main thread.

### 2. Account Verification
- **New Registrations:** Users are created in an `unverified` state.
- **Verification Email:** A unique, time-sensitive token is sent to the user's email upon signup.
- **Restricted Access:** Unverified users can log in but cannot create soundboards or post comments until verified.
- **Verification Route:** `/auth/verify/<token>` to activate the account.

### 3. Password Reset Flow
- **Request Page:** A "Forgot Password?" link on the login page leading to a request form.
- **Recovery Email:** Sends a password reset link with a time-limited token.
- **Reset Page:** `/auth/reset_password/<token>` allowing the user to set a new password.
- **Security:** Tokens are invalidated immediately after use or expiration (e.g., 1 hour).

## Technical Considerations
- **Security:** Use `itsdangerous.URLSafeTimedSerializer` for generating secure, expiring tokens.
- **Templates:** Create responsive HTML email templates for verification and resets.
- **Database:** 
  - Update `users` table: `is_verified` (boolean).
- **Graceful Failure:** If SMTP is unavailable, log the error and inform the user without crashing the app.

## Acceptance Criteria
- New users receive a verification email immediately after signup.
- Users cannot access creation tools until they click the verification link.
- Clicking an expired token link shows a clear error message.
- Users can successfully reset their password without knowing their old one, provided they have access to their email.

## Out of Scope
- Marketing email campaigns.
- In-app notification center (to be handled in a future track).
