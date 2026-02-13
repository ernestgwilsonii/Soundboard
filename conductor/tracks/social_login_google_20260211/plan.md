# Implementation Plan: Social Login Integration (Google)

## Phase 1: Preparation
- [ ] Add `Flask-Dance[sqla]` to `requirements.txt`.
- [ ] Update `.env.example` with Google OAuth placeholders.

## Phase 2: Database & Model
- [ ] Update `User` model to include social provider IDs.
- [ ] Generate and apply a database migration.

## Phase 3: OAuth Integration
- [ ] Implement a `SocialProvider` registry.
- [ ] Configure the Google blueprint with `Flask-Dance`.
- [ ] Create a callback handler to manage user login/registration.

## Phase 4: Frontend
- [ ] Update login template to conditionally display social buttons.
- [ ] Add Google "G" branding assets/icons.

## Phase 5: Documentation & Verification
- [ ] Provide step-by-step Google Cloud Console instructions.
- [ ] Test local flow with mock credentials or a test project.
