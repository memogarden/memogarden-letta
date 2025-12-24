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

### Step 1: Verify Repository State

Check which repository you're committing to:

```bash
# Check current directory
pwd

# For memogarden-core changes
cd /home/kureshii/memogarden/memogarden-core

# For root-level changes (AGENTS.md, scripts, skills, plan/)
cd /home/kureshii/memogarden
```

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
- You're committing the right files
- Changes match what change-reviewer reviewed
- No unexpected files are included

---

### Step 3: Update plan/status.md (If Needed)

**Only update status.md for meaningful milestones:**

- ✅ Completed features or implementation plan steps
- ✅ New design documents or architectural decisions
- ✅ Major refactorings or improvements
- ❌ Minor bug fixes (can skip)
- ❌ Trivial changes (typos, comments)

**Update format:**
```markdown
### [Category] (YYYY-MM-DD)
- ✅ [Brief description of completed work]
- ✅ [Another completed item]
```

**Example:**
```markdown
### Schema Extension Design (2025-12-24)
- ✅ Created plan/future/ directory for future design work
- ✅ Documented schema extension system design
```

---

### Step 4: Stage Files for Commit

```bash
# Stage specific files
git add <file1> <file2> <file3>

# Or stage all modified files (use with caution)
git add -u

# Verify what's staged
git status
```

---

### Step 5: Create Commit

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
docs: add schema extension design

- Create plan/future/ directory for future design work
- Document schema extension system design and migration mechanism
- Add Memogarden Soil architecture documentation
```

**Avoid:**
```
update
fix stuff
done
```

---

### Step 6: Verify Commit

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

## Examples

### Example 1: Commit Feature Implementation

```bash
# 1. Navigate to memogarden-core
cd /home/kureshii/memogarden/memogarden-core

# 2. Review changes
git status
git diff

# 3. Stage files
git add memogarden_core/api/v1/transactions.py
git add tests/api/test_transactions.py

# 4. Create commit
git commit -m "feat(transaction): add transaction creation endpoint

- POST /api/v1/transactions with validation
- Add TransactionCreate and TransactionResponse schemas
- Include tests for successful creation and validation errors
- Auto-generate entity ID and create entity registry entry"

# 5. Verify
git log -1 --stat
```

---

### Example 2: Commit Documentation

```bash
# 1. Navigate to root
cd /home/kureshii/memogarden

# 2. Review changes
git status
git diff

# 3. Update status.md (if needed)
vim plan/status.md

# 4. Stage files
git add .claude/skills/change-commit/
git add plan/

# 5. Create commit
git commit -m "docs: create change-commit skill

- Focused skill for git commit operations
- Assumes change-reviewer has completed review
- Provides commit message format guidelines
- Separate from review process"

# 6. Verify
git log -1 --stat
```

---

## Remember

- This skill runs **after** change-reviewer
- User must have **confirmed intention** before committing
- Focus on **git operations**, not review
- Write **good commit messages** - future you will thank present you
