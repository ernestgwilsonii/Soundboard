# Plan: Architectural Polish & Semantic Excellence

This plan focuses on elevating the code quality to professional standards by enforcing strict semantic naming and a clean separation of concerns.

## Phase 1: Semantic Renaming (Global Audit)
- [x] Refactor `app/db.py`: Rename `db` to `database_connection` and `cur` to `database_cursor` globally within the file and its callers.
- [x] Audit `app/models/`: Rename all short-form variables (`sb`, `u`, `pl`, `act`) to full descriptive names.
- [x] Audit `app/routes/`: Rename all short-form variables in all blueprints.

## Phase 2: SQL Abstraction (Routes Cleanup)
- [x] Refactor `app/main/routes.py`: Extract all inline SQL into new Model methods.
- [x] Refactor `app/soundboard/routes.py`: Extract remaining inline SQL and database cursor logic.
- [x] Refactor `app/auth/routes.py`: Ensure all database interactions go through high-level Model abstractions.

## Phase 3: Model Refinement & Type Safety
- [x] Break down `app/models/soundboard.py` into logical mixins to reduce file size and complexity.
- [x] Implement strict type hinting across all models, ensuring return types are always specific objects or `List[Model]`.
- [x] Resolve circular dependencies in `app/main/routes.py` and `app/models/` to remove function-level imports.

## Phase 4: Final Verification
- [x] Run `grep` audits to ensure zero forbidden short names remain in the codebase.
- [x] Verify `mypy --strict` passes for the `app/` directory.
- [x] Execute the full test suite (Pytest + Playwright) to ensure zero regressions.
