# MemoGarden - Session Context (2025-12-31)

**Purpose**: Session notes for next session
**Last Updated**: 2025-12-31

---

## Current Status

**Step 5 IN PROGRESS** 🔄 (Flutter App Foundation - Learning-Focused Development)

**Approach:**
- User is new to Flutter/Dart
- Interactive development: User runs commands, AI guides
- UI-first: Build screens incrementally with visual feedback
- Small reviewable steps to avoid context window limits
- Local DB-first architecture (SQLite with integer PK, extension pattern for optional sync)

**Repository:** https://github.com/memogarden/app-budget

**Architecture Decisions (2025-12-31):**
- Local SQLite with integer PK for performance
- MemoGarden UUID in `extension` column (JSON)
- Hash-based sync via `extension.memogarden.last_sync_hash`
- Extension vs Metadata pattern (avoid migrations)
- Recurrences as first-class feature
- Simple state: `setState()` (no Riverpod yet)
- Repository layer between widgets and DB
- Local-first, sync-optional (works offline)
- No API calls in Phase 1 (DB-only)

---

## Step 5: Flutter App Foundation

### Substeps (12 total, learning-focused)

- ✅ **5.1** - Project Initialization & Setup (COMPLETE 2025-12-31)
- ✅ **5.2** - Database Schema Setup (COMPLETE 2025-12-31)
- ⏳ **5.3** - Data Models
- ⏳ **5.4** - Repository Layer
- ⏳ **5.5** - Transaction Capture Screen (Static UI)
- ⏳ **5.6** - Add State to Capture Screen
- ⏳ **5.7** - Wire Up Data Flow
- ⏳ **5.8** - Transaction List Screen
- ⏳ **5.9** - Recurrence Management
- ⏳ **5.10** - Navigation Structure
- ⏳ **5.11** - Design System Polish
- ⏳ **5.12** - Testing & Refinement

### Dependencies (pubspec.yaml)

```yaml
dependencies:
  flutter:
    sdk: flutter

  # Database
  sqflite: ^2.4.2
  path: ^1.9.1
  sqflite_common_ffi_web: ^1.1.0  # Web SQLite support

  # Local storage (for auth tokens)
  shared_preferences: ^2.5.4

  # Recurrence support (iCal RRULE)
  rrule: ^0.2.0
```

**Notes:**
- `sqflite_common_ffi_web` enables SQLite on web platform (IndexedDB-based)
- No `uuid` package needed (UUIDs from MemoGarden server or integer PK locally)
- `rrule` package validates iCal RRULE client-side (enables local-only usage)

---

## Key Accomplishments This Session (2025-12-31)

### 1. PRD v4.1: Hash-Based Change Tracking for Entities

**Major Addition to Platform Architecture:**
- Added Entity Change Tracking section to PRD v4
- Hash chain pattern: `hash = SHA256(content + previous_hash)`
- Entity stores: `hash`, `previous_hash`, `version` in Core
- Enables robust conflict detection and sync
- EntityDelta type for Soil (future)
- Delta Notification Service schema (future)

**Benefits Over Version Numbers:**
- Content-addressable state
- Tamper-evident (any change → new hash)
- Revert-safe (new hash even if content matches old)
- Provenance tracking via `previous_hash`

**Documentation Updated:**
- `plan/memogarden_prd_v4.md` → v0.4.1
- `plan/memogarden_prd_v4_delta_analysis.md` - Added Part 0: PRD v4.1 Updates
- `plan/future/soil-design.md` - Added note about EntityDelta format

### 2. Budget App Local Database Architecture

**Finalized Schema Decisions:**

**Integer PK + Extension Pattern:**
- Local ID: Auto-increment INTEGER for performance
- MemoGarden UUID: Stored in `extension.memogarden.uuid` (nullable)
- Local-only users: `extension` is NULL or empty
- Sync users: `extension.memogarden.uuid` contains Core entity UUID

**Hash-Based Sync:**
- `extension.memogarden.last_sync_hash`: Last known server hash
- `extension.memogarden.version`: Server version number
- Conflict detection without scanning full history

**Extension vs Metadata:**
- `extension`: Namespaced external data (MemoGarden, bank_sync, etc.)
- `metadata`: App-specific experimental features
- Both JSON to avoid schema migrations

**Recurrence Realization Pattern:**
- Generated transactions have `recurrence_id NOT NULL`
- Displayed differently (italic, grey, bold) to indicate "pending/projection"
- User "realizes" via button tap or editing (sets `recurrence_id = NULL`)
- Future occurrences regenerate fresh from template

**Client-Side RRULE Validation:**
- Uses `rrule` Dart package (iCal RFC 5545)
- Enables local-only usage without MemoGarden Core

**Schema Documentation:**
- `plan/budget_prd.md` - Added "Budget App Local Database" section
- `plan/budget_implementation.md` - Updated Step 5 with architecture decisions
- Dependencies updated (removed uuid, added rrule)

### 3. Flutter Project Initialization (Step 5.1)

**Setup Complete:**
- Flutter SDK installed: `~/.local/flutter`
- Chrome configured for web development
- Project initialized: `app-budget/` (org: net.memogarden)
- Dependencies configured (sqflite, path, shared_preferences, rrule)
- Web target verified (Chrome)
- Initial commit created (ab415b0)

**Installation Script Created:**
- `~/bin/install-flutter.sh` - Safe Flutter installation script
- Sanity checks: git installation, available disk space, network connectivity
- Flutter doctor validation

### 4. Database Schema Setup (Step 5.2)

**What We Built:**
- `DatabaseHelper` singleton class with factory constructor pattern
- Cross-platform database initialization (web + native support)
- `transactions` table: id, date, amount, description, account, category, labels, extension, metadata
- `recurrences` table: id, rrule, template, valid_from, valid_until, last_generated, next_occurrence, extension, metadata
- Extension-ready schema (JSON columns for future extensibility)

**Key Dart/Flutter Concepts Learned:**
- Singleton pattern with factory constructors
- Private named constructors (`_internal()`)
- `static const` for class-level constants
- Async/await for database operations
- Null safety (`?` and `!` operators)
- Platform detection (`kIsWeb` from `foundation.dart`)
- Multi-platform support (sqflite for native, sqflite_common_ffi_web for web)

**Web Support Challenges:**
- SQLite doesn't work natively on Flutter web
- Solution: Use `sqflite_common_ffi_web` package
- Must call `sqflite.databaseFactory = databaseFactoryFfiWeb` in constructor
- Web uses IndexedDB for storage (simulated filesystem)

**Extension System Design Discussion:**
- `extension` column: JSON-managed data by extensions (MemoGarden, GDrive, etc.)
- `metadata` column: JSON-managed data by Budget app
- Event hook mechanism planned (future): `onRegister()`, `onDeregister()`, `onEvent()`
- Extensions add/remove their own keys from `extension` object
- When all extensions removed their keys, row can be deleted

**Deletion Pattern (Simplified for MVP):**
- Hard delete immediately (no soft delete with `is_active`)
- Extension removes its key when done processing deletion event
- Future: Cleanup daemon checks if `extension` is empty before deleting row

**Testing:**
- Successfully tested on Chrome/web platform
- Both tables created correctly
- Console output shows: "Database initialized!" and table names

**Commits:**
- app-budget commit b3ac8e1: "feat: add database schema and helper with web support"

---

## Previous Accomplishments

**Step 2 COMPLETE** ✅ (Authentication & Multi-User Support)

**Step 4 COMPLETE** ✅ (Recurrences - 2025-12-30)

---

## Development Commands (Budget App)

```bash
# Run Budget app (web)
cd app-budget
flutter run -d chrome

# Run tests
flutter test

# Check dependencies
flutter pub outdated
```

## Repository URLs

- **Core API**: https://github.com/memogarden/memogarden-core
- **Budget App**: https://github.com/memogarden/app-budget (local: `app-budget/`)

---

**Last Updated**: 2025-12-31
**Session Focus**: Step 5.2 - Database Schema Setup (Next: Create database helper)
