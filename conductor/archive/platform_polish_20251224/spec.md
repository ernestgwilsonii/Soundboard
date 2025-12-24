# Track Specification: Platform Polish and Advanced Configuration

## Overview
This track focuses on enhancing the platform's maturity by introducing administrative controls for site-wide communication and maintenance, improving social engagement, and refining the user experience on mobile devices and during soundboard management.

## Functional Requirements

### 1. Administrative Configuration
- **Global Announcement Banner:**
  - Admins can set a custom message and type (info, warning, danger) via the Settings page.
  - The banner displays at the top of every page when active.
  - Admins can disable/clear the banner.
- **Maintenance Mode:**
  - Admins can toggle "Maintenance Mode" on/off.
  - When active, non-admin users attempting to access any page (except login) are redirected to a generic "Under Maintenance" page.
  - Admins can still browse the site normally.

### 2. Social Sharing
- **Share Button:**
  - Add a "Share" button to the Soundboard View page for public boards.
  - Functionality:
    - Click copies the direct link to the clipboard.
    - Shows a temporary "Copied!" tooltip or toast.
    - (Optional) Direct links to Twitter/X, Facebook, etc.

### 3. Soundboard Management
- **Drag-and-Drop Reordering:**
  - Users can reorder sounds within their soundboard in "Edit" mode.
  - The new order is persisted to the database.
  - UI provides clear visual feedback during drag operations.

### 4. Mobile Responsiveness Polish
- **Audit & Fix:**
  - Ensure soundboard grid cards scale correctly on small screens (no horizontal scroll).
  - verifying touch targets for playback and buttons are at least 44x44px.
  - Ensure admin tables scroll horizontally on mobile instead of breaking layout.

## Technical Considerations
- **Database:**
  - `admin_settings` table needs new keys: `announcement_message`, `announcement_type`, `maintenance_mode`.
  - `sounds` table needs a new column: `display_order` (integer) for sorting.
- **Frontend:**
  - Use a library like `SortableJS` for drag-and-drop or native HTML5 Drag and Drop API.
  - Use Bootstrap 5 classes for sorting and ordering visual feedback.
  - Clipboard API for the Share button.

## Acceptance Criteria
- Banner appears globally when set by admin.
- Non-admins are blocked from accessing the site when Maintenance Mode is on.
- Clicking "Share" copies the URL to clipboard.
- Sounds retain their new order after reloading the Edit or View page.
- Site passes a visual audit on mobile viewports (375px width).
