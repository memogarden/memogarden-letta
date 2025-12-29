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

```
/home/kureshii/memogarden/
├── plan/
│   ├── prd.md                          # Product Requirements Document (source of truth)
│   └── implementation.md               # Implementation plan (read this!)
├── memogarden-core/                    # Flask backend (SQLite, no ORM)
│   └── docs/
│       └── architecture.md             # Technical architecture and design patterns
├── memogarden-budget/                  # Flutter app (web + Android) [to be created]
├── scripts/                            # Convenience scripts
│   ├── run.sh                          # Start development server
│   ├── test.sh                         # Run tests
│   └── test-coverage.sh                # Run tests with coverage
├── AGENTS.md                           # This file
└── CLAUDE.md -> AGENTS.md             # Symlink for Claude Code
```

### GitHub Repositories

- **Core API**: https://github.com/memogarden/memogarden-core
- **Budget App**: https://github.com/memogarden/memogarden-budget (to be created)
- **Organization**: https://github.com/memogarden

## Documentation Reference

The `/docs` folder contains detailed technical documentation:

- **[memogarden-core/docs/architecture.md](memogarden-core/docs/architecture.md)** - Core API design patterns,
  database layer, testing philosophy, utilities, and conventions.

When working on database operations, API endpoints, or utilities, consult `architecture.md` for
detailed implementation patterns and code examples.

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
- **change-reviewer** - Review changes against project plans before committing (pre-commit review)
- **change-commit** - Commit changes to git repository (use AFTER change-reviewer)

These skills allow AGENTS.md to focus on project context while providing detailed, task-specific
guidance on-demand. See [Claude Code Skills documentation](https://code.claude.com/docs/en/skills)
for how skills work.

## Essential Reading

Before working on any task, read these documents in order:

1. **[plan/prd.md](plan/prd.md)** - Product Requirements Document
   - Understand the "why" behind design decisions
   - Data model definitions
   - In-scope vs out-of-scope features

2. **[plan/implementation.md](plan/implementation.md)** - Implementation Plan
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
1. Use **change-reviewer** skill to review changes against project plans
2. After review and user confirmation, use **change-commit** skill to commit changes

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
