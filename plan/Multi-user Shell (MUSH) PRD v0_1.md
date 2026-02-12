Multi-user Shell — Product Requirements Document (PRD)

1. Problem Statement

Traditional terminals are hostile to agents due to blocking input, implicit state, and byte‑stream I/O

Agents cannot safely or predictably share control with humans

Goal: enable human–agent joint operation over existing CLI programs, without modifying those programs



---

2. Product Shape

The system is a PTY daemon with multiple frontends

The daemon exclusively owns all PTYs and session state

Frontends include:

Interactive terminal UI for the operator

Agent access via MCP toolcalls

Future replay / audit viewers


All representations derive from the same authoritative session state



---

3. Goals & Non‑Goals

Goals

Support common interactive CLI workflows

Humans and agents see identical output and session state

Explicit single‑controller model (human or agent)

Works with existing Unix programs via PTY

Maintain high development velocity


Non‑Goals

Perfect compatibility with all legacy or pathological TUI programs

Replacing shells, editors, multiplexers, or debuggers

Competing as a power‑user shell environment

Full semantic understanding of arbitrary CLI programs

Detecting or judging agent intent or correctness



---

4. Explicit Relaxation: Program Blacklisting

The terminal may blacklist programs that violate shared‑control or observability assumptions

Blacklisting is behavior‑based, not name‑based

Blacklisted programs:

Run in human‑only passthrough mode, or

Are explicitly unsupported


Priority is simplicity, correctness, and development velocity, not maximal compatibility


Blacklisting Criteria

Hard (immediate blacklist):

Reads directly from /dev/tty or bypasses the PTY

Spawns or manages its own PTY tree

Assumes exclusive, uninterrupted terminal control

Uses non‑reversible or opaque termios state transitions


Soft (escalates to blacklist):

Aggressive full‑screen redraws with raw input

Non‑deterministic or timing‑sensitive I/O behavior

Undefined or hostile ANSI escape usage

Unbounded interactive loops without detectable prompts

Excessive output frequency or memory footprint


Policy Constraints:

No program‑specific plugins or deep semantic adapters

Blacklist triggers always alert the operator

Overrides require explicit operator acknowledgment



---

5. Target Users

Operators using AI copilots in the terminal

Developers running interactive build, test, and deployment tools

Ops / infra workflows with human‑in‑the‑loop automation



---

6. Core Principles

Terminal is a session controller, not a byte pipe

Input intent is inferred, not declared by programs

Conservative inference beats clever automation

All control transitions are explicit, visible, and logged

Safety and traceability take precedence over convenience



---

7. System Architecture

PTY master owned by the daemon

Session abstraction per process tree

Human controller

Agent controller

Control arbiter enforcing a single active controller

Observation layer producing multiple representations



---

8. Input Handling

Structured input events:

Keystrokes

Paste

Signals (SIGINT, SIGTERM, etc.)

Resize events


Unified input model for human and agent

Hard control lock during sensitive or ambiguous modes



---

9. Input Intent Inference

Signals used (no program changes):

termios mode changes (canonical/raw, echo on/off)

stdin read size and cadence

ANSI escape patterns (alternate screen, cursor control)


Inferred modes:

Line input

Secret input (password)

Single‑key input

Full interactive control

Non‑interactive execution


Inference failures always degrade safely.


---

10. Output Handling

PTY output capture

ANSI parsing (lossy acceptable)

Normalized output frames

Identical rendering for human and agent

Raw PTY streams are not exposed to agents by default



---

11. Control Arbitration & Consent

Only one controller may inject input at any time

The operator is the ultimate authority


Operating Modes

Observe / Approve: agent proposes actions; operator edits or approves

Autonomous (Bounded): agent may act within pre‑approved capability bounds


Agents may never:

Change operating mode

Override blacklists

Escalate privileges



---

12. Session State Machine (Conceptual)

States:

Human‑Active: human has exclusive control

Agent‑Active: agent has exclusive control

Observe‑Only: no input injection allowed

Passthrough: terminal defers entirely to human (blacklisted programs)


Transitions:

Manual handoff by operator

Agent request with operator approval

Automatic downgrade on rule violation or inference failure


All transitions are visible and logged.


---

13. Failure & Degradation Policy

On failure, the session halts deterministically

Failure is reported to the operator

Best‑effort unwind is attempted where safe

No agent action may occur until the operator explicitly resumes

When uncertain, the system fails closed to Observe‑Only or Passthrough



---

14. Agent Interface

Agents interact exclusively via toolcalls

Session state and output are exposed through a Letta‑compatible memory block

Memory blocks provide:

Structured output snapshots

Windowed text views

Explicit event and state transitions


This keeps agent context bounded, predictable, and auditable



---

15. Visibility Guarantees

The operator always has visibility into:

Current controller

Inferred input mode

Operating mode

Blacklist status

Agent‑declared intent (advisory only)

Source of the last action (human / agent / system)



---

16. Logging, Replay, and Audit

All input events, actions, signals, and output are logged

Logs may be truncated or compacted post‑session

Replay supports reconstruction of actions and stated intent

The system does not attempt to reconstruct internal agent reasoning



---

17. Security & Secrets

In scope:

Secrets required for terminal operation (daemon auth, session tokens, MCP credentials)


Out of scope:

Agent‑internal secrets (LLM API keys, agent memory stores)

Environment secrets within the PTY (env vars, SSH keys)


Environment mutations may be observable without revealing secret values.


---

18. Performance Envelope

Human‑perceived latency must remain acceptable for interactive use

Total memory footprint < 100MB (daemon + active sessions)

Maximum of 10 concurrent sessions (MVP)



---

19. MVP Scope

Single daemon instance

Terminal UI frontend

MCP agent frontend

Single agent per session

Shell and common CLI tools

Manual control handoff



---

20. Explicit Out‑of‑Scope

Competing with tmux / screen

Competing with vim / emacs

Becoming a universal automation framework

Supporting all ANSI or TUI edge cases

Automated detection of agent misbehavior



---

21. Success Criteria

The system is successful if:

No action occurs without being attributable, observable, and replayable

Operators always know who acted and why an action was proposed

Agent mistakes are fully traceable

Blacklist decisions are explainable and operator‑controlled

Failures halt sessions cleanly and visibly



---

22. Survey of Existing Projects (Reference)

Termitty

Agent‑oriented terminal automation

https://github.com/termitty/termitty


Warp Terminal

AI‑assisted modern terminal (proprietary)

https://www.warp.dev


terminalcp

Structured automation for interactive CLIs

https://github.com/badlogic/terminalcp


PTY‑MCP Servers

PTY exposure via MCP

https://github.com/phoityne/pty-mcp-server


CLI Agent Tools

TermAI: https://github.com/kyco/termai

Copilot CLI (proprietary)

Gemini CLI (proprietary)