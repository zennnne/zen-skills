# Subagent System Examples

Deep reference for `designing-subagent-systems`. Three sections:
- §1 — the 6 canonical patterns in depth
- §2 — copy-paste templates for common real use cases
- §3 — decision quick reference table

## Contents

- §1 — The 6 canonical patterns
- §2 — Copy-paste templates
- §3 — Decision quick reference

---

## §1. The 6 canonical patterns

### 1. Prompt chaining (sequential)

**Shape**: A → B → C, each step uses the prior output.

**Use when**: task decomposes into fixed steps; each step builds on prior. Simplifies each call → improves accuracy.

**Avoid when**: steps are unpredictable or share complex interdependencies.

**Example**: research → plan → implement → review. Claude Code's `/plan` → implement → `/review` is exactly this.

**Common mistake**: trying to parallelize when B genuinely needs A. Result is wrong outputs, not just slower.

**Artifact passing**: parent reads each step's final message and writes the next worker's prompt. Subagents *cannot* call each other directly. Use files (Write a structured artifact, pass the path) when output is large.

---

### 2. Routing

**Shape**: classify input → branch to a specialist.

**Use when**: distinct input categories benefit from specialized prompts (refund vs tech support; fast model for easy / mid-tier for hard / frontier for complex).

**Avoid when**: categories overlap, classification is unreliable.

**Example**: support triage. A small classifier model decides if a ticket is "billing", "outage", or "feature request"; each goes to a specialist subagent with tailored tools and tone.

**Common mistake**: putting routing logic inside a generalist prompt instead of as an explicit classifier — the generalist tries to do all categories badly.

---

### 3. Sectioning (parallel, predetermined subtasks)

**Shape**: orchestrator splits task into N **known** independent subtasks → fan out → aggregate.

**Use when**: subtasks are independent, predetermined, and aggregation is cheap. Wins on speed.

**Avoid when**: subtasks are sequential, or subtask list depends on input (use orchestrator-workers instead).

**Example**: code review with reviewers per concern (security / perf / tests / style). All four spawned in one assistant turn; results synthesized into a single review.

**Common mistake**: not partitioning — workers all "review the PR" and return overlapping findings. Each worker must own a clearly disjoint slice.

---

### 4. Voting (parallel, consensus)

**Shape**: same task run N times → vote / union / intersection.

**Use when**: need consensus or robustness; one-shot accuracy isn't enough.

**Avoid when**: single pass is already accurate; cost outweighs confidence gain.

**Example**: borderline content moderation — 3 safety reviewers vote. Vulnerability scan — N reviewers each flag issues; final list is the union (high recall) or majority vote (high precision).

**Common mistake**: confusing voting with sectioning. Voting = same prompt, N times. Sectioning = different prompts, partitioned slices.

---

### 5. Orchestrator-workers (dynamic fan-out)

**Shape**: orchestrator examines input → decides at runtime how many workers and what each does → fans out → synthesizes.

**Use when**: subtasks **cannot be predetermined**. The orchestrator must look at the input first.

**Avoid when**: subtasks are predictable upfront (sectioning is cheaper and more reliable).

**Example**: Anthropic's multi-agent research system. Lead frontier-tier agent reads the user's question, decides on 3-10 subtopics, spawns mid-tier subagents in parallel, then a Citation Agent verifies claims. Effort scaling rule from their prompt:
- Simple fact-finding → 1 worker, 3-10 tool calls
- Comparison → 2-4 workers, 10-15 calls each
- Complex research → 10+ workers, divided responsibilities

**Common mistake**: orchestrator spawns max workers regardless of input. Add explicit scaling heuristics to the orchestrator prompt.

---

### 6. Evaluator-optimizer (loop)

**Shape**: generator → evaluator → (if rejected) generator with feedback → ... until accepted or budget hit.

**Use when**: clear evaluation criteria; iterative refinement measurably improves output (literary translation, complex search, code generation with tests as eval).

**Avoid when**: criteria are vague; single pass suffices.

**Example**: translation — translator generates draft, fluency evaluator critiques specific lines, translator revises only flagged lines, loop until evaluator accepts (max 5 iterations).

**Common mistake**: no termination — loop runs until token budget exhausted with marginal gains. Set a hard iteration cap and a "good enough" threshold.

---

## §2. Copy-paste templates

### Template A — Parallel code review (sectioning)

**Orchestrator (you, the main agent)** spawns 4 reviewers in one turn:

```
Agent({
  subagent_type: "code-reviewer",
  description: "Security review",
  prompt: "Review the diff in branch <X> for security issues ONLY.
    Scope: auth, input validation, secret handling, injection.
    Out of scope: performance, style, tests (other reviewers handle those).
    Output: numbered list, [severity] - [issue] - [file:line] - [fix].
    Max 10 findings."
})
Agent({ subagent_type: "code-reviewer", description: "Perf review", prompt: "..." })
Agent({ subagent_type: "code-reviewer", description: "Test coverage", prompt: "..." })
Agent({ subagent_type: "code-reviewer", description: "Style/idiom",   prompt: "..." })
```

All four in one assistant message. Then you synthesize into a single review.

---

### Template B — Research synthesis (orchestrator-workers)

**You as orchestrator** decompose user's research question:

```
1. Read the question; identify 3-N subtopics. Partition so no overlap.
2. For each subtopic, spawn a fresh research subagent with:
   - the *exact* subtopic
   - what other subagents are covering (so they don't duplicate)
   - sources to prefer
   - output: structured findings, max 300 words, citations required
3. After all return, write the synthesis yourself. Do not delegate synthesis.
```

Worker prompt skeleton:

```
You are researching ONE subtopic of a larger question.
SUBTOPIC: <exact slice>
PARENT QUESTION (for context only): <original>
OTHER SUBAGENTS ARE HANDLING: <list — do not duplicate>
SOURCES: prefer <X, Y>; avoid speculation.
OUTPUT: 5-10 bullet findings, each with citation. Max 300 words.
BUDGET: 8 tool calls.
```

---

### Template C — Ship-readiness audit (fork)

You're about to ship a branch. Fork to survey state without polluting your main context.

```
Agent({
  // no subagent_type → fork, inherits your context
  description: "Ship-readiness audit",
  prompt: "Audit this branch for ship readiness. Check:
    - uncommitted changes
    - tests cover the new code path
    - feature flag wired in build_flags.yaml
    - CI-relevant files changed
    Report: punch list of done vs missing. Under 200 words."
})
```

End your turn after launching. Wait for the notification. Don't peek at the output file.

---

### Template D — Multi-file refactor (hybrid: chain + sectioning)

```
Step 1 (sequential): planner subagent reads codebase, produces refactor plan.
Step 2 (parallel sectioning): one worker per file group, each refactors its slice.
   Partition by directory or module boundary so no two workers touch the same file.
Step 3 (sequential): integration agent runs tests, fixes cross-file issues.
Step 4 (sequential): you commit.
```

Critical: step 2 only parallelizes safely if the planner's output draws clean file-level boundaries. If files are tightly coupled, keep step 2 sequential.

---

### Template E — Test generation (sectioning per file)

```
For each source file in target directory:
  Agent({
    subagent_type: "test-writer",
    prompt: "Write tests for src/foo/<file>.ts.
      Read the file, infer behavior, write tests in test/foo/<file>.test.ts.
      Use the existing test framework (vitest).
      Out of scope: refactoring src/, adding new dependencies.
      Output: path of test file written + count of tests."
  })
```

All in one turn. Cap N — if there are 50 files, batch in groups of 8-10.

---

### Template F — Document pipeline (chain)

```
extract → validate → enrich → store
```

Each stage is a subagent or a function:
1. **Extract**: pull entities from raw doc → structured JSON
2. **Validate**: schema check + sanity rules → flag failures
3. **Enrich**: lookups, normalize, dedupe
4. **Store**: persist to DB

Why a chain works here: each stage's output is the next stage's input, and a failure at stage 2 should short-circuit (don't enrich invalid data). Add a checkpoint between extract and validate to resume on failure without re-extracting.

---

## §3. Decision quick reference

| You have... | Use |
|---|---|
| Steps where B needs A | Prompt chaining |
| N known independent subtasks | Sectioning |
| One task, want robustness | Voting |
| N depends on input | Orchestrator-workers |
| Distinct input categories | Routing |
| Output you can grade + iterate | Evaluator-optimizer |
| Surveying your own work | Fork |
| Need fresh expertise / tools | Named subagent |
| Coding with shared evolving context | Single agent (don't fan out) |

---

Sources: [Building Effective AI Agents — Anthropic](https://www.anthropic.com/research/building-effective-agents), [How we built our multi-agent research system — Anthropic Engineering](https://www.anthropic.com/engineering/multi-agent-research-system).
