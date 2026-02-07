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

⚠️ **CRITICAL:** MemoGarden has **THREE separate git repositories**. Always check which repository you're working in before committing changes.

```
/home/kureshii/memogarden/                    # Root repository (git #1)
├── .git/                                      # Root git repository
├── plan/                                      # Planning documents
│   ├── budget_prd.md                          # Budget App Requirements
│   ├── memogarden_prd_v4.md                   # Complete Platform PRD
│   ├── memogarden-implementation-plan.md      # Implementation plan
│   └── *.md                                   # RFC documents
├── scripts/                                   # Development scripts
│   ├── run.sh                                # Start server (from memogarden-api)
│   ├── test.sh                               # Run tests (from memogarden-api)
│   ├── lint.sh                               # Run ruff linter
│   └── pre-commit                            # Pre-commit hook
├── AGENTS.md                                  # This file
├── CLAUDE.md -> AGENTS.md                     # Symlink
│
├── memogarden-api/                            # Flask API package (git #2 - SEPARATE)
│   ├── .git/                                  # Separate git repository!
│   ├── api/                                   # Flask application
│   │   ├── v1/                                # REST API endpoints
│   │   │   ├── core/
│   │   │   │   ├── transactions.py           # Transaction CRUD
│   │   │   │   └── recurrences.py             # Recurrence CRUD
│   │   ├── semantic.py                        # Semantic API (/mg endpoint)
│   │   ├── handlers/                          # Semantic API handlers
│   │   ├── middleware/                        # Auth, decorators
│   │   └── main.py                            # Flask app
│   ├── tests/                                 # Integration tests
│   │   ├── test_transactions.py
│   │   ├── test_recurrences.py
│   │   ├── test_auth.py
│   │   ├── test_semantic_api.py
│   │   └── conftest.py                        # Test fixtures
│   └── pyproject.toml                         # Poetry dependencies
│
├── memogarden-system/                         # System package (git #3 - SEPARATE)
│   ├── .git/                                  # Separate git repository!
│   ├── system/                                # Core library
│   │   ├── core/                              # Database operations
│   │   │   ├── __init__.py                     # Core.get_core()
│   │   │   ├── entity.py                       # Entity operations
│   │   │   ├── transaction.py                  # Transaction operations
│   │   │   └── recurrence.py                   # Recurrence operations
│   │   ├── utils/                             # Shared utilities
│   │   │   ├── uid.py                          # UUID utilities
│   │   │   ├── isodatetime.py                  # Timestamp utilities
│   │   │   ├── hash_chain.py                   # Hash computation
│   │   │   └── secret.py                       # Secret generation
│   │   ├── exceptions.py                      # MemoGarden exceptions
│   │   ├── config.py                          # Configuration
│   │   └── schemas/sql/                       # Database schema
│   │       ├── core.sql                       # Core schema
│   │       └── migrations/                    # Schema migrations
│   └── pyproject.toml                         # Poetry dependencies
│
└── memogarden-budget/                         # Flutter app (FUTURE - to be created)
```

### ⚠️ Git Repository Boundaries

**Each repository has its own git history:**

1. **Root Repository** (`/home/kureshii/memogarden`)
   - Contains: Planning documents, automation scripts, agent skills
   - Git command: `git status` (from root directory)
   - Commits here affect: docs, plans, scripts, .claude/

2. **API Repository** (`/home/kureshii/memogarden/memogarden-api`)
   - Contains: Flask application, Semantic API, tests
   - Git command: `git status` (from memogarden-api directory)
   - Commits here affect: api/, tests/
   - **Separate from root repository!**

3. **System Repository** (`/home/kureshii/memogarden/memogarden-system`)
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
cd /home/kureshii/memogarden
git add api/semantic.py  # Error: api/ is not in this repo!

# ✅ CORRECT - Go to the sub-repo first
cd /home/kureshii/memogarden/memogarden-api
git add api/semantic.py
git commit -m "feat: add semantic API"
```

## Documentation Reference

The `/docs` folder contains detailed technical documentation:

- **[memogarden-core/docs/architecture.md](memogarden-core/docs/architecture.md)** - Core API design patterns,
  database layer, testing philosophy, utilities, and conventions.

When working on database operations, API endpoints, or utilities, consult `architecture.md` for
detailed implementation patterns and code examples.

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

1. **[plan/memogarden_prd_v4.md](plan/memogarden_prd_v4.md)** - Platform Requirements Document
   - Complete platform architecture (Soil + Core)
   - All applications (Budget app, Project system)
   - Data model and entity definitions

2. **[plan/budget_prd.md](plan/budget_prd.md)** - Budget App Requirements (optional)
   - Budget app specific requirements
   - Financial transaction model
   - Read only when working on Budget app features

3. **[plan/implementation.md](plan/implementation.md)** - Implementation Plan
   - Current step and progress
   - Detailed substeps for active work
   - Architecture decisions and rationale

3. **[memogarden-core/docs/architecture.md](memogarden-core/docs/architecture.md)** - Technical Architecture
   - Core API design (composition over inheritance, connection lifecycle)
   - Database layer patterns (WAL mode, query builders)
   - Testing philosophy (no mocks, behavior-focused)
   - Utility conventions (isodatetime, uid, domain types)

## Technology Stack

### Backend (memogarden-core)
- **Language**: Python 3.13
- **Framework**: Flask (synchronous)
- **Database**: SQLite (no ORM - raw SQL only)
- **Data Access**: Core API (`db` module) with centralized entity operations
- **Validation**: Pydantic schemas + `@validate_request` decorator
- **Testing**: pytest with pytest-flask
- **Package Manager**: Poetry with poetry-plugin-shell
- **Production Server**: gunicorn

### Frontend (memogarden-budget)
- **Framework**: Flutter
- **Platforms**: Web + Android
- **State Management**: TBD (Riverpod or Provider)
- **API Client**: http package

### Deployment
- **Local**: Development and testing
- **Production**: Raspberry Pi and/or Railway
- **Containerization**: Docker (when needed)

## Development Guidelines

**IMPORTANT**: When doing any development work on MemoGarden, ALWAYS use the **memogarden-development** skill. It contains critical architectural constraints, anti-patterns to avoid, and shell command best practices.

## Common Tasks

### Running Tests

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
2. Check implementation.md for current scope
3. Consult architecture.md for technical patterns
4. Look at existing code patterns
5. Ask the user with specific questions
6. Propose options with trade-offs

## Project Status

For current project status and completed work, see [plan/status.md](plan/status.md).

---

**Last Updated**: 2025-12-29
**For**: AI agents working on MemoGarden
**Maintained by**: Project contributors
