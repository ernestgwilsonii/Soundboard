# Track Specification: Version 2.0 - Tagging System

## Overview
This track introduces a tagging system to improve the organization and discovery of soundboards. Users can add descriptive tags to their boards, and all users can browse or search for content based on these tags.

## Functional Requirements

### 1. Tag Management
- **Create Tags:** Soundboard owners can add multiple tags (single words, max 20 chars each) to their soundboards.
- **Remove Tags:** Owners can delete tags from their boards.
- **Auto-suggestion:** (Optional) Show existing tags as the user types.

### 2. Search and Discovery
- **Browse by Tag:** A new "Tags" page or section in the Gallery listing the most popular tags.
- **Tag Search:** Clicking a tag filters the Gallery/Search results to show only soundboards with that tag.
- **Integrated Search:** Global search should prioritize results matching tags.

### 3. UI Integration
- **View Page:** Display tags as badges under the soundboard title.
- **Edit Page:** Add a tag input field (comma-separated or chips-style).
- **Gallery Cards:** Show small tag badges on soundboard cards.

## Technical Considerations
- **Database (Soundboards DB):**
  - New table `tags`: `id`, `name` (unique).
  - New association table `soundboard_tags`: `soundboard_id`, `tag_id`.
- **Search Optimization:** Update the `Soundboard.search()` method to include tag matching.

## Acceptance Criteria
- Owners can add/remove tags on their soundboards.
- Clicking a tag badge redirects to a filtered results page.
- Popular tags are visible in the community sidebar or gallery.
- Searching for a tag name returns all tagged boards.

## Out of Scope
- Hierarchical tags (sub-tags).
- Tagging individual sounds (boards only for now).
