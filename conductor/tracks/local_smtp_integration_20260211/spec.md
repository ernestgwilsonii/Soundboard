# Specification: Local SMTP Integration

## Objective
Implement a self-contained SMTP solution for the development environment to avoid external service dependencies (like Gmail) and simplify configuration.

## Requirements
- **Local SMTP Container:** Add a lightweight SMTP capture server (Mailpit) to the Docker stack.
- **Zero-Creds by Default:** The application should function without SMTP credentials in the development environment.
- **Mail Inspection:** Developers must be able to view outgoing emails (verification, password resets) via a web interface.
- **Environment Parity:** The code must remain compatible with real authenticated SMTP servers for production use.

## Technical Approach
- **Service:** `axllent/mailpit` (successor to MailHog).
- **Network:** The `app` service will communicate with the `mailpit` service over the internal Docker network on port `1025`.
- **UI:** Expose port `8025` for the web-based mailbox.
- **Config:** Update `config.py` to handle cases where `MAIL_USERNAME` and `MAIL_PASSWORD` are null.
