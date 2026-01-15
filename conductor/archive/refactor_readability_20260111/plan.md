# Plan: Refactor for Readability & Developer Experience

**Goal:** Transform the codebase into a highly human-readable, self-documenting, and maintainable project. We will focus on semantic naming, single responsibility, eliminating magic values, and modularizing monolithic files.

**Context:** The user emphasized that "Human Readable Code is Paramount." The current codebase has large files (e.g., `models.py` ~2300 lines) and likely contains "magic strings" and procedural logic that could be cleaner.

## Phase 1: Foundations (Constants & Enums) [checkpoint: 0c5ec8a]
- [x] Create `app/constants.py` for global constants (Time, Limits, Configuration defaults) 28fb169
- [x] Create `app/enums.py` for state definitions (UserRoles, SoundboardVisibility, etc.) db15b6b
- [x] Refactor `app/models.py` to use these Enums instead of string literals (e.g., "admin", "public") 3ceb365
- [x] Refactor `app/routes.py` (and blueprints) to use these Enums and Constants ee0e328

## Phase 2: Modularization (Breaking the Monoliths) [checkpoint: 67c553b]
- [x] Refactor `app/models.py`: Split into a package `app/models/` 39a352f
- [x] Update all imports across the application to point to the new model locations (or ensuring `__init__` handles it correctly) 0b43a4b
- [x] Verify application starts and runs correctly [checkpoint: 9a738ca]

## Phase 3: Semantic Refactoring (Clean Code) [checkpoint: 9a738ca]
- [x] Audit `app/utils/` and refactor complex functions into smaller, single-purpose functions 0d5175f
- [x] Rename ambiguous variables/functions in `app/main/routes.py` and `app/soundboard/routes.py` to be self-explanatory
- [x] Ensure all configuration is strictly pulled from `config.py` or `.env`, removing any hardcoded fallbacks in logic fe7273c

## Phase 4: Documentation & Guidelines [checkpoint: 9a738ca]
- [x] Create `CONTRIBUTING.md` detailing the "Human Readable" philosophy, naming conventions, and structure afcba20
- [x] Update `conductor/code_styleguides/*.md` to reflect the new strict preferences for "Clean Code" afcba20
- [x] Verify all tests pass after these massive structural changes [checkpoint: 9a738ca]
