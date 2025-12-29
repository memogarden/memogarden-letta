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

### Step 2: Authentication & Multi-User Support (Active)

**Objective:** Add user management, JWT authentication for device clients, and API key support for agents.

#### 2.1 Database Schema: Users and API Keys

**Create tables for user accounts and API key management.**

Add to `schema/schema.sql`:

```sql
-- Users table (humans, device clients)
CREATE TABLE users (
  id TEXT PRIMARY KEY,              -- UUID4
  username TEXT UNIQUE NOT NULL,    -- 'kureshii' (case-insensitive)
  password_hash TEXT NOT NULL,      -- bcrypt hash
  is_admin INTEGER NOT NULL DEFAULT 0,  -- 0 = regular user, 1 = admin
  created_at TEXT NOT NULL,         -- ISO 8601 UTC
  FOREIGN KEY (id) REFERENCES entities(id) ON DELETE CASCADE
);

-- API Keys table (agents, scripts, programmatic clients)
CREATE TABLE api_keys (
  id TEXT PRIMARY KEY,              -- UUID4
  user_id TEXT NOT NULL,            -- References users.id
  name TEXT NOT NULL,               -- 'claude-code', 'custom-script'
  key_hash TEXT NOT NULL,           -- hashed API key
  key_prefix TEXT NOT NULL,         -- 'mg_sk_agent_' (for display)
  expires_at TEXT,                  -- ISO 8601 UTC or NULL (no expiry)
  created_at TEXT NOT NULL,         -- ISO 8601 UTC
  last_seen TEXT,                   -- ISO 8601 UTC or NULL
  revoked_at TEXT,                  -- ISO 8601 UTC or NULL (active if NULL)
  FOREIGN KEY (id) REFERENCES entities(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_active ON api_keys(revoked_at) WHERE revoked_at IS NULL;
```

**Schema constraints:**
- Usernames are unique, case-insensitive (store lowercase)
- `is_admin`: 0 = regular user, 1 = admin (future: household members)
- Passwords hashed with bcrypt (work factor 12)
- API keys: `mg_sk_<agent>_<random>` format (e.g., `mg_sk_agent_abc123...`)
- API key prefix is first 14 chars for UI display (never show full key after creation)
- Cascading deletes: when user deleted, their API keys are deleted
- MVP: Only admin registration (`is_admin=1`), no regular user creation

**Implementation tasks:**
1. Add `users` and `api_keys` tables to `schema/schema.sql`
2. Create migration script (or manual SQL) for existing databases
3. Add foreign key references to `entities` table
4. Update schema version tracking (if using migrations)
5. Write tests for schema constraints (unique usernames, cascading deletes)

**Files to modify:**
- `memogarden-core/schema/schema.sql` - Add new tables
- `memogarden-core/tests/test_schema.py` - Add schema validation tests

**Dependencies to add:**
- `bcrypt` or `passlib[bcrypt]` for password hashing
- `PyJWT` for JWT token generation/validation

---

#### 2.2 Pydantic Schemas (User, APIKey, Auth)

**Create validation schemas for authentication and API key management.**

**Components:**
- User schemas: `UserCreate`, `UserLogin`, `UserResponse`
- API key schemas: `APIKeyCreate`, `APIKeyResponse`, `APIKeyListResponse`
- JWT schemas: `TokenResponse`, `TokenPayload`
- Password validation: minimum length, complexity requirements

---

#### 2.3 JWT Token Service

**Implement JWT token generation and validation.**

**Components:**
- Token generation with user identity (user_id, username, exp)
- Token validation and decoding
- Token revocation (optional blacklist or short expiry)
- Configuration: secret key, expiry duration (30 days)

---

#### 2.4 Authentication Endpoints

**Implement admin registration (localhost only), login, logout, and profile endpoints.**

**Endpoints:**
- `GET /admin/register` - HTML setup page (localhost only, available only if no users exist)
- `POST /admin/register` - Create admin account (localhost only, one-time only)
- `POST /auth/login` - Authenticate and return JWT token
- `POST /auth/logout` - Revoke current token (optional blacklist)
- `GET /auth/me` - Get current user info from token

**Admin registration constraints:**
- Only accessible from localhost (127.0.0.1, localhost, ::1)
- Only available when no users exist in database
- Creates account with `is_admin=1` (admin role enforced)
- No regular user registration endpoint in MVP (only admins allowed)
- Server logs warning on startup if no admin exists: "Visit http://localhost:5000/admin/register to setup"
- After first user created, /admin/register returns 403 Forbidden

**Implementation notes:**
- Check `request.remote_addr` against localhost aliases
- Query user count on startup (cached or checked per request)
- Return friendly error message if admin exists but accessed from non-localhost
- Return friendly error message if accessed from localhost but admin already exists

**Features:**
- Login accepts both JSON and form data (for HTML forms)
- Return JWT token with 30-day expiry
- No public user registration (security by design)

---

#### 2.5 API Key Management Endpoints

**Implement programmatic API key CRUD operations.**

**Endpoints:**
- `GET /api-keys/` - List all API keys for current user (JSON)
- `POST /api-keys/` - Create new API key (returns full key once)
- `DELETE /api-keys/:id` - Revoke API key (soft delete: set revoked_at)

**Features:**
- Full API key only shown on creation (never in list)
- List shows: id, name, prefix, created_at, expires_at, last_seen, revoked_at
- Update `last_seen` timestamp when API key is used

---

#### 2.6 Authentication Middleware

**Implement authentication decorator for protected endpoints.**

**Components:**
- `@require_auth` decorator for Flask routes
- Parse `Authorization: Bearer <token>` header
- Distinguish JWT vs API key by format
- Extract user/agent identity and populate `g.author` context
- Return 401 Unauthorized for missing/invalid tokens
- Update `last_seen` for API keys

---

#### 2.7 HTML UI Pages

**Implement HTML pages for admin setup, auth, and API key management.**

**Pages:**
- `GET /admin/register` - Admin setup form (localhost only, shown only if no users exist)
- `GET /login` - Login form (POSTs to /auth/login)
- `GET /settings` - User profile and settings
- `GET /api-keys` - API key management UI (list, create, revoke)
- `GET /api-keys/new` - Create new API key form
- `GET /` - Redirect to /api-keys or /login (based on auth)

**Features:**
- Simple Jinja2 templates (minimal CSS, mobile-friendly)
- Display API keys with metadata (no full keys after creation)
- Revoke button for each API key
- Show JWT token expiry (if available)
- Admin registration page only accessible from localhost

---

#### 2.8 Testing Infrastructure

**Write tests for authentication and API key management.**

**Test coverage:**
- Admin registration (localhost only, no users exist, username uniqueness, is_admin=1 enforced)
- Login flow (valid credentials, invalid credentials)
- JWT token generation and validation
- API key creation, listing, revocation
- Authentication middleware (missing token, invalid token, expired token)
- Protected endpoints (with JWT, with API key, without auth)
- HTML page rendering (basic smoke tests)
- Password hashing (bcrypt verification)
- Localhost enforcement (reject non-localhost requests to /admin/register)
- is_admin field validation (future: regular user vs admin permissions)

**Target:** >80% coverage for new auth code.

---

#### 2.9 Documentation & Integration

**Update documentation and integrate auth into existing endpoints.**

**Components:**
- Update README.md with authentication flow and examples
- Document API key creation and usage
- Add `@require_auth` to existing transaction endpoints
- Update test fixtures to include authenticated users
- Environment variables: JWT_SECRET_KEY, JWT_EXPIRY_DAYS
- Add .env.example entries for auth configuration

**Deliverables:**
- Complete auth system with JWT and API keys
- HTML UI for user and API key management
- Protected transaction endpoints
- Comprehensive test coverage
- Updated documentation with auth examples

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

### Current Step Critical Files (Step 2.1)
- `/home/kureshii/memogarden/plan/prd.md` - Requirements source of truth
- `memogarden-core/schema/schema.sql` - Database schema (add users, api_keys tables)
- `memogarden-core/tests/test_schema.py` - Schema validation tests
- `memogarden-core/db/` - Core API (will need UserOperations, APIKeyOperations)
- `memogarden-core/pyproject.toml` - Add bcrypt, PyJWT dependencies

---

## Next Actions

**Step 1 COMPLETE** ✅ (Core Backend Foundation - 2025-12-27)

**Currently on:** Step 2.1 (Database Schema: Users and API Keys)

**Next:** Add `users` and `api_keys` tables to `schema/schema.sql` with foreign keys to `entities` table.

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
