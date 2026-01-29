# Joint Cognitive Environment (JCE) â€” Design Whitepaper

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** 2025-01-21  
**Supersedes:** AIAS Project Brief (2024-12-09)

---

## 1. Overview

### 1.1 Purpose

This document specifies the Joint Cognitive Environment (JCE), the architectural model for building applications on the MemoGarden substrate. JCE defines how participants (humans and agents) collaborate through shared tools, mutual visibility, and a common data layer.

**Internal name:** Joint Cognitive Environment (JCE)  
**Public name:** Personal System (PS)

The internal name guides implementation decisions; the public name communicates user value. Contributors should ask "does this serve the Personal System user" to determine *whether* to build something, and "how would this work in a Joint Cognitive Environment" to determine *how* to build it.

### 1.2 Core Thesis

The environment, not the participants, is the locus of intelligence. Participants contribute different capabilities; the environment enables their synthesis.

A JCE is a workspace where two participants (the **dyad**) share tools, observe each other's work, and coordinate through a common data substrate. The environment amplifies cognition regardless of participant typeâ€”human-human, human-agent, agent-agent.

### 1.3 Relationship to MemoGarden

MemoGarden is the **data substrate**; JCE is the **interaction model**.

| Layer | Responsibility | Specified In |
|-------|----------------|--------------|
| Substrate | Persistence, audit trail, fossilization, relations | PRD, RFCs |
| Environment | Utilities, studios, coordination, attention | This document |
| Execution | Agent inference, memory blocks, tool dispatch | Letta/external |

JCE sits between substrate and execution. It defines *what participants can do* without specifying *how agents think*.

---

## 2. The Dyadic Model

### 2.1 Why Dyads

JCE is optimized for **two participants**. More than two is supported but not optimized.

This constraint enables:

| Property | Benefit |
|----------|---------|
| Simple coordination | No consensus protocols, voting, or quorum |
| Clear attention | Unambiguous "what is my partner looking at" |
| Natural turns | Conversation-like flow without scheduling |
| Reduced fragmentation | Two contexts to reconcile, not N |
| Mutual modeling | Each participant can maintain a model of the other |

The dyad is the fundamental unit. A system supporting three participants is two overlapping dyads, not a triad.

### 2.2 Participant Types

| Type | Characteristics | Typical Role |
|------|-----------------|--------------|
| **Operator** | Human, sovereign over data, sets policy | Direction, judgment, approval |
| **Agent** | LLM-based, bounded context, tool-mediated | Execution, search, synthesis |
| **Service** | Non-LLM automated process | Ingestion, monitoring, maintenance |

### 2.3 Dyad Configurations

| Configuration | Use Case |
|---------------|----------|
| Operator + Agent | Primary case. Collaborative work with AI assistance. |
| Operator + Operator | Pair work. Shared MemoGarden instance. |
| Agent + Agent | Delegated subtask. One agent coordinates another. |
| Operator + Service | Background processing. Service acts on policy. |

The Operator + Agent configuration is the design target. Other configurations should work but need not be equally polished.

### 2.4 Participant Symmetry

Both participants in a dyad:

- Use the same tools (shell commands, editor operations)
- Leave the same traces (deltas, tool calls, views)
- Can observe each other's attention (ContextFrame visibility)
- Can initiate coordination primitives (handover, fork, summon)

Asymmetry exists in **capability** (agents can't see images, humans can't search embeddings at scale) and **authority** (operator sets policy, agent operates within it), not in **interface**.

---

## 3. Architectural Stack

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Studios                                                        â”‚
â”‚  Complex coordinated toolsets for specific workflows            â”‚
â”‚  (Project, Data, Research, Triage, ...)                         â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  Utilities                                                      â”‚
â”‚  Core interaction primitives, multi-user by default             â”‚
â”‚  (Shell, Artifact Editor, Conversations, Timeline Browser, ...) â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  MemoGarden Substrate                                           â”‚
â”‚  Data layer: Soil, Core, Relations, Fossilization               â”‚
â”‚  (PRD v0.6.0, RFC-001, RFC-002, RFC-003)                        â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

**Layering principle:** Each layer only talks to the layer below. Studios compose utilities; utilities operate on substrate.

### 3.1 What the Substrate Provides

| Capability | Mechanism | Participant Benefit |
|------------|-----------|---------------------|
| Shared ground truth | Soil (immutable Items) | No disagreement about what happened |
| Evolving beliefs | Core (mutable state) | Adaptation without losing history |
| Attention visibility | View-stream, ContextFrame | Know what partner is examining |
| Causal tracing | System relations (triggers) | Understand why things happened |
| Natural forgetting | Time horizon decay | Bounded cognitive load |
| Structural memory | Artifacts, Entities | Persistent work products |

**Key property:** All participant actions leave traces (deltas, tool calls, views). The substrate is the shared memory of the dyad.

---

## 4. Utilities

Utilities are primitive tools that operate directly on the substrate. They are **multi-user by default**â€”both participants can use them simultaneously, and each can observe the other's usage.

### 4.1 Shell

Command-line interface to MemoGarden operations.

**Capabilities:**
- Query Items, relations, artifacts
- Execute tools (same tool set available to agents)
- Inspect view-streams and context frames
- Trigger fossilization sweeps, integrity checks
- Pipe-style composition of operations
- Script automation

**Dyadic features:**
- See partner's recent commands
- Replay partner's session
- Shared command history with attribution

**Design note:** The shell exposes the same operations available through other utilities. It is the canonical interface; GUIs are views onto shell semantics.

### 4.2 Artifact Editor

Collaborative document editing with MemoGarden semantics.

**Capabilities:**
- Line-numbered content (enables precise references)
- Delta-based versioning (git commit semantics)
- Inline references to other artifacts, items, fragments
- Context capture on edit (what was in focus when change made)
- Side-by-side diff against any commit
- Branch/merge for parallel editing

**Dyadic features:**
- Live cursor/selection sharing
- Propose-accept workflow for changes
- Annotation threads anchored to line ranges
- "Show me what you're editing"

**Output:** Artifacts stored in Core, with ArtifactDeltas in Soil.

### 4.3 Conversation Groups

Threaded discussions anchored to the branch/stack model.

**Capabilities:**
- ConversationLogs as containers
- Branch from any point
- Collapse with summary
- Messages contain Fragments (semantic units)
- System relations link conversations to artifacts they reference

**Dyadic features:**
- Parallel branches (user explores one path, agent explores another)
- Merge learnings back to main
- Shared vs. private branches (future: permission model)

**Output:** ConversationLogs in Core, Messages as Items in Soil.

### 4.4 Timeline Browser

Navigate and inspect Soil/Core contents.

**Capabilities:**
- Filter Items by type, participant, time range
- Trace trigger chains (forward: what did this cause; backward: what caused this)
- **Object viewer:** Inspect any Item, Entity, Artifact, Relation in detail
- **Entity editor:** Edit mutable Entities in Core (creates delta in Soil)
- Resurrect fossilized items
- Inspect fidelity states (full, summary, stub, tombstone)
- View relation graph for selected object

**Dyadic features:**
- Shared bookmarks
- "Show me what you're looking at"
- Partner sees your current selection
- Synchronized navigation mode

**Design note:** Timeline Browser is the general-purpose inspector/editor. The shell provides command-line access to the same operations.

### 4.5 Relation Inspector

Visualize and manage the relation graph.

**Capabilities:**
- View system relations (structural facts)
- View/edit user relations (engagement signals with time horizons)
- Derived views: co-access patterns from delta.context analysis
- Fossilization candidates (relations approaching horizon)
- Create explicit links between items

**Dyadic features:**
- Partner can see your explicit links
- Discuss why something matters (link to conversation)
- Shared relation queries

---

## 5. Studios

Studios are coordinated toolsets for complex workflows. They compose utilities and add workflow-specific affordances.

### 5.1 Project Studio

Artifact-centric collaboration on structured work products.

**Primary use cases:**
- Document drafting and revision
- Code development
- Design specification
- Any structured creative work

**Composed from:**
- Artifact Editor (primary surface)
- Conversation Group (scoped to project)
- Timeline Browser (project history)
- File import/export (external format interop)

**Workflow patterns:**
- Draft â†’ Review â†’ Commit
- Branch for exploration â†’ Collapse with summary
- Agent proposes changes â†’ Operator accepts/rejects
- Parallel editing with merge

**Output:** Artifacts exportable to standard formats (Markdown, PDF, code files, DOCX).

### 5.2 Data Studio

Analysis and visualization of structured data.

**Primary use cases:**
- Exploratory data analysis
- Dashboard creation
- Report generation with embedded queries

**Composed from:**
- Query builder (SQL-like over Items/Entities)
- Chart/graph renderer
- Notebook interface (interleaved prose + queries + visualizations)
- Artifact Editor (for narrative sections)

**Workflow patterns:**
- Exploratory analysis (agent suggests queries based on context)
- Dashboard creation (saved query sets with refresh)
- Annotation (findings become Items with relations to source data)
- Export snapshots for sharing

**Output:** Notebooks (artifacts), datasets (entities), visualizations (artifacts).

### 5.3 Research Studio

Long-form investigation with source management.

**Primary use cases:**
- Literature review
- Competitive analysis
- Due diligence
- Any work requiring source synthesis

**Composed from:**
- Source ingestion (PDF, web pages â†’ Items/Artifacts)
- Citation tracking (system relations: cites, derives_from)
- Artifact Editor (synthesis workspace with citation autocomplete)
- Timeline Browser (source navigation)

**Workflow patterns:**
- Collect sources â†’ Extract claims â†’ Synthesize argument
- Agent identifies relevant passages â†’ Operator evaluates
- Time horizon on sources reflects ongoing relevance
- Bibliography generation from relation graph

**Output:** Research artifacts with citation provenance; exportable bibliographies.

### 5.4 Triage Studio

Processing incoming streams (email, messages, feeds).

**Primary use cases:**
- Email processing
- Message queue management
- Feed monitoring
- Any high-volume incoming stream

**Composed from:**
- Stream viewer (chronological or priority-sorted)
- Quick actions (archive, defer, escalate, link to existing entity)
- Bulk operations
- Filter/rule builder
- Conversation Group (for items needing discussion)

**Workflow patterns:**
- Agent pre-classifies â†’ Operator confirms
- Defer = low initial time horizon; surface later based on triggers
- Escalate = create user relation to high-significance entity
- Batch processing with undo

**Output:** Processed items with relations; task items for follow-up.

### 5.5 Future Studios (Not Specified)

- **Communication Studio:** Draft and send messages across channels
- **Calendar Studio:** Time-based planning and scheduling
- **Learning Studio:** Spaced repetition, knowledge consolidation
- **Media Studio:** Image, audio, video organization and annotation

Studios share a common pattern: compose utilities, add workflow-specific affordances, produce artifacts that other programs can read.

---

## 6. Coordination Primitives

How participants transfer attention and control within the environment.

### 6.1 Handover

One participant transfers active work to another.

```
Operator working on artifact A
  â†’ Handover("finish the error handling section")
  â†’ Agent's ContextFrame inherits Operator's current state
  â†’ Agent works; Operator can observe or switch to other work
  â†’ Agent signals completion
  â†’ Operator reviews delta, accepts or continues
```

**Properties:**
- Explicit transfer of responsibility
- Context inheritance (recipient starts with sender's focus)
- Completion signal required
- Non-blocking (sender can do other things)

### 6.2 Fork

Both participants explore in parallel.

```
Discussion reaches decision point with options A and B
  â†’ Fork: Agent explores Option A in branch_1
          Operator explores Option B in branch_2
  â†’ Each works in separate ConversationLog branch
  â†’ Reconvene: Compare findings
  â†’ Collapse one, merge both, or continue exploring
```

**Properties:**
- Creates parallel branches
- No implicit coordination during exploration
- Explicit reconvene required
- Supports speculative work

### 6.3 Observe

One participant watches the other work.

```
Agent performing complex multi-step retrieval
  â†’ Operator enables Follow mode
  â†’ Operator's view tracks Agent's current attention in real-time
  â†’ Operator can: interrupt, redirect, annotate, or let continue
  â†’ Follow mode ends on explicit exit or Operator action
```

**Properties:**
- One-directional attention sync
- Observer is passive unless they act
- Action by observer ends passive observation
- Useful for supervision, learning, debugging

### 6.4 Summon

Pull partner's attention to current focus.

```
Operator finds relevant passage while Agent is working elsewhere
  â†’ Summon("look at this")
  â†’ Agent's ContextFrame updated to include Operator's current focus
  â†’ Agent acknowledges and responds to implicit context
  â†’ Agent decides whether to context-switch or defer
```

**Properties:**
- Attention request, not command
- Recipient decides response priority
- Adds to recipient's context, doesn't replace
- Supports "FYI" and "urgent" variants

### 6.5 Yield

Return control to partner or to idle.

```
Agent completes current task
  â†’ Yield(completion_summary)
  â†’ Control returns to Operator (if Handover) or to idle (if self-initiated)
  â†’ Summary added to shared context
```

**Properties:**
- Clean completion signal
- Summary enables async review
- Required after Handover; optional otherwise

---

## 7. Attention Model

How the environment tracks and shares participant attention.

### 7.1 View-Stream

Ephemeral record of attention events.

- Ringbuffer structure (~24hr retention or N entries)
- Browsing history semantics (monotonic, chronological)
- Records which containers each participant viewed
- No permanence expectation

**Use:** Operational awareness. "What has my partner been looking at recently?"

### 7.2 ContextFrame

Current working attention state.

- LRU set of N unique containers (e.g., 20)
- Single participant per frame
- Access promotes container to front
- Bounded size prevents unbounded growth

**Use:** Snapshot of focus. "What is my partner attending to right now?"

### 7.3 Context Capture

Meaningful attention is captured at mutation time.

- `ArtifactDelta.context` field contains ContextFrame snapshot
- Records what was in focus when change was made
- Enables retrospective co-access analysis
- No intermediate view-to-relation pipeline

**Use:** Understanding decisions. "What was I/my partner looking at when this change was made?"

### 7.4 Mutual Visibility

Each participant can inspect the other's:

| What | How | Latency |
|------|-----|---------|
| Current focus | ContextFrame | Real-time |
| Recent attention | View-stream | Near real-time |
| Past focus at decision points | delta.context | Historical |

This visibility is **default on**. Participants operate in a shared space, not private silos.

---

## 8. Policy Layer

Operator-configurable constraints on environment behavior. Policies are stored as artifacts in MemoGarden (self-describing system).

### 8.1 Policy Areas

| Area | Examples |
|------|----------|
| **Agent budget** | Max tokens/hour, max tool calls/task, behavior on exhaustion (block, notify, allow overflow) |
| **Fossilization** | Sweep frequency, summary method (extractive, LLM), storage pressure thresholds, target fidelity |
| **Privacy** | What data agents can access, export restrictions, retention limits |
| **Notification** | When to interrupt operator, urgency classification, channels |
| **Defaults** | Initial time horizon for new relations, default fidelity targets, auto-link rules |
| **Coordination** | Handover approval requirements, auto-yield timeout, summon priority handling |

### 8.2 Policy Hierarchy

```
System defaults (MemoGarden ships with these)
  â†“ overridden by
Deployment profile (Device/System/Personal from RFC-001)
  â†“ overridden by
Operator preferences (stored in Core)
  â†“ overridden by
Session overrides (temporary, not persisted)
```

### 8.3 Policy as Artifact

Policies are artifacts with a defined schema. This means:

- Version controlled (delta history)
- Editable with Artifact Editor
- Diffable (compare policy versions)
- Exportable (share policy configurations)
- Agent-readable (agents can query current policy)

---

## 9. Integration Points

### 9.1 Letta (Execution Layer)

JCE does not specify agent internals. Letta provides:

- Memory block management (projections into MemoGarden)
- Tool dispatch and function calling
- Context window management
- Agent state persistence (.af files)

**Interface contract:** Agents access MemoGarden through tools. Tools are specified in JCE; tool execution is Letta's responsibility.

**Memory block binding:** Agent registration specifies how MemoGarden entities project into Letta memory blocks. This is a KIV item requiring separate specification.

### 9.2 External Formats

JCE produces artifacts; artifacts can be exported.

| Internal | Export Formats |
|----------|----------------|
| Text artifact | Markdown, TXT, PDF, DOCX |
| Code artifact | Source files with standard extensions |
| Data artifact | CSV, JSON, SQLite |
| Notebook artifact | Jupyter (.ipynb), Markdown |
| Conversation artifact | Markdown, JSON transcript |

Import follows the reverse path. External files become artifacts or items with appropriate relations.

### 9.3 External Services

Studios may integrate external services:

- Email (Gmail API for Triage Studio)
- Calendar (for future Calendar Studio)
- Web (fetch, search for Research Studio)
- Version control (Git for Project Studio)

External service integration is mediated by tools. Services do not access MemoGarden directly.

---

## 10. Security Model

JCE inherits security architecture from RFC-001.

### 10.1 Key Principles

- **All agent actions go through tools** â€” no direct database/file access
- **All tool calls logged to Soil** â€” complete audit trail
- **API key scoping** â€” agents operate within granted scopes
- **Operator sovereignty** â€” operator can revoke, inspect, constrain

### 10.2 Dyadic Trust

Within a dyad, participants have high mutual visibility. This is a feature, not a bug. The dyad is a trusted collaboration unit.

Cross-dyad isolation (multi-operator in System profile) is enforced at the substrate level. One operator's JCE cannot see another's data.

### 10.3 Agent Boundaries

Agents cannot:

- Execute shell commands outside tool framework
- Access databases directly
- Modify files outside MemoGarden
- Exceed granted scopes
- Operate without audit trail

Agents can:

- Use any tool within their granted scopes
- Access any MemoGarden data within operator's namespace
- Initiate coordination primitives
- Propose changes (subject to approval workflow if configured)

---

## 11. Relation to Existing Documents

| Document | Relationship |
|----------|--------------|
| **PRD v0.6.0** | Substrate specification. JCE defines interaction model atop PRD's data model. |
| **RFC-001 v4** | Security and operations. JCE inherits deployment profiles, encryption options, API model. |
| **RFC-002 v5** | Time horizon mechanism. JCE uses for attention relevance and fossilization. |
| **RFC-003 v2** | Context capture. JCE utilities generate views; context captured per RFC-003. |
| **AIAS Brief** | **Superseded.** Archive as historical context. JCE replaces AIAS as the interaction model. |
| **MemGPT Paper** | Execution model reference. Letta implements agent-side; JCE implements environment-side. |
| **Time Horizon Whitepaper** | Cognitive science foundation. JCE inherits "natural forgetting" principle. |

---

## 12. Migration from AIAS

### 12.1 Concepts Retained

| AIAS Concept | JCE Equivalent |
|--------------|----------------|
| Memory blocks | Projections into MemoGarden (not authoritative) |
| Task queue | Tools + system relations (triggers) |
| Sessions | Utilities and studios |
| KIV Service | Time horizon on user relations |
| Event-driven control flow | Tool calls + coordination primitives |
| Background monitoring | Services (participant type) |

### 12.2 Concepts Changed

| AIAS Concept | Change |
|--------------|--------|
| Memory blocks as authoritative | Now projections only; MemoGarden is authoritative |
| PostgreSQL | SQLite (fits Raspberry Pi constraint) |
| Single-user with AI | Dyadic model; human-human also supported |
| AI-centric naming | Environment-centric; AI is one participant type |

### 12.3 Concepts Deferred

| AIAS Concept | Status |
|--------------|--------|
| Checkpoint/unwind stack | Not yet specified; may emerge from studio patterns |
| Daemon classifier | Future work; relates to Triage Studio |
| Proactive suggestions | Future work; policy-driven |
| Screenshot capture / OS telemetry | Future work; context awareness features |

---

## 13. Open Questions

### 13.1 Architectural

1. **Studio extensibility:** Fixed set of studios, or plugin architecture for custom studios?
2. **Cross-dyad sharing:** Can outputs from one JCE instance be imported to another? (Relates to satellite profile, multi-device sync.)
3. **Session persistence:** Does a "studio session" have state beyond MemoGarden? Or is all state in substrate?

### 13.2 Coordination

4. **Conflict resolution:** When optimistic locking fails, what's the UX? Conversation? Automatic merge? Branch?
5. **Handover granularity:** Can you hand over a sub-task while retaining the parent task?
6. **Summon priority:** How does recipient know if summon is FYI vs. urgent?

### 13.3 Capability

7. **Asymmetric capabilities:** How do studios adapt when one participant lacks capabilities (e.g., agent can't view images)?
8. **Offline operation:** How do coordination primitives work when one participant is unavailable?
9. **Service participation:** Can services use coordination primitives, or only operators and agents?

### 13.4 Implementation

10. **Shell command schema:** What's the canonical command set?
11. **Tool-utility mapping:** Which tools belong to which utilities?
12. **Memory block binding:** How does agent registration specify MemoGarden â†’ Letta projection?

---

## 14. Non-Goals

This document does not specify:

- Agent architecture or prompt engineering (Letta's domain)
- LLM selection or fine-tuning
- Specific UI implementation (widget layout, color schemes)
- Mobile/satellite deployment details (see RFC-001 for profiles)
- Multi-operator (>2) coordination protocols
- Pricing, packaging, or distribution

---

## 15. Glossary

| Term | Definition |
|------|------------|
| **Artifact** | Mutable document in Core; versioned via deltas in Soil |
| **Context capture** | Snapshot of ContextFrame at mutation time |
| **ContextFrame** | LRU set of containers representing current attention |
| **Core** | Mutable storage layer (beliefs, relations, artifacts) |
| **Dyad** | Two-participant unit; fundamental collaboration structure |
| **Fork** | Coordination primitive; parallel exploration |
| **Handover** | Coordination primitive; transfer of active work |
| **Item** | Immutable record in Soil (base type for Messages, Deltas, etc.) |
| **JCE** | Joint Cognitive Environment; internal name for interaction model |
| **Observe** | Coordination primitive; watch partner work |
| **Operator** | Human participant; sovereign over data |
| **Personal System** | Public name for the product |
| **Soil** | Immutable storage layer (ground truth timeline) |
| **Studio** | Coordinated toolset for complex workflows |
| **Substrate** | MemoGarden data layer |
| **Summon** | Coordination primitive; pull partner's attention |
| **Utility** | Primitive tool operating on substrate |
| **View-stream** | Ephemeral attention history |
| **Yield** | Coordination primitive; return control |

---

## 16. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-21 | Initial version. Supersedes AIAS Project Brief. |

---

## 17. Next Steps

1. **Validate utility set** against concrete user workflows
2. **Define shell command schema** â€” canonical command set and syntax
3. **Specify coordination protocols** in sufficient detail for implementation
4. **Prototype Project Studio** as first studio implementation
5. **Specify memory block binding** â€” how agent registration works
6. **Determine policy artifact schema** â€” format for stored policies

---

**END OF DOCUMENT**
