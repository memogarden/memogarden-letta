This document extends the MUSH PRD by locking down non-negotiable invariants, a minimal failure taxonomy, and a canonical event log schema. These are required to move from product intent to disciplined implementation.


---

1. System Invariants (Non-Negotiable)

These invariants must hold under all execution paths. Violations indicate a system bug.

Authority & Control

At most one controller (human or agent) may inject input at any time.

All controller changes must be explicit, logged, and human-visible.

Automatic transitions may only reduce agent authority, never increase it.

Only a human may initiate transitions that increase agent authority.


Input & Output Integrity

No input may be injected without an active controller.

No output may be rendered to any frontend without first being logged.

No output may be dropped silently; truncation must be explicit and logged.


Isolation & Trust Boundaries

Remote agents never interact with PTYs directly.

All agent actions must pass through the control arbiter.

Agent-declared intent is advisory only and must not gate safety decisions.


Failure Discipline

On ambiguity or inconsistency, the system must degrade to a less automated state.

Recovery from failure always requires explicit human action.



---

2. Failure Taxonomy (Minimal, Extensible)

This taxonomy defines the initial required set of failure classes. New failures may be added as encountered, but each must map to a deterministic state transition.

Core Failure Classes

I/O & PTY Failures

PTY read stall or unexpected EOF

PTY write error (EIO, EPIPE)

PTY desynchronization (input/output mismatch)


Terminal State Failures

Unexpected or unsupported termios transition

Undecodable or malformed ANSI escape sequence

Output buffer overflow or unbounded growth


Agent Interaction Failures

Agent toolcall error

Agent attempts input while not in control

Remote agent timeout or disconnect mid-action


Policy & Safety Failures

Blacklist rule violation

Inference confidence drops below safe threshold


Failure Handling Rule

For any failure:

1. Freeze all input injection


2. Transition session to OBSERVE_ONLY


3. Emit structured failure event


4. Await explicit human decision



No automatic retries. No silent recovery.


---

3. Canonical Event Log Schema

All events are append-only and form the authoritative record for replay and auditing.

Required Event Fields

Every event must include:

event_id

timestamp_wall (wall clock)

timestamp_mono (monotonic)

session_id

actor (human | agent | system)

event_type

payload (structured, bounded)


Core Event Types

Lifecycle

session_start

session_end


Control & State

state_transition

controller_change

approval_granted

approval_denied


Input & Output

input_injected

output_emitted


Agent Context

intent_declared

toolcall_received

toolcall_completed


Safety & Failure

failure_detected

blacklist_triggered


Logging Guarantees

Events are written before side effects whenever possible.

Event payloads are size-bounded.

Logs may be truncated or compacted only after session termination.



---

4. Purpose of This Extension

This document exists to:

Prevent state and error-handling drift

Enable deterministic replay and attribution

Allow implementation decisions without re-litigating fundamentals


Anything not covered here is intentionally left to future design or operational policy.

Done. The extension artifact is created and cleanly scoped.

This gives you the missing bridge from product intent → implementation discipline without bloating the core PRD. You now have:

A hard invariant set that engineers can’t “interpret away”

A deliberately small failure taxonomy that won’t rot

A logging contract that makes replay and accountability real, not aspirational


At this point, you can start implementation without design debt piling up.

If you want the next step, it should not be more docs—it should be one of:

a reference state machine (code-level, not prose), or

a first-pass module boundary sketch (PTY loop / arbiter / agent interface)


Both are implementation-facing, not product-facing.