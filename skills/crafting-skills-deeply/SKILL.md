---
name: crafting-skills-deeply
description: Multi-agent variant of craft-skill for hard topics. Decomposes topic into 3-7 subtopics, fans out to parallel skill-researcher subagents (each with non-overlapping scope), synthesizes findings into a draft, then runs an evaluator-optimizer critique loop with skill-critic (max 2 rounds) before the standard review→save flow. Use when crafting a skill on a topic that needs grounded citations, spans multiple distinct subtopics, or is high-leverage enough to justify ~15× token cost over single-pass research. Falls back to /craft-skill if topic decomposes to ≤2 subtopics. Triggers on "deep skill crafting", "rigorous skill research", "multi-agent skill build", "ทำ skill เรื่องยาก", "craft skill อย่างละเอียด", "crafting hard topic skill", "deep craft skill", "skill วิจัยลึก".
argument-hint: "[topic]"
allowed-tools: "Read Write Glob Grep WebSearch WebFetch AskUserQuestion Agent"
---

# Crafting Skills Deeply

Heavier-weight variant of `/craft-skill` for HARD topics — multi-agent research, structured critique loop, optional citation verification — while preserving the original Phase 1–5 structure.

<!-- Informed by /designing-subagent-systems and /designing-agent-roles — consult them only if the decomposition or agent-role design is unclear. -->

## When to use this vs /craft-skill

**Use this when:**
- Topic spans 3+ distinct subtopics each needing depth
- Risk of folklore vs grounded patterns (sources disagree, opinion-heavy domain)
- Skill will be high-leverage / reused across many sessions
- Citation-backed claims matter, not vibes

**Use `/craft-skill` (lighter) when:**
- Single-pass research suffices
- Topic is shallow / already familiar
- Speed > rigor

**If unsure**: start here. The decomposition step (2a) will fall back to `/craft-skill` automatically if the topic is shallower than expected.

## Phase 1: Get topic

Topic comes from `$ARGUMENTS`. If empty, ask the user what topic.

## Phase 1.5: Scout for published expert skills (subagent)

**Spawn a general-purpose Agent** to scout — keeps raw search noise out of main context.

Scout prompt template:
```
Search the web for published Claude Code skills, guides, or frameworks on the topic: "[TOPIC]".

Use ≤6 queries, run in parallel where possible:
- "SKILL.md" [topic] site:github.com
- [topic] "claude code skill" OR "claude skill" site:github.com
- [topic] claude code guide OR framework OR workflow
- Check known publishers: Matt Pocock (TypeScript/JS/tooling), Andrej Karpathy (AI/ML/coding practice), community packs on GitHub

Return ONLY a structured summary — do NOT return raw search results:
- found: true/false
- matches: list of { title, author, url, one_line_summary } (empty list if nothing found)
```

> **SYNC NOTE:** This scout block is duplicated from `/craft-skill` Phase 1.5. If you edit either, update the other too.

**After the agent returns:**

If `found: true` → show the user the match list and ask via `AskUserQuestion`:
- **Use as base** — WebFetch the raw content, treat as a pre-built researcher finding; fold into synthesis (2c), skip overlapping subtopics in decomposition
- **Use as reference** — pass URLs to researchers as supplementary sources; still do full decomposition
- **Ignore** — proceed as if nothing was found

If `found: false` → skip straight to Phase 2 without mentioning the scout.

## Phase 2: Deep research (multi-agent)

### 2a. Decompose + pick research source

First, the main agent decomposes the topic internally into 3–7 non-overlapping subtopics. Each subtopic gets:
- One-sentence brief (what to find out)
- Why it matters → which skill dimension it maps to: description WHAT / WHEN / KEYWORDS, body workflow, reference detail, or examples
- Tool-call budget hint

Decomposition heuristics:
- Simple → 1–2 subtopics
- Comparative → 3–4 subtopics, partition by entity
- Broad / foundational → 5–7 subtopics, partition by aspect
- **Cap at 7.** More = orchestration overhead > work.

**Fallback rule**: if topic decomposes to ≤2 meaningful subtopics, abort the multi-agent path and run `/craft-skill` instead. Tell the user why. When handing off, explicitly carry over the topic, scout result, source choice, and decomposed subtopics so `/craft-skill` can skip re-asking those questions.

Then **show the subtopics to the user** alongside a combined `AskUserQuestion`:

> "พบ N subtopics: [list]. จะใช้ source ไหนวิจัย และต้องการแบบไหน?"

**Source options** (do NOT auto-select):
1. **WebSearch + WebFetch** — general web research
2. **claude-code-guide agent** — Claude Code, Agent SDK, Anthropic API topics
3. **Local files** — Read/Glob/Grep on a path the user provides
4. **Mix** — user names which sources to combine

**Rigor options:**
- **Thorough** — run citation check after synthesis (Phase 2d)
- **Faster** — skip citation check

(If user chose "Use as base" in Phase 1.5, the fetched content is already a primary source; adjust decomposition scope to avoid redundant subtopics.)

Store the source choice and rigor preference — both are used in later phases.

### 2b. Parallel research (sectioning)

In **ONE assistant turn**, spawn N `skill-researcher` subagents. Each receives:
- Its exact subtopic brief
- The full list of subtopics OTHER researchers are handling (anti-duplication)
- Source preference
- Tool budget

The `skill-researcher` agent definition already specifies its output schema (structured findings + citations + tradeoffs + open questions + dimension fit).

**Critical**: single message, N `Agent` calls. Spawn-wait-spawn defeats parallelism.

**After all agents return — triage before synthesizing:**
- If a researcher returned <3 findings or an error: re-spawn that agent ONCE with the same brief.
- If the re-spawn also fails, flag that subtopic as a gap and proceed without it.
- If >50% of researchers failed: abort. Tell user the topic lacks grounded sources; suggest reframing or switching to `/craft-skill`.
- Document all gaps clearly so they surface in Phase 4.

### 2c. Synthesize

After all researchers return, the main agent reads:
- All findings + citations
- `~/.claude/docs/skill-authoring-checklist.md` (escalate to `skill-authoring-rules.md` only on uncertainty)

Then draft:
- SKILL.md frontmatter — `name` + `description` (WHAT + WHEN + KEYWORDS, ≤1024 chars, 3rd person, active verb)
- SKILL.md body (≤500 lines)
- `reference.md` / `examples.md` if content needs splitting (one level deep only)

Apply the checklist during drafting. **Do not delegate synthesis** — the main agent reads the research and decides; workers only fetched.

After drafting, write a `findings-bundle.md` alongside the draft files:
- One section per researcher: subtopic name + full findings output (copy verbatim, do not summarize) + source URLs
- Note any gaps from researchers that failed in 2b

This file is passed to `skill-critic` in Phase 2e and deleted after Phase 5.

### 2d. Citation check (optional)

For each citation URL in the draft:
- Quick WebFetch (HEAD or short GET)
- Flag dead links; remove or replace them in the draft **before** the critic runs

Skip if:
- Draft has <5 citations, OR
- User chose "Faster" in Phase 2a rigor preference

### 2e. Critique loop (evaluator-optimizer, max 2 rounds)

1. Spawn `skill-critic` with paths to: draft files + `findings-bundle.md` (written in 2c).
2. If `verdict = ACCEPT` → exit loop.
3. If `verdict = REVISE` → fix only the Critical issues called out. Leave rest untouched. Re-invoke `skill-critic`.
4. After 2 rounds regardless: hand off to user review (Phase 4) and surface any remaining critic notes.

Termination cap prevents endless refinement.

### 2f. Evaluation scenarios + fresh-Claude walkthrough

After the critic accepts, follow `~/.claude/docs/skill-authoring-checklist.md` → `Evaluation scenarios` (write 3) and `Fresh-Claude walkthrough` (run against each). Fix draft on failure; note unfixable gaps for Phase 4.

## Phase 3: Pre-save checklist

Run the **Pre-save checklist** in `~/.claude/docs/skill-authoring-checklist.md`. Catches anything the critic missed. Escalate to `skill-authoring-rules.md` §10 only on uncertainty.

Collect any checklist items that failed — surface them in Phase 4 item 8.

## Phase 4: Review with user

Show the user:
1. Proposed `name` and full save path
2. Full draft of SKILL.md
3. All reference files (with content)
4. One-line rationale for each non-obvious choice
5. Flagged dead citations (if 2d ran)
6. Remaining critic notes (if 2e hit max iterations)
7. The 3 evaluation scenarios from 2f + walkthrough result (pass/fail per scenario, any noted gaps)
8. **Pre-save checklist findings from Phase 3** (if any items failed — list each with severity)

Use `AskUserQuestion`:
- **Save as-is** → Phase 5
- **Edit first** → user states changes, iterate
- **Cancel** → abort, no files written

Same as `/craft-skill` Phase 4.

## Phase 5: Save on approval

1. Create `~/.claude/skills/<name>/` folder
2. Write `SKILL.md`
3. Write any reference files
4. Delete `findings-bundle.md` (ephemeral, not part of the saved skill)
5. Confirm with absolute paths

Same as `/craft-skill` Phase 5.

## Naming collisions

Before saving, check if `~/.claude/skills/<name>/` already exists. If yes, ask: rename / overwrite / cancel.

## Abort conditions (mid-phase)

- Decomposition → ≤2 subtopics → switch to `/craft-skill`, carry over topic + scout result + source choice
- All researchers return mostly-empty findings → topic may lack grounded sources. Tell user; suggest reframing or using `/craft-skill`
- Critic rejects 2 rounds with the same issues → topic may be intrinsically thin. Tell user; offer to save with caveats or abort

## Cost expectation

This skill uses **~15×** the tokens of single-pass `/craft-skill`. Worth it for durable, high-leverage skills. Not worth it for one-off topics invoked twice.

The `skill-researcher` parallel fan-out is the bulk of the cost — cap fan-out at 7 to keep this bounded.

## Anti-patterns specific to this workflow

1. **Decomposing into overlapping subtopics** → researchers duplicate work. Fix: each subtopic owns a disjoint slice; tell each worker what others cover.
2. **Synthesizing inside a worker** → loses the orchestrator's view. Fix: workers only return findings; main agent always synthesizes.
3. **Skipping the critic** → defeats the rigor that justified using this skill. Fix: always run at least round 1; only skip if topic was trivially decomposed.
4. **Endless critic loop** → wasted tokens. Fix: hard cap at 2 rounds.
5. **Reading worker `output_file` mid-flight** → pulls JSONL noise into your context. Fix: trust completion notifications.
6. **Passing only draft files to skill-critic** → critic can only check formatting, not whether claims are grounded. Fix: always pass `findings-bundle.md` alongside the draft.

---

Companion agents (saved alongside this skill):
- `skill-researcher` → `~/.claude/agents/skill-researcher.md`
- `skill-critic` → `~/.claude/agents/skill-critic.md`
