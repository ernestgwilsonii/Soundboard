# Track Plan: User Authentication

## Phase 1: Models and Login Manager
- [x] Task: Install `Flask-Login` and update `requirements.txt`. 62442a4
- [ ] Task: Update the `User` model in a new `app/models.py` file to include `UserMixin` and password hashing methods.
- [ ] Task: Initialize `Flask-Login`'s `LoginManager` in `app/__init__.py`.
- [ ] Task: Implement the `load_user` callback for `Flask-Login`.
- [ ] Task: Conductor - User Manual Verification 'Models and Login Manager' (Protocol in workflow.md)

## Phase 2: Registration and Forms
- [ ] Task: Create `app/auth/forms.py` with `RegistrationForm` and `LoginForm` using `Flask-WTF`.
- [ ] Task: Create the `auth` blueprint and register it in `app/__init__.py`.
- [ ] Task: Implement the registration route and `signup.html` template.
- [ ] Task: Verify that a new user can be created in the `accounts.sqlite3` database.
- [ ] Task: Conductor - User Manual Verification 'Registration and Forms' (Protocol in workflow.md)

## Phase 3: Login and Session Management
- [ ] Task: Implement the login route and `login.html` template.
- [ ] Task: Implement the logout route.
- [ ] Task: Update the base template to show "Login" or "Logout/Profile" based on authentication status.
- [ ] Task: Verify that a user can log in and out successfully.
- [ ] Task: Conductor - User Manual Verification 'Login and Session Management' (Protocol in workflow.md)

## Phase 4: Profile and Protection
- [ ] Task: Create a protected profile route and `profile.html` template.
- [ ] Task: Add `@login_required` decorators to protect restricted routes.
- [ ] Task: Verify that unauthorized users are redirected to the login page when accessing protected routes.
- [ ] Task: Conductor - User Manual Verification 'Profile and Protection' (Protocol in workflow.md)
