---
name: memogarden-update
description: Update workflow for completing tasks - git commits, status updates, implementation plan updates, and issue tracking. Use when finishing development work to document progress and commit changes.
---

# MemoGarden Task Completion Workflow

When you finish a development task, follow this workflow to update project documentation and commit your changes.

## Workflow Overview

1. Run tests to verify everything works
2. Update plan/status.md with completed work
3. Update plan/implementation.md if needed
4. Create git commit with descriptive message
5. Document any deviations or lessons learned

## Step 1: Verify Changes

Before committing, ensure your changes work:

```bash
cd /home/kureshii/memogarden/memogarden-core

# Run tests
./scripts/test.sh

# Or with coverage
./scripts/test-coverage.sh
```

**Checklist:**
- [ ] All tests pass
- [ ] No unexpected behavior
- [ ] Code follows architectural constraints (see memogarden-development skill)
- [ ] Documentation updated if needed

## Step 2: Update plan/status.md

Edit [plan/status.md](../../plan/status.md) to document completed work:

```markdown
## Completed Work

- ✅ [Brief description of what was completed]
- ✅ [Another completed item]

## Next Steps

- [ ] [Next task or TODO item]
```

**Guidelines:**
- **DO**: Include high-level summaries of completed features
- **DO**: Update date at the top
- **DON'T**: Include technical details (those belong in architecture.md or code)
- **DON'T**: List every small change - focus on meaningful progress

## Step 3: Update plan/implementation.md (if applicable)

If you completed items from the implementation plan:

1. Mark completed substeps with ✅
2. Move ⚡ marker if advancing to next step
3. Update "Next Actions" section
4. Note any deviations or decisions

**Example:**
```markdown
Step 1: Core Backend Foundation
  1.1 Project Setup & Structure
    ✅ 1.1.1 Clone and Initialize Repository
    ✅ 1.1.2 Set up Poetry and dependencies
```

## Step 4: Create Git Commit

Navigate to the appropriate directory and commit:

```bash
# For memogarden-core changes
cd /home/kureshii/memogarden/memogarden-core
git status
git add <files>
git commit -m "<commit message>"

# For root-level changes (AGENTS.md, scripts, skills)
cd /home/kureshii/memogarden
git status
git add <files>
git commit -m "<commit message>"
```

### Commit Message Format

Use clear, descriptive messages:

**Good:**
```
feat(transaction): add transaction creation endpoint

- POST /api/v1/transactions with validation
- Add TransactionCreate and TransactionResponse schemas
- Include tests for create and validation errors
```

**Avoid:**
```
update
fix stuff
done
```

### Commit Message Guidelines

- **WHAT**: Briefly describe what changed (50 chars or less for first line)
- **WHY** (optional but helpful): Context for the change
- **Separate details**: Put details in body, not subject line
- **Use present tense**: "Add feature" not "Added feature"
- **Focus on impact**: What does this enable?

### When to Commit

**DO commit:**
- After completing a logical unit of work
- When tests pass and code works
- After updating documentation
- Before switching to a new task

**DON'T commit:**
- Broken or incomplete code
- Without running tests first
- Mixed unrelated changes (split into multiple commits)
- Debugging code (print statements, etc.)

## Step 5: Document Learnings (Optional)

If you discovered something useful, document it:

- Update AGENTS.md if it's about agent workflows
- Update architecture.md if it's technical patterns
- Add to appropriate skill if it's task-specific guidance
- Update implementation.md "Next Actions" or "Notes"

## Example: Complete Workflow

```bash
# 1. Verify tests pass
cd /home/kureshii/memogarden/memogarden-core
./scripts/test.sh

# 2. Update status.md (manual edit)
vim ../../plan/status.md

# 3. Update implementation.md (if applicable)
vim ../../plan/implementation.md

# 4. Commit changes
git add memogarden_core/ tests/
git commit -m "feat(db): add TransactionOperations.create() method

- Auto-generates entity ID and creates entity registry entry
- Atomic transaction for entity + transaction creation
- Include tests for successful creation and validation"

# 5. Push if needed
git push
```

## Git Workflow Reminders

- **Atomic commits**: One logical change per commit
- **Test before commit**: Always run tests first
- **Review changes**: Use `git diff` before `git add`
- **Write good messages**: Future you will thank present you

## Multiple Repositories

MemoGarden has multiple repositories:
- **memogarden-core**: Backend API (main development)
- **Root directory**: AGENTS.md, scripts, skills (shared across repos)

Commit changes in the appropriate repository. For cross-repo changes, commit separately in each.

## Issue Tracking (Future)

When issue tracking is added:
- Reference issue IDs in commit messages: `#123`
- Close issues with: `Closes #123` or `Fixes #123`
- Update issue status after committing

---

**Remember**: These guidelines will evolve. Update this skill as we establish more patterns.
