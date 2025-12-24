---
name: process-improvement
description: Review errors/mistakes from session and propose process improvements (tests, tools, skills) to avoid recurrence. Evaluate complexity vs. benefit and assess tooling bloat.
---

# Process Improvement Skill

Use this skill to review errors or mistakes from a development session and propose systemic improvements to prevent recurrence.

## When to Use

**Trigger this skill when:**
- User asks to review what went wrong in a session
- Repeated errors or patterns of mistakes occur
- User asks about process improvements or better tooling
- User asks to review or simplify existing tooling/skills
- After a debugging session to prevent future issues

**DO NOT use this skill for:**
- Fixing individual bugs (use memogarden-debugging)
- Implementing new features
- Code reviews (use change-reviewer agent)
- Routine development work

---

## Workflow

### Step 1: Gather Session Context

**Review what happened:**
```bash
# Check recent git history
git log --oneline -10

# Review recent changes
git diff HEAD~5

# Check test failures (if any)
./scripts/test.sh

# Review any error logs or console output
```

**Identify:**
- Errors encountered
- Mistakes made
- Time-consuming debugging sessions
- Repetitive manual tasks
- Confusion or ambiguity in documentation
- Missing or unclear process steps

---

### Step 2: Analyze Root Causes

For each error or mistake identified, ask:

1. **What happened?** - Describe the error/mistake clearly
2. **Why did it happen?** - Root cause analysis
3. **Could it be easily avoided?** - Simple fix vs. systemic issue
4. **How often does it recur?** - One-time vs. pattern

**Common root causes:**
- Unclear documentation
- Missing tests
- Ambiguous process steps
- Lack of validation (API, schema, data)
- Manual steps prone to error
- Outdated tooling or skills
- Complexity in workflow

---

### Step 3: Propose Improvements

For each root cause, propose specific improvements:

#### Types of Improvements

**1. Tests**
- Add test for specific bug pattern
- Add integration test for workflow
- Add validation test for common mistakes
- Add regression test for fixed bugs

**2. Tools**
- Create new convenience script
- Enhance existing script
- Add CLI tool for common task
- Add linting or validation tool

**3. Skills**
- Create new skill for complex workflow
- Update existing skill with lessons learned
- Add examples to skill for common patterns
- Clarify ambiguous steps in skills

**4. Documentation**
- Update AGENTS.md with new pattern
- Update architecture.md with anti-patterns
- Add troubleshooting guide
- Clarify ambiguous documentation

**5. Process**
- Add pre-commit checks
- Add manual review step
- Change order of operations
- Add validation gate

---

### Step 4: Evaluate Proposals

For each proposed improvement, evaluate:

#### A. Marginal Complexity Increase

**Question:** Does the benefit justify the added complexity?

**Evaluation criteria:**
- **How often does this occur?** (frequent = higher value)
- **How severe is the error?** (severe = higher value)
- **How much complexity does the fix add?**
- **Is the fix proportional to the problem?**

**Complexity vs. Benefit Matrix:**

| Benefit / Complexity | Low | Medium | High |
|---------------------|-----|--------|------|
| **High** | ✅ Do it | ✅ Do it | ⚠️ Consider |
| **Medium** | ✅ Do it | ⚠️ Consider | ❌ Skip |
| **Low** | ⚠️ Consider | ❌ Skip | ❌ Skip |

**Examples:**
- ✅ **Add test for common bug** - Low complexity, High benefit → **Do it**
- ✅ **Add validation for frequent error** - Low complexity, High benefit → **Do it**
- ⚠️ **Create new agent skill** - Medium complexity, Medium benefit → **Consider**
- ❌ **Add complex automated tooling** - High complexity, Low benefit → **Skip**

---

#### B. Robustness vs. Fragility

**Question:** Will this process break from anticipated future changes?

**Evaluation criteria:**
- **Future-proof:** Works with anticipated changes
- **Flexible:** Doesn't lock in specific patterns
- **Maintainable:** Easy to update as codebase evolves
- **Brittle:** Likely to break with changes → **Avoid**

**Fragile patterns to avoid:**
- Tightly coupled to specific file structure
- Assumes specific implementation details
- Hard-coded values or paths
- Complex conditional logic
- Dependence on specific tool versions

**Robust patterns to prefer:**
- General principles over specific patterns
- Declarative over imperative
- Convention over configuration
- Simple over clever
- Composable over monolithic

---

### Step 5: Assess Tooling Complexity

**Threshold:** If tooling/skills complexity exceeds **~5% of agent context**, review and propose simplification.

**What counts as tooling:**
- `.claude/skills/` - Agent skills
- `.claude/agents/` - Specialized agents
- `scripts/` - Convenience scripts
- Complex development workflows
- Pre-commit hooks or validators

**Calculate complexity:**
```bash
# Count lines in skills
find .claude/skills -name "*.md" -exec wc -l {} + | tail -1

# Count lines in agents
find .claude/agents -name "*.md" -exec wc -l {} + | tail -1

# Count lines in scripts
find scripts -name "*.sh" -exec wc -l {} + | tail -1

# Total = sum of above
# Agent context = AGENTS.md + skills + agents
# Percentage = (Total tooling) / (Agent context)
```

**If complexity exceeds threshold:**
1. List all tools/skills/agents with usage frequency
2. Identify unused or redundant tooling
3. Identify overlapping functionality
4. Propose consolidation or removal

**Simplification strategies:**
- **Remove** - Unused or rarely-used tools
- **Consolidate** - Merge overlapping skills/tools
- **Generalize** - Make tools more broadly applicable
- **Document** - Add examples to reduce confusion

---

### Step 6: Generate Recommendations

**Report format:**

```markdown
## Process Improvement Review

### Session Summary
[Brief overview of session and issues encountered]

### Issues Identified

1. **[Issue Name]**
   - **What happened:** [Description]
   - **Root cause:** [Analysis]
   - **Frequency:** [One-time / Recurring]
   - **Severity:** [Low / Medium / High]

### Proposed Improvements

For each issue:
1. **[Proposal]**
   - **Type:** [Test / Tool / Skill / Doc / Process]
   - **Description:** [What to do]
   - **Complexity:** [Low / Medium / High]
   - **Benefit:** [Low / Medium / High]
   - **Robustness:** [Robust / Fragile]
   - **Recommendation:** [✅ Do it / ⚠️ Consider / ❌ Skip]

### Tooling Complexity Assessment

- **Current complexity:** [X lines, Y% of agent context]
- **Threshold:** 5% of agent context
- **Over threshold?** [Yes / No]

If over threshold:
- **Tools to remove:** [List]
- **Skills to consolidate:** [List]
- **Simplification recommendations:** [List]

### Priority Actions

**Immediate (high value, low complexity):**
1. [Action item]
2. [Action item]

**Consider (medium value/complexity):**
1. [Action item]
2. [Action item]

**Skip (low value or high complexity):**
1. [Action item] - Reason: [Explanation]

### Summary

[One-paragraph summary of key improvements to make]
```

---

## Examples

### Example 1: Missing Test for Common Bug

**Issue:** Repeatedly forget to call `db.commit()` after database changes.

**Root cause:** No test catches missing commits.

**Proposal:** Add test that verifies data persists after operation.

**Evaluation:**
- Complexity: Low (simple test)
- Benefit: High (catches common bug)
- Robustness: Robust (tests schema persistence)
- **Recommendation:** ✅ Do it

---

### Example 2: Complex Pre-commit Validation

**Issue:** Accidentally commit code with syntax errors.

**Proposal:** Add pre-commit hook that runs full test suite and linter.

**Evaluation:**
- Complexity: High (new tool, CI/CD setup)
- Benefit: Medium (catches syntax errors)
- Robustness: Fragile (tests may fail for unrelated reasons)
- **Recommendation:** ⚠️ Consider (simpler: just run linter)

---

### Example 3: Tooling Bloat

**Assessment:**
- Skills: 8 files, 2000 lines
- Agents: 5 files, 1500 lines
- Scripts: 10 files, 500 lines
- **Total:** 4000 lines
- **Agent context (AGENTS.md):** 200 lines
- **Complexity:** 4000 / 4200 = **95%** ❌ Over threshold

**Recommendations:**
- Remove rarely-used debugging agent
- Consolidate overlapping testing skills
- Add examples to AGENTS.md instead of separate skills
- Simplify process improvement skill (meta!)

---

## Guidelines

### DO

- ✅ Focus on systemic improvements, not one-off fixes
- ✅ Propose simple solutions over complex ones
- ✅ Prefer robust patterns that age well
- ✅ Consider maintenance burden of new tools
- ✅ Evaluate existing tooling for bloat
- ✅ Propose removals as well as additions

### DON'T

- ❌ Propose complex tooling for rare problems
- ❌ Add processes without clear benefit
- ❌ Create fragile automation that breaks easily
- ❌ Add more skills without consolidating old ones
- ❌ Increase tooling complexity without removing old tools
- ❌ Over-engineer solutions for simple problems

---

## Principles

1. **Simplicity First** - Prefer simple processes over complex tooling
2. **Proportionality** - Solution should match problem severity
3. **Robustness** - Solutions should work as codebase evolves
4. **Maintenance** - Consider long-term maintenance cost
5. **Removal** - Removing old tooling is as important as adding new
6. **Evidence-Based** - Propose based on actual errors, not hypothetical

---

## Remember

- **5% threshold** for tooling complexity
- **Complexity vs. benefit** matrix for evaluation
- **Robust over fragile** for long-term value
- **Remove before adding** to control bloat
- **Simple solutions** over complex automation
