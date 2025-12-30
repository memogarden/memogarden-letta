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

### memogarden-core

- **Focus:** Backend API implementation
- **Path:** `/home/kureshii/memogarden/memogarden-core`
- **Test before committing:** Run `./scripts/test.sh`

### Root Repository

- **Focus:** Documentation, scripts, skills, planning
- **Path:** `/home/kureshii/memogarden`
- **Includes:**
  - `AGENTS.md` - Agent guide
  - `.claude/skills/` - Agent skills
  - `scripts/` - Convenience scripts
  - `plan/` - Planning documents

---

## Auto-Detection Logic

The skill uses the following logic to detect the correct repository:

```python
def detect_repository_root() -> str:
    """
    Auto-detect which repository needs the commit based on changed files.

    Returns absolute path to repository root.
    """
    # Check if any changed files are in memogarden-core
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd="/home/kureshii/memogarden/memogarden-core",
        capture_output=True
    )
    core_files = result.stdout.strip().splitlines() if result.returncode == 0 else []

    # Check if any changed files are in root directory
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd="/home/kureshii/memogarden",
        capture_output=True
    )
    root_files = result.stdout.strip().splitlines() if result.returncode == 0 else []

    # Determine correct repository
    if core_files:
        return "/home/kureshii/memogarden/memogarden-core"
    elif root_files:
        return "/home/kureshii/memogarden"
    else:
        # Default to current directory
        return os.getcwd()
```

**Priority Order:**
1. **Core** → When core files changed
2. **Root** → When only root files changed
3. **Default** → Current directory if no changed files detected

---

## Examples

### Example 1: Commit Feature Implementation (Auto-Detection)

**Before (manual directory navigation - error-prone):**
```bash
# Manual directory checking - easy to make mistakes!
cd /home/kureshii/memogarden/memogarden-core
git commit -m "feat(transaction): add transaction creation endpoint"
```

**After (automatic repository detection - eliminates errors):**
```bash
# Skill auto-detects memogarden-core repository from changed file paths
git add memogarden_core/api/v1/transactions.py
git add tests/api/test_transactions.py

git commit -m "feat(transaction): add transaction creation endpoint

- POST /api/v1/transactions with validation
- Add TransactionCreate and TransactionResponse schemas
- Include tests for successful creation and validation errors
- Auto-generate entity ID and create entity registry entry"

# Skill automatically navigates to /home/kureshii/memogarden/memogarden-core
```

### Example 2: Commit Root Documentation (Auto-Detection)

**Before (manual directory navigation - error-prone):**
```bash
# Manual directory checking - easy to make mistakes!
cd /home/kureshii/memogarden
git commit -m "docs: create change-commit skill"
```

**After (automatic repository detection - eliminates errors):**
```bash
# Skill auto-detects root repository from skill file path
git add .claude/skills/change-commit/
git add plan/

git commit -m "docs: update change-commit skill

- Add auto-detection for correct repository
- Prevents 'pathspec did not match' errors
- Eliminates manual directory checking
- Separate concerns: Backend (core) vs Documentation (root)"

# Skill automatically navigates to /home/kureshii/memogarden
```

**Key Benefits:**
- ✅ Eliminates "pathspec did not match" errors
- ✅ No manual directory checking required
- ✅ Automatic repository detection from changed files
- ✅ Supports both repositories in monorepo structure
- ✅ Prevents committing to wrong repository
- ✅ Clear separation: Backend (core) vs Documentation (root)

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
