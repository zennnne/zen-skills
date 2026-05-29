---
name: designing-subagent-systems
description: Designs efficient subagent systems by choosing between sequential workflow and parallel decomposition shapes, then drafts orchestrator and worker prompts using proven patterns. Use when designing multi-agent systems, deciding whether to chain or parallelize subagents (workflow vs parallel), decomposing complex tasks for delegation, or diagnosing slow/expensive multi-agent setups. Covers prompt chaining, routing, sectioning (parallel independent), voting (parallel consensus), orchestrator-workers (dynamic fan-out), evaluator-optimizer loops; subagent vs fork tradeoffs; cost rules (multi-agent ~15× tokens, parallelism worth it for high-value/IO-bound work); anti-patterns like over-decomposition, vague briefs, shared mutable state. Triggers on "design subagent", "parallel agents", "multi-agent workflow", "ออกแบบ subagent", "sub agent แบบ workflow", "parallel sub agent", task decomposition, orchestrator, worker, fan-out, Task/Agent tool.
---

# Designing Subagent Systems

Pick the right execution shape (workflow vs parallel), then write briefs that survive context isolation.

## 1. The decision: which shape?

Run through these in order. Stop at the first match.

| Question | If YES → shape |
|---|---|
| Does step B need step A's output? | **Sequential workflow** (prompt chaining) |
| Are subtasks **predetermined** + independent? | **Parallel — sectioning** |
| Same task run N times for consensus / robustness? | **Parallel — voting** |
| Subtasks **discovered at runtime** by an orchestrator? | **Orchestrator-workers** |
| Distinct input categories want specialized handling? | **Routing** |
| Clear eval criteria + iterative refinement helps? | **Evaluator-optimizer loop** |

**Default bias**: start with the simplest shape that fits. Most production systems are *hybrids* — a sequential pipeline with one stage that fans out internally (e.g., `plan → [parallel implement N modules] → integrate → review`).

**Coding tasks rarely benefit from heavy parallelization** — most steps share evolving context. Research, breadth-first exploration, and independent evaluation do. (Anthropic's own guidance from the multi-agent research system writeup.)

## 2. Cost reality before you fan out

| Setup | Token cost (vs chat) |
|---|---|
| Single agent | ~4× |
| Multi-agent | ~15× |

Token usage explains ~80% of multi-agent quality variance. Parallelism pays when:

- Task is high-value (research report, critical decision)
- Wall-clock matters (90% time reduction documented)
- Workload is breadth-first / IO-bound
- Single context window is the bottleneck

Lever ranking for quality: **upgrade model > increase token budget > add agents.** Don't reach for parallelism first.

## 3. Subagent vs Fork

| Mechanism | Context | Use when |
|---|---|---|
| **Named subagent** (Agent tool with `subagent_type`) | Fresh — only the prompt you pass | Different expertise / tools, truly independent task, isolation desired |
| **Fork** (Agent tool, no `subagent_type`) | Inherits full parent context | Surveying / auditing your own current work; cheap because it shares prompt cache |

**Single-message rule for parallelism**: All parallel subagents must be spawned in *one* assistant turn (one message containing N Agent tool calls). Spawn-wait-spawn is sequential, not parallel.

**Don't peek at fork output_file** mid-flight — reading the JSONL transcript pulls the fork's tool noise into the orchestrator's context, defeating the point. Trust the completion notification.

## 4. Briefing skeletons

### Orchestrator prompt

```
ROLE: You decompose & delegate. You do not do the work yourself.
TASK: <user's high-level goal>
DECOMPOSITION:
  Simple → 1 worker
  Comparative → 2-4 workers, partition by entity
  Broad → up to N workers, partition by subtopic
PARTITIONING RULE: each worker owns a non-overlapping slice
WORKER OUTPUT FORMAT: <structured schema>
TERMINATION: stop when <criterion>; max <K> rounds
SYNTHESIS: aggregate workers' outputs into <final format>
```

### Worker (fresh subagent) brief

Fresh agents start with **zero context**. Brief like a smart colleague who just walked into the room.

```
CONTEXT: <minimum the fresh agent needs to act>
YOUR SLICE: <exact subtopic; what's IN, what's OUT, what others handle>
ALREADY TRIED / KNOWN: <to avoid duplicate work>
SUCCESS CRITERIA: <when you're done>
OUTPUT FORMAT: <structured — JSON or fixed sections>
BUDGET: <tool-call cap, word limit>
```

### Fork brief (inherited context)

Forks already have your context. Write directives, not background.

```
DIRECTIVE: <what to do, not what the situation is>
SCOPE: <what's in, what's out, what another agent is handling>
REPORT: <under N words; punch list, not narrative>
```

**Don't delegate understanding.** The orchestrator must specify exactly what to change / find / decide. Phrases like "based on your findings, fix the bug" push synthesis onto the worker — that's the orchestrator's job.

## 5. Anti-patterns

Empirical failure breakdown across production multi-agent systems: ~42% specification (ambiguous briefs / unclear roles), ~37% coordination (handoff and state drift), ~21% verification (missed errors). Fix specification first — it's the dominant failure mode and the cheapest to address. Full taxonomy in `reference.md`.

1. **Vague brief** — "research X" → workers run identical searches. Fix: explicit objective + scope + what's *out of scope*.
2. **Over-decomposition** — 50 workers for trivial query; orchestration overhead > work. Fix: scaling heuristics in the orchestrator prompt.
3. **Duplicated work** — parallel workers converge on the same thing. Fix: orchestrator must *partition* the space explicitly.
4. **Poor isolation** — worker gets too little context (can't decide) or too much (parent transcript bloats it). Fix: brief like a colleague who just walked in.
5. **Shared mutable state** between parallel workers — race conditions. Treat parallel workers as pure: in → out, no shared side effects.
6. **Unbounded fan-out** — N grows with input. Fix: cap concurrency.
7. **Context bloat in orchestrator** — workers return raw transcripts; lead's window fills. Fix: workers return *compressed* findings, not full output.
8. **Sequential disguised as parallel** — spawn-wait-spawn. Fix: one assistant turn, N Agent tool calls.
9. **Wrong workload** — coding/refactoring with shared evolving context fanned out. Fix: keep coding sequential, or fan out only at clearly independent file boundaries.
10. **Endless search** — agents looking for nonexistent sources. Fix: termination criteria + tool-call budgets in worker briefs.
11. **Flat topology (bag of agents)** — N peer agents without a designated orchestrator compound errors ~17× vs a single agent; centralized lead + workers caps amplification near ~4×. Fix: designate one orchestrator; avoid peer-to-peer chains where worker A directly calls worker B.
12. **Critic shares producer's context** — evaluator in an evaluator-optimizer loop inherits the producer's full reasoning trace → confirms producer's errors ("collective delusion"). Fix: give the critic a fresh context with only the producer's *output* and the eval criteria, not the producer's process.
13. **Orchestrator reads raw data it doesn't need** — main agent fetches a full file/page/report when it only needs a derived answer. Bloats orchestrator context unnecessarily. Fix: delegate the read to a fresh subagent; have it return only the answer, not the raw content. Ask before every fetch: *"does the orchestrator need the raw data, or just the answer?"* If just the answer, send a subagent.

## 6. Quick diagnostic

When a multi-agent setup feels slow / expensive / wrong:

| Symptom | Likely cause | Fix |
|---|---|---|
| Workers return overlapping findings | No partitioning | Add explicit slice per worker |
| Orchestrator context fills fast | Raw transcripts returned | Demand structured / compressed output |
| Total time ≈ sum of subagent times | Sequential, not parallel | One turn, N Agent calls |
| Quality didn't beat single agent | Wrong workload (probably coding-shaped) | Use single agent + bigger budget |
| Workers ask "what should I do?" | Brief too vague | Add success criteria + scope boundaries |

## 7. Reference material

`examples.md` — §1 the 6 canonical patterns in depth (when to use, when to avoid, concrete example, common mistake); §2 copy-paste templates for: parallel code review, research synthesis, ship-readiness audit, multi-file refactor, test generation, document pipeline; §3 decision quick reference table.

`reference.md` — §1 failure mode taxonomy (specification / coordination / verification, with sub-modes); §2 empirical findings table (token cost, error amplification, latency/throughput numbers); §3 emerging patterns (speculative tool execution, context offloading via fresh subagent, effort-scaled fan-out); §4 framework capability matrix.

---

Sources: [Building Effective AI Agents — Anthropic](https://www.anthropic.com/research/building-effective-agents), [How we built our multi-agent research system — Anthropic Engineering](https://www.anthropic.com/engineering/multi-agent-research-system), Claude Code subagents & Agent SDK docs.
