# MemoGarden Budget - Implementation Plan

## Overview

Building a lightweight personal expenditure capture and review system with two main components:
- **memogarden-core**: Flask backend with SQLite
- **memogarden-budget**: Flutter app (web + Android)

**Tech Stack:** Python 3.13, Flask (synchronous), SQLite (no ORM), Poetry, pytest

**Repositories:**
- Core: https://github.com/memogarden/memogarden-core
- Budget: https://github.com/memogarden/memogarden-budget (to be created)

---

## Implementation Steps

### Step 1: Core Backend Foundation ✅ COMPLETE (2025-12-27)

**Establish foundational backend API with SQLite database, transaction CRUD operations, and testing infrastructure.**

#### Completed Substeps:
- ✅ **1.1** - Project Setup & Structure (commit: 4bfbbe0)
- ✅ **1.2** - SQLite Database Schema with entity registry pattern
- ✅ **1.3** - Pydantic Schemas for API validation
- ✅ **1.4** - Flask Application & Configuration (CORS, error handling, logging)
- ✅ **1.5** - API Endpoints Implementation (7 transaction endpoints)
- ✅ **1.6** - Testing Infrastructure (231 tests, 90% coverage)
- ✅ **1.6.5** - Schema Extension & Migration Design (docs in `/plan/future/`)
- ✅ **1.7** - Documentation & Development Workflow (comprehensive README)

**Deliverables:**
- Complete CRUD API for transactions (create, read, update, delete, list, labels)
- Entity registry pattern for global metadata
- 231 tests with 90% coverage (exceeds 80% target)
- Comprehensive README with API documentation

See [memogarden-core/docs/architecture.md](memogarden-core/docs/architecture.md) for detailed architecture and design patterns.

---

### Step 2: Authentication & Multi-User Support (Next)

**Objective:** Add user management, JWT authentication, and API key support for agents.

**Components:**
- User table and registration
- JWT-based authentication for Budget app
- API key authentication for agent access
- Author tracking from auth context
- Permission model (user vs agent vs admin)
- Middleware for auth on protected endpoints

**Deliverables:**
- User registration and login endpoints
- JWT token generation and validation
- API key management
- Protected endpoints with auth middleware
- Author automatically set from context

---

### Step 3: Advanced Core Features

**Objective:** Implement recurrences, relations, and delta tracking.

**Components:**

#### 3.1 Recurrences
- Create `recurrences` table (id, rrule, entities, valid_from, valid_until)
- iCal rrule parsing library integration
- Recurrence template → transaction generation
- CRUD endpoints for recurrences
- UI in Budget app for managing recurring transactions

#### 3.2 Relations
- Create `relations` table (id, core_id, ref_id, ref_type, notes, created_at, revoked_on)
- Link any Core entity to Soil artifacts or other entities
- CRUD endpoints for relations
- Support multiple relation types (source, reconciliation, supersedes, occurs_at, occurs_during, other)

#### 3.3 Deltas (Audit Log)
- Create `deltas` table (id, entity_type, entity_id, field, old_value, new_value, rationale, author, timestamp)
- Emit deltas on all mutations (INSERT/UPDATE/DELETE)
- Delta tracking middleware/decorator
- Query endpoints for audit history

**Deliverables:**
- Recurrence system with iCal compatibility
- Relation management for document links
- Complete audit trail via deltas
- API endpoints for all three features

---

### Step 4: Flutter App Foundation

**Objective:** Initialize Budget app with basic UI and API integration.

**Components:**
- Create `memogarden-budget` repository
- Flutter project setup (web + Android)
- Project structure (clean architecture or feature-based)
- HTTP client for Core API
- State management (Riverpod or Provider)
- Navigation structure
- Design system (colors, typography, components)

**Screens:**
- Transaction capture screen (Monefy-inspired)
- Transaction list screen
- Settings screen

**Deliverables:**
- Flutter app running on web and Android
- API client connected to Core
- Basic transaction creation flow
- Simple, fast UI (<5 second capture goal)

---

### Step 5: Budget App Features

**Objective:** Complete Budget app with spending review and management features.

**Components:**

#### 5.1 Spending Review
- Daily spending view (list grouped by date)
- Monthly summary with category breakdown
- Yearly overview with trends
- Charts/visualizations (optional, defer if complex)

#### 5.2 Account & Category Management
- Account selection during transaction creation
- Category picker with icons
- Manage accounts (create, edit, delete)
- Manage categories (create, edit, delete)

#### 5.3 Transaction Management
- Edit transaction screen
- Delete transaction with confirmation
- Transaction detail view
- Search/filter transactions

#### 5.4 Recurring Transactions UI
- Create recurring transaction template
- View upcoming recurring transactions
- Mark occurrence as completed/skipped

**Deliverables:**
- Complete spending review interface
- Account and category management
- Full transaction CRUD in UI
- Recurring transaction interface

---

### Step 6: Agent Integration & Deployment

**Objective:** Enable agent workflows and prepare for production deployment.

**Components:**

#### 6.1 Agent Workflows
- Statement reconciliation endpoint
- Email parsing integration (with Soil)
- Transaction suggestion API
- Bulk operations for agents
- Reconciliation status tracking

#### 6.2 Testing & CI/CD
- Integration tests for full workflows
- E2E tests for critical paths
- GitHub Actions for CI
- Automated testing on PR

#### 6.3 Deployment
- Docker configuration for Core API
- Docker Compose for local full-stack
- Railway deployment configuration
- Raspberry Pi deployment guide
- Environment variable management
- Database backup strategy

#### 6.4 Documentation
- API documentation for agents
- Agent integration guide
- Deployment runbook
- Troubleshooting guide

**Deliverables:**
- Agent-ready API endpoints
- CI/CD pipeline
- Production deployment configurations
- Complete documentation

---

## Key Principles

### Database Philosophy
- **SQLite as source of truth**: Schema.sql defines reality, Pydantic validates API
- **Global entity registry**: Common metadata (lifecycle, grouping, supersession) stored in `entity` table, type-specific attributes in dedicated tables
- **Plain UUIDs**: Entity IDs are standard UUID4 strings (no prefixes), type stored in registry
- **UTC everywhere**: All timestamps in UTC ISO 8601 format
- **Day-level dates**: Transaction dates are DATE (YYYY-MM-DD), not timestamps
- **No ORM**: Raw SQL queries with sqlite3 for control and simplicity
- **Synchronous execution**: Deterministic, simpler debugging, sufficient for personal use

### API Philosophy
- **RESTful conventions**: Standard HTTP methods and resource URLs
- **Versioning**: `/api/v1/` prefix for future compatibility
- **Rich filtering**: Query parameters for common operations
- **Pagination ready**: Limit/offset from the start

### Development Philosophy
- **Minimal dependencies**: Only add what's needed
- **Local-first**: Everything runs without external services
- **Test early**: Tests written alongside features
- **Document as you go**: README and docstrings updated incrementally
- **Incremental delivery**: Each step delivers working software

---

## Critical Files Reference

### Current Step Critical Files
- `/home/kureshii/memogarden/plan/prd.md` - Requirements source of truth
- `memogarden-core/schema/schema.sql` - Database schema (source of truth)
- `memogarden-core/db/` - Core API: entity, transaction, query operations
- `memogarden-core/api/v1/transactions.py` - Core transaction API
- `memogarden-core/schemas/transaction.py` - API validation models
- `memogarden-core/pyproject.toml` - Dependencies and project config
- `memogarden-core/README.md` - Setup and development guide

---

## Next Actions

**Step 1.1 Complete** ✅ (commit: 4bfbbe0)
**Step 1.2 Complete** ✅ (refactored to sync Flask + sqlite3)
**Step 1.3 Complete** ✅ (Pydantic schemas with comprehensive tests)
**Step 1.4 Complete** ✅ (Flask app with CORS, error handling, logging)
**Step 1.5 Complete** ✅ (API Endpoints Implementation)
**Step 1.6 Complete** ✅ (Testing Infrastructure - 231 tests, 90% coverage)
**Step 1.6.5 Complete** ✅ (Schema Extension & Migration Design - documented in `/plan/future/`)
**Step 1.7 Complete** ✅ (Documentation & Development Workflow)

**Currently on:** Step 1 (Core Backend Foundation) COMPLETE! ✅ Ready for Step 2 (Authentication) or production deployment.

---

## Implementation Sequence Rationale

**Step 1 (Core Backend)** comes first because:
- Backend is single source of truth
- API contract defines all interactions
- Can validate data model in isolation
- Easy to test without UI dependencies

**Step 2 (Auth)** comes after Core because:
- Core CRUD validated first
- Auth affects all endpoints, easier to add after basics work
- Can test with "system" author initially

**Step 3 (Advanced Features)** deferred because:
- Recurrences, relations, deltas are complex
- Not needed for basic transaction capture
- Can learn from Step 1 & 2 experience

**Step 4-5 (Flutter)** come after stable API because:
- Need stable API contract first
- Backend can be tested independently
- Reduces rework from API changes

**Step 6 (Agents & Deployment)** last because:
- Most complex workflows
- Depends on all core features
- Can defer without blocking user value

---

**Guidelines**: Omit technical details (those belong in architecture.md or skills). Always update this file after completion of each task.
