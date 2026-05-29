---
name: designing-agent-roles
description: Designs each subagent's role, tool scope, model choice, and system prompt — the per-agent specialty layer beneath workflow shape. Use when defining agents in ~/.claude/agents/ or .claude/agents/, picking tools and model per agent, writing an agent's system prompt body, deciding specialize-vs-generalize, or composing a complementary team (lead + workers + reviewer ensemble). Covers agent definition frontmatter (tools, model, disallowedTools, permissionMode, maxTurns, mcpServers), least-privilege tool scoping, three-tier model routing (Haiku/Sonnet/Opus, ~60-70% cost cut), durable definition vs per-invocation prompt split, persona/role/goal structure, and anti-patterns like kitchen-sink agents, mismatched tool grants, description-body drift. Triggers on "design agent role", "agent specialty", "tool scoping", "pick model for agent", "subagent definition", "ออกแบบ agent", "ความถนัด agent", "สเปก agent", "agent persona", "role goal backstory".
---

# Designing Agent Roles

The *per-agent specialty* layer. Pairs with `designing-subagent-systems` (which picks workflow shape — chain vs parallel). This skill covers what each agent in that workflow actually *is*.

## 1. When to make a named agent

Create a definition in `~/.claude/agents/<name>.md` (personal) or `.claude/agents/<name>.md` (project, team-shared) when **two or more** are true:

- The role gets invoked repeatedly (frequency justifies maintenance)
- Distinct tool needs (read-only ≠ edit ≠ network access)
- Distinct model fit (cheap router ≠ deep reasoner)
- Distinct expertise lens (security ≠ perf ≠ style)
- Tighter system prompt buys you context budget vs a generalist

Otherwise: invoke a generalist subagent with a focused per-call prompt. Don't over-specialize.

## 2. The 4 levers per agent

| Lever | Question | Where it lives |
|---|---|---|
| **Role** | Who is this agent? What expertise should the LLM simulate? | System prompt body |
| **Tools** | What actions can it take? (least privilege) | `tools:` frontmatter |
| **Model** | What capability vs cost? | `model:` frontmatter |
| **Output format** | What does the caller need back? | System prompt body |

The **80/20 rule**: 80% of failures come from inadequate task specification, 20% from weak personas. Spend effort on tool scoping + output format first; backstory last.

## 3. Tool scoping — least privilege

**Principle**: ask "what *actions* do we allow this agent to perform?" — not "what tools does it have?" Each granted tool expands blast radius (prompt injection, mistakes).

Common scopes:

| Role | Tools |
|---|---|
| Reviewer / auditor | `Read, Glob, Grep, Bash` (read-only) |
| Researcher | `Read, Glob, Grep, WebSearch, WebFetch` |
| Refactorer | `Read, Edit, Glob, Grep, Bash` (no Write, no network) |
| Code fixer | `Read, Edit, Write, Glob, Grep, Bash` |
| Orchestrator | `Read, Agent(worker-a, worker-b)` (only spawn specific workers) |

Syntax notes:
- `tools:` is CSV (space or comma separated)
- Omit `tools:` → agent inherits parent's full tool set (usually too broad — set it explicitly)
- `disallowedTools:` for denylist (applied first, then `tools:` resolves remainder)
- `Agent(name1, name2)` to restrict which subagents this agent can spawn; omit `Agent` entirely to block subagent spawning

**Tool descriptions matter** — poor descriptions cut task completion by ~40% even when the right tool is available. Anthropic spent more time tuning tool descriptions than the prompt on SWE-bench. Treat descriptions as part of the prompt, not metadata.

## 4. Model selection — three tiers

| Tier | Model | Use for | Cost (rough) |
|---|---|---|---|
| Cheap | Haiku | Classification, routing, extraction, formatting, simple reads | 1× |
| Default | Sonnet | ~80% of work — multi-step reasoning, code, analysis | ~3.75× Haiku |
| Premium | Opus | Novel reasoning, planning, multi-file architecture | ~5× Sonnet |

Three-tier routing can cut total cost **60-70%** vs all-Opus with no quality loss on the complex tasks.

**Why Anthropic's research system uses Opus-lead + Sonnet-workers**:
- Lead does the *one-shot* hard part (decompose, allocate, synthesize). Worth Opus — get this wrong, the whole tree wastes tokens.
- Workers do *well-scoped, parallelizable* subtasks. Sonnet enough; you can run more of them within budget.
- Citation/verifier split out as different *shape* of task → different role → its own model choice.
- Reported result on research-style tasks: Opus-lead + Sonnet-workers outperforms a single Opus by ~90%. Lead-quality dominates outcome more than uniform model power across the tree.

**Field**: `model: haiku | sonnet | opus | inherit` (default: `inherit`).

**Flip it (cheap lead, premium worker) only when**: lead is a thin classifier and exactly one worker does the deep reasoning.

## 5. System prompt body — durable vs per-invocation

**Goes in the agent definition (durable):**
- Identity / role ("You are a senior code reviewer ensuring high standards…")
- Scope of responsibility (what's in, what's out)
- Default output format
- Hard constraints ("never modify files outside src/")
- Working approach / checklist if stable

**Goes in the per-invocation prompt:**
- This specific task
- Context the fresh agent doesn't have
- Success criteria for *this* call
- What other agents are concurrently handling

**Drift rule**: instructions that recur at every invocation belong in the definition. A definition contradicted at every invocation is wrong.

**Length norm**: 150–400 words for the system prompt body.

**Persona/role/goal/backstory** (CrewAI framing):
- **Role** — *"Senior data researcher specializing in market trends"* outperforms *"Researcher"*
- **Goal** — outcome-oriented: *"Find the 10 most impactful developments"*, not *"research things"*
- **Backstory** — only when domain expertise or edge-case judgment matters; otherwise theater

Minimum viable definition: specific role + outcome-shaped goal + tools + output format.

## 6. Frontmatter quick reference

Required:
```yaml
name: code-reviewer            # lowercase + hyphens, unique
description: ...               # WHEN Claude should delegate to this agent
```

Common optional:
```yaml
tools: Read, Glob, Grep, Bash  # allowlist (CSV)
disallowedTools: Write, Edit   # denylist
model: sonnet | haiku | opus | inherit  # default: inherit
permissionMode: default | acceptEdits | plan | bypassPermissions  # default: default
maxTurns: 10                   # cap to prevent runaway cost
mcpServers: [...]              # scoped MCP servers
skills: [skill-name]           # preload skills into agent context
hooks: { PreToolUse: ... }     # lifecycle hooks
isolation: worktree            # run in isolated git worktree
color: blue                    # UI display
```

Body = the agent's system prompt (replaces default).

**Important**: by default subagents do **not** spawn further subagents (no nesting). To allow it, explicitly grant `Agent(name1, name2)` in `tools`.

See `templates.md` for full agent definition examples.

## 7. Specialize vs generalize

The "and" test (CrewAI): if the role joins distinct operations with "and" (research AND analyze AND write), split it. Single-role agents outperform combined ones.

But — Anthropic's failure mode was the opposite: too-vague briefs ("research the semiconductor shortage") made workers duplicate searches. Each agent (or each invocation) needs **objective + output format + tool/source guidance + clear boundaries**.

Heuristic: specialize when 2+ are true (see §1). Otherwise default to generalist.

## 8. Composition patterns (per-role tradeoffs)

| Pattern | Lead role | Worker role | Why it works | Failure mode |
|---|---|---|---|---|
| Orchestrator-workers | Decompose / synthesize | Self-contained subtask | Parallel context windows; lead reasons hardest | Vague worker briefs → duplication |
| Reviewer ensemble | Aggregate findings | One concern each (security/perf/tests) | Cheap parallelism; union for recall | Reviewers tread on overlapping concerns |
| Generator + critic | n/a (loop) | Generator + evaluator | Iterative refinement, clear eval | No termination → token blowout |
| Planner + executor | High-context plan | Scoped, mechanical execution | Cheap execution; expensive thinking once | Plan too vague to execute mechanically |
| Specialist + generalist | Generalist routes | Specialists handle deep cases | Breadth + depth | Routing classifier wrong → wrong specialist |

For workflow shape choice (when to use each), see `designing-subagent-systems`.

## 9. Anti-patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| **Kitchen-sink agent** | All tools, vague role, does everything badly | Decompose into specialists with focused descriptions |
| **Over-specialized duplicates** | 5 nearly-identical reviewers | Differentiate descriptions AND prompts; or use one with parallel invocations |
| **Mismatched tool grant** | Reviewer with Edit/Write; refactorer without Write | Align tools to action verb in role |
| **Tool scope too broad** | Researcher with Edit/Write/Bash | Restrict to read + network only |
| **Wrong model** | Opus for routing; Haiku for novel reasoning | Three-tier routing (§4) |
| **Description-body drift** | Description says "reviewer", body says "implement fixes" | Keep them consistent — description controls delegation |
| **Confused identity** | Role unclear → agent does whatever's easiest | Specific role: *"Senior X specialist"* not *"Helper"* |
| **No output format** | Agent returns prose; caller needs structured | Add to body: *"Output as: severity / file:line / fix"* |
| **Unbounded turns** | Agent loops on hard task | Set `maxTurns: 10` |
| **Bad tool descriptions** | Agent picks wrong tool path | Tune tool descriptions; remove redundant tools |
| **Rigid role refusal** | Agent declines reasonable adjacent work ("not my role") → downstream agents idle waiting for handoff → throughput collapses | Define role by the *output unit* it produces, not by exclusion of adjacent work |
| **No observable done condition** | Agent loops until `maxTurns` or stops early on vague satisfaction | Specify what "done" looks like as an artifact / predicate / threshold — not "when you feel confident" |

## 10. Quick design checklist

Before saving an agent definition, verify:

- [ ] Name is lowercase + hyphens, action-oriented
- [ ] Description tells Claude **when** to delegate ("Use proactively for…" / "Use when…")
- [ ] Tools are minimal necessary set (least privilege)
- [ ] Model matches task tier (Haiku/Sonnet/Opus)
- [ ] Body ≤ ~400 words; specific role + goal + format + constraints
- [ ] Description and body agree on what the agent does
- [ ] Output format specified
- [ ] `maxTurns` set if agent risks looping
- [ ] No "and" in role (split if so)
- [ ] Done condition is observable (artifact / predicate / threshold), not just `maxTurns` expiry

## 11. Templates & deeper reference

See `templates.md` for production-ready agent definitions:
- `code-reviewer` (read-only, ensemble-friendly)
- `security-auditor` (read-only, narrow lens)
- `researcher` (web + read)
- `refactorer` (read + edit, no network)
- `planner` (read-only, Opus, no execution)
- `routing-classifier` (Haiku, no tools)

See `reference.md` for: §1 done-condition forms (artifact / predicate / threshold / schema); §2 inter-agent contracts and trust model (treat worker output as untrusted input); §3 infrastructure-layer access control (prompt < tool allowlist < sandbox < identity scoping); §4 empirical findings table (tool description quality, three-tier routing savings, lead-vs-uniform model gain); §5 framework capability matrix.

