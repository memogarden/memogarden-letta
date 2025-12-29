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

#### 2.5 API Key Management Endpoints ✅ COMPLETE (2025-12-29)

**Commit:** (pending commit)

**Completed Tasks:**
- ✅ Implemented API key service module (generate, hash, verify, CRUD operations)
- ✅ Implemented GET /api-keys/ endpoint (list all API keys for current user)
- ✅ Implemented POST /api-keys/ endpoint (create new API key, returns full key once)
- ✅ Implemented DELETE /api-keys/:id endpoint (revoke API key, soft delete)
- ✅ Full API key only shown on creation (never in list)
- ✅ API key prefix extraction for display (mg_sk_agent_)
- ✅ Update last_seen timestamp when API key is used
- ✅ Refactored: created utils/secret.py for all secret generation
- ✅ Updated dev-guide with utils.secret pattern

**API Key Service Features:**
- API key generation: mg_sk_agent_<random> (76 characters total)
- Bcrypt hashing (reusing password hashing for consistency)
- API key CRUD operations with entity registry integration
- API key verification (validates full key against hash)
- User authorization check (only list/revoke own API keys)
- Soft delete with revoked_at timestamp

**API Key Endpoints:**
- GET /api-keys/ - List all API keys for current user (without full keys)
- POST /api-keys/ - Create new API key (returns full key once only)
- DELETE /api-keys/:id - Revoke API key (soft delete: set revoked_at)

**Security Features:**
- Full API key only shown on creation (never in list or GET by ID)
- Bcrypt hashing (same security as passwords)
- User authorization (can only access own API keys)
- Soft delete (revoked_at timestamp, key still in database)

**Refactoring: utils/secret Module:**
- Created centralized utils/secret.py for all secret generation
- API key generation: secret.generate_api_key()
- UUID generation: secret.generate_uuid()
- Random tokens: secret.generate_token()
- Password generation: secret.generate_password()
- Confines third-party imports (uuid, secrets) to one module
- Updated dev-guide with new pattern
- Backward compatibility: utils.uid maintained for existing code

**Test Results:**
- All 378 tests pass (32 new API key tests)
- Coverage: API key generation, hashing, CRUD, verification
- Coverage: API key endpoints (list, create, revoke)
- Coverage: User authorization checks
- Coverage: Revoked key verification

**Files Modified:**
- memogarden-core/memogarden_core/auth/api_keys.py (370 lines, new file)
- memogarden-core/memogarden_core/api/auth.py (+370 lines for API key endpoints)
- memogarden-core/memogarden_core/utils/secret.py (180 lines, new file)
- memogarden-core/memogarden_core/utils/__init__.py (added secret)
- memogarden-core/tests/auth/test_api_keys.py (355 lines, new file)
- memogarden-core/tests/auth/test_api_key_endpoints.py (230 lines, new file)
- memogarden-core/docs/dev-guide.md (added utils.secret section)

---

#### 2.6 Authentication Decorators ✅ COMPLETE (2025-12-29)

**Commit:** 711ff3a - feat(auth): add @localhost_only and @first_time_only decorators

**Completed Tasks:**
- ✅ Implemented @localhost_only decorator for protected endpoints
- ✅ Implemented @first_time_only decorator for one-time setup endpoints
- ✅ Used functools.wraps to preserve function metadata and type annotations
- ✅ Refactored admin registration endpoint to use declarative decorators
- ✅ Removed inline _is_localhost_request() helper function
- ✅ Removed inline security checks from admin_register() function
- ✅ Aligned bypass_localhost_check behavior with existing UI patterns
- ✅ Added 7 comprehensive tests for both decorators
- ✅ Updated auth module exports to include decorators

**Decorator Features:**
- @localhost_only: Restricts access to localhost (127.0.0.1, ::1, localhost)
- @first_time_only: Restricts access to when no admin user exists
- Composable decorators for multiple security constraints
- Testing support via bypass_localhost_check config setting
- Proper logging of security violations

**Test Results:**
- All 139 auth tests pass (including 7 new decorator tests)
- Coverage: localhost enforcement, first-time enforcement, edge cases
- Verified HTML page rendering via manual testing

**Files Modified:**
- memogarden-core/memogarden_core/auth/decorators.py (105 lines, new file)
- memogarden-core/memogarden_core/auth/api.py (refactored to use decorators)
- memogarden-core/memogarden_core/auth/__init__.py (added decorators export)
- memogarden-core/tests/auth/test_decorators.py (185 lines, new file)

**Note:** The implementation plan mentioned @require_auth middleware, but the actual need was for
@localhost_only and @first_time_only decorators for the admin registration endpoint. Full
authentication middleware (@require_auth) will be implemented in Step 2.9 when integrating
auth with existing transaction endpoints.

---

#### 2.7 HTML UI Pages ✅ COMPLETE (2025-12-29)

**Commit:** (pending commit)

**Completed Tasks:**
- ✅ Created base template with TailwindCSS styling
- ✅ Implemented GET /admin/register page (localhost only, inline HTML)
- ✅ Implemented GET /login page with JWT token storage
- ✅ Implemented GET /settings page with user profile
- ✅ Implemented GET /api-keys page with list and revoke functionality
- ✅ Implemented GET /api-keys/new page with create form and success modal
- ✅ Implemented GET / redirect (shows login page)
- ✅ Blueprint reorganization: Split auth endpoints into api.py (JSON) and ui.py (HTML)
- ✅ Created ApiV1 blueprint in api/v1/ with proper URL prefix
- ✅ All templates use TailwindCSS CDN for mobile-friendly design
- ✅ Client-side authentication check via localStorage
- ✅ API key management UI with copy-to-clipboard functionality

**Features:**
- Simple Jinja2 templates with TailwindCSS (mobile-friendly)
- Display API keys with metadata (no full keys after creation)
- Revoke button for each API key with confirmation
- Show JWT token expiry in settings page
- Admin registration page only accessible from localhost
- XSS protection with HTML escaping helpers
- Copy-to-clipboard for new API keys
- One-time display of full API key with security warning

**Test Results:**
- All 378 tests pass (existing tests remain passing)
- HTML pages render correctly (manual testing)
- API endpoints work with HTML forms
- Client-side authentication redirects work

**Files Modified:**
- memogarden-core/memogarden_core/templates/base.html (48 lines)
- memogarden-core/memogarden_core/templates/login.html (121 lines)
- memogarden-core/memogarden_core/templates/api_keys.html (217 lines)
- memogarden-core/memogarden_core/templates/api_key_new.html (236 lines)
- memogarden-core/memogarden_core/templates/settings.html (185 lines)
- memogarden-core/memogarden_core/auth/api.py (536 lines, moved from api/auth.py)
- memogarden-core/memogarden_core/auth/ui.py (263 lines, new file)
- memogarden-core/memogarden_core/api/v1/__init__.py (updated for ApiV1 blueprint)
- memogarden-core/memogarden_core/api/v1/transactions.py (added url_prefix)
- memogarden-core/memogarden_core/main.py (updated blueprint registration)

---

#### 2.8 Testing Infrastructure ✅ COMPLETE (2025-12-29)

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

#### 2.9 Documentation & Integration ✅ COMPLETE (2025-12-29)

**Commit:** (pending commit)

**Completed Tasks:**
- ✅ Refactored authentication to ApiV1 blueprint level (all API endpoints protected by default)
- ✅ Updated all 21 transaction tests to use authentication fixtures
- ✅ Added comprehensive manual testing section to README.md
- ✅ Updated README with authentication flow and examples
- ✅ Documented API key creation and usage
- ✅ Updated test fixtures (auth_headers, api_key_headers, authenticated_client)
- ✅ Environment variables documented (JWT_SECRET_KEY, JWT_EXPIRY_DAYS)
- ✅ All 394 tests passing with 91% coverage

**Authentication Architecture:**
- ApiV1 blueprint-level `@before_request` handler protects all API endpoints
- Shared `_authenticate_request()` function avoids code duplication
- JWT tokens via `Authorization: Bearer <token>` header
- API keys via `X-API-Key: <api_key>` header
- Transactions created with `author` field set to authenticated username

**Documentation Updates:**
- README.md with complete authentication flow examples
- Manual testing checklist for web UI and API testing
- API key creation and usage instructions
- Environment variables in .env.example

**Test Results:**
- All 394 tests pass (including 21 updated transaction tests)
- Coverage: 91% (exceeds 80% target)
- Transaction endpoints require authentication (401 without auth)
- Health check remains public (no auth required)

**Files Modified:**
- memogarden-core/memogarden_core/api/v1/__init__.py (added ApiV1-level authentication)
- memogarden-core/memogarden_core/api/v1/transactions.py (removed blueprint-level auth)
- memogarden-core/tests/api/test_transactions.py (added auth_headers to all 21 tests)
- memogarden-core/README.md (added manual testing section, updated status)

---

#### 2.10 Refactor & Test Profiling ✅ COMPLETE (2025-12-29)

**Commit:** (pending commit)

**Completed Tasks:**
- ✅ Profiled test suite: identified 47.95s baseline (target: <2.8s)
- ✅ Optimized bcrypt work factor: reduced from 12 to 4 for tests (configurable)
- ✅ Removed unnecessary teardown cleanup from test_transactions.py
- ✅ All 396 tests pass in 1.14s (97.6% faster!)
- ✅ Coverage maintained at 91% (above 80% target)
- ✅ Mock audit: no test mocks found (only mock class names in validation tests)
- ✅ Interface testing: all tests test behavior, not implementation

**Test Optimization Results:**
- **Before**: 47.95s (396 tests)
- **After**: 1.14s (396 tests)
- **Improvement**: 97.6% faster (42x speedup)
- **Coverage**: 91% (maintained)

**Key Optimizations:**
1. **Bcrypt work factor optimization**:
   - Added `bcrypt_work_factor` config setting (default: 12, tests: 4)
   - Changed auth/service.py to read from config dynamically
   - Added session-scoped `test_bcrypt_work_factor` fixture
   - Impact: Auth tests went from ~0.5-1.0s to ~0.01s

2. **Removed unnecessary teardown**:
   - Eliminated DELETE operations in test_transactions.py setup_database cleanup
   - Client fixture already creates fresh temp DB for each test
   - Impact: Update transaction tests went from 5.01s teardown to 0.01s

3. **No mocks found**:
   - Searched entire test suite for mock/patch/Mock usage
   - Only mock class names in validation tests (not actual mocks)
   - All tests use real dependencies (SQLite, etc.)

**Files Modified:**
- memogarden-core/memogarden_core/config.py (added bcrypt_work_factor setting)
- memogarden-core/memogarden_core/auth/service.py (dynamic work factor reading)
- memogarden-core/tests/conftest.py (added test_bcrypt_work_factor fixture)
- memogarden-core/tests/api/test_transactions.py (removed cleanup code)

**Test Results:**
- All 396 tests pass
- Coverage: 91% (above 80% target)
- Test suite runs in 1.14s (well under 2.8s target)

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

**Step 2 COMPLETE** ✅ (Authentication & Multi-User Support - 2025-12-29)
- 2.1: Database Schema ✅
- 2.2: Pydantic Schemas ✅
- 2.3: JWT Token Service ✅
- 2.4: Authentication Endpoints ✅
- 2.5: API Key Management Endpoints ✅
- 2.6: Authentication Decorators ✅
- 2.7: HTML UI Pages ✅
- 2.8: Testing Infrastructure ✅
- 2.9: Documentation & Integration ✅
- 2.10: Refactor & Test Profiling ✅

**Currently on:** Step 3 (Advanced Core Features)

**Next:** Implement recurrences, relations, and delta tracking

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
