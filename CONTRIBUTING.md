# Contributing to Soundboard

First off, thank you for considering contributing to Soundboard! It's people like you that make it a better tool for everyone.

## Human Readable Code is Paramount

At Soundboard, we believe that **code is written for humans first and machines second.** Our primary goal is to maintain a codebase that is highly readable, self-documenting, and easy to reason about.

### Naming Conventions

*   **Variable Names:** Use nouns that clearly describe the *intent* and *content*. Avoid single-letter variables except for very local loop counters.
    *   *Bad:* `s`, `data`, `v`
    *   *Good:* `soundboard`, `user_profile`, `is_verified`
*   **Function Names:** Use verbs that describe the *action*.
    *   *Bad:* `logic()`, `process()`
    *   *Good:* `calculate_average_rating()`, `send_verification_email()`
*   **Boolean Variables:** Prefix with `is_`, `has_`, `can_`, or `should_`.
    *   *Example:* `is_public`, `has_comments`, `can_edit`

### Single Responsibility Principle

Each function and class should do **one thing well.** If a function is longer than 30-40 lines, it's likely doing too much and should be broken down into smaller, focused helpers.

### No Magic Values

Never use hardcoded string literals or numbers in business logic.
*   **Strings:** Use Enums (defined in `app/enums.py`).
*   **Numbers/Defaults:** Use Constants (defined in `app/constants.py`).

### Modular Structure

Large monolithic files are discouraged. We prefer a modular structure where logic is grouped into logical packages (e.g., `app/models/` package instead of a single `models.py` file).

### Database Migrations

We use **SQLAlchemy ORM** and **Alembic** (via Flask-Migrate) for database management.
- **NEVER** modify database schemas directly using raw SQL.
- **To create a migration:**
  ```bash
  export FLASK_APP=soundboard.py
  venv/bin/flask db migrate -m "Description of change"
  ```
- **To apply migrations:**
  ```bash
  venv/bin/flask db upgrade
  ```
- All new models or changes to existing models MUST include a corresponding migration file in the `migrations/versions` directory.

## Development Workflow

1.  **Fork and Clone:** Create your own branch from `main`.
2.  **Test-Driven Development:** Write unit tests for any new feature or bug fix before implementation.
3.  **Check Quality:** Run the project's quality checks:
    ```bash
    ./scripts/check_quality.sh
    ```
4.  **Security Scan:** Run the automated security scans:
    ```bash
    make scan
    ```
5.  **Documentation:** Update relevant documentation and ensure all new public functions have clear docstrings.
6.  **Commit Messages:** Follow the conventional commit format: `<type>(<scope>): <description>`.

## Style Guide

*   **Python:** Follow PEP 8 with a focus on maximum clarity. Use type hints for all function signatures.
*   **HTML/CSS:** Use semantic HTML5 and follow the project's CSS naming conventions.
*   **JavaScript:** Use modern ES6+ syntax and maintain clear, descriptive naming.

Thank you for helping us keep Soundboard clean and maintainable!
