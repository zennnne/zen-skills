---
name: craft-skill
description: Research a topic and craft a new SKILL.md from the findings, then save to ~/.claude/skills/. Use when user wants to learn something and turn it into a reusable skill, or says "ศึกษา X แล้วทำ skill", "create skill on Y", "build skill from research", "craft skill".
allowed-tools: "Read Write Glob Grep WebSearch WebFetch AskUserQuestion Agent"
argument-hint: "[topic]"
---

# Craft Skill

Two-phase workflow: **research → review → save**. Authoring rules are crystallized in `~/.claude/docs/skill-authoring-checklist.md` — read that file once during drafting (Phase 3); escalate to `skill-authoring-rules.md` only on uncertainty.

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

**After the agent returns:**

If `found: true` → show the user the match list and ask via `AskUserQuestion`:
- **Use as base** — WebFetch the raw content, adapt it into the new skill (cite source), skip redundant research
- **Use as reference** — treat as one input among others, still do full Phase 2 research
- **Ignore** — proceed as if nothing was found

If `found: false` → skip straight to Phase 2 without mentioning the scout.
If the agent **errored** (network/timeout/crash) → briefly tell the user "scout failed, proceeding without it" then continue to Phase 2.

## Phase 2: Pick research source & conduct research

**Pick source** — use `AskUserQuestion`. Do NOT auto-select:

1. **WebSearch + WebFetch** — general web research. Best for libraries, frameworks, public APIs
2. **claude-code-guide agent** — for Claude Code, Claude Agent SDK, Anthropic API topics
3. **Local files** — Read/Glob/Grep on a path the user provides. Best for codebase-specific knowledge
4. **Mix** — user names which sources to combine

(If user chose "Use as base" in Phase 1.5, pre-select the fetched content as the primary source and adjust scope accordingly.)

**Then research thoroughly.** Stop as soon as all 6 dimensions can be answered confidently — do not over-research. If after ~8 fetches the dimensions still can't be filled with confidence, ask the user via `AskUserQuestion`: "This topic seems to need deeper research — switch to `/crafting-skills-deeply`?" If yes, invoke `/crafting-skills-deeply` directly. Then abort this skill. Extract these dimensions (each maps to a part of the skill):

| Dimension | Used in |
|---|---|
| What it is / does | description WHAT |
| When it applies / typical scenarios | description WHEN |
| Domain keywords users would type | description KEYWORDS |
| Core procedures / workflows | SKILL.md body |
| Detailed reference material | separate `reference.md` file |
| Examples worth keeping | separate `examples.md` file |

## Phase 3: Load checklist then draft

Read `~/.claude/docs/skill-authoring-checklist.md` once now. Use its rules **during drafting**, then run the **Pre-save checklist** section once more **after Phase 4** (before showing user). Escalate to `skill-authoring-rules.md` only on uncertainty.

Default save target: `~/.claude/skills/<name>/SKILL.md` (Personal scope).

Decisions to make:
- Skill `name` (lowercase, hyphens, gerund preferred, ≤ 64 chars) — **check now** whether `~/.claude/skills/<name>/` already exists; if yes, resolve with user before drafting further (rename / overwrite / cancel)
- `description` (3rd person, WHAT + WHEN + KEYWORDS, ≤ 1024 chars)
- Whether body content needs splitting (`reference.md`, `examples.md`)
- Whether tools should be pre-approved via `allowed-tools`
- Whether the skill has side effects → `disable-model-invocation: true`

For edge cases not covered by the checklist, escalate per its `Escalation` section.

## Phase 4: Build evaluations + fresh-Claude walkthrough

Write 3 evaluation scenarios per the checklist's `Evaluation scenarios` section.

Then **spawn a subagent** for the fresh-Claude walkthrough — pass ONLY the draft SKILL.md content + the 3 scenarios (no research history, no topic context). Ask it: "Would this skill trigger correctly? Would steps be followable with zero prior context?"

Revise the draft if any scenario fails; note unfixable gaps for Phase 5.
Keep scenarios + subagent results in a scratch section — shown to the user in Phase 5.

## Phase 5: Review with user

Show the user:
1. Proposed `name` and full save path
2. Full draft of SKILL.md
3. Any reference files (with their content)
4. The 3 evaluation scenarios + walkthrough results from Phase 4
5. One-line rationale for each non-obvious choice (e.g., "split to reference.md because body would exceed 500 lines")

Use `AskUserQuestion` to ask:
- **Save as-is** — proceed to Phase 6
- **Edit first** — user states what to change, iterate from Phase 3
- **Cancel** — abort, no files written

## Phase 6: Save on approval

1. Create `~/.claude/skills/<name>/` folder
2. Write `SKILL.md`
3. Write any reference files (`reference.md`, `examples.md`, etc.)
4. Confirm to user with absolute paths

