# Track Plan: Administrator Dashboard and User Management

## Phase 1: Admin Decorator and Model Enhancements
- [x] Task: Implement the `@admin_required` decorator in `app/auth/routes.py` (or a utils file). 88c30cf
- [x] Task: Add a `User.get_all()` static method to `app/models.py`. 88c30cf
- [x] Task: Create unit tests to verify that `@admin_required` correctly blocks non-admin users. 88c30cf
- [x] Task: Conductor - User Manual Verification 'Admin Decorator and Model Enhancements' (Protocol in workflow.md) 88c30cf

## Phase 2: User Management Interface
- [x] Task: Create the `app/admin/` blueprint and register it in `app/__init__.py`. 8ae3ab9
- [x] Task: Implement the `/admin/users` route and a template to list all users. 8ae3ab9
- [x] Task: Add functionality to toggle a user's active status (Enable/Disable). 0f63aa0
- [x] Task: Add functionality to change a user's role (User/Admin). c939df3
- [x] Task: Conductor - User Manual Verification 'User Management Interface' (Protocol in workflow.md) c939df3

## Phase 3: Administrative Password Reset [checkpoint: a827762]
- [x] Task: Create an `AdminPasswordResetForm` in `app/admin/forms.py`. 68355a1
- [x] Task: Implement the route and template for administrators to reset any user's password. a9e5128
- [x] Task: Add integration tests for administrative password overrides. a9e5128
- [x] Task: Conductor - User Manual Verification 'Administrative Password Reset' (Protocol in workflow.md) a827762

## Phase 4: Content Moderation and Navigation [checkpoint: 7c479d0]

- [x] Task: Implement a global soundboard management view (`/admin/soundboards`). cf0c1cf

- [x] Task: Update existing Soundboard and Sound CRUD routes to allow the 'admin' role to bypass ownership checks. b004519

- [x] Task: Add an "Admin Dashboard" link to the navbar, visible only to administrators. 7c479d0

- [x] Task: Conductor - User Manual Verification 'Content Moderation and Navigation' (Protocol in workflow.md) 7c479d0
