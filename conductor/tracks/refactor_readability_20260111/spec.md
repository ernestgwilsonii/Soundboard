# Specification: Refactor for Readability & Developer Experience

## 1. Overview
This track aims to drastically improve the "Developer Experience" (DX) by making the codebase self-documenting, modular, and easy to reason about. The primary guiding principle is that code should be written for humans first, machines second.

## 2. Goals
- **Self-Explanatory Names:** Variable and function names must clearly describe *intent* (e.g., `is_user_verified` vs `verified`).
- **Single Responsibility:** Functions and classes should do one thing well.
- **No Magic Values:** All string literals ("admin") and magic numbers (60) must be replaced with named Constants or Enums.
- **Modular Structure:** Large monolithic files (like `models.py`) must be broken down into logical sub-modules.

## 3. Technical Implementation
### 3.1 Constants & Enums
- **Location:** `app/constants.py` and `app/enums.py`.
- **Usage:** Replaces all hardcoded strings and numbers in business logic.
- **Example:**
    ```python
    # Before
    if user.role == "admin": ...
    
    # After
    class UserRole(StrEnum):
        ADMIN = "admin"
        USER = "user"
    
    if user.role == UserRole.ADMIN: ...
    ```

### 3.2 Modularization
- **Models:** The `app/models.py` file will be converted into a Python package `app/models/`.
    - `__init__.py`: Exports all models to maintain backward compatibility for some imports, though explicit imports are preferred.
    - Sub-modules: `user.py`, `soundboard.py`, `playlist.py`, `social.py`.

### 3.3 Semantic Refactoring
- **Function Naming:** Verbs for functions (`get_`, `calculate_`, `is_`), Nouns for variables.
- **Conditionals:** Complex boolean logic should be extracted into named properties or functions (e.g., `if user.can_edit(soundboard):`).

## 4. Impact
### 4.1 Product
- **Stability:** Reduced risk of typos causing bugs (via Enums).
- **Velocity:** Faster onboarding for new developers and easier feature additions in the future.

### 4.2 Engineering
- **Imports:** Import paths for models will change (e.g., `from app.models.user import User`).
- **Guidelines:** New strict standard for naming and structure documented in `CONTRIBUTING.md`.
