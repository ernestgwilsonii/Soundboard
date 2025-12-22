# Track Plan: Administrator Dashboard and User Management

## Phase 1: Admin Decorator and Model Enhancements
- [ ] Task: Implement the `@admin_required` decorator in `app/auth/routes.py` (or a utils file).
- [ ] Task: Add a `User.get_all()` static method to `app/models.py`.
- [ ] Task: Create unit tests to verify that `@admin_required` correctly blocks non-admin users.
- [ ] Task: Conductor - User Manual Verification 'Admin Decorator and Model Enhancements' (Protocol in workflow.md)

## Phase 2: User Management Interface
- [ ] Task: Create the `app/admin/` blueprint and register it in `app/__init__.py`.
- [ ] Task: Implement the `/admin/users` route and a template to list all users.
- [ ] Task: Add functionality to toggle a user's active status (Enable/Disable).
- [ ] Task: Add functionality to change a user's role (User/Admin).
- [ ] Task: Conductor - User Manual Verification 'User Management Interface' (Protocol in workflow.md)

## Phase 3: Administrative Password Reset
- [ ] Task: Create an `AdminPasswordResetForm` in `app/admin/forms.py`.
- [ ] Task: Implement the route and template for administrators to reset any user's password.
- [ ] Task: Add integration tests for administrative password overrides.
- [ ] Task: Conductor - User Manual Verification 'Administrative Password Reset' (Protocol in workflow.md)

## Phase 4: Content Moderation and Navigation
- [ ] Task: Implement a global soundboard management view (`/admin/soundboards`).
- [ ] Task: Update existing Soundboard and Sound CRUD routes to allow the 'admin' role to bypass ownership checks.
- [ ] Task: Add an "Admin Dashboard" link to the navbar, visible only to administrators.
- [ ] Task: Conductor - User Manual Verification 'Content Moderation and Navigation' (Protocol in workflow.md)
