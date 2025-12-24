# Track Plan: Version 2.0 - Email Services

## Phase 1: Infrastructure and Verification [checkpoint: 4bf55dc]
- [x] Task: Install `Flask-Mail` and update `requirements.txt`. ee182bf
- [x] Task: Update `config.py` and `.env.example` with SMTP settings. ee182bf
- [x] Task: Add `is_verified` column to `users` table via `migrate.py`. ee182bf
- [x] Task: Implement token generation logic using `itsdangerous`. 0d65a25
- [x] Task: Implement the email sending utility function. a3c8f08
- [x] Task: Create verification email template and `/auth/verify/<token>` route. a3c8f08
- [x] Task: Update Registration flow to send verification email. a3c8f08
- [x] Task: Enforce verification check on restricted routes (Create, Comment). a3c8f08
- [x] Task: Conductor - User Manual Verification 'Email Infrastructure and Verification' (Protocol in workflow.md) 4bf55dc

## Phase 2: Password Recovery Flow [checkpoint: 976e5fe]
- [x] Task: Create `PasswordResetRequestForm` and `ResetPasswordForm`. 976e5fe
- [x] Task: Implement the "Forgot Password" request route and email template. a3c8f08
- [x] Task: Implement the password reset route `/auth/reset_password/<token>`. a3c8f08
- [x] Task: Add "Forgot Password?" link to the login page. a3c8f08
- [x] Task: Verify that reset tokens expire and are one-time use. a3c8f08
- [x] Task: Conductor - User Manual Verification 'Password Recovery Flow' (Protocol in workflow.md) 976e5fe

## Phase 3: Documentation and Refinement [checkpoint: 17ef812]
- [x] Task: Update `README.md` with instructions for SMTP configuration. ee182bf
- [x] Task: Refine email templates for mobile responsiveness and branding. 17ef812
- [x] Task: Conductor - User Manual Verification 'Email Services Final Polish' (Protocol in workflow.md) 17ef812
