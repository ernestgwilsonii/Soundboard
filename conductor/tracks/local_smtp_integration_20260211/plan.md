# Implementation Plan: Local SMTP Integration

## Phase 1: Infrastructure
- [ ] Add `mailpit` service to `docker-compose.yml`.
- [ ] Expose SMTP (1025) and Web UI (8025) ports.

## Phase 2: Configuration
- [ ] Update `config.py` to support unauthenticated SMTP.
- [ ] Update `.env.example` to point to `localhost` (non-docker) or `mailpit` (docker) by default.

## Phase 3: Documentation
- [ ] Update `README.md` with instructions on how to use the local mailbox.
- [ ] Remove Gmail-specific instructions as the "default" setup.

## Phase 4: Verification
- [ ] Perform a test registration.
- [ ] Verify the email appears in the Mailpit UI.
- [ ] Run the full test suite to ensure no regressions in email-related tests.
