# Track Plan: Core Setup

## Phase 1: Environment and Dependencies
- [x] Task: Create a virtual environment and activate it. d3a1f1b
- [ ] Task: Create a `requirements.txt` file with initial dependencies (Flask, Flask-WTF, python-dotenv, werkzeug).
- [ ] Task: Install dependencies and freeze the requirements.
- [ ] Task: Conductor - User Manual Verification 'Environment and Dependencies' (Protocol in workflow.md)

## Phase 2: Project Structure and Configuration
- [ ] Task: Create the project directory structure (app/, tests/, static/, templates/).
- [ ] Task: Create a `.env` file for environment variables (SECRET_KEY, DEBUG).
- [ ] Task: Create a `config.py` file to load configuration from environment variables.
- [ ] Task: Create `app/__init__.py` to implement the application factory pattern.
- [ ] Task: Conductor - User Manual Verification 'Project Structure and Configuration' (Protocol in workflow.md)

## Phase 3: Database Initialization
- [ ] Task: Create a `schema.sql` (or Python script) to define the `users` table for `accounts.sqlite3` and `soundboards` table for `soundboards.sqlite3`.
- [ ] Task: Write a script to initialize the two SQLite databases (`init_db.py`).
- [ ] Task: Execute the initialization script and verify database creation.
- [ ] Task: Conductor - User Manual Verification 'Database Initialization' (Protocol in workflow.md)

## Phase 4: Basic Routing and Logging
- [ ] Task: Create a `main` blueprint in `app/main/` with a simple route (`/`) rendering a template.
- [ ] Task: Create a base template (`base.html`) and an index template (`index.html`).
- [ ] Task: Configure Python's `logging` in `app/__init__.py`.
- [ ] Task: Register the `main` blueprint in the application factory.
- [ ] Task: Run the application and verify the landing page loads.
- [ ] Task: Conductor - User Manual Verification 'Basic Routing and Logging' (Protocol in workflow.md)
