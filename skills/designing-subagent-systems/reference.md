# Subagent System Reference

Deep reference for `designing-subagent-systems`. Complements `examples.md` (canonical patterns + copy-paste templates) with empirical findings, failure taxonomy, and emerging design patterns.

## Contents

- §1 — Failure mode taxonomy
- §2 — Empirical findings
- §3 — Emerging patterns
- §4 — Framework capability matrix

---

## §1. Failure mode taxonomy

Production multi-agent failures decompose into three categories. The percentages are empirical from large-scale evaluations of agent systems across frameworks.

### Specification failures (~42%)

Root cause: brief, role, or scope is unclear at the point of handoff.

- **Ambiguous objective** — worker can't tell when "done"
- **Missing scope boundary** — workers run overlapping work
- **Underspecified output format** — caller can't aggregate worker outputs
- **Implicit assumptions** — worker guesses wrong about the user's intent
- **No success criteria** — agent over-runs budget chasing a vague target

Highest-leverage category. Fix specification before chasing coordination or verification.

### Coordination failures (~37%)

Root cause: inter-agent handoff, state, or sequencing.

- **State drift** — workers see inconsistent views of shared state
- **Race conditions** — parallel workers mutate the same resource
- **Lost messages** — parent doesn't reliably receive worker output (e.g., truncation, parse failure)
- **Sequencing errors** — worker runs before its dependency completes
- **Deadlocks** — circular waits between agents (rare but catastrophic)

Often structural; fixes require redesigning the topology, not just the prompts.

### Verification failures (~21%)

Root cause: missing or weak checks on worker output.

- **No critic** — erroneous worker output flows into final synthesis
- **Collective delusion** — critic shares producer's context → confirms producer's errors
- **Missing termination** — loop runs until budget exhausted with marginal gains
- **No partial-failure handling** — one worker silently fails; others compute on incomplete data

Fix priority across the three categories: **specification → verification → coordination**. Specification is cheapest and highest leverage; verification adds small effort but catches the worst outcomes; coordination usually needs structural change.

---

## §2. Empirical findings

| Finding | Magnitude | Implication |
|---|---|---|
| Multi-agent token cost (vs chat baseline) | ~15× | Reserve for high-value or wall-clock-critical work |
| Single-agent token cost (vs chat baseline) | ~4× | Default; multi-agent must clear a high bar to be worth it |
| Token usage's share of quality variance | ~80% | Most quality differences come from budget, not architecture |
| Error amplification — flat/peer topology | ~17× vs single agent | Avoid bag-of-agents shape |
| Error amplification — centralized hierarchy | ~4× vs single agent | Tolerable when work value justifies it |
| Latency cut — speculative tool execution | ~48% | Significant on IO-bound research workloads |
| Throughput gain — speculative tool execution | ~1.8× | Same |
| Task completion time cut — self-improving prompts | ~40% | Worth instrumenting agents to learn from their own failures |

Treat as orders of magnitude. Exact numbers shift with model generation and workload; the relative ranking is the durable part.

---

## §3. Emerging patterns

### Speculative tool execution

While the agent reasons about its next step, optimistically execute the *likely* next tool call in parallel with the model's validation. If validation confirms the speculative choice, the result is already in hand; if not, discard.

**Use when:** tool calls have predictable next-step patterns (research workflows: search → fetch → summarize; data pipelines: extract → validate → enrich) and tool execution dominates latency.

**Avoid when:** code generation, math, or reasoning-heavy tasks — speculative paths are wrong often enough that retry cost outweighs savings.

**Risk:** wasted tokens on discarded speculative paths; debugging becomes harder because the agent's actual reasoning trace diverges from the executed path.

### Context offloading via fresh subagent

When a long-running agent's context grows large, hand off to a fresh subagent — **do not wait until the window is full**. A good trigger is ~**70–75% of the context window**; by that point there is still enough room to write a complete handoff summary without rushing, and the fresh agent starts with headroom to work. Waiting until 90–100% forces a rushed, lossy summary and risks hitting the limit mid-handoff.

**How to hand off:** run `/handoff` in the current session. This produces a structured summary of the current task state, decisions made, work remaining, and any constraints the next agent must know. Spawn a fresh subagent with that handoff document as its sole input.

**Why it works:** the fresh agent operates on focused context. The original agent's bloated history is gone, so it does not pollute downstream reasoning.

**Requirement:** the handoff must be lossless for the downstream task. Validate by checking whether the fresh subagent can complete the original goal using only the handoff document.

**Anti-pattern:** treating context offloading as "carry on with fewer tokens." If the handoff loses a key constraint, the fresh agent silently makes a wrong decision the original would have caught.

### Subagent as query proxy

When the orchestrator needs a fact or summary derived from external content (file, web page, database record), don't load the raw content into the orchestrator's context. Instead, spawn a fresh subagent whose only job is to read the source and return the answer.

**The test:** before any fetch, ask *"does the orchestrator need the raw data, or just the answer?"* If just the answer, delegate.

**Why it matters:** unlike context offloading (which is reactive — spawn a fresh agent *after* context is full), this is proactive — the orchestrator's context never gets polluted in the first place.

**Example:** multi-agent research system. Main orchestrator needs to know "what is the conclusion of report.pdf?" Wrong: orchestrator reads the full PDF. Right: orchestrator spawns a reader subagent with the file path and the specific question; subagent returns one paragraph.

**Limit:** if the orchestrator genuinely needs to reason over the raw content (e.g., line-by-line diff review), delegating loses information. Use judgment — the test is whether the answer can be fully expressed in the subagent's output format.

### Effort-scaled fan-out

Put scaling rules directly in the orchestrator prompt rather than hardcoding worker counts:

```
Effort scaling:
  Simple lookup        → 1 worker, ≤5 tool calls each
  Comparative analysis → 2-4 workers, ~10 tool calls each
  Broad research       → 10+ workers, partitioned subtopics
```

Without explicit scaling, orchestrators default to fixed fan-out regardless of input — causing over-spawn on trivial queries (token waste) or under-spawn on complex ones (quality loss).

### LLM-assisted prompt self-improvement

After failure cases, give the orchestrator (or a separate analyzer agent) its own transcript + a "what went wrong?" prompt. Apply the diagnosis as edits to the agent's system prompt. Iterate.

Reported gain: ~40% reduction in task completion time when the system can identify and correct its own failure modes. Works best when failure signal is clear (test failed, output rejected, user corrected) rather than diffuse.

---

## §4. Framework capability matrix

Phrase as capabilities rather than version-pinned recommendations — agent framework landscape shifts on a months-not-years timescale.

| Capability you need | Look for |
|---|---|
| Explicit state machine + checkpointing + replay | State-machine frameworks (LangGraph-style) |
| Quick role-based prototyping with role-goal DSL | Role-DSL frameworks (CrewAI-style) |
| Conversational error recovery loops | Conversational frameworks (AutoGen-style) |
| Native Claude tool use, subagents in markdown | Claude Code subagents / Claude Agent SDK |
| Vendor-neutral agent-to-agent communication | Emerging interop standards (discovery + capability + auth) |

Selection heuristic:

- Need production state guarantees → prefer state-machine framework
- Prototyping multi-role workflow fast → role-DSL framework
- Dialogue-shaped task with iterative repair → conversational framework
- Already inside Claude Code or Anthropic SDK → built-in subagents

Always check active maintenance status and ecosystem fit before committing. Agent-framework lifecycle changes are common.

---

Sources: Anthropic engineering writeups on Claude agent design, peer-reviewed multi-agent failure taxonomy research, topology-vs-reliability evaluations, speculative-execution and self-improving-prompt studies. See SKILL.md primary sources.
