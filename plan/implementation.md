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

#### 2.1 Database Schema: Users and API Keys ✅ COMPLETE (2025-12-29)

**Commit:** 0744b9d - feat(auth): add users and api_keys database schema with migration support

**Completed Tasks:**
- ✅ Added users and api_keys tables to schema/schema.sql
- ✅ Created migration script (migrate_20251223_to_20251229.sql)
- ✅ Added bcrypt and pyjwt dependencies to pyproject.toml
- ✅ Implemented automatic migration runner in db/__init__.py
- ✅ Added 15 tests for users, api_keys, and migration functionality
- ✅ Schema version updated to 20251229

**Migration Design:**
- Runs automatically on app startup via init_db()
- Forward compatible with newer database versions
- Supports 20251223 → 20251229 migration path
- Uses file-based migration SQL scripts

**Test Results:**
- All 246 tests pass (including 15 new auth schema tests)

---

#### 2.2 Pydantic Schemas (User, APIKey, Auth) ✅ COMPLETE (2025-12-29)

**Commit:** 1a3729a - feat(auth): add Pydantic schemas for authentication

**Completed Tasks:**
- ✅ Created UserCreate, UserLogin, UserResponse schemas with password validation
- ✅ Created APIKeyCreate, APIKeyResponse, APIKeyListResponse schemas
- ✅ Created TokenPayload and TokenResponse JWT schemas
- ✅ Created AdminRegistrationResponse for admin setup
- ✅ Implemented password validation: min 8 chars, 1 letter, 1 digit
- ✅ Implemented username validation: alphanumeric, underscore, hyphen only
- ✅ Implemented username normalization to lowercase
- ✅ Added auth module structure (memogarden_core/auth/)
- ✅ Re-exported auth schemas in api/v1/schemas for convenience
- ✅ Added 32 comprehensive tests for all auth schemas

**Schema Features:**
- Password requirements: min 8 chars, at least one letter and digit
- Username: case-insensitive (normalized to lowercase), alphanumeric + underscore/hyphen
- API keys: full key only shown on creation, prefix in list responses
- JWT tokens: access_token, token_type, and user info in response
- All timestamps in ISO 8601 UTC format
- Pydantic v2 with modern Python 3.13 type hints

**Test Results:**
- All 32 tests pass (100% pass rate)
- Coverage: user schemas, API key schemas, JWT token schemas
- Validation tests for password complexity, username constraints, field types

**Files Modified:**
- memogarden-core/memogarden_core/auth/schemas/auth.py (316 lines)
- memogarden-core/memogarden_core/auth/__init__.py
- memogarden-core/memogarden_core/auth/schemas/__init__.py
- memogarden-core/memogarden_core/api/v1/schemas/__init__.py
- memogarden-core/tests/auth/test_schemas.py (519 lines)
- memogarden-core/tests/auth/__init__.py

**Schema Reference (Step 2.1):**

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

#### 2.3 JWT Token Service ✅ COMPLETE (2025-12-29)

**Commit:** (pending commit)

**Completed Tasks:**
- ✅ Added JWT configuration to config.py (jwt_secret_key, jwt_expiry_days)
- ✅ Implemented JWT token generation with user identity claims (sub, username, is_admin, iat, exp)
- ✅ Implemented JWT token validation and decoding with HS256 algorithm
- ✅ Implemented token introspection (get_token_expiry_remaining, is_token_expired)
- ✅ Added decode_token_no_validation for debugging/inspection
- ✅ Created 19 comprehensive tests for JWT token service
- ✅ Updated auth module to export token service

**Token Service Features:**
- Token claims: sub (user_id), username, is_admin, iat (issued at), exp (expires)
- 30-day default expiry (configurable via JWT_EXPIRY_DAYS)
- HS256 algorithm for signature verification
- Timezone-aware datetime handling (UTC)
- Returns TokenPayload with decoded claims
- Raises jwt.InvalidTokenError for invalid/expired tokens
- Helper functions: get_token_expiry_remaining(), is_token_expired()

**Configuration:**
- `JWT_SECRET_KEY`: Secret key for signing tokens (default: "change-me-in-production-use-env-var")
- `JWT_EXPIRY_DAYS`: Token expiry in days (default: 30)

**Dependency Confinement:**
- Only `memogarden_core.auth.token` imports PyJWT directly
- All token operations go through the token service module
- Clean public API: generate_access_token(), validate_access_token(), is_token_expired()

**Test Results:**
- All 297 tests pass (including 19 new JWT token service tests)
- Coverage: token generation, validation, expiry handling, error cases

**Files Modified:**
- memogarden-core/memogarden_core/config.py (added jwt_secret_key, jwt_expiry_days)
- memogarden-core/memogarden_core/auth/token.py (205 lines, new file)
- memogarden-core/memogarden_core/auth/__init__.py (export token module)
- memogarden-core/tests/auth/test_token.py (376 lines, new file)

---

#### 2.4 Authentication Endpoints ✅ COMPLETE (2025-12-29)

**Commit:** (pending commit)

**Completed Tasks:**
- ✅ Implemented auth service module with password hashing (bcrypt, work factor 12)
- ✅ Implemented user CRUD operations (create, get by username, get by ID, count)
- ✅ Implemented credential verification (password hashing and checking)
- ✅ Added AuthenticationError exception class
- ✅ Implemented GET /admin/register endpoint (HTML setup page, localhost only)
- ✅ Implemented POST /admin/register endpoint (create admin account, localhost only, one-time)
- ✅ Implemented POST /auth/login endpoint (authenticate and return JWT token)
- ✅ Implemented POST /auth/logout endpoint (no-op, stateless tokens)
- ✅ Implemented GET /auth/me endpoint (get current user info from token)
- ✅ Added startup warning log when no admin exists
- ✅ Added localhost check with configurable bypass for testing
- ✅ Registered auth blueprint in main.py
- ✅ Added AuthenticationError handler (401 status)
- ✅ Created 49 comprehensive tests (20 service tests + 29 endpoint tests)

**Auth Service Features:**
- Password hashing with bcrypt (work factor 12)
- User CRUD operations with entity registry integration
- Case-insensitive username lookup (stored as lowercase)
- Password verification with bcrypt.checkpw
- Admin user detection (has_admin_user)

**Authentication Endpoints:**
- `GET /admin/register` - HTML setup page (localhost only, no users exist)
- `POST /admin/register` - Create admin account (localhost only, one-time only)
- `POST /auth/login` - Authenticate and return JWT token (30-day expiry)
- `POST /auth/logout` - Logout (no-op, stateless JWT tokens)
- `GET /auth/me` - Get current user info from JWT token

**Security Features:**
- Admin registration only accessible from localhost (127.0.0.1, ::1)
- Admin registration only available when no users exist in database
- Password requirements: min 8 chars, at least one letter and digit
- Username normalization to lowercase (case-insensitive lookup)
- JWT token validation with HS256 algorithm
- Configurable bypass_localhost_check for testing

**Test Results:**
- All 346 tests pass (including 49 new auth tests)
- Coverage: password hashing, user CRUD, credential verification
- Coverage: admin registration (localhost enforcement, one-time only)
- Coverage: login flow (valid/invalid credentials, case sensitivity)
- Coverage: logout endpoint
- Coverage: /auth/me endpoint (valid token, invalid token, deleted user)

**Files Modified:**
- memogarden-core/memogarden_core/auth/service.py (265 lines, new file)
- memogarden-core/memogarden_core/api/auth.py (370 lines, new file)
- memogarden-core/memogarden_core/exceptions.py (added AuthenticationError)
- memogarden-core/memogarden_core/config.py (added bypass_localhost_check)
- memogarden-core/memogarden_core/main.py (auth blueprint, error handler, startup check)
- memogarden-core/tests/auth/test_service.py (298 lines, new file)
- memogarden-core/tests/auth/test_endpoints.py (360 lines, new file)

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

### Current Step Critical Files (Step 2.4)
- `/home/kureshii/memogarden/plan/prd.md` - Requirements source of truth
- `memogarden-core/memogarden_core/auth/` - Auth module (schemas, services, middleware)
- `memogarden-core/memogarden_core/auth/token.py` - JWT token generation and validation
- `memogarden-core/memogarden_core/db/` - Database operations (users table)
- `memogarden-core/memogarden_core/api/v1/` - API endpoints (or top-level routes for auth)

---

## Next Actions

**Step 1 COMPLETE** ✅ (Core Backend Foundation - 2025-12-27)

**Step 2.1 COMPLETE** ✅ (Database Schema: Users and API Keys - 2025-12-29)

**Step 2.2 COMPLETE** ✅ (Pydantic Schemas: User, APIKey, Auth - 2025-12-29)

**Step 2.3 COMPLETE** ✅ (JWT Token Service - 2025-12-29)

**Step 2.4 COMPLETE** ✅ (Authentication Endpoints - 2025-12-29)

**Currently on:** Step 2.5 (API Key Management Endpoints)

**Next:** Implement programmatic API key CRUD operations (list, create, revoke).

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
