# Track Specification: Soundboard Management and File Uploads

## Objective
Implement the core functionality of the platform: allowing users to create, view, edit, and delete soundboards, and upload audio files to them.

## Requirements
- **Soundboard CRUD:**
    - Create: Logged-in users can create new soundboards with a name and an icon.
    - Read: Users can view their own soundboards and public ones.
    - Update: Users can rename their soundboards and change icons.
    - Delete: Users can delete their own soundboards (and all associated sounds).
- **Sound Management:**
    - Upload: Users can upload audio files (MP3, WAV, OGG) to a soundboard.
    - Delete: Users can remove sounds from their soundboards.
- **File Storage:**
    - Securely store uploaded audio files in a structured directory (`sounds/<soundboard_id>/`).
    - Validate file types and sizes.
- **Database Integration:**
    - Map `Soundboard` and `Sound` models to the `soundboards.sqlite3` database.
- **UI/UX:**
    - Interactive soundboard view with clickable icons to play sounds.
    - Dashboard for users to manage their collection.
    - Drag-and-drop interface (as per initial concept, to be implemented simply first).

## Detailed Design
- **Models:** Implement `Soundboard` and `Sound` classes in `app/models.py`.
- **Blueprints:** Use the `main` blueprint for viewing and a new `soundboard` blueprint for management? Or keep management in a specific blueprint. Let's use a `soundboard` blueprint.
- **Forms:** Use `Flask-WTF` for soundboard creation and sound upload.
- **Static Files:** Serve uploaded sounds via Flask's static file serving or a dedicated route.
