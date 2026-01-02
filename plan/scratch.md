# MemoGarden - Session Context (2026-01-02)

**Purpose**: Session notes for next session
**Last Updated**: 2026-01-02

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
- ✅ **5.3** - Data Models (COMPLETE 2025-12-31)
- ✅ **5.4** - Repository Layer (COMPLETE 2026-01-02)
- ✅ **5.5** - Transaction Capture Screen (Static UI) (COMPLETE 2026-01-02)
- ✅ **5.6** - Add State to Capture Screen (COMPLETE 2026-01-02)
- ⏳ **5.7** - Wire Up Data Flow
- 🔄 **5.8** - Transaction List Screen (UI complete, data connection pending)
- ⏳ **5.9** - Recurrence Management
- 🔄 **5.10** - Navigation Structure (screens connected, navigation flow established)
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

### 5. Data Models (Step 5.3)

**What We Built:**
- `Transaction` data class with SQLite serialization
  - Fields: id, date, amount, description, account, category, labels, extensionData, metadata
  - `fromMap()` factory constructor for database rows → model
  - `toMap()` method for model → database rows
  - JSON encoding/decoding for extensionData and metadata fields
- `Recurrence` data class with SQLite serialization
  - Fields: id, rrule, template, valid_from, valid_until, last_generated, next_occurrence, extensionData, metadata
  - Same serialization pattern as Transaction
  - Template stored as JSON string (matches database schema)

**Key Dart/Flutter Concepts Learned:**
- Factory constructors (`factory ClassName.fromMap()`)
- Type casting with `as Type` and `as Type?`
- Conditional map entries (`if (condition) 'key': value`)
- JSON encoding/decoding with `dart:convert` (json.encode, json.decode)
- Dart reserved keywords (renamed `extension` → `extensionData`)
- Named parameters with `required` keyword
- Nullable types (`Type?`)

**Design Decisions:**
- Kept dates as String (ISO 8601) for learning simplicity
- Will refactor to DateTime when date arithmetic needed
- Used vanilla constructor syntax (will refactor to `this.field` sugar later)
- Comma-separated labels (simple, can migrate to JSON later)
- Double for amounts (matches Core API, will handle precision with rounding helpers)

**Bug Fixes:**
- Fixed Recurrence constructor type mismatch (parameters were String?, should be Map<String, dynamic>?)
- Fixed fromMap() to use correct column name (extensionData, not extension)

**Code Quality:**
- Reviewed by code-review agent (found and fixed critical bugs)
- Reviewed by change-reviewer agent (verified alignment with implementation plan)
- Both models complete and ready for Repository layer

**Testing:**
- No unit tests yet (will add in Step 5.12 - Testing & Refinement)
- Manual verification: Models compile and match database schema

**Commits:**
- app-budget commit 620b84c: "feat(models): add Transaction and Recurrence data models"
- root repo commit e6172d7: "docs: mark Step 5.3 (Data Models) complete"

---

## Key Accomplishments This Session (2026-01-02)

### 1. Repository Layer (Step 5.4)

**What We Built:**
- `TransactionRepository` class with full CRUD operations
- `RecurrenceRepository` class with full CRUD operations
- Table name constants to avoid magic strings
- Input validation (null ID checks for create/update)
- Parameterized queries for SQL injection prevention

**Key Methods:**
- `create()` - Insert new record (auto-generates ID)
- `getAll()` - Retrieve all records with optional filtering
- `getById()` - Retrieve single record by ID
- `update()` - Update existing record
- `delete()` - Delete record by ID

**Design Decisions:**
- Business logic confined to repositories (not in widgets)
- Simple filtering (account, category) via optional parameters
- No complex queries yet (will add as needed)
- Repository layer ready for future sync integration

**Commits:**
- app-budget commit: (merged into b5bf609)

### 2. Transaction Capture Screen - Static UI (Step 5.5)

**What We Built:**
- Transaction capture screen with Monefy-inspired layout
- Large amount display (48pt font, grey bordered container)
- Calculator-style number pad (16 buttons: 0-9, decimal, operators, equals)
- Account and category dropdown selectors (placeholder data)
- Description text field
- Date display (static "Today")
- Green save button (56pt height for easy tapping)
- Placeholder for future recurrence button

**Key Flutter Concepts Learned:**
- `GridView.count` for grid layouts (crossAxisCount, childAspectRatio)
- `DropdownButtonFormField` for dropdowns
- `TextFormField` vs `TextField` (with form integration)
- Container decoration (borders, background colors)
- `EdgeInsets` for padding and margins
- `SizedBox` for fixed spacing
- `Row` with `Expanded` children for horizontal layouts

**Design Decisions:**
- Static UI first (Step 5.5), state management second (Step 5.6)
- Placeholder data for dropdowns (will add settings screen later)
- No date selector yet (shows static "Today")
- Number pad includes operator buttons (will ignore in Step 5.6)

**Commit:**
- app-budget commit b5bf609: "feat(ui): implement main screens with navigation" (includes list and settings screens too)

### 3. Transaction List Screen (Step 5.8 - UI Phase)

**What We Built:**
- Transaction list screen with collapsible category sections
- Drawer with account filter (All/Household/Personal)
- Drawer with date range selector (Day/Month/Year)
- Settings access via AppBar overflow menu (three dots)
- Category headers with emoji, name, total amount, and percentage
- Transaction items with date, description, and amount (red for expense, green for income)
- FAB (FloatingActionButton) for navigation to capture screen
- Expand/collapse state management

**Key Flutter Concepts Learned:**
- `Drawer` widget for side navigation
- `DrawerHeader` for drawer header section
- `ListView.builder` vs `ListView` (lazy loading)
- `StatefulWidget` for managing expand/collapse state
- `Map` data structure for sample transactions
- `Icon` widgets with `Icons` constants
- `Theme.of(context)` for theme colors
- `OverflowMenu` via `AppBar` actions

**Sample Data Structure:**
```dart
final Map<String, List<Map<String, dynamic>>> sampleTransactions = {
  'Food': [
    {'date': '2025-12-31', 'desc': 'Lunch at cafe', 'amount': -15.50},
    {'date': '2025-12-31', 'desc': 'Groceries', 'amount': -45.20},
  ],
  'Transport': [
    {'date': '2025-12-30', 'desc': 'Bus ticket', 'amount': -2.50},
  ],
  'Income': [
    {'date': '2025-12-30', 'desc': 'Freelance payment', 'amount': 500.00},
  ],
};
```

**Design Decisions:**
- UI-first (sample data) before data connection
- Group by category with totals
- Sort categories by total amount (descending)
- Sort transactions within category by date (ascending)
- Show percentages for budget tracking
- Color-coded amounts (red=expense, green=income)

### 4. Settings Screen (Step 5.10 - Partial)

**What We Built:**
- Settings screen with placeholder sections
- Accounts management section (placeholder)
- Categories management section (placeholder)
- Preferences section (Currency, Sync, Theme)
- Simple `ListTile` widgets for settings options

**Key Flutter Concepts Learned:**
- `ListView` with `ListTile` children
- `Switch` widget for toggle settings
- `DropdownButton` for currency selection
- `Divider` widgets for section separation
- AppBar with back navigation (automatic)

### 5. Navigation Structure (Step 5.10)

**What We Implemented:**
- FAB on transaction list screen → capture screen
- Overflow menu on transaction list screen → settings screen
- Automatic back navigation on all screens via AppBar
- MaterialPageRoute transitions between screens

**Navigation Flow:**
```
TransactionListScreen
├─ FAB → TransactionCaptureScreen
└─ Overflow menu → SettingsScreen

All screens → Back button returns to previous screen
```

**Key Flutter Concepts Learned:**
- `Navigator.push()` for screen transitions
- `MaterialPageRoute` for Material Design transitions
- `FloatingActionButton` with `floatingActionButtonLocation`
- `PopupMenuButton` for overflow menu
- AppBar automatically handles back navigation

### 6. Add State to Capture Screen (Step 5.6)

**What We Built:**
- Converted `TransactionCaptureScreen` from `StatelessWidget` to `StatefulWidget`
- Added state variables: `_amount`, `_selectedAccount`, `_selectedCategory`
- Added `TextEditingController` for description field
- Implemented `_onNumberPadPressed()` method for number pad interaction
- Connected dropdown `onChanged` handlers to update state
- Added `dispose()` method to clean up controller (prevents memory leaks)
- Implemented input validation:
  - Prevents multiple decimal points
  - Limits to 4 decimal places (for currency conversion)
  - Ignores operator buttons (+, −, ×, ÷, =)
  - Handles leading zero replacement

**Key Flutter Concepts Learned:**
- **StatefulWidget vs StatelessWidget**: When to use each
- **State lifecycle**: `initState()`, `build()`, `dispose()`
- **setState()**: Triggers UI rebuild when state changes
- **TextEditingController**: Accessing text field values
- **State variables**: Private fields with `_` prefix (`String _amount`)
- **RegExp**: Pattern matching for input validation
- **Memory management**: Disposing controllers to prevent leaks

**Number Pad Logic:**
```dart
void _onNumberPadPressed(String value) {
  // Only handle digits 0-9 and decimal .
  if (!RegExp(r'^[0-9.]$').hasMatch(value)) {
    return; // Ignore operators
  }
  setState(() {
    if (value == '.' && _amount.contains('.')) {
      return; // Prevent multiple decimals
    }
    if (_amount.contains('.') && _amount.split('.')[1].length >= 4) {
      return; // Limit to 4 decimal places
    }
    if (_amount == '0' && value != '.') {
      _amount = value; // Replace leading zero
    } else {
      _amount += value; // Append digit
    }
  });
}
```

**Why String for Amount (Not double)?**
- Partial input during typing (e.g., "12." is invalid as float)
- Trailing zeros matter for currency (12.50 vs 12.5)
- Easier to handle decimal point placement
- Will convert to double when saving (Step 5.7)

**Code Quality:**
- Reviewed by code-review agent (found and fixed critical memory leak)
- Reviewed by change-reviewer agent (verified Step 5.6 requirements met)
- Added `dispose()` method to prevent memory leaks
- Clean separation: UI state (Step 5.6) vs data persistence (Step 5.7)

**Commits:**
- app-budget commit 91246ea: "feat(ui): add state to transaction capture screen"
- root repo commit f42487b: "docs: mark Step 5.6 complete (2026-01-02)"

**Testing:**
- Manual testing: Number pad, dropdowns, text field all interactive
- Amount display updates in real-time
- Decimal point validation working (max 4 decimal places)
- Leading zero replacement working
- Operator buttons ignored (correct behavior)

**Next Steps:**
- Step 5.7: Wire Up Data Flow - Connect Save button to repository
- Step 5.8: Connect list screen to repository (pull real data)

---

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

**Last Updated**: 2026-01-02
**Session Focus**: Step 5.6 - Add State to Capture Screen (Next: 5.7 Wire Up Data Flow)
