---
name: change-commit
description: Commit changes to git repository. Use AFTER change-reviewer has completed review and user has confirmed intention. This skill focuses on git operations only.
---

# Change Commit Workflow

Use this skill **only after** the change-reviewer agent has completed its review and the user has confirmed their intention to proceed with committing.

## Precondition

⚠️ **DO NOT use this skill unless:**
1. change-reviewer has been run and delivered its review
2. User has explicitly confirmed they want to commit the changes
3. You understand what changes are being committed and why

If these conditions are not met, run change-reviewer first.

---

## Workflow

### Step 1: Auto-Detect Correct Repository

The skill automatically detects which repository needs the commit:

```python
# Auto-detect repository from changed files
# Returns: 'core' or 'root'
repo_root = detect_repository_root()
```

**Detection Logic:**
1. Check if any changed files are in `memogarden-core/` directory
2. Check if any changed files are in root directory (AGENTS.md, scripts, .claude/, plan/)
3. Prioritize `memogarden-core` if changes exist in both
4. Default to root if no core files changed

**Repository Mappings:**
- **core**: `/home/kureshii/memogarden/memogarden-core` (Backend code)
- **root**: `/home/kureshii/memogarden` (Documentation, plans, scripts, skills)

**Auto-Change Directory:**
```bash
# Automatically change to detected repository root
cd repo_root
```

**Key Features:**
- ✅ Prevents "pathspec did not match" errors
- ✅ No manual directory checking required
- ✅ Detects repository from changed file paths automatically
- ✅ Supports both root and core repositories in monorepo
- ✅ Clear separation: Backend (core) vs Documentation (root)

---

### Step 2: Review Files to Commit

```bash
# Check what's staged or modified
git status

# Review unstaged changes (if committing unstaged files)
git diff

# Review staged changes (if files already staged)
git diff --staged
```

**Verify:**
- You're committing in the correct repository (auto-detected)
- You're committing the right files
- Changes match what change-reviewer reviewed
- No unexpected files are included

---

### Step 3: Stage Files for Commit

```bash
# Stage specific files
git add <file1> <file2> <file3>

# Or stage all modified files (use with caution)
git add -u

# Verify what's staged
git status
```

---

### Step 4: Create Commit

```bash
git commit -m "<commit message>"
```

#### Commit Message Format

**Structure:**
```
<type>(<scope>): <subject>

<body> (optional)
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks
- `perf` - Performance improvements

**Examples:**

**Good:**
```
feat(transaction): add transaction creation endpoint

- POST /api/v1/transactions with validation
- Add TransactionCreate and TransactionResponse schemas
- Include tests for create and validation errors
```

```
docs: update skills with UUID systems and recurrence utility

- Add UUID systems clarification to development and schema skills
- Document Entity vs Item separation
- Add recurrence utility to centralized operations
- Updated Soil status to DEFERRED for Budget MVP
```

**Avoid:**
```
update
fix stuff
done
```

---

### Step 5: Verify Commit

```bash
# View commit details
git log -1 --stat

# Verify commit message
git log -1
```

**Confirm:**
- Commit message accurately describes changes
- All expected files are included
- No unexpected files are included
- Commit was made in the correct repository (auto-detected)

---

## Repository-Specific Notes

### ⚠️ CRITICAL: Multiple Git Repositories

The MemoGarden project has **THREE separate git repositories**. You MUST check which repository you're committing to.

```bash
# ALWAYS check current directory first
pwd
git status --short
```

### Repository Structure

```
/home/kureshii/memogarden/                    # Root repo (git #1)
├── .git/                                      # Root repository
├── AGENTS.md                                  # Agent guide
├── plan/                                      # Planning documents
├── scripts/                                   # Convenience scripts
├── .claude/                                   # Skills and agents
│
├── memogarden-api/                            # API package (git #2 - SEPARATE)
│   ├── .git/                                  # Separate repository!
│   ├── api/                                   # Flask application
│   │   ├── v1/                                # REST API endpoints
│   │   ├── semantic.py                        # Semantic API (/mg endpoint)
│   │   └── handlers/                          # Request handlers
│   ├── tests/                                 # Test suite
│   └── pyproject.toml                         # Poetry dependencies
│
└── memogarden-system/                         # System package (git #3 - SEPARATE)
    ├── .git/                                  # Separate repository!
    ├── system/                                # Core library
    │   ├── core/                              # Database operations
    │   ├── utils/                             # Utilities (uid, isodatetime)
    │   └── exceptions.py                      # Exception classes
    └── pyproject.toml                         # Poetry dependencies
```

### memogarden-api Repository

- **Git Repository:** Separate from root
- **Path:** `/home/kureshii/memogarden/memogarden-api`
- **Focus:** Flask HTTP API implementation
- **Test before committing:** `cd /home/kureshii/memogarden/memogarden-api && ./run_tests.sh ·ests/ -q`
- **Includes:**
  - `api/v1/` - REST API endpoints (/api/v1/transactions, etc.)
  - `api/semantic.py` - Semantic API dispatcher (/mg endpoint)
  - `api/handlers/` - Request handlers for Semantic API
  - `tests/` - Integration tests
  - `pyproject.toml` - Poetry configuration

### memogarden-system Repository

- **Git Repository:** Separate from root
- **Path:** `/home/kureshii/memogarden/memogarden-system`
- **Focus:** Core database library and utilities
- **Includes:**
  - `system/core/` - Database operations (entity, transaction, recurrence)
  - `system/utils/` - Shared utilities (uid, isodatetime, hash_chain)
  - `system/exceptions.py` - MemoGarden exception classes
  - `system/schemas/sql/` - Database schema migrations

### Root Repository

- **Git Repository:** Main repository
- **Path:** `/home/kureshii/memogarden`
- **Focus:** Documentation, planning, automation scripts
- **Includes:**
  - `AGENTS.md` - Agent guide (symlink to CLAUDE.md)
  - `plan/` - Planning documents (PRD, RFCs, implementation plan)
  - `scripts/` - Development automation scripts (lint.sh, pre-commit)
  - `.claude/` - Skills, agents, and configuration

---

## ⚠️ Common Pitfalls

### Pitfall 1: Wrong Repository

```bash
# ❌ WRONG - Committing to root when changes are in sub-repo
cd /home/kureshii/memogarden
git add api/semantic.py  # This won't work - api/ is a separate repo!

# ✅ CORRECT - Commit to the correct repository
cd /home/kureshii/memogarden/memogarden-api
git add api/semantic.py
git commit -m "feat(semantic): add /mg endpoint"
```

### Pitfall 2: Not Checking Current Directory

```bash
# ❌ WRONG - Assuming you're in the right directory
git commit -m "feat: add feature"  # Might commit to wrong repo!

# ✅ CORRECT - Always verify first
pwd                    # Check where you are
git status --short     # Check what will be committed
git commit -m "feat: add feature"
```

### Pitfall 3: Forgetting Sub-Repos Have Separate History

```bash
# Root repo has NO knowledge of memogarden-api commits
# memogarden-api repo has NO knowledge of root repo commits

# Always check which repo you're working in!
```

---

## Auto-Detection Logic

The skill uses the following logic to detect the correct repository:

```python
def detect_repository_root() -> str:
    """
    Auto-detect which repository needs the commit based on changed files.

    CRITICAL: MemoGarden has THREE separate git repositories:
    - /home/kureshii/memogarden (root - docs, plans, scripts)
    - /home/kureshii/memogarden/memogarden-api (Flask API)
    - /home/kureshii/memogarden/memogarden-system (Core library)

    Returns absolute path to repository root.
    """
    current_dir = os.getcwd()

    # If already in a known repository root, return it
    if current_dir == "/home/kureshii/memogarden/memogarden-api":
        return current_dir
    elif current_dir == "/home/kureshii/memogarden/memogarden-system":
        return current_dir
    elif current_dir == "/home/kureshii/memogarden":
        return current_dir

    # Check if current directory is inside one of the repos
    if current_dir.startswith("/home/kureshii/memogarden/memogarden-api"):
        return "/home/kureshii/memogarden/memogarden-api"
    elif current_dir.startswith("/home/kureshii/memogarden/memogarden-system"):
        return "/home/kureshii/memogarden/memogarden-system"
    elif current_dir.startswith("/home/kureshii/memogarden"):
        return "/home/kureshii/memogarden"

    # Default to current directory
    return current_dir
```

**Detection Steps:**
1. **Check current directory** - Most reliable indicator
2. **Check path prefix** - Detect if we're in a subdirectory
3. **Default** - Current directory if no match

**CRITICAL: Always Verify**
```bash
# Before any git operation, ALWAYS run:
pwd
git status --short

# This prevents committing to the wrong repository!
```

**Priority Order:**
1. **memogarden-api** → When working in `api/` directory
2. **memogarden-system** → When working in `system/` directory
3. **root** → When working in `plan/`, `scripts/`, `.claude/`

---

## Examples

### Example 1: Commit API Feature (memogarden-api repo)

**Before (manual directory navigation - error-prone):**
```bash
# Manual directory checking - easy to make mistakes!
cd /home/kureshii/memogarden  # Wrong repo!
git add api/semantic.py  # Error: api/ is a separate repo!
```

**After (correct repository detection):**
```bash
# Verify we're in the correct repository
pwd  # Should show: /home/kureshii/memogarden/memogarden-api
git status --short

# Stage and commit
git add api/semantic.py api/handlers/core.py
git commit -m "feat(semantic): implement Core bundle verbs

- Add /mg endpoint dispatcher with operation-based routing
- Implement create, get, edit, forget, query verbs
- Add Pydantic schemas for request/response validation
- 22 tests, all passing"

# ✅ Commit goes to memogarden-api repository
```

### Example 2: Commit Documentation (root repo)

**Before (manual directory navigation - error-prone):**
```bash
# Wrong directory!
cd /home/kureshii/memogarden/memogarden-api
git add ../plan/rfc_005.md  # Error: ../plan/ not in this repo!
```

**After (correct repository detection):**
```bash
# Verify we're in the correct repository
cd /home/kureshii/memogarden
pwd  # Should show: /home/kureshii/memogarden
git status --short

# Stage and commit
git add plan/rfc_005_memogarden_api_design_v7.md
git commit -m "docs: add Semantic API specification (RFC-005 v7)

- Define message-passing interface for /mg endpoint
- Specify request/response envelope format
- Document all verb bundles (Core, Soil, Context)
- Add null semantics and UUID prefix handling"

# ✅ Commit goes to root repository
```

### Example 3: Multi-Repository Session

**Scenario:** Working on Session 1 which touched both repos

```bash
# First commit - memogarden-api repo
cd /home/kureshii/memogarden/memogarden-api
pwd  # Verify!
git add api/semantic.py api/handlers/ tests/test_semantic_api.py
git commit -m "feat(semantic): implement Session 1 Core bundle verbs"

# Second commit - memogarden-system repo
cd /home/kureshii/memogarden/memogarden-system
pwd  # Verify!
git add system/core/entity.py
git commit -m "feat(entity): add update_data method for Semantic API"

# Third commit - root repo
cd /home/kureshii/memogarden
pwd  # Verify!
git add scripts/lint.sh scripts/pre-commit
git commit -m "chore: add development automation scripts"

# ✅ Three separate commits to three separate repos
```

---

## Guidelines

### DO

- ✅ Write clear, descriptive commit messages
- ✅ Use present tense ("Add feature" not "Added feature")
- ✅ Focus on impact in subject line (what does this enable?)
- ✅ Put details in body, not subject line
- ✅ Reference related issues or PRs when applicable
- ✅ Group related changes in one commit
- ✅ Update status.md for meaningful milestones

### DON'T

- ❌ Commit broken or incomplete code
- ❌ Commit without reviewing what's staged
- ❌ Mix unrelated changes (split into multiple commits)
- ❌ Commit debugging code (print statements, etc.)
- ❌ Write vague commit messages ("update", "fix")
- ❌ Update status.md for trivial changes

---

## Remember

- This skill runs **after** change-reviewer
- User must have **confirmed intention** before committing
- Focus on **git operations**, not review
- Write **good commit messages** - future you will thank present you
