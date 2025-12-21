# Track Specification: Core Setup

## Objective
To establish the foundational Flask application structure, including the initial file organization, configuration management, database setup (SQLite), and basic routing. This track also lays the groundwork for account management by setting up the necessary models and database schemas.

## Requirements
- **Project Structure:** Create a modular directory structure suitable for a scalable Flask application (e.g., separating blueprints, templates, static files).
- **Configuration:** Implement environment-based configuration using `.env` files.
- **Database:** Initialize two SQLite databases: `accounts.sqlite3` for user data and `soundboards.sqlite3` for soundboard content.
- **Models:** Define the initial User model with password hashing.
- **Routing:** Create a basic "Hello World" or landing page route to verify the setup.
- **Logging:** Configure basic logging to capture application events.
- **Dependencies:** Create a `requirements.txt` file with all necessary packages (Flask, Flask-WTF, etc.).

## Detailed Design
- **Application Factory:** Use the Flask application factory pattern to create the app instance.
- **Blueprints:** Use Flask Blueprints to organize code (e.g., `auth`, `main`).
- **Database Connection:** Use a pattern (like `sqlite3` or an ORM if decided, but standard `sqlite3` driver was inferred) to connect to the two databases. *Note: Using raw SQLite as per inference, or a lightweight wrapper.*
