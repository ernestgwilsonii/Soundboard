# Specification: Architectural Polish & Semantic Excellence

## 1. Overview
This track aims to move the codebase from "functional" to "professional excellence." We will eliminate raw SQL from the route layer, enforce strict semantic naming, and ensure total type safety.

## 2. Goals
- **Zero Raw SQL in Routes:** The application layer (routes) must only interact with high-level Model methods. No `cur.execute` or SQL strings allowed outside of `app/models/` or `app/db.py`.
- **Absolute Semantic Naming:** Short names like `db`, `cur`, `sb`, `u`, `pl`, `msg` are strictly forbidden. Use `database_connection`, `database_cursor`, `soundboard`, `user`, `playlist`, `message`.
- **Typed Result Sets:** Database results must be immediately converted into objects or TypedDicts. No more `row["column"]` or `row[0]` access in the application logic.
- **Strict Type Safety:** Satisfy `mypy --strict` for all modified files.
- **Decoupled Architecture:** Resolve circular dependencies that currently force local imports within functions.

## 3. Technical Standards
### 3.1 Naming Lexicon
| Short (Forbidden) | Professional (Mandatory) |
| :--- | :--- |
| `db` | `database_connection` |
| `cur` | `database_cursor` |
| `sb` | `soundboard` |
| `pl` | `playlist` |
| `u` | `user` |
| `act` | `activity` |
| `msg` | `message` |
| `ext` | `extension` |
| `req` | `request` (if not the flask global) |

### 3.2 SQL Abstraction
- **Before:**
    ```python
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM soundboards WHERE id = ?", (id,))
    row = cur.fetchone()
    ```
- **After:**
    ```python
    soundboard = Soundboard.get_by_id(soundboard_id)
    ```

### 3.3 Model Decomposition
- Large models like `Soundboard` will have their logic split into Mixins (e.g., `SoundboardCRUDMixin`, `SoundboardSocialMixin`, `SoundboardExportMixin`) if they exceed 500 lines.

## 4. Acceptance Criteria
- No raw SQL strings found in `app/main/routes.py`, `app/auth/routes.py`, or `app/soundboard/routes.py`.
- Automated search for forbidden short names (`db`, `cur`, etc.) returns zero results in the `app/` directory (excluding library imports).
- All modified files pass `mypy` strict checks.
- All unit and E2E tests pass.
