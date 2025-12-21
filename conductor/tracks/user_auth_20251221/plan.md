# Track Plan: User Authentication

## Phase 1: Models and Login Manager [checkpoint: c0c0e20]
- [x] Task: Install `Flask-Login` and update `requirements.txt`. 62442a4
- [x] Task: Update the `User` model in a new `app/models.py` file to include `UserMixin` and password hashing methods. c82c37f
- [x] Task: Initialize `Flask-Login`'s `LoginManager` in `app/__init__.py`. c025c8e
- [x] Task: Implement the `load_user` callback for `Flask-Login`. c025c8e
- [x] Task: Conductor - User Manual Verification 'Models and Login Manager' (Protocol in workflow.md) c0c0e20

## Phase 2: Registration and Forms [checkpoint: 22e9aab]
- [x] Task: Create `app/auth/forms.py` with `RegistrationForm` and `LoginForm` using `Flask-WTF`. fbb535f
- [x] Task: Create the `auth` blueprint and register it in `app/__init__.py`. 999f386
- [x] Task: Implement the registration route and `signup.html` template. f4dab8d
- [x] Task: Verify that a new user can be created in the `accounts.sqlite3` database. f4dab8d
- [x] Task: Conductor - User Manual Verification 'Registration and Forms' (Protocol in workflow.md) 22e9aab

## Phase 3: Login and Session Management
- [x] Task: Implement the login route and `login.html` template. 6104639
- [x] Task: Implement the logout route. 2a3c910
- [x] Task: Update the base template to show "Login" or "Logout/Profile" based on authentication status. 2a3c910
- [x] Task: Verify that a user can log in and out successfully. 2a3c910
- [ ] Task: Conductor - User Manual Verification 'Login and Session Management' (Protocol in workflow.md)

## Phase 4: Profile and Protection
- [ ] Task: Create a protected profile route and `profile.html` template.
- [ ] Task: Add `@login_required` decorators to protect restricted routes.
- [ ] Task: Verify that unauthorized users are redirected to the login page when accessing protected routes.
- [ ] Task: Conductor - User Manual Verification 'Profile and Protection' (Protocol in workflow.md)
