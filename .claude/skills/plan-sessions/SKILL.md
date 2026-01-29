---
name: implementation-plan
description: Session-based implementation workflow for multi-session projects. Guides chunking work into context-limited, focused sessions with clear objectives, review, and commit cycles.
---

# Implementation Plan Skill

This skill provides a structured workflow for implementing multi-session projects using session-based chunking that respects Claude Code's context limits.

## When to Use This Skill

Use this skill when:
- Starting a new multi-session implementation project
- Breaking down a large PRD or specification into implementable chunks
- Planning work that will span multiple Claude Code sessions
- Need to ensure sessions stay within context limits (no /compact needed)

## Session-Based Workflow Principles

### 1. Session Definition

A **session** is a natural completion unit that:
- Focuses on ONE clear objective
- Stays within Claude Code's context limits (no compacting needed)
- Ends with working, tested, reviewable code
- Completes with a commit after review

### 2. Work Chunking Guidelines

**Session Scope:**
- Each session should accomplish a specific, measurable outcome
- Typical session: 1 major feature component OR 2-3 related small features
- If uncertain, prefer smaller sessions (can always continue in next session)

**Task Breakdown:**
- High-level steps: Brief details only (2-3 sentence summary)
- Current task: Full implementation detail when ready to execute
- Next task: Brief preview (helps with context continuity)

**Context Management:**
- Monitor context usage throughout session
- If approaching limits, complete current task and commit
- Don't try to cram more when near context limits

### 3. Session Execution Flow

```
┌─────────────────────────────────────────────────────────┐
│ SESSION START                                           │
├─────────────────────────────────────────────────────────┤
│ 1. Review session objective                            │
│ 2. Review brief task list                              │
│ 3. Clarify any requirements/preferences with user      │
└─────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│ TASK EXPANSION                                          │
├─────────────────────────────────────────────────────────┤
│ 1. Expand current task into full detail                │
│ 2. Present detailed plan to user                       │
│ 3. Get user approval before coding                     │
└─────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│ IMPLEMENTATION                                          │
├─────────────────────────────────────────────────────────┤
│ 1. Write code following approved plan                  │
│ 2. Write tests alongside code                          │
│ 3. Update documentation as needed                      │
│ 4. Run tests and verify functionality                  │
└─────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│ REVIEW & COMMIT                                         │
├─────────────────────────────────────────────────────────┤
│ 1. Review all changes made in session                  │
│ 2. Run final tests                                     │
│ 3. Check code quality and completeness                 │
│ 4. Commit with descriptive message                     │
└─────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│ SESSION END                                             │
├─────────────────────────────────────────────────────────┤
│ Session complete. Can start next session or pause.     │
└─────────────────────────────────────────────────────────┘
```

### 4. Planning a Multi-Session Project

When creating an implementation plan:

**Structure:**
```markdown
# Project Implementation Plan

## Session 1: [Descriptive Name]
**Objective:** [One clear sentence]
**Outcome:** [Measurable result]
**Brief tasks:**
- Task 1 (brief description)
- Task 2 (brief description)
- Task 3 (brief description)

**Critical files created/modified:**
- path/to/file1.py - Purpose
- path/to/file2.js - Purpose

## Session 2: [Next Session]
...
```

**Session Naming:**
- Use descriptive names that indicate what's being built
- Example: "Project Foundation & Database Setup" not "Initial Setup"
- Example: "Event Ingestion API" not "Backend Work"

**Outcome Statements:**
- Must be specific and verifiable
- Example: "Working API endpoint that stores events in database" ✓
- Example: "API mostly done" ✗

**Brief Task Details:**
- 3-10 bullet points per session
- Each bullet: 1 line, describes what not how
- Example: "Implement POST /api/events endpoint with validation" ✓
- Example: "Write code for the events API using Flask and add all the validation logic and database stuff" ✗

### 5. Starting a Session

**Prompt template:**
```
Let's start Session [N]: [Session Name]

Objective: [restate objective]

Please expand the tasks for this session into full implementation detail,
then wait for my approval before starting implementation.
```

**Claude should:**
1. Expand each brief task into detailed steps
2. Identify any clarification questions
3. Present the detailed plan
4. Wait for user approval
5. Only then begin implementation

### 6. Ending a Session

**Standard session end:**
1. Verify all session objectives met
2. Run full test suite
3. Review git diff for quality
4. Commit changes with detailed message
5. (Optional) Brief summary of what's next

**Early session end:**
- If context limits approaching: Complete current task, commit, note continuation point
- If blocked: Commit work-in-progress, document blocker clearly
- If requirements unclear: Pause, clarify with user, resume in new session

### 7. Context Limit Management

**Signs you're approaching limits:**
- Conversation feels long (20+ back-and-forth exchanges)
- Repeated information in responses
- Claude Code warnings about context usage

**Actions to take:**
1. Complete current task (don't start new major work)
2. Run tests on completed work
3. Commit what's done
4. Note where to continue in commit message
5. Start fresh session for remaining work

**Anti-patterns to avoid:**
- "Just one more small feature" when near limits
- Trying to finish entire session despite high context usage
- Skipping tests/commits to save context

## Example: Using This Skill

**User:** "I need to implement the PRD. Let's use session-based workflow."

**Assistant:**
"I'll structure this as a series of focused sessions. Let me create an implementation plan that breaks the work into context-limited chunks, each with a clear objective and outcome.

[Creates plan with 10-13 sessions, each scoped appropriately]

Ready to start? We can begin with Session 1: Project Foundation & Database Setup, or you can review the full plan first."

**User:** "Let's start Session 1."

**Assistant:**
"Starting Session 1: Project Foundation & Database Setup

Objective: Establish repository structure, database schema, and development environment

Let me expand the brief tasks into full detail:

1. Initialize directory structure
   - Create /jupyterhub and /dashboard directories
   - Set up basic Flask app structure (app.py, routes/, services/, tests/)
   - Create README.md with setup instructions

2. Database schema creation
   - Write migration for events table (actor, verb, object_type, object_id, object_context, result, timestamp, session_id)
   - Write migration for sessions table
   - Write migration for signals table
   - Write migration for settings table with default values

3. Railway configuration
   [...]

Does this detailed plan look good? Any questions before I start implementing?"

**User:** "Looks good, proceed."

**Assistant:** [Implements, tests, commits]

"Session 1 complete! ✓

Created:
- Repository structure with /jupyterhub and /dashboard
- Database migrations for all tables
- Basic Flask app with health check endpoint
- Development setup documentation

Next session: Session 2 - Event Ingestion API

Ready to continue or would you like to pause here?"

## Common Patterns

### Multi-File Features

When a feature spans multiple files:
- Group related files in same session if they're tightly coupled
- Split into separate sessions if files are independent
- Always implement tests in same session as feature code

### Iterative Refinement

If you need to iterate on a feature:
- Session N: Core feature implementation
- Session N+1: Polish and edge cases
- Session N+2: Performance optimization (if needed)

### Dependencies

When sessions have dependencies:
- Make dependencies explicit in session descriptions
- Front-load sessions that unblock others
- Note if sessions can be parallelized (rare but possible)

## Integration with Git

**Commit message format:**
```
Session [N]: [Brief summary]

[Detailed description of what was implemented]

Session objective: [Restate objective]
Outcome: [Verify outcome achieved]

Files added/modified:
- path/to/file1
- path/to/file2

Next: Session [N+1] - [Next session name]
```

**Benefits:**
- Git history maps directly to sessions
- Easy to find when specific features were added
- Clear progression through implementation plan

## Troubleshooting

**Session feels too big:**
- Split into 2 sessions with clearer boundaries
- Move "polish" tasks to follow-up session
- Defer nice-to-haves

**Session feels too small:**
- Combine with related session
- Add tests or documentation tasks
- Include deployment/verification tasks

**Unclear where to split:**
- Look for natural integration points (e.g., API complete, frontend complete)
- Consider what makes a good commit boundary
- Ask: "Could I stop here and have working code?"

---

**Note:** This skill formalizes the workflow used in Learning Analytics Platform implementation. Adapt session sizes based on project complexity and Claude Code context behavior.
