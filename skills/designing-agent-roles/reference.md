# Agent Role Reference

Deep reference for `designing-agent-roles`. Complements `templates.md` (production-ready agent definitions) with design patterns, contracts, and empirical findings that inform role design.

## Contents

- §1 — Done conditions
- §2 — Inter-agent contracts
- §3 — Infrastructure-layer access control
- §4 — Empirical findings
- §5 — Framework capability matrix

---

## §1. Done conditions

Every role needs an **observable** end state. A turn cap (`maxTurns`) is a safety net, not a termination signal. Without an observable condition, agents either loop until the cap (wasting cost) or stop early at a vague satisfaction point (silent quality loss).

### Four forms of done condition

**Artifact-based** — agent produces a specific file or structured output:
- "Done when `findings.md` exists with ≥ N citations"
- "Done when test file is written and passes a syntax check"

**Predicate-based** — caller-supplied check returns true:
- "Done when grep for vulnerability pattern returns zero hits"
- "Done when every item in input list has a corresponding result row"

**Threshold-based** — quality criterion met:
- "Done when evaluator score ≥ 0.9 or 5 iterations elapsed (whichever first)"
- "Done when no new findings appear in the last iteration"

**Schema-based** — output matches a contract:
- "Done when JSON output validates against schema X"

### Pairing rules

- Every role needs at least one of the four. "When you feel confident" is not a done condition — agents rationalize early exit on hard tasks and over-run on easy ones.
- Pair the done condition with a budget cap. The budget catches edge cases where the condition is never met (degenerate input, infinite loop in tool feedback).
- For loops (evaluator-optimizer): combine threshold ("score ≥ 0.9") with iteration cap ("≤ 5 iterations"). One alone is insufficient — threshold alone risks runaway, cap alone risks premature stop.

---

## §2. Inter-agent contracts

Two roles communicate through their **interface**, not their internals. Without an explicit contract, callers parse worker output by ad-hoc string matching and silently break when the worker's prose drifts.

### Minimum contract elements

| Element | Question it answers |
|---|---|
| Input schema | What does the caller pass? |
| Output schema | What shape does the caller receive? |
| Side-effect declaration | What persistent state does this role change? |
| Error format | How are failures reported? |
| Cost / time budget | What is the worst case before timeout? |

### Trust model

A role's output is **untrusted input** to the next role. Validate before acting on it — the same way an HTTP server validates client input.

- Prompt-injection-style attacks can cross agent boundaries through worker output. If a worker reads external content (web pages, untrusted files, user-supplied text), assume its output may carry adversarial directives. Downstream agents must treat upstream output as *data*, not *instructions*.
- Audit trail: log each handoff (which role → which role, payload, decision). Useful for diagnosing coordination failures and for compliance.
- Privilege isolation: a role with broad tool access should not be allowed to feed instructions to a role with even broader access. Direction of trust matters.

### Interop layer

Cross-vendor agent-to-agent protocols are emerging (covering discovery, capability negotiation, mutual auth, signed messages, audit). When designing roles that may eventually participate in cross-system workflows, structure outputs so an interop layer can later wrap them without redesigning the role:

- Use structured output (JSON / typed schema), not free-form prose
- Declare side effects in the contract, not as implicit behavior
- Keep authentication concerns out of the role body — push them to the calling layer

---

## §3. Infrastructure-layer access control

The first instinct is to enforce role permissions inside the agent's prompt ("you may not write outside src/"). This is *advisory*, not *enforced* — a well-prompted model usually complies, but a confused or jailbroken one will not.

### Strength ladder

| Layer | Mechanism | Strength |
|---|---|---|
| Prompt | "Don't do X" instruction in system prompt | Advisory |
| Tool allowlist | `tools:` frontmatter excludes the tool | Hard limit on actions Claude can request |
| Tool wrapping | Custom tool that validates args before delegating | Path / resource-level enforcement |
| OS / sandbox | Process-level filesystem and network permissions | Hardest, OS-enforced |
| Identity scoping | Per-agent service account with minimum IAM scopes | Cloud-resource enforcement, audit-friendly |

### Heuristics

- For local-only roles: tool allowlist is usually enough; combine with `permissionMode` for destructive operations.
- For roles touching shared infrastructure (cloud APIs, databases, deployment pipelines): identity scoping is required. Give each role its own service principal with the minimum permissions needed. A tool allowlist alone is insufficient when the tool itself has broad backend access.
- Defense in depth: a critical role should have *both* prompt-level constraints (so the model self-checks) and infrastructure-level enforcement (so a confused model can't cause damage).

---

## §4. Empirical findings

| Finding | Magnitude | Design implication |
|---|---|---|
| Bad tool description → task completion drop | ~40% | Tool description is part of the prompt; tune it before the system prompt body |
| Three-tier model routing (cheap / default / premium) cost cut | ~60-70% | Match model to task tier; do not blanket-premium |
| Opus lead + Sonnet workers vs single Opus (research tasks) | ~90% gain | Lead-quality dominates; spend Opus where it routes the tree |
| Joint optimization (role + model + topology) cost cut | ~65% | Co-design the team; do not pick agents in isolation |
| Specification's share of multi-agent failures | ~42% | Tightening role definitions is the highest-leverage fix |

Treat these as orders of magnitude. Exact numbers shift with model generation and workload; the relative ranking has been stable across reports.

---

## §5. Framework capability matrix

Phrase as capabilities rather than version-pinned recommendations.

| Need | Look for |
|---|---|
| Durable agent definitions in markdown with frontmatter | Claude Code-style subagents |
| Role-goal-backstory DSL with quick prototyping | Role-DSL frameworks (CrewAI-style) |
| Explicit state machine, branching, checkpoints, replay | State-machine frameworks (LangGraph-style) |
| Conversational loops with self-recovery | Conversational frameworks (AutoGen-style) |
| Vendor-neutral interop | Emerging A2A-style standards |

Always check active maintenance status before committing. Agent-framework lifecycle changes are common — projects sunset or enter maintenance mode on a months-not-years timescale.

---

Sources: Anthropic engineering writeups on Claude agent design and tool description tuning, peer-reviewed multi-agent failure research, framework documentation. See SKILL.md primary sources.
