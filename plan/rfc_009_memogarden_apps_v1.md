# RFC 009: MemoGarden Application Model

**Version:** 1.0  
**Status:** Draft  
**Author:** JS  
**Date:** 2026-02-04

## Summary

This RFC specifies the MemoGarden Application Model: how apps are defined, how they communicate with MemoGarden, how they support both human and agent interaction, and how they can operate in standalone mode without MemoGarden supervision.

A **MemoGarden App** is a program that presents synchronized interfaces to both human operators and AI agents, backed by shared state in MemoGarden.

## Motivation

MemoGarden's value increases with the ecosystem of apps that use it as their data substrate. However, developing such apps requires clear answers to several questions:

1. How do apps communicate with MemoGarden?
2. How do apps expose capabilities to both humans and agents?
3. How does MemoGarden launch and manage app processes?
4. Can apps function without MemoGarden for development or simple deployments?
5. What contract do apps commit to when declaring their capabilities?

This RFC answers these questions with a design that balances simplicity (minimal overhead for simple apps) with power (full MemoGarden integration for sophisticated apps).

## Core Principle

**Same operations, different modalities:**
- Humans interact via **GUI** (graphical) or **TUI** (terminal text)
- Agents interact via **AUI** (agent/tool-based)
- Both see identical state, recorded in MemoGarden

## Architecture Overview

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚              MemoGarden App                 â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                                             â”‚
â”‚  GUI â”€â”€â”€â”€â”                                  â”‚
â”‚          â”‚                                  â”‚
â”‚  TUI â”€â”€â”€â”€â”¼â”€â”€â†’ App Core Logic                â”‚
â”‚          â”‚          â”‚                       â”‚
â”‚  AUI â”€â”€â”€â”€â”˜          â”‚                       â”‚
â”‚  (toolcalls)        â–¼                       â”‚
â”‚              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”               â”‚
â”‚              â”‚ Command Port â”‚               â”‚
â”‚              â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜               â”‚
â”‚                     â”‚                       â”‚
â”‚              â”Œâ”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”               â”‚
â”‚              â”‚ Storage Port â”‚               â”‚
â”‚              â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜               â”‚
â”‚                                             â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## MemoGarden as Hub

All app commands flow through MemoGarden. This is a deliberate architectural choice:

**Benefits:**
- Centralized audit trail (command history is queryable data)
- Single authentication point
- No NÃ—N inter-app communication complexity
- Unified resource management

**Constraint:**
- Apps cannot invoke each other directly
- All cross-app coordination happens via shared MemoGarden state

## IPC Mechanism: Supervised stdin/stdout

MemoGarden launches apps as child processes and communicates via stdin/stdout using a JSON-lines protocol.

### Process Lifecycle

1. **Launch on demand:** MemoGarden spawns app process when first command arrives
2. **Keep alive:** Process remains running for subsequent commands
3. **Graceful close:** User can send explicit close command
4. **Auto-close:** MemoGarden may terminate idle apps to conserve resources
5. **Crash recovery:** MemoGarden detects crashed apps and relaunches on next command

### Message Protocol

Messages are newline-delimited JSON objects.

**MemoGarden â†’ App (stdin):**

```json
{"id":"abc123","type":"request","method":"create_event","params":{"title":"Meeting","time":"2026-02-04T09:00:00Z"}}
{"id":"def456","type":"request","method":"get_events","params":{"date":"2026-02-04"}}
{"type":"notification","event":"entity_changed","data":{"uuid":"...","type":"Event"}}
{"type":"shutdown","grace_period_ms":5000}
```

**App â†’ MemoGarden (stdout):**

```json
{"id":"abc123","type":"response","result":{"uuid":"...","title":"Meeting"}}
{"id":"def456","type":"response","error":{"code":404,"message":"Not found"}}
{"type":"subscribe","events":["entity_changed:Event","context_activated"]}
{"type":"log","level":"info","message":"Calendar sync complete"}
```

### Message Types

| Type | Direction | Purpose |
|------|-----------|---------|
| `request` | MG â†’ App | Command invocation (has `id`, expects response) |
| `response` | App â†’ MG | Command result (echoes `id`) |
| `notification` | MG â†’ App | Push event (no `id`, no response expected) |
| `subscribe` | App â†’ MG | Declare which notifications app wants |
| `shutdown` | MG â†’ App | Request graceful termination |
| `log` | App â†’ MG | Diagnostic output (forwarded to MG logs) |

### Notification Events

Apps can subscribe to push notifications:

| Event | Payload | Use Case |
|-------|---------|----------|
| `entity_changed:{type}` | `{uuid, type, change_type}` | React to external entity modifications |
| `context_activated` | `{context_id, scope}` | Operator attention shifted |
| `context_deactivated` | `{context_id}` | Operator left context |
| `operator_preference_changed` | `{key, value}` | Settings relevant to app changed |

### GUI Integration

GUI apps run their own event loop. The stdin reader runs in a background thread and posts messages to the GUI's event queue:

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                  GUI App                     â”‚
â”‚                                              â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”      â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚ stdin       â”‚      â”‚                  â”‚  â”‚
â”‚  â”‚ reader      â”‚â”€â”€â”€â”€â”€â†’â”‚  Event Queue     â”‚  â”‚
â”‚  â”‚ (thread)    â”‚      â”‚                  â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜      â”‚  â€¢ GUI events    â”‚  â”‚
â”‚                       â”‚  â€¢ MG requests   â”‚  â”‚
â”‚                       â”‚  â€¢ MG notifs     â”‚  â”‚
â”‚                       â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â”‚                                â”‚             â”‚
â”‚                       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚                       â”‚   Event Loop     â”‚  â”‚
â”‚                       â”‚   (dispatch)     â”‚  â”‚
â”‚                       â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## Standalone Mode

Apps can function without MemoGarden supervision via the Hexagonal/Ports-and-Adapters pattern.

### Two Independent Ports

| Port | Supervised Mode | Standalone Mode |
|------|-----------------|-----------------|
| **Command** | stdin/stdout from MG | GUI events, CLI args |
| **Storage** | MemoGarden API | Local SQLite, in-memory |

### Abstract MemoGarden API

Apps code against an abstract API specification. The canonical implementation uses MemoGarden as the backend, but alternatives exist for standalone operation.

**Interface (not implementation):**

```python
class MemoGardenAPI(Protocol):
    """Abstract interface - apps code against this."""
    
    # Core bundle
    def create_entity(self, type: str, state: dict) -> Entity: ...
    def get_entity(self, uuid: str) -> Optional[Entity]: ...
    def update_entity(self, uuid: str, delta: dict) -> Entity: ...
    def delete_entity(self, uuid: str) -> None: ...
    def query_entities(self, **filters) -> List[Entity]: ...
    
    # Soil bundle
    def create_fact(self, type: str, content: dict) -> Fact: ...
    def get_facts(self, entity_uuid: str) -> List[Fact]: ...
    def query_facts(self, **filters) -> List[Fact]: ...
    
    # Relations bundle
    def create_relation(self, from_uuid: str, to_uuid: str, rel_type: str) -> Relation: ...
    def get_relations(self, uuid: str, direction: str = 'outbound') -> List[Relation]: ...
    def traverse(self, start_uuid: str, **options) -> TraversalResult: ...
    
    # Semantic bundle
    def search(self, **params) -> SearchResult: ...
    def suggest(self, **params) -> List[Suggestion]: ...
    
    # Capability discovery
    def get_capabilities(self) -> dict: ...
```

**Implementations:**

| Implementation | Bundles Supported | Use Case |
|----------------|-------------------|----------|
| `MemoGardenBackend` | All | Production with full MemoGarden |
| `SQLiteBackend` | Core only | Standalone with local storage |
| `MemoryBackend` | Core only | Testing |

### Capability Tiers

Standalone backends support limited capabilities. Apps check at startup:

```python
caps = backend.get_capabilities()
if 'semantic' not in caps['bundles']:
    # Disable search UI, fall back to basic filtering
    pass
```

### What Standalone Mode Provides

- Development/debugging without MG running
- GUI-primary apps that only occasionally need agent interaction
- Gradual adoption path for existing apps
- Testing in isolation

### What Standalone Mode Loses

- Agent push commands (no stdin channel)
- Centralized audit trail
- Lifecycle management
- Cross-app state visibility

## App Profiles

Apps declare a single profile in their manifest. Each profile implies capability bundles and a contract.

### Profile Definitions

| Profile | Bundles | Example Apps |
|---------|---------|--------------|
| **Core** | Core | Contacts, inventory, simple lists |
| **Soil** | Soil | Email archive, sensor logs, event collectors |
| **Relational** | Core + Relations | Mind maps, org charts, network diagrams |
| **Factual** | Core + Soil | Budget tracker, journal, habit tracker |
| **Semantic** | Core + Soil + Relations + Semantic | Project studio, knowledge base |

### Bundle Dependencies

```
              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
              â”‚ SEMANTIC â”‚
              â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜
                   â”‚
            requires all three
         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
         â–¼         â–¼         â–¼
   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
   â”‚   SOIL   â”‚ â”‚ CORE â”‚ â”‚ RELATIONS â”‚
   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        â”‚          â–²           â”‚
   independent     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                Relations requires Core
```

### Profile Contract

Declaring a profile commits the app to:

1. **Supporting all verbs** in that profile's bundles
2. **Exposing capabilities as toolcalls** for agent interaction
3. **Surfacing relevant UI elements:**
   - Soil â†’ history/audit trail views
   - Relations â†’ graph visualization
   - Semantic â†’ search/suggest interfaces

## App Manifest

Apps declare their identity and capabilities in a manifest file.

```yaml
# memogarden-app.yaml
name: "Budget Tracker"
id: "com.example.budget"
version: "1.0.0"
author: "Example Inc"

profile: factual

description: "Track expenses and income with full audit history"

# Entry points
entry:
  supervised: "python -m budget_tracker.supervised"
  gui: "python -m budget_tracker.gui"
  cli: "python -m budget_tracker.cli"

# Toolcall definitions for agents
tools:
  - name: add_transaction
    description: "Record an expense or income"
    parameters:
      amount: { type: number, required: true }
      category: { type: string, required: true }
      description: { type: string }
      date: { type: string, format: date }
  
  - name: get_balance
    description: "Get current balance for a category or overall"
    parameters:
      category: { type: string }
      as_of: { type: string, format: date }

  - name: list_transactions
    description: "Query transactions with filters"
    parameters:
      category: { type: string }
      since: { type: string, format: date }
      until: { type: string, format: date }
      limit: { type: integer, default: 50 }

# Schemas used by this app
schemas:
  - Transaction
  - Category
  - Budget

# Permissions requested
permissions:
  - core.entities.read
  - core.entities.write
  - soil.facts.read
  - soil.facts.write
```

## Agent Discovery Flow

Agents discover and use apps through MemoGarden:

```
1. Agent receives task requiring unknown capability
2. list_apps(category="finance")       # Discover available apps
3. get_app_info("com.example.budget")  # Review capabilities and tools
4. load_app("com.example.budget")      # Load app (MG launches process)
5. add_transaction(amount=50, ...)     # Use app tools
6. unload_app("com.example.budget")    # Free resources when done
```

### Toolcall Routing

When an agent invokes a tool, MemoGarden:

1. Looks up tool â†’ app mapping
2. Ensures app process is running (launches if needed)
3. Sends request message to app's stdin
4. Waits for response on app's stdout
5. Returns result to agent

## Interface Equivalence

The same operation should be accessible via all interfaces:

| Operation | GUI | TUI | AUI (toolcall) |
|-----------|-----|-----|----------------|
| Create event | Click "New Event" button | `calendar add "Meeting" 2026-02-04 09:00` | `create_event({title: "Meeting", time: "..."})` |
| Search notes | Type in search box | `notes search "TODO"` | `search_notes({query: "TODO"})` |
| Delete item | Select â†’ click delete â†’ confirm | `notes delete <id> --confirm` | `delete_note({uuid: "...", confirm: true})` |

## SDK Structure

The MemoGarden SDK provides building blocks for app development:

```
memogarden-sdk/
  core/
    types.py           # Fact, Entity, Relation, etc.
    schema.py          # Schema definition helpers
  
  api/
    abstract.py        # MemoGardenAPI protocol
    memogarden.py      # MemoGarden backend (HTTP client)
    sqlite.py          # SQLite backend (standalone)
    memory.py          # In-memory backend (testing)
  
  adapters/
    command/
      supervised.py    # stdin/stdout command loop
      cli.py           # CLI argument parsing
      gui.py           # GUI event integration
    
  testing/
    fixtures.py        # Test helpers
    mocks.py           # Mock backends
```

### Minimal App Example

```python
from memogarden.sdk import App, tool
from memogarden.sdk.api import MemoGardenAPI

class NotesApp(App):
    profile = "factual"
    
    def __init__(self, backend: MemoGardenAPI):
        self.backend = backend
    
    @tool(description="Create a new note")
    def create_note(self, title: str, content: str) -> dict:
        entity = self.backend.create_entity("Note", {
            "title": title,
            "content": content
        })
        # Also record as fact for audit
        self.backend.create_fact("NoteCreated", {
            "note_uuid": entity.uuid,
            "title": title
        })
        return {"uuid": entity.uuid, "title": title}
    
    @tool(description="Search notes")
    def search_notes(self, query: str, limit: int = 20) -> list:
        results = self.backend.search(
            query=query,
            entity_type="Note",
            limit=limit
        )
        return [{"uuid": r.uuid, "title": r.state["title"]} for r in results.items]
```

## App Registration

Apps register with MemoGarden at install time:

```
memogarden app install ./budget-tracker/
```

This:
1. Validates manifest
2. Registers app identity and tools
3. Records app as MemoGarden entity (type: `Application`)
4. Makes app discoverable to agents via `list_apps()`

## Open Questions

1. **App distribution:** Package format? Registry? Signing?
2. **Permissions enforcement:** How granular? Per-tool? Per-entity-type?
3. **Version compatibility:** How do tool schemas evolve without breaking agents?
4. **Resource limits:** Memory, CPU, concurrent instances per app?
5. **GUI framework guidance:** Flutter recommended? Electron supported? Web-only?
6. **TUI conventions:** Standard library? Argument parsing patterns?
7. **Inter-app data access:** Can Notes read Calendar's entities directly?

## Relationship to Studios

**Studios** (from JCE Whitepaper) are coordinated workflows.
**Apps** are concrete implementations used within studios.

Example: Project Studio (workflow pattern) uses:
- Artifact Editor app (document editing)
- Calendar app (scheduling)
- Notes app (quick capture)

Studios define *patterns of collaboration*; apps provide *tools for execution*.

## References

- RFC-001 v4: Security & Operations Architecture
- RFC-002 v5: Relation Time Horizon & Fossilization
- RFC-003 v3: Context Capture Mechanism
- RFC-005 v4: API Design (capability bundles, profiles)
- RFC-006 v1: Error Handling & Diagnostics
- PRD v0.10.0: MemoGarden Personal Information System
- JCE Whitepaper v1.0: Joint Cognitive Environment

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-04 | Initial specification |

---

**Status:** Draft  
**Next Steps:**
1. Review IPC protocol details
2. Finalize manifest schema
3. Implement SDK core (abstract API, adapters)
4. Prototype reference app (Notes or Calendar)
5. Define permission model
6. Specify app packaging format

---

**END OF RFC**
