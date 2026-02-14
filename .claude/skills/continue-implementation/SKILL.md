---
name: continue-implementation
description: MemoGarden implementation plan execution workflow. Use when continuing implementation on sessions from plan/memogarden-implementation-plan.md.
---

# MemoGarden Implementation Plan Workflow

This skill defines the standard execution cycle for working on the MemoGarden implementation plan.

## When to Use This Skill

Use this skill when:
- Working on tasks in `plan/memogarden-implementation-plan.md`
- Executing a session from the implementation plan
- Reviewing and committing session work
- Looking for process improvements

## Standard Session Execution Cycle

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. CONTINUE IMPLEMENTATION                                      │
├─────────────────────────────────────────────────────────────────┤
│ • Read current session in implementation plan                   │
│ • Check session objective and outcome                           │
│ • Note current progress (what's done, what's remaining)         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. UNPACK SESSION PLAN (if needed)                              │
├─────────────────────────────────────────────────────────────────┤
│ • If brief tasks lack clarity, expand into detailed steps       │
│ • Present expanded plan to user before proceeding               │
│ • Wait for user approval before coding                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. EXECUTE SESSION PLAN                                         │
├─────────────────────────────────────────────────────────────────┤
│ • Follow the expanded steps                                     │
│ • Write tests alongside code                                    │
│ • Run tests and ensure they pass                                │
│ • Use memogarden-development skill for patterns/constraints     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. UPDATE IMPLEMENTATION PROGRESS                               │
├─────────────────────────────────────────────────────────────────┤
│ • Mark completed checkboxes in plan document                    │
│ • Update session progress indicators                            │
│ • Note any deviations or blockers                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. CODE REVIEW                                                  │
├─────────────────────────────────────────────────────────────────┤
│ • Use code-review subagent for technical quality review          │
│ • Use change-reviewer subagent for plan alignment review        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. ADDRESS ISSUES                                               │
├─────────────────────────────────────────────────────────────────┤
│ • Critical issues: Fix immediately                              │
│ • Low-hanging fruit: Fix if quick and safe                      │
│ • Uncertain issues: Ping human for discussion                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. COMMIT CHANGES                                               │
├─────────────────────────────────────────────────────────────────┤
│ • Use change-commit skill                                       │
│ • Commit in logical chunks (related files together)             │
│ • Ping user to push when all commits ready                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. SESSION REVIEW - PROCESS IMPROVEMENT                         │
├─────────────────────────────────────────────────────────────────┤
│ • Look for obvious process improvements                         │
│ • Minimize human approval for routine tasks                     │
│ • Identify patterns to avoid repeating mistakes                 │
│ • Suggest improvements to user                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Step Details

### Step 1: Continue Implementation

Read the current session from the implementation plan:
```bash
cat plan/memogarden-implementation-plan.md
```

Identify:
- **Session objective**: What are we building?
- **Session outcome**: How do we know it's done?
- **Current progress**: What's already completed?

### Step 2: Unpack Session Plan

**Unpack (expand) when:**
- Brief tasks are too high-level to implement directly
- Dependencies or edge cases need clarification
- Multiple implementation approaches are possible
- User hasn't seen the detailed plan yet

**Don't unpack when:**
- Tasks are already clear and specific
- Just continuing from a previous unpacked plan
- Making trivial fixes or updates

**Example unpacking:**

Brief task:
```
- Implement POST /api/v1/transactions endpoint
```

Expanded detail:
```
1. Create Pydantic schema for TransactionCreate request
   - Fields: amount, date, description, category_id, counterparty_id
   - Validation: amount > 0, date is valid ISO date

2. Create handler function in api/v1/core/transactions.py
   - Decorate with @validate_request
   - Call Core.transaction_create()
   - Return 201 with created transaction

3. Add route in api/v1/core/__init__.py
   - Map POST /transactions to handler

4. Write tests in tests/test_transactions.py
   - Test valid request
   - Test validation errors
   - Test database insertion
```

### Step 3: Execute Session Plan

**Follow these patterns:**
- Write tests alongside code (or before)
- Use `memogarden-development` skill for architectural constraints
- Use `memogarden-testing` skill for testing patterns
- Use `memogarden-api-endpoint` skill for API endpoints
- Use `memogarden-schema` skill for database changes

**Running tests:**
```bash
# From memogarden-api directory
cd memogarden-api && ./run_tests.sh

# From memogarden-system directory
cd memogarden-system && ./run_tests.sh

# Or use convenience script
./scripts/test.sh (deprecated - use run_tests.sh)
```

### Step 4: Update Implementation Progress

Mark completed tasks in the plan document:

```markdown
## Session 14: [Name]
**Objective:** [One clear sentence]
**Outcome:** [Measurable result]

**Brief tasks:**
- [x] Task 1 (completed)
- [x] Task 2 (completed)
- [ ] Task 3 (in progress)
- [ ] Task 4 (not started)
```

Also update:
- "Next Actions" section if present
- Any blockers or dependencies discovered
- Deviations from the original plan (and why)

### Step 5: Code Review

**Always run both reviews:**

1. **code-review subagent** - Technical quality
   ```python
   Task("code-review", "Review code changes for quality", subagent_type="code-review")
   ```

   Reviews:
   - Code quality and style
   - Adherence to `architecture.md` patterns
   - Implementation correctness
   - Architectural constraints from `memogarden-development` skill

2. **change-reviewer subagent** - Plan alignment
   ```python
   Task("change-reviewer", "Review changes against plans", subagent_type="change-reviewer")
   ```

   Reviews:
   - PRD and implementation plan alignment
   - Documentation completeness
   - Implementation plan accuracy

### Step 6: Address Issues

**Issue categorization:**

| Category | Examples | Action |
|----------|----------|--------|
| **Critical** | Bugs, security issues, test failures, broken functionality | Fix immediately |
| **Low-hanging fruit** | Style inconsistencies, obvious refactors, missing docstrings | Fix if quick (<2 min) and safe |
| **Uncertain** | Architectural questions, trade-off decisions, future implications | Ping user for discussion |

**For uncertain issues:**
- Clearly explain the trade-offs
- Propose options with pros/cons
- Ask user for decision
- Don't guess or make assumptions

### Step 7: Commit Changes

**Use the change-commit skill:**
```
Skill("skill": "change-commit")
```

**Logical chunking strategy:**

Group related files in single commits:
```
feat: add transaction entity CRUD operations

Implementation of transaction CRUD with proper validation
and error handling.
```

Separate tests if substantial:
```
test(transaction): add comprehensive tests for CRUD operations

Tests cover:
- Valid transaction creation
- Validation errors
- Database insertion
- Retrieval and update
```

Separate documentation:
```
docs: update implementation plan - Session 14 complete

Completed transaction entity CRUD.
Next: Recurrence entity CRUD.
```

**After committing:**
- Ping user to push to remote
- Don't push automatically (user preference)

### Step 8: Session Review - Process Improvement

**Ask these questions:**

1. **What approvals could be automated?**
   - Did we ask for permission on routine tasks?
   - Are there safe commands that should be pre-approved in `.claude/settings.local.json`?

2. **What mistakes did we repeat?**
   - Same import pattern errors?
   - Same test structure issues?
   - Same documentation omissions?
   - Should we update a skill to document this?

3. **What could be made more efficient?**
   - Redundant file reads?
   - Repeated explanations?
   - Hand-off friction between agents?

4. **Should existing skills be updated?**
   - New pattern discovered that should be documented?
   - Anti-pattern identified that should be warned against?
   - Workflow change that should be added to this skill?

**Present findings to user:**
```
## Session Review - Process Improvements

### What Went Well
- [thing that worked smoothly]

### Issues to Address
- [repeating mistake] → Suggestion: [update skill X]

### Efficiency Improvements
- [redundant action] → Suggestion: [automation]
```

## Implementation Plan Structure

The plan follows this structure:

```
## Session N: [Descriptive Name]
**Objective:** [One clear sentence]
**Outcome:** [Measurable result]

**Brief tasks:**
- Task 1 (brief description)
- Task 2 (brief description)
- Task 3 (brief description)

**Context:** (optional)
- Dependencies on previous sessions
- PRD sections to reference
- Architecture patterns to follow

**Status:** (optional)
- In progress / Not started / Blocked
```

## Related Skills

Use together with these MemoGarden skills:

- **memogarden-development**: Development setup, architectural constraints, command patterns
- **memogarden-testing**: Testing philosophy and patterns
- **memogarden-api-endpoint**: API endpoint creation workflow
- **memogarden-schema**: Database schema modification workflow
- **memogarden-debugging**: Debugging and troubleshooting
- **memogarden-refactor**: Code refactoring and test optimization
- **change-commit**: Git commit workflow (use after reviews)

## Quick Reference

**Start a session:**
```
Read implementation plan → Unpack if needed → Execute
```

**End a session:**
```
Tests pass → Update plan → Code review → Fix issues → Commit → Review process
```

**Process improvement:**
```
What can we automate? What did we repeat? What should we document?
```
