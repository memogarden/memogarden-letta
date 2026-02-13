# MemoGarden - AI Agent Guide

This document provides context and guidelines for AI assistants (Claude, GPT, etc.) working on the MemoGarden project.

## Project Overview

**MemoGarden** is a personal memory system for financial transactions. It's not traditional budgeting software—it's a belief-based transaction capture and reconciliation system designed for both human users and AI agents.

### Core Philosophy

1. **Transactions Are Beliefs** - A transaction represents the user's understanding at the time of payment, not the bank's ledger
2. **Single Source of Truth** - All transactions flow through MemoGarden Core API
3. **Mutable Snapshot, Immutable Memory** - Current state can change, but all changes are logged via deltas
4. **Document-Centric Traceability** - Transactions link to immutable artifacts in Soil (emails, invoices, statements)
5. **Agent-First Design** - Humans and agents use the same APIs

## Repository Structure

⚠️ **CRITICAL:** MemoGarden has **three separate git repositories**. Always check which repository you're working in before committing changes.

### Core Repositories

1. **Root** (`/`) - Planning, scripts, agent configuration
2. **System** (`memogarden-system/`) - Core library (Soil + Core layers)
3. **API** (`memogarden-api/`) - Flask REST + Semantic API

### Related Repositories

- `app-budget/` - Budget app (Flutter) - Future development
- `memogarden-devcd/` - CD/automation for deployment
- `memogarden.github.io/` - Documentation site
- `hacm/` - Headless Agent Credential Manager

**For detailed repository structure, file listings, and module breakdowns, see [docs/repositories.md](docs/repositories.md).**

### ⚠️ Git Repository Boundaries

**Each repository has its own git history:**

1. **Root Repository** (`/`)
   - Contains: Planning documents, automation scripts, agent skills
   - Git command: `git status` (from root directory)
   - Commits here affect: docs, plans, scripts, .claude/

2. **API Repository** (`memogarden-api/`)
   - Contains: Flask application, Semantic API, tests
   - Git command: `git status` (from memogarden-api directory)
   - Commits here affect: api/, tests/
   - **Separate from root repository!**

3. **System Repository** (`memogarden-system/`)
   - Contains: Database operations, utilities, exceptions
   - Git command: `git status` (from memogarden-system directory)
   - Commits here affect: system/
   - **Separate from root repository!**

### ⚠️ Before Committing: Always Verify

```bash
# Step 1: Check current directory
pwd

# Step 2: Check what will be committed
git status --short

# Step 3: Only then commit
git commit -m "message"
```

**Common Mistake:**
```bash
# ❌ WRONG - Committing to root when changes are in sub-repo
cd /
git add api/semantic.py  # Error: api/ is not in this repo!

# ✅ CORRECT - Go to the sub-repo first
cd memogarden-api
git add api/semantic.py
git commit -m "feat: add semantic API"
```

## Documentation Reference

The `/docs` folder contains detailed technical documentation:

- **[docs/repositories.md](docs/repositories.md)** - Complete repository structure, module breakdowns, and file listings
- **[docs/quickstart.md](docs/quickstart.md)** - Getting started guide
- **[docs/deployment.md](docs/deployment.md)** - Deployment guide (RPi, Docker, etc.)
- **[docs/configuration.md](docs/configuration.md)** - Configuration reference (environment variables, TOML)
- **[memogarden-api/tests/README.md](memogarden-api/tests/README.md)** - Testing philosophy and workflows

When working on database operations, API endpoints, or utilities, use the relevant **skills** for implementation patterns and code examples.

## Agent Subagents

The `.claude/agents/` directory contains specialized subagents that autonomously handle complex,
multi-step review tasks.

**Available Subagents:**
- **code-review** - Review code changes for implementation quality, style, patterns, and adherence to project guidelines (architecture.md patterns, coding standards, architectural constraints)
- **change-reviewer** - Review changes against project requirements and plans (PRD alignment, implementation plan accuracy, documentation completeness)

These subagents provide comprehensive review coverage with distinct focuses:
- **code-review** focuses on code quality and technical implementation
- **change-reviewer** focuses on project alignment and documentation

## Agent Skills

The `.claude/skills/` directory contains task-specific skills that provide detailed workflows
and guidance. Claude loads these skills automatically when relevant to your task.

**Available Skills:**
- **continue-implementation** - Implementation plan execution workflow: unpack session, execute, test, review, commit, improve
- **memogarden-development** - Development environment setup, architectural constraints, anti-patterns, shell command best practices, working with the implementation plan
- **memogarden-testing** - Testing philosophy, running tests, writing tests, debugging test failures
- **memogarden-api-endpoint** - Workflow for creating new API endpoints
- **memogarden-debugging** - Debugging workflows for database, API, and Core API issues
- **memogarden-schema** - SQLite schema modification workflow, data model reference
- **memogarden-refactor** - Code refactoring and test optimization (duplication analysis, test profiling, mock audit, test cleanup)
- **process-improvement** - Review session errors/mistakes and propose systemic improvements (tests, tools, skills)
- **change-commit** - Commit changes to git repository (use AFTER reviews)

These skills allow AGENTS.md to focus on project context while providing detailed, task-specific
guidance on-demand. See [Claude Code Skills documentation](https://code.claude.com/docs/en/skills)
for how skills work.

## Essential Reading

Before working on any task, read these documents in order:

1. **[plan/memogarden_prd_v0_11_0.md](plan/memogarden_prd_v0_11_0.md)** - Platform Requirements Document
   - Complete platform architecture (Soil + Core)
   - All applications (Budget app, Project system)
   - Data model and entity definitions

2. **[plan/budget_prd.md](plan/budget_prd.md)** - Budget App Requirements (optional)
   - Budget app specific requirements
   - Financial transaction model
   - Read only when working on Budget app features

3. **[plan/memogarden-implementation-plan.md](plan/memogarden-implementation-plan.md)** - Implementation Plan
   - Current step and progress
   - Detailed substeps for active work
   - Architecture decisions and rationale

## Technology Stack

### Backend (memogarden-system + memogarden-api)
- **Language**: Python 3.13
- **Framework**: Flask (synchronous)
- **Database**: SQLite (no ORM - raw SQL only)
- **Data Access**: Core API with centralized entity operations
- **Validation**: Pydantic schemas + `@validate_request` decorator
- **Testing**: pytest with pytest-flask
- **Package Manager**: Poetry with poetry-plugin-shell
- **Production Server**: gunicorn

### Frontend (app-budget)
- **Framework**: Flutter
- **Platforms**: Web + Android
- **State Management**: TBD (Riverpod or Provider)
- **API Client**: http package

### Deployment
- **Local**: Development and testing
- **Production**: Raspberry Pi and/or Railway
- **Containerization**: Docker (when needed)
- **CD**: memogarden-devcd (webhook-based auto-deploy)

## Development Guidelines

**IMPORTANT**: When doing any development work on MemoGarden, ALWAYS use the **memogarden-development** skill. It contains critical architectural constraints, anti-patterns to avoid, and shell command best practices.

## Common Tasks

### Running Tests

**STANDARD WAY:** Use the standardized `run_tests.sh` script for each project. This ensures consistent behavior and provides grep-able output for automation.

```bash
# MemoGarden API Tests
./memogarden-api/run_tests.sh

# MemoGarden System Tests
./memogarden-system/run_tests.sh

# MemoGarden Client Tests
./memogarden-client/run_tests.sh

# With pytest arguments (passed through)
./memogarden-api/run_tests.sh -xvs
./memogarden-api/run_tests.sh tests/test_specific.py
./memogarden-api/run_tests.sh --cov=api --cov-report=html

# Get summary only (for agents - avoids full test output in context)
./memogarden-api/run_tests.sh --format=md --tb=no -q 2>&1 | grep -A 5 "Test Summary"
```

**Why use run_tests.sh:**
- Ensures correct Poetry environment is used (doesn't rely on venv activation)
- Works from any directory (changes to project dir automatically)
- Provides grep-able output with test run ID and summary
- Last 6 lines always contain summary (use `tail -n 6` for quick status)
- Consistent behavior across all MemoGarden projects
- Centralized implementation via `scripts/test_entrypoint.sh` (easy to update globally)

**Format options for agents:**
- `--format=markdown` (or `--format=md`) - Markdown output, easier for parsing
- `--format=plaintext` - Plain text without borders
- `--format=textbox` (default) - Unicode bordered box

**Agent note:** If you need functionality not supported by `run_tests.sh`, alert a human to improve `scripts/test_entrypoint.sh` centrally rather than using ad-hoc bash commands.

**Legacy method (deprecated):**
The old `scripts/test.sh` script still exists but is deprecated. It will be removed in a future version.

See [`memogarden-api/tests/README.md`](memogarden-api/tests/README.md) for complete testing documentation.

For testing workflows, philosophy, and debugging test failures, use the **memogarden-testing** skill.

### Writing a New API Endpoint

For the complete workflow and patterns, use the **memogarden-api-endpoint** skill.

### Working with SQLite Schema

For schema modification workflow, data model reference, and conventions, use the **memogarden-schema** skill.

### Working with the Implementation Plan

For detailed guidance on working with the implementation plan, use the **memogarden-development** skill.

### Debugging

For comprehensive debugging workflows, use the **memogarden-debugging** skill.

### Code Refactoring

For code refactoring and test optimization, use the **memogarden-refactor** skill. This includes:
- Code duplication analysis and DRY refactoring
- Test profiling and optimization (target: <2.8s)
- Interface vs implementation testing
- Mock audit and removal
- Test cleanup and consolidation

### Process Improvement

For reviewing session errors/mistakes and proposing systemic improvements, use the **process-improvement** skill.

### Completing Work

For task completion workflow (git commits, status updates, implementation plan updates):
1. Use **code-review** subagent to review code quality and technical implementation
2. Use **change-reviewer** subagent to review changes against project plans and requirements
3. After reviews and user confirmation, use **change-commit** skill to commit changes

## Communication Guidelines

When working with the user:

1. **Read before asking** - Check PRD and implementation plan first
2. **Be specific** - Reference file paths and line numbers
3. **Explain trade-offs** - When multiple approaches exist
4. **Follow the plan** - Don't suggest jumping ahead unless critical
5. **Update docs** - Keep implementation.md current

## Project Values

1. **Simplicity** - Simple code > clever code
2. **Transparency** - Clear > concise
3. **Testability** - Test early and often
4. **Incrementalism** - Small steps > big leaps
5. **Flexibility** - Learn and adjust

## Getting Help

If stuck or unsure:

1. Re-read the PRD for context
2. Check memogarden-implementation-plan.md for current scope
3. Look at existing code patterns
4. Ask the user with specific questions
5. Propose options with trade-offs

---

**Last Updated**: 2026-02-11
**For**: AI agents working on MemoGarden
**Maintained by**: Project contributors
