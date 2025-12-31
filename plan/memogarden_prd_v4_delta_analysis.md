# PRD v4 Delta Analysis

**Date**: 2025-12-30
**Last Updated**: 2025-12-31
**Purpose**: Comprehensive comparison of current PRD vs PRD v4 and impact analysis

---

## Part 0: PRD v4.1 Updates (2025-12-31)

### Hash-Based Change Tracking for Entities

**What Changed in PRD v0.4.0 → v0.4.1:**

Added comprehensive **Entity Change Tracking** system with hash chain pattern, affecting all mutable entities in Core.

#### New Components

1. **Hash Chain Pattern**:
   - `Entity.hash`: SHA256 of current state
   - `Entity.previous_hash`: Hash of prior state (NULL for initial)
   - `Entity.version`: Monotonically increasing integer
   - Hash computation: `hash = SHA256(content + previous_hash)`

2. **EntityDelta Type (Soil - Future)**:
   - Immutable record of entity changes
   - Fields: `entity_uuid`, `commit`, `parent`, `version`, `changes`
   - Enables historical reconstruction and audit trails
   - Same pattern as ArtifactDelta (git-like history)

3. **Delta Notification Service (Future)**:
   - Separate table for tracking entity changes
   - Notifies subscribed apps of updates
   - Enables multi-app synchronization (Budget, Project System, etc.)
   - Schema: `delta_notification(entity_uuid, old_hash, new_hash, version, ...)`

#### Impact on Analysis

**Updated Data Model** (from Part 1):

| Aspect | Before v0.4.1 | After v0.4.1 |
|--------|--------------|--------------|
| **Entity state tracking** | `updated_at` timestamp only | `hash`, `previous_hash`, `version` |
| **Conflict detection** | Clock-based (fragile) | Hash-based (robust) |
| **Synchronization** | Not specified | Full conflict detection protocol |
| **Historical queries** | Scan all versions | Direct hash lookup in Soil |
| **Revert handling** | Ambiguous | Clear (new hash with different parent) |

**Benefits Over Version Numbers Alone**:
- Content-addressable state (hash uniquely identifies state)
- Tamper-evident (any change produces new hash)
- Revert-safe (reverting creates new hash, not duplicate)
- Provenance tracking (previous_hash provides full lineage)

#### Implementation Impact

**For Core API (memogarden-core)**:
- Add `hash`, `previous_hash`, `version` to `entity` table
- Implement `compute_entity_hash()` utility function
- Update all entity mutation endpoints to:
  1. Validate `based_on_hash` from client
  2. Compute new hash
  3. Store `(hash, previous_hash, version + 1)`
  4. Archive EntityDelta to Soil (future)
  5. Record delta notification (future)

**For Budget App (app-budget)**:
- Local DB schema: Add `last_sync_hash` column
- Sync protocol: Send `based_on_hash` with updates
- Conflict resolution: Detect hash mismatches, prompt user
- Benefits: Multi-device sync, offline-first with conflict resolution

**For Project System (future)**:
- ArtifactDelta already uses hash chain pattern
- EntityDelta provides same pattern for non-artifact entities
- Unified change tracking across all entity types

#### Clarified Architecture Decisions

1. **Hash Storage in Core**:
   - Store `hash` and `previous_hash` in entity table (not just Soil)
   - Avoids expensive recomputation on every validation
   - Enables fast conflict detection

2. **Soil Role**:
   - Stores EntityDeltas (immutable historical record)
   - Core stores current state + hash metadata
   - Clear separation: current vs historical

3. **Delta Notification Service**:
   - Separate from entity table (not stored in Core)
   - Enables efficient pub/sub for multi-app sync
   - Apps don't need to poll entire entity set

#### Updated Recommendations

**For Platform Foundation (Layer 1)**:
- Add hash computation utilities to Core API
- Add hash fields to entity table schema
- Implement conflict detection in all mutation endpoints
- Design EntityDelta archival mechanism (defer to Soil implementation)

**For Budget App (Layer 2)**:
- Include hash-based sync protocol in initial design
- Add `last_sync_hash` to local transaction table
- Plan for conflict resolution UI (merge, discard local, discard server)

**For Future Work**:
- EntityDelta implementation tied to Soil (currently deferred)
- Delta notification service built when multi-device sync needed
- Hash-based system foundationally supports CRDTs (future enhancement)

---

## Executive Summary

**PRD v4 reveals MemoGarden as a PLATFORM architecture**, not a single application. The current PRD and implementation plan focus on one application (Budget app), while PRD v4 describes the entire platform plus a second application (Project System).

### Platform Architecture

**Platform Layer (Soil + Core)**:
- Soil: Immutable storage layer (facts, timeline, artifacts)
- Core: Mutable state layer (user beliefs, working documents)

**Application Layer**:
- Budget App: Financial transaction management (current implementation)
- Project System: Collaborative design workspace (described in PRD v4)

### Key Finding
PRD v4 is **NOT a pivot**—it's the **complete platform specification**. The current PRD only describes the Budget app (one application on the platform).

---

## Part 1: Structural and Content Differences

### Document Structure Comparison

**Current PRD (plan/budget_prd.md)**:
1. Purpose
2. Core Principles (7 principles)
3. In Scope / Out of Scope
4. Data Model (Transactions, Recurrences, Relations, Artifacts, Deltas)
5. API Requirements
6. UI Scope
7. Success Criteria
8. Non-Goals

**PRD v4 (plan/memogarden_prd_v4.md)**:
1. Overview
2. Core Principles (10 principles)
3. Storage Architecture (Soil vs Core)
4. Entity Definitions (Item hierarchy with 8+ types)
5. Relations (comprehensive two-table model)
6. Conversation Structures
7. Item Type Hierarchy
8. Key Mechanisms (7 detailed mechanisms)
9. Data Storage Model (SQLite schema)
10. Reference Parsing
11. Future Work / Identified Gaps
12. Open Questions
13. Revision History

### Core Philosophy Changes

| Aspect | Current PRD | PRD v4 |
|--------|-------------|---------|
| **Scope** | Single application (Budget app) | Complete platform (Soil + Core) + two applications |
| **Purpose** | Financial memory system | Platform with multiple applications |
| **Metaphor** | Budgeting (Monefy-inspired) | Design exploration (git-inspired) for Project System |
| **Target Audience** | Individual users (for Budget app) | Multiple user types (individuals, teams, agents) |
| **Key Value** | Transaction capture & reconciliation | Unified platform for diverse applications |

### Data Model Transformation

**Current PRD Entities** (Budget app only):
- `Transaction` (financial records)
- `Recurrence` (recurring transactions)
- Simple `Relation` table
- `Artifact` (email/PDF links)
- `Delta` (audit log)

**PRD v4 Platform Entities** (Soil + Core layers):
- `Item` (base type with dual timestamps) - **Platform foundation**
- `Fragment` (semantic message units) - **Project System feature**
- `Message` (extends Note with fragments) - **Project System feature**
- `ToolCall` (tool invocation records) - **Platform feature**
- `ArtifactCreated` (artifact creation events) - **Platform feature**
- `ArtifactDelta` (git-like commit records) - **Platform feature**
- `SystemEvent` (system notifications) - **Platform feature**
- `ConversationLog` (branch container) - **Project System feature**
- `Frame` (participant positioning) - **Project System feature**
- `ArtifactCollection` (artifact registry) - **Project System feature**

**Note**: Budget app entities will be refactored to inherit from Item base type.

**Relations System Overhaul**:

Current: Single simple `relations` table
v4: Sophisticated two-model system:
- `UniqueRelation` (1:1): triggers, supercedes, replies_to
- `MultiRelation` (N:N): mentions, derived_from, contains
- Lifecycle management (Core ↔ Soil fossilization)

### Technical Architecture Changes

**New in PRD v4**:

1. **Two-Layer Storage Architecture**:
   - **Soil**: Immutable facts (timeline of what happened)
   - **Core**: Mutable state (user beliefs and evolving documents)
   - Clear separation: ground truth vs user understanding

2. **Reference System**:
   - Fragment references (`^a7f`)
   - Artifact line references (`goals_doc:15`)
   - Conversation log references
   - Item references with UUIDs

3. **Advanced Features**:
   - Fragment-based messaging (semantic decomposition)
   - Git-inspired versioning (commit-like deltas)
   - Branch exploration (parallel conversations)
   - Tool call tracking (full audit trail)
   - Dual timestamps (system time vs user-controlled time)
   - Timeline visualization
   - Shared tool model (joint cognitive system)

### Scope Changes

**Removed Scope (Current PRD)**:
- Budget limits and forecasting
- Tax reporting
- Double-entry accounting
- Financial reconciliation
- Currency conversion
- Transaction categorization

**Added Scope (PRD v4)**:
- Collaborative design workflows
- Parallel exploration of ideas
- Artifact versioning and history
- Tool usage tracking
- Reference resolution
- Branch management
- Conversation collapse/summary

---

## Part 2: Implementation Plan Impact

### Current Implementation Status

**Completed (Steps 1-2)**:
- ✅ Core backend foundation (Flask, SQLite, entity registry)
- ✅ Authentication & multi-user support (JWT, API keys)
- ✅ Transaction CRUD operations
- ✅ Basic database patterns and utilities

**In Progress (Step 3)**:
- 🔄 Advanced Core Features:
  - Recurrences table with iCal rrule
  - Relations table for linking entities
  - Deltas table for audit log

**Planned (Steps 4-6)**:
- 📋 Flutter app foundation
- 📋 Budget app features (spending review, accounts, categories)
- 📋 Agent integration & deployment

### Critical Finding: Implementation Plan Scope

The current **implementation.md** is building the **Budget App application** only. However, **PRD v4** describes the **entire MemoGarden platform** (Soil + Core) plus the **Project System application**.

**Implication**: The current implementation plan needs to be expanded to:
1. Build platform foundations (Soil + Core with Item base type)
2. Refactor Budget app to use platform foundations
3. Add Project System as second application on platform

### PRD v4 Requirements NOT in Implementation Plan

**Major Missing Components**:

1. **Project System Architecture** (Entirely New):
   - Two-layer storage model: Soil (immutable) + Core (mutable)
   - Artifact-first collaborative workspace
   - Git-inspired versioning system with commits and deltas
   - Stack-based exploration model with branching

2. **New Entity Types**:
   - Item base type with UUID, _type, realized_at, canonical_at
   - Message with fragments and conversation threading
   - ToolCall as first-class timeline items
   - ArtifactCreated and ArtifactDelta for document versioning
   - SystemEvent for system notifications

3. **Advanced Relation System**:
   - UniqueRelation and MultiRelation tables
   - Relation lifecycle management (Core ↔ Soil fossilization)
   - Relation kinds: triggers, supercedes, replies_to, mentions, derived_from, contains

4. **Conversation Structures**:
   - ConversationLog with parent UUID and branching
   - Frame for participant positioning
   - Stack for branch management
   - Project as top-level container

5. **Fragment System**:
   - Semantic fragment generation with hash-based IDs
   - Inline reference resolution
   - Fragment-based content organization

6. **Shared Tool Model**:
   - Joint Cognitive System with user/agent tool sharing
   - Symmetric operations for ArtifactReader
   - Multiple observability modes

7. **Multi-Artifact Changes**:
   - Single message triggering multiple artifact updates

### Implementation Plan Steps Requiring Updates

**Step 3: Advanced Core Features** - Needs significant expansion:
- Add Artifact and ArtifactDelta entities
- Add Item base type with hierarchy
- Add conversation log structures
- Implement fragment system
- Add relation lifecycle management

**Step 4: Flutter App Foundation** - Needs updates for:
- Timeline visualization UI
- Reference resolution and display
- Branch navigation and management
- Fragment-based content display

**New Step Needed: Project System Implementation**:
Between Step 3 and Step 4, need a new step for:
- Soil database with Items and Relations
- Core storage for Artifacts
- Conversation management system
- Fragment generation and parsing
- Reference resolution system

---

## Part 3: Future Plans Alignment

### Future Plans Analysis

The `plan/future/` directory contains:
- `schema-extension-design.md` - Schema versioning and extension system
- `migration-mechanism.md` - Database migration workflow
- `soil-design.md` - Immutable storage architecture

### Alignment with PRD v4

**Strongly Aligned**:

1. **Core Philosophy**:
   - ✅ "Single Source of Truth" principle
   - ✅ Immutable Soil for facts vs mutable Core for beliefs
   - ✅ Document-centric traceability
   - ✅ Mutable snapshot / immutable memory paradigm

2. **Schema Extension System**:
   - Future plans implement PRD v4's "Schema as Living Document" principle
   - Two-tier schema system (base + extensions)
   - Forward compatibility requirements
   - Extension archival in Soil
   - Version capability declaration: `{base_schema}+{extension_date}`

3. **Migration Mechanism**:
   - Directly implements PRD v4's "forward-only" migration requirement
   - Export → Drop → Create → Import workflow
   - Forward compatibility (all fields optional or have defaults)
   - Rollback as new migrations (not destructive)
   - Data loss prevention with user confirmation

4. **Soil Architecture**:
   - Provides technical foundation for PRD v4's artifact requirements
   - Immutable append-only storage
   - Document-centric organization (emails, PDFs, statements)
   - Core-delta for change history
   - Fossils for long-term compaction

### Features in Future Plans That Should Move to Implementation

**High Priority** (Should be in v1):

1. **Extension System** (`schema-extension-design.md`):
   - Base schema versioning (v1.0, v1.1, v2.0)
   - Extension mechanisms (structured + JSON)
   - Extension metadata tracking
   - Migration infrastructure

2. **Migration Infrastructure** (`migration-mechanism.md`):
   - Schema compatibility checking
   - Export/import transformation
   - Default value application
   - Rollback mechanisms

**Medium Priority** (Should be in v1.1):

3. **Soil Storage System** (`soil-design.md`):
   - Directory structure
   - Archival workflows
   - Basic fossilization

4. **Advanced Relation System**:
   - UniqueRelation vs MultiRelation tables
   - Relation lifecycle (Core ↔ Soil)
   - Query abstraction layer

### Minor Conflicts and Differences

1. **Scope vs Detail**:
   - **PRD v4**: High-level requirements
   - **Future Plans**: Comprehensive technical design
   - **Resolution**: Future plans provide the "how" to PRD v4's "what"

2. **Artifact Definition**:
   - **PRD v4**: Focuses on financial artifacts (emails, PDFs, statements)
   - **Future Plans**: General-purpose artifacts (goals, mockups, requirements)
   - **Resolution**: Need to clarify if artifact system is financial-only or general-purpose

3. **Delta System Complexity**:
   - **Future Plans**: Detailed ArtifactDelta with commit-like semantics
   - **PRD v4**: Simple field-level changes with rationale
   - **Resolution**: Commit-like delta system provides better versioning but adds complexity

### Missing from PRD v4 But in Future Plans

1. **Fragment System**:
   - Detailed fragment generation and reference parsing
   - Semantic unit decomposition
   - Inline reference resolution

2. **Multi-Artifact Operations**:
   - Single message can trigger multiple artifact updates
   - Delta relations and causation chains

3. **Advanced Query Patterns**:
   - Recursive CTEs for relation chains
   - Complex temporal queries

4. **Stack-Based Exploration**:
   - Branch creation and management
   - Conversation log lifecycle
   - Parallel exploration model

---

## Part 4: Recommendations

### Platform Architecture Strategy

MemoGarden should be implemented as a **three-layer architecture**:

**Layer 1: Platform Foundation** (Soil + Core)
- Item base type with dual timestamps
- Unified relation system (UniqueRelation + MultiRelation)
- Artifact management (ArtifactCreated + ArtifactDelta)
- Reference resolution system
- Tool call tracking
- Migration infrastructure

**Layer 2: Budget App** (Application)
- Transaction entity (extends Item)
- Recurrence entity (extends Item)
- Financial artifacts (bank statements, invoices)
- Budget-specific UI and workflows
- Agent integration for reconciliation

**Layer 3: Project System** (Application)
- Message entity with fragments (extends Item)
- ConversationLog with branching
- Design artifacts (mockups, requirements)
- Project-specific UI and workflows
- Collaborative editing features

### Implementation Strategy

**Recommended Approach: Platform-First with Gradual App Expansion**

1. **Phase 1: Platform Foundation** (Replaces current Step 3)
   - Implement Item base type in Core
   - Implement Soil storage layer
   - Implement unified relation system
   - Implement artifact versioning (ArtifactCreated + ArtifactDelta)
   - Implement migration infrastructure
   - Implement reference resolution

2. **Phase 2: Budget App Refactor** (Current Step 3 → 4)
   - Refactor Transaction to extend Item
   - Refactor Recurrence to extend Item
   - Update Budget app to use platform features
   - Continue with Flutter app development
   - Complete Budget app features

3. **Phase 3: Project System** (New steps after 6)
   - Implement Message with fragments
   - Implement ConversationLog with branching
   - Implement Frame and Stack
   - Build Project System UI
   - Implement collaborative editing

### Benefits of Platform-First Approach

1. **Shared Infrastructure**: Both apps benefit from Soil + Core
2. **Reduced Duplication**: Common features (artifacts, relations, deltas) built once
3. **Future Extensibility**: Easy to add third applications later
4. **Clean Architecture**: Clear separation of platform vs application concerns
5. **Progressive Enhancement**: Ship Budget app, then add Project System

### Next Steps

1. **Update implementation.md** to reflect platform architecture:
   - Add Step 0 (or refactor Step 3): Platform Foundation
   - Integrate schema extension system from `plan/future/schema-extension-design.md`
   - Integrate migration mechanism from `plan/future/migration-mechanism.md`
   - Integrate Soil storage from `plan/future/soil-design.md`

2. **Refactor existing work** to use platform foundations:
   - Audit current database schema for Item type compatibility
   - Plan migration path for Transaction → extends Item
   - Plan migration path for Recurrence → extends Item

3. **Create detailed plan** for Project System application (to be added after Budget app completion)

4. **Update documentation**:
   - Replace plan/prd.md with plan/memogarden_prd_v4.md as primary PRD reference
   - Update CLAUDE.md to reflect platform architecture
   - Update architecture.md to describe Soil + Core layers

---

## Appendix: Architecture Comparison

### Current PRD (Budget App Only)
- **Scope**: Single application
- **Entity Types**: 5 core types
- **Relations**: Simple table
- **Domain**: Finance only
- **Complexity**: Low-Medium
- **Time to Market**: Short

### PRD v4 (Complete Platform)
- **Scope**: Platform + 2 applications
- **Entity Types**: 15+ types with inheritance (platform foundation)
- **Relations**: Two-model system with lifecycle (platform feature)
- **Domains**: Multiple (platform supports diverse applications)
- **Complexity**: High (platform) + Medium (each app)
- **Time to Market**: Platform first, then apps progressively

### Future Plans (Platform Infrastructure)
- **Depth**: Extremely detailed technical design
- **Components**: Extension system, migration, soil storage, advanced relations
- **Status**: Ready for platform foundation implementation
- **Complexity**: High (but enables both apps)

---

**Analysis Prepared By**: Claude (Explore agents a5cb73e, a021af0, aad482e)
**Date**: 2025-12-30
**Last Updated**: 2025-12-31 (added PRD v4.1 hash-based change tracking analysis)
**Status**: Analysis complete
