# Plan: Refactor for Readability & Developer Experience

**Goal:** Transform the codebase into a highly human-readable, self-documenting, and maintainable project. We will focus on semantic naming, single responsibility, eliminating magic values, and modularizing monolithic files.

**Context:** The user emphasized that "Human Readable Code is Paramount." The current codebase has large files (e.g., `models.py` ~2300 lines) and likely contains "magic strings" and procedural logic that could be cleaner.

## Phase 1: Foundations (Constants & Enums)
- [x] Create `app/constants.py` for global constants (Time, Limits, Configuration defaults) 28fb169
- [x] Create `app/enums.py` for state definitions (UserRoles, SoundboardVisibility, etc.) db15b6b
- [ ] Refactor `app/models.py` to use these Enums instead of string literals (e.g., "admin", "public")
- [ ] Refactor `app/routes.py` (and blueprints) to use these Enums and Constants

## Phase 2: Modularization (Breaking the Monoliths)
- [ ] Refactor `app/models.py`: Split into a package `app/models/`
    - [ ] `app/models/user.py`
    - [ ] `app/models/soundboard.py`
    - [ ] `app/models/social.py` (Comments, Follows)
    - [ ] `app/models/__init__.py` (Expose classes to maintain import compatibility where possible, or update imports)
- [ ] Update all imports across the application to point to the new model locations (or ensuring `__init__` handles it correctly)
- [ ] Verify application starts and runs correctly [checkpoint]

## Phase 3: Semantic Refactoring (Clean Code)
- [ ] Audit `app/utils/` and refactor complex functions into smaller, single-purpose functions
- [ ] Rename ambiguous variables/functions in `app/main/routes.py` and `app/soundboard/routes.py` to be self-explanatory
- [ ] Ensure all configuration is strictly pulled from `config.py` or `.env`, removing any hardcoded fallbacks in logic

## Phase 4: Documentation & Guidelines
- [ ] Create `CONTRIBUTING.md` detailing the "Human Readable" philosophy, naming conventions, and structure
- [ ] Update `conductor/code_styleguides/*.md` to reflect the new strict preferences for "Clean Code"
- [ ] Verify all tests pass after these massive structural changes [checkpoint]
