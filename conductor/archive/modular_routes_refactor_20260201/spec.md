# Track Specification: Modular Routes Refactor

## Overview
This track focuses on decomposing the large, monolithic `routes.py` files (specifically in the `soundboard` and `auth` blueprints) into smaller, domain-driven modules. This refactor will improve human readability, simplify testing, and accelerate future feature development by organizing code according to functional responsibility.

## Problem Statement
Currently, `app/soundboard/routes.py` is nearly 1,000 lines long, and `app/auth/routes.py` exceeds 500 lines. These files have become difficult to navigate, maintain, and test. Merging new features often leads to complex conflicts, and the lack of separation makes it harder for developers to locate specific logic quickly.

## Proposed Solution
We will transition from a single `routes.py` per blueprint to a modular directory structure within each blueprint. We will use functional decomposition to group related endpoints.

### 1. Blueprint Structure Change
Each large blueprint will follow this pattern:
```
app/soundboard/
├── __init__.py (Registers all sub-modules)
├── routes/
│   ├── __init__.py
│   ├── board_mgmt.py    (CRUD for soundboards)
│   ├── sound_mgmt.py    (CRUD for sounds, reordering)
│   ├── collaborators.py  (Sharing, Editor management)
│   ├── discovery.py      (Gallery, Search, Trending)
│   └── social.py         (Comments, Ratings)
└── forms.py
```

### 2. Implementation Strategy
- **Functional Grouping:** Move endpoints to modules based on their primary domain.
- **Maintain API Stability:** Ensure that all existing URL patterns (`url_for`) and blueprint names remain unchanged so that templates and frontend JS do not break.
- **Refactor for Readability:** While moving code, perform minor "cleanup" refactors (e.g., removing redundant imports, improving local variable naming) without changing business logic.
- **Enhanced Testing:** Update unit tests to match the new modular structure and add missing edge-case tests.

### 3. Industry Best Practices
- **Domain-Driven Design (DDD) Lite:** Grouping by feature rather than just by "routes".
- **Separation of Concerns:** Keeping board management separate from social interactions.
- **Improved Scoping:** Reducing the number of global imports per file.

## Acceptance Criteria
- [ ] `app/soundboard/routes.py` is removed and replaced by a `routes/` package.
- [ ] `app/auth/routes.py` is removed and replaced by a `routes/` package.
- [ ] All existing routes remain functional (verified via E2E and existing tests).
- [ ] `url_for` calls in templates and redirects still work correctly using existing blueprint names (e.g., `soundboard.view`).
- [ ] Code coverage for routes remains >80%.
- [ ] Code follows the Google-style docstring and strict typing guidelines.
