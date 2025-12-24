# Track Plan: Platform Polish and Advanced Configuration

## Phase 1: Admin Configuration (Banner & Maintenance) [checkpoint: 4bf55dc]
- [x] Task: Update `admin_settings` handling in `app/models.py` to support arbitrary keys (already generic, verify usage). 3332f38
- [x] Task: Update `AdminSettingsForm` in `app/admin/forms.py` to include Announcement fields and Maintenance toggle. 3332f38
- [x] Task: Update `/admin/settings` route to handle the new fields. 3332f38
- [x] Task: Update `base.html` to display the announcement banner if set. 8f7383a
- [x] Task: Create a `before_request` handler in `app/__init__.py` or `app/main/routes.py` to enforce Maintenance Mode. 4bf55dc
- [x] Task: Create `templates/maintenance.html`. 4bf55dc
- [x] Task: Conductor - User Manual Verification 'Admin Configuration' (Protocol in workflow.md) 4bf55dc

## Phase 2: Social Sharing [checkpoint: 4e79841]
- [x] Task: Add "Share" button to `templates/soundboard/view.html` (next to Favorite button). 8f7383a
- [x] Task: Implement JavaScript to copy current URL to clipboard. 8f7383a
- [x] Task: Add toast/tooltip notification for success. 8f7383a
- [x] Task: Conductor - User Manual Verification 'Social Sharing' (Protocol in workflow.md) 4e79841

## Phase 3: Drag-and-Drop Reordering
- [ ] Task: Add `display_order` column to `sounds` table (requires migration script/SQL).
- [ ] Task: Update `Sound` model to include `display_order` and default sorting.
- [ ] Task: Update `Sound.save()` to handle default order (e.g., max order + 1).
- [ ] Task: Implement drag-and-drop UI in `templates/soundboard/edit.html`.
- [ ] Task: Create API endpoint `/soundboard/<id>/reorder` to accept new order.
- [ ] Task: Connect UI to API to save new order.
- [ ] Task: Conductor - User Manual Verification 'Drag-and-Drop Reordering' (Protocol in workflow.md)

## Phase 4: Mobile Responsiveness Polish
- [ ] Task: Audit `soundboard/view.html` grid on mobile widths.
- [ ] Task: Audit `admin/*.html` tables for responsiveness (ensure `table-responsive`).
- [ ] Task: Verify touch target sizes for all primary buttons.
- [ ] Task: Conductor - User Manual Verification 'Mobile Responsiveness Polish' (Protocol in workflow.md)
