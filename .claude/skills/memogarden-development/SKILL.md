---
name: memogarden-development
description: Development environment setup, running the API server, architectural constraints, anti-patterns to avoid, shell command best practices, and working with the implementation plan. Use when doing ANY development work on MemoGarden.
---

# MemoGarden Development

## Starting Work on a Task

When beginning work on any MemoGarden task:

1. **Read the context**
   ```bash
   cd /home/kureshii/memogarden
   cat plan/memogarden_prd_v4.md      # Understand platform architecture
   cat plan/budget_prd.md             # Understand budget app (when needed)
   cat plan/implementation.md         # Check current step
   ```

2. **Navigate to working directory**
   ```bash
   cd memogarden-core                 # or memogarden-budget
   ```

3. **Check current state**
   ```bash
   git status
   git log --oneline -10
   ```

## Setting Up the Development Environment

### Install Poetry (if not present)

```bash
pip install poetry
```

### Install poetry shell plugin

```bash
poetry self add poetry-plugin-shell
```

### Navigate to project and install dependencies

```bash
cd /home/kureshii/memogarden/memogarden-core
poetry install
```

### Activate poetry shell (optional)

```bash
poetry shell
```

This activates a virtual shell with all dependencies available. You can skip this step by using `poetry run` prefix for all commands.

## Package Management with Poetry

**CRITICAL**: This project uses Poetry for dependency management. **NEVER use `pip install`**.

### Installing Dependencies

```bash
# From project root or package directory
poetry install
```

### Running Commands with Poetry

```bash
# Run Python commands
poetry run python -m module.name

# Run tests
poetry run pytest

# Run the Flask server
poetry run flask --app memogarden_core.main run --debug
```

### Adding New Dependencies

```bash
# Add a runtime dependency
poetry add package-name

# Add a development dependency
poetry add --group dev package-name

# Add a dependency from a specific package
poetry add --optional package-name
```

### During Project Restructure (Temporary)

While migrating to the new package structure (Phases 1-4 of restructure plan), some system packages may not be installed yet. Use PYTHONPATH as a temporary workaround:

```bash
# Add memogarden-system to Python path for testing
PYTHONPATH=/home/kureshii/memogarden/memogarden-system:$PYTHONPATH poetry run pytest
```

**This is temporary** - after Phase 6 (Provider Refactoring), all packages will be properly installed via Poetry.

### 🚫 NEVER Use These Commands

```bash
# ❌ DON'T - Bypasses Poetry's dependency management
pip install package-name
python -m pip install package-name
pip3 install package-name

# ❌ DON'T - Installs to system Python, breaks project isolation
sudo pip install package-name
```

**Why**: Using `pip` directly bypasses Poetry's dependency lock file, can cause version conflicts, and breaks the reproducible development environment.

### Checking Installed Packages

```bash
# Show all installed packages
poetry show

# Show package tree (dependencies)
poetry show --tree

# Check for outdated packages
poetry show --outdated
```

### Working Directory Reminder

**Always verify your current directory before running commands:**
- **memogarden-core work**: `/home/kureshii/memogarden/memogarden-core` (for `poetry run pytest`, etc.)
- **Convenience scripts**: `/home/kureshii/memogarden/` (for `./scripts/run.sh`, `./scripts/test.sh`)

Most Poetry commands should be run from `memogarden-core/`. Scripts are in the parent directory.

## Running the Core API Locally

### Using the convenience script (recommended)

```bash
./scripts/run.sh
```

### Manual startup

```bash
cd /home/kureshii/memogarden/memogarden-core
poetry run flask --app memogarden_core.main run --debug
```

The server runs at http://localhost:5000

**Note**: MemoGarden Core uses Flask (not FastAPI). There are no auto-generated API docs.

### Running in background

To run the server in the background:
```bash
./scripts/run.sh &
```

Or use the Bash tool with `run_in_background=True` parameter (when available).

## Running Tests

### Using the convenience script (recommended)

```bash
# Run all tests
./scripts/test.sh

# Run specific test file
./scripts/test.sh tests/api/test_transactions.py

# Run specific test
./scripts/test.sh tests/api/test_transactions.py::test_create_transaction
```

### With coverage

```bash
./scripts/test-coverage.sh
```

### Manual test execution

```bash
cd /home/kureshii/memogarden/memogarden-core
poetry run pytest
```

For detailed testing philosophy and patterns, use the **memogarden-testing** skill.

## Working with the Implementation Plan

### Understanding Progress

The implementation plan (`plan/implementation.md`) has this structure:

```
Step 1: Core Backend Foundation ⚡ CURRENT STEP
  1.1 Project Setup & Structure
    1.1.1 Clone and Initialize Repository
    ...
  1.2 SQLite Database Schema
    ...

Step 2: Authentication & Multi-User Support (brief)
Step 3: Advanced Core Features (brief)
...
```

- **Current step** is marked with ⚡
- Current step has detailed substeps
- Future steps have brief outlines only
- Only expand detail when ready to implement

### Updating Progress

When completing work:

1. ✅ Mark completed substeps in implementation.md
2. Update "Next Actions" section
3. Note any deviations or lessons learned
4. Don't expand future steps until current step is done

### Before Starting Work

Always check:
1. What's the current step? (look for ⚡ marker)
2. What are the detailed substeps?
3. Are there any blockers or dependencies?
4. What's the context for this work?

### After Completing Work

Always update:
1. Mark checkboxes as completed: `- [ ]` → `- [x]`
2. Move current step marker (⚡) if advancing
3. Update "Next Actions" with what's next
4. Note any decisions or deviations

## Project Structure Quick Reference

```
/home/kureshii/memogarden/
├── plan/
│   ├── budget_prd.md                   # Budget App Requirements (financial focus)
│   ├── memogarden_prd_v4.md            # Complete Platform PRD (Soil + Core + apps)
│   └── implementation.md               # Current step and progress
├── memogarden-core/                    # Flask backend
│   ├── memogarden_core/
│   │   ├── api/                        # API endpoints
│   │   ├── db/                         # Core API and database layer
│   │   ├── schema/                     # Database schema and migrations
│   │   └── utils/                      # Utility functions
│   ├── tests/                          # Test suite
│   └── docs/
│       └── architecture.md             # Technical architecture
├── scripts/
│   ├── run.sh                          # Start development server
│   ├── test.sh                         # Run tests
│   └── test-coverage.sh                # Run tests with coverage
├── .claude/
│   └── skills/                         # Agent Skills
└── AGENTS.md                           # This guide
```

## Common Workflows

### Starting a new feature
1. Check implementation.md for current step
2. Read relevant PRD sections
3. Review architecture.md for patterns
4. Write tests first (use memogarden-testing skill)
5. Implement feature
6. Update implementation.md

### Debugging an issue
1. Use memogarden-debugging skill
2. Check logs and error messages
3. Verify assumptions against architecture.md
4. Add tests to prevent regression

### Adding a new API endpoint
1. Use memogarden-api-endpoint skill
2. Follow the workflow there
3. Write tests before implementing
4. Update schema if modifying database

## Getting Help

If stuck:
1. Re-read PRD for context
2. Check implementation.md for current scope
3. Consult **dev-guide.md** for code patterns and conventions
4. Consult architecture.md for technical patterns
5. Look at existing code patterns
6. Use appropriate skill (testing, debugging, etc.)

### Key References

- **[dev-guide.md](memogarden-core/docs/dev-guide.md)** - Code patterns, utilities, conventions (READ THIS)
- **[architecture.md](memogarden-core/docs/architecture.md)** - Technical architecture and design
- **[memogarden_prd_v4.md](plan/memogarden_prd_v4.md)** - Complete platform architecture
- **[budget_prd.md](plan/budget_prd.md)** - Budget app requirements (when needed)
- **[implementation.md](plan/implementation.md)** - Current step and progress

## Future Design Reference

The `/plan/future/` directory contains design documents for features not yet implemented but architecturally significant:

- **schema-extension-design.md** - Schema extension system for multi-user compatibility
- **migration-mechanism.md** - Complete migration framework with validation and rollback
- **soil-design.md** - Immutable storage architecture for document archival (DEFERRED for Budget MVP)

**Important:** Soil implementation is DEFERRED until agent workflows are added. For Budget MVP:
- No Soil Items (emails, PDFs, statements)
- No schema snapshots (manual migration only)
- No delta archival
- Focus on Entity-based features only

When implementing related features or making architectural decisions, consult these documents to ensure alignment with the long-term design vision.

## Critical Architectural Constraints

### 🚫 What NOT to Do

1. **DO NOT use SQLAlchemy or any ORM**
   - Use raw SQL queries with parameterized statements
   - SQLite schema (`schema/schema.sql`) is the source of truth
   - Pydantic is ONLY for API request/response validation

2. **DO NOT add heavy dependencies**
   - Keep the dependency list minimal
   - Question every new package addition
   - Prefer stdlib when possible (e.g., sqlite3 over aiosqlite)

3. **DO NOT use PostgreSQL or other databases**
   - SQLite only (lightweight, portable, minimal setup)
   - Perfect for personal use and Raspberry Pi deployment

4. **DO NOT use async/await unless truly needed**
   - This is a personal system with low traffic
   - Synchronous code is simpler, more deterministic, easier to debug
   - Use Flask (not FastAPI) and built-in sqlite3 (not aiosqlite)

5. **DO NOT skip testing**
   - Write tests alongside features
   - Target >80% coverage for core functionality
   - Use pytest with pytest-flask

6. **DO NOT over-engineer**
   - Build what's needed for current step
   - Defer complex features (see implementation.md)
   - Simple > clever

### ✅ What TO Do

1. **Use centralized utilities (no loose datetime/uuid imports)**
   - **Date/time**: `from memogarden_core.utils import isodatetime`
     - `isodatetime.now()` - Current UTC as ISO string
     - `isodatetime.now_unix()` - Current UTC as Unix timestamp (for JWT)
     - `isodatetime.to_timestamp(dt)` - Convert datetime to ISO string
     - `isodatetime.to_datetime(ts)` - Convert ISO string to datetime
   - **UUIDs**: `from memogarden_core.utils import uid`
     - `uid.generate_uuid()` - Generate UUID v4 (ONLY place that imports uuid4)
     - **UUID prefixes**: `entity_` for Core Entities, `item_` for Soil Items (future)
     - **Note**: Database stores plain UUID v4, prefixes added at API layer
   - **Recurrence**: `from memogarden_core.utils import recurrence`
     - `recurrence.validate_rrule()` - Validate iCal RRULE strings
     - `recurrence.generate_occurrences()` - Generate occurrences from RRULE
     - `recurrence.get_next_occurrence()` - Get next occurrence after datetime
     - **All python-dateutil imports confined to this module**
   - **Domain types**: `from memogarden_core.schema.types import Timestamp, Date`
     - Use for type safety in API schemas and domain logic
   - See: `memogarden-core/docs/dev-guide.md` for complete patterns

2. **Use UTC timestamps everywhere**
   - Store as ISO 8601 text in SQLite: `2025-12-22T10:30:00Z`
   - Transaction dates are DATE only: `2025-12-22`
   - Never use local timezones in storage
   - All datetime operations go through `isodatetime` utility

3. **Write raw SQL queries**
   - Parameterized queries to prevent SQL injection
   - Use query builders in `db/query.py` for common patterns

4. **Confine external dependencies to single modules**
   - Create abstraction layers for complex third-party libraries
   - Only one module imports the external package directly
   - Rest of codebase uses the abstraction
   - Example: JWT tokens (only `auth/token.py` imports PyJWT)

5. **Follow the implementation plan**
   - Check current step in `plan/implementation.md`
   - Don't jump ahead to future steps

6. **Test everything**
   - Write tests before or alongside code
   - Use in-memory SQLite for tests
   - Use `isodatetime` for current time assertions in tests

7. **Document as you go**
   - Add docstrings to all functions
   - Update implementation.md progress

## Shell Command Best Practices

### Background Execution

**Use `run_in_background=True` instead of `&` and `2>&1`:**

```python
# ❌ AVOID - Triggers approval due to 2>&1 and &
Bash(command="poetry run flask --app memogarden_core.main run --debug 2>&1 &")

# ✅ PREFERRED - Use run_in_background parameter
Bash(
    command="poetry run flask --app memogarden_core.main run --debug",
    run_in_background=True
)
```

**Why:** `2>&1` redirects stderr which can hide destructive operations, triggering approval workflows. `run_in_background=True` is the proper pattern and doesn't require approvals for non-destructive commands.

### Command Chaining

**Use `&&` for dependent commands:**
```python
# Commands run sequentially, stops on first failure
Bash(command="cd memogarden-core && poetry install && poetry run pytest")
```

**Use `;` for independent commands:**
```python
# Commands run regardless of failures
Bash(command="mkdir -p data ; poetry run pytest")
```

### Approved Commands (No Approval Needed)

The following commands are pre-approved in `.claude/settings.local.json` and won't trigger workflows:
- `ln`, `ls`, `cat`, `tree` - File operations
- `poetry --version`, `poetry self`, `poetry install`, `poetry run` - Poetry operations
- `python`, `poetry run python`, `poetry run pytest` - Python execution
- `git add`, `git commit`, `git config`, `git status`, `git log` - Git operations
- `sqlite3`, `find`, `mkdir`, `touch` - Development utilities
- `curl` - HTTP testing (read-only)
- `./scripts/run.sh`, `./scripts/test.sh`, `./scripts/test-coverage.sh` - Project scripts

## Anti-Patterns to Avoid

❌ **Don't** use `pip install` - Use Poetry instead (`poetry add package-name`)
❌ **Don't** create ORM models when schema exists
❌ **Don't** add dependencies without discussion
❌ **Don't** skip tests "for now"
❌ **Don't** use local time zones
❌ **Don't** over-engineer for future needs
❌ **Don't** ignore the implementation plan
❌ **Don't** batch multiple unrelated changes
❌ **Don't** use `2>&1` in shell commands (triggers approval workflow unnecessarily)
❌ **Don't** import `datetime` directly in business logic (use `isodatetime`)
❌ **Don't** import `uuid4` directly (use `uid.generate_uuid()`)
❌ **Don't** scatter external library imports across modules (confine to one place)

✅ **Do** use Poetry for package management (`poetry add`, not `pip install`)
✅ **Do** write raw SQL queries
✅ **Do** keep dependencies minimal
✅ **Do** write tests alongside code
✅ **Do** use UTC everywhere
✅ **Do** build for current needs
✅ **Do** follow the plan
✅ **Do** make focused, atomic commits
✅ **Do** use `run_in_background=True` for long-running server processes
✅ **Do** use centralized utilities (`isodatetime`, `uid`, domain types)
✅ **Do** confine external dependencies to single modules


