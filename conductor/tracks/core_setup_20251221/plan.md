# Track Plan: Core Setup

## Phase 1: Environment and Dependencies [checkpoint: 2aa86b9]
- [x] Task: Create a virtual environment and activate it. d3a1f1b
- [x] Task: Create a `requirements.txt` file with initial dependencies (Flask, Flask-WTF, python-dotenv, werkzeug). dae3217
- [x] Task: Install dependencies and freeze the requirements. 3163099
- [x] Task: Conductor - User Manual Verification 'Environment and Dependencies' (Protocol in workflow.md) 2aa86b9

## Phase 2: Project Structure and Configuration [checkpoint: 06e6afa]
- [x] Task: Create the project directory structure (app/, tests/, static/, templates/). a2c490f
- [x] Task: Create a .env file for environment variables (SECRET_KEY, DEBUG). 6b19456
- [x] Task: Create a `config.py` file to load configuration from environment variables. 0e8088e
- [x] Task: Create `app/__init__.py` to implement the application factory pattern. 55472cf
- [x] Task: Conductor - User Manual Verification 'Project Structure and Configuration' (Protocol in workflow.md) 06e6afa

## Phase 3: Database Initialization
- [x] Task: Create a `schema.sql` (or Python script) to define the `users` table for `accounts.sqlite3` and `soundboards` table for `soundboards.sqlite3`. 104b8ae
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
